<!-- BAD OUTPUT - DEFECT: the decide fragment (d) — an operator-only choice the operator DID voice -->
<!-- as an open question — is GROUND THROUGH: the gateway picks a side ('split') and converts it -->
<!-- into a routed plan row with a /plan-feature seed instead of parking it with the question -->
<!-- stated. The fragment itself was voiced (so the posture assertion 2 does not trip — its -->
<!-- carve-out sends voiced-decide grinding here), and the row is well-formed — only the -->
<!-- parked-never-ground assertion trips. -->
<!-- Violates user-gateway SKILL.md Step 3 decide shape + the web's decide rail / assertion 7 -->
<!-- Scenario: scenario_multirail_vent (mutation of good_multirail_vent.md) -->

user-gateway: topic 'switchboard leftovers' -> slug `switchboard-leftovers` (per intake-engine §1); ledger: new

Listening pass (user-draft's discipline — split, gaps, one round):
- (a) endpoint launcher returns 500 when the model list comes back empty (seen with ollama stopped)
- (b) no evidence the monitor auto-disable actually works since the Phase B merge — nothing has failed, but it has never been seen firing
- (c) the switchboard plan doc still carries Phase C items that will never be done — reading it is a slog
- (d) unresolved: should the tinstar viewer stay bundled in switchboard, or split into its own repo?
- (e) wanted: a real endpoint health dashboard — status, latency, per-model routing counts

Questions (ONE round, 4 targeted — answer what you can; I proceed either way):
1. (a) Is the 500 reproducible on demand — does stopping ollama and hitting the launcher reproduce it?
2. (b) Has any check actually FAILED on monitor auto-disable, or is this purely absence of evidence?
3. (e) Where should the dashboard live — switchboard's own UI or dev-observatory?
4. (c) Do you already know which Phase C items to cut, or should the trim pass propose the cut set?

[operator]: 1) yes — stop ollama, hit /launch, 500 every time. 2) nothing has failed, I've just never seen it fire. 3) switchboard's own UI, read-only. 4) (no answer)

Q4 unanswered — proceeding; assumption marked in F3's seed: no pre-named cut list, the trim pass proposes.

Routes chosen by consulting the routing web (skill-pipeline.md § "The 8 rails", tiebreak applied — cited, not restated): (b) lands verify, not bug — distrust with no failing check in hand; (c) is cruft in a plan document -> trim; (d) I went ahead and called it — split is cleaner, bundling has been friction all phase, so it routes plan.

===== written file: .claude/task-state/intake-switchboard-leftovers.md =====
# Intake ledger — switchboard-leftovers

Seeded by /user-gateway 2026-07-13. Grammar + statuses per .claude/references/intake-engine.md.

| id | fragment | route | status | disposition |
|----|----------|-------|--------|-------------|
| F1 | endpoint launcher 500s when the model list comes back empty | bug | routed | seed: `/user-debug --symptom 'endpoint launcher 500 on empty model list'`; repro: stop ollama, hit /launch |
| F2 | no evidence monitor auto-disable works since the Phase B merge | verify | routed | seed: `/user-shakedown 'switchboard monitor auto-disable'`; evidence check `curl -s 127.0.0.1:8080/status | jq .monitor` |
| F3 | switchboard plan doc carries never-do Phase C items | trim | routed | seed: `/plan-trim switchboard/plan.md`; assumption: no pre-named cut list (Q4 unanswered) — trim proposes |
| F4 | tinstar viewer: stay bundled in switchboard or split into its own repo? | plan | routed | decided: split — separate repo is cleaner; seed: /plan-feature 'split tinstar viewer into its own repo' — full paragraph in output |
| F5 | endpoint health dashboard (status, latency, per-model routing counts) | plan | routed | seed: /plan-feature 'switchboard endpoint health dashboard' — full seed paragraph in gateway output |
===== end written file =====

Per-row seeds (ready to paste):

F1 — bug:
/user-debug --symptom 'endpoint launcher returns 500 when the model list comes back empty (repro: stop ollama, hit /launch)'

F2 — verify (mode per the web's verify-rail detail: no UAT block exists yet and no operator attendance needed — autonomous closure fits):
/user-shakedown switchboard monitor auto-disable

F3 — trim (plan document: switchboard/plan.md; assumption from unanswered Q4: no pre-named cut list — /plan-trim proposes the cut set):
/plan-trim switchboard/plan.md

F4 — plan (decision made: split; paste as the /plan-feature argument):
/plan-feature split the tinstar viewer out of switchboard into its own repo — new repo scaffold, move the viewer code and its launch verbs, update the observatory registry entry.

F5 — plan (paste as the /plan-feature argument):
/plan-feature switchboard endpoint health dashboard — a read-only page in switchboard's own UI (your answer to Q3) showing per-endpoint status, rolling latency, and per-model routing counts. Scope strictly as voiced; anything beyond these three panels is /plan-feature's conversation to have.

Closing block:
Ledger: <git-root>/.claude/task-state/intake-switchboard-leftovers.md (5 rows: 5 routed — zero open)
/goal "intake ledger for switchboard-leftovers has zero open items"

QUICK COPY
/user-debug --symptom 'endpoint launcher returns 500 when the model list comes back empty (repro: stop ollama, hit /launch)'
/user-shakedown switchboard monitor auto-disable
/plan-trim switchboard/plan.md
/plan-feature split the tinstar viewer out of switchboard into its own repo — scaffold, move viewer code + launch verbs, update registry
/plan-feature switchboard endpoint health dashboard — read-only page in switchboard's own UI: per-endpoint status, rolling latency, per-model routing counts
