"""Declared exploratory sensitivities, separate from primary outcomes."""
from pathlib import Path

from .acquisition import load_table
from .common import partition, save
from .evaluation import identifier, score
from .experiments import flags, historical_rules, registry, sec_lexical
from .rules import Engine
from .sec import conditions, groundtruth, table_rows


def run_robustness(root):
    root = Path(root)
    comparisons = []
    for directory in conditions(root / 'data/vendor/sec'):
        gt = [g for g in groundtruth(directory) if partition(identifier(g)) == 'exploratory']
        for heuristic in [False, True]:
            original, transformed = [], []
            changed = 0
            for g in gt:
                rows = table_rows(directory / g['fileName'])
                alternate = [[v.lstrip('$') if j else v for j, v in enumerate(r)] for r in rows]
                a = sec_lexical(rows, heuristic)
                b = sec_lexical(alternate, heuristic)
                changed += a != b
                a['fileName'] = b['fileName'] = identifier(g) + '.csv'
                original.append(a)
                transformed.append(b)
            results = {}
            for label, predictions in [('original', original), ('dollar_symbol_removed', transformed)]:
                r = score(gt, predictions)
                r.pop('per_table')
                results[label] = r
            comparisons.append({'condition': directory.name, 'missing_heuristic': heuristic,
                                'tables': len(gt), 'changed_prediction_tables': changed, 'results': results,
                                'interpretation': 'Formatting sensitivity, not a correction to primary baseline'})
    spec = registry(root)['uci_bank_marketing']
    bank = load_table(root, 'uci_bank_marketing', spec).drop(columns=['y'])
    periods = bank['cons.price.idx'].ne(bank['cons.price.idx'].shift()).cumsum()
    historical = bank[periods == 1].reset_index(drop=True)
    numeric_columns = list(bank.select_dtypes('number').columns)
    controls = historical_rules(historical, numeric_columns)
    delivery = []
    for period in [1, 2, 3]:
        batch = bank[periods == period].reset_index(drop=True)
        with Engine(batch) as engine:
            finding_set = flags(engine, controls)
        delivery.append({'period': period, 'rows': len(batch), 'alerts': len(finding_set),
                         'column_alerts': {c: sum(col == c for _, col in finding_set) for c in numeric_columns},
                         'error_accuracy': None, 'interpretation': 'Unlabelled delivery shift; no verified error labels'})
    result = {'sec_formatting': comparisons, 'bank_history_period_1_applied_to_deliveries': delivery,
              'reserved_sec_evaluated': 0, 'C_D_robustness': 'NOT_RUN: no live generated candidates'}
    save(root / 'results/robustness.json', result)
    return comparisons
