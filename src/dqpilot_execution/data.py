"""Frozen source/group splits and separately labelled controlled/reference populations."""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from dqpilot.acquisition import load_table
from dqpilot.common import digest, partition, sha
from dqpilot.experiments import contract_rules, historical_rules, normalized_pair
from dqpilot.rules import Rule


def inject(frame, columns, numeric, seed):
    cases = {}
    for fi, family in enumerate(["missing", "invalid_type_or_code", "gross_scale", "plausible_swap"]):
        dirty = frame.copy(deep=True).astype(object)
        rng = np.random.default_rng(seed + fi)
        eligible = numeric if family == "gross_scale" else columns
        indices = rng.choice(len(frame), min(24, len(frame)), replace=False)
        gold = set()
        gold_cells = set()
        for j, i in enumerate(indices):
            col = eligible[j % len(eligible)]
            old = frame.at[int(i), col]
            if family == "missing":
                value = None
            elif family == "invalid_type_or_code":
                value = "NOT_A_NUMBER" if col in numeric else "__INVALID_CODE__"
            elif family == "gross_scale":
                try:
                    value = float(old) * 10
                except (ValueError, TypeError):
                    continue
            else:
                choices = frame.loc[frame[col].astype(str) != str(old), col]
                if choices.empty:
                    continue
                value = choices.iloc[int(rng.integers(len(choices)))]
            if str(old) != str(value):
                dirty.at[int(i), col] = value
                gold.add(int(i))
                gold_cells.add((int(i), col))
        label = (
            "CONTROLLED_TYPE_OR_DOMAIN_VIOLATION"
            if family == "invalid_type_or_code"
            else "CONTROLLED_DELETION"
            if family == "missing"
            else "ALTERATION_RECOVERY_NOT_INDEPENDENTLY_VERIFIED_DQ_ERROR"
        )
        cases[family] = {
            "frame": dirty,
            "gold_rows": gold,
            "gold_cells": gold_cells,
            "groups": list(range(len(frame))),
            "label_interpretation": label,
        }
    return cases


