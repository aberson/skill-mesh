<!-- REDACTION NOTE. Machine-specific absolute paths are replaced throughout by these
     placeholders, and an appending author must keep using them — this is a public repository
     and tests/package-integrity/test_manifest_contract.py::test_no_absolute_private_paths_committed
     sweeps every tracked AND untracked-but-not-ignored text file for absolute user paths:

       <scratch-home>          the disposable install home (see § 1.8)
       <scratch-project>       that same physical root while Step 109 uses it as the project (§ 2)
       <scratch-claude-config> the distinct disposable Claude state root (see §§ 1.8 and 2.0)
       <fresh-build-output>    the build root (historical throwaway; Step 109 receipt-bound, § 1.8)
       <evidence-export>       the durable redacted-evidence root retained after cleanup (§ 1.8)
       <repo>                  this checkout's absolute path, where it appeared in tool output

     One token needs care. In §§ 1.5-1.6, `<repo>/_shared/<leaf>` is NOT a redaction — it is
     the LITERAL string canonical cores use to cite the vendored shared payload, and § 1.6 O2
     is specifically about that literal being rewritten at emit time. Read it as source bytes,
     not as a hidden path. -->

# Instruction-file symmetry — build, install and UAT transcript

**Status: § 1's historical build/install outcome is COMPLETE — its original commands produced the
recorded results. Later safety requirements are stated as contracts, not presented as retroactively
executed or ready-to-run implementations. Step 108 certification requires independent review of
these repaired instrument-boundary bytes and a stable repo-root gate; neither completion receipt is
claimed inside this frozen artifact. § 2 (Step 109) is
BLOCKED BEFORE GRADING: selected fixture and filesystem-only components were mechanically
validation-run, but no skill was invoked, no host-delivery command ran and no D10 row was graded.
The engineering blocker is recorded in § 2.5; no behavioral observation or row verdict may be
pre-filled.** Do not replace or reinterpret § 1's historical record. Step 109 must still run
§ 1.8's fresh-root build/install/reverification recipe; if #153 selects a route whose #162
implementation changes writer bytes, follow the
full hash-refresh branch in § 2 as well. Do not read § 2's blank cells as results. Its expected
results and commands are instruments, not findings.

