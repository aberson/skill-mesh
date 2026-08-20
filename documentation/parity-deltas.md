# Codex parity delta log

The running record of Claude-vs-Codex behavioral differences for the skill-mesh catalog,
and the place the operator records each M-step verdict.

Owner: Phase CP of `documentation/codex-parity-delivery-plan.md`. Scaffolded at Step 4;
filled in by the operator during M1-M4.

**This file is load-bearing, not documentation.** Phase CP Steps 6, 7, 8 and 10 are
`Type: conditional`, and their predicate is an existence check on this file followed by a
case-insensitive `grep` for the M1 line carrying its passing verdict. The plan owns the
exact predicate text; it is deliberately NOT quoted here, because a verbatim copy would
put the very token the `grep` looks for into this file and release all four steps the
moment the scaffold landed. Read it from the `**Condition:**` field of Steps 6, 7, 8 and
10 in `documentation/codex-parity-delivery-plan.md`.

Two consequences, both deliberate:

- The file must EXIST from Step 4 onward. A bare `grep` against a missing file exits `2`,
  which build-phase's conditional ABI treats as a HALT rather than a skip; the predicate's
  leading existence test turns the missing-file case into a clean `1`, but only if that
  guard is kept.
- The verdict token must NOT be written until the verdict is real. Editing the M1 line
  below to its passing value is what releases four steps to run; doing it "to unblock the
  queue" runs them on no evidence. Leave it `PENDING` until a real Codex session says
  otherwise.
- Same rule for anything ELSE written into this file: never spell the M1 line's passing
  form in prose, an example, or a quoted command. Describe it; do not reproduce it.

---

## M-step verdicts

Verdict values: `PENDING` (not yet run) | `PASS` | `FAIL - <reason>`. One line each, in
this exact `M<n>: <verdict>` shape - the cohort predicate greps it case-insensitively.

- M1: PASS
- M2: PASS
- M3: PENDING
- M4: PENDING

## Run environment

Recorded per M-step run, per D-CP7: parity targets the **installed** Codex CLI, not the
0.147.0 pin the parked-launcher research was based on. Every format assumption below
(frontmatter shape, `.agents/skills` placement, catalog budgets) came from that pinned
research and is re-verified against whatever is actually installed.

| M-step | Date (UTC) | Codex CLI version | Copilot CLI present | Notes |
|---|---|---|---|---|
| M1 | 2026-08-18 | codex-cli 0.147.0 | yes (1.0.77) | Both versions coincide with the prior research pins (the 0.147.0 format research; the Step 43/45 Copilot proofs), so every format assumption is confirmed on-pin and remains unproven on newer versions. |
| M2 | 2026-08-19 | codex-cli 0.147.0 | yes (**1.0.80**) | Codex holds the 0.147.0 pin, so its format assumptions stay confirmed on-pin. Copilot has moved OFF the 1.0.77 pin the D-CP6 `accept` was evidenced against; per the M1 disposition note that upgrade forces a re-check, which was run — see "M2 D-CP6 re-check" below. **Session mode differs from M1:** M2 was driven through `codex exec` (non-interactive, multi-turn via `codex exec resume`), M1 was interactive. Mode is a live variable between the two runs and any mode-sensitive observation must say so. |
| M3 | | | | |
| M4 | | | | |

## M1 checks

Check rows for the Step M1 table in `documentation/codex-parity-delivery-plan.md`,
observed 2026-08-18 on codex-cli 0.147.0 against the pilot toy project
(code-stencil). Each Outcome grades one check row only; the step verdict lives
solely in the M-step verdicts list above.

