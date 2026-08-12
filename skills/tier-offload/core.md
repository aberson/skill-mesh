# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/tier-offload/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. A fresh-context task invocation or workflow means an isolated host action with the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# tier-offload

Reads every `SKILL.md` under your `.claude/skills/`, classifies each skill's LLM-bearing roles with a fixed taxonomy, then applies the Switchboard routing rule to decide which (and only which) sub-tasks are safe to run on a cheap **local** model instead of the orchestrator's primary provider. It emits two artifacts: a human-readable **inventory** (markdown, grouped by routing verdict) and a **switchboard config** (`enabled_call_sites` map) that the `switchboard` `local_judge` client loads directly.

This is the generic, contributable **scanner** half of Switchboard offload. It is **discovery + config only** — it identifies and configures the local-safe slices; the actual wiring of each skill to call `local_judge` stays a guided, per-user edit you make afterward. It never edits a skill.

## When to use

- You've adopted the `switchboard` local-offload core and want to know which of *your own* skills have a sub-task safe to route to the local model.
- You want to regenerate the offload inventory after adding or changing skills (the safe surface drifts as skills evolve).
- You want a config file the `local_judge` client can load, without hand-authoring the `enabled_call_sites` map and risking a shape mismatch.

## Background — the routing rule this skill encodes

The offload's one governing rule (Switchboard Decision 9 / the 3-tier judge split): **authorship, planning, orchestration, and any final/gating judgment stay on the orchestrator's primary provider; only a fan-out array of cheap judges/graders goes local; mechanically-checkable work goes to a script (no LLM).** The local model is **never on a correctness gate** — it advises, the strong-tier provider gate decides. Default strong gate: Claude (primary provider); override via router configuration.

### Taxonomy + classification protocol — shared reference

Classification follows `<repo>/_shared/skill-role-taxonomy.md`: its **§1 taxonomy** (the seven tags — ORCH / AUTHOR / PLAN / JUDGES / GATE / MECH / SOLO — plus the tag boundaries), its **§2 fan-out classification protocol**, and its **§3 output shape**. That reference is direction-neutral; this skill layers the down-direction (offload) rules on top: the four corrections below, the hard gate-precondition invariant, and the LOCAL / PRIMARY / SCRIPT verdict columns added in Phase 2.

### The four corrections (apply them — a naive "every fan-out → local" read is wrong)

1. **Authorship fan-outs are NOT offloadable.** `user-brainstorm` / `user-learn` / `repo-init` / `repo-update` fan out, but each task *writes content* (AUTHOR), so it stays on the orchestrator's primary provider. A fan-out is only local-safe if every arm is *judging*, not *producing*.
2. **Only the Style reviewer lens is cheap.** In a multi-lens reviewer (review-gauntlet / review-deep / build-step), the **Correctness** and **Bugs** lenses are deep-reasoning drift-catchers (`code-quality.md`) and stay on the orchestrator's primary provider. Only the **Style** lens is the cheap local slice. (review-deep's Style lens already runs on the haiku tier — smallest lift.)
3. **A checklist "fan-out" that is really one primary-provider pass is NOT a drop-in.** `plan-review` / `plan-wrap` enumerate "sections" but run them as a single primary-provider pass today, not a real parallel array. Tag SOLO, route to the orchestrator's primary provider; it's refactorable-to-local later, not offloadable now.
4. **Tool-using judge arms are never local-safe.** A JUDGES array whose arms require live tool use (WebFetch/browser, `gh`, substrate commands) cannot route to `local_judge` regardless of shape — the local endpoint is text-in/text-out. Verdict PRIMARY with a tier note (`sonnet`, low effort) naming the blocking tool. Canonical example: deep-research's 3-vote source-verification array — perfect JUDGES shape, blocked by its WebSearch/WebFetch requirement.

And the hard invariant: **offloading a JUDGES array is only safe if the strong-tier provider GATE consolidates its findings.** If a skill's reviewers gate *directly* today, routing them local without first inserting a strong-tier final judge makes the weak model the gate — forbidden. Flag this in the inventory as a precondition (`gate-precondition: insert-strong-tier-final-judge`), never as already-safe.

