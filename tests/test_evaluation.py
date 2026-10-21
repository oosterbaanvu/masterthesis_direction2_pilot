
import pytest

from dqpilot.common import partition
from dqpilot.evaluation import cells, grouped_bootstrap, score
from dqpilot.sec import table_rows


def entry(i, locs=(), kinds=()):
    return {'fileName': f'{i:05d}.csv', 'errNum': len(locs), 'missNum': 0,
            'errType': list(kinds), 'errLoc': [{'row_name': r, 'col_idx': c} for r, c in locs]}


def test_official_misnamed_precision_is_recall():
    g = [entry(1, [('a', 1), ('b', 1)], ['VAL'])]
    p = [entry(1, [('a', 1), ('z', 1), ('w', 1)], ['VAL'])]
    official, corrected = score(g, p, True), score(g, p)
    assert official['errLoc Precision'] == 0.5
    assert corrected['location']['precision'] == pytest.approx(1 / 3)
    assert corrected['location']['recall'] == 0.5


def test_empty_predictions_and_missing_tables_distinct():
    assert cells(set(), {(1, 'a')})['fn'] == 1
    with pytest.raises(ValueError, match='Missing predictions'):
        score([entry(1)], [])
    with pytest.raises(ValueError, match='Duplicate'):
        score([entry(1)], [entry(1), entry(1)])


def test_fixed_type_labels_count_early_negatives():
    gt = [entry(1), entry(2, [('a', 1)], ['VAL'])]
    pred = [entry(1, [('b', 1)], ['VAL']), entry(2, [('a', 1)], ['VAL'])]
    assert score(gt, pred)['type_micro']['fp'] == 1


def test_official_empty_string_type_preserved_only_for_compatibility():
    gt = [dict(entry(1), errType=''), entry(2, [('a', 1)], ['VAL'])]
    pred = [entry(1), entry(2, [('a', 1)], ['VAL'])]
    assert score(gt, pred, True)['errType Precision'] == 0.5
    assert score(gt, pred)['type_micro']['recall'] == 1


def test_grouped_partitions_and_bootstrap():
    assert len({partition('08002') for _ in range(3)}) == 1
    assert {partition(str(i)) for i in range(1000)} == {'development', 'exploratory', 'reserved'}
    rows = [{'id': '08002', 'tp': 1, 'fp': 0, 'fn': 0}] * 3
    result = grouped_bootstrap(rows, 10)
    assert result['groups'] == 1
    assert result['f1_percentiles_2.5_97.5'] == [1, 1]


def test_multiline_and_duplicate_csv_row_names_fixture(tmp_path):
    p = tmp_path / 'table.csv'
    p.write_text(',"Year\n2024"\nTotal,1\nTotal,2\n')
    assert table_rows(p) == [['', 'Year\n2024'], ['Total', '1'], ['Total', '2']]


def test_normalization_preserves_code_semantics():
    import pandas as pd
    from dqpilot.experiments import normalized_pair
    a = pd.DataFrame({'zip': ['01907'], 'rate': ['0.0'], 'state': ['01']})
    b = pd.DataFrame({'zip': ['1907'], 'rate': ['0'], 'state': ['1']})
    strict, equivalent = normalized_pair('raha_tax', a, b)
    assert strict.sum() == 3
    assert equivalent.sum() == 2


def test_no_filename_or_label_input_in_sec_detector():
    import inspect
    from dqpilot.experiments import sec_lexical
    assert list(inspect.signature(sec_lexical).parameters) == ['rows', 'include_missing']
    assert sec_lexical([['label', '1', '2', '3']])['errNum'] == 0