| Check | Observed | Outcome |
|---|---|---|
| Probe resolves effective home | single home resolved from USERPROFILE, env_agreement=single (HOME unset, so no dual-source disagreement is possible); discovery root and ledger both absent before install | pass |
| All 5 pilot skills listed by Codex | task-handoff, user-orient, lesson-harvest, plan-review, session-wrap all enumerated with complete-sentence descriptions alongside the host built-ins; no truncation (budget holds); descriptions were paraphrased, not echoed - see Deltas; the session header counted 11 skills with 10 visible in the capture, the unresolved entry presumed a built-in since all five of ours are accounted for | pass |
| Invoking task-handoff | SKILL.md loaded and core followed: "Pick up here" rollup with route line, verified git state, handoff-prompt.md + current.md + session file written under the toy project's .claude/task-state/ (self-gitignored - the portable record, as designed), memory-check advisory rendered | pass |
| Invoking plan-review | verdict rendered via the single-context fallback: greenfield mode declared with explicit carve-outs, all severity sections + resolved decisions + readiness line present in the task-state plan-review-report.md; autofix rewrote the toy plan into full step-contract shape with correctly ISO-dated markers on all 8 steps (fix-count line misreported - see Deltas) | pass |
| Writes confined | probe before / inspect after: only .agents/skills (11 files: 5 managed portable packages + the _shared payload) and the ledger appeared; ledger valid, providers=[codex], 0 unrecognized; all 3 inspect warnings describe pre-existing claude-root state untouched by this install | pass |
| Copilot shared-root visibility | recorded: Copilot CLI 1.0.77 enumerates the codex packages from the shared root (the Deltas rows and construction note 3's outcome carry the detail and the accept reason) | recorded |
| Codex CLI version | codex-cli 0.147.0, in the Run environment table; coincides with the research pin, so format assumptions are confirmed on-pin only | recorded |

## Deltas

One row per observed Claude-vs-Codex behavioral difference.

- **skill** - the skill the difference was observed in, or `*` for a catalog-wide one.
- **delta** - what Codex did differently, stated as an observation rather than a theory;
  quotations and line anchors are as-observed at triage.
- **severity** - `blocker` (the skill cannot do its job on Codex) | `major` (a gate or an
  output contract is affected) | `minor` (cosmetic or ergonomic).
- **disposition** - `accept` (documented difference, no work) | `fix` (repair in Step 9,
  which reads the `fix` rows from M2) | `wontfix` (host limitation, recorded and left).
  Cells are frozen as observed at triage and stay bare tokens; when a `fix` row is later
  resolved or re-dispositioned, the cell keeps its token and the resolution of record
  lives in a `###` section below (see "M2 disposition of the carried-over M1 `fix` row"
  and "Step 9 resolution of the F1 `fix` row").

| skill | delta | severity | disposition |
|---|---|---|---|
| plan-review | final report line claimed "Auto-applied 0 fixes" while the working tree showed a +107/-25 plan.md rewrite with autofix-applied markers stamped on all 8 steps; the core's autofix output contract requires N to count and enumerate the applied fixes | major | fix |
| * | Codex's listing paraphrases SKILL.md descriptions rather than echoing them; all 5 stayed semantically intact, and Copilot echoes the same descriptions verbatim, proving the installed frontmatter reads back whole | minor | accept |
| * | Copilot CLI 1.0.77, run with the install home as its project cwd, enumerates all 5 codex packages from .agents/skills; its load-path self-report (model-inferred, not runtime provenance) named the task-handoff SKILL.md under .agents/skills, agreeing with the listing's exact-set match | minor | accept |
| * | from the same cwd Copilot did not enumerate the junction-backed .claude/skills tree, although documentation/providers/gpt.md records .claude/skills as a Copilot discovery root; stated as an observation - the mechanism (e.g. reparse points) was not established | minor | accept |
| plan-review (M2) | intermittently stamps fewer `<!-- autofix-applied: DATE -->` markers than the fixes it reports: Run A applied 3 fixes to one step and stamped 1 marker (core.md:513 requires one per applied fix), while Run B applied 21 fixes across 7 steps and stamped all 21 correctly - same host, same session mode, same day. plan-wrap was observed once (2 fixes, 2 markers) and was correct. All three fix COUNTS were verified against the real file diff, so the defect is marker stamping, not counting. Attribution checked: the codex/claude/gpt adapters carry no marker language, so this is core-level | major | fix |
| * (M2) | Codex enumerated 47/47 installed portable skills (plus 6 host built-ins, 53 total) with no truncation; exact set match verified mechanically against the install tree, not by eye | minor | accept |
| * (M2) | Copilot CLI **1.0.80** (upgraded from the 1.0.77 the decision was evidenced against), run with the install home as cwd, still enumerates all 47 codex packages from the shared `.agents/skills` root (49 total incl. 2 built-ins); exact set match verified mechanically. D-CP6 `accept` re-confirmed on the new version and at 47-skill scale instead of 5 | minor | accept |

Disposition notes (M1 triage, 2026-08-18):

- The plan-review `fix` row re-observes at M2: the M2 workflow pass runs
  plan-review again, and if the miscount reproduces it belongs in
  `documentation/findings/codex-parity-m2-deltas.md`, whose non-emptiness is what
  triggers Step 9's repair work. No separate issue filed at M1.
- The two Copilot rows ARE the D-CP6 decision: accept, because the bound packages
  are real skill-mesh skills with host-neutral cores, their descriptions render
  verbatim, and no misbehavior was observed. The disposition is evidence-backed
  against Copilot CLI 1.0.77 (Run environment table) and is re-checked on any
  Copilot upgrade.

## M2 checks

Check rows for the Step M2 table in `documentation/codex-parity-delivery-plan.md`, observed
2026-08-19 on codex-cli 0.147.0 against the `code-stencil` toy project. Each Outcome grades
one check row only; the step verdict lives solely in the M-step verdicts list above.

| Check | Observed | Outcome |
|---|---|---|
| Each pipeline skill invocable | all four of `plan-feature`, `plan-review`, `plan-wrap`, `session-wrap` loaded their cores, walked their phases, and honored their output contracts; every invocation exited 0 | pass |
| Workflow chains end-to-end | artifacts produced where the cores demand them: `plan-feature` wrote a nine-section `documentation/learning-export-plan.md` with one Step 9 vertical slice and correctly named the downstream pipeline (`repo-init` → `plan-expedite` → `build-phase`, noting expedite chains review+wrap); `plan-review` autofixed and reported severity sections; `plan-wrap` emitted §1-§13 plus a `READY WITH GAPS: 3 gaps` verdict line; `session-wrap` produced the "Pick up here" rollup, git/memory/flags lines, and a handoff file | pass |
| Deltas | recorded as rows above; the one `fix` row is filed in `documentation/findings/codex-parity-m2-deltas.md` | pass |
| Catalog enumeration at full scale | Codex listed 47/47 installed portable skills, no truncation; retires the plan's open risk row "Initial-list budget (8,000 chars) with 47-54 skills" on the Codex side at 47 | pass |
| Install over the pilot ledger | full 47-skill install landed over the 5-entry M1 pilot ledger with exit 0; ledger reconciled to 111 owned files with **0 stale entries and 0 unledgered files**; `inspect-host-install` reports codex root owned=48 unowned=0, ledger valid, unrecognized=0. Rehearsed first against a disposable home cloned byte-for-byte from the real one | pass |
| Conversational-skill behavior | `plan-feature` and `plan-review` stopped to ask the operator focused questions. Verified against the cores before recording: `plan-feature` core.md:70-76 and :130 make the phases explicitly conversational, so these halts are correct core-following and **not** a parity delta and **not** an autonomy-contract violation | recorded |

### M2 D-CP6 re-check (Copilot 1.0.77 → 1.0.80)

The M1 disposition note binds the shared-root `accept` to Copilot 1.0.77 and requires a
re-check "on any Copilot upgrade". The installed Copilot is now **1.0.80**, so the re-check
was run rather than deferred.

Method matched M1's: Copilot invoked non-interactively with the install home as its project
cwd, asked only to enumerate its available skills, run read-only (no `--allow-all-tools`).

Result: Copilot 1.0.80 enumerates **all 47** codex packages from the shared `.agents/skills`
root, plus 2 host built-ins (49 total). The enumerated set was diffed mechanically against
the installed tree — exact match, zero missing, zero extra.

**Disposition: `accept` re-confirmed**, now on stronger evidence than M1 had — the behavior
holds across a version bump AND at 47-skill scale rather than 5. The reason is unchanged:
the bound packages are real skill-mesh skills with host-neutral cores, and no misbehavior
was observed. Still re-check on the next Copilot upgrade.

### M2 disposition of the carried-over M1 `fix` row

The M1 `plan-review` row ("Auto-applied 0 fixes" against a +107/−25 rewrite) was left
unfiled at M1 to be re-observed at M2. **It did not reproduce.**

Both M2 autofix reports were checked against the real file diff rather than taken at face
value:

| run | reported | actual substantive diff hunks | verdict |
|---|---|---|---|
| `plan-review` on the fresh feature plan | "Auto-applied 3 fixes", all three enumerated | 3 (`Type: code` added; `Files` list added; `--reviewers code` → `deep`) | count accurate |
| `plan-wrap` on the same plan | "Auto-applied fixes (2)", both enumerated | 2 (schema summary block added; `<ID>` → `<learning_id>`) | count accurate |

**Retested at M1 scale and still did not reproduce.** The first two observations were
small-N (3 and 2 fixes on a 1-step plan), so a targeted Run B was built against the input
class that produced the M1 miscount: the `code-stencil` plan restored to its pre-autofix
`40e83b7` state (7 steps, 43 lines, 0 markers), committed as the fixture's HEAD so no
phantom working-tree diff could confound the review.

| run | plan reviewed | reported | actual applied | verdict |
|---|---|---|---|---|
| B | pre-autofix `plan.md`, 7 steps | "Auto-applied 21 fixes", all 21 enumerated | 21 (3 classes x 7 steps) | count accurate |

Run B's accuracy is proven exactly rather than by hunk-counting: stripping the 21 added
fields and 21 markers from the result yields a file byte-identical to the pre-run original.

The row's disposition of record is now `accept` (the table cell above stays frozen at its
as-observed `fix` token per the Deltas legend; this section carries the re-disposition).
This is now a non-reproduction across BOTH small-N and M1-scale inputs, materially
stronger than the small-N-only evidence the first M2 write-up had. What Run B DID surface
is a separate, narrower defect - intermittent marker under-stamping - filed as F1 in the
findings file.

