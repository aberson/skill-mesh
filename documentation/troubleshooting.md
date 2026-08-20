# Troubleshooting

Provider selection and transport authentication are separate axes (see
[`architecture.md`](architecture.md) section 5 and [`providers/`](providers/)).
Most router problems fall into one of the two categories below; check which axis
is failing before changing anything.

Codex is not a router provider at all, so neither category fits it -- its
failure modes are install- and discovery-shaped. See "Codex profile install
and discovery" below.

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
powershell -File runtime\skill-router.ps1 -Provider claude -Skill <skill>
powershell -File runtime\skill-router.ps1 -Provider gpt -Skill <skill>
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
[`providers/gpt.md`](providers/gpt.md) for the full precedence tables. Codex
has no router transport to pick because the router has no `codex` provider to
select in the first place (`runtime/skill-router.ps1`), so selection never
reaches transport selection; a codex install runs host-native inside the Codex
CLI. See [`providers/codex.md`](providers/codex.md).

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
regardless of which host (Claude, GPT/Copilot, a Codex session invoking the
router with an explicit `-Provider`, or a generic CI runner) actually invoked
the router. Making this check host-marker-based (only "true" inside an actual
Claude Code session) was considered and rejected -- it would break that exact
retry for a legitimate GPT-host session falling back to Claude, which is the
more important guarantee.

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

## Codex profile install and discovery (not a router problem)

Codex is selected when its profile is **installed**, never by the router's
`-Provider` flag (the installer's own `-Provider codex` is a different flag on
a different tool, and is mandatory there). The router accepts only `auto`,
`claude`, `gpt`, and `local` (`runtime/skill-router.ps1`), and architecture.md
section 5.3 has no codex row, so `-Provider auto` cannot detect a Codex CLI
session at all -- it reports "could not identify the host" (above) unless a
Claude or Copilot marker is also set. Codex problems are therefore never "the
router chose wrong"; they are "the profile is not in the home the host reads".
Two read-only tools answer that, and neither mutates, prompts, or contacts a
network service:

```powershell
powershell -File tools\probe-codex-skills.ps1
powershell -File tools\inspect-host-install.ps1 -Home <install-home>
```

The probe resolves the codex home from `HOME`/`USERPROFILE` -- reporting and
stopping with exit code 2 rather than picking a winner when they disagree --
then reports that home's `.agents/skills` tree, the install ledger's codex
entry, and `AGENTS.md` presence. **It never runs the Codex CLI**: filesystem
and environment only, so it is safe on a machine with no Codex installed, and
its report says so explicitly (the text header line `codex CLI NOT invoked`;
`codex_cli_invoked` under `-Format json`). The inspector reports a whole home
instead; its `HostInstallReport` is at `schema_version` 3, the version that
added the `profiles.codex` key beside `profiles.claude` and `profiles.gpt`.
Both accept `-Format json`.

### Codex: the Codex CLI sees no skill-mesh skills

Either the profile was never installed, or it went into a different home than
the one the Codex CLI reads. skill-mesh writes the codex profile to
`<install-home>/.agents/skills/` (`tools/skill-mesh-discovery.ps1` owns that
map), so an install pointed at the wrong `-Home` is invisible however correct
the build was.

**Fix:** resolve the home first:

```powershell
powershell -File tools\probe-codex-skills.ps1
```

then install into exactly that home:

```powershell
powershell -File tools\install-skill-mesh.ps1 -Provider codex -Home <install-home>
```

With `-DistDir` omitted the codex profile is built on the fly. A pre-built
`-DistDir` must have been built with `-Provider codex` or `-Provider all` --
build-distributions' `-Provider both` still means claude+gpt, so a `both` tree
has no codex profile to install.

### Codex: `.agents/skills` is present but skill-mesh did not write it

The directory existing is not evidence of an install. The evidence is the
probe's `generated-header candidates` count and its ledger line
(`.skill-mesh-install.json`: `state`, `codex_installed`, `owned_files`; that
last field is spelled `codex_owned_files` under `-Format json`) -- a root with
entries but zero candidates and no ledger entry was written by something else.
That is also why an install can refuse: it will not overwrite a path it cannot
prove it owns, so it lists every such path and writes nothing. Remove those
paths, or pass `-Force` **together with** a `-BackupDir` pointing at a
directory outside the install home: the pre-overwrite backup is mandatory for
every adopted target, so `-Force` on its own hits a second refusal and still
writes nothing. (`-ForceShared` scopes the same adoption to the `_shared/`
payload, and requires `-BackupDir` too.) A collision that is a directory
sitting at a file target is adoptable by neither flag -- a non-leaf target is
refused before the take-ownership branch is reached, so removal is the only
path. Uninstall then removes only what the ledger claims.

### Codex: Copilot enumerates the codex profile too

Expected behavior, not a collision defect. `.agents/skills` is **two distinct
things at one literal path**: skill-mesh's codex install target, and one of
GitHub Copilot CLI's own native project discovery roots. The sharing is a
deliberate design decision (**D-CP6**), accepted on measured evidence and
re-confirmed against Copilot CLI 1.0.80 -- see
[`parity-deltas.md`](parity-deltas.md). It cuts both ways: a codex install
**is** enumerable by Copilot, and the root's mere presence proves nothing
about which tool wrote it.

### Codex: a working Codex session is not proof of an installed profile

This is the codex form of the conflation
[`host-discovery.md`](host-discovery.md) exists to kill -- a model answering
plausibly proves nothing about which skill tree, if any, was discovered.
`AGENTS.md` proves nothing either: instruction injection and skill discovery
are separate, non-interchangeable mechanisms, so an `AGENTS.md` in the home is
evidence neither for nor against an installed profile. Proof comes only from
the discovery root -- the probe's `.agents/skills` report, or the
`profiles.codex` block of `inspect-host-install.ps1`.

## Test-only environment overrides (do not use in production)

`SKILL_MESH_COPILOT_BASE_URL`, `SKILL_MESH_OPENAI_BASE_URL`, and
`SKILL_MESH_TRANSPORT_TIMEOUT_SEC` let `tests/router/` point the GPT transports
at a local mock server and shorten timeouts, so auth-failure/rate-limit/
timeout/precedence behavior can be exercised without live credentials or real
network calls. They have no effect beyond redirecting the HTTP endpoint and
timeout the router already uses -- leave them unset outside of tests.
