# Skill role taxonomy and isolated classification protocol

> **Vendored shared payload.** Installed profiles carry this file under their discovery root's
> `_shared` directory. Provider adapters bind host primitives; this document defines no
> provider command, model ID, or discovery-root name.

This is the direction-neutral source of truth used by `tier-escalate` and `tier-offload`.
It defines the role tags, complete-package discovery, fresh-context classification protocol,
and base output. It deliberately defines no up-tier or down-tier verdict.

## 1. Role taxonomy

Tag every role that performs or replaces LLM work with exactly one tag. Include `MECH` so
mechanical work is classified rather than silently omitted.

| Tag | Role definition | Character |
|---|---|---|
| `ORCH` | Drives a multi-step pipeline or dispatches tasks | Stateful coordinating spine |
| `AUTHOR` | Writes code, prose, plans, or other deliverable content | Produces rather than scores |
| `PLAN` | Makes architecture or sequencing decisions | Open-ended design judgment |
| `JUDGES` | A genuine parallel array of independent scorers | Individually low-stakes scoring arms |
| `GATE` | The final or consolidating correctness-critical decision | Controls merge, ship, keep, or reject |
| `MECH` | Exit code, schema, regex, hash, or other deterministic check | No LLM judgment required |
| `SOLO` | One reasoning pass that is not a parallel scoring array | One call, one context |

Tag boundaries:

- A fan-out whose arms produce content is `AUTHOR`, not `JUDGES`.
- A checklist executed by one model pass is `SOLO`, not `JUDGES`.
- A consolidating decision over a `JUDGES` array is a separate `GATE` role.
- Tool use does not change a role tag. Direction-specific consumers decide whether tool needs
  affect routing.

## 2. Discover complete behavior packages

The provider adapter supplies an absolute `discovery_root`. An explicit operator skills
directory may replace it. Never hard-code `.claude/skills`, `.agents/skills`, or
`.github/skills` in the shared protocol.

1. Match `<skills-dir>/*/SKILL.md`; skip directories without an entrypoint.
2. List the matched entrypoint paths before constructing any classifier prompt.
3. Read each entrypoint and resolve every local Markdown link that defines required behavior,
   including an installed `core.md` and provider-specific behavior when present. Keep resolved
   bodies inside the discovery root.
4. Record the entrypoint and required behavior-body paths in the input inventory.
5. A missing, unreadable, or root-escaping required body is `required_skill_body_missing`.
   Do not classify that package from launcher prose, frontmatter, description, or memory.

A generated `SKILL.md` may be only an entrypoint. Reading it without the linked core is not a
complete classification.

## 3. Fresh isolated classification

The provider adapter supplies `isolated_readonly_task` and the capability corresponding to
the workspace's ordinary fan-out tier. These are runtime host capabilities, not provider-wide
assumptions.

1. Batch roughly 6-8 packages per classifier, bounded by available host slots.
2. Launch each classifier with fresh context, no producer history, and read-only access.
3. Dispatch independent classifiers concurrently where capacity permits. Smaller batches may
   run sequentially as slots free, but no classifier context is reused.
4. Put the complete section 1 taxonomy and tag boundaries verbatim in every classifier prompt.
5. Give each classifier the exact entrypoint and behavior-body paths for its batch.
6. Require path plus heading or line citations for every nontrivial role claim.
7. Collect the complete required result set before any direction-specific synthesis.

There is no parent-context fallback. If the host cannot provide fresh isolated read-only tasks,
the consuming skill returns `required_tool_missing: classification-fan-out`.

Classifier tasks never edit, write, install, invoke another model, or spawn graders. A requested
or configured model is not proof of the actual model. Each task reports an actual host receipt
when one exists and `UNKNOWN` otherwise.

## 4. Base result

The direction-neutral base fields are:

```text
Skill | Roles | Evidence | Notes
```

Each consuming skill appends its own verdict fields. `tier-escalate` owns seed phase, trigger,
and arm-pin fields. `tier-offload` owns local slice, gate state, tool needs, and config value.

Before a consumer accepts a positive routing claim, its parent reopens the cited behavior body.
Classification output is evidence to verify, not authority to route.

## 5. Deliberate exclusions

This file contains no:

- escalation or offload verdict enum;
- stronger-tier seed rule;
- local-model eligibility correction;
- gate-precondition or Switchboard config rule;
- provider command, model ID, or discovery-root default.

Those rules live in the consuming cores and provider adapters. When this taxonomy, discovery
protocol, or base output changes, inspect both consumers before landing.
