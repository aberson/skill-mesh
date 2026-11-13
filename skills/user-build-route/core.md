# user-build-route

Recommend how to approach a task: **Core pipeline**, **Bounded goal**, or
**Direct task**. Return advice and one ready-to-paste next prompt; never start
the recommended work, arm a goal, invoke another skill, or write project state.

## Ground the decision

Use the supplied task and conversation. When a project is available, read its
instructions, current plan and only the relevant source needed to establish the
route. Do not run builds, tests, experiments or broad discovery to make this choice.
Separate verified facts from assumptions. Ask only when an answer would change
the route; otherwise recommend one route with the relevant assumption stated.
If the task itself is missing, ask for the desired outcome.

Assess together: uncertainty about the outcome and implementation, scope and
dependencies, blast radius and reversibility, observable acceptance criteria,
and whether experiments must establish the approach. File count, estimated
duration and task size alone do not decide the route.

## Choose the next slice

| Route | Use when |
|---|---|
| **Direct task** | Outcome and approach are understood, the change is contained and reversible, risk is low, and a simple check establishes completion. |
| **Bounded goal** | A finite agent-completable investigation or experiment can answer a specific uncertainty, or a contained iterative task has a clear finish line without needing coordinated delivery. |
| **Core pipeline** | Delivery needs explicit design choices, dependency sequencing, shared-interface or data migration work, consequential risk controls, or coordinated acceptance and review. |

A tiny security or migration change can need the pipeline. A large isolated
experiment can fit a bounded goal. Unknown implementation alone does not make
every bug experimental: a known local regression can be direct; an unexplained
failure may need bounded diagnosis. For a risky fix, `user-debug` is the existing
diagnosis-to-`build-step` entry into the core build machinery.

For an ambiguous larger task, distinguish product choices from empirical questions.
Planning resolves scope, stakeholders and acceptance decisions; an experiment
resolves a testable feasibility or implementation question. Do not invent a
prototype when the missing input is what the operator wants. When both apply,
recommend only the next useful slice and name the later transition.
Preserve project-mandated gates on every route; goals are not a bypass.

## Check the route can run

Workload fit is not route compatibility. A prepared plan is not an eligible
execution route, and an eligible route is not a freshly qualified runtime. Read
the selected installed provider's adapter and core for the entry skill, and the
task's constraints; inspect only, never probe, dispatch an agent or spend
capacity to answer routing advice. Compare what the route does with what the
task allows: stash/worktree handling of pre-existing dirty paths, checkpoint
commits, the commit and push `task-handoff --next-task` performs, issue or other
publication, test and validation time against the budget, whether required
independent review is available on that host, and, when the route runs on this
machine, its current state: other test or build runs already going, and free
memory or disk against what the route's gates need. Reading the process list
and resource counters is inspection, not a probe.

- **Known conflict or observed failure** (for example build-phase checkpoint
  commits against a no-commit, preserved dirty checkout, or a recorded dispatch
  error in the destination session): give no unconditional continuation of that route.
  Unless the conflict is short-lived (below), name the conflict and
  recommend the smallest supported route that keeps the contract, or the
  constraint change the operator must authorize. Label any alternative whose
  required capabilities or independent review are unverified as conditional.
  A conflict that clears by itself with no change to the task or its
  constraints (for example another test run on the same machine that will end)
  is short-lived: keep the route, and make the next prompt start with a
  read-only check of that condition that stops and reports if it still holds.
  Do not shrink the route or ask for a constraint change because of it, and do
  not poll, wait in a loop or stop the other work.
- **Unknown runtime capability** (required by the adapter but not observable
  without a probe; this includes a fresh destination after another session's
  failure unless a session-independent conflict remains): recommend the route
  conditionally. The next prompt qualifies
  first through the entry skill's own gate, stops and reports on failure, and
  starts no unattended goal until that gate passes. If the entry skill has no
  separate gate and checks only at dispatch, qualification is an attended first
  run: the prompt first runs any project-mandated preflight the entry skill does
  not call, then starts the entry skill attended and stops and reports at the
  first failed check. Unknown is not a ban.
- **Capacity:** lifetime or thread capacity differs from active concurrency;
  finished agents may still count. Do not assume a release tool the host does
  not expose or prove capacity by consuming slots the work needs. The native
  gates revalidate at actual dispatch; this assessment certifies nothing.
  Do not suggest an undocumented thread-limit or setting change.
  Name a capacity-restoration control only when its supported mechanism is known;
  a fresh session is a conditional recovery attempt, not proof of more capacity.

Judge support per role: a documented reviewer-only CLI route may satisfy its
review contract without qualifying build orchestration. Do not infer either
whole-pipeline support or whole-pipeline failure from that one capability.
Do not narrow dispatch options the selected review adapter permits, or require
build-orchestration capabilities for a non-pipeline experiment.

Changing route never waives required independent review, acceptance or an
approval boundary. Do not add review to a trivial direct task that needs none.

## Prepare the handoff

