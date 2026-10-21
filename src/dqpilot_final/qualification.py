"""Auditable contract-based qualification; effectiveness awaits real frozen candidates.

This deliberately simple baseline is not claimed as a novel learned algorithm.
Documentation matches must be independently supplied: rule text cannot certify itself.
"""


def qualify(candidate, documentation, controls):
    if not candidate.get('technical_pass'):
        return {'decision': 'REJECT', 'reason': 'TECHNICAL_FAILURE'}
    if candidate['id'] in controls:
        return {'decision': 'REJECT', 'reason': 'ALREADY_IN_CONTROLS'}
    # The signature is derived by a trusted code/contract adapter, never asserted
    # by the model. Source contracts must have been recorded before candidates.
    if not candidate.get('signature_verified_from_executable'):
        return {'decision': 'ABSTAIN', 'reason': 'NO_VERIFIED_CONTRACT_SIGNATURE'}
    if candidate.get('contract_signature') in controls:
        return {'decision': 'REJECT', 'reason': 'ALREADY_IN_CONTROLS'}
    evidence = documentation.get(candidate.get('contract_signature'))
    if not evidence:
        return {'decision': 'ABSTAIN', 'reason': 'NO_INDEPENDENT_DOCUMENTATION'}
    if evidence.get('contradicted'):
        return {'decision': 'REJECT', 'reason': 'DOCUMENTED_CONTRADICTION'}
    required = ('source_reference', 'exact_scope', 'unit_and_missing_policy', 'frozen_before_generation')
    if not all(evidence.get(k) for k in required):
        return {'decision': 'ABSTAIN', 'reason': 'INCOMPLETE_EVIDENCE'}
    if not candidate.get('format_invariant', False):
        return {'decision': 'ABSTAIN', 'reason': 'UNRESOLVED_FORMAT_SENSITIVITY'}
    return {'decision': 'PROPOSE_FOR_REVIEW', 'reason': 'DOCUMENTED_AND_TECHNICALLY_COMPATIBLE'}


def require_model_candidates(manifest):
    """A core experiment cannot substitute handwritten rules for model outputs."""
    if not manifest or manifest.get('origin') != 'EXPERIMENTAL_MODEL_RESPONSE':
        raise ValueError('Real model response provenance is required')
    for key in ['provider', 'model_revision', 'prompt_sha256', 'response_sha256', 'source_partition']:
        if not manifest.get(key):
            raise ValueError('Missing candidate provenance: ' + key)
    if manifest['source_partition'] == 'reserved':
        raise ValueError('Reserved source is forbidden during development')


def outcomes(accepted_hits, all_candidate_hits, baseline_hits, adjudicated_errors):
    """Count unique cells; incremental benefit and rejected useful detections both matter."""
    new_hits = set(accepted_hits) - set(baseline_hits)
    useful_available = (set(all_candidate_hits) - set(baseline_hits)) & set(adjudicated_errors)
    useful_accepted = new_hits & set(adjudicated_errors)
    return {'incremental_labelled_hits': len(useful_accepted),
            'labelled_hits_lost_by_selection': len(useful_available - useful_accepted),
            'additional_findings': len(new_hits),
            'additional_unlabelled_findings': len(new_hits - set(adjudicated_errors))}
