"""Behavioural gate: review-deep's lint pre-pass must keep the findings it parses.

`skills/review-deep/scripts/lint_prepass.sh` parses ruff / mypy / eslint output
through an embedded python adapter that reads the raw tool output on stdin. It
used to be spelled

    printf %s "$raw" | python - "$tool" <<'PY' ... PY

The heredoc redirection overrides the pipe as python's stdin, so python read its
PROGRAM from the heredoc, the pipe carrying the tool output was discarded unread,
and `sys.stdin.read()` inside the adapter returned "" on every call. Every
finding was dropped and `lint-findings.json` always said `"findings": []` -- a
silent false green for every lens that cites the pre-pass.

Every case here drives the PRODUCTION entry point -- the script under Git Bash,
run from the project root exactly as `scripts/README.md` documents it -- in a
temporary project outside the repository. Fake `ruff` / `mypy` / `eslint`
executables sit first on PATH and print a fixed payload, so the result does not
depend on which real linters this machine has. Each payload must come back as
findings carrying the payload's own rule, file:line and message; the old script
returns zero findings and reds here. The known-clean anchor (the tool runs and
prints an empty result) must still yield no findings, so a script that invented
findings fails too.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "review-deep" / "scripts" / "lint_prepass.sh"
GIT_BASH = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git" / "bin" / "bash.exe"

PY_SOURCE = "src/sample.py"  # relative to the fake project, which is the run's cwd
JS_SOURCE = "web/app.js"

RUFF_PAYLOAD = [
    {"code": "F401", "filename": PY_SOURCE, "location": {"row": 1, "column": 8},
     "message": "`os` imported but unused"},
    {"code": "E711", "filename": PY_SOURCE, "location": {"row": 4, "column": 10},
     "message": "Comparison to `None` should be `cond is None`"},
]
MYPY_RECORDS = [
    {"file": PY_SOURCE, "line": 5, "column": 11, "severity": "error", "hint": None,
     "code": "return-value",
     "message": 'Incompatible return value type (got "int", expected "str")'},
    {"file": PY_SOURCE, "line": 7, "column": 4, "severity": "error", "hint": None,
     "code": "name-defined", "message": 'Name "undefined_name" is not defined'},
]
ESLINT_PAYLOAD = [
    {"filePath": JS_SOURCE, "messages": [
        {"ruleId": "no-unused-vars", "line": 2,
         "message": "'unused' is assigned a value but never used."},
    ]},
]


def _write(path: Path, text: str) -> None:
    """Write LF-only text: a CRLF shebang line would break the fake tools."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _fake_tool(bin_dir: Path, name: str, output: str, exit_code: int) -> None:
    """A PATH executable that prints `output` verbatim and exits `exit_code`.

    The payload lives beside the script and is read back with `cat`, so no
    payload byte passes through shell quoting."""
    _write(bin_dir / f"{name}.out", output)
    tool = bin_dir / name
    _write(tool, f'#!/bin/sh\ncat "$(dirname "$0")/{name}.out"\nexit {exit_code}\n')
    tool.chmod(0o755)


def _run(tmp_path: Path, diff_paths: list[str], tools: dict[str, tuple[str, int]],
         configs: tuple[str, ...] = ()) -> dict:
    """Run the pre-pass in a fresh project; return the parsed lint-findings.json.

    `tools` maps a tool name to (output, exit_code); `configs` are file names
    created empty in the project root (the script's config-ancestry probe only
    checks that they exist)."""
    assert GIT_BASH.is_file(), "Git Bash is required to run review-deep's lint pre-pass"
    project = tmp_path / "project"
    for rel in diff_paths:
        _write(project / rel, "x = 1\n")
    for name in configs:
        _write(project / name, "")
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    for name, (output, exit_code) in tools.items():
        _fake_tool(bin_dir, name, output, exit_code)
    out = tmp_path / "out"
    env = dict(os.environ)
    # Fakes first; then this interpreter, which the script's adapter runs as `python`.
    env["PATH"] = os.pathsep.join(
        [str(bin_dir), str(Path(sys.executable).parent), env.get("PATH", "")])
    proc = subprocess.run(
        [str(GIT_BASH), SCRIPT.as_posix(), "--output-dir", out.as_posix(),
         "--diff-paths", ",".join(diff_paths)],
        cwd=project, env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=180)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads((out / "lint-findings.json").read_text(encoding="utf-8"))


def _findings(result: dict, tool: str) -> list[dict]:
    return [f for f in result["findings"] if f["tool"] == tool]


def test_ruff_json_array_findings_reach_lint_findings(tmp_path: Path) -> None:
    result = _run(tmp_path, [PY_SOURCE], {"ruff": (json.dumps(RUFF_PAYLOAD), 1)})
    assert "ruff" in result["tools_run"], result
    assert _findings(result, "ruff") == [
        {"tool": "ruff", "rule": "F401", "file_line": f"{PY_SOURCE}:1",
         "message": "`os` imported but unused"},
        {"tool": "ruff", "rule": "E711", "file_line": f"{PY_SOURCE}:4",
         "message": "Comparison to `None` should be `cond is None`"},
    ], result


def test_mypy_ndjson_findings_reach_lint_findings(tmp_path: Path) -> None:
    # mypy runs only under a mypy.ini (or pyproject [tool.mypy]) in the cwd
    # ancestry. Its JSON output is NDJSON; a trailing summary line is not JSON
    # and must be skipped, not abort the parse.
    ndjson = "".join(json.dumps(r) + "\n" for r in MYPY_RECORDS)
    ndjson += "Found 2 errors in 1 file (checked 1 source file)\n"
    result = _run(tmp_path, [PY_SOURCE],
                  {"ruff": ("[]", 0), "mypy": (ndjson, 1)}, configs=("mypy.ini",))
    assert {"ruff", "mypy"} <= set(result["tools_run"]), result
    assert _findings(result, "ruff") == [], result
    assert _findings(result, "mypy") == [
        {"tool": "mypy", "rule": "return-value", "file_line": f"{PY_SOURCE}:5",
         "message": 'Incompatible return value type (got "int", expected "str")'},
        {"tool": "mypy", "rule": "name-defined", "file_line": f"{PY_SOURCE}:7",
         "message": 'Name "undefined_name" is not defined'},
    ], result


def test_eslint_findings_reach_lint_findings(tmp_path: Path) -> None:
    result = _run(tmp_path, [JS_SOURCE], {"eslint": (json.dumps(ESLINT_PAYLOAD), 1)},
                  configs=(".eslintrc.json",))
    assert result["tools_run"] == ["eslint"], result
    assert result["findings"] == [
        {"tool": "eslint", "rule": "no-unused-vars", "file_line": f"{JS_SOURCE}:2",
         "message": "'unused' is assigned a value but never used."},
    ], result


def test_clean_tool_output_yields_no_findings(tmp_path: Path) -> None:
    # Known-good anchor: the tool ran and reported nothing. A pre-pass that
    # fabricated findings (or mis-split an empty result into a row) reds here.
    result = _run(tmp_path, [PY_SOURCE], {"ruff": ("[]", 0)})
    assert "ruff" in result["tools_run"], result
    assert _findings(result, "ruff") == [], result
