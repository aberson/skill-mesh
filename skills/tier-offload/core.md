# NOTE: This is the canonical provider-independent contract. Every provider adapter must load it in full.

# tier-offload

Build an evidence-backed inventory of low-stakes judge slices that may be offered to Switchboard, plus a candidate Switchboard config. This skill discovers and classifies; it never invokes a local model, wires a skill, installs a config, changes a live profile, or enables a site without verified independent primary-provider gating review.

## Host contract

The provider adapter supplies:

- `discovery_root`: the active host discovery root containing this loaded package, unless `--skills-dir` is explicit.
- `isolated_readonly_task`: a genuinely fresh-context, read-only task invocation.
- `classification_tier`: the host capability corresponding to the workspace's ordinary fan-out tier.

If fresh isolated tasks are unavailable, stop with `required_tool_missing: classification-fan-out`. Do not classify in the parent context. Requested/configured model identity is not an actual-model receipt; report `UNKNOWN` absent a host receipt.

Never expose hidden chain-of-thought. Preserve only decisions, cited evidence, artifacts, commands, validator output, and the report required below.

## Invocation

```text
/tier-offload [--skills-dir <path>] [--out-dir <path>] [--switchboard-root <path>] [--inventory-only] [--dry-run]
```

Defaults:

- `--skills-dir`: adapter `discovery_root`.
- `--out-dir`: `./offload-scan-out` relative to invocation cwd.
- `--switchboard-root`: optional. When omitted, validation may use a prepared sibling Switchboard checkout only if an ancestor of cwd contains exactly `switchboard/switchboard/config.py`; otherwise validation is unavailable.

Validate arguments before classification or writes. An explicit Switchboard root must contain `switchboard/config.py` and `switchboard/cli.py`; otherwise report validation unavailable rather than searching elsewhere or installing anything.

Capture the invocation cwd before any directory change. Resolve `--out-dir` against that cwd to an absolute output directory, and derive the absolute `offload-config.json` path from it. Use those same resolved paths for reporting, writes, and validation even when a validator runs from another directory. Resolving paths does not create them.

## Mode matrix

| Mode | Inventory | Config candidate | Output directory | Files written |
|---|---|---|---|---|
| normal | produced | produced | created after synthesis | `inventory.md`, `offload-config.json` |
| `--inventory-only` | produced | **not produced** | created after synthesis | `inventory.md` only |
| `--dry-run` | printed | printed unless inventory-only | **not created** | **none** |
| both flags | printed | **not produced** | **not created** | **none** |

Dry-run creates no output directory, temporary file, config, cache, or receipt. Inventory-only must never claim a config path or validation result; print `offload-config.json — not produced (inventory-only)`. Normal and inventory-only mode create the directory only immediately before their first artifact write. In normal mode, failed pre-write validation suppresses only the config write: still write `inventory.md` with the exact invalid result.

## Routing rule

Authorship, planning, orchestration, synthesis, and final/gating judgment stay on the primary provider. Mechanically checkable work goes to a script. Only a genuine parallel array of low-stakes text-in/text-out judges is a local candidate.

Apply these corrections:

1. A fan-out that writes content is `AUTHOR`, not a local judge array.
2. Correctness, bugs, security, and test-quality review remain primary-provider roles. Only a narrowly bounded Style judgment may be a local candidate.
3. A checklist executed as one reasoning pass is `SOLO`, not `JUDGES`.
4. Judge arms requiring browser, network, GitHub, shell, or live substrate tools are primary-provider work; Switchboard's judge boundary is text-in/text-out.
5. `build-step-style` is a standing hard `false`, regardless of any gate evidence.

A primary-provider gating reviewer means a non-local primary-provider reviewer at its configured tier, resolved through current host policy and the loaded tier map. It is a distinct fresh independent reviewer, not the local producer; its tier need not be the separate final-judge tier.

