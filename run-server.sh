#!/usr/bin/env bash
# Starts the VAVE control plane with the project's own Python.
#
# The dependencies live in ./venv, not in the system Python, so running
# `python -m assistant.api` from a shell that has not activated the venv fails
# with "No module named 'fastapi'". This picks the right interpreter either
# way, and passes every argument straight through:
#
#   ./run-server.sh --host 0.0.0.0        # reachable from your phone
#   ./run-server.sh --pair                # print a pairing code
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    echo "No virtualenv at $ROOT/venv. Create one first:" >&2
    echo "  python -m venv venv && venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi

cd "$ROOT"
exec "$PYTHON" -m assistant.api "$@"
