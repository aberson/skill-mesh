"""Cross-skill guards for the v2 session-transition contract.

These assertions cover the seams that previously let one window execute or mutate
another window's state, and the coordinated failure path shared by task-handoff,
session-wrap, and user-wrap. They intentionally avoid grading prose length or style.
"""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_ROOT = REPO_ROOT / "skills" / "user-wrap" / "evals"
# Expected host output is fixture data, not a dependency on a host source tree.
SESSION_MARKERS = dict(
    line.split("\t", 1)
    for line in (REPO_ROOT / "tests" / "fixtures" / "session-output-markers.tsv")
    .read_text(encoding="utf-8")
    .splitlines()
)


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_task_handoff_owns_only_its_session_state():
    core = _read("skills/task-handoff/core.md")

    assert "not from an identity inherited from a launching or parent process" in core
    assert "not from another host's session variable" in core
    assert "every session file other than this" in core
    assert "session's own, is read-only orientation" in core
    assert "Never execute its Next Action as this session's" in core
    assert "sessions/<session-id>.md" in core


def test_task_handoff_git_mutations_fail_closed_on_root_or_index_uncertainty():
    core = _read("skills/task-handoff/core.md")

    # The enclosing-root walk must make progress instead of accepting the same root forever.
    assert "if ($next -and $next -ne $lib)" in core
    assert core.count("if ($next -and $next -ne $lib)") == 2

    # A moved cwd and an index failure both stop before staging. Exit 1 alone means untracked.
    assert "git root changed after session write; session file saved; nothing staged or pushed" in core
    assert "memory index check failed (git exit <code>)" in core
    assert "elseif ($memoryExit -eq 1)" in core
    assert "every other non-zero exit is a failed check" in core


def test_unwritten_checkpoint_stays_visible_across_wrap_layers():
    handoff = _read("skills/task-handoff/core.md")
    session = _read("skills/session-wrap/core.md")
    user = _read("skills/user-wrap/core.md")

    assert "Checkpoint incomplete: rollup not regenerated" in handoff
    assert "Full handoff: not rendered this turn (checkpoint not written)" in session
    assert "never `/clear` and never the fresh-window opener" in session
    assert "no `SAFE TO CLOSE` claim" in session
    assert "no `checkpoint not written` flag" in user
    assert "append nothing" in user


def test_session_wrap_retains_own_session_authority_and_uses_library_writes():
    core = _read("skills/session-wrap/core.md")
    flat = " ".join(core.split())

    assert "Retain that ID and path through triage" in flat
    assert "fallback value is ever promoted into a new own-session checkpoint" in flat
    assert "from the shared rollup." in flat
    assert "second `task-handoff --loop --no-commit`" in flat
    assert "Never edit a session file or `current.md` directly" in flat
    assert "unsaved with this window: <items>" in flat
    assert "Owner session: <session-id>" in flat
    assert "absent or unequal means another window replaced the shared render" in flat
    assert "Full handoff (owner <session-id>)" in flat


def test_session_wrap_reports_completed_and_failed_git_outcomes_distinctly():
    session = _read("skills/session-wrap/core.md")
    user = _read("skills/user-wrap/core.md")

    for outcome in (
        "repo-update completed + pushed @ <short-sha>",
        "committed <N> files + pushed <M> commit(s) @ <short-sha>",
        "pushed <N> pending @ <short-sha>",
        "commit failed: <reason>; nothing pushed",
        "commit created @ <short-sha>; push failed: <reason>",
        "pending push failed: <reason>",
    ):
        assert outcome in session
    assert "never use bare\n`repo-update` as completion evidence" in session
    assert "repo-update completed + pushed @ <short-sha>" in user
    assert "committed <N> files + pushed <M> commit(s) @ <short-sha>" in user


def test_session_wrap_consumes_closeout_state_without_mutating_it():
    core = _read("skills/session-wrap/core.md")

    assert "skill only CONSUMES it" in core
    assert "never assesses lanes and never writes or refreshes" in core
    assert "Only a live `STOP_ALLOWED` routes `end-window`" in core
    assert "Score rule 1's unattended-window gate is not applied here" in core


def test_user_wrap_never_runs_a_fallback_next_action_on_codex():
    core = _read("skills/user-wrap/core.md")
    adapter = _read("skills/user-wrap/providers/codex.md")

    assert "not this session's own; orientation only" in core
    assert "Otherwise (fallback, stale, or absent state) execute nothing" in core
    assert "If the host exposes no stable session identity" in adapter
    assert "KEEP GOING runs no Next Action" in adapter
    assert "never fabricate or guess an identity" in adapter


