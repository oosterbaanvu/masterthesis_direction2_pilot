# Same-candidate qualification experiment

The actual generated candidates were frozen and deduplicated within source/condition before selection. **A** retains supported, executable proposals; **B** invokes the unchanged LeDQeR greedy pair-coverage selector using development labels and precision 1.0; **C** requires entailment from inherited documentary contracts, no baseline redundancy, low unlabelled development alerts and format stability, otherwise rejects/abstains; **D** is the fixed conventional suite without extra model rules. A/B/C are reported with that identical conventional suite included.

All arms share the same candidate population within a track. B has privileged development-label access and is a labelled reference, not an equally deployable label-free competitor. No held-out labels are given to generation, C or threshold choice. Every selector is saved before held-out scoring. For controlled row evaluation the original pair selector uses an explicit ROW proxy; for published single-column cells its original pair algorithm and cell identities are retained. Multicolumn candidates are excluded only from the cell-localization track, equally for every arm.

For controlled sources B estimates development precision on each rule's **new flags relative to unmodified development**, because existing source alerts have no independent clean labels. Its precision-one constraint therefore does not guarantee precision one on raw batches. Published-source B instead uses raw development reference discrepancies. This target difference is explicit; the controlled adapter is not a faithful reproduction of the paper's known-dirty-tuple protocol.

## Held-out reference cells, strong controls

| Source | Arm | TP | Off-reference | FN | Precision | Recall | F1 | Extra reference hits | Extra alerts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raha_beers | A | 152 | 775 | 539 | 0.164 | 0.220 | 0.188 | 0 | 770 |
| raha_beers | B | 152 | 5 | 539 | 0.968 | 0.220 | 0.358 | 0 | 0 |
| raha_beers | C | 152 | 5 | 539 | 0.968 | 0.220 | 0.358 | 0 | 0 |
| raha_beers | D | 152 | 5 | 539 | 0.968 | 0.220 | 0.358 | 0 | 0 |
| raha_hospital | A | 18 | 453 | 59 | 0.038 | 0.234 | 0.066 | 18 | 471 |
| raha_hospital | B | 6 | 0 | 71 | 1.000 | 0.078 | 0.145 | 6 | 6 |
| raha_hospital | C | 0 | 0 | 77 | 0.000 | 0.000 | 0.000 | 0 | 0 |
| raha_hospital | D | 0 | 0 | 77 | 0.000 | 0.000 | 0.000 | 0 | 0 |


The Hospital `strong` configuration equals its weak generic missing-token screen; the Beers stronger screen adds only lexical numeric checks for ABV and IBU. These are limited controls, not complete source-specific business suites. Hospital B selected the familiar ZIP/ZIP+4 pattern `^[0-9]{5}(-[0-9]{4})?$`; such a conventional check could be authored without an LLM. It was not retroactively inserted into D after observing scores. The six extra reference hits are thus evidence above this fixed basic screen, not proof of unique AI value above a mature domain baseline.

Hospital B improves reference precision and F1 relative to A while reducing recall: six of the 18 available extra reference hits remain, with no additional off-reference cells. C removes that burden but also all available extra reference hits. Beers B/C avoid A's 770 extra off-reference alerts, retaining the same 152 baseline reference hits. This is not evidence that qualification uniformly improves detection; burden, lost coverage and label access must be read together.

## What C measures

C is a transparent conservative baseline, not a newly validated semantic estimator. It inherits the correctness/scope of existing contracts. A proof of entailment under those assumptions does not independently verify the source contract. Unknown semantics trigger ABSTAIN; unsupported execution and baseline redundancy have different reasons. `selections/*.json` contains every decision and accepted set, including the no-extra-documentation and threshold variants. No acceptance implies production activation: independent review remains required.

Entailment is checked in a native constraint abstraction. Its numeric/code normalization can differ from exact GX membership under representation changes; this is not a machine-checked proof of runtime equivalence. The padding diagnostic exposes part of that mismatch. Claims of logical redundancy are conditional on that abstraction and inherited normalization policy.

The documentary knowledge available to C is a subset of the strong conventional suite. Consequently every candidate C could certify is already entailed by that suite and fails the explicit redundancy gate: **zero strong-baseline C acceptance is structurally implied by this implementation**, not an empirical discovery about all evidence-based qualification. Under weak controls C can restore known omitted contract checks; that is not novel rule discovery and may be implemented without an LLM. The weak/strong results expose this limitation rather than hiding it behind a favorable precision score.

Formatting is tested by padding nonblank strings. That may change an exact categorical-code contract rather than preserve semantics, so the stability gate can reject a valid exact-code check. This deliberately narrow diagnostic must not be advertised as universal semantic invariance. Likewise existing controls remain visible in documentation-withheld generation; this condition removes additional documentation, not all source knowledge.

A code audit added an explicit downstream technical-pool assertion for B, plus diagnostic raw-versus-new-alert metric clarification before any new UCI holdout scoring. Both published sources had all eight candidates technically eligible, so their completed scores are unchanged. Original result files were preserved and all their scientific fields match isolated final-code rescoring (`published_score_reproduction.json`). The study is exploratory with transparent implementation amendments, not retrospectively pristine preregistration.

Semantic-validity precision, false promotion of independently invalid rules, reviewer agreement and precision on independently adjudicated natural errors remain unmeasured. Published reference precision and controlled alteration precision cannot substitute for those quantities.

The unchanged original LeDQeR confusion-count scorer also ran on 276 actual-candidate row/cell comparisons and agreed with the independent scorer in every case (`original_scorer_actual_candidates.json`). This complements the real original GX evaluator and greedy-selector runs; it does not reproduce upstream model generation, labelled correctness/coverage filtering or paper performance.
