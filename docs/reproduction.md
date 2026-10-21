# Reproduction and operational commands

Python 3.12, `uv`, HTTPS Git proxy and package-manager access are required. No GPU, Docker, network source database or persistent web server is needed. Dependency versions are pinned in `pyproject.toml` and fully resolved in `uv.lock`.

## Setup and evidence verification

```bash
cd /workspace/masterthesis_direction2_pilot
export UV_CACHE_DIR=/workspace/.cache/uv
uv sync --frozen --extra dev
.venv/bin/dqp acquire
.venv/bin/python scripts/acquire_literature.py
.venv/bin/pytest -q
.venv/bin/ruff check src scripts tests
.venv/bin/dqp verify
```

Acquisition reuses only exact pinned bytes. It verifies ZIPs and extracted/nested members, source shape and column names, and Git versions. A hash mismatch is a failure; do not disable TLS or replace pins to suppress it. Metadata-only optional Kaggle blocks are expected, not successful downloads. `dqp verify` checks the scientific run's frozen code/config/tests and output hashes. A deliberate code change can invalidate that freeze without making the environment broken: create a separate new research run, preserving the old outputs.

`dqp reproduce --work-dir results/local/reproduction-02` creates an isolated **output directory**, copies the current configuration/code/tests/protocol, and links already acquired read-only inputs. It is not a Git worktree. It audits, reruns the official released-output evaluation, and executes the regular, pair, SEC baseline, service and robustness phases. A pre-existing output directory or completed run is refused so earlier evidence is preserved. On a fresh clone, run acquisition first. On the prepared snapshot, raw inputs are retained and no source download is needed.

Official script parameters are replaced only in an in-memory AST; the upstream file and model outputs are unchanged. The original runner's CSV and logs stay under `results/local`. Corrected metrics, compatibility differences and original artifact hashes are saved in `sec_reproduction.json`. Qwen-7b 10% duplicate-ID exclusion has 976/1,000 corrected-table coverage; compatibility retains upstream last-write behavior. Published filenames do not verify exact model version, prompt or cost. Do not rename released DeepSeek-V3 outputs into a new DeepSeek-R1 reproduction.

Run inputs and outputs are hashed in `frozen_inputs.json` and `run_manifest.json`; values and positions are in ignored `results/local/injection_log.json`. Generated summaries are descriptive, with separate source/family denominators. Repeated seeds/variants are dependent. New method evaluation never scores the reserved SEC partition. Retrospective published-output scoring is a separate compatibility track. Source files have read-only permission bits; this is not protection against an owner intentionally altering files.

## Local service workflow

`rules.json` is a list of declarative rule objects, and `development.csv` contains only permitted development rows. The following commands form a complete persistent lifecycle:

```bash
.venv/bin/dqp service propose --database results/local/service.sqlite --source demo --specification rules.json --actor proposer
.venv/bin/dqp service validate --database results/local/service.sqlite --rule-id positive_amount --csv development.csv --actor qualifier
.venv/bin/dqp service transition --database results/local/service.sqlite --rule-id positive_amount --state APPROVED --actor reviewer --reason 'Contract and evidence reviewed'
.venv/bin/dqp service transition --database results/local/service.sqlite --rule-id positive_amount --state ACTIVE --actor operator --reason 'Deploy approved rule'
.venv/bin/dqp service scan --database results/local/service.sqlite --source demo --csv batch.csv
.venv/bin/dqp service history --database results/local/service.sqlite --source demo
.venv/bin/dqp service review --database results/local/service.sqlite --finding 1 --state INVESTIGATING --actor reviewer --reason 'Check source evidence'
```

Qualification may return NEEDS_REVIEW or REJECTED, so approval is conditional on VALIDATED. No automatic activation occurs. Actors/reasons provide attribution, not authenticated authority. Reproposal should use a new rule identifier; rejected specifications are not silently rewritten. `dqp scan --sqlite source.sqlite --table source_table --rules rules.json --output results/local/scan.json` exercises a read-only SQL input. No unrestricted generated SQL can be submitted.

## Optional model experiments

`config/models.yaml` names `DQP_MODEL_API_KEY` and `DQP_MODEL_BASE_URL`. Neither is configured here. No secret value belongs in Git or chat. The environment had no usable inference binding and no spend authorization. After model selection, explicit authorization, rights review and secure configuration, start with a bounded development subset and positive maximum calls/spend. Prices must match the selected model. The CLI also requires `--authorize-paid`; that flag must reflect actual prior user authorization.

Generation/detection context JSON accepts only schema, source semantics, anonymous sample/CSV and explicit `public_unrestricted` classification. Do not put GT, target outcomes, filenames, clean references or reserved-test data in it. Exact prompts are in `dqpilot/llm.py`. Responses/cache/usage/model identity are retained locally. Freeze the full candidate list before qualification; `dqpilot.comparison.compare_candidates` uses precisely that list for C and D and keeps evaluation labels outside qualification. Independently adjudicate semantic validity/useful-rule rejection; software execution does not supply those labels.

The spend ledger reserves a conservative text-token bound before calling, counts failed/in-flight requests against local caps, and refuses automatic duplicate calls after failure. It cannot enforce provider-account-wide billing. Original published inference tokens and costs are unknown, not imputed from the current adapter.

## Retained attempts

`results/attempts` records duplicate-ID and empty-type evaluator corrections, plus an excluded expanded run with invalid zero-scale labels. The full local attempt outputs are retained under `/workspace/pilot2-run-preservation`. The initial 72-scenario reconnaissance is not independent of the final expanded study. All included final injections reject numeric equality such as `0 -> 0.0`, and 18 partially realized cases remain visible rather than resampled to their requested count.