def test_locked_next_action_is_held_across_user_wrap_and_its_eval():
    core = _read("skills/user-wrap/core.md")
    codex = _read("skills/user-wrap/providers/codex.md")
    evals = json.loads((EVALS_ROOT / "evals.json").read_text(encoding="utf-8"))
    assertions = [item for category in evals["categories"] for item in category["evals"]]
    assertion_6 = next(item for item in assertions if item["id"] == 6)["statement"]

    assert "Locked bundle held (not executed by user-wrap)." in core
    assert "bundle is printed and held, never executed" in codex
    assert "locked task-handoff-next-action-v1 bundle" in assertion_6
    assert "locked-bundle run that executes" in assertion_6


def test_shared_resume_backstop_discriminates_owned_fallback_and_locked_state():
    schema = _read("_shared/task-state-schema.md")
    backstop = schema.split("### Model-side resume backstop (hook silent)", 1)[1]

    assert "Retain whether the selected source belongs to this session's verified identity" in backstop
    assert "Never execute a fallback action" in backstop
    assert "task-handoff-next-action-v1" in backstop
    assert "do not execute or flatten it" in backstop
    assert "A pending approval or failed prerequisite stays pending" in backstop


def test_session_wrap_spawn_gate_and_locked_pointer_are_closed():
    core = _read("skills/session-wrap/core.md")

    assert "spawn failed (ask-first pending) - use the Pick-up-here block above" in core
    assert "the ask must remain the last actionable" in core

    spawn_branches = core.split("if ($lockedBundle) {", 1)[1]
    locked_branch, plain_tail = spawn_branches.split("} else {", 1)
    plain_branch = plain_tail.split("\n        }", 1)[0]
    assert "do not execute or flatten it" in locked_branch
    assert "execute its Next Action" not in locked_branch
    assert "execute its Next Action" in plain_branch


def test_codex_session_wrap_uses_same_session_skill_mapping():
    adapter = _read("skills/session-wrap/providers/codex.md")

    assert "resolving the installed `SKILL.md` and its referenced core" in adapter
    assert "absence of a separate named-skill or slash-command API is not a missing capability" in adapter
    assert "Let task-handoff's own preflight report its actual missing dependency" in adapter


def test_native_codex_adapters_stop_without_router_or_cross_provider_retry():
    adapters = [
        _read("skills/task-handoff/providers/codex.md"),
        _read("skills/session-wrap/providers/codex.md"),
        _read("skills/user-wrap/providers/codex.md"),
    ]
    for adapter in adapters:
        lowered = adapter.lower()
        assert "router reason" not in lowered
        assert "cross-cloud retry" not in lowered
        assert "retry allowance" not in lowered
        assert "do not retry implicitly" in lowered
        assert "do not switch providers" in lowered


