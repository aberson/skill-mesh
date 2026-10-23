user-gateway: topic `Switchboard leftovers!` -> slug `switchboard-leftovers`; ledger: loaded intake-switchboard-leftovers.md

Listening pass:
- the empty-model 500 is the same reported bug (`already F1`)
- the operator answered the tinstar decision: keep it bundled (`F2 parked -> done`)
- the monitor concern belongs in the auto-disable shakedown (`F3 parked -> routed`)
- the overnight acceptance goal needs drafting (new F4)

Questions: none — the new vent settles the loaded rows and the new fragment is clear.

Routes were chosen by consulting `_shared/skill-pipeline.md` § "The 8 rails"; its table is not reproduced here.

===== written file: .claude/task-state/intake-switchboard-leftovers.md =====
# Intake ledger — switchboard-leftovers

| id | fragment | route | status | disposition |
|----|----------|-------|--------|-------------|
| F1 | endpoint launcher 500s when the model list is empty | bug | routed | seed: `/user-debug --symptom 'endpoint launcher 500 on empty model list'` |
| F2 | should tinstar stay bundled or split into its own repo? | decide | done | operator decision: keep tinstar bundled |
| F3 | no evidence monitor auto-disable works | verify | routed | seed: `/user-shakedown switchboard monitor auto-disable` |
| F4 | overnight acceptance goal keeps coming out mushy | draft | routed | seed: `/user-draft overnight acceptance goal for switchboard` |
===== end written file =====

F1 — already routed in an earlier pass; its seed should not be replayed.

F2 — decide resolved by the operator, so it is done and has no seed.

F3 — routed in this pass:
`/user-shakedown switchboard monitor auto-disable`

F4 — routed in this pass:
`/user-draft overnight acceptance goal for switchboard — rough thought: "keep going until acceptance is all good"`

Closing block:
Ledger: C:\repo\.claude\task-state\intake-switchboard-leftovers.md (4 rows: 3 routed, 1 done — zero open)
`/goal "intake ledger for switchboard-leftovers has zero open items"`

QUICK COPY
/user-debug --symptom 'endpoint launcher 500 on empty model list'
/user-shakedown switchboard monitor auto-disable
/user-draft overnight acceptance goal for switchboard — rough thought: "keep going until acceptance is all good"

Single intended defect: QUICK COPY replays already-routed F1's old seed, so assertion 9 fails.
