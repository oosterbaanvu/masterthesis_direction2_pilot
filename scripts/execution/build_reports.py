"""Render measured results after all generation and scoring; do not invent missing evidence."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
base = root / "results/execution"
out = root / "reports/execution"
s = json.loads((base / "summary.json").read_text())
service = json.loads((base / "service_demo.json").read_text())
evals = [json.loads(p.read_text()) for p in sorted((base / "evaluation").glob("*.json"))]
cells = [
    r for e in evals for r in e.get("published_single_column_cell_track", []) if r["baseline"] == "strong"
]
controlled = [
    r
    for e in evals
    if e["condition"] == "guided"
    for r in e["results"]
    if r["baseline"] == "strong" and r["arm"] in ["A", "B", "C", "D"]
]


def table(headers, values):
    return (
        "| "
        + " | ".join(headers)
        + " |\n| "
        + " | ".join(["---"] * len(headers))
        + " |\n"
        + "".join("| " + " | ".join(str(x) for x in row) + " |\n" for row in values)
    )


def write(name, text):
    (out / name).write_text(text.strip() + "\n")


def fmt(v):
    return f"{v:.3f}" if isinstance(v, float) else str(v)


yield_table = table(
    ["Condition", "Source", "Calls", "Parsed", "Rule occurrences", "Unique", "Executable unique"],
    [
        [
            r["condition"],
            r["source"],
            r["requests"],
            r["parsed_responses"],
            r["candidate_occurrences"],
            r["unique_candidates"],
            r["executable_unique"],
        ]
        for r in s["generation_yield"]
    ],
)
cell_table = table(
    [
        "Source",
        "Arm",
        "TP",
        "Off-reference",
        "FN",
        "Precision",
        "Recall",
        "F1",
        "Extra reference hits",
        "Extra alerts",
    ],
    [
        [
            r["source"],
            r["arm"],
            r["agreement"]["tp"],
            r["agreement"]["fp"],
            r["agreement"]["fn"],
            fmt(r["agreement"]["precision"]),
            fmt(r["agreement"]["recall"]),
            fmt(r["agreement"]["f1"]),
            r["incremental_labelled_hits"],
            r["additional_workload_cells"],
        ]
        for r in cells
    ],
)
write(
    "execution_summary.md",
    f"""
# Executed free-model research

The core exploratory experiment ran on 26 October 2026 (timestamps stored in UTC; local reporting date Europe/Amsterdam). **{s["actual_completed_requests"]} genuine local model-generation requests completed**, with zero paid calls. Qwen2.5-Coder-7B-Instruct Q4_K_M ran through pinned CPU llama.cpp. Neither Gemini nor Ollama performed inference. All previous phases and negative findings remain separate and immutable.

The bounded populations are four original-prompt smoke requests, all 48 requests in a separately frozen GX-syntax-guided condition, and four new schema-only Hospital/Beers requests. The original full 48 condition was stopped after its four-source smoke produced no executable rules; its outputs were not repaired. Thus this is not 48 successful calls under the original unchanged prompts. The guided condition retains all original source/doc/instruction/seed factors plus an explicitly documented generic syntax appendix.

The model emitted **{s["raw_declared_rule_objects"]} raw rule objects**. Strict whole-response parsing admitted **{s["candidate_occurrences"]} candidate occurrences**, representing **{s["unique_candidates_within_source_and_condition"]} unique candidates within source and condition**; **{s["executable_unique_within_source_and_condition"]}** of those executed on development data ({s["executable_occurrences"]} executable occurrences). These counts have different denominators. Malformed bundles and duplicate IDs remain in exact raw responses and are not silently salvaged. No independently adjudicated semantic-validity rate exists.

{yield_table}

## Principal held-out reference result

These are single-column cell scores with identical fixed strong controls included. B uses development labels; C does not. Off-reference means disagreement with the author reference, not independently proven false alerts.

Here `strong` names an experimental configuration, not an industry-complete suite. Hospital has only generic missing-token screening in both configurations; Beers adds lexical numeric screening of ABV/IBU. No independently justified complete business-contract baseline exists for those benchmarks. Hospital's gain therefore does not establish value beyond credible domain-specific conventional checks. UCI/journal stronger suites have the fuller pre-existing contracts.

{cell_table}

The UCI and journal controlled-family row outcomes, including zero increments and discarded coverage, are detailed in [incremental results](incremental_detection_results.md). They are not pooled with these reference cells. All ten completed evaluations can be rescored without another model request; [reproduction instructions](reproduction.md) identify the commands and frozen inputs.

