#!/usr/bin/env python3
"""
PostToolUse hook: runs Ruff + Pyright after every Python file edit.
Exit 0 = pass, Exit 2 = errors found (Claude must fix before continuing).
"""
import json
import os
import subprocess
import sys


def run(cmd: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        output = (result.stdout + result.stderr).strip()
        return result.returncode, output
    except FileNotFoundError:
        return -1, f"Tool not found: {cmd[0]}. Run /setup-python-hook to install."


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path.endswith(".py"):
        sys.exit(0)

    errors: list[str] = []

    # Ruff: check only the modified file (fast, per-file style issues)
    ruff_code, ruff_out = run(["ruff", "check", "--output-format=concise", file_path])
    if ruff_code == -1:
        print(ruff_out, file=sys.stderr)
        sys.exit(1)  # tool missing → warning, don't block
    if ruff_code != 0 and ruff_out:
        errors.append("=== Ruff (style/syntax) ===")
        errors.append(ruff_out)

    # Pyright: scan the whole project to catch cross-file type errors
    # (e.g. Claude changed a function signature but forgot to update call sites)
    pyright_code, pyright_out = run(["pyright", "--outputjson"])
    if pyright_code == -1:
        print(pyright_out, file=sys.stderr)
        sys.exit(1)  # tool missing → warning, don't block
    if pyright_code != 0:
        try:
            data_py = json.loads(pyright_out)
            diagnostics = data_py.get("generalDiagnostics", [])
            if diagnostics:
                errors.append("=== Pyright (type errors) ===")
                for d in diagnostics:
                    f = d.get("file", "").replace(os.getcwd() + "/", "")
                    line = d.get("range", {}).get("start", {}).get("line", 0) + 1
                    msg = d.get("message", "")
                    sev = d.get("severity", "error")
                    errors.append(f"  {f}:{line}: {sev}: {msg}")
        except json.JSONDecodeError:
            if pyright_out:
                errors.append("=== Pyright (type errors) ===")
                errors.append(pyright_out)

    if errors:
        print("\n".join(errors))
        sys.exit(2)

    print(f"✓ {file_path}: ruff + pyright passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
