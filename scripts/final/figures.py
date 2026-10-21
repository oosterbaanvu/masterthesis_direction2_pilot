"""Standalone figures from measured component outputs and labelled cost scenarios."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams['svg.hashsalt'] = 'dq-final-feasibility-v1'


def save_figure(figure, directory, stem):
    for extension in ['svg', 'png']:
        path = directory / (stem + '.' + extension)
        metadata = {'Date': None} if extension == 'svg' else {}
        figure.savefig(path, dpi=180, bbox_inches='tight', metadata=metadata)
        if extension == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')


root = Path(__file__).resolve().parents[2]
out = root / 'reports/final/figures'
out.mkdir(exist_ok=True)
records = json.loads((root / 'results/final/ledqer_components.json').read_text())['records']
fig, ax = plt.subplots(figsize=(8, 4.6), layout='constrained')
x = np.arange(len(records))
ax.bar(x - .18, [r['technical_fixture_agreement']['tp'] for r in records], .36, label='Technical union')
ax.bar(x + .18, [r['original_greedy'][-1]['author_label_agreement']['tp'] for r in records], .36, label='Label-assisted greedy, precision >= 1')
ax.set(xticks=x, xticklabels=[r['dataset'].title() for r in records], ylabel='Released-label hits on separate evaluation groups',
       title='Handwritten GX fixtures: component behavior only')
ax.legend(loc='upper right', fontsize=8)
fig.text(.5, -.015, 'Not LLM outputs; not independent semantic accuracy. Tax: no hits. Hospital loses 6 hits.', ha='center', fontsize=8)
save_figure(fig, out, 'component_labelled_hits')
plt.close(fig)

costs = json.loads((root / 'results/final/model_cost_proposal.json').read_text())['records']
chosen = [r for r in costs if r['model'] in {'gpt-4.1-mini', 'gpt-5.4-mini', 'gemini-2.5-flash'}]
fig, ax = plt.subplots(figsize=(8, 4.6), layout='constrained')
x = np.arange(len(chosen))
ax.bar(x - .18, [r['pilot_48_calls_usd'] for r in chosen], .36, label='48-call pilot per model')
ax.bar(x + .18, [r['full_240_calls_one_model_usd'] for r in chosen], .36, label='240 calls per model')
ax.set(xticks=x, xticklabels=[r['model'] for r in chosen], ylabel='Planned API ceiling, USD before tax',
       title='Cost proposal: 20k input + 2k output tokens per call')
ax.legend(fontsize=8)
fig.text(.5, -.015, 'Planning scenario, not spending. No cache/batch discounts; retries excluded from these bars.', ha='center', fontsize=8)
save_figure(fig, out, 'model_cost_scenarios')
plt.close(fig)
