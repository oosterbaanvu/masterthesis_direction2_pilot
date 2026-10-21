import platform
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .acquisition import load_table
from .common import digest, now, partition, save, sha
from .evaluation import cells, grouped_bootstrap, identifier, score
from .rules import Engine, Rule, missing, number
from .sec import conditions, groundtruth, table_rows
from .service import Service


def registry(root):
    return yaml.safe_load((Path(root) / 'config/datasets.yaml').read_text())['datasets']


def contract_rules(root, key):
    """Compile supported, attributed source controls, recording unsupported expressions."""
    contract = yaml.safe_load((Path(root) / f'config/contracts/{key}.yaml').read_text())
    specs = {c['name']: c for c in contract['columns']}
    rules, omitted = [], []
    for col, spec in specs.items():
        if spec['type'] == 'numeric':
            rules.append(Rule(f'type:{col}', 'numeric', [col], evidence='Source contract numeric datatype'))
    for item in contract['rules']:
        if item.get('enabled') is False or item.get('status') == 'unsupported':
            omitted.append({'id': item['id'], 'reason': 'Explicitly unsupported in source contract'})
            continue
        expanded = item.get('for_each', [None])
        for member in expanded:
            cols = list(specs) if item['columns'] == 'all' else [c.replace('{i}', str(member)) for c in item['columns']]
            kind = {'accepted_values': 'allowed'}.get(item['kind'], item['kind'])
            if kind == 'expression':
                if key == 'uci_wine_white' and item['id'] == 'D_FREE_TOTAL':
                    rules.append(Rule(item['id'], 'less_equal', cols, {'tolerance': 0}, item['evidence']))
                elif key == 'uci_bank_marketing' and item['id'] == 'D_POUTCOME_PREVIOUS':
                    rules.extend([
                        Rule('previous_implies_outcome', 'implication', ['previous', 'poutcome'],
                             {'if_value': '0', 'then_value': 'nonexistent'}, item['evidence']),
                        Rule('outcome_implies_previous', 'implication', ['poutcome', 'previous'],
                             {'if_value': 'nonexistent', 'then_value': '0'}, item['evidence'])])
                else:
                    omitted.append({'id': item['id'], 'reason': 'Expression outside constrained pilot DSL'})
                continue
            params = {k: item[k] for k in ['min', 'max'] if k in item}
            if kind == 'allowed':
                params['values'] = specs[cols[0]]['documented_values'] if item.get('from_documented') else item['values']
            for col in cols:
                rules.append(Rule(item['id'].replace('{i}', str(member)) + ':' + col,
                                  kind, [col], params, f"{item.get('status')}: {item['evidence']}"))
    # ID is a key, outside the feature-contract column list, and never a prediction target.
    if contract.get('row_id') and not any(r.kind == 'unique' for r in rules):
        rules.append(Rule('key', 'unique', [contract['row_id']], evidence='Source contract primary key'))
    return rules, omitted, contract


def flags(engine, rules):
    result = set()
    for rule in rules:
        result |= engine.execute(rule)
    return result


def historical_rules(frame, numeric_columns):
    rules = []
    for c in numeric_columns:
        s = pd.to_numeric(frame[c], errors='coerce').dropna()
        if len(s) > 1:
            lo, hi = s.quantile([0.0005, 0.9995])
            rules.append(Rule('history:' + c, 'range', [c], {'min': float(lo), 'max': float(hi)},
                              'Provisional historical 0.05/99.95% envelope fitted on development rows only'))
    return rules


def actual_change(old, new, numeric=False):
    if missing(old) or missing(new):
        return missing(old) != missing(new)
    if numeric:
        before, after = number(old), number(new)
        if before is not None and after is not None:
            return before != after
    return str(old) != str(new)


