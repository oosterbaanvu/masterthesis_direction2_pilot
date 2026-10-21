import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dqpilot_free.pilot import parse_candidates
from dqpilot_free.worker import parse_constructor

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('code', ["__import__('os').system('false')",
    "gx.expectations.ExpectColumnValuesToNotBeNull(column=__import__('os'))",
    "gx.expectations.ExpectQueryResultsToMatchComparison(query='SELECT 1')",
    "gx.expectations.ExpectColumnValuesToNotBeNull(**kwargs)"])
def test_no_arbitrary_generated_code_execution(code):
    with pytest.raises((ValueError, SyntaxError)):
        parse_constructor(code, ['x'])


def test_unknown_source_column_does_not_execute():
    with pytest.raises(ValueError, match='SCHEMA_INCOMPATIBLE'):
        parse_constructor("gx.expectations.ExpectColumnValuesToNotBeNull(column='prediction_target')", ['x'])


def test_truncated_output_is_not_a_successful_candidate_set():
    response = {'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': [{'text': '{"rules": []}'}]}}]}
    with pytest.raises(ValueError, match='TRUNCATED'):
        parse_candidates(response)


def test_prepared_inputs_send_no_actual_customer_records():
    prepared = json.loads((ROOT / 'results/free_gemini/prepared_inputs.json').read_text())
    assert prepared['requests_planned'] == 48
    for source in ['uci_credit', 'uci_bank_marketing', 'uci_wine_white']:
        assert prepared['source_contexts'][source]['sample'] == []
        assert prepared['source_contexts'][source]['raw_rows_transmitted'] is False
    assert not any(c['name'] in {'quality', 'y', 'default payment next month'}
                   for c in prepared['source_contexts']['uci_credit']['schema'])


def test_real_gx_resource_bounded_worker_on_software_fixture():
    payload = {'records': [{'x': 1}, {'x': None}], 'columns': ['x'],
               'candidates': [{'id': 'SOFTWARE_FIXTURE_NOT_MODEL',
                               'gx_code': "gx.expectations.ExpectColumnValuesToNotBeNull(column='x')"}],
               'original_evaluator': str(ROOT / 'data/vendor/ledqer/rule_eval/evaluate_rules.py')}
    environment = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    result = subprocess.run([sys.executable, '-m', 'dqpilot_free.worker'], input=json.dumps(payload),
                            text=True, capture_output=True, timeout=35, cwd=ROOT, env=environment)
    assert result.returncode == 0, result.stderr[-500:]
    outcome = json.loads(result.stdout)[0]
    assert outcome['status'] == 'EXECUTED' and outcome['unexpected_count'] == 1
    assert outcome['semantic_validity'] == 'NOT_ADJUDICATED'
