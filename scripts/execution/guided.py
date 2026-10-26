"""Separate API-syntax condition after a failed original smoke; never repair saved outputs."""

import argparse
import json
from pathlib import Path

from dqpilot.common import save, sha, now
from dqpilot_execution.providers import LocalProvider
from dqpilot_free.pilot import parse_candidates

root = Path(__file__).resolve().parents[2]
syntax = """
GX 1.9.1 API syntax reference (generic library documentation, NOT dataset rules):
gx_code must contain ONE COMPLETE CONSTRUCTOR EXPRESSION, including parentheses and
literal arguments INSIDE the gx_code string. Do not put kwargs in a separate field.
Example of the JSON format only:
{"rules":[{"id":"example","description":"A proposed check","gx_code":"gx.expectations.ExpectColumnValuesToBeBetween(column='FIELD', min_value=0, max_value=10)","evidence_references":[]}],"abstentions":[]}
FIELD above is a placeholder; use only actual SOURCE_CONTEXT column names.
Allowed pandas constructors and their argument names:
- gx.expectations.ExpectColumnValuesToNotBeNull(column='FIELD')
- gx.expectations.ExpectColumnValuesToBeBetween(column='FIELD', min_value=0, max_value=10)
- gx.expectations.ExpectColumnValuesToBeInSet(column='FIELD', value_set=['DOCUMENTED_VALUE'])
- gx.expectations.ExpectColumnValuesToBeUnique(column='FIELD')
- gx.expectations.ExpectColumnValuesToMatchRegex(column='FIELD', regex='DOCUMENTED_PATTERN')
- gx.expectations.ExpectColumnValuesToBeOfType(column='FIELD', type_='float64')
- gx.expectations.ExpectColumnPairValuesToBeEqual(column_A='FIELD_A', column_B='FIELD_B')
- gx.expectations.ExpectColumnPairValuesAToBeGreaterThanB(column_A='FIELD_A', column_B='FIELD_B', or_equal=True)
- gx.expectations.ExpectMulticolumnSumToEqual(column_list=['FIELD_A','FIELD_B'], sum_total=0)
These parameter values are syntax examples, NOT justified constraints. Do not copy
them unless source documentation independently supports them. Do not use old
gx.expect_column_* methods, imaginary GX classes, column() functions, row_condition,
SQL, imports, arithmetic expressions or dynamic arguments. A class name without
its constructor arguments is not executable. Return JSON only, at most FOUR rules.
"""
parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=int, default=16)
parser.add_argument("--smoke", action="store_true")
args = parser.parse_args()
original = json.loads((root / "results/free_gemini/prepared_inputs.json").read_text())
freeze_path = root / "results/execution/guided_input_freeze.json"
requests = []
for item in original["requests"]:
    prompt = (root / item["path"]).read_text() + syntax
    path = root / "data/cache/execution/guided_prompts" / (item["id"].replace(":", "_") + ".txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() != prompt:
        raise ValueError("Guided condition input changed")
    path.write_text(prompt)
    requests.append(
        dict(
            item,
            path=path.relative_to(root).as_posix(),
            prompt_sha256=sha(path),
            prompt_utf8_bytes=len(prompt.encode()),
            original_prompt_sha256=item["prompt_sha256"],
        )
    )
if not freeze_path.exists():
    save(
        freeze_path,
        {
            "time_utc": now(),
            "condition": "gx_syntax_guided_v1",
            "requests": requests,
            "reason": "Original smoke produced class references and legacy APIs, not executable GX1.9 constructors.",
            "adaptation_informed_by": "generation/technical smoke only, no held-out error labels or detection outcomes",
            "original_responses_retained": True,
            "handwritten_candidates_substituted": False,
        },
    )
else:
    assert json.loads(freeze_path.read_text())["requests"] == requests
items = requests[: args.limit]
if args.smoke:
    items = [next(x for x in requests if x["source"] == "uci_wine_white")]
provider = LocalProvider(root, condition="gx_syntax_guided_v1")
try:
    for item in items:
        out = root / "results/execution/guided_generations" / (item["id"].replace(":", "_") + ".json")
        if out.exists():
            print("Existing", item["id"], flush=True)
            continue
        print("Generating guided", item["id"], flush=True)
        response, provenance, cached = provider.generate((root / item["path"]).read_text(), item["seed"])
        record = {"request": item, "provenance": provenance, "cached": cached}
        try:
            rules, abstentions = parse_candidates(response)
            record.update(status="PARSED", rules=rules, abstentions=abstentions)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            record.update(status="MALFORMED_OR_TRUNCATED", failure_type=type(e).__name__, rules=[])
        save(out, record)
        print(
            "Completed guided",
            item["id"],
            record["status"],
            "rules",
            len(record["rules"]),
            "seconds",
            round(provenance["runtime_seconds"], 1),
            flush=True,
        )
finally:
    provider.close()
