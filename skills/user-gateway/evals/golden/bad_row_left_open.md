<!-- BAD OUTPUT - DEFECT: the trim fragment's row is left with status OPEN — not terminal for the -->
<!-- gateway. The row is grammatically well-formed (open is a valid status word; neutral 'not yet -->
<!-- routed' disposition in intake-engine fixture B's style; '-' route cell per §2's own rule for -->
<!-- unrouted rows), the fragment did land in the ledger, the run completes without stalling (full -->
<!-- closing block), and assertions 1 and 6 carve open-status rows out to assertion 5 — so only the -->
<!-- terminal-status assertion trips. The emitted /goal is immediately unmet (the check scores 1), -->
<!-- which is exactly the defect's consequence. -->
<!-- Violates user-gateway SKILL.md Step 2 (no row stays open at close) / assertion 5 -->
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

Routes chosen by consulting the routing web (skill-pipeline.md § "The 8 rails", tiebreak applied — cited, not restated): (b) lands verify, not bug — distrust with no failing check in hand; (d) is an operator-only choice -> parked, never ground through. (c) remains unrouted in the ledger.

===== written file: .claude/task-state/intake-switchboard-leftovers.md =====
# Intake ledger — switchboard-leftovers

Seeded by /user-gateway 2026-07-13. Grammar + statuses per <repo>/_shared/intake-engine.md.

| id | fragment | route | status | disposition |
|----|----------|-------|--------|-------------|
| F1 | endpoint launcher 500s when the model list comes back empty | bug | routed | seed: `/user-debug --symptom 'endpoint launcher 500 on empty model list'`; repro: stop ollama, hit /launch |
| F2 | no evidence monitor auto-disable works since the Phase B merge | verify | routed | seed: `/user-shakedown 'switchboard monitor auto-disable'`; evidence check `curl -s 127.0.0.1:8080/status | jq .monitor` |
| F3 | switchboard plan doc carries never-do Phase C items | - | open | not yet routed |
| F4 | tinstar viewer: stay bundled in switchboard or split into its own repo? | decide | parked | operator-only: bundle vs split — question surfaced, awaiting operator |
| F5 | endpoint health dashboard (status, latency, per-model routing counts) | plan | routed | seed: /plan-feature 'switchboard endpoint health dashboard' — full seed paragraph in gateway output |
===== end written file =====

Per-row seeds (ready to paste):

F1 — bug:
/user-debug --symptom 'endpoint launcher returns 500 when the model list comes back empty (repro: stop ollama, hit /launch)'

F2 — verify (mode per the web's verify-rail detail: no UAT block exists yet and no operator attendance needed — autonomous closure fits):
/user-shakedown switchboard monitor auto-disable

F4 — decide (PARKED — operator-only; no seed):
Open question, stated and waiting: should the tinstar viewer stay bundled in switchboard, or split into its own repo? The ledger holds it as parked; nothing proceeds on it until you call it.

F5 — plan (paste as the /plan-feature argument):
/plan-feature switchboard endpoint health dashboard — a read-only page in switchboard's own UI (your answer to Q3) showing per-endpoint status, rolling latency, and per-model routing counts. Scope strictly as voiced; anything beyond these three panels is /plan-feature's conversation to have.

Closing block:
Ledger: <git-root>/.claude/task-state/intake-switchboard-leftovers.md (5 rows: 3 routed, 1 parked, 1 open)
/goal "intake ledger for switchboard-leftovers has zero open items"

QUICK COPY
/user-debug --symptom 'endpoint launcher returns 500 when the model list comes back empty (repro: stop ollama, hit /launch)'
/user-shakedown switchboard monitor auto-disable
/plan-feature switchboard endpoint health dashboard — read-only page in switchboard's own UI: per-endpoint status, rolling latency, per-model routing counts