The verification record for Phase IS **Step 108** (build + install into a scratch home, issue
#152) and **Step 109** (operator confirmation of all five D10 rows, issue #153) of
`documentation/instruction-file-symmetry-plan.md`.

**Why both steps share one file.** Steps 100–106 edited `skills/<name>/core.md`. This
repository is the canonical *source*, not an installed skill tree, so those edits changed
nothing a host can invoke — the installed catalog elsewhere on this machine is a separate,
stale copy. Step 108 exists to produce an installed tree that provably carries the new
contract, so that Step 109's operator UAT exercises the **new** behavior rather than
reporting PASS against the old one. Step 108's transcript is therefore the precondition
evidence for Step 109's.

**That purpose is not self-executing, and § 2 is built around the gap.** Step 108 produced a
current tree; it did **not** prove any host loads from it because no host session ran. § 2.0
therefore applies this repository's accepted host-trace mechanism before any row is graded,
because without it D10 row 2 could report PASS against the stale tree. See § 2.0 for the
measurement behind that claim.

---

# 1. Step 108 — build and install into a scratch home

**Run date:** 2026-08-26
**Executed in:** a `skill-mesh` git worktree at `d4c88ee` ("checkpoint: step 107 code landed
— vendor the codex measurement (#151)"), with no modified tracked file at any point during
the run.
**Scratch home:** a disposable directory named `step108-home`; see § 1.8 for its historical
disposition and Step 109's mandatory fresh-root recipe. It was empty before the run. **The
operator's real home was never a target** — no command in this transcript names it.

Nothing outside the worktree and the session scratchpad was written. `dist/` is gitignored.

## 1.0 Shell contract

**Every command fence in § 1 is written for Windows PowerShell 5.1.** The original commands were
executed in that shell. Later fail-closed requirements are prose contracts for Step 108P; § 1
publishes no replay implementation for them, and they were not retroactively run against the
now-audit-obsoleted historical home. Historical commands are spelled
`powershell`; PowerShell 7 (`pwsh`) is not installed on this machine.

This is stated as a per-command contract rather than as scenery, because two POSIX spellings
in an earlier draft of this file did **not** hold in the declared shell, and one of them
failed *silently*. Measured in PowerShell 5.1 on this machine:

- **`grep` does not exist** — `CommandNotFoundException`. Loud and recoverable. This
  repository already documents the same fact and the same remedy at
  `documentation/codex-instruction-delivery.md` ("`grep` is not on `PATH` by default in
  Windows PowerShell, this repository's floor shell"), so `Select-String` is the house
  spelling, not an invention of this file.
- **`diff` is an alias for `Compare-Object`**, and `-r` binds as a unique prefix of
  `-ReferenceObject`. With real paths substituted, `diff -r <a> <b>` **succeeds** (`$?` is
  `True`) and compares the two path *strings*, emitting diff-shaped output asserting the two
  sides differ — the exact opposite of the zero-differences it was cited as evidence for,
  having never opened either directory. A silent wrong answer is worse than a missing command,
  so this one is called out by name.

Both were replaced with PowerShell 5.1 forms, and the core replacement operations were **run**, not
merely written; § 1.5 records their historical output. The fail-closed path, link, count, and error
requirements were specified later as prose for Step 108P, not published here as replay guards or
retroactively executed. Where a figure below was originally obtained with a POSIX tool under Git
Bash, it was re-measured in PowerShell 5.1 for this record and the two agreed.

## 1.1 Results at a glance

Each row's verdict rests on the **evidence** column, not on an exit code alone. Where an exit
code cannot discriminate the property being claimed, the row says so and cites the observation
that can.

| # | Criterion | Command (PowerShell 5.1) | Exit | Evidence the verdict rests on | Verdict |
|---|---|---|---|---|---|
| 1 | All three profiles build | `tools/build-distributions.ps1 -Provider all` | 0 | 57/54/54 skills and 128/125/125 files, matching the manifest partition (§ 1.2) | PASS |
| 2 | Claude profile installs | `tools/install-skill-mesh.ps1 -Provider claude -Home <scratch-home>` | 0 | 128 files reported and 128 recounted on disk; 58 top-level entries; ledger written (§ 1.3) | PASS |
| 3 | Inspector reports it installed | `tools/inspect-host-install.ps1 -Home <scratch-home>` | 0 — **uninformative, see below** | `state=present link=directory`, `owned=58 unowned=0`, `ledger: state=valid providers=[claude]` (§ 1.4) | PASS |
| 4 | Installed tree carries the new contract | `Get-FileHash` manifest + `Compare-Object` against a fresh build at HEAD; corroborated by `Select-String` | n/a — see evidence | **0 differences** over 128 files each side; `plan-init/core.md` body differs from canonical on 5 of 671 source lines, all five the documented repoint (§ 1.5) | PASS |

**Why row 3's exit code is called uninformative, measured rather than argued.** Running the
same inspector against a freshly created **empty** directory with nothing installed also exits
**0**, printing `state=absent` for all three profiles and `ledger: state=absent`. The script
has exactly one non-zero exit (an invalid `-Home`); it is a *report* tool, and its exit code
grades argument validity, not install state. So "exit 0" cannot fail for the thing row 3
claims to check, and the three named report lines are what carry the criterion.

**Why row 4 carries no exit code at all.** Its instrument is a PowerShell pipeline, not an
external program, so there is no process exit status to quote; the verdict is the
`Compare-Object` result (empty = identical). Quoting a `$?` of `True` there would be the same
empty gesture as row 3's `0`.

**Why row 4's evidence is the byte comparison rather than a heading search.** The heading
`## Instruction-file contract` and its owner marker both entered `skills/plan-init/core.md`
in the *same* commit — Step 100, `b713ea6` (#144) — so searching for the heading discriminates
exactly one boundary: pre-Step-100 versus post-Step-100. It would pass green against a copy
stale at any later commit, including one missing Step 101 (#145), which implements the
`plan-init` behavior Step 109 row 1 exercises. The search is recorded in § 1.5 as
corroboration; the byte comparison is what decides the row.

All four passed on the first attempt; nothing was retried. Two non-blocking observations are
recorded in § 1.6 — one expected warning and one cosmetic prose artifact.

## 1.2 Criterion 1 — build all three host distributions

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1.

```
powershell -File tools/build-distributions.ps1 -Provider all
```

**Historical command only — do not replay it for Step 109.** With the default output, the builder
removes existing `<repo>\dist\{claude,gpt,codex}` subtrees before its later containment checks.
Step 109 uses only § 1.8's proven-empty, receipt-bound custom output root.

**Exit code: 0.** Output, verbatim except for the redacted repository path:

```
build-distributions: claude -> <repo>\dist\claude (57 skills, 128 files)
build-distributions: gpt -> <repo>\dist\gpt (54 skills, 125 files)
build-distributions: codex -> <repo>\dist\codex (54 skills, 125 files)
build-distributions: done. OutputDir = <repo>\dist
```

The per-profile skill counts are exactly the manifest's: 57 claude (54 portable + the 3
provider-native Claude-only skills), 54 gpt and 54 codex (the portable set; the three
provider-native skills are correctly absent from both non-claude profiles).

## 1.3 Criterion 2 — install the claude profile into the scratch home

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1.

```
powershell -File tools/install-skill-mesh.ps1 -Provider claude -Home '<scratch-home>'
```

**Exit code: 0.** Output, verbatim except for the redacted home:

```
install-skill-mesh: installed 'claude' into <scratch-home>\.claude\skills (128 files).
```

128 files installed — the same 128 the claude profile emitted, so the install is the whole
profile and not a subset. Independently recounted on disk afterwards, the directory holds
**128** files and **58** top-level entries (57 skill directories plus the `_shared/` payload
directory).

The ownership ledger was written to `<scratch-home>/.skill-mesh-install.json`
(`ledger_version: 1`, `tool: "skill-mesh"`, `installs` keyed by the single provider
`claude`). Its contents are summarized rather than pasted: the file is a ~40 KB map of owned
paths and hashes, which would add 128 rows of noise and no evidence.

## 1.4 Criterion 3 — the inspector reports the profile installed

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1.

```
powershell -File tools/inspect-host-install.ps1 -Home '<scratch-home>'
```

**Exit code: 0** — which, per § 1.1, is uninformative on its own. The report's load-bearing
lines follow. The block below is **excerpted AND reordered**, not verbatim: the four skill
rows shown are the contract-relevant ones pulled out of a 58-row listing whose real order is
alphabetical after `_shared`. The bracketed line is an authored elision marker, not tool
output.

```
skill-mesh host-install report (schema_version 3)
consumer_home: .

instruction files:
  CLAUDE.md: present=no [unknown]
  AGENTS.md: present=no [unknown]

claude profile (.claude/skills): state=present link=directory
  owned=58 unowned=0
  adapter_sample: build-observer -> profile=claude
    - _shared: shared-payload (manifest=-, owned=yes)
    - plan-init: managed (manifest=portable, owned=yes)
    - repo-update: managed (manifest=portable, owned=yes)
    - context-slim: managed (manifest=provider-native, owned=yes)
[ ... 54 further rows elided by the author of this transcript ... ]

gpt profile (.github/skills): state=absent link=absent
codex profile (.agents/skills): state=absent link=absent
legacy .claude/skills-gpt (.claude/skills-gpt): state=absent link=absent

ledger: state=valid providers=[claude] unrecognized=0
router: classification=absent version=- path=-
legacy_shadows: []
```

`state=present`, `owned=58 unowned=0`, and `ledger: state=valid providers=[claude]` are the
three lines that answer the criterion. Across all 58 rows every entry reads `owned=yes`; 57
read `managed`, and the 58th is the `_shared` payload row, which reads `shared-payload` —
the distinction is visible in the excerpt above.

The two absent profiles and the absent legacy tree are correct: this step installs exactly one
profile by design. The inspector prints `consumer_home: .` because it relativizes paths unless
`-AbsolutePaths` is passed — the report is therefore already free of absolute paths.

The `instruction files: present=no` rows describe the **scratch home itself**, which has no
`CLAUDE.md`/`AGENTS.md` of its own. That is expected here, and § 2.0 makes deliberate use of
it: a directory in which both names are ABSENT is already a D10 **row 1** fixture.

## 1.5 Criterion 4 — the installed tree carries the new contract

The question this criterion answers is whether the bytes a host would load *from this tree*
are the current canonical contract. (Whether a host loads from this tree at all is a separate
question, and § 2.0 owns it.)

### The primary evidence — the whole installed profile equals a fresh build at HEAD

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1. Two steps: rebuild the claude
profile from canonical source into a throwaway directory, then compare the two trees by
content hash.

```
powershell -File tools/build-distributions.ps1 -Provider claude -OutputDir '<fresh-build-output>'
```

**Exit code: 0** (`claude -> <fresh-build-output>\claude (57 skills, 128 files)`). Preconditions
recorded at run time: `HEAD=d4c88ee`, and `git status --porcelain --untracked-files=no` empty,
so the rebuild is from HEAD source with no local modification.

**Historical command only — do not replay it standalone.** The builder removes an existing
`<OutputDir>\claude` before its later containment checks. Step 109 therefore does not rerun this
one-provider command or use the default `<repo>\dist`: § 1.8 requires one all-provider build only
after a committed guard proves every deletable provider child absent under a new receipt-bound
output root. The installed tree is then compared to that already-built `claude` subtree.

The historical comparison used relative-path/SHA-256 manifests plus `Compare-Object` and produced
the recorded zero-difference result below. It was a build/install observation in a cooperative
scratch tree, not a hostile-filesystem containment fence. Step 108P must supply the Step 109
comparator as a native subcommand: retain one no-follow, no-write/delete-sharing handle per root and
per entry through traversal and hashing; obtain final paths, `FILE_ID_INFO`, and
`FILE_STANDARD_INFO.NumberOfLinks` from those retained handles; traverse and hash handle-relatively;
require regular single-link entries; and compare against the receipt-bound exact manifest and count,
not merely two equal nonempty live trees. No runtime compiler or path-based replay is published here.

```text
BLOCKED: Step 108P (#162) must supply the certified native tree-comparison subcommand;
this historical transcript intentionally publishes no replayable comparator implementation.
```
Historical observed result, with the counts and `RESULT:` label emitted by the reporting wrapper
around the original comparison. It records the outcome; it does not claim the later guards above
were retroactively executed:

```
fresh files=128  installed files=128  differences=0
RESULT: IDENTICAL
```

The historical wrapper compared relative path **and** SHA-256 for every file, so in that cooperative
run it caught a renamed file, a missing file and a changed byte alike. One command covered **all 57
installed skills**, so it
covers every skill Steps 100–106 edited — `plan-init`, `repo-update`, `build-observer`,
`citation-review`, `goblin-suggest`, `research-prospect`, `review-uat`, `user-brainstorm`,
`user-learn` and `context-slim` — rather than proving currency for one of them.

This matters concretely for Step 109: the plan assigns `/repo-update` to **rows 3–5**, including
the deliberately selected row-4 arm, so an install stale at Step 102 (#146) — the commit that
implemented the `repo-update` D10 column — could make those rows report PASS
against old behavior. Spelled out for that skill specifically: installed
`repo-update/core.md` is 571 lines (564 body + the 7-line header) against a canonical 564,
differing on exactly **one** source line — a `<repo>/_shared/step-authoring.md` →
`../_shared/step-authoring.md` repoint at canonical line 160 — and it carries the Step 102
heading "Step 7 — Refresh the project instruction file (CLAUDE.md or AGENTS.md)" at installed
line 250 (canonical 243). That heading's provenance was checked with `git log -S` on the exact
string: it entered at `f5e7a84` (#146), which is Step 102.

Throughout this section, "differing on N lines" counts **changed source lines**, not
unified-diff output rows.

### `plan-init/core.md` in detail

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1.

The historical heading probe found the one match recorded below. The exact-count and exact-text
predicate shown must run only inside Step 108P's handle-bound native comparison subcommand against
Step 109's fresh installed tree; it is not a standalone containment boundary and was not
retroactively run against the historical one. The historical line number is printed but is not a
commit-independent gate. If route 1 changes writer/build bytes,
§ 1.8 requires the newly built tree's exact count and emitted heading location to be derived and
receipt-bound before install; do not copy `d4c88ee`'s `446` into that route.

```
$ContractHeadingMatches = @(Select-String `
  -LiteralPath '<scratch-home>\.claude\skills\plan-init\core.md' `
  -Pattern '^## Instruction-file contract' -CaseSensitive -ErrorAction Stop)
if ($ContractHeadingMatches.Count -ne 1 -or
    $ContractHeadingMatches[0].Line -cne '## Instruction-file contract') {
  throw 'Installed plan-init core lacks exactly one exact contract heading.'
}
"$($ContractHeadingMatches[0].LineNumber):$($ContractHeadingMatches[0].Line)"
```

One match:

```
446:## Instruction-file contract
```

The section sits at line 446 of the emitted file versus line 439 of the canonical
`skills/plan-init/core.md`. The 7-line offset is exactly the emitted provenance header, whose
six comment lines and one trailing blank are:

```
<!-- GENERATED FILE - DO NOT EDIT.
     Marker: SKILL-MESH-GENERATED-FILE
     Produced by tools/build-distributions.ps1 from config/skill-manifest.json.
     Canonical source: skills/plan-init/core.md
     Profile: claude
     Edit the canonical source and rebuild; edits here are overwritten. -->
```

Normalizing both sides (BOM stripped, CRLF→LF, the same rule the release checksums use) and
removing those 7 lines leaves **5 changed source lines out of 671**, and all five are the
documented emit-time shared-reference repoint `<repo>/_shared/<leaf>` → `../_shared/<leaf>`
described in `tools/build-distributions.ps1`'s header. Their canonical line numbers are 168,
224, 226, 424 and 454. No other line differs.

### Corroborating resolution checks

A repointed or cross-skill reference that dangles in the installed tree would make the
contract unreadable at run time, so both were resolved on disk:

- `<scratch-home>/.claude/skills/plan-init/../_shared/step-authoring.md` — **resolves.** The
  15-file `_shared/` payload sits at the profile root as a sibling of the skill dirs, which
  is the depth every `../_shared/` repoint assumes.
- `<scratch-home>/.claude/skills/repo-update/../plan-init/core.md` — **resolves.** This is
  the D11 bounded citation. The installed sentence, at installed line 255 (canonical
  `skills/repo-update/core.md:248` — the offset is the same 7-line header), reads:

  > … Which instruction file this step may write, and which it must leave alone, is
  > decided by the project's instruction-file state — see the Instruction-file contract in
  > plan-init/core.md (`../plan-init/core.md`), the ONE owner of that contract. This core
  > applies it by citation and deliberately does not restate it.

  **Two disclosed departures from the source bytes**, so the quote is not mistaken for
  verbatim. First, the leading ellipsis marks a mid-sentence start: the installed line begins
  "Which instruction file this step may write…" and is quoted from there, which is the whole
  line. Second, the source spells the reference as a *markdown link* whose display text and
  target are both `../plan-init/core.md`; above it is flattened to a plain code span. That
  flattening is forced, not stylistic — `tools/release_checks.py`'s
  `find_broken_local_links` resolves every markdown-link target in `documentation/**/*.md`
  by regex, with no fenced-code exemption, so reproducing the literal syntax anywhere in
  this file (fenced or not) would resolve `../plan-init/core.md` against
  `documentation/findings/` and red the link gate. (The same checker skips any target
  containing `<`, `>` or `*`, which is why the `<repo>/_shared/<leaf>` literals elsewhere in
  this file survive the sweep untouched.) The rendered text is unchanged, and the target's
  real resolution was checked on disk instead — that is the bullet this quote sits under.

### Single-owner property in the installed tree

The owner marker `<!-- instruction-file-contract: owner -->` appears in exactly **one**
installed file, `<scratch-home>/.claude/skills/plan-init/core.md`. Three other installed files
mention the contract by name and all three are citations, not restatements:
`repo-update/core.md` (quoted above), `goblin-suggest/core.md`, and `context-slim/SKILL.md` —
the last being the provider-native skill made inversion-aware at Step 105, whose adapter
carries the citation directly because it has no core.

## 1.6 Observations (neither blocks the step)

### O1 — the inspector's one warning is the expected consequence of a single-profile install

**Severity:** none (expected output) · **Disposition:** accept — no action.

```
warnings (1):
  [MANAGED_SKILL_MISSING_GPT_PROFILE] 54 portable managed skill(s) under .claude/skills
  have no .github/skills counterpart: build-observer, build-phase, build-queue, build-step,
  citation-distill, citation-review, citation-sweep, citation-triage, goblin-do,
  goblin-suggest, ... (+44 more)
```

(The `... (+44 more)` above **is** the inspector's own truncation, unlike the authored marker
in § 1.4.)

Step 108 installs the claude profile only, so the 54 portable skills genuinely have no GPT
counterpart in this home. The count matches the portable roster exactly. Not a defect; the
warning is doing its job. Installing the gpt profile would clear it, and this step
deliberately does not: Step 109 exercises Claude-side skills plus Codex **instruction-file
delivery**, and per `documentation/architecture.md` an instruction file is an instruction
adapter, never a skill registry — so that Codex check needs no codex skill profile. Neither
the gpt nor the codex profile is installed in this home, and neither needs to be.

**Cost of that scoping, stated plainly:** the gpt and codex profiles have build-count evidence
only (125/125 files emitted); no content check was run against either. If a later step needs an
installed codex skill tree, that install and its verification are unbudgeted work.

### O2 — the emit-time repoint inverts the meaning of one sentence that is *about* the spelling

**Severity:** minor (cosmetic; one explanatory clause in an emitted artifact) ·
**Disposition:** record, do not fix — out of this step's scope.

In the canonical owner section, the paragraph explaining why the contract has no `_shared/`
file says provider adapters "are forbidden the `<repo>/_shared/<leaf>` spelling cores must
use." The repoint rewrites that literal like any other, so the emitted claude artifact reads
"are forbidden the `../_shared/<leaf>` spelling cores must use" — which, in the emitted tree,
names the spelling everything *does* use. The rewrite is correct-by-construction for every
reference meant to resolve; this one instance is prose *mentioning* a spelling rather than
*using* it, and the builder cannot tell the two apart. It is the change at **canonical line
454**, the last of the five listed in § 1.5. (Stated as a line number rather than a hunk
ordinal: with zero context lines the five changes are five hunks and this is the fifth, but
with `diff -u`'s default three lines of context the adjacent changes at 224 and 226 merge and
it becomes the fourth of four. The line number is unambiguous under both.)

Confined to a single explanatory clause: no reference dangles, the decision the paragraph
justifies (no `_shared/` file for this contract) is unaffected, and nothing downstream reads
the sentence. Not fixed here because a fix would touch `tools/build-distributions.ps1` or a
canonical core, both out of scope for this step. If it is ever worth addressing, the cheap
repair is to reword the canonical sentence so it spells neither literal.

## 1.7 Gate

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1.

```
python -m pytest tests/package-integrity
```

**Exit code: 0. Result: 278 passed, 0 failed.** The summary line as pytest emits it, from the
last of this step's runs:

```
278 passed in 39.65s
```

**The count is the result; the wall clock is not a figure of record, and is not quoted as
one.** Across this step's runs the same 278 passes took anywhere from **under a minute to over
ten minutes** on the same machine at the same commit — an order of magnitude, extremes rounded
outward from what was observed. The slow end coincided with memory pressure (~2.1 GB
available), and these suites shell out to PowerShell once or more per test, so they are the
first thing to suffer when the machine is loaded. Read the count and the exit code; treat a
slow run as a loaded machine, not as a signal. A re-run landing anywhere in that range
contradicts nothing here.

Run with this findings file in place and still untracked. That is deliberate:
`test_no_absolute_private_paths_committed` enumerates
`git ls-files --cached --others --exclude-standard`, so it sweeps untracked-but-not-ignored
files — the sweep is meaningful *before* `git add`, which is when the author is still looking.

That summary line is a dated observation of this run at `d4c88ee`, not a new count of record.
`documentation/phase-75-baseline.md` is the single owner of the measured counts for the
repo-root DONE gate and the `tests/` iteration gate; it names `tests/package-integrity` as an
iteration gate but records no count row for it, so nothing here duplicates an owned figure.

The repo-root full-suite invocation (no path argument) was deliberately **not** part of the
historical build/install command sequence recorded here. Step 108's separate certification gate
runs it only after the repaired immutable transcript clears review. This repository has **no lint
and no typecheck command** by design; none was invented or claimed.

## 1.8 The historical scratch home — AUDIT-OBSOLETED for Step 109

The original Step 108 home remains historical build/install evidence, but it was created below
the OS temp tree, which on this host is inside the real user profile. The strengthened § 2.0
pre-flight therefore rejects it as a Step 109 target. Do not search for, revive, or reuse that
directory. Whether or not it still exists, Step 109 must create a new receipt-bound scratch
home/project, a distinct scratch Claude config root, and a distinct fresh-build output root outside
the real profile, plus a fourth distinct durable `<evidence-export>` root containing redacted
attestations only. Safely build, install, and reverify the profile. After the five behavioral rows,
delivery checks, final grade, and first verified evidence publication, dispose the three disposable
roots during Step 109 closeout; retain the evidence root so a failed publication cannot erase the record.
Nothing in any of these roots is tracked by git.

Create the fresh compliant roots through these five ordered preparation/build/install/verification
stages; orchestration remains Windows PowerShell 5.1, while the admitted native boundaries are the
ones explicitly named below:

1. Issue #153 must first record a strict immutable preparation manifest and invoke Step 108P's
   separately OS-admitted native launcher's closed `prepare` entrypoint—the sole pre-receipt
   exception. With an
   empty environment and exact handle allowlist, it locks and validates the outside-profile parent,
   real-profile, attached-source, launcher/policy/loader, bundle, helper, and manifest inputs, then
   atomically creates a new random-named
   `<scratch-home>` (also `<scratch-project>` during Step 109), a distinct
   `<scratch-claude-config>`, a distinct `<fresh-build-output>`, and a
   distinct durable `<evidence-export>` under a validated, unlinked, outside-git parent — **never** the real
   home, `$HOME`, `C:/Users/<user>`, an ancestor of that home, or an existing consumer. Caller and
   `Resolve-Path` spellings are not identity evidence: reject UNC, SUBST, 8.3, mapped-drive, and
   other aliased/nonlocal spellings. The admitted launcher becomes a lifetime guardian: from
   handle-relative creation through final disposition it retains no-follow handles opened without
   delete sharing to the one common creation parent, each created root, and the real profile, and duplicates only
   those exact handles to fresh runners. Reopening a receipt path never re-establishes authority.
   Each guardian-held handle supplies both handle-final paths,
   `FILE_ID_INFO` (formatted as uppercase `<16-hex volume serial>:<32-hex file ID>`), and
   `FILE_STANDARD_INFO.NumberOfLinks`; every mutable root must be single-link. Compare those physical
   paths and identities for equality and ancestry, and fail closed if either information class is
   unavailable. Create a `FileMode.CreateNew` schema-v5 **pre-build** JSON receipt in the new home
   that binds a random nonce, all four exact caller paths, their handle-final paths and file IDs, the
   real-profile handle identity used for the exclusion
   decision, and the source/tool/fence inputs knowable before build. Record its SHA-256 and nonce on
   #153 before any builder or installer runs; do not record an absolute path. Never rewrite this
   receipt to add facts learned from the build. It also creates a strict immutable preparation-result
   receipt binding its image/argv/environment/handle set, each created root identity, process-tree/
   quiescence, protected pre/post snapshots, and zero other mutation. The launcher writes this result
   first, then creates the pre-build receipt that binds both preparation manifest and result hashes;
   the result does not bind the later receipt hash, avoiding a hash cycle. Every later boundary
   remeasures those same guardian-held handles. If the guardian, a required handle, or its no-delete
   share denial is lost, all later execution and cleanup stay blocked; a matching path plus a reused
   file ID is never accepted as continuity.
   A familiar basename is not disposable-root evidence.
2. Immediately before the only builder invocation, the committed Step 108P subcommand must resample every
   guardian-held root, real-profile, and common creation-parent handle; duplicate only the exact handles required by
   the runner; and revalidate the receipt and physical
   unlinked/outside-git/outside-profile
   ancestry, prove the build root empty, and prove its `claude`, `gpt`, and `codex` children absent.
   Its tests must fail closed for a `\\localhost\c$` alias, a SUBST alias, an available 8.3 alias,
   roots nested in either direction, a root under the real profile, and a case-mismatched filename
   on a per-directory case-sensitive fixture when the host supports one. Before any external
   process, snapshot the protected host mutation surface. The receipt must bind one exact Windows
   PowerShell 5.1 executable path/version/hash, the handle identity and exact clean commit/tree/ref
   state of the selected source checkout, and a deterministic manifest/hash closure covering the
   builder, installer, inspector, every transitive script/module, and all distribution inputs. No
   PATH-resolved executable or unpinned repository script may run. Source-state verification uses the
   separately pinned Git boundary described below: it binds the worktree/gitdir/common-dir objects,
   suppresses ambient configuration and optional helpers, and locks every authority-bearing Git
   input. Every builder/installer/inspector child receives a receipt-pinned exact environment block
   rather than ambient inheritance; every ambient `GIT_*` authority/redirection variable is absent,
   including repository/worktree/index/object, config, discovery/ceiling, SSH/askpass, editor, and
   pager paths. Only then invoke the pinned
   executable with `-NoProfile -File <receipt-pinned-build-distributions.ps1> -Provider all
   -OutputDir '<fresh-build-output>'`, require its native launch/exit proof, and compare the protected
   host snapshot before/after while allowing only the receipt-bound build root. The broker must open
   every source/tool/input manifest member without following reparse points, require each mutable
   artifact to be a regular single-link file with expected identity/hash, deny write/delete sharing, and retain those exact
   handles through child-tree quiescence; it rechecks the same handles afterward and proves the
   started process image is the locked executable. If #153 selects route 1 and Step 108P adds a UAT
   mode, use that approved checkout and follow § 2's
   rebuild/reverification/hash-refresh branch. Never replay § 1.2 against default `<repo>\dist` or
   § 1.5's one-provider build during Step 109.
3. Create the config root's unlinked `tmp` directory. The exact per-mode environment manifest names
   `CLAUDE_CODE_OAUTH_TOKEN` only for `claude-deny-probe`, `claude-auth-status`, `behavior-row`, and
   `delivery-read-only`; names `none` for `trust-bootstrap` and `codex-delivery-read-only`; and names
   process-scoped `GH_TOKEN` only for `evidence-upload`. It records no secret value. The broker must
   prove both required presence and required absence for each mode;
   do not start Claude before launch attestation, and between launch attestation and readiness permit
   only the receipt-pinned zero-project-write `claude-deny-probe`; never log in or copy/read an ambient
   credential. Keep all settings,
   plugins, credentials, history, transcripts, and temp state under that config root.
4. Install only the prebuilt bytes by invoking the same receipt-pinned Windows PowerShell executable
   with `-NoProfile -File <receipt-pinned-install-skill-mesh.ps1> -Provider claude -Home
   '<scratch-home>' -DistDir '<fresh-build-output>'`; do not let the installer launch a second
   implicit builder. Revalidate the complete source/tool receipt and compare protected host surfaces
   immediately before and after the installer. Hold the complete prebuilt distribution manifest by
   the same no-follow, single-link, identity/hash-checked read handles until the installer process
   tree is quiescent; a pre/post path hash alone is not sufficient.
5. Invoke the receipt-pinned inspector through the same executable, then confirm with § 1.4's
   output contract and § 1.5's equality/heading predicates as implemented inside Step 108P's
   precompiled fence bundle—never by inventing a path-based or runtime-compiled replay—and § 2.0's
   receipt, path, source-state, link, and hash checks before any host launch; bind the exact sorted
   whole-profile relative-path/SHA-256 manifest and count, fresh writer hashes, receipt hash,
   receipt nonce, tool/source manifest, executable hashes, and all protected host-surface
   comparisons into the post-install launch attestation consumed by Step 108P's already-pinned
   generic fence bundle during #153. Derive the exact current
   profile/entry/owned counts and emitted contract-heading location from the selected fresh build
   before install. After install, equality, and inspector verification, the only host process allowed
   before launch attestation is a narrowly scoped trust bootstrap gated by the pre-build receipt and
   immutable generic fence. It uses the exact child environment, loads no project hook/skill/MCP or
   instruction payload, writes nothing in the project, and may create only the exact version-pinned
   trust record under the disposable config root; protected snapshots and a native action record must
   prove that boundary. Close it and verify the trust record binds both physical roots. If the pinned
   host cannot establish trust under that boundary without managed-policy refresh or another startup
   surface, remain blocked. Then create a second immutable `FileMode.CreateNew`
   **launch-attestation** receipt. It chains to the pre-build receipt's hash and nonce and binds the
   trust record, full installed-profile manifest digest/count, writer manifest, current heading facts,
   the static effective-hook manifest, and fence bundle. Record its independent hash and nonce on
   #153. Restart under those first two receipts, run only the harmless denied-hook probe, and have the
   bundle create a third immutable **readiness** receipt chaining the launch-attestation hash/nonce,
   effective-hook-manifest hash, and immutable denied-probe result. Record its hash and nonce on #153.
   The trust bootstrap validates only the pre-build receipt; the denied-probe boundary validates the
   pre-build and launch-attestation receipts; every later host boundary validates all three. None is
   edited. Route 1 must replace every `d4c88ee`-only count or
   line expectation with those values; the installed tree must match the fresh tree exactly.
   The inspector subcommand similarly locks every inspected input. Negative tests for all three tool
   subcommands overwrite an already-open file in place and replace a path between validation and
   child read; both must fail before the child can consume changed bytes.

The pre-build receipt schema will be `skill-mesh/phase-is-uat-scratch/v5` and must include at least
these semantics: `schema`, `nonce`; caller path, DOS-final path, volume-GUID-final path,
`FILE_ID_INFO` identity, and `FILE_STANDARD_INFO` link count for each of `project` (the combined
scratch-home/project root), `claude_config`, `build_output`, and `evidence_export`; the same
caller/final-path/identity/link-count fields for their one common `creation_parent` and for
`real_home`; each root must be a direct child of that parent;
`preparation_manifest_sha256`, `preparation_result_relative_path`,
`preparation_result_sha256`, `source_tool_process_manifest_relative_path`,
`source_tool_process_manifest_sha256`, `fence_bundle_sha256`; launcher relative path, SHA-256,
identity, version, policy SHA-256, and loader-manifest SHA-256; helper relative path, SHA-256,
identity, MVID, and version; and `created_utc`. Step 108P owns the machine-exact property names,
nested types, and additional-property denial. No alias key is accepted. Every identity is the
uppercase `<16-hex volume serial>:<32-hex file ID>` returned by `FILE_ID_INFO` from the same retained
handle that produced both final paths; every mutable root, launcher, helper, and source input has the
separately remeasured link count required by its policy.

The pre-build receipt's fixed source/tool/process sidecar schema is the one enforced in § 2.0: it
records the physical source checkout, gitdir, and common-dir identities plus commit/tree/ref state,
exact Git and PowerShell path/identity/version/hash facts, transitive tool/input manifest digest, and
sanitized Git/build-tool child-environment digests. Before launch attestation, create the five fixed
`FileMode.CreateNew` sidecars
named in § 2.0. The trust sidecar binds the exact trust-record bytes/hash to both physical roots. The
inspector proof binds `state`, profile count, entry/owned/unowned counts, ledger provider set, and the
fresh-build/equality evidence. The host-environment manifest enumerates every mode's exact non-secret
key/value block, allowed secret key name, executable/argv image allowlist, and ambient `GIT_*`
absence. Windows environment names are unique and compared with `OrdinalIgnoreCase`; the broker
rejects case aliases such as `Path` plus `PATH`, matches protected names/prefixes case-insensitively,
and emits one schema-canonical spelling. The effective-hook manifest binds only the static post-trust
source/command/hash/matcher/precedence facts knowable before launch attestation. The managed-policy snapshot binds the exact startup-consumed policy,
settings, instruction, hook, MCP/plugin, and output-style bytes and proves no refresh path can race
them. The launch attestation pins all five sidecar hashes. After it exists, the one denied-hook probe
produces an immutable result and the readiness receipt pins that result plus the effective-hook
manifest and launch attestation. Before cleanup, every applicable bundle subcommand reopens and
verifies the complete receipt chain and exact sidecar bytes by opening each artifact
handle-relatively beneath the guardian-held root. The post-cleanup uploader instead consumes only
the durable redacted chain defined below. No public issue comment contains an absolute path or secret
value.

Hashes pin bytes, not truth. Step 108P must commit machine-readable schemas for every receipt,
sidecar, native result, nested map, event, and public attestation; this transcript lists their
mandatory semantics and does not pretend those not-yet-implemented schemas already exist. The
committed validators must reject a missing, extra, duplicate, or case-mismatched property; hashes
are uppercase 64-hex, file identities use the receipt format, timestamps are round-trip `o`, and
only set-valued arrays are duplicate-free and ordinal-sorted. Ordered arrays—especially argv and
native event/read sequences—preserve exact order and use the duplicate policy stated by their
machine schema. The generic bundle remeasures every load-bearing field rather than trusting the
sidecar's assertion. Before any
`ConvertFrom-Json`-style materialization, it reads the exact locked UTF-8 bytes with a strict decoder
and a schema-pinned streaming tokenizer that rejects a BOM, invalid Unicode, non-JSON numbers, and
duplicate member names by `StringComparer.Ordinal` at every nesting depth. `ConvertFrom-Json` alone
is never authoritative because Windows PowerShell 5.1 silently collapses duplicate keys. This rule
applies to every receipt, sidecar, native result, hook/event record, and host diagnostic in § 2; every
displayed `ConvertFrom-Json` is only the deliberately non-runnable result shape. Negative tests place
same-case and case-variant duplicate keys at the root and inside every nested object before
re-hashing the fixture:

| Sidecar schema | Mandatory semantics for Step 108P's machine-exact schema |
|---|---|
| `skill-mesh/phase-is-source-tool-process-manifest/v1` | `schema`, source root/gitdir/common-dir caller/final path/identity, 40-hex `source_commit`/`source_tree`, exact `source_ref_mode=attached-read-only`, `source_ref_name`, `source_ref_control_manifest_sha256`, Boolean-true `source_clean`, Git and PowerShell caller/final path/identity/version/SHA-256, `git_environment_manifest_sha256`, `tool_input_manifest_sha256`, `build_environment_manifest_sha256`, `created_utc`. Before each build/install/inspect boundary, the broker locks and re-hashes both executables plus the ordinary non-linked worktree's `.git`, `HEAD`, exact branch ref/reflog or packed-ref record, index, refs/packed-refs, config, and every reachable object/control input. The selected attached checkout is never detached or otherwise mutated: its HEAD/ref/reflog/index/config/object and worktree input handles remain write/delete/rename denied through the complete build/install/inspect sequence, and any branch movement blocks. The broker rejects gitfiles, linked worktrees, `commondir`, worktree config, includes, alternates, replacements/grafts, shallow/sparse state, submodules, filters, fsmonitor, hooks, credential/pager/editor/external-diff helpers, ignored or untracked distribution inputs, and every other authority source outside that closure. On this host the receipt must pin the regular single-link `C:\Program Files\Git\bin\git.exe`; PATH discovery and `C:\Program Files\Git\cmd\git.exe` are forbidden because the measured `cmd` image has an unexpected hard-link alias. It invokes that exact `git.exe`/argv with explicit `--git-dir` and `--work-tree`, `--no-pager`, `--no-optional-locks`, and helper-disabling options inside the preventive process rail. Parent/effective-setting `GIT_*` names are absent case-insensitively; only the Git-verifier child receives the schema-pinned broker-created isolation set (`GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_SYSTEM=NUL`, `GIT_CONFIG_GLOBAL=NUL`, `GIT_OPTIONAL_LOCKS=0`, and `GIT_TERMINAL_PROMPT=0`). It proves physical `--show-toplevel`, git-dir, and common-dir results equal the receipt, clean HEAD/tree at the bound attached ref, then recomputes the transitive input and environment manifests. |
| `skill-mesh/phase-is-trust-manifest/v1` | `schema`, project/config final path and identity, trust-record relative path/identity/SHA-256, `trust_bootstrap_result_relative_path`, `trust_bootstrap_result_sha256`, Boolean-true `trusted`, `created_utc`. The strict-schema bootstrap result binds the pre-build receipt, exact mode environment/argv/image and process-tree/quiescence facts, the one allowed trust-record create, protected pre/post snapshot digests, zero project/outside mutation, and redacted proof that no hook/skill/MCP/instruction loaded. The bundle opens the actual trust record/result handle-relatively from the guardian-held roots, remeasures both live root handles, and semantically remeasures that boundary before launch attestation and every later host process. |
| `skill-mesh/phase-is-inspector-proof/v1` | `schema`, exact `state`, integer profile/entry/file/owned/unowned counts, exact `ledger_providers`, fresh/installed manifest SHA-256, zero `difference_count`, exact build/install/inspect result relative paths and SHA-256 values, `created_utc`. Each strict result receipt binds its pre-build receipt, image/argv/environment, source/tool/input closure, process-tree/quiescence/exit facts, and protected pre/post snapshot digests; the install result also binds the held distribution manifest and the inspector result binds its locked inputs. Values are parsed from the pinned inspector result and independently recounted from the locked trees, and every later boundary opens all three process receipts handle-relatively from the guardian-held roots and semantically verifies them. |
| `skill-mesh/phase-is-host-environment-manifest/v2` | Top level is exactly `schema`, `modes`, Boolean-true `ambient_git_authority_variables_absent`, `created_utc`. The mode keys are exactly `trust-bootstrap`, `claude-deny-probe`, `claude-auth-status`, `behavior-row`, `delivery-read-only`, `codex-delivery-read-only`, and `evidence-upload`; aliases are rejected. Each value has exactly an `OrdinalIgnoreCase`-unique, schema-canonically spelled, ordinal-sorted non-secret `NAME=value` array; `runtime_secret_key_name`; exact `runtime_secret_presence` (`required` or `absent`); executable and descendant-image manifest SHA-256 values; a per-mode outside-scratch transport-policy digest; and either the exact static argv or, for `evidence-upload`, the fixed argv prefix plus committed strict argv-schema SHA-256. The transport policy is exactly empty for trust, every Claude mode, and evidence upload. Codex delivery either uses tested isolated Codex state with that same empty policy or binds the one closed real-profile transport policy defined below; no third form is accepted. Secret policy is exactly `none`/`absent` for trust and Codex, `CLAUDE_CODE_OAUTH_TOKEN`/`required` for the four authenticated Claude modes, and `GH_TOKEN`/`required` for evidence upload. Each invocation result binds its exact argv, whether that one secret name was injected, and proof every other secret name was absent without recording a value. `delivery-read-only` additionally binds its pre-generated session UUID and exact new log relative leaf. The fixed `evidence-upload` value binds issue `153`, the uploader image/endpoint, and exactly two ordered invocation kinds (`evidence` then `cleanup`); it deliberately contains no future artifact hash, body-file identity, or expected remote digest. The broker reconstructs each child block from empty and compares it. |
| `skill-mesh/phase-is-effective-hook-manifest/v2` | `schema`, `trust_manifest_sha256`, Boolean-false `disable_all_hooks`/`allow_managed_hooks_only`, exact per-mode map, `created_utc`. Its mode keys are exactly the six host strings `trust-bootstrap`, `claude-deny-probe`, `claude-auth-status`, `behavior-row`, `delivery-read-only`, and `codex-delivery-read-only`; evidence upload is not a host launch and has no hook/settings artifact. Each value binds its distinct immutable settings artifact path/hash plus the complete ordinal-sorted effective event/matcher/type/source/direct-exec `command`/`args`/stdin-schema/hash/precedence set. Every permitted command hook uses the pinned 2.1.223 direct-exec form: an absolute receipt-pinned `.exe` command, exact args array, absent `shell`, no PATH or placeholder expansion, and strict stdin/result JSON grammar. `trust-bootstrap`, `claude-auth-status`, and `codex-delivery-read-only` have no Claude hook; `claude-deny-probe` has only the denying `PreToolUse` guard; `behavior-row` has the exact `PreToolUse`/`PostToolUse`/`PostToolUseFailure` clients for the preventive read/mutation broker; `delivery-read-only` has only that triplet plus its delivery-only `InstructionsLoaded` logger. These clients communicate by an authenticated receipt-bound channel with the already-allowlisted in-job native guard process and receipt-pinned kernel I/O rail. They correlate exact `tool_use_id` plus result bytes; a read handle remains held through its terminal event, and a write capability closes only after its success/failure postcondition receipt. An unmatched, missing, duplicate, or failure post terminates the job and records the exact disposition. The bundle selects the mode artifact by closed argv and re-enumerates these static post-trust facts before launch attestation; this sidecar cannot claim a probe that has not run. If pinned 2.1.223 cannot expose that direct-exec form and result fields, Step 109 stays blocked. |
| `skill-mesh/phase-is-managed-policy-snapshot/v1` | `schema`, effective-input manifest SHA-256/count, exact managed settings/instruction/hook/MCP/plugin/output-style digests/counts, zero `prohibited_surface_count`, Boolean-true `refresh_path_absent`/`startup_bound_before_hooks`, exact transport-only cache exclusions, `created_utc`. The broker remeasures the exact startup-consumed bytes before any executable/delegating surface. |

The fixed `evidence-upload` environment entry is reusable only for those two ordered invocations.
The first invocation result binds the environment-sidecar hash, evidence-attestation schema/hash,
exact body-file handle identity, exact argv, expected remote-body digest, and returned remote record.
The second additionally chains the first publication result and binds the cleanup-attestation
schema/hash, its distinct body-file handle identity, exact argv, expected digest, and returned remote
record. Each result re-reads and digest-verifies its own remote body. Neither prelaunch sidecar nor
either earlier artifact names or hashes a future artifact.

For each Claude host mode, the mandatory non-secret environment subset is exactly these fixed
entries; Step 108P's machine schema adds only the pinned executable's enumerated OS necessities and
the mode-specific fields already named above:

- Isolated roots: `CLAUDE_CONFIG_DIR=<scratch-claude-config>`,
  `CLAUDE_CODE_TMPDIR=<scratch-claude-config>/tmp`, `TEMP=<scratch-claude-config>/tmp`,
  `TMP=<scratch-claude-config>/tmp`, and
  `CLAUDE_CODE_PLUGIN_CACHE_DIR=<scratch-claude-config>/plugins`.
- Fixed value `1`: `CLAUDE_CODE_DISABLE_AUTO_MEMORY`,
  `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`, `CLAUDE_CODE_DISABLE_CRON`,
  `CLAUDE_CODE_DISABLE_AGENT_VIEW`, `CLAUDE_CODE_DISABLE_WORKFLOWS`,
  `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING`, `CLAUDE_CODE_DISABLE_POLICY_SKILLS`,
  `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS`, `CLAUDE_DISABLE_ADOPT`,
  `CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL`, `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`,
  `DISABLE_AUTOUPDATER`, `DISABLE_UPDATES`,
  `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, and
  `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL`.
- Fixed value `0`: `CLAUDE_CODE_FORK_SUBAGENT`, `CLAUDE_AUTO_BACKGROUND_TASKS`,
  `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`,
  `CLAUDE_CODE_ENABLE_BACKGROUND_PLUGIN_REFRESH`,
  `CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE`, and `MCP_DISCOVERY_CACHE`.
- Fixed value `false`: `CLAUDE_CODE_AUTO_CONNECT_IDE` and `ENABLE_CLAUDEAI_MCP_SERVERS`.
- Delivery-only: `SKILL_MESH_UAT_INSTRUCTIONS_LOG` is the receipt-bound absent direct child beneath
  `<scratch-claude-config>` named by that mode; it is absent in the other six environment modes.

`FORCE_AUTOUPDATE_PLUGINS`, `CLAUDE_CODE_PLUGIN_SEED_DIR`,
`CLAUDE_CODE_SYNC_PLUGIN_INSTALL`, and `CLAUDE_CODE_SYNC_SKILLS` are absent in every mode. This is a
mandatory subset, not permission to inherit another key; the broker constructs and validates the
complete mode block from empty.

The readiness receipt schema is `skill-mesh/phase-is-uat-readiness/v1` and must include at least `schema`,
`prebuild_receipt_sha256`, `prebuild_nonce`, `launch_attestation_sha256`, `launch_attestation_nonce`,
`readiness_nonce`, `effective_hook_manifest_sha256`, `deny_probe_result_relative_path`,
`deny_probe_result_sha256`, `fence_bundle_sha256`, and `created_utc`, all strings with the formats
above. The deny result is itself a strict-schema immutable receipt binding the effective hook source,
matcher and command hashes, the harmless requested action, the exact expected denial reason, proof
that the hook—not default permissions—made the decision, the launch receipt hashes, process-tree
result, and zero mutation. Only the receipt-pinned launcher/bundle may create either file with
`CreateNew`; all behavior, authentication, delivery, grade, and cleanup subcommands remeasure them.

Negative tests plant a wrong commit/dirty tree, `core.worktree`, include, fsmonitor command, alternate
object/index, ignored/untracked build input, executable swap, omitted transitive input, extra/missing
environment key, lower/mixed-case `GIT_*`, Claude/MCP/provider/helper names, `Path` plus `PATH`, wrong
physical trust root, wrong inspector count, altered hook source/matcher/hash/precedence, forged deny
result, and nonempty/changed managed policy. Each must fail even when the mutated sidecar or receipt is
self-consistent and re-hashed for the fixture.

**What must hold at an unchanged-writer commit, versus what is pinned to `d4c88ee`.** The exact
figures above — `owned=58`, 128 files, the heading at line `446` — are `d4c88ee`'s and may
legitimately move at a later commit. What must hold in the selected checkout is commit-independent:
`state=present` and `ledger: state=valid providers=[claude]`, the `Select-String` probe *finds*
the heading, and § 2.0's exact writer hashes match. A changed writer requires the full
reverification branch, not an "at or after" assumption.

A recreated home is equivalent to the original: § 1.5 established that the installed profile
is byte-identical to a fresh build at the same commit, so the same commands produce the same
tree. What Step 109 needs is *a* compliant scratch home carrying the current Claude profile plus
its paired isolated config root and receipt-bound build root — not the historical temp directory.
After § 2's behavioral grading and first verified evidence publication, but before Step 109
completes, dispose the three disposable roots only through Step 108P's exact receipt-bound
safe-cleanup subcommand invoked during #153; never derive a cleanup target
from a basename, wildcard, ambient environment variable, or unresolved placeholder.
The cleanup bundle subcommand first proves the full descendant tree quiescent, then resamples each
guardian-held disposable root plus the common creation-parent handle and revalidates
identity/case/non-nesting. It never
reopens a path as identity proof. Before its **first**
delete, it completes a read-only no-follow walk of the entire tree, opens and binds every entry and
parent/child relation, validates the exact receipt/runtime ownership ledger, and establishes the
write/delete freeze needed to keep that inventory stable. Only then does it delete handle-relatively,
refuse reparse or multi-link entries, remove only exact ledger-owned entries, and remove the exact root
last. An anomaly during the validation pass leaves the root intact and reports it quarantined/BLOCKED.
A failure after deletion begins may leave a partially deleted quarantined root; the bundle reports
the exact remaining locked inventory and never claims all-or-nothing deletion, retries broadly,
follows an entry, or widens the target. Negative tests place a nested file symlink, directory
junction, mount point, validation-to-delete swap, and injected mid-delete I/O failure under each root.

Cleanup is forbidden until durable redacted evidence exists. The final grade subcommand first emits
one strict-schema `skill-mesh/phase-is-step109-evidence-attestation/v1` from the locked private
preimages into a receipt-bound absent leaf below `<evidence-export>` using `CreateNew`. It contains no
absolute path, file/prompt/transcript content, environment value, or secret; it chains the fixed
prelaunch receipt/sidecar set and every required pre-grade native result hash, each row's
session/result/core-read/content/action digests and verdict, the Codex exact-payload proof, and the
Claude include proof. It does not name either later publication result or the cleanup attestation.
Step 108P's first `evidence-upload` invocation must
then attach those **exact bytes** and SHA-256 to #153 before the first delete. Its machine-exact
schema and invocation result bind the environment-sidecar hash, retained export-parent/leaf handle,
uploader image and exact argv,
closed environment with process-only `GH_TOKEN`, endpoint and issue number, artifact digest, remote
comment identifier/body digest, successful response, and descendant-tree quiescence. It re-reads the
remote body and proves an exact digest match; hand transcription or an unverified success response is
not evidence. It writes its strict-schema publication result with `CreateNew` under the durable
export root. It must not write or commit the attestation in the receipt-bound source checkout,
because that would dirty or move the locked ref before cleanup.

Because cleanup's outcome cannot honestly be known beforehand, the cleanup subcommand then writes a
second strict-schema `skill-mesh/phase-is-step109-cleanup-attestation/v1` with `CreateNew` to its own
receipt-bound absent leaf under `<evidence-export>`. It chains the evidence-attestation hash, first
publication-result hash, and
records each disposable root's exact `deleted`, `intact-quarantined`, or `partial-quarantined`
disposition. The second invocation of the same pinned upload mode publishes and remotely verifies
those exact bytes and their SHA-256. This fresh post-cleanup invocation/result opens the evidence attestation, first publication result,
and cleanup attestation handle-relatively beneath the still-guardian-held export root; validates
their exact schemas and hash chain; and does not reopen or require any deleted private root. A failed
second upload leaves the local cleanup attestation and first publication result intact in
the durable export root and cannot produce a PASS; it never causes a broader delete or loses the only
copy. Together the two verified public records are the portable attestation chain. Private preimages
may be retained only in an explicitly authorized secure artifact store; the redacted export root is
retained for recovery and is not a cleanup target.

`dist/` is gitignored and was never staged. No other durable artifact was produced by § 1.

## 1.9 Step 108 verdict

**BUILD/INSTALL PASS.** All four acceptance criteria met on the first attempt, no retries. The installed
tree provably carries the current canonical contract — 0 differences against a fresh build at
`d4c88ee` across all 128 files of the profile. Two non-blocking observations recorded (§ 1.6);
neither is a defect this step should have fixed. Step 108's plan status remains certification
pending until this repaired transcript passes independent review and the stable repo-root gate.

**What this step did NOT establish, stated so Step 109 does not inherit it as an assumption:**
that any host actually loads from this tree. Step 108 produced and verified a *tree*; binding
it to a running host is § 2.0's job, and it is not optional.

---

# 2. Step 109 — operator confirmation of all five D10 rows

> **STEP 109 IS BLOCKED BEFORE GRADING.** Its behavioral observations and row verdicts are filled
> in by the **operator** during Step 109 (issue #153) and by nobody else; a pre-execution engineering
> blocker may be recorded during closeout. Selected fixture and filesystem-only components were
> validation-run during Step 108, but no skill was invoked, no host-delivery command ran and no
> D10 row was graded. Do not pre-fill any behavioral observation or row verdict below; § 2.5
> records only the pre-execution engineering blocker. Expected results and commands are
> instruments, not findings.
>
> **This block also depends universally on Step 108 certification.** Step 108P may not replace
> a blocker or create its external-process preparation artifacts, and Step 109 may not grade
> anything, until #152
> records independent review with no high/medium defect on the exact repaired bytes and a clean,
> stable detached repo-root `python -m pytest` whose named sentinel is read as `0` before its log,
> whose pass count meets `documentation/phase-75-baseline.md`, and whose skip count is unchanged.
> This applies to the route-2 plan amendment too. After #162's launcher/bundle/broker/parser code is
> committed, **either** route also requires a new clean stable detached repo-root gate before grading;
> the package-integrity run is only its iteration gate. Route 1 has additional rebuild/equality/RC
> obligations when distribution or core inputs change.
>
> The accepted plan says to run the real named skills. It does not authorize a subsection-only
> mode, and neither installed core exposes one: `plan-init` requires its greenfield conversation,
> save and hooks; `repo-update` defines a full lifecycle whose earlier steps require a real
> repository and whose Step 12 is conditional. It exposes no contract-valid entry point at Step 7,
> and in this deliberately outside-git fixture its first Git command fails before the row under
> test. A bespoke "apply only this subsection" prompt would prove compliance with that override,
> not normal named-skill behavior. **Run no skill or host-delivery command in this section until
> issue #153 records one of two deliberate resolutions:**
>
> 1. Add a core-supported, safety-gated UAT mode. This is a new code step: use § 1.8's
>    receipt-bound preparation with three disposable roots plus the durable evidence-export root;
>    run one guarded `-Provider all -OutputDir
>    <fresh-build-output>` build, and the explicit `-DistDir` install. Then rerun the inspector,
>    equality/heading, reference, and package-gate criteria against those exact bytes (without
>    replaying § 1.2's default output or § 1.5's one-provider builder), derive and receipt-bind the
>    new checkout's exact profile/entry/owned counts and emitted heading location rather than
>    reusing any `d4c88ee` literal, regenerate
>    `documentation/release-candidate-report.md`, and replace § 2.0's four expected hashes from the
>    newly verified install. Because this route changes code, its new preparation step must then
>    clear a clean detached repo-root `python -m pytest` at or above
>    `documentation/phase-75-baseline.md` with the recorded skip count unchanged before grading
>    anything; the package-integrity run is only its iteration gate.
> 2. Deliberately amend Step 109 to accept **operator-scoped named-skill subsection overrides** and
>    their narrower evidence. It may reuse the existing installed bytes only if the committed #162
>    tooling changes are proven outside every distribution input and the applicable package/reference
>    gates are rerun; it still clears the post-code full repo-root gate and requires the native
>    Skill/Base/Profile/attribution proof below. A manual core-file read or non-skill probe is not this
>    option and needs a different plan and proof design.
>
> In either case, #162 must implement, negative-test, and certify a **preventive** containment rail
> after #153 records the route choice and before any host
> session or host-delivery command in § 2 runs: auto memory disabled; project-only settings;
> strict-empty user/project/plugin MCP configuration plus MCP denial; a fail-closed pre-launch
> inventory proving the effective managed MCP configuration is absent or empty; a built-in-tool
> and path allowlist for that exact row; and no shell/process tool. Any configured managed MCP
> server blocks the launch because its process can start outside the row's tool rail. A `PreToolUse`
> hook may implement the path guard,
> but it cannot be the sole availability gate: command-hook timeout, missing/killed helper, exit 1,
> and malformed/empty output may fall through to normal permissions. The selected host-write design
> is an independently OS-admitted, receipt-pinned kernel I/O/minifilter rail: Write/Edit may be
> present in a behavior row, but every file open is denied by default. A successful authenticated
> `PreToolUse` client may install exactly one short-lived capability. PID plus a textual `tool_use_id`
> is insufficient because filesystem I/O does not carry that ID: pinned host instrumentation must bind
> an unforgeable kernel-verifiable per-invocation execution context to the exact writer call and handle.
> Before arming it, the rail proves the host has no pre-existing writable handle to the target. The
> rail serializes or suspends every competing same-PID filesystem mutation for the capability's
> lifetime and tracks the exact granted file object/handle. The capability also binds the host PID, `tool_use_id`,
> operation, receipt-bound parent/leaf or absent-leaf namespace, expected identity/preimage, and
> allowed create/write disposition. The host's own Write/Edit then performs the real operation and
> returns the real tool result; `PostToolUse` or `PostToolUseFailure` atomically closes the grant,
> validates the same object/postimage, and emits the result receipt. The rail mediates create/open,
> every write, truncate, set-information, rename, link, and delete request—not just the first open—and
> marks any retained handle incapable of later mutation before accepting the terminal event. Hooks never synthesize success,
> and a broker-owned mutation followed by a denied native tool is invalid. If #162 cannot name and
> test this exact kernel enforcement, Step 109 stays blocked. Negative-test timeout, absent helper,
> killed helper, exit 1, malformed JSON,
> and empty output; every case must block before bytes change. Exercise ordinary deny cases too before
> the first row. Native action traces remain required
> as secondary audit; inspecting them after an action is not containment. The sole outside-scratch
> write exception is Codex delivery's receipt-bound transport-only policy. Before launch, Step 108P
> must derive it from the pinned Codex grammar and bind in the host-environment manifest every exact
> guardian-held physical cache/session root identity, permitted regular single-link relative-leaf
> grammar, allowed create/replace/append operation, pinned writer image/process identity, and
> kernel-enforced deny-by-default rule. The result records the complete pre/post manifest and exact
> aggregate delta; dynamic leaf names are allowed only through that grammar. No permitted cache may
> carry or later supply semantic memory, instructions, settings, policy, skills, hooks, MCP/plugin
> state, provider/auth selection, source, installed-profile, or project content. The other six modes
> have an empty outside-scratch policy. If that exhaustive preventive boundary is unavailable, use
> tested isolated Codex state with an empty policy or keep Step 109 blocked. Project-only settings do **not** suppress
> managed policy: managed settings outrank lower sources, hooks from effective sources merge, and
> `--strict-mcp-config` does not suppress managed MCP policy. Before launch, the selected resolution
> must enumerate the effective managed/plugin/session hook and settings surface, managed MCP
> configuration, managed skill definitions, and **every effective instruction/rule source** without
> firing a session. That inventory includes the organization-wide managed `CLAUDE.md`, managed
> `claudeMd` content and other managed policy instructions, plus a physical ancestor walk from the
> scratch project through the volume root for `CLAUDE.md`, `.claude/CLAUDE.md`,
> `CLAUDE.local.md`, `.claude/rules/**`, legacy `.claude/commands/**`, `.claude/agents/**`,
> `.claude/workflows/**`, colliding skills, output styles, imports, and dynamic `!` preprocessing.
> The audited built-in default output style must be selected; any custom/effective output-style
> content blocks launch. Disable the pinned host's bundled skills/workflows with the verified
> `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1` child-environment entry; if that setting is unsupported or
> incomplete, inventory/hash the built-in namespace from the pinned executable and prove no
> `plan-init`/`repo-update` collision or automatic invocation before launch. The
> row's root instruction fixture and the
> fence-bundle-pinned, whole-profile-hash-verified project install are the permitted project sources.
> The post-install launch attestation binds the canonical sorted full-profile manifest digest and exact file count,
> and every fresh boundary re-walks and rehashes that entire profile before any host process; four
> writer-file hashes alone are not sufficient because every installed skill description is startup
> metadata. Within
> that installed tree, only `plan-init` and `repo-update` are on the invocation allowlist for this
> UAT. Hash/allowlist every active hook; reject every configured managed MCP server; reject any
> managed or ancestor `plan-init` or `repo-update` definition; and forbid all managed/ancestor-skill
> shell preprocessing or dynamic-context commands. If the host cannot enumerate organization-wide
> managed instruction content before launch, Step 109 stays blocked. Enumeration plus a post-launch
> diff is not preventive if server-managed policy can refresh during startup. Before **every** host
> process, including `claude auth status`, the selected resolution must either prove the pinned host
> has no policy-refresh/fetch path in that launch grammar or bind the exact startup-consumed managed
> policy snapshot before any hook, MCP server, helper, instruction preprocessing, or delegated
> process can fire. If that ordering cannot be observed and enforced, Step 109 stays blocked. If the
> preventive path rail uses hooks, its exact denying pre-hook or paired pre/post native clients and
> the pinned delivery logger are the only command-hook exceptions; with a non-hook permission rail,
> the logger is the sole exception. Every other effective setting or field capable of starting, refreshing, or delegating
> to an external process must be absent — a human review does not make a helper safe. The #162
> packet must derive the exhaustive process-spawning setting list for pinned Claude 2.1.223 and
> reject it, including `policyHelper`, `apiKeyHelper`, `awsAuthRefresh`, `awsCredentialExport`,
> `gcpAuthRefresh`, `otelHeadersHelper`, `processWrapper`, `proxyAuthHelper`, command-backed
> `fileSuggestion`, command-backed `statusLine`, and command-backed `subagentStatusLine`; reject
> `forceRemoteSettingsRefresh` as a separate refresh surface. Every active plugin component is absent,
> including MCP/LSP servers, hooks, agents, monitors, workflows, channels, and persistent background
> processes. Custom agents/subagents, remote-control/cross-session startup, system-prompt injection,
> added directories/tools, and additional plugin directories are also absent. If the host cannot
> provide that pre-launch evidence, Step 109 stays
> blocked.
>
> Use § 1.8's sole pre-attestation trust-bootstrap exception, bind its exact trust record to both
> physical root identities in the immutable launch attestation, close that process, and restart. No
> behavior, delivery, authentication, or other host process may use that exception. A project hook
> present on disk is not evidence that it is active:
> reject `disableAllHooks` and managed `allowManagedHooksOnly` unless the selected design proves exact
> semantics that keep the intended hook effective. Bind the actually effective `PreToolUse`,
> `PostToolUse`, `PostToolUseFailure`, and `InstructionsLoaded` source, command, args, stdin grammar, hash, matcher, and
> precedence as applicable to each mode, then run a harmless denied probe against the pre-hook
> and prove the pinned guard fired and returned the expected reason—not merely that default permission
> handling denied the action. If trust cannot be established without an uncontained startup surface,
> or the exact hook firing cannot be proved after restart, Step 109 stays blocked.
> The effective hook set is closed, not merely reviewed: only the denying `PreToolUse` guard or the
> exact `PreToolUse`/`PostToolUse`/`PostToolUseFailure` clients for the in-job preventive broker, as appropriate to
> the mode, plus the `InstructionsLoaded` logger **only in Claude delivery mode**,
> may exist. Every other event, matcher, source, and hook type—including command, prompt, agent, and
> HTTP hooks—is absent. Each mode uses a distinct receipt-pinned immutable settings artifact selected
> by its closed argv; the static hook manifest binds the full per-mode effective set. Deny-probe
> activates only the denying pre-hook, behavior activates only the three broker clients, Claude
> delivery activates only those clients plus logger, and trust,
> auth, and Codex activate neither. A hook `command` is the absolute pinned native launcher with an
> exact `args` array and strict stdin schema; `shell` is absent. Omitted `args`, shell/Git-Bash/
> PowerShell form, `BASH_ENV` or profile injection, PATH/placeholder resolution, and changed argv are
> blocking negative tests. Negative tests also substitute the delivery artifact into auth/behavior,
> cross-wire any mode's argv/settings hash, and add every hook type; all block before host startup.
>
> Every builder, installer, inspector, authentication probe, behavior/delivery host, Codex
> diagnostic, and evidence uploader must be started by the receipt-pinned native-process broker with an exact child
> environment allowlist; direct `&`, `Start-Process`, or ambient inheritance is not permitted. The
> launch attestation binds each mode's non-secret key/value manifest plus its required or absent
> runtime-secret key name without recording any value. Reject every unrecognized
> Claude/MCP/provider/config/plugin/
> instruction/process-control key from both the parent and effective settings `env` blocks, including
> `MCP_CONFIG_BYTES`, managed/remote/mock-settings paths, additional-directory instruction controls,
> plugin sync/Cowork controls, proxy/helper controls, and every ambient `GIT_*` authority/redirection
> variable. Because Windows environment lookup is case-insensitive, collect and compare every parent,
> settings, and child name with `StringComparer.OrdinalIgnoreCase`, reject duplicate case aliases, and
> match protected names and prefixes case-insensitively; the emitted child block uses one canonical
> spelling per schema. The Git verifier's exact broker-injected null/deny keys are the sole documented
> `GIT_*` exception and never appear in a host or build-tool block.
> The broker constructs a new environment block; a finite clear-list over an inherited environment
> is not evidence.
> It also owns the complete descendant process tree in a Windows Job Object for lifetime/quiescence,
> paired with one exact, preselected and receipt-hashed kernel process-creation policy/interceptor that
> runs before **every descendant's** user code. #162 must name that mechanism and bind its effective
> policy digest; a menu of possible sandbox/WDAC/AppLocker/broker options is not an implementation. A
> Job Object notification alone is post-creation and is not the image gate. The native launcher starts
> direct children suspended as described in § 2.0, while the bound kernel rail applies the same image
> decision to descendants before their image entry point. WDAC/AppLocker may supply only the image
> half; a non-bypassable pre-execution broker/interceptor must also authorize canonical argv and
> environment for every creation path, including WMI, COM, service/task, and other mediated launches
> that do not appear as an ordinary child. The receipt allowlists
> exact absolute image identities/hashes and argv for the intended host plus the explicit guard/logger
> children; current-directory/PATH image search and every other child/grandchild are denied before they
> can act. The broker waits for tree quiescence before
> post-snapshots, result receipts, or cleanup and terminates the job on failure. Negative tests launch
> an unallowlisted child's first instruction attempting a canary write and a grandchild that tries to
> outlive its parent, an allowed image with changed argv/environment, and an approved parent that uses
> WMI/COM/service mediation; detecting or killing any after its code starts is a failure. If the pinned host's exact
> descendant images cannot be preventively gated, Step 109 stays blocked.

**The procedure of record is `documentation/instruction-file-symmetry-plan.md` § 7 Step 109.**
This section records *observations* and supplies the instruments; where the two disagree, the
plan wins and the disagreement is itself worth recording in § 2.4.

**Preconditions.** A newly created, receipt-bound scratch home carrying the Claude profile, a
distinct scratch Claude config root, and a distinct fresh-build output root, all outside the real
user profile — see § 1.8's five-step recreation recipe. The disposable home is
`<scratch-project>` during Step 109; none is a real project, the real home, or an ancestor of the
real home.

**Redaction still applies.** Everything recorded below lands in a public file. Replace
absolute paths with `<scratch-home>` / `<scratch-project>` / `<scratch-claude-config>` before
saving, per the note at the top of this file.

## 2.0 Pre-flight — bind the tree to the host, and prove it bound

**This is mandatory and blocking. Do not grade any row until it passes.** Step 108 verified a
*tree*; nothing in Step 108 proved a host loads from it.

**Why it is blocking, measured on the stale copy rather than argued.** The pre-Step-100 installed
copy this phase exists to displace is still present elsewhere on this machine (26,477 bytes, last
modified 2026-08-09). The mandatory `--setting-sources project` launch excludes that user-source
copy; it becomes eligible only if the flag is omitted or widened. Measured against it with
`Select-String`:

| Probe on the loaded `plan-init/core.md` | Current tree | Stale copy |
|---|---|---|
| lines containing `AGENTS.md` | **34** | **0** |
| contains `## Instruction-file contract` | True | False |
| contains the owner marker | True | False |

And the stale copy's bootstrap guard reads "*skip if a `CLAUDE.md` already exists*". So on
**D10 row 2** (`CLAUDE.md` SUBSTANTIVE) the stale core skips and writes nothing — which is
byte-identical on disk to row 2's Expected "**Touch neither.**" A row 2 graded only on disk
state therefore **reports PASS against the stale tree**, and row 2 is the dominant real-world
case (~32 projects). An accidentally user-enabled launch can therefore false-pass. The exact
project setting source, native base, successful core-read trace, and byte hash below prevent that
launch drift from becoming a row verdict.

**The binding mechanism is documented and already accepted.**
`documentation/host-native-discovery-cutover-plan.md` § "Step 49-50 host-trace amendment
(2026-08-09)" requires a fresh `claude --setting-sources project` session from the consumer
home. The host's native records — not a model claim and not a path the operator merely names —
must show the session `cwd`, a Skill invocation, the tool-supplied `Base directory for this
skill:`, the generated wrapper's `Profile: claude`, and `attributionSkill=<skill>`. That proves
the wrapper binding only. Because supporting files are loaded on access, every row must also show
a complete successful native `Read` of that exact wrapper's co-located `core.md` as the first
post-Skill tool/action event (apart from an exactly enumerated receipt-pinned mechanical wrapper
metadata event), before any other project/config/instruction read, response, delegation, or mutation.
`repo-update` delegates D10 to the sibling `plan-init/core.md`, so its exact order is Skill → complete
`repo-update/core.md` Read → complete `plan-init/core.md` Read → any row/input read. Each on-disk core hash is
then bound to Step 108's expected hash.

These host mechanics are grounded in Claude Code's current primary documentation: project/user
setting sources in [settings](https://code.claude.com/docs/en/settings), supporting-file loading in
[skills](https://code.claude.com/docs/en/skills), auto-memory behavior in
[memory](https://code.claude.com/docs/en/memory), the isolated state root and lifecycle switches in
[the configuration-directory](https://code.claude.com/docs/en/claude-directory) and
[environment-variable](https://code.claude.com/docs/en/env-vars) references, and the event schema in
[`InstructionsLoaded`](https://code.claude.com/docs/en/hooks#instructionsloaded). The settings and
hooks references also establish managed precedence, hook merging, and the fact that a project-level
hook disable cannot override managed hooks; workspace trust controls whether project commands may
run at all. This is why effective pre-launch enumeration plus a positive post-trust hook-firing proof
is a gate.

First validate the exact scratch target in both the observer PowerShell window and the separate
host terminal. Step 108P must replace every blocker with certified subcommands; during #153 the
operator supplies only the recorded creation-time values. Before a replacement can run, it must reject every
non-local/aliased spelling and bind the project/install, config, build-output, evidence-export, and
real-profile directories by both handle-final paths, `FILE_ID_INFO`, and
`FILE_STANDARD_INFO.NumberOfLinks` from one retained handle. Every equality, nesting,
real-profile, Git-ancestry, write-parent, and cleanup decision must use those physical facts; a
`Resolve-Path`/`FullName` string is only a secondary spelling check. The receipt must bind the exact
case-preserved caller spelling and the handle-final facts. The preparation and preflight negative
suite must reject `\\localhost\c$`, SUBST, 8.3, nested-root, under-profile, and case-mismatched
fixtures. If any handle-final, ancestor, or effective case check is unavailable, stay blocked. This
prevents an existing non-git consumer or a substituted project from becoming the serial fixture:

The mutation/launch fence is equally blocking. A hash of a live top-level PowerShell function is
not a fence because its transitive helper functions and captured variables remain replaceable. #162
must instead commit one self-contained fence bundle plus one genuinely native/static minimal
bootstrap launcher—no CLR, script host, sidecar configuration, dynamic DLL search, or unbound
runtime dependency—and
bind both manifests' exact SHA-256 into the schema-v5 receipt. The launcher is the non-recursive trust
anchor. Its separately reviewed `prepare` entrypoint is admitted by the same pre-existing OS rule and
consumes the issue-pinned immutable preparation manifest before any receipt exists. That entrypoint
alone validates the creation parent/real profile/source/fence inputs, creates all four roots
handle-relatively, writes the preparation result and then the binding pre-build receipt with
`CreateNew`, and makes no
other change. Every other entrypoint requires that receipt. Before any PowerShell or bundle
instruction executes, the launcher
opens and locks the receipt, launcher policy, exact PowerShell image, bundle script, helper assembly,
and child environment; passes only the receipt-pinned exact handle set through
`PROC_THREAD_ATTRIBUTE_HANDLE_LIST` (or an equivalent explicit allowlist), marks every other handle
non-inheritable, and consumes only those handles or an immutable byte snapshot;
creates the child suspended; assigns it to a non-breakaway `KILL_ON_JOB_CLOSE` Job Object; verifies
the mapped image, exact argv, and environment; then resumes it. The launcher itself is admitted before
its first instruction by a pre-existing, independently audited OS code-integrity policy with an exact
hash/publisher rule for that image and its complete pre-entry-point PE loader/dependency closure. Its
bootstrap environment and DLL search policy are empty/closed and receipt-bound; recording a digest
without preventive OS enforcement is not sufficient. The launcher's absolute image identity,
SHA-256, version, signer/policy digest, loader-closure digest, and only accepted argv are reviewed and
recorded on #162; #153 records the exact selected invocation values before its one root-of-trust
invocation, and the bundle remeasures the already-effective policy. If that pre-existing admission rule is absent,
Step 109 remains blocked. No script is allowed to verify the bytes
from which that same script has already begun executing. A swap between bundle hash and its first
instruction must fail without executing the swapped byte.
Negative tests place inheritable outside-root file, pipe, process, and token handles in the parent;
neither the direct child nor any descendant may receive or use them.

That immutable generic bundle owns a precompiled native-identity helper assembly,
single-handle identity/final-path sampling, receipt/path/Git/link/case verification algorithms,
immutable root-fact handling, native-executable verification, canonical whole-profile manifest
generation, and argument-grammar validation. It consumes the pre-build receipt plus the later
launch-attestation values; it does not embed those learned values or change after build. The
pre-build receipt and bundle manifest bind both exact relative paths and open-handle identities/
SHA-256 values, plus the launcher's native version/policy/loader closure and the helper assembly's
MVID/version. Runtime `Add-Type -TypeDefinition`
compilation is forbidden: on Windows PowerShell 5.1 it introduces an additional compiler process and
temporary-file surface. The fresh runner must open and lock the helper, hash its bytes before loading
that exact byte array, then use the returned assembly object to verify the same open handle's identity
and assembly metadata; it must not resolve a retained global type by name.

Before every fixture write/removal, snapshot, host process (including authentication), trace/event
parse, delivery-canary write, grade, and cleanup, have the guardian duplicate only the operation's
required retained handles into a fresh receipt-pinned PowerShell process against those hash-checked
bundle bytes. The bundle is the **actual executor**, not a Boolean precheck:
each operation is one schema-versioned subcommand that performs its own checks while holding every
needed handle and emits one redacted result receipt. That process must own the protected operation,
open every relied-on directory without
`FileShare.Delete`, and retain the same handles from identity plus both final-path reads until the
operation and its postcondition checks finish; a parent-side action after a guard merely returns
`True` is not a fence. A handle-relative primitive is required where retaining a root handle alone
cannot bind the mutated child. Require exactly one Boolean `True` only after that owned boundary
finishes; do not resolve a retained live function closure. A live mutator, snapshotter, launcher,
parser, or grader may not consume a validated-beforeward result after the bundle exits.
For every native host boundary, the broker holds no-follow, regular, expected-ID/hash read handles—or
an equivalent kernel-enforced immutable snapshot—for every installed-profile member, executable, and
non-row effective managed/hook/instruction/config input, with child reads shared but writes, delete,
and rename denied until the complete process tree is quiescent. Behavior modes make one narrow
exception for the receipt-authorized root `AGENTS.md`/`CLAUDE.md` leaves whose D10 contract requires
creation or mutation: their reads use the correlated held-handle rail below and their changes use only
the atomic mutation broker with exact pre/post receipts. No other instruction input is mutable.
Claude/Codex delivery, auth, trust, and deny-probe modes permit no project, source, or installed-profile
write and hold every existing root instruction file immutable for their entire child tree. They also
permit no real-profile write except Codex delivery's one manifest-bound transport-only policy above;
all other modes carry its exact empty-policy digest. The broker verifies the started image against
the locked executable and rechecks the same handles afterward. Negative tests attempt in-place overwrite plus restore and path replacement after
hashing for a builder script/module, distribution source, Claude/Codex image, project SKILL/core,
settings/hook, and policy artifact. If a managed/server input cannot be frozen or its exact startup-consumed bytes cannot be
bound before any executable/delegating surface fires, the launch remains blocked.
Mutable source/profile/config inputs remain single-link. An OS-serviced executable such as Windows
PowerShell may use one explicit receipt-pinned multi-link file identity only when the bundle
enumerates every hard-link name, proves each is the expected local servicing alias to that same ID,
locks the handle, matches hash/version, and verifies the started image against it. An unknown or added
link name remains blocking; the exception does not extend to project, source, profile, config, or
bundle artifacts.
This bundle's runner is the process-based path-guard exception named above; no compiler is an implied
exception, and the fence must produce no write outside its receipt-allowed output. Negative tests must
mutate the launcher, runner, or helper; swap the launcher before its first instruction; swap the
bundle after the parent hash but before its first
instruction; substitute the helper after its first probe; preload a colliding type or
assembly name, redefine the former top guard and each former dependency, redefine/substitute every
actual mutator/snapshotter/launcher/parser/grader, replace a captured
root/source/executable value, swap a directory between identity/path probes or between guard and
action, and expose a compiler or outside-root temp write; every case must fail before mutation or
launch. Step 108 publishes no illustrative live-function implementation: every PowerShell fence below
contains one standalone terminating blocker and no later statement. Step 108P must replace each
**entire fence** with the corresponding committed bundle subcommand; changing or bypassing only the
blocker is forbidden.

The same bundle must own every **observer-side** create, replace, append, and delete shown below. A
separate check followed by `WriteAllText`, `AppendAllText`, or `Remove-Item` is a follow/swap window,
not a mutation rail. For a new leaf, the bundle consumes a duplicate of the guardian-held parent
handle and uses `CreateNew` handle-relatively with the exact case-sensitive leaf. For an existing leaf, it opens without following reparse points, holds the
same object locked through the mutation, and verifies its parent identity, exact leaf spelling,
regular-file type, no reparse tag, `NumberOfLinks == 1`, and expected preimage hash before changing or
deleting it. Root disposition uses the same lifetime handle; the guardian does not close it and then
delete a newly resolved path. Host built-in Write/Edit uses the separately selected kernel I/O/minifilter design
above: the authenticated pre-hook installs one exact unforgeable per-invocation physical-object
capability, the native tool
returns its real result, and the success/failure post-hook verifies/closes it. A hook-only allow, a
guard-owned write presented as a failed host tool, or a `PreToolUse` check that releases its handles
before the host writer opens the path remains blocked. Missing/duplicate `PostToolUse` or
`PostToolUseFailure` terminates the job, revokes the grant, records whether bytes changed, and fails
the row. Negative tests race another thread in the same PID, reuse a pre-existing or retained
writable handle after a successful terminal event, and attempt set-information/rename/delete as well
as swapping an
allowed leaf to a file symlink, directory junction, and hard link both before and after the initial
probe, and must fail before any target bytes change.

Every permitted host filesystem read-like operation—read, list, stat, existence test, or glob—and
instruction classification needs an equally handle-coupled boundary. Each row receipt has a closed
target/operation grammar covering its root instructions, any explicitly required fixture such as
`uat-memory.md`, and the exact receipt-pinned installed core reads required by § 2.0. A `plan-init`
row permits its exact wrapper metadata and `plan-init/core.md`; a `repo-update` row permits its exact
wrapper metadata, then `repo-update/core.md`, then delegated `plan-init/core.md`, in that order. Those
profile files remain immutable on whole-session handles and the correlated captured result must equal
their exact bytes; no other skill/profile path is readable. Every other read-like path/tool is denied. For an existing leaf, the preventive
rail opens the exact parent and leaf without following a reparse point, requires the receipt-bound
parent, exact case, regular single-link file, and expected identity/hash, then holds a read-shared but
write/delete/rename-denying handle from `PreToolUse` through the correlated `PostToolUse` result.
Correlation uses the exact `tool_use_id`; the result receipt proves the returned captured bytes/hash
came from that same held handle before release. For an absent leaf or a directory listing/glob, it
holds the receipt-bound parent under a kernel namespace freeze/oplock or equivalent, proves the exact
absence or sorted child set handle-relatively before the tool, correlates the exact not-found/list
result, re-proves the same namespace state, and only then releases it. Any later authorized
`CreateNew` begins after that read boundary closes. An equivalent kernel-enforced read-only snapshot
is acceptable; a lexical path decision followed by the host reopening a name is not. Negative tests
replace or modify an existing file immediately after `PreToolUse` and while `Read` is active, insert a
new symlink/hard-link/regular leaf during an absence/list probe, and swap an outside file into every
allowed fixture path; all must fail without exposing outside or transient bytes. If the pinned host
cannot expose and bind every read-like result this way, Step 109 remains blocked.

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

The Claude executable pin (`2.1.223.0`, SHA-256
`A708BA811C4CC46907DF358E22F2AA6DA3DBC28192747E4D3C4A0869752FE722`) was measured during the post-merge transcript
audit. It prevents an alias/function/path shadow from bypassing the containment arguments; a host
upgrade requires an explicit re-audit and pin update before Step 109 runs.

Keep the observer window open. Capture the two writers' installed bytes before the first row:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

The unchanged-writer route's expected installed hashes are:

| Installed relative path | SHA-256 |
|---|---|
| `plan-init\SKILL.md` | `A1739A4E3D6764AE708404C3B40B74AE34183869C4B62C30AA8FCDA0696EAD9D` |
| `plan-init\core.md` | `054DE3D99002DBA86A9A64C7CC65183B261593E2971F73F9301FF441B0196920` |
| `repo-update\SKILL.md` | `3D101E75745F9E0D8965AE71BDC1B83F726CE7D6A8E4DCC2344740A1CC67597D` |
| `repo-update\core.md` | `B56A59F8373263A4F70CE77E23DB61310A9DC81BE8202881DA83CBB0A2F1AAA4` |

Those four expected hashes were taken from the same installed files whose full 128-file profile
matched the fresh Step 108 build at HEAD in § 1.5. Unlike an `AGENTS.md` substring probe, this
rejects an intermediate core that knew the filename but did not yet implement the matrix.

After issue #153 is unblocked, close the preceding session before each row, manufacture that row
at the root, then start a fresh session from the same validated root. **Run this launch in the
separate host terminal, not the observer window** retained for hashes and fixtures. The selected
resolution must replace the unconditional guard below with its committed, exact ordered argument
list plus verified hashes/content for the empty MCP config and preventive settings/hook artifacts.
That replacement must reject duplicate/unknown flags and every authority-broadening option; a
runtime-supplied array is not evidence. The closed base grammar must include
`--setting-sources project`, `--strict-mcp-config`, the receipt-pinned empty MCP artifact, and
`--no-chrome`; it must not pre-bind `--session-id`. Only `delivery-read-only` may append exactly one
`--session-id` pair whose value is the mode's pre-generated lowercase UUID. It must also bind the pre-launch effective-configuration
inventory, reject every managed/plugin/session hook or setting not explicitly reviewed, and prove
the effective managed MCP configuration is absent or empty. It must enumerate organization-wide
managed instructions (including managed `CLAUDE.md`, managed `claudeMd`, and policy/rule content),
managed skills, and every project ancestor's `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`,
`.claude/rules/**`, legacy `.claude/commands/**`, `.claude/agents/**`, `.claude/workflows/**`,
  same-name skill, output style, import, and dynamic `!` preprocessing surface through the physical
  volume root. Require the audited built-in default output style; reject every custom/effective
  output-style selection or content. Require verified disablement of bundled skills/workflows via
  `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1`; otherwise inventory/hash the pinned executable's built-in
  namespace and reject any writer collision or automatic invocation. Reject
every source except the row's root fixture and the fence-bundle-pinned,
  whole-profile-hash-verified project install. The receipt must bind its canonical sorted manifest
  digest and exact file count, and every fresh process boundary must recompute both before launch;
  allow invocation of only its `plan-init` and `repo-update` writers; reject managed or
ancestor definitions of either writer and every managed/ancestor-skill shell preprocessing path
  before the first Skill invocation. If the pinned host cannot expose any of those sources without
  starting a session, the launch remains blocked. The receipt must also prove that every host process,
  including `claude auth status`, either has no server-managed policy refresh path or consumes the
  exact pre-bound managed-policy snapshot before any hook, MCP, helper, preprocessing, or delegated
  process can fire; a post-launch config diff does not close that startup race. The committed native
  launch broker must construct the receipt-pinned exact child environment from an empty block, with
  no ambient inheritance. Reject every unrecognized Claude/MCP/provider/config/plugin/instruction/
  process-control key in the parent or any effective settings `env` block, including
  `MCP_CONFIG_BYTES`, managed/remote/mock-settings paths, additional-directory instruction controls,
  plugin sync/Cowork and proxy/helper controls. Environment-name uniqueness, protected-prefix
  matching, and parent/settings rejection use `OrdinalIgnoreCase`; case aliases are rejected and the
  child uses one canonical spelling. All ambient `GIT_*` authority/redirection variables are absent
  for builder, installer, inspector, auth, main, and Codex children; only the distinct Git-verifier
  mode receives § 1.8's exact broker-injected isolation set. The same broker must own every
  descendant in a Windows Job Object for lifetime/quiescence **plus** a separate preventive creation
  control with an exact receipt-bound policy digest that intercepts before every descendant's user
  code. The native launcher creates each direct child suspended, assigns the non-breakaway job,
  verifies image/argv/environment, and resumes only an allowed child; the separately named kernel
  rail applies before descendants enter user code. An image-policy mechanism such as WDAC/AppLocker
  supplies only the image half and must be paired with non-bypassable pre-execution canonical
  argv/environment authorization, including WMI/COM/service/task-mediated creation. Together they
  allow only receipt-pinned absolute image
  identities/hashes plus argv, deny current-directory/PATH image resolution and any
  other child/grandchild before it acts, and wait for process-tree quiescence before postconditions.
  A Job Object notification or post-start kill is not the image gate. If that preventive image gate
  is unavailable, launch remains blocked. In addition, enumerate the pinned release's entire
process-spawning settings grammar and require every such value absent across effective sources;
`policyHelper`, `apiKeyHelper`, `awsAuthRefresh`, `awsCredentialExport`, `fileSuggestion`,
`gcpAuthRefresh`, `otelHeadersHelper`, `processWrapper`, `proxyAuthHelper`, `statusLine`, and
`subagentStatusLine` are mandatory absent members; `forceRemoteSettingsRefresh` is a separate
mandatory absent refresh surface. These exact names are still not an exhaustive substitute for the
pinned grammar. Explicit review never
allowlists a startup/background helper. It must reject every settings-file `env` assignment outside
the exact receipt-bound child environment; checking only protected names leaves an injection path.
Use only the
distinct disposable `$ClaudeConfigDir` for settings, plugins, credentials, history and temp state;
for this UAT the only supported authentication path is a process-only
`CLAUDE_CODE_OAUTH_TOKEN`, named only in the four authenticated Claude mode records. It may first be injected
after launch attestation only into the zero-project-write `claude-deny-probe` mode so the real host can reach
and dispatch the harmless tool proposal; all later uses require readiness. A synthetic helper call is
not hook-dispatch evidence. A
pre-attestation or interactive login is forbidden. Never copy, print, or hash the ambient credential
file. The exact child
environment allowlist above is the security boundary: every key not in its receipt-bound manifest is
absent by construction, rather than discovered through an inherited-environment clear-list. Its
negative-test corpus must be generated from the pinned executable's provider-selector,
direct-credential, skip-auth, cloud-chain, metadata, host-auth, file-descriptor, custom-header,
Unix-socket, first-party-base, and endpoint-prefix owner surfaces. The following 107
case-insensitively unique names, plus every name with the case-insensitive `AWS_ENDPOINT_URL`
prefix, are the mandatory regression corpus; they are never an exhaustive substitute for the
closed environment:

```text
ANTHROPIC_API_KEY
ANTHROPIC_AUTH_TOKEN
ANTHROPIC_AWS_API_KEY
ANTHROPIC_CUSTOM_HEADERS
ANTHROPIC_UNIX_SOCKET
ANTHROPIC_FOUNDRY_API_KEY
ANTHROPIC_FOUNDRY_AUTH_TOKEN
AWS_BEARER_TOKEN_BEDROCK
ANTHROPIC_PROFILE
CLAUDE_CODE_OAUTH_REFRESH_TOKEN
CLAUDE_CODE_OAUTH_SCOPES
ANTHROPIC_FEDERATION_RULE_ID
ANTHROPIC_ORGANIZATION_ID
ANTHROPIC_SERVICE_ACCOUNT_ID
ANTHROPIC_IDENTITY_TOKEN
ANTHROPIC_IDENTITY_TOKEN_FILE
ANTHROPIC_SCOPE
ANTHROPIC_WORKSPACE_ID
ANTHROPIC_BASE_URL
ANTHROPIC_AWS_BASE_URL
ANTHROPIC_BEDROCK_BASE_URL
ANTHROPIC_BEDROCK_MANTLE_BASE_URL
ANTHROPIC_VERTEX_BASE_URL
ANTHROPIC_FOUNDRY_BASE_URL
ANTHROPIC_FOUNDRY_RESOURCE
ANTHROPIC_VERTEX_PROJECT_ID
ANTHROPIC_GOOGLE_CLOUD_BASE_URL
ANTHROPIC_GOOGLE_CLOUD_PROJECT
ANTHROPIC_GOOGLE_CLOUD_LOCATION
ANTHROPIC_GOOGLE_CLOUD_WORKSPACE_ID
CLOUD_ML_REGION
CLAUDE_CODE_USE_BEDROCK
CLAUDE_CODE_USE_VERTEX
CLAUDE_CODE_USE_FOUNDRY
CLAUDE_CODE_USE_MANTLE
CLAUDE_CODE_USE_ANTHROPIC_AWS
CLAUDE_CODE_USE_ANTHROPIC_GOOGLE_CLOUD
CLAUDE_CODE_USE_GATEWAY
ANTHROPIC_AWS_WORKSPACE_ID
CLAUDE_CODE_SKIP_ANTHROPIC_AWS_AUTH
CLAUDE_CODE_SKIP_BEDROCK_AUTH
CLAUDE_CODE_SKIP_ANTHROPIC_GOOGLE_CLOUD_AUTH
CLAUDE_CODE_SKIP_FOUNDRY_AUTH
CLAUDE_CODE_SKIP_MANTLE_AUTH
CLAUDE_CODE_SKIP_VERTEX_AUTH
CLAUDE_CODE_SKIP_AWS_CRED_CACHE
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN
AWS_PROFILE
AWS_CONFIG_FILE
AWS_SHARED_CREDENTIALS_FILE
AWS_REGION
AWS_DEFAULT_REGION
AWS_WEB_IDENTITY_TOKEN_FILE
AWS_ROLE_ARN
AWS_CONTAINER_CREDENTIALS_FULL_URI
AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
AWS_CONTAINER_AUTHORIZATION_TOKEN
AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE
AWS_EC2_METADATA_SERVICE_ENDPOINT
AWS_EC2_METADATA_SERVICE_ENDPOINT_MODE
GOOGLE_APPLICATION_CREDENTIALS
GOOGLE_CLOUD_PROJECT
GCLOUD_PROJECT
GOOGLE_CLOUD_QUOTA_PROJECT
GCE_METADATA_HOST
GCE_METADATA_IP
METADATA_SERVER_DETECTION
CLOUDSDK_AUTH_ACCESS_TOKEN
CLAUDE_CODE_HOST_AUTH_ENV_VAR
CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH
CLAUDE_CODE_HOST_AUTH_REFRESH_TIMEOUT_MS
CLAUDE_CODE_HOST_CREDS_FILE
CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR
CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR
CLAUDE_CODE_AWS_CHAIN_RESOLVE_TIMEOUT_MS
_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL
AWS_ENDPOINT_URL
CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST
CLAUDE_CODE_CLIENT_CERT
CLAUDE_CODE_CLIENT_KEY
CLAUDE_CODE_CLIENT_KEY_PASSPHRASE
CLAUDE_CODE_SESSION_ACCESS_TOKEN
CLAUDE_CODE_WEBSOCKET_AUTH_FILE_DESCRIPTOR
CLAUDE_SESSION_INGRESS_TOKEN_FILE
CCR_OAUTH_TOKEN_FILE
CLAUDE_BG_AUTH_SNAPSHOT_PATH
CLAUDE_CODE_SDK_HAS_OAUTH_REFRESH
CLAUDE_CODE_HFI_BEARER_TOKEN
CLAUDE_CODE_FORCE_WINDOWS_CREDMAN
CLAUDE_CODE_CERT_STORE
CLAUDE_CODE_CUSTOM_OAUTH_URL
CLAUDE_CODE_API_BASE_URL
CLAUDE_CODE_OAUTH_CLIENT_ID
CLAUDE_CODE_ARTIFACTS_API_TOKEN
AWS_LOGIN_CACHE_DIRECTORY
AWS_EC2_METADATA_DISABLED
AWS_EC2_METADATA_V1_DISABLED
CLOUDSDK_CONFIG
GOOGLE_API_CERTIFICATE_CONFIG
GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES
GOOGLE_EXTERNAL_ACCOUNT_AUDIENCE
GOOGLE_EXTERNAL_ACCOUNT_TOKEN_TYPE
GOOGLE_EXTERNAL_ACCOUNT_INTERACTIVE
GOOGLE_EXTERNAL_ACCOUNT_OUTPUT_FILE
GOOGLE_EXTERNAL_ACCOUNT_IMPERSONATED_EMAIL
```

A binary change requires re-deriving and receipt-binding the allowlist and regenerating that corpus.
The receipt must also bind the one expected
`authMethod` and `apiProvider`; an intentionally selected mTLS mode must instead pin regular,
unlinked certificate/key files below the isolated config root and update this default-reject list
in the same reviewed change. With the exact isolation environment and
launch root set and the pinned executable hash rechecked, the wrapper must run
`claude auth status`, require exit 0, and parse its default JSON output without recording that
output; `loggedIn` must be Boolean true and its method/provider must exactly equal the receipt.
A check run before containment is established is not evidence. Only the pinned path guard
(if process-based) and pinned delivery logger may execute as processes; there is no settings-helper,
status-line, credential-refresh, or other background-process exception. The
committed `Get-ContainedConfigStateSnapshot` must return a deterministic inventory of every static
or prohibited startup surface under the isolated config root: receipt-pinned settings, hooks, MCP
configuration, custom agents/subagents, output styles, legacy commands, and authentication-mode
configuration. Every plugin is inactive and its MCP/LSP, hook, agent, monitor, workflow, channel,
remote-control, and persistent-background components are absent. The closed launch grammar rejects
custom-agent, system-prompt injection, additional-directory/tool, additional-plugin-directory,
remote-control, and cross-session startup flags or settings. It may exclude only an enumerated
allowlist of transport-only history, transcript, cache, and temp artifacts. No cache carrying
settings, managed policy, instructions, skills, hooks, MCP/plugin definitions, output styles, or
provider/auth selection may be excluded; the exact startup-consumed managed-policy artifact remains
hashed and receipt-bound. It must return at least one receipt-bound invariant record; an empty snapshot is not
evidence. The wrapper compares that inventory before and after every launch and revalidates the
same containment receipt after the process exits. The current blocked skeleton cannot launch:

The committed bundle's native-launch subcommand—not a live function—returns exactly one
schema-bound result with: mode; all applicable receipt hashes (pre-build only for trust-bootstrap,
pre-build plus launch attestation for `claude-deny-probe`, and all three for every later pre-cleanup
host, grade, cleanup, and first-upload mode). The fresh post-cleanup upload instead binds the durable
evidence-attestation, first-publication-result, and cleanup-attestation hashes;
executable, argv, exact-environment, and descendant-image manifest hashes; physical launch
root identity; `started`; exit code; process-tree count/digest; `quiescent`; protected pre/post
snapshot digests; and one mode-specific redacted proof digest. Auth JSON and Codex prompt JSON are
parsed inside that same pinned subcommand and never returned raw; the mode proof carries only the
required method/provider or exact normalized project-payload hash/equality fields. A delivery result
also binds the held instruction-handle identities/hashes. Any unknown/missing/duplicate field,
unallowlisted descendant, non-quiescent tree, or mismatched receipt makes the subcommand nonzero.

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

Stale same-named `plan-init` and `repo-update` skills exist in the personal
`~/.claude/skills` root and would be eligible under the default user + project + local sources.
The mandatory project-only setting source excludes them; do not omit or widen it. Leave them
untouched. Never install this profile into the real home to make the scratch copy win: on this
host that junction target contains 1,235 tracked files, and the existing ownership ledger lets a
reinstall overwrite owned files silently without `-Force`, backup, or prompt.

Project-only settings do **not** outrank managed skills. A managed same-name writer can win before
the native Base/core parser rejects the result, and managed-skill dynamic-context shell commands can
run during preprocessing outside the ordinary tool rail. The #162-certified pre-launch inventory must
therefore prove both writer names absent from the managed skill surface and reject any managed skill
shell-preprocessing path; post-invocation attribution is too late to contain either case.

For **each** writer invocation, capture that row's own native record. Set the `HostSupplied*`
values below from that record, never from the intended directory. One successful `Read(path)` is
not enough: every required core's Read result must start at line 1, reach the expected final line,
contain the skill-specific terminal line, carry no truncation marker, and reconstruct to bytes
whose SHA-256 equals the verified co-located core under #162's pinned native-payload normalization.
Every one of those Reads must occur in that exact prefix before any other read or action:

**The requirements below are prose, not a hand-entered shape-check implementation or mechanical
ordering proof.** Step 108P must replace the terminating blocker with a committed parser over one
native session record. That
parser must bind the session/transcript identity, invoked skill name, host-supplied native Base,
generated-wrapper `Profile: claude`, matching `attributionSkill`, and every required successful Read.
For `plan-init`, the complete core Read is the first post-Skill tool/action event except exact
receipt-pinned mechanical wrapper metadata. For `repo-update`, the prefix is exactly Skill, complete
repo-update core Read, complete delegated plan-init core Read, then any row/input read. It must reconstruct each complete captured
Read payload under a pinned normalization rule and compare its SHA-256 to the corresponding
verified on-disk core; merely computing or recording a payload hash is not equality evidence. Its
unchanged-writer route uses these exact completion predicates:

| Core | Lines | Exact terminal line |
|---|---:|---|
| `plan-init/core.md` | 678 | `block plan-init's completion.` |
| `repo-update/core.md` | 571 | ``This re-derives verbs/ports from the current `CLAUDE.md` + plan and regenerates the `dev.code-workspace` tasks. Keep README/CLAUDE.md command + port mentions scrapable.`` |

Negative tests must mutate one middle payload line, move each core behind an otherwise allowed
`AGENTS.md`/`CLAUDE.md` Read, and on a `repo-update` record swap or delay only the delegated
`plan-init` Read; every case must throw. Until that parser and its negative tests land, the fence
remains only the blocker below; no manual path/full/captured/on-disk-hash implementation is
published here.

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

**Expect after #162 replaces the blocker:** the ordered native-record parser passes, followed by
`True` for the exact wrapper base and one all-true path/full/captured/hash row for `plan-init` on
rows 1–2. Rows 3–5 require two all-true rows: `repo-update` and the sibling `plan-init` owner it
cites for D10.
A complete `repo-update` read alone does not deliver the delegated contract. No row may borrow
another session's record. If a future UAT-mode change moves a count or terminal line, § 1 must be
rerun and this block updated together with the four hashes.

After the last row:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

**Expect:** no output. Any binding mismatch or changed installed byte blocks Step 109 rather
than failing a D10 behavior.

- Per-row session `cwd`, Skill/Base/Profile/attribution records: *(operator)*
- Per-row base/core-read/hash results (`True` / `False`): *(operator)*
- Post-observation installed-byte comparison: *(operator)*

## 2.1 The five D10 rows

> **Every row runs serially at the validated `<scratch-project>` root.** Close the preceding
> host session, reset only the two root instruction files, and start a fresh session from that
> same root before each row. Do not use child row directories or a project pin: host discovery
> and the writer target must coincide.

Once unblocked, the skeleton exercises **one writer contract surface per row**, i.e. 5 of
canonical D10's 10 cells. Rows 1–2 target `plan-init`'s `## After plan.md exists`; rows 3–5 and
the fixed-point check target `repo-update` Step 7. Every authorized action must request the seven
canonical standalone fact lines in the checker below verbatim. Their presence is only a structural
corroboration: a line can still sit inside a negation or false example. The native grader may not
turn presence alone into PASS; the operator must read each section in context and record whether the
line is asserted affirmatively as a project fact.

**There is intentionally no invocation text here while Step 109 is blocked.** The selected
resolution must supply a copy-ready, contract-valid literal for every action and state whether it
tests a core-supported UAT mode or a deliberately narrower named-skill subsection override. A bare
`/repo-update`, or a prompt that silently contradicts the current core's required steps, is not a
substitute. Any action outside the row allowlist is blocking evidence, not a D10 failure.

| Row | `AGENTS.md` | `CLAUDE.md` | Contract surface | Expected | Observed | Verdict |
|---|---|---|---|---|---|---|
| 1 | ABSENT | ABSENT | `plan-init` | Author `AGENTS.md` (the seven sections listed under `plan-init/core.md`'s `## After plan.md exists` section); write `CLAUDE.md` as D8's exact pointer bytes | *(operator)* | *(operator)* |
| 2 | ABSENT / POINTER | SUBSTANTIVE | `plan-init` | **Touch neither.** Report the project non-inverted | *(operator)* | *(operator)* |
| 3 | SUBSTANTIVE | POINTER *(inverted)* | `repo-update` | Refresh `AGENTS.md`; leave `CLAUDE.md` untouched | *(operator)* | *(operator)* |
| 4 | SUBSTANTIVE | ABSENT | `repo-update` *(chosen here; D10 gives both writers an identical cell)* | Refresh `AGENTS.md`; write `CLAUDE.md` as the D8 pointer | *(operator)* | *(operator)* |
| 5 | SUBSTANTIVE | SUBSTANTIVE *(drift)* | `repo-update` | Refresh **neither**; emit the P2 advisory naming both paths; **continue without blocking** | *(operator)* | *(operator)* |

### Fixtures — how to manufacture each row's starting state

**Run in:** `<scratch-project>` · the observer Windows PowerShell 5.1 window retained from
§ 2.0. Run one row at a time; record its observations and close its host session before
resetting the root for the next row.

The fixture mutator must create strict UTF-8 without a BOM and with LF only. In the following escape
notation, each `\n` denotes one LF byte and no backslash is written. The accurate SUBSTANTIVE bytes
are `# Scratch\n\n## Stack summary\n\nMarkdown. UAT preservation canary: keep this line.\n`.
Row 5's conflicting `CLAUDE.md` bytes are
`# Scratch\n\n## Stack summary\n\nConflicting non-Markdown stack.\n`. Rows 2–5 use those
preimages exactly as the table above specifies; POINTER is D8's exact 11 bytes.

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

**Expect, before the corresponding fresh host session:** `ABSENT/ABSENT`,
`ABSENT/SUBSTANTIVE`, `SUBSTANTIVE/POINTER`, `SUBSTANTIVE/ABSENT`, then
`SUBSTANTIVE/SUBSTANTIVE`.

**Historical scope of the validation run.** The pre-hardening direct-write harness produced those
five state pairs in Windows PowerShell 5.1; its state-pair/text/hash logic was exercised. Instrument
A's earlier two halves were run separately against unchanged and changed states, and Instrument B's
earlier predicate was self-tested against the five manufactured post-skill pointer states listed
below rather than concatenated after the empty row-1 fixture. The receipt-pinned atomic mutator,
fresh-process executor, chained receipts, and handle locks now specified as Step 108P contracts were
neither implemented nor run; the executable fence above is only the terminating blocker. No skill
was invoked and no D10 row was graded.

### Instrument A — did the skill touch a file it must not touch?

Rows 2–5 assert "touch neither", "leave `CLAUDE.md` untouched", or "refresh neither" for at
least one path. Instruction-file hashes grade content, a protected-root manifest catches other
filesystem changes, and the native action trace catches a forbidden byte-identical rewrite.

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

For row 5, create the absolute memory target in its subsection below **before** taking this
pre-action snapshot. Once #153 records the route and #162 supplies its certified authorized action,
run it in the separate host
session. Keep the observer window open, then run the post-action half separately:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

**Expect:** the protected-root comparison prints nothing on every row. The instruction comparison
shows row 1 adding both files; rows 2 and 5 print nothing; row 3 changes only `AGENTS.md`; row 4
changes `AGENTS.md` and adds `CLAUDE.md`. Capture both preimages for every row; § 2.2 separately
takes row 3's post-first-pass snapshot.

The preventive tool/path rail must have denied every non-allowlisted action before execution.
Also audit that invocation's native tool-action trace. For every Write/Edit target, preserve the
native spelling's case, open its existing parent by handle, require that parent's handle-final path
and file ID to equal the receipt-bound project root, and require the leaf name to be exact
case-sensitive membership in `$AllowedWrites`. If the leaf exists, open it without following reparse
points and, on the same handle held through the mutation, require a regular file with no reparse tag,
`NumberOfLinks == 1`, the exact expected preimage hash, and the receipt-bound parent identity. If it
does not exist, creation must use `CreateNew` through the bound parent. `[IO.Path]::GetFullPath()` and
textual membership in `$AllowedWritePaths` are secondary checks only; any shell/process action, case
mismatch, aliased parent, linked/multi-link leaf, released-handle check-then-write, or write outside
that physical allowlist blocks the row. Negative tests must swap each allowed leaf to a file symlink,
directory junction, and hard link on either side of the first probe.
Rows 2 and the fixed-point pass allow no write action at all. This trace requirement is what
catches an otherwise invisible byte-identical rewrite or a write-then-restore sequence.

### Instrument B — is `CLAUDE.md` D8's *exact* pointer bytes?

Rows 1 and 4 assert the pointer is written as **exactly** one line plus an LF. Text decoding would
hide an encoding preamble and normalize the question into characters, so this compares raw bytes.
Run it **after** the row's skill has written `CLAUDE.md`; the starting row-1 and row-4 fixtures
intentionally lack that file.

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

**Expect:** `True`. The only accepted bytes are ASCII/UTF-8 `@AGENTS.md` plus LF (11 bytes;
SHA-256 `336CC4FBF19BEAADA7CCF9986414FA91851A8D7A07DFB3CCBE800A69EED0AB49`). The negative
self-test rejects CRLF, UTF-8 BOM, UTF-16, missing newline, a trailing blank line, and extra content.

After rows 1, 3 and 4, require each of these seven canonical headings exactly once and in canonical
relative order, while permitting additional legitimate sections. Each exact fact line must occur as
prose inside its named canonical body, before the next level-2 heading:

| Canonical heading | Exact structural fact line |
|---|---|
| `Project overview` | `Project kind: documentation-only UAT fixture.` |
| `Stack summary` | `Primary format: Markdown.` |
| `Key commands` | `Production commands: none.` |
| `Directory layout` | `Instruction outputs: root instruction files only.` |
| `Architecture summary` | `Application architecture: none.` |
| `Current state` | `Current state: UAT-only.` |
| `Environment requirements` | `Required shell: Windows PowerShell 5.1.` |

The `Stack summary` body must also contain exactly one occurrence of these three consecutive lines:

1. `| Component | Value |`
2. `|---|---|`
3. `| Primary format | Markdown |`

The `Directory layout` body must contain exactly one occurrence of these five consecutive lines:

1. ```` ```text ````
2. `.`
3. `|-- AGENTS.md - project instructions`
4. `` `-- CLAUDE.md - @AGENTS.md pointer ``
5. ```` ``` ````

A hash delta or heading list alone is not proof of the required section walk, while the fact-line
check is not proof of its surrounding prose's semantics; both mechanical structure and the
operator's contextual affirmative-reading observation are required.
Rows 3 and 4 must also preserve the exact line planted in their already-accurate stack section:
`Markdown. UAT preservation canary: keep this line.`

The committed grader reads and hashes bytes from the same no-follow, regular, single-link handle held
through grading. It accepts only strict UTF-8 **without** a BOM, NUL, carriage return, or invalid
Unicode; fixture and writer output therefore use LF only. `[IO.File]::ReadAllText` is forbidden
because its default decoder replaces malformed sequences. Negative tests insert an invalid middle
byte, BOM, NUL, lone CR, CRLF, and a path/in-place swap after the handle opens; each must fail. This
paragraph documents the byte predicate; no path-read implementation is published here. #162
replaces the terminating blocker below with the certified handle-owning bundle subcommand.

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

**Expect (structural only):** all seven canonical headings exactly once and in relative order; any commented,
raw-HTML, indented-code, or fenced-heading facsimile; missing exact fact line; absent stack table
or annotated directory tree; duplicate or relatively reordered canonical heading; placeholder; or lost preservation canary
throws. A negated or example-wrapped fact can still satisfy that structural check and therefore
requires an operator-recorded semantic failure rather than a mechanical PASS.

### Row 5 has two independent claims

After `Set-RowFixture 5` and before Instrument A's pre-action snapshot, create one scratch-only
Step 8 target and record its preimage. The target is the absent direct child `uat-memory.md`; create
it atomically as strict no-BOM LF-only UTF-8 with exact bytes
`# UAT memory\n\n## Status\n\nBefore row-5 continuation.\n`, where each `\n` denotes one LF
byte and no backslash is written. Bind its regular single-link identity and pre-action SHA-256:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

Once Step 109 is unblocked, the selected resolution must provide an authorized slice that begins
at Step 7 and whose safe boundary ends immediately before Step 9. Supply the **absolute**
`$Row5Memory` as `MEMORY_FILE`, phase text `Phase IS Step 109 row 5 continuation observed`, issue
#153, final test count unknown, no discrepancies and overall UAT pending. Do not tell the agent to
"continue" or state that Step 8 must happen: the core's natural Step-7-to-Step-8 transition is the
property under test. Step 8 is allowed to write only `$Row5Memory`. Afterward:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

The two postcondition booleans mean, in order: the held file's SHA-256 differs from its bound
preimage, and its strict-decoded bytes contain the exact text
`Phase IS Step 109 row 5 continuation observed`.

**Expect:** `True`, `True`. Record the two contract claims separately:

- The P2 advisory **printed**, and named both paths — record the two *filenames*, redacting
  any leading path to `<scratch-project>`: *(operator)*
- The run **continued** — the native action trace shows the advisory before the Step 8 memory
  write with no intervening halt or prompt, then stops at the UAT boundary: *(operator)*

Do not inject an echo token as proof; a model can print one whether or not the core's advisory
would have blocked its natural transition.

### Row 2 has two behavioral claims; neither proves host binding

This is the row § 2.0 exists for. Record the two halves separately:

- **On disk — touched neither** (Instrument A prints nothing): *(operator)*
  *Non-discriminating on its own: the stale core also writes nothing here.*
- **In the report — stated the project is non-inverted**, in terms that name `AGENTS.md`:
  *(operator)*
  *Record this as behavior, not delivery evidence. A model can produce plausible words without
  the intended core; row 2 is gradable only because § 2.0's native host record proves the exact
  scratch wrapper, the successful co-located core read, and the expected core bytes for this
  invocation.*

## 2.2 Fixed-point check (representative row 3)

The plan calls rows 3 and 4 fixed points and requires one second `/repo-update` pass, so row 3
is the representative. Do not grade the second pass unless the first row-3 pass already changed
`AGENTS.md`, left `CLAUDE.md` byte-identical, and passed its binding record; two runs that both
did nothing are not a fixed point. The baseline, second invocation, and grader bundle receipts must
all bind the same row-3 session identity plus all three immutable UAT receipt hashes.

**Run in:** the same fresh row-3 host session, immediately after the first pass and before any
fixture reset. In the observer window, take a new post-first-pass baseline:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

Do **not** use a bare `/repo-update`; that starts the current full lifecycle. After issue #153
records its resolution, paste the exact same authorized row-3 invocation literal a second time in
the host session. Until that literal exists, this check remains blocked.

Finally, in the observer window:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

**Expect:** no output from either comparison, and no Write/Edit or shell/process action in the
second invocation's native trace. Capture that invocation's own native binding record before
assigning the verdict.

- Second-pass `Compare-Object` output: *(operator)*
- No-op confirmed: *(operator)*

## 2.3 Delivery on both hosts

The contract is only real if the bytes reach the model. Once Step 109 is unblocked, run both
checks on the completed and fixed-point-graded row-3 state at the validated root before resetting
it for row 4. First add a delivery-only random canary, after all row-3 behavior measurements:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

### Codex — decisive, and documented

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

**Expect:** the receipt-bound normalized AGENTS.md SHA-256 and `EXACT`. Step 108P must commit a
schema-pinned parser for Codex 0.147.0's JSON that identifies exactly one project-instruction record
for this physically bound `AGENTS.md`, reconstructs its entire payload, applies only the audited
UTF-8 BOM/CRLF normalization above, and compares exact content plus SHA-256 without printing the
payload. Canary/heading substrings are corroboration only: they cannot exclude a truncated,
transformed, duplicated, or stale payload. Parser negative tests must mutate a middle line, truncate
the tail, prepend/append content, duplicate the record, and relabel an ancestor/global record as the
project record; every case must fail.

**What Step 108 did and did not verify here.** The former two-substring predicate was exercised in
Windows PowerShell 5.1 against controlled input, then rejected during review because it could
false-green partial delivery. The post-merge audit pinned the `codex.cmd` discovery shim and the complete two-file native vendor bin,
then invokes the pinned `codex.exe` directly; Node, `codex.js`, aliases and functions are not in the
execution chain. The full prompt-input command was **deliberately not run**: it is Step 109's
action, it reaches the Codex backend, and Codex-home background churn makes individual cache
changes unattributable to one command. Controlled reproductions observed no project-directory write
and no persisted `-c` override; no per-invocation Codex-home file count is published. That observation
is not the Step-109 rail: #162 must either use tested isolated Codex state or enforce the exact
manifest-bound transport-only exception above, reporting only its complete session-window aggregate
delta. In both cases it must provide a receipt-bound project-read-only boundary, no project
writer/action capability, a native process/file-action audit, and the exact pre/post project and
instruction comparisons above. If the pinned Codex diagnostic cannot run inside that boundary, the
delivery check remains blocked.

**Record the expected/actual normalized project-payload hash, exact-equality verdict, heading, and
canary — never the full prompt-input dump.** That
payload also carries Codex's base instructions and any global instruction content under the
Codex home, so publishing it verbatim publishes more than the project. Redact any path to
`<scratch-home>` / `<scratch-project>` / `<scratch-claude-config>`.

- Observed: *(operator)*

### Claude — fresh-session import event

The `@AGENTS.md` import inside the `CLAUDE.md` pointer must resolve and expand. This is the
harder half to instrument honestly. Close the row-3 writer session and start a new delivery-only
session with the same fail-closed launch wrapper, auto-memory disablement, project-only source,
strict-empty MCP configuration, verified-empty managed MCP policy, and preventive tool/path rail
from § 2.0. Before invoking a skill or opening either instruction file through a tool, `/context
all` may corroborate the loaded project-instruction set.

The decisive native evidence is a **new** `InstructionsLoaded` event bound to a known fresh session.
Step 108P must supply and negative-test exactly one delivery-scoped
`InstructionsLoaded` handler with matcher `include`. Its pinned logger must validate the canonical
disposable config root and session-shaped direct-child filename, then write one compact JSON record with
`FileMode.CreateNew`; it must never append or overwrite. Pin its absolute native direct-exec image,
exact args, stdin grammar, and loader closure; no script/shell/PowerShell chain is allowed. This
logger, plus the exact paired path-guard clients only in their permitted modes, is the
complete hook-process allowlist. Prepare the absent config-root log path and launch identity before
that session. Delivery is a separate **zero-project-write** containment mode, not a reuse of a
behavior row's write allowlist: its receipt must deny Write/Edit and every project mutation. The
pinned logger is the sole hook-authorized config-root writer in this proof and may create only that
one leaf. The native host tool-action record must contain no Write/Edit or other project-mutation
action. Hash both
instruction files and snapshot the protected project root immediately before launch, then require
the same hashes and the entire project snapshot immediately after process exit with no exclusion.
The config snapshot permits only its already-enumerated host transport artifacts plus the exact new
logger leaf. Because the event reports a lexical path rather than content bytes, the
native launch broker must also open `CLAUDE.md` and `AGENTS.md` without following reparse points,
verify on those handles the exact parent/file identities, regular-file type, no reparse tag,
`NumberOfLinks == 1`, and expected hashes, and hold both handles with read sharing only (denying
write/delete/rename) for the entire delivery child and logger-close interval. Negative tests attempt
replace/symlink/hard-link swaps during that live window and must fail. The include event is grading
evidence only inside that locked unchanged-byte interval:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

After closing the fresh session, require exactly one newly logged include event with the session
identity, cwd, and import parent all bound to this fixture:

```powershell
throw 'BLOCKED: Step 108P (#162) must replace this entire illustrative fence with its certified receipt-pinned subcommand.'
```

The random absent path plus create-new logger excludes stale writer-session evidence. The exact
session, canonical cwd/file/parent paths, and regular transcript below the disposable config root
bind the event to the already-verified canary-bearing file and D8 pointer; `/context all` is
corroboration, not a substitute.

**Do not grade this row by asking the model a question about the project and judging the
answer.** This repository's own delivery doc rules that out: "a model can answer plausibly
with no instruction file delivered at all, so the answer is not evidence and the prompt
payload is."

**Honest limitation, recorded rather than papered over:** this instrument was not executed by
Step 108, and an import that fails to expand looks identical in the pointer file itself. If the
exact `InstructionsLoaded` event is unavailable, mark this check **NOT MECHANICALLY VERIFIED**,
not PASS.

- Fresh-session `cwd`: *(operator)*
- Exact `InstructionsLoaded` event fields: *(operator)*
- `/context all` corroboration: *(operator)*

## 2.4 Behavioral differences and operator notes

*(operator — record every divergence between what a core's prose instructs and what the agent
did, including ones that did not change the on-disk result. A prose contract that an agent
reliably misreads is a finding even when the output happens to be right. This is also where a
disagreement between this section and the plan's Step 109 belongs, and where a § 2.0 binding
failure is recorded.)*

Optional, if it is cheap in the moment and not required by the Done-when: D10 row 2's
*`repo-update`* arm ("refresh `CLAUDE.md` in place, exactly as today; never create
`AGENTS.md`") is the dominant real-world case — roughly 32 projects — and § 2.1 row 2
exercises only the `plan-init` arm. An observation of it would be useful; its absence is not a
gap against the plan.

## 2.5 Step 109 verdict

**BLOCKED BEFORE GRADING (Step 108 closeout).** The accepted Step 109 asks for real named-skill
behavior, but neither current core supplies a safe instruction-file-only UAT mode and a normal
`repo-update` cannot safely reach Step 7 in this outside-git fixture. Issue #153 must record either
a core-supported mode or a deliberate plan amendment accepting operator-scoped named-skill
subsection overrides. Until then every Observed/Verdict cell stays blank, no host session or
host-delivery command in § 2 runs, and this is not a D10 failure.

- Resolution selected: *(operator)*
- Operator UAT verdict after resolution: *(operator)*
