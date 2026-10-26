import json

import httpx
import pytest

from dqpilot_execution.providers import LocalProvider
from dqpilot_execution.evaluate import cell_cluster_interval


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.openai.com",
        "http://example.com",
        "http://localhost:11435",
        "http://key:secret@127.0.0.1:11435",
    ],
)
def test_nonlocal_or_credentialed_endpoints_are_rejected(tmp_path, endpoint):
    with pytest.raises(ValueError):
        LocalProvider(tmp_path, endpoint=endpoint)


def test_successful_local_response_is_not_generated_again(tmp_path):
    (tmp_path / "results/execution").mkdir(parents=True)
    (tmp_path / "data/cache/execution").mkdir(parents=True)
    (tmp_path / "results/execution/local_model.json").write_text(
        json.dumps(
            {
                "weights_sha256": "SOFTWARE_FIXTURE",
                "weights_revision": "SOFTWARE_FIXTURE",
                "runtime_commit": "SOFTWARE_FIXTURE",
                "model_alias": "fixture",
                "base_model": "SOFTWARE_FIXTURE_NOT_RESEARCH",
                "quantization": "FIXTURE",
                "server_pid": 0,
            }
        )
    )
    calls = []

    def handle(request):
        calls.append(request)
        assert request.url.host == "127.0.0.1"
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": "stop", "message": {"content": '{"rules":[]}'}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )

    provider = LocalProvider(tmp_path, transport=httpx.MockTransport(handle))
    one, meta, cached = provider.generate("SOFTWARE_FIXTURE", 11)
    assert not cached and meta["model"] == "SOFTWARE_FIXTURE_NOT_RESEARCH"
    two, _, cached = provider.generate("SOFTWARE_FIXTURE", 11)
    assert cached and one == two and len(calls) == 1
    provider.close()


def test_published_intervals_are_not_reported_for_seven_groups():
    result = cell_cluster_interval({(0, "x")}, set(), {(0, "x")}, list(range(7)))
    assert result["status"] == "WITHHELD_TOO_FEW_ENTITY_GROUPS"


def test_paired_incremental_interval_uses_identical_entity_resamples():
    gold = {(i, "x") for i in range(20)}
    result = cell_cluster_interval(gold, gold, gold, list(range(20)))
    assert result["paired_incremental_reference_recall_95pct"] == [0.0, 0.0]
