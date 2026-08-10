# skill-mesh Architecture

Provider-neutral package and host-adapter contract for the skill-mesh product.
This document is the design authority for the migration executed in Steps 33-41 of
`documentation/provider-neutral-skill-mesh-plan.md`. It is locked at Step 33: it
names one canonical location for every core, adapter, mapping, test, and doc;
distinguishes host-native binding from runtime auto-detection; carries a migration
entry for every skill; and records the exact build/install/test commands.

Nothing here depends on a host or provider being present. The public
`aberson/skill-mesh` repository is the single canonical source; Claude and GPT
hosts receive *generated* compatibility layouts built from this source.

## 1. Vocabulary

| Term | Meaning |
|---|---|
| **core** | Provider-independent workflow behavior for one skill. One per portable skill. |
| **adapter** | Thin mapping of a core to one host's tool surface (`providers/claude.md`, `providers/gpt.md`). |
| **discovery layout** | Host-specific directory/filename shape a host scans to find a skill (generated, not committed). |
| **shim** | Thin backward-compatible launcher that delegates to a canonical file. |
| **transport** | Authenticated API or host-native channel used to execute a provider model. |
| **calibration** | Existing deterministic/rubric comparison that checks adapter parity. |
| **portable skill** | Skill with a neutral core plus Claude and GPT adapters. 47 total. |
| **provider-native skill** | Skill supported on exactly one host; no neutral core. 3 total. |

`<name>` and `<skill>` in every path template mean the same stable kebab-case
`skills[].name` value from `config/skill-manifest.json`.

## 2. Canonical directory contract

Every artifact class has exactly one canonical home in this repository. Generated
host distributions (`dist/`) and release staging output (`release-stage/`) are
uncommitted build artifacts. The 46 legacy top-level `<skill>/SKILL.md` packages
committed at the repository root are non-canonical compatibility content in a
deprecation window (see `migration.md`), not canonical sources.

