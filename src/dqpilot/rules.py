"""Small declarative rule language; model SQL/Python is never executed."""
import json
import math
import re
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

from .common import digest

KINDS = {'not_null', 'numeric', 'range', 'allowed', 'unique', 'less_equal', 'reconcile', 'implication', 'fd'}
MISSING = {'', 'na', 'n/a', 'nan', 'null', 'none', '?'}


def missing(value):
    return value is None or str(value).strip().casefold() in MISSING


def number(value):
    if missing(value):
        return None
    s = str(value).strip().replace('\u00a0', ' ').strip()
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1].strip()
    s = re.sub(r'^(-?)\$', r'\1', s)
    s = s.removesuffix('%').strip()
    if not re.fullmatch(r'[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d*)?(?:[eE][+-]?\d+)?', s):
        return None
    try:
        result = float(s.replace(',', ''))
        return result if math.isfinite(result) else None
    except ValueError:
        return None


@dataclass(frozen=True)
class Rule:
    id: str
    kind: str
    columns: list[str]
    parameters: dict = field(default_factory=dict)
    evidence: str = ''
    origin: str = 'CONVENTIONAL'

    @classmethod
    def parse(cls, value):
        if set(value) - {'id', 'kind', 'columns', 'parameters', 'evidence', 'origin'}:
            raise ValueError('Unknown rule keys; arbitrary code and SQL are forbidden')
        rule = cls(**value)
        if not isinstance(rule.id, str) or not rule.id or len(rule.id) > 128:
            raise ValueError('Invalid rule ID')
        if rule.kind not in KINDS:
            raise ValueError('Unsupported rule kind')
        if (not isinstance(rule.columns, list) or not rule.columns or len(rule.columns) > 64
                or any(not isinstance(c, str) for c in rule.columns)):
            raise ValueError('Invalid columns')
        required_count = {'less_equal': 2, 'implication': 2, 'fd': 2}.get(rule.kind)
        if required_count and len(rule.columns) != required_count:
            raise ValueError('Rule requires two columns')
        if rule.kind not in {'less_equal', 'implication', 'fd', 'reconcile'} and len(rule.columns) != 1:
            raise ValueError('Rule requires one column')
        allowed = {'range': {'min', 'max'}, 'allowed': {'values'}, 'less_equal': {'tolerance'},
                   'reconcile': {'tolerance'}, 'implication': {'if_value', 'then_value'}}.get(rule.kind, set())
        if not isinstance(rule.parameters, dict) or set(rule.parameters) - allowed:
            raise ValueError('Unknown parameters')
        for k, v in rule.parameters.items():
            if k in {'min', 'max', 'tolerance'} and (type(v) not in {float, int} or not math.isfinite(v)):
                raise ValueError('Nonfinite/nonnumeric threshold')
        if rule.parameters.get('tolerance', 0) < 0:
            raise ValueError('Tolerance must be nonnegative')
        if rule.kind == 'range' and not rule.parameters:
            raise ValueError('Range requires a bound')
        if rule.kind == 'range' and rule.parameters.get('min', -math.inf) > rule.parameters.get('max', math.inf):
            raise ValueError('Contradictory range')
        if rule.kind == 'allowed' and (not isinstance(rule.parameters.get('values'), list)
                                       or not rule.parameters['values'] or len(rule.parameters['values']) > 1000):
            raise ValueError('Allowed values require a bounded list')
        if rule.kind == 'reconcile' and len(rule.columns) < 3:
            raise ValueError('Total and at least two component columns required')
        if rule.kind == 'implication' and set(rule.parameters) != {'if_value', 'then_value'}:
            raise ValueError('Implication requires two values')
        if not isinstance(rule.evidence, str) or not isinstance(rule.origin, str):
            raise ValueError('Evidence/origin must be text')
        return rule

    @property
    def signature(self):
        params = dict(self.parameters)
        if 'values' in params:
            params['values'] = sorted({str(x).strip() for x in params['values']})
        return digest({'kind': self.kind, 'columns': self.columns, 'parameters': params})


def quote(identifier):
    if not isinstance(identifier, str) or '\x00' in identifier:
        raise ValueError('Invalid SQL identifier')
    return '"' + identifier.replace('"', '""') + '"'


