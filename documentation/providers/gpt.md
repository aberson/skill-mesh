# GPT / Copilot Provider Guide

GPT/Copilot host binding, transport precedence, and capabilities for skill-mesh.
See [`../architecture.md`](../architecture.md) for the full package contract.

## Host binding (primary)

A GPT/Copilot installation binds the `gpt` adapter of every portable skill into the
host's discovery layout:

```powershell
pwsh -File tools\install-skill-mesh.ps1 -Profile gpt -Destination <gpt-skills-root>
```

Each installed skill resolves `skills/<name>/providers/gpt.md`, which references the
shared `skills/<name>/core.md`. Discovery loads the GPT adapter directly, so a GPT
session cannot accidentally discover the Claude compatibility launcher first.

Only the 47 portable skills have a GPT adapter. The 3 Claude-native exclusions are
not installed into a GPT profile.

## Transport / authentication precedence

Selecting GPT does **not** imply `OPENAI_API_KEY`. Transport is chosen
independently, in this order:

| Order | Transport | Requirement |
|---|---|---|
| 1 | GitHub Copilot authentication | Copilot sign-in; no `OPENAI_API_KEY` |
| 2 | Direct OpenAI API (optional fallback) | `OPENAI_API_KEY` |

The public README must never present `OPENAI_API_KEY` as universally required.
Copilot-first selection and the optional OpenAI fallback are implemented and tested
independently in Step 37; diagnostics report only credential presence/source class,
never values.

## Capabilities

GPT adapters support `filesystem`, `sub-agent`, and `vision`:

- `sub-agent` fan-out skills (14 GPT-portable: build-step, goblin-do,
  goblin-suggest, judge-ui, research-prospect, review-deep, review-gauntlet,
  skill-evolve, skill-iterate, test-prune, tier-escalate, tier-offload,
  user-brainstorm, user-learn) map fan-out onto the provider's action/task API;
  orchestration remains parent-owned. (context-slim and judge-motion are also
  `sub-agent` but are Claude-native exclusions with no GPT adapter.)
- `vision`: `judge-ui` uses native GPT vision (GPT-5.6 Sol) with the read-back +
  swap-and-tie calibration contract.

The GPT peer model for each skill is resolved from `config/model-tier-map.json` at
invocation time (lands Step 34).

## Explicit routing

To force GPT from any host via the router (lands Step 34):

```powershell
pwsh -File runtime\skill-router.ps1 -Provider gpt <skill>
```

`-Model gpt` remains a deprecated compatibility alias during the migration.