## Evidence categories and limits

New model responses, prior published SEC outputs, handwritten component fixtures, controlled injections, published references and pending human reviews retain distinct labels. Model calls do not become independent source replications. Technical execution does not establish meaning or applicability. New financial evidence is a controlled journal/service demonstration, not real-bank deployment. Original reserved SEC bases remain untouched.

The recommendation is **CONDITIONAL GO for a narrower empirical reliability study**, with a novelty and independent-review gate; NO-GO for a new generic algorithm or automatic production promotion claim. The [proposal](thesis_proposal.md) and [decision](final_go_no_go.md) specify what requires supervisor approval. No API key is needed to reproduce this completed local experiment.
""",
)
t = s["timing"]
m = json.loads((base / "local_model.json").read_text())
write(
    "free_model_setup.md",
    f"""
# Working free-model configuration

The successful provider is **local CPU llama.cpp**, model `{m["base_model"]}`, official GGUF revision `{m["weights_revision"]}`, quantization `{m["quantization"]}`, Apache 2.0. Weight SHA-256: `{m["weights_sha256"]}`. Exact source commit: `{m["runtime_commit"]}`. The original built server binary SHA-256 is `{m["runtime_binary_sha256"]}`. The archive build inherited an outer-repository Git label; explicit source commit/archive checksum, not that embedded label, establishes source provenance.

Gemini key and explicit free-project confirmation were absent. No Gemini generation/model substitution was attempted. A key alone would not prove an unbilled account; this route remains optional. No paid API, rented GPU or automatic billing fallback exists in the local runner. Existing historical paid-model proposals are superseded for this execution.

Ollama 0.40.11 was acquired from its official release and checksum verified (`results/execution/acquisition.json`). The user-local installation succeeded; `serve` failed attempting `/home/agent/.ollama/id_ed25519` because the home directory is read-only. No HOME override or root workaround was used. Registry access was also restricted. The permitted equivalent runtime actually loaded verified weights and generated the saved responses; changing runtime is not claimed to have fixed the Ollama registry path.

## Measured resources and performance

Cgroup limits are four equivalent vCPUs and 32 GiB RAM, with no NVIDIA device. The server binds only to literal 127.0.0.1, has one inference slot and requires a random local bearer token in an ignored mode-600 file. Model requests use an 8,192-token context, 2,048 output-token ceiling, four CPU threads, zero GPU layers, temperature 0, top-p 1, repeat penalty 1, seeds 11/23/37 and JSON-constrained output. No public preview or hosted Ollama route is used.

Across {s["actual_completed_requests"]} real calls: median wall time **{t["median_wall_seconds"]:.1f} s**, median measured prompt throughput **{t["median_prompt_tokens_per_second"]:.2f} tokens/s**, median generation throughput **{t["median_generation_tokens_per_second"]:.2f} tokens/s**; peak observed server RSS **{t["peak_observed_server_RSS_bytes"] / 1024**3:.2f} GiB**. {t["missing_RSS_instrumentation_count"]} early request records have an instrumentation sentinel of zero, meaning unavailable, not zero RAM. The monitor was corrected without rewriting those records. Some requests queued behind a second client while the server remained single-slot; walltime includes queueing. Native token speeds exclude that queue. Weight acquisition took 346.9 seconds; build/acquisition time is separate from inference.

Actual reported token usage is **{s["usage"]["prompt_tokens"]} input + {s["usage"]["completion_tokens"]} output = {s["usage"]["total_tokens"]} total**. Server usage and prefix-cache details are preserved per call; do not interpret cached prefix tokens as new processing speed. API inference charge is **US$0**. Infrastructure, electricity and labour were not priced and are not claimed free.

## Paper model and alternatives

The inspected LeDQeR uses GLM-4.7-Flash AWQ4, Qwen3-Coder-30B-A3B AWQ4 and Gemma-4-31B FP8, not this 7B Q4 GGUF configuration. Akella reports Gemma-3-12B/Qwen2.5-Coder-32B. Model size, family, quantization, prompt context and hardware all differ; no paper performance equivalence follows.

