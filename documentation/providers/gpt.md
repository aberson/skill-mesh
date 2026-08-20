# GPT / Copilot Provider Guide

GPT/Copilot host binding, transport precedence, and capabilities for skill-mesh.
See [`../architecture.md`](../architecture.md) for the full package contract.

## Host binding (primary)

A GPT/Copilot installation binds the `gpt` adapter of every portable skill into the
host's discovery layout:

```powershell
pwsh -File tools\install-skill-mesh.ps1 -Provider gpt -Home <install-home>
```

Each installed skill resolves `skills/<name>/providers/gpt.md`, which references the
shared `skills/<name>/core.md`. Discovery loads the GPT adapter directly, so a GPT
session cannot accidentally discover the Claude compatibility launcher first.

Only the 54 portable skills have a GPT adapter. The 3 Claude-native exclusions are
not installed into a GPT profile.

### Native discovery root and SKILL.md format

The generated GPT discovery tree is written to
`<install-home>/.github/skills/<skill>/` — a real GitHub Copilot CLI native
skill-discovery root (proven against a live Copilot CLI v1.0.77 in Step 43, #58).
This discovered path is what proves a GPT profile is installed.

GitHub Copilot CLI discovers project skills from three roots — `.github/skills/`,
`.agents/skills/`, and `.claude/skills/` — plus the personal root
`~/.copilot/skills/`. This package installs the GPT profile to the conventional
project root `.github/skills/`. Because `.claude/skills/` is **also** a Copilot
discovery root, a consumer with both profiles installed is doubly exposed; Step 45 (#67) resolved
that collision against a live Copilot CLI v1.0.77 — Copilot dedups by name and scans
`.github/skills` before `.claude/skills`, so the GPT profile stably wins and is never shadowed.
Installing both profiles is safe.

**Every generated GPT `SKILL.md` must lead with a YAML frontmatter block** containing
at least `name` and `description`; Copilot rejects a `SKILL.md` without it. The
builder emits that frontmatter first (with the provenance header immediately after
the closing `---`); `name` and `description` come from the single per-skill
`description` field in `config/skill-manifest.json`, never re-authored per host.

The originally-assumed project-relative `.copilot/skills` target is **retired**: Step
43 proved it is **not** a GitHub Copilot CLI discovery root (a planted skill there
returned `NOT REGISTERED`), so no install writes to it. A pre-retarget
`.copilot/skills` install is only a legacy wrong-target to migrate off.

A GPT model answering correctly is **not** proof of a native install: a Copilot CLI
can expose skills via runtime injection of a `CLAUDE.md` even when no
`.github/skills` tree is present. That is host integration, not native discovery,
and the running model does not select the skill tree.

A root `AGENTS.md` (or an injected `CLAUDE.md`) is an **instruction adapter, not a
skill registry**: it does not contain or enumerate skill implementations.
Instruction loading and skill discovery are separate mechanisms — see the
host-loading authority map [`../host-discovery.md`](../host-discovery.md).

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

- `sub-agent` fan-out skills (15 GPT-portable: build-step, citation-sweep,
  goblin-do, goblin-suggest, judge-ui, research-prospect, review-deep,
  review-gauntlet, skill-evolve, skill-iterate, test-prune, tier-escalate,
  tier-offload, user-brainstorm, user-learn) map fan-out onto the provider's
  action/task API; orchestration remains parent-owned. (context-slim and judge-motion are also
  `sub-agent` but are Claude-native exclusions with no GPT adapter.)
- `vision`: `judge-ui` uses native GPT vision (GPT-5.6 Sol) with the read-back +
  swap-and-tie calibration contract.

The GPT peer model for each skill is resolved from `config/model-tier-map.json` at
invocation time.

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
