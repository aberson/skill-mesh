# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

# plan-feature core

## Intent continuity (drift-ranger)

Follow [the intent continuity contract](../../_shared/intent-continuity.md).
Before adding phases, inspect the actual user entry point and existing implementations. Establish the intended journey and first missing capability; reuse accepted work before rebuilding it. Keep private context out of published plans.


## Purpose

Plan a feature or phase in an existing project. Produce a short, grounded plan that a fresh
reader can review and build from. Do not implement the feature, publish issues, commit, install,
launch, or claim that an independent review passed.

Invocation: `/plan-feature [feature name or one-line outcome]`. Use supplied facts immediately;
do not ask the operator to repeat them. Greenfield work belongs to `plan-init`. If discovery shows
the request is one small action or only trims an existing plan, return a concrete `goblin-do` or
`plan-trim` seed instead of padding it into a feature plan.

## 1. Establish the planning boundary

Resolve the target project and the one plan artifact to author. Read the applicable `AGENTS.md`,
`CLAUDE.md`, or equivalent project instructions before acting. Locate the project's canonical
entry plan and any parent/master-plan section that defines this feature. Preserve upstream scope,
decisions, dependencies, and reserved step IDs; report any drift rather than silently overriding
the parent.

Check the current branch, working-tree changes, active plan work, and recent relevant history.
Treat existing changes as someone else's unless proven otherwise. Write only the agreed plan and,
when required for discoverability, its existing canonical index/link. If ownership is ambiguous or
the target is being changed concurrently, hold the write and report the collision.

State the intended outcome in one sentence and record what is in and out of scope. Ask only for a
missing fact that changes scope or a consequential product/design choice. Group such questions;
there is no confirmation after each discovery stage. Use an explicit, reversible agent default for
routine details and label it as a default.

## 2. Targeted discovery

Read the producing source for every concrete value the plan will cite: schemas, function
signatures, CLI arguments, package scripts, routes, config keys, dependency versions, and runtime
entry points. Supporting docs may orient the search but are not proof of a produced value. If a
required producing file cannot be read, do not fill the gap from memory; mark the plan `HELD` and
name the missing evidence.

Start with the smallest useful set: relevant source and tests, the applicable parent-plan section,
recent commits touching that area, and current work. Expand only to answer a named uncertainty.
For any shared signature, schema field, constant, persisted shape, or public interface, search all
repository call sites and list the affected consumers. Record the search root and any exclusions;
a bounded search is evidence of its scope, not proof that no other consumer exists.

Prior-work retrieval is optional and advisory. When it could prevent repeated investigation:

1. If `find-again` is installed, run `find-again --root <workspace-root> status`, then
   `find-again --root <workspace-root> search "<feature keywords>" --limit 3`.
2. Otherwise, when the workspace contains the Find Again checkout, use
   `uv run --project <workspace-root>/find-again find-again --root <workspace-root> status` and
   the same `search` arguments.
3. Report index age, search scope, diagnostics that limit confidence, and the locators actually
   used. Do not refresh the index during planning. If the command, config, or index is unavailable,
   continue with current producing source, repository search, and the operator's supplied evidence.

Historical hits are leads. They never override current source or silently reintroduce old process
rules.

## 3. Resolve feature choices

Analyze affected existing modules, new components, shared consumers, compatibility/migration
needs, external dependencies, security boundaries, user-facing surfaces, and runtime operations.
Skip categories that do not apply and say why briefly rather than inventing complexity.

Present consequential alternatives with their tradeoffs and obtain the operator's choice before
marking the plan review-ready. Maintain a compact decision inventory with:

`Choice | Decision | Provenance (operator / agent default / inference) | Rationale | Alternatives or unresolved state`

Never convert an unresolved consequential choice or conditional predicate into an executable
default. A plan may be saved as `HELD` with the unresolved item and exact next decision, but it is
not ready for execution.

## 4. Author the plan

Save to the project's established plan location. If no feature-plan convention exists, use
`documentation/<feature-slug>-plan.md`. Keep a small feature small. Include each section below,
using a one-line `Not applicable - <reason>` when appropriate:

1. **What This Feature Does** - outcome, beneficiary, and reason.
2. **Existing Context** - only the architecture and constraints a fresh reader needs, with source
   locators and the parent-plan relationship.
3. **Scope** - explicit in/out boundaries.
4. **Impact Analysis** - `File or interface | Change | Reason | Verified evidence`; enumerate all
   found consumers for shared-interface changes and disclose the search boundary.
5. **New Components** - new files, modules, entities, services, or none.
6. **Design Decisions** - the decision inventory plus enough rationale to survive the conversation.
7. **Build Steps** - ordered vertical slices in the exact contract below.
8. **Risks and Open Questions** - item, consequence, mitigation/owner, and blocking state.
9. **Testing Strategy** - narrow tests, integration through the production caller, end-to-end
   evidence, and exact commands verified from their producing config.

