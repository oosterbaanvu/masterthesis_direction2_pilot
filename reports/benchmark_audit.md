# SEC-FinTables release audit

Pinned source: `XIEFOX/SEC-Fintables@f82f80363da1afedbe8b35cede0bae802edab20c`. Machine-readable evidence: `results/sec_audit.json`, `results/sec_splits.json`, acquisition hashes and local manual sample. Original CSV/JSON data are read-only and ignored.

| Condition | CSVs / GT entries | `errNum=0` | Positive tables | Annotated locations | Multiline-cell tables | Repeated row-label tables |
|---|---:|---:|---:|---:|---:|---:|
| 1% | 1,000 / 1,000 | 369 | 631 | 4,364 | 410 | 484 |
| 10% | 1,000 / 1,000 | 373 | 627 | 4,408 | 410 | 484 |
| 50% | 1,000 / 1,000 | 376 | 624 | 4,451 | 410 | 484 |

The same 1,000 five-digit base IDs occur in all conditions. There are no missing GT filename references, unreferenced CSVs, duplicate GT IDs or nonrectangular **parsed CSV-record** widths. Embedded newlines make physical line counting incorrect. Header depth varies; some tables have no header row, others several. Repeated first-field labels are blank labels, not repeated nonempty labels in this release; nevertheless 10/8/10 annotated locations reference ambiguous repeated blank labels. Row-name/column-coordinate scoring is not always unique physical-cell scoring.

The percentages mean **numeric VAL perturbation scope** (paper §3: e.g. ±1%, ±10%, ±50%), not a fraction of erroneous tables/cells; FMT/MISS are separate transformations. Do not infer prevalence from directory names. Paper §3 describes 11,134 original tables, a sampled 7,097-table subset, 92,261 synthetic instances and 103,395 total instances. The repository exposes 3,000 evaluation variants of 1,000 bases, not that complete collection. `clean_data` contains preprocessing scripts, not a trustworthy clean counterpart for every target. None is used as a detector input.

The paper explicitly requests **all cells involved in a violated constraint**. Annotation locations include a modified value plus associated cells; `errNum` is not simply the number of injected changes. Missing-value counts and location counts are different tasks. This release therefore cannot be silently evaluated as “which cells were actually corrupted?”

`col_idx=1` addresses the second parsed CSV field; the row-name field is index 0. This is confirmed in development examples such as base 08002 (aircraft commitments/deliveries). The evaluator follows these coordinates literally. The header row is not universally the first row. Exact matching of a truncated annotation row name can fail even with a valid column number: base 08695's long RSU/PSU label is truncated in GT, leaving one unresolved location per condition. The audit's `locations_invalid_column=1` is this unresolvable row/column pair, **not an additional independently invalid column**.

Eight table-condition records have consistency issues: two MISS type/count disagreements in 1%; base 08692 has zero error count but nonempty error types in all three conditions; base 08695 has an unresolved row label in all three. `errNum` agrees with deduplicated `errLoc` length otherwise, and no negative/noninteger counts or `missNum>errNum` were found. Zero-count examples can be identified operationally, but 08692 is not internally consistent and zero injected errors do not prove independently clean original financial statements.

Metadata-only cross-condition hash inspection found 370 base IDs with identical CSV bytes under all three settings; two of these have VAL labels in all three. This demonstrates dependence and warrants investigating rounding/generation behavior; it is not proof that every annotation is incorrect. No target clean table was used for this comparison.

## Development-only manual inspection

Twelve stratified table-condition examples were inspected directly: FMT/MISS/VAL/NONE for each setting. Some IDs repeat across conditions, so this is **not 12 independent tables**. The local sample export contains 24 selectable strata; exporting a sample is not counted as manually inspecting all 24.

| Setting | Examples inspected | Observation |
|---|---|---|
| 1% | 08009 FMT; 08021 MISS; 08022 VAL; 08489 NONE | 08009 marks a total carrying an extra `%` plus its four normal-looking contributors. 08021's missing net income has associated ordinary values. 08022 is headerless and its sum includes dash-as-zero conventions. 08489 contains many presentation blanks on a zero-count table. |
| 10% | 08010 FMT; 08012 MISS; 08058 VAL; 08001 NONE | `(1).00` is anomalous lexical formatting; 08012 uses multiple/multiline headers and a missing interest-cost value; 08058 requires accounting semantics; 08001 requires horizontal segment and elimination interpretation. |
| 50% | 08012 FMT; 08009 MISS; 08022 VAL; 08021 NONE | `$32` is numerically legitimate but annotated FMT among associated cells; local formatting expectations are not self-evident. 08009's total is blank. 08021 is numerically negative and conventionally formatted despite zero injected errors. |

Additional mixed examples 08002/08004 and the unresolved 08695 row were inspected during diagnosis. The 08020 mixed-type preview includes contract-description text rather than an ordinary numerical statement, which limits blanket arithmetic rules.

Semantically detectable cases require visible, justified relations and tolerance for rounding. A missing cell alone may be presentation, and an isolated wrong but plausible value may be unidentifiable without a relation. Formatting anomalies need an explicit representation policy. The pilot records these distinctions and does not adjudicate every released location as a true altered cell.

## Split, rights and suitability

Hash-grouped split: 582 development, 208 exploratory, 210 reserved base IDs; all conditions remain grouped. New baseline and robustness scores use only the 208 exploratory IDs. All 210 reserved bases (630 table-condition variants) remain unscored by new methods. Retrospective released-output reproduction uses all 1,000 bases solely to establish evaluator compatibility; public prediction availability and benchmark memorization remain threats to a future model study.

No repository licence file was found. The paper states the underlying SEC reports may be used for research; that statement does not establish a reusable licence for the curated annotations or predictions. Raw data, original predictions and papers are not committed or redistributed. Qualification: **CONDITIONAL, logical-constraint-participation benchmark**, not an independent natural financial cell-corruption gold standard. Resolve rights, annotation ambiguities and task definitions before using it for a confirmatory rule-qualification thesis.
