---
name: setup-python-hook
description: Installs a self-correcting Python code quality hook (Ruff + Pyright) that automatically runs after every file edit in Claude Code. Use this skill whenever the user wants Claude to catch its own type errors, wants automatic type checking after edits, mentions pyright/mypy/ruff hooks, asks why Claude keeps breaking other files when it edits one, or wants to set up PostToolUse hooks for a Python project. Trigger even if the user just says "set up type checking" or "make Claude fix its own mistakes".
---

# Setup Python Hook

Claude is a strong vertical (in-depth) reasoner but has weak horizontal awareness — it often modifies a function signature in one file and forgets to update all the call sites in other files. This skill installs a PostToolUse hook that closes that gap: after every file edit, Ruff checks style/syntax on the modified file while Pyright scans the entire project for cross-file type errors. Any errors get fed back to Claude as a forced correction prompt (exit code 2), triggering a self-repair loop without the user needing to intervene.

## Prerequisites

- Python 3.8+ available (`python3 --version`)
- This skill's `scripts/` directory is bundled — you'll copy from it directly

## Installation Steps

### 1. Locate bundled scripts

The scripts bundled with this skill are at:
```
.claude/commands/setup-python-hook/scripts/python_check_hook.py
.claude/commands/setup-python-hook/scripts/run_python_hook.sh
```

### 2. Create .venv and install tools

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip ruff pyright --quiet
```

Confirm both installed:
```bash
.venv/bin/ruff --version && .venv/bin/pyright --version
```

### 3. Create project scripts directory and copy bundled files

```bash
mkdir -p scripts
cp .claude/commands/setup-python-hook/scripts/python_check_hook.py scripts/
cp .claude/commands/setup-python-hook/scripts/run_python_hook.sh scripts/
chmod +x scripts/run_python_hook.sh
```

This is better than writing the scripts from scratch — the bundled versions are tested and handle edge cases (missing tools, non-.py files, pyright JSON output parsing).

### 4. Create requirements-dev.txt

Create `requirements-dev.txt` so teammates can replicate:
```
ruff
pyright
```

### 5. Register the hook

Create or update `.claude/settings.json`. If the file exists and has other content, merge carefully rather than overwriting.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/run_python_hook.sh"
          }
        ]
      }
    ]
  }
}
```

### 6. Verify

Create a file `_hook_smoke_test.py` with a deliberate type error, then watch the hook fire:

```python
def greet(name: str) -> str:
    return 42  # type error: returns int, not str
```

The hook should trigger immediately after you write the file and report:
```
=== Pyright (type errors) ===
  _hook_smoke_test.py:2: error: Expression of type "int" is not assignable to return type "str"
```

Then delete `_hook_smoke_test.py` — the hook is working.

### 7. Report to the user

Confirm:
- ✓ `.venv` created with ruff and pyright
- ✓ `scripts/python_check_hook.py` installed
- ✓ `scripts/run_python_hook.sh` installed (venv-aware)
- ✓ `.claude/settings.json` configured
- ✓ Hook verified with smoke test

Mention: commit `scripts/`, `.claude/settings.json`, and `requirements-dev.txt` to git. Teammates get the hook automatically after `git clone` + `pip install -r requirements-dev.txt`.

## How the hook works

| Component | Role |
|---|---|
| `run_python_hook.sh` | venv-aware wrapper — finds `.venv/bin/python` or falls back to system `python3`, prepends `.venv/bin` to PATH so ruff/pyright resolve |
| `python_check_hook.py` | Reads the JSON Claude Code sends via stdin, extracts the modified file path, runs Ruff on that file + Pyright on the whole project |
| Exit code 0 | No errors — Claude Code continues normally |
| Exit code 2 | Errors found — Claude Code injects the error output into Claude's context, forcing it to find and fix the broken call sites |
