"""Behavioral gate for the lesson-observation helper (Phase LH Step 153).

What this grades, and why it is behavioral:
`_shared/lesson_observations.py` is a PRODUCER/CONSUMER pair: the skill's record mode
writes private records, and a later harvest reads them back at unchanged Git HEAD.
The defect class that costs the most here is not a wrong return value inside one
function -- it is drift between what the writer persisted and what the reader will
accept, which a mocked unit test cannot see (CLAUDE.md, "grep all downstream
consumers"). So every test below drives the REAL CLI in a subprocess, against a REAL
temporary Git repository, and asserts on real files on disk and real exit codes.

Nothing here contacts a network, opens a pull request, or touches this repository's
own Git metadata: every fixture repository is created under pytest's `tmp_path`.

The exit-code contract under test is the plan's: 0 for a completed operation
(INCLUDING a replay and INCLUDING an empty page), 2 for invalid input, repository or
state, and 3 for conflicting content or a failed publication.
"""

import errno
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
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
EXIT_INVALID = 2
EXIT_CONFLICT = 3

STATE_PARTS = ("lesson-harvest",)
OBSERVATIONS_PARTS = ("lesson-harvest", "observations")
RECEIPTS_PARTS = ("lesson-harvest", "receipts")


# --------------------------------------------------------------------------- #
# Fixtures and drivers
# --------------------------------------------------------------------------- #

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


def error_code(result, expected_exit):
    assert result.returncode == expected_exit, (
        f"expected exit {expected_exit}, got {result.returncode}: "
        f"{result.stdout}{result.stderr}")
    assert result.stdout.strip() == "", (
        "a refusal must not print a success receipt on stdout")
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert set(payload) <= {"code", "message", "observation_id"}, payload
    return payload["code"]


@pytest.fixture
def unborn_repo(tmp_path):
    """A real Git working tree with NO commits: HEAD is unborn."""
    repo = tmp_path / "unborn"
    repo.mkdir()
    _git(repo, "init", "-q", ".")
    return repo


@pytest.fixture
def repo(tmp_path):
    """A real Git working tree with one commit, so HEAD resolves."""
    repo = tmp_path / "project"
    repo.mkdir()
    _git(repo, "init", "-q", ".")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "-c", "user.email=fixture@example.invalid", "-c", "user.name=fixture",
         "-c", "commit.gpgsign=false", "commit", "-q", "-m", "fixture commit")
    return repo


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

    Session-scoped: one build serves every consumer of the generated file.
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


def new_id():
    result = run_helper("new-id")
    assert result.returncode == EXIT_OK, result.stderr
    return result.stdout.strip()


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


def completion_request(observation_id, **overrides):
    request = {
        "observation_id": observation_id,
        "classification": "instruction-gap",
        "disposition": "rejected",
        "evidence_refs": ["tool result 12"],
        "candidate_ref": None,
    }
    request.update(overrides)
    return request


def write_request(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def record(repo, tmp_path, request, name=None):
    request_file = tmp_path / (name or (request["observation_id"] + ".request.json"))
    write_request(request_file, request)
    return run_helper("record", "--repo", repo, "--input", request_file)


def record_ok(repo, tmp_path, request, name=None):
    return ok_json(record(repo, tmp_path, request, name))


def pending(repo, *args):
    return run_helper("pending", "--repo", repo, *args)


def pending_ok(repo, *args):
    return ok_json(pending(repo, *args))


def complete(repo, tmp_path, request, name=None):
    request_file = tmp_path / (
        name or (request["observation_id"] + ".completion.json"))
    write_request(request_file, request)
    return run_helper("complete", "--repo", repo, "--input", request_file)


def state_dir(repo, *parts):
    return repo.joinpath(".git", *parts)


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


def diagnostic_codes(page):
    return [entry["code"] for entry in page["diagnostics"]]


# --------------------------------------------------------------------------- #
# new-id
# --------------------------------------------------------------------------- #

def test_new_id_prints_one_distinct_lowercase_uuid4_without_touching_a_repository(
        tmp_path):
    """`new-id` is the id SOURCE, so a model never invents one by hand.

    It must also be usable before any repository is chosen: it takes no `--repo`,
    reads nothing, and writes nothing.
    """
    pattern = re.compile(
        r"\A[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
    before = snapshot(tmp_path)
    minted = set()
    for _ in range(5):
        result = run_helper("new-id", cwd=tmp_path)
        assert result.returncode == EXIT_OK, result.stderr
        value = result.stdout.strip()
        assert pattern.match(value), value
        minted.add(value)
    assert len(minted) == 5, "new-id must mint a distinct id per call"
    assert snapshot(tmp_path) == before, "new-id wrote to the filesystem"


# --------------------------------------------------------------------------- #
# record: publication, replay, conflict
# --------------------------------------------------------------------------- #

def test_record_publishes_one_immutable_observation_outside_versioned_content(
        repo, tmp_path):
    identifier = new_id()
    receipt = record_ok(repo, tmp_path, observation_request(identifier))
    assert set(receipt) == {"schema", "observation_id", "status", "path"}
    assert receipt["schema"] == "lesson-capture-receipt-v1"
    assert receipt["status"] == "recorded"
    assert receipt["observation_id"] == identifier

    saved = state_dir(repo, *OBSERVATIONS_PARTS) / (identifier + ".md")
    assert saved.is_file(), "the observation was not published where it was claimed"
    assert Path(receipt["path"]).resolve() == saved.resolve()
    text = saved.read_text(encoding="utf-8")
    assert text.startswith("# Lesson observation\n"), text[:60]

    # The record lives in Git METADATA, so it is invisible to versioned content and
    # needs no ignore rule in the target project.
    assert _git(repo, "status", "--porcelain") == "", (
        "the capture changed the target repository's working tree")

    envelope = json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])
    assert envelope["schema"] == "lesson-observation-v1"
    assert envelope["observation_id"] == identifier
    assert envelope["repo_root"]
    assert envelope["recorded_at"].endswith("Z")
    # No temporary file survives a successful publication.
    assert not [p for p in saved.parent.iterdir() if p.name.endswith(".tmp")]


def test_replaying_an_identical_request_is_idempotent_and_changes_no_byte(
        repo, tmp_path):
    """The retry path: same id, same content, exit 0, and the saved bytes stand."""
    identifier = new_id()
    request = observation_request(identifier)
    first = record_ok(repo, tmp_path, request)
    saved = state_dir(repo, *OBSERVATIONS_PARTS) / (identifier + ".md")
    original = saved.read_bytes()

    second = record_ok(repo, tmp_path, request)
    assert first["status"] == "recorded"
    assert second["status"] == "replayed"
    assert saved.read_bytes() == original, (
        "a replay rewrote the immutable observation")
    assert len(list(saved.parent.iterdir())) == 1


def test_same_id_with_different_content_is_a_conflict_and_never_overwrites(
        repo, tmp_path):
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    saved = state_dir(repo, *OBSERVATIONS_PARTS) / (identifier + ".md")
    original = saved.read_bytes()

    divergent = observation_request(
        identifier, observed_error="a different observed error entirely")
    result = record(repo, tmp_path, divergent, name="divergent.json")
    assert error_code(result, EXIT_CONFLICT) == "observation-conflict"
    assert saved.read_bytes() == original, "a conflict overwrote history"
    assert "a different observed error entirely" not in result.stderr, (
        "the refusal echoed saved or submitted narrative content")


def test_record_refuses_to_publish_over_unreadable_bytes_at_its_destination(
        repo, tmp_path):
    """A partially published or corrupted destination is exit 3, never an overwrite."""
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    saved = state_dir(repo, *OBSERVATIONS_PARTS) / (identifier + ".md")
    saved.write_text("# Lesson observation\n\nno fence here at all\n",
                     encoding="utf-8")
    damaged = saved.read_bytes()

    result = record(repo, tmp_path, observation_request(identifier),
                    name="retry.json")
    assert result.returncode == EXIT_CONFLICT, result.stderr
    assert saved.read_bytes() == damaged, "the damaged record was overwritten"


def test_a_backtick_bearing_evidence_locator_round_trips_through_the_fence(
        repo, tmp_path):
    """The saved document is markdown; a narrative fence must not escape it."""
    identifier = new_id()
    hostile = "run ``` then `git show` -- a fence inside the locator"
    request = observation_request(identifier, evidence=[hostile])
    record_ok(repo, tmp_path, request)

    page = pending_ok(repo)
    assert observed_ids(page) == [identifier]
    assert page["observations"][0]["evidence"] == [hostile]
    saved = (state_dir(repo, *OBSERVATIONS_PARTS) / (identifier + ".md")).read_text(
        encoding="utf-8")
    assert saved.count("```") == 2, "the narrative broke out of its own fence"


# --------------------------------------------------------------------------- #
# Corrections
# --------------------------------------------------------------------------- #

def test_a_correction_makes_the_original_historical_and_keeps_the_replacement(
        repo, tmp_path):
    """Correction BEFORE classification: the original is never a candidate source."""
    original = new_id()
    record_ok(repo, tmp_path, observation_request(original))
    replacement = new_id()
    record_ok(repo, tmp_path, observation_request(
        replacement, observed_error="the real observed error, corrected",
        supersedes=original))

    page = pending_ok(repo)
    assert observed_ids(page) == [replacement], (
        "the superseded original is still offered as a candidate source")
    superseded = [d for d in page["diagnostics"]
                  if d["code"] == "observation-superseded"]
    assert len(superseded) == 1
    assert superseded[0]["observation_id"] == original
    assert superseded[0]["related_observation_ids"] == [replacement]
    # Both records survive: a correction adds, it never edits or deletes.
    assert (state_dir(repo, *OBSERVATIONS_PARTS) / (original + ".md")).is_file()


