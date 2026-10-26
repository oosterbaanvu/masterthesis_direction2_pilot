# Incremental detection and workload

The main increment is **selected-candidate findings beyond the same fixed conventional controls on the same held-out batch**. Report extra labelled hits, additional off-label alerts, discarded available labelled hits and marginal label-agreement precision together. A candidate already covered by D adds zero. Empty increments have undefined marginal precision, not precision 1. Controls are fixed independently of test errors and generated proposals.

The strong published-cell results are in [qualification](qualification_experiment.md): Hospital A adds 18 reference hits/471 alerts, B six/six, C zero/zero; Beers A zero/770, B/C zero/zero. Hospital B loses 12 potentially detected reference cells; C loses 18. Off-reference burden is not independently adjudicated false-positive count.

The published-source `strong` label is relative: Hospital still has missing-token screening only; Beers additionally checks lexical numeric ABV/IBU. Hospital's selected ZIP pattern is an ordinary conventional candidate. Full business-control increment is not established there, and no post-test baseline amendment is hidden in the primary comparison.

## Controlled rows under strong existing controls

Each A/B/C cell below gives **extra labelled hits / extra alert rows**, rather than a pooled score. D columns show baseline hits and actual changed-row denominator for that family. Detailed weak/strong precision, recall, F1, off-label workload and lost hits are in `tables/row_results.csv` and source JSONs.

| Source | Family | D hits | Changed rows | A extra hits/alerts | B extra hits/alerts | C extra hits/alerts |
| --- | --- | --- | --- | --- | --- | --- |
| synthetic_balanced_journals | missing | 24 | 24 | 0 / 232 | 0 / 118 | 0 / 0 |
| synthetic_balanced_journals | invalid_type_or_code | 8 | 24 | 8 / 124 | 8 / 124 | 0 / 0 |
| synthetic_balanced_journals | gross_scale | 24 | 24 | 0 / 232 | 0 / 114 | 0 / 0 |
| synthetic_balanced_journals | plausible_swap | 16 | 24 | 8 / 240 | 6 / 126 | 0 / 0 |
| uci_bank_marketing | missing | 24 | 24 | 0 / 17 | 0 / 0 | 0 / 0 |
| uci_bank_marketing | invalid_type_or_code | 24 | 24 | 0 / 16 | 0 / 0 | 0 / 0 |
| uci_bank_marketing | gross_scale | 21 | 24 | 0 / 18 | 0 / 0 | 0 / 0 |
| uci_bank_marketing | plausible_swap | 5 | 24 | 0 / 18 | 0 / 0 | 0 / 0 |
| uci_credit | missing | 24 | 24 | 0 / 478 | 0 / 409 | 0 / 0 |
| uci_credit | invalid_type_or_code | 24 | 24 | 0 / 459 | 0 / 406 | 0 / 0 |
| uci_credit | gross_scale | 15 | 24 | 9 / 487 | 7 / 415 | 0 / 0 |
| uci_credit | plausible_swap | 0 | 24 | 22 / 482 | 17 / 426 | 0 / 0 |
| uci_wine_white | missing | 24 | 24 | 0 / 39 | 0 / 0 | 0 / 0 |
| uci_wine_white | invalid_type_or_code | 24 | 24 | 0 / 39 | 0 / 0 | 0 / 0 |
| uci_wine_white | gross_scale | 24 | 24 | 0 / 41 | 0 / 0 | 0 / 0 |
| uci_wine_white | plausible_swap | 2 | 24 | 2 / 41 | 0 / 0 | 0 / 0 |


## Response to a controlled change

Raw hits can include a row already flagged before alteration. The following separate diagnostic gives D's newly flagged labelled rows and **additional newly flagged labelled rows / added off-label new-alert rows**. Its baseline is D's new-alert set, not D's raw batch set, so the two increment definitions must not be interchanged.

