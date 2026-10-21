"""Calculate proposal ceilings only. Contains no inference client."""
import json
from pathlib import Path

import yaml

from dqpilot.common import save


def calculate(root):
    root = Path(root)
    plan = yaml.safe_load((root / 'config/final/model_plan.yaml').read_text())
    prompts = json.loads((root / 'results/final/ledqer_components.json').read_text())['rendered_prompts']
    records = []
    for model, rates in plan['rates_usd_per_million_tokens'].items():
        per_call = (plan['input_cap_tokens'] * rates['input'] + plan['output_cap_tokens'] * rates['output']) / 1e6
        records.append({'model': model, 'input_usd_per_M': rates['input'], 'output_usd_per_M': rates['output'],
                        'per_call_ceiling_usd': per_call,
                        'pilot_48_calls_usd': round(per_call * 48, 6),
                        'pilot_60_call_cap_usd': round(per_call * 60, 6),
                        'full_240_calls_one_model_usd': round(per_call * 240, 6)})
    result = {'status': 'COST_PROPOSAL_PRIMARY_LAUNCH_AND_CURRENT_CATALOG_CORROBORATION', 'records': records,
              'price_sources': plan['primary_price_sources'], 'pricing_limit': plan['pricing_limit'],
              'input_token_ceiling': plan['input_cap_tokens'], 'output_token_ceiling': plan['output_cap_tokens'],
              'actual_prompt_bytes_range': [min(p['utf8_bytes'] for p in prompts), max(p['utf8_bytes'] for p in prompts)],
              'input_budget_basis': 'UTF8 bytes upper-bound token count plus explicit 4000-token request overhead reserve; not measured billing',
              'price_catalog_commit': plan['pricing_catalog_commit'], 'cache_or_batch_discount_assumed': False,
              'actual_new_model_calls': 0, 'actual_new_inference_cost_usd': 0,
              'proposed_full_pair_with_20pct_retry_ceiling_usd': round(sum(r['full_240_calls_one_model_usd'] for r in records if r['model'] in plan['full']['proposed_models']) * 1.2, 6),
              'tax_gpu_energy_and_human_review_costs_included': False}
    save(root / 'results/final/model_cost_proposal.json', result)
    return result
