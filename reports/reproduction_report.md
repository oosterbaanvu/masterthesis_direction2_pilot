# Released SEC evaluation reproduction

All **24 released prediction JSON artifacts** (eight filename-labelled models × three conditions) were evaluated by the unchanged official `TestAllModels.py`, with only four configuration assignments parameterized in memory. Its SHA and every prediction SHA are recorded. The independent compatibility implementation agrees with the original runner within floating-point roundoff (maximum difference approximately `2.22e-16`); all supplied result-CSV fields match within `1e-8`. This is released-output rescoring, **not newly executed LLM inference or reproduction of the entire paper**.

The official `errLoc Precision` is intersection divided by **GT location count**, i.e. recall. `errType Precision` similarly uses the GT-type denominator. Some empty-string GT types introduce an empty-string class. Compatibility preserves those conventions; corrected results use actual predicted-location precision, recall, F1, fixed VAL/FMT/MISS type metrics, count regression metrics and mean IoU. The dynamic label bookkeeping in the original script omits earlier true negatives; that by itself does not change per-label F1. The material type difference is the empty-string class and denominator interpretation.

`qwen2.5-7b_10%.json` contains 1,024 records for 1,000 canonical IDs: 24 IDs occur twice. The official dictionary silently takes the last record. Corrected scoring removes all 24 ambiguous IDs and reports 976/1,000 coverage; no arbitrary prediction is selected and no model output is changed. Other corrected artifacts cover all 1,000 tables. The discarded implementation attempts are documented under `results/attempts`.

Examples from the **released artifacts**, not live inference:

| Artifact | Tables | Table F1 | Location TP / predicted / annotated | Location precision | Location recall | Location F1 |
|---|---:|---:|---:|---:|---:|---:|
| deepseekv3_1% | 1,000 | 0.8277 | 864 / 2,967 / 4,364 | 0.2912 | 0.1980 | 0.2357 |
| deepseekv3_10% | 1,000 | 0.8410 | 915 / 2,967 / 4,408 | 0.3084 | 0.2076 | 0.2481 |
| deepseekv3_50% | 1,000 | 0.8459 | 895 / 3,044 / 4,451 | 0.2940 | 0.2011 | 0.2388 |
| gpt-4_1% | 1,000 | 0.7776 | 504 / 1,200 / 4,364 | 0.4200 | 0.1155 | 0.1812 |
| gpt-4_10% | 1,000 | 0.7872 | 522 / 1,115 / 4,408 | 0.4682 | 0.1184 | 0.1890 |
| gpt-4_50% | 1,000 | 0.7699 | 521 / 1,208 / 4,451 | 0.4313 | 0.1171 | 0.1841 |

The paper's main evaluation includes different model names/settings; filenames alone do not verify exact identities or inference parameters. Prompts, original token consumption, seeds and financial costs for these released outputs are not available as a complete reproducible inference manifest. They remain unknown. Mean IoU includes empty/empty examples scoring 1; table F1 and IoU must not be mistaken for high localized-error coverage.

All corrected scores and grouped bootstrap intervals are in `results/sec_reproduction.json`. The bootstrap groups three corruption variants by base ID (1,000 groups per complete model; the duplicate exclusion changes one model's condition coverage). It measures conditional base-table sampling uncertainty, not generation stochasticity or independence across issuers. Ambiguous row-name locations are still benchmark-coordinate labels, not re-adjudicated unique physical cells.

A complete repetition through the documented CLI finished in `results/local/reproduction-01`. All eight scientific output artifacts, including all 360 cases, matched the final run within `1e-12` after excluding timestamps/runtime. Both freezes and result manifests verified. This is local repeatability, not independent research evidence or a test of restoration in a new cloud task. Evidence: `results/repeatability.json`.
