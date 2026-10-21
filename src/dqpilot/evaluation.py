"""Keep official compatibility separate from corrected task metrics."""
from collections import defaultdict

import numpy as np
from sklearn.metrics import f1_score


def types(entry):
    value = entry.get('errType', [])
    return set(filter(None, value.split('_') if isinstance(value, str) else value))


def locations(entry):
    return {(x['row_name'], x['col_idx']) for x in entry.get('errLoc', [])}


def metrics(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {'tp': int(tp), 'fp': int(fp), 'fn': int(fn), 'precision': p, 'recall': r,
            'f1': 2 * p * r / (p + r) if p + r else 0.0}


def cells(predicted, annotated):
    return metrics(len(predicted & annotated), len(predicted - annotated), len(annotated - predicted))


def identifier(entry):
    return (entry.get('csv_name') or entry.get('fileName') or '')[:5]


def score(groundtruth, predictions, official=False):
    gt = {identifier(e): e for e in groundtruth}
    pred = {identifier(e): e for e in predictions}
    if not official and (len(gt) != len(groundtruth) or len(pred) != len(predictions)):
        raise ValueError('Duplicate canonical table ID')
    missing = set(gt) - set(pred)
    if missing and not official:
        raise ValueError(f'Missing predictions: {len(missing)}')
    ids = [i for i in gt if i in pred]
    if not ids:
        raise ValueError('No evaluated tables')
    count = len(ids)
    count_accuracy = miss_accuracy = type_hits = type_den = loc_hits = loc_den = 0
    ious = []
    labels, yt, yp = set(), defaultdict(list), defaultdict(list)
    table = [0, 0, 0]
    missing_table = [0, 0, 0]
    loc_fp = 0
    type_fp = 0
    per_table = []
    for i in ids:
        g, p = gt[i], pred[i]
        for field, accum in [('errNum', table), ('missNum', missing_table)]:
            positive, flagged = g[field] != 0, p[field] != 0
            accum[0] += int(positive and flagged)
            accum[1] += int(not positive and flagged)
            accum[2] += int(positive and not flagged)
        count_accuracy += int(g['errNum'] == p['errNum'])
        miss_accuracy += int(g['missNum'] == p['missNum'])
        raw_types = g.get('errType', [])
        gtypes = (set(raw_types.split('_')) if isinstance(raw_types, str) else set(raw_types)) if official else types(g)
        ptypes = set(p.get('errType', [])) if official else types(p)
        labels.update(gtypes | ptypes)
        # Compatibility preserves the official dynamic-label accumulation bug.
        if official:
            for label in labels:
                yt[label].append(int(label in gtypes))
                yp[label].append(int(label in ptypes))
        type_hits += len(gtypes & ptypes)
        type_den += len(gtypes)
        type_fp += len(ptypes - gtypes)
        gl, pl = locations(g), locations(p)
        intersection, union = len(gl & pl), len(gl | pl)
        loc_hits += intersection
        loc_den += len(gl)
        loc_fp += len(pl - gl)
        ious.append(intersection / union if union else 1.0)
        per_table.append({'id': i, **cells(pl, gl), 'iou': ious[-1]})
    if not official:
        labels = {'VAL', 'FMT', 'MISS'}
        for label in labels:
            yt[label] = [int(label in types(gt[i])) for i in ids]
            yp[label] = [int(label in types(pred[i])) for i in ids]
    macro = sum(f1_score(yt[x], yp[x], zero_division=0) for x in labels) / len(labels) if labels else 0
    tm, mm = metrics(*table), metrics(*missing_table)
    if official:
        return {'errNum Accuracy': count_accuracy / count,
                'errNum Precision': tm['precision'], 'errNum Recall': tm['recall'], 'errNum F1 Score': tm['f1'],
                'missNum Accuracy': miss_accuracy / count,
                'missNum Precision': mm['precision'], 'missNum Recall': mm['recall'], 'missNum F1 Score': mm['f1'],
                'errType Precision': type_hits / type_den if type_den else 0,
                'errType Macro-F1': macro,
                'errLoc Precision': loc_hits / loc_den if loc_den else 0,
                'errLoc Average IoU': sum(ious) / count, 'Total Files Evaluated': count}
    regressions = {}
    for field in ['errNum', 'missNum']:
        truth = np.array([gt[i][field] for i in ids], dtype=float)
        estimate = np.array([pred[i][field] for i in ids], dtype=float)
        ss = float(np.sum((truth - truth.mean()) ** 2))
        regressions[field] = {'mae': float(np.mean(abs(truth - estimate))),
                              'rmse': float(np.sqrt(np.mean((truth - estimate) ** 2))),
                              'r2': 1 - float(np.sum((truth - estimate) ** 2)) / ss if ss else None}
    return {'tables': count, 'table': tm, 'missing_table': mm, 'error_count_accuracy': count_accuracy / count,
            'missing_count_accuracy': miss_accuracy / count, 'type_macro_f1_fixed_labels': macro,
            'type_micro': metrics(type_hits, type_fp, type_den - type_hits),
            'location': metrics(loc_hits, loc_fp, loc_den - loc_hits),
            'mean_location_iou': sum(ious) / count, 'per_table': per_table, 'counts': regressions,
            'missing_predictions': len(missing), 'extra_prediction_ids': len(set(pred) - set(gt))}


def grouped_bootstrap(per_table, repetitions=1000, seed=20261021):
    groups = defaultdict(list)
    for record in per_table:
        groups[record['id']].append(record)
    keys = sorted(groups)
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(repetitions):
        sample = rng.choice(keys, size=len(keys), replace=True)
        rows = [r for k in sample for r in groups[k]]
        values.append(metrics(sum(r['tp'] for r in rows), sum(r['fp'] for r in rows),
                              sum(r['fn'] for r in rows))['f1'])
    return {'independent_unit': 'base_table', 'groups': len(keys), 'repetitions': repetitions,
            'f1_percentiles_2.5_97.5': np.quantile(values, [0.025, 0.975]).tolist()}