| Artifact class | Canonical location | Owner / notes |
|---|---|---|
| Skill core (portable) | `skills/<name>/core.md` | One per portable skill; `null` in the manifest for provider-native skills. |
| Claude adapter | `skills/<name>/providers/claude.md` | Thin host adapter. Self-contained for provider-native skills. |
| GPT adapter | `skills/<name>/providers/gpt.md` | Thin host adapter; absent for provider-native skills. |
| Shared prose assets | `_shared/` (repo root) | Cross-skill cores/prose referenced by multiple skills. The manifest declares `skills/_shared/` as the eventual canonical home; that directory does not exist yet, so today's references resolve to the repo-root tree. The divergence is deliberate and locked by `tests/package-integrity/test_skill_tree.py::test_shared_dest_divergence_is_intentional`. |
| Skill manifest | `config/skill-manifest.json` | Single source for distribution, install, integrity, and README counts. |
| Model capability mapping | `config/model-mapping.json` | Per-skill provider/local capability booleans (Step 34). |
| Model tier peer mapping | `config/model-tier-map.json` | Claude-tier to GPT-peer mapping (Step 34). |
| Runtime router | `runtime/skill-router.ps1` | Provider-neutral CLI router (Step 34). |
| Provider transport adapters | `runtime/providers/` | Host-metadata and transport selection (Step 37). |
| Telemetry | `runtime/telemetry/` | Neutral telemetry writer/summary (Step 34). |
| Distribution builder | `tools/build-distributions.ps1` | Generates `dist/claude/`, `dist/gpt/` (Step 36). |
| Installer | `tools/install-skill-mesh.ps1` | Installs a host profile without making canonical files host-owned (Step 36). |
| Host-install inspector | `tools/inspect-host-install.ps1` | Read-only `HostInstallReport` (text or JSON, `schema_version` 1): workspace instruction files, Claude/GPT discovery roots, provenance ownership, link type, ledger state, router version, and legacy shadowing (Step 46). |
| Release/export command | `tools/release.ps1` | Reproducible release staging + checksums (Step 38). |
| Package-integrity tests | `tests/package-integrity/` | Manifest/link/drift/claim gates: `test_manifest_contract.py`, `test_release_gates.py`, `test_host_discovery.py`, `test_skill_tree.py` (99 tests). |
| Router tests | `tests/router/` | Provider-selection and transport tests (Step 34/37). |
| Calibration tests | `tests/calibration/` | Neutral home for the existing pytest calibration suite (Step 34). |
| Telemetry tests | `tests/telemetry/` | Neutral telemetry tests (Step 34). |
| Distribution tests | `tests/distributions/` | Install/discovery/idempotence tests (Step 36). |
| Smoke tests + fixtures | `tests/smoke/`, `tests/fixtures/` | Cross-provider workflow smoke (Step 40). |
| Release-script tests | `tests/release/` | End-to-end `tools/release.ps1` behavior against throwaway repos (Step 38). |
| Architecture doc | `documentation/architecture.md` | This document. |
| Provider guides | `documentation/providers/` | Per-provider auth, capabilities, divergences, install. |
| Host-loading authority map | `documentation/host-discovery.md` | Instruction injection vs. native discovery vs. router dispatch (Step 42). |
| Migration notes | `documentation/migration.md` | Operator-facing migration narrative (Step 39). |
| Troubleshooting | `documentation/troubleshooting.md` | Provider/transport diagnostics (Step 37). |
| Generated Claude layout | `dist/claude/` | Build artifact only; never committed. |
| Generated GPT layout | `dist/gpt/` | Build artifact only; never committed. |
| Path guard | `runtime/path-guard.ps1` | Canonical real-path resolution shared by the router and release tooling. |
| Manifest generator | `tools/gen_manifest.py` | Generates `config/skill-manifest.json` + `tests/package-integrity/expected_inventory.json`. |
| Skill-tree generator | `tools/gen_skill_tree.py` | Generates the migrated `skills/` tree and its inventory. |
| Release checker | `tools/release_checks.py` | Static release-gate logic used by `tests/package-integrity/test_release_gates.py`. |
| Router shim generator | `tools/gen-router-shim.ps1` | Generates backward-compatible launcher shims for retired router paths. |
| Install provenance | `tools/skill-mesh-provenance.ps1` | Install-provenance stamping shared by the builder and installer. |

Rule: if an artifact does not map to exactly one row above, the manifest or this
table is wrong. There is no second canonical copy of any core, adapter, mapping,
test, or doc.

## 3. Skill package shape

Portable skill:

```
skills/<name>/
  core.md                 # neutral workflow contract (single source of behavior)
  providers/
    claude.md             # thin Claude adapter
    gpt.md                # thin GPT/Copilot adapter
```

Provider-native skill (Claude-only exclusion):

```
skills/<name>/
  providers/
    claude.md             # self-contained; no neutral core, no gpt.md
```

`core` is `null` in the manifest **only** for provider-native skills. Host-facing
filenames (`SKILL.md`, `SKILL-claude.md`, `SKILL-gpt.md`) are generated discovery
outputs under `dist/`; they are never canonical sources. The 46 legacy top-level
`<skill>/SKILL.md` files committed at the repository root are pre-migration
hand-authored content retained for the deprecation window.

## 4. Host capability matrix

`capabilities` uses a closed vocabulary with an explicit meaning per term
(`capability_semantics` in the manifest). Assignment is grounded in evidence from
each skill's legacy contract, not inferred from a single shared wrapper line.

**Vocabulary semantics**

- `filesystem` — the skill reads and/or writes workspace files as an intrinsic
  part of its contract (plan docs, state files, reports, evals, or source edits).
  This is true for every skill in the package; it does **not** mean "mentions a
  file", it means workspace file I/O is part of the skill's job.
- `sub-agent` — the skill's core workflow **requires dispatching one or more
  isolated fresh-context sub-agents**: the host Agent/Task primitive, a Workflow
  `agent()` call, or provider action children (e.g. parallel judge/reviewer
  fan-out, or a separate vision-judge). A **named-skill dispatch** (`/other-skill`)
  is the host's skill-dispatch primitive and does **not** count as a sub-agent
  requirement. A local text-only model cannot satisfy this.
