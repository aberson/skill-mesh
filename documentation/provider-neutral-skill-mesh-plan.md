# Provider-Neutral Skill Mesh Plan

## 1. What This Feature Does

**Proposal:** `documentation/provider-neutral-skill-mesh-proposal.html`

This phase turns skill-mesh from a Claude-first workspace implementation with GPT
variants into a provider-neutral product. The public `aberson/skill-mesh`
repository becomes the canonical source for shared skill contracts, provider
adapters, routing, configuration, tests, and operator documentation. Claude and
GPT hosts receive generated compatibility layouts from that source, so normal
skill invocation selects the adapter for the active host while explicit
cross-provider routing remains available through the router. The phase also
corrects the public README, authentication guidance, repository description, and
release claims so they describe files and behavior that actually ship.

## 2. Existing Context

- The implementation currently lives in `aberson/coding-root`: Claude launchers
  are under `.claude/skills/`, GPT launchers and the shared cores are under
  `.claude/skills-gpt/`, and the router is `.claude/lib/skill-router.ps1`.
- There are 47 Claude wrappers, 47 GPT wrappers, and 47 shared cores in the
  implementation workspace. The shared core is semantically provider-neutral
  but is physically owned by the GPT-specific tree.
- The public `aberson/skill-mesh` checkout contains 46 top-level single-file
  skills and shared prose assets. It does not contain the router, provider
  wrappers, shared cores, model mappings, calibration harness, or multi-model
  guide referenced by its README.
- The router defaults `-Model` to `claude`; GPT selection is explicit. Normal
  host-native skill discovery can bypass the router entirely, so the current
  layout does not guarantee that a GPT session loads a GPT wrapper.
- GPT transport currently prefers GitHub Copilot authentication and only uses
  `OPENAI_API_KEY` as an optional direct-OpenAI fallback. The public README
  incorrectly presents `OPENAI_API_KEY` as required.
- The existing multi-model plan established parity and fallback mechanics, but
  deliberately retained a Claude-first default and `.claude`-owned layout. This
  follow-on phase changes that product boundary rather than reopening the
  completed provider-porting work.
- The current implementation uses PowerShell for routing/telemetry and Python
  pytest for calibration tests. The public repository has no declared
  install/build/lint/typecheck command surface; this phase adds repeatable
  PowerShell build/install commands and reuses the existing pytest suite rather
  than introducing a new toolchain solely for packaging.

### Repository boundary

- **Build repository:** `aberson/skill-mesh` at
  `<workspace>\skill-mesh`. Run Steps 33-40 from this repository and
  commit only to it.
- **Legacy migration source:** `aberson/coding-root` at
  `<workspace>`. Its `.claude/skills/`, `.claude/skills-gpt/`,
  `.claude/lib/`, `.claude/references/`, and `documentation/multi-model/`
  trees are read-only inputs during Steps 33-40.
- **Compatibility installation:** Step 41 installs the released package back
  into `coding-root/.claude` through the tested installer. No implementation
  step writes both repositories.
- **Plan and issues:** This plan lives in `aberson/skill-mesh`; `/repo-sync`,
  `/build-phase`, commits, and issues target `aberson/skill-mesh`.

## 3. Scope

### In scope

- Establish a provider-neutral canonical source layout in `aberson/skill-mesh`.
- Move shared cores, provider wrappers, router, mappings, calibration assets,
  and multi-model operator documentation into that canonical layout.
- Generate/install host-native Claude and GPT skill layouts from the canonical
  source without duplicating shared behavior.
- Define deterministic provider selection for host-native invocation and CLI
  routing, including explicit override and unsupported-detection behavior.
- Keep `.claude/` compatibility shims for existing Claude Code installations.
- Publish a complete, internally consistent public repository.
- Correct authentication, installation, status, and provider-support guidance.
- Add drift checks so the public package cannot again claim or link to files it
  does not ship.
- Update GitHub repository title/description after the content is released.

### Out of scope

- Rewriting the behavioral contract of all 47 skills.
- Adding a third cloud provider.
- Making the three declared Claude-native skills portable.
- Changing model quality gates or weakening existing calibration requirements.
- Replacing host-native skill discovery with a custom editor extension.
- Guaranteeing automatic model detection on hosts that expose neither provider
  metadata nor separate provider-specific installation surfaces.