`large_model_feasibility.json` records Qwen3-Coder-30B-A3B's 18,556,689,568-byte community GGUF and prior sizing. The full expert weights remain resident despite 3B active parameters. Short-context memory sizing is plausible, but the current disk footprint fails the eight-GiB headroom policy without deliberate cache cleanup. Exact AWQ/GPU execution is unavailable. No 30B weights were fully downloaded, loaded or benchmarked; neither speed nor inherent CPU impossibility is inferred. The viable 7B run was retained. The 3B fallback was unnecessary and was not silently mixed into conditions.

## Reuse and restart

Run `PYTHONPATH=src envs/final/.venv/bin/python scripts/execution/acquire_local.py` to verify/reuse or acquire/build pinned artifacts, then `... scripts/execution/start_local.py`. The latter verifies authenticated model listing and tokenization without adding a generation request. Cached outputs can be evaluated with the server stopped. Full commands and dataset restoration are in [reproduction](reproduction.md). The durable cache quarantines incomplete requests; successful matching calls are reused. Runtime/hardware changes can alter new generation despite fixed seed; cached output rescoring is the reproducibility guarantee.
""",
)
write(
    "generated_rule_results.md",
    f"""
# Actual generated candidates and technical evaluation

**{s["actual_completed_requests"]} real requests; {s["raw_declared_rule_objects"]} emitted raw rule objects; {s["candidate_occurrences"]} parser-admitted occurrences; {s["unique_candidates_within_source_and_condition"]} unique source/condition candidates; {s["executable_unique_within_source_and_condition"]} executable unique candidates.** Uniqueness is normalized AST constructor syntax (keyword order ignored), not proof of distinct semantics. Duplicate rules across sources/conditions remain separate experimental items.

{yield_table}

`tables/generation_yield.csv` includes duplicate and executable-occurrence counts. `tables/prompt_strata.csv` separates documentation, instruction variant and seed-response diversity. `response_parsing_diagnostics.json` distinguishes emitted objects from accepted bundles. The parser is strict and rejects the entire bundle for duplicate IDs; its saved `MALFORMED_OR_TRUNCATED` label includes such schema failures even when finish reason is STOP and JSON is valid. The diagnostic names the actual observed reason; no missing token usage or truncation is invented.

## Inspectable failures and proposals

The original Wine smoke returned GX class references without complete constructor calls; Credit and journals used obsolete/unsupported methods. All 11 admitted original proposals fail the technical gate; the original Bank bundle emitted four rule objects but failed duplicate-ID validation. All seven rejected bundles across conditions have this duplicate-ID cause, not actual output truncation. The separate generic syntax appendix was frozen from technical smoke evidence before any new held-out detection score. The 48 adapted prompts were then retained regardless of Hospital/Beers results. Generic example bounds 0..10 may influence content, so this is not a clean causal syntax-only ablation.

A real journal proposal describes debits equalling credits but calls `ExpectMulticolumnSumToEqual` on both positive columns with `sum_total=0`. It can execute, yet its expression differs from the intended equality. This is an inspectable scenario-contract disagreement, not a fabricated independent semantic-review verdict. Other actual proposals implement direct pair equality correctly under the stipulated scenario. Both remain in the frozen set.

A Beers proposal constrains `abv` to 3..15 and `ounces` to 0.5..12, supplying generated web citations. Those citations are unverified model text; source units and packaging exceptions are not established by a plausible URL. Hospital includes an executing phone pattern that flags every development row. Large violation counts alone cannot determine whether the rule, representation or source is wrong. These outputs demonstrate why execution and meaning need separate evaluation.

Unsupported constructors, unknown columns, nonliteral/dynamic arguments and forbidden keywords are technical exclusions. Supported constructors can still fail GX execution, especially on mixed-type stress data; held-out execution results are preserved separately from the development gate. Failure to express a valid relation in the allowed subset is not evidence that the relation is semantically invalid. No unrestricted generated Python/SQL is executed. No hand-authored candidate replaces a model failure.

![Technical candidate yield](figures/generation_yield.svg)

The exact model text is in `raw_model_responses/`; accepted candidate files preserve original descriptions, references and request provenance. Pending reviewer packets contain real frozen candidates and blank judgments. Independent semantic precision, invalid-promotion rate and inter-rater agreement are **NOT MEASURED**.
""",
)
write(
    "qualification_experiment.md",
    f"""
# Same-candidate qualification experiment

