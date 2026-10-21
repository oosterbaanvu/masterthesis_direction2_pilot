import json
import sys
import types

import pandas as pd
import pytest

from dqpilot_final.kaggle_access import GMSC_COLUMNS, acquire, validate_gmsc


def test_gmsc_schema_and_cardinality_are_not_optional():
    with pytest.raises(ValueError, match='SCHEMA_OR_ROW'):
        validate_gmsc(pd.DataFrame(columns=['Unnamed: 0'] + GMSC_COLUMNS))


def test_sdk_exception_never_serializes_credential(tmp_path, monkeypatch):
    secret = 'SYNTHETIC_TEST_SECRET_NEVER_REAL'
    monkeypatch.setenv('KAGGLE_API_TOKEN', secret)
    module = types.ModuleType('kaggle.api.kaggle_api_extended')

    class BrokenAPI:
        def authenticate(self):
            print(secret)
            raise RuntimeError(secret)

    module.KaggleApi = BrokenAPI
    monkeypatch.setitem(sys.modules, 'kaggle.api.kaggle_api_extended', module)
    result = acquire(tmp_path)
    assert secret not in json.dumps(result)
    assert not result['local_sdk_authentication_succeeded']
    assert all(not d['downloaded'] for d in result['datasets'].values())
