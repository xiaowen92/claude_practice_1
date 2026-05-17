#!/bin/bash
# venv-aware wrapper: prefer project .venv, fall back to system python3.
# Also prepends .venv/bin to PATH so subprocess calls to ruff/pyright resolve.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -d "$PROJECT_ROOT/.venv/bin" ]; then
    export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
    PYTHON="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON="python3"
fi

exec "$PYTHON" "$SCRIPT_DIR/python_check_hook.py"
