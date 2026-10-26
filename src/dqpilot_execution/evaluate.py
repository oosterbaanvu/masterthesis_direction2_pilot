"""Same-candidate A/B/C/D evaluation with development-only selection and explicit label roles."""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from dqpilot.common import digest, save, now
from dqpilot.evaluation import cells
from dqpilot.rules import Engine, Rule
from dqpilot.experiments import flags
from dqpilot_final.ledqer import load_component
from dqpilot_execution.safety import validate


def canonical(code):
    try:
        tree = ast.parse(code, mode="eval")
        if isinstance(tree.body, ast.Call):
            tree.body.keywords.sort(key=lambda x: x.arg or "")
        return digest(ast.dump(tree, include_attributes=False))
    except SyntaxError:
        return digest(code)


def candidates(root, source, condition="guided"):
    folders = {
        "guided": "guided_generations",
        "original": "generations",
        "benchmark": "benchmark_generations",
    }
    all_rules = []
    unique = {}
    for path in sorted((Path(root) / "results/execution" / folders[condition]).glob("*.json")):
        record = json.loads(path.read_text())
        if record["request"]["source"] != source:
            continue
        for rule in record["rules"]:
            key = canonical(rule["gx_code"])
            all_rules.append(dict(rule, request_id=record["request"]["id"]))
            if key not in unique:
                unique[key] = dict(rule, id="g_" + key[:20], original_id=rule["id"], origins=[])
            unique[key]["origins"].append(record["request"]["id"])
    return all_rules, list(unique.values())


def execute(root, frame, rules):
    root = Path(root)
    records = frame.astype(object).where(pd.notnull(frame), None).to_dict("records")
    key = digest(
        {"records": records, "columns": list(frame.columns), "rules": rules, "implementation": "strict_GX_v1"}
    )
    cache = root / "data/cache/execution/evaluation" / f"{key}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    payload = {
        "records": records,
        "columns": list(frame.columns),
        "candidates": rules,
        "original_evaluator": str(root / "data/vendor/ledqer/rule_eval/evaluate_rules.py"),
    }
    env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ["KEY", "TOKEN", "SECRET"])}
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    try:
        p = subprocess.run(
            [sys.executable, "-m", "dqpilot_execution.eval_worker"],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=90,
            cwd=root,
            env=env,
        )
        if p.returncode:
            results = [
                {
                    "id": r["id"],
                    "technical_pass": False,
                    "status": "RESOURCE_OR_WORKER_FAILURE",
                    "exit_code": p.returncode,
                }
                for r in rules
            ]
        else:
            results = json.loads(p.stdout)
    except subprocess.TimeoutExpired:
        results = [{"id": r["id"], "technical_pass": False, "status": "WALL_TIMEOUT"} for r in rules]
    save(cache, results)
    return results


def row_sets(results):
    return {r["id"]: set(r.get("unexpected_rows") or []) for r in results if r.get("technical_pass")}


def native(candidate, columns):
    name, k, _ = validate(candidate["gx_code"], columns)
    rid = candidate["id"]
    column = k.get("column")
    if name == "ExpectColumnValuesToNotBeNull":
        return [Rule(rid, "not_null", [column])]
    if name == "ExpectColumnValuesToBeUnique":
        return [Rule(rid, "unique", [column])]
    if name == "ExpectColumnValuesToBeInSet":
        return [Rule(rid, "allowed", [column], {"values": list(k["value_set"])})]
    if name == "ExpectColumnValuesToBeBetween" and not k.get("strict_min") and not k.get("strict_max"):
        p = {b: k[v] for b, v in [("min", "min_value"), ("max", "max_value")] if k.get(v) is not None}
        return [Rule(rid, "range", [column], p)]
    if name == "ExpectColumnPairValuesAToBeGreaterThanB" and k.get("or_equal"):
        return [Rule(rid, "less_equal", [k["column_B"], k["column_A"]], {"tolerance": 0})]
    if name == "ExpectColumnPairValuesToBeEqual":
        return [
            Rule(rid + "a", "less_equal", [k["column_A"], k["column_B"]], {"tolerance": 0}),
            Rule(rid + "b", "less_equal", [k["column_B"], k["column_A"]], {"tolerance": 0}),
        ]
    return []


