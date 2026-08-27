# Phase IS — instruction-file symmetry

**Phase label:** `Phase IS` (instruction-file symmetry). Steps 100–109.
**Status:** BUILDING — 9 of 11 units landed; 8 of 11 certified DONE. Steps 100–107 are DONE,
Step 108 is landed / certification pending, Step 108P is blocked before implementation, and Step 109
is blocked before grading.
**Approval history:** REDLINE ACCEPTED (Publication 2, 2026-08-20) — issues synced 2026-08-21
under umbrella #143; all ten `**Issue:**` fields populated.
**Created:** 2026-08-20 against `main` @ `1f410fc`. Initial planning was revised after plan-review
round 1 (22 Blockers) and plan-wrap round 2 (9 Blockers); execution revisions continue in § 12.

**Reading aid.** `P<n>` = operator-picked decision *n* and `D<n>` = agent-defaulted decision
*n* in § 6. `A` = the project's `AGENTS.md`, `C` = its `CLAUDE.md`. Angle brackets inside a citation spelling like
`<repo>/_shared/<leaf>` are **literal source bytes**, not a substitution — see D6.
CLI = command-line interface; UAT = user acceptance testing; MCP = Model Context Protocol.

---

## 1. What This Is

Proposal: `documentation/instruction-file-symmetry-proposal.html` — Publication 2, accepted as
written on 2026-08-20. This plan remains the source of truth.

Make the skill catalog's lifecycle skills **instruction-file symmetric**: a project may keep
its content in `AGENTS.md` with `CLAUDE.md` reduced to a one-line `@AGENTS.md` import, and no
skill in the catalog may silently misread or re-duplicate that shape.

This is Phase 2 — and **only** Phase 2 — of the wider portfolio proposal (provenance: § 13).

**Why it is a prerequisite rather than a follow-up.** The wider proposal's Phase 3 inverts
project instruction files across up to 32 repositories. Skills in this catalog *write*
instruction files. Run one against an already-inverted project and it recreates the
duplication the inversion exists to remove — **silently**, because the result is two
substantive files and no gate that notices. Nothing may migrate until this lands.

### The measurement this feature rests on

Vendored here so nothing load-bearing depends on an out-of-tree file. Measured 2026-08-20
against `codex-cli 0.147.0` (`codex --version`).

| Host | Prose pointer ("Load and follow X in full") | `@`-import (`@AGENTS.md`) |
|---|---|---|
| Claude Code | **inert** — target content does not reach context | **expands** — target content reaches context |
| OpenAI Codex CLI | **inert** | **inert** — Codex expands no imports at all |

Consequence: **the file Codex reads must *be* the content.** `CLAUDE.md` carrying `@AGENTS.md`
is the only shape that serves both hosts from one copy.

**Reproduction** (runs no model session and writes nothing *in the project* on any controlled
run; Codex-home background churn prevents attributing any outside-project file count to one
invocation):

```
cd <project-dir>
codex debug prompt-input
```

Its JSON output contains the instruction text Codex would send. Grep it for a heading you
expect (`## Stack`); absence means the content never reached the model. A one-invocation
config override that does **not** persist:
`codex debug prompt-input -c "project_doc_fallback_filenames=['CLAUDE.md']"`.

> **Corrected 2026-08-26 (Step 107).** This section previously claimed the reproduction
> "writes nothing" and spelled the override with outer single / inner double quotes. Both
> were wrong and were transcribed faithfully into Step 107's first iteration before review
> caught them: the old spelling exits 1 in Windows PowerShell 5.1 (PS strips the inner
> quotes; codex reports `invalid type: string "[CLAUDE.md]", expected a sequence`). Controlled
> protocols later established only that every run leaves the project directory unchanged and
> that a `-c` override leaves nothing on disk; zero-invocation controls reproduced the observed
> Codex-home signature, so no per-invocation outside-project count is published.
> `documentation/codex-instruction-delivery.md` is now the vendored owner of this measurement;
> prefer it over this section.

---

## 2. Pre-implementation baseline (2026-08-20)

Unless a later annotation explicitly says it was re-measured, the figures in this section are
historical planning inputs captured before Steps 100–109. They are not a current inventory.

- **Cores and adapters.** `skills/<name>/core.md` is the provider-independent behavior
  contract; `skills/<name>/providers/{claude,gpt,codex}.md` are thin loaders that may never
  weaken a core gate. Verified: `plan-init` is a 488-line core against 21/22/19-line adapters.
- **54 cores, 57 skill directories.** The three provider-native skills (`claude-oauth-auth`,
  `context-slim`, `judge-motion`) carry `core: null` and have **no core.md**.
  `skills/*/core.md` reaches 54 directories; `skills/*/providers/*.md` reaches all 57
  (57 claude + 54 gpt + 54 codex = 165). The now-deferred write-surface design would re-derive
  its floors from these numbers rather than hard-code them; see § 10.
- **24 of the 54 cores name `CLAUDE.md`** (`grep -l 'CLAUDE\.md' skills/*/core.md | wc -l`);
  **3 name `AGENTS.md`** (`plan-feature`, `plan-merge`, `plan-review`); **3 of the 165 provider
  files name `CLAUDE.md`** (`context-slim/providers/claude.md`, `plan-init/providers/codex.md`,
  `judge-motion/providers/claude.md`).
- **The seven-section contract is duplicated** in `skills/plan-init/core.md:601-609` and
  `skills/repo-update/core.md:342-348` (re-measured 2026-08-26; the ranges moved when Steps 100-102 landed). **The two are NOT verbatim duplicates** — same bold
  section names, different gloss, because one bootstraps and the other refreshes. Merging them
  would change behavior under cover of a move; § 3 forbids it.
- **`_shared/` citation rules are asymmetric and restrictive.** Cores must cite as the literal
  `<repo>/_shared/<leaf>`; every relative spelling is a dangling reference against a
  **shrink-only** allowlist (`tests/package-integrity/link_baseline.json`, 149 frozen entries —
  a new key hard-fails, it is not amendable). Adapters are **forbidden** the `<repo>/_shared/`
  spelling outright (`tests/distributions/test_distributions.py:770-777`). The shared payload
  is a **transitive closure seeded from citations**, never a committed list
  (`tools/build-distributions.ps1:624-628`). These constraints are why this plan creates no
  `_shared/` file — D6.
- **Editing a core does not change any invokable skill.** This repository is the canonical
  source and build toolchain, not an installed tree. At this baseline, the installed
  `<dev-root>/.claude/skills/plan-init/core.md` was a **separate 26,477-byte copy** and the
  canonical `skills/plan-init/core.md` was 26,657 bytes. Nothing an operator can invoke changes
  until `tools/build-distributions.ps1` then `tools/install-skill-mesh.ps1` have run. Step 108
  exists solely because of this separation.
- **This repository is deliberately NOT inverted.** Its `AGENTS.md` is a 6-line prose pointer
  to `CLAUDE.md`, frozen by `tests/package-integrity/test_recovery_plan_hygiene.py:41-60`.
  D8 gives this exact pair as its worked example.
- **Zero existing coverage.** No test reads `skills/*/core.md` for instruction-file handling;
  `grep -rn "@AGENTS"` returns zero matches repo-wide outside this plan.
- **The single-owner prose pattern already exists here.**
  `tests/package-integrity/test_autofix_marker_single_owner.py` proves a named section in one
  core can be the ONE owner, cited by others, with a test catching re-duplication, owner
  renaming and citation deletion. It works because there is **one normative literal to probe**
  and a **bounded cite-site minimum guarded by named canary phrases**. D11 supplies both here.
- **Test counts are owned by `documentation/phase-75-baseline.md`.** That file states in its
  own words that `python -m pytest tests/` and `python -m pytest tests/package-integrity` are
  iteration gates and **neither may flip a step or a phase DONE**. Every remaining
  code/certification step therefore ends on the repo-root invocation. Step 109 consumes Step 108's certified bytes
  and closes on its attended checks rather than rerunning the suite. This plan restates no count.

---

## 3. Scope

**In scope**

- The instruction-file contract (D8, D10, D11), defined once as a named section in one core.
- The lifecycle writers: `plan-init`, `repo-update`.
- `skills/plan-init/providers/codex.md:11`, the one adapter naming the written artifact.
- Every core or provider file the Step 103 enumeration proves reads or authors a **project**
  instruction file.
- `context-slim`, which writes `CLAUDE.md` under `--apply` and has no core.
- One landed package-integrity single-owner gate; the proposed write-surface gate is deferred
  under § 10 and intentionally absent.
- A build + install into a scratch home, then operator confirmation.

**Out of scope — explicitly**

- Phases 0, 1, 3, 4, 5 of the wider proposal. **No consumer project is migrated by this plan.**
- **Creating any `_shared/` file** (D6).
- **Changing or merging the seven sections.** They differ deliberately (bootstrap vs refresh).
- Flipping skill-mesh's own `AGENTS.md` / `CLAUDE.md` (D5).
- **Workspace-file references, which are a different thing from project instruction files.**
  A skill that cites the operator's *workspace* `CLAUDE.md` (model-tier policy, workspace
  rules) is untouched. Named members so Step 106's predicate excludes them by construction:
  `skills/tier-escalate/core.md` (regenerates a paste-ready workspace section, never applies
  it — `:113`) and `skills/judge-motion/providers/claude.md:146` (workspace tier reference).
- The 46 legacy top-level `<skill>/SKILL.md` packages — policy-frozen per
  `CLAUDE.md § Directory layout`; deprecation-window record in
  `documentation/parity-deltas.md`. Accepted drift, D7.

---

## 4. Impact Analysis

**The authoritative classification is § 4.2 below, produced by Step 103 from the two enumeration
commands.** The artifact table in § 4.1 is a *change-surface* list — which files this phase touches
and why — and was always an INPUT, never a premise: plan-review round 1 proved its REFERENCE bucket
unreliable (it missed `citation-review` (a READ), `repo-update:164` (a READ inside a WRITE core) and
`plan-init:481`), and plan-wrap round 2 named three more candidates (`repo-sync`,
`observatory-doctor`, `build-phase`). **Wherever § 4.1 or the "needing NO change" list below
disagrees with § 4.2, § 4.2 governs** — it is the enumerated one. Step 104 repoints exactly what
§ 4.2's work-list names, and nothing else.

**Classification rules** (the taxonomy Steps 103 and 106 both consume):

- **WRITE** — the prose orders the agent to create, overwrite, or edit the file.
- **READ** — the prose orders the agent to open it for grounding or ground truth.
- **REFERENCE** — the file is named as an example, a locator, or a *workspace-level* artifact
  the skill never opens.

### 4.1 Change-surface table — which artifacts this phase touches (NOT the classification)

*Verdicts in the Reason column below are superseded by § 4.2 where the two differ. This table's
job is the Change Type column: create vs modify, per artifact.*

| File | Change Type | Reason | Verified |
|---|---|---|---|
| `skills/plan-init/core.md` | modify | WRITE core **and** contract owner: the bootstrap block, its skip guard, the seven authored sections, the write itself, the report string, the scrapability constraint, the post-save handoff. Per-line anchors dropped — they moved when Steps 100/101 landed; § 4.2 row 8 carries the governing site | `grep -n 'CLAUDE\.md'` → **39** lines / **41** occurrences |
| `skills/plan-init/providers/codex.md` | modify | `:11` names the bootstrapped `CLAUDE.md` as the file Codex writes | only provider file naming the written artifact |
| `skills/repo-update/core.md` | modify | WRITE core. The `What this skill does` instruction-file item; the stale-reference grep that hardcoded `README.md CLAUDE.md documentation/*.md`; Step 7; the report line; the dev-observatory hook (preserved). Step 102 has landed, so locate each by name, not by line — its edit moved every anchor this row originally carried | the stale-reference grep was missed by the round-1 audit |
| `skills/goblin-suggest/core.md` | modify | READ, breaks silently. `:33` is a **precondition**; a stub passes the existence check so the documented loud grounding failure never fires | `:13, :33, :102, :178` |
| `skills/build-observer/core.md` | modify | READ, breaks. `:57` has no AGENTS.md arm | `:57` |
| `skills/research-prospect/core.md` | modify | READ, breaks. `:61` baked into a dispatched sub-agent prompt | `:51, :61` |
| `skills/user-brainstorm/core.md` | modify | READ, breaks. `:154` grounding list | `:154` |
| `skills/user-learn/core.md` | modify | READ, breaks. `:161` states verbatim the failure a stub produces | `:47, :104, :161` |
| `skills/citation-review/core.md` | modify | READ — missed by round 1. `:12` names a project `CLAUDE.md` as a reviewable artifact class | `:12, :46-47` |
| `skills/context-slim/providers/claude.md` | modify | **WRITES** under `--apply` (`:166`); ancestor walk (`:21, :23-24`); classification (`:59-61`). **16 `CLAUDE.md` sites total**, incl. `:3` frontmatter and `:5` default | `ls skills/context-slim/` → `providers/claude.md` only |
| *(the round-2 candidates)* | **no change** | `repo-sync:51,:521`, `observatory-doctor:78`, `build-phase:31,:198,:229` — **all adjudicated REFERENCE** by § 4.2; none joins Step 104's work-list | § 4.2 |
| `tests/package-integrity/test_instruction_file_contract.py` | deferred / intentionally absent | future write-surface gate | deferred 2026-08-25; resurrection contract in § 10 |
| `tests/package-integrity/test_instruction_contract_single_owner.py` | create | single-owner gate | landed by Step 106 |
| `documentation/codex-instruction-delivery.md` | create | vendored measurement + reproduction recipe (§ 1's content, expanded) | landed by Step 107 |
| `documentation/host-discovery.md`, `documentation/architecture.md` | modify | document the inverted shape in the authority map and the contract | updated by Step 107 |
| `documentation/phase-75-baseline.md` | modify | single owner of the suite counts this plan changes | updated after Step 107's measured gate |

### Verified as needing NO change *(evidence corrected by § 4.2)*

`skills/plan-merge/core.md:232` (already both-file, confirm-gated `:234-235`) ·
`skills/plan-feature/core.md:50` · `skills/plan-review/core.md:201, 229, 463` ·
`skills/user-afterparty/core.md:103-104` (see D9) · `skills/review-uat/core.md:144, 148`
(fails safe, but § 4.2 nonetheless makes it work-list member 7 — the fail-safe is a fallback,
not a both-file read) ·
`skills/repo-wrap/core.md:35` (its ONLY `CLAUDE.md` site, and a **workspace** reference; the
`:124-126` cited earlier is the repo-update delegation and carries no `CLAUDE.md` literal at all —
same verdict, corrected evidence) ·
`config/skill-manifest.json` and `tools/gen_manifest.py` (paths, not core content).

**Canonical phrasing.** Steps 101–105 all adopt one spelling: **`CLAUDE.md or AGENTS.md`**, and D11
makes it the gate's marker. **Corrected by Step 103:** of the two sites this section previously
cited as existing uses, only `plan-review/core.md:229` carries the marker as a matchable literal.
`plan-merge/core.md:232` spells it with each filename separately backticked, so a gate keying on the
literal does not see it there. Enumerated marker sites at this baseline —
`grep -rno 'CLAUDE\.md or AGENTS\.md' skills/` → **14 sites in 4 files**:
`plan-init/core.md` (6), `repo-update/core.md` (6), `plan-init/providers/codex.md:11`,
`plan-review/core.md:229`.

### 4.2 Authoritative classification — Step 103

**This is the authoritative table for this phase.** It is derived mechanically from both arms of the
enumeration, not hand-listed:

**Execution-history boundary.** The classification remains evidence for the landed reader repairs,
but forward-looking instructions in this subsection that assign the write-surface gate to Step 106
are historical. Step 106 landed only the single-owner gate; § 10 supersedes those instructions and
owns the write-surface gate's resurrection conditions.

```
grep -l 'CLAUDE\.md' skills/*/core.md          # 24 hits, of 54 cores
grep -l 'CLAUDE\.md' skills/*/providers/*.md   # 3 hits, of 165 provider files
```

Both arms reproduced § 2's expected counts exactly — **24** and **3** — against denominators
re-measured at the same commit (**54** `core.md`, **165** provider files, **57** skill directories).
No discrepancy to report. Step 106 must re-derive those denominators at test time, never copy them
from here.

Finding 8 is the single statement of what that denominator does and does not cover; this section
deliberately does not restate it.

**Verdicts** are § 4's three rules, applied to the *governing site* — the one line that drives the
classification. Other `CLAUDE.md` sites in the same file are listed after it and change nothing.
Every guarded-vs-unguarded judgement below assumes **`##`-heading scoping** for D11's undefined
"its section"; finding 9 states why that choice flips real verdicts.

**Scope** is the distinction this whole step exists to draw:

- **PROJECT** — the file named is a *project's own* instruction file. Inside the contract.
- **WORKSPACE** — the operator's workspace `CLAUDE.md` (model-tier policy, parallel-session rules,
  dispatch rules). The contract owner section places these **outside the contract entirely**.
  **Step 104 must never repoint a WORKSPACE site**, and Step 106's predicate must exclude them by
  construction (§ 3 already names two; § 4.2 now names all nine).
