# skill-mesh lanes

A lane is a named, lasting slice of this project's work, worked by one window at a time and coordinated through Passing Notes (project id `skill-mesh`). No path is owned by two lanes. Approved by the operator on 2026-11-17 (`/user-pm --lanes` split).

| Lane | Purpose | Owns | Host | Hands off or needs |
|---|---|---|---|---|
| central | Coordinate, ship, relay the operator (stands in as `main`; renamed to `main` by lane-handoff later) | `docs/plans/`, `plan.md`, `README.md`, `CLAUDE.md`, `AGENTS.md`, `docs/lanes/`, releases, installs of the live profiles, merges and pushes, issue hygiene, worktree cleanup | claude | Ships every lane's commit-request |
| catalog-lifecycle | Phase CL to Step 117, then the `skill_catalog` no-write follow-up, V4-7 GPT removal and the Copilot deprecation | `tools/skill_catalog.py`, `tools/gen_manifest.py`, `tools/release_checks.py`, `tools/build-distributions.ps1`, `tools/install-skill-mesh.ps1`, `config/model-mapping.json`, `config/skill-manifest.json`, `skills/inventory.json`, `tests/package-integrity/expected_inventory.json`, `documentation/skill-catalog-lifecycle.md`, `tests/smoke/test_skill_crud_lifecycle.py`, lifecycle fixtures under `tests/fixtures/`, `documentation/phase-75-baseline.md`, `documentation/findings/skill-crud-uat.md` | claude | Hands the Step 118 UAT packet to the operator; hands the `change_pack` lifecycle row to catalog-gate |
| catalog-gate | Catalog gate CG (#244-#255, V4-8), then WF (Steps 126, 127, 120, 121) if the operator selects it | `tools/change_pack.py`, the per-file test class map, the gate prose in `skills/build-step/core.md` and `skills/build-phase/core.md` | claude | CG Step 1 needs a quiet machine; CG Step 9 (#253) edits the lifecycle guide, owned by catalog-lifecycle, so it waits for a handover; CG Step 7 (#251) is the operator's |
| user-skills | AP Step 130 (#216), then UPM Step 18 (#243) once Step 17's wait clears | `skills/user-afterparty/**`, `skills/user-pm/**` | claude | Agrees the `providers/gpt.md` edit order with catalog-lifecycle's V4-7; AP Step 131 is an operator check |

Coordinator: central
Shipper: central
Operator relay: central
Rules: [passing-notes lane rules](https://github.com/aberson/passing-notes/blob/HEAD/docs/lane-rules.md)

Operator-only work (never in a lane): CL Step 118 attended UAT (#176), the WF program selection (#196, #199), the CG Step 7 adoption decision (#251), AP Step 131 and LH Step 154 fresh-Codex observations, S8 acceptance, and the GitHub repository description.

Held (no lane): E1-E33, 47B, TM, LM and Step 109.

Shared resources, claimed through Heads Up and never owned by a lane: machine memory (each gate starts at 2 GB or more free), the installed Claude and Codex profiles, the release stage, and pushes to `origin/main`.
