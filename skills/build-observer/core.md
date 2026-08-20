# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/build-observer/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# build-observer — propose one `[project.portfolio]` registry block

Scaffolds the `[project.portfolio]` block for one project (dev-observatory portfolio-pages plan,
`dev-observatory/plans/portfolio-pages-plan.md` §5a / §5e / Step 27). Invoke as
`/build-observer <slug>`.

The **CREATIVE** work — wording the blurb, choosing proofs, naming a demo — is done here in prose,
from primary sources. The **MECHANICAL** work — verb-name validation, relates-slug validation,
length/count caps, TOML rendering — is delegated to `scaffold_portfolio.py` in this skill's asset
directory, which **imports `dev_observatory`'s own constants and renderer rather than re-declaring
any of them** (`code-quality.md` § one source of truth for data-shape constants; never duplicate
`registry.py`'s validation).

Run bare: `/build-observer <slug>`. No flags are required and **nothing prompts mid-run** — the skill
reads, drafts, validates, and prints a proposal plus a redline report every time. It never writes
into `registry.toml` or `snapshot.json` itself (see **Write mode**).

## Steps

### 1. Locate the project

Resolve the slug's path and existing registry fields (`category`, current `launch`/`launches`,
whether a `[project.portfolio]` block already exists) by reading
`.claude/observatory/registry.toml` directly, or via:

```powershell
uv run --project dev-observatory python -c "from pathlib import Path; from dev_observatory import registry; e = registry.load_registry(Path('.claude/observatory/registry.toml')).get('<slug>'); print(e)"
```

Simplest in practice: just read the relevant `[[project]]` table with the host's file-read
primitive — the registry is a small committed file. If the slug has no registry entry at all, say
so and continue anyway (the script still renders a valid snippet; it just has nowhere to be pasted
yet).

### 2. Read the derived verbs

Read `.claude/observatory/snapshot.json` and find this slug's `projects[*]` entry — its
`verbs[*].verb` names are what showcase/highlights must resolve against.

**Note:** the checked-in snapshot may be a stale `snapshot_version` relative to the current code
(new derivers land ahead of a re-scan); that is fine — `scaffold_portfolio.py` falls back to a raw
JSON read of the same `verbs` shape and says so. **This skill never runs `observatory scan`/`status`
itself** — that would refresh (i.e. WRITE) the on-disk snapshot cache, which is outside a
proposal-only skill's job.

### 3. Read the project's own documentation

In order of preference, read whichever exist: `README.md`, `CLAUDE.md`, `plans/plan.md` (or
`docs/*-plan.md`). Pull out, verbatim or close to it:

- the one- or two-sentence **mission** (for the blurb / card);
- **documented guarantees or invariants** — a "Design decisions" section, a bulleted list of hard
  rules, a schema table's "Rule" column — for `proofs`. **Never invent a guarantee the docs don't
  state.**
