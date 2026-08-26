# Phase IS handoff — Claude Code → Codex CLI (2026-08-26)

**Read this whole file before acting.** It is self-contained: it assumes you have no memory of the
session that produced it.

## 0. What you may NOT do on this host

`/build-step` is a recorded `blocker`/`wontfix` on Codex — it has no isolated fresh-context
primitive — so **`/build-phase` halts at Step 100 on this host**. Do not invoke either. Every task
below is a direct edit or a read-only check, and none of them needs `/build-step`.

Project: `skill-mesh`. Work in the project repo, not the `dev` coding root. `origin/main` is at
`90b36f0`, tree clean, nothing unpushed.

Commands are spelled `powershell`, never `pwsh` (PowerShell 7 is not installed). This repository has
**no lint and no typecheck** by design — pytest is the only automated gate. Do not invent one and do
not report "0 lint violations".

## 1. FIRST: the detached gate, and Step 107's close-out

A full repo-root `python -m pytest` was started detached at commit `d4c88ee`:

- pid `32156`, started `2026-08-26T19:53:38Z`, ~27% at handoff
- exit-code sentinel: `<session-scratchpad>/gate-exit.txt`
- log: `documentation/findings/phase-is-gate-d4c88ee.txt`
- run metadata: `<session-scratchpad>/gate-meta.txt`

**Read the sentinel for the exit code. Never infer green from the log tail** — the log is UTF-16 and
a truncated tail reads exactly like a clean one.

