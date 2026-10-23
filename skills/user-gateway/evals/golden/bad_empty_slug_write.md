# Preflight matrix with one defect

Probe A correctly returns `required_tool_missing: _shared/shakedown-engine.md` without writing or emitting seeds.

Probe B receives topic `!!!`, silently accepts an empty normalized slug, and writes:

`C:\repo\.claude\task-state\intake-.md`

Probe C correctly asks for clarification because no exact ledger exists and two near-match ledgers are present.

Single intended defect: Probe B writes a ledger for an empty slug instead of asking for a non-empty topic, so assertion 11 fails. No seeds are emitted and no other preflight behavior differs.
