# Omnigent revisit seed — deferred

**Status:** DEFERRED RESEARCH SEED — NOT AN INSTALL, INTEGRATION, MIGRATION, OR REPLACEMENT PLAN

**Requested by:** Abraham Robison

**Prepared:** 2026-08-13

**Independent experiment:** the workspace sibling `../../omnigent-lab/plan.md` remains separate from Skill Mesh and is not a dependency of this seed.

## Why this is deferred

Omnigent is genuinely relevant. It presents one interface over Claude Code, Codex, Pi, and other harnesses; its Polly agent delegates work in separate worktrees and routes cross-vendor review. Those capabilities overlap with Skill Mesh's orchestration and model-diversity goals.

It is not a sound replacement decision today:

- Omnigent's own FAQ labels it alpha and not production-ready.
- Its documented Windows mode is degraded: SDK harnesses and the web UI work, but native Claude/Codex terminal wrappers and the stronger Linux/macOS filesystem/network sandboxing are unavailable without WSL.
- Abraham's normal target experience is native Claude Code and Codex on Windows, not a new control-plane dependency.
- Replacing the current system before its product boundary and evidence contracts are stabilized would exchange a known scope problem for an external moving platform.
- The native Claude Code and Codex plugin/package experiment is cheaper and closer to the immediate distribution problem.

## Why Skill Mesh remains better for Abraham's current use

This is a fit judgment, not a claim that Skill Mesh is generally superior.

1. It already contains Abraham's mature planning, review, build, and session workflows rather than generic coding-agent roles.
2. It can run directly in the two desired hosts, preserving native interaction instead of requiring a meta-harness for routine work.
3. It can make workflow-specific contracts, acceptance, deferrals, requested/resolved model identity, and Dev Observatory evidence first-class.
4. It carries the actual Windows migration and consumer-customization history that a generic harness cannot infer.
5. Its intended narrow charter—portable workflow contracts, model-role policy, conformance, behavioral evaluation, and receipts—can complement host runtimes without replacing them.
6. It can retain deterministic tests as the primary gate and use cross-family review selectively, rather than treating multi-agent count as the product.

## What Omnigent may do better

- General multi-harness session hosting and switching.
- Parallel worktree delegation with a supervisor that does not merge.
- Cross-vendor reviewer selection as a built-in orchestration pattern.
- Shared web/mobile collaboration and persistent session infrastructure.
- Gateway/local-model access through a common execution layer.
- Central policy/sandbox controls, particularly on supported Linux/macOS environments.

Those are useful ideas to study. Skill Mesh should not rebuild them unless Abraham has an observed need that native hosts and bounded skills cannot satisfy.

## Revisit triggers

Run a fresh investigation only if at least one of these becomes true:

1. Omnigent no longer describes itself as alpha and has a documented compatibility/release policy.
2. Windows reaches parity for the native Claude/Codex experience and required sandbox behavior, or Abraham explicitly chooses WSL/Linux as the operating environment.
3. Claude/Codex native plugins fail the Skill Mesh lifecycle experiment for reasons Omnigent demonstrably solves.
4. Skill Mesh still requires substantial custom orchestration after its product boundary is narrowed.
5. The independent `omnigent-lab` experiment produces reproducible evidence that Omnigent can preserve Skill Mesh workflow contracts and exact run receipts.
6. Abraham wants mobile/shared-session operation enough to accept the added server/control-plane dependency.

## Fresh investigation prompt

Use the following in a new read-only research window. Do not install or modify either project during the investigation.

> Compare the current released Omnigent with the current Skill Mesh product charter and the evidence in `omnigent-lab/plan.md`. Verify all claims against current first-party documentation and source. Abraham Robison's routine target is native Claude Code and Codex on Windows; quality matters more than timeline. Determine whether Omnigent should remain an independent experiment, become an optional execution backend, replace only duplicated orchestration, or replace Skill Mesh entirely.
>
> Evaluate, with reproducible evidence:
>
> 1. Windows-native Claude Code and Codex parity, including install/update/uninstall, terminal behavior, sandbox/permission controls, filesystem isolation, credentials, and failure recovery.
> 2. Whether Omnigent can invoke existing Skill Mesh workflows without rewriting their contracts or forcing a server/web UI into routine use.
> 3. Whether it records requested and resolved model identity, provider/transport, fallback reason, source commit, permissions, artifact hashes, reviewer identity, verdicts, and evidence locators in an exportable versioned receipt.
> 4. Whether its cross-vendor review measurably improves seeded-defect detection versus Skill Mesh's qualified Claude/Codex reviewer lane, at comparable cost and latency.
> 5. Whether it preserves deterministic tests as the primary gate, immutable candidate review, bounded correction rounds, explicit scope rebaseline, and human merge authority.
> 6. The operational burden: daemon/server lifecycle, database/state, updates, credential homes, WSL or containers, backups, privacy, telemetry, debugging, and migration/rollback.
> 7. Which capabilities would become redundant and could be deleted from Skill Mesh, versus which Abraham-specific workflow contracts must remain.
>
> Run the smallest representative experiment necessary. Compare four outcomes: keep separate, optional backend, replace a bounded subsystem, or full replacement. Give an honest recommendation, migration cost, rollback plan, and explicit no-go findings. Do not recommend adoption merely because both projects support multiple agents.

## Sources to recheck at revisit time

- [Omnigent FAQ](https://omnigent.ai/faq) — current maturity statement.
- [Omnigent Harnesses](https://omnigent.ai/docs/build/harnesses) — supported runtimes and direct/native modes.
- [Omnigent Polly](https://omnigent.ai/docs/use/builtin-agents/polly) — worktree delegation and cross-vendor review behavior.
- [Omnigent GitHub repository](https://github.com/omnigent-ai/omnigent) — installation, current Windows limitations, source, and release activity.

The claims above are a 2026-08-13 snapshot. Treat them as stale whenever this seed is reopened.
