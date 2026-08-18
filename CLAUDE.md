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
| Skill sources | Markdown — `skills/<name>/core.md` + `providers/{claude,gpt,codex}.md` |
| Manifest / config | JSON — `config/skill-manifest.json` (authoritative skill inventory) |
| Build / install / release tooling | Windows PowerShell 5.1 floor (`powershell`) — `tools/*.ps1` |
| Manifest + release checks | Python 3 — `tools/gen_manifest.py`, `tools/release_checks.py` |
| Tests | pytest — 7 suites under `tests/` plus 3 root-only test roots; the DONE gate is the repo-root `python -m pytest` (see Key commands) |
| Lint / typecheck | **Not configured** (deliberate — see Key commands) |

## Key commands

Run from the repository root. **Commands are spelled `powershell`, not `pwsh`** — PowerShell 7 is
not installed on this machine, and every tool invocation spelled `pwsh` fails with `The term 'pwsh'
is not recognized`. Windows PowerShell 5.1 is the floor all `.ps1` tooling targets (ASCII-only, no
BOM) and the executable the test suites shell out to. (`documentation/architecture.md` §8 spells the
same commands with the PowerShell 7 name; that is the same command in the other spelling.)

**DONE gate — the full suite is the repo-root invocation, with no path argument.** It is slow
(the release, distribution, and smoke suites shell out to PowerShell once or more per test);
`documentation/phase-75-baseline.md` owns the measured wall clock. Run it from the repository
root, and report its real summary line:

```
python -m pytest
```

A path argument narrows collection. `python -m pytest tests/` reaches only the seven suites
under `tests/`; it never collects the three root-only test roots — `_shared/`,
`skill-iterate/scripts/`, and `skill-eval-setup/scripts/` — so it cannot see a regression
there. Those roots are real production code (the shared verdict engine and the two
calibration/eval script packages), so a `tests/`-only run is an iteration gate, never the
gate that flips a step or a phase DONE.

Fast iteration gates — use these while developing, never as the DONE gate:

```
python -m pytest tests/
```

```
python -m pytest tests/package-integrity
```

Measured collected / passed / failed / skipped counts for both invocations, and the date
they were measured, are owned by `documentation/phase-75-baseline.md`. That file is the
single source; this one deliberately restates no numbers.

Build host distributions (writes `dist/`, which is gitignored and never committed):

```
powershell -File tools/build-distributions.ps1 -Provider claude
powershell -File tools/build-distributions.ps1 -Provider gpt
```

Install one host profile into a consumer home:

```
powershell -File tools/install-skill-mesh.ps1 -Provider claude -Home <install-home>
powershell -File tools/install-skill-mesh.ps1 -Provider gpt    -Home <install-home>
```

Release — stage from `git ls-files`, build, run the integrity check inside the staged tree, then
SHA-256 every file under the generated `dist/`:

```
powershell -File tools/release.ps1
```

Regenerate the manifest. **Hermetic since Step 67** — it reads nothing outside this repository, takes
no argument and no environment variable, and reproduces `config/skill-manifest.json` plus
`tests/package-integrity/expected_inventory.json` exactly. Re-run only when one of the authoritative
constants in `tools/gen_manifest.py` changes:

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
                        the seven vendored workspace references (Step 66 — cores cite them
                        as `<repo>/_shared/<leaf>`, repointed to `../_shared/<leaf>` at
                        emit time), and the README's light/dark SVG diagrams
config/                 skill-manifest.json (inventory + eligibility), model-mapping.json,
                        model-tier-map.json
documentation/          architecture.md (the contract), host-discovery.md, migration.md,
                        coding-root-cutover-handoff.md (the operator cutover sequence),
                        providers/, troubleshooting.md, and the phase plans
