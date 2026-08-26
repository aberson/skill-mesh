# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/citation-review/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# Citation review — evidence-check one LLM-facing artifact

Review ONE scanned LLM-facing artifact (a rule, a skill, a memory, a CLAUDE.md or AGENTS.md,
a plan) through the Citation Needed calibrated pipeline: extract each distinct decision, cite it,
classify it, score it, and render a breakdown. Invoke as
`/citation-review <workspace-relative-path> [--calibrate]`.

Run from the coding-root workspace. **The Citation Needed CLI is the only database writer** — this
skill never opens the database directly and never re-implements scoring, quote verification, or
classification logic that already lives behind the CLI.

```powershell
uv run --project citation-needed cite init-db
uv run --project citation-needed cite seed import
uv run --project citation-needed cite scan
```

**Never modify the reviewed artifact.** The only allowed outputs are Citation Needed database rows
and its rendered breakdown document. A review is a measurement, not an edit.

## `--calibrate`

Calibration is **mandatory before a real review** — an uncalibrated score is not evidence, it is a
number. This is the measurement-validity discipline the workspace already holds (calibrate a metric
against a known-good and a known-garbage anchor before trusting it).

1. Run `cite calibrate check`.
2. If it is not valid, run `cite calibrate open`, perform the two anchor reviews from its JSON
   context, and send **exactly one** UTF-8 JSON object to `cite calibrate commit` on standard input.
3. Read `citation-needed/docs/contracts/review-commit.schema.json` before constructing either
   payload. Construct against the schema, never against a remembered shape.

The real database must remain untouched by calibration. **Do not claim calibration passed without
the CLI's own PASS result** — the CLI's verdict is the fact; this skill's impression of it is not.

## Review one artifact

1. **Ensure the target was discovered by `cite scan`**, and address it by its workspace-relative
   forward-slash path. An artifact the scanner has not seen has no reviewable identity.
2. **Run `cite calibrate check`.** STOP on a fingerprint mismatch or a stale gate unless the
   operator explicitly authorized `--accept-aged`. A stale gate is a real finding, not a nuisance.
3. **Run `cite review open <path>`.** Read its JSON together with BOTH schemas under
   `citation-needed/docs/contracts/`. Reuse a supplied prior `choice_key` for the same decision so
   one decision keeps one durable identity across runs.
4. **Extract each distinct decision.** Search the corpus FIRST, then obtain external or internal
   evidence honestly. Record a real searched-but-not-found outcome rather than inventing a citation:
   a documented absence is a legitimate, valuable result; a fabricated citation is a defect.
5. **Commit the review.** Put the complete review-commit payload on **standard input** to
   `cite review commit --run <run_id>`. Do not put large JSON on argv. Do not supply fetched page
   text or an API echo — the CLI re-verifies those paths itself, and feeding it your copy would
   replace its verification with your assertion.
6. **Report.** Run `cite report <path>` and return the rendered breakdown location, the band, the
   citations, and any documented absence. **A failed commit means there is no review result** —
   report the failure, never a partial run dressed as a verdict.

## Constraints (do not relax)

- Never edit the reviewed artifact, and never present a proposal as an applied edit.
- Never duplicate scoring, quote-verification, or database logic in this skill; use the existing
  classification prompt and the committed contracts.
- Never invent a citation id, a corpus hit, or an external verification.
- Never report a band or a score that no committed run produced.

## Next step

To turn a committed review into cited trim or rewrite proposals, hand off to `/citation-distill
<path>`. To audit a whole project rather than one file, use `/citation-sweep <project-slug>`.
