# Skill Mesh project memory

## Durable status

- Phase IS C2V is sealed at `09e7f4d`; C2A is the next active completion stage.
- Phase CL — Skill catalog lifecycle safety is planned under umbrella #167 with step issues #168–#176. Its authority is `documentation/skill-catalog-lifecycle-plan.md`.
- Phase CL implementation is parked until Phase IS C5 (#143/#153) and Phase CP M3 plus closeout (#132) are complete.
- Phase CL Steps 110–117 are the automated build/certification span. Step 118 (#176) is attended operator acceptance and is never part of unattended `/build-phase` execution.

## Lifecycle safety decisions

- A routine portable skill means one neutral core plus Claude, GPT, and Codex adapters in the same change.
- Catalog CRUD fails closed for provider-native mutations, unsupported package-resource topology, dirty target paths, incomplete provider sets, and unsafe/non-Skill-Mesh sources.
- Mutable GitHub issue text is untrusted evidence; only landed repository guidance or explicit operator ratification can change an adapter contract.
- The local roadmap mirror is `.claude/artifacts/phase-is-whats-next.html`; it is intentionally gitignored.
