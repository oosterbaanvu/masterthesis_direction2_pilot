"""Official Kaggle token route. Never serialize credentials or SDK exception text."""
import contextlib
import io
import os
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

from dqpilot.common import now, save, sha


GMSC_COLUMNS = ['SeriousDlqin2yrs', 'RevolvingUtilizationOfUnsecuredLines', 'age',
                'NumberOfTime30-59DaysPastDueNotWorse', 'DebtRatio', 'MonthlyIncome',
                'NumberOfOpenCreditLinesAndLoans', 'NumberOfTimes90DaysLate',
                'NumberRealEstateLoansOrLines', 'NumberOfTime60-89DaysPastDueNotWorse',
                'NumberOfDependents']


def validate_gmsc(frame):
    # Original competition training CSV has an unnamed leading record identifier.
    if len(frame) != 150000 or list(frame.columns)[1:] != GMSC_COLUMNS:
        raise ValueError('SOURCE_SCHEMA_OR_ROW_COUNT_MISMATCH')
    if not str(frame.columns[0]).startswith('Unnamed') or not frame.iloc[:, 0].is_unique:
        raise ValueError('SOURCE_IDENTITY_COLUMN_MISMATCH')
    if not set(frame['SeriousDlqin2yrs'].dropna().unique()) <= {0, 1}:
        raise ValueError('PREDICTION_TARGET_DOMAIN_MISMATCH')
    return True


def acquire(root):
    root = Path(root).resolve()
    config = root / 'data/cache/kaggle'
    config.mkdir(parents=True, exist_ok=True)
    os.environ['KAGGLE_CONFIG_DIR'] = str(config)
    report = {'timestamp': now(), 'token_present': bool(os.environ.get('KAGGLE_API_TOKEN')),
              'sdk_version': '2.2.4', 'credential_value_logged': False, 'datasets': {}}
    auth = False
    api = None
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            api = KaggleApi()
            api.authenticate()
            auth = True
        except (Exception, SystemExit) as e:
            report['authentication_exception_type'] = type(e).__name__
    report['local_sdk_authentication_succeeded'] = auth
    if not auth:
        report['authenticated_operation'] = 'NOT_RUN_SDK_AUTH_NOT_ESTABLISHED' if report['token_present'] else 'NOT_RUN_MISSING_CREDENTIAL'
        for key in ['baf', 'gmsc']:
            report['datasets'][key] = {'status': 'BLOCKED_CURRENT_TASK_CREDENTIAL_UNAVAILABLE',
                                      'downloaded': False, 'hash': None}
        save(root / 'results/final/kaggle_acquisition.json', report)
        return report
    # An authentication-enabled endpoint, not SDK initialization alone, verifies functionality.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        for key in ['gmsc', 'baf']:
            try:
                if key == 'gmsc':
                    api.competition_list_files('GiveMeSomeCredit')
                    report['authenticated_operation'] = 'COMPETITION_FILE_LIST_SUCCESS'
                    with tempfile.TemporaryDirectory(dir=root / 'data/cache') as temporary:
                        api.competition_download_file('GiveMeSomeCredit', 'cs-training.csv', path=temporary, quiet=True)
                        candidates = list(Path(temporary).glob('*'))
                        content = next(p for p in candidates if p.name.startswith('cs-training.csv')).read_bytes()
                        if content.startswith(b'PK'):
                            import io as _io
                            with zipfile.ZipFile(_io.BytesIO(content)) as z:
                                content = z.read(next(n for n in z.namelist() if n.endswith('cs-training.csv')))
                        target = root / 'data/raw/gmsc/cs-training.csv'
                else:
                    api.dataset_list_files('sgpjesus/bank-account-fraud-dataset-neurips-2022')
                    report['authenticated_operation'] = 'DATASET_FILE_LIST_SUCCESS'
                    # Availability is separate from lawful processing. Do not accept conflicting licences automatically.
                    report['datasets'][key] = {'status': 'ACCESSIBLE_BUT_LICENCE_REVIEW_REQUIRED',
                                              'downloaded': False, 'publisher_licence_conflict_unresolved': True}
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and target.read_bytes() != content:
                    raise ValueError('Existing source differs; preserve and review')
                if not target.exists():
                    target.write_bytes(content)
                target.chmod(0o444)
                frame = pd.read_csv(target)
                validate_gmsc(frame)
                report['datasets'][key] = {'status': 'ACQUIRED_UNPINNED_FIRST_AUTHENTIC_DOWNLOAD',
                                          'downloaded': True, 'sha256': sha(target), 'rows': len(frame),
                                          'columns': list(frame.columns), 'prediction_target_is_not_DQ_label': True,
                                          'competition_rule_acceptance': 'Required only if server denies; never accepted automatically'}
            except Exception as e:
                report['datasets'][key] = {'status': 'BLOCKED', 'downloaded': False,
                                          'exception_type': type(e).__name__,
                                          'http_status': getattr(e, 'status', getattr(getattr(e, 'response', None), 'status_code', None)),
                                          'message_not_logged': True}
    save(root / 'results/final/kaggle_acquisition.json', report)
    return report