### Build-step contract

Size each implementation step as one observable vertical slice that fits one worker context and
can be verified through its production caller. Use `<repo>/_shared/step-authoring.md` for sizing and the
authoritative deferred `Done when` sentinels. Do not split one coherent behavior into fragments.

```markdown
### Step N: <name>
- **Problem:** <one-line behavior to deliver>
- **Type:** <code | operator | conditional | wait>
- **Condition:** <real shell expression>  # required only for conditional
- **Issue:** #
- **Flags:** <supported build-step flags>
- **Start-cmd:** <verified command>        # required by runtime/full reviewer flags
- **URL:** <reachable URL>                 # required by runtime/full reviewer flags
- **Files:** <expected paths or bounded area>
- **Produces:** <artifact or behavior>
- **Done when:** <falsifiable acceptance through a real caller>
- **Depends on:** <step IDs or none>
```

Keep every `Problem`, `Type`, and blank pre-sync `Issue: #` field. Include optional fields only
when applicable, except that every step needs `Files`, `Produces`, `Done when`, and `Depends on`
for a usable handoff. Select flags from the current build-step argument contract and the applicable
plan-review field checks; do not load or copy the whole execution procedure merely to author a
plan. Use the ordinary code-review lane for an ordinary code step and escalate when current policy
or the step's blast surface requires it. Never encode reviewer counts in the plan. Runtime/full
review flags require a verified start command and reachable URL; unavailable runtime or auth access
must be surfaced and routed to a supported evidence path, not counted as passed.

A conditional step needs an executable predicate now. A placeholder may exist only in a `HELD`
draft and remains a blocker to plan-review/build readiness. `Type: operator` performs human work
and must not produce code-shaped artifacts; create an adjacent code prep step for those artifacts.
Conversely, a code step's acceptance must not hide an operator confirmation. Separate automated
and manual sections when both exist, and give manual checks copy-paste commands plus distinct
observations.

### Triggered obligations

- **Compatibility or migration:** name old/new shapes, rollout/backout, data ownership, and the
  compatibility verification. Do not assume destructive conversion authority.
- **Data pipeline or schema-bound producer/consumer chain:** place a short real-component smoke
  gate before long observation. Mocks alone do not prove the seam.
- **Autonomous, scheduled, background, or always-on behavior:** include deliberate realistic
  end-to-end observation long enough to expose time-dependent failure. A one-shot request/CLI does
  not trigger this; record that classification.
- **Deployment seam** (live workflow/role wiring, runtime-read model/config, deploy/install,
  scheduler/service, auth/secrets): include live-substrate observation using native evidence.
- **Wait or conditional work:** preserve its execution type and dependency; do not describe a wait
  or false predicate as a skipped quality gate.

These branches add applicable evidence; they do not remove normal tests or independent review.

## 5. Validate and hand off

Before saving as `REVIEW-READY`, verify the plan against current source:

- scope and every consequential choice are resolved;
- parent step IDs and dependencies do not collide;
- cited paths and exact commands exist, and shared consumers match the recorded search;
- each step has meaningful acceptance and valid fields;
- every triggered obligation above is represented;
- unrelated working-tree changes were not altered; and
- a fresh reader can locate each required fact without the planning conversation.

Do not run `plan-wrap` during authoring and do not certify independent gates. Report:

```text
Plan: <path>
SHA-256: <hash>
State: REVIEW-READY | HELD
Changed paths: <paths>
Unresolved: <none or blocking items>
Evidence: <key producing-source/search locators>
Next: /plan-review --autofix <plan-path>
```

The required downstream order is:
`/plan-review --autofix <plan-path>` -> `/plan-redline --plan <plan-path>` ->
`/plan-wrap --autofix <plan-path>` -> issue publication -> `/build-phase --plan <plan-path>`.
For a repository's first publication, issue publication is `/repo-init`; for an already initialized
repository, it is `/repo-sync --plan <plan-path>`. Proceed to each later command only after the
preceding gate's required findings or operator feedback are resolved. Do not recommend an
orchestration shortcut that omits `plan-redline`, and never run build-phase before issue publication
has populated the plan's Issue fields.

When the host already exposes native usage records, the receipt may report initial/peak input
context, net growth, cache read/write/uncached input, output, model/effort, source identities, and
observed reset/compaction boundaries. Cite the native source-record locators; state measurement
scope, deduplication rule, and cache TTL (`unknown` when unavailable); preserve reset/compaction
segments; and keep coordinator/worker usage separate. Disclose missing child usage and never add an
inclusive parent aggregate to its included children. Unsupported fields are `unknown` and never
block planning. Do not add a telemetry service, schema, dependency, synthetic record, or inferred
usage number.
