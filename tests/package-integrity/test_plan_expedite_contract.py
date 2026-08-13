from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "skills" / "plan-expedite" / "core.md"
TASK_HANDOFF = ROOT / "skills" / "task-handoff" / "core.md"
SESSION_WRAP = ROOT / "skills" / "session-wrap" / "core.md"
TASK_STATE_SCHEMA = ROOT / "_shared" / "task-state-schema.md"


def test_explicit_initial_handoff_is_fail_closed_and_preserved() -> None:
    text = CORE.read_text(encoding="utf-8")

    assert "plan-expedite-initial-handoff-v1" in text
    assert "preserve that block's command lines byte-for-byte" in text
    assert "never reconstruct its `/goal`, drop a selector such as `--steps`" in text
    assert "halt before `repo-sync`" in text
    assert "separate fenced observation block" in text


def test_explicit_handoff_has_deterministic_parser_and_safe_effective_set() -> None:
    text = CORE.read_text(encoding="utf-8")

    assert "**Structural grammar.**" in text
    assert "**Exact lexer.**" in text
    assert "**Argument grammar.**" in text
    assert "**Effective-set safety.**" in text
    assert "do this even when no selector is present" in text
    assert "each declared dependency must" in text
    assert "also be selected or already `Status: DONE`" in text
    assert "Resolve `--plan` from `HANDOFF_RUN_DIR`" in text
    assert "immediately after `plan-review` before" in text
    assert "immediately after `plan-wrap` before `repo-sync`" in text
    assert "once more after" in text and "`repo-sync` before task-handoff" in text


def test_resume_state_v2_invalidates_stale_handoffs() -> None:
    text = CORE.read_text(encoding="utf-8")

    assert '"schema_version": 2' in text
    assert '"plan_digest": "sha256:<64-lowercase-hex>"' in text
    assert '"handoff_digest": "sha256:<64-lowercase-hex>"' in text
    assert "exact `plan_digest`" in text
    assert "missing or mismatched plan/handoff digest" in text
    assert "never reuse an old completed `task-handoff`" in text
    assert '`halted_at: "initial-handoff"` is a validation pseudo-stage' in text
    assert "`handoff_digest: null`" in text
    assert "`completed: []`" in text
    assert "exact unique prefix of the mode's stage list" in text
    assert ".plan-expedite-state.stale-<timestamp>" in text


def test_run_directory_prefers_the_nearest_nested_project_marker() -> None:
    text = CORE.read_text(encoding="utf-8")

    assert "The nearest marked\nancestor is authoritative" in text
    assert "a marked containing repository never outranks a nearer nested\nproject marker" in text
    assert "Prefer the captured\ninvocation directory" not in text


def test_next_action_file_has_one_locked_cross_skill_contract() -> None:
    plan = CORE.read_text(encoding="utf-8")
    handoff = TASK_HANDOFF.read_text(encoding="utf-8")
    wrap = SESSION_WRAP.read_text(encoding="utf-8")

    for text in (plan, handoff):
        assert "task-handoff-next-action-v1" in text
        assert '"run_directory"' in text
        assert '"preview"' in text
        assert '"goal"' in text
        assert '"action"' in text

    assert "--next-action-file <absolute-temp-json>" in plan
    assert "--next-action-file <absolute-json-path>" in handoff
    assert "<!-- task-handoff-next-action-v1 -->" in handoff
    assert "<!-- /task-handoff-next-action-v1 -->" in handoff
    assert "Digest: sha256:<64-lowercase-hex>" in handoff
    assert "Preview command:" in handoff
    assert "Action command pair:" in handoff
    assert "outside the Git worktree" in handoff
    assert "Locked Next Action bundle" in wrap
    assert "recompute the task-handoff NUL-framed SHA-256" in wrap
    assert "Preview (run in <absolute run directory>)" in wrap
    assert "Start build (run in <absolute run directory>)" in wrap
    assert "full-string regex match `^/goal" in handoff
    assert "never a substring\nor search match" in handoff


def test_locked_next_action_shape_matches_shared_state_schema() -> None:
    handoff = TASK_HANDOFF.read_text(encoding="utf-8")
    schema = TASK_STATE_SCHEMA.read_text(encoding="utf-8")

    locked_lines = (
        "<!-- task-handoff-next-action-v1 -->",
        "Digest: sha256:<64-lowercase-hex>",
        "Run directory: <canonical absolute directory>",
        "Preview command:",
        "<exact preview command or NONE>",
        "Action command pair:",
        "<exact goal command>",
        "<exact action command>",
        "<!-- /task-handoff-next-action-v1 -->",
    )
    for line in locked_lines:
        assert line in handoff
        assert line in schema

    assert "joined by one NUL byte" in handoff
    assert "joined by one NUL byte" in schema
    assert "preserve the entire envelope byte-for-byte" in schema
    assert "--next-action-file <absolute-json-path>" in schema


def test_preview_and_action_have_locked_observation_safe_templates() -> None:
    plan = CORE.read_text(encoding="utf-8")
    wrap = SESSION_WRAP.read_text(encoding="utf-8")

    assert "Run in: this window after /clear @ <absolute HANDOFF_RUN_DIR>" in plan
    assert "Continue only after the preview exits 0" in plan
    assert "The preview is rendered before" in plan
    assert "each command string remains byte-for-byte unchanged" in plan
    assert "goal/action step remains final" in wrap
    assert "Never output the source/envelope order goal-preview-action" in wrap
    assert "A digest-valid\n`task-handoff-next-action-v1` bundle is the explicit exception" in wrap


def test_legacy_inference_remains_available() -> None:
    text = CORE.read_text(encoding="utf-8")

    assert "If no explicit initial handoff is declared" in text
    assert "contiguous automated" in text
    assert "Omitting it preserves the legacy" in TASK_HANDOFF.read_text(encoding="utf-8")