def compile_rule(rule, columns):
    rule = Rule.parse(asdict(rule))
    if not set(rule.columns) <= set(columns):
        raise ValueError('Unknown schema column')
    cols = [quote(c) for c in rule.columns]
    c = cols[0]
    p = rule.parameters
    params = []
    if rule.kind == 'not_null':
        predicate = f'dq_missing({c}) = 1'
    elif rule.kind == 'numeric':
        predicate = f'dq_missing({c}) = 0 AND dq_number({c}) IS NULL'
    elif rule.kind == 'range':
        terms = []
        for bound, op in [('min', '<'), ('max', '>')]:
            if bound in p:
                terms.append(f'dq_number({c}) {op} ?')
                params.append(p[bound])
        predicate = '(' + ' OR '.join(terms) + ')'
    elif rule.kind == 'allowed':
        params = [str(x).strip() for x in p['values']]
        predicate = f'dq_missing({c}) = 0 AND trim({c}) NOT IN ({",".join("?" for _ in params)})'
    elif rule.kind == 'unique':
        predicate = f'{c} IN (SELECT {c} FROM records GROUP BY {c} HAVING count(*) > 1)'
    elif rule.kind == 'less_equal':
        predicate = f'dq_number({cols[0]}) > dq_number({cols[1]}) + ?'
        params = [p.get('tolerance', 0)]
    elif rule.kind == 'reconcile':
        terms = '+'.join(f'dq_number({x})' for x in cols[1:])
        predicate = f'abs(dq_number({c}) - ({terms})) > ?'
        params = [p.get('tolerance', 0.01)]
    elif rule.kind == 'implication':
        predicate = f'trim({c}) = ? AND (dq_missing({cols[1]}) = 1 OR trim({cols[1]}) != ?)'
        params = [str(p['if_value']), str(p['then_value'])]
    elif rule.kind == 'fd':
        predicate = f'{c} IN (SELECT {c} FROM records GROUP BY {c} HAVING count(DISTINCT {cols[1]}) > 1)'
    else:
        raise ValueError('Unsupported rule')
    return f'SELECT _dq_row FROM records WHERE {predicate}', params


def read_authorizer(allowed_table='records'):
    def authorize(action, arg1, arg2, database, trigger):
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ and arg1 == allowed_table:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and arg2 in {'dq_number', 'dq_missing', 'abs', 'trim', 'count'}:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    return authorize


class Engine:
    def __init__(self, frame, timeout=10):
        if '_dq_row' in frame.columns or len(set(frame.columns)) != len(frame.columns):
            raise ValueError('Duplicate/reserved source column')
        self.frame = frame.reset_index(drop=True)
        self.timeout = timeout
        self.conn = sqlite3.connect(':memory:')
        table = self.frame.astype('string').where(self.frame.notna(), None).copy()
        table.insert(0, '_dq_row', range(len(table)))
        table.to_sql('records', self.conn, index=False)
        self.conn.create_function('dq_number', 1, number, deterministic=True)
        self.conn.create_function('dq_missing', 1, lambda x: int(missing(x)), deterministic=True)
        self.conn.execute('PRAGMA query_only=ON')
        self.conn.set_authorizer(read_authorizer())

    def execute(self, rule):
        sql, params = compile_rule(rule, self.frame.columns)
        deadline = time.monotonic() + self.timeout
        self.conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        rows = [r[0] for r in self.conn.execute(sql, params)]
        # Multi-column rules localize implicated cells, not a proven wrong component.
        return {(int(i), c) for i in rows for c in rule.columns}

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def read_sql_source(path, table):
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    with sqlite3.connect(uri, uri=True) as c:
        c.execute('PRAGMA query_only=ON')
        c.set_authorizer(read_authorizer(table))
        deadline = time.monotonic() + 10
        c.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        return pd.read_sql_query(f'SELECT * FROM {quote(table)}', c)


def qualify(candidates, development, max_alert_fraction=0.01):
    seen, decisions = set(), []
    with Engine(development) as engine:
        # Harmless surrounding whitespace is the predeclared representation perturbation.
        formatted = development.map(lambda v: f' {v} ' if not missing(v) else v)
        with Engine(formatted) as alternate:
            for candidate in candidates:
                result = {'candidate': candidate, 'state': 'REJECTED', 'reasons': []}
                try:
                    rule = Rule.parse(candidate)
                    compile_rule(rule, development.columns)
                    if rule.signature in seen:
                        result['reasons'].append('duplicate')
                    seen.add(rule.signature)
                    if not rule.evidence.strip():
                        result['reasons'].append('missing_source_evidence')
                    flags = engine.execute(rule)
                    if flags != alternate.execute(rule):
                        result['reasons'].append('formatting_sensitive')
                    fraction = len(flags) / max(1, len(development) * len(rule.columns))
                    result.update(executed=True, alerts=len(flags), alert_fraction=fraction)
                    if fraction > max_alert_fraction:
                        result['reasons'].append('excess_unlabelled_alerts')
                    if not result['reasons']:
                        result['state'] = 'VALIDATED'
                    elif result['reasons'] == ['excess_unlabelled_alerts']:
                        result['state'] = 'NEEDS_REVIEW'
                    result['semantic_validity'] = 'NOT_INDEPENDENTLY_ADJUDICATED'
                except (ValueError, TypeError, sqlite3.Error) as e:
                    result['reasons'].append(f'{type(e).__name__}: {e}')
                decisions.append(result)
    return decisions


def load_rules(path):
    return [Rule.parse(r) for r in json.loads(Path(path).read_text())]
