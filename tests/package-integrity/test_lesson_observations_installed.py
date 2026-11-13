"""Installed-package check for the lesson-observation helper (Phase LH Step 153).

The behavioural cases for `_shared/lesson_observations.py` live in
`tests/behavioural/test_lesson_observations.py` (moved there by v3 guard Step 6, so
they no longer run inside `tools/release.ps1`'s staged package-integrity check).
This one case stays in package-integrity on purpose: it grades the GENERATED helper
from a built distribution, copied into a tree with no source checkout, so it is a
package check and must keep running inside the staged release tree.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "_shared" / "lesson_observations.py"
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"
PROVENANCE_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-provenance.ps1"
# The path the builder emits the helper to, relative to one profile's output root.
EMITTED_RELATIVE = Path("claude") / "_shared" / "lesson_observations.py"

GIT = shutil.which("git")
PWSH = shutil.which("powershell")
pytestmark = pytest.mark.skipif(GIT is None, reason="git is not available on PATH")

EXIT_OK = 0


def _git(cwd, *args):
    result = subprocess.run(
        [GIT] + list(args), cwd=str(cwd), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    assert result.returncode == 0, f"git {args} failed: {result.stderr}"
    return result.stdout.strip()


def run_helper(*args, **kwargs):
    """Drive the real CLI in a subprocess and return the CompletedProcess."""
    helper = kwargs.pop("helper", HELPER)
    cwd = kwargs.pop("cwd", None)
    assert not kwargs, f"unexpected keyword arguments: {sorted(kwargs)}"
    return subprocess.run(
        [sys.executable, str(helper)] + [str(a) for a in args],
        cwd=None if cwd is None else str(cwd),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def ok_json(result):
    assert result.returncode == EXIT_OK, (
        f"expected exit 0, got {result.returncode}: {result.stderr}")
    return json.loads(result.stdout)


def _marker_literal():
    """The single-source-of-truth provenance marker, read from the shared script."""
    match = re.search(
        r"return\s+'([^']+)'", PROVENANCE_SCRIPT.read_text(encoding="utf-8"))
    assert match, "marker literal not found in tools/skill-mesh-provenance.ps1"
    return match.group(1)


@pytest.fixture(scope="session")
def emitted_helper(tmp_path_factory):
    """The GENERATED helper, built on demand. There is NO fallback to the source.

    This fixture exists because the earlier spelling of this file chose
    `dist/claude/... if it exists else _shared/...`, and `dist/` is gitignored and
    built by no test here. On a fresh clone, in CI, and on the plan's own documented
    command order (this file runs before build-distributions.ps1), that conditional
    quietly turned the one test of the SHIPPED artifact into a second test of the
    source -- green, silent, and unable to see a builder that stopped emitting the
    helper at all. A fallback path is exactly what `measurement-validity` says to
    abort on rather than warn about, so the build is performed HERE, into a
    throwaway directory, and every way it can fail to produce the artifact is a red
    test with an actionable message.
    """
    if PWSH is None:
        pytest.skip("powershell is not on PATH; the distribution cannot be built")
    out_dir = tmp_path_factory.mktemp("lesson-dist")
    result = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(BUILD_SCRIPT),
         "-OutputDir", str(out_dir), "-Provider", "claude"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert result.returncode == 0, (
        "tools/build-distributions.ps1 -Provider claude failed, so the generated "
        f"helper cannot be graded:\n{result.stdout}\n{result.stderr}")
    emitted = out_dir / EMITTED_RELATIVE
    assert emitted.is_file(), (
        "build-distributions.ps1 did not emit _shared/lesson_observations.py into "
        "the claude profile. The shared-closure walk no longer reaches it -- most "
        "likely because skills/lesson-harvest/core.md stopped referencing it as "
        "`<repo>/_shared/lesson_observations.py`. Fix the builder or the reference; "
        "do not weaken this assertion.")
    body = emitted.read_text(encoding="utf-8")
    assert _marker_literal() in body, (
        "the emitted helper carries no generated-file provenance marker, so this "
        "is not the built artifact")
    assert body != HELPER.read_text(encoding="utf-8"), (
        "the emitted helper is byte-identical to the source checkout, so this test "
        "would not be able to tell the two apart")
    return emitted


def observation_request(observation_id, **overrides):
    request = {
        "observation_id": observation_id,
        "session": "manual-session",
        "source": "assistant message 14 / tool result 12",
        "observed_error": "reported a file as edited when the edit never applied",
        "evidence": ["tool result 12", "tool result 13"],
        "correction": "re-read the target file before reporting an edit",
        "supersedes": None,
    }
    request.update(overrides)
    return request


def write_request(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def snapshot(root):
    """Every file under `root` as {relative path: bytes}. Absent root -> empty."""
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def observed_ids(page):
    return [entry["observation_id"] for entry in page["observations"]]


def test_the_generated_helper_runs_from_an_installed_package_without_this_checkout(
        tmp_path, emitted_helper):
    """The consumer executes the EMITTED file, from a tree that has no source.

    A skill resolves its helper from its own installed package, never from a source
    checkout and never from the caller's working directory -- so the artifact is
    copied out, the process is started somewhere unrelated, and every path it is
    given is absolute.

    `emitted_helper` builds the distribution and refuses to substitute the source
    checkout for it, so this test either exercises the generated artifact or fails.
    """
    source = emitted_helper
    installed = tmp_path / "home" / "skills" / "_shared"
    installed.mkdir(parents=True)
    helper = installed / "lesson_observations.py"
    shutil.copyfile(str(source), str(helper))
    assert not (tmp_path / "home" / "config").exists()

    project = tmp_path / "consumer"
    project.mkdir()
    _git(project, "init", "-q", ".")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    minted = run_helper("new-id", helper=helper, cwd=elsewhere)
    assert minted.returncode == EXIT_OK, minted.stderr
    identifier = minted.stdout.strip()

    request_file = tmp_path / "request.json"
    write_request(request_file, observation_request(identifier))
    recorded = run_helper("record", "--repo", project, "--input", request_file,
                          helper=helper, cwd=elsewhere)
    assert ok_json(recorded)["status"] == "recorded"

    page = ok_json(run_helper("pending", "--repo", project, helper=helper,
                              cwd=elsewhere))
    assert observed_ids(page) == [identifier]
    assert snapshot(elsewhere) == {}, (
        "the helper wrote into its working directory instead of the target inbox")