def test_user_wrap_repository_evals_are_complete_and_closed():
    evals = json.loads((EVALS_ROOT / "evals.json").read_text(encoding="utf-8"))
    scenarios = json.loads(
        (EVALS_ROOT / "test_scenarios.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (EVALS_ROOT / "golden" / "manifest.json").read_text(encoding="utf-8")
    )

    assertions = [item for category in evals["categories"] for item in category["evals"]]
    assert [item["id"] for item in assertions] == list(range(1, 11))
    assert evals["passing_threshold"] == "8/10"
    assert len(scenarios["scenarios"]) == 8
    assert len({item["id"] for item in scenarios["scenarios"]}) == 8
    assert len(manifest["additional_goods"]) == 8
    assert len(manifest["bads"]) == 15
    assert manifest["verification_summary"] == {"accepted": 15, "inert": 0, "total": 15}

    mapped = manifest["additional_goods"] + manifest["bads"]
    for item in mapped:
        assert (EVALS_ROOT / "golden" / item["file"]).is_file(), item["file"]

    assertion_8 = next(item for item in assertions if item["id"] == 8)["statement"]
    assert "Otherwise (no segment reads 'ask-first pending'" in assertion_8
    assert "no 'checkpoint not written' flag" in assertion_8
    assert "pushed <N> pending @ <short-sha>" in assertion_8
    assert "render must label it held data" in assertion_8


def test_user_wrap_new_goldens_discriminate_the_session_safety_failures():
    golden = EVALS_ROOT / "golden"
    fallback_good = (golden / "good_keep_going_fallback.md").read_text(encoding="utf-8")
    fallback_bad = (golden / "bad_keepgoing_runs_fallback_action.md").read_text(encoding="utf-8")
    assert "not this session's own; orientation only" in fallback_good
    assert "Next Action not run:" in fallback_good
    assert "Proceeding with Next Action:" not in fallback_good
    assert "Proceeding with Next Action:" in fallback_bad

    pending_good = (golden / "good_wrap_close_ask_pending.md").read_text(encoding="utf-8")
    pending_safe_bad = (golden / "bad_wrapclose_safe_line_after_pending.md").read_text(encoding="utf-8")
    pending_answer_bad = (golden / "bad_wrapclose_answers_ask.md").read_text(encoding="utf-8")
    assert "RAN SESSION-WRAP & SAFE TO CLOSE" not in pending_good
    assert "ask-first pending" in pending_good
    assert "Withheld Git plan:" in pending_good
    assert "scoped add: `src/session_state.py` and `tests/test_session_state.py`" in pending_good
    assert "commit message: `fix: preserve session-state ownership`" in pending_good
    assert "Step 1 — approve or adjust the withheld Git plan:" in pending_good
    assert pending_good.rstrip().endswith("```")
    assert "Approve the scoped plan above for branch main" in pending_good
    def transcript_body(text):
        return text[text.index("Resuming "):].rstrip()

    assert transcript_body(pending_safe_bad) == transcript_body(pending_good) + "\n\nRAN SESSION-WRAP & SAFE TO CLOSE"
    assert transcript_body(pending_answer_bad) == transcript_body(pending_good) + "\n\nApprove as written for branch main."

    push_good = (golden / "good_wrap_close_push_rejected.md").read_text(encoding="utf-8")
    push_bad = (golden / "bad_wrapclose_safe_line_after_push_failure.md").read_text(encoding="utf-8")
    failure = "commit created @ d4e5f6a; push failed: remote rejected (pre-receive hook declined)"
    assert push_good.rstrip().endswith(failure)
    assert "RAN SESSION-WRAP & SAFE TO CLOSE" not in push_good
    assert "RAN SESSION-WRAP & SAFE TO CLOSE" in push_bad

    unwritten_good = (golden / "good_wrap_close_unwritten_checkpoint.md").read_text(encoding="utf-8")
    unwritten_bad = (golden / "bad_wrapclose_safe_line_after_unwritten_checkpoint.md").read_text(encoding="utf-8")
    assert "Full handoff: not rendered this turn (checkpoint not written)" in unwritten_good
    assert unwritten_good.rstrip().endswith("```")
    assert "RAN SESSION-WRAP & SAFE TO CLOSE" not in unwritten_good
    assert "RAN SESSION-WRAP & SAFE TO CLOSE" in unwritten_bad


def test_rejected_push_scenario_cannot_collapse_into_clean_but_ahead():
    scenarios = json.loads(
        (EVALS_ROOT / "test_scenarios.json").read_text(encoding="utf-8")
    )["scenarios"]
    rejected = next(item for item in scenarios if item["id"] == "scenario_wrapclose_push_rejected")
    context = rejected["context"]
    assert "setup commit is already pushed" in context
    assert "make one tracked dirty edit" in context
    assert "pre-receive hook" in context
    assert "commit created @ <short-sha>; push failed" in context


def test_user_wrap_scenarios_and_goldens_use_own_session_state():
    scenarios = json.loads(
        (EVALS_ROOT / "test_scenarios.json").read_text(encoding="utf-8")
    )["scenarios"]
    by_id = {item["id"]: item for item in scenarios}
    for scenario_id in (
        "scenario_recycle_boundary",
        "scenario_wrapclose_morning",
        "scenario_safeclose_allclear",
    ):
        assert "own sessions/<session-id>.md" in by_id[scenario_id]["context"]

    golden = EVALS_ROOT / "golden"
    for name in ("good_recycle_window.md", "good_wrap_close.md"):
        rendered = (golden / name).read_text(encoding="utf-8")
        assert SESSION_MARKERS["owned_written"] in rendered
        assert SESSION_MARKERS["derived_rollup"] in rendered
        assert SESSION_MARKERS["legacy_written"] not in rendered
        assert "Owner session: <session-id>" in rendered
        assert "Full handoff (owner <session-id>)" in rendered
        assert "require Owner session <session-id>" in rendered

    mutation = (golden / "bad_mutation_before_verdict.md").read_text(encoding="utf-8")
    assert "Session SHA 41b7e02 matches HEAD" in mutation
    assert "Session SHA f3a91d2 matches HEAD" not in mutation


def test_completed_wrap_keeps_locked_bundle_as_data_through_render_and_opener():
    golden_path = EVALS_ROOT / "golden" / "good_wrap_close.md"
    golden_bytes = golden_path.read_bytes()

    def delimiter_with_eol(
        data: bytes, marker: bytes, *, before: bool = False
    ) -> bytes:
        assert data.count(marker) == 1
        marker_start = data.index(marker)
        if before:
            eol = b"\r\n" if data[marker_start - 2:marker_start] == b"\r\n" else b"\n"
            delimiter = eol + marker
        else:
            marker_end = marker_start + len(marker)
            eol = b"\r\n" if data[marker_end:marker_end + 2] == b"\r\n" else b"\n"
            delimiter = marker + eol
        assert data.count(delimiter) == 1
        return delimiter

    owned_prefix = delimiter_with_eol(
        golden_bytes, SESSION_MARKERS["owned_prefix"].encode("utf-8")
    )
    owned_suffix = delimiter_with_eol(
        golden_bytes, b"===== end written file =====", before=True
    )
    render_file_prefix = delimiter_with_eol(
        golden_bytes, SESSION_MARKERS["render_prefix"].encode("utf-8")
    )
    render_file_suffix = delimiter_with_eol(
        golden_bytes, b"===== end rendered file =====", before=True
    )
    assert golden_bytes.count(owned_prefix) == 1
    assert golden_bytes.count(owned_suffix) == 1
    assert golden_bytes.count(render_file_prefix) == 1
    assert golden_bytes.count(render_file_suffix) == 1

    owned_start = golden_bytes.index(owned_prefix) + len(owned_prefix)
    owned_end = golden_bytes.index(owned_suffix, owned_start)
    rendered_file_start = golden_bytes.index(render_file_prefix) + len(render_file_prefix)
    rendered_file_end = golden_bytes.index(render_file_suffix, rendered_file_start)
    owned_state = golden_bytes[owned_start:owned_end]
    rendered_file = golden_bytes[rendered_file_start:rendered_file_end]

    source_prefix = b"Next Action: "
    source_suffix = delimiter_with_eol(owned_state, b"Last written:", before=True)
    render_prefix = delimiter_with_eol(
        rendered_file,
        "## Held Next Action bundle — data only; owning dispatcher required".encode(),
    )
    render_suffix = delimiter_with_eol(
        rendered_file,
        b"Held bundle not executed or flattened by session-wrap.",
        before=True,
    )
    assert owned_state.count(source_prefix) == 1
    assert owned_state.count(source_suffix) == 1
    assert rendered_file.count(render_prefix) == 1
    assert rendered_file.count(render_suffix) == 1

    source_start = owned_state.index(source_prefix) + len(source_prefix)
    source_end = owned_state.index(source_suffix, source_start)
    render_start = rendered_file.index(render_prefix) + len(render_prefix)
    render_end = rendered_file.index(render_suffix, render_start)
    source_bundle = owned_state[source_start:source_end]
    rendered_bundle = rendered_file[render_start:render_end]

    assert source_bundle == rendered_bundle
    prior_indentation_mutation = b"  " + source_bundle.replace(b"\n", b"\n  ")
    assert prior_indentation_mutation != rendered_bundle
    alternate_line_endings = (
        source_bundle.replace(b"\r\n", b"\n")
        if b"\r\n" in source_bundle
        else source_bundle.replace(b"\n", b"\r\n")
    )
    assert alternate_line_endings != rendered_bundle

    golden = golden_bytes.decode("utf-8")
    scenario = next(
        item
        for item in json.loads((EVALS_ROOT / "test_scenarios.json").read_text(encoding="utf-8"))["scenarios"]
        if item["id"] == "scenario_wrapclose_morning"
    )
    assert "Next Action: task-handoff-next-action-v1" in golden
    assert "Held Next Action bundle — data only; owning dispatcher required" in golden
    assert "Held bundle not executed or flattened by session-wrap." in golden
    assert "Owner session: <session-id>" in golden
    final_block = golden.rsplit("```text", 1)[1].split("```", 1)[0]
    assert "do not execute or flatten it" in final_block
    assert "execute its Next Action" not in final_block
    assert "locked task-handoff-next-action-v1 bundle" in scenario["description"]


def test_recycle_render_records_observed_pre_commit_state():
    import re
    body = (REPO_ROOT / "skills/user-wrap/evals/golden/good_recycle_window.md").read_text(encoding="utf-8")
    opening = body.split("===== rendered file:", 1)[0]
    rendered = body.split("===== rendered file:", 1)[1].split("===== end rendered file =====", 1)[0]
    receipt = body.split("## Pick up here", 1)[1]
    observed = re.search(r"git: toybox master @ ([0-9a-f]+)", opening).group(1)
    future = re.search(r"pushed 1 commit\(s\) @ ([0-9a-f]+)", receipt).group(1)
    assert observed != future
    assert f"HEAD @ {observed} (toybox)" in rendered
    assert f"HEAD @ {future} (toybox)" not in rendered
    assert "3 dirty files (before Git verb)" in rendered
    assert "master clean" not in rendered
