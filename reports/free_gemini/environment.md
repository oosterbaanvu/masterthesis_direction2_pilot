# Free-pilot environment setup

No new dependency or paid service was installed. The separate locked final-phase environment already supplies HTTPX, pandas, Great Expectations 1.9.1 and pytest. The prior installation script remains necessary for parent inputs and is extended with these tested commands:

```bash
cd /workspace/masterthesis_direction2_pilot
export UV_CACHE_DIR=/workspace/.cache/uv
export MPLCONFIGDIR=/tmp/dq-final-mpl
export XDG_CACHE_HOME=/tmp/dq-final-cache
PYTHONPATH=src envs/final/.venv/bin/python scripts/free_gemini/run.py --prepare-only
PYTHONPATH=src envs/final/.venv/bin/pytest -q tests_free
PYTHONPATH=src envs/final/.venv/bin/python scripts/free_gemini/verify.py
```

The 21 new software tests pass, including real GX subprocess execution on software fixtures. The local preflight additionally executed one handwritten fixture on each of three real development subsets (256 rows each) and the five-row synthetic journal. Neither exercise is reported as model inference. Both parent scientific freezes remain intact.

Setup intentionally prepares and tests without contacting an inference endpoint. After the two access settings are available, run the actual free pilot using `scripts/free_gemini/run.py` without `--prepare-only`. The user's authorization for this selected free pilot persists; do not ask for paid authorization or a second model decision. Real access and quota failures still stop the run.

The saved secret requirement is `DQP_GEMINI_API_KEY`, restricted to `generativelanguage.googleapis.com`. The non-secret setting `DQP_GEMINI_FREE_TIER_CONFIRMED` defaults to false until a non-billed project is actually confirmed. The public Qwen weight CDN `us.aws.cdn.hf.co` is also declared for the optional local route; no inference key goes to it. Existing Kaggle requirements and other network domains are preserved.

The saved start instructions point to this phase and preserve prior reports, reserved SEC protection, no-paid-fallback policy and source privacy. Draft saving does not supply key values, apply runtime changes or publish an environment. Review/save the settings and publish them; newly injected values may require a fresh task. Fresh-task restoration has not been independently tested.
