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
shell it is attributed to, and its result recorded. § 2 (Step 109) is BLOCKED BEFORE GRADING:
selected fixture and filesystem-only instrument components were mechanically validation-run,
but no skill was invoked, no host-delivery command ran and no D10 row was graded. The engineering
blocker is recorded in § 2.5; no behavioral observation or row verdict may be pre-filled.** Do not
redo § 1; do not read § 2's blank cells as results. Its expected results and commands are
instruments, not findings.

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

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1.

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

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1.

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

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1.

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

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1. Two steps: rebuild the claude
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

Observed result, with the counts and `RESULT:` label emitted by the separately run reporting
wrapper around the pipeline above:

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

**Run in:** the `skill-mesh` worktree · Windows PowerShell 5.1.

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

1. From a `skill-mesh` checkout whose four writer hashes match § 2.0's recorded values, run
   § 1.2's build command. If issue #153 instead adds a UAT mode, use that approved commit and
   follow the rebuild/reverification/hash-refresh branch at the top of § 2.
2. Create an empty directory to serve as `<scratch-home>` — **never** the real home, never
   `$HOME`, never `C:/Users/<user>`. Any disposable empty directory will do; the name
   `step108-home` is a convention, not a requirement.
3. Run § 1.3's install command against it.
4. Confirm with § 1.4's inspector command and § 1.5's `Select-String` probe.

**What must hold at an unchanged-writer commit, versus what is pinned to `d4c88ee`.** The exact
figures above — `owned=58`, 128 files, the heading at line `446` — are `d4c88ee`'s and may
legitimately move at a later commit. What must hold in the selected checkout is commit-independent:
`state=present` and `ledger: state=valid providers=[claude]`, the `Select-String` probe *finds*
the heading, and § 2.0's exact writer hashes match. A changed writer requires the full
reverification branch, not an "at or after" assumption.

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