The local model is advisory only. A candidate may be emitted as `true` only when the current complete skill source proves that a fresh, independent primary-provider gating review always runs after the local result and alone fills the gating slot. Merely calling a primary-provider synthesis, running deterministic aggregation over a local verdict, or saying "advisory" is insufficient.

## Gate-evidence rule

Every local candidate has one gate state:

- `EVIDENCED`: cited source proves a fresh independent primary-provider gating reviewer always runs, its result controls the gate, and the local verdict cannot fill or waive that slot.
- `ABSENT`: no such proof is present.
- `CONFLICTING`: source sections disagree about whether local output can gate, whether the primary-provider gating reviewer always runs, or which result controls the decision.

Only `EVIDENCED` may map to `true`, except `build-step-style`, which remains `false`. `ABSENT` and `CONFLICTING` map to `false`. The parent must reopen and verify every positive citation. Missing, stale, or contradicted evidence becomes `CONFLICTING` or `ABSENT`; never infer a positive gate.

## Phase 1: discover complete skill packages

1. Resolve `skills_dir`; list matched entrypoints before constructing task prompts.
2. Discover `<skills-dir>/*/SKILL.md`; skip non-skill directories.
3. Resolve and read every local Markdown behavior link required by the entrypoint, including shared `core.md` and provider behavior. Classifying only generated launcher prose, frontmatter, or a description is invalid.
4. A missing, unreadable, or discovery-root-escaping required body produces `required_skill_body_missing`; do not infer that package's routing.
5. Record all entrypoint and behavior-body paths in the classification input inventory.

Print the resolved skills directory, skill count, output directory, flags, and Switchboard validator source or `unavailable`.

## Phase 2: fresh isolated classification

Load `<repo>/_shared/skill-role-taxonomy.md` in full, resolving its emitted relative path from this loaded package, never from `--skills-dir`. If missing or unreadable, stop with `required_tool_missing: role-taxonomy` before any classifier dispatch or write. Otherwise run its complete-package
discovery and isolated-classification protocol. Batch roughly 6-8 skills per classifier and
dispatch concurrently within host capacity. Every classifier receives the shared reference's
section 1 taxonomy and tag boundaries verbatim, plus the corrections, gate-evidence rule,
row schema, and exact package paths. It remains read-only and cites path plus heading or line
evidence.

Each classifier returns one row per skill:

```text
Skill | Roles | Verdict | Local slice | Gate state | Gate evidence | Tool needs | Note
```

Verdicts remain exactly `LOCAL`, `PRIMARY`, or `SCRIPT`:

- `LOCAL`: a genuine low-stakes text-only judge slice exists. Its gate state may still force config `false`.
- `PRIMARY`: no eligible local slice, or a correction disqualifies it.
- `SCRIPT`: the classified role is mechanical and needs no LLM.

For `LOCAL`, name one stable slice and cite both the slice implementation and gate evidence or its absence/conflict. A classifier cannot set config values. It also reports `actual model: <receipt | UNKNOWN>`.

## Phase 3: parent verification and inventory

The parent reopens every `LOCAL` citation and verifies:

- each arm judges rather than authors;
- the arm is text-in/text-out and needs no live tools;
- the primary-provider gate evidence state;
- the proposed task-class name;
- the `build-step-style` hard disable.

Unverified local-shape evidence becomes `PRIMARY`. Unverified positive gate evidence becomes `ABSENT` or `CONFLICTING` and config `false`.

Produce `inventory.md` with:

1. `## Local candidates`: `Skill | Slice | Gate state | Config value | Primary-gate evidence | Note`.
2. `## Primary-provider routed`: each PRIMARY skill and reason.
3. `## No LLM`: each SCRIPT skill and mechanical route.
4. `## Config qualification`: validator source and exact validation result, unavailable, or `not performed (inventory-only)`.
5. `## Classification receipts`: batch, packages, actual-model receipt or `UNKNOWN`.

