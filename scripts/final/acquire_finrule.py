"""Bounded public research snapshot via the repository's documented file endpoints.

No model execution. Preserve the MIT notice and research-only README; do not
redistribute raw source tables or imply an external-processing permission.
"""
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from dqpilot.common import save, sha

root = Path(__file__).resolve().parents[2]
target = root / 'data/raw/finrule_bench'
manifest_path = root / 'results/final/finrule_acquisition.json'
base = 'https://anonymous.4open.science/api/repo/FinRule-Bench-6723/'
headers = {'User-Agent': 'MSc-research-feasibility/1.0'}


def fetch(route, maximum=5000000):
    with urlopen(Request(base + route, headers=headers), timeout=30) as response:
        content = response.read(maximum + 1)
        if len(content) > maximum:
            raise ValueError('BOUNDED_ACQUISITION_SIZE_EXCEEDED')
        return content


if manifest_path.exists():
    frozen = json.loads(manifest_path.read_text())
    for item in frozen['files']:
        path = target / item['path']
        content = path.read_bytes() if path.exists() else fetch('file/' + quote(item['path']))
        if hashlib.sha256(content).hexdigest() != item['sha256']:
            raise ValueError('Public source changed; do not replace the frozen snapshot')
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(0o444)
    print('Existing FinRule content hashes verified; missing files restored without changing pins.')
    raise SystemExit(0)


listing, queue, files = {}, ['data', 'task'], ['LICENSE', 'README.md', 'extract/data.json',
    'extract/comparison_tool.py', 'extract/Inject Prompt.txt', 'run_all_fingpt.py', 'aggregate_results_fingpt.py']
while queue:
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(lambda p: (p, fetch('files?path=' + quote(p))), queue))
    queue = []
    for folder, content in responses:
        entries = json.loads(content)
        listing[folder] = entries
        for entry in entries:
            path = folder + '/' + entry['name']
            if 'size' not in entry:
                queue.append(path)
            elif Path(path).suffix.lower() in {'.json', '.csv', '.py', '.md', '.txt'}:
                files.append(path)
    if len(files) > 10000 or len(listing) > 1000:
        raise ValueError('REVIEW_REQUIRED_FOR_LARGER_REPOSITORY')
save(root / 'results/final/finrule_listing.json', listing)
listed_bytes = sum(e.get('size', 0) for entries in listing.values() for e in entries)
if listed_bytes > 80000000:
    raise ValueError('REVIEW_REQUIRED_ABOVE_80MB_BOUND')


def download(path):
    output = target / path
    content = output.read_bytes() if output.exists() else fetch('file/' + quote(path))
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_bytes(content)
    output.chmod(0o444)
    return {'path': path, 'sha256': sha(output), 'bytes': len(content), 'status': 'ACQUIRED'}


with ThreadPoolExecutor(max_workers=6) as pool:
    records = list(pool.map(download, sorted(set(files))))
save(manifest_path, {'status': 'ACQUIRED_BOUNDED_RESEARCH_SNAPSHOT', 'repository': base,
    'revision': 'ANONYMOUS_SERVICE_NO_FULL_GIT_COMMIT_EXPOSED_CONTENT_SHA256_PINNED',
    'licence_notice': 'MIT (Copyright 2026 Anonymous); README says strictly research and evaluation',
    'raw_redistribution': False, 'external_model_transmission': 'NOT_INFERRED',
    'files': records, 'listed_bytes': listed_bytes, 'paid_model_calls': 0})
print(json.dumps({'files': len(records), 'bytes': sum(r['bytes'] for r in records)}))
