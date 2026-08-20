# Claude Provider Guide

Claude Code host binding, transport, and capabilities for skill-mesh. See
[`../architecture.md`](../architecture.md) for the full package contract.

## Host binding (primary)

A Claude Code installation binds the `claude` adapter of every skill into Claude's
discovery layout:

```powershell
pwsh -File tools\install-skill-mesh.ps1 -Provider claude -Home <install-home>
```

Each installed skill resolves `skills/<name>/providers/claude.md`, which references
the shared `skills/<name>/core.md` (for portable skills). Discovery loads the
Claude adapter directly; no runtime provider decision is required. Installation copies the generated
discovery tree into the host root; junction and symlink targets that escape the
install home are rejected by `runtime/path-guard.ps1`, and the distribution tests
assert such an install must FAIL rather than write through the link.

The installer emits a generated discovery tree; it never rewrites canonical source
files.

### Native discovery root

The generated Claude discovery tree is written to
`<install-home>/.claude/skills/<skill>/` — Claude Code's native skill-discovery
root. A Claude install populates only `.claude/skills`, never a GPT root. This
discovered path is what proves a Claude profile is installed; the running model
does not select the tree.

Claude Code may also load a root `CLAUDE.md` workspace instruction file, but that
file is an **instruction adapter, not a skill registry**: it does not contain or
enumerate skill implementations. Instruction loading and skill discovery are
separate mechanisms — see the host-loading authority map
[`../host-discovery.md`](../host-discovery.md).

## Transport / authentication

| Transport | When | Requirement |
|---|---|---|
| Host-native execution | default inside Claude Code | none — the host provides the model |
| Direct Anthropic API | headless/CI direct execution | `ANTHROPIC_API_KEY` (optional) |

Claude host-native execution does **not** require `ANTHROPIC_API_KEY`. The API key
is only the optional direct-API transport, independent of provider selection.

## Capabilities

Claude adapters support the full capability vocabulary: `filesystem`, `sub-agent`,
and `vision`. All 54 portable skills and all 3 Claude-native exclusions have a
Claude adapter.

### Claude-native skills

`claude-oauth-auth`, `context-slim`, and `judge-motion` are Claude-only. They have
no neutral core and no GPT adapter; their `claude` adapter is self-contained.

## Host-metadata detection

`-Provider auto` detects a Claude host via `runtime/providers/claude-host.ps1`
(`Test-ClaudeHostMarkers`), which reads only `CLAUDECODE` / `CLAUDE_CODE_ENTRYPOINT`
-- see [`../architecture.md`](../architecture.md) section 5.3.

## Explicit routing

To force Claude from any host via the router:

```powershell
pwsh -File runtime\skill-router.ps1 -Provider claude -Skill <skill>
```

## See also

[`README.md`](../../README.md) for the installation/authentication matrices;
[`gpt.md`](gpt.md) for the GPT/Copilot counterpart; [`../migration.md`](../migration.md) for the
pre-migration → provider-neutral transition.
