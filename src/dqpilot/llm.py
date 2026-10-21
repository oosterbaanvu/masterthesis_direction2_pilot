"""Bounded provider adapter. No credentials or paid authorization are inferred."""
import json
import math
import os
import sqlite3
from pathlib import Path

import httpx

from .common import digest, now

GENERATION_PROMPT = '''Propose data-quality rules using ONLY the supplied schema, source semantics and
unlabelled development sample. Return JSON {"rules": [...]} with id, kind, columns, parameters,
evidence, origin="LLM". Allowed kinds: not_null, numeric, range, allowed, unique, less_equal,
reconcile, implication, fd. Never return SQL or Python. Cite supplied source evidence for each rule.
Do not assume financial totals reconcile without documented component semantics. Do not use filenames
as labels. Abstain when unsupported. All rules are proposals requiring independent approval.'''
DETECTION_PROMPT = '''Inspect the supplied anonymous CSV table for logical inconsistencies.
Return JSON with errNum (nonnegative integer), missNum (nonnegative integer), errType (subset of
[VAL,FMT,MISS]) and errLoc ([{row_name: string, col_idx: integer}]). Column 0 is the first CSV field;
data columns start at 1. Include all visibly implicated constraint participants, not just a blamed
component. Empty presentation cells are not automatically missing errors. Do not assume arithmetic
relationships without support. No ground-truth, clean-table or filename information is provided.'''


class BlockedInference(RuntimeError):
    pass


class Provider:
    def __init__(self, config, ledger, explicitly_authorized=False):
        self.config = config
        self.authorized = explicitly_authorized
        for name in ['max_spend_usd', 'input_price_usd_per_million', 'output_price_usd_per_million']:
            value = config.get(name)
            if value is not None and (type(value) not in {int, float} or not math.isfinite(value) or value < 0):
                raise ValueError('Invalid nonnegative finite price or budget')
        if type(config.get('max_calls')) is not int or config['max_calls'] < 0:
            raise ValueError('Invalid call cap')
        if type(config.get('max_output_tokens')) is not int or not 1 <= config['max_output_tokens'] <= 100000:
            raise ValueError('Invalid output token cap')
        Path(ledger).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(ledger)
        self.db.execute('''CREATE TABLE IF NOT EXISTS calls(
            hash TEXT PRIMARY KEY, status TEXT, reserve REAL, actual REAL,
            created TEXT, metadata TEXT, response TEXT)''')

    def estimate(self, prompt):
        c = self.config
        if c.get('input_price_usd_per_million') is None or c.get('output_price_usd_per_million') is None:
            raise BlockedInference('Configure reviewed model prices before estimating or calling')
        # UTF-8 bytes plus envelope overhead conservatively bound ordinary text tokenization.
        bound = len(prompt.encode('utf-8')) + 2048
        output = c['max_output_tokens']
        cost = (bound * c['input_price_usd_per_million'] + output * c['output_price_usd_per_million']) / 1e6
        return {'input_token_upper_bound': bound, 'output_token_limit': output, 'reserved_usd': cost}

    def infer(self, context, task='generate'):
        c = self.config
        if task not in {'generate', 'detect'}:
            raise ValueError('Unknown task')
        if not self.authorized or not c.get('enabled'):
            raise BlockedInference('No explicit paid-inference authorization')
        if context.get('data_classification') != 'public_unrestricted':
            raise BlockedInference('Only explicitly classified unrestricted public context is accepted')
        key = os.environ.get(c['api_key_variable'])
        base = os.environ.get(c['base_url_variable'], '')
        if not key or not base.startswith('https://') or not c.get('model'):
            raise BlockedInference('Missing model, HTTPS endpoint or inference credential')
        # Context is allowlisted; filenames, partitions, annotations and reference tables cannot pass.
        permitted = {'data_classification', 'schema', 'source_semantics', 'sample', 'csv'}
        if set(context) - permitted:
            raise ValueError('Disallowed model context keys')
        system = GENERATION_PROMPT if task == 'generate' else DETECTION_PROMPT
        prompt = system + '\n' + json.dumps(context, ensure_ascii=False)
        request = {'model': c['model'], 'temperature': c['temperature'], 'max_tokens': c['max_output_tokens'],
                   'messages': [{'role': 'user', 'content': prompt}], 'response_format': {'type': 'json_object'}}
        fingerprint = digest({'endpoint': base, 'request': request, 'task': task})
        cached = self.db.execute('SELECT status,response FROM calls WHERE hash=?', (fingerprint,)).fetchone()
        if cached:
            if cached[0] == 'COMPLETE':
                return json.loads(cached[1])
            raise BlockedInference('Prior failed/in-flight call retained; no automatic duplicate paid call')
        estimate = self.estimate(prompt)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            count, reserved = self.db.execute('SELECT count(*),coalesce(sum(reserve),0) FROM calls').fetchone()
            if count >= c['max_calls'] or reserved + estimate['reserved_usd'] > c['max_spend_usd']:
                raise BlockedInference('Call or spend cap would be exceeded')
            # Unique key and transaction reserve budget before any network request.
            self.db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?)',
                            (fingerprint, 'RESERVED', estimate['reserved_usd'], None, now(),
                             json.dumps({'model': c['model'], 'parameters': request, 'estimate': estimate}), None))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        try:
            with httpx.Client(verify=__import__('dqpilot.acquisition', fromlist=['tls_context']).tls_context(),
                              timeout=90, follow_redirects=False) as client:
                response = client.post(base.rstrip('/') + '/chat/completions', json=request,
                                       headers={'Authorization': f'Bearer {key}'})
                response.raise_for_status()
                payload = response.json()
            usage = payload.get('usage', {})
            actual = None
            if 'prompt_tokens' in usage and 'completion_tokens' in usage:
                actual = (usage['prompt_tokens'] * c['input_price_usd_per_million'] +
                          usage['completion_tokens'] * c['output_price_usd_per_million']) / 1e6
            payload['pilot_metadata'] = {'hash': fingerprint, 'usage': usage, 'actual_cost_usd': actual,
                                         'reservation': estimate, 'model_returned': payload.get('model')}
            self.db.execute('UPDATE calls SET status=?,actual=?,response=? WHERE hash=?',
                            ('COMPLETE', actual, json.dumps(payload), fingerprint))
            self.db.commit()
            return payload
        except Exception as e:
            # Do not retain HTTP messages that might echo a credential or supplied data.
            self.db.execute('UPDATE calls SET status=? WHERE hash=?', ('FAILED_' + type(e).__name__, fingerprint))
            self.db.commit()
            raise BlockedInference('Inference failed; reservation preserved, see local call status') from None

    def close(self):
        self.db.close()