If the process is gone and no sentinel exists, the run died; re-run it detached from the repo root
and wait. Do not run any other pytest concurrently — a concurrent run contends for memory and can
push the machine under 2 GB, where this suite reds random subprocess tests that pass in isolation
(issue #156). Check `Get-Counter '\Memory\Available MBytes'` before believing any red.

When it returns green, do these **in this exact order** — it is Step 107's `Done when`, and the
order is what keeps the comparison non-circular:

1. Compare the measured count against the **1335 passed / 1 skipped** currently recorded in
   `documentation/phase-75-baseline.md` (see its `CURRENT` row, ~line 170).
2. **Then** write the new figure into that owner. It is the single source; no other file may restate it.
3. **Then** flip Step 107 to `**Status:** DONE (<date>)` in
   `documentation/instruction-file-symmetry-plan.md`.
4. **Then** close issue #151 with the measurement as evidence.
5. Remove the two `phase-is-gate-d4c88ee` lines from `.git/info/exclude` and commit the log as evidence.

Expected: `+6` or more against 1335 is fine; a count **below** 1335 is a regression and a hard stop.

## 2. Four defects proven LIVE on `main`

A second `/build-phase --resume 107` ran concurrently with the one that produced `d4c88ee`. That
session lost the race, but its review found defects that are live on `main` today. Full evidence:
`documentation/findings/step-107-parallel-review-evidence.md` § 2. Each was re-confirmed by direct
enumeration against the landed files.

| # | Location | Defect |
|---|---|---|
| 1 | `documentation/architecture.md:627,632` | Claims the write surface is "never the adapter, for every portable skill" and that adapters "need no instruction-file prose of their own". **False.** `skills/plan-init/providers/codex.md:11` is a *portable* skill's adapter carrying exactly that prose, mandated by this plan's Step 101 — and `tests/package-integrity/test_instruction_contract_single_owner.py` counts it in `CITER_FLOOR = 4`. **A maintainer who follows the prose and deletes it reds the suite.** Fix this one first. |
| 2 | `documentation/host-discovery.md:257` | A pre-existing row answers "Are workspace instructions loaded?" with "the host's instruction-file convention". This repository follows that convention exactly and Codex receives none of the content. |
| 3 | `documentation/architecture.md:538,:603`; `documentation/host-discovery.md:189,:274` | Four unqualified "read-only" descriptions of the reproduction, contradicted by `documentation/codex-instruction-delivery.md:72`, which the same change landed and which says in bold it is "not side-effect-free". |
| 4 | `documentation/codex-instruction-delivery.md:73-74` | "three files under the Codex home re-stamped" — a per-invocation count from one uncontrolled sample. See § 4 below; **publish no per-invocation count.** |

Gate your edits with `python -m pytest tests/package-integrity` (~40 s, 278 passed at `90b36f0`) —
but only once the detached full gate has finished.

## 3. Step 108 (#152) is BLOCKED — 1 high, 9 medium

The **install is verified correct and is not in question**: `-Provider all` exit 0; install exit 0
(128 files, 58 entries); inspector `state=present owned=58 unowned=0 ledger=valid`; and a
whole-profile comparison against a fresh build at HEAD showed **zero differences across all 57
skills**. One reviewer graded § 1 "merge-ready standing alone".

What blocked it is the transcript's **§ 2 operator half, which was never executed by a host**.

- Work is preserved **unmerged** on branch `build-step-s108-1787768088` @ `ea5eff8`, worktree at
  `../worktree_build-step-s108-1787768088`. The 805-line transcript is committed there.
- Per-lens findings: `.build-step/review-{correctness,bugs,security,testquality,style}.md` in that
  worktree.

**The HIGH, and the thing worth knowing:** § 2.0 states that this repository does not document how an
arbitrary directory becomes a running host's discovery home. **It does.**
`documentation/host-native-discovery-cutover-plan.md:99` § "Step 49-50 host-trace amendment
(2026-08-09)" documents it for both hosts — for Claude, run a fresh `claude --setting-sources
project` session **from the consumer home**, verified by the session JSONL `cwd` and the
host-supplied `Base directory for this skill:` line resolving to `<home>/.claude/skills/<skill>`;
for GPT, `copilot -C <home> skill list --json`. Steps 49 and 50 are both `Status: DONE (2026-08-09)`.

That instrument grades the **binding**. § 2.0's `Select-String` probe only grades a tree the operator
names, which is why it cannot catch the collision in § 5 below.

Three of the nine mediums are **false-green** classes, which is why this blocked rather than passing
with findings recorded: concatenating the § 2.1 fixture and instrument blocks exits 0 while
Instrument B throws and prints `False`; Instrument A embeds a manual host action mid-block, so a
whole-block paste yields a silent false PASS on rows 2–4; and two "Observed output" blocks cannot
have been emitted by the command above them.

These are 1–3 line edits each. Fix them directly on the preserved branch, then merge it to `main` —
do not re-run `/build-step`.

## 4. Measurement correction — supersedes § 1 of the phase plan and Round 7

The figure "`codex debug prompt-input` rewrites two files under the Codex cache on every invocation"
is **refuted**. Two independently designed re-measurements, each bracketed by **zero-invocation
control intervals**, found: attributable changes ranged from none to three, the two protocols
disagreed about the same command, and **a control interval with the command never run reproduced the
exact same signature**. The Codex home churns on its own.

What survives is only the project-scoped claim: the command writes nothing in the project directory,
and `config.toml`, `auth.json` and every session/skill/plugin file were unchanged in every manifest,
so a `-c` override leaves nothing on disk. **Do not publish a per-invocation file count.**

Method note: the Codex home cannot be fingerprinted while any codex process is live.

## 5. Two facts you need before Step 109 (#153)

Step 109 is the operator UAT — five D10 rows plus two host-delivery checks. It needs a human at a
host session; do not attempt it headless.

1. **A stale `plan-init` is live in the personal `~/.claude/skills` root** — 26,477 bytes, **0**
   occurrences of `AGENTS.md`, no `## Instruction-file contract` heading — and Claude Code discovers
   that root **regardless of cwd**. The current tree has 34 `AGENTS.md` lines and the heading at
   `:446`. On D10 **row 2** the stale core skips and writes nothing, which is byte-identical to row
   2's expected "Touch neither" — so **row 2 can report PASS against the stale tree**, which is the
   exact failure Step 108 exists to prevent. Bind the host per § 3's documented mechanism and confirm
   via the `Base directory for this skill:` line before grading any row.
2. **Do not install into the real home to "make the host read it".** `~/.claude/skills` is a symlink
   to `~/dev/.claude/skills`, which sits inside the `dev` coding-root repo with **1,235 git-tracked
   files** under it, and the real home already carries a skill-mesh install ledger — so the installer
   treats it as an *owned* home and overwrites **silently**: measured, no `-Force`, no `-BackupDir`,
   no prompt.

The scratch install home Step 109 depends on is at
`<session-scratchpad>/step108-home` (129 files). It is a temp tree and may be cleaned. If it is gone,
recreate it from § 1.8 of the transcript committed at `ea5eff8` — the recipe is complete, and a
recreated home is equivalent because the profile is byte-identical to a fresh build at HEAD.

## 6. Transferable lessons from this session

- **A step that transcribes an upstream artifact inherits that artifact's errors.** Four instances:
  three from § 1 of the phase plan (a false "writes nothing", an override spelling that exits 1 in
  PowerShell 5.1, `§ N` spacing against the repo's `§N`) and one from the orchestrator's own
  instruction (`Step 101 (#146)`; the plan maps 101→#145, 102→#146). Fix the upstream artifact, not
  just the copy.
- **A universal claim is cleared only by ENUMERATING the set it quantifies over.** Of 10 claims
  audited ("every", "only", "never", "no …"): 3 TRUE, 4 FALSE, 3 NEEDS-SCOPING. Three false
  universals had already survived review, each refuted by a *single* live counter-example nobody had
  looked for. Reading never catches these. Defect § 2.1 above is one of them.
- **A measurement without a control interval measures background churn.** See § 4.
- **Documentation that paraphrases a contract it should cite has no mechanical guard**, because the
  single-owner gate probes designated *literals*, not meaning. That is why Step 107's iteration 3 cut
  eight paraphrase sites rather than rewriting them more carefully.
- **`tools/release_checks.py`'s `find_broken_local_links` sweeps whole text with no fenced-code
  exemption** — a markdown link cannot be quoted anywhere in `documentation/**/*.md`, even inside a
  fence. Measured and settled: 299 links repo-wide, 0 inside fences, so this is correct behavior, not
  a bug to work around.

## 7. Order of work

1. Wait for the gate → close out Step 107 (§ 1). Highest value; it is blocked only on wall-clock.
2. Fix defect § 2.1 (it can red the suite), then § 2.2–2.4.
3. Step 108's ten findings on the preserved branch, then merge (§ 3).
4. Hand Step 109 back to the operator with § 5's two facts stated up front.