**`build-step-style` is a standing hard `false` — never emit `true`.** A "build-step now consolidates on its Step 7 primary-provider aggregate" observation does NOT re-license it: Step 7 *is* the merge-decision gate, and Switchboard Decision 3 keeps the local model out of a merge context entirely (even as an advisory Style lens); Style is also the lowest-token lens, so there is no offset to weigh. This exact "precondition satisfied → enable" read already emitted a defective `true` into `offload-scan-out/offload-config.json` (found + reverted 2026-07-21). The skill's own eval enforces `false` (`test_sample_config_loads.py::test_enabled_call_sites_gate_as_expected`); emit `build-step-style: false` regardless of the Step 7 check.

## Phase 1 — Bootstrap: discover the skill set

Parse args. Resolve `--skills-dir`:
- If given, resolve to an absolute path.
- Default: walk up from cwd to the innermost ancestor containing a `.claude/skills/` directory; use that.

Enumerate the skill set per the shared reference's §2 steps 1–2 (Glob discovery, skip non-skill entries, `ls` the matched filenames before quoting any into a sub-agent prompt).

Resolve `--out-dir` (default `./offload-scan-out`). Create it if absent (PowerShell: `New-Item -ItemType Directory -Force <path>`).

Print the discovery line before analysis: the resolved skills dir, the count of skills found, and the out dir.

## Phase 2 — Parallel classification (read-only fresh-context fan-out)

Run the shared reference's **§2 fan-out classification protocol** exactly (read-only fresh-context task invocations using the sonnet tier (resolve via model-tier-map.json) per the reference §2, 6–8 skills per batch, all of a batch's tasks dispatched in one message, the §1 taxonomy verbatim in every task's prompt, read-only/classify-only discipline), with these down-direction additions:

- Each task's prompt must include — besides the reference's §1 taxonomy verbatim, per the reference's own protocol — the **four corrections** verbatim (above). Every task must apply the SAME rules, or the inventory drifts per-batch.
- Each task extends the reference's §3 output shape with the down-direction verdict columns, returning per skill: `Skill | Roles (tags) | Verdict | Local slice (if LOCAL) | Note`, where **Verdict** is:
  - **LOCAL** — has a genuine JUDGES array (parallel cheap scoring), every arm judging not producing. Name the specific slice (e.g. "structural/rubric grader", "Style lens").
  - **PRIMARY** — only ORCH / AUTHOR / PLAN / GATE / SOLO roles (or a JUDGES array that fails a correction).
  - **SCRIPT** — only MECH roles; nothing to offload to an LLM.
