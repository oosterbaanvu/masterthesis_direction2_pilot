"""Explicitly authorised free generation; no paid provider is imported or selected."""
import argparse
from pathlib import Path

from dqpilot_free.pilot import run
from dqpilot_free.prepare import prepare

parser = argparse.ArgumentParser()
parser.add_argument('--prepare-only', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
report = prepare(root) if args.prepare_only else run(root)
print(report['status'])
if report.get('reason'):
    print(report['reason'])
