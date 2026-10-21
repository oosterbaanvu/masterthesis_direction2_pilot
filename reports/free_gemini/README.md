# Free-only generation pilot — 21 October 2026

The user has selected **Gemini 2.5 Flash on its free API tier**, conditional on access, quotas, privacy and source rights. No paid API, billed fallback or silent model substitution is enabled. This supersedes the earlier paid-model recommendation for the next experiment; historical reports and their freezes remain unchanged.

## Current measured state

The dedicated Gemini credential and the non-billed-project confirmation are absent in this task. The actual runner stopped with `MISSING_DQP_GEMINI_API_KEY` before any inference. **Actual Gemini generations: 0; paid calls: 0.** No candidate rules, token usage or detection results have been invented. Software tests use explicitly synthetic mocked responses and are not model experiments.

Forty-eight prompts have been prepared and content-hashed: three public UCI schemas plus one self-authored synthetic journal scenario, two additional-documentation contexts, two prompt variants and three recorded seeds. Prepared sizes are 2,283–10,162 UTF-8 bytes. The UCI contexts transmit **no individual data records**. Repeated prompts are within-source replications, not independent datasets. The controlled journal is not real financial gold.

The local triage path was actually exercised with four labelled **handwritten software fixtures**, using development-only subsets of Credit, Bank Marketing and Wine and the synthetic journal. This checks real data loading, subprocess limits and original GX evaluation. It provides no evidence about actual model-rule quality. The request/candidate pipeline tests cover credential gates, non-billed-project confirmation, fixed endpoint, caching, quota failures, attempt caps, model-version changes, unsafe code and actual GX worker execution.

## Free access required

In secure cloud environment settings, supply:

| Variable | Required value/purpose |
|---|---|
| `DQP_GEMINI_API_KEY` | A Google AI Studio Gemini API key from a project **without an active billing account**, with access to Gemini 2.5 Flash. Never put its value in chat or Git |
| `DQP_GEMINI_FREE_TIER_CONFIRMED` | Literal `true`, only after verifying that the selected project has no active billing and is on the free tier |

The destination is fixed to `generativelanguage.googleapis.com`, with the key sent in the `x-goog-api-key` header. No OpenAI or Vertex AI credential/endpoint is used. A Gemini key alone does not reveal its project's billing tier; the confirmation is an explicit configuration assertion, **not an API-verified billing fact**. There is no invented `free=true` API parameter. Do not attach billing or upgrade tiers to work around quota/access failures.

Google now limits its 2.5 models to users who actively used them previously. The model is still listed with a free tier and no announced shutdown, but **a new key may not have access**. The runner checks model access and stops on refusal. Current project quota cannot be verified before access; generic historic RPM/RPD numbers are not treated as the user's allowance.

The saved secret requirement, destination and confirmation variable are draft configuration. Review/save and publish the environment settings; a fresh task may be needed for injection. Once the key and confirmed free project are available, the user's free-generation authorization is sufficient to run the pilot. No additional paid/model approval is required for this selected free experiment.

## Execution and provenance

```bash
cd /workspace/masterthesis_direction2_pilot
export MPLCONFIGDIR=/tmp/dq-final-mpl
export XDG_CACHE_HOME=/tmp/dq-final-cache
PYTHONPATH=src envs/final/.venv/bin/python scripts/free_gemini/run.py --prepare-only
PYTHONPATH=src envs/final/.venv/bin/python scripts/free_gemini/run.py
```

Generation uses the fixed `gemini-2.5-flash` API model, temperature 0, explicit seeds, disabled thinking and at most 2,048 output tokens. The stable alias does not provide immutable open weights. Every successful response records the **returned modelVersion**, exact usageMetadata, request/response hashes, runtime and finish status. A model-version change halts further execution and preserves responses. Responses with safety blocks, malformed JSON, truncation or unsupported GX remain in the attempt record, not successful-rule counts.

Prompt hashes cover exact UTF-8 file bytes; request/response hashes cover canonical JSON. Literal returned model text remains in the response cache. Missing usage stays unknown rather than becoming an estimated token count. A response without modelVersion is still preserved with its actual usage, but blocks further qualification because version provenance is incomplete. Local data-loading failures are recorded as infrastructure failures, not failed model generations.

Requests and responses are cached durably in ignored `data/cache/free_gemini/requests.sqlite`. Cached completions do not trigger new generation. There is a maximum of 48 attempts overall, 12 new attempts per invocation, 20 per Pacific calendar day and at least 31 seconds between generation attempts. These are **local ceilings, not claims about actual quota**. Pacific time is used because Google's daily quota resets there. An access/quota/provider failure stops the run without automatic retry or fallback; inspect the preserved failure before any retry/protocol amendment. Resume capped successful batches through the same cache; never delete records merely to evade quota or attempt caps.

Generated code is parsed as literal standard GX constructors and triaged in a CPU/memory/wall-time-limited subprocess without inherited API-key variables. A bounded pure-pandas constructor subset is supported; unsupported candidates are recorded as such, not declared semantically invalid. Source values and provider error bodies are not exported. Results are technical execution and unlabelled-development workload only: semantic validity, independent review and the full A–D efficacy comparison remain pending.

See [privacy and quotas](privacy_and_quotas.md), [Qwen feasibility](qwen_feasibility.md), `config/free_gemini/pilot.yaml`, `results/free_gemini/prepared_inputs.json` and the actual `run_status.json`. The new source/input freeze can be checked with `scripts/free_gemini/verify.py`.
