import json
import sqlite3
from pathlib import Path

import httpx
import pytest
import yaml

from dqpilot_free.gemini import FreeInferenceBlocked, GeminiFree


@pytest.fixture
def config():
    result = yaml.safe_load((Path(__file__).resolve().parents[1] / 'config/free_gemini/pilot.yaml').read_text())
    result['minimum_seconds_between_generation_requests'] = 0  # Software test transport only.
    return result


@pytest.fixture
def free_key(monkeypatch):
    monkeypatch.setenv('DQP_GEMINI_API_KEY', 'SYNTHETIC_SOFTWARE_TEST_KEY')
    monkeypatch.setenv('DQP_GEMINI_FREE_TIER_CONFIRMED', 'true')


def payload(version='gemini-2.5-flash-test-fixture'):
    return {'modelVersion': version, 'usageMetadata': {'promptTokenCount': 7, 'candidatesTokenCount': 9,
            'totalTokenCount': 16, 'thoughtsTokenCount': 0},
            'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '{"rules": [], "abstentions": []}'}]}}]}


def test_missing_key_does_not_send_a_request(config, tmp_path, monkeypatch):
    monkeypatch.delenv('DQP_GEMINI_API_KEY', raising=False)
    provider = GeminiFree(config, tmp_path / 'calls.sqlite', httpx.MockTransport(lambda _: pytest.fail('network called')))
    with pytest.raises(FreeInferenceBlocked, match='MISSING'):
        provider.model_access()
    provider.close()


def test_key_alone_cannot_enable_a_billed_project(config, free_key, tmp_path, monkeypatch):
    monkeypatch.setenv('DQP_GEMINI_FREE_TIER_CONFIRMED', 'false')
    provider = GeminiFree(config, tmp_path / 'calls.sqlite', httpx.MockTransport(lambda _: pytest.fail('network called')))
    with pytest.raises(FreeInferenceBlocked, match='NON_BILLED'):
        provider.generate('safe metadata', 11, source_approved=True)
    provider.close()


@pytest.mark.parametrize('change', [{'paid_calls_authorized': True}, {'automatic_paid_fallback': True},
                                  {'automatic_model_substitution': True}, {'model': 'other-model'}])
def test_no_paid_or_model_fallback_can_be_configured(config, tmp_path, change):
    config.update(change)
    with pytest.raises(ValueError):
        GeminiFree(config, tmp_path / 'calls.sqlite')


def test_success_is_cached_with_real_usage_and_header_key_only(config, free_key, tmp_path):
    requests = []

    def handle(request):
        requests.append(request)
        assert request.url.host == 'generativelanguage.googleapis.com'
        assert not request.url.query
        assert request.headers['x-goog-api-key'] == 'SYNTHETIC_SOFTWARE_TEST_KEY'
        body = json.loads(request.content)
        assert body['generationConfig']['thinkingConfig']['thinkingBudget'] == 0
        assert body['generationConfig']['maxOutputTokens'] == 2048
        return httpx.Response(200, json=payload())

    path = tmp_path / 'calls.sqlite'
    provider = GeminiFree(config, path, httpx.MockTransport(handle))
    first, cached = provider.generate('safe metadata', 11, source_approved=True)
    assert not cached
    second, cached = provider.generate('safe metadata', 11, source_approved=True)
    assert cached and first == second and len(requests) == 1
    metadata = json.loads(provider.db.execute('SELECT metadata FROM requests').fetchone()[0])
    assert metadata['usage']['totalTokenCount'] == 16
    provider.close()
    assert b'SYNTHETIC_SOFTWARE_TEST_KEY' not in path.read_bytes()


def test_quota_error_is_preserved_and_never_retried(config, free_key, tmp_path):
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(429, json={'error': 'SYNTHETIC_SOFTWARE_TEST_KEY'})

    provider = GeminiFree(config, tmp_path / 'calls.sqlite', httpx.MockTransport(handle))
    for _ in range(2):
        with pytest.raises(FreeInferenceBlocked):
            provider.generate('safe metadata', 11, source_approved=True)
    assert len(requests) == 1
    assert provider.db.execute('SELECT status FROM requests').fetchone()[0] == 'HTTP_429'
    provider.close()


def test_attempt_cap_reserves_before_post(config, free_key, tmp_path):
    config['max_attempts'] = 1
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=payload())

    provider = GeminiFree(config, tmp_path / 'calls.sqlite', httpx.MockTransport(handle))
    provider.generate('safe metadata', 11, source_approved=True)
    with pytest.raises(FreeInferenceBlocked, match='ATTEMPT_CAP'):
        provider.generate('other metadata', 23, source_approved=True)
    assert len(requests) == 1
    provider.close()


def test_response_secret_echo_is_redacted(config, free_key, tmp_path):
    response = payload()
    response['unexpected_provider_echo'] = 'SYNTHETIC_SOFTWARE_TEST_KEY'
    path = tmp_path / 'calls.sqlite'
    provider = GeminiFree(config, path, httpx.MockTransport(lambda _: httpx.Response(200, json=response)))
    result, _ = provider.generate('safe metadata', 11, source_approved=True)
    assert 'SYNTHETIC_SOFTWARE_TEST_KEY' not in json.dumps(result)
    provider.close()
    with sqlite3.connect(path) as db:
        assert 'SYNTHETIC_SOFTWARE_TEST_KEY' not in db.execute('SELECT response FROM requests').fetchone()[0]


def test_changed_model_version_stops_further_calls(config, free_key, tmp_path):
    versions = iter(['fixture-v1', 'fixture-v2'])
    provider = GeminiFree(config, tmp_path / 'calls.sqlite',
        httpx.MockTransport(lambda _: httpx.Response(200, json=payload(next(versions)))))
    provider.generate('safe metadata', 11, source_approved=True)
    with pytest.raises(FreeInferenceBlocked, match='VERSION_CHANGED'):
        provider.generate('other metadata', 23, source_approved=True)
    with pytest.raises(FreeInferenceBlocked, match='MIXED_RETURNED'):
        provider.generate('third metadata', 37, source_approved=True)
    assert provider.db.execute("SELECT count(*) FROM requests WHERE status='COMPLETE'").fetchone()[0] == 2
    provider.close()


def test_missing_model_version_still_preserves_actual_response_and_usage(config, free_key, tmp_path):
    response = payload()
    del response['modelVersion']
    provider = GeminiFree(config, tmp_path / 'calls.sqlite',
        httpx.MockTransport(lambda _: httpx.Response(200, json=response)))
    with pytest.raises(FreeInferenceBlocked, match='MISSING_RETURNED_MODEL_VERSION'):
        provider.generate('safe metadata', 11, source_approved=True)
    status, stored, metadata = provider.db.execute('SELECT status,response,metadata FROM requests').fetchone()
    assert status == 'MISSING_RETURNED_MODEL_VERSION'
    assert json.loads(stored) == response
    assert json.loads(metadata)['usage']['totalTokenCount'] == 16
    provider.close()