- Publishing private workspace memory, project-specific adapters, credentials,
  or omitted second-brain data.

## 4. Impact Analysis

| File or area | Change Type | Reason | Verified |
|---|---|---|---|
| `skill-mesh/` | refactor | Becomes the canonical provider-neutral source and release repository | Directory inspection found 46 `SKILL.md` packages but no router or provider wrapper files |
| `skill-mesh/README.md` | refactor | Rename/reframe product, correct auth and installation, document real support | Read current title, GPT callout, router section, status, and Claude-only install section |
| `skill-mesh/<skill>/SKILL.md` | replace with generated compatibility output | Preserve existing consumers while moving shared logic to canonical cores | Glob found 46 published single-file skills |
| `coding-root/.claude/skills/` and `.claude/skills-gpt/` | read-only migration source | Supply current cores and wrappers without cross-repository writes | Counted 47 Claude wrappers, 47 GPT wrappers, and 47 shared cores |
| `coding-root/.claude/lib/skill-router.ps1` | read-only migration source | Supply current routing behavior for neutral re-homing | Read constants, provider default, transport checks, and entry-point resolution |
| `coding-root/.claude/references/model-mapping.md` and `model-tier-map.json` | read-only migration source | Supply current capability and tier mappings | Read current rows, defaults, and JSON schema |
| `coding-root/.claude/lib/calibration/` and `.claude/lib/telemetry/` | read-only migration source | Supply tests and telemetry behavior for neutral paths | Glob and test inspection confirmed router tests hardcode `.claude` paths |
| `coding-root/documentation/multi-model/` | read-only migration source | Supply existing guides for publication and correction | Directory inspection confirmed guides exist only in coding-root |
| `coding-root/docs/skill-mesh-plan.md` | pointer only | Keep the historical implementation plan connected to this public-repository follow-on | Read existing phases, repository boundary, and Phase 5 status |
| GitHub repository metadata | modify | Current description still advertises “Claude Code skills” | `gh repo view aberson/skill-mesh` confirmed current description |

No public function signature or persisted data schema changes are planned. The
router CLI is a compatibility surface; all existing explicit flags remain
supported while the new neutral command and `auto` selection are added.

## 5. New Components

| Component | Purpose |
|---|---|
| `skill-mesh/skills/<name>/core.md` | Canonical provider-independent contract for each portable skill |
| `skill-mesh/skills/<name>/providers/claude.md` | Thin Claude host adapter |
| `skill-mesh/skills/<name>/providers/gpt.md` | Thin GPT/Copilot host adapter |
| `skill-mesh/runtime/skill-router.ps1` | Provider-neutral CLI router and bounded fallback implementation |
| `skill-mesh/config/model-mapping.json` | Machine-readable skill/provider capability mapping |
| `skill-mesh/config/model-tier-map.json` | Machine-readable model peer mapping |
| `skill-mesh/tools/build-distributions.ps1` | Deterministically generates host-specific compatibility trees |
| `skill-mesh/tools/install-skill-mesh.ps1` | Installs a selected host profile without making canonical files host-owned |
| `skill-mesh/tests/package-integrity/` | Verifies manifests, links, generated output, docs claims, and source/distribution drift |
| Release artifact `dist/claude/` | Generated Claude Code discovery layout |
| Release artifact `dist/gpt/` | Generated GPT/Copilot discovery layout |
| `skill-mesh/documentation/providers/` | Provider-specific authentication, capabilities, divergences, and installation guides |

Generated distributions are not committed. The release command builds them into
a clean staging directory, runs integrity checks, and attaches them as versioned
release artifacts. The source manifest and reproducible generation command are
committed and mandatory.

## 6. Design Decisions

### Public skill-mesh is the canonical source

The public repository will own portable skill contracts and runtime
infrastructure. `coding-root/.claude` becomes an installed consumer plus
compatibility layer. This eliminates the current private-source/public-mirror
split that allowed documentation and published artifacts to drift.

Alternative rejected: keep `.claude` canonical and improve the export script.
That would make publishing more reliable but would preserve Claude ownership in
both naming and directory semantics.

