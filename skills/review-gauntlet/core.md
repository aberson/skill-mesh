# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/review-gauntlet/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

## Non-relaxable review invariants

These invariants from [`judge-core.md`](../../_shared/judge-core.md) apply identically on every provider and cannot be relaxed:

1. The producer never grades itself; review lenses run in independent context.
2. Every finding and verdict cites concrete artifact evidence; evidence-free findings are dropped, never counted.
3. Mechanical checks run before model judgment and ground-truth is cross-checked.
4. Low confidence abstains or escalates; it never becomes PASS.
5. Aggregation is deterministic for identical normalized lens outputs, including fixed deduplication and tie/escalation rules.
6. Weak/local model judgments are advisory only and cannot gate.

# Review Gauntlet

> **Judging doctrine:** the producer-grader split, evidence-on-every-verdict,
> deterministic-aggregation, and primary-owner dedup rules this profile runs on
> live in [`_shared/judge-core.md`](../../_shared/judge-core.md). review-gauntlet
> does not re-implement them — it inherits them through review-deep's engine
> (review-deep is one of judge-core's reference implementations, §10).

review-gauntlet is a **thin profile over [`review-deep`](../review-deep/core.md)** —
not a separate review engine. It runs review-deep's **code lenses** (the
`--reviewers code` set) with review-deep's deterministic aggregation, but in a
**LEAN configuration**: positional args instead of named flags, and a terse
PASS / NEEDS-WORK report instead of review-deep's JSON audit-trail sidecar.

It exists so the common case — "review this diff, fast, give me a verdict" — has
a one-line invocation with no sidecar bookkeeping, while the heavy case
(high-stakes substrate / schema / key-shape diffs that want the full audit
trail, plan-conformance, runtime lenses, or `--prior-sidecar` persistent-
disagreement tracking) reaches for `review-deep` directly.

**review-gauntlet does NOT define its own reviewer prompts.** The lens
definitions, severity rubric, anti-pattern catalog, evidence discipline, and
aggregation rules are review-deep's — review-gauntlet points at them so the two
never drift as a duplicate pair. If you need to change how a lens reasons, edit
review-deep; the change flows through here automatically.

---

## Invocation contract

```
/review-gauntlet <prompt> <diff>
```

**Positional args (this is review-gauntlet's contract — NOT review-deep's named
`--prompt` / `--diff`):**

1. **`<prompt>`** — the developer's intent (what the diff is supposed to accomplish).
2. **`<diff>`** — the code diff to review. Same three accepted forms as review-deep:
   - A `git diff` output (staged, unstaged, or between commits)
   - A PR number (the skill fetches the diff via `gh pr diff <NUMBER>`)
   - An explicit paste of the changed code

If the invoker doesn't supply both a prompt and a diff, ask for them before
proceeding.

**No sidecar.** Unlike review-deep (which writes a JSON audit-trail sidecar to
`.review-deep/<timestamp>.json` by default), review-gauntlet writes **NO sidecar
and NO output file**. Its only output is the terse markdown verdict below,
printed to stdout. This is the lean contract — a fast gate, not an archived
audit trail. If you want the audit trail, run `review-deep` instead.

---

## What runs: review-deep's code lenses, lean

review-gauntlet maps to exactly this review-deep configuration:

| review-deep arg | review-gauntlet value | Why |
|---|---|---|
| `--prompt` | positional `<prompt>` | lean positional contract |
| `--diff` | positional `<diff>` | lean positional contract |
| `--reviewers` | `code` (the code-lens lane) | gauntlet is a static code gate |
| `--plan-step` | *(never passed)* | plan-conformance is review-deep's job; gauntlet's lens set is the 5 always-on code lenses |
| `--output-dir` / sidecar | *(suppressed)* | LEAN: no JSON sidecar written |

So an operator running `/review-gauntlet <prompt> <diff>` gets review-deep's
**five always-on code lenses** with deterministic aggregation — dispatched with
one fresh-context reviewer invocation for each lens. Resolve each capability tier
through `config/model-tier-map.json`; arms never inherit an escalated
session:

1. **Correctness** — diff vs stated intent
2. **Bugs** — defects in the diff itself
3. **Security** — adversarial-input / secrets / unsafe-config defects (a free
   upgrade over the historical four-pass gauntlet, which had no Security lens)
4. **Test quality** — focus, trim, missing critical coverage
5. **Style and conventions** — surrounding-code conformance

The sixth review-deep lens, **plan-conformance**, only runs when `--plan-step`
is supplied; review-gauntlet never passes it, so plan-conformance reports
`SKIPPED` and does not affect the verdict (use `review-deep --plan-step ...` when
you want it). Runtime lenses (`--reviewers runtime|full`) are likewise out of
scope for the lean gate — reach for `review-deep` when a diff needs them.

**Lens definitions are review-deep's, verbatim.** Read review-deep's SKILL.md
for the authoritative per-lens Scope / Coverage / Non-coverage / evidence-shape /
severity-rubric / verdict-threshold sub-sections:

- [Correctness lens](../review-deep/core.md#correctness-lens)
- [Bugs lens](../review-deep/core.md#bugs-lens)
- [Security lens](../review-deep/core.md#security-lens)
- [Test quality lens](../review-deep/core.md#test-quality-lens)
- [Style and conventions lens](../review-deep/core.md#style-and-conventions-lens)

The **anti-pattern catalog** (silent-wiring, producer-consumer-drift,
codifying-test-diff, silent-fallthrough-in-loop, silent-fallthrough-in-hot-path,
duplicate-shape-constants, create-table-without-migration), the **universal
evidence discipline** (every finding cites `file:line` + excerpt + reasoning),
the **`Block | Nit | FYI` severity rubric**, and the **cross-section dedup /
lens-owns-dimension** rules all live in review-deep's
[Anti-pattern catalog](../review-deep/core.md#anti-pattern-catalog) and
[Aggregation](../review-deep/core.md#aggregation) sections. review-gauntlet runs
them unchanged — it does not restate or fork them.

> **Lineage note.** review-deep's anti-pattern catalog cites this skill as the
> origin of its first three anti-patterns (silent-fallthrough-in-loop,
> duplicate-shape-constants, create-table-without-migration came from the
> historical review-gauntlet Bug Reviewer). Those definitions now live in
> review-deep as the single source of truth; review-gauntlet defers to them.

### Style-lens offload (switchboard, INERT BY DEFAULT)

review-gauntlet inherits review-deep's
[Style-lens local-judge offload](../review-deep/core.md#style-and-conventions-lens):
the Style lens is the only code lens cheap enough to route to a local model, it
is **off unless switchboard offload is enabled**, and on a `defer` (the default)
it falls back to a fresh-context Style reviewer invocation with no behavior change. The historical
`review-gauntlet-style` task_class remains a valid switchboard config slice
(tier-offload; Switchboard Decision 9) — it is the lean profile's name for the
same offload review-deep documents as `review-deep-style`. Either slice routes
ONLY the advisory Style judgment; the four deep-reasoning lenses (Correctness,
Bugs, Security, Test-quality) ALWAYS spawn fresh-context reviewer invocations.
Resolve their tiers through `config/model-tier-map.json`. The local
model never sets the gate (Decision 3).

---

## Aggregation and output (lean)

review-gauntlet uses review-deep's
[deterministic aggregation](../review-deep/core.md#aggregation) over the five
code lenses' verdicts — the same severity-dominance, lens-owns-dimension,
NO-EVIDENCE-handling, and absence/lint dedup rules. The aggregation step is a pure
reducer over normalized lens outputs; it does not spawn a model.

Final verdict aggregation is deterministic: it is a pure function of the lens verdict set.
No LLM judgment is applied at aggregation time. This is invariant 5 and is non-relaxable.
Apply this fixed precedence:

1. **NEEDS-WORK** if any lens returns `NEEDS-WORK`.
2. **UNCERTAIN** if any lens returns `UNCERTAIN` and no lens contradicts it with an
   evidence-backed `NEEDS-WORK`.
3. **PASS** only if all lenses return `PASS`.

The **difference from review-deep is output only** — review-gauntlet emits a
terse report and **no JSON sidecar**:

```
## Review Gauntlet Results

### Correctness
<findings or "Correctness verdict: PASS">

### Bugs
<findings or "Bugs verdict: PASS">

### Security
<findings or "Security verdict: PASS">

### Test Quality
<per-test verdicts or "Test quality verdict: PASS">

### Style & Conventions
<findings or "Style verdict: PASS">

---

**Verdict: PASS / NEEDS-WORK / UNCERTAIN**
```

Each finding renders in review-deep's evidence shape (`file:line` + excerpt +
reasoning). The five code-lens verdict lines (`Correctness verdict: …`, etc.)
are review-deep's, verbatim.

**Verdict logic:** normalize review-deep's evidence/severity outcomes into each
lens verdict, then apply the fixed reducer above. `NO-EVIDENCE` normalizes to
`UNCERTAIN`; an evidence-backed `Block` or `Nit` normalizes to `NEEDS-WORK`.
There is no `DEFERRED-TO-UAT`, since runtime/auth-gate deferral is a
review-deep-only path.

If NEEDS-WORK, end with: "Want me to fix these issues, or discuss any findings first?"

---

## What NOT to do

- Do not re-define the reviewer prompts here — defer to review-deep's lens
  definitions (re-defining them is exactly the duplication this profile removes).
- Do not write a JSON sidecar or any output file — the lean contract is a terse
  stdout verdict. Use `review-deep` when you want the audit trail.
- Do not pass `--plan-step` or runtime flags — those are review-deep's lane.
- Do not let the local Style offload set the verdict — it is advisory; the
  deterministic aggregation reducer is the gate.

---

## Cross-references

- [`review-deep/SKILL.md`](../review-deep/core.md) — the engine this profile runs
  on (lens definitions, anti-pattern catalog, aggregation rules, severity rubric)
- [`_shared/judge-core.md`](../../_shared/judge-core.md) — the judging doctrine both
  skills inherit
- [`review-proof/SKILL.md`](../review-proof/core.md) — primary-source verification discipline
- `dev/.claude/rules/code-quality.md` — anti-pattern catalog source
