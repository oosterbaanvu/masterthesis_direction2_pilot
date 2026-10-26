# Executed free-model research

The core exploratory experiment ran on 26 October 2026 (timestamps stored in UTC; local reporting date Europe/Amsterdam). **56 genuine local model-generation requests completed**, with zero paid calls. Qwen2.5-Coder-7B-Instruct Q4_K_M ran through pinned CPU llama.cpp. Neither Gemini nor Ollama performed inference. All previous phases and negative findings remain separate and immutable.

The bounded populations are four original-prompt smoke requests, all 48 requests in a separately frozen GX-syntax-guided condition, and four new schema-only Hospital/Beers requests. The original full 48 condition was stopped after its four-source smoke produced no executable rules; its outputs were not repaired. Thus this is not 48 successful calls under the original unchanged prompts. The guided condition retains all original source/doc/instruction/seed factors plus an explicitly documented generic syntax appendix.

The model emitted **211 raw rule objects**. Strict whole-response parsing admitted **183 candidate occurrences**, representing **62 unique candidates within source and condition**; **47** of those executed on development data (160 executable occurrences). These counts have different denominators. Malformed bundles and duplicate IDs remain in exact raw responses and are not silently salvaged. No independently adjudicated semantic-validity rate exists.

| Condition | Source | Calls | Parsed | Rule occurrences | Unique | Executable unique |
| --- | --- | --- | --- | --- | --- | --- |
| benchmark | raha_beers | 2 | 2 | 8 | 8 | 8 |
| benchmark | raha_hospital | 2 | 2 | 8 | 8 | 8 |
| guided | synthetic_balanced_journals | 12 | 12 | 45 | 7 | 7 |
| guided | uci_bank_marketing | 12 | 9 | 27 | 5 | 5 |
| guided | uci_credit | 12 | 9 | 36 | 12 | 8 |
| guided | uci_wine_white | 12 | 12 | 48 | 11 | 11 |
| original | synthetic_balanced_journals | 1 | 1 | 4 | 4 | 0 |
| original | uci_bank_marketing | 1 | 0 | 0 | 0 | 0 |
| original | uci_credit | 1 | 1 | 4 | 4 | 0 |
| original | uci_wine_white | 1 | 1 | 3 | 3 | 0 |


## Principal held-out reference result

These are single-column cell scores with identical fixed strong controls included. B uses development labels; C does not. Off-reference means disagreement with the author reference, not independently proven false alerts.

Here `strong` names an experimental configuration, not an industry-complete suite. Hospital has only generic missing-token screening in both configurations; Beers adds lexical numeric screening of ABV/IBU. No independently justified complete business-contract baseline exists for those benchmarks. Hospital's gain therefore does not establish value beyond credible domain-specific conventional checks. UCI/journal stronger suites have the fuller pre-existing contracts.

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


The UCI and journal controlled-family row outcomes, including zero increments and discarded coverage, are detailed in [incremental results](incremental_detection_results.md). They are not pooled with these reference cells. All ten completed evaluations can be rescored without another model request; [reproduction instructions](reproduction.md) identify the commands and frozen inputs.

## Evidence categories and limits

New model responses, prior published SEC outputs, handwritten component fixtures, controlled injections, published references and pending human reviews retain distinct labels. Model calls do not become independent source replications. Technical execution does not establish meaning or applicability. New financial evidence is a controlled journal/service demonstration, not real-bank deployment. Original reserved SEC bases remain untouched.

The recommendation is **CONDITIONAL GO for a narrower empirical reliability study**, with a novelty and independent-review gate; NO-GO for a new generic algorithm or automatic production promotion claim. The [proposal](thesis_proposal.md) and [decision](final_go_no_go.md) specify what requires supervisor approval. No API key is needed to reproduce this completed local experiment.