def freeze(root):
    root = Path(root)
    files = sorted(p for folder in ['src', 'config', 'tests', 'scripts'] for p in (root / folder).rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts)
    files += [root / 'uv.lock', root / 'pyproject.toml', root / 'reports/research_design.md',
              root / 'reports/protocol_amendments.md']
    save(root / 'results/frozen_inputs.json', {'timestamp': now(), 'python': platform.python_version(),
                                             'files': {str(p.relative_to(root)): sha(p) for p in files}})


def regular(root):
    root = Path(root)
    specs = registry(root)
    cases, splits, injections, omitted_all = [], {}, [], {}
    configuration = yaml.safe_load((root / 'config/pilot.yaml').read_text())
    targets = configuration['regular_numeric_columns']
    categorical = configuration['regular_categorical_columns']
    for key, target_columns in targets.items():
        frame = load_table(root, key, specs[key])
        rules, omitted, contract = contract_rules(root, key)
        frame = frame.drop(columns=list(contract.get('excluded_columns', {})))
        omitted_all[key] = omitted
        numbers = [c['name'] for c in contract['columns'] if c['type'] == 'numeric']
        group_columns = [c for c in frame if c != contract.get('row_id')]
        groups = [digest([str(v) for v in row]) for row in frame[group_columns].itertuples(index=False, name=None)]
        for seed in configuration['regular_seeds']:
            assignments = [partition(g, f'uci-pilot2-{seed}') for g in groups]
            dev_idx = [i for i, s in enumerate(assignments) if s == 'development']
            eval_idx = [i for i, s in enumerate(assignments) if s == 'exploratory']
            ref = frame.iloc[dev_idx].reset_index(drop=True)
            original = frame.iloc[eval_idx].reset_index(drop=True).astype(object)
            hist = historical_rules(ref, numbers)
            splits[f'{key}:{seed}'] = {'counts': dict(Counter(assignments)),
                                      'row_assignment_sha256': digest(assignments),
                                      'overlap_group_count': len(set(groups[i] for i in dev_idx) &
                                                                 set(groups[i] for i in eval_idx))}
            with Engine(original) as eng:
                original_flags = flags(eng, rules)
            for column in target_columns + categorical[key]:
                families = (['missing', 'invalid_code', 'plausible_swap'] if column in categorical[key]
                            else ['missing', 'invalid_type', 'gross_scale', 'plausible_swap'])
                for rate in configuration['injection_rates']:
                    for family in families:
                        started = time.monotonic()
                        rng = np.random.default_rng(seed + int(rate * 10000) +
                                                    families.index(family))
                        n = max(1, round(len(original) * rate))
                        indices = rng.choice(len(original), n, replace=False)
                        corrupted = original.copy(deep=True)
                        gold = set()
                        for i in indices:
                            old = corrupted.at[i, column]
                            if family == 'missing':
                                new = None
                            elif family in {'invalid_type', 'invalid_code'}:
                                new = 'NOT_A_NUMBER' if family == 'invalid_type' else '__INVALID_CODE__'
                            elif family == 'gross_scale':
                                new = float(old) * 10
                            else:
                                choices = ref.loc[ref[column] != old, column]
                                if choices.empty:
                                    continue
                                new = choices.iloc[int(rng.integers(len(choices)))]
                            if actual_change(old, new, numeric=column in numbers):
                                corrupted.at[i, column] = new
                                gold.add((int(i), column))
                                injections.append({'source': key, 'seed': seed, 'rate': rate, 'family': family,
                                                   'row': int(i), 'original_row': eval_idx[i], 'column': column,
                                                   'old': str(old), 'new': str(new)})
                        if not gold:
                            cases.append({'source': key, 'seed': seed, 'rate': rate, 'family': family,
                                          'column': column, 'intended': n, 'realized': 0,
                                          'status': 'FAILED', 'reason': 'No actual changed cells'})
                            continue
                        with Engine(corrupted) as engine:
                            a = flags(engine, rules)
                            historical = flags(engine, hist)
                        combined = a | historical
                        outcomes = {}
                        for name, predicted in [('A_contract', a), ('A_plus_history', combined)]:
                            outcomes[name] = {**cells(predicted, gold), 'alerts': len(predicted),
                                              'off_injection_alerts': len(predicted - gold),
                                              'interpretation': 'Precision is injection-relative; off-label alerts unadjudicated'}
                        cases.append({'source': key, 'seed': seed, 'rate': rate, 'family': family, 'status': 'COMPLETE',
                                      'rows': len(original), 'column': column, 'intended': n, 'realized': len(gold),
                                      'unchanged_selected_cells': n - len(gold),
                                      'all_feature_cell_prevalence': len(gold) / corrupted.size,
                                      'untouched_contract_alerts': len(original_flags), 'methods': outcomes,
                                      'additional_injected_detections_history': len((combined - a) & gold),
                                      'runtime_seconds': time.monotonic() - started})
    save(root / 'results/regular_experiments.json', {'cases': cases, 'splits': splits, 'omitted_controls': omitted_all})
    save(root / 'results/local/injection_log.json', injections)
    return cases


