"""Run original GX evaluator/greedy components with explicitly handwritten fixtures."""
import ast
import contextlib
import importlib.util
import io
import logging
import time
from pathlib import Path

import great_expectations as gx
import pandas as pd

from dqpilot.common import digest, partition, save, sha
from dqpilot.evaluation import cells

METADATA = {'isDirty', 'errRule', 'errCol', 'pk'}


def load_component(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_constructor(code):
    """AST-check a standard GX constructor before passing it to original eval code."""
    tree = ast.parse(code, mode='eval')
    call = tree.body
    if not isinstance(call, ast.Call) or call.args:
        raise ValueError('A keyword-only GX constructor is required')
    f = call.func
    if not (isinstance(f, ast.Attribute) and f.attr.startswith('Expect')
            and 'Query' not in f.attr and isinstance(f.value, ast.Attribute)
            and f.value.attr == 'expectations' and isinstance(f.value.value, ast.Name)
            and f.value.value.id == 'gx'):
        raise ValueError('Only standard pandas GX expectation constructors are permitted')
    for keyword in call.keywords:
        if keyword.arg is None:
            raise ValueError('No dynamic keyword expansion')
        ast.literal_eval(keyword.value)
    return True


def handwritten_candidates(dataset, columns):
    result = [{'id': 'not_null:' + c, 'column': c,
               'code': f'gx.expectations.ExpectColumnValuesToNotBeNull(column={c!r})',
               'origin': 'HUMAN_WRITTEN_COMPONENT_FIXTURE'} for c in columns]
    patterns = {'beers': ('ounces', r'^\d+(\.\d+)?$'),
                'flights': ('act_dep_time', r'^\d{1,2}:\d{2}.*$'),
                'hospital': ('State', r'^[A-Z]{2}$'), 'tax': ('rate', r'^\d+\.\d+$')}
    c, pattern = patterns[dataset]
    result.append({'id': 'format_fixture:' + c, 'column': c,
                   'code': f'gx.expectations.ExpectColumnValuesToMatchRegex(column={c!r}, regex={pattern!r})',
                   'origin': 'HUMAN_WRITTEN_COMPONENT_FIXTURE_NOT_A_BUSINESS_TRUTH'})
    return result


def label_cells(frame, columns):
    result = set()
    for _, row in frame.iterrows():
        for token in str(row['errCol']).split(';'):
            for c in token.split('<->'):
                if c in columns:
                    result.add((int(row['pk']), c))
    return result


def reproduce(root, output=None):
    root = Path(root).resolve()
    source = root / 'data/vendor/ledqer'
    output = Path(output) if output is not None else root / 'results/final'
    if (output / 'ledqer_components.json').exists():
        raise ValueError('Preserve completed reproduction; use a new output location')
    original = load_component(source / 'rule_eval/evaluate_rules.py', 'ledqer_original_evaluation')
    selection = load_component(source / 'rule_eval/rule_selection.py', 'ledqer_original_selection')
    prompt_module = load_component(source / 'rule_gen/rule_gen_prompt.py', 'ledqer_original_prompts')
    logging.getLogger().setLevel(logging.ERROR)
    records, prompt_records, fixture_manifest, raw_checks = [], [], {}, []
    started = time.monotonic()
    for dataset in ['flights', 'beers', 'hospital', 'tax']:
        file = source / f'data/in/{dataset}_dirty_lab.csv'
        frame = pd.read_csv(file)
        clean = pd.read_csv(source / f'data/in/{dataset}_clean.csv')
        columns = [c for c in frame if c not in METADATA]
        fixture = handwritten_candidates(dataset, columns)
        fixture_manifest[dataset] = fixture
        # Group repeated entities. Tax's released pk identity gives row groups; no new target labels used for grouping.
        group_column = {'flights': 'flight', 'beers': 'brewery_id', 'hospital': 'ProviderNumber', 'tax': 'pk'}[dataset]
        groups = frame[group_column].astype(str).map(lambda x: partition(x, 'ledqer-component-v1:' + dataset))
        gold = label_cells(frame, columns)
        predictions = {}
        failures = []
        for index, candidate in enumerate(fixture):
            safe_constructor(candidate['code'])
            gx.get_context(mode='ephemeral')
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = original.validate_rule_on_dataframe(frame[columns].copy(), [{'code': candidate['code']}])
            if not result['can_run']:
                failures.append({'index': index, 'exception_count': result.get('exception_count'),
                                 'exception_type_or_message': result.get('exception')})
                continue
            raw = result['validation_results'].to_json_dict()['results'][0]['result']
            indices = raw.get('unexpected_index_list')
            if indices is None:
                raise ValueError('GX COMPLETE output omitted unexpected indices')
            predicted = {(int(frame.loc[i, 'pk']), candidate['column']) for i in indices}
            predictions[index] = predicted
            # Check official set scorer against independently computed confusion counts.
            relevant_gold = {pk for pk, c in gold if c == candidate['column']}
            official = original.calculate_precision_recall(list(relevant_gold), [pk for pk, _ in predicted])
            independent = cells(predicted, {(pk, candidate['column']) for pk in relevant_gold})
            if [official['TP'], official['FP'], official['FN']] != [independent['tp'], independent['fp'], independent['fn']]:
                raise ValueError('Official/independent scorer discrepancy')
            raw_checks.append({'dataset': dataset, 'fixture': candidate['id'], 'match': True})
        dev_ids = set(frame.loc[groups == 'development', 'pk'].astype(int))
        eval_ids = set(frame.loc[groups == 'exploratory', 'pk'].astype(int))
        dev_gold = {(pk, c) for pk, c in gold if pk in dev_ids}
        eval_gold = {(pk, c) for pk, c in gold if pk in eval_ids}
        rule_rows, pair_rows = [], []
        for ri, predicted in predictions.items():
            relevant = {(pk, c) for pk, c in predicted if pk in dev_ids}
            counts = cells(relevant, dev_gold)
            rule_rows.append({'ri': ri, 'col_set': fixture[ri]['column'], 'precision': counts['precision']})
            pair_rows.extend({'ri': ri, 'pk': pk, 'col': c, 'isDirty': int((pk, c) in dev_gold)}
                             for pk, c in relevant)
        df_rules = pd.DataFrame(rule_rows, columns=['ri', 'col_set', 'precision'])
        df_pairs = pd.DataFrame(pair_rows, columns=['ri', 'pk', 'col', 'isDirty'])
        all_pred = set().union(*predictions.values()) if predictions else set()
        technical = cells({p for p in all_pred if p[0] in eval_ids}, eval_gold)
        selected_outcomes = []
        for threshold in [0.0, 0.8, 1.0]:
            selected, cover, covered = selection.greedy_rule_selection_pairs(df_pairs, df_rules, threshold)
            combined = set().union(*(predictions[i] for i in selected)) if selected else set()
            evaluation = {p for p in combined if p[0] in eval_ids}
            selected_outcomes.append({'precision_threshold': threshold, 'selected_fixtures': selected,
                'development_label_access': True, 'evaluated_on_separate_groups': True,
                'author_label_agreement': cells(evaluation, eval_gold),
                'evaluation_labelled_hits_lost_vs_technical': technical['tp'] - len(evaluation & eval_gold)})
        records.append({'dataset': dataset, 'status': 'COMPONENT_REPRODUCTION_ONLY',
                        'candidate_origin': 'HUMAN_WRITTEN_FIXTURES_NOT_MODEL_OUTPUTS',
                        'rows': len(frame), 'groups': frame[group_column].nunique(), 'group_key': group_column,
                        'development_rows': len(dev_ids), 'evaluation_rows': len(eval_ids),
                        'labelled_evaluation_cells': len(eval_gold), 'candidate_count': len(fixture),
                        'executed_candidates': len(predictions), 'execution_failures': failures,
                        'technical_fixture_agreement': technical, 'original_greedy': selected_outcomes,
                        'data_sha256': sha(file), 'semantic_precision_claim': False})
        first = frame[frame['isDirty'] == True].iloc[[0]]  # noqa: E712
        for prompt in [0, 1, 2]:
            for syntax in [0, 2]:
                rendered = prompt_module.generate_prompt(clean, first, n_cols=len(columns),
                                  id_column='pk', prompt_id=prompt, expectation_list_id=syntax,
                                  error_detection_info='Dataset-specific domain description intentionally unavailable in this rendering audit.')
                path = output / f'local/prompts/{dataset}_{prompt}_{syntax}.txt'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rendered)
                prompt_records.append({'dataset': dataset, 'prompt': prompt, 'syntax_list': syntax,
                                       'sha256': sha(path), 'utf8_bytes': len(rendered.encode()),
                                       'model_called': False})
    result = {'status': 'PARTIAL_COMPONENT_REPRODUCTION', 'original_commit': 'fb42051026ee6ccded9347349ff95b597804962d',
              'great_expectations_version': gx.__version__, 'runtime_seconds': time.monotonic() - started,
              'records': records, 'original_scorer_checks': raw_checks, 'rendered_prompts': prompt_records,
              'candidate_fixture_sha256': digest(fixture_manifest), 'new_model_calls': 0,
              'paper_performance_reproduction': 'NOT_RUN_NO_MODEL_OR_RELEASED_GENERATED_RULES',
              'reserved_sec_accessed': False}
    save(output / 'ledqer_components.json', result)
    save(output / 'handwritten_component_candidates.json', fixture_manifest)
    return result
