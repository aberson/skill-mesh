"""Build-level checks for build-observer's reviewed packaged validator."""

import json
import py_compile
import re
import shutil
import subprocess
from pathlib import Path

import pytest


PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"
PROVENANCE_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-provenance.ps1"
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
SKILL_ROOT = REPO_ROOT / "skills" / "build-observer"
RESOURCE = "scaffold_portfolio.py"
PROVIDERS = ("claude", "gpt", "codex")


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    assert PWSH is not None, "powershell is required for distribution resource tests"
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(script), *args],
        capture_output=True,
        text=True,
    )


def _skill_entry() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return next(entry for entry in manifest["skills"] if entry["name"] == "build-observer")


def _normalized_source() -> bytes:
    return (SKILL_ROOT / RESOURCE).read_bytes().lstrip(b"\xef\xbb\xbf").replace(
        b"\r\n", b"\n"
    ).replace(b"\r", b"\n")


def _strip_python_provenance(emitted: str) -> str:
    start = emitted.index("\n<!-- GENERATED FILE - DO NOT EDIT.")
    closing = "edits here are overwritten. -->"
    end = emitted.index(closing, start) + len(closing)
    assert emitted[start - 3 : start] == '\"\"\"'
    return emitted[:start] + emitted[end:]


@pytest.fixture(scope="module")
def built_profiles(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("build-observer-resources")
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"skills": [_skill_entry()]}), encoding="utf-8")
    output = root / "dist"
    result = _run(
        BUILD_SCRIPT,
        "-ManifestPath",
        str(manifest),
        "-OutputDir",
        str(output),
        "-Provider",
        "all",
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    return output


@pytest.mark.parametrize("provider", PROVIDERS)
def test_validator_is_contained_provenanced_and_compiles(
    built_profiles: Path, provider: str, tmp_path: Path
) -> None:
    package = built_profiles / provider / "build-observer"
    files = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
    assert files == {"SKILL.md", "core.md", RESOURCE}

    emitted_path = package / RESOURCE
    assert emitted_path.resolve().is_relative_to(built_profiles.resolve())
    matches = set(built_profiles.rglob(RESOURCE))
    assert matches == {
        built_profiles / current / "build-observer" / RESOURCE for current in PROVIDERS
    }

    emitted = emitted_path.read_text(encoding="utf-8")
    marker = re.search(r"return\s+'([^']+)'", PROVENANCE_SCRIPT.read_text(encoding="utf-8"))
    assert marker and marker.group(1) in emitted
    assert f"Canonical source: skills/build-observer/{RESOURCE}" in emitted
    assert f"Profile: {provider}" in emitted
    assert _strip_python_provenance(emitted).encode("utf-8") == _normalized_source()

    cfile = tmp_path / provider / "scaffold_portfolio.pyc"
    cfile.parent.mkdir(parents=True)
    py_compile.compile(str(emitted_path), cfile=str(cfile), doraise=True)
    assert cfile.is_file()
    assert not list(package.rglob("__pycache__"))


def test_builder_refuses_missing_validator_before_emitting_package(tmp_path: Path) -> None:
    repo = tmp_path / "synthetic-repo"
    for relative in ("tools", "runtime", "config", "_shared", "skills/build-observer/providers"):
        (repo / relative).mkdir(parents=True, exist_ok=True)
    for name in ("build-distributions.ps1", "skill-mesh-provenance.ps1"):
        shutil.copy2(REPO_ROOT / "tools" / name, repo / "tools" / name)
    shutil.copy2(REPO_ROOT / "runtime" / "path-guard.ps1", repo / "runtime" / "path-guard.ps1")
    (repo / "_shared" / "build_step_verdict.py").write_text(
        '\"\"\"synthetic verdict helper.\"\"\"\n', encoding="utf-8"
    )
    shutil.copy2(SKILL_ROOT / "core.md", repo / "skills" / "build-observer" / "core.md")
    for provider in PROVIDERS:
        shutil.copy2(
            SKILL_ROOT / "providers" / f"{provider}.md",
            repo / "skills" / "build-observer" / "providers" / f"{provider}.md",
        )
    (repo / "config" / "skill-manifest.json").write_text(
        json.dumps({"skills": [_skill_entry()]}), encoding="utf-8"
    )

    output = tmp_path / "dist"
    result = _run(
        repo / "tools" / "build-distributions.ps1",
        "-OutputDir",
        str(output),
        "-Provider",
        "all",
    )
    assert result.returncode != 0
    assert "build-observer resource source missing: scaffold_portfolio.py" in result.stderr
    if output.exists():
        assert not any(output.rglob("build-observer"))
