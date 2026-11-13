"""Build-level checks for user-fermize's generated profiles (v3 catalog cleanup Step 5, #261).

user-fermize was created in the catalog from the operator's personal Codex skill. It has no
production caller yet (the v3 user-pm plan's Steps 17 and 18 add one), so this is not a
caller test: it proves the generated Claude and Codex profiles, built from the committed
manifest record, load the co-located core in full and carry its read-only, advice-only
contract. The garbage anchors prove the check can fail: an adapter that stops loading the
core, and a core that loses the read-only or advice-only clause, must both be rejected.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest


PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
SKILL = "user-fermize"
PROVIDERS = ("claude", "codex")

LOAD_LINE = "See [core.md](core.md) for the full specification. Load the core in full before acting."
# The clauses that make the skill read-only and advice-only; each is a sentence of the core.
CONTRACT = (
    "Supply advice, not approval or certification.",
    "Use read-only inspection.",
    "Do not execute project code, tests, builds, or plan commands; edit files, queues, or "
    "gates; install anything; dispatch agents; or contact external services.",
    "Recommendations do not authorize their execution.",
)
ADAPTER_GUARD = "Keep the core's scope, gates, and advisory boundary unchanged."


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    assert PWSH is not None, "powershell is required for distribution profile tests"
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(script), *args],
        capture_output=True,
        text=True,
    )


def _skill_entry() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return next(entry for entry in manifest["skills"] if entry["name"] == SKILL)


def _package_loads_the_contract(launcher: str, core: str) -> bool:
    """True when the launcher loads the co-located core in full and the core carries the contract."""
    return (
        LOAD_LINE in launcher
        and ADAPTER_GUARD in launcher
        and all(clause in core for clause in CONTRACT)
    )


@pytest.fixture(scope="module")
def built_profiles(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("user-fermize-profiles")
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"skills": [_skill_entry()]}), encoding="utf-8")
    output = root / "dist"
    result = _run(BUILD_SCRIPT, "-ManifestPath", str(manifest), "-OutputDir", str(output),
                  "-Provider", "all")
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    return output


def test_manifest_record_is_portable_with_all_three_adapters() -> None:
    entry = _skill_entry()
    assert entry["status"] == "portable"
    assert entry["core"] == "skills/user-fermize/core.md"
    assert set(entry["providers"]) == {"claude", "gpt", "codex"}


@pytest.mark.parametrize("provider", PROVIDERS)
def test_profile_loads_the_core_and_carries_the_read_only_advice_only_contract(
    built_profiles: Path, provider: str
) -> None:
    package = built_profiles / provider / SKILL
    files = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
    assert files == {"SKILL.md", "core.md"}
    launcher = (package / "SKILL.md").read_text(encoding="utf-8")
    core = (package / "core.md").read_text(encoding="utf-8")
    assert launcher.startswith("---\nname: user-fermize\n"), launcher[:80]
    assert _package_loads_the_contract(launcher, core)


def test_check_rejects_a_launcher_or_core_that_drops_the_contract(built_profiles: Path) -> None:
    package = built_profiles / "codex" / SKILL
    launcher = (package / "SKILL.md").read_text(encoding="utf-8")
    core = (package / "core.md").read_text(encoding="utf-8")
    assert _package_loads_the_contract(launcher, core)
    # An adapter that no longer loads the co-located core in full.
    assert not _package_loads_the_contract(
        launcher.replace("Load the core in full before acting.", ""), core)
    # An adapter that drops the scope-and-gates guard.
    assert not _package_loads_the_contract(launcher.replace(ADAPTER_GUARD, ""), core)
    # A core that loses any one read-only or advice-only clause.
    for clause in CONTRACT:
        assert not _package_loads_the_contract(launcher, core.replace(clause, ""))
