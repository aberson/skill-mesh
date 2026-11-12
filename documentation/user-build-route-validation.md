# user-build-route validation

## Scope and authority

On 2026-10-31 the operator explicitly authorized a scoped catalog exception,
including the inventory-generation changes needed to register and validate this
skill. This does not mark Phase CL Step 111 complete or authorize installation.
The source checkout was on main, synchronized with origin/main after fetch; the
workspace freeze file was absent. The unrelated untracked `dev/` directory was
reported and preserved under the lifecycle's unrelated-dirty-path rule.

Normalized request:

```json
{
  "operation": "CREATE",
  "skill_name": "user-build-route",
  "new_name": null,
  "base_ref": "6ad91748a5d886c2d6631131bb16d68efd82985d",
  "description": "Recommend pipeline, bounded goal, or direct task with rationale and a pasteable prompt; advice only.",
  "capabilities": ["filesystem"],
  "resource_paths": [],
  "reference_dispositions": []
}
```

The new identity was absent. Target-path hashes were captured before editing in
the authoring session. Authoring covers the new core and three adapters, manifest
constants, the model mapping, the existing pure inventory builder's integration,
affected catalog count/regeneration checks and catalog documentation. No package
resources are added. The three inventories and host profiles are generated.

Inspected source contracts: `plan-init`, `plan-feature`, `plan-expedite`,
`build-phase`, `build-step`, `user-debug`, `user-draft`, and `user-pm`, plus the
catalog lifecycle, manifest generator and provider wrappers. Source inspection
was for authoring, not execution of an uninstalled skill.

## Behavioral walkthrough

These are manual authoring checks against the core, not independent model trials
or evidence that an installed host executed the skill. Each case checks route,
decisive rationale, immediate handoff and non-execution.

| Input | Decision and rationale | Ready-to-paste next prompt |
|---|---|---|
| A settings label misspells a word; exact location known, no behavior changes. | Direct task: known approach, low risk, simple acceptance. | Correct the settings label spelling at the identified location. Keep behavior and layout unchanged; verify the rendered label and report the diff. |
| Compare two dashboard density treatments before choosing a design. | Bounded goal: the implementation direction depends on visible evidence and operator preference. | See the full bounded prompt below. |
| Add approved role-based export across API and UI; acceptance includes permissions and audit records. No prepared plan exists. | Core pipeline, plan-feature: shared boundaries and coordinated acceptance warrant design and gated delivery. | Use plan-feature to plan the approved role-based export in this project. Trace API/UI permissions and audit behavior, preserve the agreed acceptance criteria, and identify integration checks. Produce the plan for preparation; do not start implementation. |
| Modernize our entire reporting platform; stakeholders and desired outcomes are unclear. | Core pipeline, planning first: this is product ambiguity, not yet a testable implementation question. | Use plan-feature to establish the reporting modernization scope from current entry points and stakeholder needs. Identify unresolved outcome and acceptance decisions before defining executable build steps. Do not start implementation. |
| One-line authorization bypass fix affecting every tenant. | Core pipeline despite tiny size: high blast radius needs verification and review. | Use user-debug to investigate the reported tenant authorization bypass, establish a reproduction and required regression coverage, and route the fix through the project's required build/review gates. |
| Large isolated renderer spike with a fixed benchmark and no production changes. | Bounded goal despite size: one empirical feasibility question and a contained evidence-producing slice. | Run a 45-minute feasibility investigation in an isolated scratch area. Compare the current renderer with one candidate on the supplied benchmark; preserve commands, baseline, measurements and limitations. Stop on completion, deadline, unavailable inputs, boundary breach or repeated attempts with no new evidence. Do not integrate, change public interfaces or contact external services. Report feasible, infeasible, inconclusive or blocked with evidence for operator review; production adoption requires a separate plan. |

The ambiguous-platform case needs no question merely to choose planning. If the
same request could mean either a disposable feasibility spike or a production
replacement, ask which deliverable is intended because that answer changes the
route. Do not ask questions about routine details that leave the route unchanged.

## Visual experiment sample output

### Decision: Bounded goal

Why: Choosing a density treatment requires comparison evidence and operator
judgment. The experiment can stay isolated from production integration.

Next: Produce two inspectable variants and a comparison. Stop for operator
selection; if the chosen direction needs shared component changes or broader
integration, carry the evidence into plan-feature.

Copy and paste:

```text
Run a bounded dashboard-density experiment with a proposed default total budget
of 45 minutes, including evidence capture and reporting. Track elapsed time; if
you cannot track and honor the budget, report that limitation before starting.

Question: which of two density treatments better preserves readable labels and
usable controls for the current dashboard? Use the existing dashboard and sample
data in an isolated branch or scratch copy. Limit changes to spacing, typography
and table density. Do not alter APIs, persistence, authentication, production
configuration or deployment. Do not add paid services or dependencies.

Capture the unchanged baseline and both variants at matching desktop and mobile
viewports. Provide inspectable artifacts, screenshots, reproduction instructions,
checks for clipped labels and inaccessible controls, tradeoffs, failed attempts
and limitations. Completion means that comparison is available for operator review;
it does not mean the operator has approved a design or production is ready.

Stop at the earliest of completion, 45 minutes, a scope boundary, unavailable
required inputs/tools, or repeated attempts producing no new evidence. Reserve
time to report the partial result. Label the outcome success, negative,
inconclusive or blocked; do not extend the budget or relax the criteria.

Stop for operator input before a consequential design choice or scope expansion.
The final checkpoint is the evidence handoff for operator selection; do not keep
working while waiting. After selection, recommend plan-feature if integration or
hardening needs coordinated work; otherwise recommend a bounded direct edit.
Do not begin either follow-on route automatically.
```

## Verification

- `python tools/gen_manifest.py`: generated all three inventories; catalog is
  58 total, 55 portable, with all 55 portable skills carrying Codex adapters.
- All three provider builds passed, including a rebuild after the description
  trim. Each generated core preserves the canonical core in full.
- Initial `python -m pytest tests/package-integrity -q`: **2 failed, 693 passed
  in 325.41s**. Failures were the discovery-budget headroom guard and exact cohort
  roster. The candidate was preserved and the authoring workflow repaired only
  the new description and roster membership; budget limits were not weakened.
- Post-repair focused run of `test_codex_budgets.py`,
  `test_codex_capability_claims_honesty.py`, `test_manifest_contract.py` and
  `test_skill_tree.py`: **117 passed in 18.41s**, including both prior failures.
- Final lifecycle document checks: **44 passed in 0.82s**.
- Distribution checks for manifest descriptions, complete emitted Codex roster,
  and byte-identical reruns: **3 passed, 173 deselected in 29.66s**.
- Codex skill-creator quick validation passed for the generated Codex and GPT
  packages. Applying that host-specific validator to Claude rejected its valid
  `user-invocable` field; the repository's provider checks and successful Claude
  build are the appropriate evidence for that profile.
- `git diff --check` passed. The six routing cases above were manually checked;
  no independent agent or installed-host behavioral trial was performed.

The broad run was not repeated after the repairs; the affected checks were rerun
as listed. The full repository-root suite was not run. This maintenance change
advances no numbered plan step and claims no full repository-root DONE gate.
No commit, push, live installation or recommended task execution occurred.
