import ast
import contextlib
import csv
import io
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from .common import partition, save, sha
from .evaluation import grouped_bootstrap, identifier, locations, score, types


def conditions(sec):
    return sorted(Path(sec).glob('1000test*'))


def groundtruth(directory):
    files = list(Path(directory).glob('groundtruth*.json'))
    if len(files) != 1:
        raise ValueError('Expected one ground-truth artifact per condition')
    return json.loads(files[0].read_text())


def table_rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.reader(f))


def audit(root):
    root = Path(root)
    sec = root / 'data/vendor/sec'
    summary, issues, splits, samples = {}, [], {}, []
    id_sets = []
    for directory in conditions(sec):
        gt = groundtruth(directory)
        counts = Counter()
        ids = []
        sample_strata = {}
        references = []
        for g in gt:
            name = g.get('fileName') or g.get('csv_name')
            base = identifier(g)
            ids.append(base)
            splits[base] = partition(base)
            references.append(name)
            file = directory / name
            if not file.is_file():
                issues.append({'condition': directory.name, 'id': base, 'issue': 'missing_csv'})
                continue
            rows = table_rows(file)
            by_name = {}
            for n, row in enumerate(rows):
                if row:
                    by_name.setdefault(row[0], []).append((n, row))
            counts['tables'] += 1
            counts['zero_error_tables'] += int(g['errNum'] == 0)
            counts['positive_tables'] += int(g['errNum'] > 0)
            counts['locations'] += len(g.get('errLoc', []))
            counts['multiline_tables'] += int(any('\n' in c for r in rows for c in r))
            counts['irregular_width_tables'] += int(len({len(r) for r in rows}) > 1)
            counts['duplicate_row_label_tables'] += int(any(len(v) > 1 for v in by_name.values()))
            counts['duplicate_nonempty_row_label_tables'] += int(any(k.strip() and len(v) > 1 for k, v in by_name.items()))
            found = []
            locs = locations(g)
            if len(locs) != len(g['errLoc']):
                found.append('duplicate_annotation_locations')
            if g['errNum'] != len(locs):
                found.append('errNum_location_count_mismatch')
            for field in ['errNum', 'missNum']:
                if type(g[field]) is not int or g[field] < 0:
                    found.append(f'invalid_{field}')
            if g['missNum'] > g['errNum']:
                found.append('missNum_exceeds_errNum')
            if (g['missNum'] > 0) != ('MISS' in types(g)):
                found.append('MISS_type_count_disagreement')
            if not types(g) <= {'MISS', 'VAL', 'FMT'}:
                found.append('unknown_error_type')
            if g['errNum'] == 0 and (locs or types(g) or g['missNum']):
                found.append('inconsistent_zero_example')
            local_examples = []
            for label, col in sorted(locs):
                matching = by_name.get(label, [])
                if not matching:
                    counts['locations_missing_row'] += 1
                    found.append('location_missing_row')
                if len(matching) > 1:
                    counts['locations_ambiguous_row'] += 1
                valid = [(n, r) for n, r in matching if type(col) is int and 0 < col < len(r)]
                if not valid:
                    counts['locations_invalid_column'] += 1
                    found.append('location_invalid_column')
                counts['labelled_blank_locations'] += int(any(not r[col].strip() for _, r in valid))
                local_examples.append({'row_name': label, 'col_idx': col,
                                       'row_offsets': [n for n, _ in valid],
                                       'values': [r[col] for _, r in valid]})
            if found:
                issues.append({'condition': directory.name, 'id': base, 'issues': sorted(set(found))})
            stratum = '_'.join(sorted(types(g))) or 'NONE'
            if partition(base) == 'development':
                sample_strata.setdefault(stratum, (name, g, local_examples))
        csvs = {p.name for p in directory.glob('*.csv')}
        counts['unreferenced_csvs'] = len(csvs - set(references))
        counts['unique_ids'] = len(set(ids))
        counts['duplicate_gt_ids'] = len(ids) - len(set(ids))
        counts['missing_references'] = len(set(references) - csvs)
        summary[directory.name] = dict(counts)
        id_sets.append(set(ids))
        for stratum, (name, g, locs) in sorted(sample_strata.items()):
            samples.append({'condition': directory.name, 'filename': name, 'stratum': stratum,
                            'annotation': g, 'visible_locations': locs})
    result = {'conditions': summary, 'same_base_ids_across_conditions': all(s == id_sets[0] for s in id_sets),
              'partition_counts': dict(Counter(splits.values())), 'issues': issues,
              'split_policy': 'canonical base ID grouped; reserved is not evaluated by new methods',
              'licence_files': [str(p.relative_to(sec)) for p in sec.rglob('*') if 'licen' in p.name.lower()]}
    save(root / 'results/sec_audit.json', result)
    save(root / 'results/sec_splits.json', splits)
    save(root / 'results/local/sec_manual_sample.json', samples)
    return result