**Core pipeline:** name the actual entry stage. Use `plan-init` for greenfield
planning or `plan-feature` for an existing project. An existing plan needing
preparation goes to `plan-expedite` (review, redline, wrap, issue sync, handoff).
A verified prepared plan with a compatible build route goes to `build-phase`
(qualification first when runtime capability is unknown); one already-planned
change can use `build-step`. Carry the known project, plan, outcome, constraints
and acceptance criteria into the prompt. Never invent plan paths, flags, issue IDs or readiness.
Do not paste an entire automatic chain across unresolved decision points.

**Bounded goal:** the pasted prompt must include:

- One question or objective and an observable agent-completable finish line.
- A concrete total wall-clock budget, including validation and reporting; use the
  operator's budget or label a proposed default (normally 45 minutes). Work
  already under a deadline keeps that deadline and its elapsed time.
- In-scope surfaces and explicit exclusions, appropriate isolation, and limits on
  external effects. For experiments, keep production integration out of scope.
- Evidence appropriate to the claim: reproduction and before/after checks for
  diagnosis; inspectable variants and screenshots for visual comparisons;
  repeatable commands, baseline and measurements for technical feasibility.
  Include limitations and failed attempts; do not substitute confidence for proof.
- Stop at the earliest of the deadline, completion, a boundary breach, a missing
  required capability/input, or repeated attempts yielding no new evidence.
  Report success, negative result, inconclusive result or blocker honestly; do not
  auto-extend the budget, relax criteria or retry indefinitely.
- Operator checkpoints before consequential choices or scope expansion, and at
  the final evidence handoff before accepting a visual direction or integration.
  End the automated slice at that handoff; operator approval is outside its
  completion condition, never a reason for an unattended goal to keep looping.

An experiment succeeds by answering its question, including evidence against an
approach. A promising prototype is not production acceptance. After the operator
accepts the evidence and direction, transition to `plan-feature` (or `plan-init`)
when delivery needs integration, hardening, dependencies or risk controls. Carry
the evidence, selected approach, rejected alternatives and remaining acceptance
criteria into that plan. If the remaining work meets the direct-task criteria,
recommend it directly; a negative or inconclusive result goes back to the operator
for a new scope decision, not an automatic build or another experiment.

**Direct task:** give a short prompt containing the concrete change, scope limits
and completion check. Do not introduce planning ceremonies or a persistent goal.

**Every continuation** keeps the scope, required independent review, acceptance,
and any existing absolute deadline or budget with its elapsed time. Never present
an unauthorized deadline as existing; no restart or resume resets one. Past the
deadline, give no command that restarts the build; name the new authorization
needed. A qualification-first prompt stops on failure; it never switches workflow
or substitutes self-review.
Carry the exact start and deadline; print elapsed/remaining estimates only when
verified, otherwise have the runner calculate them from its current clock.

A prompt a host may run as a persistent goal keeps its finish line pure (halting
is not success) and adds this failure rule: on a blocker, record ONE compact
blocker (stage, actual error, unfinished checks, completed work, original
deadline, cleanup, external change needed) in this session's existing private
state through a supported no-commit checkpoint such as `task-handoff --loop`, or
in chat when that is unavailable or the task forbids the write; never assume
another session's identity. Respect the host's own blocked-goal threshold (three
consecutive blocked goal turns where the host uses that rule): before it, only
cheap read-only state revalidation and genuinely independent allowed work, with
no repeated probes, issues, handoffs or status messages; at it, mark blocked once
only when the host's full conditions hold and no meaningful independent progress
remains.
Never mark an unfinished objective complete. A user resume restarts only the
host's audit, not the deadline.

## Output

Keep the recommendation short; spend detail on usable boundaries inside the copy
block. Keep Why and Next to one or two sentences each. Name the pipeline stage
and preserve its gates without copying its probe protocol or implementation
procedure into the prompt. Return exactly this shape, substituting task-specific text:

```text
## Decision: <Core pipeline | Bounded goal | Direct task>

Why: <one or two sentences identifying the decisive facts and any assumption>

Next: <one or two sentences stating the immediate step and any later transition>

Copy and paste:
```

One optional line may follow `Copy and paste:`: an execution-context line. When
the project or workspace instructions in force require a line above a next-step
block naming where and on what model it runs (for example a `Run in:` line),
print exactly one such line, in the format those instructions give, directly
above the fenced block. Fill it from verified facts about the destination and
use no window or model term the destination host lacks. Otherwise omit it, with
no placeholder or blank line in its place; put nothing else between
`Copy and paste:` and the block.

Follow with one fenced block containing the complete next prompt or command.
Use the current host's verified invocation syntax when known; otherwise use a
plain-language prompt naming the skill. A bounded-goal prompt is portable text,
not a claim that every host supports `/goal` or enforces a timer. Include a goal
command only when the destination host's support is verified and the route is
compatible and qualified; never claim a goal is armed. Require the next
runner to track elapsed time and stop; if it cannot, it must report that limitation
before starting. Leave no avoidable placeholders and do not execute the block.