def entails(known, proposal):
    if known.kind != proposal.kind or known.columns != proposal.columns:
        return False
    if known.kind == "range":
        return proposal.parameters.get("min", -float("inf")) <= known.parameters.get(
            "min", -float("inf")
        ) and proposal.parameters.get("max", float("inf")) >= known.parameters.get("max", float("inf"))
    if known.kind == "allowed":
        return set(map(str, known.parameters["values"])) <= set(map(str, proposal.parameters["values"]))
    return known.signature == proposal.signature


def evidence_select(data, rules, technical, unlabelled, formatted, baseline, max_fraction=0.01, docs=True):
    selected = []
    decisions = []
    known = [
        r
        for r in data["strong_rules"]
        if r.evidence.startswith("verified:") or data["source"] == "synthetic_balanced_journals"
    ]
    for r in rules:
        reason = "NO_DOCUMENTARY_CERTIFICATE"
        decision = "ABSTAIN"
        if r["id"] not in technical:
            decision, reason = "REJECT", "TECHNICAL_FAILURE_OR_UNSUPPORTED"
        else:
            try:
                proposals = native(r, list(data["dev"].columns))
            except (ValueError, KeyError, TypeError):
                proposals = []
            if proposals and all(any(entails(k, p) for k in baseline) for p in proposals):
                decision, reason = "REJECT", "LOGICALLY_REDUNDANT_WITH_INSTALLED_CONTROLS"
            elif docs and proposals and all(any(entails(k, p) for k in known) for p in proposals):
                alerts = unlabelled.get(r["id"], set())
                if len(alerts) / len(data["dev"]) > max_fraction:
                    decision, reason = "ABSTAIN", "UNLABELLED_WORKLOAD_THRESHOLD"
                elif alerts != formatted.get(r["id"], set()):
                    decision, reason = "ABSTAIN", "FORMATTING_SENSITIVITY"
                else:
                    decision, reason = (
                        "PROPOSE_FOR_REVIEW",
                        "INHERITED_DOCUMENTARY_ENTAILMENT_NOT_INDEPENDENT_VALIDITY",
                    )
        if decision == "PROPOSE_FOR_REVIEW":
            selected.append(r["id"])
        decisions.append(
            {
                "id": r["id"],
                "decision": decision,
                "reason": reason,
                "independent_semantic_validity": "NOT_ADJUDICATED",
            }
        )
    return selected, decisions


def baseline_rows(frame, rules):
    with Engine(frame) as engine:
        return {i for i, _ in flags(engine, rules)}


def union(predictions, ids):
    return set().union(*(predictions.get(i, set()) for i in ids)) if ids else set()


def cluster_interval(pred, gold, groups, seed=20261026):
    units = sorted(set(map(str, groups)))
    if len(units) < 10:
        return {"status": "WITHHELD_TOO_FEW_GROUPS", "groups": len(units)}
    by = {g: [i for i, v in enumerate(groups) if str(v) == g] for g in units}
    counts = np.array(
        [
            [len(set(by[g]) & pred & gold), len((set(by[g]) & pred) - gold), len((set(by[g]) & gold) - pred)]
            for g in units
        ]
    )
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(500):
        tp, fp, fn = counts[rng.integers(len(units), size=len(units))].sum(axis=0)
        values.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0)
    return {
        "groups": len(units),
        "f1_95pct_percentile": list(np.quantile(values, [0.025, 0.975])),
        "interpretation": "Conditional source/entity sampling uncertainty; fixed generated rules, not unseen-domain or generation uncertainty",
    }


