import pytest

from dqpilot.rules import Rule
from dqpilot_execution.evaluate import entails, canonical, evidence_select, union
from dqpilot_execution.safety import validate


@pytest.mark.parametrize(
    "code",
    [
        "__import__('os').system('false')",
        "gx.expectations.ExpectColumnValuesToNotBeNull(column='x',row_condition='@__import__(\"os\")')",
        "gx.expectations.ExpectColumnValuesToNotBeNull(column='x',condition_parser='pandas')",
        "gx.expectations.ExpectQueryResultsToMatchComparison(query='SELECT 1')",
        "gx.expectations.ExpectColumnValuesToBeBetween(column='x',min_value=float('inf'))",
    ],
)
def test_generated_code_cannot_inject_execution(code):
    with pytest.raises((ValueError, SyntaxError)):
        validate(code, ["x"])


def test_normalized_duplicate_key_is_argument_order_independent():
    a = "gx.expectations.ExpectColumnValuesToBeBetween(column='x',min_value=0)"
    b = 'gx.expectations.ExpectColumnValuesToBeBetween(min_value=0, column="x")'
    assert canonical(a) == canonical(b)


def test_interval_entailment_never_promotes_a_stronger_unjustified_bound():
    known = Rule("source", "range", ["x"], {"min": 0, "max": 14})
    assert entails(known, Rule("weak", "range", ["x"], {"min": -1, "max": 100}))
    assert not entails(known, Rule("strong", "range", ["x"], {"min": 1, "max": 10}))


def test_documentary_qualifier_has_no_label_input_and_abstains_without_certificate():
    import pandas as pd

    data = {"source": "source", "dev": pd.DataFrame({"x": [1, 2]}), "strong_rules": []}
    rule = {"id": "c", "gx_code": "gx.expectations.ExpectColumnValuesToBeBetween(column='x',min_value=0)"}
    selected, decisions = evidence_select(data, [rule], {"c"}, {"c": set()}, {"c": set()}, [])
    assert selected == [] and decisions[0]["decision"] == "ABSTAIN"


def test_installed_control_redundancy_is_not_hidden_as_incremental_value():
    import pandas as pd

    control = Rule("existing", "not_null", ["x"], evidence="verified: controlled source")
    data = {"source": "source", "dev": pd.DataFrame({"x": [1, 2]}), "strong_rules": [control]}
    rule = {"id": "c", "gx_code": "gx.expectations.ExpectColumnValuesToNotBeNull(column='x')"}
    selected, decisions = evidence_select(data, [rule], {"c"}, {"c": set()}, {"c": set()}, [control])
    assert not selected and decisions[0]["reason"] == "LOGICALLY_REDUNDANT_WITH_INSTALLED_CONTROLS"


def test_union_of_new_rule_findings_cannot_remove_baseline_detections():
    baseline = {1, 3}
    deltas = {"a": {2, 3}, "b": {4}}
    assert baseline <= baseline | union(deltas, ["a", "b"])
