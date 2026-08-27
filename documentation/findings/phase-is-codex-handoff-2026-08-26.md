# Phase IS handoff — Claude Code → Codex CLI (2026-08-26)

**Read this whole file before acting.** It is self-contained: it assumes you have no memory of the
session that produced it.

## 0. What you may NOT do on this host

`/build-step` is a recorded `blocker`/`wontfix` on Codex — it has no isolated fresh-context
primitive — so **`/build-phase` halts at Step 100 on this host**. Do not invoke either. Every task
below is a direct edit or a read-only check, and none of them needs `/build-step`.

Project: `skill-mesh`. Work in the project repo, not the `dev` coding root. This file names no
current HEAD on purpose — `plan.md` is the execution-status index; read it for where things stand.

Commands are spelled `powershell`, never `pwsh` (PowerShell 7 is not installed). This repository has
**no lint and no typecheck** by design — pytest is the only automated gate. Do not invent one and do
not report "0 lint violations".

> ## SUPERSEDED IN PART — 2026-08-27
>
> A **concurrent session** was driving the same phase while this file was written and has since
> overtaken most of it. Do **not** act on §§ 1–3 below; they are removed. What actually happened:
>
> - **Step 107 (#151) is DONE and CLOSED.** The detached gate returned `1341 passed, 1 skipped`,
>   exit 0, 2:27:23, at `d4c88ee` — `+6` on the recorded 1335, skip unchanged. That figure is
>   written into `documentation/phase-75-baseline.md` as CURRENT and the log is committed at
>   `719e622`.
> - **Step 108 (#152) is no longer BLOCKED.** It is `LANDED / CERTIFICATION PENDING` after five
>   independent checkpoint reviews, now reporting 0 high / 0 medium. Its repo-root gate is pending.
> - **Two of the four defects this file listed are fixed** (`architecture.md`'s "never the adapter"
>   claim, and the published per-invocation cache count). The `host-discovery.md` "host's
>   instruction-file convention" row was still present at the time of writing.
>
> **For current state read the owners, not this file:** `plan.md` (the execution-status index),
> `documentation/instruction-file-symmetry-plan.md` §§ 7 and 12, and issues #151–#153. Volatile
> status is deliberately not restated here — that is the same one-owner discipline § 6 below
> describes.
>
> §§ 4–6 remain accurate and are the reason this file is kept: a measurement correction, two facts
> that decide whether Step 109 can produce a true result, and the transferable lessons.

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
   exact failure Step 108 exists to prevent. **Bind the host before grading any row**, by the
   mechanism `documentation/host-native-discovery-cutover-plan.md:99` § "Step 49-50 host-trace
   amendment (2026-08-09)" records and Steps 49/50 executed: run a fresh
   `claude --setting-sources project` session **from the consumer home**, and confirm via the
   session JSONL `cwd` plus the host-supplied `Base directory for this skill:` line resolving to
   `<home>/.claude/skills/<skill>`. For GPT, `copilot -C <home> skill list --json`. That
   instrument grades the **binding**; a `Select-String` probe over a path you supply grades only
   a tree and cannot see this collision.
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
  looked for. Reading never catches these — one of the four was a claim that adapters never carry
  instruction-file prose, refuted by the single portable adapter that does, which a gate counts.
- **A measurement without a control interval measures background churn.** See § 4.
- **Documentation that paraphrases a contract it should cite has no mechanical guard**, because the
  single-owner gate probes designated *literals*, not meaning. That is why Step 107's iteration 3 cut
  eight paraphrase sites rather than rewriting them more carefully.
- **`tools/release_checks.py`'s `find_broken_local_links` sweeps whole text with no fenced-code
  exemption** — a markdown link cannot be quoted anywhere in `documentation/**/*.md`, even inside a
  fence. Measured and settled: 299 links repo-wide, 0 inside fences, so this is correct behavior, not
  a bug to work around.

## 7. What is actually left

Read `plan.md` and issues #151–#153 first; they own current state. As of this file's last edit the
outstanding work was: Step 108's repo-root certification gate, the `host-discovery.md` "host's
instruction-file convention" row, and Step 109 — which is an operator UAT needing a human at a host
session, and which should not begin until § 5's two facts are addressed.
