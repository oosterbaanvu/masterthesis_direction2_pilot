"""Verify additive scientific artifacts and their parent freezes, without inference."""

import json
from pathlib import Path
import subprocess
import sys

from dqpilot.common import sha, digest

root = Path(__file__).resolve().parents[2]
manifest = json.loads((root / "results/execution/artifact_freeze.json").read_text())
for relative, expected in manifest["files"].items():
    path = root / relative
    if not path.is_file() or sha(path) != expected:
        raise AssertionError("Frozen execution artifact changed: " + relative)
summary = json.loads((root / "results/execution/summary.json").read_text())
assert summary["actual_completed_requests"] == 56
assert summary["request_conditions"] == {"original": 4, "guided": 48, "benchmark": 4}
assert summary["paid_calls"] == 0
assert summary["human_reviews_completed"] == 0
inventory = json.loads((root / "results/execution/response_inventory.json").read_text())
assert inventory["actual_completed_generation_requests"] == 56
assert len({item["request_cache_key"] for item in inventory["files"]}) == 56
for item in inventory["files"]:
    assert sha(root / item["path"]) == item["response_wire_sha256"]
    assert digest(json.loads((root / item["request_path"]).read_text())) == item["request_canonical_sha256"]
for item in json.loads((root / "results/execution/actual_prompt_inventory.json").read_text())["prompts"]:
    assert sha(root / item["path"]) == item["sha256"]
generation_records = [
    json.loads(p.read_text())
    for folder in ["generations", "guided_generations", "benchmark_generations"]
    for p in (root / "results/execution" / folder).glob("*.json")
]
assert len(generation_records) == 56
assert {r["provenance"]["response_wire_sha256"] for r in generation_records} == {
    item["response_wire_sha256"] for item in inventory["files"]
}
assert sum(len(r["rules"]) for r in generation_records) == summary["candidate_occurrences"]
evaluations = list((root / "results/execution/evaluation").glob("*.json"))
assert len(evaluations) == 10
for path in evaluations:
    result = json.loads(path.read_text())
    folder = {
        "guided": "guided_generations",
        "original": "generations",
        "benchmark": "benchmark_generations",
    }[result["condition"]]
    count = sum(
        json.loads(p.read_text())["request"]["source"] == result["source"]
        for p in (root / "results/execution" / folder).glob("*.json")
    )
    assert count == {"guided": 12, "original": 1, "benchmark": 2}[result["condition"]]
    if "complete_candidate_population" in result:
        assert result["complete_candidate_population"] is True
    assert result["group_overlap"] == 0
    assert result["candidate_count"] == len(result["technical_results"])
assert json.loads((root / "results/execution/service_demo.json").read_text())["model_rules_active"] == 0
supplement = json.loads((root / "results/execution/service_schema_guard_supplement.json").read_text())
assert supplement["model_rules_active"] == 0
assert supplement["principal_A_B_C_D_results_modified"] is False
subprocess.run([sys.executable, "scripts/free_gemini/verify.py"], cwd=root, check=True)
print(
    "Execution freeze verified:",
    len(manifest["files"]),
    "files; 56 genuine outputs; ten evaluations; parent phases preserved.",
)
