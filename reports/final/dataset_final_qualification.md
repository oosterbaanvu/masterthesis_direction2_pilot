# Final dataset qualification

Fourteen sources are registered; registration is not full scientific qualification. The original thirteen-source registry and acquisition results are preserved. `config/final/datasets.yaml` adds roles, dimensions, source references, rights and current status; the parent registry retains exact schemas, citation details and byte pins. Raw files and vendor checkouts remain outside Git.

| Source | Dimensions / status | Label interpretation | Appropriate role; main restriction |
|---|---|---|---|
| UCI Credit, DOI 10.24432/C55S3H | 30,000 × 25 | Default is a prediction target; no natural cell-error gold | Controlled financial error injections and service demo; targets excluded; negative balances can be valid; inherited contract domains are provisional |
| UCI Bank Marketing, DOI 10.24432/C5K306 | 41,188 × 21 | `y` is a prediction target | Controlled financial/generalization and descriptive deliveries; `unknown` and `pdays=999` are legitimate sentinels; no customer-level dated longitudinal truth |
| UCI White Wine, DOI 10.24432/C56S3T | 4,898 × 12 | Sensory quality is not DQ truth | Nonfinancial controlled generalization; no natural error labels; provisional ranges require a defined experiment |
| Raha Flights | 2,376 × 7 | Published cross-source/clean-reference differences, including uncertain repairs | Conditional reference agreement and LeDQeR components; group flight entities; not re-adjudicated airline truth |
| Raha Beers | 2,410 × 11 | Missingness, units, values and representation are mixed | Representation sensitivity and reproduction; explicit header adapter; group breweries; strict differences are not semantic precision |
| Raha Tax | 200,000 × 15; LeDQeR subset 6,000 | Synthetic/reference normalization; ZIP zeros and rate formatting matter | Scale and normalization sensitivity; do not pool full/source-subset scores; released pk does not establish source independence |
| Raha Hospital | 1,000 × 20 | Published predominantly typo/synthetic reference discrepancies | Narrow typo sanity and reproduction; group providers; not financial logic truth |
| Raha Rayyan | 1,000 × 11 | Bibliographic repair/date/header uncertainty | Workload and independent review only; withhold accuracy rather than assign zero |
| Jung Restaurant | 864 × 6 | Published synthetic variant; reference class changes excluded | Conditional missingness track; 125 eligible differences in parent analysis; row alignment remains an assumption |
| Jung Cars | 406 × 9 | Published synthetic variant; 710/820 strict differences numerically equivalent on explicitly typed fields | Conditional missingness track with 110 eligible differences; no blanket numeric normalization of codes |
| Feedzai BAF Base | Not acquired here; expected one million rows and 32 fields | Synthetic population; fraud_bool is not DQ gold | Optional engineering/generalization only; current credential absent and licence conflict unresolved |
| Give Me Some Credit | Not acquired here; expected training 150,000 rows, ID + 11 fields | SeriousDlqin2yrs is default prediction, not DQ gold | Optional source onboarding only; authentic competition access/terms required; no substitute mirrors |
| SEC-FinTables | 3,000 variants of 1,000 bases | Synthetic errors with labels for **all logical participants**, not exclusively modified cells | Conditional financial consistency and existing released-output rescoring; ambiguous coordinates and rights; reserved 210 bases remain untouched by new phase |
| FinRule-Bench | **Acquired** 147 files, 23,343,599 bytes; released originals BS 212, CF 323, SE 287, SI 300 | Model-transcribed originals, principle-aware synthetic variants and released task labels | Conditional provided-principle execution/diagnosis and release audit. Not yet independent semantic-rule gold |

Column counts above include original prediction targets/IDs where present. LeDQeR adds pk and label metadata and can retain source index columns; its widths must not be substituted for the parent Raha schemas. Exact observed columns are in the manifests.

## Kaggle: observed credential state and integrity behavior

