<!-- REDACTION NOTE. Machine-specific absolute paths are replaced throughout by these
     placeholders, and an appending author must keep using them — this is a public repository
     and tests/package-integrity/test_manifest_contract.py::test_no_absolute_private_paths_committed
     sweeps every tracked AND untracked-but-not-ignored text file for absolute user paths:

       <scratch-home>          the disposable install home (see § 1.8)
       <scratch-project>       the disposable project Step 109 runs against (see § 2)
       <fresh-build-output>    the throwaway build directory used by § 1.5's comparison
       <repo>                  this checkout's absolute path, where it appeared in tool output

     One token needs care. In §§ 1.5-1.6, `<repo>/_shared/<leaf>` is NOT a redaction — it is
     the LITERAL string canonical cores use to cite the vendored shared payload, and § 1.6 O2
     is specifically about that literal being rewritten at emit time. Read it as source bytes,
     not as a hidden path. -->

# Instruction-file symmetry — build, install and UAT transcript

**Status: § 1 (Step 108) is COMPLETE and verified — every command in it has been run in the
shell it is attributed to, and its result recorded. § 2 (Step 109) is an UNEXECUTED operator
skeleton — no command in it has been run, and no verdict in it may be pre-filled.** Do not
redo § 1; do not read § 2's blank cells as results. § 2's `Expected` column and its commands
*are* authored in advance, deliberately — those are the instruments, not the findings.

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
current tree; it did **not** prove any host loads from it, and it could not — that is a host
behavior outside this repository. § 2.0 therefore opens with a mandatory pre-flight that
settles it empirically before any row is graded, because without it D10 row 2 would report
PASS against the stale tree. See § 2.0 for the measurement behind that claim.

---

# 1. Step 108 — build and install into a scratch home