> **STEP 109 IS BLOCKED BEFORE GRADING.** Its behavioral observations and row verdicts are filled
> in by the **operator** during Step 109 (issue #153) and by nobody else; a pre-execution engineering
> blocker may be recorded during closeout. Selected fixture and filesystem-only components were
> validation-run during Step 108, but no skill was invoked, no host-delivery command ran and no
> D10 row was graded. Do not pre-fill any behavioral observation or row verdict below; § 2.5
> records only the pre-execution engineering blocker. Expected results and commands are
> instruments, not findings.
>
> The accepted plan says to run the real named skills. It does not authorize a subsection-only
> mode, and neither installed core exposes one: `plan-init` requires its greenfield conversation,
> save and hooks; `repo-update` requires ordered Steps 1–12 and explicitly forbids required-step
> skips. A bespoke "apply only this subsection" prompt would prove compliance with that override,
> not normal named-skill behavior. **Run no skill or host-delivery command in this section until
> issue #153 records one of two deliberate resolutions:**
>
> 1. Add a core-supported, safety-gated UAT mode. This is a new code step: rebuild all profiles,
>    reinstall the Claude profile, rerun § 1.2–1.7, regenerate
>    `documentation/release-candidate-report.md`, and
>    replace § 2.0's four expected hashes from the newly verified
>    install before grading anything.
> 2. Deliberately amend Step 109 to accept **operator-scoped named-skill subsection overrides** and
>    their narrower evidence. This keeps the existing installed bytes and still requires the
>    native Skill/Base/Profile/attribution proof below. A manual core-file read or non-skill probe
>    is not this option and needs a different plan and proof design.
>
> In either case, the plan must authorize bounded routine host session/cache records or provide
> tested isolated host state before **any host session or host-delivery command in § 2** runs. The
> remaining skeleton defines the containment and measurements every permitted resolution must
> preserve.

**The procedure of record is `documentation/instruction-file-symmetry-plan.md` § 7 Step 109.**
This section records *observations* and supplies the instruments; where the two disagree, the
plan wins and the disagreement is itself worth recording in § 2.4.

**Preconditions.** A scratch home carrying the claude profile — see § 1.8 for where it is and,
if it has been cleaned up, how to recreate it in four steps. That same disposable directory is
`<scratch-project>` during Step 109; it is never a real project or the real home.

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

**The binding mechanism is documented and already accepted.**
`documentation/host-native-discovery-cutover-plan.md` § "Step 49-50 host-trace amendment
(2026-08-09)" requires a fresh `claude --setting-sources project` session from the consumer
home. The host's native records — not a model claim and not a path the operator merely names —
must show the session `cwd`, a Skill invocation, the tool-supplied `Base directory for this
skill:`, the generated wrapper's `Profile: claude`, and `attributionSkill=<skill>`.

First validate the exact scratch target in both the observer PowerShell window and the separate
host terminal. This prevents a substituted real project from becoming the serial fixture:

```powershell
$Proj = (Resolve-Path -LiteralPath '<scratch-project>').Path.TrimEnd('\')
$ScratchHome = (Resolve-Path -LiteralPath '<scratch-home>').Path.TrimEnd('\')
$RealHome = (Resolve-Path -LiteralPath `
  ([Environment]::GetFolderPath('UserProfile'))).Path.TrimEnd('\')
if (-not $Proj.Equals($ScratchHome, [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Scratch project must be the verified scratch install home.'
}
if ($Proj.Equals($RealHome, [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Refusing the real home as a scratch root.'
}
$Cursor = Get-Item -LiteralPath $Proj -Force
while ($null -ne $Cursor) {
  if (($Cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw "Refusing a scratch path with a reparse-point component: $($Cursor.FullName)"
  }
  $Cursor = $Cursor.Parent
}
Get-Command git -ErrorAction Stop | Out-Null
$PriorErrorActionPreference = $ErrorActionPreference
try {
  $ErrorActionPreference = 'Continue' # PS 5.1 can surface native stderr as NativeCommandError
  & git -C $Proj rev-parse --show-toplevel *> $null
  $GitProbeExit = $LASTEXITCODE
} finally {
  $ErrorActionPreference = $PriorErrorActionPreference
}
if ($GitProbeExit -eq 0) { throw 'Scratch project must be outside every git worktree.' }
$Ledger = Get-Content -LiteralPath (Join-Path $Proj '.skill-mesh-install.json') `
                      -Raw | ConvertFrom-Json
if ($Ledger.tool -cne 'skill-mesh' -or $null -eq $Ledger.installs.claude) {
  throw 'Verified claude scratch-install ledger is absent.'
}
$WriterFiles = @(
  '.claude\skills\plan-init\SKILL.md', '.claude\skills\plan-init\core.md',
  '.claude\skills\repo-update\SKILL.md', '.claude\skills\repo-update\core.md'
)
foreach ($relative in $WriterFiles) {
  $CurrentPath = (Get-Item -LiteralPath (Join-Path $Proj $relative) -Force).FullName
  while ($CurrentPath.Equals($Proj, [StringComparison]::OrdinalIgnoreCase) -or
         $CurrentPath.StartsWith($Proj + '\', [StringComparison]::OrdinalIgnoreCase)) {
    $Node = Get-Item -LiteralPath $CurrentPath -Force
    if (($Node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
      throw "Refusing a writer path with a reparse-point component: $($Node.FullName)"
    }
    if ($CurrentPath.Equals($Proj, [StringComparison]::OrdinalIgnoreCase)) { break }
    $CurrentPath = [IO.Path]::GetDirectoryName($CurrentPath)
  }
}
```

Keep the observer window open. Capture the two writers' installed bytes before the first row:

```powershell
$ObservedSkillFiles = @(
  'plan-init\SKILL.md', 'plan-init\core.md',
  'repo-update\SKILL.md', 'repo-update\core.md'
)
function Get-ObservedSkillHashes {
  $ObservedSkillFiles | ForEach-Object {
    '{0} {1}' -f $_, (Get-FileHash -LiteralPath `
      (Join-Path $Proj ('.claude\skills\' + $_)) -Algorithm SHA256).Hash
  }
}
$ExpectedSkillHashes = @(
  'plan-init\SKILL.md A1739A4E3D6764AE708404C3B40B74AE34183869C4B62C30AA8FCDA0696EAD9D',
  'plan-init\core.md 054DE3D99002DBA86A9A64C7CC65183B261593E2971F73F9301FF441B0196920',
  'repo-update\SKILL.md 3D101E75745F9E0D8965AE71BDC1B83F726CE7D6A8E4DCC2344740A1CC67597D',
  'repo-update\core.md B56A59F8373263A4F70CE77E23DB61310A9DC81BE8202881DA83CBB0A2F1AAA4'
)
$SkillHashesBefore = @(Get-ObservedSkillHashes)
$CurrencyDifference = @(Compare-Object $ExpectedSkillHashes $SkillHashesBefore)
if ($CurrencyDifference.Count -ne 0) {
  $CurrencyDifference
  throw 'Installed writer bytes differ from the Step 108 verified build.'
}
```

Those four expected hashes were taken from the same installed files whose full 128-file profile
matched the fresh Step 108 build at HEAD in § 1.5. Unlike an `AGENTS.md` substring probe, this
rejects an intermediate core that knew the filename but did not yet implement the matrix.

After issue #153 is unblocked, close the preceding session before each row, manufacture that row
at the root, then start a fresh session from the same validated root. **Run this launch in the
separate host terminal, not the observer window** retained for hashes and fixtures:

```powershell
Set-Location -LiteralPath $Proj
claude --setting-sources project
```

Stale same-named `plan-init` and `repo-update` skills are live in the personal
`~/.claude/skills` root, which Claude discovers regardless of cwd. Leave them untouched. Never
install this profile into the real home to make it win: on this host that skills root is a
Windows junction into a repository with 1,235 tracked files, and the existing ownership ledger
lets a reinstall overwrite owned files silently without `-Force`, backup, or prompt.

For **each** writer invocation, capture that row's own native record. Set
`$HostSuppliedBase` from the tool-supplied record, never from the intended directory:

```powershell
$HostSuppliedBase = '<host-supplied-base>'
if (-not [IO.Path]::IsPathRooted($HostSuppliedBase)) {
  throw 'Host-supplied skill base must be absolute.'
}
$ExpectedSkillBase = (Resolve-Path -LiteralPath `
  (Join-Path $Proj '.claude\skills\plan-init')).Path.TrimEnd('\')
$LoadedSkillBase = [IO.Path]::GetFullPath($HostSuppliedBase).TrimEnd('\')
$LoadedSkillBase.Equals($ExpectedSkillBase, [StringComparison]::OrdinalIgnoreCase)
Select-String -LiteralPath (Join-Path $LoadedSkillBase 'core.md') `
              -SimpleMatch 'AGENTS.md' -Quiet
```

**Expect:** `True`, `True` — exact base, then current bytes. The currency probe was
mechanically run against both real trees: `True` on the current install, `False` on the stale
copy. Substitute `repo-update` for its rows. No row may borrow another fresh session's record.

After the last row:

```powershell
$SkillHashesAfter = @(Get-ObservedSkillHashes)
Compare-Object $SkillHashesBefore $SkillHashesAfter
```

**Expect:** no output. Any binding mismatch or changed installed byte blocks Step 109 rather
than failing a D10 behavior.

- Per-row session `cwd`, Skill/Base/Profile/attribution records: *(operator)*
- Per-row currency results (`True` / `False`): *(operator)*
- Post-observation installed-byte comparison: *(operator)*

## 2.1 The five D10 rows

> **Every row runs serially at the validated `<scratch-project>` root.** Close the preceding
> host session, reset only the two root instruction files, and start a fresh session from that
> same root before each row. Do not use child row directories or a project pin: host discovery
> and the writer target must coincide.

Once unblocked, the skeleton exercises **one writer contract surface per row**, i.e. 5 of
canonical D10's 10 cells. Rows 1–2 target `plan-init`'s `## After plan.md exists`; rows 3–5 and
the fixed-point check target `repo-update` Step 7. Use the same deterministic facts for every
authorized action: documentation-only UAT fixture; Markdown stack; no production commands; root
instruction files are the only instruction outputs; no application architecture; UAT-only
current state; Windows PowerShell 5.1 environment.

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

```
$Sub  = "# Scratch`n`n## Stack`n`nNothing.`n"   # any '##' heading makes a file SUBSTANTIVE

function Clear-InstructionFixture {
  if (-not $Proj.Equals((Resolve-Path -LiteralPath '<scratch-home>').Path.TrimEnd('\'),
                        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Scratch target changed; refusing fixture reset.'
  }
  foreach ($name in 'AGENTS.md','CLAUDE.md') {
    $path = Join-Path $Proj $name
    if (Test-Path -LiteralPath $path) {
      $item = Get-Item -LiteralPath $path -Force
      if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or
          (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
        throw "Refusing to remove non-file fixture path: $name"
      }
      Remove-Item -LiteralPath $path -Force
    }
  }
}

function Set-RowFixture([ValidateSet(1,2,3,4,5)][int]$Row) {
  Clear-InstructionFixture
  switch ($Row) {
    1 { } # both ABSENT
    2 { [IO.File]::WriteAllText((Join-Path $Proj 'CLAUDE.md'), $Sub) }
    3 {
      [IO.File]::WriteAllText((Join-Path $Proj 'AGENTS.md'), $Sub)
      [IO.File]::WriteAllText((Join-Path $Proj 'CLAUDE.md'), "@AGENTS.md`n")
    }
    4 { [IO.File]::WriteAllText((Join-Path $Proj 'AGENTS.md'), $Sub) }
    5 {
      [IO.File]::WriteAllText((Join-Path $Proj 'AGENTS.md'), $Sub)
      [IO.File]::WriteAllText((Join-Path $Proj 'CLAUDE.md'),
        "# Scratch`n`n## Stack`n`nAlso nothing.`n")
    }
  }
}

$RowNumber = 1  # change only this argument immediately before each later row
Set-RowFixture $RowNumber
```

**Expect, before the corresponding fresh host session:** `ABSENT/ABSENT`,
`ABSENT/SUBSTANTIVE`, `SUBSTANTIVE/POINTER`, `SUBSTANTIVE/ABSENT`, then
`SUBSTANTIVE/SUBSTANTIVE`.

**The filesystem mechanics were validation-run, not merely written.** The serial fixture logic
produced those five state pairs in Windows PowerShell 5.1. Instrument A's two halves were run
separately against unchanged and changed states. Instrument B was self-tested separately
against the five manufactured post-skill pointer states listed below; it was not concatenated
after the empty row-1 fixture. No skill was invoked and no D10 row was graded.

### Instrument A — did the skill touch a file it must not touch?

Rows 2–5 assert "touch neither", "leave `CLAUDE.md` untouched", or "refresh neither" for at
least one path. Instruction-file hashes grade content, a protected-root manifest catches other
filesystem changes, and the native action trace catches a forbidden byte-identical rewrite.

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```
function Get-InstructionSnapshot($Dir) {
  Get-ChildItem -LiteralPath $Dir -File |
    Where-Object { $_.Name -eq 'AGENTS.md' -or $_.Name -eq 'CLAUDE.md' } |
    ForEach-Object { '{0} {1}' -f $_.Name, (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } |
    Sort-Object
}

function Get-ProtectedRootSnapshot($Dir, [string[]]$ExcludedRelativePaths) {
  $Root = (Resolve-Path -LiteralPath $Dir).Path.TrimEnd('\')
  $Pending = New-Object 'System.Collections.Generic.Stack[string]'
  $Pending.Push($Root)
  $Snapshot = @()
  while ($Pending.Count -gt 0) {
    $Current = $Pending.Pop()
    foreach ($Child in Get-ChildItem -LiteralPath $Current -Force -ErrorAction Stop) {
      if (($Child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing a reparse-point child in the protected root: $($Child.FullName)"
      }
      $Relative = $Child.FullName.Substring($Root.Length).TrimStart('\')
      if ($Child.PSIsContainer) {
        if ($ExcludedRelativePaths -contains $Relative) {
          throw "An allowed file path became a directory: $Relative"
        }
        $Snapshot += "D $Relative"
        $Pending.Push($Child.FullName)
      } elseif ($ExcludedRelativePaths -notcontains $Relative) {
        $Snapshot += "F $Relative $($Child.Length) $((Get-FileHash -LiteralPath $Child.FullName -Algorithm SHA256).Hash)"
      }
    }
  }
  $Snapshot | Sort-Object
}

$AllowedWrites = switch ($RowNumber) {
  1 { @('AGENTS.md', 'CLAUDE.md') }
  2 { @() }
  3 { @('AGENTS.md') }
  4 { @('AGENTS.md', 'CLAUDE.md') }
  5 { @('uat-memory.md') }
}
$AllowedWritePaths = @($AllowedWrites | ForEach-Object {
  [IO.Path]::GetFullPath((Join-Path $Proj $_))
})
$Row             = $Proj                           # validated root being graded
$before          = @(Get-InstructionSnapshot $Row)
$protectedBefore = @(Get-ProtectedRootSnapshot $Row $AllowedWrites)
```

For row 5, create the absolute memory target in its subsection below **before** taking this
pre-action snapshot. Once issue #153 supplies an authorized action, run it in the separate host
session. Keep the observer window open, then run the post-action half separately:

```
$after          = @(Get-InstructionSnapshot $Row)
$protectedAfter = @(Get-ProtectedRootSnapshot $Row $AllowedWrites)
Compare-Object $protectedBefore $protectedAfter
Compare-Object $before $after
```

**Expect:** the protected-root comparison prints nothing on every row. The instruction comparison
shows row 1 adding both files; rows 2 and 5 print nothing; row 3 changes only `AGENTS.md`; row 4
changes `AGENTS.md` and adds `CLAUDE.md`. Capture both preimages for every row; § 2.2 separately
takes row 3's post-first-pass snapshot.

Also audit that invocation's native tool-action trace. Normalize every Write/Edit target with
`[IO.Path]::GetFullPath()` and require exact case-insensitive membership in
`$AllowedWritePaths`; any shell/process tool action or a write outside that list blocks the row.
Rows 2 and the fixed-point pass allow no write action at all. This trace requirement is what
catches an otherwise invisible byte-identical rewrite or a write-then-restore sequence.

### Instrument B — is `CLAUDE.md` D8's *exact* pointer bytes?

Rows 1 and 4 assert the pointer is written as **exactly** one line plus a trailing newline.
A length check alone is not enough, so this compares content. Run it **after** the row's skill
has written `CLAUDE.md`; the starting row-1 and row-4 fixtures intentionally lack that file.

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```
$Row = $Proj                                        # validated post-skill root
$s   = [System.IO.File]::ReadAllText((Join-Path $Row 'CLAUDE.md'))
($s -eq "@AGENTS.md`n") -or ($s -eq "@AGENTS.md`r`n")
```

**Expect:** `True`. This instrument was self-tested against five inputs before being written
here: it returns `True` for the pointer with an LF ending (11 bytes) and with a CRLF ending
(12 bytes), and `False` for a trailing blank line (12 bytes), a missing final newline (10
bytes) and any extra content. Note the trailing-blank-line case is also 12 bytes — so a
byte-count check would have accepted it, which is why the comparison is on content.

After rows 1, 3 and 4, also list `AGENTS.md`'s `##` headings. A hash delta alone is not proof
of the required seven-section walk:

```powershell
Select-String -LiteralPath (Join-Path $Proj 'AGENTS.md') -Pattern '^## ' |
  ForEach-Object Line
```

**Expect:** headings covering project overview, stack, commands, directory layout,
architecture, current state and environment requirements.

### Row 5 has two independent claims

After `Set-RowFixture 5` and before Instrument A's pre-action snapshot, create one scratch-only
Step 8 target and record its preimage:

```powershell
$Row5Memory = [IO.Path]::GetFullPath((Join-Path $Proj 'uat-memory.md'))
$Row5MemoryParent = [IO.Path]::GetDirectoryName($Row5Memory)
if (-not $Row5MemoryParent.Equals($Proj, [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Row-5 MEMORY_FILE must be directly under the validated scratch root.'
}
if (Test-Path -LiteralPath $Row5Memory) {
  $MemoryItem = Get-Item -LiteralPath $Row5Memory -Force
  if (-not (Test-Path -LiteralPath $Row5Memory -PathType Leaf) -or
      (($MemoryItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
    throw 'Refusing non-file or reparse-point uat-memory.md.'
  }
}
[IO.File]::WriteAllText($Row5Memory,
  "# UAT memory`n`n## Status`n`nBefore row-5 continuation.`n")
$Row5MemoryBefore = (Get-FileHash -LiteralPath $Row5Memory -Algorithm SHA256).Hash
```

Once Step 109 is unblocked, the selected resolution must provide an authorized slice that begins
at Step 7 and whose safe boundary ends immediately before Step 9. Supply the **absolute**
`$Row5Memory` as `MEMORY_FILE`, phase text `Phase IS Step 109 row 5 continuation observed`, issue
#153, final test count unknown, no discrepancies and overall UAT pending. Do not tell the agent to
"continue" or state that Step 8 must happen: the core's natural Step-7-to-Step-8 transition is the
property under test. Step 8 is allowed to write only `$Row5Memory`. Afterward:

```powershell
$Row5MemoryAfter = (Get-FileHash -LiteralPath $Row5Memory -Algorithm SHA256).Hash
(-not $Row5MemoryAfter.Equals($Row5MemoryBefore,
                              [StringComparison]::OrdinalIgnoreCase))
Select-String -LiteralPath $Row5Memory `
              -SimpleMatch 'Phase IS Step 109 row 5 continuation observed' -Quiet
```

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
  the intended core; row 2 is gradable only because § 2.0's native host record already proved
  the exact scratch-tree binding for this invocation.*

## 2.2 Fixed-point check (representative row 3)

The plan calls rows 3 and 4 fixed points and requires one second `/repo-update` pass, so row 3
is the representative. Do not grade the second pass unless the first row-3 pass already changed
`AGENTS.md`, left `CLAUDE.md` byte-identical, and passed its binding record; two runs that both
did nothing are not a fixed point.

**Run in:** the same fresh row-3 host session, immediately after the first pass and before any
fixture reset. In the observer window, take a new post-first-pass baseline:

```powershell
$Row = $Proj
$before = @(Get-InstructionSnapshot $Row)
$fixedRootBefore = @(Get-ProtectedRootSnapshot $Row -ExcludedRelativePaths @())
```

Do **not** use a bare `/repo-update`; that starts the current full lifecycle. After issue #153
records its resolution, paste the exact same authorized row-3 invocation literal a second time in
the host session. Until that literal exists, this check remains blocked.

Finally, in the observer window:

```powershell
$after = @(Get-InstructionSnapshot $Row)
$fixedRootAfter = @(Get-ProtectedRootSnapshot $Row -ExcludedRelativePaths @())
Compare-Object $fixedRootBefore $fixedRootAfter
Compare-Object $before $after
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
$DeliveryCanary = 'skill-mesh-step109-delivery-' + [Guid]::NewGuid().ToString('N')
$PriorCanaryHit = @(Get-ChildItem -LiteralPath $Proj -File -Force -Recurse |
  Select-String -SimpleMatch $DeliveryCanary)
if ($PriorCanaryHit.Count -ne 0) { throw 'Random delivery canary already exists.' }
$AgentsPath = Join-Path $Proj 'AGENTS.md'
$AgentsItem = Get-Item -LiteralPath $AgentsPath -Force
if (($AgentsItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
  throw 'Refusing a reparse-point AGENTS.md delivery target.'
}
[IO.File]::AppendAllText($AgentsPath, "`n<!-- $DeliveryCanary -->`n")
$CanaryFiles = @(Get-ChildItem -LiteralPath $Proj -File -Force -Recurse |
  Select-String -SimpleMatch $DeliveryCanary | Select-Object -ExpandProperty Path -Unique)
if ($CanaryFiles.Count -ne 1 -or
    -not $CanaryFiles[0].Equals($AgentsPath, [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Delivery canary is not unique to root AGENTS.md.'
}
$VerifiedHeading = (Select-String -LiteralPath $AgentsPath -Pattern '^## ' |
  Select-Object -First 1).Line
if ([String]::IsNullOrWhiteSpace($VerifiedHeading)) {
  throw 'Completed row-3 AGENTS.md has no section heading to verify.'
}
```

### Codex — decisive, and documented

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```
Set-Location -LiteralPath $Proj
$PromptCanaryFound = $false
$PromptHeadingFound = $false
codex debug prompt-input | ForEach-Object {
  $PromptLine = [string]$_
  if ($PromptLine.Contains($DeliveryCanary)) { $PromptCanaryFound = $true }
  if ($PromptLine.Contains($VerifiedHeading)) { $PromptHeadingFound = $true }
}
$PromptCanaryFound
$PromptHeadingFound
```

**Expect:** `True`, `True` — the collision-proof canary and one real row-3 section heading. This
is the probe form this repository already documents at
`documentation/codex-instruction-delivery.md`, and it is decisive because it tests the bytes
actually delivered rather than the model's answer. The random token was proved absent before it
was added and unique to this project's `AGENTS.md`, so a base, global or ancestor instruction file
cannot satisfy the search accidentally.

**What Step 108 did and did not verify here.** The two-boolean stream predicate was exercised in
Windows PowerShell 5.1 against controlled input and requires both strings independently, and
`codex` resolves on `PATH`. The full command was **deliberately not run** by Step 108: it is Step
109's action, it reaches the Codex backend, and Codex-home background churn makes individual
cache changes unattributable. Controlled reproductions observed no project-directory write and
no persisted `-c` override; no per-invocation Codex-home file count is published.

**Record both booleans, the exact heading and the canary — never the full prompt-input dump.** That
payload also carries Codex's base instructions and any global instruction content under the
Codex home, so publishing it verbatim publishes more than the project. Redact any path to
`<scratch-home>` / `<scratch-project>`.

- Observed: *(operator)*

### Claude — fresh-session import check

The `@AGENTS.md` import inside the `CLAUDE.md` pointer must resolve and expand. This is the
harder half to instrument honestly. Close the row-3 writer session and start a new
delivery-only `claude --setting-sources project` session from the validated root. Before
invoking a skill or opening either instruction file through a tool, use `/context` to confirm
the host reports `AGENTS.md` in the loaded project-instruction set and, if it exposes source
content, the same `$DeliveryCanary` inside that source.

**Do not grade this row by asking the model a question about the project and judging the
answer.** This repository's own delivery doc rules that out: "a model can answer plausibly
with no instruction file delivered at all, so the answer is not evidence and the prompt
payload is."

**Honest limitation, recorded rather than papered over:** this instrument was not executed by
Step 108, and an import that fails to expand looks identical in the pointer file itself. If
payload inspection is unavailable, mark this check **NOT MECHANICALLY VERIFIED**, not PASS.

- Fresh-session `cwd`: *(operator)*
- `/context` source/canary observation: *(operator)*

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
subsection overrides. Until then every Observed/Verdict cell stays blank, no host command in § 2
runs, and this is not a D10 failure.

- Resolution selected: *(operator)*
- Operator UAT verdict after resolution: *(operator)*