def load(root, source):
    root = Path(root)
    registry = yaml.safe_load((root / "config/datasets.yaml").read_text())["datasets"]
    cfg = yaml.safe_load((root / "config/pilot.yaml").read_text())
    if source.startswith("uci_"):
        frame = load_table(root, source, registry[source])
        full, omitted, contract = contract_rules(root, source)
        frame = frame.drop(columns=list(contract.get("excluded_columns", {}))).astype(object)
        features = [c for c in frame if c != contract.get("row_id")]
        hashes = [digest([str(v) for v in row]) for row in frame[features].itertuples(index=False, name=None)]
        splits = [partition(g, "uci-pilot2-11") for g in hashes]
        chosen = {}
        for split in ["development", "exploratory"]:
            ids = sorted([i for i, s in enumerate(splits) if s == split], key=lambda i: hashes[i])[:512]
            chosen[split] = (frame.iloc[ids].reset_index(drop=True), [hashes[i] for i in ids])
        dev, dg = chosen["development"]
        test, tg = chosen["exploratory"]
        assert not set(dg) & set(tg)
        numeric = [c["name"] for c in contract["columns"] if c["type"] == "numeric"]
        weak = [r for r in full if r.kind in {"not_null", "numeric"}]
        full += historical_rules(dev, numeric)
        targets = cfg["regular_numeric_columns"][source] + cfg["regular_categorical_columns"][source]
        devcases = inject(dev, targets, [c for c in targets if c in numeric], 20261026)
        testcases = inject(test, targets, [c for c in targets if c in numeric], 20262026)
        for case in devcases.values():
            case["groups"] = dg
        for case in testcases.values():
            case["groups"] = tg
        inputs = [p for p in (root / "data/raw" / source).iterdir() if p.is_file()]
        return {
            "source": source,
            "kind": "CONTROLLED_INJECTION_RELATIVE",
            "dev": dev,
            "test": test,
            "dev_cases": devcases,
            "test_cases": testcases,
            "dev_groups": dg,
            "test_groups": tg,
            "weak_rules": weak,
            "strong_rules": full,
            "contract": contract,
            "omitted_controls": omitted,
            "input_hashes": {p.name: sha(p) for p in inputs},
            "split_hash": digest(splits),
            "group_overlap": 0,
            "note": "Mixed-type object-cell representation; delta flags subtract uncorrupted alerts. Off-injection alerts are unadjudicated.",
        }
    if source == "synthetic_balanced_journals":

        def make(prefix):
            return pd.DataFrame(
                [
                    {
                        "journal_id": f"{prefix}_{i}",
                        "currency": "USD" if i % 2 else "EUR",
                        "total_debits": (10000 + i * 100 if prefix == "DEV" else 50000 + i * 73),
                        "total_credits": (10000 + i * 100 if prefix == "DEV" else 50000 + i * 73),
                    }
                    for i in range(256)
                ]
            ).astype(object)

        dev, test = make("DEV"), make("TEST")
        weak = [Rule("required:" + c, "not_null", [c], evidence="Stipulated synthetic contract") for c in dev]
        full = weak + [
            Rule(
                "currency",
                "allowed",
                ["currency"],
                {"values": ["USD", "EUR"]},
                "Stipulated synthetic contract",
            ),
            Rule("unique", "unique", ["journal_id"], evidence="Stipulated synthetic contract"),
        ]
        full += [
            Rule("nonneg:" + c, "range", [c], {"min": 0}, "verified: synthetic cents nonnegative")
            for c in ["total_debits", "total_credits"]
        ]
        full += [
            Rule(
                "balanceA",
                "less_equal",
                ["total_debits", "total_credits"],
                {"tolerance": 0},
                "verified: balanced synthetic journal",
            ),
            Rule(
                "balanceB",
                "less_equal",
                ["total_credits", "total_debits"],
                {"tolerance": 0},
                "verified: balanced synthetic journal",
            ),
        ]
        targets = ["total_debits", "total_credits", "currency"]
        dc, tc = inject(dev, targets, targets[:2], 20261026), inject(test, targets, targets[:2], 20262026)
        dg, tg = [f"DEV_{i}" for i in range(256)], [f"TEST_{i}" for i in range(256)]
        for case in dc.values():
            case["groups"] = dg
        for case in tc.values():
            case["groups"] = tg
        return {
            "source": source,
            "kind": "SELF_AUTHORED_CONTROLLED_SCENARIO",
            "dev": dev,
            "test": test,
            "dev_cases": dc,
            "test_cases": tc,
            "dev_groups": dg,
            "test_groups": tg,
            "weak_rules": weak,
            "strong_rules": full,
            "contract": {},
            "input_hashes": {"generator": sha(__file__)},
            "group_overlap": 0,
            "note": "Stipulated engineering scenario, not independent natural financial gold.",
        }
    spec = registry[source]
    dirty, clean = load_table(root, source, spec), load_table(root, source, spec, clean=True)
    clean.columns = dirty.columns
    strict, equivalent = normalized_pair(source, dirty, clean)
    gold = {(int(i), str(dirty.columns[j])) for i, j in zip(*np.where(strict & ~equivalent))}
    group_col = "provider_number" if source == "raha_hospital" else "brewery_id"
    # Reference identity used only as split metadata, never as model or qualifier input.
    groups = clean[group_col].astype(str).tolist()
    assignments = [partition(g, "free-model-execution-v1") for g in groups]
    frames, cases, group_sets = {}, {}, {}
    for split in ["development", "exploratory"]:
        ids = [i for i, s in enumerate(assignments) if s == split]
        frames[split] = dirty.iloc[ids].reset_index(drop=True)
        group_sets[split] = [groups[i] for i in ids]
        rows = {j for j, i in enumerate(ids) if any((i, c) in gold for c in dirty)}
        cell_gold = {(j, c) for j, i in enumerate(ids) for c in dirty if (i, c) in gold}
        cases[split] = {
            "reference": {
                "frame": frames[split],
                "gold_rows": rows,
                "gold_cells": cell_gold,
                "groups": group_sets[split],
                "label_interpretation": "PUBLISHED_REFERENCE_DISCREPANCY_AGREEMENT_NOT_SEMANTIC_GOLD",
            }
        }
    assert not set(group_sets["development"]) & set(group_sets["exploratory"])
    missing = [
        Rule(
            "missing:" + c,
            "not_null",
            [c],
            evidence="Generic missing-token workload control, mandatory status unverified",
        )
        for c in dirty
        if c != "index"
    ]
    # Stronger baseline adds lexical-numeric checks only on stated numeric source fields.
    numeric = ["abv", "ibu"] if source == "raha_beers" else []
    numeric = [c for c in numeric if c in dirty]
    stronger = missing + [
        Rule("numeric:" + c, "numeric", [c], evidence="Provisional numeric representation screening")
        for c in numeric
    ]
    return {
        "source": source,
        "kind": "CONDITIONAL_PUBLISHED_REFERENCE_AGREEMENT",
        "dev": frames["development"],
        "test": frames["exploratory"],
        "dev_cases": cases["development"],
        "test_cases": cases["exploratory"],
        "dev_groups": group_sets["development"],
        "test_groups": group_sets["exploratory"],
        "weak_rules": missing,
        "strong_rules": stronger,
        "contract": {},
        "group_overlap": 0,
        "input_hashes": {
            f: sha(root / "data/raw" / source / f) for f in [spec["pair"]["dirty"], spec["pair"]["clean"]]
        },
        "split_hash": digest(assignments),
        "note": "Published dirty/clean discrepancy agreement, not independent semantic precision. Clean identity used for leakage-safe provider/brewery grouping only.",
    }
