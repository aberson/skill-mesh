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
                        coding-root-cutover-handoff.md (the operator cutover sequence),
                        providers/, troubleshooting.md, and the phase plans
runtime/                skill-router.ps1, path-guard.ps1, providers/, telemetry/
tools/                  build-distributions, install-skill-mesh, inspect-host-install, release,
                        release_checks, gen_manifest, gen_skill_tree, gen-router-shim, provenance,
                        migrate-legacy-install + skill-mesh-transaction (the reversible migrator
                        and its shared journaled engine), skill-mesh-discovery (sole owner of the
                        provider-to-discovery-root map)
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

**Phase 7 — Host-Native Discovery & Consumer Cutover, complete.** Steps 42–50 are DONE; Step 47b
remains the separately scheduled, off-critical-path containment-gate hardening follow-up. Steps 42–46:
the host-loading authority map (locked by 17 package-integrity tests); the live
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
back. **Step 47 (reversible legacy-install migration, #60) is DONE** — merged `29d73dc` on
2026-08-05. It had been re-scoped the same day by `documentation/step-47-decomposition-decision.md`
after five review rounds of the unmerged `build-step-1785890195` branch failed to converge; the
re-scoped step restored the two round-5-changed files to `5ef1045`, implemented the decided
three-case preserve-drift policy, and merged alone. Its ONE bounded confirming round returned
**0 Block findings across all six lenses** (the Block trend across rounds 1–6 was 4 → 5 → 4 → 1 → 6
→ 0); all 6 Nits it did raise were fixed pre-merge. The load-bearing correction: a `rolled_back`
status now claims only what it can prove — *every byte this tool mutated was restored* — because
`preserve` actions carry no backup payload by design, so a consumer editing their own preserved
skill during downtime gets an advisory naming the path and both hashes rather than a false "the
consumer home is MIXED" claim that invited restoring a stale backup over their newer bytes.
**Step 48 (#61) is also DONE** — merged `f377c54` on 2026-08-06. It produced
`documentation/coding-root-cutover-handoff.md`, the copy-pasteable sequence Steps 49–50 execute, plus
a structure gate (`tests/package-integrity/test_cutover_handoff.py`) that fails on an omitted **or
mis-ordered** required unit and resolves every backticked command and path token — closing a real gap,
since markdown links were already checked but command tokens were checked nowhere. Its four-lens
review caught **two operator-safety Blocks**, both fixed pre-merge: the handoff sent an operator who
hit exit 3 into `-Resume`/`-Rollback`, which both *refuse* `failed_incomplete` (unresolved AND
terminal) — two dead ends and a blocked home; and the untracked-deletion fallback destroyed the
managed legacy GPT tree while claiming backups that provably do not cover it.

**Steps 49 and 50 are complete.** Step 49 recorded clean temporary-home host acceptance and rollback.
Step 50 satisfied the verified-parking gate, installed 50 Claude and 47 GPT generated entries in the
live consumer, confirmed both native hosts resolved the representative `plan-review` profile from their
own discovery root, and preserved the legacy `-Model` router path through the generated compatibility
shim. The external backup is retained; the coding-root-owned cutover branch retires 47 managed legacy GPT
entries, preserves the consumer-only `goblin-sweep` tree by hash, and carries the GPT `judge-ui`
calibration note forward byte-for-byte. **Step 47b** remains pending and off the completed cutover path.
Current collected / passed / skipped counts for both the repo-root DONE gate and the
`tests/` iteration gate live in `documentation/phase-75-baseline.md` (the one owner) — this
section deliberately restates none of them, because a count copied into a status paragraph
is a count that drifts.

(Step 45 also surfaced #69: the Claude-profile `SKILL.md` frontmatter emits `description`/`argument`
unquoted, so a colon-bearing value fails Copilot's YAML parse — a bounded builder defect, does not
block the cutover. #87 fixed `/repo-sync`'s hardcoded default branch in minted issue-body links; its
data-repair half is done for #56–#82, while #1–#37 still point at a plan doc that is not on any pushed
branch of `aberson/coding-root` — a publishing gap in that repo, not a branch-name defect.)

Phases 1–6 delivered the canonical `skills/` source tree, the provider-neutral router, and the
distribution, installer, and release tooling. Plan:
`documentation/host-native-discovery-cutover-plan.md` (it supersedes the unexecuted Step 41
acceptance intent of `documentation/provider-neutral-skill-mesh-plan.md`). Phase 8 —
`documentation/provider-expansion-plan.md` (Steps 51–61, Gemini + local lanes) — is BUILD-READY;
the Phase 7 cutover prerequisite is satisfied. It has been through `/plan-expedite` (commit 5f3d9af): plan-review autofix
resolved both authoring blockers (Step 55 re-scoped around `tools/gen_manifest.py`'s `LOCAL_CAPABLE`;
Step 54 given a fork-on-failure provider-set obligation), plan-wrap returned READY (0 blockers, 0 gaps),
and repo-sync minted umbrella #70 plus step issues #71–#82 — every step now carries `**Type:**` and a
populated `**Issue:**`. The plan is ready for its next unblocked step.

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
