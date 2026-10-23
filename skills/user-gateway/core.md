# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, Codex, GPT) must load it in full.

## Provider-neutral host abstractions

- Resolve runtime supporting assets and relative script paths against `.claude/skills/user-gateway/`. The repository evaluation corpus described under Maintenance is source-only and is not a runtime asset.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Before Step 0, read `<repo>/_shared/skill-pipeline.md`, `<repo>/_shared/intake-engine.md`, and `<repo>/_shared/shakedown-engine.md` in full. These three files jointly own route selection, ledger behavior, and the reused topic-slug rule. If any is unavailable, write nothing and return `required_tool_missing` naming it.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# user-gateway

A THIN converter for the pre-work moment. The operator has a head full of half-formed
observations about a topic — some broken things, some worries, some wishes, an undecided
question — and wants them made concrete without anything getting lost or invented. This
skill composes three existing contracts and owns NO routing table and NO ledger grammar
of its own:

- **Routing** — `<repo>/_shared/skill-pipeline.md`
  (the routing web) is the ONE owner of the rails, their entry conditions, the tiebreak
  rule, the re-route edges, and the re-route contract. The gateway CONSULTS it per
  fragment and cites it in output; per the web's own intro, no skill hardcodes its own
  routing table — reproducing the web's rail/entry-condition table in this file or in
  gateway output (verbatim or paraphrased) is a DEFECT.
- **Ledger** — `<repo>/_shared/intake-engine.md`
  owns the ledger path formula + topic-slug rule (§1 — which itself reuses the
  shakedown-engine §1 slug rule by cross-reference), the row grammar + `F<N>` ids +
  status vocabulary + one-line disposition rule (§2), the zero-open check + canonical
  `/goal` string (§3), and idempotent seeding (§4). Cite it; never restate it.
- **Listening** — [`../user-draft/core.md`](../user-draft/core.md) Step 2 + Principles
  own the discipline: find the gaps, ask 3-5 targeted questions in at most ONE round,
  never block.

**Pinned posture: CONVERT, DON'T PROPOSE.** Every ledger row and every seed traces to a
fragment the operator voiced (or to their answer to a clarifying question). The gateway
never invents work the operator didn't voice — generating improvement ideas is
[`/goblin-suggest`](../goblin-suggest/core.md)'s job, and the boundary is hard: an
unprompted suggestion in gateway output ("while we're in there…", "you should also…") is
a DEFECT, not a bonus.

## Contract