def test_a_correction_outside_the_current_page_still_hides_its_original(
        repo, tmp_path):
    """Bounded paging must not be able to hide a correction relationship."""
    original = new_id()
    record_ok(repo, tmp_path, observation_request(original))
    replacement = new_id()
    record_ok(repo, tmp_path, observation_request(
        replacement, observed_error="corrected", supersedes=original))

    page = pending_ok(repo, "--limit", 1)
    assert page["remaining"] == 1, page
    assert observed_ids(page) == [], (
        "the original was offered even though its correction is off-page")
    assert "observation-superseded" in diagnostic_codes(page)


def test_conflicting_corrections_are_reported_and_left_undecided(repo, tmp_path):
    """Two corrective branches are never resolved by newest timestamp."""
    original = new_id()
    record_ok(repo, tmp_path, observation_request(original))
    first = new_id()
    record_ok(repo, tmp_path, observation_request(
        first, observed_error="branch one", supersedes=original))
    second = new_id()
    record_ok(repo, tmp_path, observation_request(
        second, observed_error="branch two", supersedes=original))

    page = pending_ok(repo)
    assert observed_ids(page) == [], (
        "a conflicting corrective branch produced a candidate source anyway")
    conflicts = [d for d in page["diagnostics"] if d["code"] == "correction-conflict"]
    assert conflicts, page["diagnostics"]
    reported = set()
    for entry in conflicts:
        reported.update(entry["related_observation_ids"])
    assert reported == {first, second}


def test_supersedes_must_name_an_existing_observation_in_this_inbox(repo, tmp_path):
    stranger = new_id()
    result = record(repo, tmp_path, observation_request(
        new_id(), supersedes=stranger))
    assert error_code(result, EXIT_INVALID) == "supersedes-not-found"


def test_supersedes_may_not_name_the_record_itself(repo, tmp_path):
    identifier = new_id()
    result = record(repo, tmp_path, observation_request(
        identifier, supersedes=identifier))
    assert error_code(result, EXIT_INVALID) == "supersedes-self"


# --------------------------------------------------------------------------- #
# pending: read-only, bounded, stateless
# --------------------------------------------------------------------------- #

def test_pending_is_read_only_and_creates_no_private_state(repo):
    """The preview path writes NOTHING -- not even the inbox directories.

    This is the helper-level half of the skill's one dry-run rule: a preview that
    quietly created its own state would make "creates nothing" untrue at the only
    layer that can be measured.
    """
    before = snapshot(repo / ".git")
    page = pending_ok(repo)
    assert page["observations"] == []
    assert page["remaining"] == 0
    assert page["next_after"] is None
    assert not state_dir(repo, *STATE_PARTS).exists(), (
        "a read command created the private inbox")
    assert snapshot(repo / ".git") == before, "a read command mutated private state"


def test_pending_on_a_populated_inbox_mutates_nothing(repo, tmp_path):
    for _ in range(3):
        record_ok(repo, tmp_path, observation_request(new_id()))
    before = snapshot(state_dir(repo, *STATE_PARTS))
    assert before, "the fixture published nothing"
    for _ in range(2):
        pending_ok(repo)
    assert snapshot(state_dir(repo, *STATE_PARTS)) == before


def test_pending_reports_observations_at_unchanged_head(repo, tmp_path):
    """The whole point of the slice: HEAD has not moved and there is still work."""
    head_before = _git(repo, "rev-parse", "HEAD")
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    assert _git(repo, "rev-parse", "HEAD") == head_before

    page = pending_ok(repo)
    assert page["schema"] == "lesson-pending-v1"
    assert set(page) == {
        "schema", "observations", "diagnostics", "remaining", "next_after"}
    assert observed_ids(page) == [identifier]


def test_record_and_pending_work_with_an_unborn_head(unborn_repo, tmp_path):
    """A young repository with no commits still captures and still reports."""
    assert subprocess.run([GIT, "rev-parse", "HEAD"], cwd=str(unborn_repo),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).returncode != 0, (
        "the fixture repository unexpectedly has a resolvable HEAD")
    identifier = new_id()
    record_ok(unborn_repo, tmp_path, observation_request(identifier))
    page = pending_ok(unborn_repo)
    assert observed_ids(page) == [identifier]


def test_pagination_is_stateless_and_reaches_past_retained_items(repo, tmp_path):
    """`--after` walks the WHOLE inbox, one bounded page at a time.

    The ordering is taken from the helper's own full page rather than from creation
    order, so the test grades the cursor contract instead of re-deriving the sort.
    """
    for _ in range(5):
        record_ok(repo, tmp_path, observation_request(new_id()))
    order = observed_ids(pending_ok(repo, "--limit", 50))
    assert len(order) == 5

    walked, cursor, pages = [], None, 0
    while True:
        args = ["--limit", 2]
        if cursor is not None:
            args += ["--after", cursor]
        page = pending_ok(repo, *args)
        pages += 1
        walked += observed_ids(page)
        cursor = page["next_after"]
        if cursor is None:
            assert page["remaining"] == 0
            break
        assert pages < 10, "the cursor walk did not terminate"
    assert walked == order, "a stateless walk did not reach every observation"


def test_a_completed_observation_consumes_its_page_slot_but_not_a_candidate(
        repo, tmp_path):
    """A retained, already-dispositioned record must not starve later entries."""
    for _ in range(3):
        record_ok(repo, tmp_path, observation_request(new_id()))
    order = observed_ids(pending_ok(repo, "--limit", 50))
    first = order[0]
    assert ok_json(complete(repo, tmp_path, completion_request(first)))["status"] \
        == "recorded"

    page = pending_ok(repo, "--limit", 1)
    assert observed_ids(page) == [], "a completed observation was offered again"
    assert "observation-completed" in diagnostic_codes(page)
    assert page["next_after"] == first, (
        "the cursor must advance across a completed observation")

    nxt = pending_ok(repo, "--limit", 2, "--after", first)
    assert observed_ids(nxt) == order[1:], (
        "later observations were starved by a retained completed record")


def test_the_cursor_may_name_an_observation_that_already_has_a_receipt(
        repo, tmp_path):
    for _ in range(2):
        record_ok(repo, tmp_path, observation_request(new_id()))
    order = observed_ids(pending_ok(repo, "--limit", 50))
    complete(repo, tmp_path, completion_request(order[0]))
    page = pending_ok(repo, "--after", order[0])
    assert observed_ids(page) == [order[1]]


def test_an_unknown_cursor_is_an_error_not_a_silent_restart(repo, tmp_path):
    record_ok(repo, tmp_path, observation_request(new_id()))
    result = pending(repo, "--after", new_id())
    assert error_code(result, EXIT_INVALID) == "unknown-cursor"

    malformed = pending(repo, "--after", "not-a-uuid")
    assert error_code(malformed, EXIT_INVALID) == "invalid-cursor"


@pytest.mark.parametrize("limit", ["0", "51", "-3"])
def test_page_limit_is_bounded(repo, limit):
    result = pending(repo, "--limit", limit)
    assert error_code(result, EXIT_INVALID) == "invalid-limit"


def test_a_malformed_saved_observation_is_reported_without_advancing_the_cursor(
        repo, tmp_path):
    """One unreadable file must not hide every later observation behind it."""
    for _ in range(3):
        record_ok(repo, tmp_path, observation_request(new_id()))
    order = observed_ids(pending_ok(repo, "--limit", 50))
    damaged = order[1]
    (state_dir(repo, *OBSERVATIONS_PARTS) / (damaged + ".md")).write_text(
        "# Lesson observation\n\nthis is no longer an envelope\n", encoding="utf-8")

    page = pending_ok(repo, "--limit", 50)
    assert observed_ids(page) == [order[0], order[2]]
    malformed = [d for d in page["diagnostics"]
                 if d["code"] == "observation-malformed"]
    assert len(malformed) == 1 and malformed[0]["observation_id"] == damaged
    # It is not in the ordering, so it can neither BE a cursor...
    assert error_code(pending(repo, "--after", damaged), EXIT_INVALID) == \
        "unknown-cursor"
    # ...nor consume the slot that would hide the record after it.
    assert observed_ids(pending_ok(repo, "--limit", 1, "--after", order[0])) == \
        [order[2]]
    # The file is left exactly where it was; a reader never repairs or deletes.
    assert (state_dir(repo, *OBSERVATIONS_PARTS) / (damaged + ".md")).is_file()


def test_an_abandoned_temporary_file_is_reported_and_ignored(repo, tmp_path):
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    abandoned = state_dir(repo, *OBSERVATIONS_PARTS) / (identifier + ".md.abc.tmp")
    abandoned.write_text("partial", encoding="utf-8")

    page = pending_ok(repo)
    assert observed_ids(page) == [identifier]
    assert "abandoned-temporary-file" in diagnostic_codes(page)
    assert abandoned.is_file(), "a reader deleted an abandoned temporary file"


# --------------------------------------------------------------------------- #
# complete: dispositions
# --------------------------------------------------------------------------- #

