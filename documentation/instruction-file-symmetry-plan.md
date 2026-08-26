# Phase IS — instruction-file symmetry

**Phase label:** `Phase IS` (instruction-file symmetry). Steps 100–109.
**Status:** REDLINE ACCEPTED (Publication 2, 2026-08-20) — issues synced 2026-08-21 under
umbrella #143; all ten `**Issue:**` fields populated.
**Created:** 2026-08-20 against `main` @ `1f410fc`. **Revised twice** — after plan-review
round 1 (22 Blockers) and plan-wrap round 2 (9 Blockers). Revision log: § 12.

**Reading aid.** `P<n>` = operator-picked decision *n* and `D<n>` = agent-defaulted decision
*n* in § 6. `A` = the project's `AGENTS.md`, `C` = its `CLAUDE.md`. Angle brackets inside a citation spelling like
`<repo>/_shared/<leaf>` are **literal source bytes**, not a substitution — see D6.

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

**Reproduction** (read-only; runs no model session and writes nothing):

```
cd <project-dir>
codex debug prompt-input
```

Its JSON output contains the instruction text Codex would send. Grep it for a heading you
expect (`## Stack`); absence means the content never reached the model. A one-invocation
config override that does **not** persist:
`codex debug prompt-input -c 'project_doc_fallback_filenames=["CLAUDE.md"]'`.

---

## 2. Existing Context

- **Cores and adapters.** `skills/<name>/core.md` is the provider-independent behavior
  contract; `skills/<name>/providers/{claude,gpt,codex}.md` are thin loaders that may never
  weaken a core gate. Verified: `plan-init` is a 488-line core against 21/22/19-line adapters.
- **54 cores, 57 skill directories.** The three provider-native skills (`claude-oauth-auth`,
  `context-slim`, `judge-motion`) carry `core: null` and have **no core.md**.
  `skills/*/core.md` reaches 54 directories; `skills/*/providers/*.md` reaches all 57
  (57 claude + 54 gpt + 54 codex = 165). Step 106 derives its floors from these numbers by
  re-running the enumeration, never by hard-coding them.
- **24 of the 54 cores name `CLAUDE.md`** (`grep -l 'CLAUDE\.md' skills/*/core.md | wc -l`);
  **3 name `AGENTS.md`** (`plan-feature`, `plan-merge`, `plan-review`); **3 of the 165 provider
  files name `CLAUDE.md`** (`context-slim/providers/claude.md`, `plan-init/providers/codex.md`,
  `judge-motion/providers/claude.md`).
- **The seven-section contract is duplicated** in `skills/plan-init/core.md:446-458` and
  `skills/repo-update/core.md:240-248`. **The two are NOT verbatim duplicates** — same bold
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
  source and build toolchain, not an installed tree. The installed
  `<dev-root>/.claude/skills/plan-init/core.md` is a **separate 26,477-byte copy**; the
  canonical `skills/plan-init/core.md` is 26,657 bytes. Nothing an operator can invoke changes
  until `tools/build-distributions.ps1` then `tools/install-skill-mesh.ps1` have run. Step 108
  exists solely because of this.
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
  iteration gates and **neither may flip a step or a phase DONE**. Every step below therefore
  ends on the repo-root invocation. This plan restates no count.

---

## 3. Scope

**In scope**

- The instruction-file contract (D8, D10, D11), defined once as a named section in one core.
- The lifecycle writers: `plan-init`, `repo-update`.
- `skills/plan-init/providers/codex.md:11`, the one adapter naming the written artifact.
- Every core or provider file the Step 103 enumeration proves reads or authors a **project**
  instruction file.
