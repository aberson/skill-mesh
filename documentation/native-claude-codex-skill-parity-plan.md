# Native Claude/Codex Skill Parity and Maintenance Plan

**Status:** READY FOR PLAN SIGNOFF — PLAN-REVIEW, PLAN-WRAP, AND PLAN-REDLINE PASS

**Proposal:** `documentation/native-claude-codex-skill-parity-proposal.html`

**Planning branch:** `plan/native-codex-skill-parity`

**Planning base:** `50fb9a36db0627da9e71c32d53bf81c4b98e7d4a`

## 1. What This Is

This is a feature plan for a full native Claude Code and Codex skill cutover. It replaces the failed
Copilot-to-Codex assumption with an implementation that uses each host's real discovery mechanism:
Claude packages under the existing Claude discovery tree and Codex packages under
`$HOME/.agents/skills`.

The user problem is already established. Abraham uses the Claude skills and wants the same maintained
behaviors available in Codex, with known utility hookups, truthful model evidence, and Dev Observatory
visibility. This plan does not require a small value pilot before building parity.

The result is one authored behavior core per skill, explicit Claude and Codex adapters, generated
self-contained packages for both hosts, a one-time migration, an ordinary update workflow, exhaustive
per-skill qualification, and a reversible live cutover.

### Problem

The repository still treats the second profile as generic `gpt`/GitHub Copilot, while Abraham no
longer uses Copilot. Codex has no managed `$HOME/.agents/skills` Skill Mesh catalog. Most active
provider adapters contain router, Copilot, model-tier, or Claude-artifact assumptions rather than
native Codex instructions. The build also declares support assets that it neither owns canonically nor
packages. Maintenance evaluation can optimize a shared core for whichever model happened to propose
or grade the edit, and known utility integrations remain partly unwired.

### Type

Feature plan with cross-repository integration, distribution, migration, evaluation, telemetry, and
live-cutover work.

### Authority

Creating and reviewing this plan is authorized. Implementation is not authorized until Approval 1.
The old Goal A terminal `stop` remains historically correct. Approval 1 creates a new, independent
Goal NP and supersedes the old recovery-plan implementation lock only for the paths and work described
here. It does not reinterpret or reopen Goal A evidence.

The product charter's former statement that release would not test every skill is superseded for this
Goal NP migration: native parity requires an explicit test cell for every shipped skill on every
supported host.

## 2. Outcomes and Non-Goals

### Required outcomes

1. Claude and Codex discover native Skill Mesh packages without a router.
2. Every shared skill has one authored `core.md`, one Claude adapter, and one Codex adapter.
3. Generated packages are self-contained and carry byte-identical core content for both hosts.
4. All globally installed Claude skills intended to be portable are represented in Codex.
5. Every final managed skill is tested through its actual host discovery and invocation path.
6. The known utility hookup map is implemented once and verified mechanically; it is not deferred
   until Abraham re-encounters known friction.
7. Dev Observatory presents read-only skill, utility, qualification, and model-evidence status.
8. Requested and provider-reported model identity remain separate. Missing identity is visible, not
   invented.
9. Shared-core maintenance uses dual-host Pareto acceptance. A gain on one host cannot cancel a
   regression on the other.
10. Initial cutover and every later managed update are transactional and recoverable.

### Out of scope

- GitHub Copilot support as an active provider.
- A generic model/provider router or control plane.
- Automatic provider or fallback-model selection.
- New provider families, local-model integration, or model-equivalence claims.
- Redesigning the substance of all existing skill behaviors during migration.
- New utility product features beyond the minimal stable interfaces already planned.
- Making Dev Observatory an invocation dependency, router, or mutation owner.
- Changing the behaviors of the three Claude-native skills merely to force false portability.
- Unrelated coding-root, utility-repository, or Dev Observatory work.
- Reusing Goal A experiment runners as the new production architecture.

### 2.1 Glossary

- **WIP (work in progress):** staged, tracked-modified, or untracked bytes not yet in the frozen
  candidate commit.
- **UAT (user acceptance testing):** operator feedback or exercise; it is not a build gate unless a
  numbered operator step says so.
- **argv (argument vector):** ordered process arguments passed without shell-string interpolation.
- **JSONL (newline-delimited JSON):** exactly one JSON object per line.
- **BOM (byte-order mark):** a leading encoding marker; Goal NP JSON and JSONL state is UTF-8 without
  one.
- **frontmatter:** the YAML metadata block between the opening `---` delimiters in `SKILL.md`.

## 3. Approved Architecture

### 3.1 One authoring source, generated native packages

The only authored behavior source for each global package is:

```text
skill-mesh/skills/<skill>/core.md
skill-mesh/skills/<skill>/providers/claude.md
skill-mesh/skills/<skill>/providers/codex.md
skill-mesh/skills/<skill>/<declared support assets>
skill-mesh/_shared/<shared assets>
```

Repo-local packages use the same pattern under `<owner-repo>/skills/<name>/`; their generated
`.claude/skills` and `.agents/skills` packages are artifacts, not authoring sources.

Claude and Codex receive generated, self-contained packages. Generated `core.md` files are release
artifacts, not second authoring sources. A build records the canonical core hash and requires the
Claude and Codex copies to match it exactly.

This deliberately does not make live shells load an external mutable checkout. Codex's documented
unit is a skill directory containing `SKILL.md` and optional co-located assets. Self-contained packages
work from nested repositories, worktrees, sandboxes, and another machine. A source edit changes
neither host until a qualified release is activated.

### 3.2 Placement

| Purpose | Location | Rule |
|---|---|---|
| Authoritative source | committed `skill-mesh` main checkout | ordinary files; no worktree is an install source |
| Repo-local source | committed owner-repository `skills/<name>` | ordinary files; isolated candidate worktrees until Approval 2 |
| Build staging | `%LOCALAPPDATA%\SkillMesh\Staging\<run-id>` | create-new, ordinary, non-discoverable files |
| Release store | `%LOCALAPPDATA%\SkillMesh\Releases\<release-id>` | immutable generated packages, release-owned utility runtimes, and manifest |
| State | `%LOCALAPPDATA%\SkillMesh\State\profiles-v1.json` | exact managed path/hash ownership and release-relative utility-runtime locators |
| Backups | `%LOCALAPPDATA%\SkillMesh\Backups\<run-id>` | pre-mutation bytes and rollback journal |
| Codex discovery | `$CODEX_EFFECTIVE_HOME\.agents\skills\<name>` | ordinary self-contained generated directories |
| Claude discovery | existing `%USERPROFILE%\.claude\skills` topology | preserve the existing home junction and consumer files |

There is no global catalog at `dev/.agents/skills`: it would be invisible from nested repositories and
external worktrees because Codex stops its project scan at the repository root. There is no duplicate
repo-local copy of a global Skill Mesh name. Repo-local skills remain additive and must use unique,
case-insensitive names.

`$CODEX_EFFECTIVE_HOME` is a logical value resolved once from the environment inherited by the native
Codex process. On Windows, absolute `HOME` and `USERPROFILE` must resolve to the same directory; a
missing value uses the other, and a disagreement stops before mutation unless an explicit reviewed
override is recorded. Build, child process, receipt, inspector, and cutover use that one value.

The existing Claude home junction remains unchanged. Updating managed files behind that junction is a
live mutation and is therefore forbidden before Approval 2.

### 3.3 Catalog

The current canonical manifest has 50 skills: 47 portable and 3 Claude-native. The live Claude target
also has seven global custom skills outside the manifest: `build-observer`, `citation-distill`,
`citation-review`, `citation-sweep`, `citation-triage`, `goblin-sweep`, and `repo-wrap`.

Goal NP promotes those seven into canonical portable packages and adds `skill-ablation`. The target
global catalog is therefore:

- 58 Claude skills: 55 shared plus 3 Claude-native.
- 55 Codex skills: every shared skill.
- one `_shared` payload per profile, which is not a skill and contains no `SKILL.md`.

Repo-local skills remain uniquely named and are registered in the placement/collision inventory. The
known starting matrix is: `career-ops` exists for Claude and Codex, Claude-only `apply-sheet` receives
a canonical repo-local source and Codex counterpart, `brand-fidelity` currently exists only for Claude
and receives a canonical source and Codex counterpart, and planned `change-benchmark` does not yet
exist and is created for both hosts. These
packages stay outside the 58/55 global counts but inside native qualification and collision checks.

The exact production serialization of Skill Mesh name, description, and source metadata must be at
most 7,500 UTF-8 characters, leaving at least 500 characters below Codex's documented 8,000-character
initial skill-list ceiling. Final native acceptance also requires all 55 global names to remain listed
and explicitly selectable beside system, plugin, and repo-local skills with no truncation or omission
warning.

### 3.4 Native invocation

Claude and Codex discover and invoke their own native packages. No Skill Mesh router selects a host or
model. A native skill may name another skill using the host's supported skill mechanism, but the
dependency must be declared and qualified. Provider-specific tool vocabulary, permission syntax, and
presentation stay in the provider adapter; behavioral gates stay in `core.md`.

## 4. Human Approval Model

There are exactly two program-level approval points.

### Approval 1 — implementation plan

Abraham approves this exact plan and proposal. That authorizes:

- clean isolated implementation worktrees and issue creation;
- recovery and scoped adoption of exactly these four preserved Step 4 files:
  `tests/distributions/test_distributions.py`,
  `tests/distributions/test_legacy_migration.py`,
  `tools/install-skill-mesh.ps1`, and
  `tools/migrate-legacy-install.ps1`;
- code, docs, tests, utility bindings, and Dev Observatory integration within the declared scope;
- disposable-home Claude and Codex invocations for architecture proof and qualification;
- external staging, release, telemetry, evaluation, and evidence roots under `%LOCALAPPDATA%`;
- preparation of an immutable cutover packet.

It does not authorize writes to live Claude/Codex discovery roots, the existing Claude junction target,
active workspace instructions, the live install ledger, or managed legacy profile paths.

The four-file authority is bound to
`%LOCALAPPDATA%\SkillMesh\Recovery\skill-mesh-step-4-20260814T021546Z-73e9e215\manifest.json`
(SHA-256 `2c907271bb7213f56cd0d9c374a2b5803ba65a8cdc46c0508a0e7c55e133df2e`)
and its patch SHA-256
`5f2b7f51a691b7244a0247c9d7dde5c8eaf300e2f7afe6dadd5b78221ee29bf3`.
It grants no authority over the other files retained in that historical recovery set.

Approval 1 also authorizes non-destructive reconciliation of in-scope coding-root and utility-project
WIP. Every overlapping dirty path is hashed/exported first, then classified as
`adopt-to-canonical`, `preserve-foreign`, `already-owned-implementation`, or `superseded`. No working
byte is overwritten without a byte-backed recovery copy and an explicit classification record.

#### Approval-1 receipt and administrative issue synchronization

Approval 1 is recorded once, without adding another approval gate, in the create-new external receipt
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\approval1\approval1-v1.json`. It contains schema version 1,
a lowercase UUIDv4 receipt ID, decision `approve-goal-np-plan`, exact operator choices `P01` through
`P10`, exact approved defaults `D01` through `D10` plus any user-authored override text, the approved
`aberson/skill-mesh` 40-hex commit, plan/proposal paths and SHA-256 values, the canonical workspace
target-inventory SHA-256, the create-new `workspace-roots-v1.json` byte length and SHA-256, Abraham's
approval message SHA-256 and locator, and UTC time.

The administrative recorder preserves Abraham's approval verbatim in
`documentation/native-parity-approval1-journal.md`, materializes the plan-defined
`config/workspace-targets.json` and
`schemas/{approval1-v1,issue-sync-v1,workspace-targets-v1}.schema.json`, and commits only those
administrative artifacts plus subsequent `**Issue:**` number backfill. The approved commit's
plan/proposal blobs remain immutable; the descendant plan copy may change only the 41 Issue values,
with that diff sealed by the issue-sync receipt. Any other plan change or any proposal change
invalidates Approval 1 and requires a revised plan approval.

Before GitHub mutation, `/repo-sync` validates the Approval-1 receipt, approved Git blobs, decisions,
defaults, target inventory, and target repository. It runs from the clean isolated Skill Mesh signoff
worktree with logical current directory `skill-mesh` and invokes:

```text
/repo-sync --plan documentation/native-claude-codex-skill-parity-plan.md --phase NP --scope both
```

`gh repo view --json nameWithOwner -q .nameWithOwner` must return `aberson/skill-mesh`, and every
mutating `gh` call is pinned with `-R aberson/skill-mesh`. The administrative recorder then backfills
the 41 decimal issue numbers and creates
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\approval1\issue-sync-v1.json`. That receipt records schema
version, UUID receipt ID, Approval-1 receipt SHA-256, target repository/default branch, resolved
logical current directory, exact invocation, pre/post commits, Plan-ID-to-issue number/URL map, the
umbrella issue number/URL, allowlisted issue-only plan diff, exit results, and UTC interval. NP-01 validates both receipts and
their ancestry/diff chain before its first write.

### Approval 2 — immutable live cutover

Abraham approves one exact deliverable packet after disposable rehearsal passes. That approval binds
the candidate commits, release manifest, mutation list, commands, backups, postchecks, and automatic
rollback. It authorizes one live apply and, if a required postcheck fails, one reverse-order rollback.

Normal UAT feedback, auth help, quota reset, and resumable qualification are inputs rather than new
approval gates. A code or policy change after Approval 2 invalidates the packet and returns to
qualification; it is not corrected during cutover.

After the initial cutover, the approved routine maintenance contract permits an operator to activate a
new release only after its deterministic scope-appropriate qualification passes. High-impact behavior
changes still require normal source review, but not a new architecture program.

## 5. Versioned Contracts

### 5.1 Profile state

`profiles-v1.json` is the ownership authority:

```json
{
  "schema_version": 1,
  "active_release_id": "r-<64-lowerhex>",
  "source_commit": "40-hex",
  "profiles": {
    "claude": {"root": "redacted logical locator", "owned_files": {"relative/path": "sha256"}},
    "codex": {"root": "redacted logical locator", "owned_files": {"relative/path": "sha256"}}
  },
  "utility_runtimes": {
    "UB01": {"release_relative_root": "utility-runtimes/UB01", "manifest_sha256": "sha256", "entrypoint": "relative/path"}
  },
  "legacy": {"copilot_profile": "retired|preserved-foreign"}
}
```

Paths stored in committed evidence are logical/redacted. Live state may hold canonical local paths but
never credentials. A retired file is removed only when its current hash matches the previous owned
hash. Foreign or drifted content is preserved and reported. `utility_runtimes` contains exactly one
entry for each `UB01` through `UB13`. A utility-runtime locator must resolve
inside the active immutable release and match that runtime's manifest; it never points to a source
checkout, candidate worktree, staging directory, ambient environment, or editable project install.

### 5.2 Model profiles and maintenance policy

