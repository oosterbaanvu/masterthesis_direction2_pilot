"""Integrate genuine proposals into the preserved service without inventing human approval."""

from pathlib import Path

from dqpilot.common import save
from dqpilot.service import Service
from dqpilot_execution.data import load
from dqpilot_execution.evaluate import candidates, native

root = Path(__file__).resolve().parents[2]
output = root / "results/execution/service_demo.json"
if output.exists():
    raise ValueError("Preserve completed demo; use a new run directory")
data = load(root, "synthetic_balanced_journals")
_, rules = candidates(root, "synthetic_balanced_journals", "guided")
db = root / "data/cache/execution/service_demo.sqlite"
if db.exists():
    raise ValueError("Do not overwrite an existing service database")
service = Service(db)
# These are existing stipulated conventional controls, not model rules or human judgments.
for control in data["strong_rules"]:
    service.propose(control, "journal_demo", "controlled_contract_operator")
    service.validate(control.id, data["dev"], "automated_technical_validation")
    service.transition(
        control.id,
        "APPROVED",
        "controlled_contract_operator",
        "Existing self-authored scenario contract, not independent model-rule review",
    )
    service.transition(
        control.id, "ACTIVE", "controlled_contract_operator", "Activate conventional scenario controls only"
    )
imported = []
unsupported = []
for generated in rules:
    try:
        converted = native(generated, list(data["dev"].columns))
    except (ValueError, KeyError, TypeError):
        converted = []
    if not converted:
        unsupported.append(generated["id"])
        continue
    for rule in converted:
        from dataclasses import replace

        proposal = replace(
            rule,
            id="model_" + rule.id,
            evidence="Actual locally generated candidate; independent semantic approval PENDING",
            origin="LLM",
        )
        try:
            service.propose(proposal, "journal_demo", "model_import_adapter")
            decision = service.validate(proposal.id, data["dev"], "automated_technical_validation")
            from dataclasses import asdict

            imported.append(
                {
                    "id": proposal.id,
                    "state": decision["state"],
                    "origin": "ACTUAL_MODEL_GENERATED",
                    "gx_candidate_id": generated["id"],
                    "gx_code": generated["gx_code"],
                    "native_proposal": asdict(proposal),
                }
            )
        except ValueError:
            unsupported.append(generated["id"])
first = service.scan("journal_demo", data["test"])
second = service.scan("journal_demo", data["test_cases"]["gross_scale"]["frame"])
states = dict(
    service.db.execute(
        "SELECT state,count(*) FROM rules WHERE specification LIKE ? GROUP BY state", ('%"origin": "LLM"%',)
    ).fetchall()
)
active_models = service.db.execute(
    "SELECT count(*) FROM rules WHERE state='ACTIVE' AND specification LIKE ?", ('%"origin": "LLM"%',)
).fetchone()[0]
events = service.db.execute("SELECT count(*) FROM events").fetchone()[0]
result = {
    "status": "FUNCTIONAL_PUBLIC_CONTROLLED_DEMONSTRATION",
    "real_generated_rules_imported": imported,
    "unsupported_native_service_mapping": unsupported,
    "model_states": states,
    "model_rules_active": active_models,
    "independent_human_approvals": 0,
    "clean_scenario_scan": first,
    "changed_scenario_scan": second,
    "events": events,
    "monitoring_records": len(service.monitoring("journal_demo")),
    "approval_interpretation": "Only conventional self-authored contract controls activated; actual model proposals remain gated.",
    "identity_limit": "Local actor strings are attribution, not enterprise authentication",
    "native_mapping_limit": "Native numeric/code normalization can differ from exact GX semantics under representation changes; original GX and mapped proposal retained, no generated proposal activated",
    "financial_scope": "Explicit per-journal same-currency integer-cent debit/credit equality; no universal table-total assumption",
    "preserved_SEC_financial_adapter": "src/dqpilot_final/financial.py; prior development proposals remain pending independent review",
}
service.close()
save(output, result)
print("Service demo completed; model rules active:", active_models)
