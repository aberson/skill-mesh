# Build Step 33 — Dev Report

**Step:** 33 — Lock the neutral package and host-adapter contract
**Issue:** #42
**Worktree:** `C:\Users\abero\dev\worktree_build-step-33-20260726101916` (branch `build-step-33-20260726101916`)
**Baseline:** `bb9505eb3c0e7ac756684b97ba55ab3d98bfc882`
**Result:** DONE

## What was implemented

A design-only step: one provider-neutral package + host-adapter contract, locked
before any code moves. No skill behavior changed.

### Files created

| File | Purpose |
|---|---|
| `config/skill-manifest.json` | Canonical machine-readable manifest. One record per skill (50): `name`, `status`, `core`, `providers`, `capabilities`, `local_capable`, `migration` (launcher/adapter split), `support_assets`. Top-level `schema_version`, `capability_vocabulary`, `capability_semantics`, `providers`, `legacy_migration_root`, `host_metadata_sources`, `global_support_assets`, `counts` (total/portable/provider_native/local_capable/sub_agent/vision/filesystem). |
| `documentation/architecture.md` | Framework design: canonical directory contract, skill package shape, host capability matrix, host-native binding vs runtime auto-detection, CLI compatibility table, migration manifest (per-skill + support assets + exclusions), exact PowerShell build/install/test commands, lint/typecheck explicitly not configured, test-enforced invariants. |
| `documentation/providers/README.md` | Provider index + capability/exclusion matrix + auth-axis summary. |
| `documentation/providers/claude.md` | Claude host binding, transport (host-native; optional `ANTHROPIC_API_KEY`), capabilities, native exclusions. |
| `documentation/providers/gpt.md` | GPT/Copilot host binding, Copilot-first transport precedence (`OPENAI_API_KEY` not universally required), capabilities. |
| `tests/package-integrity/test_manifest_contract.py` | 27 checks (see Tests): schema, exact counts + name sets, provider-native/local-capable/vision/sub-agent sets vs committed fixture, path scoping, launcher/adapter migration convention, support-asset scoping, host-metadata sources, capability semantics, normalized command contract, no-absolute-paths, optional source verification. |
| `tests/package-integrity/expected_inventory.json` | Committed authoritative inventory fixture so the public package tests need no private source. |
| `tools/gen_manifest.py` | Generator that emits the manifest + fixture from authoritative constants and a READ-ONLY scan of the legacy source. Requires `SKILL_MESH_LEGACY_SOURCE` (or `--legacy-source`); no private path defaulted. |

## Iteration 2 — review findings addressed

All eight consolidated review findings were addressed surgically:

1. **Launcher vs adapter separated.** The per-skill `migration` block now carries
   four truthful fields — `legacy_core`, `legacy_claude_launcher` (`SKILL.md`
   compatibility launcher), `legacy_claude_adapter` (`SKILL-claude.md` substantive
   adapter), `legacy_gpt` — with `null` where a native skill has no launcher/core/gpt
   (native skills carry the substantive skill in `SKILL.md`, recorded as the adapter).
   Package tests validate exact source paths against the committed
   `expected_inventory.json` fixture (no private source needed); an optional
   `test_migration_source_files_exist` verifies against the real READ-ONLY source and
   **skips cleanly** when `SKILL_MESH_LEGACY_SOURCE` is unset.
2. **Migration-root contradiction fixed.** `legacy_migration_root` is now the
   coding-root (not `coding-root/.claude`); all legacy paths are coding-root-relative
   (`.claude/...`), and `documentation/multi-model` is handled as a sibling of
   `.claude` (architecture §7).
3. **Support assets are machine-readable.** Every skill record carries a
   `support_assets` array (skill-local scripts/workflows/fixtures/evals inventoried
   from the READ-ONLY source), and a top-level `global_support_assets` lists the
   shared trees. Canonical destinations are scoped under `skills/<name>/...` or a
   neutral global tree; ownership documented in architecture §7.2.
4. **Host-metadata sources enumerated.** `host_metadata_sources` (manifest) +
   architecture §5.3 list the approved explicit environment markers
   (`CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT` for Claude; `COPILOT_CLI`,
   `COPILOT_AGENT_SESSION_ID` for GPT/Copilot), explicitly exclude credential
   variables as identity sources, and define precedence: exactly-one → select;
   both → ambiguous (exit 2); neither → unset (exit 2, never default to Claude).
   No executable-name guessing.
5. **Portable command lines.** Architecture §8 uses `python -m pytest ...` and the
   legacy baseline is expressed via `$env:SKILL_MESH_LEGACY_SOURCE` — no checkout
   `.venv-1` absolute path. Tests assert complete normalized command lines.
