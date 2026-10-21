# Bounded financial-rule support and actual evaluation

The new module supports **signed linear equalities over explicitly identified cells**. It is an experimental adapter alongside the preserved service, not an unrestricted accounting reasoner or an enterprise approval mechanism.

Each term records row label, optional occurrence for repeated labels, parsed CSV column, coefficient, currency unit and scale. Contracts require semantic and unit evidence and an absolute rounding tolerance. Accounting forms `$1,234`, `(1,234)`, `$(163)` and `($163)` parse with exact decimal arithmetic. Percentage strings, missing amounts, malformed numbers and an unspecified dash-as-zero policy remain unresolved. Different currencies cannot be combined; NaN/infinite scales or coefficients are rejected. Every arithmetic finding includes actual participating row offsets and columns, coefficients, scaled contributions and residual.

The representation handles documented totals of components, revenue/expense/profit relations and signed subtotals across rows or columns. Comparative periods can be expressed only through separately specified coordinates and a justified relation. It never infers that all rows sum to a total. Repeated labels require disambiguation. No comparative-period financial relation was independently verified or evaluated in this phase.

## Real SEC development demonstration

Only development base **08001**, condition 1%, is loaded. The header explicitly says `(US$ in millions)` and names six segments, including Eliminations, followed by Total. Four analyst proposals compare the total with those headed components: external-customer net sales, cost of goods sold, gross profit and total assets. Scale is one million USD. The proposed dash-zero convention and semantic scope still require independent review. A 3.5-million absolute tolerance is derived from seven displayed rounded amounts at at most .5 million each; it is not tuned to error labels.

| Measure | Actual result |
|---|---|
| Proposals | 4 |
| Arithmetic diagnostics | 4 satisfied; residual zero in each |
| Production gate | **4 NEEDS_REVIEW**, no active rule |
| Independently reviewed contracts | **0** |
| New error-detection precision/recall | Not measurable |
| SEC ground-truth files used to construct contracts | 0 |
| Reserved SEC tables accessed | 0 |

An explicitly labelled diagnostic mode evaluates the arithmetic without approval and sets `detection_claim=false`. Its satisfied results do not validate the proposed meaning. The strict path refuses promotion while review is pending. No review state is manufactured.

## FinRule provided-principle diagnostic

The acquired paper and BS01 prompt provide the balance equation, including mezzanine and noncontrolling interests. A separate, conservative adapter recognises only explicit Total Assets, Total Liabilities and Total Equity, optionally one mezzanine item; noncontrolling interests already in Total Equity are not added twice. It does not sum all rows or guess aliases.

| Released variant | Satisfied | Display-equation violation | Unresolved | Semantic validity conclusion |
|---|---:|---:|---:|---|
| BS-00, nominal original | 29 | 10 | 173 | None; unit/rounding/transcription/scope not independently checked |
| BS-01, nominal injected | 20 | 19 | 173 | None; no claim of independent detection precision |

These are exact displayed-number, zero-tolerance **component diagnostics**, not results of AI-generated rule selection. Most unresolved cases lack this exact total scope; other failures concern layout, duplicates or numeric representation. The normalized markdown does not independently establish currency/scale/rounding. The result supports cautious qualification of the resource and shows why automatically applying a universal equation is unsafe.

The unfilled `results/final/semantic_review_packet.csv` provides two reviewer slots for every SEC proposal. Reviewers must check original context, unit, signs, eliminations, presentation blanks and rounding. Without this review the requested independently verified financial sample is **still unavailable**. Tests cover signed cross-row execution, coordinates, negative accounting notation, scale, tolerance, duplicate labels, missing policies, invalid units and pending-review enforcement. This software validation cannot substitute for accountant judgments.

Evidence: `results/final/financial_diagnostics.json`, `financial_contract_proposals.json`, `finrule_audit.json`; implementation: `src/dqpilot_final/financial.py`. Original service code and historical results remain unchanged.
