import json
import subprocess
import sys
from dataclasses import asdict

import pandas as pd

from dqpilot.acquisition import write_verified
from dqpilot.common import sha
from dqpilot.comparison import compare_candidates
from dqpilot.rules import Rule


def test_complete_cli_csv_pipeline(tmp_path):
    data = tmp_path / 'source.csv'
    data.write_text('amount\n10\n-5\n')
    spec = tmp_path / 'rules.json'
    spec.write_text(json.dumps([asdict(Rule('nonnegative', 'range', ['amount'], {'min': 0},
                                           'Documented positive payments'))]))
    result = tmp_path / 'findings.json'
    r = subprocess.run([sys.executable, '-m', 'dqpilot.cli', 'scan', '--csv', str(data),
                        '--rules', str(spec), '--output', str(result)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    findings = json.loads(result.read_text())['findings']
    assert findings == [{'row': 1, 'column': 'amount', 'rule': 'nonnegative', 'evidence': 'Documented positive payments'}]


def test_cd_frozen_candidate_evaluation_is_fixture_not_llm_result():
    candidates = [asdict(Rule('useful', 'range', ['a'], {'min': 0}, 'Nonnegative contract', 'HUMAN_FIXTURE')),
                  asdict(Rule('overstrict', 'range', ['a'], {'max': 0}, 'Unsupported narrow claim', 'HUMAN_FIXTURE'))]
    before = json.dumps(candidates)
    result = compare_candidates(candidates, pd.DataFrame({'a': [1, 2, 3]}),
                                pd.DataFrame({'a': [1, -1, 2]}), {(1, 'a')})
    assert result['C']['tp'] == result['D']['tp'] == 1
    assert result['C']['fp'] == 2 and result['D']['fp'] == 0
    assert result['acceptance_count'] == 1
    assert json.dumps(candidates) == before


def test_acquisition_integrity_and_readonly(tmp_path):
    import hashlib
    import pytest
    data = b'source,value\na,1\n'
    expected = hashlib.sha256(data).hexdigest()
    p = tmp_path / 'raw.csv'
    write_verified(p, data, expected)
    assert sha(p) == expected
    assert p.stat().st_mode & 0o222 == 0
    write_verified(p, data, expected)
    with pytest.raises(ValueError):
        write_verified(tmp_path / 'bad.csv', b'corrupt', expected)
    assert not (tmp_path / 'bad.csv').exists()


def test_numeric_injection_labels_require_semantic_change():
    from dqpilot.experiments import actual_change
    assert not actual_change(0, 0.0, numeric=True)
    assert not actual_change('10', '10.0', numeric=True)
    assert actual_change(10, 100.0, numeric=True)
    assert actual_change(10, None, numeric=True)
    assert actual_change(10, 'NOT_A_NUMBER', numeric=True)
    assert not actual_change(None, '', numeric=True)
    assert actual_change('001', '1', numeric=False)