The actual generated candidates were frozen and deduplicated within source/condition before selection. **A** retains supported, executable proposals; **B** invokes the unchanged LeDQeR greedy pair-coverage selector using development labels and precision 1.0; **C** requires entailment from inherited documentary contracts, no baseline redundancy, low unlabelled development alerts and format stability, otherwise rejects/abstains; **D** is the fixed conventional suite without extra model rules. A/B/C are reported with that identical conventional suite included.

All arms share the same candidate population within a track. B has privileged development-label access and is a labelled reference, not an equally deployable label-free competitor. No held-out labels are given to generation, C or threshold choice. Every selector is saved before held-out scoring. For controlled row evaluation the original pair selector uses an explicit ROW proxy; for published single-column cells its original pair algorithm and cell identities are retained. Multicolumn candidates are excluded only from the cell-localization track, equally for every arm.

For controlled sources B estimates development precision on each rule's **new flags relative to unmodified development**, because existing source alerts have no independent clean labels. Its precision-one constraint therefore does not guarantee precision one on raw batches. Published-source B instead uses raw development reference discrepancies. This target difference is explicit; the controlled adapter is not a faithful reproduction of the paper's known-dirty-tuple protocol.

## Held-out reference cells, strong controls

{cell_table}

The Hospital `strong` configuration equals its weak generic missing-token screen; the Beers stronger screen adds only lexical numeric checks for ABV and IBU. These are limited controls, not complete source-specific business suites. Hospital B selected the familiar ZIP/ZIP+4 pattern `^[0-9]{{5}}(-[0-9]{{4}})?$`; such a conventional check could be authored without an LLM. It was not retroactively inserted into D after observing scores. The six extra reference hits are thus evidence above this fixed basic screen, not proof of unique AI value above a mature domain baseline.

Hospital B improves reference precision and F1 relative to A while reducing recall: six of the 18 available extra reference hits remain, with no additional off-reference cells. C removes that burden but also all available extra reference hits. Beers B/C avoid A's 770 extra off-reference alerts, retaining the same 152 baseline reference hits. This is not evidence that qualification uniformly improves detection; burden, lost coverage and label access must be read together.

## What C measures

C is a transparent conservative baseline, not a newly validated semantic estimator. It inherits the correctness/scope of existing contracts. A proof of entailment under those assumptions does not independently verify the source contract. Unknown semantics trigger ABSTAIN; unsupported execution and baseline redundancy have different reasons. `selections/*.json` contains every decision and accepted set, including the no-extra-documentation and threshold variants. No acceptance implies production activation: independent review remains required.

Entailment is checked in a native constraint abstraction. Its numeric/code normalization can differ from exact GX membership under representation changes; this is not a machine-checked proof of runtime equivalence. The padding diagnostic exposes part of that mismatch. Claims of logical redundancy are conditional on that abstraction and inherited normalization policy.

The documentary knowledge available to C is a subset of the strong conventional suite. Consequently every candidate C could certify is already entailed by that suite and fails the explicit redundancy gate: **zero strong-baseline C acceptance is structurally implied by this implementation**, not an empirical discovery about all evidence-based qualification. Under weak controls C can restore known omitted contract checks; that is not novel rule discovery and may be implemented without an LLM. The weak/strong results expose this limitation rather than hiding it behind a favorable precision score.

Formatting is tested by padding nonblank strings. That may change an exact categorical-code contract rather than preserve semantics, so the stability gate can reject a valid exact-code check. This deliberately narrow diagnostic must not be advertised as universal semantic invariance. Likewise existing controls remain visible in documentation-withheld generation; this condition removes additional documentation, not all source knowledge.

A code audit added an explicit downstream technical-pool assertion for B, plus diagnostic raw-versus-new-alert metric clarification before any new UCI holdout scoring. Both published sources had all eight candidates technically eligible, so their completed scores are unchanged. Original result files were preserved and all their scientific fields match isolated final-code rescoring (`published_score_reproduction.json`). The study is exploratory with transparent implementation amendments, not retrospectively pristine preregistration.

Semantic-validity precision, false promotion of independently invalid rules, reviewer agreement and precision on independently adjudicated natural errors remain unmeasured. Published reference precision and controlled alteration precision cannot substitute for those quantities.

