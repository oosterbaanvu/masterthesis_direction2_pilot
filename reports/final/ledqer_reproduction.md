# LeDQeR reproduction: partial components, no new model inference

**Status: PARTIAL COMPONENT REPRODUCTION.** The original Great Expectations evaluator, confusion-count scorer, greedy pair-coverage selector and prompt renderer ran against all four overlapping released datasets. The model-generation experiment and paper performance reproduction did not run.

Official source: [Anna-Christina-Glock/dq_rule_generation](https://github.com/Anna-Christina-Glock/dq_rule_generation), commit `fb42051026ee6ccded9347349ff95b597804962d`. The inspected full history has three commits and no released generated-rule/response artifacts. There is no top-level licence; source/data remain ignored. Their absence prevents replacing inference with a faithful saved-output reproduction.

## Actual execution

The isolated, locked environment uses Python 3.12 and **Great Expectations 1.9.1**. It leaves the old pilot lockfile and environment unchanged. Fifty-seven explicitly handwritten GX expectations exercise the original evaluator: column non-null fixtures plus one deliberately simple format fixture per source. These are **software/component fixtures**, not model outputs or justified business rules. All 57 executed; their original TP/FP/FN calculations agree with an independent set-based scorer. Twenty-four real prompts were rendered and hashed, without sending them to a provider. Measured prompt sizes are 5,948–11,605 UTF-8 bytes. The recorded component runtime is about 2.04 seconds; it excludes installation, acquisition, prompt inspection and inference.

| Released source | Rows | Entity grouping | GX fixtures executed | Technical union author-label P / R / F1 | Label-assisted greedy at precision 1: author-label P / R / F1 | Labelled hits lost |
|---|---:|---|---:|---|---|---:|
| Flights | 2,376 | flight | 8 | 1.000 / .498 / .665 | 1.000 / .498 / .665 | 0 |
| Beers | 2,410 | brewery_id | 12 | .689 / .758 / .722 | 1.000 / .758 / .862 | 0 |
| Hospital | 1,000 | ProviderNumber | 21 | .023 / .051 / .031 | .000 / .000 / .000 | 6 |
| Tax | 6,000 | released pk | 16 | .000 / .000 / .000 | .000 / .000 / .000 | 0 |

These are agreement with released labels, not independently verified semantic precision. Empty prediction sets use the existing scorer's zero convention; a zero precision does not establish that an accepted rule was invalid. Hospital illustrates that rejecting an imprecise fixture can also lose labelled detections. This is a component behavior, not evidence about LLM selection effectiveness. Thresholds 0, .8 and 1 were all executed; full counts and chosen fixture IDs are in `results/final/ledqer_components.json`.

## Fidelity and deviations

1. Importing upstream `rule_eval` fails because its initializer imports a missing `load_latest_per_unique_file`. We load the original component files directly without editing them.
2. GX requires an active context before the original suite helper adds expectations. The wrapper initializes an ephemeral context. Upstream code is unchanged.
3. We AST-check one literal-keyword standard GX constructor before passing it to the original evaluator's `eval`. Query expectations, imports and dynamic calls are rejected. This is a safety restriction, not the old nine-kind DSL, and is not claimed to be a complete operating-system sandbox for future untrusted code.
4. We use handcrafted fixtures because no selected research model or released generated candidates is available. Consequently correctness/coverage-filter effectiveness and the reported model scores are **NOT REPRODUCED**.
5. Greedy precision/coverage uses **development labels** only, with evaluation on separate entity groups. This intentionally departs from the inspected published redundancy evaluation on `D_test`. It does not reproduce its five-fold aggregate. Tax row IDs are weaker than genuine independent source/issuer groups.
6. Prompt rendering supplies an explicit domain-description-unavailable string instead of silently using upstream's Austrian postal-domain default. Full paper configuration, exact sampled tuples, fold manifests and generation settings are not reconstructable from the inspected release.
7. Upstream models are GLM-4.7-Flash AWQ4, Qwen3-Coder-30B-A3B AWQ4 and Gemma-4-31B FP8. The Qwen quantizer namespace differs between prose and footnote. No NVIDIA device is present here; none of those weights was downloaded or run. A smaller CPU model would be an additional model experiment, not an exact reproduction.

The released LeDQeR Tax subset has 6,000 rows rather than the parent Raha portfolio's 200,000; all 6,000 are marked dirty and most labels concern rate representation. Beers likewise marks every tuple dirty. These distributions and normalization choices constrain interpretation. Label availability does not certify every difference as a substantive error.

Reproduce components in a **fresh** output location with:

```bash
export UV_CACHE_DIR=/workspace/.cache/uv
uv sync --project envs/final --frozen
PYTHONPATH=src envs/final/.venv/bin/python scripts/final/acquire.py
MPLCONFIGDIR=/tmp/dq-final-mpl PYTHONPATH=src envs/final/.venv/bin/python scripts/final/run.py --component-output results/final/local/repeat-gx
```

The wrapper refuses to overwrite a completed component run. Original candidate-code provenance, input hashes and prompt hashes are preserved in the committed results; raw prompt samples remain ignored.
