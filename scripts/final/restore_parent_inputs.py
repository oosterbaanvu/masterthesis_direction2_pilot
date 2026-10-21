"""Restore pinned raw inputs without rewriting historical acquisition reports.

Use a temporary report root: newly injected Kaggle variable presence must not
change the parent's frozen acquisition JSON during future environment startup.
"""
import tempfile
from pathlib import Path

from dqpilot.acquisition import acquire

root = Path(__file__).resolve().parents[2]
(root / 'data/cache').mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(dir=root / 'data/cache') as temporary:
    work = Path(temporary)
    (work / 'config').symlink_to(root / 'config', target_is_directory=True)
    (work / 'data').symlink_to(root / 'data', target_is_directory=True)
    records = acquire(work)
    if any(record['status'] == 'FAILED' for record in records.values()):
        raise ValueError('Pinned parent acquisition failed; historical reports were preserved')
print('Parent raw inputs verified/restored; historical acquisition reports unchanged.')
