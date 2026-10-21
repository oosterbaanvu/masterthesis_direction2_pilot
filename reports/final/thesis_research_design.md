# Proposed scientific design — frozen-candidate reliability study

This is a prospective design, not a claim that the main experiment has run. The main candidates, independent judgments and final model/provider remain unavailable. `protocol.yaml`, `model_plan.yaml` and the generation prompt record the present boundary; model-specific settings require a dated amendment before inference.

## Scope and hypotheses

Study promotion reliability and incremental detection for executable relational/table checks under source change. The experimental unit is an independent source group; financial variants and periods are clustered by issuer or canonical table family. Repeated prompts and corruptions are within-source replications. Financial and nonfinancial tracks are reported separately.

Predefine two co-primary outcomes: (1) incremental labelled detections beyond a frozen control suite, macro-averaged over eligible independent source groups; (2) the fraction of independently adjudicated invalid/inapplicable candidates that a selector promotes. Always accompany them with useful-rule rejection/detection loss and total additional findings. Abstentions count toward coverage and loss, not as proven valid rejections. Do not optimize a single fixed review-budget score.

H1 asks whether documentary evidence reduces false promotion relative to technical-only filtering. H2 asks what incremental coverage is lost by that restriction. H3 asks whether applicability errors increase after documented/undocumented scope changes. No hypothesis assumes that conservative selection dominates. Existing literature and a full Bayesian-method comparison may change or invalidate these hypotheses before confirmation.

## Data and source separation

Use UCI sources for controlled corruption and known convention tests; qualified Raha/Jung pairs for author-reference agreement; independently reviewed financial contracts for semantic applicability; SEC and FinRule only for clearly defined conditional logical/principle tasks. Do not present default, fraud, model-generated repair or every lexical dirty/clean difference as natural DQ gold.

Prospective target: approximately 40 eligible source groups, with issuer clustering in finance. Forty groups is a planning target, not a power claim or 40 independent domains. A four-source micro-pilot estimates candidate yield, label quality, annotation time and between-source variability. Freeze genuine development/validation/final groups before generation. Current SEC reserved 210 base IDs remain untouched. Newly inspected FinRule material is exploratory and cannot become a pristine confirmation set retrospectively. Keep public benchmark contamination and repeated-company dependence explicit.

The conventional controls, source contracts and allowed documentary evidence are frozen before candidates. Existing inherited controls were not all learned exclusively from a clean new-source training split; they represent an installed-control setting. Source-change cases distinguish harmless encoding/presentation changes, genuinely changed semantics and missing or misleading documentation. Interventions need a justified invariant and must not fabricate natural errors.

## Generation and candidate freeze

After model approval, generate at most four candidates per call using schema, explicit documentation availability, a development-only unlabelled sample and existing-control descriptions. Exclude targets, dirty/clean pairs, errCol/errRule, test labels and reserved data from new-source prompts. Freeze prompt template, provider/model revision, request parameters, response bytes/hashes, timing, token accounting and retries. Use a deterministic sample order and durable cache. Retain failed/invalid outputs in denominators; repair is a separately counted, capped experimental condition.

Pilot planning uses four sources × two documentation contexts × two prompts × three repetitions: 48 calls for one model. Within each context, all selectors receive the same frozen candidates; differences between generation contexts are separate ablations. The full plan is 40 groups × two prompts × three repetitions: 240 calls per model. A second model is optional until reviewer workload and pilot yield are known. These repeated generations are not independent source samples.

## Comparison arms

A accepts technically valid, executable, schema-compatible candidates. B uses original LeDQeR greedy coverage with **development labels**, explicitly a label-assisted reference. Its thresholds are fixed before final evaluation; no test labels choose rules. Where the closest Bayesian full implementation is available and applicable, add its faithful label-free method with provenance and deviations documented; an abstract-inspired guess does not satisfy this requirement.

C begins with a transparent contract-matching baseline: independently frozen documentation, trusted executable-derived signatures, scope/unit/missing conventions and format-invariance evidence. Missing evidence means abstention; explicit contradictions mean rejection. This is not a claimed new method. Broader uncertainty/violation-rate heuristics require a separately specified comparator and development-only thresholds. A manual candidate entailment label would change its information tier and cannot be hidden as “documentation.”

D adds no candidate checks to the same baseline controls. Every arm is evaluated on the same cases, candidate provenance and control suite. The artifact may require human approval for activation, but blinded evaluator judgments are never fed back into the scientific selector on test groups.

## Independent semantic evaluation

Two reviewers independently judge validity, applicability and convention support, blinded to selector decision and model identity. They inspect original documentation/filings, not just successful execution or another model's explanation. Use VALID / INVALID / CANNOT_JUDGE separately for validity and applicability, with evidence and rationale. Consensus occurs only after independent judgments are frozen. Report raw agreement, an appropriate chance-corrected statistic, prevalence, cannot-judge rate and disagreements; do not generate a kappa value before reviews exist.

Review both accepted and rejected candidates. Predefine useful as: valid and applicable **and** adds at least one adjudicated target error beyond existing controls on an eligible evaluation case. Distinguish a justified rule with no observed extra error from a demonstrated useful one. Human error-label adjudication is separate from rule-meaning review. If only one reviewer exists, report that limitation and avoid a two-reviewer reliability claim. Unresolvable meaning shrinks the admissible claim rather than becoming an LLM-generated label.

At four candidates per full call, one model can create up to 960 candidates before deduplication. Two reviews at an assumed four minutes each would total about 128 reviewer-hours, excluding detection adjudication and disagreements. This is a workload scenario, not a measured throughput estimate. The micro-pilot must establish realistic throughput and simplify the scope if independent review is unavailable. Do not silently select only attractive candidates for review.

## Metrics, uncertainty and reporting

Report validity/applicability per candidate; accepted, rejected and abstained counts; invalid-rule promotion; useful-rule rejection; unique incremental labelled detections; lost potential detections; additional unadjudicated alerts; execution failure; runtime and cost. Labelled coverage is counted once per location/case, with a fixed localization definition. Report controlled injected-cell recovery and SEC logical-participant localization separately. For incompletely labelled natural data, extra unlabelled alerts are workload, not false positives.

Use paired source-group differences and cluster bootstrap intervals when group counts support them; issuer clustering takes precedence over table count. With four micro-pilot sources, show raw per-source results rather than a falsely precise population interval. For macro means, state eligible denominators and abstention coverage. Predefine exclusions for ambiguous IDs, misalignment and unsupported relations; report their coverage, not only successful cases. Threshold sensitivity is an explicit secondary analysis fixed before final labels are inspected.

## Feasibility and stopping

Weeks 1–2: closest-work full-text decision and reviewer/rights agreement. Weeks 3–4: authorised one-model micro-pilot, label audit and workload decision. Months 2–3: pre-register the final estimands and adapted baseline, freeze sources/candidates. Months 4–5: main comparison and independent review. Month 6: source-change and prompt robustness. Month 7: confirmation and error analysis. Months 8–9: thesis, reproducibility package and bounded service handover.

Stop or narrow if the closest work removes the question, source meaning cannot be independently evaluated, eligible independent sources are insufficient, or review effort is infeasible. Scientific failure does not require a favorable treatment effect: a well-designed negative result is acceptable. No private Rabobank integration, production authentication claim or UI expansion is part of this experiment.
