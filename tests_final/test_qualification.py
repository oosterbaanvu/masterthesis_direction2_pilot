import pytest

from dqpilot_final.ledqer import safe_constructor
from dqpilot_final.qualification import outcomes, qualify, require_model_candidates


@pytest.mark.parametrize('code', ["__import__('os').system('false')",
    "gx.expectations.ExpectColumnValuesToNotBeNull(column=__import__('os'))",
    "gx.expectations.ExpectQueryResultsToMatchComparison(query='DROP TABLE x')",
    "gx.expectations.ExpectColumnValuesToNotBeNull(**x)"])
def test_arbitrary_execution_rejected(code):
    with pytest.raises(ValueError):
        safe_constructor(code)


def test_gx_not_restricted_to_old_dsl():
    assert safe_constructor("gx.expectations.ExpectColumnValuesToBeBetween(column='x', min_value=0)")


def test_fixtures_cannot_be_substituted_for_model_outputs():
    with pytest.raises(ValueError):
        require_model_candidates({'origin': 'HUMAN_WRITTEN_COMPONENT_FIXTURE'})


def test_unlabelled_low_violation_rate_does_not_prove_validity():
    candidate = {'id': 'x', 'technical_pass': True, 'format_invariant': True, 'violation_rate': 0,
                 'signature_verified_from_executable': True, 'contract_signature': 'not_null:required_field'}
    assert qualify(candidate, {}, set())['decision'] == 'ABSTAIN'


def test_independent_documentation_and_reviewer_gate():
    candidate = {'id': 'x', 'technical_pass': True, 'format_invariant': True,
                 'signature_verified_from_executable': True, 'contract_signature': 'not_null:required_field'}
    evidence = {'source_reference': 'manual:section1', 'exact_scope': 'batchA',
                'unit_and_missing_policy': 'explicit', 'frozen_before_generation': True}
    assert qualify(candidate, {'not_null:required_field': evidence}, set())['decision'] == 'PROPOSE_FOR_REVIEW'
    evidence['contradicted'] = True
    assert qualify(candidate, {'not_null:required_field': evidence}, set())['decision'] == 'REJECT'


def test_rejection_loss_and_incremental_value_are_both_counted():
    assert outcomes({1, 2, 4}, {1, 2, 3, 4}, {1}, {1, 2, 3}) == {
        'incremental_labelled_hits': 1, 'labelled_hits_lost_by_selection': 1,
        'additional_findings': 2, 'additional_unlabelled_findings': 1}
