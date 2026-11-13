---
name: user-fermize
description: Break down a complex build decision and identify a useful simpler first milestone, deferrals, and necessary evidence.
user-invocable: true
---

# user-fermize - Claude entry point

See [../core.md](../core.md) for the full specification. Load the core in full before acting.

## Provider-specific instructions

- Use Claude Code's file-reading and shell tools for the local read-only inspection permitted by the core. Use an available clock for its inspection bound.
- This workflow requires no Agent/Workflow dispatch, named-skill dispatch, browser, or Artifact action. Follow the core's existing evidence/time fallbacks when tools or sources are unavailable; never claim an inspection that did not occur.
- Keep the core's scope, gates, and advisory boundary unchanged. Return its plain-language Markdown report, source references, and optional text tree.