def normalized_pair(key, dirty, clean):
    diff = dirty.to_numpy() != clean.to_numpy()
    equivalent = np.zeros(diff.shape, dtype=bool)
    for j, column in enumerate(dirty.columns):
        numeric = key == 'jung_cars' and column in {'MPG', 'Cylinders', 'Displacement', 'Horsepower',
                                                    'Weight', 'Acceleration', 'Model'}
        for i in np.flatnonzero(diff[:, j]):
            a, b = dirty.iat[i, j], clean.iat[i, j]
            if numeric or (key == 'raha_tax' and column.lower() in {'rate', 'zip'}):
                if key == 'raha_tax' and column.lower() == 'zip':
                    equivalent[i, j] = a.isdigit() and b.isdigit() and a.zfill(5) == b.zfill(5)
                else:
                    na, nb = number(a), number(b)
                    equivalent[i, j] = na is not None and nb is not None and na == nb
    return diff, equivalent


def pairs(root):
    root = Path(root)
    specs = registry(root)
    results = []
    for key, spec in specs.items():
        if 'pair' not in spec:
            continue
        dirty, clean = load_table(root, key, spec), load_table(root, key, spec, clean=True)
        reference_headers = list(clean.columns)
        clean.columns = dirty.columns  # Explicit source-declared positional alignment, never a name join.
        strict, equivalent = normalized_pair(key, dirty, clean)
        excluded = np.zeros(strict.shape, dtype=bool)
        if key == 'jung_restaurant' and 'class' in dirty:
            excluded[:, list(dirty.columns).index('class')] = True
        rules = [Rule('completeness:' + c, 'not_null', [c],
                      evidence='Generic missing-token review finding; mandatory status unestablished') for c in dirty]
        with Engine(dirty) as engine:
            predicted = flags(engine, rules)
        strict_gold = {(int(i), str(dirty.columns[j])) for i, j in zip(*np.where(strict & ~excluded))}
        normalized_gold = {(int(i), str(dirty.columns[j])) for i, j in zip(*np.where(strict & ~equivalent & ~excluded))}
        result = {'source': key, 'rows': len(dirty), 'columns': list(dirty.columns),
                  'reference_headers': reference_headers, 'strict_differences': int(strict.sum()),
                  'numeric_equivalent_differences': int(equivalent.sum()),
                  'excluded_annotation_differences': int((strict & excluded).sum()),
                  'generic_completeness_alerts': len(predicted),
                  'reference_alignment': 'position; source headers retained in manifest; row identity not independently guaranteed'}
        if key == 'raha_rayyan':
            result.update(status='WORKLOAD_ONLY', accuracy=None,
                          reason='Reference date/encoding/missing-value interpretation not independently adjudicated')
        else:
            result.update(status='CONDITIONAL_REFERENCE', strict_difference_agreement=cells(predicted, strict_gold),
                          normalized_difference_agreement=cells(predicted, normalized_gold),
                          interpretation='Agreement with published reference, not independently adjudicated semantic precision')
        results.append(result)
    save(root / 'results/published_pairs.json', results)
    return results


