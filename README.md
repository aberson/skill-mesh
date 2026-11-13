# skill-mesh

**Agent skills for planning, building, reviewing, and shipping software — a shared
workflow for Claude Code and OpenAI Codex.**

- **A connected pipeline.** Turn an idea into a plan, a bounded build, an independently reviewed change, and a release.
- **Explicit quality gates.** Automated checks and fresh-context reviewers inform the result; missing required capabilities stop the workflow.
- **One contract, several hosts.** 50 Claude skills; 48 also packaged for Codex through host adapters, and for GitHub Copilot one last time in v3.0.0.

**[v3.0.0 is released](https://github.com/aberson/skill-mesh/releases/tag/v3.0.0)** ·
[Try it](#install-or-upgrade) · [Browse the skills](documentation/skill-reference.md) ·
[Detailed workflows](docs/workflows/README.md)

## Workflows

The skills work together, but you can start with one: plan a feature, debug a bug,
review a change, or recover where a session left off.

### The core pipeline

Plan → sync → build → ship. Everything else supports this spine.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="_shared/core-pipeline-dark.svg">
  <img alt="Plan, review, redline and wrap; sync issues and save a handoff; run checks, selected review and landing gates inside each build step; then acceptance and repository publishing." src="_shared/core-pipeline-light.svg">
</picture>

`plan-expedite` connects review, proposal, wrap, issue sync, and handoff.
`build-phase` runs the planned steps through `build-step`.

### Inside one build step: the review gate

Implementation and judgment are separate jobs. A failed check sends the change
back for repair; a passing candidate still has to clear the landing checks.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="_shared/review-gate-dark.svg">
  <img alt="Code-lane example: an isolated developer, configured checks, five reviewers, a strong orchestrator judge, uncommitted landing and final verification; fixable failures retry within budget and blockers can occur throughout." src="_shared/review-gate-light.svg">
</picture>

The illustration shows the five-lens `code` lane. The default `auto` lane uses
mechanical checks without reviewer agents; `deep`, `runtime`, and `full` select
other review paths. Landing is uncommitted; final PASS follows verification,
restoration, and cleanup. The [build-step contract](skills/build-step/core.md) defines the full gates,
iteration limits, and recovery behavior.

### One workflow, several hosts

Portable behavior lives in shared contracts. Adapters map that behavior to each
host's capabilities; installation puts the generated skills where the host finds them.
The GitHub Copilot profile is deprecated and ships for the last time in v3.0.0.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="_shared/host-profiles-dark.svg">
  <img alt="Shared Skill Mesh contracts generate three host profiles: 50 Claude skills and 48 portable skills each for GitHub Copilot (deprecated) and OpenAI Codex." src="_shared/host-profiles-light.svg">
</picture>

### The routing web

Have several half-formed ideas at once? `user-gateway` separates the fragments
and routes each to a useful next step.

<details>
<summary><strong>See the core routes: bug, do, plan, investigate, verify, trim, decide, draft</strong></summary>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="_shared/routing-web-dark.svg">
  <img alt="An operator's notes enter user-gateway and split across the core routes, from debugging and planning to verification and drafting." src="_shared/routing-web-light.svg">
</picture>

The `do` route hands a small task to `user-pm`, whose board picks its build route; the
gateway executes no work. `user-pm` is also the status door ("where does this project
stand?"). The `decide` route records the open question with `user-dr` (a complex scope
choice goes to `user-fermize`), and `plan` can start with `code-consigliere` when you want
to understand a project before agreeing a change. Host commands such as `/goal` and
`/deep-research` are separate from this skill catalog. The routing contract adds five more
routes (review, research, tend, session, learn) so a vent can reach every vent-worthy skill:
[Routing contract](_shared/skill-pipeline.md).

</details>

## What's inside

| Family | Examples |
|---|---|
| Route & decide | `user-gateway`, `user-build-route`, `user-dr`, `user-fermize` |
| Plan | `plan-init`, `plan-feature`, `code-consigliere`, `plan-review`, `plan-redline` |
| Build & ship | `build-step`, `build-phase`, `build-queue`, `repo-update` |
| Review & acceptance | `review-deep`, `review-gauntlet`, `user-uat`, `judge-ui` |
| Sessions & status | `session-wrap`, `task-handoff`, `user-wrap`, `user-pm` |
| Evidence & improvement | `citation-review`, `lesson-harvest`, `skill-evolve`, `tier-offload` |

<details>
<summary><strong>Explore all 50 skills and available workflow documentation</strong></summary>

The [complete reference table](documentation/skill-reference.md) lists each skill's
purpose, host coverage, source contract, and individual workflow. The
[source-linked workflow catalog](docs/workflows/README.md) records the details and
omissions behind each flow, checked with [Show Your Work](https://github.com/aberson/show-your-work).

`claude-oauth-auth` and `context-slim` are Claude-only.
An adapter's presence does not guarantee every required native capability is
available in your session.

</details>

## Pick your entry point

| You want to… | Start with |
|---|---|
| Sort several half-formed ideas into next steps | `user-gateway` |
| See where a project stands and what to do next | `user-pm` |
| Choose between planning/build, a bounded goal, or a direct task | `user-build-route` |
| Plan a new project or extend an existing one | `plan-init` / `plan-feature` |
| Understand a project before agreeing a change | `code-consigliere` |
| Record a decision or find a simpler first milestone | `user-dr` / `user-fermize` |
| Deliver one well-scoped change | `build-step` |
| Work through an entire phase | `build-phase` |
| Investigate a stubborn bug | `user-debug` |
| Review a diff or prepare acceptance | `review-gauntlet` / `review-uat` |
| Resume work or leave a durable handoff | `user-wrap` / `session-wrap` |

<details>
<summary><strong>Example: from a feature idea to a reviewed build</strong></summary>

Use your host's skill invocation mechanism:

```text
plan-feature       investigate the existing project and write the plan
plan-expedite      review → redline → wrap → issue sync → handoff
build-phase        run the eligible steps through build-step
repo-update        refresh documentation and publish the scoped changes
```

The skills preserve their own decision points, prerequisites, and stop conditions.
The [individual workflows](docs/workflows/README.md) show those branches.

</details>

## How utility projects are used

Skills coordinate the work. Small utility projects provide specific operations:
tracking the intended outcome, finding prior work, keeping evidence, and validating
project information.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="_shared/utility-support-dark.svg">
  <img alt="Skill workflows use Drift Ranger for intent, Find Again for retrieval, Citation Needed for evidence, and dev-observatory for portfolio validation and static diagnostics. Show Your Work documents the workflows." src="_shared/utility-support-light.svg">
</picture>

These projects remain separate. Installing Skill Mesh does not install every
utility or start background services.

<details>
<summary><strong>Which integrations are in v3?</strong></summary>

| Utility | How it is used |
|---|---|
| [Drift Ranger](https://github.com/aberson/drift-ranger) | Private outcome records and capability checkpoints; existing session state is the fallback. |
| [Find Again](https://github.com/aberson/find-again) | Optional prior-work retrieval in `plan-feature`; current source stays authoritative. |
| dev-observatory | Its static doctor and the portfolio-block proposer are dev-observatory project-local skills, not Skill Mesh skills. |
| [Citation Needed](https://github.com/aberson/citation-needed) | Evidence storage and scoring for the citation skills; review and sweep dispatch independent judges. Requires the [overview-filters branch](https://github.com/aberson/citation-needed/tree/skill-mesh-v2/overview-filters). |
| Goblin | External CLI/private atom store. No catalog skill drives it in v3: the Goblin skills were retired, and `user-pm` lists improvement ideas. |
| Switchboard | `tier-offload` produces advisory, inactive routing candidates. |
| [Show Your Work](https://github.com/aberson/show-your-work) | Checks diagram sources and generates the detailed workflow index; not a skill runtime dependency. |

Build, review, and explicit mistake-observation helpers also ship inside the
packages. The [older utility hookup investigation](documentation/findings/utility-hookup-map-resolved.md)
is historical planning, not proof that every proposed caller is wired.

</details>

**v1 is retired.** Its launchers are removed; the [compressed historical archive](archive/v1/README.md) is for reference only.

## Install or upgrade

Download the [v3.0.0 release](https://github.com/aberson/skill-mesh/releases/tag/v3.0.0),
verify its checksum, and choose one host profile.

**GitHub Copilot (GPT) support is deprecated.** v3.0.0 is the last release that ships the GPT profile. It is included unchanged, so nothing breaks today, but the GPT adapters, the `.github/skills` install target and the GPT build will be removed in the next release. Skill Mesh will then support Claude Code and the OpenAI Codex CLI. If you use the GPT profile, plan to move to one of those.

<details>
<summary><strong>Installation, upgrades, and restoration</strong></summary>

Of the portable catalog, 48/48 skills are GPT-capable; Claude provides all 50 skills.

| Provider | Discovery root under the chosen home |
|---|---|
| claude | `.claude/skills/` |
| gpt | `.github/skills/` |
| codex | `.agents/skills/` |

Use Windows PowerShell 5.1. From the extracted bundle, replacing the example home:

```powershell
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider claude -Home C:\path\to\consumer-home -DistDir .\dist
```

Use `-Provider codex` for Codex or `-Provider gpt` for GitHub Copilot (deprecated).
Preserve the previous distribution and installation ledger before upgrading.
See the [installation and restoration guide](documentation/v2-installation.md)
for home resolution, collision handling, and legacy migration.

</details>

## Status & adapting

**v3.0.0 tidies the catalog and rebuilds /user-pm:** `/user-pm` is the status door for a
project (verified status, a routed board, lanes); `/user-gateway` routes a vent to every
skill; build and wrap skills size tests to the change; eleven skills were retired, folded,
moved or replaced by a script, and `/user-fermize` joined. GitHub Copilot (GPT) support is deprecated and leaves in
the next release. The [release notes](https://github.com/aberson/skill-mesh/releases/tag/v3.0.0)
record what changed, the checks that ran and installation limits.

<details>
<summary><strong>Scope, dependencies, and known limitations</strong></summary>

Catalog coverage is not blanket live qualification of every skill on every host.
Required review and vision capabilities remain explicit. Lesson harvesting is
preview-only; session advice has an accepted presentation limitation; session-bound
writes require authoritative identity. Normal profiles are not upgraded by publishing
a release. Adapt workspace conventions and external utility dependencies to your setup.

[Provider guides](documentation/providers/README.md) ·
[Source and development](CLAUDE.md) · [Architecture](documentation/architecture.md)

</details>

<details>
<summary>Historical cutover evidence</summary>

Phase 7 complete: issues #62 and #63 closed; Step 48 is DONE.
The [historical cutover handoff](documentation/coding-root-cutover-handoff.md)
preserves that acceptance record. It does not authorize reactivating v1;
use the current installation guide for active consumers.

</details>

## Contributing

[Issues and suggestions](https://github.com/aberson/skill-mesh/issues) are welcome.
Edit canonical sources under `skills/`, then rebuild; installed profiles are generated.

## License

MIT — see [LICENSE](LICENSE). Built by [Abraham Robison](https://github.com/aberson).
