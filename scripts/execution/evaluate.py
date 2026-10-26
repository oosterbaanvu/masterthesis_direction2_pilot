"""Freeze real candidates, then run development selection and held-out evaluation."""

import argparse
import json
from pathlib import Path

from dqpilot.common import save, digest, now, sha
from dqpilot_execution.data import load
from dqpilot_execution.evaluate import candidates, evaluate_source, published_cell_track

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--source", required=True)
parser.add_argument("--condition", choices=["guided", "original", "benchmark"], default="guided")
parser.add_argument("--output-dir", type=Path, help="Fresh isolated result directory for repeat scoring")
parser.add_argument(
    "--allow-partial",
    action="store_true",
    help="Explicitly labelled interim scoring into a separate directory only",
)
args = parser.parse_args()
folder = {"guided": "guided_generations", "original": "generations", "benchmark": "benchmark_generations"}[
    args.condition
]
records = [json.loads(p.read_text()) for p in (root / "results/execution" / folder).glob("*.json")]
request_count = sum(r["request"]["source"] == args.source for r in records)
expected = {"guided": 12, "original": 1, "benchmark": 2}[args.condition]
if request_count != expected and not (args.allow_partial and args.output_dir):
    raise ValueError(
        f"Candidate population incomplete: {request_count}/{expected}; partial runs require an explicit isolated output directory"
    )
output = args.output_dir.resolve() if args.output_dir else root / "results/execution"
out = output / f"evaluation/{args.condition}_{args.source}.json"
if out.exists():
    raise ValueError("Preserve completed evaluation; use a separately versioned condition")
all_rules, rules = candidates(root, args.source, args.condition)
data = load(root, args.source)
save(
    output / f"candidate_freezes/{args.condition}_{args.source}.json",
    {
        "time_utc": now(),
        "raw_candidate_count": len(all_rules),
        "unique_count": len(rules),
        "candidate_sha256": digest(rules),
        "candidates": rules,
        "protocol_sha256": sha(root / "config/execution/protocol.yaml"),
        "evaluation_implementation_sha256": sha(root / "src/dqpilot_execution/evaluate.py"),
        "data_implementation_sha256": sha(root / "src/dqpilot_execution/data.py"),
        "selection_uses_heldout_labels": False,
        "raw_records_or_error_labels_in_generation": False,
    },
)
result = evaluate_source(root, data, rules, args.condition, output)
result["generation_request_count"] = request_count
result["complete_candidate_population"] = request_count == expected
if data["kind"].startswith("CONDITIONAL"):
    result["published_single_column_cell_track"] = published_cell_track(
        root, data, rules, args.condition, output
    )
save(out, result)
print(
    args.source,
    "unique candidates",
    len(rules),
    "executed",
    sum(r.get("technical_pass", False) for r in result["technical_results"]),
)
