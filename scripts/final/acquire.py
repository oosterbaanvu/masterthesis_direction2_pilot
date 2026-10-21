"""Acquire the pinned public LeDQeR source; never overwrite an existing clone."""
import subprocess
from pathlib import Path

from dqpilot.common import save, sha

root = Path(__file__).resolve().parents[2]
source = root / 'data/vendor/ledqer'
commit = 'fb42051026ee6ccded9347349ff95b597804962d'
if not source.exists():
    subprocess.run(['git', 'clone', 'https://github.com/Anna-Christina-Glock/dq_rule_generation', str(source)], check=True)
    subprocess.run(['git', '-C', str(source), 'checkout', '--detach', commit], check=True)
head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
if head != commit:
    raise ValueError('Existing LeDQeR checkout differs from frozen source')
if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip():
    raise ValueError('Do not reproduce from a modified upstream checkout')
files = subprocess.check_output(['git', '-C', str(source), 'ls-files'], text=True).splitlines()
for path in (source / 'data/in').glob('*.csv'):
    path.chmod(0o444)
manifest = {'repository': 'https://github.com/Anna-Christina-Glock/dq_rule_generation', 'commit': head,
            'files': {p: sha(source / p) for p in files}, 'licence': 'NO_TOP_LEVEL_LICENCE_FOUND',
            'redistributed': False, 'generated_rules_available_in_inspected_full_history': False}
target = root / 'results/final/ledqer_acquisition.json'
if not target.exists():
    save(target, manifest)
print('Pinned official source verified; raw source and datasets remain ignored.')