Official Kaggle SDK 2.2.4 supports `KAGGLE_API_TOKEN`. The variable and legacy token files are absent in this running task. SDK authentication was attempted without printing values or raw exception text; no authenticated operation or download could run. This is **unavailable credentials**, not evidence that the user's token is invalid or that competition terms were rejected. The reusable draft records the secret requirement and Kaggle destinations. Applying/publishing the configuration and starting a fresh task may be necessary for newly configured bindings.

The acquisition helper never accepts competition terms automatically. An authenticated competition-file listing followed by the authorised training-file request will test actual access. Rule-acceptance status cannot be determined from a missing-token run. A successful download must have the original 150,000 rows, leading unique ID, exact expected columns and binary target; it receives an observed SHA-256, read-only mode and an explicit first-authentic-download status. There is no invented GMSC hash. `KAGGLE_CONFIG_DIR` points into ignored cache because the SDK's default home directory is not writable.

BAF's **publisher datasheet Q44**, at Feedzai commit `3377cfd8fc20edcda3dd9dd14c10ed3dd276c6de`, explicitly says **CC BY-NC-ND 4.0**. This conflicts with prior Kaggle NC-SA metadata. The repository's code licence is a separate document and does not resolve that dataset conflict. An Avanade internship does not automatically determine commercial/noncommercial status. Until clarified, BAF download/transmission is not treated as licensed merely because a listing becomes accessible.

## FinRule release audit and suitability

Public access initially failed. An identifiable research user agent and the service's correct `files?path=...` endpoint allowed a bounded snapshot. The MIT notice and README's research/evaluation restriction are retained locally; no original tables or papers are redistributed. There is no exposed full Git commit, so every downloaded file has a content hash. Source images were not acquired, and transcriptions were not checked against original filings.

The paper reports 1,117 original statements (CF 318), but the acquired markdown originals contain **1,122 headings (CF 323)**, each unique within that CF file. This mismatch remains unresolved. Multi-rule BS-HARD has 212 table titles but only 189 truth keys: 23 tables lack a matching truth key. Mixed CF/SE/SI files each contain 100 table blocks but only 97/95/90 unique titles and corresponding truth records. Do not silently apply dictionary-last-wins or count duplicated titles as independent sources.

Released injection-verification CSVs contain BS 307 PASS / 203 FAIL, CF 0 PASS / 306 FAIL, and SI 143 PASS / 367 FAIL. These are **upstream verification-log statuses**, not our model accuracy and not proof that every FAIL is an incorrect benchmark label. Messages include expected-pattern and source-line mismatches; their relationship to the final processed files needs investigation. The complete deterministic validation implementation claimed by the paper was not established in this snapshot.

A fixed explicit-total balance-equation diagnostic can resolve only 39/212 BS tables in each of BS-00 and BS-01. Scope/layout/numeric uncertainty causes abstention on the rest. Even on BS-00 it finds 10 display-equation discrepancies; no independent review establishes whether these represent transcription, scope, rounding or actual financial inconsistencies. Hence this is a useful **conditional resource audit**, not a validated replacement gold standard.

## Splits, rights and valid estimands

UCI sources are registered under CC BY 4.0; Raha upstream dataset rights and Jung/SEC redistribution remain conditional. Raw visibility is not permission to transmit data to a model. Every actual model input needs a source-specific rights decision; public company tables do not remove curated-data conditions. No private bank data is used.

Keep duplicate records, entity groups, financial periods/variants and issuers together. Split canonical SEC base IDs before any new method; the existing reserved 630 variants remain unscored and unopened by the new phase. All newly inspected FinRule material is exploratory; do not later describe it as a pristine confirmatory holdout. Future confirmation needs new eligible source groups or a genuinely isolated release split.

Accuracy is valid only for a specified label population: controlled injection recovery, qualified author-reference agreement, independently reviewed financial-rule validity, or logical-participant localization. These are different estimands. Do not pool them into a leaderboard. TableEG Credit repairs remain rejected as independent gold, and fraud/default labels remain prediction targets.
