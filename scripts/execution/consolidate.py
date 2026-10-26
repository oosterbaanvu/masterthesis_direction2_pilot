"""Build descriptive tables and figures from actual saved experiments; no new inference."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import shutil
import statistics
from hashlib import sha256

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dqpilot.common import save, sha, digest
from dqpilot_execution.evaluate import candidates

root = Path(__file__).resolve().parents[2]
base = root / "results/execution"
conditions = {"original": "generations", "guided": "guided_generations", "benchmark": "benchmark_generations"}
records = []
for condition, folder in conditions.items():
    for path in sorted((base / folder).glob("*.json")):
        record = json.loads(path.read_text())
        record["condition"] = condition
        records.append(record)
counts = Counter(r["condition"] for r in records)
if counts != {"original": 4, "guided": 48, "benchmark": 4}:
    raise ValueError("Complete genuine generation population required: " + str(counts))
wire_by_hash = {
    sha256(p.read_bytes()).hexdigest(): p for p in (root / "data/cache/execution/responses").glob("*.json")
}
raw_diagnostics = []
for record in records:
    wire = json.loads(wire_by_hash[record["provenance"]["response_wire_sha256"]].read_text())
    text = wire["choices"][0]["message"]["content"]
    try:
        body = json.loads(text)
        emitted = body.get("rules", [])
        if not isinstance(emitted, list):
            emitted = []
        ids = [r.get("id") for r in emitted if isinstance(r, dict)]
        reason = "DUPLICATE_RULE_IDS" if len(set(ids)) < len(ids) else "BUNDLE_OR_SCHEMA_FAILURE"
    except (ValueError, AttributeError, TypeError):
        emitted, reason = [], "INVALID_JSON_OR_CONTAINER"
    raw_diagnostics.append(
        {
            "condition": record["condition"],
            "request_id": record["request"]["id"],
            "raw_declared_rule_objects": len(emitted),
            "parsed_accepted_rules": len(record["rules"]),
            "bundle_status": record["status"],
            "failure_diagnostic": reason if record["status"] != "PARSED" else None,
            "raw_rule_objects_are_not_salvaged_into_selection": True,
        }
    )
evaluations = [json.loads(p.read_text()) for p in sorted((base / "evaluation").glob("*.json"))]
lookup = {(e["condition"], e["source"]): e for e in evaluations}
execution_health = []
for evaluation in evaluations:
    stages = {"unmodified_development": evaluation["technical_results"]}
    stages.update(evaluation.get("heldout_execution_results", {}))
    for stage, outcomes in stages.items():
        counts_by_status = Counter(r["status"] for r in outcomes)
        execution_health.append(
            {
                "condition": evaluation["condition"],
                "source": evaluation["source"],
                "stage": stage,
                "candidates": len(outcomes),
                "executed": sum(r.get("technical_pass", False) for r in outcomes),
                "status_counts": json.dumps(dict(counts_by_status), sort_keys=True),
            }
        )
rows = []
review = []
for condition, source in sorted({(r["condition"], r["request"]["source"]) for r in records}):
    matched = [r for r in records if r["condition"] == condition and r["request"]["source"] == source]
    raw, unique = candidates(root, source, condition)
    context_record = next(
        r
        for r in matched
        if r["request"]["documentation"] == "provided"
        and r["request"].get("prompt_variant", "direct") == "direct"
    )
    context_text = (root / context_record["request"]["path"]).read_text().split("SOURCE_CONTEXT:\n", 1)[1]
    context, _ = json.JSONDecoder().raw_decode(context_text)
    context_path = base / "review_source_contexts" / (source + ".json")
    if context_path.exists() and json.loads(context_path.read_text()) != context:
        raise ValueError("Source review context differs between conditions")
    save(context_path, context)
    evaluation = lookup[condition, source]
    statuses = {r["id"]: r for r in evaluation["technical_results"]}
    executable = sum(r.get("technical_pass", False) for r in statuses.values())
    executable_occurrences = sum(len(r["origins"]) for r in unique if statuses[r["id"]].get("technical_pass"))
    rows.append(
        {
            "condition": condition,
            "source": source,
            "requests": len(matched),
            "parsed_responses": sum(r["status"] == "PARSED" for r in matched),
            "candidate_occurrences": len(raw),
            "unique_candidates": len(unique),
            "duplicate_occurrences": len(raw) - len(unique),
            "executable_unique": executable,
            "executable_occurrences": executable_occurrences,
            "unique_execution_rate": executable / len(unique) if unique else None,
            "technical_status_counts": dict(Counter(r["status"] for r in statuses.values())),
        }
    )
    for r in unique:
        review.append(
            {
                "review_id": digest([source, r["gx_code"]])[:20],
                "source": source,
                "description": r["description"],
                "gx_code": r["gx_code"],
                "source_context": f"review_source_contexts/{source}.json",
                "validity": "",
                "applicability": "",
                "source_citation": "",
                "rationale": "",
                "reviewer": "",
            }
        )


def write_csv(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in values for key in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            {k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()}
            for row in values
        )


write_csv(base / "tables/generation_yield.csv", rows)
write_csv(base / "tables/execution_by_family.csv", execution_health)
scenario = lookup["guided", "synthetic_balanced_journals"]
save(
    base / "scenario_contract_diagnostics.json",
    {
        "source": "synthetic_balanced_journals",
        "evidence_type": "SELF_AUTHORED_STIPULATED_VALID_EXAMPLE_COUNTEREXAMPLES_NOT_HUMAN_ADJUDICATION",
        "rows": scenario["dev_rows"],
        "technical_passes_flagging_stipulated_valid_rows": [
            {"id": r["id"], "valid_scenario_rows_flagged": len(r.get("unexpected_rows") or [])}
            for r in scenario["technical_results"]
            if r.get("technical_pass") and r.get("unexpected_rows")
        ],
        "interpretation": "A flag on a stipulated valid scenario supplies a counterexample to universality within that scenario. Zero flags do not certify universal validity or financial transfer.",
    },
)
# Keep a separate copy for each reviewer; no fabricated human judgments.
review = list({r["review_id"]: r for r in review}.values())
for reviewer in ["reviewer_A", "reviewer_B"]:
    write_csv(base / f"{reviewer}_pending.csv", review)
strata = []
for condition, source, docs, variant in sorted(
    {
        (
            r["condition"],
            r["request"]["source"],
            r["request"]["documentation"],
            r["request"].get("prompt_variant", "direct"),
        )
        for r in records
    }
):
    matched = [
        r
        for r in records
        if (
            r["condition"],
            r["request"]["source"],
            r["request"]["documentation"],
            r["request"].get("prompt_variant", "direct"),
        )
        == (condition, source, docs, variant)
    ]
    _, unique = candidates(root, source, condition)
    status = {r["id"]: r.get("technical_pass", False) for r in lookup[condition, source]["technical_results"]}
    origin_to_status = defaultdict(list)
    for rule in unique:
        for origin in rule["origins"]:
            origin_to_status[origin].append(status[rule["id"]])
    flags = [v for r in matched for v in origin_to_status[r["request"]["id"]]]
    signatures = [digest(sorted(x["gx_code"] for x in r["rules"])) for r in matched]
    strata.append(
        {
            "condition": condition,
            "source": source,
            "documentation": docs,
            "prompt_variant": variant,
            "requests": len(matched),
            "parsed": sum(r["status"] == "PARSED" for r in matched),
            "candidate_occurrences": len(flags),
            "executable_occurrences": sum(flags),
            "distinct_response_rule_sets": len(set(signatures)),
        }
    )
write_csv(base / "tables/prompt_strata.csv", strata)
primary_rows = []
cells = []
for e in evaluations:
    for r in e["results"]:
        primary_rows.append(
            {k: v for k, v in r.items() if not isinstance(v, (dict, list))}
            | {
                "tp": r["agreement"]["tp"],
                "fp": r["agreement"]["fp"],
                "fn": r["agreement"]["fn"],
                "precision": r["agreement"]["precision"],
                "recall": r["agreement"]["recall"],
                "f1": r["agreement"]["f1"],
            }
        )
    for r in e.get("published_single_column_cell_track", []):
        cells.append({k: v for k, v in r.items() if not isinstance(v, (dict, list))} | r["agreement"])
write_csv(base / "tables/row_results.csv", primary_rows)
write_csv(base / "tables/published_cell_results.csv", cells)
# Export the precise prompts actually used, preserving originals and separate adaptation.
prompts = []
for r in records:
    p = root / r["request"]["path"]
    if sha(p) != r["request"]["prompt_sha256"]:
        raise ValueError("Prompt changed after generation")
    destination = base / "prompts" / r["condition"] / (r["request"]["id"].replace(":", "_") + ".txt")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.read_bytes() != p.read_bytes():
        raise ValueError("Committed prompt overwrite refused")
    shutil.copyfile(p, destination)
    prompts.append(
        {
            "condition": r["condition"],
            "request_id": r["request"]["id"],
            "path": destination.relative_to(root).as_posix(),
            "sha256": sha(destination),
        }
    )
save(base / "actual_prompt_inventory.json", {"prompts": prompts, "source_records_included": False})
save(
    base / "response_parsing_diagnostics.json",
    {
        "responses": raw_diagnostics,
        "raw_declared_rule_objects": sum(d["raw_declared_rule_objects"] for d in raw_diagnostics),
        "strict_all_or_nothing_bundle_parser": True,
    },
)
usage = Counter()
for r in records:
    u = r["provenance"]["usage"]
    usage.update({k: u.get(k, 0) or 0 for k in ["prompt_tokens", "completion_tokens", "total_tokens"]})
summary = {
    "actual_completed_requests": len(records),
    "raw_declared_rule_objects": sum(d["raw_declared_rule_objects"] for d in raw_diagnostics),
    "request_conditions": dict(counts),
    "candidate_occurrences": sum(r["candidate_occurrences"] for r in rows),
    "unique_candidates_within_source_and_condition": sum(r["unique_candidates"] for r in rows),
    "executable_unique_within_source_and_condition": sum(r["executable_unique"] for r in rows),
    "executable_occurrences": sum(r["executable_occurrences"] for r in rows),
    "parsed_responses": sum(r["status"] == "PARSED" for r in records),
    "legitimate_empty_parsed_responses": sum(r["status"] == "PARSED" and not r["rules"] for r in records),
    "response_failures": [
        {
            "id": r["request"]["id"],
            "condition": r["condition"],
            "status": r["status"],
            "finish": r["provenance"]["finish_reason"],
        }
        for r in records
        if r["status"] != "PARSED"
    ],
    "usage": dict(usage),
    "paid_calls": 0,
    "api_inference_cost_USD": 0,
    "infrastructure_and_labor_cost": "NOT_ESTIMATED",
    "human_reviews_completed": 0,
    "timing": {
        "median_wall_seconds": statistics.median(r["provenance"]["runtime_seconds"] for r in records),
        "sum_wall_seconds_including_queueing": sum(r["provenance"]["runtime_seconds"] for r in records),
        "median_prompt_tokens_per_second": statistics.median(
            r["provenance"]["timings"]["prompt_per_second"] for r in records
        ),
        "median_generation_tokens_per_second": statistics.median(
            r["provenance"]["timings"]["predicted_per_second"] for r in records
        ),
        "peak_observed_server_RSS_bytes": max(r["provenance"]["peak_server_tree_RSS_bytes"] for r in records),
        "missing_RSS_instrumentation_count": sum(
            r["provenance"]["peak_server_tree_RSS_bytes"] == 0 for r in records
        ),
    },
    "generation_yield": rows,
    "reviewable_unique_source_code_pairs": len(review),
    "interpretation": "Exploratory fixed-model study. Candidate uniqueness is within source/condition, not independent source replication; same rules can occur across conditions.",
}
save(base / "summary.json", summary)
plt.rcParams.update({"svg.hashsalt": "dqpilot_execution_v1", "font.size": 10})
figure_dir = root / "reports/execution/figures"
figure_dir.mkdir(parents=True, exist_ok=True)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
for ax, source in zip(axes, ["raha_hospital", "raha_beers"]):
    values = [r for r in cells if r["source"] == source and r["baseline"] == "strong"]
    by = {r["arm"]: r for r in values}
    order = ["A", "B", "C", "D"]
    positions = list(range(4))
    ax.bar(positions, [by[a]["tp"] for a in order], label="Reference hits")
    ax.bar(
        positions,
        [by[a]["fp"] for a in order],
        bottom=[by[a]["tp"] for a in order],
        label="Off-reference alerts",
        color="#d68c45",
    )
    ax.set_xticks(positions, order)
    ax.set_title(source.replace("raha_", "").title())
    ax.set_ylabel("Flagged single-column cells")
axes[0].legend()
fig.suptitle("Held-out reference agreement; fixed missing/type screens included")
fig.tight_layout()
fig.savefig(figure_dir / "published_reference_burden.svg", metadata={"Date": None})
fig.savefig(figure_dir / "published_reference_burden.png", dpi=180)
plt.close(fig)
fig, ax = plt.subplots(figsize=(9, 4))
guided = [r for r in rows if r["condition"] == "guided"]
labels = [r["source"].replace("uci_", "").replace("synthetic_balanced_journals", "journals") for r in guided]
ax.bar(labels, [r["unique_candidates"] for r in guided], label="Unique proposals", color="#d68c45")
ax.bar(labels, [r["executable_unique"] for r in guided], label="Executable unique", color="#3478a3")
ax.set_ylabel("Candidate count")
ax.set_title("Real Qwen outputs: technical execution does not adjudicate meaning")
ax.legend()
fig.tight_layout()
fig.savefig(figure_dir / "generation_yield.svg", metadata={"Date": None})
fig.savefig(figure_dir / "generation_yield.png", dpi=180)
plt.close(fig)
print(json.dumps({k: v for k, v in summary.items() if k not in {"generation_yield"}}, indent=2))
