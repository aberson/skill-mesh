# Claude Provider Guide

Claude Code host binding, transport, and capabilities for skill-mesh. See
[`../architecture.md`](../architecture.md) for the full package contract.

## Host binding (primary)

A Claude Code installation binds the `claude` adapter of every skill into Claude's
discovery layout:

```powershell
pwsh -File tools\install-skill-mesh.ps1 -Profile claude -Destination <claude-skills-root>
```

Each installed skill resolves `skills/<name>/providers/claude.md`, which references
the shared `skills/<name>/core.md` (for portable skills). Discovery loads the
Claude adapter directly; no runtime provider decision is required. Windows junction
(`mklink /J`) installation is the primary pattern and is exercised by the
distribution tests in Step 36.

The installer emits a generated discovery tree; it never rewrites canonical source
files.

## Transport / authentication

| Transport | When | Requirement |
|---|---|---|
| Host-native execution | default inside Claude Code | none — the host provides the model |
| Direct Anthropic API | headless/CI direct execution | `ANTHROPIC_API_KEY` (optional) |

Claude host-native execution does **not** require `ANTHROPIC_API_KEY`. The API key
is only the optional direct-API transport, independent of provider selection.

## Capabilities

Claude adapters support the full capability vocabulary: `filesystem`, `sub-agent`,
and `vision`. All 47 portable skills and all 3 Claude-native exclusions have a
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
