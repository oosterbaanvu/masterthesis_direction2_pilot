# Pilot 2 — measured feasibility report

**Recommendation: NO-GO for the current broad scientific formulation.** The software and non-LLM workflow work; a novel, empirically supported generated-rule qualification contribution has not been established. See the [decision and exact gates](go_no_go.md).

## What actually ran

| Phase | Status and evidence |
|---|---|
| Qualification | Thirteen-source registry; eleven acquired with SHA/version/schema checks, two optional Kaggle sources blocked. Full released SEC structural audit; bounded primary literature review with inaccessible full-text limitations. |
| Reproduction | All 24 released prediction artifacts rescored with the official runner and an independent compatible implementation; maximum numerical discrepancy about `2.22e-16`, supplied CSV agreement within `1e-8`. No new LLM inference. |
| Deterministic experiments | 360 completed UCI source/field/family/rate/seed cases; 28,541 actual injected changes out of 29,308 selected cells. Eighteen partial realizations retained; seven published pairs assessed with source-specific roles. |
| LLM generation / direct detection | NOT_RUN: no configured experimental model/usable inference binding and no explicit spend authorization. Provider, caching and caps implemented; tests mock HTTP. |
| Generated-rule qualification | Safe same-candidate C/D pipeline implemented and tested with human fixtures; scientific acceptance, semantic validity, useful-rule rejection and C/D detection comparison NOT_RUN. |
| Scaling / robustness | Twelve numerical and four categorical target fields across three regular datasets; 208 exploratory SEC bases × three conditions; numeric-format sensitivity and real Bank delivery-shift workload executed. No reserved SEC method evaluation. |
| Engineering | Full scans of ten regular/pair sources plus one development SEC table, three bank delivery batches, explicit lifecycle/exception workflow and 36 passing tests. Local governance identities are simulated. |

All substantive raw files, original predictions, value-level logs, caches and SQLite state are ignored. The final scientific run has frozen input/output manifests. Earlier failed scoring attempts and the excluded zero-scale label run are retained. Pilot 1 was inspected read-only at the exact requested branch/commit; its results were not rerun or mixed into this pilot.

## Main measurements

Every missing/type/invalid-code injection is caught by the applicable conventional contracts. Scale-error detection is less uniform:

| Source | Actual scale positives | Contract hits | Contract + historical hits |
|---|---:|---:|---:|
| Credit | 2,026 | 537 | 1,084 |
| Bank | 2,271 | 729 | 1,777 |
| White Wine | 364 | 91 | 362 |

For plausible replacements: Credit 0/3,222 contract and historical detections; Wine 0/364; Bank 722/4,374 contract and 725/4,374 with history, largely through existing cross-field semantics. These are descriptive totals over dependent fields/seeds/rates, not independent observations or estimates of natural financial error recall. Extra off-label findings are unadjudicated workload; full denominators and counts are in [deterministic results](deterministic_results.md).

The SEC lexical baseline has location F1 **0.0357–0.0450** across the three conditions on 208 exploratory tables each. Adding an unsupported missing-cell heuristic gives **0.1287–0.1352**; it is a sensitivity, not an approved mandatory-field rule. No arithmetic business rule was inferred from test annotations. The reserved 210 bases (630 variants) remain unscored by new methods. Retrospective released-output reproduction separately uses all bases for compatibility and is not a new holdout comparison. For example, released `deepseekv3_10%` has table F1 0.8410 but location F1 0.2481; this cannot be directly compared to Pilot 1's budgeted injection recall or the exploratory-only baseline without matching populations.

Published reference inspection finds 118,253/121,219 Tax differences are equivalent under the specified rate/ZIP normalization, and 710/820 Cars differences are numerically equivalent. Cars' remaining 110 differences and Restaurant's 125 eligible differences are completeness sanity cases; Rayyan accuracy is withheld. Full qualification and benchmark interpretation are in the [dataset report](dataset_qualification.md) and [SEC audit](benchmark_audit.md).

An envelope trained on Bank delivery 1 gives 21,272 alerts on 4,374 delivery-2 rows and 33,436 on 6,685 delivery-3 rows. Without adjudicated DQ labels, these are source-change burdens, not meaningful detection gains. Numeric accounting-format changes also alter SEC lexical predictions. Together these results undermine treating successful execution or a low development violation rate as sufficient deployment evidence.

## Novelty, artifact and decision

The [literature gate](literature_review.md) identifies Akella, LLM-DQR, Auto-Test and a particularly close Bayesian rule-verification abstract published 20 October 2026. Generation + deduplication + execute/debug + qualification cannot be claimed as a new contribution. Full review of inaccessible close work is outstanding. No broad literature performance claim has been promoted to a reproduced result.

The engineering demonstrator produces findings and batch profiles across all eleven acquired sources and enforces a restricted DSL, read-only query execution, timeouts and explicit activation. It records 14 batches, 567 events and 5,666 findings in the measured demo. Qualification there uses explicitly handcrafted lifecycle fixtures; it is not scientific candidate adjudication. See [engineering evidence](engineering_evaluation.md) and [architecture](../docs/architecture.md).

[Pilot 1 versus Pilot 2](pilot1_vs_pilot2.md) favors Pilot 1's present evidence maturity, while retaining both directions' novelty/ground-truth limitations. A narrower Pilot 2 may be worth reconsidering only after independent semantic labels, closest-work reproduction and a small authorized generation study establish a defensible contribution. No paid calls were made; original published-model costs remain unknown. No Git push or environment publication is claimed.
