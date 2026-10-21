import json

import pandas as pd
import pytest

from dqpilot.llm import BlockedInference, Provider
from dqpilot.rules import Rule
from dqpilot.service import Service


def test_lifecycle_never_autoactivates_and_monitoring(tmp_path):
    s = Service(tmp_path / 'service.sqlite')
    s.propose(Rule('r', 'not_null', ['a'], evidence='Required field', origin='LLM'), 'source', 'generator')
    frame = pd.DataFrame({'a': ['x', '']})
    assert s.scan('source', frame)['findings'] == 0
    with pytest.raises(ValueError):
        s.transition('r', 'ACTIVE', 'actor', 'shortcut')
    s.validate('r', pd.DataFrame({'a': ['x']}), 'qualifier')
    assert s.scan('source', frame)['findings'] == 0
    s.transition('r', 'APPROVED', 'reviewer', 'Accepted')
    s.transition('r', 'ACTIVE', 'operator', 'Deploy')
    assert s.scan('source', frame)['findings'] == 1
    s.review(1, 'INVESTIGATING', 'reviewer', 'Investigate')
    assert len(s.monitoring('source')) == 3
    s.transition('r', 'DISABLED', 'operator', 'Pause')
    assert s.scan('source', frame)['findings'] == 0
    assert s.db.execute('SELECT count(*) FROM events').fetchone()[0] >= 9
    s.close()


def config():
    return {'enabled': True, 'model': 'test-model', 'api_key_variable': 'DQP_TEST_KEY',
            'base_url_variable': 'DQP_TEST_URL', 'temperature': 0, 'max_output_tokens': 100,
            'input_price_usd_per_million': 1, 'output_price_usd_per_million': 2,
            'max_calls': 1, 'max_spend_usd': 1}


def test_no_paid_calls_without_authorization(tmp_path):
    p = Provider(config(), tmp_path / 'ledger.sqlite')
    with pytest.raises(BlockedInference, match='authorization'):
        p.infer({'data_classification': 'public_unrestricted'})
    assert p.db.execute('SELECT count(*) FROM calls').fetchone()[0] == 0


def test_cache_and_spend_caps_use_mocked_inference_only(tmp_path, monkeypatch):
    monkeypatch.setenv('DQP_TEST_KEY', 'test-only-not-a-credential')
    monkeypatch.setenv('DQP_TEST_URL', 'https://example.invalid/v1')
    import httpx
    calls = []

    def fake_post(self, url, **kwargs):
        calls.append(url)
        return httpx.Response(200, request=httpx.Request('POST', url),
                              json={'model': 'test-model', 'usage': {'prompt_tokens': 10, 'completion_tokens': 10},
                                    'choices': [{'message': {'content': json.dumps({'rules': []})}}]})
    monkeypatch.setattr(httpx.Client, 'post', fake_post)
    p = Provider(config(), tmp_path / 'ledger.sqlite', True)
    context = {'data_classification': 'public_unrestricted', 'schema': {'a': 'numeric'}}
    first = p.infer(context)
    assert p.infer(context) == first
    assert len(calls) == 1
    with pytest.raises(BlockedInference, match='cap'):
        p.infer(dict(context, sample=[{'a': 1}]))
    assert len(calls) == 1
    with pytest.raises(BlockedInference):
        p.infer({'data_classification': 'restricted'})
    with pytest.raises(ValueError, match='Disallowed'):
        p.infer(dict(context, groundtruth='not allowed'))


def test_failed_call_not_retried_on_resume(tmp_path, monkeypatch):
    monkeypatch.setenv('DQP_TEST_KEY', 'test-only')
    monkeypatch.setenv('DQP_TEST_URL', 'https://example.invalid/v1')
    import httpx

    def fail(*args, **kwargs):
        raise httpx.ConnectError('Mock failure')
    monkeypatch.setattr(httpx.Client, 'post', fail)
    p = Provider(config(), tmp_path / 'ledger.sqlite', True)
    ctx = {'data_classification': 'public_unrestricted'}
    with pytest.raises(BlockedInference, match='failed'):
        p.infer(ctx)
    with pytest.raises(BlockedInference, match='Prior'):
        p.infer(ctx)
