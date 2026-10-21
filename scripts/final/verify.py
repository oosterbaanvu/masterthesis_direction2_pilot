"""Verify additive deliverable hashes and the unchanged parent scientific freeze."""
import argparse
import json
import subprocess
from pathlib import Path

from dqpilot.common import save, sha

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--write-manifest', action='store_true')
args = parser.parse_args()
manifest = root / 'results/final/manifest.json'
if args.write_manifest:
    if manifest.exists():
        raise ValueError('Do not replace a completed freeze')
    patterns = ['README.md', '.gitignore', 'src/dqpilot_final/*.py', 'scripts/final/*.py', 'tests_final/*.py',
                'config/final/*', 'envs/final/pyproject.toml', 'envs/final/uv.lock',
                'reports/final/*.md', 'reports/final/figures/*',
                'results/final/*.json', 'results/final/*.xml', 'results/final/*.csv',
                'results/final/attempts/*.json']
    files = sorted({p for pattern in patterns for p in root.glob(pattern) if p.is_file() and p != manifest})
    save(manifest, {'parent_commit': '103d272827bcc5b3211d6b65f4f1a6bd6d8dd36f',
                    'files': {p.relative_to(root).as_posix(): sha(p) for p in files},
                    'paid_model_calls': 0, 'reserved_sec_read_in_new_phase': False})
frozen = json.loads(manifest.read_text())
for name, expected in frozen['files'].items():
    if sha(root / name) != expected:
        raise ValueError('Final deliverable changed: ' + name)
subprocess.run([str(root / '.venv/bin/dqp'), 'verify'], cwd=root, check=True)
print(f"Verified {len(frozen['files'])} added deliverables and unchanged parent scientific hashes.")
