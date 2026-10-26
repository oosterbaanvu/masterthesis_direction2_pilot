# Reproduction and evidence boundaries

Use branch `codex/free-model-execution` of `oosterbaanvu/masterthesis_direction2_pilot`. It starts from the preserved free-pilot commit `bf11edd1504ad25e52741ddcdd9315a986cd4dc7`; earlier original/final/free reports are historical records. No root README, lockfile or previous result is replaced.

## Cached analysis, no model key or new inference

```bash
cd /workspace/masterthesis_direction2_pilot
export UV_CACHE_DIR=/workspace/.cache/uv
export UV_TOOL_DIR=/workspace/.cache/uv/tools
export UV_TOOL_BIN_DIR=/workspace/.cache/uv/bin
export MPLCONFIGDIR=/tmp/dq-final-mpl
export XDG_CACHE_HOME=/tmp/dq-final-cache
uv sync --frozen --extra dev
uv sync --project envs/final --frozen
PYTHONPATH=src .venv/bin/python scripts/final/restore_parent_inputs.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/final/acquire.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/free_gemini/run.py --prepare-only
PYTHONPATH=src envs/final/.venv/bin/python scripts/execution/verify.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/execution/reproduce.py
```

Raw sources retain their existing access/rights restrictions. `restore_parent_inputs.py` uses temporary acquisition-report paths and does not rewrite frozen acquisition reports. The original LeDQeR source is pinned and verified by `acquire.py`. Reproduction creates a fresh ignored result directory, checks all saved scientific result fields and refuses to overwrite completed evaluations. The initial full result is in `results/execution/reproduction.json`. The benchmark pair was also independently rescored before consolidation. No inference server or API key is required for this analysis path.

Committed candidate files suffice for scoring; exact new public-metadata prompts and raw responses let a reader inspect parser failures and provenance. They do not redistribute original data/weights or make unverifiable generated citations authoritative. Export hashes verify stored bytes. Normalized AST deduplication retains origin request IDs, including repeated proposals. A request with a valid JSON body but duplicate rule IDs is rejected as an entire bundle; emitted rule-object and parser-admitted counts are separate.

## Local model acquisition and restart

```bash
PYTHONPATH=src envs/final/.venv/bin/python scripts/execution/acquire_local.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/execution/start_local.py
```

The acquisition helper verifies pinned official Qwen weights and official llama.cpp source, preserving TLS/checksum verification, and reuses the original verified binary when present. Missing weights require approximately 4.68 GB plus eight GiB free headroom. CMake 4.1.2 and compiler flags are recorded. A new CPU/compiler can produce a different binary; preserve that provenance before any new generation. Source archive and model checksums remain fixed. The original embedded build-version label came from the surrounding Git repository; the explicit source archive commit/hash is authoritative.

The startup helper either reuses the authenticated loopback model or starts it with 8k context, four threads, one slot and zero GPU layers. It checks the loaded model alias and tokenization, adding no research-generation request. The local random bearer token is ignored and mode 600; no user secret is needed. A fresh cloud process must run startup again; publication does not preserve a running server. Successful current-instance startup and a saved draft do not prove a fresh-task restore.

Completed generation scripts skip saved outputs; the durable response ledger additionally caches matching successes and retains failed/incomplete attempts. Do not delete it, rewrite prompts or rerun to obtain favorable results. The original smoke ledger has a deliberate four-call stage gate, and the guided full condition is frozen. New models/prompts need a separate named condition and a new scientific protocol, rather than overwriting this execution. No paid API fallback is configured.

## Validation and scope

```bash
.venv/bin/pytest -q
PYTHONPATH=src envs/final/.venv/bin/pytest -q tests_final tests_free tests_execution
PYTHONPATH=src envs/final/.venv/bin/python scripts/execution/verify.py
```

Software tests check caching, endpoint restrictions, generated-code argument safety, documentary-selection assumptions and metrics. Mocked unit-test responses are explicitly software fixtures and are not included in actual model-request counts. The new suite has 17 tests; actual suite outcomes are in committed XML evidence. The scientific verifier checks the additive freeze, exact actual prompt/response bytes and the previous final/free/original freezes.

The connected artifact has two preserved stages: `service_demo.py` imports actual candidates into the existing service; `service_schema_guard_demo.py` then appends two conventional numeric guards after a primary-baseline omission was found. Both scripts require fresh/preserved stage state and refuse overwrite of completed outputs. Use a fresh ignored service database for a new engineering demonstration rather than deleting research evidence. The post hoc numeric-guard result is not a replacement for the principal frozen comparison.

Evidence categories remain distinct: 56 actual new model-generation requests; prior published SEC predictions; prior handwritten GX component fixtures; controlled changes; published reference discrepancies; and blank independent-review packets. No semantic-review score or natural-error precision is manufactured. Deterministic rescoring of cached responses is demonstrated; bitwise model regeneration across hardware/runtime changes and fresh-task restoration are not.