| Source | Family | D new hits | A new hits/off-label | B new hits/off-label | C new hits/off-label |
| --- | --- | --- | --- | --- | --- |
| synthetic_balanced_journals | missing | 24 | 0 / 0 | 0 / 0 | 0 / 0 |
| synthetic_balanced_journals | invalid_type_or_code | 8 | 0 / 0 | 0 / 0 | 0 / 0 |
| synthetic_balanced_journals | gross_scale | 24 | 0 / 0 | 0 / 0 | 0 / 0 |
| synthetic_balanced_journals | plausible_swap | 16 | 6 / 0 | 6 / 0 | 0 / 0 |
| uci_bank_marketing | missing | 24 | 0 / 0 | 0 / 0 | 0 / 0 |
| uci_bank_marketing | invalid_type_or_code | 24 | 0 / 0 | 0 / 0 | 0 / 0 |
| uci_bank_marketing | gross_scale | 21 | 0 / 0 | 0 / 0 | 0 / 0 |
| uci_bank_marketing | plausible_swap | 4 | 0 / 0 | 0 / 0 | 0 / 0 |
| uci_credit | missing | 23 | 1 / 488 | 0 / 0 | 0 / 0 |
| uci_credit | invalid_type_or_code | 24 | 0 / 0 | 0 / 0 | 0 / 0 |
| uci_credit | gross_scale | 14 | 10 / 488 | 1 / 0 | 0 / 0 |
| uci_credit | plausible_swap | 0 | 1 / 0 | 1 / 0 | 0 / 0 |
| uci_wine_white | missing | 24 | 0 / 0 | 0 / 0 | 0 / 0 |
| uci_wine_white | invalid_type_or_code | 24 | 0 / 0 | 0 / 0 | 0 / 0 |
| uci_wine_white | gross_scale | 24 | 0 / 0 | 0 / 0 | 0 / 0 |
| uci_wine_white | plausible_swap | 1 | 0 / 0 | 0 / 0 | 0 / 0 |


Some dtype checks react to pandas batch inference: introducing a floating-point value can turn an originally integral column into float dtype when the worker reconstructs a DataFrame. An unchanged numeric cell may then trigger a type expectation. These are adapter/representation effects, not evidence of independently invalid source values. Credit's raw swap hits largely include pre-existing alerts, while newly triggered swap coverage is much smaller. The before/after diagnostic prevents treating every already-flagged altered row as sensitivity to the change.

The journal primary `strong` suite also omitted explicit numeric guards: its range/equality engine skips nonnumeric strings, so it detects only the eight currency-code changes in the 24-row invalid-type/code case. This is an incomplete conventional baseline, not evidence that an LLM supplied a new business constraint. An explicitly post hoc engineering supplement adds two numeric guards and flags all 24 stipulated invalid rows. The principal experimental files and scores remain unchanged; the supplement cannot support a confirmatory AI-value claim.

Missingness is controlled deletion; invalid type/code is an operational violation. Gross scale and plausible swaps measure recovery of an alteration, which may remain legitimate under the source's semantics. The synthetic journal has a stipulated additional equality contract, not natural financial gold. Strong-suite ceilings and deliberate overlap with injection families can make zero increment unsurprising; this does not prove language models never add value.

The weak suite retains basic schema/missing/type checks; the strong suite adds pre-existing contracts and development-only historical envelopes. Both run through the same engine. No model-selected baseline replacement or test-fitted bound is used. The full weak/strong comparison is preserved, including cases where a weak baseline makes an apparent model gain disappear under stronger controls.

C's known documentary constraints are contained in strong D, so its zero increment there is implied by entailment plus redundancy rejection. A weak-baseline C increment can be recovery of an already known conventional constraint. Neither supports a new-method superiority claim.

For controlled sources, raw batch findings may include pre-existing unadjudicated source alerts. The separate `delta_agreement` uses baseline new alerts and a union of each rule's new alerts relative to the unmodified source. This avoids masking an additional rule finding through subtraction of an aggregate before/after union. New-alert increments and losses have explicit names alongside raw increments. Neither off-injection alerts nor unchanged source values are declared clean by assumption. No aggregate F1 combines these incompatible populations.
