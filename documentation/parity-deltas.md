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
- M2: PENDING
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
| M2 | | | | |
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
- **delta** - what Codex did differently, stated as an observation rather than a theory.
- **severity** - `blocker` (the skill cannot do its job on Codex) | `major` (a gate or an
  output contract is affected) | `minor` (cosmetic or ergonomic).
- **disposition** - `accept` (documented difference, no work) | `fix` (repair in Step 9,
  which reads the `fix` rows from M2) | `wontfix` (host limitation, recorded and left).

| skill | delta | severity | disposition |
|---|---|---|---|
| plan-review | final report line claimed "Auto-applied 0 fixes" while the working tree showed a +107/-25 plan.md rewrite with autofix-applied markers stamped on all 8 steps; the core's autofix output contract requires N to count and enumerate the applied fixes | major | fix |
| * | Codex's listing paraphrases SKILL.md descriptions rather than echoing them; all 5 stayed semantically intact, and Copilot echoes the same descriptions verbatim, proving the installed frontmatter reads back whole | minor | accept |
| * | Copilot CLI 1.0.77, run with the install home as its project cwd, enumerates all 5 codex packages from .agents/skills; its load-path self-report (model-inferred, not runtime provenance) named the task-handoff SKILL.md under .agents/skills, agreeing with the listing's exact-set match | minor | accept |
| * | from the same cwd Copilot did not enumerate the junction-backed .claude/skills tree, although documentation/providers/gpt.md records .claude/skills as a Copilot discovery root; stated as an observation - the mechanism (e.g. reparse points) was not established | minor | accept |

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
