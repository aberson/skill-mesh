# Skill Mesh v2

Agent skills for planning, building, reviewing, and shipping software on Claude Code,
GitHub Copilot CLI, and OpenAI Codex. Each portable skill has one shared behavior
contract and a host adapter; required review and safety gates stay in the contract.

**[Download v2.0.0](https://github.com/aberson/skill-mesh/releases/tag/v2.0.0)**
— 57 Claude skills, including 54 portable skills also packaged for Codex and Copilot.
The release reconciles 15 retained skills and completes 42 rebuilds. It improves
workflow contracts and packaging; it does not promise that every skill is shorter.

| Start here | What you get |
|---|---|
| [Install or upgrade](#install-or-upgrade) | Versioned bundle, host selection and rollback |
| [Skill reference](documentation/skill-reference.md) | All 57 skills: purpose, hosts, contract and individual diagram |
| [Workflow diagrams](docs/workflows/README.md) | Source-linked Mermaid diagrams generated with show-your-work |
| [Utility projects](#how-utility-projects-are-used) | Bundled helpers, separate dependencies and deferred integrations |
| [Release notes](https://github.com/aberson/skill-mesh/releases/tag/v2.0.0) | Qualification evidence and scoped limitations |

## Install or upgrade

Use **Windows PowerShell 5.1**. Download the release ZIP and its SHA-256 file,
compare the archive hash with the checksum, then extract into a dedicated directory.
The bundle includes generated distributions; installation needs no source build.

From the directory holding the downloaded archive:

```powershell
Get-FileHash .\skill-mesh-v2.0.0.zip -Algorithm SHA256
```

Choose one host profile and an explicit consumer home:

| Provider flag | Host | Discovery root under the chosen home |
|---|---|---|
| `claude` | Claude Code | `.claude/skills/` |
| `gpt` | GitHub Copilot CLI | `.github/skills/` |
| `codex` | OpenAI Codex CLI | `.agents/skills/` |

From the extracted bundle root, replacing the example home:

```powershell
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider claude -Home C:\path\to\consumer-home -DistDir .\dist
```

For Codex use `-Provider codex`; first resolve its effective home with the
read-only [probe](tools/probe-codex-skills.ps1) and
[Codex guide](documentation/providers/codex.md). For Copilot use `-Provider gpt`.
Start a fresh host session after installation. Installing does not authenticate
the host or supply missing native capabilities. Codex uses its own adapter and
authenticated host, not the GPT/Copilot transport.

Before upgrading, preserve the previous distribution and back up the target
discovery tree and `.skill-mesh-install.json`. Stop sessions writing those paths.
Run the installer with the new distribution and existing home. It checks
ownership and current bytes; investigate collisions instead of routinely using
`-Force`. Multiple hosts may scan overlapping roots, so directory names alone
do not establish ownership.

<details>
<summary>Uninstall, restoration and legacy installations</summary>

Remove the selected profile's unchanged owned files:

```powershell
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider claude -Home C:\path\to\consumer-home -Uninstall
```

To restore a preserved prior generated profile, uninstall the current profile,
then use the v2 installer with `-DistDir` pointing to that prior distribution.
Qualification covered preserved pre-rebuild bytes with the final installer,
not every historical v1 release or older installer. Modified files may need
explicit resolution. Uninstall does not reconstruct hand-maintained legacy
files; retain a separate backup and follow the
[migration guide](documentation/migration.md).

</details>

## Choose a workflow

| Need | Entry point | Typical next steps |
|---|---|---|
| Start a project | `plan-init` | `repo-init` → `plan-expedite` → `build-phase` |
| Extend existing code | `plan-feature` | `plan-review` → `plan-redline` → `plan-wrap` |
| Deliver a bounded change | `build-step` | Isolated implementation, automated gates, independent review, integration |
| Execute a phase or queue | `build-phase` / `build-queue` | Ordered steps, checkpoints, explicit holds |
| Diagnose a bug | `user-debug` | Evidence and independent reproduction before repair |
| Review code | `review-gauntlet` / `review-deep` | Independent lenses and evidence-backed verdict |
| Prepare and run acceptance | `review-uat` → `user-uat` | Separate mechanical checks from human judgment |
| Return to work | `user-wrap` / `user-orient` | Inspect evidence and choose the next action |
| Save or close a session | `session-wrap` | Triage → `task-handoff` → route-specific actions |
| Learn from mistakes | `lesson-harvest` | Bounded, zero-write candidate preview in v2 |

Use the installed skill through your host's invocation mechanism. Host commands
such as `/goal`, `/loop` and `/schedule` are not Skill Mesh packages.
The [complete reference table](documentation/skill-reference.md) links every
skill to its individual diagram and authoritative contract.

## How utility projects are used

Skills coordinate judgment and permissions. Utility projects supply mechanical
operations such as retrieval, validation, evidence storage and documentation
rendering. Installing Skill Mesh does not install every utility, start
Observatory, or enable every proposed integration.

| Project or packaged helper | Used by | Role and v2 boundary |
|---|---|---|
| [Drift Ranger](https://github.com/aberson/drift-ranger) | Planning, build orchestration, `task-handoff`, `session-wrap` | Private outcome records and capability checkpoints. If unavailable, use existing private session state. Assertions are not delivery proof. |
| [Find Again](https://github.com/aberson/find-again) | `plan-feature` | Optional prior-work search with index age and scope reported. No automatic refresh; current source remains authoritative. |
| [dev-observatory](https://github.com/aberson/coding-root/tree/master/dev-observatory) | `build-observer`, `observatory-doctor` | The packaged scaffold imports Observatory's own validation and prints portfolio proposals. Doctor uses `--no-probe` static checks, not live launches. |
| [Citation Needed](https://github.com/aberson/citation-needed) | Four `citation-*` skills | Separate `cite` CLI owns scans, calibrated review records and scoring. Review and sweep prepare evidence and dispatch independent judges; distill and triage handle proposals and operator decisions. v2 requires the published [overview-filters branch](https://github.com/aberson/citation-needed/tree/skill-mesh-v2/overview-filters), not the default branch. |
| Goblin CLI and private atom store | Three `goblin-*` skills | External project-specific dependency; see the [reconstruction guide](_shared/goblin-second-brain.md). `goblin-do` prints a next-action seed without executing it. `goblin-suggest` generation modes remain explicitly held in v2. |
| Switchboard | `tier-offload` | Produces an advisory inventory and inactive candidate routing configuration. It does not activate or claim to benchmark a local model. |
| Lavish Editor (`lavish-axi`) | `user-lavishify` | Re-presents a selected artifact as private annotatable HTML through a loopback editor. Requires Node 22+, an accessible local browser and the separate npm tool; the artifact is not published. |
| Packaged build, review and observation helpers | `build-step`, `review-deep`, `lesson-harvest` | Evidence capture, deterministic verdict handling and explicit private mistake observations. `lesson-harvest --publish` is unavailable in v2. |
| [Show Your Work](https://github.com/aberson/show-your-work) | This repository's documentation | Validates source-linked Mermaid and generates the workflow README/index. An authoring tool, not a skill runtime prerequisite. |

The older [utility hookup investigation](documentation/findings/utility-hookup-map-resolved.md)
is historical planning evidence. It does not establish that Heads Up, Tripwire,
Same Page, Changed Check, Paper Trail, Mesh Lens or every proposed Find Again
caller is wired into this release. Passing Notes is not a bundled runtime
dependency. Utility availability, caller wiring and native acceptance are
separate claims.

## What v2 qualifies

The [release notes](https://github.com/aberson/skill-mesh/releases/tag/v2.0.0)
record the exact source, full root-suite result, all-provider package checks,
and disposable-home installation, upgrade, uninstall and prior-profile restoration.
Downloaded assets were checked against the published archive checksum.
Qualification did not change normal installed profiles.

Catalog coverage is not blanket live qualification of every workflow:

- `claude-oauth-auth`, `context-slim` and `judge-motion` are Claude-only.
- Required independent-review, vision and Workflow capabilities must exist in the
  invoking host. Missing capabilities produce a hold, not self-review.
- Session advice may add a progress sentence and vary triage formatting;
  strict presentation is deferred to v3.
- `lesson-harvest` is preview-only; `observatory-doctor` is static-only.
- Session-bound writes require authoritative session identity. Judge Motion needs
  runtime/browser dependencies and native permissions. PowerShell 7 is not qualified.

See the [provider guides](documentation/providers/README.md) and release notes
for precise native-observation scope and outstanding limitations.

## Source and development

`skills/<name>/core.md` holds portable behavior; `providers/` binds the host.
The [manifest](config/skill-manifest.json) owns membership. The three Claude-native
entries use provider source directly. Generated `dist/` and installed profiles
are outputs; edit canonical sources and rebuild. Legacy top-level packages are
compatibility material, not v2 sources.

From a source checkout, build one profile:

```powershell
powershell -NoProfile -File tools/build-distributions.ps1 -Provider codex
```

The repository-root qualification command is `python -m pytest` without a path
argument. Requirements and gate details live in [CLAUDE.md](CLAUDE.md);
release staging is documented in [architecture](documentation/architecture.md).
For diagram maintenance see [workflow regeneration](docs/workflows/README.md#regenerating).

Adapt workspace paths, conventions and optional utilities to your setup.
Keep private observation stores, session records and credentials outside Git.
[Issues and contributions](https://github.com/aberson/skill-mesh/issues) are welcome.

MIT — see [LICENSE](LICENSE). Built by [Abraham Robison](https://github.com/aberson).