- For each LOCAL verdict, require: the slice name, and whether a `gate-precondition` applies (does the skill's array gate directly today, needing a strong-tier final judge inserted first?).

Collect every task's table before Phase 3.

## Phase 3 — Synthesize the inventory + config

Merge all agent tables into one inventory, grouped exactly like the Switchboard Appendix:

1. **The local surface** — the table of LOCAL skills only: `Skill | Local slice (small model) | Everything else → primary provider | Note`. This is the load-bearing output.
2. **Primary-provider routed** — bulleted list of PRIMARY-verdict skills (authorship / planning / single-pass reasoning / orchestration / final-gate).
3. **No LLM (scriptable / mechanical / doc)** — bulleted list of SCRIPT-verdict skills.

Write the inventory to `<out-dir>/inventory.md`. Lead it with a one-paragraph summary: N skills scanned, K local-safe slices found, and the date.

### Build the config (skip if `--inventory-only`)

For each LOCAL slice, mint a **task_class** name and add it to the `enabled_call_sites` map. The task_class is the call-site identifier the wired skill will pass to `local_judge(task_class=...)`. It MUST satisfy switchboard's name-safety rule — match `^[A-Za-z0-9._\-]+$` exactly (letters, digits, `.`, `_`, `-` only; **no spaces, no slashes, no `:` or other metacharacters**). Use a stable `<skill>-<slice>` slug, e.g. `skill-iterate-grader`, `review-gauntlet-style`, `context-slim-classifier`.

Map each task_class to:
- `true` — offload allowed, use switchboard's default model (the common case; the production deployment uses one model for all slices per switchboard D2).
- a model-name string — only if you deliberately pin a different model for that slice (must also match `^[A-Za-z0-9._\-]+$`). Default to `true`.

**Do NOT include a slice that has an unmet `gate-precondition`** as plain `true` — instead emit it as `false` (configured but disabled) and note in the inventory that it activates only after the strong-tier final judge is inserted. This keeps an unsafe slice from silently becoming a live gate.

Write the config as JSON to `<out-dir>/offload-config.json` with exactly this shape (this is the integration contract — it must load into `switchboard.config.SwitchboardConfig`):

```json
{
  "less_token_mode": true,
  "enabled_call_sites": {
    "skill-iterate-grader": true,
    "skill-evolve-grader": true,
    "review-gauntlet-style": true,
    "review-deep-style": true,
    "goblin-suggest-judge": true,
    "context-slim-classifier": true,
    "build-step-style": false
  }
}
```

Shape rules (match `switchboard/config.py` exactly):
- Top-level keys are a subset of `SwitchboardConfig`'s fields: `less_token_mode` (bool), `enabled_call_sites` (object), optionally `effort` (object), and optionally `base_url` / `model` / `cold_timeout_s` / `warm_timeout_s` / `max_tokens`. Emit only `less_token_mode` + `enabled_call_sites` unless the user pinned endpoint values — let the rest default.
- `enabled_call_sites` is an **object** mapping each task_class **string** to a **bool or a model-name string**. No nested objects, no arrays, no nulls.
- `effort` (optional) is an **object** mapping a task_class **string** to a primary-provider reasoning-effort tier — one of `low` / `medium` / `high` / `xhigh` / `max`. HONEST SCOPE: this is a hint for **primary-provider task dispatch** (a host reasoning-effort override when the slice's judges run on the orchestrator's primary provider); `local_judge` does NOT consume it. switchboard validates + round-trips it but acts on nothing — emit `effort` only to record a per-slice recommendation (e.g. `{"review-deep-style": "low"}`), never as a live local knob.
- Every task_class key AND every model-name value must match `^[A-Za-z0-9._\-]+$`.
- A slice that gates directly today (unmet `gate-precondition`) is emitted as `false`.

## Phase 4 — Report

Print a summary (do not truncate):

```text
tier-offload — <skills-dir>

Scanned:        N skills
Local-safe:     K slices  (M live / G gated-pending-final-judge)
Primary-routed: A skills
No-LLM:         S skills

Artifacts:
  inventory.md       — <out-dir>/inventory.md
  offload-config.json — <out-dir>/offload-config.json   (loads into SwitchboardConfig.enabled_call_sites)

Next (per-user, NOT done by this skill):
  Install the config so the switchboard client loads it: copy offload-config.json to
  ~/.switchboard/config.json (the home default, $HOME\.switchboard\config.json on Windows)
  OR set $env:SWITCHBOARD_CONFIG to its path, then verify with `python -m switchboard config`
  (offload_active:true means it is live). See switchboard/README.md "Turning offload on/off"
  for the full enable/disable flow + resolution order.
  For each live slice, wire the skill's sub-task to call local_judge(task_class="<key>").
  For each gated slice, first insert a strong-tier final judge that consolidates, then flip the
  config entry from false → true.
```

End with the exact standalone line:

`tier-offload wrote the inventory + config — wiring each slice to local_judge stays a guided per-user edit (it was NOT auto-applied).`

## Constraints

- **Discovery + config only. Never auto-wire.** This skill never edits a `SKILL.md` to call `local_judge`. It writes the inventory and the config; the operator wires each slice.
- **Use read-only fresh-context task invocations for classification.** They cannot edit or write — the safe substrate for reading someone's skills. Use the sonnet tier (resolve via model-tier-map.json).
- **Apply the four corrections.** Authorship fan-outs → the orchestrator's primary provider; only the Style reviewer lens is cheap; checklist single-passes are SOLO not LOCAL; tool-using judge arms are never local.
- **Never emit a directly-gating array as live (`true`).** Emit `false` + a `gate-precondition` note; it activates only after a strong-tier final judge is inserted (Switchboard Decision 3 — the local model is never the gate).
- **The config must load.** Every task_class key and model-name value must match `^[A-Za-z0-9._\-]+$`. No spaces/slashes/colons. Values are bool or model-name string only. A mismatch here is the bug class `test_sample_config_loads.py` exists to catch — if unsure, validate against `switchboard/config.py` before writing.
- **Autonomous — no mid-run (y/n) prompts.** Run bare = scan + report + write inventory + config. `--dry-run` prints the report and writes nothing.
- Do not commit. Leave artifacts in the out dir for the operator.