- **Input:** an optional topic and the free-text vent (Step 0).
- **Output:** chat only — the opening line (when held, only Step 0's HELD line), the vent
  ask when no vent was given, the echoed fragment split with Step 2's resume echoes
  (`already F<n>`, `F<n> parked → done`, `F<n> parked → routed`), at most one question
  round, the routing-web citation, the ledger table as written, each row's seed or parked
  question, and the Step 4 closing block.
- **Writes:** exactly one file, the intake ledger at the intake-engine §1 path — seeded only
  when absent, otherwise loaded and appended or updated per §4 and Step 2 (one writing
  session at a time). No other file, no seed files, no staging, no commit, no push.
- **Dispatches nothing:** besides that one write, the only commands the gateway runs are
  Step 0's read-only git-root and ledger resolution (intake-engine §1, §4); reading the
  composed contracts and the loaded ledger is not a dispatch. Every seed is paste-ready
  text for the window that will run it. The gateway invokes no rail skill, Workflow, Explore
  agent or sub-agent, never executes a seed, and never arms `/goal`.
- **Held:** no resolvable git root → no ledger and no seeds (Step 0).
- **Re-runs:** resumable on the same topic — the ledger on disk is the state (Step 2's
  load, append and parked-resolution rules). A pass interrupted before close leaves `open`
  rows that the zero-open check counts and the next pass closes.

---

## When to use / when NOT to use

**Use** when the operator opens the intake valve: "here's everything on my mind about X",
"this project doesn't feel right", "take my rough observations and make them concrete",
or an unstructured vent about a topic.

**Do NOT use:**

- **A single, already-clear fragment** → go straight to its rail (one broken thing →
  `/user-debug`; one capability wish → `/plan-feature`; …). The gateway earns its
  overhead only when fragments are plural or tangled.
- **Wanting IDEAS** ("what should I improve?") → `/goblin-suggest`. The gateway converts
  what was said; it does not generate what wasn't.
- **Refining ONE prompt or goal** → `/user-draft`.

---

## Steps

### Step 0 — take topic + vent

First resolve `<git-root>` exactly as intake-engine §1 requires — before asking for a
missing vent, so the operator never types a vent only to be held. If it does not resolve,
write nothing and stop with `user-gateway: HELD (no git root); ledger not written` plus the
next action (re-run from inside the target repository) — never a cwd-relative ledger.

Inputs: a **topic** and the **free-text vent**. Compute the topic slug per intake-engine
§1 (its cross-reference chain to shakedown-engine §1 owns the rule — never restate it).
No topic given → derive one from the vent's dominant subject and say so in the opening
line. **No vent given → ask for it.** That single ask is the skill's missing input, not
a block — the never-block rule (Step 1) governs refine questions, not the vent itself.

Then apply §4's load-before-derive check and end the opening line with `ledger: new` or
`ledger: loaded <file name>`, so a near-miss load is visible. After a load, the loaded
file's slug (its name without the `intake-` prefix and `.md`) is the topic slug for the
rest of the pass, so Step 4's path and `/goal` name the file actually written.

### Step 1 — listening pass (user-draft's discipline, cited)

Per user-draft Step 2: split the vent into its distinct fragments (echo the split so the
operator can correct it), find the gaps that would change a route or a seed, then ask
**3-5 targeted questions in ONE round max** — zero when the vent is already clear (say
so). **Never block:** when answers don't come, or only some do, proceed with what's there
and mark each assumption inline in the affected row/seed. No second round, ever.

Only ask questions that change the outcome: a repro-vs-distrust split, a constraint a
seed needs, which document a cruft-smell is about. Never ask for more work items — see
the pinned posture.

### Step 2 — one ledger row per fragment

Seed the ledger per intake-engine (path + slug: §1; load-before-derive idempotence: §4 —
an existing ledger for this topic is LOADED and appended, new rows continuing the `F<N>`
sequence). Every fragment from Step 1 becomes exactly one row (§2 grammar; one-line
disposition). On a loaded ledger, a fragment an existing row already captures IS that row:
echo it as `already F<n>` and add nothing. Earlier `routed` and `done` rows are never
rewritten (re-route notes belong to rail skills, §5). A `parked` row changes only when the
vent, or the operator's answer in the one question round, states the operator's own answer
to its question — and the kind of parked row decides the change (intake-engine §2 allows
both outcomes for an operator decision):

- **A decide-rail row** (route `decide`, its fragment itself an operator-only choice)
  resolves to `done` with the decision recorded in its disposition, echoed
  `F<n> parked → done`. Any work the operator voiced alongside that decision is its own
  fragment and row.
- **A row parked on a routing question** (a work fragment the gateway could not route, its
  disposition asking which rail or target it belongs to — see below) is never closed by
  the answer: it is routed on the rail that answer settles, per the routing web, its
  disposition gaining the seed pointer, echoed `F<n> parked → routed`, and Step 3 emits
  its seed with this pass's other routed rows.

When the row's kind is unclear, or the answer does not settle its question, the row stays
parked (`already F<n>`) and the one question round may ask. A pre-existing `open` row is
routed or parked in this pass like a new one.

Choose each row's route by CONSULTING the routing web — read its rails and entry
conditions, apply its tiebreak rule. Cite it in the output; do not reproduce its table.
Rows flip `open` → `routed` (or `parked`) as Step 3 emits or parks them; **no row stays
`open` at close** — a fragment the gateway cannot safely route parks with the routing
question stated (that is an operator-only call), never a "will route later" leftover.

### Step 3 — per-row ready-to-paste seed

Each routed row gets a seed the operator can paste unchanged; the gateway runs none of
them (Contract). Seed shapes by rail (this is the gateway's OUTPUT contract — which rail a
fragment belongs on stays the web's call):

- **bug** → one complete `/user-debug --symptom '<one-line symptom>'` line (plus the
  repro when one was voiced).
- **plan** → the FULL `/plan-feature` seed paragraph in the gateway output (problem +
  voiced constraints, scope strictly as voiced); the ledger disposition keeps only the
  one-line form (intake-engine §2 owns that rule — the ledger never holds paragraphs).
- **investigate** → external/multi-source: a deep-research charter for the receiving
  window to dispatch via `Workflow({name: "deep-research-pinned"})` — never the built-in
  name (CLAUDE.md's dispatch rule, echoed by the web); codebase-local: a scoped
  Explore-agent framing (what to sweep, what a finding looks like).
- **verify** → the applicable invocation among the verify rail's four modes —
  `/review-uat` / `/user-uat` / `/user-shakedown` / `/user-walkthrough` — chosen per the
  web's verify-rail detail section.
- **trim** → a `/plan-trim` invocation naming the plan document. (Cruft-smell that is
  NOT about a plan document is not trim's — the web's trim note routes it
  investigate-first.)
- **do** → the two-step pair matching the do rail's real mechanics: `1.` a
  `/goblin-suggest --small <project>` line (persists the atom — the voiced task text
  guides which atom to pick, or confirms it appears), then `2.` a
  `/goblin-do <matching atom id or fuzzy text>` line. `/goblin-do` resolves persisted
  atoms only — a bare `/goblin-do` on a freshly-voiced task fails to resolve.
- **draft** → a `/user-draft <the operator's rough thoughts>` line.
- **decide** → NOT a seed: the row parks with the open question stated verbatim in its
  disposition. Never answer it, never pick a side, never convert it into work — parked
  rows wait for the operator (intake-engine §2/§3 own parked semantics; deciding is the
  one thing the gateway must never do for them).

### Step 4 — closing block

Three elements, always:

1. **Ledger path** — absolute, per the intake-engine §1 formula (after a Step 0 load, the
   loaded file).
2. **The canonical `/goal` line** for this topic slug (after a Step 0 load, the loaded
   file's slug) — the string is defined ONCE in intake-engine §3; emit it exactly, never
   author a variant. (Arming it is the operator's choice.)
3. **QUICK COPY** — every routed row's seed, one paste-able line each (the plan rail's
   line invokes `/plan-feature` with a compact form, the full paragraph staying above;
   the do rail contributes its two-step pair as two lines). Parked rows are questions,
   not seeds — they appear above with their open question, never in QUICK COPY. On a
   loaded ledger, QUICK COPY holds only rows routed in this pass (a parked row this pass
   routed included); earlier `routed` rows and `already F<n>` echoes keep their seed
   pointer in the ledger and are not re-emitted.

---

## After the gateway

Rows may later re-route: a rail skill that discovers wrong-rail work mid-run follows the
web's re-route contract and writes back to this ledger per intake-engine §5. The gateway
plays no part in that — it ends at the closing block.

---

## Maintenance

The `evals/` suite targets THIS gateway contract (created 2026-07-13, plan Step 12 /
#313): **11 assertions** across **3 categories** in `evals/evals.json` (passing threshold
**9/11**), **4 scenarios** in `evals/test_scenarios.json` (two fresh-ledger vents, one
loaded-ledger resume, and one preflight matrix), and a golden corpus of **4 goods + 12
single-defect bads** under
`evals/golden/` (manifest.json maps each bad to the one assertion it trips). Any edit
that changes an output contract here (listening pass, ledger seeding, seed shapes,
closing block) must update the affected assertions and goldens in the same diff, keeping
this footer's numbers equal to `evals.json`'s. The rails + entry conditions + tiebreak +
re-route contract stay owned by `skill-pipeline.md`, and the ledger grammar + statuses +
zero-open check + canonical `/goal` stay owned by `intake-engine.md` — when either
changes, re-check the citation-consistency assertions here instead of duplicating the
contract.

These evaluation inputs are canonical only in the source repository at
`skills/user-gateway/evals/`; the distribution builder does not install them. An installed
evaluation route therefore requires an explicit `evals_dir` that points to this corpus. If
that input is absent, the evaluation route stops with its missing-input result; it must not
pretend the corpus shipped beside the installed skill. This source-only absence does not
disable ordinary `/user-gateway` runtime use, whose required runtime contracts are listed
under Provider-neutral host abstractions.
