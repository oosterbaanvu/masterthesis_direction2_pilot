"""Exercise the unchanged paper scorer on actual generated-rule detections."""

import json
from pathlib import Path

from dqpilot.common import save
from dqpilot.evaluation import cells
from dqpilot_execution.data import load
from dqpilot_execution.evaluate import candidates, execute, cell_sets
from dqpilot_final.ledqer import load_component

root = Path(__file__).resolve().parents[2]
original = load_component(
    root / "data/vendor/ledqer/rule_eval/evaluate_rules.py", "original_actual_candidate_scorer"
)
checks = []
paths = sorted((root / "results/execution/evaluation").glob("*.json"))
if len(paths) != 10:
    raise ValueError("All ten frozen evaluations are required before final component comparison")
for path in paths:
    result = json.loads(path.read_text())
    data = load(root, result["source"])
    _, proposals = candidates(root, result["source"], result["condition"])
    for family, case in data["test_cases"].items():
        outputs = execute(root, case["frame"], proposals)
        cell_predictions = cell_sets(outputs)
        for output in outputs:
            if not output.get("technical_pass"):
                continue
            units = [("row", set(output.get("unexpected_rows") or []), case["gold_rows"])]
            if output["id"] in cell_predictions:
                units.append(("single_column_cell", cell_predictions[output["id"]], case["gold_cells"]))
            for unit, predicted, gold in units:
                paper = original.calculate_precision_recall(list(gold), list(predicted))
                independent = cells(predicted, gold)
                assert [paper[k] for k in ["TP", "FP", "FN", "precision", "recall"]] == [
                    independent[k] for k in ["tp", "fp", "fn", "precision", "recall"]
                ]
                checks.append(
                    {
                        "source": result["source"],
                        "condition": result["condition"],
                        "family": family,
                        "candidate": output["id"],
                        "unit": unit,
                        "counts_and_precision_recall_match": True,
                    }
                )
save(
    root / "results/execution/original_scorer_actual_candidates.json",
    {
        "status": "UNCHANGED_ORIGINAL_SCORER_COMPONENT_REPRODUCED_ON_ACTUAL_MODEL_DETECTIONS",
        "checks": checks,
        "count": len(checks),
        "new_model_requests": 0,
        "full_paper_performance_reproduction": False,
    },
)
print("Original scorer agrees with independent counts for", len(checks), "actual-candidate comparisons.")
