set -euo pipefail
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
PYTHONPATH=src envs/final/.venv/bin/python scripts/final/acquire_finrule.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/final/acquire_literature.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/free_gemini/run.py --prepare-only
.venv/bin/pytest -q
PYTHONPATH=src envs/final/.venv/bin/pytest -q tests_final tests_free tests_execution
PYTHONPATH=src envs/final/.venv/bin/python scripts/execution/acquire_local.py
PYTHONPATH=src envs/final/.venv/bin/python scripts/execution/verify.py
