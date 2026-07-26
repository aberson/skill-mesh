# Provider Guides

Per-provider authentication, capabilities, divergences, and installation notes for
skill-mesh. Provider **selection** and transport **authentication** are separate
axes (see [`../architecture.md`](../architecture.md) §5): choosing a provider never
implies a specific API key.

skill-mesh is provider-neutral. A Claude session runs Claude adapters; a
GPT/Copilot session runs GPT adapters. Neither is "the default product." The shared
pipeline is identical; only host-specific exceptions differ.

## Guides

- [claude.md](claude.md) — Claude Code host binding, transport, capabilities.
- [gpt.md](gpt.md) — GPT/Copilot host binding, transport precedence, capabilities.

## Capability & exclusion matrix

Derived from `config/skill-manifest.json`. 47 skills are portable (Claude + GPT
adapters); 3 are Claude-native exclusions with no GPT adapter.

| Capability class | Claude | GPT/Copilot | Local (`code-30b`) |
|---|---|---|---|
| Portable skills (47) | yes | yes | 24 of 47 (`local_capable`) |
| Vision skills (2: judge-ui, judge-motion) | yes | judge-ui only (judge-motion is a native exclusion) | no |
| `sub-agent` fan-out skills (16) | yes | yes, parent-owned actions (14 GPT-portable; context-slim + judge-motion are native exclusions) | no |
| Claude-native exclusions (3) | yes | **no adapter** | no |

### Claude-native exclusions

These three skills have `core: null` and a single truthful `claude` adapter. They
receive no misleading GPT stubs:

| Skill | Reason |
|---|---|
| `claude-oauth-auth` | Claude OAuth flow; Claude-native. |
| `context-slim` | Claude Code context management; Claude-native. |
| `judge-motion` | Claude-native motion/vision capture; Claude-native. |

## Authentication axes (summary)

| Axis | Claude | GPT/Copilot |
|---|---|---|
| Provider selection | `-Provider claude` or Claude host binding | `-Provider gpt` or GPT host binding |
| Primary transport | host-native execution (no API key required) | GitHub Copilot authentication |
| Optional transport | direct Anthropic API (`ANTHROPIC_API_KEY`) | direct OpenAI API (`OPENAI_API_KEY`) |

`OPENAI_API_KEY` is **not** universally required for GPT; it is only the optional
direct-OpenAI transport. Full precedence and diagnostics land with the router work
in Step 37.
