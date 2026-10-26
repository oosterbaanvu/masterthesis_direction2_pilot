"""Rescore committed real candidates without inference; retain isolated repeat-run outputs."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from dqpilot.common import now, save

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--record", action="store_true", help="Save the initial reproduction evidence once")
args = parser.parse_args()
destination = root / "results/execution/reproduction.json"
if args.record and destination.exists():
    raise ValueError("Preserve the first reproduction evidence; omit --record for another isolated run")
cache = root / "data/cache/execution"
cache.mkdir(parents=True, exist_ok=True)
output = Path(tempfile.mkdtemp(prefix="rescore_", dir=cache))


def agrees(old, new):
    if isinstance(old, dict):
        return all(k in new and agrees(v, new[k]) for k, v in old.items())
    if isinstance(old, list):
        return len(old) == len(new) and all(agrees(x, y) for x, y in zip(old, new))
    return old == new


checks = []
for original in sorted((root / "results/execution/evaluation").glob("*.json")):
    saved = json.loads(original.read_text())
    command = [
        sys.executable,
        "scripts/execution/evaluate.py",
        "--source",
        saved["source"],
        "--condition",
        saved["condition"],
        "--output-dir",
        str(output),
    ]
    subprocess.run(command, cwd=root, check=True)
    repeated = json.loads((output / "evaluation" / original.name).read_text())
    equal = agrees(saved, repeated)
    checks.append({"file": original.name, "all_original_scientific_fields_equal": equal})
    if not equal:
        raise AssertionError("Rescoring differed: " + original.name)
result = {
    "time_utc": now(),
    "new_model_requests": 0,
    "sources": checks,
    "isolated_output": output.relative_to(root).as_posix(),
    "comparison": "All original scientific result fields, including candidate execution and confusion counts; final code may add explicit diagnostics",
}
if args.record:
    save(destination, result)
else:
    save(output / "comparison.json", result)
print("All", len(checks), "evaluations reproduced without inference. Outputs:", output)
