# NOTE: This is the canonical provider-independent contract. Every provider adapter must load it in full.

# tier-escalate

Build a current, evidence-backed map of the skill phases that warrant a stronger model tier. The skill scans the active host's discovered skill packages, classifies their complete behavior, and emits an operator map. It never changes a model selection, a setting, an instruction file, or a skill.

## Host contract

The provider adapter supplies these host bindings without weakening this core:

- `discovery_root`: the active host discovery root that contains this loaded skill package, unless the operator passed `--skills-dir`.
- `isolated_readonly_task`: a genuinely fresh-context, read-only task invocation. It must not share producer reasoning or prior batch history.
- `classification_tier`: the host capability corresponding to the workspace's ordinary fan-out tier. Resolve capability roles through the loaded profile's tier map when one exists. A configured or requested model is not an actual-model receipt.
- `policy_locator`: the host-specific way to locate the nearest workspace model-tiering policy when the operator did not pass `--policy`.

If fresh isolated tasks are unavailable, stop with `required_tool_missing: classification-fan-out`. Do not classify in the parent context and do not serialize multiple classifier roles through one context.

Never expose hidden chain-of-thought. Preserve only decisions, cited evidence, artifacts, commands, and the report required below.

## Invocation

```text
/tier-escalate [--skills-dir <path>] [--out-dir <path>] [--policy <path>] [--dry-run]
```

Defaults:

- `--skills-dir`: the adapter's `discovery_root`.
- `--out-dir`: `./tier-escalate-out` relative to the invocation cwd.
- `--policy`: the adapter's nearest model-tiering policy, when one exists.

Parse and validate all arguments before any output setup. Unknown flags, missing values, a missing skills directory, or an unreadable explicit policy are input errors and stop before classification or writes.

## Safety and mode contract

| Mode | Reads | Isolated classification | Creates output directory | Writes map |
|---|---|---|---|---|
| normal | yes | yes | immediately before artifact write | yes |
| `--dry-run` | yes | yes | **no** | **no** |

Dry-run is a true zero-write preview for declared task outputs. It does not create the output directory, a temporary file, a cache, or a receipt. It prints the complete proposed map in the report and labels the artifact `not written (dry-run)`. Host transcript storage outside the task's declared outputs is not attributed to this skill.

Normal mode writes only `<out-dir>/escalation-map.md`. Create the output directory only after classification and synthesis succeed. Never edit a discovered package, workspace instructions, model settings, or live host profiles. Never commit, push, install, or switch a session model.

## Governing escalation rule

Recommend a stronger session tier only for a single load-bearing seed artifact whose quality sets the deliverable's ceiling and for which a diversity committee cannot substitute. Typical shapes are greenfield architecture authoring, hard root-cause diagnosis, and deep cited synthesis.

Apply all four corrections:

1. A parallel reviewer, grader, search, or retry array is never the stronger-tier target. Diversity carries its quality. A single named-trigger diagnosis arm may be a seed phase; an array may not.
2. A synthesis that must preserve one coherent judgment is a SOLO/GATE candidate. Do not relabel it as a cheap fan-out merely because parallelism is available.
3. `CONDITIONAL` requires a concrete trigger an operator can check before the phase starts. A trigger such as "when it feels big" is invalid.
4. A session escalation can cascade into unpinned child arms. Any candidate that dispatches arms must prove those arms are explicitly pinned to the ordinary fan-out tier. Otherwise mark `arms-unpinned` and require pinning before escalation.

The map is derived from both this fixed rule and the current policy source. When a located policy disagrees with the skill source or with this fixed rule, report the disagreement with citations. Do not silently choose one, rewrite policy, or claim that changing the current session repairs it. If no policy source is available, say `policy comparison: unavailable`; do not invent a path or current setting.

## Phase 1: discover complete skill packages

1. Resolve `skills_dir` and list the matched package entrypoints before forming task prompts.
2. Discover exactly `<skills-dir>/*/SKILL.md`; skip directories without `SKILL.md`.
3. For every entrypoint, resolve its local Markdown links that define behavior, including its shared `core.md` and provider adapter when present. Read the entrypoint and every required linked behavior body. Classification of the generated launcher or entrypoint alone is invalid.
4. Reject a package whose entrypoint cites a required behavior body that is missing, escapes the discovery root, or cannot be read. Report `required_skill_body_missing` with the entrypoint and link; do not infer its behavior.
5. Record the resolved entrypoint and behavior-body paths in the classification input inventory.

