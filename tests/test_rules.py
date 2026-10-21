import sqlite3
from dataclasses import asdict

import pandas as pd
import pytest

from dqpilot.rules import Engine, Rule, compile_rule, number, qualify, read_sql_source


@pytest.mark.parametrize('value,expected', [('$1,234.50', 1234.5), ('(3)', -3), ('1.0', 1),
                                           ('12,34', None), ('nan', None), ('1e999', None),
                                           ('3e2', 300), ('—', None), ('', None)])
def test_number(value, expected):
    assert number(value) == expected


def test_rules_execute_and_localize():
    frame = pd.DataFrame({'a': ['1', 'bad', ''], 'b': ['0', '2', '3'], 'key': ['a', 'a', 'b']})
    with Engine(frame) as e:
        assert e.execute(Rule('n', 'not_null', ['a'])) == {(2, 'a')}
        assert e.execute(Rule('t', 'numeric', ['a'])) == {(1, 'a')}
        assert e.execute(Rule('r', 'range', ['b'], {'max': 1})) == {(1, 'b'), (2, 'b')}
        assert e.execute(Rule('c', 'less_equal', ['a', 'b'])) == {(0, 'a'), (0, 'b')}
        assert e.execute(Rule('k', 'unique', ['key'])) == {(0, 'key'), (1, 'key')}
        assert e.execute(Rule('v', 'allowed', ['key'], {'values': ['b']})) == {(0, 'key'), (1, 'key')}
        with pytest.raises(sqlite3.DatabaseError):
            e.conn.execute('DROP TABLE records')
        with pytest.raises(sqlite3.DatabaseError):
            e.conn.execute("SELECT load_extension('bad')")


def test_reconciliation_and_functional_dependency():
    frame = pd.DataFrame({'total': [4, 5], 'a': [2, 2], 'b': [2, 2], 'key': ['x', 'x']})
    with Engine(frame) as e:
        assert e.execute(Rule('rec', 'reconcile', ['total', 'a', 'b'])) == {(1, c) for c in ['total', 'a', 'b']}
        assert e.execute(Rule('fd', 'fd', ['key', 'total'])) == {(i, c) for i in [0, 1] for c in ['key', 'total']}


@pytest.mark.parametrize('candidate', [
    {'id': 'x', 'kind': 'sql', 'columns': ['a'], 'sql': 'DELETE FROM records'},
    {'id': 'x', 'kind': 'range', 'columns': ['a'], 'parameters': {'min': 10, 'max': 0}},
    {'id': 'x', 'kind': 'range', 'columns': ['a'], 'parameters': {'min': float('inf')}},
    {'id': 'x', 'kind': 'allowed', 'columns': ['a'], 'parameters': {'values': []}},
    {'id': 'x', 'kind': 'less_equal', 'columns': ['a']},
])
def test_bad_rules_rejected(candidate):
    with pytest.raises((ValueError, TypeError)):
        Rule.parse(candidate)


def test_identifier_and_bound_parameter_safety():
    column = 'a"; DROP TABLE records; --'
    frame = pd.DataFrame({column: ['x', 'y']})
    rule = Rule('x', 'allowed', [column], {'values': ["x' OR 1=1 --"]})
    sql, params = compile_rule(rule, frame.columns)
    assert "x' OR" not in sql
    assert params == ["x' OR 1=1 --"]
    with Engine(frame) as e:
        assert len(e.execute(rule)) == 2


def test_qualification_same_candidates_and_whitespace():
    candidate = asdict(Rule('ok', 'range', ['a'], {'min': 0}, evidence='Documented nonnegative count', origin='LLM'))
    duplicate = dict(candidate, id='duplicate')
    invalid = dict(candidate, columns=['unknown'])
    absent_evidence = dict(candidate, id='unsupported', evidence='', parameters={'max': 5})
    decisions = qualify([candidate, duplicate, invalid, absent_evidence], pd.DataFrame({'a': [1, 2, 3]}))
    assert [d['state'] for d in decisions] == ['VALIDATED', 'REJECTED', 'REJECTED', 'REJECTED']
    assert [d['candidate'] for d in decisions] == [candidate, duplicate, invalid, absent_evidence]
    assert 'duplicate' in decisions[1]['reasons']


def test_high_workload_needs_review_not_false_positive_claim():
    c = asdict(Rule('r', 'range', ['a'], {'max': 1}, evidence='Uncertain threshold'))
    d = qualify([c], pd.DataFrame({'a': [1, 2, 3]}))[0]
    assert d['state'] == 'NEEDS_REVIEW'
    assert d['semantic_validity'] == 'NOT_INDEPENDENTLY_ADJUDICATED'


def test_readonly_sql_connector(tmp_path):
    path = tmp_path / 'source.sqlite'
    with sqlite3.connect(path) as c:
        c.execute('CREATE TABLE source(a TEXT)')
        c.execute("INSERT INTO source VALUES('one')")
    before = path.read_bytes()
    assert read_sql_source(path, 'source')['a'].tolist() == ['one']
    assert path.read_bytes() == before