`config/model-profiles.json` owns volatile host/model requests. It defines production executor and
grader profiles for Claude and Codex. Approval-1 default D08 freezes profile set `np-initial-v1`:

| Profile | Exact request | Effort | Allowed roles |
|---|---|---|---|
| `claude-production-v1` | `claude-opus-4-8` | `xhigh` | executor, proposer, challenger |
| `codex-production-v1` | `gpt-5.6-sol` | `ultra` | executor, proposer, challenger |
| `claude-grader-v1` | `claude-sonnet-5` | `xhigh` | grader only |
| `codex-grader-v1` | `gpt-5.6-terra` | `medium` | grader only |

The implementation records these as `exact-id`; it does not resolve an alias, host default, tier, or
alternate ID. Unsupported request/effort, role substitution, requested-versus-reported mismatch,
observed fallback, missing required role, or ambiguous configuration is `INVALID` and stops before
baseline generation. Authentication, quota, or transient availability is `INCOMPLETE`. Reported
identity `unavailable` may support an exact-request functional claim because argv/profile bytes remain
bound, but never an exact observed-model claim. Changing any ID, effort, or role requires an explicit
D08 plan amendment; it is not fallback.

For a high-impact change, both production profiles independently propose one candidate. The
opposite-family production profile challenges each candidate without rewriting it; both production
profiles render baseline/candidate; and both grader profiles grade every blinded artifact. A routine
change may have one proposer but still executes and grades both hosts whenever behavior is normative.

Baseline generation precedes candidate generation. `baseline_id` binds source/release, core, adapter,
support assets, exact profile-set hash and role map, host executable hashes, policy, eval, fixture,
holdout, and grader-prompt hashes. Trials pair baseline/candidate on host, profile, effort, scenario,
input/seed, judge profile, and bounds. Any profile, CLI, or identity-status change forces matched
rebaseline and calibration; stale or cross-profile baselines cannot qualify.

`config/shared-core-maintenance-policy.json` owns stable governance:

- either current production host may propose a routine candidate;
- the proposer has candidate authority only;
- Claude and Codex production profiles execute shared-core candidates;
- AI ablation, material behavior changes, and eval-contract changes require independent proposals from
  both families, blinded artifacts, both judge families, a sealed holdout, and at least three fresh
  end-to-end renders per host/scenario;
- deterministic code applies a per-host Pareto gate; cross-host averaging is forbidden;
- hard assertion regression tolerance is zero;
- a missing required host cell is `INDETERMINATE`, never a pass;
- a one-host win and other-host loss keeps the shared core unchanged; genuinely host-specific behavior
  may become a provider-adapter candidate after separate review;
- fallback is forbidden in maintenance acceptance.

Soft metrics are declared per scenario as a vector with direction, scale, host-specific
non-inferiority margin, and minimum meaningful gain. The default margin is zero unless a fixture
demonstrates irreducible noise before candidates are generated. A high-impact candidate is eligible
only when every host/scenario median is inside its margin, no paired trial crosses a hard regression
boundary, and it either reduces canonical tokens/lines or beats at least one predeclared metric by its
minimum gain. An uncertain boundary or grader disagreement is `INDETERMINATE`. If both blinded family
proposals qualify, the deterministic frontier presentation order is smallest canonical token count,
then greatest minimum per-host delta, then lexical candidate SHA-256. The operator selects one or keeps
the baseline; no LLM or automatic merge breaks the tie.

Routine mechanical typo/link fixes may use deterministic build/link/hash gates. Any deletion,
reordering, or change to normative behavior, tools, models, side effects, gates, or output contracts is
high-impact. A routine run automatically escalates to high-impact when hosts disagree, an assertion
flips, identity is incompatible, or the result is on the decision boundary.

### 5.3 Evaluation record

Authoritative evaluation JSON records:

- run, scenario, trial, executor host, judge host, and role;
- requested model kind/value and provider-reported model status/value/source separately;
- host executable/version/hash;
- source commit and core, adapter, support-asset, profile, policy, eval, and grader-prompt hashes;
- hard assertion results, soft scores, artifact hashes, tokens, latency, cost, and availability status;
- fallback policy/attempts and the deterministic `accept|reject|indeterminate` reason.

Requested identity is never copied into reported identity. Missing tokens/cost are `null` plus
`unavailable`, not numeric zero. Prompts, outputs, credentials, private absolute paths, and reusable
secrets are not telemetry fields.

### 5.4 Runtime telemetry v2

Native packages emit privacy-bounded records to
`%LOCALAPPDATA%\SkillMesh\Telemetry\v2\invocations.jsonl`. Records carry UUID run/call IDs, skill,
role, host, requested and reported identity, fallback facts, usage/cost availability, latency, outcome,
and release/core/adapter hashes. A Windows named mutex protects append. Rotation and record-size bounds
are deterministic. Telemetry failure is fail-open for ordinary skill execution and visible in status.

Native hosts do not currently provide a proven universal skill-invocation lifecycle hook. The receipt
contract therefore records `coverage=instrumented|best-effort|unobserved` plus its source. Evaluation,
installer, and utility-runner calls are guaranteed only when they pass through an instrumented seam.
Generated interactive skill instructions may request start/end receipts, but qualification must prove
host compliance and still labels that coverage `best-effort` unless an official host hook is found.
Dev Observatory shows recorded calls and each package's coverage capability; it never implies that an
absent record proves no invocation occurred. Requested model remains visible when reported identity is
unavailable.

### 5.5 Utility bindings

`config/utility-bindings.json` is a closed inventory. Every row names:

- utility project and stable command/artifact contract;
- owning skill and exact hook;
- advisory or required behavior;
- timeout, output, path, and redaction bounds;
- deterministic fixture and bounded real smoke;
- telemetry field and Dev Observatory view;
- state `called`, `evidence-only`, or `not-applicable`, with a reason for either non-called state.

Missing advisory utilities skip visibly without failing the skill. Safety-critical required bindings
fail closed. Utility availability never changes which provider/model is selected.

Machine-specific utility roots live in
`%LOCALAPPDATA%\SkillMesh\State\utility-roots-v1.json`; committed bindings refer to stable root IDs,
not private absolute paths. A row is `called` only when at least one listed native hook actually
executes the utility; conditional opt-in still counts when its qualification fixture enables the
hook. `evidence-only` means no hook executes and only a producer artifact is consumed;
`not-applicable` means no supported-host hook exists. Approval-1 targets are exactly 13 rows, 6
required plus 7 advisory, all 13 `called`; no step may downgrade a row without a plan amendment.

| ID | Utility | Policy/state | Native hooks | Required bounded smoke | Owning test |
|---|---|---|---|---|---|
| `UB01` | `b2_project_goblin` | required/called | `goblin-suggest`, `goblin-do`, `goblin-sweep` | `<utility-entry:UB01> sweep <fixture-project> --json` | NP-21 `tests/utilities/test_b2_project_goblin.py` |
| `UB02` | `citation-needed` | required/called | `citation-distill`, `citation-review`, `citation-sweep`, `citation-triage` | `<utility-entry:UB02> init-db --db <scratch-db>`, then `<utility-entry:UB02> status --db <scratch-db>` | NP-21 `tests/utilities/test_citation_needed.py` |
| `UB03` | `dev-observatory` | required/called | `observatory-doctor`, `build-observer`, `build-step` port check; read-only | `<utility-entry:UB03> doctor --root <fixture-root> --registry <fixture-registry> --json` | NP-21 `tests/utilities/test_dev_observatory.py` |
| `UB04` | `on-brand` | required/called | repo-local `brand-fidelity`; Observatory consumer | `<utility-node:UB04> <utility-runtime:UB04>/bin/onbrand.mjs check <fixture-project> --json` | NP-23 `on-brand/test/brand-fidelity-native.test.ts` |
| `UB05` | `switchboard` | advisory/called | `tier-offload`, `build-step` judge seam; no router | `<utility-python:UB05> -m switchboard config --path <disabled-fixture-config>` | NP-21 `tests/utilities/test_switchboard.py` |
| `UB06` | `heads-up` | advisory/called | `plan-expedite`, `build-phase`, `session-wrap` | `<utility-entry:UB06> claim --ledger <scratch-ledger> --claim-id <fixed-uuid> --resource-kind path --resource <fixture-path> --ttl 5m --json`, then matching `check` and `release` argv with the same ledger/claim ID | NP-25 `tests/utilities/test_heads_up.py` |
| `UB07` | `tripwire` | required/called | `plan-expedite`, `build-phase`, `session-wrap` | `<utility-entry:UB07> check --root <fixture-root> --json` | NP-26 `tests/utilities/test_tripwire.py` |
| `UB08` | `same-page` | advisory/called | `repo-update`, `session-wrap`, `plan-expedite` | `<utility-entry:UB08> check <fixture-manifest> --format json` | NP-27 `tests/utilities/test_same_page.py` |
| `UB09` | `changed-check` | advisory/called | `build-step`, `plan-expedite`, `session-wrap` | `<utility-entry:UB09> plan --root <fixture-root> --json` | NP-28 `tests/utilities/test_changed_check.py` |
| `UB10` | `paper-trail` | advisory/called | `plan-redline` suggestion, `session-wrap`, `repo-update` | `<utility-entry:UB10> --root <fixture-store> audit` | NP-29 `tests/utilities/test_paper_trail.py` |
| `UB11` | `find-again` | advisory/called | `plan-feature`, `plan-review`, `user-debug`, `lesson-harvest`, `memory-distill` | `<utility-entry:UB11> --root <fixture-root> --json index`, then `<utility-entry:UB11> --root <fixture-root> --json search <query> --limit 5` | NP-30 `tests/utilities/test_find_again.py` |
| `UB12` | `mesh-lens` | advisory/called | `session-wrap`, telemetry ingest/report, Observatory export | `<utility-entry:UB12> ingest --source <fixture-jsonl> --store <scratch-store>`, then `<utility-entry:UB12> report --store <scratch-store> --out <scratch-report> --format json` | NP-31 `tests/utilities/test_mesh_lens.py` |
| `UB13` | `measure-twice` | required/called | repo-local `change-benchmark` | `<utility-entry:UB13> validate <fixture-suite>` | NP-24 `measure-twice/tests/test_change_benchmark_skill.py` |

UB03's `required` label is a qualification requirement, not a universal runtime dependency.
`observatory-doctor` and `build-observer` require Dev Observatory only when those Observatory-specific
skills are explicitly invoked. `build-step`'s port check is conditional/advisory: it runs only when
the validated registry/config enables it, and unavailable state skips visibly without failing the
build. No other skill waits on Observatory, and Observatory never routes/invokes a skill.

Every fixture parameterizes every hook listed in its row, not merely the representative smoke argv.
NP-37 builds each Python utility from its frozen owner commit into a wheel, installs the project and
locked dependencies non-editably into
`%LOCALAPPDATA%\SkillMesh\Releases\<release-id>\utility-runtimes\<root-id>`, and records the source
commit/tree, lockfile, wheel, interpreter, entrypoint, installed-file, and environment hashes in a
per-runtime manifest. On Brand is built from its exact package/lockfile into an equally immutable
release-owned Node bundle. Source-owner `uv sync` and `npm ci` commands in §5.8 are build/test inputs
only; their environments are never runtime dependencies.

`<utility-runtime:UBnn>`, `<utility-entry:UBnn>`, `<utility-python:UBnn>`, and
`<utility-node:UBnn>` are exact release-relative locators resolved from the active release manifest,
then canonicalized beneath that immutable runtime root. The runner passes those argv tokens directly
without shell interpolation or ambient `PATH`. It rejects editable installs, external `.pth`/launcher
targets, missing lock coverage, interpreter mismatch, and any executable/runtime dependency on a
source checkout, candidate worktree, staging directory, or active repository. Qualification invokes
the exact released runtime bytes. Activation installs only their State locators; rollback and release
retention keep the prior runtime set with the prior release.

Qualification cell IDs are `utility.<UBnn>.fixture` and
`utility.<UBnn>.smoke.<claude|codex>`: exactly 13 fixture cells plus 26 real native-host smoke cells,
or 39 utility integrated-flow cells separate from the 113 global native-skill cells. Raw evidence may
be shared, but each cell's assertions pass independently. NP-21 freezes all targets; NP-34 registers
the scenarios; NP-39 freezes all 39 IDs; NP-40 requires expected/completed/passed = 39 and the final
6/7 policy and 13/0/0 state counts.

`utility-roots-v1.json` has `schema_version=1`, `coding_root`, and `roots` keyed by the 13 stable
binding root IDs. Each value records canonical local `path`, `owner_repo`, relative sentinel
(`package.json` for On Brand, otherwise `pyproject.toml`), and
`availability=present|missing|invalid`. Private path values never enter committed evidence. The
bootstrap derives only `<coding-root>/<binding.relative_repo>` and never searches or guesses.

Goal NP always creates and validates `coding-root/.changed-check.toml`. For another repository the
binding is applicable exactly when
`Test-Path -LiteralPath (Join-Path $targetRepo '.changed-check.toml') -PathType Leaf`; absence means
`not-applicable` and zero spawn, while present-invalid follows the binding's declared visible error
policy. Goal NP also creates or validates `same-page.toml`, `find-again.toml` plus its initial on-demand
index, the Paper Trail store locator, and Mesh Lens store/report locators. No scheduler or soak is
introduced.

### 5.6 Transaction and Approval 2 receipt

Activation uses an exclusive named mutex and a create-new transaction journal with phases
`planned`, `backed-up`, `writing`, `verifying`, `committed`, `rolling-back`, `rolled-back`, or `failed`.
Every phase records the immutable release, expected before/after hashes, and completed mutation index.
Recovery is deterministic from any phase; concurrent activation is rejected before mutation.

Approval 2 is persisted as `approval2-v1.json` with schema version, exact deliverable-packet SHA-256,
decision `approve-exact-cutover`, Abraham's message locator and UTC time, and a create-new one-shot
nonce. The frozen cutover script stops before any write when the receipt is missing, malformed,
mismatched, already consumed, or points to a different packet.

### 5.7 Contract registry, IDs, persistence, and corruption

