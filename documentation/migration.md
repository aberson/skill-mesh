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
| 46 top-level single-file `<skill>/SKILL.md` packages (Claude-only content, no GPT adapter, no shared core) | `skills/<name>/core.md` (neutral behavior contract) + `skills/<name>/providers/{claude,gpt}.md` (thin host adapters), 47 portable + 3 Claude-native exclusions = 50 skills |
| No router, no provider selection, no install tooling shipped in the public repo | `runtime/skill-router.ps1` (`-Provider auto\|claude\|gpt\|local`), `tools/build-distributions.ps1`, `tools/install-skill-mesh.ps1`, `tools/release.ps1` |
| README documented `OPENAI_API_KEY` as required for the GPT path | GPT selects GitHub Copilot authentication first; `OPENAI_API_KEY` is an optional direct-OpenAI fallback only (see the README's [authentication matrix](../README.md#authentication-matrix)) |
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
  `tests/distributions/`, `tests/telemetry/`, `tests/release/`.

None of this was previously in the public repository at all — it was implemented in a private
workspace (`aberson/coding-root`, referred to below as the legacy migration source) and read-only
migrated in during Steps 33-38. That source repository is not part of this public package and is
not referenced by any shipped file.

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
[installation matrix](../README.md#installation-matrix)) rather than the top-level path. Retiring
the top-level compatibility directories entirely is tracked as a follow-up beyond this docs-only
step (Step 39 only rewrites documentation and does not delete or regenerate files outside
`README.md`, `documentation/`, or the manifest).

## `.claude` compatibility shims (coding-root)

The legacy migration source's own `.claude/skills/` and `.claude/skills-gpt/` trees (in
`aberson/coding-root`) were **read-only** for the whole of Steps 33-40 — nothing in this
migration wrote to them. Step 41 (operator, not yet run as of this document) performs the one-time
cutover: installing the released `aberson/skill-mesh` package back into `coding-root/.claude` via
`tools/install-skill-mesh.ps1 -Provider claude -Home <coding-root>`, generating a marker-tagged,
ownership-safe discovery tree rather than hand-edited files.

After Step 41, `coding-root/.claude/skills/` becomes an **installed consumer** of this package, not
an independent source: future skill changes are made in `aberson/skill-mesh` and flow out via a
re-install (`install-skill-mesh.ps1`, idempotent — see `documentation/architecture.md` §8.2),
never by hand-editing files under the installed `.claude/skills/` tree directly.

## Authentication guidance correction

Earlier public guidance said "set `OPENAI_API_KEY` to activate the GPT path." That was never
accurate to the shipped router and has been corrected: GPT selection uses GitHub Copilot
authentication by default (`gh auth login`, or `GH_TOKEN` / `COPILOT_GITHUB_TOKEN`) and only falls
back to a direct OpenAI API call — using `OPENAI_API_KEY` — if Copilot is unavailable or fails.
See the README's [authentication matrix](../README.md#authentication-matrix) and
[`providers/gpt.md`](providers/gpt.md) for the full transport-precedence contract.

## Repository metadata

Proposed (not yet applied) GitHub repository title/description text for the operator to apply in
Step 41: [`repo-metadata.md`](repo-metadata.md).
