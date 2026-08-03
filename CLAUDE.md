# skill-mesh — project instructions

## Project overview

skill-mesh is a provider-neutral collection of ~50 agent skills for planning, building, reviewing,
and shipping software. Each skill is authored once as a shared behavior contract (`core.md`) plus
thin per-host adapters, so the same skill runs on Claude Code and GitHub Copilot CLI.

This repository is the **canonical source and the build/release toolchain** — it is not itself an
installed skill tree. Installing produces a host-native discovery tree in a consumer home.

## Stack

| Layer | Choice |
|---|---|
| Skill sources | Markdown — `skills/<name>/core.md` + `providers/{claude,gpt}.md` |
| Manifest / config | JSON — `config/skill-manifest.json` (authoritative skill inventory) |
| Build / install / release tooling | PowerShell (`pwsh`) — `tools/*.ps1` |
| Manifest + release checks | Python 3 — `tools/gen_manifest.py`, `tools/release_checks.py` |
| Tests | pytest — 7 suites under `tests/` |
| Lint / typecheck | **Not configured** (deliberate — see Key commands) |

## Key commands

Run from the repository root.

Full test suite (~13 minutes — the release, distribution, and smoke suites shell out to PowerShell):

```
python -m pytest tests/
```

Fast contract gate — use this during iteration, not as a release gate:

```
python -m pytest tests/package-integrity
```

Build host distributions (writes `dist/`, which is gitignored and never committed):

```
pwsh -File tools/build-distributions.ps1 -Provider claude
pwsh -File tools/build-distributions.ps1 -Provider gpt
```

Install one host profile into a consumer home:

```
pwsh -File tools/install-skill-mesh.ps1 -Provider claude -Home <install-home>
pwsh -File tools/install-skill-mesh.ps1 -Provider gpt    -Home <install-home>
```

Release — stage from `git ls-files`, build, run the integrity check inside the staged tree, then
SHA-256 every file under the generated `dist/`:

```
pwsh -File tools/release.ps1
```

Regenerate the manifest (only when the legacy source or the authoritative constants change; the
source root comes from the `SKILL_MESH_LEGACY_SOURCE` environment variable, never a committed path):

```
python tools/gen_manifest.py
```

**There is no lint command and no typecheck command, by design** (`documentation/architecture.md`
§8.4). Do not invent one, and do not report "0 lint violations / 0 type errors" when wrapping a
phase — pytest is the only automated gate this repository has.

## Directory layout

```
skills/<name>/          Canonical source: core.md + providers/{claude,gpt}.md (50 skills)
<skill>/SKILL.md        Legacy top-level packages (46) — compatibility surface during the
                        deprecation window; NOT canonical, not updated by the migration
_shared/                Shared cores (judge-core, intake-engine), grader/verdict engines,
                        and the README's light/dark SVG diagrams
config/                 skill-manifest.json (inventory + eligibility), model-mapping.json,
                        model-tier-map.json
documentation/          architecture.md (the contract), host-discovery.md, migration.md,
                        providers/, troubleshooting.md, and the phase plans
runtime/                skill-router.ps1, path-guard.ps1, providers/, telemetry/
tools/                  build-distributions, install-skill-mesh, release, release_checks,
                        gen_manifest, gen_skill_tree, gen-router-shim, provenance
tests/                  calibration, distributions, package-integrity, release, router,
                        smoke, telemetry (+ fixtures/)
```

## Architecture summary

- **One behavior contract per skill.** `skills/<name>/core.md` is provider-independent; each
  `providers/<host>.md` wrapper loads the core in full and maps host abstractions onto it. A wrapper
  may never weaken a gate defined in the core. 47 skills are portable (both adapters); 3 are
  provider-native Claude-only (`claude-oauth-auth`, `context-slim`, `judge-motion`) and carry
  `core: null` in the manifest.
- **Manifest-driven build.** `tools/build-distributions.ps1` reads `config/skill-manifest.json` and
  emits host-native `SKILL.md` discovery trees into `dist/claude` and `dist/gpt`.
- **Install binds exactly one profile** into a consumer home — Claude at `<home>/.claude/skills/`,
  GPT at `<home>/.copilot/skills/` — recording an ownership ledger so uninstall only removes files
  it installed, and refusing foreign-file collisions by default.
- **Three host-loading mechanisms are distinct and non-interchangeable**
  (`documentation/host-discovery.md`): workspace instruction injection (`CLAUDE.md` / `AGENTS.md`
  are instruction adapters, never skill registries), host-native skill discovery (the two roots
  above), and explicit router dispatch. **Model choice does not select a skill tree** — a running
  GPT model is not proof of an installed GPT profile.
- **Releases are reproducible.** Staging enumerates git-tracked files only, so an untracked scratch
  file can never enter an artifact; checksums cover the generated `dist/` (normalized CRLF→LF, BOM
  stripped) rather than the source checkout, whose line endings vary by clone.

## Current state

**Phase 7 — Host-Native Discovery & Consumer Cutover, in progress.** Step 42 of Steps 42–48 is
DONE (the host-loading authority map, locked by 12 package-integrity tests); Steps 43–48 are
pending, starting with the operator-run GPT discovery-root proof. 285 tests pass, 3 skip.

Phases 1–6 delivered the canonical `skills/` source tree, the provider-neutral router, and the
distribution, installer, and release tooling. Plan:
`documentation/host-native-discovery-cutover-plan.md` (it supersedes the unexecuted Step 41
acceptance intent of `documentation/provider-neutral-skill-mesh-plan.md`).

## Environment requirements

- **Windows with PowerShell.** All build, install, and release tooling is `.ps1`; the distribution
  and release test suites shell out to it. There is no POSIX path.
- **Python 3 with pytest** on `PATH` (or an activated project venv). No `pyproject.toml`, no
  dependency lockfile, and no pinned interpreter is committed — supply your own.
- **git** — release staging is `git ls-files`-driven and fails outside a working tree.
- **`gh` CLI** for issue/PR work.
- **GitHub Copilot CLI, signed in via `gh auth login`**, for any GPT-side host acceptance.
  Copilot subscription auth is the transport — **no `OPENAI_API_KEY` is used or needed**.
- Writing this file: keep absolute user paths out of every committed file. This is a public
  repository and `tests/package-integrity/test_manifest_contract.py` gates it.
