#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Dedicated environment: no packages are installed into system Python.
python3 -m venv .venv-checks
.venv-checks/bin/python -m pip install -r scripts/requirements-checks.txt
