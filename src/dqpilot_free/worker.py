"""Resource-bounded pure-pandas GX triage of generated candidates; not semantic review."""
import ast
import contextlib
import io
import json
import resource
import sys

ALLOWED = {
    'ExpectColumnValuesToNotBeNull', 'ExpectColumnValuesToBeBetween',
    'ExpectColumnValuesToBeInSet', 'ExpectColumnValuesToBeUnique',
    'ExpectColumnValuesToMatchRegex', 'ExpectColumnValuesToNotMatchRegex',
    'ExpectColumnValueLengthsToBeBetween', 'ExpectColumnValuesToBeOfType',
    'ExpectColumnPairValuesToBeEqual', 'ExpectColumnPairValuesAToBeGreaterThanB',
    'ExpectMulticolumnSumToEqual', 'ExpectCompoundColumnsToBeUnique',
}


def parse_constructor(code, columns):
    if not isinstance(code, str) or len(code.encode()) > 8000:
        raise ValueError('INVALID_CODE_SIZE')
    tree = ast.parse(code, mode='eval')
    call = tree.body
    if not isinstance(call, ast.Call) or call.args:
        raise ValueError('NOT_LITERAL_GX_CONSTRUCTOR')
    f = call.func
    if not (isinstance(f, ast.Attribute) and f.attr in ALLOWED
            and isinstance(f.value, ast.Attribute) and f.value.attr == 'expectations'
            and isinstance(f.value.value, ast.Name) and f.value.value.id == 'gx'):
        raise ValueError('UNSUPPORTED_OR_UNSAFE_GX_CONSTRUCTOR')
    kwargs = {}
    for k in call.keywords:
        if k.arg is None or k.arg in kwargs:
            raise ValueError('DYNAMIC_OR_DUPLICATE_KEYWORD')
        kwargs[k.arg] = ast.literal_eval(k.value)
    selected = []
    for key, value in kwargs.items():
        if key in {'column', 'column_A', 'column_B'}:
            if not isinstance(value, str):
                raise ValueError('COLUMN_MUST_BE_LITERAL_NAME')
            selected.append(value)
        elif key == 'column_list':
            if not isinstance(value, list) or not 1 <= len(value) <= 32 or not all(isinstance(c, str) for c in value):
                raise ValueError('INVALID_COLUMN_LIST')
            selected.extend(value)
    if not selected or set(selected) - set(columns):
        raise ValueError('SCHEMA_INCOMPATIBLE')
    return f.attr, kwargs, sorted(set(selected))


def execute(payload):
    import great_expectations as gx
    import pandas as pd
    from dqpilot_final.ledqer import load_component

    frame = pd.DataFrame(payload['records'], columns=payload['columns'])
    output = []
    original = load_component(payload['original_evaluator'], 'original_gx_free_triage')
    for candidate in payload['candidates']:
        record = {'id': candidate.get('id'), 'semantic_validity': 'NOT_ADJUDICATED'}
        try:
            _, _, columns = parse_constructor(candidate['gx_code'], frame.columns)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                gx.get_context(mode='ephemeral')
                result = original.validate_rule_on_dataframe(frame.copy(), [{'code': candidate['gx_code']}])
            if not result['can_run']:
                record.update(status='EXECUTION_FAILED', technical_pass=False)
            else:
                raw = result['validation_results'].to_json_dict()['results'][0]['result']
                indices = raw.get('unexpected_index_list')
                if not isinstance(indices, list) or not all(type(i) is int for i in indices):
                    indices = None  # Never export unexpected-value dictionaries from real source rows.
                record.update(status='EXECUTED', technical_pass=True, columns=columns,
                    unexpected_count=raw.get('unexpected_count'), unexpected_rows=indices,
                    interpretation='Unlabelled development workload, not error precision/recall')
        except Exception as e:
            # Exception text may include source values or adversarial model text.
            record.update(status='TECHNICAL_FAILURE_OR_UNSUPPORTED', technical_pass=False,
                          exception_type=type(e).__name__)
        output.append(record)
    return output


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))
    payload = json.load(sys.stdin)
    output = execute(payload)
    print(json.dumps(output, allow_nan=False))


if __name__ == '__main__':
    main()
