# Migration Notes

Operator-facing narrative for the provider-neutral repackaging done in Steps 33-40 of
[`provider-neutral-skill-mesh-plan.md`](provider-neutral-skill-mesh-plan.md). This document
answers "what changed, what do I point at now, and what still needs a follow-up" for anyone
who already had a link, clone, or install of the pre-migration `aberson/skill-mesh` package.
For the underlying design and the full canonical-location table, see
[`architecture.md`](architecture.md).

## What changed

| Before | After |
|---|---|
| 46 top-level single-file `<skill>/SKILL.md` packages (Claude-only content, no GPT adapter, no shared core) | `skills/<name>/core.md` (neutral behavior contract) + `skills/<name>/providers/{claude,gpt}.md` (thin host adapters), 54 portable + 3 Claude-native exclusions = 57 skills |
| No router, no provider selection, no install tooling shipped in the public repo | `runtime/skill-router.ps1` (`-Provider auto\|claude\|gpt\|local`), `tools/build-distributions.ps1`, `tools/install-skill-mesh.ps1`, `tools/release.ps1` |
| README documented `OPENAI_API_KEY` as required for the GPT path | GPT selects GitHub Copilot authentication first; `OPENAI_API_KEY` is an optional direct-OpenAI fallback only (see the README's [Providers & installation](../README.md#providers--installation) section) |
| README framed Claude as the primary/default provider | README leads with the shared pipeline; Claude and GPT get parallel, equally-weighted installation paths |
| No package-integrity gate — the README could (and did) drift from what the package actually ships | `tests/package-integrity/` fails the build on a broken link, a missing adapter, stale generated output, a mismatched skill count, or an unsupported README claim |

## Where things live now

Every artifact class has exactly one canonical home, enumerated in
[`architecture.md`](architecture.md) §2 and §7. In short:

- **Skill behavior**: `skills/<name>/core.md` (portable) or `skills/<name>/providers/claude.md`
  (the 3 Claude-native exclusions — `claude-oauth-auth`, `context-slim`, `judge-motion`).
- **Provider adapters**: `skills/<name>/providers/claude.md`, `skills/<name>/providers/gpt.md`.
- **Router and provider-detection**: `runtime/skill-router.ps1`, `runtime/providers/`.
- **Manifest** (single source of truth for counts, adapters, exclusions): `config/skill-manifest.json`.
- **Build/install/release tooling**: `tools/build-distributions.ps1`, `tools/install-skill-mesh.ps1`,
  `tools/release.ps1`.
- **Tests**: `tests/package-integrity/`, `tests/router/`, `tests/calibration/`,
  `tests/distributions/`, `tests/telemetry/`, `tests/release/`, `tests/smoke/`.

None of this was previously in the public repository at all — it was implemented in a private
workspace (`aberson/coding-root`, referred to below as the legacy migration source) and read-only
migrated in during Steps 33-38. That source repository is not part of this public package.

## The legacy top-level `<skill>/SKILL.md` layout (deprecation window)

The original public release (`Initial public release: 39 Claude Code skills`, later extended to
46 skills) shipped one flat file per skill at the repository root — e.g. `plan-init/SKILL.md`.
Those 46 directories are **still present on disk** and still resolve for anyone with an existing
link, clone, or `mklink /J` junction pointed at them.

They are **not** the canonical source: they were not touched by Steps 33-38, they do not carry
GPT adapters, and the 4 skills added since this migration started
(`judge-motion`, `observatory-doctor`, `plan-redline`, `user-project`) exist **only** in the new
`skills/<name>/` tree — they have no top-level counterpart. Treat any content difference between
a top-level `<skill>/SKILL.md` and `skills/<skill>/core.md` (or `providers/claude.md`) as the new
canonical tree being authoritative.

**If you have an existing install or bookmark:** switch it to point at `skills/<name>/core.md`
(or install via `tools/install-skill-mesh.ps1` — see the README's
[Quick start](../README.md#quick-start)) rather than the top-level path. Retiring
the top-level compatibility directories entirely is tracked as a follow-up beyond this docs-only
step (Step 39 only rewrites documentation and does not delete or regenerate files outside
`README.md`, `documentation/`, or the manifest).

## `.claude` compatibility shims (coding-root)

The legacy migration source's own `.claude/skills/` and `.claude/skills-gpt/` trees (in
`aberson/coding-root`) were **read-only** for the whole of Steps 33-40 — nothing in this
migration wrote to them. Step 41 has been superseded by
[`host-native-discovery-cutover-plan.md`](host-native-discovery-cutover-plan.md) and now carries
an explicit `**Status:** SUPERSEDED` marker in
[`provider-neutral-skill-mesh-plan.md`](provider-neutral-skill-mesh-plan.md); the one-time
cutover is now Steps 42-50 of the **host-native-discovery cutover plan** (the first link above —
`provider-neutral-skill-mesh-plan.md` has no Steps 42-50).

**Status:** Steps 42-50 are complete — the host-loading authority map, the live Copilot CLI
discovery-root proof, the GPT retarget, the both-profile discovery proof, read-only host-install
inspection, reversible migrator, operator host acceptance, and live consumer cutover. On 2026-08-09,
the operator accepted a clean temporary-home installation and rollback, then cut over the live
consumer on its own dedicated branch with an external backup retained. **Step 48 (this handoff) is
DONE.** Step 47b (containment-gate
hardening) remains pending and deliberately off the completed cutover path.

**Topology correction.** A consumer gets **three** discovery roots, not one, and the legacy GPT
core tree is none of them. It was two through the Step-48 cutover; Phase CP Step 5 made the codex
root installable, and `tools/skill-mesh-discovery.ps1` is the one owner of the map:

| Tree | Role today |
|---|---|
| `<consumer-home>/.claude/skills/` | Claude Code discovery root — the Claude profile's install target |
| `<consumer-home>/.github/skills/` | GitHub Copilot CLI discovery root — the GPT profile's install target |
| `<consumer-home>/.agents/skills/` | Codex CLI discovery root — the codex profile's install target (Phase CP Step 5). The same literal path Copilot already scanned as an active alternate, so its presence is not evidence of which host wrote it |
| `<consumer-home>/.claude/skills-gpt/` | **Legacy** hand-authored GPT core tree. Superseded by the generated `.github/skills` profile; retired entry-by-entry at cutover, never wholesale |

The full authority map — and why a running GPT model is not evidence of an installed GPT
profile — is [`host-discovery.md`](host-discovery.md).

## The one-time consumer cutover

The exact operator sequence lives in
[`coding-root-cutover-handoff.md`](coding-root-cutover-handoff.md). Four properties of it are
worth knowing before you open it:

- **Inspect before you migrate.** `tools/inspect-host-install.ps1` is a read-only preflight that
  classifies every skill-bearing tree; the migrator's dry run comes next, and only then
  `-Apply`. Nothing mutates until two separate read-only passes have reported.
- **The backup is mandatory and external.** `tools/migrate-legacy-install.ps1` requires
  `-BackupDir` in every mode and refuses a directory inside the consumer home. Retention and the
  exact secure-deletion command are in the handoff's last section.
- **Retirement is classify-then-retire.** Only `managed` entries — those with a manifest record
  and a generated counterpart — are retired from `.claude/skills-gpt`. Consumer-only entries are
  preserved byte-for-byte in place and recorded by path and hash, never payload-copied.
- **Host acceptance is operator evidence.** The handoff prepares Steps 49-50; it does not perform
  them, and no test in this repository asserts that a host discovered anything.

With Step 50 of the host-native-discovery cutover plan complete, `coding-root/.claude/skills/` is an **installed consumer** of this package, not
an independent source: future skill changes are made in `aberson/skill-mesh` and flow out via a
re-install (`install-skill-mesh.ps1`, idempotent — see `documentation/architecture.md` §8.2),
never by hand-editing files under the installed `.claude/skills/` tree directly.

## Legacy migration and the `codex` provider

`config/skill-manifest.json` declares three installable providers -- `claude`, `gpt`, and
`codex`. `tools/migrate-legacy-install.ps1` binds **every declared provider**, not the subset
a given distribution happens to ship: `New-MigrationPlan` loads the manifest's top-level
`providers` block into its known-provider vocabulary, resolves a discovery root for each via
`tools/skill-mesh-discovery.ps1`, and emits a `MISSING_PROFILE` blocker (`exit 2`) when the
distribution it was handed omits one.

**Consequence, and it is deliberate:** a `both` distribution (claude + gpt -- still
`release.ps1`'s default) is no longer a complete migration source. **Legacy migration requires
a `-Provider all` distribution:**

```powershell
powershell -File tools/build-distributions.ps1 -Provider all
powershell -File tools/migrate-legacy-install.ps1 -ProjectRoot '<consumer-home>' -DistDir 'dist' -BackupDir '<backup-dir>'
```

Handing the migrator a `both` dist does not silently skip codex -- it refuses the whole
migration and names the missing profile. That fail-loud is the point. The considered
alternative, scoping the migrator's bound roots to whatever the dist ships, was implemented
and then **rejected** during Phase CP Step 5: it makes a declared-but-unshipped provider root
*unbound*, and bytes under an unbound root can be left in a consumer home without a ledger
record -- silent orphaning, where uninstall can never remove what install left behind. Refusing
an incomplete artifact costs one build flag; orphaning costs bytes nobody can find.

Hardening the migrator so that a partial distribution can be migrated safely is tracked
separately as issue **#138** (reparse-aware discovery, unbound-root accounting). Until it
lands, build `-Provider all` before migrating.

## Authentication guidance correction

Earlier public guidance said "set `OPENAI_API_KEY` to activate the GPT path." That was never
accurate to the shipped router and has been corrected: GPT selection uses GitHub Copilot
authentication by default (`gh auth login`, or `GH_TOKEN` / `COPILOT_GITHUB_TOKEN`) and only falls
back to a direct OpenAI API call — using `OPENAI_API_KEY` — if Copilot is unavailable or fails.
See the README's [Providers & installation](../README.md#providers--installation) section and
[`providers/gpt.md`](providers/gpt.md) for the full transport-precedence contract.

## Repository metadata

GitHub repository title/description text, applied to the live repository:
[`repo-metadata.md`](repo-metadata.md).