def evaluate_source(root, data, rules, condition, output_root=None):
    root = Path(root)
    output_root = Path(output_root) if output_root is not None else root / "results/execution"
    source = data["source"]
    published = data["kind"].startswith("CONDITIONAL")
    dev_original = execute(root, data["dev"], rules)
    dev_original_flags = row_sets(dev_original)
    technical = {r["id"] for r in dev_original if r.get("technical_pass")}
    formatted = data["dev"].copy(deep=True)
    for c in formatted:
        formatted[c] = formatted[c].map(lambda v: " " + v + " " if isinstance(v, str) and v.strip() else v)
    format_flags = row_sets(execute(root, formatted, rules))
    dev_case_flags = {
        name: row_sets(execute(root, case["frame"], rules)) for name, case in data["dev_cases"].items()
    }
    original = load_component(
        root / "data/vendor/ledqer/rule_eval/rule_selection.py", "executed_original_greedy"
    )
    summaries = []
    for strength in ["weak", "strong"]:
        baseline = data[strength + "_rules"]
        # Label-assisted reference uses only development labels, never test rows.
        rows = []
        pairs = []
        for index, r in enumerate(rules):
            if r["id"] not in technical:
                rows.append({"ri": index, "precision": 0, "col_set": "ROW"})
                continue
            tp = fp = 0
            for family, case in data["dev_cases"].items():
                p = dev_case_flags[family].get(r["id"], set())
                if not published:
                    p = p - dev_original_flags.get(r["id"], set())
                tp += len(p & case["gold_rows"])
                fp += len(p - case["gold_rows"])
                pairs.extend(
                    {"ri": index, "pk": f"{family}:{i}", "col": "ROW", "isDirty": int(i in case["gold_rows"])}
                    for i in p
                )
            rows.append({"ri": index, "precision": tp / (tp + fp) if tp + fp else 0, "col_set": "ROW"})
        df_rules = pd.DataFrame(rows, columns=["ri", "precision", "col_set"])
        df_pairs = pd.DataFrame(pairs, columns=["ri", "pk", "col", "isDirty"])
        selected, _, _ = original.greedy_rule_selection_pairs(df_pairs, df_rules, 1.0)
        b = [rules[i]["id"] for i in selected]
        assert set(b) <= technical
        c, decisions = evidence_select(data, rules, technical, dev_original_flags, format_flags, baseline)
        arms = {"A": sorted(technical), "B": b, "C": c, "D": []}
        sensitivity = {}
        for threshold in [0.0, 0.01, 0.05]:
            sensitivity["C_" + str(threshold)] = evidence_select(
                data, rules, technical, dev_original_flags, format_flags, baseline, threshold
            )[0]
        low, _, _ = original.greedy_rule_selection_pairs(df_pairs, df_rules, 0.8)
        sensitivity["B_0.8"] = [rules[i]["id"] for i in low]
        sensitivity["C_no_extra_documentation"] = evidence_select(
            data, rules, technical, dev_original_flags, format_flags, baseline, docs=False
        )[0]
        freeze = {
            "source": source,
            "condition": condition,
            "baseline": strength,
            "arms": arms,
            "C_decisions": decisions,
            "sensitivity": sensitivity,
            "candidate_sha256": digest(rules),
            "time_utc": now(),
            "test_labels_used": False,
            "selection_information": {
                "A": "technical",
                "B": "development labels",
                "C": "inherited source contracts and unlabelled development only",
                "D": "fixed conventional suite",
            },
        }
        save(output_root / f"selections/{condition}_{source}_{strength}.json", freeze)
        summaries.append((strength, baseline, arms, decisions, sensitivity))
    # No held-out scoring happens before every selector/threshold above is frozen.
    test_original = row_sets(execute(root, data["test"], rules)) if not published else {}
    test_execution = {name: execute(root, case["frame"], rules) for name, case in data["test_cases"].items()}
    test_case_flags = {name: row_sets(results) for name, results in test_execution.items()}
    results = []
    for strength, baseline, arms, decisions, sensitivity in summaries:
        baseline_before = baseline_rows(data["test"], baseline) if not published else set()
        for family, case in data["test_cases"].items():
            bp = baseline_rows(case["frame"], baseline)
            predictions = test_case_flags[family]
            gold = case["gold_rows"]
            d = bp if published else bp - baseline_before
            available = union(predictions, arms["A"])
            deltas = {rid: p - test_original.get(rid, set()) for rid, p in predictions.items()}
            potential = (available if published else union(deltas, arms["A"])) - d
            for arm, chosen in {**arms, **sensitivity}.items():
                candidate_after = union(predictions, chosen)
                candidate_before = union(test_original, chosen) if not published else set()
                combined = (bp | candidate_after) if published else d | union(deltas, chosen)
                raw_combined = bp | candidate_after
                added = raw_combined - bp
                retained = added & gold
                raw_potential = available - bp
                results.append(
                    {
                        "source": source,
                        "condition": condition,
                        "baseline": strength,
                        "family": family,
                        "arm": arm,
                        "rows": len(case["frame"]),
                        "candidate_count": len(rules),
                        "accepted_count": len(chosen),
                        "label_interpretation": case.get("label_interpretation", data["kind"]),
                        "agreement": cells(raw_combined, gold),
                        "delta_agreement": cells(combined, gold),
                        "baseline_labelled_hits": len(bp & gold),
                        "incremental_labelled_hits": len(retained),
                        "new_alert_incremental_labelled_hits": len((combined - d) & gold),
                        "additional_off_label_rows": len(added - gold),
                        "potential_labelled_hits_lost": len((raw_potential & gold) - retained),
                        "new_alert_labelled_hits_lost": len((potential & gold) - ((combined - d) & gold)),
                        "marginal_label_agreement_precision": len(retained) / len(added) if added else None,
                        "additional_workload_rows": len(added),
                        "total_alert_rows": len(bp | candidate_after),
                        "unadjudicated_original_candidate_alert_rows": len(candidate_before),
                        "conditional_uncertainty": cluster_interval(combined, gold, case["groups"])
                        if published and arm in arms
                        else None,
                        "semantic_precision": "NOT_MEASURED",
                        "invalid_rule_promotion": "NOT_ADJUDICATED",
                    }
                )
    return {
        "source": source,
        "condition": condition,
        "label_population": data["kind"],
        "dev_rows": len(data["dev"]),
        "test_rows": len(data["test"]),
        "test_groups": len(set(map(str, data["test_groups"]))),
        "input_hashes": data["input_hashes"],
        "split_hash": data.get("split_hash"),
        "group_overlap": data["group_overlap"],
        "technical_results": dev_original,
        "heldout_execution_results": test_execution,
        "candidate_count": len(rules),
        "results": results,
        "note": data["note"],
    }


