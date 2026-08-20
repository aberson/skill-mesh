# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/citation-distill/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# Citation distill — cited trim/rewrite proposals for one artifact

Turn a **committed, calibration-valid** Citation Needed review into evidence-backed trim or rewrite
proposals for one LLM-facing artifact. Invoke as `/citation-distill <workspace-relative-path>`.

**This skill proposes changes only. It never edits the target artifact.** A proposal is not an
applied edit and must never be reported as one.

## Procedure

1. **Require real review evidence.** If there is no fresh committed review for the target, run
   `/citation-review <path>` first. Do **not** treat an open run, a mock, or an uncommitted payload
   as review evidence — an uncommitted run is a draft, not a fact.
2. **Generate the mechanical queue defaults** for the committed scores:

   ```powershell
   uv run --project citation-needed cite distill generate --run <run_id>
   ```

3. **Read `citation-needed/prompts/distill.v1.md` before drafting any optional refinement.** Every
   cut or rewrite must retain the cited evidence IDs, or the documented searched-but-not-found
   record. A proposal that drops its evidence basis is not a distillation, it is an opinion.
4. **Send any refinement as JSON on standard input:**

   ```powershell
   uv run --project citation-needed cite distill propose --run <run_id>
   ```

   Send the complete JSON proposal on stdin. **Never place a large payload on argv, and never invent
   a citation id.**
5. **Report.** Run `cite queue list` and return the proposal IDs, their ranks, the evidence basis for
   each, and the explicit statement that an operator must choose keep, cut, or rewrite through
   `/citation-triage`.

## Constraints (do not relax)

- Do not change review scores, classifications, citations, or source files.
- Do not report a proposal as an applied edit, and do not apply one.
- Do not fabricate a citation id or an evidence basis; a documented absence is the honest result.
- Do not proceed from an open or mocked run — only a committed, calibration-valid review qualifies.

## Next step

The operator decides each proposal through `/citation-triage [--project <slug>]`. Accepted work is
handed to an existing editing workflow; the queue record stays as the evidence trail.
