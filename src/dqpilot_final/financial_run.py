"""Development-only SEC arithmetic diagnostics and an unfilled independent review packet."""
import csv
from collections import Counter
from pathlib import Path

from dqpilot.common import partition, save, sha
from dqpilot_final.financial import evaluate


def run(root):
    root = Path(root)
    output = root / 'results/final'
    if (output / 'financial_diagnostics.json').exists():
        raise ValueError('Use a fresh checkout/output to preserve completed diagnostics')
    base = '08001'
    assert partition(base) == 'development'
    path = root / 'data/vendor/sec/1000test_1%/08001.csv'
    rows = list(csv.reader(path.open()))
    assert rows[1][0] == '(US$ in millions)' and rows[1][-1] == 'Total'
    contracts, records = [], []
    # Six explicitly headed segment columns, including eliminations; never all table rows.
    # These are analyst proposals, not independent semantic adjudications.
    for label in ['Net sales to external customers', 'Cost of goods sold', 'Gross profit', 'Total assets']:
        contract = {'id': 'sec08001:' + label, 'kind': 'signed_linear_equality',
            'review_state': 'PENDING_INDEPENDENT_HUMAN_ADJUDICATION',
            'evidence': {'table_header_row': 1, 'period_row': 0, 'column_headers': rows[1][1:],
                         'proposal': 'Displayed total versus explicitly headed segments including eliminations'},
            'unit_evidence': {'row': 1, 'text': rows[1][0]},
            'dash_is_zero': True, 'dash_policy_status': 'ANALYST_PROPOSED_REQUIRES_REVIEW',
            # 7 rounded cells, each at most 0.5 million rounding; not an error-rate tuning parameter.
            'absolute_tolerance_base_units': '3500000',
            'terms': [{'row': label, 'column': c, 'coefficient': -1 if c == 7 else 1,
                       'unit': 'USD', 'scale': 1000000} for c in range(1, 8)]}
        contracts.append(contract)
        records.append({'rule_id': contract['id'], 'production_gate': evaluate(rows, contract),
                        'arithmetic_only_diagnostic': evaluate(rows, contract, require_human_approval=False)})
    save(output / 'financial_contract_proposals.json', contracts)
    result = {'status': 'ENGINEERING_DIAGNOSTIC_NOT_SEMANTIC_EVALUATION', 'base_id': base,
              'source_partition': 'development', 'source_sha256': sha(path),
              'rows': len(rows), 'contracts_proposed': len(contracts),
              'independent_reviewers': 0, 'groundtruth_file_read': False, 'reserved_sec_accessed': False,
              'production_status_counts': dict(Counter(r['production_gate']['status'] for r in records)),
              'diagnostic_status_counts': dict(Counter(r['arithmetic_only_diagnostic']['status'] for r in records)),
              'records': records, 'accuracy_or_error_localization_claim': False}
    save(output / 'financial_diagnostics.json', result)
    packet = output / 'semantic_review_packet.csv'
    with packet.open('w', newline='') as f:
        writer = csv.DictWriter(f, lineterminator='\n', fieldnames=['rule_id', 'source_group', 'candidate_origin', 'reviewer_id',
                'validity', 'applicability', 'unit_and_rounding_supported', 'missing_policy_supported',
                'evidence_reference', 'rationale', 'cannot_judge_reason'])
        writer.writeheader()
        for contract in contracts:
            for reviewer in ['R1', 'R2']:
                writer.writerow({'rule_id': contract['id'], 'source_group': base,
                                 'candidate_origin': 'ANALYST_PROPOSAL_NOT_MODEL_OUTPUT', 'reviewer_id': reviewer})
    return result