def test_complete_persists_one_immutable_receipt_and_replays(repo, tmp_path):
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    request = completion_request(
        identifier, classification="unsupported", disposition="rejected")

    first = ok_json(complete(repo, tmp_path, request))
    assert set(first) == {"schema", "observation_id", "status"}
    assert first["schema"] == "lesson-completion-receipt-v1"
    assert first["status"] == "recorded"
    receipt = state_dir(repo, *RECEIPTS_PARTS) / (identifier + ".json")
    saved = receipt.read_bytes()
    envelope = json.loads(saved.decode("utf-8"))
    assert envelope["schema"] == "lesson-disposition-v1"
    assert envelope["classification"] == "unsupported"

    second = ok_json(complete(repo, tmp_path, request, name="replay.json"))
    assert second["status"] == "replayed"
    assert receipt.read_bytes() == saved


def test_a_conflicting_final_disposition_never_overwrites_the_historical_receipt(
        repo, tmp_path):
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    complete(repo, tmp_path, completion_request(identifier))
    receipt = state_dir(repo, *RECEIPTS_PARTS) / (identifier + ".json")
    original = receipt.read_bytes()

    result = complete(repo, tmp_path, completion_request(
        identifier, disposition="already-codified"), name="second.json")
    assert error_code(result, EXIT_CONFLICT) == "disposition-conflict"
    assert receipt.read_bytes() == original


def test_complete_requires_an_observation_that_exists_here(repo, tmp_path):
    result = complete(repo, tmp_path, completion_request(new_id()))
    assert error_code(result, EXIT_INVALID) == "observation-not-found"
    assert not state_dir(repo, *RECEIPTS_PARTS).exists() or not list(
        state_dir(repo, *RECEIPTS_PARTS).iterdir())


@pytest.mark.parametrize("candidate_ref", [
    "http://github.com/owner/repo/pull/7",          # not HTTPS
    "https://github.com/owner/repo/pulls/7",        # not the pull-request path
    "https://example.invalid/owner/repo/pull/7",    # not the expected host
    "https://github.com/owner/repo/pull/7/files",   # trailing path
    "https://github.com/owner/repo/pull/abc",       # no number
    "https://github.com/owner/repo/issues/7",       # an issue, not a pull request
])
def test_candidate_ref_shape_is_validated_for_a_prepared_candidate(
        repo, tmp_path, candidate_ref):
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    result = complete(repo, tmp_path, completion_request(
        identifier, disposition="candidate-prepared", candidate_ref=candidate_ref),
        name="bad-ref.json")
    assert error_code(result, EXIT_INVALID) == "candidate-ref-shape"


def test_a_well_shaped_candidate_ref_is_accepted_without_any_network_call(
        repo, tmp_path):
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    receipt = ok_json(complete(repo, tmp_path, completion_request(
        identifier, disposition="candidate-prepared",
        candidate_ref="https://github.com/owner/repo/pull/7")))
    assert receipt["status"] == "recorded"


def test_a_candidate_ref_is_required_and_forbidden_by_disposition(repo, tmp_path):
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    missing = complete(repo, tmp_path, completion_request(
        identifier, disposition="candidate-prepared"), name="missing-ref.json")
    assert error_code(missing, EXIT_INVALID) == "candidate-ref-required"

    unexpected = complete(repo, tmp_path, completion_request(
        identifier, disposition="rejected",
        candidate_ref="https://github.com/owner/repo/pull/7"),
        name="extra-ref.json")
    assert error_code(unexpected, EXIT_INVALID) == "candidate-ref-unexpected"


@pytest.mark.parametrize("field,value", [
    ("classification", "made-up"),
    ("disposition", "merged"),
])
def test_completion_enums_are_closed(repo, tmp_path, field, value):
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    result = complete(repo, tmp_path, completion_request(
        identifier, **{field: value}), name="enum.json")
    assert error_code(result, EXIT_INVALID) == "field-enum"


# --------------------------------------------------------------------------- #
# Input rejection
# --------------------------------------------------------------------------- #

def test_an_unknown_key_is_rejected_rather_than_ignored(repo, tmp_path):
    request = observation_request(new_id())
    request["priority"] = "high"
    assert error_code(record(repo, tmp_path, request), EXIT_INVALID) == "unknown-field"


def test_a_missing_field_is_rejected(repo, tmp_path):
    request = observation_request(new_id())
    del request["correction"]
    assert error_code(record(repo, tmp_path, request), EXIT_INVALID) == "missing-field"


def test_an_oversized_request_file_is_rejected_before_any_parse(repo, tmp_path):
    request = observation_request(new_id(), correction="x" * 20000)
    result = record(repo, tmp_path, request, name="huge.json")
    assert error_code(result, EXIT_INVALID) == "input-too-large"
    assert not state_dir(repo, *STATE_PARTS).exists()


def test_an_over_long_field_inside_a_small_file_is_rejected(repo, tmp_path):
    request = observation_request(new_id(), observed_error="x" * 2001)
    assert error_code(record(repo, tmp_path, request), EXIT_INVALID) == \
        "field-too-long"


@pytest.mark.parametrize("payload", ["not json at all", "[1, 2, 3]", "\"a string\""])
def test_a_request_that_is_not_one_json_object_is_rejected(repo, tmp_path, payload):
    request_file = tmp_path / "bad.json"
    request_file.write_text(payload, encoding="utf-8")
    result = run_helper("record", "--repo", repo, "--input", request_file)
    assert error_code(result, EXIT_INVALID) in {"input-not-json", "input-not-object"}


def test_a_missing_request_file_is_rejected(repo, tmp_path):
    result = run_helper("record", "--repo", repo, "--input", tmp_path / "absent.json")
    assert error_code(result, EXIT_INVALID) == "input-unreadable"


@pytest.mark.parametrize("hostile", ["bell \x07 here", "carriage \r return",
                                     "null \x00 byte"])
def test_control_characters_in_a_narrative_string_are_rejected(
        repo, tmp_path, hostile):
    """Tab and line feed are the only control characters a narrative may carry."""
    request = observation_request(new_id(), observed_error=hostile)
    assert error_code(record(repo, tmp_path, request), EXIT_INVALID) == \
        "field-control-characters"


def test_tab_and_line_feed_remain_acceptable(repo, tmp_path):
    identifier = new_id()
    text = "first line\n\tindented second line"
    record_ok(repo, tmp_path, observation_request(identifier, correction=text))
    page = pending_ok(repo)
    assert page["observations"][0]["correction"] == text


@pytest.mark.parametrize("evidence", [[], ["a", "b", "c", "d", "e", "f"]])
def test_evidence_cardinality_is_bounded(repo, tmp_path, evidence):
    request = observation_request(new_id(), evidence=evidence)
    assert error_code(record(repo, tmp_path, request), EXIT_INVALID) == \
        "field-cardinality"


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_a_blank_narrative_is_rejected(repo, tmp_path, blank):
    request = observation_request(new_id(), correction=blank)
    assert error_code(record(repo, tmp_path, request), EXIT_INVALID) == "field-blank"


@pytest.mark.parametrize("identifier", [
    "00000000-0000-0000-0000-000000000000",   # not version 4
    "1A2B3C4D-5E6F-4A8B-9C0D-1E2F3A4B5C6D",   # not lowercase
    "short",
])
def test_a_hand_invented_observation_id_is_rejected(repo, tmp_path, identifier):
    request = observation_request(identifier)
    result = record(repo, tmp_path, request, name="invented.json")
    assert error_code(result, EXIT_INVALID) == "field-shape"


# --------------------------------------------------------------------------- #
# Repository and state-path refusals
# --------------------------------------------------------------------------- #

def test_a_path_outside_any_git_working_tree_is_refused(tmp_path):
    """`tmp_path` is not a Git working tree, so every command must refuse it."""
    outside = tmp_path / "plain"
    outside.mkdir()
    assert error_code(pending(outside), EXIT_INVALID) == "not-a-git-working-tree"


def test_a_missing_repository_path_is_refused(tmp_path):
    assert error_code(pending(tmp_path / "absent"), EXIT_INVALID) == \
        "repository-not-found"


def test_a_bare_repository_is_refused(tmp_path):
    """A bare repository has no working tree for an observation to belong to."""
    bare = tmp_path / "bare.git"
    bare.mkdir()
    _git(bare, "init", "-q", "--bare", ".")
    assert error_code(pending(bare), EXIT_INVALID) == "bare-repository"
    assert error_code(record(bare, tmp_path, observation_request(new_id())),
                      EXIT_INVALID) == "bare-repository"


def _make_reparse_point(link, target):
    """Create a directory reparse point at `link`, or return the reason it failed.

    A symlink is the POSIX form and needs a privilege Windows does not grant an
    ordinary account, so this repository's own floor would SKIP the refusal gate --
    and a skipped gate is a false green on the one machine nobody checked. A Windows
    directory JUNCTION is the same reparse-point class, carries the same danger (the
    inbox silently resolving somewhere else), and needs no elevation, so it is the
    fallback rather than a skip.
    """
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
        return None
    except (OSError, NotImplementedError, AttributeError) as exc:
        first = str(exc)
    if os.name != "nt":
        return first
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0 and os.path.exists(str(link)):
        return None
    return f"{first}; junction fallback: {result.stdout}{result.stderr}"


