from pathlib import Path

import pandas as pd

from dqpilot_final.ledqer import load_component


def test_original_greedy_uses_only_explicit_development_pairs():
    source = Path(__file__).resolve().parents[1] / 'data/vendor/ledqer/rule_eval/rule_selection.py'
    selector = load_component(source, 'original_selection_software_test')
    # Synthetic software fixture: no test-label input exists in this API call.
    rules = pd.DataFrame([{'ri': 0, 'precision': 1.0}, {'ri': 1, 'precision': .5}])
    pairs = pd.DataFrame([{'ri': 0, 'pk': 10, 'col': 'x', 'isDirty': 1},
                          {'ri': 1, 'pk': 11, 'col': 'x', 'isDirty': 1}])
    selected, _, covered = selector.greedy_rule_selection_pairs(pairs, rules, 1.0)
    assert selected == [0] and covered == {(10, 'x')}
