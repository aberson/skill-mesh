from pathlib import Path
import re
import shutil
import subprocess
import textwrap


ROOT = Path(__file__).resolve().parents[2]
BUILD_PHASE = (ROOT / "skills" / "build-phase" / "core.md").read_text(encoding="utf-8")
BUILD_STEP = (ROOT / "skills" / "build-step" / "core.md").read_text(encoding="utf-8")


def _bash_executable() -> str:
    candidates = [
        Path(r"C:\Program Files\Git\bin\bash.exe"),
        Path(r"C:\Program Files\Git\usr\bin\bash.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    executable = shutil.which("bash")
    assert executable, "Bash is required to execute the build adapter contracts"
    return executable


def _bash_function(contract: str, name: str) -> str:
    start = contract.index(f"{name}() {{")
    end = contract.index("\n}\n", start) + len("\n}\n")
    return contract[start:end]


def _bash_block_after(contract: str, marker: str) -> str:
    marker_offset = contract.index(marker)
    match = re.search(
        r"^[ \t]*```bash\r?\n(.*?)^[ \t]*```[ \t]*$",
        contract[marker_offset:],
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match
    return textwrap.dedent(match.group(1))


def _run_bash(script: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_bash_executable(), "-s"],
        cwd=cwd,
        input=script,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def test_both_build_contracts_distinguish_project_and_git_roots() -> None:
    for contract in (BUILD_PHASE, BUILD_STEP):
        assert 'PROJECT_ROOT="$(pwd -P)"' in contract
        assert 'GIT_ROOT="$(git -C "$PROJECT_ROOT" rev-parse --show-toplevel)"' in contract
        assert 'PROJECT_PREFIX="."' in contract
        assert 'PROJECT_PREFIX="${PROJECT_ROOT#"$GIT_ROOT"/}"' in contract
        assert 'PROJECT_PATHSPEC="$PROJECT_PREFIX"' in contract
        assert "PROJECT_SCOPE_HALT" in contract


def test_build_step_enters_the_prefixed_project_in_an_external_child_worktree() -> None:
    assert 'WORKTREE_ROOT="$(dirname "$GIT_ROOT")/worktree_$BRANCH"' in BUILD_STEP
    assert 'git -C "$GIT_ROOT" worktree add "$WORKTREE_ROOT"' in BUILD_STEP
    assert 'WORKTREE_PROJECT="$WORKTREE_ROOT/$PROJECT_PREFIX"' in BUILD_STEP
    assert 'cd "$WORKTREE_PROJECT"' in BUILD_STEP
    assert 'cd "$WORKTREE_PROJECT"  # or project-scoped container workspace' in BUILD_STEP
    assert 'cd "$PROJECT_ROOT"' in BUILD_STEP
    assert "list_all_child_changes" in BUILD_STEP
    assert "list_project_child_changes" in BUILD_STEP
    assert "audit_child_scope" in BUILD_STEP
    assert 'git -C "$WORKTREE_ROOT" diff "$WORKTREE_BASELINE" --name-only -z -- "$PROJECT_PATHSPEC"' in BUILD_STEP
    assert 'git -C "$WORKTREE_ROOT" diff HEAD --name-only' not in BUILD_STEP
    assert 'git -C "$WORKTREE_ROOT" ls-files --others --exclude-standard -z' in BUILD_STEP
    assert 'require_project_path "$f" || exit 2' in BUILD_STEP

    # These aliases encoded the old and unsafe project-root-equals-Git-root assumption.
    assert 'PROJECT="$(pwd)"' not in BUILD_STEP
    assert 'WORKTREE="../worktree_$BRANCH"' not in BUILD_STEP
    assert 'cd "$WORKTREE"' not in BUILD_STEP


def test_git_mutations_and_checkpoint_are_project_scoped() -> None:
    for contract in (BUILD_PHASE, BUILD_STEP):
        assert 'status --porcelain -- "$PROJECT_PATHSPEC"' in contract
        assert 'stash push --include-untracked' in contract
        assert '-- "$PROJECT_PATHSPEC"' in contract
        assert "\ngit stash pop" not in contract

    assert 'git -C "$GIT_ROOT" add --all -- "$PROJECT_PATHSPEC"' in BUILD_PHASE
    assert 'git -C "$GIT_ROOT" commit --only' in BUILD_PHASE
    assert 'diff --cached --name-only -z -- "$PROJECT_PATHSPEC"' in BUILD_PHASE
    assert "PROJECT_STASH_OID" in BUILD_STEP
    assert "PHASE_STASH_OID" in BUILD_PHASE

    # The old commands swept unrelated files from a containing repository.
    combined = BUILD_PHASE + BUILD_STEP
    assert "git add -A" not in combined
    assert "git status --porcelain\n" not in combined
    assert 'git stash push -m "build-step pre-run state" --include-untracked' not in combined


def test_windows_conditions_use_explicit_git_bash_from_project_root() -> None:
    assert "C:\\Program Files\\Git\\bin\\bash.exe" in BUILD_PHASE
    assert "Push-Location -LiteralPath $PROJECT_ROOT" in BUILD_PHASE
    assert "& $conditionShell -c $condition" in BUILD_PHASE
    assert 'bash -c "<expr>"' not in BUILD_PHASE
    assert "never resolve `bash`, `bash.exe`, or" in BUILD_PHASE


def test_greenfield_baseline_is_zero_only_until_project_gates_exist() -> None:
    assert "NO_BASELINE (greenfield)" in BUILD_PHASE
    assert "BASELINE_TEST_COUNT=0" in BUILD_PHASE
    assert "[ ! -e pyproject.toml ] && [ ! -d src ] && [ ! -d tests ]" in BUILD_PHASE
    assert "one-time bootstrap state, not a waiver" in BUILD_PHASE
    assert "all applicable gates are mandatory" in BUILD_PHASE
    assert 'cd "$PROJECT_ROOT"\n<typecheck_command> && <lint_command> && <test_command>' in BUILD_PHASE
    assert "NO_BASELINE (greenfield)" in BUILD_STEP
    assert "count `0` only when Python is detected" in BUILD_STEP
    assert "redetect\n   the commands inside `WORKTREE_PROJECT`" in BUILD_STEP
    assert "newly applicable gate that cannot" in BUILD_STEP


def test_every_reviewer_dispatch_is_pinned_to_worktree_project() -> None:
    assert "Immediately before the parallel reviewer tool calls" in BUILD_STEP
    assert "Immediately before the parallel runtime-reviewer tool calls" in BUILD_STEP
    assert "Immediately before the single eight-call dispatch" in BUILD_STEP
    assert 'cd "$WORKTREE_PROJECT"\n[ "$(pwd -P)" = "$(cd "$WORKTREE_PROJECT" && pwd -P)" ]' in BUILD_STEP
    assert BUILD_STEP.count("working-directory field") >= 4
    assert "$WORKTREE_PROJECT/.build-step/review-deep" in BUILD_STEP


def test_stash_transactions_share_a_git_root_lock_and_never_steal_stale_lock() -> None:
    for contract, owner_prefix in (
        (BUILD_PHASE, "skill-mesh-build-phase-"),
        (BUILD_STEP, "skill-mesh-build-step-"),
    ):
        assert owner_prefix in contract
        assert 'STASH_LOCK_DIR="$GIT_COMMON_DIR/skill-mesh-stash.lock"' in contract
        assert "acquire_stash_lock()" in contract
        assert "release_stash_lock()" in contract
        assert "marker=%s pid=%s host=%s started=%s" in contract
        assert "retained without stealing" in contract
        assert "never steal or recursively delete" in contract
        assert "if ! acquire_stash_lock; then" in contract
        assert "release_stash_lock ||" in contract
        assert "stash apply --index" in contract
        assert "stash drop" in contract


def test_stash_guard_failures_finalize_and_cannot_fall_through(tmp_path: Path) -> None:
    cases = (
        (
            _bash_block_after(BUILD_PHASE, "4. **Check or stash only `PROJECT_PATHSPEC`"),
            "restore_phase_stash() { printf phase-restore > finalized; }\n"
            + _bash_function(BUILD_PHASE, "finalize_phase_state")
            + _bash_function(BUILD_PHASE, "phase_scope_halt"),
            "phase-restore",
        ),
        (
            _bash_block_after(BUILD_STEP, "4. **Stash only uncommitted project changes"),
            "rollback_ui_preview() { printf rollback > finalized; }\n"
            "restore_project_stash() { printf -- -stash >> finalized; }\n"
            + _bash_function(BUILD_STEP, "finalize_project_state")
            + _bash_function(BUILD_STEP, "project_scope_halt"),
            "rollback-stash",
        ),
    )
    for index, (block, finalizer_functions, expected_finalizer) in enumerate(cases):
        for failure_mode in ("lock", "push"):
            case_dir = tmp_path / f"case-{index}-{failure_mode}"
            case_dir.mkdir()
            script = f"""
set +e
FAILURE_MODE={failure_mode!r}
GIT_ROOT=.
PROJECT_PATHSPEC=.
PROJECT_PREFIX=.
acquire_stash_lock() {{ [ "$FAILURE_MODE" != lock ]; }}
release_stash_lock() {{ return 0; }}
git() {{
  if [ "$1" = -C ] && [ "$3" = status ]; then printf ' M product.txt\\n'; return 0; fi
  if [ "$1" = -C ] && [ "$3" = stash ] && [ "$4" = push ]; then
    [ "$FAILURE_MODE" != push ]; return $?
  fi
  return 1
}}
{finalizer_functions}
(
{textwrap.indent(block, '  ')}
  printf fell-through > fell-through
)
rc=$?
[ "$rc" -eq 2 ] || exit 20
[ -f finalized ] || exit 21
[ "$(cat finalized)" = {expected_finalizer!r} ] || exit 23
[ ! -e fell-through ] || exit 22
"""
            result = _run_bash(script, case_dir)
            assert result.returncode == 0, result.stderr + result.stdout


def test_overlap_is_nul_safe_for_newline_paths_in_both_contracts(tmp_path: Path) -> None:
    variants = (
        (
            _bash_function(BUILD_PHASE, "write_project_overlap_set"),
            "write_project_overlap_set",
            "list_project_changes_since",
        ),
        (
            _bash_function(BUILD_STEP, "write_main_overlap_set"),
            "write_main_overlap_set",
            "list_main_project_changes_since",
        ),
    )
    assert 'diff "$CHANGE_BASE" --name-only -z' in BUILD_PHASE
    assert 'diff "$CHANGE_BASE" --name-only -z' in BUILD_STEP
    for index, (overlap_function, call_name, list_name) in enumerate(variants):
        repo = tmp_path / f"overlap-{index}"
        repo.mkdir()
        script = f"""
set -eu
git init -q
git config user.email contract@example.invalid
git config user.name contract-test
EMPTY_TREE=$(git mktree </dev/null)
BASELINE=$(git commit-tree "$EMPTY_TREE" -m baseline)
UPSTREAM_BLOB=$(printf upstream | git hash-object -w --stdin)
UPSTREAM_TREE=$(printf '100644 blob %s\\tline\\nbreak.txt\\0' "$UPSTREAM_BLOB" | git mktree -z)
UPSTREAM=$(git commit-tree "$UPSTREAM_TREE" -p "$BASELINE" -m upstream)
LOCAL_BLOB=$(printf local | git hash-object -w --stdin)
LOCAL_TREE=$(printf '100644 blob %s\\tline\\nbreak.txt\\0' "$LOCAL_BLOB" | git mktree -z)
LOCAL=$(git commit-tree "$LOCAL_TREE" -p "$BASELINE" -m local)
GIT_ROOT="$(pwd -P)"
PROJECT_PATHSPEC=.
{list_name}() {{ git -C "$GIT_ROOT" diff --name-only -z "$BASELINE..$LOCAL"; }}
{overlap_function}
{call_name} "$BASELINE..$UPSTREAM" "$BASELINE" overlap.z
printf 'line\\nbreak.txt\\0' > expected.z
cmp expected.z overlap.z
"""
        result = _run_bash(script, repo)
        assert result.returncode == 0, result.stderr + result.stdout


def test_orchestrator_artifacts_are_audited_but_not_payload_without_ignore(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "artifact-filter"
    repo.mkdir()
    functions = "\n".join(
        _bash_function(BUILD_STEP, name)
        for name in (
            "require_project_path",
            "list_all_child_changes",
            "list_project_child_changes",
            "list_project_payload_changes",
        )
    )
    script = f"""
set -eu
git init -q
git config user.email contract@example.invalid
git config user.name contract-test
printf baseline > baseline.txt
git add baseline.txt
git commit -qm baseline
WORKTREE_ROOT="$(pwd -P)"
WORKTREE_BASELINE=$(git rev-parse HEAD)
PROJECT_PREFIX=.
PROJECT_PATHSPEC=.
project_scope_halt() {{ return 2; }}
{functions}
mkdir -p .build-step .ui-review-evidence src
printf gate > .build-step/gate.log
printf image > .ui-review-evidence/view.png
printf product > src/product.txt
printf spaced > 'src/product with space.txt'
list_all_child_changes > audited.z
list_project_payload_changes > payload.z
"""
    result = _run_bash(script, repo)
    assert result.returncode == 0, result.stderr + result.stdout
    audited = (repo / "audited.z").read_bytes().split(b"\0")[:-1]
    payload = (repo / "payload.z").read_bytes().split(b"\0")[:-1]
    assert b".build-step/gate.log" in audited
    assert b".ui-review-evidence/view.png" in audited
    assert b".build-step/gate.log" not in payload
    assert b".ui-review-evidence/view.png" not in payload
    assert b"src/product.txt" in payload
    assert b"src/product with space.txt" in payload


def test_ui_preview_snapshot_exactly_restores_all_original_states(tmp_path: Path) -> None:
    repo = tmp_path / "ui-rollback"
    repo.mkdir()
    functions = "\n".join(
        _bash_function(BUILD_STEP, name)
        for name in (
            "discard_ui_snapshot",
            "ui_preview_path_in_scope",
            "snapshot_ui_preview",
            "rollback_ui_preview",
            "finalize_project_state",
        )
    )
    script = f"""
set -eu
git init -q
git config user.email contract@example.invalid
git config user.name contract-test
printf tracked-original > tracked-present.txt
printf deleted-original > tracked-deleted.txt
git add tracked-present.txt tracked-deleted.txt
git commit -qm baseline
rm tracked-deleted.txt
printf untracked-original > untracked-present.txt
GIT_ROOT="$(pwd -P)"
WORKTREE_ROOT="$(dirname "$GIT_ROOT")/unrelated-child"
PROJECT_PREFIX=.
UI_PREVIEW_ACTIVE=false
UI_PREVIEW_SNAPSHOT_DIR=
UI_PREVIEW_MANIFEST=
UI_PREVIEW_PAYLOAD=
list_project_payload_changes() {{
  printf '%s\\0' tracked-present.txt tracked-deleted.txt untracked-present.txt absent.txt
}}
restore_project_stash() {{ printf stash >> finalizer-order; }}
{functions}
snapshot_ui_preview
cp "$UI_PREVIEW_MANIFEST" manifest-copy.z
printf preview > tracked-present.txt
printf preview > tracked-deleted.txt
printf preview > untracked-present.txt
printf preview > absent.txt
rollback_ui_preview
[ "$(cat tracked-present.txt)" = tracked-original ]
[ ! -e tracked-deleted.txt ]
[ "$(cat untracked-present.txt)" = untracked-original ]
[ ! -e absent.txt ]
[ "$UI_PREVIEW_ACTIVE" = false ]
[ -z "$UI_PREVIEW_SNAPSHOT_DIR" ]
rollback_ui_preview
rollback_ui_preview() {{ printf rollback >> finalizer-order; }}
: > finalizer-order
finalize_project_state
[ "$(cat finalizer-order)" = rollbackstash ]
"""
    result = _run_bash(script, repo)
    assert result.returncode == 0, result.stderr + result.stdout
    records = (repo / "manifest-copy.z").read_bytes().split(b"\0")
    states = records[0:-1:3]
    assert states == [
        b"tracked-present",
        b"tracked-deleted",
        b"untracked-present",
        b"absent",
    ]


def test_ui_rollback_precedes_retry_landing_and_stash_restore() -> None:
    step_five = BUILD_STEP.index("7. **Roll back the preview")
    ship_gate = BUILD_STEP.index("### Step 5.5")
    step_eight = BUILD_STEP.index("### Step 8 -- On PASS")
    landing_audit = BUILD_STEP.index("audit_child_scope || exit 2", step_eight)
    landing_rollback = BUILD_STEP.index("if ! rollback_ui_preview", step_eight)
    step_nine = BUILD_STEP.index("### Step 9 -- On NEEDS WORK")
    retry = BUILD_STEP.index("Go to Step 2 with all findings", step_nine)
    retry_rollback = BUILD_STEP.index("if ! rollback_ui_preview", step_nine)

    assert step_five < ship_gate
    assert landing_rollback < landing_audit
    assert retry_rollback < retry
    assert "git -C \"$GIT_ROOT\" restore --worktree" not in BUILD_STEP
    assert "copied-files.txt" not in BUILD_STEP
    finalizer = _bash_function(BUILD_STEP, "finalize_project_state")
    assert finalizer.index("rollback_ui_preview") < finalizer.index("restore_project_stash")