def cell_sets(results):
    return {
        r["id"]: {(i, r["columns"][0]) for i in r.get("unexpected_rows") or []}
        for r in results
        if r.get("technical_pass") and len(r.get("columns", [])) == 1
    }


def published_cell_track(root, data, rules, condition, output_root=None):
    """Faithful original pair-coverage selection on single-column model candidates only."""
    root = Path(root)
    output_root = Path(output_root) if output_root is not None else root / "results/execution"
    dev_results = execute(root, data["dev"], rules)
    dev = cell_sets(dev_results)
    eligible = [r for r in rules if r["id"] in dev]
    dev_gold = data["dev_cases"]["reference"]["gold_cells"]
    original = load_component(
        root / "data/vendor/ledqer/rule_eval/rule_selection.py", "published_original_pair_greedy"
    )
    rules_df = []
    pairs = []
    for ri, r in enumerate(eligible):
        predicted = dev[r["id"]]
        rules_df.append(
            {
                "ri": ri,
                "precision": len(predicted & dev_gold) / len(predicted) if predicted else 0,
                "col_set": "CELL",
            }
        )
        pairs.extend({"ri": ri, "pk": i, "col": c, "isDirty": int((i, c) in dev_gold)} for i, c in predicted)
    selected, _, _ = original.greedy_rule_selection_pairs(
        pd.DataFrame(pairs, columns=["ri", "pk", "col", "isDirty"]),
        pd.DataFrame(rules_df, columns=["ri", "precision", "col_set"]),
        1.0,
    )
    b = [eligible[i]["id"] for i in selected]
    technical = set(dev)
    formatted = data["dev"].copy()
    for col in formatted:
        formatted[col] = formatted[col].map(
            lambda v: " " + v + " " if isinstance(v, str) and v.strip() else v
        )
    fm = row_sets(execute(root, formatted, rules))
    unlabelled = row_sets(dev_results)
    methods = []
    for strength in ["weak", "strong"]:
        baseline = data[strength + "_rules"]
        c, decisions = evidence_select(data, eligible, technical, unlabelled, fm, baseline)
        arms = {"A": list(technical), "B": b, "C": c, "D": []}
        save(
            output_root / f"selections/{condition}_{data['source']}_{strength}_cells.json",
            {
                "arms": arms,
                "candidate_sha256": digest(eligible),
                "label_access": "B development cells only",
                "test_labels_used": False,
                "C_decisions": decisions,
                "unit": "single-column predicted cells",
                "excluded_multicolumn_or_unsupported_candidates": len(rules) - len(eligible),
            },
        )
        methods.append((strength, baseline, arms))
    test = cell_sets(execute(root, data["test"], rules))
    gold = data["test_cases"]["reference"]["gold_cells"]
    output = []
    for strength, baseline, arms in methods:
        with Engine(data["test"]) as engine:
            d = flags(engine, baseline)
        available = union(test, arms["A"]) - d
        for arm, chosen in arms.items():
            p = d | union(test, chosen)
            extra = p - d
            output.append(
                {
                    "source": data["source"],
                    "condition": condition,
                    "baseline": strength,
                    "arm": arm,
                    "unit": "single-column cells",
                    "candidate_coverage": len(eligible),
                    "all_unique_candidates": len(rules),
                    "agreement": cells(p, gold),
                    "baseline_labelled_hits": len(d & gold),
                    "incremental_labelled_hits": len(extra & gold),
                    "additional_off_reference_cells": len(extra - gold),
                    "additional_workload_cells": len(extra),
                    "potential_labelled_hits_lost": len((available & gold) - extra),
                    "label_interpretation": "CONDITIONAL_PUBLISHED_REFERENCE_DISCREPANCY_AGREEMENT",
                    "semantic_precision": "NOT_ADJUDICATED",
                    "test_rows": len(data["test"]),
                    "test_groups": len(set(data["test_groups"])),
                    "cluster_uncertainty": cell_cluster_interval(p, d, gold, data["test_groups"]),
                }
            )
    return output


