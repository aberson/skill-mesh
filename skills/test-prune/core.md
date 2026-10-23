# NOTE: This is the canonical provider-independent contract. All provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/test-prune/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# test-prune

Audit and trim a test suite. Find tests that duplicate other coverage, test library behavior, or only assert that a mock was called. Verify before removing: a test cannot be declared redundant without showing the other test that covers the same behavior.

Run this skill when:
- A project has shipped several build phases and the test suite has grown faster than the source tree.
- Test runs are slow and a chunk of the slowness is integration tests that re-cover unit-test scenarios.
- The user says "prune the tests", "clean up the test suite", or "the integration tests are redundant".

This skill does not touch application code, README, plan docs, or git state. It edits only the project's declared test directories, runs bounded quality gates, and reports. Read-only git inspection is allowed only for the recoverability checks below.

---

## Phase 1 — Identify candidates

Always dispatch this phase as parallel Explore agents; never replace it with a serial in-session scan. Launch 1–3 read-only, fresh-context flagging arms that never edit, move, or write a file. Each arm explicitly requests the `sonnet` capability tier. Resolve that tier through `config/model-tier-map.json` and do not let an arm silently inherit the invoking session's tier. When the map has no peer for a host, the provider wrapper may select the closest native capability and must record the model that actually ran; if the host cannot provide the required isolation or selection, return `required_tool_missing`.

Scale the arms to the number of test files: one for 5 or fewer files, two for 6–20, and three for more than 20. Divide every file under the project's declared test directories among them, with no file omitted or scanned by more than one arm. Flag:

1. **Redundant tests** — the same behavior is tested in multiple files, especially when an integration test duplicates a unit test.
2. **Trivial tests** — a test checks library behavior such as dictionary assignment, dataclass defaults, or directory creation rather than project behavior.
3. **Mock theater** — a test only asserts a mock call and exercises no real project behavior.
4. **Duplicate coverage** — an entire integration file re-tests scenarios already covered elsewhere.

Return one list of `(file:line, category, brief)` tuples per arm, not full transcripts. Record each arm's actual model with its list.

---

## Phase 2 — Verify and bind authority

For every flagged test, determine whether it is the only coverage for the behavior. Use repository search to find the function or class under test elsewhere. Cite the command and match count for every search.

Every delete verdict needs category-specific evidence:

- `redundant`: cite the covering test's file and line.
- `trivial`: quote the assertion that tests no project behavior.
- `mock theater`: quote the mock-only assertion and explain why no real logic is under test.
- `duplicate coverage`: cite the covering file and line for every test the file contains.

Apply these false-positive checks:

- Relocate rather than delete a test that is the only coverage for project behavior.
- Keep error-handling paths tested only through mocks when they prevent a crash regression.
- Keep wiring tests that exercise glue behavior absent from the unit tests.

### Stable row identity

Give each row a stable test identifier, such as a pytest node id or `file::function`. In the Evidence cell include that identifier and a definition hash: the first 12 hexadecimal digits of SHA-256 over the exact on-disk byte span from the test's first decorator or definition line through the last line of its body. Record how the span was extracted so the identical extraction can be repeated at the mutation boundary. A line number is only a locator and never authorizes mutation.

### Whole-file actions

List every proposed whole-file delete or move as a separate item below the table. This includes a duplicate-coverage file and a file that would contain only imports, comments, or a module docstring after its confirmed rows leave. Include the path, action, reason, SHA-256 of the complete current file bytes, ordered prerequisite row identifiers, and the expected complete-file SHA-256 immediately before the whole-file action after those rows run. If any helper, fixture, constant, setup, or other definition would remain, never delete the file; remove only confirmed rows. A whole-file action runs only when it was listed before confirmation.

For every proposed action, compute and bind before confirmation the expected complete-file preimage and postimage for every path it touches; an absent relocation destination has the explicit preimage `absent`, and a deleted path has the explicit postimage `absent`. Where actions overlap on a path, also build one deterministic dependency order whose next preimage is the preceding authorized postimage. Bind those hashes and dependencies to the listed action. This rule applies equally to a standalone row deletion, each side of a relocation, and an overlapping row/whole-file chain. It authorizes only the displayed transformation and never turns row authority into whole-file authority.