| Contract | Required identity and payload |
|---|---|
| Approval 1 | receipt ID, decision, exact D/P selections and overrides, approved commit, plan/proposal/message hashes and locators, workspace-target inventory hash, create-new `workspace-roots-v1.json` byte length/SHA-256, UTC time |
| issue sync | receipt ID, Approval-1 receipt hash, `aberson/skill-mesh`, exact invocation/cwd, pre/post commits, Plan-ID-to-issue map, allowlisted diff, exits, UTC interval |
| workspace targets / local roots | stable target/root IDs and role, role cardinality, Git owner and path-within-owner, expected remote/default branch, gate profile; local canonical path/ref/HEAD/tree/index/status hashes and observation time |
| candidate registry | candidate/target/step IDs, exact predecessor frontier, base/tip commit/tree/ref, ordered commit set, allowed/changed paths, cwd, test receipts, WIP inventory, before/after live-state hashes, disposition |
| WIP inventory | inventory/target/root IDs, baseline Git/status hashes, path/state/mode/length/content hash, Goal-NP overlap, classification, recovery locator/hash, disposition/reason |
| support import ledger | import/inventory IDs, skill, frozen source kind/locator/commit or recovery hash, source/destination hashes, destination, importer hash, collision result |
| adapter audit ledger | audit ID, skill/provider, core/adapter/support hashes, native primitive map, forbidden-token findings/locators, unsupported-capability policy, reviewer verdict/evidence hashes |
| model profiles | `schema_version`, unique `profile_id`, `host`, `provider_family`, `transport=host-native`, purposes, requested model kind/value/source, reasoning request |
| maintenance policy | `schema_version`, `policy_id`, referenced profile IDs, risk class, proposer/challenger/executor/grader roles, trial/holdout/calibration rules, per-metric margins/gains, acceptance/fallback/identity rules |
| eval inventory | skill, scenario, applicable hosts, shared neutral prompt/fixture hash, hard assertions, additive adapter assertions, metrics, call/network/time/output bounds, dependencies, holdout locator |
| eval run | UUID `run_id`, UUID call/trial IDs, immutable fingerprint set, attempts, executor/judge roles, requested/reported identity, artifacts, hard/soft results, acceptance reason, resume parent |
| preflight attempt index | separate hash-chained JSONL start/close events for immutable preflight attempts; request/profile/cwd/commit/parent hashes, status and receipt/evidence hashes |
| preflight attempt receipt | create-new `preflight-attempts/<attempt-id>/receipt.json`; all four D08 role calls, exact argv/exits, requested/reported identity, fallback, auth/quota status, containment/cleanup, evidence hashes; creates no matrix cell |
| preflight terminal aggregate | stable `preflight.json` created only for `PASS|INVALID`; request/profile/cwd/commit hashes, ordered preflight lineage and index length/SHA, terminal reason |
| native substrate proof request | `schema_version`, UUID `request_id`, source/profile/fixture/core/adapter/support/catalog hashes, exact host commands and credential mode, path/network/time/output/process bounds, no-fallback policy, cleanup roots, evidence root |
| substrate attempt index | hash-chained JSONL events with sequence, start/close, attempt/parent IDs, request/fingerprint/previous-event hashes; close adds status, attempt-receipt hash, and evidence-manifest hash |
| substrate attempt receipt | create-new `attempts/<uuid>/receipt.json`, request/parent/fingerprint, `PASS|FAIL|INCOMPLETE|INVALID`, UTC/exits, per-host discovery/catalog/load/canary/asset/named-call results and hashes, identity/fallback/containment/cleanup |
| substrate terminal aggregate | create-new stable `receipt.json` only for terminal `PASS|FAIL|INVALID`; ordered attempt IDs/hashes, exact index length/SHA, request/profile fingerprints, result/evidence union, terminal reason |
| native qualification request | `schema_version`, UUID `request_id`, immutable source/release/profile/policy/eval/baseline fingerprints, exact required cell IDs and integrated flows, per-cell host/model/call/network/time/output/attempt bounds, resume rules, evidence root |
| qualification attempt index | hash-chained JSONL start/close events with sequence, attempt/parent/request/fingerprint hashes, status, receipt/evidence hashes |
| qualification attempt receipt | create-new `attempts/<uuid>/receipt.json`, request/parent/fingerprints, status, completed cell/result hashes, integrated flows, fallback, unchanged-release proof, containment, cleanup |
| qualification terminal aggregate | create-new stable `receipt.json` only for terminal `PASS|FAIL|INVALID`; ordered lineage, index length/SHA, expected/completed/passed counts, sorted cell/result hashes, integrated flows, terminal reason |
| telemetry v2 | UUID record/run/call lineage, UTC interval, skill/role/host, identity/coverage/fallback, nullable measured usage/cost, outcome, release/core/adapter/policy hashes |
| utility binding | stable binding ID, project/root ID, owner repo, call sites/hosts, argv, required/advisory policy, bounds/redaction, fixture/smoke, receipt field, state evidence |
| utility roots | schema version 1, coding-root ID, 13 stable root IDs, canonical local path, owner repo, sentinel, availability; private paths stay outside Git |
| utility runtime | binding/root ID, runtime kind, frozen source commit/tree and lock hashes, wheel/package and interpreter/runtime hashes, release-relative root/entrypoint, sorted installed-file hashes, no-editable/no-external-dependency proof |
| release manifest | stored `release_id=r-<64-lowerhex>` recomputed from the canonical manifest payload with `release_id` omitted; source commits, builder hash, sorted profile and utility-runtime path/hash maps excluding the manifest itself, dependency graph, catalog budget, schema hashes |
| transaction journal | UUID transaction ID, release/before-state IDs, exclusive-lock identity, phase enum, ordered mutation list, completed index, backup hashes, error/rollback state |
| Approval-2 packet | canonical `packet.json`, source/release/candidate/profile/baseline/qualification/utility/Observatory/mutation/backup/postcheck/rollback hashes; excludes its own digest |
| Approval 2 | packet SHA-256, exact decision, message locator/time, create-new nonce, unused/consumed state |
| cutover/rollback receipt | transaction/packet/approval IDs, before/after hashes, commands, exit results, postchecks, nonce consumption, rollback reason/result |

JSON state is UTF-8 without BOM, canonical key order where hashed, and JSON-schema validated before
use. Mutable snapshots write create-new same-directory temporary bytes, flush, then atomically replace;
append-only telemetry/index writes hold the named mutex. A truncated, duplicate-ID, invalid, or
hash-mismatched record is retained as evidence and stops the state-changing operation; code never
guesses a repair. Resume requires the exact immutable fingerprint and creates a child run/transaction
record rather than rewriting history.

Release construction uses a create-new staging directory whose package/runtime references are all
release-relative. The builder canonicalizes the manifest object with `release_id` absent and without a
self-entry in its file map, hashes those bytes, inserts `release_id=r-<digest>`, then independently
removes/recanonicalizes/recomputes the stored value. Only after that check and the no-external-path
scan pass may it atomically rename the complete location-independent tree to create-new
`%LOCALAPPDATA%\SkillMesh\Releases\<release-id>`. An existing destination is accepted only as an exact
immutable byte match and is never overwritten; any mismatch is corruption.

For either operator runner, first Preflight requires an empty `preflight-index.jsonl`. A controlled
`INCOMPLETE` appends an immutable attempt and prints `-Action PreflightResume` with the exact
highest-sequence closed INCOMPLETE leaf ID/hash; no stable `preflight.json` exists yet. A later PASS or
terminal INVALID creates it once. Run refuses anything except a schema-valid PASS preflight bound to
the same request/profile/cwd/commit, and its first invocation requires an empty proof/qualification
attempt index. Resume requires the
highest-sequence closed `INCOMPLETE` leaf with no child and no aggregate; the caller supplies both its
UUID and receipt SHA-256. Reusing an older parent, branching, corruption, a duplicate parent, or bytes
appended after a terminal aggregate is refused. An `INCOMPLETE` attempt never creates the stable
aggregate. Once a proof/qualification terminal aggregate exists, Run, Resume, and its index append are
refused; a PASS preflight aggregate is instead a required immutable input to Run.

If power loss follows a durable closed terminal attempt but precedes aggregate creation, `Inspect`
prints a fully substituted `-Action Finalize -TerminalAttemptId <uuid> -TerminalReceiptSha256
<64-lowerhex>` command. Finalize makes zero host calls and only validates the lineage before creating
the aggregate. A started-but-unclosed attempt is deterministically sealed `INCOMPLETE` from durable
checkpoints, or terminal `INVALID` when proof is impossible; it is never silently skipped.

Identifier definitions:

- `<run-id>` is a lowercase canonical UUIDv4 generated create-new by the initiating runner and used
  unchanged in paths, journals, telemetry, and child lineage.
- `<inventory-id>` is `inv-` plus a lowercase UUIDv4, generated by NP-01 before enumeration; the
  completed canonical inventory has a separate SHA-256.
- `<request-id>` and `<attempt-id>` are independent lowercase canonical UUIDv4 values generated
  create-new by the request producer and runner. A corrected request always gets a new request ID and
  directory; no prior request/evidence path is overwritten.
- `<np01-coding-root-commit>` is the exact 40-lowerhex coding-root HEAD captured by NP-01 before Goal
  NP candidate work; it is not the Skill Mesh adoption commit.
- `<packet-sha256>` is 64 lowercase hex: SHA-256 of NP-41's exact UTF-8-without-BOM, LF-normalized
  canonical `packet.json`. That file omits its own digest; the Approval-2 receipt and packet manifest
  store it.

| Identifier | Exact format / generation | Producer -> consumers |
|---|---|---|
| target/root ID | lowercase slug `[a-z0-9][a-z0-9_-]{0,63}` from the approved §5.8 name; case-insensitive collision stops, never auto-suffixes | Approval-1 registry -> all cross-repo steps |
| import ID | `imp-<uuidv4>` create-new | NP-02 -> provenance/build gates |
| audit ID | `audit-<uuidv4>` create-new per skill/provider audit | NP-04..NP-10 -> release/qualification |
| candidate ID | `cand-<target-id>-<40-lowerhex-tip>` | each code step -> later target frontier, NP-36..NP-41 |
| baseline ID | `base-<64-lowerhex>`, SHA-256 of canonical baseline-fingerprint JSON listed in §5.2 | NP-15/NP-16 -> NP-18..NP-20, NP-34, NP-39..NP-41 |
| request/attempt/run IDs | independent lowercase canonical UUIDv4 values; no reuse across roles | NP-11/NP-39 and runners -> receipts/telemetry/packet |
| release ID | `r-<64-lowerhex>`, where the suffix is SHA-256 of canonical release-manifest payload bytes with the `release_id` member omitted; verification removes that member, recanonicalizes, and requires equality | NP-37 -> NP-38..NP-41/cutover |

All ID comparisons are byte-exact after the declared lowercase normalization. Duplicate generation,
case-fold collision, or a value that does not match its producer's content is corruption and stops;
no code guesses, renames, or merges IDs.

### 5.8 Workspace resolution, candidate lineage, and repository gates

`config/workspace-targets.json`, validated by `schemas/workspace-targets-v1.schema.json`, is the
committed authority for every repo-qualified alias. Each row contains schema version, stable lowercase
`target_id`, `git_owner_target_id`, `path_within_git_owner`, expected `owner/name` remote and default
branch, `root_id`, `root_role`, `resolution_kind=signoff-cwd|coding-root-relative`, required
cardinality, mutation class, live-discovery flag, and `gate_profile_id`. The closed target set is
`skill-mesh`, `coding-root`, `dev-observatory`, `switchboard`, `career-ops`, `on-brand`,
`measure-twice`, `b2_project_goblin`, `citation-needed`, `heads-up`, `tripwire`, `same-page`,
`changed-check`, `paper-trail`, `find-again`, and `mesh-lens`. Dev Observatory and Switchboard use
`git_owner_target_id=coding-root` and their subdirectory paths; they are not separate Git owners.
The committed registry has two rows for `target_id=skill-mesh`, one for each exact root role below;
every other target ID occurs once.

The registry's frozen remote/default-branch expectations are:

| Git owner targets | Expected remote | Default branch |
|---|---|---|
| `skill-mesh` | `aberson/skill-mesh` | `main` |
| `coding-root` (owns `dev-observatory` and `switchboard`) | `aberson/coding-root` | `master` |
| `career-ops` | `santifer/career-ops` | `main` |
| `on-brand`, `measure-twice`, `b2_project_goblin`, `citation-needed`, `heads-up`, `tripwire`, `same-page`, `changed-check`, `paper-trail`, `find-again`, `mesh-lens` | matching `aberson/<target-id>` | `master` |

Machine-local absolute paths exist only in
`%LOCALAPPDATA%\SkillMesh\State\workspace-roots-v1.json`. Each row binds the committed registry hash
and target/root ID plus root role to canonical local path, resolved Git top-level, remote/default
branch, current ref/HEAD/tree, index hash, status-manifest hash, and observation time. Resolution stops
on missing targets, containment escape, unexpected Git owner, remote mismatch, duplicate canonical
paths, cardinality mismatch, or nested-repository mismatch. `utility-roots-v1.json` references these
target IDs instead of creating a second path authority.

The `skill-mesh` target is the one intentional two-root exception; every other root ID has exactly one
row. The create-new registry must contain exactly one row for each of these roles:

| Root ID | Role | Location authority | Consumers |
|---|---|---|---|
| `skill-mesh-signoff-source` | `signoff-source` | the clean worktree from which the approved plan/Approval-1 recorder runs | approval/blob validation, issue synchronization, and the first isolated implementation-worktree seed; never installation |
| `skill-mesh-active-main` | `active-main` | `<coding-root>\skill-mesh`, with remote `aberson/skill-mesh` and branch `main` | NP-01 four-file adoption, NP-36 reviewed integration, repository-status verification, and final canonical fast-forward; never an implementation input before reconciliation |

Both rows share `target_id=skill-mesh` but have distinct canonical worktree paths and root IDs. They
must resolve to the same expected remote and Git common repository while preserving their independent
ref/HEAD/tree/index/status identities. Any missing, duplicate, swapped, or extra `skill-mesh` role
stops before issue synchronization.

Initial root bootstrap has one non-registry input: the current-machine coding root is exactly
`[IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'dev'))`. The Approval-1 recorder runs from the
clean Skill Mesh signoff worktree, resolves that worktree with `git rev-parse --show-toplevel`, and
then, before NP-01:

1. requires the derived coding-root path to be an existing ordinary directory whose Git top-level is
   itself and whose origin/default branch are `aberson/coding-root`/`master`;
2. reads `workspace-targets.json` and derives every non-Skill-Mesh local target only by joining the
   coding root with the row's fixed relative path; it never searches drives or guesses;
3. validates each derived target's containment, Git owner, remote, default branch, ref/HEAD/tree,
   index, and status manifest against the row, while recording the current signoff worktree exactly as
   `root_id=skill-mesh-signoff-source, role=signoff-source` and the derived coding-root checkout exactly
   as `root_id=skill-mesh-active-main, role=active-main`;
4. writes `workspace-roots-v1.json` create-new with UTF-8/no BOM and reopens/schema-validates it;
5. stores its byte length/SHA-256 in the Approval-1 receipt before `/repo-sync`.

Any mismatch stops the administrative bootstrap before issue or implementation mutation. A different
coding-root location is a new explicit machine-configuration input and receipt, not an inferred scan
or another program approval.

Candidate lineage lives in the schema-validated, atomically replaced
`%LOCALAPPDATA%\SkillMesh\State\GoalNP\candidate-registry-v1.json`. Each candidate records
`candidate_id=cand-<target-id>-<40-lowerhex-tip>`, owner/target/step IDs, exact predecessor candidate
IDs and commits, base/tip commit/tree/ref, ordered introduced commits, allowed/changed paths, logical
cwd, exact test argv/version/exit/time/evidence hashes, WIP inventory ID, before/after ref/index/status
hashes, and disposition `integrate-before-qualification|hold-for-approval2|verify-only`.