def test_a_symlinked_state_path_is_refused_before_it_is_opened(repo, tmp_path):
    """A reparse point at the inbox would publish private records somewhere else."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    link = state_dir(repo, *STATE_PARTS)
    failure = _make_reparse_point(link, elsewhere)
    if failure is not None:
        pytest.skip(f"this platform refused every reparse-point fixture: {failure}")

    result = record(repo, tmp_path, observation_request(new_id()))
    assert error_code(result, EXIT_INVALID) == "state-path-is-a-reparse-point"
    assert snapshot(elsewhere) == {}, "a record was written through a reparse point"
    assert error_code(pending(repo), EXIT_INVALID) == \
        "state-path-is-a-reparse-point"


def test_a_linked_worktree_shares_one_repository_inbox(repo, tmp_path):
    """LH-D2: linked worktrees share the COMMON Git directory, so records are one set."""
    linked = tmp_path / "linked"
    _git(repo, "worktree", "add", "-q", "-b", "lh-fixture", str(linked))
    try:
        identifier = new_id()
        record_ok(linked, tmp_path, observation_request(identifier))
        # Published into the MAIN repository's metadata, not the linked worktree's.
        assert (state_dir(repo, *OBSERVATIONS_PARTS) / (identifier + ".md")).is_file()
        assert observed_ids(pending_ok(repo)) == [identifier]
        assert observed_ids(pending_ok(linked)) == [identifier]
    finally:
        subprocess.run([GIT, "worktree", "remove", "--force", str(linked)],
                       cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# --------------------------------------------------------------------------- #
# Producer / consumer smoke through the shipped artifact
# --------------------------------------------------------------------------- #

def test_the_helper_drives_a_full_capture_cycle_in_a_temporary_git_repository(
        tmp_path):
    """One end-to-end cycle: mint, record, read back, correct, disposition, replay.

    Deliberately a single narrative test rather than six assertions spread across
    fixtures: the defect this slice is most exposed to is a writer and a reader that
    each pass their own test and disagree with each other.
    """
    project = tmp_path / "smoke"
    project.mkdir()
    _git(project, "init", "-q", ".")
    (project / "app.py").write_text("print('hi')\n", encoding="utf-8")
    _git(project, "add", "app.py")
    _git(project, "-c", "user.email=smoke@example.invalid", "-c", "user.name=smoke",
         "-c", "commit.gpgsign=false", "commit", "-q", "-m", "initial")
    head = _git(project, "rev-parse", "HEAD")

    requests = tmp_path / "requests"
    requests.mkdir()

    first = new_id()
    assert record_ok(project, requests, observation_request(
        first, observed_error="asserted the suite was green without running it",
        evidence=["assistant message 8", "tool result 9"]))["status"] == "recorded"

    page = pending_ok(project)
    assert observed_ids(page) == [first]
    assert page["observations"][0]["session"] == "manual-session"

    correction = new_id()
    record_ok(project, requests, observation_request(
        correction, observed_error="asserted a green suite from a stale run log",
        supersedes=first))
    page = pending_ok(project)
    assert observed_ids(page) == [correction]

    assert ok_json(complete(project, requests, completion_request(
        correction, classification="instruction-not-used",
        disposition="already-codified")))["status"] == "recorded"

    final = pending_ok(project)
    assert observed_ids(final) == []
    assert final["remaining"] == 0 and final["next_after"] is None

    # HEAD never moved and the working tree is untouched: the whole cycle lived in
    # private Git metadata.
    assert _git(project, "rev-parse", "HEAD") == head
    assert _git(project, "status", "--porcelain") == ""


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


# --------------------------------------------------------------------------- #
# Code points that are valid JSON and not valid UTF-8
# --------------------------------------------------------------------------- #

# A LONE UTF-16 surrogate. "\ud800" is a legal JSON escape, Python's json decoder
# does not require surrogate pairing, and the resulting str is not a control
# character -- so it clears the UTF-8 file decode, the JSON parse, and the
# control-character screen, and only fails at the .encode("utf-8") that renders the
# record. Written here as an escape rather than a literal so this source file stays
# encodable itself.
LONE_SURROGATE = "\ud800"

SURROGATE_OBSERVATION_FIELDS = ("session", "source", "observed_error", "correction")


def _write_raw_request(path, payload):
    """Serialize with ensure_ascii so the surrogate travels as a JSON escape.

    ensure_ascii=True emits the six-character escape, which makes the request file
    itself perfectly valid UTF-8 -- the whole point of the case. Writing the file
    with a plain encode would fail in the TEST instead of in the helper.
    """
    path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
    return path


def _assert_clean_refusal(result, code):
    """Exit 2, one parseable JSON diagnostic, and no traceback anywhere."""
    assert result.returncode == EXIT_INVALID, (
        f"expected exit {EXIT_INVALID}, got {result.returncode}: "
        f"{result.stdout}{result.stderr}")
    assert result.stdout.strip() == "", "a refusal must not print a receipt"
    assert "Traceback (most recent call last)" not in result.stderr, (
        f"a refusal leaked an interpreter traceback:\n{result.stderr}")
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert set(payload) <= {"code", "message", "observation_id"}, payload
    assert payload["code"] == code, payload
    return payload


@pytest.mark.parametrize("field", SURROGATE_OBSERVATION_FIELDS)
def test_a_lone_surrogate_in_a_recorded_field_is_a_refusal_not_a_traceback(
        repo, tmp_path, field):
    """LH-B1: valid JSON that Python cannot encode must refuse, never crash.

    Before this gate the value passed every check and blew up inside
    render_observation_document(...).encode("utf-8") -- an uncaught
    UnicodeEncodeError, exit 1 (outside the closed {0,2,3} contract), an interpreter
    traceback on stderr where a JSON diagnostic was promised, and the helper's
    absolute source path printed along with it.
    """
    identifier = new_id()
    request = observation_request(identifier, **{field: "before " + LONE_SURROGATE})
    request_file = _write_raw_request(tmp_path / "surrogate.json", request)
    result = run_helper("record", "--repo", repo, "--input", request_file)
    _assert_clean_refusal(result, "field-not-encodable")
    assert snapshot(state_dir(repo, *OBSERVATIONS_PARTS)) == {}, (
        "a record was published despite the refusal")


def test_a_lone_surrogate_in_a_recorded_evidence_locator_is_a_refusal(repo, tmp_path):
    """The list items are validated too -- evidence is caller-supplied free text."""
    identifier = new_id()
    request = observation_request(
        identifier, evidence=["tool result 12", "tool result " + LONE_SURROGATE])
    request_file = _write_raw_request(tmp_path / "surrogate-evidence.json", request)
    result = run_helper("record", "--repo", repo, "--input", request_file)
    _assert_clean_refusal(result, "field-not-encodable")
    assert snapshot(state_dir(repo, *OBSERVATIONS_PARTS)) == {}


def test_a_lone_surrogate_in_a_completion_field_is_a_refusal(repo, tmp_path):
    """The same class on the OTHER command: complete renders a record too."""
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    before = snapshot(state_dir(repo, *RECEIPTS_PARTS))
    request = completion_request(
        identifier, evidence_refs=["tool result " + LONE_SURROGATE])
    request_file = _write_raw_request(tmp_path / "surrogate-completion.json", request)
    result = run_helper("complete", "--repo", repo, "--input", request_file)
    payload = _assert_clean_refusal(result, "field-not-encodable")
    assert LONE_SURROGATE not in payload["message"], (
        "the diagnostic echoed the rejected value back at the caller")
    assert snapshot(state_dir(repo, *RECEIPTS_PARTS)) == before, (
        "a receipt was published despite the refusal")


def test_no_reachable_invocation_produces_an_out_of_contract_exit_code(repo, tmp_path):
    """The {0, 2, 3} contract holds across the refusals a caller can actually reach."""
    identifier = new_id()
    request_file = _write_raw_request(
        tmp_path / "surrogate-contract.json",
        observation_request(identifier, correction="x " + LONE_SURROGATE))
    invocations = [
        ("new-id",),
        ("pending", "--repo", repo),
        ("pending", "--repo", repo, "--limit", "notanumber"),
        ("pending", "--repo", repo, "--limit", "0"),
        ("pending",),
        ("record", "--repo", repo, "--input", request_file),
        ("nonesuch", "--repo", repo),
    ]
    for invocation in invocations:
        result = run_helper(*invocation)
        assert result.returncode in (EXIT_OK, EXIT_INVALID, EXIT_CONFLICT), (
            f"{invocation} exited {result.returncode}, outside the closed contract:\n"
            f"{result.stderr}")
        assert "Traceback (most recent call last)" not in result.stderr, (
            f"{invocation} leaked an interpreter traceback:\n{result.stderr}")


# --------------------------------------------------------------------------- #
# Argument-parsing refusals obey the same error contract
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("head, needs_repo", [
    (("pending", "--limit", "notanumber"), True),
    (("pending",), False),
    (("record",), True),
    (("nonesuch",), False),
])
def test_a_malformed_command_line_is_one_json_diagnostic_on_stderr(
        repo, head, needs_repo):
    """argparse refuses BEFORE main's body runs, and must still speak JSON.

    Stock ArgumentParser.error writes a bare usage/error pair and exits by itself.
    The exit code would be right by coincidence and the bytes wrong: a caller that
    json.loads(stderr) on a nonzero exit would crash on a typo and succeed on every
    other refusal.
    """
    args = list(head) + (["--repo", str(repo)] if needs_repo else [])
    result = run_helper(*args)
    assert result.returncode == EXIT_INVALID, result.stderr
    assert result.stdout.strip() == ""
    assert "usage:" not in result.stderr, (
        f"argparse printed its own usage text instead of a diagnostic:\n"
        f"{result.stderr}")
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload["code"] == "invalid-arguments", payload
    assert set(payload) <= {"code", "message", "observation_id"}, payload


def test_help_still_prints_usage_and_exits_zero():
    """The JSON error contract covers REFUSALS; --help is not one of them."""
    result = run_helper("--help")
    assert result.returncode == EXIT_OK, result.stderr
    assert "usage:" in result.stdout


# --------------------------------------------------------------------------- #
# Reparse points on an ANCESTOR of the path being opened
# --------------------------------------------------------------------------- #

def test_a_reparse_point_on_an_ancestor_directory_is_refused_on_every_command(
        repo, tmp_path):
    """os.lstat only declines to follow a link at the LAST path component.

    Guarding the leaf alone therefore inspects the REDIRECTED target's attributes
    and reports a perfectly ordinary file, while the open happens somewhere else
    entirely. The inbox root down to the leaf is one chain and the whole chain is
    the guard's subject; here the reparse point sits on the observations DIRECTORY,
    never on the record path any single call is about to open.
    """
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    observations = state_dir(repo, *OBSERVATIONS_PARTS)
    elsewhere = tmp_path / "redirected-observations"
    shutil.move(str(observations), str(elsewhere))
    failure = _make_reparse_point(observations, elsewhere)
    if failure is not None:
        pytest.skip(f"this platform refused every reparse-point fixture: {failure}")
    before = snapshot(elsewhere)

    assert error_code(pending(repo), EXIT_INVALID) == \
        "state-path-is-a-reparse-point"
    assert error_code(record(repo, tmp_path, observation_request(new_id())),
                      EXIT_INVALID) == "state-path-is-a-reparse-point"
    assert error_code(complete(repo, tmp_path, completion_request(identifier)),
                      EXIT_INVALID) == "state-path-is-a-reparse-point"
    assert snapshot(elsewhere) == before, (
        "the redirected directory was written through despite the refusal")


def test_a_dangling_reparse_point_in_the_inbox_is_refused_not_read_as_empty(
        repo, tmp_path):
    """A refusal reported as "nothing here yet" is the worst shape of this bug.

    os.path.isdir FOLLOWS links, so probing existence before inspecting the chain
    answers False for a reparse point whose target is gone -- and the reader then
    reports an EMPTY receipt set, i.e. every completed observation silently pending
    again. Inspecting the chain first turns that into the refusal it always was.
    """
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    assert ok_json(complete(repo, tmp_path, completion_request(identifier)))
    assert "observation-completed" in diagnostic_codes(pending_ok(repo))

    receipts = state_dir(repo, *RECEIPTS_PARTS)
    target = tmp_path / "removed-receipts"
    shutil.move(str(receipts), str(target))
    failure = _make_reparse_point(receipts, target)
    if failure is not None:
        pytest.skip(f"this platform refused every reparse-point fixture: {failure}")
    shutil.rmtree(str(target))

    assert error_code(pending(repo), EXIT_INVALID) == \
        "state-path-is-a-reparse-point"


def test_a_reparse_point_on_ONE_receipt_leaf_withholds_only_that_observation(
        repo, tmp_path):
    """A single poisoned receipt must not fail the whole `pending` command.

    The observation loader pre-checks each leaf itself, so one poisoned entry
    downgrades to a soft per-entry diagnostic and every later observation is still
    served. The receipt loader used to have no equivalent pre-check: it called
    _read_state_file directly, whose internal guard raises a bare LessonError --
    NOT a StateFileError -- so `except StateFileError` missed it and the bare error
    escaped cmd_pending, failing the ENTIRE page with exit 2. A merely malformed
    (non-reparse) receipt on the very same path is correctly withheld one entry at a
    time, so the two failure modes disagreed about the same class of problem.

    The existing reparse tests cover ancestor DIRECTORIES and a dangling inbox
    entry; none covers a reparse point on an individual receipt leaf.
    """
    poisoned = new_id()
    healthy = new_id()
    record_ok(repo, tmp_path, observation_request(poisoned))
    record_ok(repo, tmp_path, observation_request(healthy))
    assert ok_json(complete(repo, tmp_path, completion_request(poisoned)))

    receipt = state_dir(repo, *RECEIPTS_PARTS) / (poisoned + ".json")
    receipt.unlink()
    elsewhere = tmp_path / "receipt-target"
    elsewhere.mkdir()
    failure = _make_reparse_point(receipt, elsewhere)
    if failure is not None:
        pytest.skip(f"this platform refused every reparse-point fixture: {failure}")

    # The command still SUCCEEDS -- the regression was exit 2 for the whole page.
    page = pending_ok(repo)
    refusals = [d for d in page["diagnostics"]
                if d["code"] == "unexpected-inbox-entry"]
    assert [d.get("observation_id") for d in refusals] == [poisoned]
    # The poisoned id is withheld, and every OTHER observation is still served.
    assert observed_ids(page) == [healthy]


def test_a_malformed_receipt_leaf_withholds_only_that_observation(repo, tmp_path):
    """The parallel path the reparse pre-check above is made consistent with.

    A receipt whose bytes do not parse is already a per-entry withholding, not a
    failed command. Pinning it here makes the pair a matched set: the same class of
    problem -- one unreadable receipt leaf -- must produce the same shape of answer
    whichever way the leaf is unreadable.
    """
    poisoned = new_id()
    healthy = new_id()
    record_ok(repo, tmp_path, observation_request(poisoned))
    record_ok(repo, tmp_path, observation_request(healthy))
    assert ok_json(complete(repo, tmp_path, completion_request(poisoned)))

    receipt = state_dir(repo, *RECEIPTS_PARTS) / (poisoned + ".json")
    receipt.write_text("not a receipt envelope\n", encoding="utf-8")

    page = pending_ok(repo)
    withheld = [d for d in page["diagnostics"] if d["code"] == "receipt-malformed"]
    assert [d.get("observation_id") for d in withheld] == [poisoned]
    assert observed_ids(page) == [healthy]


# --------------------------------------------------------------------------- #
# Publication when the filesystem refuses hardlinks
# --------------------------------------------------------------------------- #

def _helper_module():
    """Import the helper as a module, to drive one primitive directly.

    Every other test here drives the real CLI in a subprocess, deliberately. This
    one cannot: the branch under test is reached only when os.link fails for a
    reason unrelated to the destination existing, which no request can arrange and
    no filesystem on this machine provides.
    """
    spec = importlib.util.spec_from_file_location(
        "lesson_observations_under_test", str(HELPER))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RENAME_IS_NO_CLOBBER = (os.name == "nt")


@pytest.fixture
def linkless(monkeypatch):
    """os.link refuses for a reason that is NOT "the destination exists".

    The two guards below are the two properties publication must hold AT ONCE, each
    one pinned as a tripwire so that a future fallback which drops either is a red
    test rather than a silent regression. They are deliberately kept together: the
    first review round removed the no-overwrite half, the second removed the atomic
    half while restoring the first.
    """
    module = _helper_module()
    real_rename = os.rename
    real_open = os.open

    def refuse(*args, **kwargs):
        raise OSError(errno.EPERM, "hardlinks are not supported here")

    def guarded_rename(src, dst, *args, **kwargs):
        """NO-OVERWRITE tripwire.

        Round 1's guard, kept and made precise rather than removed. The defect it
        caught was publishing with os.rename where rename(2) REPLACES an existing
        destination -- that is POSIX, and the module must still never reach rename
        there. On Windows os.rename is implemented with MoveFileExW WITHOUT
        MOVEFILE_REPLACE_EXISTING and raises FileExistsError instead of replacing,
        so there it is a legitimate atomic no-clobber primitive and the guard hands
        the call through to the real one.
        """
        if not RENAME_IS_NO_CLOBBER:
            raise AssertionError(
                "publication used os.rename on a platform where rename(2) REPLACES "
                "an existing destination, so it cannot preserve the no-overwrite "
                "guarantee")
        return real_rename(src, dst, *args, **kwargs)

    def guarded_open(path, flags, *args, **kwargs):
        """ATOMIC tripwire.

        Round 2's defect: the no-hardlink fallback created the file at the RECORD'S
        FINAL path with O_CREAT|O_EXCL and wrote the payload into it there. That is
        no-overwrite but not atomic -- a concurrent reader sees a truncated record,
        and an abrupt kill leaves one behind forever. The payload must always land
        in a same-directory temporary file first.
        """
        name = os.path.basename(str(path))
        if (flags & os.O_CREAT) and name.endswith((".md", ".json")):
            raise AssertionError(
                "publication created a file directly at a record's FINAL path "
                f"({name}); the payload must be written to a same-directory "
                "temporary file and then published atomically, so no reader can "
                "ever observe a half-written record")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "link", refuse)
    monkeypatch.setattr(os, "rename", guarded_rename)
    monkeypatch.setattr(os, "open", guarded_open)
    return module


def test_publication_without_hardlinks_publishes_atomically_or_refuses_outright(
        repo, linkless):
    """The fallback either publishes a WHOLE record or writes nothing at all.

    Where the platform still offers an atomic no-clobber primitive (Windows
    os.rename) the fallback must publish, because on such a filesystem it is the
    ONLY path. Where it does not, the contract is an explicit fail-closed refusal
    inside the closed exit-code set -- never a payload dribbled into the record's
    final path.
    """
    module = linkless
    inbox = module.resolve_inbox(str(repo))
    module._ensure_state_dirs(inbox)
    identifier = new_id()
    payload = b"# Lesson observation\n\nfallback body\n"
    dest = Path(inbox.observations_dir) / (identifier + ".md")

    if RENAME_IS_NO_CLOBBER:
        path = module._publish_atomically(
            inbox, inbox.observations_dir, identifier + ".md", payload)
        assert Path(path) == dest
        assert dest.read_bytes() == payload
    else:
        with pytest.raises(module.LessonError) as caught:
            module._publish_atomically(
                inbox, inbox.observations_dir, identifier + ".md", payload)
        assert caught.value.code == "publication-unsupported"
        assert caught.value.exit_code == EXIT_CONFLICT
        assert not dest.exists(), (
            "a refusal left something at the record's final path")

    leftovers = [name for name in os.listdir(inbox.observations_dir)
                 if name.endswith(".tmp")]
    assert leftovers == [], f"the fallback abandoned a temporary file: {leftovers}"


def test_publication_fails_closed_when_no_atomic_no_clobber_primitive_exists(
        repo, tmp_path, linkless, monkeypatch):
    """LH-B4/R2: the documented refusal, forced on every platform.

    A filesystem with neither hardlinks nor a no-clobber rename cannot satisfy both
    publication properties, and the module says so instead of dropping one. The
    refusal must be IN CONTRACT: a LessonError carrying exit 3 and a machine-readable
    code, nothing at the record's final path, no abandoned temporary, and the
    observation id still recordable afterwards.
    """
    module = linkless
    monkeypatch.setattr(
        module, "_rename_refuses_an_existing_destination", lambda: False)
    inbox = module.resolve_inbox(str(repo))
    module._ensure_state_dirs(inbox)
    identifier = new_id()
    dest = Path(inbox.observations_dir) / (identifier + ".md")

    with pytest.raises(module.LessonError) as caught:
        module._publish_atomically(
            inbox, inbox.observations_dir, identifier + ".md",
            b"# Lesson observation\n\nrefused body\n")
    assert caught.value.code == "publication-unsupported"
    assert caught.value.exit_code == EXIT_CONFLICT
    assert not dest.exists()
    assert os.listdir(inbox.observations_dir) == [], (
        "a fail-closed publication left state behind in the private inbox")

    # The id survives the refusal: a later attempt on a working filesystem records
    # it. That attempt is the REAL CLI in a subprocess, so it sees a real os.link
    # and none of the patches above.
    record_ok(repo, tmp_path, observation_request(identifier))
    assert observed_ids(pending_ok(repo)) == [identifier]


def test_publication_without_hardlinks_never_exposes_a_partial_record(
        repo, tmp_path, linkless, monkeypatch):
    """A concurrent reader must never see a record mid-write at its final path.

    The regression this pins: the fallback opened the RECORD'S FINAL path and wrote
    the payload into it, so a `pending` that listed the directory in between read a
    truncated file and reported a perfectly good capture as `observation-malformed`.
    The module docstring promises that "concurrent capture and reading are supported",
    and this is the exact shape that promise is about.

    The publication is suspended deterministically (no sleeps, no timing luck) inside
    the fsync of the temporary file -- after the payload bytes exist somewhere, and
    before the record is published -- while a REAL `pending` runs in a subprocess.
    """
    module = linkless
    inbox = module.resolve_inbox(str(repo))
    module._ensure_state_dirs(inbox)
    identifier = new_id()

    # The payload the real writer would publish, assembled through the module's OWN
    # constants and renderer exactly as cmd_record does -- so a concurrent reader
    # would genuinely accept this document once it lands, and a future change to the
    # envelope shape cannot leave this test measuring a stale proxy.
    request = observation_request(identifier)
    envelope = {"schema": module.SCHEMA_OBSERVATION}
    for field in module.OBSERVATION_REQUEST_FIELDS:
        envelope[field] = request[field]
    envelope["recorded_at"] = module._utc_now()
    envelope["repo_root"] = inbox.repo_root
    document = module.render_observation_document(envelope).encode("utf-8")
    dest = Path(inbox.observations_dir) / (identifier + ".md")

    suspended = threading.Event()
    released = threading.Event()
    real_fsync = os.fsync

    def suspending_fsync(fd):
        real_fsync(fd)
        suspended.set()
        assert released.wait(60), "the concurrent reader never released publication"

    monkeypatch.setattr(os, "fsync", suspending_fsync)

    failures = []

    def publish():
        try:
            module._publish_atomically(
                inbox, inbox.observations_dir, identifier + ".md", document)
        except BaseException as exc:            # surfaced in the assertions below
            failures.append(exc)
            suspended.set()

    worker = threading.Thread(target=publish)
    worker.start()
    try:
        assert suspended.wait(60), "publication never reached its suspension point"
        assert not dest.exists(), (
            "a file appeared at the record's FINAL path before publication completed")
        mid_flight = pending_ok(repo)
        assert "observation-malformed" not in diagnostic_codes(mid_flight), (
            "a concurrent reader saw a partially written record and reported a "
            "perfectly good capture as malformed")
        assert observed_ids(mid_flight) == [], (
            "an unpublished record was served to a concurrent reader")
    finally:
        released.set()
        worker.join(60)
    assert not worker.is_alive()
    assert failures == [], f"publication failed: {failures}"

    if RENAME_IS_NO_CLOBBER:
        assert dest.read_bytes() == document
        after = pending_ok(repo)
        assert observed_ids(after) == [identifier]
        assert "observation-malformed" not in diagnostic_codes(after)


def test_publication_without_hardlinks_never_overwrites_an_existing_record(
        repo, linkless):
    """LH-B4: the no-hardlink fallback keeps the no-overwrite guarantee.

    The earlier spelling was a lexists check followed by os.rename. On POSIX
    rename(2) REPLACES the destination atomically and without error, so a writer
    that lost the race between the two lines destroyed a historical, supposedly
    immutable record -- and the comment above it claimed the lexists check gave
    POSIX the same refusal Windows gets, which is false.

    The load-bearing assertion is the last one: whatever refusal the platform
    produces, the historical bytes are still there.
    """
    module = linkless
    inbox = module.resolve_inbox(str(repo))
    module._ensure_state_dirs(inbox)
    identifier = new_id()
    historical = b"# Lesson observation\n\nthe original bytes\n"
    dest = Path(inbox.observations_dir) / (identifier + ".md")
    dest.write_bytes(historical)

    with pytest.raises(module.LessonError) as caught:
        module._publish_atomically(
            inbox, inbox.observations_dir, identifier + ".md",
            b"# Lesson observation\n\ndifferent bytes\n")
    assert caught.value.code == (
        "destination-exists" if RENAME_IS_NO_CLOBBER else "publication-unsupported")
    assert caught.value.exit_code == EXIT_CONFLICT
    assert dest.read_bytes() == historical, (
        "the fallback overwrote a historical record")
    leftovers = [name for name in os.listdir(inbox.observations_dir)
                 if name.endswith(".tmp")]
    assert leftovers == [], f"the refusal abandoned a temporary file: {leftovers}"


# --------------------------------------------------------------------------- #
# Crash during publication
# --------------------------------------------------------------------------- #

CRASH_HARNESS = '''\
"""Run one real `record` and stop the process dead at a chosen instant.

