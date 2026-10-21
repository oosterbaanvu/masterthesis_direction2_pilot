# Reusable cloud setup and outstanding external dependencies

The project checkout is `/workspace/masterthesis_direction2_pilot`. The final work is published on its own `codex/final-research-feasibility` branch; previous reports/branches and Pilot 1 are preserved. A complete discovery identified one requested project plus read-only literature/source references and ignored vendor/build caches. `/workspace/.git` is an empty directory with no HEAD/config, not an unborn project checkout.

The saved installation workflow uses two separate frozen Python environments, verifies/restores parent raw inputs without rewriting historical acquisition reports, restores pinned LeDQeR/FinRule sources and primary PDFs, and runs the original and new suites. The saved startup instructions select the correct checkout, describe reproduction and preserve the inference/independent-review gates. No Git worktree is needed: cloud tasks already have an isolated environment.

```bash
set -euo pipefail
cd /workspace/masterthesis_direction2_pilot
export UV_CACHE_DIR=/workspace/.cache/uv
export MPLCONFIGDIR=/tmp/dq-final-mpl
export XDG_CACHE_HOME=/tmp/dq-final-cache
uv sync --frozen --extra dev
uv sync --project envs/final --frozen
PYTHONPATH=src .venv/bin/python scripts/final/restore_parent_inputs.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/final/acquire.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/final/acquire_finrule.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/final/acquire_literature.py
.venv/bin/pytest -q
PYTHONPATH=src envs/final/.venv/bin/pytest -q tests_final
PYTHONPATH=src envs/final/.venv/bin/python scripts/final/verify.py
```

`UV_CACHE_DIR` is required because the default home cache is read-only; the writable cache override resolves that setup failure. The cloud draft preserves existing network destinations and adds research/public-pricing/Kaggle domains, including `developers.openai.com`. Actual access still varies: developer API pricing and the Bayesian PDF remain unavailable, while Gemini prices, official OpenAI launch pages and the public FinRule API were acquired. A destination being saved is not proof that every endpoint is accessible in the running instance.

The `KAGGLE_API_TOKEN` requirement is saved for `www.kaggle.com` and `api.kaggle.com`. No value was read, printed or stored by the agent. It is absent in this task; newly configured bindings may require applying/publishing the settings and starting a fresh task. No research-model secret is assumed; choose the proposed provider/model/budget before adding a model credential. New paid inference remains unauthorised.

Saving the draft does not apply scripts, create secrets, publish the environment or validate restoration in a new task. The user must review/save the environment settings and publish them to activate the saved configuration. Current-instance checks and a remotely pushed branch are distinct from that publication.
