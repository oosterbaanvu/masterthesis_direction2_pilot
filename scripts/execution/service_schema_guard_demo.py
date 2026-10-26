"""Post-experiment engineering correction; never replace the frozen principal baseline."""

from pathlib import Path

from dqpilot.common import save
from dqpilot.rules import Rule
from dqpilot.service import Service
from dqpilot_execution.data import load

root = Path(__file__).resolve().parents[2]
target = root / "results/execution/service_schema_guard_supplement.json"
if target.exists():
    raise ValueError("Preserve completed engineering supplement")
data = load(root, "synthetic_balanced_journals")
service = Service(root / "data/cache/execution/service_demo.sqlite")
for column in ["total_debits", "total_credits"]:
    rule = Rule(
        "schema_numeric:" + column,
        "numeric",
        [column],
        evidence="Self-authored scenario schema states numeric integer cents; explicit numeric guard needed because range/equality skip nonnumeric inputs",
    )
    service.propose(rule, "journal_demo", "controlled_schema_operator")
    service.validate(rule.id, data["dev"], "automated_technical_validation")
    service.transition(
        rule.id,
        "APPROVED",
        "controlled_schema_operator",
        "Conventional stipulated numeric schema guard; not model semantic approval",
    )
    service.transition(
        rule.id,
        "ACTIVE",
        "controlled_schema_operator",
        "Engineering guard added after primary exploratory results; do not overwrite principal comparison",
    )
case = data["test_cases"]["invalid_type_or_code"]
scan = service.scan("journal_demo", case["frame"])
predicted = {
    row[0] for row in service.db.execute("SELECT row_idx FROM findings WHERE batch=?", (scan["batch"],))
}
active_models = service.db.execute(
    "SELECT count(*) FROM rules WHERE state='ACTIVE' AND specification LIKE ?", ('%"origin": "LLM"%',)
).fetchone()[0]
assert len(predicted & case["gold_rows"]) == len(case["gold_rows"]) == 24
assert active_models == 0
save(
    target,
    {
        "status": "POST_EXPERIMENT_ENGINEERING_SCHEMA_CORRECTION",
        "principal_A_B_C_D_results_modified": False,
        "reason": "Principal journal strong suite omitted explicit numeric checks; native ranges/equalities skip nonnumeric strings. Initial schema already specified numeric amounts, but this correction was made after observing exploratory outputs.",
        "added_conventional_numeric_guards": 2,
        "scan": scan,
        "controlled_labelled_rows_detected": len(predicted & case["gold_rows"]),
        "controlled_labelled_rows": len(case["gold_rows"]),
        "off_scenario_labelled_rows": len(predicted - case["gold_rows"]),
        "model_rules_active": active_models,
        "human_model_approvals": 0,
        "interpretation": "Functional self-authored scenario only; post hoc engineering correction, not confirmatory detection improvement or model benefit",
    },
)
service.close()
print("Engineering schema guard supplement: 24/24 stipulated invalid rows flagged; no model rule active.")
