# Robustness and generalization

All 48 adapted source/doc/instruction/seed conditions were completed without changing the model, prompts or selector thresholds after held-out outcomes. This is a fixed-model exploratory study. Five real datasets, three seeds and many candidate occurrences do not establish a population of independent domains or significant model superiority.

## Prespecified selector sensitivity

The table reports accepted candidate counts. Outcome sensitivity, including held-out hits and workload for each threshold, is in `tables/row_results.csv`; changing accepted count is not itself an improvement. C thresholds were 0, .01 and .05 unlabelled development alert fraction; B precision 1 and .8. No threshold was selected for a favorable held-out score.

| Source | Controls | A | B1 | C.01 | C0 | C.01 | C.05 | B.8 | C without extra docs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic_balanced_journals | strong | 7 | 2 | 0 | 0 | 0 | 0 | 2 | 0 |
| synthetic_balanced_journals | weak | 7 | 2 | 2 | 2 | 2 | 2 | 2 | 0 |
| uci_bank_marketing | strong | 5 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| uci_bank_marketing | weak | 5 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| uci_credit | strong | 8 | 3 | 0 | 0 | 0 | 0 | 3 | 0 |
| uci_credit | weak | 8 | 3 | 0 | 0 | 0 | 0 | 3 | 0 |
| uci_wine_white | strong | 11 | 2 | 0 | 0 | 0 | 0 | 2 | 0 |
| uci_wine_white | weak | 11 | 2 | 0 | 0 | 0 | 0 | 2 | 0 |


`tables/prompt_strata.csv` reports response parse/execution yield and distinct rule sets for each source, documentation and direct/cautious instruction condition. This is a generation-quality ablation. The primary selector comparison pools the frozen candidates within source; it must not be described as a clean causal detection comparison between documentation conditions. The original four-call smoke and adapted condition are also not balanced equivalent populations. The generic syntax examples can anchor thresholds, and temperature-zero seed repetitions can be highly dependent.

Whitespace padding is an explicit diagnostic only. Exact categorical codes can change validity under padding; this limits interpretation of C's stability requirement. Unsupported conditional/relational classes restrict what a model can express. Held-out mixed-type execution failures are preserved rather than silently dropping the difficult family or treating failure as a successful negative check.

## Conditional uncertainty and dependence

| Source | Arm | Conditional group uncertainty |
| --- | --- | --- |
| raha_beers | A | {"groups":95,"reference_F1_95pct":[0.15986464824587931,0.2207693856998993],"paired_incremental_reference_recall_95pct":[0.0,0.0],"interpretation":"Fixed-model conditional entity-group bootstrap, not independent source/generalization uncertainty"} |
| raha_beers | B | {"groups":95,"reference_F1_95pct":[0.31213037950842826,0.40226278746451943],"paired_incremental_reference_recall_95pct":[0.0,0.0],"interpretation":"Fixed-model conditional entity-group bootstrap, not independent source/generalization uncertainty"} |
| raha_beers | C | {"groups":95,"reference_F1_95pct":[0.31213037950842826,0.40226278746451943],"paired_incremental_reference_recall_95pct":[0.0,0.0],"interpretation":"Fixed-model conditional entity-group bootstrap, not independent source/generalization uncertainty"} |
| raha_beers | D | {"groups":95,"reference_F1_95pct":[0.31213037950842826,0.40226278746451943],"paired_incremental_reference_recall_95pct":[0.0,0.0],"interpretation":"Fixed-model conditional entity-group bootstrap, not independent source/generalization uncertainty"} |
| raha_hospital | A | {"status":"WITHHELD_TOO_FEW_ENTITY_GROUPS","groups":7} |
| raha_hospital | B | {"status":"WITHHELD_TOO_FEW_ENTITY_GROUPS","groups":7} |
| raha_hospital | C | {"status":"WITHHELD_TOO_FEW_ENTITY_GROUPS","groups":7} |
| raha_hospital | D | {"status":"WITHHELD_TOO_FEW_ENTITY_GROUPS","groups":7} |


The Beers intervals resample the same brewery groups for a paired increment relative to D, conditional on this fixed model/candidate set. Degenerate zero intervals mean identical measured reference hits in these resamples, not a proof of no benefit on other sources. Hospital has seven providers, so intervals are withheld. These are no source-level cross-model confidence bounds and no multiple-condition significance claims. Controlled-family outcomes are descriptive; dependent injections/candidates are not independent population trials.

Original scientific fields reproduce exactly under isolated rescoring without model calls. This verifies deterministic analysis of cached outputs, not bitwise regeneration across CPU/compiler changes. Broader claims require a new source holdout, independent semantic review and a second justified model configuration. Unit/period/sign applicability shifts in natural financial data have not been tested here; the old SEC diagnostic and controlled journals do not fill that gap.