runtime/                skill-router.ps1, path-guard.ps1, providers/, telemetry/
tools/                  build-distributions, install-skill-mesh, inspect-host-install, release,
                        release_checks, gen_manifest, gen_skill_tree, gen-router-shim, provenance,
                        migrate-legacy-install + skill-mesh-transaction (the reversible migrator
                        and its shared journaled engine), probe-codex-skills (read-only codex
                        bring-up probe), skill-mesh-discovery (sole owner of the
                        provider-to-discovery-root map)
tests/                  calibration, distributions, package-integrity, release, router,
                        smoke, telemetry (+ fixtures/)
```

## Architecture summary

- **One behavior contract per skill.** `skills/<name>/core.md` is provider-independent; each
  `providers/<host>.md` wrapper loads the core in full and maps host abstractions onto it. A wrapper
  may never weaken a gate defined in the core. 5 skills additionally carry a `providers/codex.md`
  adapter (the Phase CP pilot: task-handoff, user-orient, lesson-harvest, plan-review,
  session-wrap) — codex capability is ADDITIVE on a portable record, never a third status, so the
  portable/native counts below keep their exact meaning. 47 skills are portable (both adapters); 3 are
  provider-native Claude-only (`claude-oauth-auth`, `context-slim`, `judge-motion`) and carry
  `core: null` in the manifest.
- **Manifest-driven build.** `tools/build-distributions.ps1` reads `config/skill-manifest.json` and
  emits host-native `SKILL.md` discovery trees into `dist/claude` and `dist/gpt`.
- **Install binds exactly one profile** into a consumer home — Claude at `<home>/.claude/skills/`,
  codex at `<home>/.agents/skills/`, GPT at `<home>/.github/skills/` (a real GitHub Copilot CLI discovery root; the project-relative
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

## Current authority

`plan.md` is the only mutable execution-status and evidence index. The approved recovery
contract is `documentation/skill-mesh-recovery-plan.md`; the product boundary is
`documentation/product-charter.md`. Do not copy volatile step status into this file.

Read `plan.md` before acting. It names the current phase, gate, accepted contract identity,
evidence locators, and deferred tracks. Do not infer current execution state from historical
plans or status prose.

Historical implementation detail lives in `documentation/host-native-discovery-cutover-plan.md`,
the Phase 7.5 status documents, and `documentation/step-4-checkpoint-2026-08-13.md`.

## Environment requirements

- **Windows with PowerShell.** All build, install, and release tooling is `.ps1`; the distribution
  and release test suites shell out to it. There is no POSIX path.
- **Python 3 with pytest** on `PATH` (or an activated project venv). No `pyproject.toml`, no
  dependency lockfile, and no pinned interpreter is committed — supply your own.
- **PyYAML** (`pip install pyyaml`) — the only third-party Python dependency, and test-only.
  The frontmatter gate (`tests/package-integrity/frontmatter_contract.py`) needs a *real*
  strict parser, because the consumer it models is one (Copilot CLI's scan of the discovery
  roots); a hand-rolled scanner would only be this repository's *model* of YAML. Without
  PyYAML that gate **fails loudly and by name**: 20 red tests across the two files that grade
  frontmatter, each message naming the dependency and pointing back at this section, plus the
  5 `tests/release` cases that assert `release.ps1` exits 0 — it re-runs the integrity check
  inside the staged tree, so a release genuinely cannot be certified without the parser. The
  gate does not skip (a skipped gate is a false green on the one machine nobody checked) and
  it does not abort collection (that would erase every other test's verdict): measured at
  1024 collected, 25 failed, **998 passed, 1 skipped** — the same single skip as a healthy run.
- **git** — release staging is `git ls-files`-driven and fails outside a working tree.
- **`gh` CLI** for issue/PR work.
- **GitHub Copilot CLI, signed in via `gh auth login`**, for any GPT-side host acceptance.
  Copilot subscription auth is the transport — **no `OPENAI_API_KEY` is used or needed**.
- Writing this file: keep absolute user paths out of every committed file. This is a public
  repository and `tests/package-integrity/test_manifest_contract.py` gates it.
