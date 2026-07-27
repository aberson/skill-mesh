# Repository Metadata (Proposed)

Proposed GitHub repository title and description text for `aberson/skill-mesh`, to correct the
Claude-only framing left over from before the provider-neutral migration (Steps 33-40 of
[`provider-neutral-skill-mesh-plan.md`](provider-neutral-skill-mesh-plan.md)).

**This document only proposes text. It does not change the live repository metadata.** Applying
it is Step 41 (operator action, gated on real Claude-host and GPT/Copilot-host acceptance —
see the plan's Step 41), run via `gh repo edit aberson/skill-mesh --description "..." --add-topic
... --remove-topic ...` or the GitHub web UI.

## Current (as of this migration)

Read via `gh repo view aberson/skill-mesh --json description,repositoryTopics`:

- **Description:** "36 Claude Code skills for an autonomous plan -> build -> review -> ship
  pipeline (judges, graders, scorers), with install/adapt docs."
- **Topics:** `agentic-workflows`, `claude`, `claude-code`, `developer-tools`, `llm`, `python`

Both the skill count (36) and the exclusive "Claude Code skills" framing are stale: the package
now ships 50 skills (47 portable with parallel Claude and GPT adapters, 3 explicit Claude-native
exclusions), and Claude is one of two first-class providers, not the only one.

## Proposed

- **Title:** `skill-mesh` (unchanged — already accurate and matches the package name).
- **Description:**
  > Provider-neutral skill pipeline (Claude + GitHub Copilot/GPT) for an autonomous
  > plan -> build -> review -> ship workflow: 47 portable skills with parallel Claude and GPT
  > adapters, 3 Claude-native exclusions, judges/graders/scorers, and install/build/release
  > tooling.
- **Topics:** keep `agentic-workflows`, `claude`, `claude-code`, `developer-tools`, `llm`,
  `python`; add `github-copilot`, `gpt`, `ai-agents`, `provider-neutral`.

## Rationale

- Neither provider should read as "the default" in the first thing a visitor sees — the
  description leads with "provider-neutral" and names both hosts before any workflow detail,
  matching the README's framing (see [`README.md`](../README.md)).
- The skill count (47 portable / 3 native / 50 total) is generated-consistent with
  `config/skill-manifest.json`, the same source the README's own count claim is checked against
  by `tests/package-integrity`.
- Adding `github-copilot` and `gpt` as topics makes the package discoverable from a GPT/Copilot
  search angle, not only a Claude one.
