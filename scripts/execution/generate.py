"""Bounded checkpoints of the unchanged 48 prepared model-generation requests."""

import argparse
import json
from pathlib import Path

from dqpilot.common import save, sha
from dqpilot_execution.providers import LocalProvider
from dqpilot_free.pilot import parse_candidates

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=int, default=16)
parser.add_argument("--smoke", action="store_true")
args = parser.parse_args()
manifest = json.loads((root / "results/free_gemini/prepared_inputs.json").read_text())
items = manifest["requests"][: args.limit]
if args.smoke:
    items = [next(x for x in manifest["requests"] if x["source"] == "uci_wine_white")]
provider = LocalProvider(root)
try:
    for position, item in enumerate(items):
        limit_file = root / "data/cache/execution/generation_limit"
        if limit_file.exists() and position >= int(limit_file.read_text()):
            print("Stopped at bounded quality-review checkpoint", position, flush=True)
            break
        output = root / "results/execution/generations" / (item["id"].replace(":", "_") + ".json")
        if output.exists():
            print("Existing checkpoint", item["id"], flush=True)
            continue
        prompt_path = root / item["path"]
        if sha(prompt_path) != item["prompt_sha256"]:
            raise ValueError("Frozen prompt changed")
        print("Generating", item["id"], flush=True)
        response, provenance, cached = provider.generate(prompt_path.read_text(), item["seed"])
        record = {"request": item, "provenance": provenance, "cached": cached}
        try:
            rules, abstentions = parse_candidates(response)
            record.update(status="PARSED", rules=rules, abstentions=abstentions)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            record.update(status="MALFORMED_OR_TRUNCATED", failure_type=type(e).__name__, rules=[])
        save(output, record)
        print(
            "Completed",
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