- `vision` — the skill requires a native image/vision capability (screenshot or
  filmstrip judging).
- **Invariant:** any skill declaring `vision` or `sub-agent` has
  `local_capable: false`. The text-only local path admits neither capability.
  (Enforced by `tests/package-integrity/test_manifest_contract.py`.)

| Capability | Count | Skills |
|---|---|---|
| `filesystem` | 50 | all skills |
| `sub-agent` | 16 | build-step, context-slim, goblin-do, goblin-suggest, judge-motion, judge-ui, research-prospect, review-deep, review-gauntlet, skill-evolve, skill-iterate, test-prune, tier-escalate, tier-offload, user-brainstorm, user-learn |
| `vision` | 2 | judge-ui, judge-motion |

The `sub-agent` set is derived by auditing all 50 legacy contracts for explicit
isolated-agent dispatch. Representative evidence (legacy `SKILL-core.md` /
`SKILL.md`): build-step "Spawn a sub-agent" + "Step 6 — Spawn reviewer agents";
context-slim "Spawn three parallel subagents using the Agent tool"; goblin-do runs
`/build-step` via a Workflow `agent()` call; goblin-suggest "fan out `--n-judges`
judge agent calls IN PARALLEL"; judge-motion "separate sub-agent per transition";
judge-ui "dispatches an independent vision-judge sub-agent"; research-prospect
"Fan out parallel Explore agents"; review-deep "spawns six fresh-context
sub-agents, one per lens"; review-gauntlet "one fresh-context reviewer invocation
for each lens"; skill-iterate "Dispatch ONE sub-agent" via a fresh-context task;
test-prune "dispatch this phase as parallel Explore agents"; user-brainstorm /
user-learn "one background sub-agent per file". Skills that only spawn a *named
skill* (e.g. build-phase → `/build-step`, build-queue → `/build-phase`,
plan-expedite chaining) are **not** marked `sub-agent`.

`local_capable: true` (24 skills) marks the text-only `code-30b` both-clouds-down
fallback path; it is authoritative hard data copied from the legacy mapping table
(`model-mapping.md`, the `local-capable=Y` rows).

## 5. Host binding vs. runtime auto-detection

Two independent mechanisms select which adapter executes. Binding is primary;
detection is a bounded convenience.

### 5.1 Host-native binding (primary)

Normal installation writes exactly one provider adapter into each host's discovery
layout. A Claude Code install receives Claude adapters; a GPT/Copilot install
receives GPT adapters. When a host discovers a skill through its own scan, the
adapter is already the correct one — no runtime provider decision occurs. This
removes the current failure mode where a GPT session can discover the Claude
compatibility launcher before any router runs.

Binding is decided at install time by `tools/install-skill-mesh.ps1 -Provider
claude|gpt` and recorded in the generated discovery layout. Binding never rewrites
canonical files; it emits a generated tree under `dist/<profile>/`.

### 5.2 Runtime auto-detection (secondary, via the router)

Explicit cross-provider routing runs through `runtime/skill-router.ps1`:

- `-Provider claude|gpt|local` — explicit selection; always honored.
- `-Provider auto` — the default. Uses **trustworthy host metadata only** (§5.3)
  to pick a provider. If metadata is absent or ambiguous, it **fails with an
  actionable selection message and exit code 2**; it never silently defaults to
  Claude.
- `-Model <value>` — deprecated compatibility alias retained through the migration;
  maps onto `-Provider` and emits a deprecation notice.

Auto-detection is explicitly **not** a claim of universal active-model detection:
on hosts that expose neither provider metadata nor separate provider-specific
install surfaces, `auto` errors rather than guesses.

Provider choice and transport authentication are separate axes: selecting GPT does
not imply `OPENAI_API_KEY`, and Claude host-native execution does not require
`ANTHROPIC_API_KEY`. See `documentation/providers/`.

