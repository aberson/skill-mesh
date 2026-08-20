# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/citation-triage/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# Citation triage — record operator decisions on the distill queue

Walk Citation Needed's ranked distill queue **with the operator** and record keep, cut, or rewrite
decisions. Invoke as `/citation-triage [--project <slug>]`.

This skill changes **no source artifact**. It records decisions; it does not apply them.

## Present the queue

```powershell
uv run --project citation-needed cite queue list
```

Add `--project <slug>` when a project scope was supplied. Present each open proposal with:

- its **target**,
- its **rank**,
- its **proposed action**,
- its **supporting citation IDs**, and
- any **documented search absence**.

Treat the list as decision support, **not** as a command to edit anything. Rank orders the queue; it
does not decide it.

## Record each decision

For each operator decision, invoke **exactly one** of:

```powershell
uv run --project citation-needed cite queue resolve <id> --keep
uv run --project citation-needed cite queue resolve <id> --cut
uv run --project citation-needed cite queue resolve <id> --rewrite
```

Pass `--by <operator>` when the operator identity is supplied.

- `--keep` records a **rejected** proposal.
- `--cut` and `--rewrite` record **accepted** proposals.

Neither state edits or applies the target. Hand accepted work to the appropriate existing editing
workflow and retain the queue record as evidence.

## Constraints (do not relax)

- **Never infer an operator decision** from rank, from model output, or from a citation alone. The
  decision is the operator's; this skill is the recorder.
- On cancel, **write nothing** — no partial resolution, no placeholder row.
- Never edit, apply, or stage a change to a target artifact from this skill.