### Shared core sits beside neither provider

Each portable skill gets a neutral `core.md`; Claude and GPT adapters are
siblings under `providers/`. `SKILL.md`, `SKILL-claude.md`, and `SKILL-gpt.md`
remain generated host-facing filenames only.

Alternative rejected: keep `SKILL-core.md` under `skills-gpt`. Although
functionally workable, it communicates that shared behavior belongs to GPT and
makes the topology harder to explain.

### Host binding is primary; runtime detection is secondary

Normal installation binds the correct provider adapter into the host’s discovery
layout. The neutral router supports `-Provider auto|claude|gpt|local`, with
`auto` using trustworthy host metadata when available. If metadata is absent or
ambiguous, it fails with an actionable selection message rather than silently
choosing Claude. `-Model` remains as a deprecated compatibility alias during the
migration.

This avoids claiming universal active-model detection where the host does not
expose that fact. It also fixes the current failure mode where GPT sessions can
discover the Claude compatibility launcher before the router runs.

### Provider choice and transport authentication are separate

Selecting GPT does not imply `OPENAI_API_KEY`. GPT transport precedence is
documented and tested independently: GitHub Copilot authentication first,
optional direct OpenAI second. Claude host-native execution likewise does not
require `ANTHROPIC_API_KEY`; direct API execution is a separate transport.

### Compatibility is generated and tested

Existing `.claude` paths and public top-level `SKILL.md` consumers receive thin
generated shims. Generated files contain source metadata and are checked for
drift in CI. No shared behavioral contract is copied into multiple wrappers.

### Provider-neutral does not mean capability-identical

Claude-only exclusions remain visible and honest. The README leads with the
shared pipeline, then presents a capability matrix and provider-specific
exceptions instead of describing one provider as the default product.

### Canonical data contracts

`config/skill-manifest.json` is the single source used by distribution,
installation, integrity, and README-count generation:

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | integer | Manifest parser compatibility version |
| `skills` | array | One record per published skill |
| `skills[].name` | kebab-case string | Stable skill identifier and canonical directory name |
| `skills[].core` | repository-relative path or `null` | Neutral core path; `null` only for provider-native exclusions |
| `skills[].providers` | object | Provider name to adapter path mapping |
| `skills[].capabilities` | array of strings | Required host capability roles such as filesystem, sub-agent, or vision |
| `skills[].status` | `portable` or `provider-native` | Whether multiple provider adapters are expected |

`config/model-mapping.json` records runtime support:

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | integer | Mapping parser compatibility version |
| `providers` | object | Supported provider and transport metadata |
| `skills` | object keyed by skill name | Per-skill provider and local capability booleans |
| `default_provider` | `auto` | Forces host binding or trustworthy metadata rather than a Claude default |

`<name>` and `<skill>` in path examples mean the same stable kebab-case
`skills[].name` value. A **core** is provider-independent workflow behavior; an
**adapter** maps that behavior to one host’s tools; a **discovery layout** is the
host-specific directory/filename shape used to find a skill; a **shim** is a
thin backward-compatible launcher; a **transport** is the authenticated API or
host-native channel used to execute a provider model; and **calibration** is the
existing deterministic/rubric comparison that checks adapter parity.

### Builder quickstart

1. `Set-Location <workspace>\skill-mesh`.
2. Verify `git branch --show-current` reports the intended skill-mesh branch and
   `git remote get-url origin` reports `aberson/skill-mesh`.
3. Confirm the read-only legacy source exists at
   `<workspace>\.claude`; do not edit it during Steps 33-40.
4. Run `/plan-expedite --plan documentation/provider-neutral-skill-mesh-plan.md`.
5. Run the emitted `/build-phase` command from the skill-mesh repository.
6. During implementation, use the existing calibration baseline command
   `python -m pytest <workspace>\.claude\lib\calibration\test_calibrate.py`
   until Step 34 lands the neutral test path; thereafter use the neutral command
   recorded by Step 33.
7. No lint or typecheck command is currently configured. Do not invent one;
   package-integrity and existing calibration tests are the initial gates.

## 7. Build Steps