- **PROJECT (locator)** — a project instruction file named only as *where a thing is defined*, or as
  a directory marker for an existence test. The skill never opens it, so the rule makes it
  REFERENCE, not READ.

| # | Surface | Governing site | Verdict | Scope | Other sites in file | Step 104 |
|---|---|---|---|---|---|---|
| 1 | `skills/build-observer/core.md` | `:57` — "read whichever exist: `README.md`, `CLAUDE.md`, `plans/plan.md`" | READ | PROJECT | — | **REPOINT** |
| 2 | `skills/build-phase/core.md` | `:31` — a UI smoke command "defined in the project's CLAUDE.md"; never opened | REFERENCE | PROJECT (locator) | `:198`, `:229` (locator); `:464` (WORKSPACE) | no |
| 3 | `skills/build-step/core.md` | `:456` — "tier policy, CLAUDE.md model paragraph" | REFERENCE | WORKSPACE | — | no |
| 4 | `skills/citation-review/core.md` | `:12` — names a `CLAUDE.md` as a reviewable artifact class; `:50` then opens it via `cite review open <path>` | READ | PROJECT | `:50` | **REPOINT** |
| 5 | `skills/goblin-suggest/core.md` | `:33` — a **precondition**: target "has a `CLAUDE.md` ... (grounding fails loud otherwise)" | READ | PROJECT | `:13`, `:102`, `:178` | **REPOINT + precondition** |
| 6 | `skills/observatory-doctor/core.md` | `:78` — where the operator's fix lives; `:84` forbids auto-applying | REFERENCE | PROJECT (locator) | — | no |
| 7 | `skills/plan-feature/core.md` | `:50` — "README, CLAUDE.md, AGENTS.md, any existing `documentation/*.md` plans" | READ | PROJECT | — | no — already names both |
| 8 | `skills/plan-init/core.md` | `:568` — row 1 authors `AGENTS.md`, writes the pointer | WRITE | PROJECT | contract owner at `:439`; 39 sites total | done (Steps 100, 101) |
| 9 | `skills/plan-merge/core.md` | `:232` — "update if they name the old plans", confirm-gated at `:234-235` | WRITE | PROJECT | — | no — names both (see marker note) |
| 10 | `skills/plan-review/core.md` | `:229` — "If the project has a CLAUDE.md or AGENTS.md with conventions" | READ | PROJECT | `:201`, `:463` | no — already canonical |
| 11 | `skills/repo-sync/core.md` | `:51` — names the project's `CLAUDE.md` as where a UI smoke command is defined | REFERENCE | PROJECT (locator) | `:521` (same phrase, inside the emitted issue body) | no |
| 12 | `skills/repo-update/core.md` | `:291` — row 2 refreshes `CLAUDE.md` in place | WRITE | PROJECT | `:52`, `:165-171`, `:243`, `:506`; 38 sites total | done (Step 102) |
| 13 | `skills/repo-wrap/core.md` | `:35` — "the workspace `CLAUDE.md` §§ Parallel session safety" | REFERENCE | WORKSPACE | — | no |
| 14 | `skills/research-prospect/core.md` | `:61` — "`<PROJECT_DIR>/CLAUDE.md` — stack, commands, known gotchas", inside a dispatched sub-agent prompt | READ | PROJECT | `:51` (WORKSPACE tier policy) | **REPOINT** |
| 15 | `skills/review-uat/core.md` | `:144` — "determine the target shell from the project's CLAUDE.md or workspace instructions" | READ | PROJECT | `:148` (the fail-safe default) | **REPOINT** |
| 16 | `skills/session-wrap/core.md` | `:60` — "plan located per CLAUDE.md § Plan location", restated inline | REFERENCE | WORKSPACE | `:184` | no |
| 17 | `skills/skill-iterate/core.md` | `:588` — "workspace `CLAUDE.md` § Parallel session safety" | REFERENCE | WORKSPACE | — | no |
| 18 | `skills/task-handoff/core.md` | `:21` — "CLAUDE.md § Session wrap & commit discipline" | REFERENCE | WORKSPACE | — | no |
| 19 | `skills/test-prune/core.md` | `:25` — "tier policy, CLAUDE.md model paragraph" | REFERENCE | WORKSPACE | — | no |
| 20 | `skills/tier-escalate/core.md` | `:113` — "never edits CLAUDE.md ... regenerated output, never applied" | REFERENCE | WORKSPACE | `:14`, `:20`, `:26`, `:73`, `:97`, `:109` | no |
| 21 | `skills/user-afterparty/core.md` | `:104` — "nearest ancestor directory ... that contains a CLAUDE.md"; an existence test, never an open | REFERENCE | PROJECT (locator) | `:107`, `:134`, `:145`, `:194` (locator); `:36`, `:47`, `:172`, `:442` (WORKSPACE) | no — D9 pins the anchor |
| 22 | `skills/user-brainstorm/core.md` | `:154` — "Project root `CLAUDE.md` if present", in the per-agent grounding list | READ | PROJECT | `:81` (WORKSPACE tier policy) | **REPOINT** |
| 23 | `skills/user-gateway/core.md` | `:106` — "CLAUDE.md's dispatch rule" | REFERENCE | WORKSPACE | — | no |
| 24 | `skills/user-learn/core.md` | `:161` — "read their CLAUDE.md; generic ... is the failure mode" | READ | PROJECT | `:47`, `:104` (further project reads); `:52` (WORKSPACE); `:66` (an example project's files) | **REPOINT** |
| 25 | `skills/context-slim/providers/claude.md` | `:166` — under `--apply`: "Read the target CLAUDE.md; append a `## Topic-specific guidance` section" | WRITE | PROJECT | all 19 lines, 20 occurrences (`:21` carries two): `:3` frontmatter · `:5` `--project` default · `:15` trigger · `:21`, `:23`, `:24` ancestor walk · `:30` rules-link scan · `:40`, `:41` report rows · `:55` tier note (WORKSPACE) · `:59`, `:61` Agent A classification · `:76` MOVE OUT pointer · `:132` `dev/CLAUDE.md` cell (WORKSPACE) · `:139` needs-review list · `:199` apply summary · `:213` never-auto-apply · `:216` missing-rules rule | Step 105 |
| 26 | `skills/judge-motion/providers/claude.md` | `:146` — "owner: the workspace CLAUDE.md" | REFERENCE | WORKSPACE | — | no |
| 27 | `skills/plan-init/providers/codex.md` | `:11` — names the bootstrapped instruction file the core writes | WRITE | PROJECT | — | done (Step 101) |

**Bucket totals — `WRITE = 5`, `READ = 9`, `REFERENCE = 13`, summing to the 27 enumerated hits.**

### 4.2.1 The REFERENCE bucket, enumerated by name

Step 106's write-surface gate must prove it produces **no false positive against this bucket**, which
is only checkable if the bucket is a list. All 13 members, with the site that classifies them:

**WORKSPACE `CLAUDE.md` — outside the contract entirely (9 members).** These name the operator's
workspace instruction file, not any project's. § 3 already named two of them; here are all nine:

`skills/build-step/core.md:456` · `skills/judge-motion/providers/claude.md:146` ·
`skills/repo-wrap/core.md:35` · `skills/session-wrap/core.md:60` ·
`skills/skill-iterate/core.md:588` · `skills/task-handoff/core.md:21` ·
`skills/test-prune/core.md:25` · `skills/tier-escalate/core.md:113` ·
`skills/user-gateway/core.md:106`

**PROJECT instruction file named as a locator, never opened (4 members).**

`skills/build-phase/core.md:31` · `skills/observatory-doctor/core.md:78` ·
`skills/repo-sync/core.md:51` · `skills/user-afterparty/core.md:104`

Nine plus four is the full thirteen, and no surface appears in both runs.

**The false-positive count against this bucket is predicate-relative — do not record a single
number.** Two review rounds produced four different counts against these same 13 members — 1, 2, 4
and 9 — and none was wrong. The count is a property of **D11's predicate**, which is unpinned on
five independent axes:

| Axis | The competing readings | Owner today |
|---|---|---|
| Token matching | exact token (`write`) vs inflected (`writes` / `written` / `writing`) | unstated |
| Verb-to-filename binding | verb on the same LINE as the `CLAUDE.md` vs anywhere in the same section | unstated |
| Marker lookup scope | `##`-heading scope | finding 9 — the one axis this plan settles |
| Negation awareness | does "never edits CLAUDE.md" suppress a match? | unstated |
| Path qualification | is `dev/CLAUDE.md` (workspace) the same token as a bare project `CLAUDE.md`? | unstated |

Measured over the 13 members at this baseline:

| Reading (binding / tokens) | FP | Members flagged |
|---|---|---|
| same-line / exact | **0** | none |
| same-line / inflected | **2** | `skill-iterate:588` (`written`) · `tier-escalate:113` (`writes`) |
| `##`-co-occurrence / exact | **9** | build-step:456 · judge-motion:146 · session-wrap:60 · skill-iterate:588 · task-handoff:21 · tier-escalate:73 · build-phase:198 · repo-sync:51 · user-afterparty:36 |
| `##`-co-occurrence / inflected | **10** | the nine above, plus `repo-wrap:35` |

**Two careful implementations of the SAME reading disagreed — resolved: the axis was case.** An
independent arm measuring the co-occurrence rows got 8 and 9 where this measurement gets 9 and 10.
Not the hyphen convention: `build-phase`'s `## Flow` (`:155-313`) carries a bare `write` at `:290`
and `Create` at `:306`, so it flags either way. The **sole** delta member is
`judge-motion/providers/claude.md:146`, whose governing `## Vision-judge dispatch` (`:137-283`)
carries exactly one line with a five-list verb — `:213`, spelled `Write`, with no lower-case one
anywhere in the section. Case-sensitively that section matches nothing and the member drops;
case-insensitively it flags. The other twelve members are case-invariant, so the two arms differ by
exactly this one site. **The printed 9 and 10 are the case-insensitive figures** — consistent with
the pin's case bullet, not in tension with it. The lesson survives the resolution: this count is a
property of a stated pin and must be derived, never asserted.

**The pin § 4.2's verdicts assume.** Every verdict above was reached under this reading, and Step 106
must implement it to reproduce them:

- **Token matching** — exact whole-word tokens only: `write` / `save` / `create` / `bootstrap` /
  `refresh`. No inflections; **case-insensitive**, which is how § 4.2's verdicts were measured — row
  12's governing site `repo-update:291` spells its verb `Refresh`, so a case-sensitive predicate
  could not reproduce that WRITE verdict. This bucket measures FP = 0 under either case convention.
- **Verb-to-filename binding** — the verb must sit on the **same line** as the `CLAUDE.md` it governs.
- **Marker lookup** — `##`-heading scope, per finding 9.
- **Path qualification** — exempt **only** the literal workspace spellings `dev/CLAUDE.md` and the
  prose "workspace `CLAUDE.md`". A *project*-path-qualified spelling is **in scope, not exempt**:
  `<dev-root>/<name>/CLAUDE.md` (`context-slim/providers/claude.md:21` — the resolution of the very
  file `:166` writes to) and `<PROJECT_DIR>/CLAUDE.md` (`research-prospect:61`) are PROJECT in § 4.2.
- **Negation awareness** — **none; the predicate is negation-blind.** § 4.2's recorded verdicts do
  not discriminate this axis, so the pin chooses rather than reads it off. Measured over
  `skills/*/core.md` + `skills/*/providers/*.md`, with the verb list, same-line binding, `##` marker
  lookup and path qualification held to the pin, UNGUARDED is **0 in all 16 combinations** of case
  × fenced-block awareness × negation × pre-first-`##` unit — so Step 106's zero-count `Done when`
  is safe whichever way this resolves. What the choice *does* move is the **positive-control** set:
  negation awareness removes **6** sites in every combination (19 → 13 case-insensitive and
  fence-aware; 15 → 9 case-sensitive and fence-aware). Finding 10 records that the gate has zero
  live true positives, so this axis decides what Step 106 can plant as a control. Negation-blind is
  also what the withdrawn-exclusion note below already implies: exclusion comes from the pin, never
  from reading negations.

**Under this pin the bucket measures 0 false positives with zero per-site exemptions** (row 1 of the
measurement table). That is what makes Step 106's "false-positive count … is zero" clause satisfiable
rather than impossible — but only if the pin is adopted. Under any looser reading the clause fails,
and narrowing the predicate ad hoc until it reaches zero is exactly the failure finding 10 describes.

**Pinning D11 formally is an OWNER-SECTION edit, and it belongs to Step 106.** The predicate's
normative home is `skills/plan-init/core.md:525-526`, which Step 103 may not touch. Step 106's
`Files:` line now carries `skills/plan-init/core.md`, so the pin has somewhere to land: write the
five axes into the owner section there, and key the test on them.

**Sites that wider readings flag, with dispositions** — recorded so Step 106 need not rediscover them:

- `skills/tier-escalate/core.md:113` reads "This skill never edits a `SKILL.md`, never edits
  CLAUDE.md, and never changes any model setting. **It writes the map;** the operator escalates per
  session." Flagged by any inflected reading, and by exact-token co-occurrence via `:114`'s "cannot
  edit or write". Semantically REFERENCE — both verbs govern the *map* the skill emits, not the
  instruction file. **Cleared by the pin.**
- `skills/skill-iterate/core.md:588` (`written`) — the verb governs the m2-launcher's untracked log
  directory, and the `CLAUDE.md` on that line is the **workspace** file. `AGENTS.md` = 0 and
  marker = 0, so it can never become guarded. **Cleared by the pin's exact-token axis.**
- `skills/context-slim/providers/claude.md:132` — the report-template row
  `| rules/python.md | dev/CLAUDE.md | MISSING — create to fix broken link |`: exact verb `create`,
  naming the **workspace** file. It is **not in this bucket** (its file is WRITE-classified via
  `:166`), so a clean-bucket proof does not cover it — yet it reds the gate itself unless excluded.
  It can never be *guarded*: § 4.2 forbids repointing a WORKSPACE site and Step 105's scope does not
  reach it, so a marker there would be a lie. **Cleared only by the pin's path-qualification axis** —
  which is why that axis is in the pin. `:216` (`creating`) is the same shape, cleared by
  exact-token matching.

**A negation-aware exclusion rule does not work, and the suggestion has been withdrawn.** An earlier
draft of this section offered one; the flagging verb at `tier-escalate:113` is `writes` in the
*un-negated* clause "It writes the map", so a predicate suppressing on "never edits" still flags the
line. Exclusion must come from the pin, not from reading negations.

### 4.2.2 The round-2 candidates, adjudicated

Each was flagged by plan-wrap round 2 as uncertain. **All three groups resolve to REFERENCE; none
joins Step 104's work-list.**

- **`repo-sync:51` and `repo-sync:521` → REFERENCE, PROJECT (locator).** Both carry the same
  parenthetical — UI evidence may be "any project-specific UI/dashboard smoke commands defined in
  the project's `CLAUDE.md`". `:51` is repo-sync's own rule for grading an issue body's `Done when`;
  `:521` is the same phrase inside the issue body repo-sync *emits*. Neither orders repo-sync to open
  the file: it names where a command is *defined*, and repo-sync checks only that the issue
  references UI evidence at all. Not a READ (no open is ordered) and not a WRITE. Because it is a
  **project** file being named, a future step could choose to widen the spelling for tidiness, but
  nothing breaks on an inverted project — repo-sync's behavior does not depend on the file.
- **`observatory-doctor:78` → REFERENCE, PROJECT (locator).** The line tells the operator where a
  broken scraped command's fix lives ("in the project's `CLAUDE.md`"), and `:84` immediately forbids
  the skill from acting: "Do not auto-apply any of these — hand the operator the `open-repo` command
  and let them decide." So it neither writes nor reads; it points a human at a path. Note for Step
  106: the `CLAUDE.md` line itself carries no write verb — the "Fix the path" clause opens on the
  preceding line (`:77`) — and "Fix" is not in D11's write-verb list either way.
- **`build-phase:31`, `:198`, `:229` → all REFERENCE, PROJECT (locator).** `:31` names the project's
  `CLAUDE.md` as where a project-specific UI smoke command may be defined; build-phase's actual
  behavior is to check whether the plan step declared `--ui` and emit a UI-MISSING note. `:198`
  says projects "extend the list via their `CLAUDE.md`" while the shipped heuristic is an explicit
  hard-coded substring match and the line itself calls per-project enumeration "a follow-up" — so no
  read happens today. `:229` is a literal inside the always-print Step 0 output template, i.e. text
  build-phase *prints*. A fourth site, `:464`, is a **WORKSPACE** reference (Git Bash availability)
  and is out of the contract on scope grounds.

### 4.2.3 Derived work-list for Step 104

Step 104's bucket is **READ ∩ PROJECT ∩ not-already-both-file**. Applying that formula to the table
yields **seven** members:

| Core | Site | Why it breaks on an inverted project |
|---|---|---|
| `skills/build-observer/core.md` | `:57` | preference list has no `AGENTS.md` arm; reads the pointer and finds no stack/commands |
| `skills/citation-review/core.md` | `:12` | the reviewable artifact class omits `AGENTS.md`, so an inverted project's real instruction file is out of scope for review |
| `skills/goblin-suggest/core.md` | `:33` | existence-only precondition: a POINTER satisfies it, so the documented loud grounding failure never fires |
| `skills/research-prospect/core.md` | `:61` | baked into the dispatched sub-agent prompt; the agent reads a one-line pointer as "the project's context" |
| `skills/review-uat/core.md` | `:144` | reads the shell declaration from `CLAUDE.md` only (the file measures `AGENTS.md` = 0); on an inverted project it silently loses the project's declared shell |
| `skills/user-brainstorm/core.md` | `:154` | grounding list names one filename; on an inverted project every fan-out arm grounds on a pointer |
| `skills/user-learn/core.md` | `:161` | states verbatim the failure a pointer produces ("generic 'you could use this for X'") |

**Six were named in advance; `review-uat:144` is the one member Step 103 adds.** Step 104's Problem
field lists the other six as *known* members "plus whatever Step 103 added" — that qualifier resolves
to `review-uat:144`, and to nothing else. Step 104's `Files:` line has been extended to match.

§ 4.1 had cleared `:144` as needing no change because it fails safe, and that remains true as a
*safety* claim: `:148` defaults to PowerShell-safe syntax when the shell is ambiguous. But the safety
comes from that fallback, not from the line having considered both files, and the line satisfies all
three conjuncts of the formula above. **It is therefore a required member, not a discretionary one.**
A bucket defined by a formula cannot carry a hand-excluded exception without making § 4's "Step 104
repoints exactly what § 4.2's work-list names, and nothing else" false — which would leave Step 104
holding two contradictory instructions for the same line. Repointing it is one phrase with no
behavior risk.

Two cores carry additional project-read sites, and **Step 104 repoints them in the same pass**:
`user-learn:47` and `:104` alongside `:161`, and **`goblin-suggest:102`** ("read its real
CLAUDE.md + plan + open issues") alongside `:33`. The goblin-suggest pairing is the load-bearing
one: once Step 104 repairs the `:33` precondition so a POINTER fails loud, a project that passes
the repaired precondition still grounds on the pointer at `:102` — silently, which is the exact
failure mode `:33` exists to prevent. Leaving some sites in a core single-filename is the drift
this phase exists to remove.

**Two READ-of-a-PROJECT-file cores are deliberately NOT on the list**, because they already name
both files: `plan-feature/core.md:50` ("README, CLAUDE.md, AGENTS.md") and
`plan-review/core.md:229` (the canonical marker verbatim). Both keep § 4.1's "no change" verdict, now
on enumerated evidence rather than assertion.

### 4.2.4 Findings this enumeration produced

Recorded because each is an input another step consumes, and none is repaired here (Step 103 changes
no behavior and edits no core):

1. **`plan-merge:232` does not carry the canonical marker as a literal** — it backticks each filename
   separately. § 4's earlier "already used at `plan-merge:232`" claim is corrected above. Today the
   write verb on that line is "update", which is not among D11's five, so Step 106's gate does not
   flag it — but that immunity is incidental, not designed, and finding 2 shows why it matters.
2. **D11's write-verb list omits `append`, and that is how one of the two unguarded
   project-`CLAUDE.md` writes is spelled.** `context-slim/providers/claude.md:166` appends to a
   project's `CLAUDE.md` under `--apply`, and that file contains **zero** occurrences of `AGENTS.md`,
   so the write is unguarded by D11's own definition — yet a gate matching only
   `write`/`save`/`create`/`bootstrap`/`refresh` cannot see it. It is one of *two* unguarded writes in
   the bucket, not the only one: `plan-merge:232` is the second, per finding 1.
   **The verb list has an owner — `skills/plan-init/core.md:525-526`**, inside the contract section.
   Closing the hole is therefore an **owner-section edit, not a test-file edit**, and Step 106's
   `Files:` line has been extended with `skills/plan-init/core.md` so that branch is actually
   reachable; without it the only outcome Step 106 could reach was "accept the hole", and the phase
   would have shipped a contract telling future skill authors that an unguarded `append` to a user's
   project `CLAUDE.md` is legal. The edit is narrow — extending one verb list — and must not
   relegislate the matrix or any other part of the contract. Step 105 repairs the `context-slim`
   surface; Step 106 decides the verb list, and **if it accepts the hole instead it must say so in the
   test.** Two couplings to weigh before widening: adding `append` also flags `tier-escalate:73`
   (§ 4.2.1's known false positive), and adding `update` also flags `plan-merge:232` — a WRITE/PROJECT
   site that no step's `Files:` line can currently repair.
3. **`context-slim` names `CLAUDE.md` at 19 lines / 20 occurrences, not the 16 stated** in § 4.1 and in
   Step 105's Problem field. Step 105's instruction to enumerate all of them rather than work from the
   cited four is unaffected in substance; the stated number is stale and the enumeration governs.
4. **§ 4.1's `repo-wrap:124-126` citation names no `CLAUDE.md` line.** Those lines are the Rail A
   delegation to repo-update. The file's only `CLAUDE.md` site is `:35`, a workspace reference. Same
   verdict, corrected evidence — and the delegation independently corroborates that repo-wrap does no
   instruction-file handling of its own.
5. **§ 2's "3 name `AGENTS.md` (`plan-feature`, `plan-merge`, `plan-review`)" is a pre-Step-100
   measurement.** At this baseline it is **5 cores** (those three plus `plan-init` and `repo-update`)
   and **1 provider file** (`plan-init/providers/codex.md`). Not a defect — Steps 100–102 landed the
   difference — but Step 106 must re-derive rather than trust the stated three.
6. **The `CLAUDE.md`-arm count will move as this phase lands.** 24 cores and 3 provider files is the
   figure at this baseline; Steps 104 and 105 add `AGENTS.md` alongside, which changes the `AGENTS.md`
   arm but not the `CLAUDE.md` arm (no repoint deletes the `CLAUDE.md` mention — the canonical spelling
   keeps both filenames). Step 106's floors are therefore re-derived, never these numbers.
7. **`tier-escalate` — see § 4.2.1**, which owns the counts, the `path:line`s, and what they do to
   Step 106's zero-false-positive clause. Nothing is restated here.
8. **§ 4.2's denominator is `skills/**` — 54 cores plus 165 provider files — not the repository.** The
   46 legacy top-level `<skill>/SKILL.md` packages sit outside both globs. They are git-tracked, so
   `release.ps1` stages them via `git ls-files`, and three carry unguarded project `CLAUDE.md` writes
   measured at this baseline (each of those files has `AGENTS.md` = 0): `context-slim/SKILL.md:166`
   (`append`), `plan-init/SKILL.md:461` (`Save`), and `repo-update/SKILL.md:230` (`Create`). **Two of
   the three qualify under the existing five-verb list with no widening at all** — both spellings
   are sentence-initial, so this holds only under the pin's case-insensitive token matching. D7 accepts
   the legacy tree as drift and § 3 puts it out of scope — **this finding does not re-open D7** — but
   D7 records that tree as *stale content*, never as *live unguarded writes*. Stated here so the word
   "authoritative" carries its true scope rather than an unwritten denominator.
9. **D11's predicate unit "its section" is undefined, and the granularity flips real verdicts.**
   § 4.2 assumes **`##`-heading scoping** — nearest preceding `##` heading through to the next one.
   The choice is load-bearing. `repo-update:243` is `## Step 7 — Refresh the project instruction file
   (CLAUDE.md or AGENTS.md)`: the heading itself carries the marker, so every write in rows 2–5
   beneath it is guarded, and `plan-init:546` guards its rows the same way. Under paragraph- or
   bullet-scoping instead, `repo-update` rows 3–4 (`:298-309`) and `plan-init` rows 3–4 (`:577-584`)
   contain **no** marker and would both read as unguarded — turning two correct writer cores red.
   Step 106 must implement `##`-heading scoping to reproduce these verdicts, and must state the unit
   in the test rather than leaving it implicit.
10. **The write-surface gate is unfalsifiable as Step 106 currently specifies it. This is the most
    consequential finding in this section.** After Steps 104 and 105 land, the gate has **zero live
    true positives**: all five WRITE sites are either marker-guarded (`plan-init:568`,
    `repo-update:291`, `plan-init/providers/codex.md:11`, and `context-slim:166` once Step 105 guards
    it) or invisible to D11's five verbs (`plan-merge:232`, whose verb is `update`). Zero live true
    positives is normal for a preventive gate — the defect is that Step 106's proofs cannot detect a
    predicate narrowed into uselessness. All six required planted defects are author-spelled with
    in-list verbs and nearby markers, so a predicate narrowed until the false-positive count reaches
    zero still passes every one of them, and the gate would prove nothing. **Step 106 must therefore
    add, beyond its six:** (a) **one planted unguarded write per covered verb** — `append` included if
    adopted — each proven red and restored, so the verb list is exercised rather than asserted; and
    (b) **one far-marker proof** — a write with no marker in its own `##` section whose nearest
    canonical marker sits >100 lines away **under a different `##` heading**, proven red: the arm
    that distinguishes a genuinely `##`-scoped lookup from a whole-file marker search. (Under
    finding 9's unit a same-section marker guards however distant, **by design**: `repo-update:243`
    carries the marker in the `##` heading itself and so guards all 125 lines through `:367`.
    Nothing bounds a section's length, so the cheapest way to green a red gate is to plant a marker
    at the top of a long section — a live hazard of the chosen unit, not a target of (b).)
11. **Step 106's Problem and its `Done when` contradict each other on exactly this point, and the
    contradiction predates Step 103.** The Problem says to report the measured false-positive count
    "**rather than asserting zero**"; the `Done when` requires that the count "is reported and **is
    zero**". § 4.2.1 resolves the tension in the Problem's favour by supplying a pin under which zero
    is a *measured* result rather than an assertion — but the two clauses still read differently, and
    Step 103 does not amend another step's acceptance criteria. **Recorded for the operator, not
    repaired here.**

---

## 5. New Components

- **A named `## Instruction-file contract` section in `skills/plan-init/core.md`** — the ONE
  owner, holding D8, D10 and D11 including their designated probe literals. No new file, no
  new payload surface (D6).
- **`documentation/codex-instruction-delivery.md`** — the vendored measurement and recipe.
- **`tests/package-integrity/test_instruction_contract_single_owner.py`** — the single-owner
  gate.

---

## 6. Design Decisions

**P1 — `plan-init` emits the inverted shape when it authors an instruction file.** *(operator,
2026-08-20.)* Scoped by D10: it applies to D10 row 1 (both files ABSENT) only. It **never
overwrites an existing SUBSTANTIVE `CLAUDE.md`**. *Rejected:* detect-then-follow; an opt-in flag.

**P2 — `repo-update` reports drift as an always-print advisory that never blocks.** *(operator,
2026-08-20.)* The in-repo implementation contract is `skills/repo-update/core.md:310-318`; it keeps
the `/build-phase` halt allowlist closed. Load-bearing because `/repo-update` also runs
**unattended** inside phase wraps and via
`/repo-wrap` Rail A — its registered-owned-project rail, which delegates verbatim to
`/repo-update` (`skills/repo-wrap/core.md:124-126`).

**D3 — Resurrection contract for the deferred write-surface gate.** If resurrected, it enumerates
`skills/*/core.md` **and** `skills/*/providers/*.md`, each arm carrying its own non-empty floor
re-derived at test time (54 and 165 per § 2), because one combined floor is satisfiable while an
arm is empty. Implementation is deferred under § 10. D6 removes the would-be third surface rather
than gating it. *Rationale:* this
repository closed #142 on 2026-08-20 — a gate whose enumeration set was narrower than the
product. The first draft of this plan reintroduced that shape.

**D4 — Fix what the Step 103 enumeration proves breaks.** Not a fixed list.

**D5 — skill-mesh's own root files are not touched, and the cost is recorded.** Frozen by
`test_recovery_plan_hygiene.py:41-60`. The catalog can *emit* the inverted shape without *being*
in it, which is what makes backward compatibility real. **The cost:** by this plan's own
premise a Codex session in *this* repository receives no project content, because its
`AGENTS.md` is an inert prose pointer. Accepted here; it belongs to the wider proposal's Phase 1.

**D6 — The contract is a named section in one owning core. NO `_shared/` file is created.**
Reverses the first draft, on four measured grounds:
1. A `_shared/` file would be a **third instruction-authoring surface** D3's two globs cannot
   open — #142 reproduced by the fix for #142.
2. Cores may cite `_shared/` only as the literal `<repo>/_shared/<leaf>`; every relative
   spelling is a new dangling reference against a **shrink-only** allowlist.
3. **Adapters are forbidden that spelling** (`test_distributions.py:770-777`), so
   `context-slim` — an adapter with no core — could not cite the owner in *any* legal spelling.
4. The payload is a **citation-seeded transitive closure**, so a Done-when asserting the file is
   emitted is unsatisfiable before anything cites it.

**D7 — Legacy `<skill>/SKILL.md` packages stay stale, recorded as accepted drift.**
Policy-frozen; deprecation-window record in `documentation/parity-deltas.md`.

**D8 — Instruction-file states are THREE-VALUED and defined for BOTH filenames.** *(Promoted
from an open question; corrected in round 2, which proved a two-valued definition made an
absent file read as substantive and killed P1.)*

For either `AGENTS.md` or `CLAUDE.md`:

- **ABSENT** — the path does not exist.
- **POINTER** — the file exists but its whole body defers to the other file: it contains an
  `@AGENTS.md` import line, **or** a prose sentence directing the reader to the sibling file,
  and carries **no `##` section heading**. (§ 1: a prose pointer is inert on both hosts. A
  pointer may legally carry a comment line; byte thresholds are rejected.)
- **SUBSTANTIVE** — the file exists and is not a POINTER. A `##` section heading is the typical
  shape, never a necessary condition.

The three are exhaustive and mutually exclusive. "Stub" is a synonym for POINTER and is not
used normatively below.

**Worked example — this repository's own root pair.** `AGENTS.md` is 6 lines,
"Load and follow `CLAUDE.md` in full", no `##` heading → **POINTER**. `CLAUDE.md` has many `##`
headings → **SUBSTANTIVE**. That is D10 **row 2**, not row 4 — so `/repo-update` keeps
refreshing this repository's `CLAUDE.md` exactly as today, and no drift advisory fires. Any
implementation that classifies this pair as row 4 is wrong.

**The emitted `CLAUDE.md` pointer is exactly these bytes**, and nothing else — a single line
plus a trailing newline:

```
@AGENTS.md
```

**D9 — `user-afterparty`'s resolution parity is preserved by construction.** It pins "current
project" to "nearest ancestor containing a `CLAUDE.md` — the same resolution `context-slim`
itself already uses" (`:103-104`). Step 105 therefore **keeps context-slim's CLAUDE.md-anchored
ancestor walk** — an inverted project still has the pointer file, so the walk still resolves —
and changes only what context-slim *reads and appends to*.

**D10 — The behavior matrix, in D8's three-valued terms.** Every writer step implements exactly
this. POINTER-`A` is treated as ABSENT (an inert pointer is not content).

| `A` | `C` | `plan-init` | `repo-update` |
|---|---|---|---|
| ABSENT | ABSENT | Author `A` (seven sections); write `C` as the D8 pointer | Same — this is its create-if-absent path |
| ABSENT / POINTER | SUBSTANTIVE | **Touch neither.** Report the project is non-inverted | **Refresh `C` in place, exactly as today.** Never create `A` |
| SUBSTANTIVE | POINTER *(inverted)* | Refresh `A`; leave `C` untouched | Refresh `A`; leave `C` untouched |
| SUBSTANTIVE | ABSENT | Refresh `A`; write `C` as the D8 pointer | Refresh `A`; write `C` as the D8 pointer |
| SUBSTANTIVE | SUBSTANTIVE *(drift)* | Do not write. Report drift | Refresh **neither**; emit the P2 advisory naming both paths; continue |

Row 2 is the dominant case — roughly 32 projects — and is what makes this plan non-migrating.
**The only path that creates an `AGENTS.md` is row 1 (both ABSENT).** Rows 3 and 4 are fixed
points: re-running either skill converges.

**D11 — A GUARDED `CLAUDE.md` write is legal; an unguarded one is not. This is what the gate
keys on.** *(Added in round 2, which proved Step 106's original predicate forbade exactly what
D10 row 2 requires.)*

D10 row 2 obliges `repo-update` to keep writing `CLAUDE.md` on ~32 projects, so a gate asserting
"no surface writes `CLAUDE.md`" would red on correct output. The distinction the gate enforces:

- **Legal (guarded)** — the write is inside a section that also carries the canonical marker
  **`CLAUDE.md or AGENTS.md`**, i.e. the prose demonstrably considered both files.
- **Illegal (unguarded)** — a `CLAUDE.md` write verb (`write`/`save`/`create`/`bootstrap`/
  `refresh`) with no such marker anywhere in its section.

**Designated probe literals.** These exact strings live in the owner section and nowhere else
under `skills/`; the single-owner gate probes for them, and any future resurrected write-surface
gate must exclude their own section:

- the sentinel comment `<!-- instruction-file-contract: owner -->`
- the sentence `Instruction-file states are three-valued`

**Bounded cite-site minimum.** A citing core or adapter carries **only** the phrase
`see the Instruction-file contract in plan-init/core.md` plus, where it must act, the canonical
marker `CLAUDE.md or AGENTS.md`. It must **not** carry either designated probe literal — those
are the canaries that distinguish a legal citation from a re-duplication. This is the same
mechanism `test_autofix_marker_single_owner.py` uses.

**Classification statements required by the planning contract**

- **Autonomous-behavior trigger does NOT fire.** No daemon, scheduled job, soak or watcher.
  Precision P2 depends on: `/repo-update` is not purely operator-invoked — it runs unattended
  inside phase wraps — which is why its drift path must never block.
- **Data-pipeline trigger DOES fire and is handled by a prose-analogue smoke gate.** The
  contract is a shared definition multiple cores must agree on. A runtime smoke gate cannot
  exist for prose; the achievable analogue is the single-owner gate (Step 106), proven here by
  `test_autofix_marker_single_owner.py`. Steps 108–109 are the executed end-to-end confirmation.
- **Prose-core limitation, stated honestly.** A test can assert what the prose *instructs*,
  never what an agent *does*. Steps 108 and 109 exist because that gap cannot be closed by
  pytest.

---

## 7. Build Steps

### Step 100: Define the instruction-file contract in one owning core
- **Problem:** D8, D10 and D11 exist nowhere in the catalog. Add a named `## Instruction-file contract` section to `skills/plan-init/core.md` as the ONE owner, holding D8's three states and worked example, D8's exact pointer bytes, D10's five-row matrix, and D11's guarded/unguarded rule plus its two designated probe literals and the bounded cite-site minimum. Do **not** create a `_shared/` file (D6). Do **not** move or merge the seven-section bodies (§ 3). Add the bounded citation to `skills/repo-update/core.md`.
- **Type:** code
- **Issue:** #144
- **Files:** skills/plan-init/core.md, skills/repo-update/core.md
- **Flags:** --reviewers code
- **Produces:** the owner section; a bounded citation in repo-update's core
- **Done when:** the owner section carries D8, D10, D11, both probe literals and the exact pointer bytes; repo-update carries only the bounded cite phrase and neither probe literal; **no `_shared/` file was created**; no new dangling reference; the repo-root `python -m pytest` (no path argument) is green at or above the count recorded in `documentation/phase-75-baseline.md`, skip count unchanged
- **Depends on:** none
- **Status:** DONE (2026-08-24)

### Step 101: plan-init authors AGENTS.md-primary, without overwriting anyone
- **Problem:** `skills/plan-init/core.md:439-475` bootstraps `CLAUDE.md` as the content file. Implement D10's `plan-init` column, walking all five rows explicitly. Author `AGENTS.md` and write `CLAUDE.md` as D8's exact pointer bytes **only on row 1**; on row 2 touch neither and report the project non-inverted. Repair the `:443` skip guard, which keys on `CLAUDE.md` existence — a POINTER satisfies it, so plan-init writes nothing on an inverted project. Update the report string at `:462`, the scrapability constraint at `:475` (it is the dev-observatory scrape contract — see § 8's resolved row for what it must say on an inverted project), and the post-save handoff at `:481`. Update `skills/plan-init/providers/codex.md:11`; the adapter carries only D11's bounded cite phrase and neither probe literal.
- **Type:** code
- **Issue:** #145
- **Files:** skills/plan-init/core.md, skills/plan-init/providers/codex.md
- **Flags:** --reviewers deep
- **Produces:** modified plan-init core and codex adapter; the new report string quoted verbatim in the step's checkpoint entry
- **Done when:** all five D10 rows are walked explicitly in the prose; **row 2 provably writes nothing**; the skip guard no longer suppresses on a POINTER; every `CLAUDE.md` write in the file carries D11's canonical marker in its section; the adapter carries neither probe literal; the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 100
- **Status:** DONE (2026-08-25)

### Step 102: repo-update refreshes the content file and advises on drift
- **Problem:** `skills/repo-update/core.md` Step 7 (`:52`, `:236-250`, `:400`) verifies and creates `CLAUDE.md`. Implement D10's `repo-update` column, walking all five rows. **The only creation path for `AGENTS.md` is D10 row 1 (both files ABSENT); in a project that already has a SUBSTANTIVE `CLAUDE.md` it must never create one** — row 2 refreshes `CLAUDE.md` in place exactly as today, and that write stays legal under D11 by carrying the canonical marker. On row 3 refresh `AGENTS.md` and leave the pointer alone. On row 5 refresh neither and emit the P2 advisory naming both paths, non-blocking. Repoint `:164`, the stale-reference grep hardcoded to `README.md CLAUDE.md documentation/*.md`. Update the report line at `:400`; preserve `:438`.
- **Type:** code
- **Issue:** #146
- **Files:** skills/repo-update/core.md
- **Flags:** --reviewers deep
- **Produces:** modified repo-update core; the new report string quoted verbatim in the step's checkpoint entry
- **Done when:** all five D10 rows walked; **row 2 creates no `AGENTS.md`**; row 5 never blocks and never halts; `:164` scans the content file; every `CLAUDE.md` write carries D11's canonical marker in its section; the prose states that row 3 refreshes only `AGENTS.md`, while row 4 refreshes `AGENTS.md` and creates the exact `CLAUDE.md` pointer, so a second pass is a textual no-op (the *executed* fixed-point check belongs to Step 109); the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 100
- **Status:** DONE (2026-08-25)

### Step 103: Re-derive the full classification and record it
- **Problem:** Round 1 proved the § 4 table unreliable and round 2 named three more candidates. Produce the authoritative classification, changing no behavior. Enumerate both arms — `grep -l 'CLAUDE\.md' skills/*/core.md` (24) and `grep -l 'CLAUDE\.md' skills/*/providers/*.md` (3) — and classify every hit WRITE / READ / REFERENCE by § 4's rules, distinguishing a **project** instruction file from a **workspace** one. Adjudicate the round-2 candidates explicitly: `repo-sync:51,:521`, `observatory-doctor:78`, `build-phase:31,:198,:229`. Record the result as a table in this plan. Do not edit any core in this step.
- **Type:** code
- **Issue:** #147
- **Files:** documentation/instruction-file-symmetry-plan.md
- **Flags:** --reviewers code
- **Produces:** the authoritative WRITE/READ/REFERENCE table recorded in § 4, derived by the two enumeration commands
- **Done when:** all 24 cores and all 3 provider files are classified with a `path:line` citation each; every round-2 candidate has an explicit verdict; the REFERENCE bucket is fully enumerated by name so Step 106 can prove no false positive against it; no core was modified
- **Depends on:** 100
- **Status:** DONE (2026-08-25)

### Step 104: Repoint every reader Step 103 proved broken
- **Problem:** Repoint each core Step 103 classified as a READ of a **project** instruction file to the canonical phrasing `CLAUDE.md or AGENTS.md`. The work-list is **seven** members (§ 4.2): `build-observer:57`, `citation-review:12`, `goblin-suggest:33`, `research-prospect:61`, `review-uat:144` (added by Step 103), `user-brainstorm:154`, `user-learn:161`. `goblin-suggest:33` additionally needs its grounding **precondition** repaired: it currently treats existence as sufficient, so a POINTER passes and the documented loud failure never fires. Two site-level riders the per-core Done-when does not gate but § 4.2.3 requires: `goblin-suggest:102` must be repointed in the same pass as `:33` (repairing only `:33` leaves an inverted project grounding silently on the pointer), and `user-learn:47`/`:104` ride along with `:161`. All seven measure AGENTS.md=0 and marker=0 today, so a 0→≥1 per-file assertion is clean.
- **Type:** code
- **Issue:** #148
- **Files:** skills/goblin-suggest/core.md, skills/build-observer/core.md, skills/research-prospect/core.md, skills/user-brainstorm/core.md, skills/user-learn/core.md, skills/citation-review/core.md, skills/review-uat/core.md
- **Flags:** --reviewers code
- **Produces:** modified cores for every reader Step 103 proved broken
- **Done when:** every core on Step 103's broken list names both files with the canonical phrasing; goblin-suggest's precondition fails loud on a POINTER; the verified-safe readers are unmodified; no core carries a designated probe literal; `python -m pytest tests/package-integrity` green as the iteration gate. **DONE gate (amended by operator 2026-08-25, batched with Steps 105 and 106):** this step flips DONE on the single repo-root `python -m pytest` run executed once, after Steps 104, 105, and 106 have all landed — green at or above the recorded count, skip unchanged, checkpoint naming it as the shared gate for all three steps
- **Depends on:** 103
- **Status:** DONE (2026-08-26)

### Step 105: Make context-slim inversion-aware
- **Problem:** `skills/context-slim/providers/claude.md` walks the `CLAUDE.md` ancestor chain (`:21, :23-24`), classifies sections (`:59-61`), and **writes** under `--apply` (`:166`). Provider-native, no `core.md`. On an inverted project it audits a pointer file and reports near-zero context cost — a false green. Per D9 **keep the CLAUDE.md-anchored ancestor walk** and change only what is read and appended to. The file names `CLAUDE.md` on **19 lines carrying 20 occurrences** (re-measured 2026-08-26; the plan's earlier figure of 16 was wrong — see § 4.2.4 finding 3), including `:3` (its emitted `description:` frontmatter) and `:5` (the `--project` default) — enumerate all of them, do not work from the four cited here. As an adapter it may not cite `<repo>/_shared/`; it carries D11's bounded cite phrase.
- **Type:** code
- **Issue:** #149
- **Files:** skills/context-slim/providers/claude.md
- **Flags:** --reviewers code
- **Produces:** modified context-slim adapter
- **Done when:** **every `CLAUDE.md` occurrence in the file is enumerated and given an explicit keep-or-repoint verdict**; on an inverted project the audit reads and `--apply` appends to the content file; the ancestor-walk anchor is unchanged so `user-afterparty`'s parity holds; non-inverted behavior unchanged; the file carries no `<repo>/_shared/` citation and neither probe literal; `python -m pytest tests/package-integrity` green as the iteration gate. **DONE gate (amended by operator 2026-08-25, batched with Steps 104 and 106):** this step flips DONE on the single repo-root `python -m pytest` run executed once, after Steps 104, 105, and 106 have all landed — green at or above the recorded count, skip unchanged, checkpoint naming it as the shared gate for all three steps
- **Depends on:** 100
- **Status:** DONE (2026-08-26)

### Step 106: The single-owner gate (write-surface gate deferred)
- **Problem:** Nothing asserts instruction-file handling anywhere. **Scope trimmed by operator decision 2026-08-25** (§ 4.2.4 findings 10 and 11): the originally specified **write-surface gate** (`test_instruction_file_contract.py`) is **DEFERRED** to a future phase — after Steps 104/105 land it has zero live true positives, so as specified it cannot fail; see § 10 for the deferral record and resurrection condition. This step builds only the **single-owner gate** (`test_instruction_contract_single_owner.py`): modeled on `test_autofix_marker_single_owner.py` — the owner section exists and carries both D11 probe literals; each declared citer carries the bounded cite phrase; **no other file under `skills/**/*.md`, `_shared/**/*.md` or `documentation/**/*.md` carries either probe literal** (the sweep must include `_shared/`, which is also the only mechanical enforcement of Step 100's "no `_shared/` file was created"). The gate may not red on this repository's own root files (D5), and may not be worded as a restatement of `documentation/host-discovery.md:158-160`, which is the installer axis. **Known self-collision, found during Step 101 (2026-08-25) — resolved in the landed gate.** The gate applies a path-independent use/mention rule: a probe literal inside a backtick code span is a permitted mention, while a bare occurrence is a use forbidden outside the owner; fenced-code occurrences remain uses, and citer sites may carry neither literal in any form.
- **Type:** code
- **Issue:** #150
- **Files:** tests/package-integrity/test_instruction_contract_single_owner.py, skills/plan-init/core.md (only if a proof requires an owner-side canary adjustment; the § 4.2.1 predicate pin defers with the write-surface gate)
- **Flags:** --reviewers deep
- **Produces:** the single-owner gate file
- **Done when:** the single-owner gate is green; **every new assertion proven RED against a planted defect** — the owner section renamed, a citation deleted, a probe literal re-duplicated into a second file, and a `_shared/` file created carrying one (four proofs, each restored); `test_recovery_plan_hygiene.py` still passes; `python -m pytest tests/package-integrity` green as the iteration gate. **DONE gate (amended by operator 2026-08-25):** this step flips DONE on the same single repo-root `python -m pytest` run shared with Steps 104 and 105, executed after all three steps' edits land — green at or above the recorded count, skip unchanged, checkpoint naming it as the shared gate
- **Depends on:** 101, 102, 104, 105
- **Status:** DONE (2026-08-26)

### Step 107: Vendor the measurement, document the shape, update the count owner
- **Problem:** Create `documentation/codex-instruction-delivery.md` holding § 1's measurement table, the `codex-cli 0.147.0` pin, and the `codex debug prompt-input` reproduction recipe, so nothing load-bearing depends on an out-of-tree file. Document the inverted shape in `documentation/host-discovery.md` (the host-loading authority) and the adapter view in `documentation/architecture.md` (the contract). Record D7's accepted legacy drift citing `documentation/parity-deltas.md`. Then **measure the repo-root run first, compare against the count recorded in `documentation/phase-75-baseline.md` BEFORE this step, and only then write the new count into that owner** — in that order, so the comparison is not circular.
- **Type:** code
- **Issue:** #151
- **Files:** documentation/codex-instruction-delivery.md, documentation/host-discovery.md, documentation/architecture.md, documentation/phase-75-baseline.md
- **Flags:** --reviewers code
- **Produces:** the vendored measurement file; the inverted shape documented in the authority map and the contract; updated count owner
- **Done when:** the measurement and recipe are verifiable from inside this repository with no out-of-tree link; the authority map and the contract both describe the inverted shape; the legacy-drift decision cites its record; the repo-root `python -m pytest` was measured, compared against the pre-step recorded count, and the owner then updated to the new figure
- **Depends on:** 106
- **Status:** DONE (2026-08-26)

### Step 108: Build and install into a scratch home
- **Problem:** Editing a core changes nothing invokable — this repository is the canonical source, not an installed tree, and the live pre-Step-100 install is a separate stale copy. Without this step, Step 109 would exercise the OLD behavior and report PASS. Build all three profiles and install the claude profile into a **disposable scratch home** (never the operator's real home), then verify the emitted tree carries the new contract. The transcript must preserve that historical evidence without publishing unimplemented containment code as runnable; every downstream execution fence stays inert until Step 108P owns and certifies its replacement.
- **Type:** code
- **Issue:** #152
- **Files:** documentation/findings/instruction-file-symmetry-uat.md
- **Flags:** --reviewers code
- **Produces:** a scratch install home plus the verification transcript appended to the findings file
- **Done when:** `powershell -File tools/build-distributions.ps1 -Provider all` exits 0; `powershell -File tools/install-skill-mesh.ps1 -Provider claude -Home <scratch-home>` exits 0; `powershell -File tools/inspect-host-install.ps1 -Home <scratch-home>` reports the profile installed; the emitted profile is byte-compared to the fresh build and the installed writer cores are hash-bound to it; the seven canonical writer sections, fixture fact lines, stack table, directory tree, and structural-versus-semantic grading split are stated without claiming a downstream behavior result; all 18 Step-109 PowerShell fences contain only one standalone terminating blocker owned by Step 108P, so linewise or whole-block execution cannot reach a stateful/host action; the immutable Git blob identity and raw SHA-256, not checkout-dependent line endings, bind independent review; two independent reviews report no high or medium defect; all 24 PowerShell-bearing fences parse under Windows PowerShell 5.1; `python -m pytest tests/package-integrity` passes; and a clean stable detached repo-root `python -m pytest` reads its sentinel as `0`, meets `documentation/phase-75-baseline.md`, and preserves the recorded skip count. All packet implementation, negative corpus, and the post-code full gate belong to Step 108P.
- **Depends on:** 107
- **Status:** LANDED / CERTIFICATION PENDING (2026-08-26) — build/install acceptance remains PASS. Three immutable checkpoints were rejected by one of their independent reviewers (0 high / 2 medium, 0 high / 4 medium, then 0 high / 2 medium). Those eight plus two pre-freeze phase-plan ordering contradictions are repaired across the affected files. The resulting UAT candidate is Git blob `417813e04007167dbe81b081e56ea07b017d3427`, raw SHA-256 `3C8BD6D64DE5B99F9D5E9C54DB8A67B5461AFA30F589E9AEF17C28A0179F34A9` (139,223 bytes; 1,917 lines). The repaired bytes pass 24/24 PowerShell parses, 18/18 streamed nonzero blockers, the 107/107 credential check, unchanged manifest regeneration, and all 278 package-integrity tests. Two independent reviews of the next immutable commit and the stable repo-root gate remain pending; #152 stays open and Step 108 is not DONE. Every behavioral cell remains blank. See § 12 Round 10 and issues #152–#153.

### Step 108P: Implement and certify the Step-109 containment packet
- **Problem:** Step 109 is attended operator acceptance and may not create the substantial code needed to make its host actions safe. This preparation step owns that code after #153 records one of its two accepted routes. It replaces every unconditional blocker in the UAT skeleton with a reviewed packet: a static native `prepare`/launcher/guardian trust root, precompiled helper, self-contained Windows PowerShell 5.1 executor bundle, strict parsers and machine-readable schemas, exact mode artifacts, handle-coupled read broker, kernel I/O rail, portable evidence uploader/exporter, and safe cleanup. Native user/kernel components use pinned Microsoft Visual C++ (**MSVC**) C++17 with the Windows Software Development Kit (**SDK**) and Windows Driver Kit (**WDK**) because the required pre-entry-point code-integrity, handle, Job Object, process-creation, and minifilter boundaries cannot begin inside the Common Language Runtime (**CLR**) or a script; orchestration stays on Windows PowerShell 5.1 because that is the repository's supported Windows floor. The implementation records the exact compiler/SDK/WDK/signing manifest. In this step, **MVID** means a managed assembly Module Version ID, **UNC** means a Universal Naming Convention network path, and **SUBST** means a Windows substituted drive. A file identity is uppercase `<16-hex volume serial>:<32-hex file ID>` from `FILE_ID_INFO`, produced from one retained no-follow handle by the pinned helper; that same handle produces DOS-final and volume-GUID-final paths plus `FILE_STANDARD_INFO.NumberOfLinks`. The admitted guardian retains no-delete-sharing handles to the common creation parent, the combined install-home/project root, the config root, the build root, the evidence-export root, and the real profile from creation through handle-based final disposition and duplicates only the required handles to fresh runners; a path reopen plus a reused ID cannot re-establish continuity. Preparation, every later guard, and cleanup consume those live handles and fail closed if the guardian, either information class, or share denial is unavailable.
- **Structures:** The strict pre-build receipt minimally binds schema/nonce; caller/final paths, identities, and link counts for the common creation parent, the four created roots (combined install-home/project, config, build, and durable evidence export), and the real profile; preparation/source-tool-process/fence/launcher/helper hashes; and creation time. Each root is a direct child of the bound common parent. The evidence-export root is never a cleanup target. The launch attestation chains its hash/nonce and minimally binds trust/bootstrap, inspector/build/install/process, whole-profile/writer/heading, per-mode environment/secret-presence/hook/policy, fence, and creation facts. The readiness receipt chains both earlier receipts and minimally binds the effective-hook manifest, real denied-probe result, fence, nonce, and time. Every native result minimally binds schema/mode, applicable receipt hashes, executable/argv/environment and descendant manifests, physical root, started/exit/process-tree/quiescence facts, protected pre/post digests, and one redacted mode proof. `tools/phase-is-uat/**` must contain the machine-exact schemas, property names, nested scalar types, additional-property denial and negative mutations; `documentation/findings/instruction-file-symmetry-uat.md` § 1.8/§ 2.0 states their mandatory semantic minima.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-uat/**` (new); `tests/phase-is-uat/**` (new); `documentation/findings/instruction-file-symmetry-uat.md`; `documentation/release-candidate-report.md` plus `skills/plan-init/core.md`, `skills/repo-update/core.md`, and affected package-integrity tests only if the selected route changes a distribution/core input
- **Flags:** --reviewers code
- **Produces:** committed, versioned containment binaries/bundle/schemas/tests and exact artifact hashes that #153 only invokes; no behavioral UAT observation
- **Done when:** #153 records the selected route; the one text comparator placeholder, all 18 unconditional Step-109 PowerShell blockers, and the `<receipt-pinned-build-distributions.ps1>` plus `<receipt-pinned-install-skill-mesh.ps1>` command tokens are replaced by committed artifacts while redaction tokens and Step-109 operator observation/verdict blanks remain; all strict receipt/result/public-attestation schemas and the complete negative corpus pass; identity uses guardian-lifetime retained handles with `FILE_ID_INFO`, both final paths and link count, and tests delete/recreate plus simulated ID reuse after every path checkpoint; exact per-mode secret presence/absence passes, with OAuth only in the four authenticated Claude modes, no runtime secret in trust/Codex, and process-only `GH_TOKEN` only in `evidence-upload`; the prepare/launcher/guardian/loader/signing closure, exact environment/hook/policy/process rails, unforgeable per-invocation read/write containment, durable export root, remotely round-tripped evidence uploads, and handle-based cleanup are independently reviewed; route 1 rebuilds/reinstalls/reverifies and refreshes release-candidate/writer facts, while route 2 proves tooling changes are outside distribution inputs and reruns its package/reference gates; and a clean stable detached repo-root `python -m pytest` reads its sentinel as `0`, meets `documentation/phase-75-baseline.md`, and preserves the recorded skip count
- **Depends on:** 108
- **Status:** BLOCKED (2026-08-26) — #152 must first return to certified DONE and #153 must record the route choice. No implementation or host action has run.

### Step 109: Operator confirmation of all five D10 rows
- **Problem:** These cores are prose read by an agent; a test asserts what the prose instructs, never what an agent does. Consume Step 108P's already-committed and certified packet without creating or modifying code. Using that packet, create the receipt-bound project/config/build roots plus the distinct durable evidence-export root, build/install/reverify the selected route's exact bytes, establish the complete receipt and containment preconditions, then exercise every D10 row: run `/plan-init` from nothing (row 1) and verify `AGENTS.md` plus a `CLAUDE.md` matching D8's exact pointer bytes; run it beside a SUBSTANTIVE `CLAUDE.md` (row 2) and verify it writes nothing; run `/repo-update` on the inverted project (row 3) and verify it refreshes `AGENTS.md`, leaves the pointer, and is a no-op on a second pass; run `/repo-update` with SUBSTANTIVE `AGENTS.md` and absent `CLAUDE.md` (row 4) and verify it refreshes `AGENTS.md` plus writes the exact D8 pointer; manufacture row 5 and verify the advisory prints without blocking. Then verify exact normalized Codex project-payload equality and the Claude import event while both instruction files remain locked to their attested bytes; emit, publish, remotely reread and verify the redacted evidence attestation; dispose only the three disposable roots through the certified no-follow bundle and emit the cleanup attestation; publish, remotely reread and verify that second attestation; and retain the durable evidence-export root.
- **Type:** operator
- **Issue:** #153
- **Files:** documentation/findings/instruction-file-symmetry-uat.md
- **Flags:** --reviewers code
- **Produces:** operator observations in `documentation/findings/instruction-file-symmetry-uat.md`, two remotely verified redacted records, and their retained evidence-export attestations; no code artifacts
- **Done when:** the certified packet creates and binds the four roots, builds/installs/reverifies the selected-route bytes, and passes the pre-build, launch-attestation, readiness, build/install/inspect, environment/hook/policy, read/write/process, evidence-publication, and cleanup gates; all five D10 rows are confirmed on disk; the second `/repo-update` pass is observed to be a no-op; `codex debug prompt-input` shows the content; the Claude `@` import resolves; the row-5 advisory prints without blocking; every behavioral difference is recorded; the redacted evidence and cleanup attestations are each published and remotely hash-verified; all three disposable roots have an exact `deleted`, `intact-quarantined`, or `partial-quarantined` disposition in the cleanup attestation; and the durable evidence-export root is retained
- **Depends on:** 108P
- **Status:** BLOCKED BEFORE GRADING (2026-08-26) — the accepted step requires real named-skill behavior, but neither current core exposes a safe instruction-file-only UAT mode and normal `repo-update` cannot safely reach Step 7 in the deliberately outside-git fixture. Issue #153 must choose either a new core-supported UAT mode (with rebuild/reinstall/reverification) or a deliberate plan amendment accepting narrower operator-scoped named-skill subsection overrides; #162 then implements and certifies that route's packet. No row or host-delivery check has run.

**Rollback.** Every repository change, including Step 108P's containment packet, is `git revert`-able
here; no step writes into a consumer project. Step 108's historical install artifact is retained only
as evidence. Step 109 must create
a new receipt-bound scratch home/project, a distinct scratch Claude config root, a distinct
fresh-build output root, and a distinct durable redacted-evidence export root outside the real user
profile. During Step 109 closeout, after behavioral acceptance and the first verified evidence
publication but before the step completes, the three disposable roots are disposed rather than
reverted through Step 108P's reviewed safe-cleanup block; the cleanup attestation is then remotely
verified in the second publication and the export root is retained. Attended Step 109 host sessions also
create routine native session records and may refresh host-owned caches outside that scratch root;
that bounded observational transport state is explicitly permitted before any host session runs,
but it authorizes no auto-memory/semantic-memory, installer, skill-tree, source-tree or
consumer-project write outside scratch. Auto memory must be disabled for every row. Use tested
isolated host state instead if that bounded native state is unacceptable.

---

## 8. Risks and Open Questions

| Item | Risk | Mitigation |
|---|---|---|
| Prose cores are not executable | A gate asserts instructions, never agent behavior | Steps 108–109 build, install and run for real; the limitation is stated in § 6 |
| The future write-surface predicate over prose | An unguarded-write predicate could still false-red the REFERENCE bucket | D11 gives the marker; any resurrection step must **report a measured false-positive count** against Step 103's enumerated bucket, not assert zero |
| Enumeration set | A narrow single-owner sweep could miss a third contract carrier — the #142 shape | Step 106 sweeps `skills/**/*.md`, `_shared/**/*.md`, and `documentation/**/*.md`; D6 removes the third authored surface |
| Backward compatibility | ~32 non-inverted projects must keep working | D10 row 2; every writer step's Done-when carries it; Step 109 exercises it |
| Destructive overwrite | A naive P1 implementation would replace a user's `CLAUDE.md` with a pointer | P1 is scoped to D10 row 1; Step 101's Done-when requires the no-write case be provable |
| `repo-update` runs unattended | It executes inside phase wraps and `/repo-wrap` Rail A | P2's never-block/never-halt is load-bearing and stated |
| Report strings | `:462` and `:400` change | Verified: no test and no code consumes either. Steps 101/102 quote the new strings verbatim in their checkpoints so both writers agree |
| skill-mesh's own root files | An edit reds `test_recovery_plan_hygiene.py:41-60` | D5 scopes them out; D8's worked example fixes their classification as row 2; Step 106's Done-when re-asserts the test passes |
| **Resolved — dev-observatory scrape** | Does the descriptor scrape follow content to `AGENTS.md`? | **Yes.** `descriptor.py:31-33` — the scrape checks every descriptor file present and **unions** commands and ports, reporting the highest-precedence present file only as the `source` label; `AGENTS.md` is at PRECEDENCE index 1. An inverted project keeps its verbs and ports; only the attributed label changes. *(Step 101 correction, 2026-08-25: that last clause is loose. `descriptor.py:272` does `source = present[0]` over a `PRECEDENCE` tuple led by `CLAUDE.md`, so on an inverted project the label stays `CLAUDE.md` — it does not move to `AGENTS.md`. The operative half of this row is correct and unchanged: verbs and ports survive because the same loop unions them across every present file. plan-init's prose states the corrected version.)* Step 101 must therefore keep `:475`'s scrapability constraint but apply it to whichever file is SUBSTANTIVE. *(Round 2 also retracted an incorrect caveat: `descriptor.py:246`'s `except OSError, UnicodeDecodeError:` is PEP 758 syntax, legal on the installed Python 3.14.3 — not Python 2, not broken.)* |

---

## 9. Testing Strategy

**What is added.** One gate (§ 5). The single-owner gate follows
`test_autofix_marker_single_owner.py` — this repository's proven pattern for a shared prose
constant, and the achievable analogue of a data-pipeline smoke gate.

**Proof obligation.** Four planted-defect proofs, each restored: the owner section renamed; a
citation deleted; a probe literal re-duplicated into a second file; a `_shared/` file created
carrying one.

**What might break, and why each is named.** `test_recovery_plan_hygiene.py:41-60` if this
repo's own root files are touched (D5 forbids it). `test_link_resolution.py` if any step
introduces a new dangling reference — its allowlist is **shrink-only**, so a new key is a hard
fail, not an amendable baseline. `test_distributions.py:770-777` if any adapter acquires a
`<repo>/_shared/` citation. D6 avoids all three by creating no `_shared/` file.

**Gates.** `python -m pytest tests/` and `python -m pytest tests/package-integrity` are
in-step **iteration** gates only — `documentation/phase-75-baseline.md` states in its own words
that neither may flip a step or a phase DONE. **Every remaining code/certification step's final Done-when
therefore runs the repo-root `python -m pytest` with no path argument**, covering the eight `tests/` suites plus
`_shared/`, `skill-iterate/scripts/` and `skill-eval-setup/scripts/`. Counts are owned by
`phase-75-baseline.md`; this plan restates none, and Step 107 updates the owner in a
non-circular order. Step 108P starts only from Step 108's certified bytes, owns the new containment
code and its full gate, and hands immutable artifacts to Step 109. Step 109 closes only after its
attended behavior/delivery checks, first verified evidence publication, cleanup and cleanup
attestation, and second verified publication, without creating code or rerunning the suite.

**End-to-end.** Step 108 makes the edited prose actually loadable; Step 108P implements and certifies
the selected safe UAT packet; Step 109 invokes that packet and exercises the prose. Step 109 is
`Type: operator` and produces observations only.

---

## 10. Deferred to a future phase

Round 2 identified these as real but out of scope here; recorded so they are not lost:

- `session-wrap:60`'s plan-location citation is genuinely ambiguous between the project and
  workspace instruction file. Step 103 classified it as a WORKSPACE reference (§ 4.2 row 16), so it
  is out of the contract and is not a Step 104 member.
- The seven-section contract remains duplicated across `plan-init` and `repo-update` with no
  single owner. This plan deliberately does not merge them (§ 3); the duplication predates the
  feature and is tracked separately.
- **The write-surface gate (`test_instruction_file_contract.py`), deferred by operator decision
  2026-08-25** (Round 5). Grounds: § 4.2.4 finding 10 — after Steps 104/105 land the gate has
  zero live true positives, so a predicate narrowed into uselessness still passes every planted-defect
  proof the original `Done when` required (a gate that cannot fail); and finding 11 — the step's
  `Problem` and `Done when` contradicted each other on the zero-count clause. **Resurrection
  condition:** build it when a genuine unguarded `CLAUDE.md` write surface exists to catch, and only
  with (a) the § 4.2.1 predicate pin adopted as the owner-section edit at `skills/plan-init/core.md`,
  (b) one planted-defect proof per covered write verb, and (c) the far-marker proof — the three
  things finding 10 records as necessary for the gate to prove anything. Step 106 retains the
  single-owner gate, which has neither defect.
- The opening rationale in `skills/plan-init/core.md`'s `## Instruction-file contract` still
  describes the deferred plural/two-glob write-surface design and overstates the adapter citation
  constraint. Correcting that canonical core is not a documentation-only closeout: it requires its
  own code step, package gate, rebuild/reinstall, and installed-byte reverification.

---

## 11. Verdict history

| Round | Skill | Verdict |
|---|---|---|
| 1 | `/plan-review` | 22 Blockers, 38 significant gaps — all addressed in § 12 |
| 2 | `/plan-wrap` | 9 Blockers — all addressed in § 12 |
| 3 | `/plan-redline` | Publication 2 accepted as written — ready for `/repo-sync` |

---

## 12. Revision log

**Round 1 (plan-review)** — `_shared/` file dropped entirely (D6, four measured grounds);
seven-section relocation dropped (the two bodies are not verbatim duplicates); D10 added; D8
added; D9 added; classification demoted to a hypothesis after `citation-review`,
`repo-update:164` and `plan-init:481` were found missed; `tier-escalate` named and scoped out;
`**Type:**`/`**Issue:**`/`**Files:**`/`**Status:**` added to every step; rollback recorded;
counts switched to citing `phase-75-baseline.md`.

**Round 2 (plan-wrap)** — the plan was NOT self-sufficient; a blind builder could not start
Step 100 unaided. Material changes:

- **D11 added.** Round 2's sharpest finding: Step 106's original predicate ("no surface writes
  `CLAUDE.md` as a content file") forbade exactly what D10 row 2 **requires** `repo-update` to
  keep doing on ~32 projects. Steps 102 and 106 could not both be satisfied. D11 replaces it
  with guarded-vs-unguarded and names the marker the gate keys on.
- **D8 made three-valued and typed to both filenames.** Two-valued + "exhaustive" made an
  ABSENT file read as SUBSTANTIVE, routing greenfield into row 2's "touch neither" and killing
  P1. It also left `AGENTS.md` unclassified, which made **this repository's own root pair**
  classify as row-4 drift. D8 now carries that pair as its worked example, and the exact
  pointer bytes are specified.
- **D10 restated in three-valued terms**, gaining the missing `SUBSTANTIVE`/`ABSENT` row.
- **Step 102's absolute corrected** — "never create an `AGENTS.md`" now carries its row-1
  exception inline, where an implementer reading only the step block will see it.
- **Probe literals and the bounded cite-site minimum designated** (D11). Steps 101/105 order
  adapters to restate while Step 106b forbade re-duplication under `skills/` — adapters are
  under `skills/`. The precedent solves this with canaries; the plan had cited the precedent
  and dropped the mechanism.
- **Step 103 split** into derive-and-record (103) and repoint (104), because the original
  step's `Files:` list foreclosed the cores its own enumeration was supposed to find.
- **Step 108 inserted.** Round 2 proved Step 109 had no path to the behavior it grades: the
  installed core is a separate 26,477-byte copy and no step built or installed anything, so the
  operator step would have confirmed the OLD behavior and passed.
- **Every later code/certification step after Step 103 now ends on the repo-root DONE gate.** Six steps had been flipping DONE on
  `python -m pytest tests/`, which the cited count owner explicitly forbids.
- **Step 102's executed fixed-point check moved to Step 109** — it required operator presence
  in a `Type: code` step.
- **§ 1 renamed to "What This Is"** so dev-observatory's goal scrape matches
  (`observer.py:50` tests exact membership), and the measurement vendored inline.
- **Resolved the dev-observatory open row** and retracted its incorrect Python-2 caveat.
- Minor: `repo-update:240-248` citation corrected (it had excluded section 7); `<repo>`/`<leaf>`
  noted as literal bytes; decision-ID legend added; Rail A glossed; Step 107's count update ordered
  non-circularly; `judge-motion/providers/claude.md:146` named alongside `tier-escalate`;
  context-slim's 19 lines / 20 occurrences flagged against the 4 cited.

**Round 3 (plan-redline)** — Publication 1 rendered beside this plan; the stable proposal
locator and append-only Decision Inventory were added. The two choices already marked
`operator, 2026-08-20` became P1–P2; the remaining design decisions remain D3–D11 as agent
defaults pending feedback. No implementation behavior changed.

**Round 4 (plan-redline feedback)** — the operator accepted Publication 1 as written on
2026-08-20. D3–D11 retain their stable IDs and are marked accepted; the same proposal locator
was refreshed as Publication 2. No decision or implementation behavior changed.

**Round 5 (mid-build operator amendment, 2026-08-25)** — four changes, each authorized by the
operator in-session after Steps 100–103 landed:

- **Steps 104, 105, and 106 now share one batched DONE gate.** Each iterates on
  `tests/package-integrity` (~40s); the full repo-root `python -m pytest` (~2h20m per
  `phase-75-baseline.md`) runs **once**, after all three land, and flips all three DONE. This
  satisfies the gate-scope rule — the DONE-flipping gate is still the full suite — while removing
  two redundant full-suite runs.
- **Step 106 trimmed to the single-owner gate.** The write-surface gate is deferred to § 10 with
  its resurrection condition, resolving § 4.2.4 findings 10 and 11 (unfalsifiable-as-specified;
  Problem/Done-when contradiction). Issue #150 stays open at the narrowed scope.
- **Step 104's Problem made self-contained** — the seven-member work-list (review-uat:144 included)
  and the two § 4.2.3 site-level riders (goblin-suggest:102; user-learn:47/:104) folded inline.
- **Park-and-pivot recorded.** The build parks after the shared gate flips 104–106 DONE; Steps
  107–109 stay open and are not abandoned. The next window pivots to the utility track:
  refresh `<dev-root>/documentation/utility-hookup-plan.md` (stale prerequisites — host-parity
  Step 65 is DONE 2026-08-13; predates the codex adapter catalog) and build its Step 4, the
  installer current-byte-authority repair, which unblocks host-parity Step 70 and the entire
  utility wiring sequence. **Superseded 2026-08-26 — see Round 6.**

**Round 6 (build outcome + operator redirect, 2026-08-26)** — Steps 104, 105 and 106 built and
DONE. Recorded because three things happened that the plan did not predict:

- **The shared gate came back `1341 passed, 1 skipped`** in 2:16:29 at `dc21c9e`, exit 0 — exactly
  `+6` on the 1335 recorded in `phase-75-baseline.md`, being Step 106's six new tests, skip count
  unchanged. Summary at `documentation/findings/phase-is-shared-gate-dc21c9e.txt`. Available memory
  stayed between 1737 and 1864 MB throughout, continuously inside issue #156's spurious-red band,
  and the run was clean anyway.

- **§ 6 D8's text was stale relative to the owner section Step 100 landed, and it cost an
  iteration.** Before this wrap, § 6 D8 defined SUBSTANTIVE as requiring "at least one `##`
  section heading";
  `skills/plan-init/core.md:475-477` — the ONE owner, and authoritative — says that heading is "the
  TYPICAL shape, **never a necessary condition**", SUBSTANTIVE being the complement of POINTER. A
  Step 104 iteration transcribed § 6's wording into `goblin-suggest` and was rejected for
  contradicting the owner. This wrap corrected § 6 D8; the incident remains the plan's own example
  of Finding 2's "one source of truth" argument.

- **Two findings outlived the steps.** (a) Step 103 classified sites by reading skill *prose* and
  never opened the source of the CLIs two of those skills drive: `goblin`'s
  `grounding.py:293` hard-codes `project_dir / "CLAUDE.md"` and `citation-needed`'s
  `discover.py:592` classifies only `filename == "CLAUDE.md"`, so `goblin-suggest` and
  `citation-review` now name both files in prose that their tools cannot act on. Tracked as
  **#159**; out of scope here (no step writes into a consumer project). A skill that delegates to an
  external tool cannot be classified from its own prose alone — worth folding into how a future
  instruction-file audit enumerates. (b) **`/review-deep`'s calibration gate cannot run in this
  repository**: `calibrate_judge.py` resolves `review-deep/evals/golden/recorded_scores.json` and
  `skill-mesh` carries no `evals/` tree at all, so it exits 1 here. Step 106's deep review was run
  and reported as **uncalibrated** rather than pointed at the installed tree, per
  `measurement-validity.md`'s rule that a fallback path is an abort condition, not a warning.

- **Park-and-pivot superseded.** The operator redirected in-session on 2026-08-26 after the gate
  returned: the next step is **Step 107**, not the utility track. Steps 107–109 run first; the
  utility track is deferred behind them, not cancelled. Step 107 is well-placed regardless — its
  `Done when` needs a repo-root measurement compared against the pre-step count before the owner is
  updated, and a fresh Step-107 gate supplies exactly that.

**Round 7 (build outcome, 2026-08-26)** — Step 107 built and its code landed. Four things are
recorded because the plan did not predict them:

- **A shared Steps 107–108 gate was authorized here but did not become the execution record.** The
  Step-107 gate completed first at `d4c88ee`: measure, compare against the 1335 recorded in
  `documentation/phase-75-baseline.md`, and only then write the new figure into that owner. Step 108
  therefore needs its own later certification gate after its transcript repairs land.

- **Three of Step 107's review findings originated in § 1 of this plan, not in the build.** The
  developer transcribed § 1 faithfully and inherited its defects: § 1 claimed the reproduction
  "writes nothing" without a project scope (controlled protocols establish no project write;
  zero-invocation controls make Codex-home churn unattributable), spelled the config override with outer-single /
  inner-double quotes (**exits 1** in Windows PowerShell 5.1, this repository's declared floor —
  PS strips the inner quotes and codex reports `invalid type: string "[CLAUDE.md]", expected a
  sequence`), and writes `§ N` with a space where the rest of `documentation/` writes `§N` by
  roughly 240:7. § 1 is corrected above; `documentation/codex-instruction-delivery.md` is now the
  vendored owner. **A step that transcribes this plan inherits this plan's errors** — the same
  lesson Round 6 recorded for § 6 D8, now with a second instance.

- **Step 107 took three iterations, and the third was re-scoped rather than patched.** Iterations 1
  and 2 each fixed every finding put to them (2 high + 10 medium, then all of them), but three of
  iteration 2's five new findings sat *inside the hunk written to fix iteration 1's HIGH*. That is
  build-step's oscillation trigger, so iteration 3 applied one invariant instead of more line
  patches: **`architecture.md`, `host-discovery.md` and `codex-instruction-delivery.md` are CITERS
  of the instruction-file contract, not its owner, so any clause whose ground truth lives elsewhere
  must be a resolvable citation, never a local paraphrase** — because the single-owner gate probes
  designated *literals*, not meaning, so a paraphrase carries no mechanical guard. Eight sites were
  cut or converted; fourteen already-compliant ones were left alone. The deciding argument was that
  `architecture.md` already *declared* this policy ("cites it … rather than restating the file
  states or the writer matrix") and did not follow it. Final review: five APPROVEs, 0 high /
  1 medium / 11 low.

- **The unguarded-paraphrase risk was already realized, undetected.** `architecture.md` claimed
  reading a pointer yields "simply an empty read", while this repository's own vendored measurement
  records the import line as *delivered verbatim* — a drift that survived five reviewer passes
  across two rounds and was found only by the re-scope's diagnosis arm. Cut, not corrected. The
  obvious remedy — widening the citer gate's glob to `documentation/` — was **executed and
  measured** before being declined: two immediate false reds, zero true positives, because that
  gate's marker arm models a write surface and the owner scopes the cite-site minimum to "a citing
  core or adapter." Recorded so a later reviewer does not re-propose it.

**Round 8 (build outcome, 2026-08-26)** — Step 107 landed at `d4c88ee`; **Step 108 BLOCKED**
after 3/3 iterations. Recorded because four things generalize beyond these steps:

- **Step 107 PASSED 5/5 at iteration 3, re-scoped rather than patched.** Iterations 1 and 2 each
  fixed every finding put to them, but three of iteration 2's five new findings sat *inside the
  hunk that fixed iteration 1's HIGH*. Iteration 3 applied one invariant instead: `architecture.md`,
  `host-discovery.md` and `codex-instruction-delivery.md` are **citers** of the instruction-file
  contract, not its owner, so any clause whose ground truth lives elsewhere is a resolvable
  citation, never a local paraphrase — the single-owner gate probes designated *literals*, not
  meaning, so a paraphrase carries no mechanical guard. Eight sites cut, fourteen compliant ones
  left. The risk was already realized: `architecture.md` claimed reading a pointer gives "simply an
  empty read" while this repository's own vendored measurement records the import line as
  *delivered verbatim* — a drift that survived five reviewer passes across two rounds.

- **Three of Step 107's findings originated in § 1 of this plan** (corrected in `d4c88ee`): a false
  "writes nothing", an override spelling that **exits 1** in Windows PowerShell 5.1, and `§ N`
  spacing against the repository's `§N`. A fourth originated in the orchestrator's own instruction
  (`Step 101 (#146)`; the plan maps 101→#145, 102→#146). **A step that transcribes an upstream
  artifact inherits that artifact's errors** — Round 6 recorded this for § 6 D8; there are now four
  instances across two rounds.

- **Step 108's install is verified; its transcript's operator half is not.** `-Provider all` exit 0,
  install exit 0, inspector `state=present owned=58 unowned=0`, and whole-profile `diff -r` against a
  fresh build at HEAD = **zero differences across all 57 skills**. What blocked it: § 2 was never
  executed by a host. Three separate false-green classes were measured — concatenated fixture +
  instrument blocks exit 0 while Instrument B throws and prints `False`; Instrument A embeds a manual
  host action mid-block so a whole-block paste silently passes rows 2–4; and two "Observed output"
  blocks cannot have been emitted by the command above them.

- **The HIGH is a false admission with a better answer already in the repository.** § 2.0 claims this
  repository does not document how an arbitrary directory becomes a running host's discovery home.
  `documentation/host-native-discovery-cutover-plan.md:99` § "Step 49-50 host-trace amendment"
  documents it for both hosts — `claude --setting-sources project` from the consumer home, verified by
  session-JSONL `cwd` and the host-supplied `Base directory for this skill:` line, and
  `copilot -C <home> skill list --json` — and Steps 49/50 are **DONE (2026-08-09)**. That instrument
  grades the **binding**; § 2.0's probe grades only a tree the operator names. Two measured
  consequences for Step 109: a stale `plan-init` (26,477 bytes, **0** `AGENTS.md`) is live in the
  personal `~/.claude/skills` root and becomes eligible under the default user + project + local
  setting sources — so an invocation that omits or widens the mandatory project-only source can
  **report PASS against it**; and that junction target contains **1,235 git-tracked files** with an
  install ledger already present, making § 2.0's option-2 install a routine *owned* overwrite (no
  `-Force`, no prompt, measured). Following the documented mechanism removes the need for option 2
  entirely.

**Round 8 addendum — a concurrent session, and four defects then live at `d4c88ee`.** A second
`/build-phase --resume 107` ran at the same time and authored Step 107 independently; `d4c88ee`
won the race, and commit `d5afe97` plus branch `build-step-1787765607` @ `8af9e36` are that
session's. Its review (ten reviewer passes, two adversarial workflows) is preserved at
`documentation/findings/step-107-parallel-review-evidence.md`. **Four of its findings were
re-confirmed by direct enumeration against the landed files at `d4c88ee`**; commit `52d44c9`
subsequently fixed all four:

1. `architecture.md:627,632` — "the write surface is the core, never the adapter, for every
   portable skill" and adapters "need no instruction-file prose of their own". **False**, and
   load-bearing: `skills/plan-init/providers/codex.md:11` is a *portable* skill's adapter carrying
   exactly that prose (mandated by Step 101), and `test_instruction_contract_single_owner.py`
   counts it in `CITER_FLOOR = 4` — a maintainer who follows the prose and deletes it **reds the
   suite**. Verified at wrap time.
2. `host-discovery.md:257` — a pre-existing row answers "Are workspace instructions loaded?" with
   "the host's instruction-file convention"; this repository follows that convention exactly and
   Codex receives none of the content.
3. `architecture.md:538,:603` and `host-discovery.md:189,:274` — four unqualified "read-only"
   descriptions of the reproduction, contradicted by `codex-instruction-delivery.md:72`, which the
   same change landed and which says in bold it is "not side-effect-free".
4. `codex-instruction-delivery.md:73-74` — "three files under the Codex home re-stamped" is a
   per-invocation count from one uncontrolled sample.

**The measurement correction, which supersedes this plan's § 1 and the Round 7 record.** Two
independently designed re-measurements, each bracketed by **zero-invocation control intervals**,
refuted the "two files rewritten per invocation" figure: attributable changes ranged from none to
three, the two protocols disagreed, and **a control interval with the command never run reproduced
the exact same signature**. The Codex home churns with no invocation at all. What survives is only
the project-scoped claim: `codex debug prompt-input` writes nothing in the project directory, and
`config.toml`/`auth.json`/session/skill/plugin files were unchanged in every manifest, so a `-c`
override leaves nothing on disk. **No per-invocation file count should be published.** The original
figure was carried forward from task state as "verified" and re-confirmed by an equally
uncontrolled measurement in this session — `measurement-validity.md`'s known-good/known-garbage
anchor is exactly what neither had.

**Transferable method, worth more than the findings.** The parallel session enumerated every claim
in its prose quantifying over a set ("every", "only", "never", "no …") and ran one falsifying
enumeration per claim: of 10, **3 TRUE, 4 FALSE, 3 NEEDS-SCOPING**. Three false universals had
already survived review, each refuted by a *single* live counter-example nobody had looked for.
**A universal claim is cleared only by enumerating the set it quantifies over** — reading never
catches these. That audit should be re-run against the landed prose; its verdicts were computed
against the parallel branch's wording and its line numbers do not map onto `d4c88ee`.

**Separate defect, in the contract owner itself** (out of scope for any documentation step):
`skills/plan-init/core.md:452-455` says an adapter "could not cite it in any legal spelling". The
premise is true, the conclusion false — `skills/judge-motion/providers/claude.md:10` is
provider-native and cites `_shared/judge-core.md` via the relative spelling today, and
`tests/distributions/test_distributions.py:769-777` forbids only the repo-rooted spelling. A sweep
found exactly two instances and no third, so stop-and-audit was not reached.

**Round 9 (interim Codex handoff closeout, 2026-08-26; superseded by Round 10)** — At this
checkpoint Steps 107–108 were marked DONE and Step 109 was blocked before grading. Four outcomes
were recorded:

- **Step 107's gate passed from its sentinel, not its log tail.** The named scratch sentinel was
  `0`; only after that was read did the UTF-16 log supply `1341 passed, 1 skipped in 8843.47s`.
  Against the unmodified 1335/1 owner this is +6 with no skip regression. Commit `719e622` updates
  the baseline and closes #151.
- **The four live documentation defects from Round 8's concurrent review are fixed.** Commit
  `52d44c9` corrects portable-adapter ownership, workspace-delivery wording, project-scoped
  read-only claims and the unsupported per-invocation Codex-home file count. The package-integrity
  iteration gate passed `278` tests after those changes.
- **Step 108's own acceptance was always independent of downstream UAT.** Its all-profile build,
  scratch Claude install, inspector result, current owner section and whole-profile equality are
  verified in `documentation/findings/instruction-file-symmetry-uat.md`; the repaired transcript
  merged at `600af9e` after the then-current review reported no high or medium defect. Round 10's
  fresh audit refuted that review result without refuting the historical build/install evidence.
- **Step 109 has a newly exposed design blocker, not a D10 failure.** The plan requires real named
  skills, but `plan-init` and `repo-update` expose no instruction-only UAT mode; a normal
  `repo-update` cannot safely reach Step 7 in the outside-git fixture. Every behavioral cell stays
  blank. Issue #153 must choose a core-supported mode or deliberately amend the acceptance to
  named-skill subsection overrides; Step 108P/#162, not the operator step, owns the resulting code
  packet. The Rollback clause now records the bounded native host
  session/cache state inherent in either attended route.

**Round 10 (post-merge certification audit, 2026-08-26)** — Step 108 is landed but its
certification is pending; Step 108P is blocked before implementation; Step 109 remains blocked before
grading.

- The historical build/install evidence still passes its four acceptance criteria. The defects are
  in the published replay and downstream UAT instruments: exact-pointer decoding accepted multiple
  byte sequences; mandatory predicates printed false values with exit 0; the tree comparator could
  print `IDENTICAL` after probe errors or compare one directory through its long and 8.3 aliases;
  path changes and Git containment failed open; hard links
  could escape the scratch boundary; and the heading-only grader did not prove seven populated,
  surgically refreshed sections.
- The host design also proved too weak. Wrapper/base attribution did not prove Claude read the
  co-located canonical `core.md`; `--setting-sources project` excludes the stale user skill but does
  not disable auto memory; post-action trace inspection is audit rather than prevention; and Claude
  strips block HTML comments before injection, so the original delivery canary was not decisive.
  The repaired skeleton therefore requires a successful native core `Read`, exact core hash,
  auto-memory disablement, strict-empty MCP plus verified absence of any managed MCP server,
  fail-closed tool/path containment, plain-text canary, and an exact `InstructionsLoaded` include
  event. The historical OS-temp install is now audit-obsoleted for Step 109: #153 must always invoke
  Step 108P's certified packet to create receipt-bound project/config/build/evidence-export roots
  outside the real profile, prove every builder
  deletion target absent immediately before the one explicit build, install from that output, and
  reverify. Step 108P's native parser must compare every captured complete core-read payload to the exact
  verified on-disk bytes and place each required read before the first action.
  The Claude wrapper relocates configuration/temp/plugin state, disables background lifecycle
  surfaces, verifies authentication under the exact isolated environment without exposing a
  credential, waits for the asynchronous delivery logger, and snapshots both contained static
  state and outside-host mutation surfaces. Because managed settings outrank lower sources and effective hooks merge, the selected
  resolution must also enumerate and hash/allowlist the effective managed/plugin/session hook
  surface, managed MCP configuration, and managed skill definitions before launch; managed
  same-name writers and managed-skill shell preprocessing must be rejected. That inventory also
  covers organization-wide managed `CLAUDE.md`/`claudeMd`/policy instructions and every physical
  project ancestor's root or `.claude/CLAUDE.md`, local instruction, rule, same-name-skill, and
  legacy-command/agent/dynamic-context surface. It rejects every process-spawning setting exposed
  by the pinned host, including policy/credential/telemetry helpers and command-backed
  file-suggestion/status-line settings, plus every plugin MCP/LSP/hook/agent/monitor/workflow/channel
  or background component. Each of the four created roots, their common creation parent, and the real profile has both final paths,
  `FILE_ID_INFO`, and link count sampled from one retained handle, and every destructive
  or launch boundary uses a fresh receipt-pinned self-contained fence bundle rooted in an
  OS-admitted static native launcher with a precompiled hash/file-ID/MVID-bound helper as the actual
  executor rather than a mutable live-function consumer or runtime compiler. Immutable pre-build,
  post-install launch-attestation, and post-hook-probe readiness receipts bind the full profile,
  inspector/process results, trust, hook, policy, and exact-environment facts; its process broker
  preventively image/argv-gates every descendant to quiescence. It also proves managed policy cannot
  refresh during startup or binds the exact startup-consumed snapshot before any hook/process can
  fire; a post-launch diff is not preventive. Route 1 derives current build/profile/inspector counts
  and emitted heading location rather than copying `d4c88ee` literals. The three disposable roots,
  durable evidence-export root, their common creation parent, and real profile remain bound from creation through
  disposition by guardian-held handles; both handle-final paths, `FILE_ID_INFO`, and link count are
  remeasured from those same live objects. UNC,
  SUBST, 8.3,
  other aliases, nesting, and case-mismatched allowlist targets are rejected. Project-only settings
  and `--strict-mcp-config` are not treated as managed-policy boundaries.
- No Step-109 host session or writer skill ran. Issue #153 must still choose a core-supported UAT
  mode or deliberately amend the acceptance to operator-scoped named-skill subsection overrides;
  Step 108P/#162 must then implement and negative-test the complete containment packet before the
  first operator row.
- A fresh immutable-blob audit refuted the prior `5B3FC466…995F8` high-0/medium-0 claim. Proven
  defects included PowerShell stdin continuation past a flat `throw`, checkout-dependent mixed-EOL
  hashing, a legacy file-ID shape, an uncontained evidence uploader, global rather than per-mode
  secret binding, stale #153 implementation ownership, a Step-108/108P dependency cycle, a false
  row assignment, and a semantic-grader overclaim. The repair removes unimplemented executable
  sketches, gives every Step-109 fence one terminating statement, binds certification to the Git
  blob, and moves all implementation/schema/post-code-gate obligations to #162. The first immutable
  checkpoint, `bad6f77`, bound Git blob `bec161f56ec42f37b0e2d89cbcbc3b0a51e28f95`; one independent
  review passed, while the second reported 0 high / 2 medium because the UAT still described removed
  replay implementations as present and `plan.md` simultaneously named Phase CP and Phase IS as the
  active authority. Both contradictions were repaired at `596af1b`; one reviewer passed that second
  checkpoint while the other reported 0 high / 4 medium: a removed shape-check implementation was
  still described as present, the historical full-suite paragraph denied Step 108's gate ownership,
  Step 102 falsely said D10 row 4 writes only `AGENTS.md`, and one Phase-CP paragraph still called M3
  the immediate next action. All four were repaired at `e4cdad0`; one reviewer passed that third
  checkpoint while the other reported 0 high / 2 medium: the fixed prelaunch environment sidecar
  circularly required future upload-artifact facts and could not represent two bodies, while cleanup
  was placed both after and inside Step 109. Both ordering defects are repaired. A subsequent
  pre-freeze cross-file pass found two phase-plan summaries that still ordered the entire evidence
  chain before cleanup or placed cleanup after acceptance; they now state first publication,
  cleanup/cleanup attestation, then second publication before Step 109 closes. The next frozen
  candidate is Git blob `417813e04007167dbe81b081e56ea07b017d3427`, whose raw blob bytes have
  SHA-256 `3C8BD6D64DE5B99F9D5E9C54DB8A67B5461AFA30F589E9AEF17C28A0179F34A9`, length 139,223 bytes and
  1,917 LF-terminated lines. All 24 PowerShell-bearing fences parse under Windows PowerShell 5.1,
  all 18 blockers exit nonzero when streamed through `powershell -NoProfile -Command -`, the closed
  credential corpus is 107/107 ordinal-ignore-case unique, manifest regeneration is unchanged, and
  the package-integrity iteration gate passes 278 tests. Two independent reviews of the next
  immutable commit and a stable repo-root gate are still required; neither is claimed by this
  addendum.
- Two attempted post-`52d44c9` repo-root runs are explicitly invalid evidence: one was stopped when
  another session moved `HEAD` and dirtied documentation; the second was stopped when this audit
  found the fail-open transcript. Both sentinels are `-1`. A clean detached repo-root gate at a
  stable repaired commit is still required before Step 108 may return to DONE.

---

## 13. Provenance

Phase 2 of the portfolio proposal at `<dev-root>/docs/agents-md-host-symmetry-plan.md` § Phase
2, a document outside this repository. That reference is **provenance only** — § 1 vendors the
decisive measurement and Step 107 lands it in `documentation/`, so nothing load-bearing depends
on an out-of-tree file.

---

## Appendix

### Decision Inventory

`P` records explicit operator choices already present in this plan. `D` records agent defaults,
accepted as written on 2026-08-20. IDs are stable and append-only: later decisions take the next
ID, while a reversal keeps its ID and records `changed <date>` rather than being removed or
renumbered.

| ID | P/D | Choice | Status |
|---|---|---|---|
| P1 | P | `plan-init` authors the inverted `AGENTS.md`-primary shape only when both instruction files are absent and never overwrites a substantive `CLAUDE.md` | operator-picked 2026-08-20 |
| P2 | P | `repo-update` reports dual-substantive drift as an always-print advisory that never blocks or halts | operator-picked 2026-08-20 |
| D3 | D | If the write-surface gate is resurrected, enumerate both core and provider surfaces with separate non-empty floors derived at test time | implementation deferred 2026-08-25 (§ 10) |
| D4 | D | Let the complete Step 103 enumeration determine the repair set instead of freezing a file list | accepted 2026-08-20 |
| D5 | D | Leave this repository's own root instruction files unchanged and accept its temporary Codex content gap | accepted 2026-08-20 |
| D6 | D | Keep the instruction-file contract in one owning core and create no `_shared/` file | accepted 2026-08-20 |
| D7 | D | Leave legacy top-level skill packages stale as recorded, accepted drift | accepted 2026-08-20 |
| D8 | D | Classify both instruction filenames as ABSENT, POINTER, or SUBSTANTIVE using the stated content rules | accepted 2026-08-20 |
| D9 | D | Preserve context-slim's `CLAUDE.md`-anchored ancestor walk and change only the content file it reads or appends to | accepted 2026-08-20 |
| D10 | D | Apply the five-row instruction-file behavior matrix exactly across `plan-init` and `repo-update` | accepted 2026-08-20 |
| D11 | D | Permit only guarded `CLAUDE.md` writes and enforce one owner through marker, probe-literal, and bounded-citation gates | accepted 2026-08-20 |