The unchanged original LeDQeR confusion-count scorer also ran on 276 actual-candidate row/cell comparisons and agreed with the independent scorer in every case (`original_scorer_actual_candidates.json`). This complements the real original GX evaluator and greedy-selector runs; it does not reproduce upstream model generation, labelled correctness/coverage filtering or paper performance.
""",
)
case_rows = []
new_case_rows = []
for source in sorted({r["source"] for r in controlled}):
    for family in ["missing", "invalid_type_or_code", "gross_scale", "plausible_swap"]:
        by = {r["arm"]: r for r in controlled if r["source"] == source and r["family"] == family}
        new_case_rows.append(
            [source, family, by["D"]["delta_agreement"]["tp"]]
            + [
                f"{by[a]['new_alert_incremental_labelled_hits']} / {by[a]['delta_agreement']['fp'] - by['D']['delta_agreement']['fp']}"
                for a in ["A", "B", "C"]
            ]
        )
        case_rows.append(
            [
                source,
                family,
                by["D"]["agreement"]["tp"],
                by["D"]["agreement"]["tp"] + by["D"]["agreement"]["fn"],
            ]
            + [
                f"{by[a]['incremental_labelled_hits']} / {by[a]['additional_workload_rows']}"
                for a in ["A", "B", "C"]
            ]
        )
write(
    "incremental_detection_results.md",
    f"""
# Incremental detection and workload

The main increment is **selected-candidate findings beyond the same fixed conventional controls on the same held-out batch**. Report extra labelled hits, additional off-label alerts, discarded available labelled hits and marginal label-agreement precision together. A candidate already covered by D adds zero. Empty increments have undefined marginal precision, not precision 1. Controls are fixed independently of test errors and generated proposals.

The strong published-cell results are in [qualification](qualification_experiment.md): Hospital A adds 18 reference hits/471 alerts, B six/six, C zero/zero; Beers A zero/770, B/C zero/zero. Hospital B loses 12 potentially detected reference cells; C loses 18. Off-reference burden is not independently adjudicated false-positive count.

The published-source `strong` label is relative: Hospital still has missing-token screening only; Beers additionally checks lexical numeric ABV/IBU. Hospital's selected ZIP pattern is an ordinary conventional candidate. Full business-control increment is not established there, and no post-test baseline amendment is hidden in the primary comparison.

## Controlled rows under strong existing controls

Each A/B/C cell below gives **extra labelled hits / extra alert rows**, rather than a pooled score. D columns show baseline hits and actual changed-row denominator for that family. Detailed weak/strong precision, recall, F1, off-label workload and lost hits are in `tables/row_results.csv` and source JSONs.

{table(["Source", "Family", "D hits", "Changed rows", "A extra hits/alerts", "B extra hits/alerts", "C extra hits/alerts"], case_rows)}

## Response to a controlled change

Raw hits can include a row already flagged before alteration. The following separate diagnostic gives D's newly flagged labelled rows and **additional newly flagged labelled rows / added off-label new-alert rows**. Its baseline is D's new-alert set, not D's raw batch set, so the two increment definitions must not be interchanged.

{table(["Source", "Family", "D new hits", "A new hits/off-label", "B new hits/off-label", "C new hits/off-label"], new_case_rows)}

Some dtype checks react to pandas batch inference: introducing a floating-point value can turn an originally integral column into float dtype when the worker reconstructs a DataFrame. An unchanged numeric cell may then trigger a type expectation. These are adapter/representation effects, not evidence of independently invalid source values. Credit's raw swap hits largely include pre-existing alerts, while newly triggered swap coverage is much smaller. The before/after diagnostic prevents treating every already-flagged altered row as sensitivity to the change.

The journal primary `strong` suite also omitted explicit numeric guards: its range/equality engine skips nonnumeric strings, so it detects only the eight currency-code changes in the 24-row invalid-type/code case. This is an incomplete conventional baseline, not evidence that an LLM supplied a new business constraint. An explicitly post hoc engineering supplement adds two numeric guards and flags all 24 stipulated invalid rows. The principal experimental files and scores remain unchanged; the supplement cannot support a confirmatory AI-value claim.

Missingness is controlled deletion; invalid type/code is an operational violation. Gross scale and plausible swaps measure recovery of an alteration, which may remain legitimate under the source's semantics. The synthetic journal has a stipulated additional equality contract, not natural financial gold. Strong-suite ceilings and deliberate overlap with injection families can make zero increment unsurprising; this does not prove language models never add value.

The weak suite retains basic schema/missing/type checks; the strong suite adds pre-existing contracts and development-only historical envelopes. Both run through the same engine. No model-selected baseline replacement or test-fitted bound is used. The full weak/strong comparison is preserved, including cases where a weak baseline makes an apparent model gain disappear under stronger controls.

