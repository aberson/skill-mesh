# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/citation-sweep/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# Citation sweep — a bounded project-wide rigor pass

Run a **bounded** project-wide Citation Needed rigor pass: discover the project's LLM-facing
artifacts, cluster near-duplicate decisions, review the artifacts with terse per-artifact returns,
and produce a citation-backed distill backlog. Invoke as `/citation-sweep <project-slug>`.

Sweep an owned project **without editing any target**. The only allowed writes are Citation Needed
database rows and its breakdown/queue artifacts.

## Procedure

1. **Verify calibration, then scan.**

   ```powershell
   uv run --project citation-needed cite calibrate check
   uv run --project citation-needed cite scan --project <project-slug>
   ```

   STOP if calibration is invalid. An uncalibrated sweep produces numbers, not evidence.
2. **Use the discovered workspace-relative artifact paths only.** Before fanning out, **cluster
   decisions that are genuinely near-duplicate**, so equivalent claims do not receive independent
   citation searches or duplicate durable keys. Clustering is what keeps the sweep bounded.
3. **Launch bounded per-artifact review work** using the `/citation-review` contract — one isolated
   fresh-context worker per artifact. Each worker MUST return only:

   - path,
   - run id,
   - band,
   - number of choices,
   - citation/absence summary, and
   - blocker (if any).

   A worker must **never** edit the artifact and must **never** silently pass an unavailable review.
   The terse return is deliberate: the sweep holds conclusions, not transcripts.
4. **Build the backlog.** For each committed run, invoke `cite distill generate --run <run_id>`.
   Aggregate with `cite queue list --project <project-slug>`, preserving which results are
   evidence-backed, internal-only, or documented no-literature-found. Those three are different
   epistemic states and must not be collapsed into one.
5. **Report** scope, clusters, completed and blocked reviews, queue rows, and any producer/API
   failure. Hand target edits to the operator via `/citation-triage` or an existing editing skill.

## Constraints (do not relax)

- Do not fabricate a corpus hit, an external verification, a calibrated verdict, or a completed
  review. **Stop rather than substituting a synthetic sweep for the required live evidence.**
- Do not edit any target artifact, in any rail.
- Do not report a blocked review as completed, or an unavailable review as a pass.
- Keep per-worker returns terse and file-backed; a sweep that inlines every review body defeats its
  own bound.