Lead with counts for scanned skills, local candidates, primary skills, mechanical skills, mode, and date. When a config is produced or printed, count its proposed `true` and `false` entries; these are proposals, never live or activated sites. Under inventory-only, report eligible and ineligible slices instead, with config `not produced` and validation `not performed (inventory-only)`. Never call a candidate `local-safe` unless both its local shape and `EVIDENCED` gate have been parent-verified.

## Phase 4: candidate config

Skip this entire phase under `--inventory-only`.

Create exactly:

```json
{
  "less_token_mode": true,
  "enabled_call_sites": {
    "example-slice": false,
    "build-step-style": false
  }
}
```

Rules matching the current `SwitchboardConfig` interface:

- Emit only `less_token_mode` and `enabled_call_sites` unless the operator explicitly supplied endpoint values; this skill defines no endpoint flags, so routine output contains only those two keys.
- `enabled_call_sites` is an object from task-class string to bool or model-name string. This skill emits bool values only.
- Every task-class must match `^[A-Za-z0-9._\-]+$`; mint stable `<skill>-<slice>` slugs.
- `true` requires parent-verified `EVIDENCED` gate state.
- `ABSENT`, `CONFLICTING`, and every unmet precondition emit `false`.
- Always include `build-step-style: false` if that slice is present in the inventory; never emit it as true.
- Do not read a live home config, environment-selected config, endpoint, or local model.

### Optional read-only Switchboard validation

When a prepared Switchboard source is available, validate the exact in-memory candidate with its own `SwitchboardConfig.from_mapping` implementation. Set `PYTHONDONTWRITEBYTECODE=1`; pass the JSON through stdin or memory; create no temp file. After a normal-mode write, the equivalent loud check is:

```text
python -m switchboard config --path "<absolute-config-path>"
```

run with cwd set to the prepared Switchboard root and `PYTHONDONTWRITEBYTECODE=1`. `<absolute-config-path>` is the exact artifact path resolved from the original invocation cwd before changing directories; quote it to preserve spaces. Do not rebase a relative output path in the Switchboard checkout. This command validates config only; never run bare `python -m switchboard`, `inspect`, `judge`, or any endpoint probe.

Record exact command or in-memory validator description, stdout, stderr, and exit status in the report. Exit zero qualifies schema compatibility only; it is not gate evidence, bake-off certification, or permission to install. A nonzero pre-write result suppresses the normal-mode config write and reports `not written (invalid candidate)`; still write the inventory with that result. Under dry-run it reports the candidate invalid and writes nothing. If the optional post-write loud check fails, retain the already-written file without cleanup and report its path as `invalid candidate retained`; write or update the inventory with that exact result before the final report. Label proposed-entry counts as invalid whenever either validation fails; they never describe enabled sites.

If no prepared loader exists, report `Switchboard validation: unavailable (prepared loader not found)`. The candidate may be printed or written as `unvalidated candidate`; never call it loadable, qualified, enabled, or active.

## Phase 5: persist and report

After successful synthesis, persist only the files allowed by the mode matrix as UTF-8. Config validation must occur against the exact candidate before normal-mode config write; inventory records its result.

Print:

```text
tier-offload — <skills-dir>

Scanned:        N skills
Local candidates: K (E eligible / G ineligible slices)
Proposed config entries: <M true / F false | not produced (inventory-only)>
Primary-routed: A skills
No-LLM:         S skills
Switchboard validation: <valid via path | invalid | unavailable | not performed (inventory-only)>
Actual models:  <batch=receipt | batch=UNKNOWN; ...>

Artifacts:
  inventory.md        — <path | not written (dry-run)>
  offload-config.json — <path | not written (dry-run) | not produced (inventory-only) | not written (invalid candidate) | path (invalid candidate retained)>

Next (operator action, not performed):
  Review false entries and their missing/conflicting gate evidence.
  Validate an unvalidated candidate with a prepared Switchboard checkout before installation.
  Wiring and installation require a separate workflow.
```

End with the exact line:

`tier-offload produced discovery artifacts only; it did not invoke a local model, wire a skill, install a config, or change a live profile.`