os._exit is used rather than an exception: it skips every finally block, every
atexit handler, and every buffered flush, which is the closest a portable test gets
to SIGKILL or a power loss. Nothing in the helper's own error handling can run, so
whatever is on disk afterwards is exactly what a hard kill would leave.
"""
import importlib.util
import os
import sys

helper, repo, request_file, crash_at = sys.argv[1:5]
spec = importlib.util.spec_from_file_location("lesson_observations_crash", helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

CRASH_CODE = 137


def die(*args, **kwargs):
    os._exit(CRASH_CODE)


def refuse_link(*args, **kwargs):
    raise OSError(13, "hardlinks are not supported here")


if crash_at == "before-link":
    # The temporary file is complete and fsynced; nothing is published yet.
    os.link = die
elif crash_at == "instead-of-rename":
    # The no-hardlink fallback is reached and dies at its publication instant.
    os.link = refuse_link
    module._rename_refuses_an_existing_destination = lambda: True
    os.rename = die
elif crash_at == "after-link":
    # The record IS published; the process dies before the temporary is discarded.
    module._discard = die
elif crash_at == "mid-final-path-write":
    # Die the instant anything is CREATED at a record's final path. A correct
    # publication never does that -- it only ever creates the same-directory
    # temporary -- so this harness simply completes, exit 0. An implementation that
    # writes the payload straight to the final path dies holding an empty or
    # truncated record there, which is the exact permanent-corruption shape the
    # caller's invariant below refuses.
    os.link = refuse_link
    module._rename_refuses_an_existing_destination = lambda: True
    real_open = os.open

    def open_or_die(path, flags, *args, **kwargs):
        name = os.path.basename(str(path))
        if (flags & os.O_CREAT) and not name.endswith(".tmp"):
            handle = real_open(path, flags, *args, **kwargs)
            os.close(handle)
            os._exit(CRASH_CODE)
        return real_open(path, flags, *args, **kwargs)

    os.open = open_or_die
else:
    raise SystemExit("unknown crash point: " + crash_at)

sys.exit(module.main(["record", "--repo", repo, "--input", request_file]))
'''


@pytest.fixture
def crash_harness(tmp_path):
    path = tmp_path / "crash_harness.py"
    path.write_text(CRASH_HARNESS, encoding="utf-8")
    return path


@pytest.mark.parametrize("crash_at,expected_codes", [
    ("before-link", {137}),
    ("instead-of-rename", {137}),
    ("after-link", {137}),
    # Unreachable in a correct publication (nothing is ever created at the final
    # path), so exit 0 is the expected answer HERE and a 137 with a truncated record
    # is the answer from the implementation this arm exists to catch.
    ("mid-final-path-write", {0, 137}),
])
def test_a_hard_kill_during_publication_leaves_the_id_recordable(
        repo, tmp_path, crash_harness, crash_at, expected_codes):
    """A crash mid-publication must never brick an observation id.

    The regression this pins: a fallback that wrote the payload straight into the
    record's FINAL path left corrupt bytes there on a hard kill, permanently. The
    next `record` for that id then found unparseable bytes at the destination and
    refused with exit 3 forever -- an id no operator could use again without deleting
    a file by hand, from an inbox whose whole design says records are never deleted.

    With write-temp-then-publish, only two states are reachable from any crash
    point: nothing at the final path, or the WHOLE record at the final path. Both
    leave the id usable -- the first records, the second replays.
    """
    identifier = new_id()
    request = observation_request(identifier)
    request_file = write_request(tmp_path / (identifier + ".request.json"), request)
    dest = state_dir(repo, *OBSERVATIONS_PARTS) / (identifier + ".md")

    crashed = subprocess.run(
        [sys.executable, str(crash_harness), str(HELPER), str(repo),
         str(request_file), crash_at],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert crashed.returncode in expected_codes, (
        f"the harness exited out of contract at {crash_at}: "
        f"{crashed.returncode} {crashed.stdout}{crashed.stderr}")

    if dest.exists():
        # Published before the kill: the bytes must be the COMPLETE record, never a
        # prefix of it, and a reader must accept them.
        assert dest.read_bytes().endswith(b"```\n")
        page = pending_ok(repo)
        assert observed_ids(page) == [identifier]
        assert "observation-malformed" not in diagnostic_codes(page)

    # The id is still recordable: identical content is accepted either as a fresh
    # record or as an idempotent replay, and never as a permanent conflict.
    receipt = record_ok(repo, tmp_path, request)
    assert receipt["observation_id"] == identifier
    assert receipt["status"] in {"recorded", "replayed"}
    page = pending_ok(repo)
    assert observed_ids(page) == [identifier]
    assert "observation-malformed" not in diagnostic_codes(page)


# --------------------------------------------------------------------------- #
# The per-entry read boundary
# --------------------------------------------------------------------------- #
#
# THE PROPERTY every test in this section grades, stated once:
#
#     A `pending` page that meets ONE unreadable entry serves every other entry
#     and names the withheld one in a diagnostic. It never fails the whole
#     command, and it never answers a question it could not look up.
#
# Three review rounds found three different raise sites with the same shape: a
# guard helper beneath the per-entry loops raising the WHOLE-command refusal class,
# which walks straight past an `except StateFileError` handler and fails the page.
# Each round's fix respelled one more named site, and the next round found the next
# one -- one call deeper, where no leaf pre-check can reach it (_read_state_file
# re-walks and re-lstats the leaf and every ancestor through its own
# _guard_state_path, AFTER any pre-check has already passed).
#
# So these tests are deliberately NOT aimed at named functions. They inject the
# real transient failure class at os.lstat -- the one primitive every one of those
# guards ends up calling -- at different DEPTHS of the same read, and assert the
# page-level property. A future fourth site inherits this coverage.

def _denied(_real):
    """The transient failure class this whole section models.

    An antivirus scan, an advisory file lock, a sharing violation, a network-share
    hiccup: the file is there, and for this instant it cannot be inspected. It is
    NOT FileNotFoundError, which is the only OSError that proves absence.
    """
    raise PermissionError(errno.EACCES, "the file is held by another process")


def _looks_like_a_link(real):
    """A stat result that claims to be a symlink, for the TOCTOU race window.

    A reparse point present BEFORE the page starts is intercepted by the loop's own
    leaf check and is already covered by the tests above. This models the one that
    appears between that check and the re-walk inside the read -- the only way the
    deeper reparse-point refusal is reachable per entry.
    """
    st = real()
    return os.stat_result((stat.S_IFLNK | 0o600,) + tuple(st)[1:])


class _LstatFault(object):
    """Make os.lstat misbehave for ONE path, after N successful calls on it.

    Installed on os.lstat itself rather than on any helper function, so a test
    cannot pass merely by agreeing with a mock: every real caller underneath the
    loop sees it, including ones this file does not name. `after=0` fails the very
    first look (the loop's own check); `after=1` lets that one succeed and fails the
    NEXT look at the same leaf, which is the re-walk inside the read -- the depth a
    pre-check fix cannot reach.
    """

    def __init__(self, target, effect, after=0):
        self.target = os.path.normcase(os.path.abspath(str(target)))
        self.effect = effect
        self.after = after
        self.real = os.lstat
        self.calls = 0

    def install(self, monkeypatch):
        monkeypatch.setattr(os, "lstat", self)
        return self

    def __call__(self, path, *args, **kwargs):
        def real():
            return self.real(path, *args, **kwargs)
        try:
            same = os.path.normcase(os.path.abspath(str(path))) == self.target
        except (TypeError, ValueError):
            same = False
        if same:
            self.calls += 1
            if self.calls > self.after:
                return self.effect(real)
        return real()


def pending_in_process(module, repo, capsys):
    """Run `pending` through main() IN THIS PROCESS: (exit code, page, error).

    The subprocess driver every other test uses cannot inject a fault into the
    helper's own os.lstat, and the fault is the whole point here. main() is still
    the entry point, so the closed exit-code contract and the stderr JSON shape are
    graded exactly as the CLI produces them.
    """
    code = module.main(["pending", "--repo", str(repo)])
    captured = capsys.readouterr()
    page = json.loads(captured.out) if captured.out.strip() else None
    error = None
    if captured.err.strip():
        error = json.loads(captured.err.strip().splitlines()[-1])
        assert set(error) <= {"code", "message", "observation_id"}, error
    return code, page, error


@pytest.fixture
def two_observations(repo, tmp_path):
    """The helper as a module, plus two REAL recorded observations."""
    poisoned = new_id()
    healthy = new_id()
    record_ok(repo, tmp_path, observation_request(poisoned))
    record_ok(repo, tmp_path, observation_request(healthy))
    return _helper_module(), poisoned, healthy


@pytest.fixture
def two_observations_one_completed(repo, tmp_path, two_observations):
    """As above, with the poisoned observation carrying a real receipt."""
    module, poisoned, healthy = two_observations
    assert ok_json(complete(repo, tmp_path, completion_request(poisoned)))
    return module, poisoned, healthy


@pytest.mark.parametrize("after,effect,expected", [
    (0, _denied, "observation-malformed"),
    (1, _denied, "observation-malformed"),
    (1, _looks_like_a_link, "unexpected-inbox-entry"),
], ids=["first-look", "the-re-walk-inside-the-read", "a-link-appears-mid-read"])
def test_an_unreadable_observation_leaf_withholds_only_that_observation(
        repo, two_observations, monkeypatch, capsys, after, effect, expected):
    """One locked observation file must not hide every healthy one behind it.

    `first-look` is the arm a reviewer reproduced live: a PermissionError on the
    loop's own lstat raised the whole-command refusal and the ENTIRE page failed
    with exit 2, for one entry an antivirus scanner happened to hold open.
    `the-re-walk-inside-the-read` is the same failure one call deeper, past any leaf
    pre-check, which is why the fix is at the loop's call boundary and not at a
    raise site.
    """
    module, poisoned, healthy = two_observations
    leaf = state_dir(repo, *OBSERVATIONS_PARTS) / (poisoned + ".md")
    _LstatFault(leaf, effect, after=after).install(monkeypatch)

    code, page, error = pending_in_process(module, repo, capsys)

    assert code == EXIT_OK, f"one unreadable entry failed the whole page: {error}"
    assert observed_ids(page) == [healthy], (
        "the healthy observation was hidden behind the unreadable one")
    withheld = [d for d in page["diagnostics"] if d["code"] == expected]
    assert [d.get("observation_id") for d in withheld] == [poisoned], (
        f"the withheld entry was not named in a {expected} diagnostic: "
        f"{page['diagnostics']}")


@pytest.mark.parametrize("after,effect,expected", [
    (0, _denied, "receipt-malformed"),
    (1, _denied, "receipt-malformed"),
    (1, _looks_like_a_link, "unexpected-inbox-entry"),
], ids=["first-look", "the-re-walk-inside-the-read", "a-link-appears-mid-read"])
def test_an_unreadable_receipt_leaf_withholds_only_that_observation(
        repo, two_observations_one_completed, monkeypatch, capsys,
        after, effect, expected):
    """A receipt that cannot be read is WITHHELD, never assumed absent.

    Two opposite wrong answers used to live on this path, from one root cause. The
    deep one failed the whole command with exit 2. The shallow one was worse and
    silent: os.path.lexists swallows OSError and answers False, so a receipt that
    could not be inspected was read as "no receipt", and an observation that was
    already dispositioned came back as a fresh pending candidate with no diagnostic
    at all. The assertion that catches that one is `observed_ids == [healthy]`: the
    poisoned id is completed, so any spelling that offers it is a wrong answer.
    """
    module, poisoned, healthy = two_observations_one_completed
    leaf = state_dir(repo, *RECEIPTS_PARTS) / (poisoned + ".json")
    _LstatFault(leaf, effect, after=after).install(monkeypatch)

    code, page, error = pending_in_process(module, repo, capsys)

    assert code == EXIT_OK, f"one unreadable receipt failed the whole page: {error}"
    assert observed_ids(page) == [healthy], (
        "an observation whose receipt could not be read was offered as a candidate")
    withheld = [d for d in page["diagnostics"] if d["code"] == expected]
    assert [d.get("observation_id") for d in withheld] == [poisoned]
    assert "observation-completed" not in diagnostic_codes(page), (
        "the page claimed to know a disposition it could not read")


def test_an_entry_path_outside_the_inbox_is_withheld_rather_than_raised(
        repo, tmp_path):
    """The third refusal on the per-entry path, pinned before it can ever arm.

    `state-path-outside-inbox` is believed unreachable today -- observation names
    are filtered by the UUID pattern, and receipt names are built from an id the
    envelope check already matched against its own filename -- but it sits on the
    per-entry path, and a relaxed filename filter or a new caller would arm it. It
    is graded through the real boundary with a real out-of-inbox path rather than
    asserted to be unreachable, so the day it arms it degrades instead of escaping.
    """
    module = _helper_module()
    inbox = module.resolve_inbox(str(repo))
    outside = tmp_path / "outside-the-inbox.md"
    outside.write_text("# Lesson observation\n", encoding="utf-8")

    outcome, parsed = module._read_inbox_entry(
        inbox, str(outside), new_id(), module.parse_observation_document)

    assert outcome == module.ENTRY_REFUSED
    assert parsed is None


def test_an_unreadable_observations_DIRECTORY_still_fails_the_whole_command(
        repo, two_observations, monkeypatch, capsys):
    """The other half of the contract, and the false-positive check for the fix.

    The boundary absorbs failures raised while reading ONE entry. It must not have
    widened to absorb a failure at DIRECTORY scope: a reader that cannot inspect the
    inbox directory itself cannot know what it is not showing, so serving a page
    would be a silent wrong answer. That one still refuses, loudly, at exit 2.
    """
    module, poisoned, healthy = two_observations
    _LstatFault(state_dir(repo, *OBSERVATIONS_PARTS), _denied).install(monkeypatch)

    code, page, error = pending_in_process(module, repo, capsys)

    assert code == EXIT_INVALID, "a directory-scope failure was degraded to a note"
    assert page is None
    assert error["code"] == "state-path-unreadable"


def test_an_unlistable_inbox_directory_refuses_rather_than_crashing(
        repo, two_observations, monkeypatch, capsys):
    """Directory scope again, but on the listing rather than the inspection.

    os.listdir was the one unguarded call left on this path: an ordinary permission
    denial fell through to main's bare-Exception backstop and was reported as a
    generic `internal-error` at exit 3 -- "this helper has a bug" rather than "this
    directory could not be read". The same whole-command decision, now in the
    module's own closed refusal class.
    """
    module, poisoned, healthy = two_observations
    target = os.path.normcase(
        os.path.abspath(str(state_dir(repo, *OBSERVATIONS_PARTS))))
    real_listdir = os.listdir

    def refuse(path=".", *args, **kwargs):
        if os.path.normcase(os.path.abspath(str(path))) == target:
            raise PermissionError(errno.EACCES, "the directory cannot be listed")
        return real_listdir(path, *args, **kwargs)

    monkeypatch.setattr(os, "listdir", refuse)

    code, page, error = pending_in_process(module, repo, capsys)

    assert code == EXIT_INVALID
    assert page is None
    assert error["code"] == "state-dir-unreadable"


def test_a_genuine_bug_beneath_the_loop_still_reaches_the_backstop(
        repo, two_observations, monkeypatch, capsys):
    """The boundary catches this module's refusal class, NOT every exception.

    Widening it to `except Exception` would turn a real defect -- a TypeError, a
    KeyError, a name that no longer exists -- into a tidy per-entry diagnostic, and
    the page would keep serving while the reader was broken. A bug must still reach
    main's fail-closed backstop and report exit 3.
    """
    module, poisoned, healthy = two_observations

    def broken(text, observation_id):
        raise TypeError("a genuine defect, not an unreadable file")

    monkeypatch.setattr(module, "parse_observation_document", broken)

    code, page, error = pending_in_process(module, repo, capsys)

    assert code == EXIT_CONFLICT
    assert page is None
    assert error["code"] == "internal-error"


# --------------------------------------------------------------------------- #
# An ancestor that goes dangling DURING the page
# --------------------------------------------------------------------------- #
#
# The ancestor tests above poison the chain BEFORE the command starts, which the
# directory-level guards intercept at exit 2. These two cover the other timing, and
# specifically the sub-case where the redirected ancestor resolves NOTHING at the
# leaf's name: the leaf's own os.lstat then raises FileNotFoundError while transiting
# the poisoned ancestor, so the read sees an ordinary deletion. Both callers treat
# absence as innocuous and continue without a diagnostic, so an unverified absence
# drops a LIVE record from the page with no trace at all -- worse than the named
# per-entry refusal, and the exact shape the boundary exists to rule out.

def _dangle_ancestor(directory, target):
    """Turn a live inbox DIRECTORY into a reparse point whose target is gone.

    mklink /J needs an existing target, so the only way to build a dangling junction
    is to move the real directory aside, link to it, and then remove it -- the same
    sequence test_a_dangling_reparse_point_in_the_inbox_is_refused_not_read_as_empty
    uses. Returns None on success, or the reason this platform refused the fixture
    (restoring the directory first, so the caller can skip by name rather than assert
    a weaker property against a half-built fixture).
    """
    shutil.move(str(directory), str(target))
    failure = _make_reparse_point(directory, target)
    if failure is not None:
        shutil.move(str(target), str(directory))
        return failure
    shutil.rmtree(str(target))
    return None


def test_an_absent_leaf_under_a_poisoned_ancestor_is_refused_not_reported_absent(
        repo, tmp_path):
    """Absence is a conclusion about the CHAIN, not about one lstat.

    Graded at the boundary rather than through a page because the observation loop's
    caller happens to have a later directory-scope guard that would refuse the whole
    command anyway; the receipt loop below has none, and both loops share THIS
    function. The premise is pinned with a real os.lstat rather than assumed: if this
    platform ever stopped raising FileNotFoundError through a dangling junction, the
    test would say so instead of passing for the wrong reason.
    """
    module = _helper_module()
    inbox = module.resolve_inbox(str(repo))
    identifier = new_id()
    record_ok(repo, tmp_path, observation_request(identifier))
    observations = state_dir(repo, *OBSERVATIONS_PARTS)
    leaf = observations / (identifier + ".md")

    failure = _dangle_ancestor(observations, tmp_path / "observations-target")
    if failure is not None:
        pytest.skip(f"this platform refused every reparse-point fixture: {failure}")

    with pytest.raises(FileNotFoundError):
        os.lstat(str(leaf))

    outcome, parsed = module._read_inbox_entry(
        inbox, str(leaf), identifier, module.parse_observation_document)

    assert outcome == module.ENTRY_REFUSED, (
        "a redirected ancestor was reported as an ordinary deletion")
    assert parsed is None


def test_an_ancestor_that_goes_dangling_MID_PAGE_never_drops_a_record_silently(
        repo, two_observations_one_completed, tmp_path, monkeypatch, capsys):
    """The page-level harm, on the loop with no directory-scope guard behind it.

    The receipt loop reads ENTRY_ABSENT as "genuinely undispositioned", so an absence
    manufactured by a redirected ancestor re-offers an observation that already
    carries a final disposition receipt -- as a fresh candidate, with no diagnostic,
    on a page that exits 0. The ancestor is poisoned for real, from inside the first
    lstat of the first receipt leaf, so the fault is the filesystem's and the
    FileNotFoundError is the OS's.
    """
    module, poisoned, healthy = two_observations_one_completed
    receipts = state_dir(repo, *RECEIPTS_PARTS)
    leaf = receipts / (poisoned + ".json")
    fixture = {"poisoned": False, "failure": None}

    def poison_the_ancestor_then_look(real):
        if not fixture["poisoned"]:
            fixture["poisoned"] = True
            fixture["failure"] = _dangle_ancestor(
                receipts, tmp_path / "receipts-target")
        return real()

    _LstatFault(leaf, poison_the_ancestor_then_look).install(monkeypatch)

    code, page, error = pending_in_process(module, repo, capsys)

    if fixture["failure"] is not None:
        pytest.skip(
            "this platform refused every reparse-point fixture: "
            f"{fixture['failure']}")
    assert code == EXIT_OK, f"a per-entry race failed the whole page: {error}"
    assert poisoned not in observed_ids(page), (
        "an observation whose receipt was hidden by a redirected ancestor was "
        "offered as a fresh candidate")
    named = {d.get("observation_id") for d in page["diagnostics"]}
    assert poisoned in named, (
        f"the withheld observation was not named in any diagnostic: "
        f"{page['diagnostics']}")
    assert [d["code"] for d in page["diagnostics"]
            if d.get("observation_id") == poisoned] == ["unexpected-inbox-entry"]
    # The general invariant, stated over every record this inbox holds: a live
    # record is either SERVED or NAMED. Vanishing is not one of the outcomes.
    assert set(observed_ids(page)) | named >= {poisoned, healthy}