### Step 33: Lock the neutral package and host-adapter contract
- **Problem:** The current framework defines provider wrappers but still assumes `.claude` ownership and explicit Claude-first routing.
- **Type:** code
- **Issue:** #42
- **Flags:** --reviewers code --isolation worktree
- **Files:** `documentation/architecture.md`, `documentation/providers/`, `config/skill-manifest.json`
- **Produces:** Updated framework design, host capability matrix, canonical directory contract, CLI compatibility table, and migration manifest covering all current skills and support assets.
- **Done when:** The design names one canonical location for every core, adapter, mapping, test, and doc; documents host-native binding versus runtime auto-detection; includes a migration entry for all 47 portable skills plus the 3 Claude-native exclusions; and records the exact PowerShell build/install/test commands with absent lint/typecheck commands explicitly marked not configured.
- **Depends on:** none
- **Status:** DONE (2026-07-26)

### Step 34: Create the provider-neutral runtime and configuration surface
- **Problem:** Router, mappings, telemetry, and tests are physically and logically rooted under `.claude`.
- **Type:** code
- **Issue:** #43
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `runtime/`, `config/model-mapping.json`, `config/model-tier-map.json`, `tests/router/`, `tests/calibration/`, `tests/telemetry/`
- **Produces:** `runtime/`, `config/`, neutral telemetry paths, neutral calibration paths, and temporary `.claude` router/config shims.
- **Done when:** Existing explicit Claude/GPT/local router scenarios pass from the neutral path; a generated legacy `.claude/lib/skill-router.ps1` shim delegates in a temporary installation without behavior loss; no neutral runtime code requires a `.claude` source root; and path canonicalization rejects traversal through `..`, symlinks, or Windows junctions outside allowed roots.
- **Depends on:** 33
- **Status:** DONE (2026-07-26)

### Step 35: Migrate skill cores and provider adapters into the neutral source tree
- **Problem:** Shared cores currently live under the GPT tree and the public repository publishes only flattened Claude-oriented skills.
- **Type:** code
- **Issue:** #44
- **Flags:** --reviewers deep --isolation worktree
- **Files:** existing top-level skill directories, `skills/`, `config/skill-manifest.json`
- **Produces:** `skills/<name>/core.md`, provider adapters, a machine-readable inventory, and explicit provider-native exclusion records.
- **Done when:** All 47 portable skills have exactly one core plus Claude and GPT adapters; the 3 exclusions have only truthful supported adapters; hashes or normalized comparisons prove no required core clauses were lost during migration.
- **Depends on:** 33, 34
- **Status:** DONE (2026-07-26)

### Step 36: Build deterministic host distributions and installers
- **Problem:** Host discovery requires provider-specific filenames and directories, but those requirements should not dictate canonical ownership.
- **Type:** code
- **Issue:** #45
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/build-distributions.ps1`, `tools/install-skill-mesh.ps1`, `config/skill-manifest.json`, `tests/distributions/`
- **Produces:** Distribution builder, Claude installer/profile, GPT/Copilot installer/profile, compatibility launchers, uninstall/upgrade behavior, and generated-file provenance markers.
- **Done when:** A clean temporary home can install each profile; Claude discovery resolves the Claude adapter, GPT discovery resolves the GPT adapter, relative core references resolve, reinstall is idempotent, and uninstall removes only files owned by skill-mesh.
- **Depends on:** 35
- **Status:** DONE (2026-07-27)

### Step 37: Implement honest provider selection and transport authentication
- **Problem:** The router silently defaults to Claude, host-native discovery can bypass routing, and public auth guidance conflates GPT with direct OpenAI API access.
- **Type:** code
- **Issue:** #46
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `runtime/skill-router.ps1`, `runtime/providers/`, `config/model-mapping.json`, `tests/router/`, `documentation/providers/`, `documentation/troubleshooting.md`
- **Produces:** `-Provider auto|claude|gpt|local`, compatibility handling for `-Model`, host metadata adapters, explicit ambiguity error, Copilot-first GPT transport selection, optional OpenAI transport, and sanitized diagnostics.
- **Done when:** Tests cover host-bound Claude and GPT invocation, explicit overrides, each host metadata source approved in Step 33, ambiguous detection, Copilot auth without `OPENAI_API_KEY`, optional OpenAI fallback, token expiry/authentication failure, provider rate-limit/timeout behavior, no secret output, and the bounded cross-provider retry contract.
- **Depends on:** 34, 36
- **Status:** DONE (2026-07-27)

### Step 38: Add package integrity, drift, and release gates
- **Problem:** The public README currently claims files and capabilities absent from the public package.
- **Type:** code
- **Issue:** #47
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/build-distributions.ps1`, `tools/release.ps1`, `tests/package-integrity/`, `config/skill-manifest.json`, `.gitignore`
- **Produces:** Link checker, manifest completeness test, source-to-distribution drift test, provider-wrapper/core-reference test, README claim checks, and a repeatable release/export command.
- **Done when:** Tests fail on a missing linked file, missing provider adapter, stale generated wrapper, mismatched skill count, invalid core path, README claim unsupported by the release manifest, or tracked generated distribution; a clean release staging run reproduces the checked artifacts and emits checksums.
- **Depends on:** 35, 36, 37
- **Status:** DONE (2026-07-27)

