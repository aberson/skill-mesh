# Troubleshooting

Provider selection and transport authentication are separate axes (see
[`architecture.md`](architecture.md) section 5 and [`providers/`](providers/)).
Most router problems fall into one of the two categories below; check which axis
is failing before changing anything.

## Provider selection (`-Provider auto` fails)

`-Provider auto` consults **only** the approved host-identity environment
variables (architecture.md section 5.3). It never guesses and never silently
defaults to Claude.

### "`-Provider auto` could not identify the host" (exit code 2)

Neither Claude's markers (`CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`) nor
Copilot's markers (`COPILOT_CLI`, `COPILOT_AGENT_SESSION_ID`) are set. This is
expected outside a Claude Code or GitHub Copilot CLI session (e.g. a bare
terminal, a generic CI runner, or a host neither product recognizes yet).

**Fix:** pass the provider explicitly:

```powershell
pwsh -File runtime\skill-router.ps1 -Provider claude -Skill <skill>
pwsh -File runtime\skill-router.ps1 -Provider gpt -Skill <skill>
```

### "`-Provider auto` is ambiguous" (exit code 2)

Both Claude AND Copilot host markers are set at once (e.g. a Copilot CLI task
launched from inside a Claude Code terminal). The router refuses to guess.

**Fix:** pass `-Provider claude` or `-Provider gpt` explicitly for that
invocation.

### Setting a credential does not select a provider

`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, `GH_TOKEN`,
and `GITHUB_TOKEN` are **transport credentials**, not host identity, and
`-Provider auto` never reads them (architecture.md section 5.3 explicitly
excludes them). If you set one hoping it would pick a provider, it will not --
pass `-Provider` explicitly instead.

### `-Model` deprecation warning

`-Model claude|gpt|local` is a deprecated compatibility alias for `-Provider`,
retained during the migration. It still works and maps 1:1 onto `-Provider`,
but emits a deprecation notice on stderr. Update call sites to `-Provider` when
convenient; there is no forced-removal deadline yet.

## Transport authentication (a selected provider fails to run)

Once a provider is selected (by binding, `-Provider`, or `auto`), the router
picks a **transport** for that provider independently. See
[`providers/claude.md`](providers/claude.md) and
[`providers/gpt.md`](providers/gpt.md) for the full precedence tables.

### GPT: "No GPT transport available" (exit code 2, falls back to Claude)

Both the primary transport (GitHub Copilot) and the optional fallback (direct
OpenAI) are unavailable:

- Copilot: no GitHub token was found via `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` /
  `GITHUB_TOKEN` / `gh auth token`, or the Copilot health check failed
  (expired/invalid token, network error, rate limit, timeout -- the router
  reports the failure class but never the credential value).
- Direct OpenAI: `OPENAI_API_KEY` is not set (this is expected -- it is
  optional).

**Fix:** authenticate Copilot (`gh auth login`, or set `GH_TOKEN` /
`COPILOT_GITHUB_TOKEN`) -- this alone is sufficient; you do **not** need
`OPENAI_API_KEY`. Setting `OPENAI_API_KEY` as a fallback is optional and only
helps if Copilot itself is down.

### GPT: it used the direct-OpenAI transport when I expected Copilot

Copilot is always tried first. If the router reports
`GPT invocation succeeded ... via openai-direct`, Copilot was unavailable or
failed for this call (check the preceding `WARNING -- Copilot ... failed`
line for the reason) and the optional fallback was used instead. This is
correct precedence, not a bug -- but if Copilot should have been available,
re-check its own credential/health status.

### GPT: token expired / 401 from Copilot or OpenAI

The router treats an auth failure exactly like any other transport failure:
warn, try the next transport (OpenAI, if configured), and if both are
exhausted, fall back to Claude once. Re-authenticate the failing transport
(`gh auth login` for Copilot; rotate `OPENAI_API_KEY` for the direct-OpenAI
fallback) and retry.

### GPT: rate limited (429) or timed out

Same fail-open path as an auth failure: the failing transport is treated as
unavailable for this call, the next configured transport is tried, and Claude
is the last resort. No retry loop runs against the same transport within one
invocation (see the bounded retry contract below).

### Claude: "Both Claude and GPT unavailable" (exit code 3 -- HALT)

**Currently unreachable in practice, by design.** `Invoke-ClaudeModel` is a
stub (it returns a marker string; the router does not itself place a live
Anthropic API call), and `Test-AnthropicAvailable` correspondingly always
reports Claude as available -- there is no real transport for it to probe.
This is deliberate: it preserves the fail-open contract that a GPT-provider
failure always lands successfully on the single bounded Claude retry,
regardless of which host (Claude, GPT/Copilot, or a generic CI runner)
actually invoked the router. Making this check host-marker-based (only "true"
inside an actual Claude Code session) was considered and rejected -- it would
break that exact retry for a legitimate GPT-host session falling back to
Claude, which is the more important guarantee.

Exit-3 itself is NOT entirely dead code -- `-Provider local` on a skill that
isn't `local-capable`, or with no local model reachable
(`Test-LocalModelAvailable` false), reaches it directly and is tested. Only
the specific combination this heading names ("Claude unavailable, so fall
through to local, and if THAT'S also unavailable, halt" -- the branch inside
`Invoke-ClaudeVariant`) is unreachable today, because its gate
(`Test-AnthropicAvailable`) never returns false. If a real direct-Anthropic-API
transport is added later (see `providers/claude.md`'s "optional" row), this
section should be revisited alongside making `Test-AnthropicAvailable` a real
check.

### Diagnostics never show a secret value

By design: every router diagnostic reports credential **presence** and
**source class** only (e.g. `Copilot token: present (COPILOT_GITHUB_TOKEN/...)`,
`OPENAI_API_KEY: SET`), never a token/key value -- not even truncated. If you
need to confirm which literal credential is active, check your own shell
environment directly; the router will not print it for you, on purpose.

### The bounded cross-provider retry contract

A GPT-provider failure (both transports exhausted) triggers **exactly one**
retry, to Claude. This budget is fixed and is not widened by the optional
OpenAI fallback: trying Copilot then OpenAI is a same-provider **transport**
choice, not an extra cross-provider retry. If you see more than one
Claude-retry line for a single invocation, that is a defect, not the intended
contract.

## Test-only environment overrides (do not use in production)

`SKILL_MESH_COPILOT_BASE_URL`, `SKILL_MESH_OPENAI_BASE_URL`, and
`SKILL_MESH_TRANSPORT_TIMEOUT_SEC` let `tests/router/` point the GPT transports
at a local mock server and shorten timeouts, so auth-failure/rate-limit/
timeout/precedence behavior can be exercised without live credentials or real
network calls. They have no effect beyond redirecting the HTTP endpoint and
timeout the router already uses -- leave them unset outside of tests.
