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

Three further behaviours are pinned here (morning item 62):

- Non-ASCII text. Linters print UTF-8. Without UTF-8 mode, python on Windows
  decodes stdin with the locale code page (cp1252), so both python calls -- the
  adapter and `json_escape` -- turned a message such as `café` into mojibake.
  Every run sets `PYTHONUTF8=0` and drops `PYTHONIOENCODING`, so the script
  must get this right on its own, whatever the host's settings or python
  version.
- Option guard. A changed file whose name starts with `-` must reach ruff,
  mypy and eslint as a path, after a `--`, never as an option. The fakes record
  their argv so the test reads exactly what each tool was handed.
- `--help` (and `-h`) prints usage on stdout and exits 0. The usage-error
  anchor keeps the error paths at exit 2 with usage on stderr.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

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
    payload byte passes through shell quoting. Each argument the tool received
    is recorded, one per line, in `<name>.argv` beside it."""
    _write(bin_dir / f"{name}.out", output)
    tool = bin_dir / name
    _write(tool, "#!/bin/sh\n"
                 f"printf '%s\\n' \"$@\" > \"$(dirname \"$0\")/{name}.argv\"\n"
                 f'cat "$(dirname "$0")/{name}.out"\nexit {exit_code}\n')
    tool.chmod(0o755)


def _invoke(cwd: Path, args: list[str], bin_dir: Path | None = None) -> subprocess.CompletedProcess:
    """Run the script under Git Bash from `cwd` with `args`.

    PATH puts the fakes first (when given), then this interpreter, which the
    script runs as `python`. `PYTHONUTF8=0` and no `PYTHONIOENCODING` model
    python's Windows default, the locale code page, on every host and python
    version: the script has to ask for UTF-8 itself."""
    assert GIT_BASH.is_file(), "Git Bash is required to run review-deep's lint pre-pass"
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env["PYTHONUTF8"] = "0"
    path = [str(Path(sys.executable).parent), env.get("PATH", "")]
    if bin_dir is not None:
        path.insert(0, str(bin_dir))
    env["PATH"] = os.pathsep.join(path)
    return subprocess.run(
        [str(GIT_BASH), SCRIPT.as_posix(), *args],
        cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=180)


def _run(tmp_path: Path, diff_paths: list[str], tools: dict[str, tuple[str, int]],
         configs: tuple[str, ...] = ()) -> dict:
    """Run the pre-pass in a fresh project; return the parsed lint-findings.json.

    `tools` maps a tool name to (output, exit_code); `configs` are file names
    created empty in the project root (the script's config-ancestry probe only
    checks that they exist)."""
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
    proc = _invoke(project, ["--output-dir", out.as_posix(),
                             "--diff-paths", ",".join(diff_paths)], bin_dir)
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


# Latin-1 (2 bytes), curly quotes (U+201D's UTF-8 holds 0x9D, a byte cp1252
# leaves undefined), an arrow, CJK (3 bytes) and an emoji outside the BMP.
# The final `à` is UTF-8 C3 A0, and cp1252 reads A0 as a no-break space. The
# adapter strips each message, so without UTF-8 mode the adapter, not only
# `json_escape`, cuts that byte and breaks the last character.
NON_ASCII_MESSAGE = "café “quoted” → 中文 \U0001F600 voilà"


def test_non_ascii_message_survives_end_to_end(tmp_path: Path) -> None:
    payload = [{"code": "E501", "filename": PY_SOURCE, "location": {"row": 3},
                "message": NON_ASCII_MESSAGE}]
    # Raw UTF-8 on the wire, as ruff and eslint print it, not \u escapes.
    raw = json.dumps(payload, ensure_ascii=False)
    assert not raw.isascii()
    result = _run(tmp_path, [PY_SOURCE], {"ruff": (raw, 1)})
    assert "ruff" in result["tools_run"], result
    assert _findings(result, "ruff") == [
        {"tool": "ruff", "rule": "E501", "file_line": f"{PY_SOURCE}:3",
         "message": NON_ASCII_MESSAGE},
    ], result


def test_dash_file_names_reach_every_tool_as_paths_not_options(tmp_path: Path) -> None:
    py_name, js_name = "--fix.py", "--debug.js"
    result = _run(tmp_path, [py_name, js_name],
                  {"ruff": ("[]", 0), "mypy": ("", 0), "eslint": ("[]", 0)},
                  configs=("mypy.ini", ".eslintrc.json"))
    assert result["tools_run"] == ["ruff", "mypy", "eslint"], result
    for tool, name in (("ruff", py_name), ("mypy", py_name), ("eslint", js_name)):
        argv = (tmp_path / "fakebin" / f"{tool}.argv").read_text(encoding="utf-8").splitlines()
        assert "--" in argv, (tool, argv)
        end = argv.index("--")
        assert name not in argv[:end], (tool, argv)
        assert argv[end + 1:] == [name], (tool, argv)


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_help_exits_zero_with_usage_on_stdout(tmp_path: Path, flag: str) -> None:
    proc = _invoke(tmp_path, [flag])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.startswith("usage: bash lint_prepass.sh --output-dir"), proc.stdout
    assert proc.stderr == "", proc.stderr
    assert list(tmp_path.iterdir()) == []  # help writes nothing


@pytest.mark.parametrize("args", [["--bogus"], []], ids=["unknown-argument", "no-output-dir"])
def test_usage_errors_still_exit_two_with_usage_on_stderr(tmp_path: Path, args: list[str]) -> None:
    # Anchor for the --help change: usage now prints to stdout, and the error
    # paths must still send it to stderr with exit 2.
    proc = _invoke(tmp_path, args)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert proc.stdout == "", proc.stdout
    assert "usage: bash lint_prepass.sh" in proc.stderr, proc.stderr
