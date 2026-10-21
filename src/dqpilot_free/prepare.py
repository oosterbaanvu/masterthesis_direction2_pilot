"""Freeze only source metadata and explicit synthetic examples for free-tier input."""
import json
from pathlib import Path

import yaml

from dqpilot.common import digest, save, sha

PROMPT = '''Generate at most FOUR proposed data-quality checks for SOURCE_CONTEXT.
Return a JSON object with rules (a list) and abstentions (a list of strings).
Each rule has id, description, gx_code and evidence_references (list of strings).
gx_code must be ONE standard gx.expectations.Expect... constructor with literal
keyword arguments, supported by Great Expectations 1.9.1 on pandas. No imports,
SQL/query checks, user-defined functions, files, network or arbitrary Python.
Use only the schema and supplied documentation. There are no known dirty examples,
error labels or reference repairs. Do not treat prediction targets as DQ labels.
Do not silently strengthen provisional screening assumptions into universal rules.
Respect signed balances, unknown/sentinel conventions, units and source scope.
Successful execution does not prove semantic validity. Unsupported checks may be
proposed only with their assumption explicit; abstain when meaning is insufficient.
No rule is activated automatically. Avoid checks already listed in existing_controls.
SOURCE_CONTEXT:
'''


def prepare(root):
    root = Path(root)
    config = yaml.safe_load((root / 'config/free_gemini/pilot.yaml').read_text())
    output = root / 'results/free_gemini'
    cache = root / config['local_cache']
    contexts = {}
    citations = {'uci_credit': 'https://doi.org/10.24432/C55S3H',
                 'uci_bank_marketing': 'https://doi.org/10.24432/C5K306',
                 'uci_wine_white': 'https://doi.org/10.24432/C56S3T'}
    for source, citation in citations.items():
        path = root / 'config/contracts' / (source + '.yaml')
        contract = yaml.safe_load(path.read_text())
        columns = [{k: c[k] for k in ['name', 'type', 'semantic', 'unit', 'description', 'documented_values'] if k in c}
                   for c in contract['columns']]
        contexts[source] = {'source': source, 'citation': citation,
            'schema': columns, 'source_documentation': contract['description'],
            'convention_notes': [{'id': r['id'], 'status': r.get('status'), 'evidence': r.get('evidence')}
                                 for r in contract.get('rules', [])],
            'existing_controls': contract.get('rules', []), 'sample': [],
            'sample_note': 'No individual records are transmitted; schema/documentation-only generation.',
            'source_contract_sha256': sha(path), 'raw_rows_transmitted': False,
            'licence_basis': 'UCI public dataset metadata, CC BY 4.0, citation retained; inherited provisional assumptions remain marked'}
    contexts['synthetic_balanced_journals'] = {
        'source': 'synthetic_balanced_journals', 'citation': 'Self-authored controlled engineering scenario v1',
        'schema': [{'name': 'journal_id', 'type': 'string'}, {'name': 'currency', 'type': 'string'},
                   {'name': 'total_debits', 'type': 'numeric'}, {'name': 'total_credits', 'type': 'numeric'}],
        'source_documentation': 'One row is a whole balanced journal within one currency. IDs are unique and required. '
            'Currency is USD or EUR. Amounts are nonnegative integer cents, not rounded display values. '
            'Total debits equal total credits exactly. No presentation blanks or missing-value sentinels exist. '
            'These are stipulated synthetic semantics, not independently verified accounting records.',
        'convention_notes': [], 'existing_controls': [{'kind': 'not_null', 'columns': 'all'},
            {'kind': 'unique', 'column': 'journal_id'}, {'kind': 'allowed', 'column': 'currency', 'values': ['USD', 'EUR']}],
        'sample': [{'journal_id': 'SYNTHETIC_' + str(i), 'currency': 'USD',
                    'total_debits': 10000 + i, 'total_credits': 10000 + i} for i in range(5)],
        'sample_note': 'Entirely self-authored artificial examples, not bank/customer data.',
        'raw_rows_transmitted': False, 'licence_basis': 'Self-authored synthetic content'}
    requests = []
    for seed in config['seeds']:
        for variant in config['prompt_variants']:
            for documentation in config['documentation_contexts']:
                for source in config['sources']:
                    context = json.loads(json.dumps(contexts[source]))
                    if documentation == 'withheld':
                        context['source_documentation'] = 'Documentation intentionally withheld.'
                        context['convention_notes'] = []
                        # Field descriptions/domains are documentary evidence too.
                        context['schema'] = [{k: c[k] for k in ['name', 'type'] if k in c} for c in context['schema']]
                    suffix = '\nExplicitly list unsupported assumptions and abstain where source semantics are absent.' if variant == 'cautious' else ''
                    prompt = PROMPT + json.dumps(context, ensure_ascii=False, sort_keys=True) + suffix
                    if len(prompt.encode()) > config['max_prompt_utf8_bytes']:
                        raise ValueError('Frozen prompt exceeds ceiling')
                    identifier = f'{source}:{documentation}:{variant}:{seed}'
                    path = cache / 'prompts' / (identifier.replace(':', '_') + '.txt')
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if path.exists() and path.read_text() != prompt:
                        raise ValueError('Prepared prompt changed; use a new protocol version')
                    path.write_text(prompt)
                    requests.append({'id': identifier, 'source': source, 'documentation': documentation,
                        'prompt_variant': variant, 'seed': seed, 'prompt_sha256': sha(path),
                        'prompt_utf8_bytes': len(prompt.encode()), 'path': path.relative_to(root).as_posix(),
                        'approved_source_class': 'PUBLIC_METADATA_OR_SELF_AUTHORED_SYNTHETIC',
                        'real_person_records_transmitted': False})
    result = {'status': 'PREPARED_NOT_MODEL_OUTPUTS', 'config_sha256': sha(root / 'config/free_gemini/pilot.yaml'),
              'requests': requests, 'contexts_sha256': digest(contexts), 'source_contexts': contexts,
              'requests_planned': len(requests), 'model_calls': 0,
              'statistical_unit_note': 'Three public source schemas and one synthetic scenario; repeated prompts are not independent domains.'}
    target = output / 'prepared_inputs.json'
    if target.exists() and json.loads(target.read_text()) != result:
        raise ValueError('Do not replace a completed prompt freeze')
    save(target, result)
    return result
