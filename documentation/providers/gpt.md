# GPT / Copilot Provider Guide

GPT/Copilot host binding, transport precedence, and capabilities for skill-mesh.
See [`../architecture.md`](../architecture.md) for the full package contract.

## Host binding (primary)

A GPT/Copilot installation binds the `gpt` adapter of every portable skill into the
host's discovery layout:

```powershell
pwsh -File tools\install-skill-mesh.ps1 -Provider gpt -Home <gpt-skills-root>
```

Each installed skill resolves `skills/<name>/providers/gpt.md`, which references the
shared `skills/<name>/core.md`. Discovery loads the GPT adapter directly, so a GPT
session cannot accidentally discover the Claude compatibility launcher first.

Only the 47 portable skills have a GPT adapter. The 3 Claude-native exclusions are
not installed into a GPT profile.

## Transport / authentication precedence

Selecting GPT does **not** imply `OPENAI_API_KEY`. `runtime/skill-router.ps1`
chooses a transport independently, in this order (`Invoke-GptWithTransportPrecedence`):

| Order | Transport | Requirement |
|---|---|---|
| 1 | GitHub Copilot authentication | Copilot sign-in (`COPILOT_GITHUB_TOKEN` / `GH_TOKEN` / `GITHUB_TOKEN` / `gh auth token`); no `OPENAI_API_KEY` |
| 2 | Direct OpenAI API (optional fallback) | `OPENAI_API_KEY`; tried only if Copilot is unavailable or fails |

The public README must never present `OPENAI_API_KEY` as universally required.
Copilot-first selection and the optional direct-OpenAI fallback transport are
implemented and tested in Step 37 (see `tests/router/test_gpt_transport_precedence.py`);
diagnostics report only credential presence/source class, never values (see
[`../troubleshooting.md`](../troubleshooting.md)).

Falling through BOTH GPT transports counts as a single GPT-provider failure and
triggers the router's existing bounded single-retry-to-Claude fallback -- trying
Copilot then OpenAI is a same-provider transport choice, not an extra
cross-provider retry (see [`../troubleshooting.md`](../troubleshooting.md)).

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

## Host-metadata detection

`-Provider auto` detects a GPT/Copilot host via `runtime/providers/copilot-host.ps1`
(`Test-CopilotHostMarkers`), which reads only `COPILOT_CLI` / `COPILOT_AGENT_SESSION_ID`
-- see [`../architecture.md`](../architecture.md) section 5.3.

## Explicit routing

To force GPT from any host via the router:

```powershell
pwsh -File runtime\skill-router.ps1 -Provider gpt -Skill <skill>
```

`-Model gpt` remains a deprecated compatibility alias during the migration.

## See also

[`README.md`](../../README.md) for the installation/authentication matrices (including why
`OPENAI_API_KEY` is never universally required); [`claude.md`](claude.md) for the Claude
counterpart; [`../migration.md`](../migration.md) for the pre-migration → provider-neutral
transition.
