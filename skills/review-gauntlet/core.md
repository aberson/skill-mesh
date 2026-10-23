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
3. Mechanical checks run before model judgment; a mechanical failure is itself a verdict and cannot be waived; ground-truth is cross-checked.
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
`--reviewers code` set) under review-deep's evidence and dedup rules, but in a
**LEAN configuration**: positional args instead of named flags, its own fixed
deterministic verdict ladder (§ Aggregation and output), and a terse
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

**No sidecar, no persisted review output.** Unlike review-deep (which writes a JSON audit-trail sidecar to
`.review-deep/<timestamp>.json` by default), review-gauntlet writes **NO sidecar
and NO persisted review output**. Its only output is the terse markdown verdict below,
printed to stdout. Mechanical-check output and any per-lens detail files exist
only in one ephemeral run directory created outside the repository and the
working directory and deleted before the run ends (§ Mechanical checks).
review-gauntlet itself writes no review output (sidecar, lint file or lens detail
file) into the repository. The project's own lint and test commands can still
create caches or bytecode there: § Mechanical checks redirects them into the
ephemeral directory where the tool allows it, and reports every repository path
that is new or whose status line changed between a snapshot taken before the
checks and one taken after them. A content change to a path that was already
modified, untracked or ignored before the checks is not detectable, so the report
never claims the repository is unchanged. This is the lean contract — a fast gate, not an archived
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
the Style lens is the only code lens cheap enough to route to a local model, and it
is **off unless switchboard offload is enabled** for this profile's site,
`review-gauntlet-style` (`python -m switchboard judge --site review-gauntlet-style ...`).
A local **verdict** is an advisory annotation only: it never fills the Style lens
slot. On a verdict and on a `defer` (the default) alike, a fresh-context Style
reviewer invocation runs on the Style lens's configured tier, and its verdict is the
gating Style lens verdict, so the offload never changes the gate. The historical
`review-gauntlet-style` task_class remains a valid switchboard config slice
(tier-offload; Switchboard Decision 9) — it is the lean profile's name for the
same offload review-deep documents as `review-deep-style`. Either slice routes
ONLY the advisory Style judgment; the four deep-reasoning lenses (Correctness,
Bugs, Security, Test-quality) ALWAYS spawn fresh-context reviewer invocations.
Resolve their tiers through `config/model-tier-map.json`. The local
model never sets the gate (Decision 3).

### Mechanical checks

Before dispatching any lens, the review parent runs the mechanical checks
(invariant 3) and keeps their output out of the repository:

1. Create one ephemeral run directory with the platform temp-directory primitive,
   outside the repository and the working directory. Delete it before the run
   ends, on every exit path.
2. Before any check runs, take the before-snapshot: from the project root, run
   `git status --porcelain -uall --ignored` with its output redirected to
   `<ephemeral>/status-before.txt`. Never read a snapshot into the session. If
   the project root is not a git working tree, skip both snapshots and say so on
   the `Mechanical checks:` report line.
3. Run review-deep's `scripts/lint_prepass.sh` from the review-deep package
   installed beside this one, from the project root, with `--output-dir` set to
   the ephemeral run directory and `--diff-paths` set to the diff's files. If that
   package or script is absent, return `required_tool_missing`. Run the project's
   test suite where applicable. Point each check's side effects into the
   ephemeral run directory where the tool allows it: set
   `PYTHONDONTWRITEBYTECODE=1` (or `PYTHONPYCACHEPREFIX=<ephemeral>/pycache`),
   run pytest with `-p no:cacheprovider` (or `-o cache_dir=<ephemeral>/pytest`),
   and set `RUFF_CACHE_DIR=<ephemeral>/ruff` and `MYPY_CACHE_DIR=<ephemeral>/mypy`
   for the lint pre-pass; use the equivalent setting for any other tool the
   project's checks run. A tool with no such setting may still write into the
   repository; step 6 reports such a write when it creates a path or changes a
   path's status line, and cannot detect a content change to a path that was
   already modified, untracked or ignored before the checks.
4. Record each check as `pass`, `fail` or `missing-tool`. A check that ran and
   failed (type-check errors, failing tests, blocker-class lint) is `fail`;
   style-class lint keeps review-deep's FYI rule. An absent tool is `MISSING-TOOL`:
   warn, skip only that check and list it; it does not block.
5. Every lens prompt names the ephemeral `lint-findings.json` path explicitly, in
   place of review-deep's `<--output-dir>` default. No lens and no parent step loads
   `.review-deep/lint-findings.json` or a lint file from an earlier run.