For every target, a step consumes the maximal completed candidate frontier among its declared
dependencies; with none, it consumes the NP-01 baseline. Multiple tips require an explicit reviewed
integration commit in Plan-ID order. The step then commits only declared paths and records the output
tip. It never starts from an active checkout or inferred branch. Exact live-candidate handoffs are:

- coding-root: NP-01 baseline -> NP-21 -> NP-27 -> NP-28 -> NP-29 -> NP-30 -> NP-33 -> NP-35;
- Career Ops: NP-01 baseline -> NP-22;
- On Brand: NP-01 baseline -> NP-23;
- Measure Twice: NP-01 baseline -> NP-24.

Those four tips remain unmerged through NP-41. Mesh Lens hands off NP-21 -> NP-31 -> NP-32 ->
NP-36. Skill Mesh uses the general dependency-frontier rule and converges its reviewed tips at NP-36.

Every gate also runs `git diff --check` from its Git-owner root. Exact repository profiles are:

| Targets | Relative cwd | Bootstrap and required tests |
|---|---|---|
| `skill-mesh` | `.` | `python -m pip install pytest pyyaml`; `python -m pytest` |
| `career-ops` | `.` | `npm ci`; `node test-all.mjs`; `node --test tests/skill-parity/*.test.mjs` |
| `on-brand` | `.` | `npm ci`; `npx playwright install chromium`; `npm test`; `npm run typecheck` |
| `measure-twice` | `.` | `uv sync --frozen --extra dev`; `uv run pytest -q`; `uv run ruff check .`; `uv run mypy --strict measure_twice`; `uv run mt validate suites/smoke.json` |
| `heads-up`, `same-page`, `changed-check`, `paper-trail`, `find-again`, `mesh-lens` | `.` | `uv sync --frozen --extra dev`; `uv run pytest -q`; `uv run ruff check .`; `uv run mypy --strict src` |
| `tripwire` | `.` | `uv sync --frozen --extra dev`; `uv run pytest -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy --strict src` |
| `b2_project_goblin` | `.` | `uv sync --frozen`; `uv run pytest`; `uv run ruff check`; `uv run mypy src` |
| `citation-needed` | `.` | `uv sync --frozen`; `uv run pytest`; `uv run ruff check .`; `uv run mypy src` |
| `switchboard` | `switchboard` | `uv sync --frozen --extra dev`; `uv run pytest -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy --strict switchboard` |
| `dev-observatory` | `dev-observatory` | `uv sync --frozen`; `uv run pytest -q`; `uv run ruff check .`; `uv run mypy src --strict` |

Keep the first-cutover prior release and backup for at least 30 days **and** 10 successful normal
activations/invocations, whichever is later. Rotation never deletes an active release, an unresolved
failure, or evidence referenced by the current state/Approval-2 packet.

## 6. Plan Steps

Implementation issues are blank before Approval 1. `/repo-sync --scope both` creates/enriches 41 step
issues plus one umbrella in `aberson/skill-mesh`; the administrative recorder backfills only each `**Issue:** #` field and seals
the issue-sync receipt after signoff. Code steps use scoped worktrees and path-specific staging.
Operator steps invoke frozen commands; they do not author or repair code. Paths in `Files` are
repo-qualified; a path marked `(new)` does not exist yet.

### Step 1: Reconcile overlapping WIP and adopt the four Step 4 files

- **Plan ID:** `NP-01`
- **Status:** NOT STARTED
- **Problem:** Skill Mesh main has four preserved files dirty, while the coding root and owner repos have dirty bytes on Goal NP paths.
- **Type:** code
- **Issue:** #
- **Depends on:** Approval 1
- **Files:** `skill-mesh/config/workspace-targets.json`, `skill-mesh/schemas/{approval1-v1,issue-sync-v1,workspace-targets-v1}.schema.json`, `skill-mesh/schemas/{workspace-roots-v1,candidate-registry-v1,wip-inventory-v1}.schema.json` (new), `skill-mesh/plan.md`, `skill-mesh/documentation/{native-parity-approval1-journal.md,native-parity-wip-inventory.md}` (new where absent), `skill-mesh/documentation/phase-75-baseline.md`, `skill-mesh/tests/distributions/test_distributions.py`, `skill-mesh/tests/distributions/test_legacy_migration.py`, `skill-mesh/tools/install-skill-mesh.ps1`, `skill-mesh/tools/migrate-legacy-install.ps1`, external `%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\approval1\{approval1-v1,issue-sync-v1}.json` (read-only)
- **Produces:** validated workspace/local-root/candidate registries, frozen Git commit/tree/status identities for every target, `%LOCALAPPDATA%\SkillMesh\Recovery\GoalNP\<inventory-id>\**`, a schema-valid hash-bound WIP classification, and a four-file adoption commit in an isolated Skill Mesh worktree
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** Approval-1 and issue-sync receipts, their ancestry/allowlisted diff, all workspace aliases, Git owners/remotes, and baseline records validate before mutation; every overlapping path is exported/classified; committed source comes only from frozen Git blobs; dirty/live-only adoption input comes only from the hashed recovery bundle; the four files match the cited recovery record before review; focused and root tests pass; source working bytes remain unchanged.

Re-enumerate the currently observed coding-root dirty set rather than trusting its old count. Classify
each overlap as `adopt-to-canonical`, `preserve-foreign`, `already-owned-implementation`, or
`superseded`. No byte is overwritten without a recovery copy.

### Step 2: Import canonical support assets with a one-shot importer

- **Plan ID:** `NP-02`
- **Status:** NOT STARTED
- **Problem:** The manifest declares 62 per-skill support-asset destinations, but 61 are absent and the builder emits only adapters/cores.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-01
- **Files:** `skill-mesh/tools/import-legacy-support-assets.py` (new), `skill-mesh/tools/build-distributions.ps1`, `skill-mesh/schemas/support-import-ledger-v1.schema.json` (new), `skill-mesh/config/skill-manifest.json`, every exact `skill-mesh/<support_assets[*].dest>` declared there, `skill-mesh/skills/inventory.json`, `skill-mesh/_shared/**`, frozen `coding-root@<np01-coding-root-commit>:.claude/skills/**` Git blobs (read-only), frozen `coding-root@<np01-coding-root-commit>:.claude/skills-gpt/**` Git blobs (read-only), `%LOCALAPPDATA%\SkillMesh\Recovery\GoalNP\<inventory-id>\adopt-to-canonical\**` (read-only classified input), `skill-mesh/tests/package-integrity/test_skill_tree.py`, `skill-mesh/tests/distributions/test_distributions.py`, `skill-mesh/documentation/architecture.md`
- **Produces:** canonical asset tree and schema-valid source/destination SHA-256 import ledger
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** every imported byte has one validated ledger row; all declared destinations exist; references resolve; normal builds read canonical files only; missing/collision/unlisted paths fail; two builds are byte-identical; tests pass.

Keep `gen_manifest.py` hermetic. The separate importer reads exported/frozen bytes, never the live
Claude junction target, and is not a normal build input after its one-time, hash-bound use.

### Step 3: Replace the active GPT/Copilot schema with native Codex

- **Plan ID:** `NP-03`
- **Status:** NOT STARTED
- **Problem:** Active manifests, provider contracts, docs, and tests still name `gpt` and encode Copilot/router assumptions.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-02
- **Files:** `skill-mesh/config/skill-manifest.json`, `skill-mesh/config/model-mapping.json`, `skill-mesh/config/model-tier-map.json`, `skill-mesh/skills/inventory.json`, `skill-mesh/tools/gen_manifest.py`, `skill-mesh/tools/gen_skill_tree.py`, `skill-mesh/tools/build-distributions.ps1`, `skill-mesh/README.md`, `skill-mesh/CLAUDE.md`, `skill-mesh/documentation/architecture.md`, `skill-mesh/documentation/host-discovery.md`, `skill-mesh/documentation/migration.md`, `skill-mesh/documentation/troubleshooting.md`, `skill-mesh/documentation/providers/{README.md,gpt.md,codex.md}`, `skill-mesh/documentation/host-parity-repair-plan.md`, `skill-mesh/tests/package-integrity/{test_manifest_contract.py,test_skill_tree.py,test_host_discovery.py}`, `skill-mesh/tests/distributions/test_distributions.py`
- **Produces:** provider key `codex`, `providers/codex.md` contract, `dist/codex` contract, explicit Claude-native exclusions
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** active contracts use Claude/Codex vocabulary; history stays labeled historical; observed identity is never inferred from a tier; tests pass.

Only repo/staged instruction templates change here. Active coding-root `AGENTS.md`, workspace
instructions, live ledgers, and discovery roots remain untouched until Approval 2. Approval 1 also
marks `documentation/host-parity-repair-plan.md` superseded/historical so it cannot compete for these
paths.

### Step 4: Build the native adapter generator and contract

- **Plan ID:** `NP-04`
- **Status:** NOT STARTED
- **Problem:** Forty-seven hand-maintained wrappers would recreate drift after provider renaming.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-03
- **Files:** `skill-mesh/tools/build-distributions.ps1`, `skill-mesh/templates/skills/{claude,codex}/SKILL.md.tmpl` (new), `skill-mesh/config/skill-manifest.json`, `skill-mesh/schemas/native-adapter-audit-v1.schema.json` (new), `skill-mesh/tests/distributions/test_distributions.py`, `skill-mesh/tests/package-integrity/test_skill_tree.py`, `skill-mesh/documentation/native-adapter-audit.md` (new)
- **Produces:** generated Claude/Codex shell contract, bounded exception mechanism, and schema-valid audit ledger
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** generated `SKILL.md` requires the co-located `core.md`; provider fragments are explicit; exception entries are schema-bound; core-only canary and forbidden-token fixtures pass; root tests pass.

### Step 5: Retarget portable adapters, cohort A

- **Plan ID:** `NP-05`
- **Status:** NOT STARTED
- **Problem:** The first bounded adapter cohort still contains generic GPT/Copilot/router assumptions.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-04
- **Files:** `skill-mesh/skills/{build-phase,build-queue,build-step,goblin-do,goblin-suggest,judge-ui,lesson-harvest,memory-distill,observatory-doctor,plan-expedite,plan-feature,plan-init,plan-merge,plan-redline,plan-review,plan-trim}/providers/{claude,codex}.md`, `skill-mesh/documentation/native-adapter-audit.md`, `skill-mesh/tests/distributions/test_distributions.py`
- **Produces:** 16 audited native adapter pairs and ledger rows
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** each named core has both native adapters; only host tool/permission/presentation differences remain; Copilot/router/fallback claims are absent; focused and root tests pass.

### Step 6: Retarget portable adapters, cohort B

- **Plan ID:** `NP-06`
- **Status:** NOT STARTED
- **Problem:** The second bounded adapter cohort still contains generic GPT/Copilot/router assumptions.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-05
- **Files:** `skill-mesh/skills/{plan-wrap,repo-init,repo-sync,repo-update,research-prospect,review-deep,review-gauntlet,review-proof,review-uat,session-wrap,skill-eval-setup,skill-evolve,skill-iterate,task-handoff,test-prune,tier-escalate}/providers/{claude,codex}.md`, `skill-mesh/documentation/native-adapter-audit.md`, `skill-mesh/tests/distributions/test_distributions.py`
- **Produces:** 16 audited native adapter pairs and ledger rows
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** each named core has both native adapters; only host tool/permission/presentation differences remain; Copilot/router/fallback claims are absent; focused and root tests pass.

### Step 7: Retarget portable adapters, cohort C

- **Plan ID:** `NP-07`
- **Status:** NOT STARTED
- **Problem:** The final bounded adapter cohort still contains generic GPT/Copilot/router assumptions.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-06
- **Files:** `skill-mesh/skills/{tier-offload,user-afterparty,user-brainstorm,user-debug,user-draft,user-gateway,user-lavishify,user-learn,user-orient,user-pm,user-project,user-shakedown,user-uat,user-walkthrough,user-wrap}/providers/{claude,codex}.md`, `skill-mesh/documentation/native-adapter-audit.md`, `skill-mesh/tests/distributions/test_distributions.py`
- **Produces:** 15 audited native adapter pairs and a complete 47-skill migration ledger
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** all 47 portable cores have both adapters; the audit ledger is complete; forbidden active Copilot/router/fallback claims are absent; focused and root tests pass.

### Step 8: Promote `build-observer` and `repo-wrap`

- **Plan ID:** `NP-08`
- **Status:** NOT STARTED
- **Problem:** Two global custom workflows are outside the canonical catalog.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-03, NP-07
- **Files:** frozen `coding-root@<np01-coding-root-commit>:.claude/skills/{build-observer,repo-wrap}/**` Git blobs and `%LOCALAPPDATA%\SkillMesh\Recovery\GoalNP\<inventory-id>\adopt-to-canonical\.claude\skills\{build-observer,repo-wrap}\**` (read-only), `skill-mesh/skills/{build-observer,repo-wrap}/**`, `skill-mesh/config/skill-manifest.json`, `skill-mesh/skills/inventory.json`, `skill-mesh/tests/package-integrity/{test_manifest_contract.py,test_skill_tree.py}`, `skill-mesh/tests/distributions/test_distributions.py`
- **Produces:** two provenance-bound portable packages
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** each package has one canonical core/assets and two adapters; frozen/imported provenance rehashes; package, distribution, and root tests pass.

### Step 9: Promote the four Citation Needed skills

- **Plan ID:** `NP-09`
- **Status:** NOT STARTED
- **Problem:** The four related citation workflows are outside the canonical catalog.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-08
- **Files:** frozen `coding-root@<np01-coding-root-commit>:.claude/skills/{citation-distill,citation-review,citation-sweep,citation-triage}/**` Git blobs and `%LOCALAPPDATA%\SkillMesh\Recovery\GoalNP\<inventory-id>\adopt-to-canonical\.claude\skills\{citation-distill,citation-review,citation-sweep,citation-triage}\**` (read-only), `skill-mesh/skills/{citation-distill,citation-review,citation-sweep,citation-triage}/**`, `skill-mesh/config/skill-manifest.json`, `skill-mesh/skills/inventory.json`, `skill-mesh/tests/package-integrity/{test_manifest_contract.py,test_skill_tree.py}`, `skill-mesh/tests/distributions/test_distributions.py`
- **Produces:** four provenance-bound portable packages
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** each package has one canonical core/assets and two adapters; their declared dependency closure is exact; package, distribution, and root tests pass.

### Step 10: Promote `goblin-sweep`

