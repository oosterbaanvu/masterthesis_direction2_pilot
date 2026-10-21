"""Run a frozen free-only generation pilot once its dedicated access is configured."""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from dqpilot.acquisition import load_table
from dqpilot.common import digest, partition, save, sha
from dqpilot_free.gemini import FreeInferenceBlocked, GeminiFree
from dqpilot_free.prepare import prepare


def parse_candidates(response, maximum=4):
    candidates = response.get('candidates', [])
    if len(candidates) != 1 or candidates[0].get('finishReason') != 'STOP':
        raise ValueError('MISSING_BLOCKED_OR_TRUNCATED_RESPONSE')
    parts = candidates[0].get('content', {}).get('parts', [])
    text = ''.join(p.get('text', '') for p in parts if not p.get('thought'))
    parsed = json.loads(text)
    rules = parsed.get('rules')
    if not isinstance(rules, list) or len(rules) > maximum:
        raise ValueError('INVALID_RULE_COUNT')
    ids = set()
    for rule in rules:
        if not isinstance(rule, dict) or not all(isinstance(rule.get(k), str) for k in ['id', 'description', 'gx_code']):
            raise ValueError('INVALID_RULE_SCHEMA')
        if rule['id'] in ids or not isinstance(rule.get('evidence_references'), list) or not all(
                isinstance(value, str) for value in rule['evidence_references']):
            raise ValueError('INVALID_RULE_IDENTIFIERS_OR_EVIDENCE')
        ids.add(rule['id'])
    abstentions = parsed.get('abstentions', [])
    if not isinstance(abstentions, list) or not all(isinstance(value, str) for value in abstentions):
        raise ValueError('INVALID_ABSTENTION_SCHEMA')
    return rules, abstentions


def local_frame(root, source, context):
    if source == 'synthetic_balanced_journals':
        return pd.DataFrame(context['sample']), 'SELF_AUTHORED_SYNTHETIC'
    registry = yaml.safe_load((root / 'config/datasets.yaml').read_text())['datasets']
    frame = load_table(root, source, registry[source])
    columns = [c['name'] for c in context['schema']]
    frame = frame[columns]
    # Duplicate feature records stay together; no labels or targets select rows.
    keep = [partition(digest([str(x) for x in row]), 'free-gemini-local-development-v1') == 'development'
            for row in frame.itertuples(index=False, name=None)]
    return frame.loc[keep].head(256).reset_index(drop=True), 'UNLABELLED_DEVELOPMENT_ONLY'


def triage(root, source, candidates, context):
    frame, role = local_frame(root, source, context)
    payload = {'columns': list(frame.columns),
               'records': frame.astype(object).where(pd.notnull(frame), None).to_dict('records'),
               'candidates': candidates,
               'original_evaluator': str(root / 'data/vendor/ledqer/rule_eval/evaluate_rules.py')}
    child_env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ['KEY', 'TOKEN', 'SECRET'])}
    child_env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    try:
        process = subprocess.run([sys.executable, '-m', 'dqpilot_free.worker'], input=json.dumps(payload),
            text=True, capture_output=True, timeout=35, env=child_env, cwd=root)
        if process.returncode:
            return {'status': 'WORKER_FAILED_OR_RESOURCE_LIMIT', 'exit_code': process.returncode, 'rows': len(frame)}
        return {'status': 'TRIAGED', 'rows': len(frame), 'role': role, 'results': json.loads(process.stdout),
                'held_out_error_performance': 'NOT_MEASURED', 'independent_semantic_judgments': 0}
    except subprocess.TimeoutExpired:
        return {'status': 'WORKER_WALL_TIMEOUT', 'rows': len(frame)}


def run(root):
    root = Path(root).resolve()
    inputs = prepare(root)
    config = yaml.safe_load((root / 'config/free_gemini/pilot.yaml').read_text())
    provider = GeminiFree(config, root / config['local_cache'] / 'requests.sqlite')
    report = {'started_utc': datetime.now(timezone.utc).isoformat(), 'provider': config['provider'],
              'requested_model': config['model'], 'access': provider.readiness(), 'planned_requests': len(inputs['requests']),
              'paid_calls': 0, 'automatic_paid_fallback': False, 'reserved_sec_accessed': False,
              'real_person_records_transmitted': False, 'records': []}
    try:
        report['model_access'] = provider.model_access()
        new_calls = 0
        for item in inputs['requests']:
            if new_calls >= config['max_attempts_per_invocation']:
                report['status'] = 'PARTIAL_INVOCATION_CAP_RESUME_FROM_CACHE'
                break
            path = root / item['path']
            if sha(path) != item['prompt_sha256']:
                raise FreeInferenceBlocked('FROZEN_PROMPT_CHANGED')
            while True:
                try:
                    response, cached = provider.generate(path.read_text(), item['seed'], source_approved=True)
                    break
                except FreeInferenceBlocked as e:
                    if str(e).startswith('RATE_WINDOW_WAIT_'):
                        time.sleep(min(30, int(str(e).rsplit('_', 1)[1])))
                        continue
                    raise
            new_calls += int(not cached)
            record = {k: item[k] for k in ['id', 'source', 'documentation', 'prompt_variant', 'seed', 'prompt_sha256']}
            record.update(cached=cached, model_version=response.get('modelVersion'),
                          usage=response.get('usageMetadata'), response_sha256=digest(response),
                          origin='EXPERIMENTAL_MODEL_RESPONSE')
            try:
                rules, abstentions = parse_candidates(response, config['max_rules_per_response'])
            except (ValueError, KeyError, TypeError):
                record['status'] = 'INVALID_BLOCKED_OR_TRUNCATED_OUTPUT_PRESERVED_IN_CACHE'
            else:
                record.update(status='GENERATED', rules=rules, abstentions=abstentions)
                # Infrastructure failure is not a failed model generation.
                try:
                    record['technical_triage'] = triage(root, item['source'], rules, inputs['source_contexts'][item['source']])
                except Exception as e:
                    record['technical_triage'] = {'status': 'INFRASTRUCTURE_FAILURE', 'exception_type': type(e).__name__}
            report['records'].append(record)
            save(root / 'data/cache/free_gemini/progress.json', report)
            print('Recorded', item['id'], record['status'], flush=True)
        else:
            report['status'] = 'GENERATION_PILOT_COMPLETE_SEMANTIC_EVALUATION_PENDING'
    except FreeInferenceBlocked as e:
        report.update(status='BLOCKED_OR_STOPPED', reason=str(e))
    except Exception as e:
        report.update(status='PIPELINE_FAILURE', reason=type(e).__name__)
    finally:
        counts = dict(provider.db.execute('SELECT status,count(*) FROM requests GROUP BY status').fetchall())
        report['durable_attempt_status_counts'] = counts
        report['new_generation_attempts_total'] = sum(counts.values())
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        provider.close()
        tag = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        save(root / 'results/free_gemini/attempts' / (tag + '.json'), report)
        save(root / 'results/free_gemini/run_status.json', report)
    return report
