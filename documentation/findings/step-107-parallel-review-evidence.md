# Step 107 — parallel review evidence (2026-08-26)

A second `/build-phase --resume 107` session ran concurrently with the one that produced
`d4c88ee`. Both sessions authored Step 107 independently. `d4c88ee` won the race and is on
`main`; this document records what the losing session's review round measured, because that
evidence does not exist anywhere in `d4c88ee` and four of its findings are **live on `main`**.

Nothing here is a gate. It is an evidence record for a follow-up step.

## 1. What the parallel session produced

| Artifact | Location |
|---|---|
| Alternate Step 107 implementation (254-line vendored doc) | branch `build-step-1787765607` @ `8af9e36`, unmerged |
| Measurement adjudication (2 protocols + controls + 3 judges) | `.build-step/measurement-adjudication.md` on that branch's worktree |
| Per-lens findings, two rounds | `.build-step/review-*.json`, `.build-step/review2-*.json` |
| Universal-claim audit (10 claims falsified individually) | `.build-step/iteration-3-brief.md` |

Review effort behind it: two developer iterations, ten reviewer passes (five lenses × two
rounds), and two adversarial verification workflows. Round 1 gated 1 high / 12 medium / 30 low;
round 2 gated 2 high / 19 medium / 22 low.

## 2. Live on `main` at `d4c88ee`

Each row was confirmed by direct enumeration against the landed files, not inferred from the
parallel branch.

| # | Location on `main` | Defect | Refuted by |
|---|---|---|---|
| 1 | `architecture.md:627`, `:632` | "the write surface is the core, never the adapter, for every portable skill"; adapters "need no instruction-file prose of their own" | `skills/plan-init/providers/codex.md:11` — a **portable** skill's adapter carrying exactly that prose, mandated by this plan's Step 101 |
| 2 | `host-discovery.md:257` | pre-existing row answers "Are workspace instructions loaded?" with "the host's instruction-file convention" | this repository — it follows the convention exactly and Codex receives none of the content |
| 3 | `architecture.md:538`, `:603`; `host-discovery.md:189`, `:274` | four unqualified "read-only" descriptions of the reproduction | `codex-instruction-delivery.md:72` — the same change states in bold that it is "not side-effect-free, and should not be described that way" |
| 4 | `codex-instruction-delivery.md:73-74` | "Measured over one run … three files under the Codex home re-stamped" — a per-invocation count from one uncontrolled sample | control intervals (§3) reproduced the same signature with the command never run |

Row 1 is the sharpest: `test_instruction_contract_single_owner.py` counts that adapter in
`CITER_FLOOR = 4`, so a maintainer who follows the prose and deletes it turns the suite red.

Rows 1–3 were each found independently by two of the five lenses.

## 3. The measurement finding (§3 of the adjudication)

The claim that `codex debug prompt-input` "rewrites two files under the Codex cache on every
invocation, mtimes advancing and sizes unchanged" was carried into the parallel session's
developer brief from prior task state, where it was recorded as verified. Two independently
designed re-measurements — one hashing every file, one recording size and mtime — each
bracketed by **zero-invocation control intervals**, refuted it:

- No run of either protocol produced exactly two attributable writes.
- Attributable changes ranged from none to three per invocation, and the two protocols
  disagreed about the same command.
- **A control interval with the command never run reproduced the exact "two files, mtimes
  advanced, sizes unchanged" signature.** The original measurement was observing background
  churn in the Codex home, not the command.

A competing counter-measurement (62 / 0 / 7 files across three runs) was rejected on the same
grounds — equally uncontrolled.

What survives: the command writes nothing in the project directory, on any run of either
protocol; `config.toml`, `auth.json` and every session, skill and plugin file were unchanged in
every manifest, so a `-c` override leaves nothing on disk. **How many files it touches under the
Codex home is not stable between runs, so no per-invocation count should be published.**

Method note worth keeping: the Codex home churns with no invocation at all, so it cannot be
fingerprinted while any codex process is live.

## 4. The universal-claim audit

Every claim in the parallel branch's prose that quantified over a set ("every", "only",
"never", "no …") was enumerated, and one agent per claim ran the enumeration that would falsify
it. Of 10 claims: **3 TRUE, 4 FALSE, 3 NEEDS-SCOPING.**

The method is the transferable part. Three false universal claims had already reached review,
each refuted by a *single* live counter-example nobody had looked for — and in each case the
repo contained exactly one counter-example, which is why reading alone never caught them. A
universal claim is only cleared by enumerating the set it quantifies over.

Those verdicts were computed against the parallel branch's wording; the line numbers do not map
onto `d4c88ee`. **The audit should be re-run against the landed prose** rather than
transcribed — §2 above lists only what was re-confirmed on `main` directly.

## 5. Separate defect found in the contract owner

`skills/plan-init/core.md:452-455` states that a provider adapter is "forbidden the
`<repo>/_shared/<leaf>` spelling cores must use, so an adapter could not cite it in any legal
spelling."

The premise is true; the conclusion is false. `skills/judge-motion/providers/claude.md:10` is
provider-native (`core: null` in the manifest) and cites `_shared/judge-core.md` today via the
relative spelling. `tests/distributions/test_distributions.py:769-777` forbids only the
repo-rooted spelling, and its own assertion message calls that an extendable scope guard.

This is the **owner** of the instruction-file contract, so it is out of scope for any
documentation step and needs its own change. A sweep found exactly two instances of the shape
and no third, so `/build-step`'s stop-and-audit threshold was not reached.