- **Plan ID:** `NP-10`
- **Status:** NOT STARTED
- **Problem:** The final global custom workflow is outside the canonical catalog.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-09
- **Files:** frozen `coding-root@<np01-coding-root-commit>:.claude/skills/goblin-sweep/**` Git blobs and `%LOCALAPPDATA%\SkillMesh\Recovery\GoalNP\<inventory-id>\adopt-to-canonical\.claude\skills\goblin-sweep\**` (read-only), `skill-mesh/skills/goblin-sweep/**`, `skill-mesh/config/skill-manifest.json`, `skill-mesh/skills/inventory.json`, `skill-mesh/tests/package-integrity/{test_manifest_contract.py,test_skill_tree.py}`, `skill-mesh/tests/distributions/test_distributions.py`
- **Produces:** one provenance-bound portable package and complete seven-skill promotion ledger
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** the pre-ablation catalog is 57 Claude/54 Codex; the package has one canonical core/assets and two adapters; package, distribution, and root tests pass.

### Step 11: Build native profiles and the substrate-proof runner

- **Plan ID:** `NP-11`
- **Status:** NOT STARTED
- **Problem:** Placement, package loading, dependency closure, catalog size, auth, and containment need a bounded real-host proof before installer work.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-07, NP-10
- **Files:** `skill-mesh/config/model-profiles.json` (new), `skill-mesh/tools/build-distributions.ps1`, `skill-mesh/tools/run-native-substrate-proof.ps1` (new), `skill-mesh/tools/native-host-runtime.py` (new), `skill-mesh/schemas/{model-profiles-v1,native-preflight-attempt-v1,native-preflight-aggregate-v1,native-substrate-proof-request-v1,native-attempt-index-event-v1,native-substrate-attempt-receipt-v1,native-substrate-aggregate-v1}.schema.json` (new), `skill-mesh/tests/native-host/{test_runtime.py,test_profile_discovery.py,test_catalog_budget.py,test_attempt_lineage.py}` (new), `skill-mesh/tests/distributions/test_distributions.py`, `skill-mesh/documentation/native-substrate-proof.md` (new), external `%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\native-substrate-proof\requests\<request-id>\request.json` (create-new)
- **Produces:** deterministic profiles, D08 exact profile/role map, collision/budget report, fixture, schema-valid hash-bound request, attempt/index/aggregate contracts, and exact Preflight/Run/Resume/Finalize commands
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** D08's four exact requests/efforts/roles validate with no substitution; builds match; names are unique; `_shared` has no `SKILL.md`; exact production serialization of Skill Mesh name/description/source metadata is at most 7,500 UTF-8 characters; fake-host auth/containment/cleanup, INCOMPLETE-to-PASS lineage, terminal FAIL/INVALID, fork/tamper/concurrency refusal, both aggregate crash windows, and recovery tests pass; request is create-new/hash-bound to the registry's `skill-mesh` cwd and commit.

The proof also requires every then-current global name to remain listed and explicitly selectable
beside system, plugin, and repo-local skills with no truncation/omission warning. Use minimal
environments, allowlisted credential projection into disposable homes, auth preflight,
process-tree containment, bounded time/output, no fallback, and cleanup. Credential bytes/hashes never
enter evidence. Only disposable host state may change.

### Step 12: Run the disposable native substrate proof

- **Plan ID:** `NP-12`
- **Status:** NOT STARTED
- **Problem:** Simulated packages cannot prove real Claude/Codex discovery and core behavior.
- **Type:** operator
- **Issue:** #
- **Depends on:** NP-11
- **Files:** external `%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\native-substrate-proof\requests\<request-id>\**` only: immutable `request.json`; `preflight-index.jsonl`, immutable `preflight-attempts/<attempt-id>/receipt.json`, and terminal `preflight.json`; proof `attempt-index.jsonl`; immutable `attempts/<attempt-id>/receipt.json` plus manifest-bound raw evidence; and terminal aggregate `receipt.json`
- **Produces:** hash-chained attempt lineage and one terminal `native-substrate-aggregate-v1` receipt plus manifest-bound Claude/Codex raw evidence
- **Flags:** (operator — no `/build-step`)
- **Commands to run:** from the request-bound `skill-mesh` registry root/commit, run the exact command block below.
- **Done when:** terminal `receipt.json` validates against the committed aggregate schema, binds the exact request/profile/cwd/commit fingerprints and full attempt-index length/SHA-256, records `PASS`, and both host records prove discovery path, wrapper/core/adapter hashes, core-only canary, asset/script resolution, named-skill call, full then-current catalog visibility, contained effects, no fallback, cleanup, and honest telemetry coverage; every attempt, manifest, and referenced evidence hash rehashes.

```powershell
gh auth status
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-substrate-proof.ps1 -Action Preflight -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-substrate-proof\requests\<request-id>\request.json"
if ($LASTEXITCODE -ne 0) { throw 'Native substrate preflight did not PASS; do not start Run.' }
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-substrate-proof.ps1 -Action Run -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-substrate-proof\requests\<request-id>\request.json"
```

Preflight runs each host's auth-status command and one bounded `reply with the single word ok` call for
each of the four exact D08 profiles inside disposable homes, with no fallback, and records
requested/reported identity and cleanup. Transient auth, quota, or availability returns `INCOMPLETE`
before any proof cell starts; unsupported/mismatched exact profile is terminal `INVALID`.

An INCOMPLETE Preflight prints `PREFLIGHT_ATTEMPT_ID`, `PREFLIGHT_RECEIPT_SHA256`, and this fully
substituted retry. A PASS retry prints the exact Run command; the operator does not rerun the original
two-command block.

```powershell
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-substrate-proof.ps1 -Action PreflightResume -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-substrate-proof\requests\<request-id>\request.json" -ParentPreflightAttemptId "<attempt-id>" -ParentPreflightReceiptSha256 "<64-lowerhex>"
```

For controlled `INCOMPLETE`, the runner prints `ATTEMPT_ID`, `ATTEMPT_RECEIPT_SHA256`, and this fully
substituted command; the operator runs it verbatim:

```powershell
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-substrate-proof.ps1 -Action Resume -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-substrate-proof\requests\<request-id>\request.json" -ParentAttemptId "<attempt-id>" -ParentReceiptSha256 "<64-lowerhex>"
```

If `Inspect` finds a closed terminal attempt after an aggregate-creation crash, it prints an exact
zero-host-call command. No parent is auto-selected:

```powershell
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-substrate-proof.ps1 -Action Finalize -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-substrate-proof\requests\<request-id>\request.json" -TerminalAttemptId "<attempt-id>" -TerminalReceiptSha256 "<64-lowerhex>"
```

This is execution, not a new approval. A valid native placement/core-load contradiction invalidates
the architecture. Authentication/quota is `INCOMPLETE` and creates no aggregate; a runner/protocol
defect returns to NP-11, invalidates the request/lineage, and reruns only after a reviewed correction.
The corrected request uses a new UUID directory and preserves the old one. `FAIL` or `INVALID` creates
a terminal aggregate and the unchanged request cannot retry. Later steps
require the exact PASS aggregate and cannot substitute pointers, copied prompts, or a router.

### Step 13: Build transaction state, locking, and crash recovery

- **Plan ID:** `NP-13`
- **Status:** NOT STARTED
- **Problem:** Two mixed-ownership discovery roots need a cross-root transaction and concurrent-activation protection.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-12 PASS receipt
- **Files:** `skill-mesh/tools/skill-mesh-transaction.ps1`, `skill-mesh/tools/skill-mesh-provenance.ps1`, `skill-mesh/schemas/{profiles-v1,transaction-journal-v1,release-manifest-v1,native-attempt-index-event-v1,native-substrate-attempt-receipt-v1,native-substrate-aggregate-v1}.schema.json` (new where absent), `skill-mesh/tests/distributions/{test_transactions.py,test_path_choke_point.py}`, `skill-mesh/tests/package-integrity/test_manifest_contract.py`, external `%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\native-substrate-proof\requests\<request-id>\**` (read-only; exact PASS request ID from NP-12)
- **Produces:** exclusive activation lock, phase journal, immutable release/state schema, recovery engine
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** the exact NP-12 PASS aggregate, bound index prefix/length/hash, every attempt receipt/manifest, D08 profile hash, and absence of post-final bytes validate before mutation; recovery works from every phase; concurrent activation loses before mutation; attacks/corruption stop honestly; injected failure restores exact bytes; tests pass. Editing the reused ledger/schema/runtime semantics invalidates NP-12 and requires a new request/run.

### Step 14: Retarget install, inspect, migrate, retire, and rollback

- **Plan ID:** `NP-14`
- **Status:** NOT STARTED
- **Problem:** Legacy tools target `.github/skills`, have a hashless ledger, and cannot safely preserve mixed Claude content.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-13
- **Files:** `skill-mesh/tools/sync-skills.ps1` (new), `skill-mesh/tools/install-skill-mesh.ps1`, `skill-mesh/tools/migrate-legacy-install.ps1`, `skill-mesh/tools/inspect-host-install.ps1`, `skill-mesh/tools/skill-mesh-discovery.ps1`, `skill-mesh/tools/skill-mesh-provenance.ps1`, `skill-mesh/tools/skill-mesh-transaction.ps1`, `skill-mesh/tests/distributions/{test_distributions.py,test_host_inspect.py,test_legacy_migration.py,test_path_choke_point.py,test_transactions.py}`, `skill-mesh/tests/package-integrity/test_host_discovery.py`, `skill-mesh/documentation/{migration.md,host-discovery.md,troubleshooting.md}`
- **Produces:** one prepare/inspect/activate/rollback CLI and legacy-Copilot classification
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** dry-run, install, idempotent update, modified-managed refusal, stale retirement, crash recovery, uninstall, and rollback pass in temp homes; Claude junction/consumer files survive; Codex uses ordinary files; repos stay unchanged.

Resolve Codex home once from the effective Codex process environment. `HOME`/`USERPROFILE`
disagreement stops unless an explicit reviewed override selects one root used by all children/receipts.

### Step 15: Define model profiles, eval schemas, and the Pareto gate

- **Plan ID:** `NP-15`
- **Status:** NOT STARTED
- **Problem:** Current maintenance conflates intent, identity, host family, scalar scores, and stale baselines.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-07, NP-11
- **Files:** `skill-mesh/config/model-profiles.json`, `skill-mesh/config/shared-core-maintenance-policy.json` (new), `skill-mesh/config/skill-evaluation-inventory.json` (new), `skill-mesh/schemas/{model-profiles-v1,evaluation-policy-v1,evaluation-run-v1}.schema.json` (new where absent), `skill-mesh/tools/evaluate-skill-matrix.py` (new), `skill-mesh/tests/evaluation/{test_policy.py,test_matrix_contract.py,test_pareto_gate.py}` (new), `skill-mesh/documentation/skill-maintenance.md` (new)
- **Produces:** executable model, fingerprint, metric-vector, acceptance, identity, and resume contracts
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** configs contain supported requests; baseline/candidate profiles match; exact-model claims require reported identity; functional host-profile claims show unavailable identity honestly; margins/gains/uncertainty are executable; regression/missing cell/stale fingerprint/fallback/disagreement cannot pass.

High-impact work freezes exact requests; aliases/defaults cannot qualify it. CLI/profile changes force
matched rebaseline and calibration. Multiple safe candidates yield a blinded Pareto frontier for
operator choice, not an automatic merge.

### Step 16: Implement the disposable dual-host evaluation matrix

- **Plan ID:** `NP-16`
- **Status:** NOT STARTED
- **Problem:** Current trials regrade one render and use invoking-host agents rather than both production hosts.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-11, NP-14, NP-15
- **Files:** `skill-mesh/tools/native-host-runtime.py`, `skill-mesh/tools/skill-eval-host.py` (new), `skill-mesh/tools/evaluate-skill-matrix.py`, `skill-mesh/schemas/evaluation-run-v1.schema.json`, `skill-mesh/tests/evaluation/{test_host_runner.py,test_profile_execution.py,test_matrix_contract.py,fixtures/**}` (new)
- **Produces:** resumable immutable real/fake-host matrix
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** every trial rerenders; labels/order are blind; credential, containment, default-deny network, untrusted-input, timeout/output/attempt, identity, resume, and cleanup tests pass; missing cells stay indeterminate.

### Step 17: Retarget `skill-eval-setup`

- **Plan ID:** `NP-17`
- **Status:** NOT STARTED
- **Problem:** Eval setup emits a same-host loop and still contains incomplete generator/scorer seams.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-02, NP-15, NP-16
- **Files:** `skill-mesh/skills/skill-eval-setup/**`, `skill-mesh/_shared/score-skill.md`, `skill-mesh/tests/evaluation/{test_eval_setup.py,test_matrix_contract.py,fixtures/**}` (new where absent)
- **Produces:** one matrix-owned eval authoring/bootstrap path with complete deterministic seams
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** generated evals target the common matrix; missing goldens/axes cannot qualify; golden and garbage anchors catch planted defects; focused and root tests pass.

### Step 18: Retarget `skill-evolve`

- **Plan ID:** `NP-18`
- **Status:** NOT STARTED
- **Problem:** Skill Evolve mutates the baseline, leaks labels, accepts stale results, and selects on one scalar.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-17
- **Files:** `skill-mesh/skills/skill-evolve/**`, `skill-mesh/_shared/score_skill.workflow.js`, `skill-mesh/_shared/score_skill_{absolute,composite}.py`, `skill-mesh/tests/evaluation/{test_skill_evolve.py,test_policy.py,test_pareto_gate.py}` (new where absent)
- **Produces:** exact-baseline, blinded, dual-host Pareto evolution path
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** baseline bypasses mutation; qualifier prompts stay sealed; labels/order are opaque; trials rerender; stale fingerprints and host regressions cannot pass; focused and root tests pass.

### Step 19: Retarget `skill-iterate`

- **Plan ID:** `NP-19`
- **Status:** NOT STARTED
- **Problem:** Skill Iterate pins one editor family, regrades fixed renders, and ships from a scalar score.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-18
- **Files:** `skill-mesh/skills/skill-iterate/**`, `skill-mesh/_shared/score_skill.workflow.js`, `skill-mesh/_shared/score_skill_{absolute,composite}.py`, `skill-mesh/tests/evaluation/{test_skill_iterate.py,test_policy.py,test_pareto_gate.py}` (new where absent)
- **Produces:** routine-only, current-editor maintenance path with automatic high-impact escalation
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** every trial rerenders; initiating host is recorded rather than pinned; semantic deletion routes to high-impact evaluation; host-only wins do not mutate shared core; focused and root tests pass.

### Step 20: Create the native `skill-ablation` workflow

- **Plan ID:** `NP-20`
- **Status:** NOT STARTED
- **Problem:** No operator workflow safely removes instruction groups from a shared core.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-19
- **Files:** `skill-mesh/skills/skill-ablation/**` (new), `skill-mesh/config/skill-manifest.json`, `skill-mesh/skills/inventory.json`, `skill-mesh/config/skill-evaluation-inventory.json`, `skill-mesh/tests/evaluation/test_skill_ablation.py` (new), `skill-mesh/tests/package-integrity/{test_manifest_contract.py,test_skill_tree.py}`
- **Produces:** core, two adapters, evals, matrix request/report contract
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** input selects one skill/claim/contiguous group; baseline is byte-copied; both families propose blinded candidates; source/live files stay unchanged; output is reject/indeterminate/Pareto frontier; catalog is 58 Claude/55 Codex; forward/planted-regression tests pass.

