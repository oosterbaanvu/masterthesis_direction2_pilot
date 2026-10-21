"""Fetch pinned primary material without redistributing papers in Git."""
import json
from pathlib import Path

from dqpilot.acquisition import fetch, write_verified
from dqpilot.common import save

root = Path(__file__).resolve().parents[1]
sources = json.loads((root / 'config/literature_sources.json').read_text())['sources']
outcomes = []
for source in sources:
    path = root / 'data/raw/literature' / source['file']
    try:
        content = path.read_bytes() if path.exists() else fetch(source['url'])
        write_verified(path, content, source['sha256'])
        outcomes.append({'key': source['key'], 'status': 'VERIFIED', 'sha256': source['sha256']})
    except Exception as e:
        outcomes.append({'key': source['key'], 'status': 'FAILED', 'reason': str(e)})
save(root / 'results/literature_acquisition.json', outcomes)
print(json.dumps(outcomes, indent=2))
if any(x['status'] == 'FAILED' for x in outcomes):
    raise SystemExit(1)
