import argparse
import json
import shutil
from pathlib import Path

import pandas as pd
import yaml

from .acquisition import acquire
from .common import save, sha
from .experiments import run_all
from .llm import Provider
from .rules import Engine, load_rules, qualify, read_sql_source
from .sec import audit, reproduce
from .service import Service


def main():
    parser = argparse.ArgumentParser(description='Pilot 2 reproducible research and local DQ service')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['acquire', 'audit-sec', 'reproduce-sec', 'experiments', 'verify']:
        sub.add_parser(name)
    fresh = sub.add_parser('reproduce')
    fresh.add_argument('--work-dir', type=Path, required=True,
                       help='New isolated output directory; raw inputs reused read-only, no Git worktree')
    scan = sub.add_parser('scan')
    scan.add_argument('--csv', type=Path)
    scan.add_argument('--sqlite', type=Path)
    scan.add_argument('--table')
    scan.add_argument('--rules', type=Path, required=True)
    scan.add_argument('--output', type=Path, required=True)
    q = sub.add_parser('qualify')
    q.add_argument('--candidates', type=Path, required=True)
    q.add_argument('--development-csv', type=Path, required=True)
    q.add_argument('--output', type=Path, required=True)
    infer = sub.add_parser('infer')
    infer.add_argument('--context', type=Path, required=True)
    infer.add_argument('--task', choices=['generate', 'detect'], required=True)
    infer.add_argument('--authorize-paid', action='store_true')
    infer.add_argument('--output', type=Path, required=True)
    svc = sub.add_parser('service')
    svc.add_argument('action', choices=['propose', 'validate', 'transition', 'scan', 'review', 'history'])
    svc.add_argument('--database', type=Path, required=True)
    svc.add_argument('--source')
    svc.add_argument('--actor', default='local_operator')
    svc.add_argument('--reason', default='')
    svc.add_argument('--rule-id')
    svc.add_argument('--specification', type=Path)
    svc.add_argument('--csv', type=Path)
    svc.add_argument('--state')
    svc.add_argument('--finding', type=int)
    a = parser.parse_args()
    root = a.root.resolve()
    if a.command == 'acquire':
        result = acquire(root)
        print(json.dumps({k: v['status'] for k, v in result.items()}, indent=2))
        if any(v['status'] == 'FAILED' for v in result.values()):
            raise SystemExit(1)
    elif a.command == 'audit-sec':
        print(json.dumps(audit(root)['conditions'], indent=2))
    elif a.command == 'reproduce-sec':
        print('Reproduced', len(reproduce(root)), 'released prediction artifacts')
    elif a.command == 'experiments':
        result = run_all(root)
        print(json.dumps(result, indent=2))
        if any(v['status'] == 'FAILED' for v in result.values()):
            raise SystemExit(1)
    elif a.command == 'verify':
        manifest = json.loads((root / 'results/run_manifest.json').read_text())
        for name, expected in manifest['artifacts'].items():
            if sha(root / name) != expected:
                raise ValueError('Result artifact changed: ' + name)
        frozen = json.loads((root / 'results/frozen_inputs.json').read_text())
        for name, expected in frozen['files'].items():
            if sha(root / name) != expected:
                raise ValueError('Frozen input changed: ' + name)
        print('Verified all frozen input and result hashes')
    elif a.command == 'reproduce':
        work = a.work_dir.resolve()
        if work.exists():
            raise ValueError('Use a new output directory')
        work.mkdir(parents=True)
        for name in ['src', 'tests', 'config']:
            shutil.copytree(root / name, work / name, ignore=shutil.ignore_patterns('__pycache__'))
        (work / 'reports').mkdir()
        shutil.copyfile(root / 'reports/research_design.md', work / 'reports/research_design.md')
        shutil.copyfile(root / 'reports/protocol_amendments.md', work / 'reports/protocol_amendments.md')
        shutil.copyfile(root / 'uv.lock', work / 'uv.lock')
        shutil.copyfile(root / 'pyproject.toml', work / 'pyproject.toml')
        if (root / 'scripts').exists():
            shutil.copytree(root / 'scripts', work / 'scripts')
        (work / 'data').symlink_to(root / 'data', target_is_directory=True)
        audit(work)
        reproduce(work)
        result = run_all(work)
        print(json.dumps(result, indent=2))
        if any(v['status'] == 'FAILED' for v in result.values()):
            raise SystemExit(1)
    elif a.command == 'scan':
        if bool(a.csv) == bool(a.sqlite):
            parser.error('Choose exactly one CSV or SQLite source')
        frame = pd.read_csv(a.csv, dtype=str, keep_default_na=False) if a.csv else read_sql_source(a.sqlite, a.table)
        findings = []
        with Engine(frame) as engine:
            for rule in load_rules(a.rules):
                findings.extend({'row': row, 'column': col, 'rule': rule.id, 'evidence': rule.evidence}
                                for row, col in sorted(engine.execute(rule)))
        save(a.output, {'rows': len(frame), 'findings': findings})
        print('Findings:', len(findings))
    elif a.command == 'qualify':
        candidates = json.loads(a.candidates.read_text())
        frame = pd.read_csv(a.development_csv, dtype=str, keep_default_na=False)
        decisions = qualify(candidates, frame)
        save(a.output, {'candidate_file_sha256': sha(a.candidates), 'decisions': decisions,
                        'note': 'Qualification never activates rules; semantic review remains necessary'})
        print(json.dumps({s: sum(d['state'] == s for d in decisions)
                          for s in ['VALIDATED', 'REJECTED', 'NEEDS_REVIEW']}, indent=2))
    elif a.command == 'infer':
        c = yaml.safe_load((root / 'config/models.yaml').read_text())
        provider = Provider(c, root / 'data/cache/inference.sqlite', a.authorize_paid)
        try:
            result = provider.infer(json.loads(a.context.read_text()), a.task)
            save(a.output, result)
        finally:
            provider.close()
    elif a.command == 'service':
        service = Service(a.database)
        try:
            if a.action == 'propose':
                for rule in load_rules(a.specification):
                    service.propose(rule, a.source, a.actor)
            elif a.action == 'validate':
                frame = pd.read_csv(a.csv, dtype=str, keep_default_na=False)
                print(json.dumps(service.validate(a.rule_id, frame, a.actor), indent=2))
            elif a.action == 'transition':
                service.transition(a.rule_id, a.state, a.actor, a.reason)
            elif a.action == 'scan':
                frame = pd.read_csv(a.csv, dtype=str, keep_default_na=False)
                print(json.dumps(service.scan(a.source, frame)))
            elif a.action == 'review':
                service.review(a.finding, a.state, a.actor, a.reason)
            elif a.action == 'history':
                print(json.dumps(service.monitoring(a.source), indent=2))
        finally:
            service.close()


if __name__ == '__main__':
    main()
