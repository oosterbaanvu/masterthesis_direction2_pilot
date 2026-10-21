"""Audit a released research snapshot; no model calls or human labels are invented."""
import csv
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

from dqpilot.common import save, sha
from dqpilot_final.financial import FinancialInputError, amount


def markdown_tables(text):
    tables = []
    for block in re.split(r'^#{2,3} ', text, flags=re.MULTILINE)[1:]:
        lines = block.splitlines()
        title = lines[0].strip()
        rows = []
        for line in lines[1:]:
            if line.startswith('|'):
                fields = [s.strip() for s in line.strip().strip('|').split('|')]
                if all(re.fullmatch(r'[-:]+', s or '-') for s in fields):
                    continue
                rows.append(fields)
        tables.append({'title': title, 'rows': rows})
    return tables


def explicit_balance(table):
    """Display-unit arithmetic diagnostic. Missing currency/scale forbids deployment."""
    values = {}
    mezzanine = []
    for row in table['rows'][1:]:
        if len(row) != 4:
            return {'status': 'UNRESOLVED_LAYOUT'}
        section, _, label, value = row
        key = label.casefold()
        if key in {'total assets', 'total liabilities', 'total equity'}:
            if key in values:
                return {'status': 'UNRESOLVED_DUPLICATE_TOTAL'}
            try:
                values[key] = amount(value)
            except FinancialInputError:
                return {'status': 'UNRESOLVED_NUMERIC_FORMAT'}
        if section == 'Mezzanine_Equity':
            mezzanine.append(value)
    if len(values) != 3 or len(mezzanine) > 1:
        return {'status': 'UNRESOLVED_TOTAL_SCOPE'}
    try:
        redeemable = amount(mezzanine[0]) if mezzanine else Decimal(0)
    except FinancialInputError:
        return {'status': 'UNRESOLVED_MEZZANINE_FORMAT'}
    residual = values['total assets'] - values['total liabilities'] - values['total equity'] - redeemable
    return {'status': 'DISPLAY_EQUATION_SATISFIED' if residual == 0 else 'DISPLAY_EQUATION_VIOLATION',
            'residual_display_units': str(residual), 'included_mezzanine': bool(mezzanine),
            'absolute_tolerance_display_units': '0', 'unit_and_rounding_independently_verified': False,
            'semantic_validity_claim': False}


def audit(root):
    root = Path(root)
    source = root / 'data/raw/finrule_bench'
    manifest = json.loads((root / 'results/final/finrule_acquisition.json').read_text())
    for item in manifest['files']:
        if sha(source / item['path']) != item['sha256']:
            raise ValueError('FinRule snapshot integrity mismatch')
    counts, balances = [], []
    for path in sorted(source.glob('data/single_rule_violation/*/*.md')):
        tables = markdown_tables(path.read_text())
        counts.append({'path': path.relative_to(source).as_posix(), 'tables': len(tables),
            'unique_titles': len({t['title'] for t in tables}),
            'issuer_groups': len({t['title'].split(' — ')[0] for t in tables}),
            'schema_shapes': dict(Counter(str(len(row)) for t in tables for row in t['rows']))})
        if path.stem in {'BS-00', 'BS-01'}:
            outcomes = [explicit_balance(t) for t in tables]
            balances.append({'variant': path.stem, 'tables': len(tables),
                'status_counts': dict(Counter(o['status'] for o in outcomes)),
                'role': 'FIXED_PUBLISHED_PRINCIPLE_COMPONENT_NOT_GENERATED_RULE_SELECTION',
                'independent_semantic_precision': 'NOT_MEASURED'})
    summaries = []
    for path in sorted(source.glob('data/single_rule_violation/*/verify_output/*.csv')):
        rows = list(csv.DictReader(path.open()))
        summaries.append({'path': path.relative_to(source).as_posix(), 'rows': len(rows),
            'result_counts': dict(Counter(r.get('result') for r in rows)),
            'meaning': 'UPSTREAM_INJECTION_VERIFICATION_LOG_NOT_OUR_MODEL_DETECTION_ACCURACY'})
    multi = []
    for path in sorted(source.glob('data/multi_rule_violation/*/*truth.json')):
        data = json.loads(path.read_text())
        md = path.with_name(path.name.replace('-truth.json', '.md'))
        titles = [t['title'] for t in markdown_tables(md.read_text())]
        gold = data['ground_truth']
        multi.append({'path': path.relative_to(source).as_posix(), 'truth_records': len(gold),
                      'markdown_tables': len(titles), 'unique_markdown_titles': len(set(titles)),
                      'truth_titles_missing_in_markdown': len(set(gold) - set(titles)),
                      'markdown_titles_missing_in_truth': len(set(titles) - set(gold))})
    result = {'status': 'ACQUIRED_AND_AUDITED_CONDITIONAL_RESEARCH_RESOURCE',
              'snapshot_files': len(manifest['files']), 'snapshot_bytes': sum(f['bytes'] for f in manifest['files']),
              'single_rule_variants': counts, 'multi_rule_integrity': multi,
              'provided_balance_equation_diagnostic': balances, 'upstream_verification_artifacts': summaries,
              'full_original_images_acquired': False, 'all_claimed_deterministic_validator_implementations_found': False,
              'new_model_calls': 0, 'semantic_rule_ground_truth_independently_verified': False,
              'all_inspected_finrule_material_is_exploratory': True, 'reserved_sec_accessed': False}
    save(root / 'results/final/finrule_audit.json', result)
    return result
