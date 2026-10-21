"""Controller software fixture: no provider or inference endpoint is contacted."""
import json
import sqlite3

import yaml

from dqpilot.common import sha
from dqpilot_free import pilot


def test_local_failure_is_not_misreported_as_failed_model_generation(tmp_path, monkeypatch):
    config_path = tmp_path / 'config/free_gemini/pilot.yaml'
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({'local_cache': 'cache', 'provider': 'SOFTWARE_FIXTURE',
        'model': 'SOFTWARE_FIXTURE', 'max_attempts_per_invocation': 1, 'max_rules_per_response': 4}))
    prompt = tmp_path / 'prompt.txt'
    prompt.write_text('SOFTWARE FIXTURE ONLY')
    item = {'id': 'fixture', 'source': 'synthetic', 'documentation': 'provided',
            'prompt_variant': 'direct', 'seed': 11, 'prompt_sha256': sha(prompt), 'path': 'prompt.txt'}
    monkeypatch.setattr(pilot, 'prepare', lambda _: {'requests': [item], 'source_contexts': {'synthetic': {}}})

    class FakeProvider:
        def __init__(self, *_):
            self.db = sqlite3.connect(':memory:')
            self.db.execute('CREATE TABLE requests(status TEXT)')

        def readiness(self):
            return {'SOFTWARE_FIXTURE': True}

        def model_access(self):
            return {'name': 'SOFTWARE_FIXTURE'}

        def generate(self, *_args, **_kwargs):
            self.db.execute("INSERT INTO requests VALUES('COMPLETE')")
            return {'modelVersion': 'SOFTWARE_FIXTURE', 'candidates': [{'finishReason': 'STOP',
                'content': {'parts': [{'text': json.dumps({'rules': [], 'abstentions': []})}]}}]}, False

        def close(self):
            self.db.close()

    def missing_local_data(*_):
        raise FileNotFoundError('SOFTWARE FIXTURE: source unavailable')

    monkeypatch.setattr(pilot, 'GeminiFree', FakeProvider)
    monkeypatch.setattr(pilot, 'triage', missing_local_data)
    result = pilot.run(tmp_path)
    assert result['records'][0]['status'] == 'GENERATED'
    assert result['records'][0]['technical_triage']['status'] == 'INFRASTRUCTURE_FAILURE'
