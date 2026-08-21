# Phase IS — instruction-file symmetry

**Phase label:** `Phase IS` (instruction-file symmetry). Steps 100–109.
**Status:** WRAPPED (round 2) — not sync'd. No issues minted; all ten `**Issue:**` fields blank.
**Created:** 2026-08-20 against `main` @ `1f410fc`. **Revised twice** — after plan-review
round 1 (22 Blockers) and plan-wrap round 2 (9 Blockers). Revision log: § 12.

**Reading aid.** `D<n>` = design decision *n* in § 6. `A` = the project's `AGENTS.md`,
`C` = its `CLAUDE.md`. Angle brackets inside a citation spelling like
`<repo>/_shared/<leaf>` are **literal source bytes**, not a substitution — see D6.

---

## 1. What This Is

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

**This table is an INPUT, not a premise.** Plan-review round 1 proved the original audit's
REFERENCE bucket unreliable — it missed `citation-review` (a READ), `repo-update:164` (a READ
inside a WRITE core) and `plan-init:481`. Plan-wrap round 2 found three more candidates
(`repo-sync`, `observatory-doctor`, `build-phase`). **Step 103 re-derives the whole
classification by enumeration and records it; Step 104 then repoints what it proves broken.**

**Classification rules** (the taxonomy Steps 103 and 106 both consume):

- **WRITE** — the prose orders the agent to create, overwrite, or edit the file.
- **READ** — the prose orders the agent to open it for grounding or ground truth.
- **REFERENCE** — the file is named as an example, a locator, or a *workspace-level* artifact
  the skill never opens.