def sec_lexical(rows, include_missing=False):
    """Input is CSV rows only. No filename or annotation is accepted."""
    locs, error_types = set(), set()
    for row in rows:
        if not row or not row[0].strip():
            continue
        values = row[1:]
        numeric_count = sum(number(v) is not None or v.strip().lstrip('$') in {'—', '–', '-'} for v in values)
        if not values or numeric_count / len(values) < 0.6:
            continue
        for j, value in enumerate(values, 1):
            if include_missing and not value.strip():
                locs.add((row[0], j))
                error_types.add('MISS')
            elif (value.strip() and any(c.isdigit() for c in value) and number(value) is None
                  and value.strip().lstrip('$') not in {'—', '–', '-'}):
                locs.add((row[0], j))
                error_types.add('FMT')
    return {'errNum': len(locs), 'missNum': sum(1 for r, c in locs for row in rows
                                               if row and row[0] == r and c < len(row) and not row[c].strip()),
            'errType': sorted(error_types), 'errLoc': [{'row_name': r, 'col_idx': c} for r, c in sorted(locs)]}


def sec_baseline(root):
    root = Path(root)
    results, grouped = [], {}
    for directory in conditions(root / 'data/vendor/sec'):
        gt = [g for g in groundtruth(directory) if partition(identifier(g)) == 'exploratory']
        for heuristic in [False, True]:
            predictions = []
            for g in gt:
                rows = table_rows(directory / g['fileName'])
                prediction = sec_lexical(rows, include_missing=heuristic)
                prediction['fileName'] = identifier(g) + '.csv'  # Anonymous ID assigned after detection.
                predictions.append(prediction)
            result = score(gt, predictions)
            per = result.pop('per_table')
            grouped.setdefault(str(heuristic), []).extend(per)
            slices = {}
            for kind in ['VAL', 'FMT', 'MISS']:
                selected = [g for g in gt if kind in __import__('dqpilot.evaluation', fromlist=['types']).types(g)]
                if selected:
                    sub = score(selected, predictions)
                    slices[kind] = {'tables': sub['tables'], 'location': sub['location'], 'table': sub['table']}
            results.append({'condition': directory.name, 'missing_heuristic': heuristic,
                            'partition': 'exploratory', **result, 'error_type_slices': slices})
    save(root / 'results/sec_baseline.json', {'results': results,
        'grouped_uncertainty': {k: grouped_bootstrap(v) for k, v in grouped.items()},
        'reserved_tables_evaluated': 0,
        'note': 'Lexical coverage baseline; missing heuristic is unsupported-business-semantics sensitivity only'})
    return results


