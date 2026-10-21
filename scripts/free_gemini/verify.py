"""Freeze/check additive free-pilot inputs without blocking append-only future runs."""
import argparse
import json
import subprocess
from pathlib import Path

from dqpilot.common import save, sha

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--write-manifest', action='store_true')
args = parser.parse_args()
path = root / 'results/free_gemini/source_manifest.json'
if args.write_manifest:
    if path.exists():
        raise ValueError('Preserve a completed source freeze; use a new phase for changes')
    patterns = ['src/dqpilot_free/*.py', 'scripts/free_gemini/*.py', 'tests_free/*.py',
                'config/free_gemini/*', 'reports/free_gemini/*.md', 'results/free_gemini/*.json',
                'results/free_gemini/*.xml', 'results/free_gemini/attempts/*.json']
    files = sorted({p for pattern in patterns for p in root.glob(pattern)
                    if p.is_file() and p != path and p.name != 'run_status.json'})
    save(path, {'parent_commit': '37113d4b209210444a3bd65de6b4fc808741a493',
                'files': {p.relative_to(root).as_posix(): sha(p) for p in files},
                'live_run_status_excluded': True, 'additional_future_attempt_files_permitted': True})
manifest = json.loads(path.read_text())
for file, expected in manifest['files'].items():
    if sha(root / file) != expected:
        raise ValueError('Free-pilot source/input changed: ' + file)
prepared = json.loads((root / 'results/free_gemini/prepared_inputs.json').read_text())
for item in prepared['requests']:
    if sha(root / item['path']) != item['prompt_sha256']:
        raise ValueError('Cached prompt differs from frozen input')
subprocess.run([str(root / 'envs/final/.venv/bin/python'), str(root / 'scripts/final/verify.py')],
               cwd=root, env=None, check=True)
print(f"Verified {len(manifest['files'])} additive inputs and 48 prompt hashes; parent freezes preserved.")
