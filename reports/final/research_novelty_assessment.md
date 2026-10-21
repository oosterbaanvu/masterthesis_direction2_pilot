# Novelty assessment and narrowed question

The broad proposal, “generate, execute and qualify LLM data-quality rules for finance,” is **not supported as a novel MSc contribution**. LeDQeR, Akella, LLM-DQR, Auto-Test and SPADE establish major ingredients. The Bayesian verification abstract overlaps directly with shared candidate sets, semantic priors and observed SQL violations. Its inaccessible full method prevents a positive priority claim.

The starting question remains useful as a practical motivation:

> How reliably can AI-generated data-quality rules be selected for new data sources using source documentation and unlabeled validation data, while preserving incremental error detection beyond existing controls?

It is too broad for a confirmed contribution. A narrower provisional question is:

> Under documented and undocumented source changes, when does label-free qualification of a frozen set of generated relational checks falsely promote unjustified rules or discard checks with incremental labelled coverage, relative to technical filtering, contract matching and a label-assisted coverage reference?

This would be an **empirical reliability and limitation study**, not a new algorithm claim. A credible contribution would establish a previously unreported failure boundary with independently adjudicated rule meaning and source-group evaluation. Financial tables supply demanding relational cases; financial context alone does not establish novelty.

## Precise distinctions and risks

| Distinction | Why it could matter | Why it is not yet a novelty proof |
|---|---|---|
| Known-error generation versus arbitrary source onboarding | LeDQeR selects a known dirty record even in JustDirty | Akella already uses schema/sample/domain information; LLM-DQR and broader constraint discovery must be compared |
| Label-free versus labelled selection | LeDQeR precision/greedy stages require labels; practical new sources often lack error labels | Auto-Test learns reusable constraints; Bayesian verification directly combines semantic and unlabelled evidence |
| Same candidates and same controls | Isolates selection from generation and measures marginal benefit | Shared-candidate comparisons and augmentation already have precedents |
| Relational units/signs/periods and source change | Applicability can fail while execution and empirical violation rates remain unchanged | Different domain representation is an engineering difference unless a new empirical limitation is demonstrated |
| Abstention together with rejected useful detections | Prevents “reject everything” from appearing successful | Selective prediction and risk/coverage tradeoffs are established; terminology is not a contribution |

An important design limitation follows without a model experiment: the same observed unlabelled values can be compatible with two source contracts, one requiring a constraint and one permitting exceptions. Empirical violation frequency alone cannot distinguish those contracts. This is a design argument, **not a new theorem or an executed result**. Documentation, justified assumptions or independent labels are necessary to resolve meaning.

Exact contract matching also exposes a redundancy problem. If every documented relation is already implemented in the conventional control suite, accepting only exact contract matches can add no novel detection. If a source contract is incomplete, an unlabelled sample cannot by itself certify additional rules. The experiment must examine that tradeoff rather than assume C improves both precision and recall.

## Decision gate

Before claiming a thesis gap, obtain the Bayesian full text/package, map its information access, supervision, source shifts and independent semantic evaluation, and compare Akella/Auto-Test/SPADE on the same axes. Missing evidence is an unresolved gate, not a favorable result. If the narrowed question is already adequately answered, either specify a genuinely different limitation that the supervisor accepts or stop this direction.

Negative empirical results can support a thesis when the question and labels are sound. Failure to establish independent meaning, fair baselines or a distinct question cannot be repaired by more model calls, a larger dashboard or a renamed filter. Current recommendation is bounded continuation, with no unconditional claim of novelty.