C's known documentary constraints are contained in strong D, so its zero increment there is implied by entailment plus redundancy rejection. A weak-baseline C increment can be recovery of an already known conventional constraint. Neither supports a new-method superiority claim.

For controlled sources, raw batch findings may include pre-existing unadjudicated source alerts. The separate `delta_agreement` uses baseline new alerts and a union of each rule's new alerts relative to the unmodified source. This avoids masking an additional rule finding through subtraction of an aggregate before/after union. New-alert increments and losses have explicit names alongside raw increments. Neither off-injection alerts nor unchanged source values are declared clean by assumption. No aggregate F1 combines these incompatible populations.
""",
)
selection_rows = []
for p in sorted((base / "selections").glob("guided_*.json")):
    a = json.loads(p.read_text())
    selection_rows.append(
        [
            a["source"],
            a["baseline"],
            *[len(a["arms"][x]) for x in ["A", "B", "C"]],
            *[
                len(a["sensitivity"][x])
                for x in ["C_0.0", "C_0.01", "C_0.05", "B_0.8", "C_no_extra_documentation"]
            ],
        ]
    )
uncertainty = table(
    ["Source", "Arm", "Conditional group uncertainty"],
    [[r["source"], r["arm"], json.dumps(r["cluster_uncertainty"], separators=(",", ":"))] for r in cells],
)
write(
    "robustness_and_generalization.md",
    f"""
# Robustness and generalization

All 48 adapted source/doc/instruction/seed conditions were completed without changing the model, prompts or selector thresholds after held-out outcomes. This is a fixed-model exploratory study. Five real datasets, three seeds and many candidate occurrences do not establish a population of independent domains or significant model superiority.

## Prespecified selector sensitivity

The table reports accepted candidate counts. Outcome sensitivity, including held-out hits and workload for each threshold, is in `tables/row_results.csv`; changing accepted count is not itself an improvement. C thresholds were 0, .01 and .05 unlabelled development alert fraction; B precision 1 and .8. No threshold was selected for a favorable held-out score.

{table(["Source", "Controls", "A", "B1", "C.01", "C0", "C.01", "C.05", "B.8", "C without extra docs"], selection_rows)}

`tables/prompt_strata.csv` reports response parse/execution yield and distinct rule sets for each source, documentation and direct/cautious instruction condition. This is a generation-quality ablation. The primary selector comparison pools the frozen candidates within source; it must not be described as a clean causal detection comparison between documentation conditions. The original four-call smoke and adapted condition are also not balanced equivalent populations. The generic syntax examples can anchor thresholds, and temperature-zero seed repetitions can be highly dependent.

Whitespace padding is an explicit diagnostic only. Exact categorical codes can change validity under padding; this limits interpretation of C's stability requirement. Unsupported conditional/relational classes restrict what a model can express. Held-out mixed-type execution failures are preserved rather than silently dropping the difficult family or treating failure as a successful negative check.

## Conditional uncertainty and dependence

{uncertainty}

The Beers intervals resample the same brewery groups for a paired increment relative to D, conditional on this fixed model/candidate set. Degenerate zero intervals mean identical measured reference hits in these resamples, not a proof of no benefit on other sources. Hospital has seven providers, so intervals are withheld. These are no source-level cross-model confidence bounds and no multiple-condition significance claims. Controlled-family outcomes are descriptive; dependent injections/candidates are not independent population trials.

Original scientific fields reproduce exactly under isolated rescoring without model calls. This verifies deterministic analysis of cached outputs, not bitwise regeneration across CPU/compiler changes. Broader claims require a new source holdout, independent semantic review and a second justified model configuration. Unit/period/sign applicability shifts in natural financial data have not been tested here; the old SEC diagnostic and controlled journals do not fill that gap.
""",
)
write(
    "engineering_artifact.md",
    f"""
# Connected engineering artifact

The artifact extends the preserved provider/cache/GX pipeline and the existing SQLite control service. Actual model proposals enter its lifecycle; hand-authored fixtures and published predictions never substitute for generated candidates. A safe native mapping supports existing service rule types while the research evaluator retains a broader literal GX subset.

```mermaid
flowchart LR
  P[Frozen metadata prompts] --> L[Local Qwen CPU server]
  L --> R[Exact response cache and hashes]
  R --> S[Strict parser and constructor gate]
  S --> G[Resource-limited GX execution]
  G --> Q[A / labelled B / documentary C]
  Q --> V[Proposals and technical validation]
  V --> H[Independent review pending]
  D[Conventional approved controls] --> M[Batch scan and findings]
  H --> M
  M --> A[Profiling, audit and monitoring history]
```

