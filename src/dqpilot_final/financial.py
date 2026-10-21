"""Bounded signed linear financial constraints with explicit coordinates and units."""
import re
from decimal import Decimal, InvalidOperation


class FinancialInputError(ValueError):
    pass


def amount(text, dash_is_zero=False):
    if text is None or str(text).strip() == '':
        raise FinancialInputError('MISSING_INPUT')
    s = str(text).replace('\u00a0', ' ').strip()
    if '%' in s:
        raise FinancialInputError('PERCENT_IS_NOT_A_CURRENCY_AMOUNT')
    s = s.removeprefix('$').strip()
    if s in {'—', '–', '-'}:
        if dash_is_zero:
            return Decimal(0)
        raise FinancialInputError('DASH_ZERO_POLICY_UNSPECIFIED')
    negative = s.startswith('(') and s.endswith(')')
    if negative:
        s = s[1:-1].strip().removeprefix('$').strip()
        if s.startswith(('+', '-')):
            raise FinancialInputError('AMBIGUOUS_SIGN_INSIDE_PARENTHESES')
    if not re.fullmatch(r'[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?', s):
        raise FinancialInputError('UNRECOGNIZED_ACCOUNTING_FORMAT')
    try:
        value = Decimal(s.replace(',', ''))
        return -value if negative else value
    except InvalidOperation:
        raise FinancialInputError('INVALID_DECIMAL') from None


def resolve(rows, reference):
    matches = [(i, r) for i, r in enumerate(rows) if r and r[0] == reference['row']]
    occurrence = reference.get('occurrence')
    if occurrence is None:
        if len(matches) != 1:
            raise FinancialInputError('ROW_MISSING_OR_AMBIGUOUS')
        offset, row = matches[0]
    elif type(occurrence) is int and 0 <= occurrence < len(matches):
        offset, row = matches[occurrence]
    else:
        raise FinancialInputError('INVALID_ROW_OCCURRENCE')
    col = reference['column']
    if type(col) is not int or col < 1 or col >= len(row):
        raise FinancialInputError('COLUMN_OUTSIDE_DATA_FIELDS')
    return offset, col, row[col]


def validate_contract(contract):
    if contract.get('kind') != 'signed_linear_equality':
        raise FinancialInputError('UNSUPPORTED_FINANCIAL_STRUCTURE')
    if not contract.get('evidence') or not contract.get('unit_evidence'):
        raise FinancialInputError('MISSING_SEMANTIC_OR_UNIT_EVIDENCE')
    terms = contract.get('terms', [])
    if not 2 <= len(terms) <= 32:
        raise FinancialInputError('BOUNDED_TERM_COUNT_REQUIRED')
    units = {t['unit'] for t in terms}
    if len(units) != 1:
        raise FinancialInputError('INCOMPATIBLE_UNITS')
    for term in terms:
        scale = Decimal(str(term['scale']))
        coefficient = Decimal(str(term['coefficient']))
        if not scale.is_finite() or scale <= 0:
            raise FinancialInputError('INVALID_SCALE')
        if not coefficient.is_finite() or coefficient == 0:
            raise FinancialInputError('INVALID_COEFFICIENT')
    tolerance = Decimal(str(contract['absolute_tolerance_base_units']))
    if not tolerance.is_finite() or tolerance < 0:
        raise FinancialInputError('INVALID_ROUNDING_TOLERANCE')


def evaluate(rows, contract, require_human_approval=True):
    result = {'rule_id': contract['id'], 'review_state': contract.get('review_state'),
              'evidence': contract.get('evidence'), 'participants': []}
    try:
        validate_contract(contract)
        if require_human_approval and contract.get('review_state') != 'APPROVED_BY_INDEPENDENT_REVIEWER':
            result.update(status='NEEDS_REVIEW', detection_claim=False)
            return result
        residual = Decimal(0)
        for term in contract['terms']:
            row, col, value = resolve(rows, term)
            parsed = amount(value, contract.get('dash_is_zero', False))
            contribution = parsed * Decimal(str(term['scale'])) * Decimal(str(term['coefficient']))
            residual += contribution
            result['participants'].append({'row_offset': row, 'row_label': term['row'], 'column': col,
                                           'unit': term['unit'], 'scale': term['scale'],
                                           'coefficient': term['coefficient'], 'contribution': str(contribution)})
        tolerance = Decimal(str(contract['absolute_tolerance_base_units']))
        result.update(status='VIOLATION' if abs(residual) > tolerance else 'SATISFIED',
                      residual_base_units=str(residual), tolerance_base_units=str(tolerance),
                      detection_claim=require_human_approval)
    except (FinancialInputError, KeyError, InvalidOperation) as e:
        result.update(status='UNRESOLVED', reason=str(e), detection_claim=False)
    return result
