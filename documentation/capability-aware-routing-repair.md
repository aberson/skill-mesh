# Capability-aware routing repair

## Authorization and scope

On 2026-11-01 the operator requested implementation of the reviewed seed using
Opus subagents. This supersedes the seed's earlier advice-only boundary for this
repair. It continues the same session's uncommitted `user-build-route` creation
and authorizes an UPDATE to `plan-expedite`; it is not a general catalog waiver.
Existing changes and the unrelated `dev/` directory are preserved.

The intended outcome is a compatible recommendation with explicit runtime
qualification status, followed by a host-appropriate continuation that preserves
constraints, deadlines and required reviews. Preparation alone must not promise
an executable unattended build. The seed's sibling-project incident is supplied
evidence; this repair does not claim to reproduce its host thread exhaustion.

Canonical scope: `skills/user-build-route/core.md`,
`skills/plan-expedite/core.md`, and affected `plan-expedite` provider adapters.
Build isolation, signing, reviewer independence and the host's blocked-goal
threshold remain authoritative. No scheduler, agent manager, new capability
registry, package resources or alternative build implementation is introduced.

## Preflight and delegation

The source base is `6ad91748a5d886c2d6631131bb16d68efd82985d`. A fresh fetch showed
main and origin/main synchronized; the workspace freeze file was absent. The
dirty paths are the earlier authorized creation and unrelated work, not a clean
checkout claim. Target hashes, original file snapshots and the dirty-path list
were captured outside the repository before implementation.

The UPDATE request has `skill_name: plan-expedite`, `new_name: null`, the base
above, `description: null`, `capabilities: [filesystem]`, empty `resource_paths`
and empty `reference_dispositions`. The routing-skill change continues its
already-authorized CREATE request rather than pretending it exists at HEAD.

Independent Claude CLI calls requested `--model opus`, without fallback. The
first read-only analysis reported `claude-opus-5-5` and no permission denials.
The implementation worker is restricted to the named source files. Review and
behavioral workers receive read-only tools and do not run pipeline stages,
publish issues or mutate a consumer profile.

## Changes

- `user-build-route` separates workload fit from execution compatibility. It
  checks installed contracts and observable facts without consuming agent slots.
  Known conflicts fail closed; unknown runtime support gets qualification first.
  Review support is assessed per role, and required gates are preserved by
  reference rather than copied into an invented execution procedure.
- `plan-expedite` checks compatibility before mutations, on resume, before
  publication/checkpoint boundaries and before its final continuation. It
  distinguishes completed preparation from an unqualified destination build.
  Completed stages are not replayed to repair a stale continuation.
- Handoffs preserve the original deadline, scope, review and acceptance
  obligations. A stale saved Next Action or rendered handoff is explicitly
  superseded; an unavailable safe refresh halts rather than publishing a runnable
  stale instruction. An expired window requires new authorization.
- Codex and Copilot continuations use verified destination syntax or portable
  prose. No unsupported goal command, capacity-control setting or capability
  certificate is invented. A blocker records unfinished checks and cleanup once,
  respects the host's blocked-audit threshold, and never counts as completion.

## Independent Opus work

Read-only analysis, implementation and independent review were delegated through
Claude CLI with `--model opus`; completed outputs identify `claude-opus-5-5`.
The implementation worker reached its 420-second bound after writing a candidate.
Its edits were preserved and inspected, not represented as a completed worker
result. Subsequent independent reviews found defects involving fresh-session
recovery, stale handoffs, deadline enforcement and destination command rendering;
those were corrected. The full closing review returned **PASS**. Behavioral
trials then exposed unchecked elapsed-time arithmetic, an undocumented capacity
suggestion and over-restrictive reviewer dispatch wording. Narrow corrections
received a further independent Opus **PASS**. No fallback model was used.

## Verification

All three profiles built: Claude 58 skills / 158 files, GPT and Codex each
55 skills / 144 files. The normal installer refreshed a disposable Claude
consumer home. Behavioral workers read its generated `SKILL.md` and co-located
core; generated destination-provider contracts were available for inspection.
They had read-only tools, and did not execute goals, pipeline stages or probes.

