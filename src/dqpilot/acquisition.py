"""Pinned first-party acquisition. Neither credentials nor raw data are committed."""
import io
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
import yaml

from .common import now, save, sha

SOURCES = {
    'pilot1': ('oosterbaanvu/masterthesis2', '0dcf2c3cb7f0c1ddb0666ebd83e70fb255946af6'),
    'sec': ('XIEFOX/SEC-Fintables', 'f82f80363da1afedbe8b35cede0bae802edab20c'),
    'llm_dqr': ('casperx6/LLM-DQR', 'b92f83ad5878d6a81245872270677d203075a4a2'),
}


def tls_context():
    return ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE'))


def fetch(url):
    if not url.startswith('https://'):
        raise ValueError('HTTPS required')
    with urllib.request.urlopen(url, context=tls_context(), timeout=90) as r:
        return r.read()


def write_verified(path, content, expected):
    import hashlib
    if not expected or hashlib.sha256(content).hexdigest() != expected:
        raise ValueError(f'SHA256 mismatch or unpinned artifact: {path}')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if sha(path) != expected:
            raise ValueError(f'Existing raw file changed: {path}')
        path.chmod(0o444)
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        f.write(content)
    temporary.chmod(0o444)
    temporary.replace(path)


def vendor(root, name):
    identity, commit = SOURCES[name]
    target = Path(root) / 'data/vendor' / name
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', '--no-checkout', '--depth', '1',
                        f'https://github.com/{identity}.git', str(target)], check=True)
        subprocess.run(['git', '-C', str(target), 'fetch', '--depth', '1', 'origin', commit], check=True)
        subprocess.run(['git', '-C', str(target), 'checkout', '--detach', commit], check=True)
    head = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
    if head != commit:
        raise ValueError(f'{name}: wrong vendor commit')
    if subprocess.check_output(['git', '-C', str(target), 'status', '--porcelain'], text=True):
        raise ValueError(f'{name}: modified vendor checkout')
    if name == 'sec':
        for path in target.rglob('*'):
            if path.is_file() and '.git' not in path.parts and path.suffix in {'.csv', '.json'}:
                path.chmod(0o444)
    return target


def acquire(root):
    root = Path(root)
    registry = yaml.safe_load((root / 'config/datasets.yaml').read_text())['datasets']
    records = {}
    for key, spec in registry.items():
        if key == 'sec_fintables':
            try:
                path = vendor(root, 'sec')
                files = {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob('*'))
                         if p.is_file() and '.git' not in p.parts}
                records[key] = {'status': 'ACQUIRED', 'commit': SOURCES['sec'][1], 'files': files}
            except Exception as e:
                records[key] = {'status': 'FAILED', 'reason': str(e)}
            continue
        if spec.get('acquisition', {}).get('source') == 'kaggle':
            names = ['KAGGLE_API_TOKEN', 'KAGGLE_USERNAME', 'KAGGLE_KEY']
            records[key] = {'status': 'BLOCKED', 'reason': 'Optional source; rights unresolved; no authorized acquisition',
                            'credential_presence': {n: bool(os.environ.get(n)) for n in names}}
            continue
        try:
            dest = root / 'data/raw' / key
            evidence = []
            for entry in spec['acquisition']['files']:
                name = entry.get('path', entry['name'])
                file = dest / name
                data = file.read_bytes() if file.exists() else fetch(entry['url'])
                write_verified(file, data, entry['sha256'])
                evidence.append({'file': name, 'url': entry['url'], 'sha256': sha(file), 'bytes': len(data)})
                for member in entry.get('extract', []):
                    content = data
                    for part in member['member'].split('!/'):
                        with zipfile.ZipFile(io.BytesIO(content)) as z:
                            content = z.read(part)
                    write_verified(dest / member['path'], content, member['sha256'])
                    evidence.append({'file': member['path'], 'sha256': sha(dest / member['path'])})
            frame = load_table(root, key, spec)
            table = spec.get('table', {})
            if 'expected_rows' in table and len(frame) != table['expected_rows']:
                raise ValueError('Row count mismatch')
            if 'expected_columns' in table and list(frame.columns) != table['expected_columns']:
                raise ValueError(f'Column mismatch: {list(frame.columns)}')
            if 'pair' in spec:
                clean = pd.read_csv(dest / spec['pair']['clean'], dtype=str, keep_default_na=False)
                if frame.shape != clean.shape:
                    raise ValueError('Dirty/clean shape mismatch')
                headers = list(clean.columns)
            else:
                headers = None
            records[key] = {'status': 'ACQUIRED', 'rows': len(frame), 'columns': list(frame.columns),
                            'reference_columns': headers, 'files': evidence, 'licence': spec.get('licence')}
        except Exception as e:
            records[key] = {'status': 'FAILED', 'reason': f'{type(e).__name__}: {e}'}
    manifest = root / 'results/acquisition.json'
    previous = json.loads(manifest.read_text()) if manifest.exists() else None
    if previous is None or previous.get('datasets') != records:
        save(manifest, {'timestamp': now(), 'datasets': records})
    return records


def load_table(root, key, spec, clean=False):
    dest = Path(root) / 'data/raw' / key
    if 'pair' in spec:
        return pd.read_csv(dest / spec['pair']['clean' if clean else 'dirty'], dtype=str, keep_default_na=False)
    table = spec['table']
    options = table.get('read_options', {})
    if table.get('format') == 'xls':
        return pd.read_excel(dest / table['file'], **options)
    return pd.read_csv(dest / table['file'], **options)


def snapshot_external_sources(root, existing):
    """Reuse validated local clones without modifying the Pilot 1 checkout."""
    root = Path(root)
    for name, folder in existing.items():
        target = root / 'data/vendor' / name
        if target.exists():
            continue
        folder = Path(folder)
        commit = subprocess.check_output(['git', '-C', str(folder), 'rev-parse', 'HEAD'], text=True).strip()
        if commit != SOURCES[name][1]:
            raise ValueError('Unpinned source')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(folder, target)
    save(root / 'results/source_provenance.json', {
        'timestamp': now(), 'sources': {n: {'repository': r, 'commit': c} for n, (r, c) in SOURCES.items()},
        'reuse': 'Pilot 1 dataset registry and contract metadata copied; no Pilot 1 experiments executed or altered',
    })