The completed journal demonstration imports **{len(service["real_generated_rules_imported"])} actual generated native proposals**, records **{service["events"]} audit events** and **{service["monitoring_records"]} monitoring records**. Model state counts: `{service["model_states"]}`. **{service["model_rules_active"]} generated rules are ACTIVE; independent human approvals: {service["independent_human_approvals"]}.** Existing self-authored conventional contract controls alone are approved/activated by an explicitly named controlled operator. No artificial reviewer is invented. Clean and changed-batch scans, findings and state counts are saved in `results/execution/service_demo.json`.

The scenario states a per-journal, same-currency integer-cent debit/credit equality. It does not sum arbitrary positive debit/credit columns to zero or assume all financial statement totals balance universally. The inherited SEC adapter separately handles explicit coordinates, signed coefficients, units and rounding; its analyst development proposals remain pending and reserved bases untouched.

The counts above describe the initial demo. An additional executed engineering correction (`service_schema_guard_supplement.json`) adds explicit numeric guards for both amount fields. The principal journal baseline lacked them and skipped nonnumeric values in range/equality checks, detecting only eight currency-code changes. With these two ordinary schema guards the service flags 24/24 stipulated invalid rows, with no off-scenario labelled rows and no active model rule. This was added after inspecting exploratory outcomes, is labelled post hoc, and does not replace any primary A/B/C/D result or establish a research improvement. Run `service_demo.py` then `service_schema_guard_demo.py` to recreate the two stages on a fresh ignored service database.

Technical code execution is confined to allowed literal GX constructors and class-specific primitive keyword arguments. Imports, dynamic calls, row conditions, arbitrary SQL and query constructors are rejected before the unchanged upstream evaluator is reached. CPU/address-space/wall ceilings limit the worker; regex length and payload size are bounded. This is a constrained local research threat model, not a hardened multi-tenant sandbox.

The model endpoint is authenticated and loopback-only. Requests are content-addressed by pinned model/runtime/prompt/settings, successful results reused and incomplete attempts retained. Secrets, raw datasets, weights and databases remain ignored. Exact new metadata-only responses and prompts are exported for analysis reproduction. No paid endpoint or public server is started.

Limitations: actor names are attribution strings rather than enterprise identity; SQLite logs are not tamper-proof authorization; automated documentary certificates are not independent human approval; the adapter cannot represent every GX expression; no private Avanade/Rabobank integration or production deployment occurred. The artifact demonstrates a connected workflow and preserves review gates. Its usefulness does not establish a novel AI algorithm.

The native engine normalizes numeric/code strings, which can differ from exact GX membership on changed representations. The demo therefore records the original GX expression and the mapped native proposal together, and activates none of them. Research detection scores come from the actual GX evaluator; service mappings are not silently substituted into those results.
""",
)
write(
    "README.md",
    """
# Free-model research execution

This additive package contains actual local model generation, technical evaluation, same-candidate A/B/C/D comparisons, held-out reference/controlled scoring and a connected service demonstration. Start with [the execution summary](execution_summary.md).

1. [Working model and measured performance](free_model_setup.md)
2. [Actual candidate yield and failures](generated_rule_results.md)
3. [Datasets, rights and label interpretation](dataset_and_ground_truth_review.md)
4. [Closest work and unresolved novelty](literature_and_novelty.md)
5. [Qualification comparison](qualification_experiment.md)
6. [Incremental value and burden](incremental_detection_results.md)
7. [Sensitivity, uncertainty and generalization](robustness_and_generalization.md)
8. [Functional engineering artifact](engineering_artifact.md)
9. [Recommended direction and Pilot 1 comparison](final_thesis_direction.md)
10. [Supervisor-ready proposal](thesis_proposal.md)
11. [GO/NO-GO decision](final_go_no_go.md)
12. [Reproduction and evidence categories](reproduction.md)

Machine-readable outputs are in `results/execution/`: summary, raw response/prompt inventories, per-source candidate freezes, selection records, evaluation JSONs, CSV tables, actual response bytes, pending review packets and software-test evidence. No independent human judgments or private bank records are included. Prior phases remain immutable historical checkpoints.
""",
)
print("Seven measured reports and index rendered from completed experiment outputs.")
