"""Fixed Gemini endpoint, explicit free-project gate and durable attempt accounting.

There is no API parameter that forces a billed project's key onto a free tier.
The required confirmation therefore refers to a genuinely non-billed project.
No other provider, model, service tier or retry is selected automatically.
"""
import json
import hashlib
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from dqpilot.acquisition import tls_context
from dqpilot.common import digest, now

BASE = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash'


class FreeInferenceBlocked(RuntimeError):
    pass


class GeminiFree:
    def __init__(self, config, ledger, transport=None):
        if config.get('model') != 'gemini-2.5-flash' or config.get('paid_calls_authorized') is not False:
            raise ValueError('Only the explicitly selected free model is permitted')
        if config.get('automatic_paid_fallback') is not False or config.get('automatic_model_substitution') is not False:
            raise ValueError('Fallbacks are forbidden')
        for key in ['max_attempts', 'max_attempts_per_pacific_day', 'max_output_tokens', 'max_prompt_utf8_bytes']:
            if type(config.get(key)) is not int or config[key] <= 0:
                raise ValueError('Positive integer cap required: ' + key)
        if config['max_output_tokens'] > 2048 or config['max_prompt_utf8_bytes'] > 16000:
            raise ValueError('Pilot token/prompt ceilings cannot be raised implicitly')
        if config.get('thinking_budget') != 0 or config.get('user_authorized_free_generation') is not True:
            raise ValueError('Free authorization and disabled thinking are required')
        self.config, self.transport = config, transport
        Path(ledger).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(ledger)
        self.db.execute('''CREATE TABLE IF NOT EXISTS requests(
            hash TEXT PRIMARY KEY, status TEXT NOT NULL, created TEXT NOT NULL,
            pacific_day TEXT NOT NULL, started_epoch REAL NOT NULL, request TEXT NOT NULL,
            response TEXT, metadata TEXT)''')
        self.db.commit()

    def readiness(self):
        return {'credential_present': bool(os.environ.get(self.config['api_key_variable'])),
                'free_project_confirmed': os.environ.get(self.config['free_project_confirmation_variable']) == 'true',
                'model': 'gemini-2.5-flash', 'paid_fallback': False,
                'billing_tier_verified_via_api': False}

    def _key(self):
        state = self.readiness()
        if not state['credential_present']:
            raise FreeInferenceBlocked('MISSING_DQP_GEMINI_API_KEY')
        if not state['free_project_confirmed']:
            raise FreeInferenceBlocked('NON_BILLED_PROJECT_NOT_CONFIRMED')
        return os.environ[self.config['api_key_variable']]

    def _request(self, method, suffix, payload=None):
        key = self._key()
        try:
            with httpx.Client(transport=self.transport, verify=tls_context(), timeout=90,
                              follow_redirects=False, trust_env=True) as client:
                response = client.request(method, BASE + suffix, json=payload,
                                          headers={'x-goog-api-key': key})
            if response.status_code != 200:
                # Do not persist provider error bodies/URLs that might repeat credentials.
                raise FreeInferenceBlocked('HTTP_' + str(response.status_code))
            encoded = response.content
            if len(encoded) > 2000000:
                raise FreeInferenceBlocked('RESPONSE_SIZE_LIMIT')
            safe = encoded.decode().replace(key, '[REDACTED_CREDENTIAL]')
            return json.loads(safe)
        except FreeInferenceBlocked:
            raise
        except Exception as e:
            raise FreeInferenceBlocked('REQUEST_FAILED_' + type(e).__name__) from None

    def model_access(self):
        metadata = self._request('GET', '')
        if 'generateContent' not in metadata.get('supportedGenerationMethods', []):
            raise FreeInferenceBlocked('MODEL_DOES_NOT_ADVERTISE_GENERATION')
        return {k: metadata.get(k) for k in ['name', 'version', 'inputTokenLimit', 'outputTokenLimit',
                                             'supportedGenerationMethods']}

    def generate(self, prompt, seed, source_approved=False):
        self._key()
        versions = {r[0] for r in self.db.execute(
            "SELECT json_extract(metadata,'$.model_version') FROM requests WHERE status='COMPLETE'")}
        if len(versions) > 1:
            raise FreeInferenceBlocked('MIXED_RETURNED_MODEL_VERSIONS_REQUIRE_NEW_PROTOCOL')
        if source_approved is not True:
            raise FreeInferenceBlocked('INPUT_NOT_APPROVED_FOR_FREE_PROVIDER')
        if len(prompt.encode()) > self.config['max_prompt_utf8_bytes']:
            raise FreeInferenceBlocked('PROMPT_BYTE_LIMIT')
        payload = {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                   'generationConfig': {'temperature': self.config['temperature'], 'seed': seed,
                     'maxOutputTokens': self.config['max_output_tokens'], 'responseMimeType': 'application/json',
                     'thinkingConfig': {'thinkingBudget': 0}}}
        fingerprint = digest({'endpoint': BASE, 'payload': payload})
        cached = self.db.execute('SELECT status,response FROM requests WHERE hash=?', (fingerprint,)).fetchone()
        if cached:
            if cached[0] == 'COMPLETE':
                return json.loads(cached[1]), True
            raise FreeInferenceBlocked('PRIOR_ATTEMPT_PRESERVED_' + cached[0])
        self.db.execute('BEGIN IMMEDIATE')
        try:
            pacific_day = datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
            total = self.db.execute('SELECT count(*) FROM requests').fetchone()[0]
            daily = self.db.execute('SELECT count(*) FROM requests WHERE pacific_day=?', (pacific_day,)).fetchone()[0]
            last = self.db.execute('SELECT max(started_epoch) FROM requests').fetchone()[0]
            if total >= self.config['max_attempts'] or daily >= self.config['max_attempts_per_pacific_day']:
                raise FreeInferenceBlocked('LOCAL_ATTEMPT_CAP')
            wait = self.config['minimum_seconds_between_generation_requests'] - (time.time() - last) if last else 0
            if wait > 0:
                raise FreeInferenceBlocked('RATE_WINDOW_WAIT_' + str(int(wait) + 1))
            self.db.execute('INSERT INTO requests VALUES(?,?,?,?,?,?,?,?)',
                (fingerprint, 'RESERVED', now(), pacific_day, time.time(), json.dumps(payload), None, None))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        started = time.perf_counter()
        try:
            response = self._request('POST', ':generateContent', payload)
            prior_versions = {r[0] for r in self.db.execute(
                "SELECT json_extract(metadata,'$.model_version') FROM requests WHERE status='COMPLETE'")}
            version = response.get('modelVersion')
            version_present = isinstance(version, str) and bool(version)
            metadata = {'request_sha256': fingerprint, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                        'model_version': version, 'response_canonical_sha256': digest(response),
                        'usage': response.get('usageMetadata'),
                        'runtime_seconds': time.perf_counter() - started,
                        'expected_charge_usd_under_confirmed_free_project': 0,
                        'server_billing_tier_independently_verified': False,
                        'created_utc': datetime.now(timezone.utc).isoformat()}
            self.db.execute('UPDATE requests SET status=?,response=?,metadata=? WHERE hash=?',
                ('COMPLETE' if version_present else 'MISSING_RETURNED_MODEL_VERSION',
                 json.dumps(response), json.dumps(metadata), fingerprint))
            self.db.commit()
            if not version_present:
                raise FreeInferenceBlocked('MISSING_RETURNED_MODEL_VERSION_RESULT_PRESERVED')
            if prior_versions and version not in prior_versions:
                raise FreeInferenceBlocked('RETURNED_MODEL_VERSION_CHANGED_RESULT_PRESERVED')
            return response, False
        except FreeInferenceBlocked as e:
            # A successfully saved response stays intact, including a version-change response.
            self.db.execute("UPDATE requests SET status=? WHERE hash=? AND status='RESERVED'", (str(e), fingerprint))
            self.db.commit()
            raise

    def close(self):
        self.db.close()