| File | Change Type | Reason | Verified |
|---|---|---|---|
| `skills/plan-init/core.md` | modify | WRITE core **and** contract owner. `:439-475` bootstrap; `:443` skip guard; `:446-458` seven sections; `:460` the write; `:462` report string; `:475` scrapability; `:481` post-save handoff | `grep -n` → **7** lines: 439, 441, 443, 460, 462, 475, 481 |
| `skills/plan-init/providers/codex.md` | modify | `:11` names the bootstrapped `CLAUDE.md` as the file Codex writes | only provider file naming the written artifact |
| `skills/repo-update/core.md` | modify | WRITE core. `:52`; **`:164`** stale-reference grep hardcoding `README.md CLAUDE.md documentation/*.md`; `:236-250` Step 7; `:400` report line; `:438` scrapability | `:164` missed by the round-1 audit |
| `skills/goblin-suggest/core.md` | modify | READ, breaks silently. `:33` is a **precondition**; a stub passes the existence check so the documented loud grounding failure never fires | `:13, :33, :102, :178` |
| `skills/build-observer/core.md` | modify | READ, breaks. `:57` has no AGENTS.md arm | `:57` |
| `skills/research-prospect/core.md` | modify | READ, breaks. `:61` baked into a dispatched sub-agent prompt | `:51, :61` |
| `skills/user-brainstorm/core.md` | modify | READ, breaks. `:154` grounding list | `:154` |
| `skills/user-learn/core.md` | modify | READ, breaks. `:161` states verbatim the failure a stub produces | `:47, :104, :161` |
| `skills/citation-review/core.md` | modify | READ — missed by round 1. `:12` names a project `CLAUDE.md` as a reviewable artifact class | `:12, :46-47` |
| `skills/context-slim/providers/claude.md` | modify | **WRITES** under `--apply` (`:166`); ancestor walk (`:21, :23-24`); classification (`:59-61`). **16 `CLAUDE.md` sites total**, incl. `:3` frontmatter and `:5` default | `ls skills/context-slim/` → `providers/claude.md` only |
| *(whatever Step 103 adds)* | modify | candidates round 2 named: `repo-sync:51,:521`, `observatory-doctor:78`, `build-phase:31,:198,:229` | Step 103 adjudicates each |
| `tests/package-integrity/test_instruction_file_contract.py` | create | write-surface gate | absent today |
| `tests/package-integrity/test_instruction_contract_single_owner.py` | create | single-owner gate | absent today |
| `documentation/codex-instruction-delivery.md` | create | vendored measurement + reproduction recipe (§ 1's content, expanded) | absent today |
| `documentation/host-discovery.md`, `documentation/architecture.md` | modify | document the inverted shape in the authority map and the contract | both exist |
| `documentation/phase-75-baseline.md` | modify | single owner of the suite counts this plan changes | `CLAUDE.md` names it the one owner |

### Verified as needing NO change

`skills/plan-merge/core.md:232` (already both-file, confirm-gated `:234-235`) ·
`skills/plan-feature/core.md:50` · `skills/plan-review/core.md:201, 229, 463` ·
`skills/user-afterparty/core.md:103-104` (see D9) · `skills/review-uat/core.md:144, 148`
(fails safe) · `skills/repo-wrap/core.md:124-126` (delegates wholly to repo-update) ·
`config/skill-manifest.json` and `tools/gen_manifest.py` (paths, not core content).

**Canonical phrasing.** Steps 101–105 all adopt one spelling: **`CLAUDE.md or AGENTS.md`**, as
already used at `plan-merge:232` and `plan-review:229`. D11 makes it the gate's marker.

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

**D1 — `plan-init` emits the inverted shape when it authors an instruction file.** *(operator,
2026-08-20.)* Scoped by D10: it applies to D10 row 1 (both files ABSENT) only. It **never
overwrites an existing SUBSTANTIVE `CLAUDE.md`**. *Rejected:* detect-then-follow; an opt-in flag.

**D2 — `repo-update` reports drift as an always-print advisory that never blocks.** *(operator,
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
absent file read as substantive and killed D1.)*

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
| SUBSTANTIVE | SUBSTANTIVE *(drift)* | Do not write. Report drift | Refresh **neither**; emit the D2 advisory naming both paths; continue |

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
  Precision D2 depends on: `/repo-update` is not purely operator-invoked — it runs unattended
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
- **Issue:** #
- **Files:** skills/plan-init/core.md, skills/repo-update/core.md
- **Flags:** --reviewers code
- **Produces:** the owner section; a bounded citation in repo-update's core
- **Done when:** the owner section carries D8, D10, D11, both probe literals and the exact pointer bytes; repo-update carries only the bounded cite phrase and neither probe literal; **no `_shared/` file was created**; no new dangling reference; the repo-root `python -m pytest` (no path argument) is green at or above the count recorded in `documentation/phase-75-baseline.md`, skip count unchanged
- **Depends on:** none
- **Status:** NOT STARTED

### Step 101: plan-init authors AGENTS.md-primary, without overwriting anyone
- **Problem:** `skills/plan-init/core.md:439-475` bootstraps `CLAUDE.md` as the content file. Implement D10's `plan-init` column, walking all five rows explicitly. Author `AGENTS.md` and write `CLAUDE.md` as D8's exact pointer bytes **only on row 1**; on row 2 touch neither and report the project non-inverted. Repair the `:443` skip guard, which keys on `CLAUDE.md` existence — a POINTER satisfies it, so plan-init writes nothing on an inverted project. Update the report string at `:462`, the scrapability constraint at `:475` (it is the dev-observatory scrape contract — see § 8's resolved row for what it must say on an inverted project), and the post-save handoff at `:481`. Update `skills/plan-init/providers/codex.md:11`; the adapter carries only D11's bounded cite phrase and neither probe literal.
- **Type:** code
- **Issue:** #
- **Files:** skills/plan-init/core.md, skills/plan-init/providers/codex.md
- **Flags:** --reviewers deep
- **Produces:** modified plan-init core and codex adapter; the new report string quoted verbatim in the step's checkpoint entry
- **Done when:** all five D10 rows are walked explicitly in the prose; **row 2 provably writes nothing**; the skip guard no longer suppresses on a POINTER; every `CLAUDE.md` write in the file carries D11's canonical marker in its section; the adapter carries neither probe literal; the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 100
- **Status:** NOT STARTED

### Step 102: repo-update refreshes the content file and advises on drift
- **Problem:** `skills/repo-update/core.md` Step 7 (`:52`, `:236-250`, `:400`) verifies and creates `CLAUDE.md`. Implement D10's `repo-update` column, walking all five rows. **The only creation path for `AGENTS.md` is D10 row 1 (both files ABSENT); in a project that already has a SUBSTANTIVE `CLAUDE.md` it must never create one** — row 2 refreshes `CLAUDE.md` in place exactly as today, and that write stays legal under D11 by carrying the canonical marker. On row 3 refresh `AGENTS.md` and leave the pointer alone. On row 5 refresh neither and emit the D2 advisory naming both paths, non-blocking. Repoint `:164`, the stale-reference grep hardcoded to `README.md CLAUDE.md documentation/*.md`. Update the report line at `:400`; preserve `:438`.
- **Type:** code
- **Issue:** #
- **Files:** skills/repo-update/core.md
- **Flags:** --reviewers deep
- **Produces:** modified repo-update core; the new report string quoted verbatim in the step's checkpoint entry
- **Done when:** all five D10 rows walked; **row 2 creates no `AGENTS.md`**; row 5 never blocks and never halts; `:164` scans the content file; every `CLAUDE.md` write carries D11's canonical marker in its section; the prose states that rows 3–4 write only `AGENTS.md`, so a second pass is a textual no-op (the *executed* fixed-point check belongs to Step 109); the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 100
- **Status:** NOT STARTED

### Step 103: Re-derive the full classification and record it
- **Problem:** Round 1 proved the § 4 table unreliable and round 2 named three more candidates. Produce the authoritative classification, changing no behavior. Enumerate both arms — `grep -l 'CLAUDE\.md' skills/*/core.md` (24) and `grep -l 'CLAUDE\.md' skills/*/providers/*.md` (3) — and classify every hit WRITE / READ / REFERENCE by § 4's rules, distinguishing a **project** instruction file from a **workspace** one. Adjudicate the round-2 candidates explicitly: `repo-sync:51,:521`, `observatory-doctor:78`, `build-phase:31,:198,:229`. Record the result as a table in this plan. Do not edit any core in this step.
- **Type:** code
- **Issue:** #
- **Files:** documentation/instruction-file-symmetry-plan.md
- **Flags:** --reviewers code
- **Produces:** the authoritative WRITE/READ/REFERENCE table recorded in § 4, derived by the two enumeration commands
- **Done when:** all 24 cores and all 3 provider files are classified with a `path:line` citation each; every round-2 candidate has an explicit verdict; the REFERENCE bucket is fully enumerated by name so Step 106 can prove no false positive against it; no core was modified
- **Depends on:** 100
- **Status:** NOT STARTED

### Step 104: Repoint every reader Step 103 proved broken
- **Problem:** Repoint each core Step 103 classified as a READ of a **project** instruction file to the canonical phrasing `CLAUDE.md or AGENTS.md`. Known members: `build-observer:57`, `research-prospect:61`, `user-brainstorm:154`, `user-learn:161`, `citation-review:12`, plus whatever Step 103 added. `goblin-suggest:33` additionally needs its grounding **precondition** repaired: it currently treats existence as sufficient, so a POINTER passes and the documented loud failure never fires.
- **Type:** code
- **Issue:** #
- **Files:** skills/goblin-suggest/core.md, skills/build-observer/core.md, skills/research-prospect/core.md, skills/user-brainstorm/core.md, skills/user-learn/core.md, skills/citation-review/core.md
- **Flags:** --reviewers code
- **Produces:** modified cores for every reader Step 103 proved broken
- **Done when:** every core on Step 103's broken list names both files with the canonical phrasing; goblin-suggest's precondition fails loud on a POINTER; the verified-safe readers are unmodified; no core carries a designated probe literal; the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 103
- **Status:** NOT STARTED

### Step 105: Make context-slim inversion-aware
- **Problem:** `skills/context-slim/providers/claude.md` walks the `CLAUDE.md` ancestor chain (`:21, :23-24`), classifies sections (`:59-61`), and **writes** under `--apply` (`:166`). Provider-native, no `core.md`. On an inverted project it audits a pointer file and reports near-zero context cost — a false green. Per D9 **keep the CLAUDE.md-anchored ancestor walk** and change only what is read and appended to. The file names `CLAUDE.md` at **16 sites**, including `:3` (its emitted `description:` frontmatter) and `:5` (the `--project` default) — enumerate all of them, do not work from the four cited here. As an adapter it may not cite `<repo>/_shared/`; it carries D11's bounded cite phrase.
- **Type:** code
- **Issue:** #
- **Files:** skills/context-slim/providers/claude.md
- **Flags:** --reviewers code
- **Produces:** modified context-slim adapter
- **Done when:** **every `CLAUDE.md` occurrence in the file is enumerated and given an explicit keep-or-repoint verdict**; on an inverted project the audit reads and `--apply` appends to the content file; the ancestor-walk anchor is unchanged so `user-afterparty`'s parity holds; non-inverted behavior unchanged; the file carries no `<repo>/_shared/` citation and neither probe literal; the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 100
- **Status:** NOT STARTED

### Step 106: The two gates
- **Problem:** Nothing asserts instruction-file handling anywhere. **(a) Write-surface gate** (`test_instruction_file_contract.py`): enumerate `skills/*/core.md` AND `skills/*/providers/*.md`, asserting no surface carries an **unguarded** `CLAUDE.md` write per D11 — a write verb in a section with no `CLAUDE.md or AGENTS.md` marker. Per-arm non-empty floors re-derived at test time (§ 2's 54 and 165), never hard-coded. Report the measured false-positive count against Step 103's enumerated REFERENCE bucket rather than asserting zero. **(b) Single-owner gate** (`test_instruction_contract_single_owner.py`): modeled on `test_autofix_marker_single_owner.py` — the owner section exists and carries both D11 probe literals; each declared citer carries the bounded cite phrase; **no other file under `skills/**/*.md`, `_shared/**/*.md` or `documentation/**/*.md` carries either probe literal** (the sweep must include `_shared/`, which is also the only mechanical enforcement of Step 100's "no `_shared/` file was created"). Neither gate may red on this repository's own root files (D5), and neither may be worded as a restatement of `documentation/host-discovery.md:158-160`, which is the installer axis.
- **Type:** code
- **Issue:** #
- **Files:** tests/package-integrity/test_instruction_file_contract.py, tests/package-integrity/test_instruction_contract_single_owner.py
- **Flags:** --reviewers deep
- **Produces:** both gate files
- **Done when:** both gates green; **every new assertion proven RED against a planted defect** — an unguarded `CLAUDE.md` write re-introduced in a core, again in a provider file, the owner section renamed, a citation deleted, a probe literal re-duplicated into a second file, and a `_shared/` file created carrying one (six proofs, each restored); the measured false-positive count against Step 103's REFERENCE bucket is reported and is zero; `test_recovery_plan_hygiene.py` still passes; the repo-root `python -m pytest` green at or above the recorded count, skip unchanged
- **Depends on:** 101, 102, 104, 105
- **Status:** NOT STARTED

### Step 107: Vendor the measurement, document the shape, update the count owner
- **Problem:** Create `documentation/codex-instruction-delivery.md` holding § 1's measurement table, the `codex-cli 0.147.0` pin, and the `codex debug prompt-input` reproduction recipe, so nothing load-bearing depends on an out-of-tree file. Document the inverted shape in `documentation/host-discovery.md` (the host-loading authority) and the adapter view in `documentation/architecture.md` (the contract). Record D7's accepted legacy drift citing `documentation/parity-deltas.md`. Then **measure the repo-root run first, compare against the count recorded in `documentation/phase-75-baseline.md` BEFORE this step, and only then write the new count into that owner** — in that order, so the comparison is not circular.
- **Type:** code
- **Issue:** #
- **Files:** documentation/codex-instruction-delivery.md, documentation/host-discovery.md, documentation/architecture.md, documentation/phase-75-baseline.md
- **Flags:** --reviewers code
- **Produces:** the vendored measurement file; the inverted shape documented in the authority map and the contract; updated count owner
- **Done when:** the measurement and recipe are verifiable from inside this repository with no out-of-tree link; the authority map and the contract both describe the inverted shape; the legacy-drift decision cites its record; the repo-root `python -m pytest` was measured, compared against the pre-step recorded count, and the owner then updated to the new figure
- **Depends on:** 106
- **Status:** NOT STARTED

### Step 108: Build and install into a scratch home
- **Problem:** Editing a core changes nothing invokable — this repository is the canonical source, not an installed tree, and the installed `<dev-root>/.claude/skills/plan-init/core.md` is a separate 26,477-byte copy against the canonical 26,657. Without this step, Step 109 would exercise the OLD behavior and report PASS. Build all three profiles and install the claude profile into a **disposable scratch home** (never the operator's real home), then verify the emitted core actually carries the new contract.
- **Type:** code
- **Issue:** #
- **Files:** documentation/findings/instruction-file-symmetry-uat.md
- **Flags:** --reviewers code
- **Produces:** a scratch install home plus the verification transcript appended to the findings file
- **Done when:** `powershell -File tools/build-distributions.ps1 -Provider all` exits 0; `powershell -File tools/install-skill-mesh.ps1 -Provider claude -Home <scratch-home>` exits 0; `powershell -File tools/inspect-host-install.ps1 -Home <scratch-home>` reports the profile installed; and the emitted `plan-init/core.md` under the scratch home is confirmed to contain the `## Instruction-file contract` section — i.e. the new behavior is what a host would load
- **Depends on:** 107
- **Status:** NOT STARTED

### Step 109: Operator confirmation of all five D10 rows
- **Problem:** These cores are prose read by an agent; a test asserts what the prose instructs, never what an agent does. Using the Step 108 scratch home and a **disposable scratch project**, exercise every D10 row: run `/plan-init` from nothing (row 1) and verify `AGENTS.md` plus a `CLAUDE.md` matching D8's exact pointer bytes; run it beside a SUBSTANTIVE `CLAUDE.md` (row 2) and verify it writes nothing; run `/repo-update` on the inverted project (row 3) and verify it refreshes `AGENTS.md`, leaves the pointer, and is a no-op on a second pass; manufacture row 5 and verify the advisory prints without blocking. Then verify delivery on both hosts: `codex debug prompt-input` in the scratch project must show the section headings, and the Claude-side `@AGENTS.md` import must resolve.
- **Type:** operator
- **Issue:** #
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
| Destructive overwrite | A naive D1 would replace a user's `CLAUDE.md` with a pointer | D1 is scoped to D10 row 1; Step 101's Done-when requires the no-write case be provable |
| `repo-update` runs unattended | It executes inside phase wraps and `/repo-wrap` Rail A | D2's never-block/never-halt is load-bearing and stated |
| Report strings | `:462` and `:400` change | Verified: no test and no code consumes either. Steps 101/102 quote the new strings verbatim in their checkpoints so both writers agree |
| skill-mesh's own root files | An edit reds `test_recovery_plan_hygiene.py:41-60` | D5 scopes them out; D8's worked example fixes their classification as row 2; Step 106's Done-when re-asserts the test passes |
| **Resolved — dev-observatory scrape** | Does the descriptor scrape follow content to `AGENTS.md`? | **Yes.** `descriptor.py:31-33` — the scrape checks every descriptor file present and **unions** commands and ports, reporting the highest-precedence present file only as the `source` label; `AGENTS.md` is at PRECEDENCE index 1. An inverted project keeps its verbs and ports; only the attributed label changes. Step 101 must therefore keep `:475`'s scrapability constraint but apply it to whichever file is SUBSTANTIVE. *(Round 2 also retracted an incorrect caveat: `descriptor.py:246`'s `except OSError, UnicodeDecodeError:` is PEP 758 syntax, legal on the installed Python 3.14.3 — not Python 2, not broken.)* |

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
  workspace instruction file. Step 103 will classify it; if it lands as a project READ it moves
  into Step 104, otherwise it is deferred.
- The seven-section contract remains duplicated across `plan-init` and `repo-update` with no
  single owner. This plan deliberately does not merge them (§ 3); the duplication predates the
  feature and is tracked separately.

---

## 11. Verdict history

| Round | Skill | Verdict |
|---|---|---|
| 1 | `/plan-review` | 22 Blockers, 38 significant gaps — all addressed in § 12 |
| 2 | `/plan-wrap` | 9 Blockers — all addressed in § 12 |
| — | `/plan-redline` | **Not run.** Operator P/D feedback still owed before `/repo-sync` |

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
  D1. It also left `AGENTS.md` unclassified, which made **this repository's own root pair**
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
  noted as literal bytes; `D<n>` legend added; Rail A glossed; Step 107's count update ordered
  non-circularly; `judge-motion/providers/claude.md:146` named alongside `tier-escalate`;
  context-slim's 16 sites flagged against the 4 cited.

---

## 13. Provenance

Phase 2 of the portfolio proposal at `<dev-root>/docs/agents-md-host-symmetry-plan.md` § Phase
2, a document outside this repository. That reference is **provenance only** — § 1 vendors the
decisive measurement and Step 107 lands it in `documentation/`, so nothing load-bearing depends
on an out-of-tree file.