6. After the last check, take the after-snapshot the same way into
   `<ephemeral>/status-after.txt` and compare the two files mechanically (for
   example `diff`, or `comm -3` over sorted copies of the two files), so that only
   the changed lines enter the report. Every path that is new in the after-snapshot,
   or whose status line changed between the snapshots, is a residual side effect of
   the checks: list each one on the `Mechanical checks:` report line. Do not delete
   or hide it. A content change to a path that was already modified, untracked or
   ignored before the checks leaves its status line unchanged, so it is not
   detectable; when no line changed, the field reads `none detected`.

A mechanical `fail` is itself a verdict: it feeds the ladder below and cannot be
waived. A lens sub-agent that writes longer detail to a file (the workspace
subagent-economy rule) writes it only inside the ephemeral run directory and
returns its path. The parent reads all five lens results before applying the
ladder and never merges them first.

---

## Aggregation and output (lean)

review-gauntlet applies review-deep's evidence and dedup rules from its
[Aggregation](../review-deep/core.md#aggregation) section (evidence-free findings
dropped, severity dominance, lens-owns-dimension, absence and lint dedup) to the
five code lenses' findings. **The fixed ladder below is review-gauntlet's only
verdict authority:** it does not run review-deep's reducer script and writes no
sidecar. The ladder is a pure rule over the five lens verdicts and the mechanical
results; it does not spawn a model.

Final verdict aggregation is deterministic: it is a pure function of the lens verdict set
and the mechanical results. No LLM judgment is applied at aggregation time. This is invariant 5 and is non-relaxable.
Apply this fixed precedence (default-deny, aligned with review-deep's ladder):

1. **NEEDS-WORK** if any lens returns `NEEDS-WORK`, `FAILED` or `NO-EVIDENCE`; if
   the lens results are not exactly Correctness, Bugs, Security, Test quality and
   Style, each once (a missing, duplicated, extra or malformed result, or a verdict
   outside `PASS` / `NEEDS-WORK` / `UNCERTAIN` / `FAILED` / `NO-EVIDENCE`, including
   `SKIPPED`); or if any mechanical check failed.
2. **UNCERTAIN** if any lens returns `UNCERTAIN` and rule 1 does not apply. It
   escalates to the operator; it never becomes PASS.
3. **PASS** only if exactly the five lenses each return `PASS` and no mechanical
   check failed. Anything else is not PASS.

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

Mechanical checks: <check>: pass | fail | missing-tool; ... (or "none applicable"); residual repository paths (new or status-changed): <path>, ... | none detected

**Verdict: PASS / NEEDS-WORK / UNCERTAIN**

Judgment: self-review evidence (advisory) — applied by the invoking session, not an independent final judgment.
```

Each finding renders in review-deep's evidence shape (`file:line` + excerpt +
reasoning). The five code-lens verdict lines (`Correctness verdict: …`, etc.)
are review-deep's, verbatim.

**Verdict logic:** normalize review-deep's evidence/severity outcomes into each
lens verdict, then apply the fixed reducer above. `NO-EVIDENCE` and `FAILED`
normalize to `NEEDS-WORK` (review-deep rules 4 and 5); an evidence-backed `Block`
or `Nit` normalizes to `NEEDS-WORK`.
There is no `DEFERRED-TO-UAT`, since runtime/auth-gate deferral is a
review-deep-only path.

**Judgment line (always printed).** The ladder is applied by the invoking session,
which is often the session that produced the diff. Until an independent final judge
is defined for this profile, every verdict is self-review evidence: advisory, and not
an independent final judgment. The same holds for a re-review of a fix made after the
offer below. Never present a gauntlet verdict as an independent review.

If NEEDS-WORK, end with: "Want me to fix these issues, or discuss any findings first?"

---

## What NOT to do

- Do not re-define the reviewer prompts here — defer to review-deep's lens
  definitions (re-defining them is exactly the duplication this profile removes).
- Do not write a JSON sidecar or any other review output into the repository — the
  lean contract is a terse stdout verdict; mechanical output and lens detail files
  live only in the ephemeral run directory. Do not claim the run left the
  repository unchanged: report the residual paths the before/after snapshot found.
  Use `review-deep` when you want the audit trail.
- Do not pass `--plan-step` or runtime flags — those are review-deep's lane.
- Do not let the local Style offload set the verdict or fill the Style slot — it is
  advisory; the deterministic aggregation ladder is the gate.
- Do not merge the five lens results before the ladder, and do not load a lint file
  from an earlier run.

---

## Cross-references

- [`review-deep/SKILL.md`](../review-deep/core.md) — the engine this profile runs
  on (lens definitions, anti-pattern catalog, aggregation rules, severity rubric)
- [`_shared/judge-core.md`](../../_shared/judge-core.md) — the judging doctrine both
  skills inherit
- [`review-proof/SKILL.md`](../review-proof/core.md) — primary-source verification discipline
- `dev/.claude/rules/code-quality.md` — anti-pattern catalog source