def service_demo(root):
    root = Path(root)
    path = root / 'results/local/demo.sqlite'
    if path.exists():
        raise ValueError('Do not overwrite prior service evidence')
    specs = registry(root)
    service = Service(path)
    summaries = []
    for key, spec in specs.items():
        if key in {'baf', 'gmsc', 'sec_fintables'}:
            continue
        frame = load_table(root, key, spec)
        # Every acquired regular/pair source gets a complete scan, including 200k Tax rows.
        # Sparse token counts are review findings, not confirmed mandatory-field errors.
        for column in frame:
            rule = Rule(f'{key}:missing:{column}', 'not_null', [column],
                        evidence='Operator-approved missing-token monitoring; mandatory status not established')
            service.propose(rule, key, 'demo_operator')
            # A clean development fixture only demonstrates the governance path, not real rule qualification.
            development_fixture = pd.DataFrame({column: ['present']})
            service.validate(rule.id, development_fixture, 'demo_qualifier')
            service.transition(rule.id, 'APPROVED', 'demo_reviewer', 'Explicit demonstration approval')
            service.transition(rule.id, 'ACTIVE', 'demo_operator', 'Activate missing-token monitoring')
        summaries.append(service.scan(key, frame))
    # SEC adapter preserves irregular headers via raw-field columns, with no business-rule claims.
    directory = conditions(root / 'data/vendor/sec')[0]
    g = next(g for g in groundtruth(directory) if partition(identifier(g)) == 'development')
    raw = table_rows(directory / g['fileName'])
    width = max(map(len, raw))
    sec_frame = pd.DataFrame([r + [''] * (width - len(r)) for r in raw],
                             columns=[f'field_{i}' for i in range(width)])
    rule = Rule('sec:row_label', 'not_null', ['field_0'], evidence='Review presentation blanks; no error assertion')
    service.propose(rule, 'sec_fintables', 'demo_operator')
    service.validate(rule.id, pd.DataFrame({'field_0': ['present']}), 'demo_qualifier')
    service.transition(rule.id, 'APPROVED', 'demo_reviewer', 'Explicit presentation review demo')
    service.transition(rule.id, 'ACTIVE', 'demo_operator', 'Activate demo')
    summaries.append(service.scan('sec_fintables', sec_frame))
    # Actual earlier/later Bank deliveries. These are not calibrated concept-drift alarms.
    bank = load_table(root, 'uci_bank_marketing', specs['uci_bank_marketing'])
    period = bank['cons.price.idx'].ne(bank['cons.price.idx'].shift()).cumsum()
    for n in [1, 2, 3]:
        summaries.append(service.scan('uci_bank_marketing', bank[period == n].reset_index(drop=True)))
    first = service.db.execute('SELECT id FROM findings ORDER BY id LIMIT 1').fetchone()
    if first:
        service.review(first[0], 'INVESTIGATING', 'demo_reviewer', 'Exercise exception workflow; no adjudication claimed')
    monitoring = service.monitoring('uci_bank_marketing')
    save(root / 'results/service_demo.json', {'batches': summaries, 'bank_monitoring_rows': len(monitoring),
        'events': service.db.execute('SELECT count(*) FROM events').fetchone()[0],
        'findings': service.db.execute('SELECT count(*) FROM findings').fetchone()[0],
        'exceptions_exercised': bool(first), 'governance': 'Local attributed-actor simulation; no authentication/RBAC',
        'qualification_fixture': 'Synthetic clean fixture for lifecycle test only; no real deployment recommendation'})
    save(root / 'results/local/bank_monitoring.json', monitoring)
    service.close()
    return summaries


def run_all(root):
    root = Path(root)
    if (root / 'results/run_manifest.json').exists():
        raise ValueError('Completed run exists; verify it rather than overwrite scientific evidence')
    started = time.monotonic()
    from .robustness import run_robustness
    freeze(root)
    outcomes = {}
    for name, function in [('regular', regular), ('published_pairs', pairs), ('sec_baseline', sec_baseline),
                           ('service_demo', service_demo), ('robustness', run_robustness)]:
        try:
            result = function(root)
            outcomes[name] = {'status': 'COMPLETE', 'records': len(result)}
        except Exception as e:
            outcomes[name] = {'status': 'FAILED', 'reason': f'{type(e).__name__}: {e}'}
            save(root / f'results/attempts/{name}_failure.json', outcomes[name])
    outcomes.update({name: {'status': 'NOT_RUN', 'reason': 'No explicit inference spend authorization or configured model'}
                     for name in ['B_live_detection', 'C_generated_rules', 'D_validated_generated_rules', 'C_vs_D']})
    save(root / 'results/run_manifest.json', {'timestamp': now(), 'outcomes': outcomes,
         'runtime_seconds': time.monotonic() - started,
         'artifacts': {str(p.relative_to(root)): sha(p) for p in sorted((root / 'results').glob('*.json'))
                       if p.name != 'run_manifest.json'}})
    return outcomes
