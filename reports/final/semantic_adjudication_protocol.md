# Independent semantic review protocol — prepared, not executed

Review unit: a frozen executable candidate plus its source/context. Evaluate validity and applicability separately using VALID / INVALID / CANNOT_JUDGE, not a single plausible/implausible score. Successful arithmetic or code execution does not answer either question.

1. Freeze source documents, candidate implementation and input hashes before review. Assign anonymous rule/source IDs. Hide model, selector decision, development precision and other reviewer's answer.
2. Each reviewer cites the authoritative source and exact scope, period, unit/scale, sign, rounding and missing-value conventions. Unsupported assumptions are recorded, not repaired silently. For SEC proposals, check the original filing context before accepting analyst-proposed dash-zero behavior.
3. Record independent validity and applicability judgments and a rationale. A valid equation may be inapplicable to a table with mezzanine interests, differently scoped totals or an unsupported period. A format convention is not a universal accounting law.
4. Independently label actual target violations and localization separately. For SEC, state whether the task concerns altered cells or logical participants. Do not convert every candidate alert into an error because it violates the candidate.
5. Review accepted, rejected and abstained candidates. Predefine usefulness as validity plus applicability plus an additional adjudicated target error beyond the frozen controls. Report valid rules with no observed increment separately.
6. Freeze both initial reviews, then adjudicate disagreements. Preserve originals. Report numbers reviewed, cannot-judge rate, raw agreement and a suitable chance-corrected statistic with its denominator. No agreement value exists yet.

`results/final/semantic_review_packet.csv` has eight empty reviewer slots for four analyst SEC proposals; the local source is identified by development base 08001 and input hash in the diagnostic manifest. The rule definitions and coordinates are in `financial_contract_proposals.json`. These entries are **not model candidates**. The packet is intentionally unfilled; no person has completed an independent judgment.

Two reviewers with financial-context competence are preferred. If only one is available, state that explicitly and do not claim inter-rater reliability. Model opinions can be a separate method but never masquerade as human ground truth. If documentation/original filing rights prevent source inspection, mark CANNOT_JUDGE and restrict or stop the associated experiment.

Production activation remains separate from this research protocol. Local review-state strings and service actor labels demonstrate a lifecycle; they do not authenticate an enterprise reviewer or provide tamper-proof authorization.
