"""Local-only schema generation for two published reference benchmarks; no labels in prompts."""

import json
from pathlib import Path

import yaml

from dqpilot.acquisition import load_table
from dqpilot.common import save, sha, now
from dqpilot_execution.providers import LocalProvider
from dqpilot_free.prepare import PROMPT
from dqpilot_free.pilot import parse_candidates

root = Path(__file__).resolve().parents[2]
original = json.loads((root / "results/free_gemini/prepared_inputs.json").read_text())
guided = json.loads((root / "results/execution/guided_input_freeze.json").read_text())
suffix = (root / guided["requests"][0]["path"]).read_text()[
    len((root / original["requests"][0]["path"]).read_text()) :
]
registry = yaml.safe_load((root / "config/datasets.yaml").read_text())["datasets"]
descriptions = {
    "raha_hospital": "US hospital/provider quality-measure records. A provider can appear in multiple measure rows. "
    "Postal/telephone/provider codes are text identifiers. Optionality and exact business formats are not independently established. "
    "Any additional assumptions are provisional. This is a public research benchmark, not patient-level private clinical data.",
    "raha_beers": "Craft beer and brewery lookup records. Multiple beers can share a brewery. "
    "ABV is alcohol-by-volume, IBU bitterness, ounces package capacity. Exact required-field and unit-format policies "
    "are not established here; do not infer them from a clean reference. Additional assumptions are provisional.",
}
requests = []
for source in descriptions:
    frame = load_table(root, source, registry[source])
    for docs in ["provided", "withheld"]:
        context = {
            "source": source,
            "citation": registry[source]["landing_page"],
            "schema": [{"name": c, "type": "string"} for c in frame if c != "index"],
            "source_documentation": descriptions[source]
            if docs == "provided"
            else "Additional source documentation withheld.",
            "existing_controls": [
                {"kind": "missing_token_screen", "column": c, "mandatory_status": "NOT_ESTABLISHED"}
                for c in frame
                if c != "index"
            ],
            "sample": [],
            "format_note": "CSV fields are delivered as strings. Numeric-named fields are not automatically floating-point dataframe columns.",
        }
        prompt = PROMPT + json.dumps(context, sort_keys=True) + suffix
        path = root / "data/cache/execution/benchmark_prompts" / f"{source}_{docs}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text() != prompt:
            raise ValueError("Frozen benchmark prompt changed")
        path.write_text(prompt)
        requests.append(
            {
                "id": source + ":" + docs,
                "source": source,
                "documentation": docs,
                "seed": 11,
                "path": path.relative_to(root).as_posix(),
                "prompt_sha256": sha(path),
            }
        )
manifest = root / "results/execution/benchmark_input_freeze.json"
if not manifest.exists():
    save(
        manifest,
        {
            "time_utc": now(),
            "requests": requests,
            "labels_or_clean_values_in_prompt": False,
            "raw_records_in_prompt": False,
            "local_inference_only": True,
            "source_rights": "Conditional public research reuse; no raw dataset redistributed or externally transmitted",
        },
    )
else:
    assert json.loads(manifest.read_text())["requests"] == requests
provider = LocalProvider(root, condition="published_schema_v1")
try:
    for item in requests:
        out = (
            root
            / "results/execution/benchmark_generations"
            / f"{item['source']}_{item['documentation']}.json"
        )
        if out.exists():
            continue
        print("Generating benchmark", item["id"], flush=True)
        response, provenance, cached = provider.generate((root / item["path"]).read_text(), 11)
        record = {"request": item, "provenance": provenance, "cached": cached}
        try:
            rules, abstentions = parse_candidates(response)
            record.update(status="PARSED", rules=rules, abstentions=abstentions)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            record.update(status="MALFORMED_OR_TRUNCATED", failure_type=type(e).__name__, rules=[])
        save(out, record)
        print("Completed benchmark", item["id"], record["status"], len(record["rules"]), flush=True)
finally:
    provider.close()
