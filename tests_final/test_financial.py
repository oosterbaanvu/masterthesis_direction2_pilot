from copy import deepcopy
from decimal import Decimal

import pytest

from dqpilot_final.financial import FinancialInputError, amount, evaluate


def contract():
    return {'id': 'SOFTWARE_TEST_FIXTURE', 'kind': 'signed_linear_equality',
            'review_state': 'ENGINEERING_FIXTURE_NOT_HUMAN_REVIEW',
            'evidence': 'Synthetic software fixture', 'unit_evidence': 'Synthetic USD millions header',
            'absolute_tolerance_base_units': '0', 'terms': [
                {'row': 'revenue', 'column': 1, 'coefficient': 1, 'unit': 'USD', 'scale': 1000000},
                {'row': 'expense', 'column': 1, 'coefficient': -1, 'unit': 'USD', 'scale': 1000000},
                {'row': 'profit', 'column': 1, 'coefficient': -1, 'unit': 'USD', 'scale': 1000000}]}


@pytest.mark.parametrize('text,want', [('$1,234', '1234'), ('(1,234)', '-1234'),
    ('$(163)', '-163'), ('($163)', '-163'), ('-2.5', '-2.5'), ('0', '0')])
def test_accounting_amount(text, want):
    assert amount(text) == Decimal(want)


@pytest.mark.parametrize('text', ['23%', '1,23', '', 'NaN', 'Infinity', '—', '(-2)', '(+2)'])
def test_ambiguous_amount_not_guessed(text):
    with pytest.raises(FinancialInputError):
        amount(text)


def test_unreviewed_contract_cannot_activate():
    result = evaluate([['revenue', '10'], ['expense', '8'], ['profit', '3']], contract())
    assert result['status'] == 'NEEDS_REVIEW' and not result['detection_claim']


def test_signed_cross_row_and_actual_coordinates():
    rows = [['revenue', '10'], ['expense', '12'], ['profit', '(2)']]
    result = evaluate(rows, contract(), require_human_approval=False)
    assert result['status'] == 'SATISFIED' and result['residual_base_units'] == '0'
    assert [p['row_offset'] for p in result['participants']] == [0, 1, 2]
    assert not result['detection_claim']


def test_rounding_and_scale_are_explicit():
    rule = contract()
    rule['absolute_tolerance_base_units'] = '1500000'
    rows = [['revenue', '10'], ['expense', '8'], ['profit', '3']]
    assert evaluate(rows, rule, False)['status'] == 'SATISFIED'
    rule['absolute_tolerance_base_units'] = '499999'
    assert evaluate(rows, rule, False)['status'] == 'VIOLATION'


def test_repeated_labels_require_explicit_occurrence():
    rows = [['revenue', '10'], ['expense', '8'], ['profit', '2'], ['profit', '7']]
    rule = contract()
    assert evaluate(rows, rule, False)['reason'] == 'ROW_MISSING_OR_AMBIGUOUS'
    rule['terms'][2]['occurrence'] = 0
    assert evaluate(rows, rule, False)['status'] == 'SATISFIED'


@pytest.mark.parametrize('field,value', [('scale', 'NaN'), ('scale', '-1'), ('coefficient', 'Infinity'), ('coefficient', '0')])
def test_invalid_numeric_contract_is_unresolved(field, value):
    rule = deepcopy(contract())
    rule['terms'][0][field] = value
    assert evaluate([], rule, False)['status'] == 'UNRESOLVED'


def test_incompatible_units_rejected():
    rule = contract()
    rule['terms'][1]['unit'] = 'EUR'
    assert evaluate([], rule, False)['reason'] == 'INCOMPATIBLE_UNITS'


def test_dash_requires_documented_policy():
    assert amount('—', dash_is_zero=True) == 0
