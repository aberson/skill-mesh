"""Release-gate checks (Step 38 of documentation/provider-neutral-skill-mesh-plan.md):
link checker, manifest completeness, source->distribution drift, provider-wrapper/
core-reference, skill-count, README-claim, and no-tracked-generated-distribution.

Each of the 7 checks has a POSITIVE test against the real repository (or a real
build produced by the real tools/build-distributions.ps1) and a NEGATIVE test
that plants the exact defect named in plan Step 38's Done-when list and asserts
the checker goes red -- a gate that cannot go red is worthless
(.claude/rules/measurement-validity.md). All check LOGIC lives in
tools/release_checks.py (imported here, never re-implemented) so this test
suite and tools/release.ps1's CHECK phase are graded by the identical code.

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
README_PATH = REPO_ROOT / "README.md"
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import release_checks  # noqa: E402

PWSH = shutil.which("powershell")
GIT = shutil.which("git")

pwsh_skip = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")
git_skip = pytest.mark.skipif(GIT is None, reason="git is not available on PATH")


def load_manifest():
    return release_checks.load_manifest(REPO_ROOT)


def load_readme():
    return README_PATH.read_text(encoding="utf-8")


def _doc_paths():
    paths = [README_PATH]
    paths += sorted((REPO_ROOT / "documentation").rglob("*.md"))
    return paths


def _build(out_dir, provider="both"):
    r = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(BUILD_SCRIPT),
         "-OutputDir", str(out_dir), "-Provider", provider],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"build failed:\n{r.stdout}\n{r.stderr}"
    return out_dir


# --------------------------------------------------------------------------- #
# 1. LINK CHECKER
# --------------------------------------------------------------------------- #

def test_link_checker_clean_on_real_docs():
    offenders = release_checks.find_broken_local_links(_doc_paths(), REPO_ROOT)
    assert not offenders, "broken local link(s):\n" + "\n".join(offenders)


def test_link_checker_reds_on_planted_broken_link(tmp_path):
    (tmp_path / "documentation").mkdir()
    doc = tmp_path / "README.md"
    doc.write_text("See the [missing guide](documentation/DOES_NOT_EXIST.md).\n",
                    encoding="utf-8")
    offenders = release_checks.find_broken_local_links([doc], tmp_path)
    assert offenders and "DOES_NOT_EXIST.md" in offenders[0]


def test_link_checker_ignores_external_and_placeholder_targets(tmp_path):
    doc = tmp_path / "README.md"
    doc.write_text(
        "[anthropic](https://docs.anthropic.com/claude-code) "
        "[mail](mailto:a@b.com) "
        "[tpl](<workspace>/x.md)\n",
        encoding="utf-8")
    offenders = release_checks.find_broken_local_links([doc], tmp_path)
    assert not offenders


def test_link_checker_ignores_refs_escaping_the_release_root(tmp_path):
    (tmp_path / "release").mkdir()
    doc = tmp_path / "release" / "README.md"
    # A citation that resolves OUTSIDE the release root entirely (a legacy/
    # external workspace reference) is not a package-integrity defect here.
    doc.write_text("[external](../../outside-the-release/notes.md)\n", encoding="utf-8")
    offenders = release_checks.find_broken_local_links([doc], tmp_path / "release")
    assert not offenders


def test_link_checker_reds_on_broken_img_src(tmp_path):
    doc = tmp_path / "README.md"
    doc.write_text('<img alt="diagram" src="_shared/missing-diagram.svg">\n', encoding="utf-8")
    offenders = release_checks.find_broken_local_links([doc], tmp_path)
    assert offenders and "missing-diagram.svg" in offenders[0]


def test_link_checker_reds_on_broken_picture_source_srcset(tmp_path):
    (tmp_path / "_shared").mkdir()
    doc = tmp_path / "README.md"
    doc.write_text(
        '<picture>\n'
        '  <source media="(prefers-color-scheme: dark)" srcset="_shared/missing-dark.svg">\n'
        '  <img alt="x" src="_shared/present-light.svg">\n'
        '</picture>\n',
        encoding="utf-8")
    (tmp_path / "_shared" / "present-light.svg").write_text("<svg/>", encoding="utf-8")
    offenders = release_checks.find_broken_local_links([doc], tmp_path)
    assert offenders and "missing-dark.svg" in offenders[0]


def test_link_checker_clean_on_present_img_and_srcset(tmp_path):
    (tmp_path / "_shared").mkdir()
    (tmp_path / "_shared" / "a-dark.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / "_shared" / "a-light.svg").write_text("<svg/>", encoding="utf-8")
    doc = tmp_path / "README.md"
    doc.write_text(
        '<picture>\n'
        '  <source media="(prefers-color-scheme: dark)" srcset="_shared/a-dark.svg">\n'
        '  <img alt="x" src="_shared/a-light.svg">\n'
        '</picture>\n',
        encoding="utf-8")
    offenders = release_checks.find_broken_local_links([doc], tmp_path)
    assert not offenders


def test_link_checker_strips_hover_title_before_resolving(tmp_path):
    (tmp_path / "documentation").mkdir()
    (tmp_path / "documentation" / "guide.md").write_text("x", encoding="utf-8")
    doc = tmp_path / "README.md"
    # A hover-title suffix must not leak into the resolved path.
    doc.write_text('[guide](documentation/guide.md "The Guide")\n', encoding="utf-8")
    offenders = release_checks.find_broken_local_links([doc], tmp_path)
    assert not offenders


# --------------------------------------------------------------------------- #
# 2. MANIFEST COMPLETENESS
# --------------------------------------------------------------------------- #

def test_manifest_completeness_clean_on_real_tree():
    defects = release_checks.manifest_completeness_defects(load_manifest(), REPO_ROOT)
    assert not defects, "manifest completeness defect(s):\n" + "\n".join(defects)


def test_manifest_completeness_reds_on_missing_adapter(tmp_path):
    (tmp_path / "skills" / "foo" / "providers").mkdir(parents=True)
    (tmp_path / "skills" / "foo" / "core.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "foo" / "providers" / "claude.md").write_text("x", encoding="utf-8")
    manifest = {"skills": [{
        "name": "foo", "status": "portable",
        "core": "skills/foo/core.md",
        "providers": {"claude": "skills/foo/providers/claude.md"},
        # gpt adapter deliberately absent -- must be flagged
    }]}
    defects = release_checks.manifest_completeness_defects(manifest, tmp_path)
    assert any("gpt" in d and "foo" in d for d in defects)


def test_manifest_completeness_reds_on_orphan_skill_dir(tmp_path):
    (tmp_path / "skills" / "known" / "providers").mkdir(parents=True)
    (tmp_path / "skills" / "known" / "core.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "known" / "providers" / "claude.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "known" / "providers" / "gpt.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "orphan").mkdir(parents=True)  # not in manifest
    manifest = {"skills": [{
        "name": "known", "status": "portable",
        "core": "skills/known/core.md",
        "providers": {"claude": "skills/known/providers/claude.md",
                      "gpt": "skills/known/providers/gpt.md"},
    }]}
    defects = release_checks.manifest_completeness_defects(manifest, tmp_path)
    assert any("orphan" in d for d in defects)


def test_manifest_completeness_reds_on_missing_core_file(tmp_path):
    (tmp_path / "skills" / "foo" / "providers").mkdir(parents=True)
    (tmp_path / "skills" / "foo" / "providers" / "claude.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "foo" / "providers" / "gpt.md").write_text("x", encoding="utf-8")
    manifest = {"skills": [{
        "name": "foo", "status": "portable",
        "core": "skills/foo/core.md",  # declared but never written to disk
        "providers": {"claude": "skills/foo/providers/claude.md",
                      "gpt": "skills/foo/providers/gpt.md"},
    }]}
    defects = release_checks.manifest_completeness_defects(manifest, tmp_path)
    assert any("core" in d and "does not exist" in d for d in defects)


def test_manifest_completeness_reds_on_provider_native_with_core(tmp_path):
    (tmp_path / "skills" / "native" / "providers").mkdir(parents=True)
    (tmp_path / "skills" / "native" / "core.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "native" / "providers" / "claude.md").write_text("x", encoding="utf-8")
    manifest = {"skills": [{
        "name": "native", "status": "provider-native",
        "core": "skills/native/core.md",  # must be null for provider-native
        "providers": {"claude": "skills/native/providers/claude.md"},
    }]}
    defects = release_checks.manifest_completeness_defects(manifest, tmp_path)
    assert any("non-null core" in d and "native" in d for d in defects)


def test_manifest_completeness_reds_on_provider_native_with_gpt_adapter(tmp_path):
    (tmp_path / "skills" / "native" / "providers").mkdir(parents=True)
    (tmp_path / "skills" / "native" / "providers" / "claude.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "native" / "providers" / "gpt.md").write_text("x", encoding="utf-8")
    manifest = {"skills": [{
        "name": "native", "status": "provider-native",
        "core": None,
        "providers": {"claude": "skills/native/providers/claude.md",
                      "gpt": "skills/native/providers/gpt.md"},  # must be truthfully absent
    }]}
    defects = release_checks.manifest_completeness_defects(manifest, tmp_path)
    assert any("gpt adapter" in d and "native" in d for d in defects)


def test_manifest_completeness_reds_on_unknown_status(tmp_path):
    manifest = {"skills": [{"name": "mystery", "status": "bogus-status", "core": None, "providers": {}}]}
    defects = release_checks.manifest_completeness_defects(manifest, tmp_path)
    assert any("unknown status" in d and "mystery" in d for d in defects)


def test_manifest_completeness_reds_on_path_traversal_escape(tmp_path):
    # A hostile manifest 'core' pointing OUTSIDE the release root must be
    # refused, never silently followed (mirrors build-distributions.ps1's own
    # Resolve-SafeSource treatment of the manifest as untrusted input).
    (tmp_path / "skills" / "foo" / "providers").mkdir(parents=True)
    (tmp_path / "skills" / "foo" / "providers" / "claude.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "foo" / "providers" / "gpt.md").write_text("x", encoding="utf-8")
    outside = tmp_path.parent / "escape-target.md"
    outside.write_text("secret", encoding="utf-8")
    manifest = {"skills": [{
        "name": "foo", "status": "portable",
        "core": "skills/foo/../../../escape-target.md",
        "providers": {"claude": "skills/foo/providers/claude.md",
                      "gpt": "skills/foo/providers/gpt.md"},
    }]}
    defects = release_checks.manifest_completeness_defects(manifest, tmp_path)
    assert any("foo" in d and "core" in d for d in defects)


# --------------------------------------------------------------------------- #
# 3. SOURCE -> DISTRIBUTION DRIFT
# --------------------------------------------------------------------------- #
#
# A single module-scoped real build is shared as the "reference" across every
# drift/wrapper/core-reference test below (each subprocess build spawns a
# fresh powershell.exe, the dominant cost in this file); negative tests mutate
# their OWN throwaway copy of it, never the shared fixture, and each test that
# needs a genuinely-independent rebuild (to prove determinism/drift) still
# performs exactly one FRESH `_build()` of its own.

@pytest.fixture(scope="module")
def built_dist(tmp_path_factory):
    if PWSH is None:
        pytest.skip("powershell is not available on PATH")
    return _build(tmp_path_factory.mktemp("built-dist"))


def _copy_dist(built_dist, dest):
    shutil.copytree(built_dist, dest)
    return dest


@pwsh_skip
def test_drift_check_clean_between_two_independent_builds(built_dist, tmp_path):
    fresh = _build(tmp_path / "fresh")
    defects = release_checks.distribution_drift_defects(built_dist, fresh)
    assert not defects, "unexpected drift between two independent builds:\n" + "\n".join(defects)


@pwsh_skip
def test_drift_check_reds_on_hand_edited_stale_wrapper(built_dist, tmp_path):
    reference = _copy_dist(built_dist, tmp_path / "reference")
    target = next((reference / "claude").rglob("SKILL.md"))
    target.write_text(target.read_text(encoding="utf-8") + "\nHAND-EDITED-STALE-CONTENT\n",
                       encoding="utf-8")
    fresh = _build(tmp_path / "fresh")
    defects = release_checks.distribution_drift_defects(reference, fresh)
    assert defects, "drift check did not detect a hand-edited/stale generated wrapper"


# --------------------------------------------------------------------------- #
# 4. PROVIDER-WRAPPER / CORE-REFERENCE
# --------------------------------------------------------------------------- #

@pwsh_skip
def test_wrapper_core_reference_clean_on_real_build(built_dist):
    defects = release_checks.wrapper_core_reference_defects(built_dist, REPO_ROOT)
    assert not defects, "wrapper/core-reference defect(s):\n" + "\n".join(defects)


@pwsh_skip
def test_wrapper_core_reference_reds_on_invalid_core_path(built_dist, tmp_path):
    dist = _copy_dist(built_dist, tmp_path / "dist")
    skill_md = dist / "claude" / "build-phase" / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    assert "Canonical source: skills/build-phase/providers/claude.md" in text
    text = text.replace("Canonical source: skills/build-phase/providers/claude.md",
                         "Canonical source: skills/build-phase/providers/NOPE.md")
    skill_md.write_text(text, encoding="utf-8")
    defects = release_checks.wrapper_core_reference_defects(dist, REPO_ROOT)
    assert any("NOPE.md" in d for d in defects)


@pwsh_skip
def test_wrapper_core_reference_reds_on_missing_core_sibling(built_dist, tmp_path):
    dist = _copy_dist(built_dist, tmp_path / "dist")
    core_md = dist / "claude" / "build-phase" / "core.md"
    assert core_md.is_file()
    core_md.unlink()
    defects = release_checks.wrapper_core_reference_defects(dist, REPO_ROOT)
    assert any("build-phase" in d and "core.md" in d for d in defects)


# --------------------------------------------------------------------------- #
# 5. SKILL-COUNT
# --------------------------------------------------------------------------- #

def test_skill_count_matches_manifest_on_real_readme():
    defects = release_checks.readme_skill_count_defects(load_readme(), load_manifest())
    assert not defects, defects


def test_skill_count_reds_on_mismatched_count():
    manifest = {"counts": {"portable": 47}}
    text = "- 46/46 skills are GPT-capable; 37 calibration tests pass.\n"
    defects = release_checks.readme_skill_count_defects(text, manifest)
    assert defects


def test_skill_count_reds_on_missing_status_line():
    manifest = {"counts": {"portable": 47}}
    defects = release_checks.readme_skill_count_defects("no status line in this doc", manifest)
    assert defects


# --------------------------------------------------------------------------- #
# 6. README-CLAIM
# --------------------------------------------------------------------------- #

def test_readme_claims_supported_by_real_manifest():
    # repo_root supplied: exercises the full canonical-shape check (manifest path
    # match + on-disk existence), not just the name-only legacy check -- the real
    # README's skill links are all in the new `skills/<name>/...` shape (Step 39).
    defects = release_checks.readme_claim_defects(load_readme(), load_manifest(), REPO_ROOT)
    assert not defects, defects


def test_readme_claim_reds_on_unsupported_skill_link():
    """Legacy shape (`name/SKILL.md`): an unknown skill name is still caught."""
    manifest = {"skills": [{"name": "plan-review"}]}
    text = "[fake-skill](fake-skill/SKILL.md)\n"
    defects = release_checks.readme_claim_defects(text, manifest)
    assert defects and "fake-skill" in defects[0]


def test_readme_claim_clean_when_referenced_skill_is_real():
    """Legacy shape (`name/SKILL.md`): a real skill name stays clean."""
    manifest = {"skills": [{"name": "plan-review"}]}
    text = "[plan-review](plan-review/SKILL.md)\n"
    defects = release_checks.readme_claim_defects(text, manifest)
    assert not defects


def _new_shape_manifest():
    return {
        "skills": [
            {
                "name": "plan-review",
                "core": "skills/plan-review/core.md",
                "providers": {
                    "claude": "skills/plan-review/providers/claude.md",
                    "gpt": "skills/plan-review/providers/gpt.md",
                },
            },
            {
                "name": "context-slim",
                "core": None,
                "providers": {"claude": "skills/context-slim/providers/claude.md"},
            },
        ]
    }


def test_readme_claim_reds_on_unsupported_new_shape_skill_link():
    """Regression guard: Step 39 rewrote every README self-link from the legacy
    `name/SKILL.md` shape to `skills/name/core.md` / `skills/name/providers/
    claude.md`. The old regex only matched the legacy shape, so after the
    rewrite this gate matched ZERO candidates and passed trivially -- a planted
    defect in the NEW shape must still go red."""
    manifest = _new_shape_manifest()
    text = "[bogus-skill](skills/bogus-skill/core.md)\n"
    defects = release_checks.readme_claim_defects(text, manifest)
    assert defects and "bogus-skill" in defects[0]


def test_readme_claim_clean_when_new_shape_core_link_is_real():
    manifest = _new_shape_manifest()
    text = "[plan-review](skills/plan-review/core.md)\n"
    defects = release_checks.readme_claim_defects(text, manifest)
    assert not defects


def test_readme_claim_clean_when_new_shape_provider_native_link_is_real():
    manifest = _new_shape_manifest()
    text = "[context-slim](skills/context-slim/providers/claude.md)\n"
    defects = release_checks.readme_claim_defects(text, manifest)
    assert not defects


def test_readme_claim_reds_on_new_shape_core_link_for_provider_native_skill():
    """A core.md link for a skill the manifest marks provider-native (core: null)
    is a defect even though the skill NAME is real."""
    manifest = _new_shape_manifest()
    text = "[context-slim](skills/context-slim/core.md)\n"
    defects = release_checks.readme_claim_defects(text, manifest)
    assert defects and "context-slim" in defects[0]


def test_readme_claim_reds_on_new_shape_link_when_target_missing_on_disk(tmp_path):
    """With repo_root supplied, a syntactically-correct new-shape link to a real
    manifest entry still reds if the declared file does not actually exist."""
    manifest = _new_shape_manifest()
    text = "[plan-review](skills/plan-review/core.md)\n"
    defects = release_checks.readme_claim_defects(text, manifest, tmp_path)
    assert defects and "plan-review" in defects[0]


# --------------------------------------------------------------------------- #
# 7. NO TRACKED GENERATED DISTRIBUTION
# --------------------------------------------------------------------------- #

def _no_tracked_dist_target():
    """The git checkout to check for a tracked dist/ path. tools/release.ps1's
    CHECK phase sets SKILL_MESH_SOURCE_ROOT to the SOURCE repository (which
    still has '.git' -- release.ps1 stages ONLY git-tracked files, so the
    staged tree this suite is otherwise running from during a release never
    has one) precisely so this check genuinely RUNS during a real release
    instead of self-skipping. Falls back to REPO_ROOT for a normal
    `pytest tests/package-integrity` invocation outside release.ps1."""
    env_root = os.environ.get("SKILL_MESH_SOURCE_ROOT")
    return Path(env_root) if env_root else REPO_ROOT


@git_skip
def test_no_tracked_dist_on_real_repo():
    target = _no_tracked_dist_target()
    if not (target / ".git").exists():
        pytest.skip(f"{target} is not a git checkout (e.g. a release-staged tree "
                    "with no SKILL_MESH_SOURCE_ROOT override)")
    r = subprocess.run(["git", "-C", str(target), "ls-files"],
                        capture_output=True, text=True, check=True)
    defects = release_checks.tracked_dist_defects(r.stdout.splitlines())
    assert not defects, defects


@git_skip
def test_no_tracked_dist_reds_on_planted_tracked_dist_file(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)
    (repo / "dist" / "claude").mkdir(parents=True)
    (repo / "dist" / "claude" / "SKILL.md").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    r = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True, check=True)
    defects = release_checks.tracked_dist_defects(r.stdout.splitlines())
    assert defects
    assert any("dist/claude/SKILL.md" in d.replace("\\", "/") for d in defects)


def _all_tests():
    return [v for k, v in sorted(globals().items())
            if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    passed = skipped = 0
    for fn in _all_tests():
        try:
            fn()
            passed += 1
            print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            if e.__class__.__name__ == "Skipped":
                skipped += 1
                print(f"SKIP {fn.__name__}: {e}")
            else:
                raise
    print(f"\n{passed} checks passed, {skipped} skipped")
