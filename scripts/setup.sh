#!/usr/bin/env bash
set -euo pipefail
cd /workspace/masterthesis_direction2_pilot
export UV_CACHE_DIR=/workspace/.cache/uv
uv sync --frozen --extra dev
.venv/bin/dqp acquire
.venv/bin/python scripts/acquire_literature.py
.venv/bin/pytest -q
