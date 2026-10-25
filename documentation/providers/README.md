# Provider Guides

**v2.0.0 is published.** Get the versioned bundle and scoped qualification notes
from the [release](https://github.com/aberson/skill-mesh/releases/tag/v2.0.0).
The [installation guide](../../README.md#install-or-upgrade) covers upgrades and
restoration; the [skill reference](../skill-reference.md) links every packaged
skill to its individual workflow diagram. Catalog coverage does not establish
that every host supplies every required native capability.

Per-provider authentication, capabilities, divergences, and installation notes for
skill-mesh. Provider **selection** and transport **authentication** are separate
axes (see [`../architecture.md`](../architecture.md) §5): choosing a provider never
implies a specific API key.

skill-mesh is provider-neutral. A Claude session runs Claude adapters; a
GPT/Copilot session runs GPT adapters; an OpenAI Codex CLI session runs Codex
adapters. None of the three is "the default product." The shared pipeline is
identical; only host-specific exceptions differ.

## Guides

- [claude.md](claude.md) — Claude Code host binding, transport, capabilities.
- [gpt.md](gpt.md) — GPT/Copilot host binding, transport precedence, capabilities.
- [codex.md](codex.md) — OpenAI Codex CLI host binding, transport, capabilities.
- [../host-discovery.md](../host-discovery.md) — host-loading authority map: instruction injection vs. native discovery vs. router dispatch.

## Capability & exclusion matrix

Counts derived from `config/skill-manifest.json`; the per-host runtime behavior
in the Codex cells below from the `skills/<name>/providers/codex.md` adapters and
[`../parity-deltas.md`](../parity-deltas.md). 54 skills are portable and carry all
three adapters — Claude, GPT, and Codex (`counts.gpt` and `counts.codex` are both
54); 3 are Claude-native exclusions with a `claude` adapter only. Codex coverage is
additive on a portable record, not a third status: the manifest's only `status`
values are `portable` and `provider-native`.

| Capability class | Claude | GPT/Copilot | Codex | Local (`code-30b`) |
|---|---|---|---|---|
| Portable skills (54) | yes | yes | an adapter for all 54; agent-dependent behavior is capability-conditioned. `build-step` and `user-debug` support a proven fresh-context host, while an ordinary CLI host halts `required_tool_missing` — see [codex.md](codex.md) § Known limitations | 21 of 54 (`local_capable`) |
| Vision skills (2: judge-ui, judge-motion) | yes | judge-ui only (judge-motion is a native exclusion) | judge-ui adapter only; its independent vision-judge dispatch is capability-conditioned on BOTH the agent-isolation contract and a proven image-capable child, and halts with `required_tool_missing` on a host that fails either | no |
| `sub-agent` skills (20) | yes | yes, parent-owned actions (18 GPT-portable; context-slim + judge-motion are native exclusions). `lesson-harvest` is packaged here, but its current GPT preview halts where D-GPT leaves fresh-context proof unavailable | the same 18 adapters: `citation-review` and `citation-sweep` keep preparation, exact run identity and commits in the parent and dispatch only fresh depth-1 classification judges; sweep opens every selected run before any commit. `lesson-harvest` produces only a bounded, audited local preview on a host that proves fresh siblings; automatic publication is unavailable in v2. `build-step` uses proven fresh-context dispatch plus separate opaque parent state and parent-only verdict service when phase-run; `user-debug` separately requires proven fresh siblings for Step 2 and Option 4; the remaining agent-dependent adapters retain their documented capability gates, and unsupported hosts halt `required_tool_missing`. `skill-evolve` and `skill-iterate` still require their Workflow primitive; `goblin-suggest` maps no Codex Workflow route; `user-uat` retains its independent assessor and strong-final gates. `goblin-do` remains outside this capability set | no |
| Claude-native exclusions (3) | yes | **no adapter** | **no adapter** | no |

### Claude-native exclusions

These three skills have `core: null` and a single truthful `claude` adapter. They
receive no misleading GPT or Codex stubs:

| Skill | Reason |
|---|---|
| `claude-oauth-auth` | Claude OAuth flow; Claude-native. |
| `context-slim` | Claude Code context management; Claude-native. |
| `judge-motion` | Claude-native motion/vision capture; Claude-native. |

## Authentication axes (summary)

| Axis | Claude | GPT/Copilot | Codex |
|---|---|---|---|
| Provider selection | `-Provider claude` or Claude host binding | `-Provider gpt` or GPT host binding | `-Provider codex` at install time, or Codex CLI host binding (no router value) |
| Primary transport | host-native execution (no API key required) | GitHub Copilot authentication | host-native execution (no API key required) |
| Optional transport | direct Anthropic API (`ANTHROPIC_API_KEY`) | direct OpenAI API (`OPENAI_API_KEY`) | none |

`OPENAI_API_KEY` is **not** universally required for GPT; it is only the optional
direct-OpenAI transport, tried only when Copilot is unavailable or fails. Full
precedence and diagnostics (Step 37): [`gpt.md`](gpt.md), and
[`../troubleshooting.md`](../troubleshooting.md) for provider-selection and
transport-auth failure modes.

Codex involves no transport credential at all: `providers.codex.transport_default`
in `config/skill-manifest.json` is `host-native`, the same class as Claude — not
Copilot authentication, and not an API key. See [`codex.md`](codex.md).

## Host-metadata adapters

`-Provider auto` delegates detection to one adapter per approved source
(`runtime/providers/`): `claude-host.ps1` (`Test-ClaudeHostMarkers`) and
`copilot-host.ps1` (`Test-CopilotHostMarkers`). `runtime/skill-router.ps1`
composes their results and applies the ambiguous/absent contract
(architecture.md section 5.3) -- it never guesses and never silently defaults
to Claude. There is no codex host-metadata adapter, and `codex` is not a value in
the router's `-Provider` set (`auto`, `claude`, `gpt`, `local`): a codex profile is
bound at install time by
`tools/install-skill-mesh.ps1 -Provider codex -Home <install-home>`, never by
`-Provider auto`.

## See also

[`README.md`](../../README.md) (repository root) for the skill catalog and top-level
installation/authentication matrices; [`migration.md`](../migration.md) for what changed from the
pre-migration, Claude-first layout.
