# Intent continuity

The coordinator preserves the user's observable workflow across planning, delegation,
implementation and handoff. Component acceptance is evidence, not a replacement goal.

## One private record per outcome

Keep: the user's intended outcome, actual entry point, observable journey, explicit
non-goals, current user capability, missing capability, next gap, and evidence pointers.
Retain the original intent; record a user-authorized scope change explicitly rather
than rewriting history. A fixture may prove a component but cannot replace the journey.
Records live outside source repositories. Never copy private records into issues,
commits, public reports, telemetry, or published examples.

## At intake and resume

Find the existing record before creating one. Inspect the actual shortcut, command,
page or API the user uses. Reuse available observations; do not repeatedly launch
side-effectful flows. If the entry point is unknown, record that uncertainty and
resolve it before claiming readiness. Preserve the intent record locator and a brief
capability summary in private session state. A worker receives the intent and the
specific missing step its assignment advances, with only the private context it needs.

## Before a next-step decision

Before recommending, selecting, or dispatching the next delivery task, read the
existing intent record. This includes ordinary conversational "what next?" advice,
not only skill invocations. Compare the proposed work with the user's outcome,
actual entry point and definition of done; identify the specific gap it closes.
Reconcile stale details with current user instructions and observed evidence.

Include one brief receipt in the recommendation or dispatch update:
"Intent checked: this closes ...; done means ...". Use it only after actually
reading the record; the receipt is not proof of completion or permission to act.
If the record is unavailable, disclose that, use saved intent and label the receipt
"Intent fallback". Do not create a tooling prerequisite. Keep private details out
of public artifacts; record the check in private session state instead when needed.

Private handoffs carry the exact intent-record path and the latest checked gap,
so the receiving session can read it before choosing or following Next Action.
This decision check adds no new approval gate, watcher or dispatch hook.

## At meaningful work boundaries

Record one checkpoint per completed work unit, not per tool call or repeated handoff:
"You can now ...; you still cannot ...; next gap ...". Separate implemented,
verified-in-isolation, available-at-entry-point, and user-accepted states. Attach
evidence to advancement; unknown is not progress. Tests, review rounds, documents,
and grants do not themselves count as user-visible capability changes.

After two consecutive units without observable advancement, REASSESS before adding
supporting work: explain the remaining dependency, inspect already-built work for
reuse/integration, and simplify or defer scope within existing authorization. If a
necessary safety repair must continue, record why and its bounded exit condition.
This is a coordinator decision, not a new approval gate or review campaign. Handoffs,
new agents and new sessions do not reset the count. Only evidenced capability
advancement resets it; user changes to the goal remain explicit history.

## At closeout

Check the journey through its actual entry point using existing evidence or a minimal
authorized observation. Do not infer readiness from a fixture, source review, or test
count. If execution is deferred or the user waived verification, say unverified;
do not invent evidence or run unwanted checks. User acceptance stays distinct.

## Skill Mesh integration

Planning skills establish the record; build coordinators map work to gaps and reassess;
task-handoff preserves it across transitions; session-wrap reports actual capability.
Use the local `drift_ranger.py` CLI when available. Its output records assertions and
signals reassessment; it does not certify delivery or authorize actions. If unavailable,
keep the same small record in existing private session state and continue. Do not
build or install supporting tooling as a prerequisite to the user's task.