### Recoverability precheck

Before printing the table, collect every existing path and proposed destination touched by every possible row verdict, including `keep` rows that the operator could change, relocation targets, and whole-file items. Inspect git read-only and never create or change git state.

An existing path is `recoverable` only when all three conditions hold:

1. `git ls-files --error-unmatch -- <path>` exits 0.
2. If the project root contains its own `.git`, `git -C <project-root> rev-parse --show-toplevel` resolves to that project root.
3. From the project root, `git --no-optional-locks status --porcelain --ignored -uall -- <path>` prints nothing.

A relocation target inside a declared test directory that does not yet exist is `created by this run`; its restore action is deletion. Every other path is `unrecoverable`, including an untracked, ignored, locally modified, outside-work-tree, or differently rooted path. Classify every collected path. Print unrecoverable paths below the table rather than adding a fifth column. This printed list is the pre-confirmation unrecoverable disclosure set; naming a path later does not add it to that set.

### Operator gate

Print the triage table before mutation:

| File:line | Category | Verdict | Evidence |
|---|---|---|---|
| `tests/test_foo.py:42` | redundant | delete | `tests/test_foo.py::test_x #9a12bc34de56`; duplicated by `tests/unit/test_foo.py:80` |
| `tests/test_bar.py:15` | trivial | delete | `tests/test_bar.py::test_dict #123456789abc`; asserts `d["k"] == "v"` after assignment |
| `tests/integration/test_baz.py:120` | redundant | relocate | `tests/integration/test_baz.py::test_compute #abcdef123456`; only coverage for `baz.compute()` |
| `tests/test_qux.py:30` | mock theater | **keep** | `tests/test_qux.py::test_dispatch #654321abcdef`; real post-condition is asserted |

Then show the whole-file items, unrecoverable paths, commands proposed for the baseline and post-prune gates, and the exact confirmation rule. Stop and wait for explicit confirmation. The operator owns every verdict.

A bare confirmation authorizes only listed rows and whole-file items whose paths are all `recoverable` or `created by this run`. An action touching an `unrecoverable` path runs only when that exact path was printed in the pre-confirmation unrecoverable disclosure set **and** the confirmation names it. A path that becomes unrecoverable after confirmation was not disclosed in that state and must be skipped even when its path was named. Operator verdict changes are requests to regenerate the affected rows, ordered expected-state chain, path classifications, and disclosures, then wait for fresh confirmation; never execute a changed verdict against the old table or infer authority for a new path or unlisted whole-file action.

---

## Phase 3 — Execute cleanup

After confirmation:

0. **Baseline.** Discover every declared test suite from project instructions and test configuration, including instruction-file `## Commands`, test roots such as `pyproject.toml` `testpaths`, and package test scripts. Inventory configured test, lint, and typecheck gates separately from genuinely unconfigured gate types. Run every configured gate, subject to the bounded-command and check-only rules below, and record per-suite results and collected-test counts. These are the report's `Before` values. Mutate nothing unless every configured baseline gate actually completed and passed. A skipped, unrun, unavailable, indeterminate, incomplete, timed-out, unsafe-writing, prerequisite-blocked, red, or erroring configured gate halts before cleanup; report its observed state and stop. A genuinely unconfigured lint or typecheck gate is recorded explicitly and does not prevent a green baseline.
1. **Mutation-boundary recheck.** Immediately before a row or whole-file item runs, repeat the recoverability checks on every path it touches that this run has not yet written. An absent destination stays `created by this run`. Once this run writes a path, keep the result from its last mutation-boundary recheck so the run's own edit does not reclassify it. A newly reached path, including one introduced by an operator-changed verdict, must be classified now.
2. **Recheck current bytes.** Before each action, require every touched path's complete current bytes to equal that action's confirmed expected preimage (or remain absent for an `absent` preimage). Re-resolve every row by its identifier and recompute its definition hash with the same byte-span extraction. For a whole-file item, require the expected pre-cleanup hash produced by its confirmed prerequisite chain, not the original pre-run hash. On a missing identifier, definition mismatch, complete-preimage mismatch, unlisted whole-file action, newly unrecoverable path, or an `unrecoverable` path that was not both disclosed as unrecoverable and named by the confirmation, skip that action and report the exact reason. Recoverable and `created by this run` paths remain eligible under bare confirmation when their other checks pass. Never refresh an expected hash from current bytes or fall back to a line number.
3. **Relocate first.** Move confirmed sole-coverage tests to the confirmed destination under a declared test directory.
4. **Delete second.** Delete confirmed rows of any category only when they carry the required category-specific evidence. After every action, require every touched path to equal its confirmed expected postimage, including required absence after a deletion, before any dependent action. Delete or move a whole file only through its separately confirmed whole-file item. An authorized relocation and deletion chain may therefore reach its confirmed whole-file cleanup; any unrelated or incorrectly produced byte stops the remaining chain.
5. **Run the full declared test suite.** Run every declared test root or suite, not only the root that held the pruned tests. Adapt to the project (`uv run pytest`, `npm test`, `pnpm test`, and similar). Name every suite that ran. The after-count must equal the baseline count minus deleted tests; a relocated test counts once. Any unexplained count difference is a failure.
6. **Run declared lint and typecheck gates.** Run each in check-only mode. Inspect the declared command first: never pass `--fix`, run a formatter-writing mode, or accept any command whose effects cannot be determined. Use the tool's direct check-only form when known; otherwise report `lint not run (declared command writes)` or the corresponding typecheck result. A gate that writes outside the declared test directories breaches scope and halts the run.

Only test, lint, and typecheck runners are allowed. Never run a start, serve, build, migrate, data-reset, or prerequisite-start command. Do not start a server or database. Report a suite that needs one as `not run (prerequisite)`. If the full suite exceeds an applicable time limit, name the suites that ran and those that did not; an unnamed subset count is not gate evidence.

If a post-prune gate fails, halt and identify the deletion or relocation most likely related to it. Do not fix forward, revert, reset, clean, or alter the index. For each touched path proven recoverable at its mutation-boundary recheck, name the operator's restore command (`git restore -- <path>`). For a path created by this run, name its deletion. For every other path, state that no restore exists. Preserve and report the actual partial tree state.

---

## Phase 4 — Report

Use `test-prune complete.` only when every authorized action was resolved and all post-prune gates ran and passed. Otherwise title the report `test-prune halted.` and state every skipped, failed, or unrun item.

```text
test-prune complete.

Before: X test files, Y tests
After:  X' test files, Y' tests
Removed: N tests (K files deleted)
Relocated: M tests (J files moved)

Quality gates: Y'/Y' tests · 0 type errors · 0 lint violations
```

The template shows a run whose tests, typecheck, and lint all ran clean. State only results observed in this run and name the suites that ran. Name an absent gate (`typecheck not configured`, `lint not configured`), an unrun gate (`not run (prerequisite)` or the declared-writing form above), and a failing gate by its actual result. Never write `0` for a gate that did not run. Report every skipped action and the final status of each touched path.

---

## What not to do

- Do not remove coverage without the Phase 2 evidence.
- Do not rewrite application code; this skill is test-directory-only.
- Do not update README, plan docs, memory, manifests, or shared resources.
- Do not commit, push, create issues, publish externally, or change git state.
- Do not auto-execute: the triage table and whole-file list are the authority gate.
- Do not describe skipped, unrun, red, or prerequisite-blocked gates as passing.

---

## See also

- [`/repo-update`](../repo-update/core.md) — end-of-phase commit and push, when the operator later wants the cleanup landed.
- `.claude/rules/code-quality.md` § "New components require an integration test through the production caller" — context for identifying load-bearing tests.