### Step 39: Rewrite the public product documentation and repository metadata
- **Problem:** The public presentation still says `claude-skills`, leads with Claude, requires `OPENAI_API_KEY`, and documents a router and guide that are not shipped.
- **Type:** code
- **Issue:** #48
- **Flags:** --reviewers code --isolation worktree
- **Files:** `README.md`, `documentation/architecture.md`, `documentation/providers/`, `documentation/migration.md`
- **Produces:** Provider-neutral README, architecture overview, provider guides, installation matrix, authentication matrix, capability/exclusion table, migration notes, accurate status section, and proposed GitHub title/description text.
- **Done when:** Every local link passes the package-integrity checker; the README never presents `OPENAI_API_KEY` as universally required; Claude and GPT receive parallel first-class installation examples; exclusions are explicit; and every documented command runs against files present in the public repository.
- **Depends on:** 36, 37, 38
- **Status:** DONE (2026-07-27)

### Step 40: Run cross-provider package and workflow smoke tests
- **Problem:** Structural parity does not prove that installed profiles execute the expected adapters and preserve skill output contracts.
- **Type:** code
- **Issue:** #49
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tests/smoke/`, `tests/fixtures/`, `documentation/release-candidate-report.md`, `runtime/`, `skills/`
- **Produces:** Automated smoke fixtures and a release candidate report containing adapter selected, core hash, transport used, normalized verdict, exit code, and fallback disclosure for representative planning, review, build-orchestration, and session skill families.
- **Done when:** Automated package tests pass; representative Claude and GPT dry/integration runs select the intended adapters; direct GPT via Copilot works without `OPENAI_API_KEY`; fallback tests preserve the one-transition budget; and no test relies on the private pre-migration paths.
- **Depends on:** 37, 38, 39
- **Status:** DONE (2026-07-27)

### Step 41: Perform host-native acceptance and publish
- **Problem:** The final goal depends on real host discovery behavior that fixtures cannot fully establish.
- **Type:** operator
- **Issue:** #50
- **Done when:** The operator invokes one representative skill from a Claude session and one from a GPT/Copilot session, confirms each loaded its matching adapter and shared core, confirms explicit cross-provider override behavior, approves the README, publishes the release, and updates the GitHub repository description to provider-neutral wording.
- **Depends on:** 40

## 8. Risks and Open Questions

| Item | Risk | Mitigation |
|---|---|---|
| Host model metadata | Some hosts may not expose the active provider before skill discovery | Bind provider at installation; use `auto` only with trustworthy metadata; emit an explicit selection error otherwise |
| Two-repository migration | Changes can land in the wrong repository or public/private state can diverge | Keep Steps 33-40 write-scoped to `aberson/skill-mesh`; treat coding-root as read-only input; install only the released artifact in Step 41 |
| Compatibility breakage | Existing `.claude/skills` junctions and direct `SKILL.md` links may stop resolving | Generate backward-compatible shims, test Windows junctions, and document a deprecation window |
| Missing private assets | Some skills reference unpublished workspace contracts or project adapters | Classify each reference as publish, replace with neutral interface, or mark as explicit adaptation point; fail integrity checks on accidental broken links |
| Generated-tree review noise | Generated Claude/GPT trees can overwhelm source review | Keep distributions uncommitted; generate them only in clean release staging and publish versioned artifacts with checksums |
| Provider capability drift | Model upgrades can silently change output quality | Retain explicit model pinning and rerun affected calibration before changing mappings |
| Auth confusion | Copilot, GitHub, OpenAI, and host-native credentials can be conflated | Publish transport-specific auth tables and test each transport independently |
| Silent fallback masking errors | Provider-neutral branding could hide that a different provider executed | Preserve exit code `2`, fallback disclosure, adapter/core identity, and telemetry attempt roles |
| Public skill count drift | The implementation already has more skills than the public mirror | Generate counts from the manifest and prohibit hand-maintained README totals |

## 9. Testing Strategy

### Static and package integrity

- Validate every manifest entry has the required neutral core and declared
  provider adapters.
- Validate every generated wrapper resolves within an allowed canonical root.
- Check all README and documentation links against the release tree.
- Compare generated artifacts with committed/release artifacts and fail on drift.
- Verify no secret values, private paths, or unpublished required dependencies
  enter the public package.

### Router and transport tests

- Preserve current explicit Claude, GPT, local, fallback, exit-code, spend, and
  telemetry tests after moving the router.
- Add provider-selection cases for installed host profiles, trusted metadata,
  explicit override, ambiguity, unsupported provider, and legacy `-Model`.
- Add GitHub Copilot authentication tests that do not set `OPENAI_API_KEY`.
- Add optional direct OpenAI transport tests and verify transport precedence.
- Verify diagnostics report only credential presence/source class, never values.

### Distribution tests

- Generate Claude and GPT distributions into temporary directories.
- Install each into a temporary home using Windows-compatible paths.
- Assert that the discovered `SKILL.md` loads the expected provider adapter and
  the same canonical core.
- Assert idempotent upgrade and ownership-safe uninstall behavior.
- Exercise Windows junction resolution because that is the current primary
  installation pattern.

### Behavioral parity

- Reuse existing calibration scenarios against canonical cores and both provider
  adapters.
- Smoke at least one skill from planning, review, orchestration, repository, and
  session families.
- Preserve all hard gates, halt contracts, locked verdicts, and normalized output
  schemas across providers.

### Release acceptance

- Run the public package from a clean checkout rather than `coding-root`.
- Invoke a representative skill in a real Claude host and a real GPT/Copilot
  host and record which adapter/core loaded.
- Run an explicit cross-provider invocation and a simulated provider outage.
- Run package-integrity and link checks against the exact release candidate.

This feature changes packaging and invocation, not autonomous wall-clock
behavior, so the long-running observation trigger does not apply. It does alter
provider-to-skill dispatch, so real host-native acceptance in Step 41 is required
in addition to automated tests.

## Appendix

### Decision Inventory

| ID | P/D | Choice | Status |
|---|---|---|---|
| P1 | P | Skill-mesh is provider-neutral: Claude sessions use Claude adapters and GPT sessions use GPT adapters | active |
| P2 | P | Shared skills and routing infrastructure must not be canonically owned by `.claude/` | active |
| P3 | P | GPT usage must not be documented as universally requiring `OPENAI_API_KEY` | active |
| D1 | D | `aberson/skill-mesh` becomes the canonical source; `coding-root/.claude` becomes an installed compatibility consumer after Step 41 | proposed |
| D2 | D | Each portable skill uses `skills/<name>/core.md` plus sibling `providers/claude.md` and `providers/gpt.md` adapters | proposed |
| D3 | D | Host-bound adapters are primary; router `auto` uses only trustworthy metadata and errors on ambiguity instead of defaulting to Claude | proposed |
| D4 | D | Generated Claude/GPT distributions are release artifacts with checksums, not committed source | proposed |
| D5 | D | The three existing Claude-native exclusions remain explicit rather than receiving misleading GPT stubs | proposed |
| D6 | D | Migration executes as Steps 33-41, ending with real Claude and GPT host acceptance before publication | proposed |
