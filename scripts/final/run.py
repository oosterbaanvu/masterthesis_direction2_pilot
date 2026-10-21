"""Run all feasible added components; preserve previously completed phase outputs."""
import argparse
import json
from pathlib import Path

from dqpilot_final.costs import calculate
from dqpilot_final.financial_run import run
from dqpilot_final.finrule import audit
from dqpilot_final.kaggle_access import acquire
from dqpilot_final.ledqer import reproduce

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--component-output', type=Path, help='Repeat GX components in a fresh output directory only')
args = parser.parse_args()
if args.component_output:
    report = reproduce(root, args.component_output)
    print(json.dumps({'status': report['status'], 'datasets': len(report['records'])}))
else:
    output = root / 'results/final'
    if not (output / 'ledqer_components.json').exists():
        reproduce(root)
    if not (output / 'financial_diagnostics.json').exists():
        run(root)
    if not (output / 'kaggle_acquisition.json').exists():
        acquire(root)
    if (output / 'finrule_acquisition.json').exists() and not (output / 'finrule_audit.json').exists():
        audit(root)
    calculate(root)
    print('Non-paid components completed; no inference client called. Historical outputs preserved.')
