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
tools/                  build-distributions, install-skill-mesh, inspect-host-install, release,
                        release_checks, gen_manifest, gen_skill_tree, gen-router-shim, provenance
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
  GPT at `<home>/.github/skills/` (a real GitHub Copilot CLI discovery root; the project-relative
  `.copilot/skills` target is **retired** per the Step 43 proof, and every generated GPT `SKILL.md`
  leads with a YAML `name`/`description` frontmatter block) — recording an ownership ledger so
  uninstall only removes files it installed, and refusing foreign-file collisions by default.
- **Three host-loading mechanisms are distinct and non-interchangeable**
  (`documentation/host-discovery.md`): workspace instruction injection (`CLAUDE.md` / `AGENTS.md`
  are instruction adapters, never skill registries), host-native skill discovery (the two roots
  above), and explicit router dispatch. **Model choice does not select a skill tree** — a running
  GPT model is not proof of an installed GPT profile.
- **Releases are reproducible.** Staging enumerates git-tracked files only, so an untracked scratch
  file can never enter an artifact; checksums cover the generated `dist/` (normalized CRLF→LF, BOM
  stripped) rather than the source checkout, whose line endings vary by clone.

## Current state

**Phase 7 — Host-Native Discovery & Consumer Cutover, in progress.** Steps 42–46 of Steps 42–50
are DONE: the host-loading authority map (locked by 17 package-integrity tests); the live
Copilot CLI v1.0.77 discovery-root proof, which **disproved** the assumed `.copilot/skills`
target; the resulting GPT retarget to `.github/skills` with YAML-frontmatter `SKILL.md`; and the
both-profile discovery proof (Step 45, #67) — with both profiles installed, Copilot dedups skills
by name and the `.github/skills` GPT profile wins the `.claude/skills` collision by discovery-root
precedence (`.github/skills` scanned first), so the migrator may install both profiles without the
GPT skill being shadowed; and read-only host-install inspection (Step 46, #59) — `tools/inspect-host-install.ps1`
plus `tests/distributions/test_host_inspect.py`, since **hardened** against the four defects a
full-suite wrap found in it (#83–#86, closed 2026-08-04): the `evidence_class` inversion that let a
bare `Test-Path` claim `observed`; ten channels echoing untrusted consumer bytes into the default
report; four untested behaviors (no `foreign` fixture, the corrupt-ledger paths, router
`canonical`/`legacy`, the `<external>` junction sentinel); and — highest blast radius — twelve
committed fixture `SKILL.md` files sitting at real discovery paths, which made this repository
publish phantom skills into its own host. Consumer-home fixtures are now synthesized at test time by
`tests/distributions/legacy_install_fixtures.py` and a `git ls-files` gate keeps them from coming
back. Steps 47–50 are pending, starting with
reversible legacy-install migration (Step 47) — re-scoped 2026-08-05 by
`documentation/step-47-decomposition-decision.md` after five review rounds of the unmerged
`build-step-1785890195` branch failed to converge: Step 47 keeps the migrator/engine with a decided
three-case preserve-drift policy and merges alone (build resumes from the branch, restoring the two
round-5-changed files to `5ef1045`), while new Step 47b — off the Step 48→50 critical path — owns
the containment gate's hardening (differential corpus + content-identity tripwire; AST rewrite
deferred with a named trigger). 440 tests across seven suites. (Step 45 also surfaced #69: the Claude-profile `SKILL.md`
frontmatter emits `description`/`argument` unquoted, so a colon-bearing value fails Copilot's YAML
parse — a bounded builder defect, does not block the cutover. #87 fixed `/repo-sync`'s hardcoded
default branch in minted issue-body links; its data-repair half is done for #56–#82, while #1–#37
still point at a plan doc that is not on any pushed branch of `aberson/coding-root` — a publishing
gap in that repo, not a branch-name defect.)

Phases 1–6 delivered the canonical `skills/` source tree, the provider-neutral router, and the
distribution, installer, and release tooling. Plan:
`documentation/host-native-discovery-cutover-plan.md` (it supersedes the unexecuted Step 41
acceptance intent of `documentation/provider-neutral-skill-mesh-plan.md`). Phase 8 —
`documentation/provider-expansion-plan.md` (Steps 51–61, Gemini + local lanes) — is PLANNED and
gated on Phase 7's cutover. It has been through `/plan-expedite` (commit 5f3d9af): plan-review autofix
resolved both authoring blockers (Step 55 re-scoped around `tools/gen_manifest.py`'s `LOCAL_CAPABLE`;
Step 54 given a fork-on-failure provider-set obligation), plan-wrap returned READY (0 blockers, 0 gaps),
and repo-sync minted umbrella #70 plus step issues #71–#82 — every step now carries `**Type:**` and a
populated `**Issue:**`. The plan is build-ready; the only thing outstanding is the Phase 7 Step 50 gate.

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