- any **named mention of a sibling registry project** (e.g. "External consumers such as Find
  Again... read records only through the format contract") — that sentence is a legitimate,
  grounded `relates` clause. **Never invent a relationship between two projects that isn't written
  down somewhere.**
- **CLI usage / commands** that suggest which verb best demonstrates the tool — candidate
  `showcase`/`highlights` picks (validated in Step 5; a good guess that isn't a real verb yet still
  gets reported, per Step 6).

### 4. Draft the field values (house voice)

- **`blurb`** — at most 140 chars, a noun-phrase pitch, no leading article, present tense implied.
  Example house voice (plan §5a): *"Immutable Markdown decision records with validated
  supersession"*. Fallback if nothing confident emerges: leave it unset — render falls back to the
  derived plan goal.
- **`card`** — only draft this for a flagship project's fuller card copy; omit for
  utility/fun/professional/third-party entries (plan §5a: "site flagship cards only").
- **`tag`** — one word from the palette in plan §5a (Safety, Decisions, Verification, Coordination,
  Retrieval, Consistency, Measurement, Hygiene, Rigor, Management, Benchmarking, Aesthetics,
  Routing, ...) or coin a new one-word chip if none fits; fall back to the group label.
- **`proofs`** — up to 3, each a short guarantee noun-phrase, each traceable to a specific line you
  just read.
- **`showcase`** — the ONE verb name that best answers "watch this work". Prefer an already-derived,
  non-`status` verb. If the ideal demo command doesn't exist as a derived verb yet, still name it —
  the validator will drop it and the redline report will tell you exactly what `[project.launch]`
  entry would need to be added to realize it.
- **`highlights`** — up to 3 more verb names, same reasoning.
- **`relates`** — up to 4 `"slug: clause"` pairs, only for documented relationships (Step 3).
- **`repo_public` / `public`** — leave both unset (default false) **UNLESS** the operator's
  instruction explicitly named this project as display-listed. If it did, pass
  `--public --public-reason "<quote the instruction>"` in Step 5 — the script hard-refuses
  `--public` without a reason string, and this skill's prose never fabricates one.
- **`live_url` / `contribution`** — only when the docs state a deployed URL or (third-party rows
  only) an operator contribution.

### 5. Validate + render

```powershell
uv run --project dev-observatory python .claude/skills/build-observer/scaffold_portfolio.py <slug> `
  --blurb "..." --tag "..." `
  --proof "..." --proof "..." `
  --showcase "<verb-name>" --highlight "<verb-name>" `
  --relates "sibling-slug: clause" `
  --card "..." --live-url "https://..." --contribution "..." `
  --repo-public --public --public-reason "..."
```

Omit any flag whose field you have nothing confident to say (no `--card` for non-flagship projects,
no `--public*` unless told, etc.). The script prints:

- **stderr** — one line per field: `KEPT` (with what was validated against), `DROPPED` (with the
  exact mechanical reason — bad length/charset, unknown verb name, dead relates slug, self-relate,
  not-yet-derived showcase), or `OMITTED`. **This IS the redline report — relay it close to
  verbatim.**
- **stdout** — the `[project.portfolio]` TOML snippet, ready to paste under the project's existing
  `[[project]]` entry in `registry.toml`. Empty (with a stderr note) if nothing survived validation.

### 6. Report

Return, in order:

1. the printed TOML snippet;
2. the `KEPT`/`DROPPED`/`OMITTED` lines verbatim, so the operator sees confident-vs-guessed at a
   glance;
3. any explicit "add a `[project.launch]` entry for X" follow-ups the validator surfaced;
4. a one-line reminder that **nothing was written** — the operator (or Step 28's authoring pass)
   pastes the block manually.

## Write mode

Plan §5e allows either "into the project's registry entry, or emit it for the operator to paste" —
**this skill implements only the latter.** Concretely: `/build-observer <slug>` PROPOSES a block and
PRINTS it (stdout: the TOML snippet; stderr: the redline report). It is **read-only** against both
`registry.toml` and `snapshot.json` — `scaffold_portfolio.py` never opens either for writing, never
calls `registry.upsert_entry`, and never runs `observatory scan`/`status` (which would refresh the
snapshot cache on disk). Two things always stay separate, deliberate, human actions performed AFTER
this skill returns:

1. **Pasting the block** into `registry.toml` under the project's existing `[[project]]` entry.
2. **Setting `public = true` / `repo_public = true`** for real — this skill only ever *proposes*
   those fields when explicitly told to (see **Constraints**); it never applies them to the file
   either way.

Direct-write-into-the-registry tooling belongs to the plan's Step 28 (authoring all the real
blocks). If that step wants it, it can compose `registry.load_registry` + `registry.upsert_entry`
(both already exist and already handle the atomic-write + round-trip contract) around this script's
validated `Portfolio` object; duplicating that logic here would violate the same one-source-of-truth
rule this script exists to uphold.

## Constraints (do not relax)

- **Never invents stats.** `tests`, `last_commit_days`, `commits_30d`, `gap`, and the plan-derived
  goal are DERIVED by dev-observatory at scan time — this skill never writes a stats-shaped field
  into `[project.portfolio]` (there isn't one; the schema in plan §5a has none).
- **Never sets `public = true`** without an explicit, quoted instruction that the project is
  display-listed — mechanically enforced by `scaffold_portfolio.py --public` requiring
  `--public-reason`.
- **Never promotes `status`** into `showcase`/`highlights` — mechanically dropped by the validator
  regardless of what is passed in.
- **Never invents a `relates` clause** — only pairs traceable to a sentence actually read in Step 3,
  and only slugs that exist in the registry (dead slugs are dropped with a loud reason, mirroring
  `registry._drop_dead_relates`).
- **Never edits `registry.toml` or `snapshot.json`.** Propose, validate, print. Autonomous
  end-to-end (no confirmation prompts) precisely because it never mutates anything.

## Reference

- Block schema + parse-time validation: `dev-observatory/src/dev_observatory/registry.py`
  `_parse_portfolio` / `_drop_dead_relates` / `_portfolio_to_table`.
- Verb derivation: `dev-observatory/src/dev_observatory/verbs.py` `derive_verbs`, `is_button_verb`.
- Showcase fallback ladder (render-time; informs what makes a good `showcase` pick):
  `dev-observatory/src/dev_observatory/arc.py` `resolve_showcase_verb`, `resolve_highlights`.
- Dataclass: `dev-observatory/src/dev_observatory/model.py` `Portfolio`.
- Worked example against a thin utility (`paper-trail`) and a flagship (`void_furnace`), including
  the validator catching an invalid showcase guess: `sample-dry-run.md` in this skill's asset
  directory.
- Registry facts (`owned`, ports, verb schema) are governed by `descriptor-contract.md`; an
  unregistered project is write-blocked by default.
