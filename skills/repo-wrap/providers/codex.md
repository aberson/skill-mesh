# repo-wrap - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Load the core in full and follow its rail dispatch verbatim. Resolve exactly ONE target per invocation in the core's precedence (explicit positional arg, then the `/user-project` pin, then cwd), classify it against `.claude/observatory/registry.toml`, and state the classification line before acting. `owned` is an explicit registry fact -- no heuristic in this wrapper may promote a repo to Rail A.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Run all git and `gh` operations through Codex's shell tool as `git -C <target> ...`, preserving command order and exit codes and verifying repository identity before writes. Never infer command success from prose.
- Safety-critical, never weakened: apply the Owner-match check exactly as the core defines it -- extract the owner segment with the core's regex, compare case-insensitively for exact equality against `gh api user --jq .login`, and treat ANY error along the way as NOT owned. Never push a ref to a remote the operator does not own, never a bare `git push`, never `git push origin`, and never rely on a branch's configured upstream. Never open PRs or issues upstream.
- Preserve Rail B's commit discipline exactly: build the add list explicitly from `git status --porcelain` minus anomalies, foreign-session state files, and concurrent-edit suspects; never `git add -A`, never `git add .`, and never stash at the coding root. Preserve Rail D's creation guard: `gh repo create` runs only for an EXPLICITLY named positional target, and a pin- or cwd-resolved target gets the commands printed instead.
- Codex has no Artifact tool and needs none: every next-step block is printed text with an execution-context line naming the target directory. Autonomous by default -- never a `(y/n)` gate; a parked advisory is a legal, common outcome, and `--dry-run` performs zero mutations.
- Secrets are screened by filename metadata only. Never `cat`, `grep`, or otherwise print the contents of a suspected secrets file; a hit is parked with an advisory line.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: the classification line, one line per action taken, the parked-advisory list with exact commands, and any next-step blocks last. Preserve locked strings, the classification enum, paths, and command ordering exactly; reject missing required fields instead of inferring success.