### 5.3 Approved host-metadata sources

`-Provider auto` may consult **only explicit host-identity environment variables**
set by the host itself. These are the complete approved set; `runtime/providers/`
implements and `tests/router/` tests exactly these. The machine-readable copy is `host_metadata_sources` in
`config/skill-manifest.json`.

| Provider | Approved marker variable(s) | Present when |
|---|---|---|
| Claude | `CLAUDECODE` (`=1`), `CLAUDE_CODE_ENTRYPOINT` (non-empty) | Claude Code sets either marker |
| GPT/Copilot | `COPILOT_CLI` (non-empty), `COPILOT_AGENT_SESSION_ID` (non-empty) | GitHub Copilot CLI sets either marker |

A provider is "detected" when **any** of its marker variables is set to a non-empty
value (and, for `CLAUDECODE`, equal to `1`). These names are grounded in the real
host environments: Claude Code exports `CLAUDECODE`/`CLAUDE_CODE_ENTRYPOINT`, and
the GitHub Copilot CLI exports `COPILOT_CLI`/`COPILOT_AGENT_SESSION_ID`.

**Explicitly excluded (not host-identity):** `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, `GITHUB_TOKEN`. A credential can be
exported in any shell and identifies a *transport*, not the *active host* — using
it for host selection would conflate provider choice with authentication (§5.2).
No executable-name guessing (e.g. inspecting the parent process name) is permitted.

**Precedence and edge behavior (testable):**

1. **Exactly one** provider's markers present → select that provider.
2. **Both** providers' markers present → **ambiguous**: error with an actionable
   message and **exit code 2**. Never default to Claude.
3. **Neither** present → **unset/unsupported**: error with **exit code 2**
   instructing the operator to pass `-Provider claude|gpt` explicitly.

## 6. CLI compatibility contract

| Invocation | Behavior | Status |
|---|---|---|
| `skill-router.ps1 -Provider auto <skill>` | Bind via trustworthy metadata; error on ambiguity | new default |
| `skill-router.ps1 -Provider claude <skill>` | Force Claude adapter | supported |
| `skill-router.ps1 -Provider gpt <skill>` | Force GPT adapter | supported |
| `skill-router.ps1 -Provider local <skill>` | Force local `code-30b` path (local_capable skills only) | supported |
| `skill-router.ps1 -Model claude\|gpt <skill>` | Legacy alias → `-Provider`; emits deprecation notice | deprecated, retained |
| host-native discovery (no router) | Loads the bound adapter directly | primary path |

Exit code `2` and fallback disclosure semantics from the existing router are
preserved when the neutral router lands in Step 34; this table is the contract
those steps must satisfy.

## 7. Migration manifest

Every skill has a machine-readable migration entry in `config/skill-manifest.json`
(the `migration` + `support_assets` blocks per skill, plus top-level
`global_support_assets`), covering **all 47 portable skills plus the 3
Claude-native exclusions (50 total)**.

**Migration root.** All `source` / `legacy_*` paths are relative to **coding-root**
(`aberson/coding-root` — the operator's `dev` checkout), READ-ONLY during Steps
33-40. The `.claude/...` trees **and** `documentation/multi-model/...` are both
direct children of coding-root; `documentation/multi-model` is a **sibling of
`.claude`, not under it**. (This resolves the earlier root contradiction: paths are
coding-root-relative, so `.claude/skills/...` and `documentation/multi-model/...`
are both valid siblings.)

### 7.1 Per-skill mapping — launcher vs. adapter are distinct

The legacy Claude tree ships **two** files per portable skill: a thin
compatibility **launcher** (`SKILL.md`, which only delegates) and the substantive
**adapter** (`SKILL-claude.md`, the real provider entry point). The manifest
records them separately so migration copies the substantive adapter, not the
launcher. Provider-native skills have no launcher/adapter split — their single
`SKILL.md` **is** the substantive skill.

Portable skill `<name>` (`migration` block):

| Manifest field | Legacy source (coding-root-relative, read-only) | Canonical target |
|---|---|---|
| `legacy_core` | `.claude/skills-gpt/<name>/SKILL-core.md` | `skills/<name>/core.md` |
| `legacy_claude_adapter` | `.claude/skills/<name>/SKILL-claude.md` | `skills/<name>/providers/claude.md` |
| `legacy_claude_launcher` | `.claude/skills/<name>/SKILL.md` (compat launcher) | regenerated as a `dist/` shim; **not** a canonical source |
| `legacy_gpt` | `.claude/skills-gpt/<name>/SKILL-gpt.md` | `skills/<name>/providers/gpt.md` |

Provider-native skill `<name>` (claude-oauth-auth, context-slim, judge-motion):

| Manifest field | Legacy source (read-only) | Canonical target |
|---|---|---|
| `legacy_claude_adapter` | `.claude/skills/<name>/SKILL.md` | `skills/<name>/providers/claude.md` |
| `legacy_core`, `legacy_claude_launcher`, `legacy_gpt` | `null` (truthfully none) | — (`core: null`, no gpt adapter) |

### 7.2 Support-asset ownership (machine-readable)

Skill-local scripts, workflows, fixtures, and eval suites shipped in the legacy
source are enumerated per skill in `support_assets` (each `{source, dest}` pair).
Canonical ownership: a skill-local asset at `.claude/skills/<name>/<rel>` (or
`.claude/skills-gpt/<name>/<rel>`) is owned by that skill and lands at
`skills/<name>/<rel>`. Representative examples:

| Legacy source (read-only) | Canonical target | Owner |
|---|---|---|
| `.claude/skills/<name>/evals/` | `skills/<name>/evals/` | per-skill eval suite (most skills) |
| `.claude/skills/build-step/scripts/` | `skills/build-step/scripts/` | build-step |
| `.claude/skills/goblin-do/goblin_do.workflow.js` | `skills/goblin-do/goblin_do.workflow.js` | goblin-do |
| `.claude/skills/judge-motion/{package.json,package-lock.json,scripts/,fixtures/,tests/}` | `skills/judge-motion/...` | judge-motion |
| `.claude/skills/plan-expedite/test-fixtures/` | `skills/plan-expedite/test-fixtures/` | plan-expedite |
| `.claude/skills/plan-redline/reference-proposal.html` | `skills/plan-redline/reference-proposal.html` | plan-redline |
| `.claude/skills/tier-offload/{sample-*,test_*.py}` | `skills/tier-offload/...` | tier-offload |
| `.claude/skills-gpt/judge-ui/calibration-notes.md` | `skills/judge-ui/calibration-notes.md` | judge-ui (from the GPT tree) |

Build-output and cache directories are **never** migrated: `node_modules/`,
`.pytest_cache/`, `__pycache__/`, `tmp/`, and `.judge-motion/` are excluded.

Global (cross-skill) assets are recorded in top-level `global_support_assets`:

| Legacy source (coding-root-relative) | Canonical target |
|---|---|
| `.claude/lib/skill-router.ps1` | `runtime/skill-router.ps1` |
| `.claude/lib/telemetry/` | `runtime/telemetry/` |
| `.claude/lib/calibration/` | `tests/calibration/` |
| `.claude/references/model-mapping.md` | `config/model-mapping.json` (transformed) |
| `.claude/references/model-tier-map.json` | `config/model-tier-map.json` |
| `.claude/skills/_shared/` | `skills/_shared/` |
| `documentation/multi-model/` | `documentation/providers/` + `documentation/architecture.md` |

Only `.claude/skills/_shared/` exists in the legacy source — there is **no**
`.claude/skills-gpt/_shared/` tree, so the shared cores/graders migrate from the
single `skills/_shared` location.

### 7.3 Provider-native exclusions (explicit, not stubbed)

| Skill | Reason (from legacy mapping notes) |
|---|---|
| `claude-oauth-auth` | Claude-native — Claude OAuth flow; excluded from GPT porting. |
| `context-slim` | Claude-native — Claude Code context management; excluded from GPT porting. |
| `judge-motion` | Claude-native — depends on Claude-native motion/vision capture; excluded from GPT porting. |

These three receive no misleading GPT stubs. The manifest records `core: null`
and a single truthful `claude` adapter.

## 8. Build, install, and test commands

All commands are PowerShell on Windows, run from the **skill-mesh repository root**
(the checkout of `aberson/skill-mesh`; `Set-Location` there first). Commands whose
target files land in a later step are marked with the step that introduced them;
every one of them exists in the repository today. No absolute private path is embedded:
the pinned interpreter and the legacy source root are supplied by the environment.

### 8.1 Build (distribution generation)

```powershell
pwsh -File tools\build-distributions.ps1 -Provider claude
pwsh -File tools\build-distributions.ps1 -Provider gpt
```

Generates `dist\claude\` and `dist\gpt\` from `config\skill-manifest.json`. Output
is never committed.

### 8.2 Install (host profile)

```powershell
pwsh -File tools\install-skill-mesh.ps1 -Provider claude -Home <host-skills-root>
pwsh -File tools\install-skill-mesh.ps1 -Provider gpt    -Home <host-skills-root>
```

Each profile lands in its own host-native discovery root under `-Home`: Claude at
`<host-skills-root>/.claude/skills/<skill>/`, GPT at
`<host-skills-root>/.github/skills/<skill>/` — a real GitHub Copilot CLI discovery
root, whose `SKILL.md` leads with a YAML `name`/`description` frontmatter block.
The install-target table and the full set of Copilot discovery roots are owned by
[`host-discovery.md`](host-discovery.md).

### 8.3 Test

`python` below is the repository's selected interpreter (activate the project venv,
or substitute the pinned interpreter path via your own environment — do not hardcode
a private absolute path).

**The DONE gate is the repo-root invocation.** Run from the repository root with no
path argument, so collection reaches the seven suites under `tests` *and* the three
test roots a `tests`-scoped run never touches — `_shared`, `skill-iterate/scripts`,
and `skill-eval-setup/scripts`, all of which hold production modules this project
edits:

```powershell
python -m pytest
```

A path-scoped run is a fast iteration gate, never the gate that flips a step or a
phase DONE — it cannot observe a regression in the root-only roots. The measured
collected / passed / failed / skipped counts for both invocations, and the date they
were measured, are owned by [`phase-75-baseline.md`](phase-75-baseline.md); it is the
single source and no other document restates them.

Package-integrity contract gate — fast iteration subset:

```powershell
python -m pytest tests\package-integrity
```

Baseline calibration against the READ-ONLY legacy source (historical; `tests/calibration` is now the live suite).
The legacy source root is supplied via the `SKILL_MESH_LEGACY_SOURCE` environment
variable (the READ-ONLY coding-root checkout), never a hardcoded private path:

```powershell
python -m pytest $env:SKILL_MESH_LEGACY_SOURCE\.claude\lib\calibration\test_calibrate.py
```

Calibration suite — fast iteration subset:

```powershell
python -m pytest tests\calibration
```

### 8.4 Lint / typecheck

**Not configured.** The repository has no lint command and no typecheck command.
Do not invent one. pytest is the only automated gate: the seven suites under `tests`
(`tests/router`, `tests/calibration`, `tests/package-integrity`, `tests/distributions`,
`tests/release`, `tests/telemetry`, `tests/smoke`) plus the three root-only test roots
described in section 8.3, all collected by the repo-root `python -m pytest`. Per-suite
and total counts are NOT restated here -- they live in
[`phase-75-baseline.md`](phase-75-baseline.md), which is the one owner of the measured
numbers. An earlier revision of this paragraph attributed a path-scoped total to the
repo-root command; that is the drift the single-owner rule exists to stop.

### 8.5 Regenerating the manifest

`config\skill-manifest.json` and `tests\package-integrity\expected_inventory.json`
are generated from the authoritative constants + a scan of the READ-ONLY legacy
source by `tools\gen_manifest.py`. Regenerate only when the legacy source or those
constants change; the source root is supplied by the environment (no private path
committed):

```powershell
$env:SKILL_MESH_LEGACY_SOURCE = "<coding-root>"
python tools\gen_manifest.py
```

### 8.6 Release (staging, integrity gate, checksums)

```powershell
pwsh -File tools\release.ps1
```

Four phases. **Stage**: enumerates `SourceRoot`'s git-**tracked** files
(`git ls-files`) and copies exactly those paths into `release-stage\`
(gitignored, never committed) — a release is only committed content, so this
is authoritative and can never leak an untracked scratch file, local note, or
another worktree's stray file into the artifact (never a hand-maintained
denylist). **Build**: invokes the STAGED `tools\build-distributions.ps1`
(never the source copy), producing `release-stage\dist\claude` and
`\dist\gpt`. **Check**: runs `python -m pytest tests\package-integrity` FROM
WITHIN the staged tree (so the checker resolves the staged copy, not the
source tree — a release is graded by the exact same checker code as a normal
`pytest tests/` run), with `SKILL_MESH_SOURCE_ROOT` set to `SourceRoot` so the
NO TRACKED GENERATED DISTRIBUTION check runs against the source repository's
own index (which still has `.git`, unlike the — deliberately git-less —
stage) instead of self-skipping; this also means a `git add -f`'d `dist/`
path is caught even though the Build phase will already have wiped and
regenerated `dist/claude`/`dist/gpt` by the time Check runs. A failing check
aborts the release: no `CHECKSUMS.txt` is written and the staged output is
left in place for inspection. **Checksum**: SHA-256 over every file under
`release-stage\dist\` only — the deterministically-**generated** artifact a
consumer installs and verifies, never the raw source tree (whose checked-out
line endings / BOM depend on incidental `core.autocrlf` / clone history and so
are not reproducible across machines; `build-distributions.ps1` already
normalizes CRLF→LF and strips BOM when producing `dist/`, so hashing only
`dist/` reproduces byte-for-byte regardless of the source checkout's line
endings) — sorted by path, no wall-clock timestamp.

Destructive-delete safety: `StageDir` is canonicalized via
`runtime/path-guard.ps1`'s `Get-CanonicalRealPath` (resolves `..`, trailing
separators, and junctions/symlinks to one real path) and refused if it equals
`SourceRoot`'s real path or is an ANCESTOR of it; a pre-existing non-empty
`StageDir` is refused unless it carries this script's own marker file from a
prior run. `-StageDir` overrides the staging root; `-SourceRoot` is a test
seam (defaults to this repository) that must be a git working tree.

## 9. Invariants enforced by tests

`tests/package-integrity/test_manifest_contract.py` fails on any of:

- Skill count != 50, portable != 47, provider-native != 3, sub-agent != 16,
  vision != 2 (each set checked exactly against the committed
  `tests/package-integrity/expected_inventory.json` fixture — the package tests
  need no private source).
- The provider-native set != {claude-oauth-auth, context-slim, judge-motion}, or
  the exact local-capable / sub-agent / vision name sets not matching the fixture.
- A portable skill missing a `core`, a `claude` adapter, or a `gpt` adapter.
- A provider-native skill with a non-null `core` or a `gpt` adapter.
- Any core/adapter path outside `skills/<name>/` or with the wrong `<name>`.
- A `status` not in {portable, provider-native}, or a capability outside the
  declared vocabulary; missing `capability_semantics`.
- A skill declaring `vision` or `sub-agent` while `local_capable` is true.
- A `migration` block not carrying the launcher/adapter convention
  (`legacy_claude_launcher` + `legacy_claude_adapter`, truthful nulls for native
  skills), or a legacy path that is not coding-root-relative.
- A `support_assets` entry whose `dest` is not scoped to `skills/<name>/`, or a
  missing known skill-local/global asset; `global_support_assets` not matching the
  fixture.
- `host_metadata_sources` missing the approved marker variables, listing a
  credential variable as a host-identity source, or lacking the ambiguous/unset
  precedence rules; the architecture not enumerating the marker variable names.
- `counts` disagreeing with the `skills` array or the fixture.
- Any absolute private path (`?:\Users\...`) committed in the manifest, fixture,
  architecture, provider docs, generator, or this test.
- The normalized build/install/test command lines or the "lint/typecheck not
  configured" statement missing from this document.
- (Optional, source-verification) any manifest legacy/support path absent from the
  real READ-ONLY source when `SKILL_MESH_LEGACY_SOURCE` is set; skips cleanly when
  it is not.

## 10. Related documents

This document is the design authority; the following describe how to *use* the
package rather than how it is built:

| Document | Covers |
|---|---|
| [`../README.md`](../README.md) | Skill catalog, installation matrix, authentication matrix, capability/exclusion table, workflows |
| [`providers/README.md`](providers/README.md), [`providers/claude.md`](providers/claude.md), [`providers/gpt.md`](providers/gpt.md) | Per-provider host binding, transport precedence, capabilities |
| [`troubleshooting.md`](troubleshooting.md) | Provider-selection and transport-authentication failure modes |
| [`migration.md`](migration.md) | What changed from the pre-migration layout, where things live now, and the top-level `<skill>/SKILL.md` deprecation window |
| [`repo-metadata.md`](repo-metadata.md) | GitHub repository title/description/topic text, applied to `aberson/skill-mesh` |
| [`host-discovery.md`](host-discovery.md) | Host-loading authority map: instruction injection vs. native discovery vs. router dispatch |

`tests/package-integrity/test_release_gates.py` (checker logic in
`tools/release_checks.py`, Step 38) additionally fails on any of:

- A local link/reference (markdown link or HTML `<img src>` / `<source
  srcset>`) in `README.md` or `documentation/**/*.md` that does not resolve to
  a real file/dir in the release tree (LINK CHECKER).
- A manifest entry missing its required core/adapter file on disk (path
  containment-checked — a manifest `core`/adapter value that escapes the
  release root is treated as missing, never followed), a portable/
  provider-native entry with the wrong core/adapter shape, an unknown
  `status`, or a `skills/<name>/` directory on disk with no manifest entry
  (MANIFEST COMPLETENESS).
- A generated distribution tree that does not byte-for-byte match a fresh
  rebuild from the same source — a hand-edited or stale generated wrapper
  (SOURCE → DISTRIBUTION DRIFT).
- A generated wrapper resolving outside its canonical dist root, or whose
  `Canonical source:` / co-located `core.md` reference does not exist
  (PROVIDER-WRAPPER / CORE-REFERENCE).
- The README's `N/N skills are GPT-capable` claim not equal to the manifest's
  portable count (SKILL-COUNT).
- A README skill self-link (a skill name linking to its own `SKILL.md`) naming
  a skill absent from the release manifest (README-CLAIM).
- A `dist/` path tracked in git — checked against `SKILL_MESH_SOURCE_ROOT`
  when set (the real source repository during a `release.ps1` run, which
  still has `.git`) so this genuinely runs during a release rather than
  self-skipping against the git-less stage; falls back to the live repo
  otherwise (NO TRACKED GENERATED DISTRIBUTION).

`tests/release/test_release_script.py` exercises `tools/release.ps1` end to
end against throwaway git repositories (never this repository's own git
state): a clean run stages only tracked files, builds, checks, and
checksums `dist/` only; two runs over an unchanged tree reproduce an
identical `CHECKSUMS.txt`, including across a source checkout with different
line endings; an untracked working-tree file never leaks into the stage; a
`git add -f`'d `dist/` path and a planted broken README link each abort the
release with no `CHECKSUMS.txt` written; and `-StageDir` equal to, a
trailing-separator variant of, or an ancestor of `-SourceRoot` — or a
pre-existing non-empty foreign `-StageDir` — is refused without deleting
anything.
