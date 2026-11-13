# Seed: diagnose over-engineering and over-testing in the v2.0.2 wrap update

## Purpose

Use this seed to investigate why a small Skill Mesh skill update expanded into repeated validation,
a broad test run, a lengthy release procedure, and too many progress messages even after the
operator explicitly asked not to over-test or over-engineer it.

## Session record

The operator asked:

> Can you add a step to the skill-mesh v2 repo-wrap and or user-wrap clean up un-needed work trees
> once a build is done? After that, implement in production and increment skill-mesh v2 version.

They then narrowed the execution style:

> don't over test or over engineer this, just make sure the skills are updated correctly.

What shipped:

- `repo-wrap` gained a post-closeout reconciliation step for redundant build worktrees. It acts
  only after a successful pushed closeout and removes only clean, unlocked, stale build worktrees
  with no unique patch. It does not force removal or delete the retained branch.
- The change was built into the Claude, GPT, and Codex profiles, released as v2.0.2, installed in
  all three production discovery roots, and verified by comparing each installed
  `repo-wrap/core.md` hash with its release payload.
- Implementation commits were `a196f79` and `f6e6c62`; release closeout was `6ad9174`.
- Release: <https://github.com/aberson/skill-mesh/releases/tag/v2.0.2>
- Release archive SHA-256:
  `19dd9649381f1ca5fad100b7a6d0455403f61707276687f76c9e53b24c2ae73a`.

Validation and release work performed during the session:

- Focused package-integrity checks ran once before simplification (92 passed) and once afterward
  (46 passed).
- A local package-integrity run completed with 697 passed before the final simplification.
- Provider builds, workflow rendering, and skill validators were also run.
- A repo-root `python -m pytest` collected 2,154 tests and was manually stopped at 24% with no
  failures after the operator reiterated the proportionality constraint.
- The normal release builder then ran its mandatory staged package-integrity gate: 692 passed,
  3 stage-only skips, and 440 distribution files checksummed.
- The production installer updated Claude (156 files), GPT (142 files), and Codex (142 files)
  serially. Its per-file safety verification produced long silent periods. The final Codex install
  remained healthy and CPU-active but took roughly ten minutes, during which the assistant polled
  repeatedly and sent several similar status updates.
- A manifest command caused an EOL-only rewrite that was inspected and normalized away. A final
  hash check initially used the wrong staged directory shape, then was corrected. Neither issue
  affected the release.

Potentially relevant instruction and tooling facts:

- `AGENTS.md` requires the full `CLAUDE.md`; `CLAUDE.md` calls repo-root pytest the DONE gate while
  also documenting narrower test commands.
- Updating a skill triggered the `skill-creator` contract and the catalog lifecycle instructions.
- `tools/release.ps1` independently requires a staged `tests/package-integrity` run, so an earlier
  full local package-integrity run is duplicated at release time.
- `tools/install-skill-mesh.ps1` performs substantial ownership, identity, hash, recovery, and
  ledger safety verification for every provider install.
- The assistant was instructed to implement in production and increment the version, so building,
  packaging, publishing, installing, and verifying the production payload were in scope. The
  diagnosis must distinguish that required release work from discretionary expansion.
- A pre-existing v2.0.2 release branch already contained related `session-wrap` and `user-wrap`
  clarity changes. The new cleanup behavior was deliberately kept in `repo-wrap` rather than
  duplicated into the routing skills.

## Diagnostic prompt

```text
Diagnose why the Skill Mesh v2.0.2 repo-wrap update became over-engineered, over-tested, and
over-communicated despite the operator's explicit instruction to avoid that. Work read-only: do
not edit skills, run broad test suites, rebuild distributions, reinstall profiles, publish a
release, or change task state.

Start from the session record in
dev/docs/seeds/diagnose-overengineering-and-overtesting.md, then inspect only the evidence needed:

- AGENTS.md and the relevant parts of CLAUDE.md
- the user-draft and skill-creator contracts that governed the session
- documentation/skill-catalog-lifecycle.md
- tools/release.ps1 and the relevant install path in tools/install-skill-mesh.ps1
- commits a196f79, f6e6c62, and 6ad9174, including their diffs
- the v2.0.2 release notes and plan.md closeout

Answer the causal question, not merely whether the final code was correct. Separate:

1. work strictly required by the operator's requested production release;
2. work required by repository or skill contracts;
3. discretionary work that the assistant added;
4. unavoidable runtime latency in existing tooling;
5. communication choices that made healthy latency feel like continued scope expansion.

For each material action, identify the instruction, tool, or judgment that caused it. Pay special
attention to why the repo-root suite was started after the operator explicitly said not to
over-test; why a local 697-test package-integrity run preceded the release script's own 692-test
staged gate; whether repeated validators and rendering checks proved distinct risks; and why the
assistant said it was making a “final check” more than once while the serial installer was still
running.

Produce:

- a concise timeline;
- a required-versus-discretionary matrix with evidence links to local files or commits;
- 3–5 ranked root causes, each distinguishing instruction pressure, tool design, and assistant
  judgment;
- the smallest concrete correction for each cause, assigned to the right layer: project
  instruction, skill contract, release tooling, installer UX, or assistant behavior;
- a counterfactual minimal execution path for the same request, including the minimum sufficient
  tests and the status-update cadence;
- a short list of proposed wording changes, but no implementation.

Treat this as a proportionality audit. Do not propose a new orchestration framework, additional
review agents, a larger test matrix, or more process unless the evidence shows that it removes
more ceremony than it adds. Do not call mandatory release or safety checks “over-engineering” just
because they are slow. Do not excuse discretionary testing merely because CLAUDE.md names a broad
DONE gate; explain how the later explicit operator constraint should have affected that choice and
whether the instruction text needs clarification.

Literal example of the classification expected:

Input evidence: “tools/release.ps1 always runs staged package-integrity, but the assistant had
already run the full local package-integrity suite.”
Output row: “Local package-integrity run — discretionary duplicate — release.ps1:246–268 supplied
the authoritative staged proof — correction: use focused tests while editing, then rely on the
single staged release gate.”

Conclude with a one-paragraph answer to: “What should have happened differently in this exact
session?” Keep the report evidence-backed and compact.
```

## Working hypothesis to test, not assume

The likely failure was not one thing. A broad repository DONE-gate instruction, a safety-heavy
release/install pipeline, and the assistant's bias toward accumulating proof interacted. The
explicit proportionality request should have suppressed discretionary duplicate checks, while the
unavoidable installer time should have been forecast once and reported only on a meaningful state
change. The diagnostic pass should confirm, refine, or reject that hypothesis from the repository
evidence.