def run_original(script, model, gt, result, model_name):
    """Parameterize only path assignments in memory; the official file stays unchanged."""
    tree = ast.parse(Path(script).read_text())
    settings = {'model_name': model_name, 'model_path': str(model), 'gt_path': str(gt), 'result_path': str(result)}
    changed = Counter()
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in settings:
                node.value = ast.Constant(settings[name])
                changed[name] += 1
    if dict(changed) != dict.fromkeys(settings, 1):
        raise ValueError('Official runner structure changed')
    ast.fix_missing_locations(tree)
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        exec(compile(tree, str(script), 'exec'), {'__name__': '__main__'})
    return stream.getvalue()


def reproduce(root):
    root = Path(root)
    sec = root / 'data/vendor/sec'
    official_file = root / 'results/local/official_rerun.csv'
    if official_file.exists():
        raise ValueError('Preserve the existing reproduction; use a fresh results directory for another run')
    official_file.parent.mkdir(parents=True, exist_ok=True)
    summaries, compatibility, grouped = [], [], []
    published = pd.read_csv(sec / 'result/all_model_results.csv').set_index('Model Name')
    for file in sorted((sec / 'result').glob('*.json')):
        condition = file.stem.rsplit('_', 1)[1]
        directory = sec / f'1000test_{condition}'
        gt = groundtruth(directory)
        preds = json.loads(file.read_text())
        log = run_original(sec / 'TestAllModels.py', file, next(directory.glob('groundtruth*.json')),
                           official_file, file.stem)
        (root / f'results/local/{file.stem}.log').write_text(log)
        ours = score(gt, preds, official=True)
        actual = pd.read_csv(official_file).iloc[-1]
        diffs = {k: abs(float(actual[k]) - float(v)) for k, v in ours.items()}
        existing = published.loc[file.stem] if file.stem in published.index else None
        pub_diffs = {k: abs(float(existing[k]) - float(v)) for k, v in ours.items()} if existing is not None else {}
        compatibility.append({'model_artifact': file.name, 'max_difference_official': max(diffs.values()),
                              'max_difference_published_csv': max(pub_diffs.values()) if pub_diffs else None,
                              'different_published_fields': {k: v for k, v in pub_diffs.items() if v > 1e-8},
                              'prediction_sha256': sha(file), 'official_metrics': ours})
        multiplicities = Counter(identifier(p) for p in preds)
        ambiguous_ids = {i for i, n in multiplicities.items() if n > 1}
        # Do not choose an arbitrary conflicting prediction in corrected scoring.
        eligible_gt = [g for g in gt if identifier(g) not in ambiguous_ids]
        eligible_preds = [p for p in preds if identifier(p) not in ambiguous_ids]
        corrected = score(eligible_gt, eligible_preds)
        corrected['excluded_duplicate_prediction_ids'] = sorted(ambiguous_ids)
        corrected['coverage_of_released_tables'] = len(eligible_gt) / len(gt)
        rows = corrected.pop('per_table')
        grouped.extend([{'model': file.stem.rsplit('_', 1)[0], 'condition': condition, **r} for r in rows])
        summaries.append({'artifact': file.name, 'interpretation': 'released outputs rescored, no new inference',
                          **corrected})
    boot = {}
    for model in sorted({r['model'] for r in grouped}):
        boot[model] = grouped_bootstrap([r for r in grouped if r['model'] == model])
    save(root / 'results/sec_reproduction.json', {'official_script_sha256': sha(sec / 'TestAllModels.py'),
                                                'compatibility': compatibility, 'corrected': summaries,
                                                'grouped_location_uncertainty': boot})
    save(root / 'results/local/released_per_table.json', grouped)
    return summaries
