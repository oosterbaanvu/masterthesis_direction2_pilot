"""Restore byte-pinned primary papers into ignored storage; never change pins."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

from dqpilot.acquisition import write_verified

root = Path(__file__).resolve().parents[2]
sources = json.loads((root / 'config/final/literature_sources.json').read_text())['sources']


def acquire(item):
    path = root / 'data/raw/final_literature' / (item['key'] + '.pdf')
    if path.exists():
        content = path.read_bytes()
    else:
        with urlopen(Request(item['url'], headers={'User-Agent': 'MSc-research-feasibility/1.0'}), timeout=30) as response:
            content = response.read(16000001)
        if len(content) > 16000000 or not content.startswith(b'%PDF'):
            raise ValueError('Expected bounded PDF: ' + item['key'])
    write_verified(path, content, item['sha256'])
    return item['key']


with ThreadPoolExecutor(max_workers=4) as pool:
    verified = list(pool.map(acquire, sources))
print('Pinned primary PDFs verified:', ', '.join(verified))