**Run date:** 2026-08-26
**Executed in:** a `skill-mesh` git worktree at `d4c88ee` ("checkpoint: step 107 code landed
— vendor the codex measurement (#151)"), with no modified tracked file at any point during
the run.
**Scratch home:** a disposable directory named `step108-home`; see § 1.8 for where it lives
and how to recreate it. It was empty before the run. **The operator's real home was never a
target** — no command in this transcript names it.

Nothing outside the worktree and the session scratchpad was written. `dist/` is gitignored.

## 1.0 Shell contract

**Every fenced command in § 1 is Windows PowerShell 5.1**, and every one was executed in that
shell. Commands are spelled `powershell`; PowerShell 7 (`pwsh`) is not installed on this
machine.

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

Both were replaced with PowerShell 5.1 forms, and the replacements were **run**, not merely
written; § 1.5 records their output. Where a figure below was originally obtained with a POSIX
tool under Git Bash, it was re-measured in PowerShell 5.1 for this record and the two agreed.

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

Run in: the `skill-mesh` worktree · Windows PowerShell 5.1.

```
powershell -File tools/build-distributions.ps1 -Provider all
```

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

Run in: the `skill-mesh` worktree · Windows PowerShell 5.1.

```
powershell -File tools/install-skill-mesh.ps1 -Provider claude -Home <scratch-home>
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

Run in: the `skill-mesh` worktree · Windows PowerShell 5.1.

```
powershell -File tools/inspect-host-install.ps1 -Home <scratch-home>
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

Run in: the `skill-mesh` worktree · Windows PowerShell 5.1. Two steps: rebuild the claude
profile from canonical source into a throwaway directory, then compare the two trees by
content hash.

```
powershell -File tools/build-distributions.ps1 -Provider claude -OutputDir <fresh-build-output>
```

**Exit code: 0** (`claude -> <fresh-build-output>\claude (57 skills, 128 files)`). Preconditions
recorded at run time: `HEAD=d4c88ee`, and `git status --porcelain --untracked-files=no` empty,
so the rebuild is from HEAD source with no local modification.

```
$Fresh     = '<fresh-build-output>\claude'
$Installed = '<scratch-home>\.claude\skills'

function Get-TreeManifest($Root) {
  Get-ChildItem -LiteralPath $Root -Recurse -File | ForEach-Object {
    '{0}  {1}' -f $_.FullName.Substring($Root.Length + 1),
                  (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
  } | Sort-Object
}

$delta = Compare-Object (Get-TreeManifest $Fresh) (Get-TreeManifest $Installed)
if (-not $delta) { 'IDENTICAL' } else { 'DIFFERENT'; $delta }
```

Observed output:

```
fresh files=128  installed files=128  differences=0
RESULT: IDENTICAL
```

Relative path **and** SHA-256 are compared for every file, so this catches a renamed file, a
missing file and a changed byte alike. One command covers **all 57 installed skills**, so it
covers every skill Steps 100–106 edited — `plan-init`, `repo-update`, `build-observer`,
`citation-review`, `goblin-suggest`, `research-prospect`, `review-uat`, `user-brainstorm`,
`user-learn` and `context-slim` — rather than proving currency for one of them.

This matters concretely for Step 109: the plan's Step 109 assigns `/repo-update` to **rows 3
and 5** (row 4 it assigns to neither writer), so an install stale at Step 102 (#146) — the
commit that implemented the `repo-update` D10 column — would make those rows report PASS
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

Run in: the `skill-mesh` worktree · Windows PowerShell 5.1.

```
Select-String -Path '<scratch-home>\.claude\skills\plan-init\core.md' `
              -Pattern '^## Instruction-file contract' |
  ForEach-Object { "$($_.LineNumber):$($_.Line)" }
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
only (54/54 files emitted); no content check was run against either. If a later step needs an
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

Run in: the `skill-mesh` worktree · Windows PowerShell 5.1.

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

Per `CLAUDE.md § Key commands`, the repo-root full-suite invocation (no path argument) was
deliberately **not** run here — it is hours long and belongs to the phase gate, not to this
step. This repository has **no lint and no typecheck command** by design; none was invented or
claimed.

## 1.8 The scratch home — RETAINED for Step 109

**Do not delete it now.** The plan's § 7 Rollback clause covers Steps 108 and 109 *jointly*,
so deleting the scratch home is the rollback of **both** — it is not a Step 108 teardown to
perform on finishing § 1. Step 109 consumes this tree as a precondition. Delete it only after
§ 2 is complete, and delete rather than revert: nothing in it is tracked by git.

**Where it is.** A directory named `step108-home`, in the scratchpad of **the session that ran
Step 108** — which is a *different* directory from a later session's, and this machine holds
thousands of sibling session directories under the OS temp tree. So search the temp tree for
the basename rather than looking in your own session's scratchpad. The absolute path is
deliberately not written here — it contains a username, and this file is public. The basename
is the handle: the profile lives at `step108-home/.claude/skills` and the ownership ledger at
`step108-home/.skill-mesh-install.json`.

**If it is gone, recreate it — this handoff does not depend on the tree surviving.** A session
scratchpad lives under a temp directory, and temp directories get cleaned; this file will
outlive it. Recreation is cheap and fully specified above. All four steps are Windows
PowerShell 5.1:

1. From a `skill-mesh` checkout at or after `d4c88ee`, run § 1.2's build command.
2. Create an empty directory to serve as `<scratch-home>` — **never** the real home, never
   `$HOME`, never `C:/Users/<user>`. Any disposable empty directory will do; the name
   `step108-home` is a convention, not a requirement.
3. Run § 1.3's install command against it.
4. Confirm with § 1.4's inspector command and § 1.5's `Select-String` probe.

**What must hold at any commit, versus what is pinned to `d4c88ee`.** The exact figures above
— `owned=58`, 128 files, the heading at line `446` — are `d4c88ee`'s and may legitimately move
at a later commit. What must hold at *any* commit is commit-independent: the inspector reports
`state=present` and `ledger: state=valid providers=[claude]`, and the `Select-String` probe
*finds* the heading. Grade a recreated home on those.

A recreated home is equivalent to the original: § 1.5 established that the installed profile
is byte-identical to a fresh build at the same commit, so the same commands produce the same
tree. What Step 109 needs is *a* scratch home carrying the current claude profile — not this
particular directory.

`dist/` is gitignored and was never staged. No other durable artifact was produced by § 1.

## 1.9 Step 108 verdict

**PASS.** All four acceptance criteria met on the first attempt, no retries. The installed
tree provably carries the current canonical contract — 0 differences against a fresh build at
`d4c88ee` across all 128 files of the profile. Two non-blocking observations recorded (§ 1.6);
neither is a defect this step should have fixed.

**What this step did NOT establish, stated so Step 109 does not inherit it as an assumption:**
that any host actually loads from this tree. Step 108 produced and verified a *tree*; binding
it to a running host is § 2.0's job, and it is not optional.

---

# 2. Step 109 — operator confirmation of all five D10 rows

> **THIS SECTION IS UNEXECUTED.** It is filled in by the **operator** during Step 109 (issue
> #153) and by nobody else. Do not pre-fill any verdict below; an unfilled `Observed` or
> `Verdict` means "not yet run", which is exactly what it should mean until the operator runs
> it. The `Expected` column and the commands *are* authored in advance on purpose — they are
> the instruments.

**The procedure of record is `documentation/instruction-file-symmetry-plan.md` § 7 Step 109.**
This section records *observations* and supplies the instruments; where the two disagree, the
plan wins and the disagreement is itself worth recording in § 2.4.

**Preconditions.** A scratch home carrying the claude profile — see § 1.8 for where it is and,
if it has been cleaned up, how to recreate it in four steps. Plus a **disposable scratch
project**: a throwaway directory, created fresh, never a real project.

**Redaction still applies.** Everything recorded below lands in a public file. Replace
absolute paths with `<scratch-home>` / `<scratch-project>` before saving, per the note at the
top of this file.

## 2.0 Pre-flight — bind the tree to the host, and prove it bound

**This is mandatory and blocking. Do not grade any row until it passes.** Step 108 verified a
*tree*; nothing in Step 108 proved a host loads from it.

**Why it is blocking, measured on the live stale copy rather than argued.** The pre-Step-100
installed copy this phase exists to displace is still present elsewhere on this machine
(26,477 bytes, last modified 2026-08-09). Measured against it with `Select-String`:

| Probe on the loaded `plan-init/core.md` | Current tree | Stale copy |
|---|---|---|
| lines containing `AGENTS.md` | **34** | **0** |
| contains `## Instruction-file contract` | True | False |
| contains the owner marker | True | False |

And the stale copy's bootstrap guard reads "*skip if a `CLAUDE.md` already exists*". So on
**D10 row 2** (`CLAUDE.md` SUBSTANTIVE) the stale core skips and writes nothing — which is
byte-identical on disk to row 2's Expected "**Touch neither.**" A row 2 graded only on disk
state therefore **reports PASS against the stale tree**, and row 2 is the dominant real-world
case (~32 projects). That is precisely the failure Step 108 exists to prevent, surviving into
Step 109. Rows 1, 3, 4 and 5 all grade behavior the stale core does not have and would red
against it, so the exposure is bounded to row 2 — but row 2 is the one that matters most.

**The binding mechanism.** Claude Code discovers skills at
`<install-home>/.claude/skills/<skill>/SKILL.md` (`documentation/host-discovery.md` § "Host-native
skill discovery"). The installed profile is at `<scratch-home>/.claude/skills`, so the scratch
home must *be* the home (or the project root) the Step 109 session reads. Two options, in
preference order:

1. **Use `<scratch-home>` itself as `<scratch-project>`** — start the Step 109 session with its
   working directory set to `step108-home`. The profile is already at
   `step108-home/.claude/skills`, and § 1.4 recorded that both `CLAUDE.md` and `AGENTS.md` are
   ABSENT there, so the directory is *already* a clean D10 row 1 fixture.
2. **Install into whatever home the host actually reads**, by re-running § 1.3's install
   command with `-Home` set to that directory — still never the operator's real home.

**This repository does not document how an arbitrary directory becomes a running host's
discovery home, and Step 108 did not execute a host session to find out.** That is an honest
gap, not an oversight: it is host behavior outside this repository. The probe below is what
settles it empirically, and it is why the pre-flight is blocking rather than advisory.

**Run in:** `<scratch-project>` · Windows PowerShell 5.1, before starting the host session.

```
# Set this to the .claude\skills directory the Step 109 session actually loads from.
$LoadedSkills = '<scratch-home>\.claude\skills'

Select-String -LiteralPath (Join-Path $LoadedSkills 'plan-init\core.md') `
              -SimpleMatch 'AGENTS.md' -Quiet
```

**Expect:** `True`. This block was **extracted verbatim from this file and run** in Windows
PowerShell 5.1 against both trees: `True` against the current installed tree, `False` against
the live stale copy, exit 0. So the probe discriminates rather than merely confirming — a
check that could only ever return `True` would be no pre-flight at all.

- Which directory the Step 109 session actually loaded skills from: *(operator)*
- Probe result (`True` / `False`): *(operator)*
- **If `False`, or if the loaded directory cannot be determined: STOP.** Do not grade any row;
  record the outcome in § 2.4 and treat Step 109 as blocked on the binding, not failed on
  behavior.

## 2.1 The five D10 rows

> **Every row runs in `<scratch-project>`.** `/plan-init` and `/repo-update` both **write**
> `AGENTS.md` / `CLAUDE.md` into whatever project they resolve — via cwd or a `/user-project`
> pin. Confirm the pin *and* the cwd before each row. Running row 3 in whatever window happens
> to be open would rewrite a real project's instruction files, and row 5 explicitly expects the
> skill to continue without blocking.

Scope, stated so it is not mistaken for a gap: the skeleton exercises **one writer per row**,
i.e. 5 of canonical D10's 10 cells. That is exactly the plan's Step 109 Problem statement and
Done-when.

| Row | `AGENTS.md` | `CLAUDE.md` | Skill exercised | Expected | Observed | Verdict |
|---|---|---|---|---|---|---|
| 1 | ABSENT | ABSENT | `/plan-init` | Author `AGENTS.md` (the seven sections named in `plan-init/core.md`'s own `## Instruction-file contract` section); write `CLAUDE.md` as D8's exact pointer bytes | *(operator)* | *(operator)* |
| 2 | ABSENT / POINTER | SUBSTANTIVE | `/plan-init` | **Touch neither.** Report the project non-inverted | *(operator)* | *(operator)* |
| 3 | SUBSTANTIVE | POINTER *(inverted)* | `/repo-update` | Refresh `AGENTS.md`; leave `CLAUDE.md` untouched | *(operator)* | *(operator)* |
| 4 | SUBSTANTIVE | ABSENT | either writer — D10 gives this row an identical cell for both, and the plan assigns it to neither | Refresh `AGENTS.md`; write `CLAUDE.md` as the D8 pointer | *(operator)* | *(operator)* |
| 5 | SUBSTANTIVE | SUBSTANTIVE *(drift)* | `/repo-update` | Refresh **neither**; emit the P2 advisory naming both paths; **continue without blocking** | *(operator)* | *(operator)* |

### Fixtures — how to manufacture each row's starting state

**Run in:** `<scratch-project>` · Windows PowerShell 5.1. Give **each row its own fresh
directory** under `<scratch-project>` rather than mutating one directory between rows — a
leftover file from the previous row is the easiest way to grade the wrong D10 state, and a
fresh directory is already row 1's fixture.

```
$Sub  = "# Scratch`n`n## Stack`n`nNothing.`n"   # any '##' heading makes a file SUBSTANTIVE
$Proj = '<scratch-project>'

foreach ($r in 'row1','row2','row3','row4','row5') {
  New-Item -ItemType Directory -Force -Path (Join-Path $Proj $r) | Out-Null
}

# row 1 - both ABSENT: the freshly created directory already IS this state, write nothing

# row 2 - CLAUDE.md SUBSTANTIVE, AGENTS.md ABSENT
[System.IO.File]::WriteAllText((Join-Path $Proj 'row2\CLAUDE.md'), $Sub)

# row 3 - AGENTS.md SUBSTANTIVE, CLAUDE.md a POINTER (inverted)
[System.IO.File]::WriteAllText((Join-Path $Proj 'row3\AGENTS.md'), $Sub)
[System.IO.File]::WriteAllText((Join-Path $Proj 'row3\CLAUDE.md'), "@AGENTS.md`n")

# row 4 - AGENTS.md SUBSTANTIVE, CLAUDE.md ABSENT
[System.IO.File]::WriteAllText((Join-Path $Proj 'row4\AGENTS.md'), $Sub)

# row 5 - BOTH SUBSTANTIVE (drift)
[System.IO.File]::WriteAllText((Join-Path $Proj 'row5\AGENTS.md'), $Sub)
[System.IO.File]::WriteAllText((Join-Path $Proj 'row5\CLAUDE.md'), "# Scratch`n`n## Stack`n`nAlso nothing.`n")
```

**Expect:** each directory holds exactly the state its row's first two columns name. D8's
definitions are the authority: ABSENT = the path does not exist; POINTER = exists, defers to
the sibling, carries **no** `##` heading; SUBSTANTIVE = exists and carries at least one `##`
heading. Verify a fixture with
`Select-String -LiteralPath <file> -Pattern '^## ' -Quiet` (`True` = SUBSTANTIVE).

**These blocks were executed, not merely written.** The fixture block above and both
instruments below were **extracted verbatim from this file**, had `<scratch-project>`
substituted for a throwaway directory, and were run as a script under Windows PowerShell 5.1
during Step 108. Exit code **0**, producing exactly the five intended states — row 1: 0
instruction files; row 2: 1; row 3: 2; row 4: 1; row 5: 2 — with each file's D8 classification
checked as recorded above. Extracting from the document rather than retyping is deliberate:
it is the difference between testing what was *meant* and testing what is *written*, and an
earlier draft of this very block shipped a broken path because those two diverged.

That run exercised only the fixtures and the instruments. **No skill was invoked and no D10
row was graded** — that is entirely Step 109's work.

### Instrument A — did the skill touch a file it must not touch?

Rows 2, 3 and 4 assert "touch neither" or "leave `CLAUDE.md` untouched". An eyeball cannot
grade that; a hash before and after can.

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```
function Get-InstructionSnapshot($Dir) {
  Get-ChildItem -LiteralPath $Dir -File |
    Where-Object { $_.Name -eq 'AGENTS.md' -or $_.Name -eq 'CLAUDE.md' } |
    ForEach-Object { '{0} {1}' -f $_.Name, (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } |
    Sort-Object
}

$Row    = Join-Path '<scratch-project>' 'row2'      # the row being graded
$before = Get-InstructionSnapshot $Row
# ... run the row's skill against $Row now ...
$after  = Get-InstructionSnapshot $Row
Compare-Object $before $after
```

**Expect:** for an untouched file, `Compare-Object` prints **nothing**. Any output names the
file that changed. Capture `$before` for every row, not only the ones asserting "untouched" —
§ 2.2's fixed-point check needs row 3's post-first-pass snapshot to compare against.

### Instrument B — is `CLAUDE.md` D8's *exact* pointer bytes?

Rows 1 and 4 assert the pointer is written as **exactly** one line plus a trailing newline.
A length check alone is not enough, so this compares content.

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```
$Row = Join-Path '<scratch-project>' 'row1'         # the row being graded
$s   = [System.IO.File]::ReadAllText((Join-Path $Row 'CLAUDE.md'))
($s -eq "@AGENTS.md`n") -or ($s -eq "@AGENTS.md`r`n")
```

**Expect:** `True`. This instrument was self-tested against five inputs before being written
here: it returns `True` for the pointer with an LF ending (11 bytes) and with a CRLF ending
(12 bytes), and `False` for a trailing blank line (12 bytes), a missing final newline (10
bytes) and any extra content. Note the trailing-blank-line case is also 12 bytes — so a
byte-count check would have accepted it, which is why the comparison is on content.

### Row 5 has two independent claims

The plan's Done-when lists the second on its own, so record them separately rather than
folding both into one cell:

- The P2 advisory **printed**, and named both paths — record the two *filenames*, redacting
  any leading path to `<scratch-project>`: *(operator)*
- The run **continued** — the advisory did not block, halt, or prompt: *(operator)*

### Row 2 has two claims too, and only one of them discriminates

This is the row § 2.0 exists for. Record the two halves separately:

- **On disk — touched neither** (Instrument A prints nothing): *(operator)*
  *Non-discriminating on its own: the stale core also writes nothing here.*
- **In the report — stated the project is non-inverted**, in terms that name `AGENTS.md`:
  *(operator)*
  *This is the discriminating half. The stale core contains **zero** occurrences of the string
  `AGENTS.md` anywhere in its 26,477 bytes, so it cannot produce this report at all.*

## 2.2 Fixed-point check (rows 3 and 4)

The plan calls rows 3 and 4 fixed points, so a second pass must be an observable no-op.

**Run in:** `<scratch-project>` · the host session, immediately after the row-3 pass.

```
/repo-update
```

**Expect:** Instrument A, run with `$before` set to the snapshot taken *after* the first pass,
prints nothing for both `AGENTS.md` and `CLAUDE.md`.

- Second-pass `Compare-Object` output: *(operator)*
- No-op confirmed: *(operator)*

## 2.3 Delivery on both hosts

The contract is only real if the bytes reach the model. Both checks run in `<scratch-project>`.

### Codex — decisive, and documented

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```
codex debug prompt-input | Select-String -SimpleMatch '## Stack' -Quiet
```

**Expect:** `True`. This is the probe form this repository already documents at
`documentation/codex-instruction-delivery.md`, and it is decisive because it tests the bytes
actually delivered rather than the model's answer. Substitute any `##` heading the scratch
project's `AGENTS.md` genuinely carries.

**What Step 108 did and did not verify here.** The `Select-String -SimpleMatch … -Quiet` half
was exercised in Windows PowerShell 5.1 and discriminates (`True` on input containing the
heading, empty on input without it), and `codex` resolves on `PATH`. The full command was
**deliberately not run** by Step 108: it is Step 109's action, it reaches the Codex backend,
and per the delivery doc it re-stamps three files under the Codex home — a side effect this
step has no reason to cause.

**Record the boolean and the heading list only — never the full prompt-input dump.** That
payload also carries Codex's base instructions and any global instruction content under the
Codex home, so publishing it verbatim publishes more than the project. Redact any path to
`<scratch-home>` / `<scratch-project>`.

- Observed: *(operator)*

### Claude — the weaker check, and it is labeled as such

The `@AGENTS.md` import inside the `CLAUDE.md` pointer must resolve and expand. This is the
harder half to instrument honestly, and this repository documents no probe for it. Two
instruments, strongest first:

1. **Payload-level (preferred).** Use the session's own context inspection (`/context`) to
   confirm `AGENTS.md` appears in the loaded set. This is the analogue of the Codex probe:
   it grades what was delivered, not what the model said.
2. **Nonce canary (fallback, weaker).** Put a random token in `AGENTS.md` that appears nowhere
   else in the loaded chain, then ask the session to repeat it verbatim. A model cannot guess a
   random nonce, so reproducing it is real evidence of delivery — but absence is *not* proof of
   non-delivery, so this instrument can confirm and cannot refute.

**Do not grade this row by asking the model a question about the project and judging the
answer.** This repository's own delivery doc rules that out: "a model can answer plausibly
with no instruction file delivered at all, so the answer is not evidence and the prompt
payload is."

**Honest limitation, recorded rather than papered over:** neither instrument above was
executed by Step 108, and the document's own hazard statement applies — an import that fails
to expand looks identical to success in the pointer file itself. If neither instrument is
available in the operator's session, mark this check **NOT MECHANICALLY VERIFIED** rather than
PASS, and say so in § 2.4.

- Instrument used: *(operator)*
- Observed: *(operator)*

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

*(operator)*