Use `skill-creator` for structure. The skill delegates all host launch, grading, and acceptance to the
common matrix.

### Step 21: Freeze utility bindings and bootstrap state contracts

- **Plan ID:** `NP-21`
- **Status:** NOT STARTED
- **Problem:** The 13-project utility map lacks one executable, machine-neutral binding and bootstrap contract.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-10, NP-14
- **Files:** `skill-mesh/config/utility-bindings.json` (new), `skill-mesh/schemas/{utility-binding-v1,utility-roots-v1,utility-runtime-v1}.schema.json` (new), `skill-mesh/tools/configure-utility-roots.ps1` (new), `skill-mesh/tests/utilities/{test_binding_schema.py,test_bootstrap_contract.py,test_b2_project_goblin.py,test_citation_needed.py,test_dev_observatory.py,test_switchboard.py}` (new), candidate-worktree `coding-root/same-page.toml` (new), candidate-worktree `coding-root/find-again.toml` (new), candidate-worktree `coding-root/.changed-check.toml` (new), candidate-worktree `coding-root/decisions/**` (NP-01-classified existing/untracked input plus bounded new records), `mesh-lens/tests/fixtures/telemetry-v2/**` (new), external `%LOCALAPPDATA%\SkillMesh\State\GoalNP\candidate-registry-v1.json` (read/write under schema)
- **Produces:** validated 13-row/39-cell inventory, 6-required/7-advisory and 13-called state contract, source-root and immutable runtime contracts, deterministic bootstrap fixtures, and the NP-21 coding-root candidate tip
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** every row names exact source root, runtime kind, release-relative entrypoint argv, hosts, policy, bounds, fixture, smoke, and evidence; all 13 fixture plus 26 host-smoke IDs are unique; coding-root Same Page and Changed Check configs always validate; Find Again initial index plus on-demand reindex work; Paper Trail stays suggested-only; Mesh Lens locators are bounded; focused and root tests pass.

Machine-local values are written only to disposable State roots during implementation. The listed
coding-root artifacts are staged in the frozen coding-root candidate and do not enter the active
checkout before Approval 2. The Approval-2 packet carries the exact inspected mapping;
`apply-native-cutover.ps1` installs the live State copy and applies the approved Same Page, Changed
Check, Paper Trail, Find Again initial-index, and Mesh Lens locator bootstrap. There is no separate
live bootstrap command.

### Step 22: Requalify Career Ops and create native `apply-sheet`

- **Plan ID:** `NP-22`
- **Status:** NOT STARTED
- **Problem:** Career Ops has one two-host skill but its Claude-only `apply-sheet` lacks a shared source and Codex package.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-21
- **Files:** `skill-mesh/tools/build-repo-local-skills.py` (new), `skill-mesh/config/repo-local-skill-inventory.json` (new), `career-ops/skills/{career-ops,apply-sheet}/**` (new canonical sources), candidate-worktree `career-ops/.claude/skills/{career-ops,apply-sheet}/**`, candidate-worktree `career-ops/.agents/skills/{career-ops,apply-sheet}/**` (new where absent), `career-ops/tests/skill-parity/**` (new)
- **Produces:** deterministic source-to-two-host generator contract and one unmerged Career Ops candidate ref
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** `apply-sheet` and `career-ops` each have one behavior source; generated shells resolve the same core/scripts; names are collision-free; both native fixture cells and owner tests pass; the checked-out Career Ops ref/index/worktree is byte-identical.

### Step 23: Create native `brand-fidelity`

- **Plan ID:** `NP-23`
- **Status:** NOT STARTED
- **Problem:** On Brand's Claude-only skill has no canonical repo-local source or Codex package.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-22
- **Files:** `skill-mesh/tools/build-repo-local-skills.py`, `skill-mesh/config/repo-local-skill-inventory.json`, `on-brand/skills/brand-fidelity/**` (new canonical source), candidate-worktree `on-brand/.claude/skills/brand-fidelity/**`, candidate-worktree `on-brand/.agents/skills/brand-fidelity/**` (new), `on-brand/test/brand-fidelity-native.test.ts` (new)
- **Produces:** one unmerged On Brand candidate ref with Claude/Codex packages from one source
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** both packages resolve the same core/assets; the unique-name inventory passes; both native fixture cells and owner tests pass; the checked-out On Brand ref/index/worktree is byte-identical.

### Step 24: Create native `change-benchmark`

- **Plan ID:** `NP-24`
- **Status:** NOT STARTED
- **Problem:** Measure Twice has no repo-local benchmark skill on either host.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-23
- **Files:** `skill-mesh/tools/build-repo-local-skills.py`, `skill-mesh/config/repo-local-skill-inventory.json`, `measure-twice/skills/change-benchmark/**` (new canonical source), candidate-worktree `measure-twice/.claude/skills/change-benchmark/**` (new), candidate-worktree `measure-twice/.agents/skills/change-benchmark/**` (new), `measure-twice/tests/test_change_benchmark_skill.py` (new)
- **Produces:** one unmerged Measure Twice candidate ref with Claude/Codex packages from one source
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** both packages resolve the same core/scripts; the unique-name inventory passes; both native fixture cells and owner tests pass; the checked-out Measure Twice ref/index/worktree is byte-identical.

All three candidate refs remain unmerged until Approval 2 because their package paths are native
repo-local discovery roots. Approval 1 authorizes isolated candidate worktrees, not activation.

#### Utility-owner repair boundary for NP-25 through NP-31

Listed utility-owner paths are read-only contract inputs unless the step's frozen real-contract test
fails at the recorded owner HEAD and evidence localizes the failure to an exact listed path. An
authorized repair may change only documented argv, exit, schema, timeout, output, or redaction
conformance plus the matching test/doc. It may not add a verb, feature, persistence, network/model
behavior, or unlisted path. Anything broader requires a plan amendment.

### Step 25: Wire Heads Up

- **Plan ID:** `NP-25`
- **Status:** NOT STARTED
- **Problem:** Heads Up has no complete native caller path for coordination claims.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-21, NP-24
- **Files:** `skill-mesh/skills/{plan-expedite,build-phase,session-wrap}/core.md`, `skill-mesh/tests/utilities/test_heads_up.py` (new), `heads-up/{src/heads_up/cli.py,tests/test_cli.py,docs/integration-contract.md}` (contract inputs; writable only under the Utility-owner repair boundary)
- **Produces:** bounded claims/release/renew callers and receipt fixtures
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** each planned call exists on both portable profiles; missing advisory state skips visibly; output is bounded/untrusted; real owner smoke and root tests pass.

### Step 26: Wire Tripwire

- **Plan ID:** `NP-26`
- **Status:** NOT STARTED
- **Problem:** Tripwire has no complete native preflight caller path.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-25
- **Files:** `skill-mesh/skills/{plan-expedite,build-phase,session-wrap}/core.md`, `skill-mesh/tests/utilities/test_tripwire.py` (new), `tripwire/{src/tripwire/cli.py,tests/test_cli.py,README.md}` (contract inputs; writable only under the Utility-owner repair boundary)
- **Produces:** bounded safety-preflight callers and receipt fixtures
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** required findings fail closed; advisory findings remain visible; utility output cannot become instructions; real owner smoke and root tests pass.

### Step 27: Wire Same Page

- **Plan ID:** `NP-27`
- **Status:** NOT STARTED
- **Problem:** Same Page has no complete native documentation-drift caller path.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-26
- **Files:** `skill-mesh/skills/{repo-update,session-wrap,plan-expedite}/core.md`, `skill-mesh/tests/utilities/test_same_page.py` (new), `same-page/{src/same_page/cli.py,tests/test_cli.py,README.md}` (contract inputs; writable only under the Utility-owner repair boundary), `coding-root/same-page.toml`
- **Produces:** bounded drift callers and receipt fixtures
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** absent config skips before spawn; configured invalid state is visible; output is bounded/untrusted; real owner smoke and root tests pass.

### Step 28: Wire Changed Check

- **Plan ID:** `NP-28`
- **Status:** NOT STARTED
- **Problem:** Changed Check is not called from the known planning/build quality seams.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-27
- **Files:** `skill-mesh/skills/{build-step,plan-expedite,session-wrap}/core.md`, `skill-mesh/tests/utilities/test_changed_check.py` (new), `changed-check/{src/changed_check/cli.py,tests/test_cli.py,docs/descriptor-reference.md}` (contract inputs; writable only under the Utility-owner repair boundary), `coding-root/.changed-check.toml`
- **Produces:** bounded informational change-plan callers and receipt fixtures
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** coding-root descriptor is present and valid; for any other target the exact §5.5 predicate controls zero-spawn absence versus visible invalid state; findings never narrow mandatory gates; JSON is bounded/untrusted; real owner smoke and root tests pass.

### Step 29: Wire Paper Trail

- **Plan ID:** `NP-29`
- **Status:** NOT STARTED
- **Problem:** Decision-history suggestions and audits remain disconnected from native skills.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-28
- **Files:** `skill-mesh/skills/{plan-redline,session-wrap,repo-update}/core.md`, `skill-mesh/tests/utilities/test_paper_trail.py` (new), `paper-trail/{src/paper_trail/cli.py,tests/test_cli.py,docs/decision-authoring-guide.md}` (contract inputs; writable only under the Utility-owner repair boundary), `coding-root/decisions/**` (NP-01-classified existing/untracked input plus bounded records)
- **Produces:** suggested-write and bounded read/audit seams with receipt fixtures
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** no skill executes `add`; suggested commands are complete; list/audit calls are bounded/redacted; real owner smoke and root tests pass.

### Step 30: Wire Find Again

- **Plan ID:** `NP-30`
- **Status:** NOT STARTED
- **Problem:** Retrieval remains disconnected from the five known native research/debug seams.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-29
- **Files:** `skill-mesh/skills/{plan-feature,plan-review,user-debug,lesson-harvest,memory-distill}/core.md`, `skill-mesh/tests/utilities/test_find_again.py` (new), `find-again/{src/find_again/{cli.py,config.py,indexer.py,search.py},tests/{test_cli.py,test_config.py,test_indexer.py,test_search.py},README.md}` (contract inputs; writable only under the Utility-owner repair boundary), `coding-root/find-again.toml`
- **Produces:** bounded top-k retrieval callers and receipt fixtures
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** config/index absence is explicit; on-demand reindex is deterministic; results are bounded evidence rather than instructions; real owner smoke and root tests pass.

### Step 31: Wire Mesh Lens

- **Plan ID:** `NP-31`
- **Status:** NOT STARTED
- **Problem:** Skill evidence has no single bounded native writer/report seam.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-30
- **Files:** `skill-mesh/skills/session-wrap/core.md`, `skill-mesh/tests/utilities/test_mesh_lens.py` (new), `mesh-lens/{src/mesh_lens/{cli.py,store.py,render.py,adapters/**},tests/{test_cli.py,test_store.py,test_render.py,test_adapter_skill_mesh.py},README.md}` (contract inputs; writable only under the Utility-owner repair boundary), `mesh-lens/tests/fixtures/telemetry-v2/**`
- **Produces:** one bounded end-window ingest/report caller and receipt fixtures
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** one writer window is explicit; missing/stale stores are visible; output stays bounded data; real owner smoke and root tests pass.

### Step 32: Implement telemetry v2 and Mesh Lens analytics

- **Plan ID:** `NP-32`
- **Status:** NOT STARTED
- **Problem:** Existing telemetry has ambiguous model and placeholder-zero fields with no lineage or coverage truth.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-15, NP-16, NP-21, NP-31
- **Files:** `skill-mesh/runtime/telemetry/{telemetry-writer.ps1,telemetry-summary.ps1}`, `skill-mesh/schemas/telemetry-v2.schema.json` (new), `skill-mesh/tests/telemetry/test_telemetry.py`, `mesh-lens/src/mesh_lens/{models.py,store.py,cli.py,adapters/skill_mesh.py}`, `mesh-lens/tests/{test_models.py,test_store.py,test_cli.py,test_adapter_skill_mesh.py}`, `mesh-lens/docs/telemetry-v2.md` (new)
- **Produces:** locked telemetry v2, legacy reader, Mesh Lens ingest/report, bounded Observatory export
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** concurrency is valid; null differs from measured zero; requested never populates reported; coverage is honest; prompts/outputs/secrets/private paths are absent; incompatible cohorts are refused; owner tests pass.

### Step 33: Add read-only Dev Observatory views

- **Plan ID:** `NP-33`
- **Status:** NOT STARTED
- **Problem:** Abraham needs truthful skill/utility/model status without making Observatory a runtime dependency.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-21, NP-32
- **Files:** `coding-root/.claude/observatory/registry.toml`, `coding-root/dev-observatory/src/dev_observatory/{model.py,view_sources.py,view_adapters.py,render_static.py,render_cli.py,cli.py,web/app.py}`, `coding-root/dev-observatory/tests/{test_model_single_source.py,test_view_sources.py,test_view_adapters.py,test_render_static.py,test_render_cli.py,test_web.py,test_cli.py,test_smoke_pipeline.py}`, `coding-root/dev-observatory/README.md`, `coding-root/dev-observatory/CLAUDE.md`, `mesh-lens/docs/telemetry-v2.md`
- **Produces:** skill-call, qualification, release/core, identity/fallback, binding, and coverage views on an isolated coding-root candidate branch
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** Observatory reads bounded producer artifacts only; rendering launches nothing; stale/malformed/unavailable are explicit; served/static match; all 13 utilities and managed skills are visible; owner tests pass; the active coding-root ref/index/worktree is byte-identical.

### Step 34: Build the parity-bound exhaustive eval inventory

- **Plan ID:** `NP-34`
- **Status:** NOT STARTED
- **Problem:** Unrelated green host tests do not prove shared behavior.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-20, NP-24, NP-31
- **Files:** `skill-mesh/config/skill-evaluation-inventory.json`, `skill-mesh/skills/*/evals/**`, `skill-mesh/tests/evaluation/{test_inventory_coverage.py,test_scenario_contract.py,fixtures/**}` (new), `skill-mesh/config/repo-local-skill-inventory.json`, candidate-worktree `career-ops/tests/skill-parity/**`, candidate-worktree `on-brand/test/brand-fidelity-native.test.ts`, candidate-worktree `measure-twice/tests/test_change_benchmark_skill.py`
- **Produces:** closed global/repo-local host-cell inventory with holdouts
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** shared cells bind both hosts to the same neutral scenario/hard assertions with additive provider assertions; exactly 110 shared plus 3 Claude-native global cells and 39 utility flow cells exist; local cells are explicit; each has success and critical/failure assertions; all 13 utility fixtures parameterize every declared hook; bad anchors are caught.

