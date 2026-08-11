# Worktree hygiene

> **Vendored into skill-mesh.** This is a copy of the workspace reference document of the
> same name, vendored into the shared payload (`_shared`) so that the skill cores citing it
> resolve inside a host discovery root rather than against a workspace directory no
> consumer home has.
> Two adaptations apply throughout: citations to workspace documents that are **not** part
> of this payload are rendered as plain names rather than links (their targets do not ship
> here), and operator-specific identifiers, private issue/cron references and
> harness-configuration paths have been removed. The per-file sign-off and the full list of
> link dispositions are recorded in this repository's Step 66 decision record.

`/build-phase` and `/build-step` spawn git worktrees for parallel agent work. Seven landmines have each cost a session.

## 1. Fresh worktrees do not inherit deps

`git worktree add` creates a new working tree but does NOT copy `.venv/` (Windows: often binds the wrong Python) or `frontend/node_modules/` (gitignored). Before the first quality gate in a new worktree:

```bash
uv sync
# if the project has a frontend:
cd frontend && npm install && cd ..
```

Orchestrators (`/build-step`, `/build-step-tdd`) should run these upfront in the dev prompt's pre-flight.

## 2. `git worktree remove` fails when shell is inside it

On Windows, `git worktree remove <path>` returns `Permission denied` if:
- the shell's cwd is inside the worktree, or
- a Python process holds open `.pyc` handles to files in the worktree.

Git's registry usually unregisters the worktree anyway but the directory persists on disk. Always:

```bash
cd <project_root> && git worktree remove <worktree_path>
```

Chain via `&&` so the cwd change is in the same compound command. Use `--force` only if cleanup is otherwise blocked. After removal, verify both `git worktree list` and `ls <worktree_path>` show it gone.

## 3. Check unmerged commits before `git worktree remove --force`

A locked worktree means the creating tooling explicitly said "don't auto-clean me." Force-removing it (or `git branch -D` on its branch) can silently destroy unmerged work. Before destroying any worktree or non-default branch, run:

```bash
git stash list                                           # orphaned stashes in the worktree?
git worktree list                                        # registry state across repos
git merge-base --is-ancestor <branch> <main> && echo MERGED || echo NOT MERGED
```

If `NOT MERGED`, halt and surface the diff to the user — "looks abandoned" / "is locked" / "old timestamp" all admit false positives; the ancestor check is the only durable signal. Saved a `review-uat` autoresearch run from silent loss on 2026-05-13.

**Refinements (2026-06-03 dev/ cleanup — pruned ~16 worktrees + 18 branches; two false signals each nearly cost a wrong call):**

- **`--is-ancestor == MERGED` is positive proof** the branch is safe to delete. When it reports `NOT MERGED`, that is *not* proof of unique work — keep/surface, then verify with one of the checks below before assuming loss.
- **`git cherry` false-positives on empty-delta branches.** A branch whose tip tree equals its merge-base introduced nothing (or its work already landed), so there is no patch for `git cherry` / patch-id to match — it prints `+` (not-merged), a false alarm. Confirm "no unique content" with a tree check instead: `[ "$(git rev-parse <branch>^{tree})" = "$(git rev-parse "$(git merge-base <main> <branch>)^{tree}")" ]` true ⇒ safe to delete. (All 11 stray build-step branches in the 2026-06-03 cleanup were this case — `git cherry` said NOT MERGED, but they were merged ancestors with empty deltas.)
- **Every check above is about COMMITS — run `git -C <worktree> status --porcelain` too.** `--is-ancestor == MERGED` is positive proof only that the *branch* is safe; it says nothing about uncommitted working-tree state, and a stale worktree can hold unique work that was never committed. On 2026-08-10 `build-step-step7-1784733479` was a zero-unique-commit ancestor of master — MERGED by every check in this section — while its working tree held ~1,036 uncommitted lines (a `seed.py` rewrite plus 479 lines of tests) fixing two defects that had shipped broken. Following this section verbatim would have destroyed it. Commit or rescue any dirty state to its own branch BEFORE removing, and **push that branch** — a rescue commit that never leaves the machine is one `git branch -D` from being undone.
- **Squash-merged branches are not ancestors,** so `--is-ancestor` reports `NOT MERGED` even though the content landed. To positively confirm a squash-merge, collapse the branch's delta-from-merge-base into one commit and check its patch is in `<main>`: `git cherry <main> "$(git commit-tree <branch>^{tree} -p "$(git merge-base <main> <branch>)" -m _)"` — a leading `-` means merged.

## 4. Stale `worktree_*` dirs accumulate at the workspace root

`/build-phase` and `/build-step` create dirs like `dev/worktree_step-23-...-<epoch>/`. When `git worktree remove` fails on Windows (file locks, AV holding `.pyc` handles), the registry entry is cleaned but the on-disk directory persists — orphaned. They quietly cost gigabytes (one toybox-step-23 husk was 512 MB of `node_modules` alone). Periodic hygiene at the dev/ root:

```bash
ls -d worktree_* 2>/dev/null | head            # see what's there
# for each one: check the git registry first
cat <wt>/.git 2>/dev/null                      # points to /repo/.git/worktrees/<name>?
# if the registry entry no longer exists, the dir is orphaned and safe to rm -rf
```

`.gitignore` should include `worktree_*/` and `.claude/worktrees/` so orphans don't pollute `git status`.

## 5. `git merge` is a silent no-op when run in the wrong worktree

If a worktree's HEAD is already the merge target (e.g., you're sitting on `master` in the worktree), `git merge <feature>` becomes a no-op and prints nothing useful. Use `git -C <abs-path-to-correct-worktree> merge <feature>` or `cd <correct-worktree> && git merge <feature>` to be unambiguous.

## 6. Shared-file merges across steps

`/build-phase` steps that all touch the same file (e.g., a routes module, a config file) overwrite each other on merge if the dev agent rewrote the whole file rather than applying a surgical edit. After each step's merge, re-run the project's test gate before launching the next step.

## 7. Stale feature branches: merge default before validating

For branches >1 day old or >3 commits behind the default branch, `git merge main` (or rebase) before running any test gate. Otherwise test failures are ambiguous between real regressions and drift — and the ambiguous failures look exactly like the real-regression ones.

```bash
git log --oneline <branch>..main | wc -l    # >3 lines → stale
git merge main                              # or rebase, project preference
```

Alpha4Gate Phase A: 2-day-old `feat/lstm-kl-imitation` showed 7 "regressions" that evaporated after a conflict-free merge.

Exception: if catching drift is the *point* of the validation, run tests before AND after the merge to separate the two failure modes.

## See also

- `windows-shell.md` for the `git -C` rationale and the Bash-tool cwd unreliability that compounds this.