### M2 open threads

- **Large-rewrite reproduction run (Run B) - DONE, exit 0.** Completed after the first M2
  write-up. It did NOT reproduce the miscount (21 reported, 21 applied, verified exactly),
  and it produced the counterexample that narrowed F1 from "plan-review stamps one marker per
  step" to "plan-review intermittently under-stamps". Both the delta row above and the
  findings file were corrected accordingly; the findings file carries an explicit correction
  notice naming what was withdrawn.
- **`documentation/providers/README.md` capability matrix** still has no Codex column. M2
  produced per-skill behavior for only the four chain skills, which is not enough to fill
  it; Step 9 remains the intended source.

### Step 9 resolution of the F1 `fix` row (2026-08-19)

The one `fix`-severity M2 row (F1, filed in
`documentation/findings/codex-parity-m2-deltas.md`; issue #126) is resolved as a
root-cause core change, not a restatement of the rule that was already being violated:

- **Chosen resolution: option 1 - one marker per step touched.** The per-fix rule was
  itself the compliance hazard: N identical stacked `<!-- autofix-applied: YYYY-MM-DD -->`
  lines are indistinguishable from one another and carry no per-fix information, so a
  writer naturally dedupes them - Run A's "3 fixes, 1 marker" is exactly the shape the old
  rule invites. One-marker-per-step is trivially idempotent (skip the stamp when the
  heading already carries one) and leaves the byte format unchanged, so every committed
  date-only marker in this repository remains valid to every reader.
- **Single owner.** `skills/plan-review/core.md` § "Autofix marker" now owns format,
  granularity, and idempotency; `skills/plan-wrap/core.md` cites it instead of restating.
  Both cores' "per-finding-class, not per-step" re-run sentences were reconciled: fix
  idempotency stays keyed to the plan's actual state, and markers still never exempt a
  step from any check.
- **`/plan-expedite` reader re-checked - two prose lines amended.** Its core carries no
  literal marker regex, and the literal regex
  `<!-- autofix-applied: \d{4}-\d{2}-\d{2} -->` the writer cores pin is byte-identical
  before and after. Its resume detection never reads the markers at all - it reads the
  `.plan-expedite-state` JSON file - so no marker-reading mechanism needed re-verifying;
  the owner section now states that no in-tree reader greps the markers to decide
  anything today (the halt template only reports what they say). The two
  prose consumers of the old per-fix semantics were amended to the new granularity: the
  "When to use" bullet no longer attributes sub-skill idempotency to the markers
  (idempotency is keyed to the plan's actual state), and the halt template's Plan-state
  line now cites which STEPS autofix touched per the markers, sourcing the per-fix
  enumeration from the sub-skill's "Auto-applied N fixes" report block.
- **Deliberate three-provider output change.** The three amended cores (plan-review,
  plan-wrap, plan-expedite) regenerate into all three providers' distributions -
  dist/claude, dist/gpt, and dist/codex carry the new wording at the next build. This is
  intended: per the F1 attribution check, marker granularity is core-owned and identical
  for every host, so the fix lands once in the cores and nowhere in the adapters. No
  `providers/*.md` file was edited. This bullet is the F1 row's "delta log says
  otherwise" record for Step 9's byte-identical constraint (the cell stays frozen per
  the Deltas legend).
- **Legacy top-level packages deliberately unchanged.** `plan-review/SKILL.md`,
  `plan-wrap/SKILL.md`, and `plan-expedite/SKILL.md` retain the pre-2026-08-19 per-fix
  marker language (and the superseded marker-keyed skip-all re-run rule) per the
  deprecation-window policy in `CLAUDE.md` - the legacy tree is not canonical, not a
  build input, and never installed, so no consumer tree receives that wording. Recorded
  so a later diff of the two trees reads the divergence as policy, not as an incomplete
  fix.
- **Mechanical single-owner guard added.**
  `tests/package-integrity/test_autofix_marker_single_owner.py` sweeps every markdown
  file under `skills/` (cores and provider adapters alike) and `_shared/` and asserts
  the literal marker regex lives in exactly one of them - `skills/plan-review/core.md`,
  inside its `### Autofix marker` section, alongside the Format bullet - and that
  `skills/plan-wrap/core.md` still cites the owner by relative path and section name
  while carrying neither the literal regex nor the retired per-fix phrasings (the cite
  site's bounded minimum - date shape, placement, one-new-marker rule - is deliberate
  and stays; the guard polices the regex and those canary phrases, not paraphrase).
  Silent re-duplication into any core, adapter, or `_shared/` doc, the definition
  leaving the cited section, or a dropped citation now fails CI. The legacy top-level
  `*/SKILL.md` packages stay out of the sweep per the deprecation-window policy above.

## Step 6 authoring deltas (Cohort B - authored by construction, not host-observed)

Recorded while authoring the twelve Cohort B adapters (plan-init, plan-feature,
plan-expedite, plan-merge, plan-redline, plan-trim, plan-wrap, repo-init, repo-sync,
repo-update, user-wrap, user-project; issue #123). Like the Pre-M1 construction notes
below, these are mappings made BY CONSTRUCTION - nothing here has been observed on a
real host yet; the M2 workflow pass is what confirms or contradicts each row. Same
columns as the Deltas table so M2 can promote a row unchanged if it re-observes it.

| skill | delta | severity | disposition |
|---|---|---|---|
| plan-redline | no Artifact tool: the publication mechanism is the core's own standalone-HTML fallback - a print-faithful HTML file beside the plan, with the repository-relative path as the stable Proposal locator; republish overwrites the same file preserving decision IDs | minor | accept |
| plan-init | the closing line's proposal locator inherits plan-redline's file-path form (the auto-run redline hook publishes through the codex renderer), so operators get a path, not an artifact URL | minor | accept |
| plan-expedite | `/goal` and `/clear` are Claude-Code window primitives with no Codex equivalent; the adapter emits the core's continue-command block verbatim for the window that will run the build and never claims a Stop hook is armed - the durable task-state writes (current.md, handoff-prompt.md) are the cross-host handoff | minor | accept |
| repo-update | core Step 12 publishes the guided tour with the native Artifact tool; on codex the tour is authored as a self-contained HTML FILE in the repository and the final report's `Tour:` line carries that path instead of a private artifact URL; skip semantics unchanged | minor | accept |
| user-project | session identity comes from the abstract session-I/O layer; with no stable Codex identity the pin write follows the schema fallback (freshest sessions/*.md) and never mints a session file under a fabricated UUID - with no session file at all, the adapter reports the pin unset in one line and writes nothing (the pin is advisory; honoring skills fall back to cwd) | minor | accept |
| * | no Cohort B skill is in the manifest's `sub-agent` capability set, so the no-Agent-primitive mapping stays the pilot's single-context fallback with no capability loss for any of the twelve | minor | accept |

## Step 7 authoring deltas (Cohort C - authored by construction, not host-observed)

Recorded while authoring the sixteen Cohort C adapters (build-phase, build-step,
build-queue, review-deep, review-gauntlet, review-proof, review-uat, skill-iterate,
skill-evolve, skill-eval-setup, tier-escalate, tier-offload, judge-ui, test-prune,
goblin-do, goblin-suggest; issue #124). Like the sections above, these are mappings made
BY CONSTRUCTION - nothing here has been observed on a real host yet; the M-step passes
confirm or contradict each row. Same columns as the Deltas table so a later pass can
promote a row unchanged if it re-observes it.

Cohort C is the first cohort where the no-Agent-primitive mapping is NOT the pilot's
single-context fallback: eleven of the sixteen are in the manifest's `sub-agent`
capability set, and for nine of those eleven the core documents no single-context
fallback at all - so per the delivery plan's rule ("halt visibly with
`required_tool_missing` where core requires an unavailable host tool"), those wrappers
halt at the isolated dispatch instead of weakening the producer-never-grades-itself
gate. The two goblin skills ride their cores' documented CLI fallback, and build-phase
(not itself in the sub-agent set) runs its orchestration natively - same-context
named-skill dispatch keeps the verdict key in parent private state, satisfying the
core's guard - and inherits the downstream /build-step halt.

| skill | delta | severity | disposition |
|---|---|---|---|
| build-step | no isolated fresh-context agent primitive and the core documents no single-context fallback for its developer/reviewer arms (independence IS context isolation; the producer never grades itself) - the adapter halts `required_tool_missing` at the first isolated dispatch and never runs producer and reviewer in one context; worktree lifecycle, mechanical gates, and Playwright probing remain portable shell | blocker | wontfix |
| build-phase | orchestration runs natively: same-context named-skill dispatch keeps the parent-local HMAC verdict key in private parent state, satisfying the core's private-parent-state guard (its `required_tool_missing` halt stays armed only for a host that genuinely cannot retain it); every dispatched `/build-step` halts `required_tool_missing` on this host, so a run stops at the first code step's dispatch and the halt is surfaced by the core's own halt handling | major | accept |
| build-queue | queue orchestration (pre-flight, `.build-queue-state`, kill-switch, park procedure, morning report) runs natively, but every dispatched `/build-phase` halts `required_tool_missing` on this host, so items park rather than build - the park-not-abort contract renders exactly as designed | major | accept |
| review-deep | the per-lens fresh-context reviewer fan-out is required with no documented single-context fallback (lens independence comes from context isolation); the adapter halts `required_tool_missing` at the lens dispatch; the mechanical pre-pass, diff gathering, lint pre-pass, and auth-gate probe remain runnable shell | blocker | wontfix |
| review-gauntlet | same isolation requirement as review-deep, whose lens definitions it imports verbatim; the adapter halts `required_tool_missing` at the five-lens dispatch and never feeds the deterministic reducer from in-session opinions | blocker | wontfix |
| review-proof | no degradation: the whole contract is file reads, greps, and shell through the host's own tools, and a single conversational context is the contract; the secret-file effect-based-check discipline is carried into the wrapper verbatim | minor | accept |
| review-uat | refinement runs natively; `--exec`/`--ui` delegate to `/user-uat` and `/judge-ui` via named-skill dispatch, and where the downstream skill is unavailable on this host the adapter surfaces `required_tool_missing` naming it rather than executing steps inline or dropping the flag | minor | accept |
| skill-iterate | the workflow primitive and the fresh-context render/grade split are required ("keeping render and grade as separate agents is non-negotiable") with no documented fallback; the adapter halts `required_tool_missing` at the score-loop dispatch; the deterministic scoring scripts stay portable | blocker | wontfix |
| skill-evolve | the core's own halt contract governs: workflow unavailable is core halt #2, halting rather than falling back to a single self-grading agent (the defect the skill was rebuilt to avoid); the adapter maps that halt to `required_tool_missing`; brainstorm mode runs natively | blocker | wontfix |
| skill-eval-setup | authoring runs natively; where the corpus generator script's sub-agent backend is absent the adapter uses the core's documented non-dispatch modes (`--dry-run`, `--verify-only`, hand-crafted examples) and reports which mode ran; the emitted Part 3 loop text keeps the producer/grader invariant verbatim and the script-deterministic verification gate is unchanged | minor | accept |
| test-prune | Phase 1 requires parallel Explore flagging arms ("never as a serial in-line scan, even for small test suites") and documents no single-context fallback; the adapter halts `required_tool_missing` at the Phase 1 dispatch rather than substituting an in-session scan - documenting such a fallback would be a core change, not a wrapper's call | blocker | wontfix |
| tier-escalate | the classification constraint requires read-only fresh-context task invocations with batch-uniform rules and documents no single-context fallback; the adapter halts `required_tool_missing` at the Phase 2 fan-out and never classifies the catalog in-session | blocker | wontfix |
| tier-offload | same read-only fresh-context classification constraint as tier-escalate, same halt; the emitted-config gates (standing `build-step-style: false`, unmet gate-precondition emits `false`) are authoring rules and are unaffected | blocker | wontfix |
| judge-ui | the driving leg (Playwright capture, adapter or documented inline-flow fallback, mandatory structured read-back, mechanical asserts first) is portable shell, and a mechanical-gate failure still renders its FAIL with no vision call; the verdict leg requires an independent vision-judge sub-agent with no documented single-context fallback, so the adapter halts `required_tool_missing` at the judge dispatch rather than grading its own driving | blocker | wontfix |
| goblin-do | the Workflow session path is unavailable; the execute rail rides the core's documented CLI fallback (`uv run goblin do <id>`, dispatching `/build-step` to a `claude -p` subprocess where that host's isolation applies); absent the `claude` CLI or its OAuth token the adapter halts `required_tool_missing` rather than degrading to an unreviewed inline edit | minor | accept |
| goblin-suggest | the Workflow session path is unavailable; the core's documented CLI fallback (`claude -p` subprocesses, a ThreadPoolExecutor per candidate) preserves judge independence and parallelism unchanged; absent the `claude` CLI or its OAuth token the adapter halts `required_tool_missing` rather than generating and judging in one session | minor | accept |

Disposition notes (Step 7 authoring triage):

- The `wontfix` rows are host limitations, not defects to repair in Step 9: the missing
  capability is the isolated fresh-context primitive itself, and every core involved
  either documents no fallback or (skill-evolve) explicitly forbids the single-context
  one. If a later M-step decides a documented single-context mode is wanted for any of
  them, that is a CORE change with its own review, never a wrapper edit.
- The `accept` rows lose no gate: build-queue's parks and build-phase's surfaced
  downstream `/build-step` halts are their cores' designed halt handling, and the
  goblin CLI fallback, review-uat delegation, and skill-eval-setup non-dispatch modes
  are all core-documented paths.

## Step 8 authoring deltas (Cohort D - authored by construction, not host-observed)

Recorded while authoring the fourteen Cohort D adapters (memory-distill,
observatory-doctor, research-prospect, user-afterparty, user-brainstorm, user-debug,
user-draft, user-gateway, user-lavishify, user-learn, user-pm, user-shakedown,
user-uat, user-walkthrough; issue #125) - the remainder of the portable catalog, which
this cohort closes at 47/47. Like the sections above, these are mappings made BY
CONSTRUCTION - nothing here has been observed on a real host yet; the M-step passes
confirm or contradict each row. Same columns as the Deltas table so a later pass can
promote a row unchanged if it re-observes it.

Three of the fourteen are in the manifest's `sub-agent` capability set
(research-prospect, user-brainstorm, user-learn) and none of the three cores documents
a single-context fallback, so per the delivery plan's rule those wrappers halt visibly
with `required_tool_missing` at the isolated dispatch. A fourth, user-debug, is NOT in
the `sub-agent` set, but its core's Step 2 independent-reproduction arm ("always") is
defined by not sharing the parent's suspected root cause - a constraint a single
context cannot satisfy about itself - so its wrapper halts on the same rule; the
capability-set question is metadata owned elsewhere and is recorded here, not changed
here. The remaining ten map natively.

| skill | delta | severity | disposition |
|---|---|---|---|
| memory-distill | `<workspace-memory>` resolves through the host's own project-memory convention or an operator-named directory; with no memory directory on disk the adapter reports that in one line and stops - it never invents a memory store or reviews from recollection; the conversational round gates run unchanged | minor | accept |
| observatory-doctor | no degradation: the skill is a thin relay over the `observatory doctor` CLI through the host shell; the read-only discipline (no auto-fix, no server/demo probes) is carried verbatim, and a machine without the dev-observatory workspace gets a one-line report, never a reimplementation of the checks | minor | accept |
| research-prospect | Step 2 requires one isolated Explore arm per project dispatched in parallel ("sequential dispatch is a defect") and the core documents no single-context fallback; the adapter halts `required_tool_missing` at the fan-out rather than sweeping projects in-session - Step 1's project-list resolution still runs so the halt names the arms that could not dispatch | blocker | wontfix |
| user-afterparty | the glue (sequencing, collection, orphan-cleanup, rollup seam) runs natively, but several swept items cannot run on this host: `context-slim` is Claude-native and absent from the codex profile, and `test-prune` plus the `tier-drift` pair halt `required_tool_missing`; each lands in the ONE report as its reason code - unavailable is its own result, never reimplemented inline | major | accept |
| user-brainstorm | interactive ideation and the meta-file writes run natively; the Step 7 per-file background authoring dispatch has no documented single-context fallback, so the adapter halts `required_tool_missing` there, leaving topics.md/plan.md as the durable record a capable host resumes from | blocker | wontfix |
| user-debug | Step 1's investigation and Diagnosis Block run natively and remain durable output; the Step 2 independent-reproduction arm must not see the suspected root cause this parent context already holds, so no single-context substitute exists by construction and the adapter halts `required_tool_missing` before any fix design or code change | blocker | wontfix |
| user-draft | fully native: the task-state checkpoint is ordinary file I/O and the emitted draft is paste-ready text for the window that will run it, reproduced verbatim (including any host-window primitives the target window supplies) - the adapter never claims this host arms or runs them | minor | accept |
| user-gateway | ledger writes are intake-engine file I/O and run natively; every per-row seed is paste-ready text emitted verbatim in its rail's spelled shape - including the investigate rail's pinned `Workflow({name: "deep-research-pinned"})` charter line - and the gateway dispatches nothing | minor | accept |
| user-lavishify | the `lavish-axi` CLI runs through the host shell; the Claude scratchpad maps to a durable host-local temp `.lavish/` directory reported by path, the long-poll runs via the host's background facility or the core's own re-run-in-bounded-stints rule, and the security gates (telemetry off, loopback only, never `share`) are carried verbatim | minor | accept |
| user-learn | interactive setup runs natively; the Step 4 per-file authoring waves (notebook agents author AND execute their own notebook) have no documented single-context fallback, so the adapter halts `required_tool_missing` at the dispatch rather than authoring the ramp serially in-session | blocker | wontfix |
| user-pm | no degradation: a read-only project-axis overview through the host's shell and file tools; the dev-observatory hook stays additive (consulted only where the registry exists, one-line note where absent) | minor | accept |
| user-shakedown | the autonomous closure loop, quick fixes with the narrowest test, and the zero-open termination check run natively; the recommended `/goal` arming is a Claude-window primitive reproduced as operator text - on this host the loop simply keeps driving in-session until the engine's check returns 0 | minor | accept |
| user-uat | classification, the side-effect gate, and the mechanical tier run natively with background readiness probes; `--deep` is the core's own in-session labeled assessment; `--ui` delegation surfaces `required_tool_missing` where the judge is unavailable (`judge-motion` is Claude-native; `/judge-ui` halts at its vision-judge dispatch on this host) and the step lands in `Needs you` - never a self-viewed visual verdict | minor | accept |
| user-walkthrough | no degradation: the operator-driven loop, primary-source answers with `file:line`, and the shared shakedown-engine ledger are conversational, shell, and file work that run unchanged | minor | accept |

Disposition notes (Step 8 authoring triage):

- The `wontfix` rows are host limitations, not defects to repair in Step 9: the missing
  capability is the isolated fresh-context primitive itself, and each core involved
  either documents no fallback or (user-debug) states an independence constraint a
  single context cannot satisfy about itself. If a later M-step decides a documented
  single-context mode is wanted for any of them, that is a CORE change with its own
  review, never a wrapper edit.
- The `accept` rows lose no gate: the afterparty sweep reports unavailable items as
  results (its core's SEQUENCE-DON'T-REIMPLEMENT posture), user-uat's `--ui`
  degradation is the core's own escalate-to-Human shape with the reason code named,
  and every conversational gate runs verbatim.
- With this cohort the authored roster equals the portable catalog (47/47); the
  whole-catalog initial-list budget gate in
  tests/package-integrity/test_codex_budgets.py now measures the real catalog a Codex
  host serializes, and passes with the full 47-name list.

## Pre-M1 construction notes

Not deltas - nothing has been observed on a real host yet. These are the two mappings the
Step 4 pilot adapters had to make by construction, recorded here so M1 can confirm or
contradict them rather than rediscover them.

1. **No isolated-agent primitive.** Codex has no Claude Agent/Workflow tool, so every
   pilot adapter routes the core's isolated fresh-context agent role through the core's
   documented single-context fallback. None of the pilot five is in the manifest's
   `sub-agent` capability set, so no pilot skill loses a capability here; M1's plan-review
   check is the confirmation that the fallback path actually renders a verdict.
   **M1 outcome (2026-08-18):** confirmed - the fallback rendered plan-review's
   contract-shaped verdict with no sub-agent primitive available.
2. **No Codex peer in the tier map.** `config/model-tier-map.json` maps Claude tier names
   onto GPT peer models and declares no Codex entry, and `runtime/skill-router.ps1` reads
   `config/model-mapping.json` only for the per-skill `claude`/`gpt`/`local` booleans with
   a provider vocabulary closed at `claude|gpt|local`. Nothing in either file is consulted
   for a Codex run today, so Step 4 added no speculative entry; the pilot adapters instead
   state that tier names resolve as capability ROLES. If M1 or M2 shows a real need for a
   named Codex peer, that is a config change with a consumer, and it belongs to the step
   that adds the consumer. **M1 outcome (2026-08-18):** no such need surfaced.

3. **The codex install root and Copilot's active-scan `.agents/skills` root are the SAME
   literal path, so D-CP6's collision is real rather than vacuous.**
   `tools/skill-mesh-discovery.ps1` is the sole owner of both answers and has exactly ONE
   base. `Get-SkillMeshDiscoveryRoots` returns `codex -> .agents/skills`, and
   `Get-SkillMeshActiveProjectDiscoveryRoots` - the set of roots a host may already be
   scanning - also contains `.agents/skills`. Both return bare home-relative POSIX
   strings, and every consumer (`tools/install-skill-mesh.ps1`,
   `tools/inspect-host-install.ps1`, `tools/migrate-legacy-install.ps1`,
   `tools/probe-codex-skills.ps1`) joins them onto its own `-Home`. There is no
   project-root variable anywhere in the tool closure, so nothing at the code level
   distinguishes "the codex install target" from "the Copilot active alternate": they are
   the identical string resolved against the identical base, and only the operator's
   choice of home directory separates them on disk. The two functions are kept separate
   anyway, because they answer different questions ("where does skill-mesh WRITE?" vs
   "could a host SEE bytes here?"). Pinned by
   `tests/distributions/test_legacy_migration.py::test_the_owner_actually_defines_every_root`,
   which asserts both facts together, so a future edit that quietly forks them into two
   different paths has to say so there.

   **No guard was pre-built, by design.** D-CP6 held that a collision guard is speculative
   until a real host shows whether the collision has a consequence, so Step 5 shipped the
   root, the installer vocabulary and the probe without one. That decision is still open,
   and the accept-vs-guard policy is M1's to make ON EVIDENCE. This file is where that
   record has to live: the build worktree is deleted and its dev reports are archived off,
   so a finding that exists only in a PowerShell doc-comment or a step report is a finding
   M1 will not see.

   **What M1 should actually look for.** Install the codex profile into a home
   (`tools/install-skill-mesh.ps1 -Provider codex -Home <home>`), confirm the tree with
   `tools/probe-codex-skills.ps1`, then - from a directory Copilot treats as a project
   with that same tree in scope - ask Copilot to list the skills it can see, and check
   whether the codex-profile packages are enumerated.
   - If Copilot enumerates them, the collision has a real consequence (one tree, two
     hosts; packages authored for one host offered by the other). Record it as a Deltas
     row above with a severity, and decide guard-vs-accept there with a stated reason.
   - If Copilot does not enumerate them, record that observation together with the Copilot
     CLI version that produced it, in the Run environment table. The `accept` disposition
     is then evidence-backed rather than assumed, and re-checking it becomes a cheap
     regression on the next Copilot upgrade.
   Either way this is an M1 OBSERVATION to write down here, not a build defect and not
   something to infer from the code - the code cannot answer it.

   **M1 outcome (2026-08-18):** Copilot CLI 1.0.77 DOES enumerate the codex
   packages from the shared root, and did not enumerate the junction-backed
   .claude/skills tree from the same cwd. The collision therefore has a real
   consequence, and the accept-vs-guard policy was decided on that evidence:
   accept, with the reason and the upgrade re-check trigger recorded in the
   Deltas rows above.

---

## Phase CP pass-3 blocker — Step 11 invalid premise, and the cross-plan dependency it exposed

**Recorded 2026-08-20 during `/build-phase --resume 10` (Steps 9 and 10 both DONE and green).**
Step 11 (#128) and Step 12 (#129) are `Status: BLOCKED`. This section is the delta-log record
of why, and of the cross-plan dependency the investigation surfaced. It records facts only —
the scope decision is the operator's and is offered as options on #128.

### What is actually true about the utility advisory-call wiring

| Claim in Step 11's problem statement | Evidence | Verdict |
|---|---|---|
| "Steps 1-3 DONE wired advisory calls into 16 installed `.github/skills/*/core.md`" | That diff is commit `af7a867`: 38 content lines, **all** `_shared/` relative-link repoints (`../../_shared/x` -> `../_shared/x`, the Step 66 emit-time repoint). Zero mention `DEV_UTILITIES_ROOT` or any of the 7 utilities. | **FALSE** |
| Those installed copies drifted and a reinstall would overwrite the wiring | `git status --porcelain -- .github/skills` is clean, and the files already equal what the canonical sources emit. There is no drift to reconcile. | **FALSE** |
| The advisory-call convention is the owner of "the authoritative hookup map" | The convention disclaims it at §5: *"This doc owns only the shared shape; the map owns the moments."* It owns the 8-point shape and §2's 7-row CLI call-shape table, nothing more. | **FALSE** |
| The 16-skill working set | 13 of the 16 appear **zero** times in both owner documents. The ratified set is a different 11 skills; overlap is 3 (plan-feature, plan-review, repo-update). | **UNRATIFIED** |
| Done-when: "advisory blocks match the convention's 8 points verbatim" | The convention requires each core to carry **a one-line citation, never a copy** of the convention text. Only §2's CLI token/option order is verbatim-locked. A block-presence test would gate the wrong artifact. | **MIS-STATED** |

Current wiring state, verified: **0** of 47 installed `core.md` and **0** canonical
`skills/*/core.md` contain `DEV_UTILITIES_ROOT`. A prior dev-session task-state record
independently reached the same conclusion ("wired into ZERO skill cores — verified").

### Cross-plan dependency (the Step 12 record, as far as it can honestly go)

- The real hookup map is `dev/docs/investigations/utility-hookup/README.md` §3. Its anchors
  still point at the legacy `.claude/skills-gpt/<skill>/SKILL-core.md` layout and must be
  re-resolved onto `skill-mesh/skills/<name>/core.md` before any wiring step can execute.
- `dev/documentation/utility-hookup-plan.md` decision **D12** already assigns these exact
  edits to `skill-mesh/skills/<name>/core.md`. Its Steps 6-23 and Phase CP Step 11 are
  therefore **the same work, currently double-owned across two plans.** One owner must be
  chosen before either executes.
- Execution on either plan is gated behind utility-hookup **Step 5** (`Type: wait`), which
  persists `DEV_UTILITIES_ROOT` and has never run. Measured 2026-08-20:
  `DEV_UTILITIES_ROOT` is unset at Process, User **and** Machine scope.
- **Consequence for M4.** With the variable unset, only the fails-open half is testable:
  absent utilities root -> zero behavior change. The advisory-line half — M4's row *"one
  wired skill run with `DEV_UTILITIES_ROOT` set shows its advisory line"* — is **unrunnable
  in this phase** regardless of which scope option is chosen, until Step 5 runs.
- Step 12's observatory-visibility question is untouched by this: with no wiring in any core,
  there is nothing for a registry entry or a scrape to surface. Its first Done-when branch is
  unsatisfiable by construction, not merely unbuilt.

### Exhaustive confirmation (added 2026-08-20, after the scoped searches above)

A full-tree search of the coding root (excluding `skill-mesh/` and `node_modules`) finds
`DEV_UTILITIES_ROOT` in exactly **10 files. Every one is a planning or convention document.
Not one is a skill core.**

- `.claude/references/advisory-call-convention.md` (the convention)
- `.claude/rules/advisory-calls.md` (the rule stub) — and `citation-needed/breakdowns/…` , a
  derived breakdown of that same rules file
- `.claude/task-state/sessions/6174bae3-…md` (the prior session's verified record)
- `documentation/utility-hookup-plan.md` (the owning plan)
- `documentation/coding-root-closeout-plan.md`
- `dev-observatory/plans/utility-project-surfaces-plan.md`
- three copies inside stale `worktree_*` checkouts (`host-parity-repair-plan.md`,
  `codex-parity-delivery-plan.md`)

This upgrades the finding from a scoped negative to an exhaustive one: **the advisory-call
wiring exists only as specification, and has never been rendered into any executable skill
core anywhere on this machine** — not the canonical `skills/`, not the Claude install tree,
not the Copilot install tree.

**Lead for Step 12.** `dev-observatory/plans/utility-project-surfaces-plan.md` was not among
the sources Step 12 names, but it is the only observatory-side plan that mentions the
utilities root. Read it before deciding Step 12's visibility mechanism — it may already own
the "surface the utility projects" question that Step 12 was going to answer from scratch.

## Step 12 record — the cross-plan dependency, and exactly what M4 can and cannot see

**Recorded 2026-08-20.** Step 12's Done-when offers two branches. The first ("the wiring for
the 16 skills is resolvable through an observatory surface") is unsatisfiable by construction —
no wiring exists in any core. This section satisfies the **second** branch: a named cross-plan
dependency stating exactly what M4 will and will not be able to see. No observatory features
were built; this is a read-only finding.

### The dependency is dev-observatory Step 37 — not Step 43

Step 12's brief guessed the dependency was dev-observatory **Step 43**. That is wrong, and the
correction matters:

- **Step 43 is unrelated.** It is that plan's own On Brand explorer step, status `READY`.
- **The real dependency is dev-observatory Step 37**, which already carries Step 12's
  deliverable verbatim: *"the seven hookup locators resolve `wired`."*
- **The direction is the reverse of what this plan assumed.** Step 37 is
  `BLOCKED ON UTILITY-HOOKUP STEP 4`. **The observatory waits on the hookup work; the hookup
  never waits on the observatory.** Phase CP Step 12 was written as though skill-mesh had to
  make the wiring visible. It does not — the surface already exists and is waiting to be fed.

### The mechanism already exists and is built

Visibility is **not** scrape-derivation. It is registry-declared `WiringLocator` rows
(`id` / `role` / `label` / `path` / `pattern`) that `resolve_wiring_evidence` matches as a
**literal substring at scan time**, classifying each into `wired` / `referenced` / `unwired`
on a transparency page. Specified at that plan's §5 and **built** — its Steps 32–34 and 36 are
all DONE across `model.py`, `registry.py`, `view_sources.py`, `snapshot.py`, `templates.py`.
All seven portfolio utilities already have a "Planned …" locator declared in the coding-root
registry today.

### What M4 WILL be able to see

- The transparency page itself, and all seven utilities present as declared locator rows.
- Their current honest state: **`unwired`** — which is the correct reading of reality, not a
  defect in the surface.

### What M4 will NOT be able to see, and why

1. **No locator resolving `wired`** — because no advisory-call wiring exists in any core, on
   any host. This is the whole of the Step 11 blocker, and it is not an observatory gap.
2. **Three of the seven would stay `unwired` even after wiring lands.** The declared patterns
   for `paper-trail --root`, `changed-check plan --root` and `find-again --root` **cannot
   match** the call shapes ratified in the convention's §4 under literal single-line matching.
   This is a live defect in the coding-root registry's locator patterns and belongs to
   dev-observatory, not here. Whoever executes the hookup must fix these patterns or the
   surface will under-report a correct wiring.
3. **`wired` flips only after an install propagates.** Every locator `path` points at the
   **installed** `.claude/skills/<name>/core.md` tree, not skill-mesh's canonical
   `skills/<name>/core.md`. Editing a canonical core changes nothing on the page until a
   reinstall lands it in a discovery root — which is M4's own operator-gated write (D-CP14).
4. **The advisory line cannot be demonstrated at all this phase.** `DEV_UTILITIES_ROOT` is
   unset at Process, User and Machine scope, and the operator deliberately deferred persisting
   it on 2026-08-20. Only the fails-open half (absent root → zero behavior change) is testable.

### Re-resolved hookup map (for whoever executes the work in utility-hookup-plan)

The real map ratifies **11 skills**, not this plan's 16, and the overlap is 3:
`plan-expedite`, `build-phase`, `build-step`, `session-wrap`, `repo-update`, `plan-redline`,
`plan-feature`, `plan-review`, `user-debug`, `lesson-harvest`, `memory-distill`. (Counting
second-wave moments adds `repo-sync` for 12; `repo-sync` has no first-wave moment.)

**All 11 have a live canonical core. 9 of 11 have an unambiguous live anchor.** The two that
do not are both `find-again` moments with no live equivalent: `plan-review` (it reviews an
already-drafted plan; no pre-draft moment exists in its 27-check structure) and
`memory-distill` (it reviews existing memories; no add-a-new-entry moment). Two softer spots
need a plan decision rather than a mechanical re-anchor: `changed-check` m3 on `session-wrap`
(route body vs the Git-verb router's Step C), and `same-page` m2's "touched-repo loop"
sub-anchor. Sizing flag: `plan-redline` was rewritten down to 35 lines, so its S-effort
estimate was measured against prose that no longer exists.