6. **Migration tests strengthened.** Exact 50 names/statuses, exact local-capable
   (24), vision (2), and sub-agent (16) sets, launcher/adapter field conventions,
   support-asset scoping, host-metadata rules, and capability semantics are all
   asserted against the committed fixture; vocabulary semantics are documented and
   the "filesystem" meaning is clarified (baseline capability, not a scarce host gate).
7. **Sub-agent set corrected (9 → 16).** All 50 legacy contracts were audited. A
   *named-skill dispatch* (e.g. `/build-step`) is the host skill-dispatch primitive
   and does NOT count as sub-agent; only isolated fresh-context Agent/Task/workflow
   `agent()` / action-child dispatch counts. Result: build-step, context-slim,
   goblin-do, goblin-suggest, judge-motion, judge-ui, research-prospect, review-deep,
   review-gauntlet, skill-evolve, skill-iterate, test-prune, tier-escalate,
   tier-offload, user-brainstorm, user-learn. build-phase/build-queue/plan-expedite
   are excluded (named-skill dispatch only). Correlates with `local_capable=false`.
8. **No absolute private paths committed.** `test_no_absolute_private_paths_committed`
   scans the manifest, fixture, architecture, provider docs, generator, and the test
   itself for `?:\Users\...` and fails if any appears. The two required run commands
   use the pinned interpreter only at runtime (not committed).

## Evidence for the acceptance criteria

- **One canonical location for every core, adapter, mapping, test, doc:**
  `documentation/architecture.md` §2 (canonical directory contract table) + §3.
- **Host-native binding vs runtime auto-detection:** §5 (binding primary; router
  `-Provider auto|claude|gpt|local`; `auto` errors on ambiguity, never silently
  defaults to Claude) + §6 CLI compatibility table.
- **Migration entry for all 47 portable + 3 Claude-native exclusions (50):**
  every skill has a `migration` block in `config/skill-manifest.json`; §7 documents
  the uniform per-skill rule, support-asset mapping, and the 3 explicit exclusions.
- **Exact PowerShell build/install/test commands; lint/typecheck marked not
  configured:** §8 (build, install, test) + §8.4 ("Not configured").

## Derivation (evidence, not guessed)

Skill names/status derived from the READ-ONLY legacy source
`C:\Users\abero\dev\.claude`:

- 47 portable = intersection of `.claude/skills/` and `.claude/skills-gpt/`
  directory names (excluding `_shared`).
- 3 Claude-native exclusions = in `.claude/skills/` but not `.claude/skills-gpt/`:
  `claude-oauth-auth`, `context-slim`, `judge-motion` (also `gpt-capable=N` in
  `.claude/references/model-mapping.md`).
- `local_capable` (24) copied from the `local-capable=Y` rows of
  `model-mapping.md`.
- `capabilities`: `filesystem` (all 50 — baseline capability every skill uses;
  not a scarce host gate), `vision` (2: judge-ui, judge-motion), `sub-agent`
  (16 — see Iteration 2 finding #7 audit). Invariant: vision/sub-agent ⇒ not
  local-capable (test-enforced).

## Tests

Package-integrity (public, no private source required):
```
python -m pytest tests\package-integrity
```
Result: **26 passed, 1 skipped** without `SKILL_MESH_LEGACY_SOURCE`
(the optional source-verification test skips cleanly); **27 passed** with it set.

Baseline calibration:
```
python -m pytest $env:SKILL_MESH_LEGACY_SOURCE\.claude\lib\calibration\test_calibrate.py
```
Result: **40 passed**.

Combined for this iteration: **67 passed** (27 package-integrity + 40 calibration)
with the legacy source env set; the public package suite alone is 26 passed +
1 skipped.

Generator determinism verified: re-running `tools/gen_manifest.py` reproduces the
committed manifest and fixture with no drift.

No lint/typecheck command exists in this repository; none was invented (per plan §6).

## Scope discipline

- Only Step 33 files created. No plan status edits, no merge/push/issue close.
- Nothing outside the worktree modified; `C:\Users\abero\dev\.claude` used
  read-only for derivation.
- Legacy paths in public docs/manifest are coding-root-relative (`.claude/...`),
  clearly labeled as READ-ONLY migration-source context. No absolute private user
  path is embedded in any committed public deliverable (manifest, fixture,
  architecture, provider docs, generator, test) — enforced by
  `test_no_absolute_private_paths_committed`. The pinned `.venv-1` interpreter and
  the legacy source root are supplied by the environment at runtime only.

## Pre-existing debt (not fixed — out of scope, read-only source)

- `.claude/references/model-mapping.md` prose states "Count: 22 skills" for
  local-capable, but the table actually has 24 `local-capable=Y` rows. The manifest
  uses the authoritative table rows (24). The legacy file is READ-ONLY and was not
  modified.

## Report path

`C:\Users\abero\dev\worktree_build-step-33-20260726101916\.build-step\dev-report.md`
