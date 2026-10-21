"""C/D evaluation boundary: qualification receives development inputs, never scoring labels."""
from .common import digest
from .evaluation import cells
from .rules import Engine, Rule, qualify


def compare_candidates(candidates, development, evaluation, evaluation_labels, baseline_flags=frozenset()):
    frozen = digest(candidates)
    decisions = qualify(candidates, development)
    raw, accepted, failed = set(), set(), []
    with Engine(evaluation) as engine:
        for candidate, decision in zip(candidates, decisions, strict=True):
            try:
                flags = engine.execute(Rule.parse(candidate))
                raw |= flags
                if decision['state'] == 'VALIDATED':
                    accepted |= flags
            except Exception as e:
                failed.append({'candidate': candidate, 'error': type(e).__name__})
    if digest(candidates) != frozen:
        raise RuntimeError('Candidate mutation during qualification')
    gold = set(evaluation_labels)
    return {'frozen_candidate_sha256': frozen, 'candidate_count': len(candidates), 'decisions': decisions,
            'C': cells(raw, gold), 'D': cells(accepted, gold), 'execution_failures': failed,
            'additional_labelled_detections_C': len((raw - baseline_flags) & gold),
            'additional_labelled_detections_D': len((accepted - baseline_flags) & gold),
            'labelled_detections_lost': len((raw - accepted) & gold),
            'acceptance_count': sum(d['state'] == 'VALIDATED' for d in decisions),
            'semantic_validity': 'Requires independent adjudication; not inferred from execution'}