The final focused command passed **97 tests in 2.92 seconds**:

```text
python -m pytest tests/package-integrity/test_v2_orientation_contract.py tests/package-integrity/test_v2_session_contract.py tests/package-integrity/test_codex_capability_claims_honesty.py tests/package-integrity/test_manifest_contract.py -q
```

Both generated Codex packages passed `quick_validate.py`; the disposable
consumer's entrypoint and core hashes match the generated Claude packages.
`git diff --check` passed. No representative core changed, so the representative
release-candidate report is unaffected. The earlier catalog-creation validation
remains in `user-build-route-validation.md` and is not replaced by these results.

### Consumed-profile behavioral observations

These are actual Opus responses after reading the installed generated Claude
skill, with supplied target-host facts. They are not live Codex dispatch,
signing, isolation or capacity evidence. Each worker was asked for the actual
operator-facing response, not a critique or a hypothetical test plan.

| Scenario input | Observed final response |
|---|---|
| Compare two combat-animation timing treatments in 45 minutes; preserve dirty checkout; no staging, stash, commits, pushes or issue publication; independent read-only review required | Recommended an attended bounded experiment, limited to operator-selected experiment files, with comparable captures, review, stop conditions and operator acceptance. Production integration stays outside scope. |
| Prepared export plan; current Codex dispatch failed with `collab spawn failed: agent thread limit reached`; no release tool; original deadline still active | Kept pipeline workload classification but refused execution in the failed session; offered a conditional fresh-session qualification-first handoff, preserving review and deadline. No invented capacity setting. |
| Same prepared plan; clean checkout; authorized Git/issue effects; exact current route freshly qualified and enough observed capacity | Recommended ordinary `build-phase`, with dispatch-time gates and independent review intact. No persistent goal or invented deadline. |
| No-commit/no-stash dirty experiment submitted to plan-expedite before any stage | Halted at input, named incompatible preparation and build effects, left plan and GitHub unchanged, and offered a conditional non-pipeline experiment with independent review. |
| Successful preparation supplied as scenario state; new Codex destination unqualified; start 05:59:22 UTC and deadline 06:59:22 UTC | Reported preparation complete but build unqualified. Rendered portable attended qualification-first prose, retained exact timestamps, delegated elapsed/remaining calculation to the runner's clock, and armed no goal. |
| Fresh conversation after original deadline; no new time authorization | Emitted status/recovery instructions only; no build or probe before explicit new time authorization. |
| Different old session failed dispatch; new destination has no observed failure or qualification | Treated new destination as unqualified rather than permanently incompatible; preserved the old deadline and required qualification before implementation. |
| All preparation stages already complete; same-session dispatch now fails; saved unconditional goal is stale; no safe checkpoint identity | Halted, marked saved Next Action superseded and forbidden to run, acknowledged stale bytes were not changed, and emitted no build/goal continuation. No completed stage was replayed. |

The routing and safety outcomes above were observed, not inferred from string
checks. Presentation remains imperfect: some responses exceed the requested
one-or-two-sentence Why/Next format and repeat low-level probe details despite
the core's brevity instruction. This is recorded as a limitation rather than a
claim that the concise-output requirement was fully demonstrated.

Final consumed Claude core SHA-256 values:

| Skill | SHA-256 |
|---|---|
| user-build-route | `53985247ff966ec98804bf323497375d92cebc212e727ad0cd92ab3af01e19ae` |
| plan-expedite | `ef74e48038f155130378ddc2b123b3896066a1d45d42347456f4e322aa22f2ce` |

### Boundaries

No full repository-root DONE gate, live build qualification, installed daily
profile update, commit or push is claimed by this record.
The supported-build observation demonstrates a usable recommendation, not an
executed production build. The re-drive contract was reviewed and stale-resume
behavior observed; no live persistent goal was armed to force three blocked
turns. Host capacity exhaustion itself remains an external condition, not a
defect this prose change repairs. No numbered plan step or release is marked DONE.
