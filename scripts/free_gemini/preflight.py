"""Exercise local real-data triage with explicitly handwritten software fixtures."""
import json
from pathlib import Path
from time import perf_counter

from dqpilot.common import save
from dqpilot_free.pilot import triage

root = Path(__file__).resolve().parents[2]
contexts = json.loads((root / 'results/free_gemini/prepared_inputs.json').read_text())['source_contexts']
codes = {'uci_credit': "gx.expectations.ExpectColumnValuesToNotBeNull(column='LIMIT_BAL')",
         'uci_bank_marketing': "gx.expectations.ExpectColumnValuesToNotBeNull(column='age')",
         'uci_wine_white': "gx.expectations.ExpectColumnValuesToNotBeNull(column='pH')",
         'synthetic_balanced_journals': "gx.expectations.ExpectColumnPairValuesToBeEqual(column_A='total_debits', column_B='total_credits')"}
records = []
started = perf_counter()
for source, code in codes.items():
    result = triage(root, source, [{'id': 'HANDWRITTEN_SOFTWARE_PREFLIGHT', 'gx_code': code}], contexts[source])
    if result['status'] != 'TRIAGED' or result['results'][0]['status'] != 'EXECUTED':
        raise ValueError('Local triage not ready: ' + source + ' ' + result['status'])
    records.append({'source': source, 'origin': 'HANDWRITTEN_SOFTWARE_PREFLIGHT_NOT_MODEL_OUTPUT', 'result': result})
save(root / 'results/free_gemini/local_preflight.json', {'status': 'PIPELINE_PREFLIGHT_PASSED_NOT_MODEL_RESEARCH',
     'records': records, 'runtime_seconds': perf_counter() - started, 'model_generations': 0,
     'paid_calls': 0, 'reserved_sec_accessed': False})
print('Four local source paths executed; no model call and no semantic-validity claim.')
