"""Execute the actual documented ledger checks against completion counterexamples."""

from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
BASH = Path("C:/Program Files/Git/bin/bash.exe")


@pytest.mark.parametrize("engine", ["intake", "shakedown"])
@pytest.mark.parametrize("case", [
    "empty", "blank", "pipe_only", "valid_pipes", "open", "bad_id",
    "bad_status", "partial_header", "duplicate_header", "missing_separator",
    "reversed_header", "header_only", "missing", "zero_byte",
])
def test_zero_requires_valid_table_and_outcome(engine, case, tmp_path):
    bash = str(BASH) if BASH.is_file() else shutil.which("bash")
    if not bash:
        pytest.skip("Bash is required to execute the documented Bash checks")
    core = (ROOT / "_shared" / f"{engine}-engine.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\n(.*?)\n```", core, re.S)
    check = next(block for block in blocks if "WELL=$(grep" in block)
    # Bind only the ledger locator to a disposable fixture; execute every guard unchanged.
    lines = check.splitlines()
    assert lines[0].startswith("LEDGER=")
    lines[0] = 'LEDGER="$1"'
    script = tmp_path / "check.sh"
    script.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    if engine == "intake":
        header = "| id | fragment | route | status | disposition |"
        separator = "|---|---|---|---|---|"
        prefix, status = "| F1 | task | do |", "routed"
    else:
        header = "| id | source | status | evidence |"
        separator = "|---|---|---|---|"
        prefix, status = "| D1 | derived |", "satisfied"
    tail = {"empty": "", "blank": "   |", "pipe_only": " | |  |"}.get(
        case, " command `printf yes | cat` observed yes |"
    )
    if case == "open":
        status = "open"
    elif case == "bad_status":
        status = "invented"
    if case == "bad_id":
        prefix = prefix.replace("F1", "X1").replace("D1", "X1")
    row = f"{prefix} {status} |{tail}"
    body = f"{header}\n{separator}\n{row}\n"
    if case == "partial_header":
        body = "| id |\n"
    elif case == "duplicate_header":
        body = f"{header}\n{separator}\n{header}\n"
    elif case == "missing_separator":
        body = header + "\n"
    elif case == "reversed_header":
        body = f"{separator}\n{header}\n"
    elif case == "header_only":
        body = f"{header}\n{separator}\n"
    elif case == "zero_byte":
        body = ""
    ledger = tmp_path / "ledger.md"
    if case != "missing":
        ledger.write_text(body, encoding="utf-8", newline="\n")

    def shell_path(path):
        value = path.as_posix()
        return f"/{value[0].lower()}{value[2:]}" if len(value) > 1 and value[1] == ":" else value

    result = subprocess.run(
        [bash, shell_path(script), shell_path(ledger)],
        capture_output=True, text=True, timeout=15,
    )
    clean = result.returncode == 0 and result.stdout.strip() == "0"
    assert clean == (case in {"valid_pipes", "header_only"}), (
        engine, case, result.returncode, result.stdout, result.stderr
    )
    if case in {"empty", "blank", "pipe_only", "open", "bad_id", "bad_status"}:
        assert result.returncode == 0 and int(result.stdout.strip()) > 0
    elif case not in {"valid_pipes", "header_only"}:
        assert result.returncode != 0