def cell_cluster_interval(pred, baseline, gold, groups):
    units = sorted(set(map(str, groups)))
    if len(units) < 10:
        return {"status": "WITHHELD_TOO_FEW_ENTITY_GROUPS", "groups": len(units)}
    counts = []
    for g in units:
        rows = {i for i, v in enumerate(groups) if str(v) == g}
        pg = {v for v in pred if v[0] in rows}
        bg = {v for v in baseline if v[0] in rows}
        gg = {v for v in gold if v[0] in rows}
        counts.append([len(pg & gg), len(pg - gg), len(gg - pg), len(bg & gg), len(gg)])
    counts = np.array(counts)
    rng = np.random.default_rng(20261026)
    f1 = []
    delta = []
    for _ in range(500):
        tp, fp, fn, btp, ng = counts[rng.integers(len(units), size=len(units))].sum(axis=0)
        f1.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0)
        delta.append((tp - btp) / ng if ng else 0)
    return {
        "groups": len(units),
        "reference_F1_95pct": list(np.quantile(f1, [0.025, 0.975])),
        "paired_incremental_reference_recall_95pct": list(np.quantile(delta, [0.025, 0.975])),
        "interpretation": "Fixed-model conditional entity-group bootstrap, not independent source/generalization uncertainty",
    }