### Step 35: Prepare the frozen coding-root candidate

- **Plan ID:** `NP-35`
- **Status:** NOT STARTED
- **Problem:** Active workspace instructions, tracked generated Claude files, the tracked legacy ledger, managed Copilot files, and three older in-progress plans would otherwise contradict native ownership or retain competing execution authority.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-03, NP-14, NP-20, NP-21, NP-33
- **Files:** candidate-worktree `coding-root/AGENTS.md`, candidate-worktree `coding-root/.claude/workspace-instructions.md`, candidate-worktree `coding-root/.gitignore`, candidate-worktree `coding-root/.skill-mesh-install.json` (retire from tracked authority), candidate-worktree `coding-root/.github/skills/**` (only exact NP-01-classified managed paths), candidate-worktree `coding-root/.claude/skills/**` (only manifest-owned generated paths), candidate-worktree `coding-root/{same-page.toml,find-again.toml,.changed-check.toml,decisions/**}`, candidate-worktree `coding-root/documentation/{utility-hookup-plan.md,coding-root-closeout-plan.md}`, candidate-worktree `coding-root/.claude/observatory/registry.toml`, candidate-worktree `coding-root/dev-observatory/**`, including `coding-root/dev-observatory/plans/utility-project-surfaces-plan.md`, `skill-mesh/config/skill-manifest.json` (read-only), `skill-mesh/documentation/native-parity-coding-root-candidate.md` (new), external `%LOCALAPPDATA%\SkillMesh\State\GoalNP\candidate-registry-v1.json` (read/write under schema)
- **Produces:** one unmerged, fast-forwardable, hash-bound coding-root candidate, exact managed-file disposition, and a non-competing active-plan authority set
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** the candidate registry proves the exact NP-21 -> NP-27 -> NP-28 -> NP-29 -> NP-30 -> NP-33 -> NP-35 coding-root lineage and gate profile; active instructions name native Claude/Codex discovery; only exact generated Claude paths are untracked and ignored while consumer/private paths remain tracked and unchanged; the legacy repo ledger is retired in favor of LocalAppData state; only classified managed Copilot paths retire; utility/Observatory commits are included; completed/history sections in the three older plans remain intact while their Goal-NP-overlapping utility/host/cutover portions are explicitly superseded or rebound to this plan; no active plan still claims `.github/skills`, provider `gpt`, or old Step 70/71/utility live authority for these paths; coding-root tests pass; the active ref/index/worktree and unrelated WIP remain byte-identical.

The candidate records exact index operations rather than ignoring whole skill roots. Hosts stay closed
during live application: the candidate removes tracked generated outputs, then the transaction installs
the same frozen release into the now-ignored managed paths. Later qualified syncs must leave coding-root
status unchanged. `documentation/utility-hookup-plan.md`, `documentation/coding-root-closeout-plan.md`,
and `dev-observatory/plans/utility-project-surfaces-plan.md` remain historical evidence; only their
overlapping future authority is closed or rebound, never rewritten as though prior work did not happen.

### Step 36: Integrate reviewed source without live discovery mutation

- **Plan ID:** `NP-36`
- **Status:** NOT STARTED
- **Problem:** Qualification must use canonical reviewed heads while coding-root live Claude files cannot land before Approval 2.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-13, NP-14, NP-20, NP-24, NP-31, NP-32, NP-33, NP-34, NP-35
- **Files:** `skill-mesh/plan.md`, `skill-mesh/documentation/native-parity-wip-inventory.md`, `skill-mesh/documentation/native-parity-integration-report.md` (new), immutable reviewed commit sets under `skill-mesh/{skills,config,schemas,tools,runtime,tests,documentation}/**`, `heads-up/{src,tests,docs}/**`, `tripwire/{src,tests}/**`, `same-page/{src,tests}/**`, `changed-check/{src,tests,docs}/**`, `paper-trail/{src,tests,docs}/**`, `find-again/{src,tests}/**`, and `mesh-lens/{src,tests,docs}/**`; frozen unmerged candidates for `coding-root`, `career-ops`, `on-brand`, and `measure-twice`; external `%LOCALAPPDATA%\SkillMesh\State\GoalNP\candidate-registry-v1.json`
- **Produces:** clean non-live canonical heads, four unmerged fast-forwardable/hash-bound live-discovery candidates, and an immutable evidence copy/SHA-256 of the candidate registry
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** every predecessor graph, commit/tree/ref, logical cwd, exact command, and test receipt validates; Skill Mesh main contains the four-file adoption and is clean; non-live utility/Mesh Lens heads are clean; all four candidate refs are overlap-safe and unmerged; active live-discovery repos and unrelated WIP match NP-01 hashes; every head/tree is recorded and the frozen candidate-registry hash revalidates.

This restores Skill Mesh `repo-update`. It does not falsely claim the outer coding root is clean; unrelated
WIP remains reported.

### Step 37: Build the immutable release and offline gates

- **Plan ID:** `NP-37`
- **Status:** NOT STARTED
- **Problem:** Native qualification needs one frozen release with reproducible offline gates and commands.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-36
- **Files:** `skill-mesh/tools/{release.ps1,release_checks.py,build-distributions.ps1,build-utility-runtimes.py,sync-skills.ps1}` (`build-utility-runtimes.py` new), `skill-mesh/schemas/{profiles-v1,release-manifest-v1,utility-runtime-v1}.schema.json` (new where absent), `skill-mesh/tests/release/{test_release_script.py,test_utility_runtimes.py}` (`test_utility_runtimes.py` new), `skill-mesh/tests/smoke/test_cross_host_smoke.py` (new; final path), `skill-mesh/tests/package-integrity/**`, `skill-mesh/documentation/{release-candidate-report.md,native-claude-codex-cutover.md}` (new where absent), `skill-mesh/README.md`
- **Produces:** immutable native profiles and release-owned utility runtimes, quickstart, build-twice report, and offline gate receipt
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** build-twice, root, release, install/update/rollback, path, package, and documentation gates pass; every Python utility is built from the frozen owner commit/lock into a non-editable wheel-based release environment and On Brand into a lock-bound release bundle; runtime manifests bind source/lock/package/interpreter/entrypoint/installed-file hashes; no runtime launcher, `.pth`, import metadata, or dependency resolves to staging, a candidate worktree, an owner checkout, or ambient `PATH`; removing and recanonicalizing the stored `release_id` reproduces its exact digest, all artifacts are location-independent before the atomic final rename, and an existing unequal release destination is refused; final 55-skill Codex metadata serialization is at most 7,500 UTF-8 characters; exact commands and tool identities are recorded; release bytes are frozen.

### Step 38: Prove transactional cutover and Git rollback in fixtures

- **Plan ID:** `NP-38`
- **Status:** NOT STARTED
- **Problem:** A green release does not prove restoration of mixed discovery roots and dirty Git state after failure.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-37
- **Files:** `skill-mesh/tools/{rehearse-native-cutover.ps1,apply-native-cutover.ps1}` (new), `skill-mesh/tests/cutover/{test_rehearsal.py,test_git_state_rollback.py,test_mixed_profile_rollback.py}` (new), `skill-mesh/schemas/{approval2-v1,cutover-receipt-v1,rollback-receipt-v1}.schema.json` (new), `skill-mesh/documentation/native-claude-codex-cutover.md`
- **Produces:** failed and successful fixture receipts plus frozen apply/rollback scripts
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** injected failure restores Claude junction/consumer/legacy/ledger bytes, active and prior release-owned utility-runtime sets/State locators, and each of the four candidate repositories' ref/index/tracked-dirty/untracked state across overlapping and unrelated WIP; successful initial and subsequent-update rehearsals qualify the exact release runtimes, leave pre-existing Git status unchanged, and retain the prior runtime set with the prior release; concurrent activation loses before write; root tests pass.

### Step 39: Freeze the exhaustive qualification request

- **Plan ID:** `NP-39`
- **Status:** NOT STARTED
- **Problem:** Real-host qualification needs one exact bounded request rather than operator-authored parameters.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-38
- **Files:** `skill-mesh/tools/run-native-rehearsal.ps1` (new), `skill-mesh/schemas/{native-preflight-attempt-v1,native-preflight-aggregate-v1,native-qualification-request-v1,native-attempt-index-event-v1,native-qualification-attempt-receipt-v1,native-qualification-aggregate-v1}.schema.json` (new where absent), `skill-mesh/tests/native-host/{test_qualification_request.py,test_runtime.py,test_profile_discovery.py,test_qualification_lineage.py}`, `skill-mesh/documentation/native-qualification-runbook.md` (new), external `%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\native-qualification\requests\<request-id>\request.json` (create-new)
- **Produces:** hash-bound request, D08 role/profile and baseline bindings, per-cell bounds, exact Preflight/Run/Resume/Finalize commands, evidence paths, and immutable attempt policy
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** every global/local native cell and all 39 utility-flow IDs have call/nested-call/timeout/output/network/attempt bounds; request binds canonical heads, immutable release, every utility-runtime manifest/hash/entrypoint, exact D08 profile/role map, baseline IDs, schema hashes, evidence root, and initial/resume rules; fake-host multi-INCOMPLETE resume, explicit latest-leaf parent, fork/old-parent/concurrency refusal, terminal PASS/FAIL/INVALID, crash Finalize, aggregate rewrite/post-final append rejection, cleanup, and corruption tests pass; root tests pass.

### Step 40: Run exhaustive disposable native qualification

- **Plan ID:** `NP-40`
- **Status:** NOT STARTED
- **Problem:** Structural gates cannot prove every real native skill.
- **Type:** operator
- **Issue:** #
- **Depends on:** NP-39
- **Files:** external `%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\native-qualification\requests\<request-id>\**` only: immutable `request.json`; `preflight-index.jsonl`, immutable `preflight-attempts/<attempt-id>/receipt.json`, and terminal `preflight.json`; qualification `attempt-index.jsonl`; immutable `attempts/<attempt-id>/receipt.json` plus raw evidence; and terminal aggregate `receipt.json`
- **Produces:** hash-chained attempt lineage, one terminal `native-qualification-aggregate-v1` receipt, complete native matrix, integrated workflow receipts, and cleanup report
- **Flags:** (operator — no `/build-step`)
- **Commands to run:** from the request-bound `skill-mesh` registry root/commit, run the exact command block below.
- **Done when:** terminal `receipt.json` validates against the aggregate schema, binds the exact request, D08 profile/role map, baselines, full attempt-index length/SHA-256, and immutable fingerprints, records `PASS`, and proves 55/55 shared skills PASS on both hosts; native `/skills` shows all 55 global names beside system/plugin/repo-local skills with no truncation or omission warning; 3/3 Claude-native PASS; required repo-local cells and integrated review/orchestration/filesystem/repo-update/ablation flows PASS; all 39 utility cells execute only the exact release-owned runtime hashes and PASS with 6/7 policy and 13/0/0 state counts; no source/staging/candidate runtime dependency or missing/fallback cell exists; every attempt/cell/evidence hash rehashes; release stays unchanged; cleanup is proven.

```powershell
gh auth status
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-rehearsal.ps1 -Action Preflight -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-qualification\requests\<request-id>\request.json"
if ($LASTEXITCODE -ne 0) { throw 'Native qualification preflight did not PASS; do not start Run.' }
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-rehearsal.ps1 -Action Run -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-qualification\requests\<request-id>\request.json"
```

Preflight repeats contained auth-status plus the four exact D08 disposable-home profile calls and
starts zero matrix cells on transient auth/quota/availability problems; unsupported/mismatched exact
profile is terminal INVALID. For controlled preflight INCOMPLETE it prints this only valid retry; a
PASS retry prints the exact Run command:

```powershell
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-rehearsal.ps1 -Action PreflightResume -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-qualification\requests\<request-id>\request.json" -ParentPreflightAttemptId "<attempt-id>" -ParentPreflightReceiptSha256 "<64-lowerhex>"
```

For a controlled matrix `INCOMPLETE`, the runner prints the only valid
parent ID/hash and this fully substituted command:

```powershell
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-rehearsal.ps1 -Action Resume -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-qualification\requests\<request-id>\request.json" -ParentAttemptId "<attempt-id>" -ParentReceiptSha256 "<64-lowerhex>"
```

Resume skips only previously PASS cells whose hashes validate under the identical request/profile/
baseline fingerprints. A crash after a terminal attempt uses the zero-host-call Finalize form defined
in §5.7, concretely:

```powershell
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\run-native-rehearsal.ps1 -Action Finalize -RequestFile "$env:LOCALAPPDATA\SkillMesh\Evidence\GoalNP\native-qualification\requests\<request-id>\request.json" -TerminalAttemptId "<attempt-id>" -TerminalReceiptSha256 "<64-lowerhex>"
```

No parent or cell is auto-selected.

This is execution, not approval. Quota/auth interruption resumes only with identical fingerprints and
creates no terminal aggregate. An infrastructure/auth/quota interruption is `INCOMPLETE` and resumes only under the immutable
fingerprint. A runner/protocol defect returns to NP-39; a real skill/utility/installer defect returns
to its owning code step. Either correction rebuilds the release, invalidates affected evidence, and
creates a new request UUID/evidence directory before rerunning the required matrix. Old request series
remain immutable. Unchanged failing output is never retried into a pass.

### Step 41: Freeze the Approval-2 deliverable packet

- **Plan ID:** `NP-41`
- **Status:** NOT STARTED
- **Problem:** Final approval must bind one immutable, executable, recoverable live change.
- **Type:** code
- **Issue:** #
- **Depends on:** NP-40 PASS receipt
- **Files:** `skill-mesh/documentation/{release-candidate-report.md,native-claude-codex-cutover.md,native-parity-approval2-packet.md}` (new where absent), `skill-mesh/plan.md`, `skill-mesh/schemas/{native-attempt-index-event-v1,native-qualification-attempt-receipt-v1,native-qualification-aggregate-v1,native-parity-approval2-packet-v1,approval2-v1,cutover-receipt-v1,rollback-receipt-v1}.schema.json`, external `%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\native-qualification\requests\<request-id>\**` (read-only; exact PASS request ID from NP-40), external `%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\approval2-packet\packet.json` (new), external `%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\approval2-packet\**`
- **Produces:** canonical `packet.json` and immutable packet with source/release/profile/utility-runtime/baseline/attempt-lineage/matrix/utility/Observatory/model/mutation/backup/postcheck/rollback hashes
- **Flags:** --isolation worktree --reviewers deep --max-iter 2
- **Done when:** the exact NP-40 PASS aggregate, whole attempt lineage, request, D08 profile set, baseline IDs, release and utility-runtime manifests, index prefix/length/hash, cell counts, every attempt manifest/hash, and absence of post-final bytes validate before packet work; evidence rehashes; no post-qualification code/profile/runtime changed; the mutation set and four candidate fast-forwards are exact; `packet.json` canonical bytes yield `<packet-sha256>`; commands are copy-paste complete; schema validates; status is WAITING FOR APPROVAL 2.