- `context-slim`, which writes `CLAUDE.md` under `--apply` and has no core.
- Two package-integrity gates.
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
| `skills/repo-update/core.md` | modify | WRITE core. `:52`; **`:164`** stale-reference grep hardcoding `README.md CLAUDE.md documentation/*.md`; `:236-250` Step 7; `:400` report line; `:438` scrapability | `:164` missed by the round-1 audit |
| `skills/goblin-suggest/core.md` | modify | READ, breaks silently. `:33` is a **precondition**; a stub passes the existence check so the documented loud grounding failure never fires | `:13, :33, :102, :178` |
| `skills/build-observer/core.md` | modify | READ, breaks. `:57` has no AGENTS.md arm | `:57` |
| `skills/research-prospect/core.md` | modify | READ, breaks. `:61` baked into a dispatched sub-agent prompt | `:51, :61` |
| `skills/user-brainstorm/core.md` | modify | READ, breaks. `:154` grounding list | `:154` |
| `skills/user-learn/core.md` | modify | READ, breaks. `:161` states verbatim the failure a stub produces | `:47, :104, :161` |
| `skills/citation-review/core.md` | modify | READ — missed by round 1. `:12` names a project `CLAUDE.md` as a reviewable artifact class | `:12, :46-47` |
| `skills/context-slim/providers/claude.md` | modify | **WRITES** under `--apply` (`:166`); ancestor walk (`:21, :23-24`); classification (`:59-61`). **16 `CLAUDE.md` sites total**, incl. `:3` frontmatter and `:5` default | `ls skills/context-slim/` → `providers/claude.md` only |
| *(the round-2 candidates)* | **no change** | `repo-sync:51,:521`, `observatory-doctor:78`, `build-phase:31,:198,:229` — **all adjudicated REFERENCE** by § 4.2; none joins Step 104's work-list | § 4.2 |
| `tests/package-integrity/test_instruction_file_contract.py` | create | write-surface gate | absent today |
| `tests/package-integrity/test_instruction_contract_single_owner.py` | create | single-owner gate | absent today |
| `documentation/codex-instruction-delivery.md` | create | vendored measurement + reproduction recipe (§ 1's content, expanded) | absent today |
| `documentation/host-discovery.md`, `documentation/architecture.md` | modify | document the inverted shape in the authority map and the contract | both exist |
| `documentation/phase-75-baseline.md` | modify | single owner of the suite counts this plan changes | `CLAUDE.md` names it the one owner |

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
- **`tests/package-integrity/test_instruction_file_contract.py`** — the write-surface gate.
- **`tests/package-integrity/test_instruction_contract_single_owner.py`** — the single-owner
  gate.

---

## 6. Design Decisions

**P1 — `plan-init` emits the inverted shape when it authors an instruction file.** *(operator,
2026-08-20.)* Scoped by D10: it applies to D10 row 1 (both files ABSENT) only. It **never
overwrites an existing SUBSTANTIVE `CLAUDE.md`**. *Rejected:* detect-then-follow; an opt-in flag.

**P2 — `repo-update` reports drift as an always-print advisory that never blocks.** *(operator,
2026-08-20.)* Matches `.claude/rules/advisory-calls.md`; keeps the `/build-phase` halt allowlist
closed. Load-bearing because `/repo-update` also runs **unattended** inside phase wraps and via
`/repo-wrap` Rail A — its registered-owned-project rail, which delegates verbatim to
`/repo-update` (`skills/repo-wrap/core.md:124-126`).

**D3 — The write-surface gate enumerates every surface, with a PER-ARM floor.** Enumerates
`skills/*/core.md` **and** `skills/*/providers/*.md`, each arm carrying its own non-empty floor
re-derived at test time (54 and 165 per § 2), because one combined floor is satisfiable while an
arm is empty. D6 removes the would-be third surface rather than gating it. *Rationale:* this
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
- **SUBSTANTIVE** — the file exists, carries at least one `##` section heading, and is not a
  pointer.

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
under `skills/`; the single-owner gate probes for them and the write-surface gate excludes
their own section:

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
  exist for prose; the achievable analogue is the single-owner gate (Step 106b), proven here by
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
- **Done when:** all five D10 rows walked; **row 2 creates no `AGENTS.md`**; row 5 never blocks and never halts; `:164` scans the content file; every `CLAUDE.md` write carries D11's canonical marker in its section; the prose states that rows 3–4 write only `AGENTS.md`, so a second pass is a textual no-op (the *executed* fixed-point check belongs to Step 109); the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
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
- **Problem:** Repoint each core Step 103 classified as a READ of a **project** instruction file to the canonical phrasing `CLAUDE.md or AGENTS.md`. Known members: `build-observer:57`, `research-prospect:61`, `user-brainstorm:154`, `user-learn:161`, `citation-review:12`, plus whatever Step 103 added. `goblin-suggest:33` additionally needs its grounding **precondition** repaired: it currently treats existence as sufficient, so a POINTER passes and the documented loud failure never fires.
- **Type:** code
- **Issue:** #148
- **Files:** skills/goblin-suggest/core.md, skills/build-observer/core.md, skills/research-prospect/core.md, skills/user-brainstorm/core.md, skills/user-learn/core.md, skills/citation-review/core.md, skills/review-uat/core.md
- **Flags:** --reviewers code
- **Produces:** modified cores for every reader Step 103 proved broken
- **Done when:** every core on Step 103's broken list names both files with the canonical phrasing; goblin-suggest's precondition fails loud on a POINTER; the verified-safe readers are unmodified; no core carries a designated probe literal; the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 103
- **Status:** NOT STARTED

### Step 105: Make context-slim inversion-aware
- **Problem:** `skills/context-slim/providers/claude.md` walks the `CLAUDE.md` ancestor chain (`:21, :23-24`), classifies sections (`:59-61`), and **writes** under `--apply` (`:166`). Provider-native, no `core.md`. On an inverted project it audits a pointer file and reports near-zero context cost — a false green. Per D9 **keep the CLAUDE.md-anchored ancestor walk** and change only what is read and appended to. The file names `CLAUDE.md` at **16 sites**, including `:3` (its emitted `description:` frontmatter) and `:5` (the `--project` default) — enumerate all of them, do not work from the four cited here. As an adapter it may not cite `<repo>/_shared/`; it carries D11's bounded cite phrase.
- **Type:** code
- **Issue:** #149
- **Files:** skills/context-slim/providers/claude.md
- **Flags:** --reviewers code
- **Produces:** modified context-slim adapter
- **Done when:** **every `CLAUDE.md` occurrence in the file is enumerated and given an explicit keep-or-repoint verdict**; on an inverted project the audit reads and `--apply` appends to the content file; the ancestor-walk anchor is unchanged so `user-afterparty`'s parity holds; non-inverted behavior unchanged; the file carries no `<repo>/_shared/` citation and neither probe literal; the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 100
- **Status:** NOT STARTED

### Step 106: The two gates
- **Problem:** Nothing asserts instruction-file handling anywhere. **(a) Write-surface gate** (`test_instruction_file_contract.py`): enumerate `skills/*/core.md` AND `skills/*/providers/*.md`, asserting no surface carries an **unguarded** `CLAUDE.md` write per D11 — a write verb in a section with no `CLAUDE.md or AGENTS.md` marker. Per-arm non-empty floors re-derived at test time (§ 2's 54 and 165), never hard-coded. Report the measured false-positive count against Step 103's enumerated REFERENCE bucket rather than asserting zero. **Read § 4.2.4 finding 10 before authoring the proofs** — it records that the planted defects named in this step's `Done when` cannot detect a predicate narrowed into uselessness, and names the additional proofs (one per covered write verb, plus the far-marker proof) the gate needs beyond them. **(b) Single-owner gate** (`test_instruction_contract_single_owner.py`): modeled on `test_autofix_marker_single_owner.py` — the owner section exists and carries both D11 probe literals; each declared citer carries the bounded cite phrase; **no other file under `skills/**/*.md`, `_shared/**/*.md` or `documentation/**/*.md` carries either probe literal** (the sweep must include `_shared/`, which is also the only mechanical enforcement of Step 100's "no `_shared/` file was created"). Neither gate may red on this repository's own root files (D5), and neither may be worded as a restatement of `documentation/host-discovery.md:158-160`, which is the installer axis. **Known self-collision, found during Step 101 (2026-08-25) — do not rediscover this at build time.** This plan file is itself under `documentation/**` and quotes probe literal 1 *verbatim* inside D11's designated-probe-literals bullet — **locate both literals by grep, never by a line number: this plan's numbers shift on every edit and this citation has already gone stale three times** — so the sweep as specified reds on the plan. Probe literal 2 sits on the following line, **unbolded** inside backticks, so it collides only if the gate matches the bare sentence rather than the bolded literal the owner declares. Decide the rule explicitly and state it in the test: exempt this plan by path, or match the exact bolded literal and re-word the literal-1 line.
- **Type:** code
- **Issue:** #150
- **Files:** tests/package-integrity/test_instruction_file_contract.py, tests/package-integrity/test_instruction_contract_single_owner.py, skills/plan-init/core.md
- **Flags:** --reviewers deep
- **Produces:** both gate files
- **Done when:** both gates green; **every new assertion proven RED against a planted defect** — an unguarded `CLAUDE.md` write re-introduced in a core, again in a provider file, the owner section renamed, a citation deleted, a probe literal re-duplicated into a second file, and a `_shared/` file created carrying one (six proofs, each restored); the measured false-positive count against Step 103's REFERENCE bucket is reported and is zero; `test_recovery_plan_hygiene.py` still passes; the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 101, 102, 104, 105
- **Status:** NOT STARTED

### Step 107: Vendor the measurement, document the shape, update the count owner
- **Problem:** Create `documentation/codex-instruction-delivery.md` holding § 1's measurement table, the `codex-cli 0.147.0` pin, and the `codex debug prompt-input` reproduction recipe, so nothing load-bearing depends on an out-of-tree file. Document the inverted shape in `documentation/host-discovery.md` (the host-loading authority) and the adapter view in `documentation/architecture.md` (the contract). Record D7's accepted legacy drift citing `documentation/parity-deltas.md`. Then **measure the repo-root run first, compare against the count recorded in `documentation/phase-75-baseline.md` BEFORE this step, and only then write the new count into that owner** — in that order, so the comparison is not circular.
- **Type:** code
- **Issue:** #151
- **Files:** documentation/codex-instruction-delivery.md, documentation/host-discovery.md, documentation/architecture.md, documentation/phase-75-baseline.md
- **Flags:** --reviewers code
- **Produces:** the vendored measurement file; the inverted shape documented in the authority map and the contract; updated count owner
- **Done when:** the measurement and recipe are verifiable from inside this repository with no out-of-tree link; the authority map and the contract both describe the inverted shape; the legacy-drift decision cites its record; the repo-root `python -m pytest` was measured, compared against the pre-step recorded count, and the owner then updated to the new figure
- **Depends on:** 106
- **Status:** NOT STARTED

### Step 108: Build and install into a scratch home
- **Problem:** Editing a core changes nothing invokable — this repository is the canonical source, not an installed tree, and the installed `<dev-root>/.claude/skills/plan-init/core.md` is a separate 26,477-byte copy against the canonical 26,657. Without this step, Step 109 would exercise the OLD behavior and report PASS. Build all three profiles and install the claude profile into a **disposable scratch home** (never the operator's real home), then verify the emitted core actually carries the new contract.
- **Type:** code
- **Issue:** #152
- **Files:** documentation/findings/instruction-file-symmetry-uat.md
- **Flags:** --reviewers code
- **Produces:** a scratch install home plus the verification transcript appended to the findings file
- **Done when:** `powershell -File tools/build-distributions.ps1 -Provider all` exits 0; `powershell -File tools/install-skill-mesh.ps1 -Provider claude -Home <scratch-home>` exits 0; `powershell -File tools/inspect-host-install.ps1 -Home <scratch-home>` reports the profile installed; and the emitted `plan-init/core.md` under the scratch home is confirmed to contain the `## Instruction-file contract` section — i.e. the new behavior is what a host would load
- **Depends on:** 107
- **Status:** NOT STARTED

### Step 109: Operator confirmation of all five D10 rows
- **Problem:** These cores are prose read by an agent; a test asserts what the prose instructs, never what an agent does. Using the Step 108 scratch home and a **disposable scratch project**, exercise every D10 row: run `/plan-init` from nothing (row 1) and verify `AGENTS.md` plus a `CLAUDE.md` matching D8's exact pointer bytes; run it beside a SUBSTANTIVE `CLAUDE.md` (row 2) and verify it writes nothing; run `/repo-update` on the inverted project (row 3) and verify it refreshes `AGENTS.md`, leaves the pointer, and is a no-op on a second pass; manufacture row 5 and verify the advisory prints without blocking. Then verify delivery on both hosts: `codex debug prompt-input` in the scratch project must show the section headings, and the Claude-side `@AGENTS.md` import must resolve.
- **Type:** operator
- **Issue:** #153
- **Files:** documentation/findings/instruction-file-symmetry-uat.md
- **Flags:** --reviewers code
- **Produces:** `documentation/findings/instruction-file-symmetry-uat.md` — operator observations only, no code artifacts
- **Done when:** all five D10 rows confirmed on disk; the second `/repo-update` pass is observed to be a no-op; `codex debug prompt-input` shows the content; the Claude `@` import resolves; the row-5 advisory prints without blocking; every behavioral difference recorded
- **Depends on:** 108
- **Status:** NOT STARTED

**Rollback.** Every step is `git revert`-able in this repository alone; no step writes into any
consumer project. Steps 108–109 write only into a disposable scratch home and scratch project,
which are deleted rather than reverted.

---

## 8. Risks and Open Questions

| Item | Risk | Mitigation |
|---|---|---|
| Prose cores are not executable | A gate asserts instructions, never agent behavior | Steps 108–109 build, install and run for real; the limitation is stated in § 6 |
| The gate's predicate over prose | An unguarded-write predicate could still false-red the REFERENCE bucket | D11 gives the marker; Step 106 must **report a measured false-positive count** against Step 103's enumerated bucket, not assert zero |
| Enumeration set | A cores-only sweep misses `context-slim` — the #142 shape | D3's dual enumeration with per-arm floors; D6 removes the third surface; Step 106b's sweep includes `_shared/` |
| Backward compatibility | ~32 non-inverted projects must keep working | D10 row 2; every writer step's Done-when carries it; Step 109 exercises it |
| Destructive overwrite | A naive P1 implementation would replace a user's `CLAUDE.md` with a pointer | P1 is scoped to D10 row 1; Step 101's Done-when requires the no-write case be provable |
| `repo-update` runs unattended | It executes inside phase wraps and `/repo-wrap` Rail A | P2's never-block/never-halt is load-bearing and stated |
| Report strings | `:462` and `:400` change | Verified: no test and no code consumes either. Steps 101/102 quote the new strings verbatim in their checkpoints so both writers agree |
| skill-mesh's own root files | An edit reds `test_recovery_plan_hygiene.py:41-60` | D5 scopes them out; D8's worked example fixes their classification as row 2; Step 106's Done-when re-asserts the test passes |
| **Resolved — dev-observatory scrape** | Does the descriptor scrape follow content to `AGENTS.md`? | **Yes.** `descriptor.py:31-33` — the scrape checks every descriptor file present and **unions** commands and ports, reporting the highest-precedence present file only as the `source` label; `AGENTS.md` is at PRECEDENCE index 1. An inverted project keeps its verbs and ports; only the attributed label changes. *(Step 101 correction, 2026-08-25: that last clause is loose. `descriptor.py:272` does `source = present[0]` over a `PRECEDENCE` tuple led by `CLAUDE.md`, so on an inverted project the label stays `CLAUDE.md` — it does not move to `AGENTS.md`. The operative half of this row is correct and unchanged: verbs and ports survive because the same loop unions them across every present file. plan-init's prose states the corrected version.)* Step 101 must therefore keep `:475`'s scrapability constraint but apply it to whichever file is SUBSTANTIVE. *(Round 2 also retracted an incorrect caveat: `descriptor.py:246`'s `except OSError, UnicodeDecodeError:` is PEP 758 syntax, legal on the installed Python 3.14.3 — not Python 2, not broken.)* |

---

## 9. Testing Strategy

**What is added.** Two gates (§ 5). The write-surface gate enumerates both arms with per-arm
floors re-derived at test time. The single-owner gate follows
`test_autofix_marker_single_owner.py` — this repository's proven pattern for a shared prose
constant, and the achievable analogue of a data-pipeline smoke gate.

**Proof obligation.** Six planted-defect proofs, each restored: an unguarded `CLAUDE.md` write
in a core; the same in a provider file; the owner section renamed; a citation deleted; a probe
literal re-duplicated into a second file; a `_shared/` file created carrying one.

**What might break, and why each is named.** `test_recovery_plan_hygiene.py:41-60` if this
repo's own root files are touched (D5 forbids it). `test_link_resolution.py` if any step
introduces a new dangling reference — its allowlist is **shrink-only**, so a new key is a hard
fail, not an amendable baseline. `test_distributions.py:770-777` if any adapter acquires a
`<repo>/_shared/` citation. D6 avoids all three by creating no `_shared/` file.

**Gates.** `python -m pytest tests/` and `python -m pytest tests/package-integrity` are
in-step **iteration** gates only — `documentation/phase-75-baseline.md` states in its own words
that neither may flip a step or a phase DONE. **Every step's final Done-when therefore runs the
repo-root `python -m pytest` with no path argument**, covering the eight `tests/` suites plus
`_shared/`, `skill-iterate/scripts/` and `skill-eval-setup/scripts/`. Counts are owned by
`phase-75-baseline.md`; this plan restates none, and Step 107 updates the owner in a
non-circular order.

**End-to-end.** Step 108 makes the edited prose actually loadable; Step 109 exercises it. Step
109 is `Type: operator` and produces observations only.

---

## 10. Deferred to a future phase

Round 2 identified these as real but out of scope here; recorded so they are not lost:

- `session-wrap:60`'s plan-location citation is genuinely ambiguous between the project and
  workspace instruction file. Step 103 classified it as a WORKSPACE reference (§ 4.2 row 16), so it
  is out of the contract and is not a Step 104 member.
- The seven-section contract remains duplicated across `plan-init` and `repo-update` with no
  single owner. This plan deliberately does not merge them (§ 3); the duplication predates the
  feature and is tracked separately.

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
- **Every step now ends on the repo-root DONE gate.** Six steps had been flipping DONE on
  `python -m pytest tests/`, which the cited count owner explicitly forbids.
- **Step 102's executed fixed-point check moved to Step 109** — it required operator presence
  in a `Type: code` step.
- **§ 1 renamed to "What This Is"** so dev-observatory's goal scrape matches
  (`observer.py:50` tests exact membership), and the measurement vendored inline.
- **Resolved the dev-observatory open row** and retracted its incorrect Python-2 caveat.
- Minor: `repo-update:240-248` citation corrected (it had excluded section 7); `<repo>`/`<leaf>`
  noted as literal bytes; decision-ID legend added; Rail A glossed; Step 107's count update ordered
  non-circularly; `judge-motion/providers/claude.md:146` named alongside `tier-escalate`;
  context-slim's 16 sites flagged against the 4 cited.

**Round 3 (plan-redline)** — Publication 1 rendered beside this plan; the stable proposal
locator and append-only Decision Inventory were added. The two choices already marked
`operator, 2026-08-20` became P1–P2; the remaining design decisions remain D3–D11 as agent
defaults pending feedback. No implementation behavior changed.

**Round 4 (plan-redline feedback)** — the operator accepted Publication 1 as written on
2026-08-20. D3–D11 retain their stable IDs and are marked accepted; the same proposal locator
was refreshed as Publication 2. No decision or implementation behavior changed.

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
| D3 | D | Enumerate both core and provider write surfaces with separate non-empty floors derived at test time | accepted 2026-08-20 |
| D4 | D | Let the complete Step 103 enumeration determine the repair set instead of freezing a file list | accepted 2026-08-20 |
| D5 | D | Leave this repository's own root instruction files unchanged and accept its temporary Codex content gap | accepted 2026-08-20 |
| D6 | D | Keep the instruction-file contract in one owning core and create no `_shared/` file | accepted 2026-08-20 |
| D7 | D | Leave legacy top-level skill packages stale as recorded, accepted drift | accepted 2026-08-20 |
| D8 | D | Classify both instruction filenames as ABSENT, POINTER, or SUBSTANTIVE using the stated content rules | accepted 2026-08-20 |
| D9 | D | Preserve context-slim's `CLAUDE.md`-anchored ancestor walk and change only the content file it reads or appends to | accepted 2026-08-20 |
| D10 | D | Apply the five-row instruction-file behavior matrix exactly across `plan-init` and `repo-update` | accepted 2026-08-20 |
| D11 | D | Permit only guarded `CLAUDE.md` writes and enforce one owner through marker, probe-literal, and bounded-citation gates | accepted 2026-08-20 |