Print one discovery line containing the resolved skills directory, skill count, output directory, mode, and policy source or `unavailable`.

## Phase 2: fresh isolated classification

Batch roughly 6-8 skills per classifier, bounded by host capacity. Dispatch independent classifiers concurrently where the host supports it. Capacity may change batching, never isolation or completeness.

Load `<repo>/_shared/skill-role-taxonomy.md` in full, resolving its emitted relative path from this loaded package, never from `--skills-dir`. If missing or unreadable, stop with `required_tool_missing: role-taxonomy` before any classifier dispatch or write. Run its complete-package
discovery and isolated-classification protocol. Every classifier receives:

- the exact entrypoint and behavior-body paths for its batch;
- that shared reference's section 1 taxonomy and tag boundaries verbatim;
- the four corrections above verbatim;
- the same output schema below;
- an instruction to remain read-only and cite path plus heading or line evidence for every nontrivial claim.

Each classifier returns exactly one row per skill:

```text
Skill | Roles | Verdict | Seed phase | Trigger | Arms pinned | Evidence | Note
```

Verdicts:

- `FABLE-SEED`: one named seed-artifact phase satisfies the governing rule.
- `CONDITIONAL`: that named seed shape exists only under a concrete named trigger.
- `STAY`: diversity, iteration, or mechanical execution carries quality.

`FABLE-SEED` requires a seed phase. `CONDITIONAL` requires both a phase and trigger. `Arms pinned` is `yes`, `no`, or `n-a`; a skill that dispatches arms cannot use `n-a`. Evidence must cite the complete behavior body, not only `SKILL.md` frontmatter or launcher prose.

Each task also reports `actual model: <receipt value | UNKNOWN>`. Requested tier, adapter configuration, or model-map resolution is not a receipt. The parent reports `UNKNOWN` when the host supplies no actual-model receipt.

## Phase 3: verify and synthesize

Before accepting a `FABLE-SEED` or `CONDITIONAL` row, the parent reopens every cited behavior body and verifies the seed phase, trigger, dispatch shape, and arm pin. A missing or contradicted citation becomes `STAY` with note `classification evidence not verified`; it never becomes a positive escalation by inference.

Create a map with:

1. `## Stronger-tier seed phases`: `Skill | Seed-artifact phase | Why diversity cannot substitute | Arms pinned | How to apply | Evidence`.
2. `## Conditional escalations`: `Skill | Trigger | Phase | How to apply | Evidence`.
3. `## Stay on the default orchestration tier`: every other skill with its diversity or mechanical reason.
4. `## Policy comparison`: source path or unavailable, current-policy agreements, and cited policy/source disagreements.
5. `## Classification receipts`: batch identifier, input package names, and actual model receipt or `UNKNOWN`.

For a positive row with pinned or no arms, `How to apply` says to use the target host's operator model-selection mechanism for the seed phase and then restore the workspace default. For `arms-unpinned`, it says `pin fan-out arms to the ordinary fan-out tier before any session escalation`. These are operator instructions, never claims that the current host changed its model.

An optional paste-ready policy block may be included, clearly labeled `PASTE-READY — NOT APPLIED`. It contains only verified seed rows and triggers.

Lead the map with the scan count, positive and conditional counts, mode, policy source, and date.

## Phase 4: persist and report

In normal mode, create the output directory and write UTF-8 `<out-dir>/escalation-map.md` only after the complete map exists. In dry-run, print that same body and write nothing.

Print:

```text
tier-escalate — <skills-dir>

Scanned:       N skills
FABLE-SEED:    F skills
CONDITIONAL:   C skills
STAY:          S skills
Policy:        <path | unavailable>
Actual models: <batch=receipt | batch=UNKNOWN; ...>

Artifact:
  escalation-map.md — <path | not written (dry-run)>

Next (operator action, not performed):
  Apply a verified seed row only through the target host's model-selection mechanism.
  Resolve every reported policy/source disagreement before treating the map as policy.
```

End with the exact line:

`tier-escalate produced the escalation map; it did not change any session model, setting, instruction file, or skill.`