Approval-1 build execution terminates here.

### Gate 2: Abraham approves the immutable live cutover

**Type:** operator decision

Abraham chooses `approve-exact-cutover <packet-sha256>` or `stop`. Approval creates the versioned
one-shot `approval2-v1.json`. No code/config is written at this gate.

### Post-Approval 2 execution: Apply once or roll back once

This is outside the Approval-1 `/build-phase` step set. From plain offline Windows PowerShell, Abraham
invokes the frozen `apply-native-cutover.ps1` command. It validates packet/receipt/nonce before write,
backs up, applies the four frozen repository fast-forwards and managed profiles, verifies
discovery/receipts, and
consumes the nonce. A required postcheck failure runs the frozen reverse rollback once. A reopened
agent verifies receipts/hashes/status read-only. No correction, retry, fallback, or third approval occurs.


## 7. Dependency Graph and Execution Policy

```text
NP-01 <- Approval 1
NP-02 <- NP-01
NP-03 <- NP-02
NP-04 <- NP-03
NP-05 <- NP-04
NP-06 <- NP-05
NP-07 <- NP-06
NP-08 <- NP-03 + NP-07
NP-09 <- NP-08
NP-10 <- NP-09
NP-11 <- NP-07 + NP-10
NP-12 <- NP-11
NP-13 <- NP-12 PASS receipt
NP-14 <- NP-13
NP-15 <- NP-07 + NP-11
NP-16 <- NP-11 + NP-14 + NP-15
NP-17 <- NP-02 + NP-15 + NP-16
NP-18 <- NP-17
NP-19 <- NP-18
NP-20 <- NP-19
NP-21 <- NP-10 + NP-14
NP-22 <- NP-21
NP-23 <- NP-22
NP-24 <- NP-23
NP-25 <- NP-21 + NP-24
NP-26 <- NP-25
NP-27 <- NP-26
NP-28 <- NP-27
NP-29 <- NP-28
NP-30 <- NP-29
NP-31 <- NP-30
NP-32 <- NP-15 + NP-16 + NP-21 + NP-31
NP-33 <- NP-21 + NP-32
NP-34 <- NP-20 + NP-24 + NP-31
NP-35 <- NP-03 + NP-14 + NP-20 + NP-21 + NP-33
NP-36 <- NP-13 + NP-14 + NP-20 + NP-24 + NP-31 + NP-32 + NP-33 + NP-34 + NP-35
NP-37 <- NP-36
NP-38 <- NP-37
NP-39 <- NP-38
NP-40 <- NP-39
NP-41 <- NP-40 PASS receipt
Approval 2 <- NP-41
frozen offline cutover <- Approval 2
```

No implementation step begins until all declared dependencies pass. Any shared builder/template,
transaction engine, model-policy, or evaluator-contract change after NP-40 invalidates the full fleet
matrix. An isolated core change invalidates that skill and reverse dependents. An adapter-only change
invalidates its target-host cells and requires proof that the opposite distribution is byte-identical.

NP-12 and NP-40 are hard operator execution boundaries, not deferred UAT that later code may bypass.
NP-13 begins by validating the NP-12 PASS receipt and exits nonzero before mutation if it is absent.
NP-41 does the same for NP-40. Approval-1 orchestration runs in three slices: NP-01..NP-11,
NP-13..NP-39 after NP-12, and NP-41 after NP-40. Approval-1 execution always stops at NP-41.

Authentication or quota failure before a cell starts is `INCOMPLETE`, not a behavior failure. The same
cell may resume only with identical candidate/config hashes; otherwise its matched baseline/candidate
block reruns. There is no fallback model or score-improving retry.

## 8. Build, Test, and Quickstart Contract

Implementation establishes these exact command surfaces:

```powershell
# Prerequisite inventory (versions are captured in receipts)
$PSVersionTable.PSVersion
python --version
uv --version
node --version
npm --version
git --version
gh --version
claude --version
codex --version
python -c "import yaml; print(yaml.__version__)"
gh auth status

# From the registry-resolved Skill Mesh root: build and test
python -m pip install pytest pyyaml
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\build-distributions.ps1 -Provider all -OutputRoot <staging-root>
python .\tools\build-utility-runtimes.py --workspace-roots "$env:LOCALAPPDATA\SkillMesh\State\workspace-roots-v1.json" --candidate-registry "$env:LOCALAPPDATA\SkillMesh\State\GoalNP\candidate-registry-v1.json" --output-root <staging-root>\ReleaseCandidate
python -m pytest
git diff --check

# Approval 1: bootstrap and inspect disposable utility-root state
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\configure-utility-roots.ps1 -Action Bootstrap -CodingRoot <coding-root> -StateFile <staging-root>\State\utility-roots-v1.json -Mode Disposable -RequireAll
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\configure-utility-roots.ps1 -Action Inspect -StateFile <staging-root>\State\utility-roots-v1.json -RequireAll

# Approval 1: prepare and inspect; no live discovery write
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\sync-skills.ps1 -Action Prepare -SourceCommit <40-hex>
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\sync-skills.ps1 -Action Inspect -ReleaseId <release-id>

# POST-APPROVAL 2 ONLY: initial one-shot apply; its frozen script invokes rollback on failed postcheck
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\apply-native-cutover.ps1 -PacketFile <packet-file> -ApprovalFile <approval2-receipt>

# POST-APPROVAL 2 failed-transaction/manual-recovery surface only
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\sync-skills.ps1 -Action Rollback -TransactionId <transaction-id>

# AFTER a successful initial cutover only: ordinary qualified release activation
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\tools\sync-skills.ps1 -Action Activate -ReleaseId <qualified-release-id>
```

These names are plan contracts, not placeholders. There is no `dev` service command, no dedicated
linter beyond `git diff --check` and repository tests, and no separate static type checker in the
current stack. A new required linter or type checker needs a plan amendment and issue resync rather
than a silent runbook change. Host prompts never reimplement transactions.

Quickstart metavariables are deterministic: `<staging-root>` is a create-new directory under
`%LOCALAPPDATA%\SkillMesh\Staging`; `<40-hex>` is the exact committed Skill Mesh source identity;
for the one administrative bootstrap `<coding-root>` is exactly
`[IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'dev'))`, and afterward it is the matching
canonical path in `workspace-roots-v1.json`; `<release-id>` and
`<qualified-release-id>` are `r-<64-lowerhex>` values recomputed from canonical manifest payloads
with `release_id` omitted and whose applicable gates PASS; `<packet-file>` and
`<approval2-receipt>` are exact external paths frozen by NP-41/Gate 2; and
`<transaction-id>` is the UUID in the create-new journal. A `<utility-runtime:UBnn>` and its
`<utility-entry>`, `<utility-python>`, or `<utility-node>` are release-relative values from the same
qualified release manifest, never a staging or owner-repository path.

Every command resolves its target/cwd from §5.8 and validates the expected ref/commit before running;
relative `\.\tools` never means the agent's ambient cwd. Repository gates use the exact §5.8 bootstrap
and test profile. Every code step runs its focused suites plus that profile and status checks.
Distribution builds run twice and compare hashes. No long-lived development service exists.

### Minimum gate matrix

- schema/frontmatter/dependency/support-asset validation for every package;
- deterministic Claude/Codex profile builds;
- deterministic non-editable utility-runtime builds with no source/candidate/staging dependency;
- path containment, reparse, traversal, collision, and mixed-ownership tests;
- fresh install, dry-run, idempotent update, stale-file retirement, crash recovery, and rollback;
- native discovery across nested/external worktrees;
- 113 exhaustive native skill cells;
- dual-host maintenance Pareto and planted-regression tests;
- exactly 13 utility fixtures plus 26 real native-host smokes, all PASS;
- telemetry concurrency/privacy/identity tests;
- Mesh Lens v2 and bounded Observatory served/static views;
- full root and release gates;
- successful and injected-failure disposable cutover rehearsals.

## 9. Live Mutation and Rollback Boundary

Approval 2 must enumerate exact frozen paths. The expected mutation classes are:

- managed files behind the existing Claude junction target;
- `$CODEX_EFFECTIVE_HOME\.agents\skills` managed Codex packages;
- `%LOCALAPPDATA%\SkillMesh\Releases` including immutable utility runtimes, State runtime locators,
  backup, telemetry, and transaction records;
- LocalAppData profile state plus exact retirement of the tracked legacy install ledger;
- active coding-root `AGENTS.md`/workspace instruction sources that currently say Copilot and
  `.github/skills`;
- exact package-owned legacy `.github/skills` files selected for retirement;
- exact untrack/ignore disposition for manifest-owned generated `.claude/skills` files while preserving
  every consumer/private file;
- the frozen `coding-root`, `career-ops`, `on-brand`, and `measure-twice` candidate refs and their exact
  managed implementation paths.

Skill Mesh and non-live utility and Mesh Lens heads were integrated in NP-36 and are verify-only during
cutover. Dev Observatory belongs to the outer coding-root candidate rather than a separate Git head.
The live transaction moves only the four frozen candidate refs among repository branches. Its
backup/rehearsal covers each branch ref, index, tracked dirty bytes, untracked files, and both
overlapping and non-overlapping WIP; rollback must restore byte-for-byte status.

Everything else is protected. Preflight drift stops before write. Backup/install/static postcheck
failure rolls back in reverse order. Auth/quota/unavailable host fails before mutation. Discovery,
core-hash, package, or required receipt failure after apply triggers rollback. Rollback failure retains
backup/journal and reports manual recovery; it never claims clean state.

The prior release, its complete utility-runtime set, and first-cutover backup are kept for at least 30
days and 10 successful normal activations/invocations, whichever is later. No first-cutover pruning is
allowed.

## 10. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Codex skill list exceeds initial metadata budget | concise descriptions, serialized-budget test, explicit selection check for every name |
| Native Codex adapter is only a renamed Copilot adapter | all 55 adapters audited; forbidden-token gate; real native cells |
| Shared-core edit favors its proposer family | both hosts execute; high-impact both-family proposals/judges; deterministic per-host veto |
| Generated copies drift from canonical core | source/core hashes in release, install state, telemetry, and every evaluation |
| Live Claude mixed tree loses private/consumer content | file-level ownership, collision refusal, exact backup, unchanged junction, rollback rehearsal |
| Dirty Step 4 or other WIP is swept into work | external hash preservation, isolated worktrees, scoped staging, status invariants |
| Utility hook hangs or leaks output/path data | manifest bounds, advisory fail-open by default, deterministic fixtures and redaction |
| Utility runtime points back to a disposable/source checkout | non-editable release-owned builds, external-reference scan, manifest-bound entrypoints, transactional retention/rollback |
| Model identity is unavailable | requested/reported split; visible unavailable status; no identity inference |
| Observatory becomes a control-plane dependency | producer-owned bounded export; read-only rendering; unavailable-safe behavior |
| Qualification cost/quota interrupts fleet run | resumable immutable ledger; no fallback; matched block restarts on identity/config drift |
| Cutover changes after evidence | immutable packet; any relevant byte change invalidates affected evidence before Approval 2 |

## 11. Appendix

### Decision Inventory

`P` records Abraham's explicit planning choices. `D` records agent defaults that become approved only
if Abraham accepts the final plan without changing them. IDs are stable after the first proposal
publication.

| ID | P/D | Choice | Status |
|---|---|---|---|
| `P01` | P | Build full Claude/Codex parity; do not require another usefulness pilot. | confirmed by Abraham 2026-08-14 |
| `P02` | P | Use one canonical authored core with explicit Claude/Codex adapters and generated self-contained packages. | confirmed by Abraham 2026-08-14 |
| `P03` | P | Put the global Codex catalog at `$CODEX_EFFECTIVE_HOME\.agents\skills`; do not duplicate it under `dev/.agents/skills`. | confirmed by Abraham 2026-08-14 |
| `P04` | P | Preserve the current Claude junction and manage only owned files behind it. | confirmed by Abraham 2026-08-14 |
| `P05` | P | Perform one full-catalog migration, then maintain both native profiles from the canonical source. | confirmed by Abraham 2026-08-14 |
| `P06` | P | Retire Copilot as an active provider; use no router and no automatic fallback. | confirmed by Abraham 2026-08-14 |
| `P07` | P | Test every shipped skill through every supported native host. | confirmed by Abraham 2026-08-14 |
| `P08` | P | Implement the known utility hookup map now and keep Dev Observatory read-only. | confirmed by Abraham 2026-08-14 |
| `P09` | P | Use single-editor freedom with dual-host Pareto acceptance for shared-core maintenance. | confirmed by Abraham 2026-08-14 |
| `P10` | P | Use exactly two program-level approvals: this plan, then the immutable live cutover. | confirmed by Abraham 2026-08-14 |
| `D01` | D | Promote all seven current global custom Claude skills into the portable canonical catalog. | proposed default for Approval 1 |
| `D02` | D | Reverify and adopt the four preserved Step 4 files as the implementation starting checkpoint rather than discard their work. | proposed default for Approval 1 |
| `D03` | D | Back up and retire only exact classified managed Copilot-profile files at live cutover; adopt reviewed drift into canonical source or preserve it in recovery, and preserve foreign content. | proposed default for Approval 1 |
| `D04` | D | Keep the first-cutover release and backup for at least 30 days and 10 successful normal activations/invocations, whichever is later. | proposed default for Approval 1 |
| `D05` | D | Keep model requests in versioned configuration; a supported-model change rebaselines and requalifies instead of silently changing a skill. | proposed default for Approval 1 |
| `D06` | D | Reconcile every in-scope dirty coding-root, utility, and Observatory path through the NP-01 hash/export/classification contract. | proposed default for Approval 1 |
| `D07` | D | At cutover, untrack and ignore only exact manifest-managed Claude outputs and the retired legacy ledger; preserve every consumer/private file. | proposed default for Approval 1 |
| `D08` | D | Use Opus 4.8/`xhigh` and `gpt-5.6-sol`/`ultra` for production/proposal/challenge, and Sonnet 5/`xhigh` plus `gpt-5.6-terra`/`medium` for grading; no substitution or fallback. | proposed default for Approval 1 |
| `D09` | D | Add `skill-ablation` after the neutral evaluation substrate exists; every ablation uses the high-impact dual-family protocol. | proposed default for Approval 1 |
| `D10` | D | Keep coding-root, Career Ops, On Brand, and Measure Twice discovery-path candidates unmerged until Approval 2. | proposed default for Approval 1 |

### Proposal feedback grammar

Abraham may approve the defaults as written or respond with stable IDs, for example:

```text
Approve Goal NP plan with D01-D10.
D04: retain first-cutover backup for 60 days.
```

No implementation or live mutation follows from viewing the proposal. Approval 1 authorizes only
Steps NP-01 through NP-41; Approval 2 is still required for the frozen live operation.
