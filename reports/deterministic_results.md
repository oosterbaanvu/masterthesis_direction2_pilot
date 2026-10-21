# Executed deterministic experiments

Descriptive counts over dependent seeds/rates/fields; each source and family stays separate. Off-label alerts are unadjudicated, not established false positives. A = source contracts; B = A plus development-fitted historical envelopes.

| Source | Family | Cases | Actual positives | A hits | B hits | A recall | B recall | Off-label A / B |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| uci_credit | missing | 36 | 3222 | 3222 | 3222 | 1.000 | 1.000 | 0 / 2204 |
| uci_credit | invalid_type | 24 | 2148 | 2148 | 2148 | 1.000 | 1.000 | 0 / 1470 |
| uci_credit | invalid_code | 12 | 1074 | 1074 | 1074 | 1.000 | 1.000 | 0 / 736 |
| uci_credit | gross_scale | 24 | 2026 | 537 | 1084 | 0.265 | 0.535 | 0 / 1468 |
| uci_credit | plausible_swap | 36 | 3222 | 0 | 0 | 0.000 | 0.000 | 0 / 2203 |
| uci_bank_marketing | missing | 36 | 4374 | 4374 | 4374 | 1.000 | 1.000 | 629 / 1589 |
| uci_bank_marketing | invalid_type | 24 | 2916 | 2916 | 2916 | 1.000 | 1.000 | 647 / 1285 |
| uci_bank_marketing | invalid_code | 12 | 1458 | 1458 | 1458 | 1.000 | 1.000 | 0 / 320 |
| uci_bank_marketing | gross_scale | 24 | 2271 | 729 | 1777 | 0.321 | 0.782 | 0 / 640 |
| uci_bank_marketing | plausible_swap | 36 | 4374 | 722 | 725 | 0.165 | 0.166 | 722 / 1679 |
| uci_wine_white | missing | 24 | 364 | 364 | 364 | 1.000 | 1.000 | 0 / 424 |
| uci_wine_white | invalid_type | 24 | 364 | 364 | 364 | 1.000 | 1.000 | 0 / 423 |
| uci_wine_white | gross_scale | 24 | 364 | 91 | 362 | 0.250 | 0.995 | 0 / 423 |
| uci_wine_white | plausible_swap | 24 | 364 | 0 | 0 | 0.000 | 0.000 | 0 / 424 |

All 360 planned scenarios completed, with 18 partial realizations. Exactly 28541 substantive changes were realized out of 29308 selected cells. Zero multiplication was not counted as corruption in the final run. No replacement resampling forced the planned count.

Historical envelopes add coverage for some scale errors but also unverified workload. Plausible substitutions largely survive both checks; Bank cross-field semantics catch a subset. These results motivate a potential detection gap but do not show an LLM can fill it. The controls were not weakened for model comparison.

Numerical baseline qualification results are not substituted for C/D: no live LLM candidates exist. C/D provider, frozen-candidate comparison and safety behavior were exercised only with clearly labelled human fixtures in software tests.
