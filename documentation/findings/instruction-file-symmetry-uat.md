<!-- REDACTION NOTE. Machine-specific absolute paths are replaced throughout by these
     placeholders, and an appending author must keep using them — this is a public repository
     and tests/package-integrity/test_manifest_contract.py::test_no_absolute_private_paths_committed
     sweeps every tracked AND untracked-but-not-ignored text file for absolute user paths:

       <scratch-home>          the disposable install home (see § 1.8)
       <scratch-project>       the disposable project Step 109 runs against (see § 2)
       <scratch-claude-config> the distinct disposable Claude state root (see §§ 1.8 and 2.0)
       <fresh-build-output>    the build root (historical throwaway; Step 109 receipt-bound, § 1.8)
       <repo>                  this checkout's absolute path, where it appeared in tool output

     One token needs care. In §§ 1.5-1.6, `<repo>/_shared/<leaf>` is NOT a redaction — it is
     the LITERAL string canonical cores use to cite the vendored shared payload, and § 1.6 O2
     is specifically about that literal being rewritten at emit time. Read it as source bytes,
     not as a hidden path. -->

# Instruction-file symmetry — build, install and UAT transcript

**Status: § 1's historical build/install outcome is COMPLETE — its original commands produced the
recorded results. Some replay blocks now shown in § 1 were strengthened post-merge; those added
guards are reproduction instruments, not represented as the exact historical invocations. Step
108 certification is pending the post-merge instrument repairs, independent review, and stable
repo-root gate. § 2 (Step 109) is
BLOCKED BEFORE GRADING: selected fixture and filesystem-only components were mechanically
validation-run, but no skill was invoked, no host-delivery command ran and no D10 row was graded.
The engineering blocker is recorded in § 2.5; no behavioral observation or row verdict may be
pre-filled.** Do not replace or reinterpret § 1's historical record. Step 109 must still run
§ 1.8's fresh-root build/install/reverification recipe; if #153 changes writer bytes, follow the
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

**Every fenced command in § 1 is written for Windows PowerShell 5.1.** The original commands were
executed in that shell. Post-merge fail-closed guards added to the replay blocks are identified
where they appear and must be executed against Step 109's newly created roots; they were not
retroactively run against the now-audit-obsoleted historical home. Commands are spelled
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
merely written; § 1.5 records their historical output. The surrounding fail-closed path, link,
count, and error guards shown now were added later. Where a figure below was originally obtained
with a POSIX tool under Git Bash, it was re-measured in PowerShell 5.1 for this record and the two
agreed.

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
the recorded zero-difference result below. The replay block now shown here is its post-merge,
fail-closed replacement: it adds canonical-root, filesystem-identity, non-nesting, link-ancestry,
nonempty/count/hash, and throwing-delta guards. Those added guards must run against Step 109's
safely prebuilt fresh roots; this exact hardened block was not rerun against the historical temp
home.

```
$FreshInput = '<fresh-build-output>\claude'
$InstalledInput = '<scratch-home>\.claude\skills'
$FreshRootItem = Get-Item -LiteralPath `
  (Resolve-Path -LiteralPath $FreshInput -ErrorAction Stop).Path `
  -Force -ErrorAction Stop
$InstalledRootItem = Get-Item -LiteralPath `
  (Resolve-Path -LiteralPath $InstalledInput -ErrorAction Stop).Path `
  -Force -ErrorAction Stop
$Fresh = $FreshRootItem.FullName.TrimEnd('\')
$Installed = $InstalledRootItem.FullName.TrimEnd('\')
if (-not ('SkillMeshUat.NativeFileIdentity' -as [type])) {
  Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;
namespace SkillMeshUat {
  [StructLayout(LayoutKind.Sequential)]
  public struct ByHandleFileInformation {
    public uint FileAttributes;
    public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
    public uint VolumeSerialNumber;
    public uint FileSizeHigh;
    public uint FileSizeLow;
    public uint NumberOfLinks;
    public uint FileIndexHigh;
    public uint FileIndexLow;
  }
  public static class NativeFileIdentity {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true,
      EntryPoint = "CreateFileW")]
    public static extern SafeFileHandle CreateFile(
      string name, uint access, FileShare share, IntPtr security,
      FileMode mode, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool GetFileInformationByHandle(
      SafeFileHandle handle, out ByHandleFileInformation information);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true,
      EntryPoint = "GetFinalPathNameByHandleW")]
    public static extern uint GetFinalPathNameByHandle(
      SafeFileHandle handle, StringBuilder path, uint capacity, uint flags);
  }
}
'@ -ErrorAction Stop
}
function Get-DirectoryFileIdentity([string]$Path, [string]$Label) {
  $DirectoryItem = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if (-not $DirectoryItem.PSIsContainer) {
    throw "$Label is not a directory: $Path"
  }
  $Handle = [SkillMeshUat.NativeFileIdentity]::CreateFile(
    $DirectoryItem.FullName, 0, [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete,
    [IntPtr]::Zero, [IO.FileMode]::Open, 0x02000000, [IntPtr]::Zero)
  if ($Handle.IsInvalid) {
    $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    $Handle.Dispose()
    throw [ComponentModel.Win32Exception]::new(
      $ErrorCode, "Cannot open $Label identity handle: $Path")
  }
  try {
    $Information = New-Object SkillMeshUat.ByHandleFileInformation
    if (-not [SkillMeshUat.NativeFileIdentity]::GetFileInformationByHandle(
        $Handle, [ref]$Information)) {
      $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
      throw [ComponentModel.Win32Exception]::new(
        $ErrorCode, "Cannot read $Label identity: $Path")
    }
    return ('{0:X8}:{1:X8}{2:X8}' -f $Information.VolumeSerialNumber,
      $Information.FileIndexHigh, $Information.FileIndexLow)
  } finally {
    $Handle.Dispose()
  }
}
function Get-DirectoryHandleFacts([string]$Path, [string]$Label) {
  $DirectoryItem = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if (-not $DirectoryItem.PSIsContainer) {
    throw "$Label is not a directory: $Path"
  }
  $Identity = Get-DirectoryFileIdentity $DirectoryItem.FullName $Label
  try {
    $CallerPath = [IO.Path]::GetFullPath([string]$Path).TrimEnd('\')
  } catch {
    throw "$Label caller path cannot be normalized: $Path"
  }
  $Handle = [SkillMeshUat.NativeFileIdentity]::CreateFile(
    $DirectoryItem.FullName, 0, [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete,
    [IntPtr]::Zero, [IO.FileMode]::Open, 0x02000000, [IntPtr]::Zero)
  if ($Handle.IsInvalid) {
    $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    $Handle.Dispose()
    throw [ComponentModel.Win32Exception]::new(
      $ErrorCode, "Cannot open $Label final-path handle: $Path")
  }
  try {
    $DosBuffer = New-Object Text.StringBuilder 32768
    $DosLength = [SkillMeshUat.NativeFileIdentity]::GetFinalPathNameByHandle(
      $Handle, $DosBuffer, $DosBuffer.Capacity, 0x0)
    if ($DosLength -eq 0 -or $DosLength -ge $DosBuffer.Capacity) {
      $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
      throw [ComponentModel.Win32Exception]::new(
        $ErrorCode, "Cannot resolve $Label into the local DOS namespace: $Path")
    }
    $DosFinalPath = $DosBuffer.ToString().TrimEnd('\')
    if ($DosFinalPath -cnotmatch '^\\\\\?\\[A-Za-z]:\\' -or
        $CallerPath -cne $DosFinalPath.Substring(4)) {
      throw "$Label must use its exact case-preserved local long path: $Path"
    }
    $Buffer = New-Object Text.StringBuilder 32768
    $FinalLength = [SkillMeshUat.NativeFileIdentity]::GetFinalPathNameByHandle(
      $Handle, $Buffer, $Buffer.Capacity, 0x1)
    if ($FinalLength -eq 0 -or $FinalLength -ge $Buffer.Capacity) {
      $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
      throw [ComponentModel.Win32Exception]::new(
        $ErrorCode, "Cannot resolve $Label into the local volume-GUID namespace: $Path")
    }
    $FinalPath = $Buffer.ToString().TrimEnd('\')
    if ($FinalPath -cnotmatch `
        '^\\\\\?\\Volume\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}(?:\\|$)') {
      throw "$Label did not resolve to a local volume-GUID path: $FinalPath"
    }
    return [pscustomobject]@{
      Identity = $Identity
      FinalPath = $FinalPath
      DosPath = $DosFinalPath.Substring(4)
    }
  } finally {
    $Handle.Dispose()
  }
}
function Test-FinalPathWithin([string]$Candidate, [string]$Container) {
  return ($Candidate.Equals($Container, [StringComparison]::Ordinal) -or
          $Candidate.StartsWith($Container + '\', [StringComparison]::Ordinal))
}
$FreshIdentity = Get-DirectoryFileIdentity $FreshInput 'fresh build root'
$InstalledIdentity = Get-DirectoryFileIdentity $InstalledInput 'installed profile root'
if ($FreshIdentity -ceq $InstalledIdentity) {
  throw 'Fresh and installed roots resolve to the same filesystem directory.'
}
$FreshFacts = Get-DirectoryHandleFacts $FreshInput 'fresh build root'
$InstalledFacts = Get-DirectoryHandleFacts $InstalledInput 'installed profile root'
if ((Test-FinalPathWithin $FreshFacts.FinalPath $InstalledFacts.FinalPath) -or
    (Test-FinalPathWithin $InstalledFacts.FinalPath $FreshFacts.FinalPath)) {
  throw 'Fresh and installed roots must be distinct and non-nested.'
}

function Get-TreeManifest($Root) {
  $RootItem = Get-Item -LiteralPath $Root -Force -ErrorAction Stop
  if (-not $RootItem.PSIsContainer -or
      (($RootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or
      -not [String]::IsNullOrEmpty([string]$RootItem.LinkType)) {
    throw "Tree manifest requires an unlinked directory: $Root"
  }
  $Ancestor = $RootItem
  while ($null -ne $Ancestor) {
    if ((($Ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or
        -not [String]::IsNullOrEmpty([string]$Ancestor.LinkType)) {
      throw "Tree manifest refuses linked ancestor: $($Ancestor.FullName)"
    }
    $Ancestor = $Ancestor.Parent
  }
  $Pending = New-Object 'System.Collections.Generic.Stack[string]'
  $Pending.Push($RootItem.FullName.TrimEnd('\'))
  $Entries = @()
  $FileCount = 0
  while ($Pending.Count -gt 0) {
    $Current = $Pending.Pop()
    foreach ($Child in Get-ChildItem -LiteralPath $Current -Force -ErrorAction Stop) {
      if ((($Child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or
          -not [String]::IsNullOrEmpty([string]$Child.LinkType)) {
        throw "Tree manifest refuses linked entry: $($Child.FullName)"
      }
      $Relative = $Child.FullName.Substring($RootItem.FullName.TrimEnd('\').Length + 1)
      if ($Child.PSIsContainer) {
        $Entries += "D  $Relative"
        $Pending.Push($Child.FullName)
      } else {
        $Digest = (Get-FileHash -LiteralPath $Child.FullName -Algorithm SHA256 `
                                -ErrorAction Stop).Hash
        if ($Digest -cnotmatch '^[0-9A-F]{64}$') {
          throw "Invalid SHA-256 result: $($Child.FullName)"
        }
        $Entries += "F  $Relative  $Digest"
        $FileCount++
      }
    }
  }
  if ($FileCount -eq 0) { throw "Tree manifest has no files: $Root" }
  @($Entries | Sort-Object)
}

$FreshManifest = @(Get-TreeManifest $Fresh)
$InstalledManifest = @(Get-TreeManifest $Installed)
$FreshFileCount = @($FreshManifest | Where-Object { $_.StartsWith('F  ') }).Count
$InstalledFileCount = @($InstalledManifest | Where-Object { $_.StartsWith('F  ') }).Count
if ($FreshFileCount -ne 128 -or $InstalledFileCount -ne 128) {
  throw "Expected 128 files per tree; got fresh=$FreshFileCount installed=$InstalledFileCount."
}
$Delta = @(Compare-Object -ReferenceObject $FreshManifest `
                         -DifferenceObject $InstalledManifest -CaseSensitive `
                         -ErrorAction Stop)
if ($Delta.Count -ne 0) {
  $Delta
  throw 'Fresh and installed profiles differ.'
}
'IDENTICAL'
```

Historical observed result, with the counts and `RESULT:` label emitted by the reporting wrapper
around the original comparison. It records the outcome; it does not claim the later guards above
were retroactively executed:

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

The historical heading probe found the one match recorded below. The block now shown is the
post-merge fail-closed replay form: its exact-count, line-number, and exact-text guards must be run
against Step 109's fresh installed tree and were not retroactively run against the historical one.

```
$ContractHeadingMatches = @(Select-String `
  -LiteralPath '<scratch-home>\.claude\skills\plan-init\core.md' `
  -Pattern '^## Instruction-file contract' -CaseSensitive -ErrorAction Stop)
if ($ContractHeadingMatches.Count -ne 1 -or
    $ContractHeadingMatches[0].LineNumber -ne 446 -or
    $ContractHeadingMatches[0].Line -cne '## Instruction-file contract') {
  throw 'Installed plan-init core lacks exactly one contract heading at line 446.'
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

## 1.8 The historical scratch home — AUDIT-OBSOLETED for Step 109

The original Step 108 home remains historical build/install evidence, but it was created below
the OS temp tree, which on this host is inside the real user profile. The strengthened § 2.0
pre-flight therefore rejects it as a Step 109 target. Do not search for, revive, or reuse that
directory. Whether or not it still exists, Step 109 must create a new receipt-bound scratch
home/project, a distinct scratch Claude config root, and a distinct fresh-build output root outside
the real profile, then safely build, install, and reverify the profile. Delete those three new
roots only after § 2 is complete, and delete rather than revert: nothing in them is tracked by git.

Create the fresh compliant roots using these five Windows PowerShell 5.1 steps:

1. Issue #153's committed preparation block must atomically create a new random-named
   `<scratch-home>`, a distinct `<scratch-claude-config>`, and a distinct
   `<fresh-build-output>` under a validated, unlinked, outside-git parent — **never** the real
   home, `$HOME`, `C:/Users/<user>`, an ancestor of that home, or an existing consumer. Caller and
   `Resolve-Path` spellings are not identity evidence: reject UNC, SUBST, 8.3, mapped-drive, and
   other aliased/nonlocal spellings, then bind each disposable root and the real profile by a
   Win32 handle-final local volume-GUID path plus volume-serial/file ID. Compare those physical
   paths for equality and ancestry. Create a `FileMode.CreateNew` schema-v3 JSON receipt in the new
   home that binds a random nonce, all three exact caller paths, their handle-final paths and file
   IDs, and the real-profile handle identity used for the exclusion decision. Record its SHA-256
   and nonce on #153 before any builder or installer runs; do not record an absolute path. A
   familiar basename is not disposable-root evidence.
2. Immediately before the only builder invocation, the committed block must re-open all four
   handle identities, revalidate the receipt and physical unlinked/outside-git/outside-profile
   ancestry, prove the build root empty, and prove its `claude`, `gpt`, and `codex` children absent.
   Its tests must fail closed for a `\\localhost\c$` alias, a SUBST alias, an available 8.3 alias,
   roots nested in either direction, a root under the real profile, and a case-mismatched filename
   on a per-directory case-sensitive fixture when the host supports one. Only then run
   `powershell -File tools/build-distributions.ps1 -Provider all -OutputDir
   '<fresh-build-output>'`. If #153 adds a UAT mode, use that approved checkout and follow § 2's
   rebuild/reverification/hash-refresh branch. Never replay § 1.2 against default `<repo>\dist` or
   § 1.5's one-provider build during Step 109.
3. Create the config root's unlinked `tmp` directory and establish the approved isolated
   authentication mode without copying or exposing an ambient credential. Keep all settings,
   plugins, credentials, history, transcripts, and temp state under that config root.
4. Install only the prebuilt bytes with `powershell -File tools/install-skill-mesh.ps1 -Provider
   claude -Home '<scratch-home>' -DistDir '<fresh-build-output>'`; do not let the installer launch
   a second implicit builder.
5. Confirm with § 1.4's inspector command, § 1.5's equality and heading probes, and § 2.0's
   receipt, path, Git, link, and writer-hash checks before any host launch; bind the fresh writer
   hashes, receipt hash, and receipt nonce into #153's committed preflight.

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
After Step 109, delete all three new roots only through #153's exact receipt-bound safe-cleanup
block; never derive a cleanup target
from a basename, wildcard, ambient environment variable, or unresolved placeholder.

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
>    receipt-bound three-root preparation, one guarded `-Provider all -OutputDir
>    <fresh-build-output>` build, and the explicit `-DistDir` install. Then rerun the inspector,
>    equality/heading, reference, and package-gate criteria against those exact bytes (without
>    replaying § 1.2's default output or § 1.5's one-provider builder), regenerate
>    `documentation/release-candidate-report.md`, and replace § 2.0's four expected hashes from the
>    newly verified install. Because this route changes code, its new preparation step must then
>    clear a clean detached repo-root `python -m pytest` at or above
>    `documentation/phase-75-baseline.md` with the recorded skip count unchanged before grading
>    anything; the package-integrity run is only its iteration gate.
> 2. Deliberately amend Step 109 to accept **operator-scoped named-skill subsection overrides** and
>    their narrower evidence. This keeps the existing installed bytes and still requires the
>    native Skill/Base/Profile/attribution proof below. A manual core-file read or non-skill probe
>    is not this option and needs a different plan and proof design.
>
> In either case, issue #153 must record a tested **preventive** containment rail before any host
> session or host-delivery command in § 2 runs: auto memory disabled; project-only settings;
> strict-empty user/project/plugin MCP configuration plus MCP denial; a fail-closed pre-launch
> inventory proving the effective managed MCP configuration is absent or empty; a built-in-tool
> and path allowlist for that exact row; and no shell/process tool. Any configured managed MCP
> server blocks the launch because its process can start outside the row's tool rail. A `PreToolUse`
> hook may implement the path guard,
> but its deny cases must be exercised before the first row. Native action traces remain required
> as secondary audit; inspecting them after an action is not containment. Bounded native
> session/cache transport records are allowed, but semantic memory, source-tree, skill-tree,
> installer, and outside-scratch project writes are not. Project-only settings do **not** suppress
> managed policy: managed settings outrank lower sources, hooks from effective sources merge, and
> `--strict-mcp-config` does not suppress managed MCP policy. Before launch, the selected resolution
> must enumerate the effective managed/plugin/session hook and settings surface, managed MCP
> configuration, managed skill definitions, and **every effective instruction/rule source** without
> firing a session. That inventory includes the organization-wide managed `CLAUDE.md`, managed
> `claudeMd` content and other managed policy instructions, plus a physical ancestor walk from the
> scratch project through the volume root for `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/**`,
> colliding skills, and dynamic-context preprocessing. The row's root instruction fixture and the
> two receipt-pinned installed writer skills are the only permitted project instruction/skill
> sources. Hash/allowlist every active hook; reject every configured managed MCP server; reject any
> managed or ancestor `plan-init` or `repo-update` definition; and forbid all managed/ancestor-skill
> shell preprocessing or dynamic-context commands. If the host cannot enumerate organization-wide
> managed instruction content before launch, Step 109 stays blocked. If the
> preventive path rail uses `PreToolUse`, that one pinned guard and the pinned delivery logger are
> the only two command-hook exceptions; with a non-process permission rail, the logger is the sole
> exception. If the host cannot provide that pre-launch evidence, Step 109 stays blocked.

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
a complete successful native `Read` of that exact wrapper's co-located `core.md`, after Skill
invocation and before any response or non-read behavior action. `repo-update` delegates D10 to the sibling
`plan-init/core.md`, so its rows must show that complete second read too. Each on-disk core hash is
then bound to Step 108's expected hash.

These host mechanics are grounded in Claude Code's current primary documentation: project/user
setting sources in [settings](https://code.claude.com/docs/en/settings), supporting-file loading in
[skills](https://code.claude.com/docs/en/skills), auto-memory behavior in
[memory](https://code.claude.com/docs/en/memory), the isolated state root and lifecycle switches in
[the configuration-directory](https://code.claude.com/docs/en/claude-directory) and
[environment-variable](https://code.claude.com/docs/en/env-vars) references, and the event schema in
[`InstructionsLoaded`](https://code.claude.com/docs/en/hooks#instructionsloaded). The settings and
hooks references also establish managed precedence, hook merging, and the fact that a project-level
hook disable cannot override managed hooks; this is why effective pre-launch enumeration is a gate.

First validate the exact scratch target in both the observer PowerShell window and the separate
host terminal. The #153 resolution must replace the receipt blocker and placeholders below with
the recorded creation-time values. Before that replacement can run, it must reject every
non-local/aliased spelling and bind the project/install, config, build-output, and real-profile
directories by handle-final volume-GUID path and volume-serial/file ID. Every equality, nesting,
real-profile, Git-ancestry, write-parent, and cleanup decision must use those physical facts; a
`Resolve-Path`/`FullName` string is only a secondary spelling check. The receipt must bind the exact
case-preserved caller spelling and the handle-final facts. The preparation and preflight negative
suite must reject `\\localhost\c$`, SUBST, 8.3, nested-root, under-profile, and case-mismatched
fixtures. If any handle-final, ancestor, or effective case check is unavailable, stay blocked. This
prevents an existing non-git consumer or a substituted project from becoming the serial fixture:

```powershell
foreach ($StaleUatFunction in @(
    'Assert-UatScratchReceipt', 'Assert-UatFenceReady',
    'Get-HostMutationSurfaceSnapshot', 'Get-ContainedConfigStateSnapshot',
    'Test-ResolutionContainmentReceipt', 'Invoke-ContainedClaude',
    'Clear-InstructionFixture', 'Write-InstructionFixture', 'Set-RowFixture',
    'Get-InstructionSnapshot', 'Get-ProtectedRootSnapshot')) {
  Remove-Item -LiteralPath ("Function:\$StaleUatFunction") -Force `
    -ErrorAction SilentlyContinue
}
foreach ($StaleUatVariable in @(
    'ExpectedScratchReceiptHash', 'ExpectedScratchNonce',
    'ExpectedUatFenceGuardHash', 'ResolutionContainmentReceipt',
    'ResolutionLaunchArguments', 'ResolutionExpectedAuthMethod',
    'ResolutionExpectedApiProvider', 'Proj', 'ScratchHome', 'ClaudeConfigDir',
    'FreshBuildRoot', 'ProjInput', 'ScratchHomeInput', 'ClaudeConfigInput',
    'FreshBuildInput', 'ProjFacts', 'ScratchHomeFacts', 'ClaudeConfigFacts',
    'FreshBuildFacts', 'RealHome', 'RealHomeFacts', 'ExpectedSkillHashes',
    'SkillHashesBefore')) {
  Remove-Variable -Name $StaleUatVariable -Force -ErrorAction SilentlyContinue
}
function Assert-UatScratchReceipt {
  throw 'BLOCKED: #153 has not installed the receipt-bound scratch guard in this process.'
}
function Assert-UatFenceReady {
  throw 'BLOCKED: #153 has not installed the hash-bound UAT fence guard in this process.'
}
throw 'BLOCKED: #153 must replace this guard only with committed handle-final root identity, ancestry, case, and receipt-v3 checks.'
if (-not ('SkillMeshUat.NativeFileIdentity' -as [type])) {
  Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;
namespace SkillMeshUat {
  [StructLayout(LayoutKind.Sequential)]
  public struct ByHandleFileInformation {
    public uint FileAttributes;
    public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
    public uint VolumeSerialNumber;
    public uint FileSizeHigh;
    public uint FileSizeLow;
    public uint NumberOfLinks;
    public uint FileIndexHigh;
    public uint FileIndexLow;
  }
  public static class NativeFileIdentity {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true,
      EntryPoint = "CreateFileW")]
    public static extern SafeFileHandle CreateFile(
      string name, uint access, FileShare share, IntPtr security,
      FileMode mode, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool GetFileInformationByHandle(
      SafeFileHandle handle, out ByHandleFileInformation information);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true,
      EntryPoint = "GetFinalPathNameByHandleW")]
    public static extern uint GetFinalPathNameByHandle(
      SafeFileHandle handle, StringBuilder path, uint capacity, uint flags);
  }
}
'@ -ErrorAction Stop
}
function Get-DirectoryFileIdentity([string]$Path, [string]$Label) {
  $DirectoryItem = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if (-not $DirectoryItem.PSIsContainer) {
    throw "$Label is not a directory: $Path"
  }
  $Handle = [SkillMeshUat.NativeFileIdentity]::CreateFile(
    $DirectoryItem.FullName, 0, [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete,
    [IntPtr]::Zero, [IO.FileMode]::Open, 0x02000000, [IntPtr]::Zero)
  if ($Handle.IsInvalid) {
    $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    $Handle.Dispose()
    throw [ComponentModel.Win32Exception]::new(
      $ErrorCode, "Cannot open $Label identity handle: $Path")
  }
  try {
    $Information = New-Object SkillMeshUat.ByHandleFileInformation
    if (-not [SkillMeshUat.NativeFileIdentity]::GetFileInformationByHandle(
        $Handle, [ref]$Information)) {
      $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
      throw [ComponentModel.Win32Exception]::new(
        $ErrorCode, "Cannot read $Label identity: $Path")
    }
    return ('{0:X8}:{1:X8}{2:X8}' -f $Information.VolumeSerialNumber,
      $Information.FileIndexHigh, $Information.FileIndexLow)
  } finally {
    $Handle.Dispose()
  }
}
function Get-DirectoryHandleFacts([string]$Path, [string]$Label) {
  $DirectoryItem = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if (-not $DirectoryItem.PSIsContainer) {
    throw "$Label is not a directory: $Path"
  }
  $Identity = Get-DirectoryFileIdentity $DirectoryItem.FullName $Label
  try {
    $CallerPath = [IO.Path]::GetFullPath([string]$Path).TrimEnd('\')
  } catch {
    throw "$Label caller path cannot be normalized: $Path"
  }
  $Handle = [SkillMeshUat.NativeFileIdentity]::CreateFile(
    $DirectoryItem.FullName, 0, [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete,
    [IntPtr]::Zero, [IO.FileMode]::Open, 0x02000000, [IntPtr]::Zero)
  if ($Handle.IsInvalid) {
    $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    $Handle.Dispose()
    throw [ComponentModel.Win32Exception]::new(
      $ErrorCode, "Cannot open $Label final-path handle: $Path")
  }
  try {
    $DosBuffer = New-Object Text.StringBuilder 32768
    $DosLength = [SkillMeshUat.NativeFileIdentity]::GetFinalPathNameByHandle(
      $Handle, $DosBuffer, $DosBuffer.Capacity, 0x0)
    if ($DosLength -eq 0 -or $DosLength -ge $DosBuffer.Capacity) {
      $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
      throw [ComponentModel.Win32Exception]::new(
        $ErrorCode, "Cannot resolve $Label into the local DOS namespace: $Path")
    }
    $DosFinalPath = $DosBuffer.ToString().TrimEnd('\')
    if ($DosFinalPath -cnotmatch '^\\\\\?\\[A-Za-z]:\\' -or
        $CallerPath -cne $DosFinalPath.Substring(4)) {
      throw "$Label must use its exact case-preserved local long path: $Path"
    }
    $Buffer = New-Object Text.StringBuilder 32768
    $FinalLength = [SkillMeshUat.NativeFileIdentity]::GetFinalPathNameByHandle(
      $Handle, $Buffer, $Buffer.Capacity, 0x1)
    if ($FinalLength -eq 0 -or $FinalLength -ge $Buffer.Capacity) {
      $ErrorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
      throw [ComponentModel.Win32Exception]::new(
        $ErrorCode, "Cannot resolve $Label into the local volume-GUID namespace: $Path")
    }
    $FinalPath = $Buffer.ToString().TrimEnd('\')
    if ($FinalPath -cnotmatch `
        '^\\\\\?\\Volume\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}(?:\\|$)') {
      throw "$Label did not resolve to a local volume-GUID path: $FinalPath"
    }
    return [pscustomobject]@{
      Identity = $Identity
      FinalPath = $FinalPath
      DosPath = $DosFinalPath.Substring(4)
    }
  } finally {
    $Handle.Dispose()
  }
}
function Test-FinalPathWithin([string]$Candidate, [string]$Container) {
  return ($Candidate.Equals($Container, [StringComparison]::Ordinal) -or
          $Candidate.StartsWith($Container + '\', [StringComparison]::Ordinal))
}
$ProjInput = '<scratch-project>'
$ScratchHomeInput = '<scratch-home>'
$ClaudeConfigInput = '<scratch-claude-config>'
$FreshBuildInput = '<fresh-build-output>'
$ProjItem = Get-Item -LiteralPath `
  (Resolve-Path -LiteralPath $ProjInput -ErrorAction Stop).Path -Force -ErrorAction Stop
$ScratchHomeItem = Get-Item -LiteralPath `
  (Resolve-Path -LiteralPath $ScratchHomeInput -ErrorAction Stop).Path -Force -ErrorAction Stop
$ClaudeConfigItem = Get-Item -LiteralPath `
  (Resolve-Path -LiteralPath $ClaudeConfigInput -ErrorAction Stop).Path `
  -Force -ErrorAction Stop
$FreshBuildItem = Get-Item -LiteralPath `
  (Resolve-Path -LiteralPath $FreshBuildInput -ErrorAction Stop).Path `
  -Force -ErrorAction Stop
if (-not $ProjItem.PSIsContainer -or $null -eq $ProjItem.Parent -or
    -not $ScratchHomeItem.PSIsContainer -or $null -eq $ScratchHomeItem.Parent -or
    -not $ClaudeConfigItem.PSIsContainer -or $null -eq $ClaudeConfigItem.Parent -or
    -not $FreshBuildItem.PSIsContainer -or $null -eq $FreshBuildItem.Parent) {
  throw 'Scratch roots must be non-root directories.'
}
$Proj = $ProjItem.FullName.TrimEnd('\')
$ScratchHome = $ScratchHomeItem.FullName.TrimEnd('\')
$ClaudeConfigDir = $ClaudeConfigItem.FullName.TrimEnd('\')
$FreshBuildRoot = $FreshBuildItem.FullName.TrimEnd('\')
$RealHomeItem = Get-Item -LiteralPath (Resolve-Path -LiteralPath `
  ([Environment]::GetFolderPath('UserProfile')) -ErrorAction Stop).Path `
  -Force -ErrorAction Stop
$RealHome = $RealHomeItem.FullName.TrimEnd('\')
$ProjFacts = Get-DirectoryHandleFacts $ProjInput 'scratch project'
$ScratchHomeFacts = Get-DirectoryHandleFacts $ScratchHomeInput 'scratch install home'
$ClaudeConfigFacts = Get-DirectoryHandleFacts $ClaudeConfigInput 'scratch Claude config'
$FreshBuildFacts = Get-DirectoryHandleFacts $FreshBuildInput 'fresh build output'
$RealHomeFacts = Get-DirectoryHandleFacts $RealHome 'real user profile'
if ($ProjFacts.Identity -cne $ScratchHomeFacts.Identity -or
    -not $ProjFacts.FinalPath.Equals(
      $ScratchHomeFacts.FinalPath, [StringComparison]::Ordinal)) {
  throw 'Scratch project must be the verified scratch install home.'
}
$DisposableFacts = @($ProjFacts, $ClaudeConfigFacts, $FreshBuildFacts)
foreach ($DisposableFact in $DisposableFacts) {
  if ((Test-FinalPathWithin $DisposableFact.FinalPath $RealHomeFacts.FinalPath) -or
      (Test-FinalPathWithin $RealHomeFacts.FinalPath $DisposableFact.FinalPath)) {
    throw 'A disposable root is inside or above the real home.'
  }
}
for ($LeftIndex = 0; $LeftIndex -lt $DisposableFacts.Count; $LeftIndex++) {
  for ($RightIndex = $LeftIndex + 1;
       $RightIndex -lt $DisposableFacts.Count; $RightIndex++) {
    if ($DisposableFacts[$LeftIndex].Identity -ceq
          $DisposableFacts[$RightIndex].Identity -or
        (Test-FinalPathWithin $DisposableFacts[$LeftIndex].FinalPath `
          $DisposableFacts[$RightIndex].FinalPath) -or
        (Test-FinalPathWithin $DisposableFacts[$RightIndex].FinalPath `
          $DisposableFacts[$LeftIndex].FinalPath)) {
      throw 'Disposable project, config, and build roots must be distinct and non-nested.'
    }
  }
}
function Test-LinkedItem($Item) {
  return ((($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or
          -not [String]::IsNullOrEmpty([string]$Item.LinkType))
}
function Assert-RegularUnlinkedFile($Path, $Label) {
  $Item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf) -or (Test-LinkedItem $Item)) {
    throw "Refusing non-file or linked ${Label}: $Path"
  }
  return $Item
}
function Get-CanonicalAbsolutePath($Path, $Label) {
  $PathText = [string]$Path
  if ([String]::IsNullOrWhiteSpace($PathText)) {
    throw "$Label path is empty."
  }
  $IsDriveAbsolute = $PathText -cmatch '^[A-Za-z]:\\'
  if (-not $IsDriveAbsolute) {
    throw "$Label path is not a direct local drive-absolute spelling: $PathText"
  }
  try {
    $FullPath = [IO.Path]::GetFullPath($PathText)
  } catch {
    throw "$Label path cannot be normalized: $PathText"
  }
  if (-not $PathText.Equals($FullPath, [StringComparison]::Ordinal)) {
    throw "$Label path is relative, aliased, case-mismatched, or non-canonical: $Path"
  }
  return $FullPath
}
function Assert-UnlinkedPathAncestry($Path, $Label) {
  $RootItem = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if (-not $RootItem.PSIsContainer -or $null -eq $RootItem.Parent) {
    throw "$Label must be a non-root directory."
  }
  $Ancestor = $RootItem
  while ($null -ne $Ancestor) {
    if (Test-LinkedItem $Ancestor) {
      throw "$Label has a linked path component: $($Ancestor.FullName)"
    }
    $Ancestor = $Ancestor.Parent
  }
  return $RootItem
}

$GitCommand = (Get-Command git -CommandType Application -ErrorAction Stop).Source
function Assert-OutsideGitWorktree([string]$Path, [string]$Label) {
  Assert-UnlinkedPathAncestry $Path $Label | Out-Null
  $Cursor = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  while ($null -ne $Cursor) {
    if (Test-LinkedItem $Cursor) {
      throw "$Label has a linked component: $($Cursor.FullName)"
    }
    if (Test-Path -LiteralPath (Join-Path $Cursor.FullName '.git')) {
      throw "$Label must be outside every git worktree: $($Cursor.FullName)"
    }
    $Cursor = $Cursor.Parent
  }
  $PriorErrorActionPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = 'Continue' # PS 5.1 can surface native stderr as NativeCommandError
    $GitProbeOutput = @(& $GitCommand -C $Path rev-parse --show-toplevel 2>&1 |
      ForEach-Object { [string]$_ })
    $GitProbeExit = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $PriorErrorActionPreference
  }
  $GitProbeText = $GitProbeOutput -join "`n"
  if ($GitProbeExit -ne 128 -or $GitProbeOutput.Count -ne 1 -or
      $GitProbeText -cnotmatch '^fatal: not a git repository \(or any of the parent directories\): \.git$') {
    throw "$Label Git worktree probe was indeterminate (exit $GitProbeExit)."
  }
}
Assert-OutsideGitWorktree $Proj 'scratch project'
Assert-OutsideGitWorktree $ClaudeConfigDir 'scratch Claude config'
Assert-OutsideGitWorktree $FreshBuildRoot 'fresh build output'
throw 'BLOCKED: #153 must commit the creation-time receipt and fence-guard hashes here.'
$ExpectedScratchReceiptHash = '<issue-153-recorded-creation-receipt-sha256>'
$ExpectedScratchNonce = '<issue-153-recorded-random-nonce>'
$ExpectedUatFenceGuardHash = '<issue-153-recorded-fence-guard-sha256>'
function Assert-UatScratchReceipt {
  Assert-UnlinkedPathAncestry $Proj 'receipt-bound scratch project' | Out-Null
  Assert-UnlinkedPathAncestry $ClaudeConfigDir 'receipt-bound scratch config' | Out-Null
  Assert-UnlinkedPathAncestry $FreshBuildRoot 'receipt-bound fresh build output' | Out-Null
  Assert-OutsideGitWorktree $Proj 'receipt-bound scratch project'
  Assert-OutsideGitWorktree $ClaudeConfigDir 'receipt-bound scratch config'
  Assert-OutsideGitWorktree $FreshBuildRoot 'receipt-bound fresh build output'
  $CurrentProjFacts = Get-DirectoryHandleFacts $Proj 'current scratch project'
  $CurrentConfigFacts = Get-DirectoryHandleFacts $ClaudeConfigDir `
    'current scratch Claude config'
  $CurrentBuildFacts = Get-DirectoryHandleFacts $FreshBuildRoot `
    'current fresh build output'
  $CurrentRealHomeFacts = Get-DirectoryHandleFacts $RealHome 'current real user profile'
  if ($CurrentProjFacts.Identity -cne $ProjFacts.Identity -or
      -not $CurrentProjFacts.FinalPath.Equals(
        $ProjFacts.FinalPath, [StringComparison]::Ordinal) -or
      $CurrentConfigFacts.Identity -cne $ClaudeConfigFacts.Identity -or
      -not $CurrentConfigFacts.FinalPath.Equals(
        $ClaudeConfigFacts.FinalPath, [StringComparison]::Ordinal) -or
      $CurrentBuildFacts.Identity -cne $FreshBuildFacts.Identity -or
      -not $CurrentBuildFacts.FinalPath.Equals(
        $FreshBuildFacts.FinalPath, [StringComparison]::Ordinal) -or
      $CurrentRealHomeFacts.Identity -cne $RealHomeFacts.Identity -or
      -not $CurrentRealHomeFacts.FinalPath.Equals(
        $RealHomeFacts.FinalPath, [StringComparison]::Ordinal)) {
    throw 'A disposable root changed filesystem identity after preflight.'
  }
  $CurrentDisposableFacts = @($CurrentProjFacts, $CurrentConfigFacts, $CurrentBuildFacts)
  foreach ($CurrentDisposableFact in $CurrentDisposableFacts) {
    if ((Test-FinalPathWithin $CurrentDisposableFact.FinalPath `
          $CurrentRealHomeFacts.FinalPath) -or
        (Test-FinalPathWithin $CurrentRealHomeFacts.FinalPath `
          $CurrentDisposableFact.FinalPath)) {
      throw 'A receipt-bound disposable root is inside or above the real home.'
    }
  }
  for ($LeftIndex = 0; $LeftIndex -lt $CurrentDisposableFacts.Count; $LeftIndex++) {
    for ($RightIndex = $LeftIndex + 1;
         $RightIndex -lt $CurrentDisposableFacts.Count; $RightIndex++) {
      if ($CurrentDisposableFacts[$LeftIndex].Identity -ceq
            $CurrentDisposableFacts[$RightIndex].Identity -or
          (Test-FinalPathWithin $CurrentDisposableFacts[$LeftIndex].FinalPath `
            $CurrentDisposableFacts[$RightIndex].FinalPath) -or
          (Test-FinalPathWithin $CurrentDisposableFacts[$RightIndex].FinalPath `
            $CurrentDisposableFacts[$LeftIndex].FinalPath)) {
        throw 'Receipt-bound project, config, and build roots are the same or nested.'
      }
    }
  }
  $ReceiptPath = Join-Path $Proj '.skill-mesh-phase-is-uat-receipt.json'
  Assert-RegularUnlinkedFile $ReceiptPath 'UAT scratch receipt' | Out-Null
  $ReceiptHash = (Get-FileHash -LiteralPath $ReceiptPath -Algorithm SHA256 `
                              -ErrorAction Stop).Hash
  if ($ExpectedScratchReceiptHash -cnotmatch '^[0-9A-F]{64}$' -or
      $ExpectedScratchNonce -cnotmatch `
        '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' -or
      $ReceiptHash -cne $ExpectedScratchReceiptHash) {
    throw 'Scratch receipt does not match the creation-time record on issue #153.'
  }
  $Receipt = Get-Content -LiteralPath $ReceiptPath -Raw -ErrorAction Stop |
    ConvertFrom-Json -ErrorAction Stop
  $ExpectedReceiptProperties = @(
    'schema', 'nonce', 'project_path', 'claude_config_path', 'build_output_path',
    'project_final_path', 'claude_config_final_path', 'build_output_final_path',
    'project_identity', 'claude_config_identity', 'build_output_identity',
    'real_home_final_path', 'real_home_identity',
    'fence_guard_sha256', 'created_utc'
  )
  $ReceiptProperties = @($Receipt.PSObject.Properties | ForEach-Object { $_.Name })
  $ReceiptPropertyDifference = @(Compare-Object $ExpectedReceiptProperties `
    $ReceiptProperties -CaseSensitive -ErrorAction Stop)
  $ParsedCreatedUtc = [DateTime]::MinValue
  $CreatedUtcIsExact = [DateTime]::TryParseExact(
    [string]$Receipt.created_utc, 'o', [Globalization.CultureInfo]::InvariantCulture,
    [Globalization.DateTimeStyles]::RoundtripKind, [ref]$ParsedCreatedUtc)
  $ReceiptProjectPath = Get-CanonicalAbsolutePath $Receipt.project_path `
    'receipt project root'
  $ReceiptConfigPath = Get-CanonicalAbsolutePath $Receipt.claude_config_path `
    'receipt Claude config root'
  $ReceiptBuildPath = Get-CanonicalAbsolutePath $Receipt.build_output_path `
    'receipt build output root'
  $ReceiptProjectFacts = Get-DirectoryHandleFacts $ReceiptProjectPath `
    'receipt project root'
  $ReceiptConfigFacts = Get-DirectoryHandleFacts $ReceiptConfigPath `
    'receipt Claude config root'
  $ReceiptBuildFacts = Get-DirectoryHandleFacts $ReceiptBuildPath `
    'receipt build output root'
  if ($ReceiptPropertyDifference.Count -ne 0 -or
      $Receipt.schema -cne 'skill-mesh/phase-is-uat-scratch/v3' -or
      $Receipt.nonce -cne $ExpectedScratchNonce -or -not $CreatedUtcIsExact -or
      $Receipt.project_path -cne $ProjInput -or
      $Receipt.claude_config_path -cne $ClaudeConfigInput -or
      $Receipt.build_output_path -cne $FreshBuildInput -or
      $Receipt.project_identity -cne $CurrentProjFacts.Identity -or
      $Receipt.claude_config_identity -cne $CurrentConfigFacts.Identity -or
      $Receipt.build_output_identity -cne $CurrentBuildFacts.Identity -or
      $Receipt.real_home_identity -cne $CurrentRealHomeFacts.Identity -or
      $Receipt.project_final_path -cne $CurrentProjFacts.FinalPath -or
      $Receipt.claude_config_final_path -cne $CurrentConfigFacts.FinalPath -or
      $Receipt.build_output_final_path -cne $CurrentBuildFacts.FinalPath -or
      $Receipt.real_home_final_path -cne $CurrentRealHomeFacts.FinalPath -or
      $ReceiptProjectPath -cne $Proj -or
      $ReceiptConfigPath -cne $ClaudeConfigDir -or
      $ReceiptBuildPath -cne $FreshBuildRoot -or
      $Receipt.fence_guard_sha256 -cne $ExpectedUatFenceGuardHash -or
      $ExpectedUatFenceGuardHash -cnotmatch '^[0-9A-F]{64}$' -or
      $ReceiptProjectFacts.Identity -cne $CurrentProjFacts.Identity -or
      -not $ReceiptProjectFacts.FinalPath.Equals(
        $CurrentProjFacts.FinalPath, [StringComparison]::Ordinal) -or
      $ReceiptConfigFacts.Identity -cne $CurrentConfigFacts.Identity -or
      -not $ReceiptConfigFacts.FinalPath.Equals(
        $CurrentConfigFacts.FinalPath, [StringComparison]::Ordinal) -or
      $ReceiptBuildFacts.Identity -cne $CurrentBuildFacts.Identity -or
      -not $ReceiptBuildFacts.FinalPath.Equals(
        $CurrentBuildFacts.FinalPath, [StringComparison]::Ordinal)) {
    $ReceiptPropertyDifference
    throw 'Scratch receipt fields do not bind the validated disposable roots.'
  }
  return $true
}
function Assert-UatFenceReady {
  $GuardCommand = Get-Command Assert-UatFenceReady -CommandType Function `
    -ErrorAction Stop
  $GuardBytes = [Text.Encoding]::UTF8.GetBytes($GuardCommand.ScriptBlock.ToString())
  $GuardHash = [BitConverter]::ToString(
    [Security.Cryptography.SHA256]::Create().ComputeHash($GuardBytes)).Replace('-', '')
  if ($ExpectedUatFenceGuardHash -cnotmatch '^[0-9A-F]{64}$' -or
      $GuardHash -cne $ExpectedUatFenceGuardHash) {
    throw 'The live UAT fence guard does not match its receipt-bound script hash.'
  }
  $ReceiptResult = @(Assert-UatScratchReceipt)
  if ($ReceiptResult.Count -ne 1 -or $ReceiptResult[0] -isnot [bool] -or
      $ReceiptResult[0] -cne $true) {
    throw 'The UAT scratch receipt guard did not return exactly one True result.'
  }
  return $true
}
$InitialFenceResult = @(Assert-UatFenceReady)
if ($InitialFenceResult.Count -ne 1 -or $InitialFenceResult[0] -isnot [bool] -or
    $InitialFenceResult[0] -cne $true) {
  throw 'Initial UAT fence guard did not return exactly one True result.'
}
$LedgerPath = Join-Path $Proj '.skill-mesh-install.json'
Assert-RegularUnlinkedFile $LedgerPath 'scratch-install ledger' | Out-Null
$Ledger = Get-Content -LiteralPath $LedgerPath -Raw -ErrorAction Stop | ConvertFrom-Json
if ($Ledger.tool -cne 'skill-mesh' -or $null -eq $Ledger.installs.claude) {
  throw 'Verified claude scratch-install ledger is absent.'
}
$WriterFiles = @(
  '.claude\skills\plan-init\SKILL.md', '.claude\skills\plan-init\core.md',
  '.claude\skills\repo-update\SKILL.md', '.claude\skills\repo-update\core.md'
)
foreach ($relative in $WriterFiles) {
  $WriterPath = Join-Path $Proj $relative
  Assert-RegularUnlinkedFile $WriterPath 'writer file' | Out-Null
  $CurrentPath = (Get-Item -LiteralPath $WriterPath -Force -ErrorAction Stop).FullName
  while ($CurrentPath.Equals($Proj, [StringComparison]::Ordinal) -or
         $CurrentPath.StartsWith($Proj + '\', [StringComparison]::Ordinal)) {
    $Node = Get-Item -LiteralPath $CurrentPath -Force -ErrorAction Stop
    if (Test-LinkedItem $Node) {
      throw "Refusing a writer path with a linked component: $($Node.FullName)"
    }
    if ($CurrentPath.Equals($Proj, [StringComparison]::Ordinal)) { break }
    $CurrentPath = [IO.Path]::GetDirectoryName($CurrentPath)
  }
}
$ClaudeCommandInfo = Get-Command claude.exe -All -CommandType Application `
                                -ErrorAction Stop | Select-Object -First 1
$ClaudeCommand = $ClaudeCommandInfo.Source
if (-not [IO.Path]::IsPathRooted($ClaudeCommand)) {
  throw 'Claude executable path is not absolute.'
}
Assert-UnlinkedPathAncestry (Split-Path -Parent $ClaudeCommand) `
  'Claude executable parent' | Out-Null
Assert-RegularUnlinkedFile $ClaudeCommand 'Claude executable' | Out-Null
$ClaudeCommandHash = (Get-FileHash -LiteralPath $ClaudeCommand -Algorithm SHA256 `
                                  -ErrorAction Stop).Hash
$ClaudeVersionInfo = (Get-Item -LiteralPath $ClaudeCommand -Force -ErrorAction Stop).VersionInfo
if ($ClaudeCommandHash -cne 'A708BA811C4CC46907DF358E22F2AA6DA3DBC28192747E4D3C4A0869752FE722' -or
    $ClaudeVersionInfo.ProductName -cne 'Claude Code' -or
    $ClaudeVersionInfo.ProductVersion -cne '2.1.223.0') {
  throw 'Claude executable bytes/metadata differ from the audited Step-109 host.'
}
```

The Claude executable pin (`2.1.223`, hash above) was measured during the post-merge transcript
audit. It prevents an alias/function/path shadow from bypassing the containment arguments; a host
upgrade requires an explicit re-audit and pin update before Step 109 runs.

Keep the observer window open. Capture the two writers' installed bytes before the first row:

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound installed-writer preflight here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$ObservedSkillFiles = @(
  'plan-init\SKILL.md', 'plan-init\core.md',
  'repo-update\SKILL.md', 'repo-update\core.md'
)
function Get-ObservedSkillHashes {
  $ObservedSkillFiles | ForEach-Object {
    $ObservedPath = Join-Path $Proj ('.claude\skills\' + $_)
    Assert-RegularUnlinkedFile $ObservedPath 'observed writer file' | Out-Null
    $Digest = (Get-FileHash -LiteralPath $ObservedPath -Algorithm SHA256 `
                            -ErrorAction Stop).Hash
    if ($Digest -cnotmatch '^[0-9A-F]{64}$') {
      throw "Invalid SHA-256 result: $ObservedPath"
    }
    '{0} {1}' -f $_, $Digest
  }
}
$ExpectedSkillHashes = @(
  'plan-init\SKILL.md A1739A4E3D6764AE708404C3B40B74AE34183869C4B62C30AA8FCDA0696EAD9D',
  'plan-init\core.md 054DE3D99002DBA86A9A64C7CC65183B261593E2971F73F9301FF441B0196920',
  'repo-update\SKILL.md 3D101E75745F9E0D8965AE71BDC1B83F726CE7D6A8E4DCC2344740A1CC67597D',
  'repo-update\core.md B56A59F8373263A4F70CE77E23DB61310A9DC81BE8202881DA83CBB0A2F1AAA4'
)
$SkillHashesBefore = @(Get-ObservedSkillHashes)
$CurrencyDifference = @(Compare-Object $ExpectedSkillHashes $SkillHashesBefore `
                                      -CaseSensitive -ErrorAction Stop)
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
separate host terminal, not the observer window** retained for hashes and fixtures. The selected
resolution must replace the unconditional guard below with its committed, exact ordered argument
list plus verified hashes/content for the empty MCP config and preventive settings/hook artifacts.
That replacement must reject duplicate/unknown flags and every authority-broadening option; a
runtime-supplied array is not evidence. It must also bind the pre-launch effective-configuration
inventory, reject every managed/plugin/session hook or setting not explicitly reviewed, and prove
the effective managed MCP configuration is absent or empty. It must enumerate organization-wide
managed instructions (including managed `CLAUDE.md`, managed `claudeMd`, and policy/rule content),
managed skills, and every project ancestor's `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/**`,
same-name skill, and dynamic-context preprocessing surface through the physical volume root. Reject
every source except the row's root fixture and the two receipt-pinned writer skills; reject managed
or ancestor definitions of either writer and every managed/ancestor-skill shell preprocessing path
before the first Skill invocation. If the pinned host cannot expose any of those sources without
starting a session, the launch remains blocked. It must also reject every settings-file `env` assignment to a protected
isolation key, because those values can replace inherited shell values during startup. Use only the
distinct disposable `$ClaudeConfigDir` for settings, plugins, credentials, history and temp state;
on Windows that means either a process-only `CLAUDE_CODE_OAUTH_TOKEN` or a login performed directly
into that scratch config. Never copy, print, or hash the ambient credential file. The committed
receipt must enumerate and reject every competing credential/provider-selection environment
variable supported by the pinned release, including direct API-key/token and Bedrock, Vertex,
Foundry, Mantle, Anthropic-AWS, host-managed-provider, workspace, mTLS client-certificate,
profile, federation, and custom-base-URL paths. The receipt must also bind the one expected
`authMethod` and `apiProvider`; an intentionally selected mTLS mode must instead pin regular,
unlinked certificate/key files below the isolated config root and update this default-reject list
in the same reviewed change. With the exact isolation environment and
launch root set and the pinned executable hash rechecked, the wrapper must run
`claude auth status`, require exit 0, and parse its default JSON output without recording that
output; `loggedIn` must be Boolean true and its method/provider must exactly equal the receipt.
A check run before containment is established is not evidence. Only the pinned path guard
(if process-based) and pinned delivery logger may be command-hook exceptions. The
committed `Get-ContainedConfigStateSnapshot` must return a deterministic inventory of every static
or prohibited startup surface under the isolated config root: receipt-pinned settings, hooks, MCP
configuration, managed-skill and plugin state, and authentication-mode configuration. It may
exclude only the resolution's explicit allowlist of mutable history, transcript, cache, and temp
paths. It must return at least one receipt-bound invariant record; an empty snapshot is not
evidence. The wrapper compares that inventory before and after every launch and revalidates the
same containment receipt after the process exits. The current blocked skeleton cannot launch:

```powershell
throw 'BLOCKED: #153 must commit an exact launch grammar and containment-artifact hashes here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
# The selected resolution replaces the throw with the exact $ResolutionLaunchArguments literal
# and $ResolutionContainmentReceipt, exact $ResolutionExpectedAuthMethod and
# $ResolutionExpectedApiProvider literals, plus closed-grammar/artifact/auth verification and committed
# Get-HostMutationSurfaceSnapshot, Get-ContainedConfigStateSnapshot, and
# Test-ResolutionContainmentReceipt functions. Do not define any of them ad hoc in the shell.
function Invoke-ContainedClaude(
    [string]$ExpectedRoot,
    [object[]]$AdditionalArguments,
    [string]$InstructionsLogPath) {
  $LiveFenceGuard = Get-Command Assert-UatFenceReady -CommandType Function `
    -ErrorAction Stop
  $LiveFenceResult = @(& $LiveFenceGuard)
  if ($LiveFenceResult.Count -ne 1 -or $LiveFenceResult[0] -isnot [bool] -or
      $LiveFenceResult[0] -cne $true) {
    throw 'Contained Claude launch fence did not return exactly one True.'
  }
  $ResolutionArgsVariable = Get-Variable -Name ResolutionLaunchArguments `
    -ErrorAction SilentlyContinue
  $ResolutionReceiptVariable = Get-Variable -Name ResolutionContainmentReceipt `
    -ErrorAction SilentlyContinue
  $ResolutionAuthMethodVariable = Get-Variable -Name ResolutionExpectedAuthMethod `
    -ErrorAction SilentlyContinue
  $ResolutionApiProviderVariable = Get-Variable -Name ResolutionExpectedApiProvider `
    -ErrorAction SilentlyContinue
  foreach ($RequiredFunction in @(
      'Get-HostMutationSurfaceSnapshot', 'Get-ContainedConfigStateSnapshot',
      'Test-ResolutionContainmentReceipt', 'Assert-UatScratchReceipt')) {
    if ($null -eq (Get-Command $RequiredFunction -CommandType Function `
                                -ErrorAction SilentlyContinue)) {
      throw "Resolution omitted reviewed function: $RequiredFunction"
    }
  }
  if ($null -eq $ResolutionArgsVariable -or $null -eq $ResolutionReceiptVariable -or
      $ResolutionReceiptVariable.Value -isnot [string] -or
      $ResolutionReceiptVariable.Value -cnotmatch '^[0-9A-F]{64}$' -or
      $null -eq $ResolutionAuthMethodVariable -or
      $ResolutionAuthMethodVariable.Value -isnot [string] -or
      [String]::IsNullOrWhiteSpace($ResolutionAuthMethodVariable.Value) -or
      $null -eq $ResolutionApiProviderVariable -or
      $ResolutionApiProviderVariable.Value -isnot [string] -or
      [String]::IsNullOrWhiteSpace($ResolutionApiProviderVariable.Value)) {
    throw 'Resolution launch grammar/receipt/auth expectation is absent or malformed.'
  }
  $ResolutionExpectedAuthMethod = [string]$ResolutionAuthMethodVariable.Value
  $ResolutionExpectedApiProvider = [string]$ResolutionApiProviderVariable.Value
  $BaseArguments = @($ResolutionArgsVariable.Value)
  if ($BaseArguments.Count -eq 0 -or @($BaseArguments | Where-Object {
        $_ -isnot [string] -or [String]::IsNullOrWhiteSpace($_)
      }).Count -ne 0 -or @($BaseArguments | Where-Object {
        $_ -cmatch '^--session-id(?:=|$)'
      }).Count -ne 0 -or $BaseArguments -cnotcontains '--no-chrome') {
    throw 'Resolution launch grammar is empty, ill-typed, pre-binds a session id, or omits --no-chrome.'
  }
  $ExtraArguments = @($AdditionalArguments)
  $IsDeliveryLaunch = $ExtraArguments.Count -eq 2
  if (($ExtraArguments.Count -ne 0 -and -not $IsDeliveryLaunch) -or
      ($IsDeliveryLaunch -and ($ExtraArguments[0] -cne '--session-id' -or
        $ExtraArguments[1] -isnot [string] -or
        $ExtraArguments[1] -cnotmatch `
          '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'))) {
    throw 'Only one exact delivery --session-id pair may extend the committed grammar.'
  }
  $LaunchRoot = Get-CanonicalAbsolutePath $ExpectedRoot 'Claude launch root'
  $LaunchRootFacts = Get-DirectoryHandleFacts $LaunchRoot 'Claude launch root'
  $CurrentProjFacts = Get-DirectoryHandleFacts $Proj 'current scratch project'
  if ($LaunchRootFacts.Identity -cne $CurrentProjFacts.Identity -or
      -not $LaunchRootFacts.FinalPath.Equals(
        $CurrentProjFacts.FinalPath, [StringComparison]::Ordinal)) {
    throw 'Claude launch root does not match the validated scratch project.'
  }
  $ContainedConfigRoot = Get-CanonicalAbsolutePath $ClaudeConfigDir `
    'scratch Claude config'
  Assert-UnlinkedPathAncestry $ContainedConfigRoot 'scratch Claude config' | Out-Null
  $ContainedConfigFacts = Get-DirectoryHandleFacts $ContainedConfigRoot `
    'scratch Claude config'
  $CurrentConfigFacts = Get-DirectoryHandleFacts $ClaudeConfigDir `
    'current scratch Claude config'
  $CurrentRealHomeFacts = Get-DirectoryHandleFacts $RealHome 'current real user profile'
  if ($ContainedConfigFacts.Identity -cne $CurrentConfigFacts.Identity -or
      -not $ContainedConfigFacts.FinalPath.Equals(
        $CurrentConfigFacts.FinalPath, [StringComparison]::Ordinal) -or
      (Test-FinalPathWithin $ContainedConfigFacts.FinalPath `
        $LaunchRootFacts.FinalPath) -or
      (Test-FinalPathWithin $LaunchRootFacts.FinalPath `
        $ContainedConfigFacts.FinalPath) -or
      (Test-FinalPathWithin $ContainedConfigFacts.FinalPath `
        $CurrentRealHomeFacts.FinalPath)) {
    throw 'Claude config root is not the validated isolated scratch root.'
  }
  $ClaudeTempRoot = (Resolve-Path -LiteralPath `
    (Join-Path $ContainedConfigRoot 'tmp') -ErrorAction Stop).Path.TrimEnd('\')
  Assert-UnlinkedPathAncestry $ClaudeTempRoot 'scratch Claude temp root' | Out-Null
  $ClaudeTempFacts = Get-DirectoryHandleFacts $ClaudeTempRoot 'scratch Claude temp root'
  if ($ClaudeTempFacts.Identity -ceq $ContainedConfigFacts.Identity -or
      -not (Test-FinalPathWithin $ClaudeTempFacts.FinalPath `
        $ContainedConfigFacts.FinalPath)) {
    throw 'Claude temp root is not a proper child of the isolated config root.'
  }
  $ContainmentReceiptResult = @(Test-ResolutionContainmentReceipt $BaseArguments `
    $ResolutionReceiptVariable.Value $LaunchRoot $ContainedConfigRoot `
    $ResolutionExpectedAuthMethod $ResolutionExpectedApiProvider)
  if ($ContainmentReceiptResult.Count -ne 1 -or
      $ContainmentReceiptResult[0] -isnot [bool] -or
      $ContainmentReceiptResult[0] -cne $true) {
    throw 'Resolution containment receipt does not match committed arguments/artifacts/auth.'
  }
  if ($IsDeliveryLaunch) {
    $CanonicalInstructionsLog = Get-CanonicalAbsolutePath $InstructionsLogPath `
      'InstructionsLoaded log'
    $InstructionsLogParent = [IO.Path]::GetDirectoryName($CanonicalInstructionsLog)
    $InstructionsLogParentFacts = Get-DirectoryHandleFacts $InstructionsLogParent `
      'InstructionsLoaded log parent'
    if ($InstructionsLogParentFacts.Identity -cne $LaunchRootFacts.Identity -or
        -not $InstructionsLogParentFacts.FinalPath.Equals(
          $LaunchRootFacts.FinalPath, [StringComparison]::Ordinal) -or
        (Test-Path -LiteralPath $CanonicalInstructionsLog)) {
      throw 'Delivery log must be a new direct child of the scratch project.'
    }
  } elseif (-not [String]::IsNullOrEmpty($InstructionsLogPath)) {
    throw 'A non-delivery launch cannot receive an InstructionsLoaded log target.'
  }
  $ClearedIsolationNames = @(
    'FORCE_AUTOUPDATE_PLUGINS', 'CLAUDE_CODE_PLUGIN_SEED_DIR',
    'CLAUDE_CODE_SYNC_PLUGIN_INSTALL', 'CLAUDE_CODE_SYNC_SKILLS',
    'SKILL_MESH_UAT_INSTRUCTIONS_LOG'
  )
  $ForbiddenCredentialNames = @(
    'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_AWS_API_KEY',
    'ANTHROPIC_FOUNDRY_API_KEY', 'ANTHROPIC_FOUNDRY_AUTH_TOKEN',
    'AWS_BEARER_TOKEN_BEDROCK', 'ANTHROPIC_PROFILE',
    'ANTHROPIC_FEDERATION_RULE_ID', 'ANTHROPIC_ORGANIZATION_ID',
    'ANTHROPIC_WORKSPACE_ID', 'ANTHROPIC_BASE_URL', 'ANTHROPIC_AWS_BASE_URL',
    'ANTHROPIC_BEDROCK_BASE_URL', 'ANTHROPIC_BEDROCK_MANTLE_BASE_URL',
    'ANTHROPIC_VERTEX_BASE_URL', 'ANTHROPIC_FOUNDRY_BASE_URL',
    'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX',
    'CLAUDE_CODE_USE_FOUNDRY', 'CLAUDE_CODE_USE_MANTLE',
    'CLAUDE_CODE_USE_ANTHROPIC_AWS', 'ANTHROPIC_AWS_WORKSPACE_ID',
    'CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST', 'CLAUDE_CODE_CLIENT_CERT',
    'CLAUDE_CODE_CLIENT_KEY', 'CLAUDE_CODE_CLIENT_KEY_PASSPHRASE'
  )
  foreach ($ForbiddenAmbientName in @($ClearedIsolationNames) +
      @('CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE') + $ForbiddenCredentialNames) {
    if (-not [String]::IsNullOrEmpty(
        [Environment]::GetEnvironmentVariable($ForbiddenAmbientName, 'Process'))) {
      throw "Forbidden ambient Claude lifecycle override: $ForbiddenAmbientName"
    }
  }
  $IsolationValues = [ordered]@{
    'CLAUDE_CONFIG_DIR' = $ContainedConfigRoot
    'CLAUDE_CODE_TMPDIR' = $ClaudeTempRoot
    'CLAUDE_CODE_DISABLE_AUTO_MEMORY' = '1'
    'CLAUDE_CODE_DISABLE_BACKGROUND_TASKS' = '1'
    'CLAUDE_CODE_DISABLE_CRON' = '1'
    'CLAUDE_CODE_DISABLE_AGENT_VIEW' = '1'
    'CLAUDE_CODE_DISABLE_WORKFLOWS' = '1'
    'CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING' = '1'
    'CLAUDE_CODE_DISABLE_POLICY_SKILLS' = '1'
    'CLAUDE_DISABLE_ADOPT' = '1'
    'CLAUDE_CODE_AUTO_CONNECT_IDE' = 'false'
    'CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL' = '1'
    'CLAUDE_CODE_FORK_SUBAGENT' = '0'
    'CLAUDE_AUTO_BACKGROUND_TASKS' = '0'
    'CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS' = '0'
    'CLAUDE_CODE_ENABLE_BACKGROUND_PLUGIN_REFRESH' = '0'
    'CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE' = '0'
    'CLAUDE_CODE_SUBPROCESS_ENV_SCRUB' = '1'
    'CLAUDE_CODE_PLUGIN_CACHE_DIR' = (Join-Path $ContainedConfigRoot 'plugins')
    'ENABLE_CLAUDEAI_MCP_SERVERS' = 'false'
    'MCP_DISCOVERY_CACHE' = '0'
    'DISABLE_AUTOUPDATER' = '1'
    'DISABLE_UPDATES' = '1'
    'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC' = '1'
    'CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL' = '1'
  }
  if ($IsDeliveryLaunch) {
    $IsolationValues['SKILL_MESH_UAT_INSTRUCTIONS_LOG'] = $CanonicalInstructionsLog
  }
  $ClearedAtLaunchNames = @(@($ClearedIsolationNames) + $ForbiddenCredentialNames |
    Where-Object {
      $IsolationValues.Keys -cnotcontains $_
    })
  $PriorIsolationValues = @{}
  foreach ($Name in @($IsolationValues.Keys) + $ClearedAtLaunchNames) {
    $PriorIsolationValues[$Name] =
      [Environment]::GetEnvironmentVariable($Name, 'Process')
  }
  $HostMutationSurfaceBefore = @(Get-HostMutationSurfaceSnapshot)
  if ($HostMutationSurfaceBefore.Count -eq 0) {
    throw 'Host mutation-surface snapshot is empty.'
  }
  $ContainedConfigBefore = @(Get-ContainedConfigStateSnapshot $ContainedConfigRoot)
  if ($ContainedConfigBefore.Count -eq 0) {
    throw 'Contained config-state snapshot is empty.'
  }
  $PriorLocation = (Get-Location).ProviderPath
  $ClaudeExit = $null
  $LaunchFailure = $null
  try {
    foreach ($Name in $IsolationValues.Keys) {
      [Environment]::SetEnvironmentVariable($Name, $IsolationValues[$Name], 'Process')
    }
    foreach ($Name in $ClearedAtLaunchNames) {
      [Environment]::SetEnvironmentVariable($Name, $null, 'Process')
    }
    foreach ($Name in $IsolationValues.Keys) {
      $ObservedIsolationValue = [Environment]::GetEnvironmentVariable($Name, 'Process')
      if ($ObservedIsolationValue -cne [string]$IsolationValues[$Name]) {
        throw "Failed to set protected Claude environment value: $Name"
      }
    }
    foreach ($Name in $ClearedAtLaunchNames) {
      if ($null -ne [Environment]::GetEnvironmentVariable($Name, 'Process')) {
        throw "Failed to clear forbidden Claude environment value: $Name"
      }
    }
    $ReceiptBoundary = @(Assert-UatScratchReceipt)
    if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
        $ReceiptBoundary[0] -cne $true) {
      throw 'Pre-launch scratch receipt did not return exactly one True.'
    }
    Assert-UnlinkedPathAncestry $LaunchRoot 'Claude launch root' | Out-Null
    Assert-UnlinkedPathAncestry $ContainedConfigRoot 'scratch Claude config' | Out-Null
    Assert-UnlinkedPathAncestry $ClaudeTempRoot 'scratch Claude temp root' | Out-Null
    $ClaudeCommandHashAtLaunch = (Get-FileHash -LiteralPath $ClaudeCommand -Algorithm SHA256 `
      -ErrorAction Stop).Hash
    if ($ClaudeCommandHashAtLaunch -cne
        'A708BA811C4CC46907DF358E22F2AA6DA3DBC28192747E4D3C4A0869752FE722') {
      throw 'Claude executable bytes changed before launch.'
    }
    Set-Location -LiteralPath $LaunchRoot -ErrorAction Stop
    $ObservedLaunchRoot = (Get-Location).ProviderPath.TrimEnd('\')
    if (-not $ObservedLaunchRoot.Equals($LaunchRoot,
          [StringComparison]::Ordinal)) {
      throw 'Claude launch root does not match the validated scratch project.'
    }
    $LASTEXITCODE = $null
    $AuthStatusOutput = @(& $ClaudeCommand auth status 2>$null)
    $AuthStatusInvocationSucceeded = $?
    $AuthStatusExit = $LASTEXITCODE
    if (-not $AuthStatusInvocationSucceeded -or $null -eq $AuthStatusExit -or
        $AuthStatusExit -ne 0 -or $AuthStatusOutput.Count -eq 0) {
      throw 'Pinned Claude executable is not authenticated in the isolated configuration.'
    }
    try {
      $AuthStatusObject = (($AuthStatusOutput | Out-String) |
        ConvertFrom-Json -ErrorAction Stop)
    } catch {
      throw 'Pinned Claude auth status did not return valid JSON.'
    }
    $AuthStatusProperties = @($AuthStatusObject.PSObject.Properties |
      ForEach-Object { $_.Name })
    $MissingAuthStatusProperties = @(Compare-Object `
      @('loggedIn', 'authMethod', 'apiProvider') $AuthStatusProperties `
      -PassThru -ErrorAction Stop | Where-Object { $_.SideIndicator -ceq '<=' })
    if ($null -eq $AuthStatusObject -or $MissingAuthStatusProperties.Count -ne 0 -or
        $AuthStatusObject.loggedIn -isnot [bool] -or
        $AuthStatusObject.loggedIn -ne $true -or
        $AuthStatusObject.authMethod -isnot [string] -or
        $AuthStatusObject.apiProvider -isnot [string] -or
        $AuthStatusObject.authMethod -cne $ResolutionExpectedAuthMethod -or
        $AuthStatusObject.apiProvider -cne $ResolutionExpectedApiProvider) {
      throw 'Pinned Claude auth status did not match the receipt-bound authentication mode/provider.'
    }
    $ClaudeCommandHashAfterAuth = (Get-FileHash -LiteralPath $ClaudeCommand -Algorithm SHA256 `
      -ErrorAction Stop).Hash
    if ($ClaudeCommandHashAfterAuth -cne $ClaudeCommandHashAtLaunch) {
      throw 'Claude executable bytes changed during isolated authentication verification.'
    }
    $FinalArguments = @($BaseArguments) + $ExtraArguments
    $LASTEXITCODE = $null
    & $ClaudeCommand @FinalArguments
    $ClaudeInvocationSucceeded = $?
    $ClaudeExit = $LASTEXITCODE
    if (-not $ClaudeInvocationSucceeded -or $null -eq $ClaudeExit) {
      throw 'Pinned Claude native launch did not start and return an exit code.'
    }
    if ($IsDeliveryLaunch) {
      $LogDeadline = [DateTime]::UtcNow.AddSeconds(10)
      $LogIsClosed = $false
      do {
        if (Test-Path -LiteralPath $CanonicalInstructionsLog -PathType Leaf) {
          try {
            $LogStream = [IO.File]::Open($CanonicalInstructionsLog,
              [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
            try { $LogIsClosed = $LogStream.Length -gt 0 } finally { $LogStream.Dispose() }
          } catch [IO.IOException] { $LogIsClosed = $false }
        }
        if (-not $LogIsClosed) { Start-Sleep -Milliseconds 100 }
      } while (-not $LogIsClosed -and [DateTime]::UtcNow -lt $LogDeadline)
      if (-not $LogIsClosed) {
        throw 'Pinned InstructionsLoaded logger did not create one closed record in time.'
      }
    }
  } catch {
    $LaunchFailure = $_
  } finally {
    foreach ($Name in @($IsolationValues.Keys) + $ClearedAtLaunchNames) {
      [Environment]::SetEnvironmentVariable($Name, $PriorIsolationValues[$Name], 'Process')
    }
    Set-Location -LiteralPath $PriorLocation -ErrorAction Stop
  }
  $ContainedConfigAfter = @(Get-ContainedConfigStateSnapshot $ContainedConfigRoot)
  $ContainedConfigDifference = @(Compare-Object $ContainedConfigBefore `
                                                  $ContainedConfigAfter -CaseSensitive `
                                                  -ErrorAction Stop)
  $ContainmentReceiptAfterResult = @(Test-ResolutionContainmentReceipt $BaseArguments `
    $ResolutionReceiptVariable.Value $LaunchRoot $ContainedConfigRoot `
    $ResolutionExpectedAuthMethod $ResolutionExpectedApiProvider)
  $HostMutationSurfaceAfter = @(Get-HostMutationSurfaceSnapshot)
  $HostMutationDifference = @(Compare-Object $HostMutationSurfaceBefore `
                                             $HostMutationSurfaceAfter -CaseSensitive `
                                             -ErrorAction Stop)
  $ClaudeCommandHashAfter = (Get-FileHash -LiteralPath $ClaudeCommand -Algorithm SHA256 `
                                         -ErrorAction Stop).Hash
  if ($ContainedConfigDifference.Count -ne 0) {
    $ContainedConfigDifference
    throw 'Claude changed a static or prohibited surface inside the scratch config root.'
  }
  if ($ContainmentReceiptAfterResult.Count -ne 1 -or
      $ContainmentReceiptAfterResult[0] -isnot [bool] -or
      $ContainmentReceiptAfterResult[0] -cne $true) {
    throw 'Resolution containment receipt changed or became invalid during launch.'
  }
  if ($HostMutationDifference.Count -ne 0 -or
      $ClaudeCommandHashAfter -cne $ClaudeCommandHash) {
    $HostMutationDifference
    throw 'Claude changed an install/plugin host surface outside scratch.'
  }
  if ($null -ne $LaunchFailure) { throw $LaunchFailure }
  if ($ClaudeExit -ne 0) { throw "Claude exited $ClaudeExit." }
}
$NoAdditionalArguments = @()
Invoke-ContainedClaude -ExpectedRoot $Proj -AdditionalArguments $NoAdditionalArguments `
  -InstructionsLogPath $null
```

Stale same-named `plan-init` and `repo-update` skills exist in the personal
`~/.claude/skills` root and would be eligible under the default user + project + local sources.
The mandatory project-only setting source excludes them; do not omit or widen it. Leave them
untouched. Never install this profile into the real home to make the scratch copy win: on this
host that junction target contains 1,235 tracked files, and the existing ownership ledger lets a
reinstall overwrite owned files silently without `-Force`, backup, or prompt.

Project-only settings do **not** outrank managed skills. A managed same-name writer can win before
the native Base/core parser rejects the result, and managed-skill dynamic-context shell commands can
run during preprocessing outside the ordinary tool rail. The #153 pre-launch inventory must
therefore prove both writer names absent from the managed skill surface and reject any managed skill
shell-preprocessing path; post-invocation attribution is too late to contain either case.

For **each** writer invocation, capture that row's own native record. Set the `HostSupplied*`
values below from that record, never from the intended directory. One successful `Read(path)` is
not enough: every required core's Read result must start at line 1, reach the expected final line,
contain the skill-specific terminal line, carry no truncation marker, and reconstruct to bytes
whose SHA-256 equals the verified co-located core under #153's pinned native-payload normalization.
Every one of those Reads must occur after Skill invocation and before any response or non-read
behavior action:

**The hand-entered block below is a non-grading shape check, not mechanical ordering proof.** Issue
#153's resolution must replace it with a committed parser over one native session record. That
parser must bind the session/transcript identity, invoked skill name, host-supplied native Base,
generated-wrapper `Profile: claude`, matching `attributionSkill`, every required successful Read
result, and first response or non-read action to event indices satisfying `SkillIndex < ReadIndex <
FirstActionIndex` independently for each required core. It must reconstruct each complete captured
Read payload under a pinned normalization rule and compare its SHA-256 to the corresponding
verified on-disk core; merely computing or recording a payload hash is not equality evidence. Its
negative tests must mutate one middle payload line and, on a `repo-update` record, move only the
delegated `plan-init` Read after the first action; both cases must throw. Until that parser and its
negative tests land, this instrument remains blocked even when its manual
path/full/captured/on-disk-hash booleans are all true.

```powershell
throw 'BLOCKED: #153 must replace hand-entered core-read evidence with an ordered native-record parser.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$InvokedSkill = 'plan-init' # use repo-update on its rows
$HostSuppliedBase = '<host-supplied-base>'
$HostSuppliedCoreReads = @(
  [pscustomobject]@{
    Skill = 'plan-init'
    Path = '<host-supplied-successful-core-read-path>'
    StartLine = 1
    EndLine = 678
    WasTruncated = $false
    TerminalLine = "block plan-init's completion."
    CapturedPayloadHash = '<sha256-of-pinned-normalized-native-read-payload>'
  }
)
$ExpectedCoreHashes = @{
  'plan-init' = '054DE3D99002DBA86A9A64C7CC65183B261593E2971F73F9301FF441B0196920'
  'repo-update' = 'B56A59F8373263A4F70CE77E23DB61310A9DC81BE8202881DA83CBB0A2F1AAA4'
}
$ExpectedCoreLineCounts = @{ 'plan-init' = 678; 'repo-update' = 571 }
$ExpectedCoreTerminalLines = @{
  'plan-init' = "block plan-init's completion."
  'repo-update' = 'This re-derives verbs/ports from the current `CLAUDE.md` + plan and regenerates the `dev.code-workspace` tasks. Keep README/CLAUDE.md command + port mentions scrapable.'
}
if (-not $ExpectedCoreHashes.ContainsKey($InvokedSkill)) {
  throw "Unknown writer skill: $InvokedSkill"
}
$RequiredCoreSkills = if ($InvokedSkill -ceq 'repo-update') {
  @('repo-update', 'plan-init')
} else {
  @('plan-init')
}
$ExpectedSkillBase = (Resolve-Path -LiteralPath `
  (Join-Path $Proj ('.claude\skills\' + $InvokedSkill)) -ErrorAction Stop).Path.TrimEnd('\')
$LoadedSkillBase = (Get-CanonicalAbsolutePath $HostSuppliedBase `
  'host-supplied skill base').TrimEnd('\')
$BaseMatches = $LoadedSkillBase.Equals(
  $ExpectedSkillBase, [StringComparison]::Ordinal)
$BaseMatches
if (-not $BaseMatches) { throw 'Host loaded a different skill wrapper.' }
$RequiredReadProperties = @(
  'Skill', 'Path', 'StartLine', 'EndLine', 'WasTruncated', 'TerminalLine',
  'CapturedPayloadHash'
)
if (@($HostSuppliedCoreReads).Count -ne $RequiredCoreSkills.Count) {
  throw 'Native core-read evidence has an unexpected record count.'
}
foreach ($CoreSkill in $RequiredCoreSkills) {
  $ObservedReads = @($HostSuppliedCoreReads | Where-Object { $_.Skill -ceq $CoreSkill })
  if ($ObservedReads.Count -ne 1) {
    throw "Expected exactly one native core read for $CoreSkill."
  }
  $ObservedRead = $ObservedReads[0]
  $ObservedPropertyNames = @($ObservedRead.PSObject.Properties | ForEach-Object { $_.Name })
  $MissingReadProperties = @($RequiredReadProperties | Where-Object {
    $ObservedPropertyNames -cnotcontains $_
  })
  if ($MissingReadProperties.Count -ne 0 -or
      $ObservedRead.Skill -isnot [string] -or
      $ObservedRead.Path -isnot [string] -or
      $ObservedRead.StartLine -isnot [int] -or
      $ObservedRead.EndLine -isnot [int] -or
      $ObservedRead.WasTruncated -isnot [bool] -or
      $ObservedRead.TerminalLine -isnot [string] -or
      $ObservedRead.CapturedPayloadHash -isnot [string] -or
      $ObservedRead.CapturedPayloadHash -cnotmatch '^[0-9A-F]{64}$') {
    $MissingReadProperties
    throw "Native core-read evidence for $CoreSkill is incomplete or ill-typed."
  }
  $ExpectedCorePath = (Resolve-Path -LiteralPath (Join-Path $Proj `
    ('.claude\skills\' + $CoreSkill + '\core.md')) -ErrorAction Stop).Path
  $LoadedCoreReadPath = Get-CanonicalAbsolutePath $ObservedRead.Path `
    "host-supplied $CoreSkill core read"
  $CoreReadMatches = $LoadedCoreReadPath.Equals(
    $ExpectedCorePath, [StringComparison]::Ordinal)
  $CoreReadIsComplete = (($ObservedRead.StartLine -eq 1) -and
    ($ObservedRead.EndLine -eq $ExpectedCoreLineCounts[$CoreSkill]) -and
    ($ObservedRead.WasTruncated -ceq $false) -and
    $ObservedRead.TerminalLine.Equals(
      $ExpectedCoreTerminalLines[$CoreSkill], [StringComparison]::Ordinal))
  Assert-RegularUnlinkedFile $ExpectedCorePath 'loaded core' | Out-Null
  $LoadedCoreHash = (Get-FileHash -LiteralPath $ExpectedCorePath -Algorithm SHA256 `
                                 -ErrorAction Stop).Hash
  $CoreHashMatches = $LoadedCoreHash -ceq $ExpectedCoreHashes[$CoreSkill]
  $CapturedPayloadMatches = $ObservedRead.CapturedPayloadHash -ceq $LoadedCoreHash
  "$CoreSkill path=$CoreReadMatches full=$CoreReadIsComplete captured=$CapturedPayloadMatches hash=$CoreHashMatches"
  if (-not $CoreReadMatches -or -not $CoreReadIsComplete -or
      -not $CapturedPayloadMatches -or -not $CoreHashMatches) {
    throw "Host did not load the exact current $CoreSkill core in full."
  }
}
```

**Expect after #153 replaces the blocker:** the ordered native-record parser passes, followed by
`True` for the exact wrapper base and one all-true path/full/captured/hash row for `plan-init` on
rows 1–2. Rows 3–5 require two all-true rows: `repo-update` and the sibling `plan-init` owner it
cites for D10.
A complete `repo-update` read alone does not deliver the delegated contract. No row may borrow
another session's record. If a future UAT-mode change moves a count or terminal line, § 1 must be
rerun and this block updated together with the four hashes.

After the last row:

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound post-host hash fence here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$SkillHashesAfter = @(Get-ObservedSkillHashes)
$SkillHashDifference = @(Compare-Object $SkillHashesBefore $SkillHashesAfter `
                                        -CaseSensitive -ErrorAction Stop)
if ($SkillHashDifference.Count -ne 0) {
  $SkillHashDifference
  throw 'Installed writer bytes changed during Step 109.'
}
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
canonical standalone fact lines in the checker below verbatim. That makes the behavior grade
semantic rather than accepting a required phrase embedded in a negation or example.

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

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound fixture mutation rail here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$Sub = "# Scratch`n`n## Stack summary`n`nMarkdown. UAT preservation canary: keep this line.`n"

function Clear-InstructionFixture {
  $LiveFenceGuard = Get-Command Assert-UatFenceReady -CommandType Function `
    -ErrorAction Stop
  $LiveFenceResult = @(& $LiveFenceGuard)
  if ($LiveFenceResult.Count -ne 1 -or $LiveFenceResult[0] -isnot [bool] -or
      $LiveFenceResult[0] -cne $true) {
    throw 'Fixture-reset fence did not return exactly one True.'
  }
  $ExpectedFixtureRoot = (Resolve-Path -LiteralPath '<scratch-home>' `
    -ErrorAction Stop).Path.TrimEnd('\')
  if (-not $Proj.Equals($ExpectedFixtureRoot,
                        [StringComparison]::Ordinal)) {
    throw 'Scratch target changed; refusing fixture reset.'
  }
  Assert-UnlinkedPathAncestry $Proj 'fixture scratch root' | Out-Null
  foreach ($name in 'AGENTS.md','CLAUDE.md') {
    $path = Join-Path $Proj $name
    if (Test-Path -LiteralPath $path) {
      $item = Get-Item -LiteralPath $path -Force -ErrorAction Stop
      if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or
          (Test-LinkedItem $item)) {
        throw "Refusing to remove non-file or linked fixture path: $name"
      }
      $ReceiptBoundary = @(Assert-UatScratchReceipt)
      if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
          $ReceiptBoundary[0] -cne $true) {
        throw 'Pre-remove scratch receipt did not return exactly one True.'
      }
      Remove-Item -LiteralPath $path -Force -ErrorAction Stop
      Assert-UnlinkedPathAncestry $Proj 'fixture scratch root' | Out-Null
    }
  }
}

function Write-InstructionFixture([string]$Name, [string]$Text) {
  $LiveFenceGuard = Get-Command Assert-UatFenceReady -CommandType Function `
    -ErrorAction Stop
  $LiveFenceResult = @(& $LiveFenceGuard)
  if ($LiveFenceResult.Count -ne 1 -or $LiveFenceResult[0] -isnot [bool] -or
      $LiveFenceResult[0] -cne $true) {
    throw 'Fixture-write fence did not return exactly one True.'
  }
  if (@('AGENTS.md', 'CLAUDE.md') -cnotcontains $Name) {
    throw "Unexpected fixture filename: $Name"
  }
  $FixtureRoot = (Assert-UnlinkedPathAncestry $Proj `
    'fixture scratch root').FullName.TrimEnd('\')
  if (-not $FixtureRoot.Equals($Proj, [StringComparison]::Ordinal)) {
    throw 'Fixture scratch root changed before write.'
  }
  $FixturePath = Join-Path $FixtureRoot $Name
  if (Test-Path -LiteralPath $FixturePath) {
    throw "Fixture write target unexpectedly exists: $Name"
  }
  $ReceiptBoundary = @(Assert-UatScratchReceipt)
  if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
      $ReceiptBoundary[0] -cne $true) {
    throw 'Pre-write scratch receipt did not return exactly one True.'
  }
  [IO.File]::WriteAllText($FixturePath, $Text)
  $ReceiptBoundary = @(Assert-UatScratchReceipt)
  if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
      $ReceiptBoundary[0] -cne $true) {
    throw 'Post-write scratch receipt did not return exactly one True.'
  }
  Assert-UnlinkedPathAncestry $Proj 'fixture scratch root' | Out-Null
  Assert-RegularUnlinkedFile $FixturePath 'new fixture file' | Out-Null
}

function Set-RowFixture([ValidateSet(1,2,3,4,5)][int]$Row) {
  $LiveFenceGuard = Get-Command Assert-UatFenceReady -CommandType Function `
    -ErrorAction Stop
  $LiveFenceResult = @(& $LiveFenceGuard)
  if ($LiveFenceResult.Count -ne 1 -or $LiveFenceResult[0] -isnot [bool] -or
      $LiveFenceResult[0] -cne $true) {
    throw 'Row-fixture fence did not return exactly one True.'
  }
  Clear-InstructionFixture
  switch ($Row) {
    1 { } # both ABSENT
    2 { Write-InstructionFixture 'CLAUDE.md' $Sub }
    3 {
      Write-InstructionFixture 'AGENTS.md' $Sub
      Write-InstructionFixture 'CLAUDE.md' "@AGENTS.md`n"
    }
    4 { Write-InstructionFixture 'AGENTS.md' $Sub }
    5 {
      Write-InstructionFixture 'AGENTS.md' $Sub
      Write-InstructionFixture 'CLAUDE.md' `
        "# Scratch`n`n## Stack summary`n`nConflicting non-Markdown stack.`n"
    }
  }
  function Get-InstructionState($Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return 'ABSENT' }
    Assert-RegularUnlinkedFile $Path 'row fixture instruction file' | Out-Null
    $Bytes = [IO.File]::ReadAllBytes($Path)
    if ([Convert]::ToBase64String($Bytes) -ceq 'QEFHRU5UUy5tZAo=') { return 'POINTER' }
    $Text = [IO.File]::ReadAllText($Path)
    if ($Text -match '(?m)^## ') { return 'SUBSTANTIVE' }
    return 'OTHER'
  }
  $ExpectedPair = switch ($Row) {
    1 { 'ABSENT/ABSENT' }
    2 { 'ABSENT/SUBSTANTIVE' }
    3 { 'SUBSTANTIVE/POINTER' }
    4 { 'SUBSTANTIVE/ABSENT' }
    5 { 'SUBSTANTIVE/SUBSTANTIVE' }
  }
  $ActualPair = '{0}/{1}' -f
    (Get-InstructionState (Join-Path $Proj 'AGENTS.md')),
    (Get-InstructionState (Join-Path $Proj 'CLAUDE.md'))
  if ($ActualPair -cne $ExpectedPair) {
    throw "Row $Row fixture expected $ExpectedPair, got $ActualPair."
  }
  $ActualPair
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

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound snapshot rail here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
function Get-InstructionSnapshot($Dir) {
  $SnapshotRoot = (Assert-UnlinkedPathAncestry $Dir `
    'instruction snapshot root').FullName.TrimEnd('\')
  Get-ChildItem -LiteralPath $SnapshotRoot -File -ErrorAction Stop |
    Where-Object { $_.Name -ceq 'AGENTS.md' -or $_.Name -ceq 'CLAUDE.md' } |
    ForEach-Object {
      if (Test-LinkedItem $_) { throw "Refusing linked instruction file: $($_.FullName)" }
      $Digest = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256 `
                              -ErrorAction Stop).Hash
      if ($Digest -cnotmatch '^[0-9A-F]{64}$') {
        throw "Invalid SHA-256 result: $($_.FullName)"
      }
      '{0} {1}' -f $_.Name, $Digest
    } |
    Sort-Object
}

function Get-ProtectedRootSnapshot($Dir, [string[]]$ExcludedRelativePaths) {
  $Root = (Assert-UnlinkedPathAncestry $Dir `
    'protected snapshot root').FullName.TrimEnd('\')
  $Pending = New-Object 'System.Collections.Generic.Stack[string]'
  $Pending.Push($Root)
  $Snapshot = @()
  while ($Pending.Count -gt 0) {
    $Current = $Pending.Pop()
    foreach ($Child in Get-ChildItem -LiteralPath $Current -Force -ErrorAction Stop) {
      if (Test-LinkedItem $Child) {
        throw "Refusing a linked child in the protected root: $($Child.FullName)"
      }
      $Relative = $Child.FullName.Substring($Root.Length).TrimStart('\')
      if ($Child.PSIsContainer) {
        if ($ExcludedRelativePaths -ccontains $Relative) {
          throw "An allowed file path became a directory: $Relative"
        }
        $Snapshot += "D $Relative"
        $Pending.Push($Child.FullName)
      } elseif ($ExcludedRelativePaths -cnotcontains $Relative) {
        $Digest = (Get-FileHash -LiteralPath $Child.FullName -Algorithm SHA256 `
                                -ErrorAction Stop).Hash
        if ($Digest -cnotmatch '^[0-9A-F]{64}$') {
          throw "Invalid SHA-256 result: $($Child.FullName)"
        }
        $Snapshot += "F $Relative $($Child.Length) $Digest"
      }
    }
  }
  $Snapshot | Sort-Object
}

function Get-UnlinkedFilePaths($Dir) {
  $Root = (Assert-UnlinkedPathAncestry $Dir `
    'unlinked file-enumeration root').FullName.TrimEnd('\')
  $Pending = New-Object 'System.Collections.Generic.Stack[string]'
  $Pending.Push($Root)
  while ($Pending.Count -gt 0) {
    $Current = $Pending.Pop()
    foreach ($Child in Get-ChildItem -LiteralPath $Current -Force -ErrorAction Stop) {
      if (Test-LinkedItem $Child) {
        throw "Refusing a linked child during file enumeration: $($Child.FullName)"
      }
      if ($Child.PSIsContainer) {
        $Pending.Push($Child.FullName)
      } else {
        $Child.FullName
      }
    }
  }
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

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound post-action snapshot here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$after          = @(Get-InstructionSnapshot $Row)
$protectedAfter = @(Get-ProtectedRootSnapshot $Row $AllowedWrites)
$ProtectedDifference = @(Compare-Object $protectedBefore $protectedAfter `
                                        -CaseSensitive -ErrorAction Stop)
$InstructionDifference = @(Compare-Object $before $after `
                                          -CaseSensitive -ErrorAction Stop)
if ($ProtectedDifference.Count -ne 0) {
  $ProtectedDifference
  throw 'A path outside the row allowlist changed.'
}
$InstructionDifference
```

**Expect:** the protected-root comparison prints nothing on every row. The instruction comparison
shows row 1 adding both files; rows 2 and 5 print nothing; row 3 changes only `AGENTS.md`; row 4
changes `AGENTS.md` and adds `CLAUDE.md`. Capture both preimages for every row; § 2.2 separately
takes row 3's post-first-pass snapshot.

The preventive tool/path rail must have denied every non-allowlisted action before execution.
Also audit that invocation's native tool-action trace. For every Write/Edit target, preserve the
native spelling's case, open its existing parent by handle, require that parent's handle-final path
and file ID to equal the receipt-bound project root, and require the leaf name to be exact
case-sensitive membership in `$AllowedWrites`. `[IO.Path]::GetFullPath()` and textual membership in
`$AllowedWritePaths` are secondary checks only; any shell/process action, case mismatch, aliased
parent, or write outside that physical allowlist blocks the row.
Rows 2 and the fixed-point pass allow no write action at all. This trace requirement is what
catches an otherwise invisible byte-identical rewrite or a write-then-restore sequence.

### Instrument B — is `CLAUDE.md` D8's *exact* pointer bytes?

Rows 1 and 4 assert the pointer is written as **exactly** one line plus an LF. Text decoding would
hide an encoding preamble and normalize the question into characters, so this compares raw bytes.
Run it **after** the row's skill has written `CLAUDE.md`; the starting row-1 and row-4 fixtures
intentionally lack that file.

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound row-root check here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$Row = $Proj
$PointerPath = Join-Path $Row 'CLAUDE.md'
Assert-RegularUnlinkedFile $PointerPath 'D8 pointer' | Out-Null
$PointerBytes = [IO.File]::ReadAllBytes($PointerPath)
$ExactPointer = [Convert]::ToBase64String($PointerBytes) -ceq 'QEFHRU5UUy5tZAo='
$ExactPointer
if (-not $ExactPointer) { throw 'CLAUDE.md is not the exact 11-byte D8 pointer.' }
```

**Expect:** `True`. The only accepted bytes are ASCII/UTF-8 `@AGENTS.md` plus LF (11 bytes;
SHA-256 `336CC4FBF19BEAADA7CCF9986414FA91851A8D7A07DFB3CCBE800A69EED0AB49`). The negative
self-test rejects CRLF, UTF-8 BOM, UTF-16, missing newline, a trailing blank line, and extra content.

After rows 1, 3 and 4, require the exact ordered seven headings and the canonical affirmative fact
line inside every body. A hash delta or heading list alone is not proof of the required section walk.
Rows 3 and 4 must also preserve the line planted in their already-accurate stack section:

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound D10 grader here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$ContentPath = Join-Path $Proj 'AGENTS.md'
Assert-RegularUnlinkedFile $ContentPath 'content file' | Out-Null
$ContentText = [IO.File]::ReadAllText($ContentPath)
$ExpectedSections = [ordered]@{
  'Project overview' = 'Project kind: documentation-only UAT fixture.'
  'Stack summary' = 'Primary format: Markdown.'
  'Key commands' = 'Production commands: none.'
  'Directory layout' = 'Instruction outputs: root instruction files only.'
  'Architecture summary' = 'Application architecture: none.'
  'Current state' = 'Current state: UAT-only.'
  'Environment requirements' = 'Required shell: Windows PowerShell 5.1.'
}
if ($ContentText.Contains('<!--') -or $ContentText.Contains('-->')) {
  throw 'AGENTS.md contains an HTML comment; section evidence must be delivered prose.'
}
if ([regex]::IsMatch($ContentText, '(?m)^[ \t]{0,3}</?[A-Za-z][^>]*>[ \t]*$') -or
    [regex]::IsMatch($ContentText,
      '(?i)(?:<[^>\r\n]+>|\b(?:TBD|TODO|FIXME|placeholder|fill\s+in\s+later|unknown)\b)')) {
  throw 'AGENTS.md contains raw-HTML or placeholder-like content.'
}
$ContentLines = @([regex]::Split($ContentText, '\r?\n'))
$LineOutsideFence = @()
$HeadingRecords = @()
$FenceOpeningLineIndexes = @()
$OpenFenceCharacter = $null
$OpenFenceLength = 0
for ($LineIndex = 0; $LineIndex -lt $ContentLines.Count; $LineIndex++) {
  $Line = $ContentLines[$LineIndex]
  if ($null -eq $OpenFenceCharacter) {
    $OpeningFence = [regex]::Match(
      $Line, '^[ \t]{0,3}(?<marker>`{3,}|~{3,})')
    if ($OpeningFence.Success) {
      $FenceOpeningLineIndexes += $LineIndex
      $OpenFenceCharacter = $OpeningFence.Groups['marker'].Value.Substring(0, 1)
      $OpenFenceLength = $OpeningFence.Groups['marker'].Value.Length
      $LineOutsideFence += $false
      continue
    }
    $LineOutsideFence += $true
    $HeadingMatch = [regex]::Match($Line, '^## (?<name>[^\r\n]+)$')
    if ($HeadingMatch.Success) {
      $HeadingRecords += [pscustomobject]@{
        Name = $HeadingMatch.Groups['name'].Value
        Index = $LineIndex
      }
    }
  } else {
    $LineOutsideFence += $false
    $ClosingFencePattern = '^[ \t]{0,3}' +
      [regex]::Escape($OpenFenceCharacter) +
      '{' + $OpenFenceLength + ',}[ \t]*$'
    if ([regex]::IsMatch($Line, $ClosingFencePattern)) {
      $OpenFenceCharacter = $null
      $OpenFenceLength = 0
    }
  }
}
if ($null -ne $OpenFenceCharacter) { throw 'AGENTS.md has an unclosed fenced code block.' }
$ActualHeadings = @($HeadingRecords | ForEach-Object { $_.Name })
$ExpectedHeadings = @($ExpectedSections.Keys)
$HeadingSequenceMatches = (($ActualHeadings.Count -eq $ExpectedHeadings.Count) -and
  (($ActualHeadings -join "`n") -ceq ($ExpectedHeadings -join "`n")))
if (-not $HeadingSequenceMatches) {
  throw 'AGENTS.md does not contain the exact ordered seven-section heading set.'
}
if ($HeadingRecords.Count -ne $ExpectedHeadings.Count) {
  throw 'AGENTS.md heading parser did not produce exactly seven prose headings.'
}
$SectionBodies = @{}
$SectionProseBodies = @{}
for ($SectionIndex = 0; $SectionIndex -lt $HeadingRecords.Count; $SectionIndex++) {
  $Heading = $HeadingRecords[$SectionIndex].Name
  $BodyStart = $HeadingRecords[$SectionIndex].Index + 1
  $BodyEnd = if ($SectionIndex + 1 -lt $HeadingRecords.Count) {
    $HeadingRecords[$SectionIndex + 1].Index - 1
  } else {
    $ContentLines.Count - 1
  }
  $BodyLines = @()
  $ProseLines = @()
  if ($BodyStart -le $BodyEnd) {
    for ($BodyIndex = $BodyStart; $BodyIndex -le $BodyEnd; $BodyIndex++) {
      $BodyLines += $ContentLines[$BodyIndex]
      if ($LineOutsideFence[$BodyIndex] -and
          $ContentLines[$BodyIndex] -cnotmatch '^(?: {4}|\t)') {
        $ProseLines += $ContentLines[$BodyIndex]
      }
    }
  }
  $SectionBodies[$Heading] = $BodyLines
  $SectionProseBodies[$Heading] = $ProseLines
  $RequiredFact = [string]$ExpectedSections[$Heading]
  if ($ProseLines -cnotcontains $RequiredFact) {
    throw "Section '$Heading' omits its exact affirmative fact line: $RequiredFact"
  }
}
$RequiredStackTable = @(
  '| Component | Value |',
  '|---|---|',
  '| Primary format | Markdown |'
)
$StackProseLines = @($SectionProseBodies['Stack summary'])
$ValidStackTableStarts = @()
for ($TableIndex = 0; $TableIndex -le $StackProseLines.Count - 3; $TableIndex++) {
  $CandidateTable = @($StackProseLines[$TableIndex..($TableIndex + 2)])
  if (($CandidateTable -join "`n") -ceq ($RequiredStackTable -join "`n")) {
    $ValidStackTableStarts += $TableIndex
  }
}
if ($ValidStackTableStarts.Count -ne 1) {
  throw 'Stack summary must contain exactly one contiguous ordered Component/Value table.'
}
$RequiredTreeLines = @(
  '```text',
  '.',
  '|-- AGENTS.md - project instructions',
  '`-- CLAUDE.md - @AGENTS.md pointer',
  '```'
)
$DirectoryRecord = @($HeadingRecords | Where-Object {
  $_.Name -ceq 'Directory layout'
})[0]
$DirectoryEnd = @($HeadingRecords | Where-Object {
  $_.Index -gt $DirectoryRecord.Index
} | Select-Object -First 1).Index - 1
$ValidTreeStarts = @()
for ($TreeIndex = $DirectoryRecord.Index + 1;
     $TreeIndex -le $DirectoryEnd - 4; $TreeIndex++) {
  $CandidateTree = @($ContentLines[$TreeIndex..($TreeIndex + 4)])
  if ($FenceOpeningLineIndexes -contains $TreeIndex -and
      ($CandidateTree -join "`n") -ceq ($RequiredTreeLines -join "`n")) {
    $ValidTreeStarts += $TreeIndex
  }
}
if ($ValidTreeStarts.Count -ne 1) {
  throw 'Directory layout omits the exact annotated instruction-file tree.'
}
if (($RowNumber -eq 3 -or $RowNumber -eq 4) -and
    @($SectionProseBodies['Stack summary']) -cnotcontains
      'Markdown. UAT preservation canary: keep this line.') {
  throw 'Refresh rewrote an already-accurate stack fact instead of preserving it.'
}
$ActualHeadings
```

**Expect:** the seven headings in the order shown by `$ExpectedSections`; any commented,
raw-HTML, indented-code, or fenced-heading facsimile; missing exact fact line; absent stack table
or annotated directory tree; duplicate/reordered heading; placeholder; or lost preservation canary
throws.

### Row 5 has two independent claims

After `Set-RowFixture 5` and before Instrument A's pre-action snapshot, create one scratch-only
Step 8 target and record its preimage:

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound row-5 fixture write here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$Row5Memory = [IO.Path]::GetFullPath((Join-Path $Proj 'uat-memory.md'))
$Row5MemoryParent = [IO.Path]::GetDirectoryName($Row5Memory)
if (-not $Row5MemoryParent.Equals($Proj, [StringComparison]::Ordinal)) {
  throw 'Row-5 MEMORY_FILE must be directly under the validated scratch root.'
}
if (Test-Path -LiteralPath $Row5Memory) {
  Assert-RegularUnlinkedFile $Row5Memory 'uat-memory.md' | Out-Null
}
$ReceiptBoundary = @(Assert-UatScratchReceipt)
if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
    $ReceiptBoundary[0] -cne $true) { throw 'Pre-row-5-write receipt was not exactly True.' }
Assert-UnlinkedPathAncestry $Proj 'row-5 scratch root' | Out-Null
[IO.File]::WriteAllText($Row5Memory,
  "# UAT memory`n`n## Status`n`nBefore row-5 continuation.`n")
$ReceiptBoundary = @(Assert-UatScratchReceipt)
if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
    $ReceiptBoundary[0] -cne $true) { throw 'Post-row-5-write receipt was not exactly True.' }
Assert-UnlinkedPathAncestry $Proj 'row-5 scratch root' | Out-Null
Assert-RegularUnlinkedFile $Row5Memory 'uat-memory.md' | Out-Null
$Row5MemoryBefore = (Get-FileHash -LiteralPath $Row5Memory -Algorithm SHA256 `
                                  -ErrorAction Stop).Hash
if ($Row5MemoryBefore -cnotmatch '^[0-9A-F]{64}$') {
  throw 'Invalid pre-action SHA-256 for uat-memory.md.'
}
```

Once Step 109 is unblocked, the selected resolution must provide an authorized slice that begins
at Step 7 and whose safe boundary ends immediately before Step 9. Supply the **absolute**
`$Row5Memory` as `MEMORY_FILE`, phase text `Phase IS Step 109 row 5 continuation observed`, issue
#153, final test count unknown, no discrepancies and overall UAT pending. Do not tell the agent to
"continue" or state that Step 8 must happen: the core's natural Step-7-to-Step-8 transition is the
property under test. Step 8 is allowed to write only `$Row5Memory`. Afterward:

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound row-5 post-action evidence here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
Assert-RegularUnlinkedFile $Row5Memory 'uat-memory.md' | Out-Null
$Row5MemoryAfter = (Get-FileHash -LiteralPath $Row5Memory -Algorithm SHA256 `
                                 -ErrorAction Stop).Hash
if ($Row5MemoryAfter -cnotmatch '^[0-9A-F]{64}$') {
  throw 'Invalid post-action SHA-256 for uat-memory.md.'
}
$Row5MemoryChanged = -not $Row5MemoryAfter.Equals(
  $Row5MemoryBefore, [StringComparison]::Ordinal)
$ContinuationFound = Select-String -LiteralPath $Row5Memory `
  -SimpleMatch 'Phase IS Step 109 row 5 continuation observed' -Quiet -ErrorAction Stop
$Row5MemoryChanged
$ContinuationFound
if (-not $Row5MemoryChanged -or -not $ContinuationFound) {
  throw 'Row 5 did not continue into the permitted Step 8 memory update.'
}
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
  the intended core; row 2 is gradable only because § 2.0's native host record proves the exact
  scratch wrapper, the successful co-located core read, and the expected core bytes for this
  invocation.*

## 2.2 Fixed-point check (representative row 3)

The plan calls rows 3 and 4 fixed points and requires one second `/repo-update` pass, so row 3
is the representative. Do not grade the second pass unless the first row-3 pass already changed
`AGENTS.md`, left `CLAUDE.md` byte-identical, and passed its binding record; two runs that both
did nothing are not a fixed point.

**Run in:** the same fresh row-3 host session, immediately after the first pass and before any
fixture reset. In the observer window, take a new post-first-pass baseline:

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound row-5 grading root here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$Row = $Proj
$before = @(Get-InstructionSnapshot $Row)
$fixedRootBefore = @(Get-ProtectedRootSnapshot $Row -ExcludedRelativePaths @())
```

Do **not** use a bare `/repo-update`; that starts the current full lifecycle. After issue #153
records its resolution, paste the exact same authorized row-3 invocation literal a second time in
the host session. Until that literal exists, this check remains blocked.

Finally, in the observer window:

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound row-5 grader here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$after = @(Get-InstructionSnapshot $Row)
$fixedRootAfter = @(Get-ProtectedRootSnapshot $Row -ExcludedRelativePaths @())
$FixedRootDifference = @(Compare-Object $fixedRootBefore $fixedRootAfter `
                                        -CaseSensitive -ErrorAction Stop)
$FixedInstructionDifference = @(Compare-Object $before $after `
                                               -CaseSensitive -ErrorAction Stop)
if ($FixedRootDifference.Count -ne 0 -or $FixedInstructionDifference.Count -ne 0) {
  $FixedRootDifference
  $FixedInstructionDifference
  throw 'The representative second pass was not a filesystem fixed point.'
}
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
throw 'BLOCKED: #153 must commit and verify the receipt-bound delivery-canary write here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$DeliveryCanary = 'skill-mesh-step109-delivery-' + [Guid]::NewGuid().ToString('N')
$CanarySearchPathsBefore = @(Get-UnlinkedFilePaths $Proj)
$PriorCanaryHit = @(
  if ($CanarySearchPathsBefore.Count -ne 0) {
    Select-String -LiteralPath $CanarySearchPathsBefore -SimpleMatch $DeliveryCanary `
      -ErrorAction Stop
  }
)
if ($PriorCanaryHit.Count -ne 0) { throw 'Random delivery canary already exists.' }
$AgentsPath = Join-Path $Proj 'AGENTS.md'
Assert-RegularUnlinkedFile $AgentsPath 'AGENTS.md delivery target' | Out-Null
$ReceiptBoundary = @(Assert-UatScratchReceipt)
if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
    $ReceiptBoundary[0] -cne $true) { throw 'Pre-canary-write receipt was not exactly True.' }
Assert-UnlinkedPathAncestry $Proj 'delivery scratch root' | Out-Null
[IO.File]::AppendAllText($AgentsPath, "`nUAT delivery canary: $DeliveryCanary`n")
$ReceiptBoundary = @(Assert-UatScratchReceipt)
if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
    $ReceiptBoundary[0] -cne $true) { throw 'Post-canary-write receipt was not exactly True.' }
Assert-UnlinkedPathAncestry $Proj 'delivery scratch root' | Out-Null
Assert-RegularUnlinkedFile $AgentsPath 'AGENTS.md delivery target' | Out-Null
$CanarySearchPathsAfter = @(Get-UnlinkedFilePaths $Proj)
$CanaryFiles = @(
  if ($CanarySearchPathsAfter.Count -ne 0) {
    Select-String -LiteralPath $CanarySearchPathsAfter -SimpleMatch $DeliveryCanary `
      -ErrorAction Stop |
      Select-Object -ExpandProperty Path -Unique
  }
)
if ($CanaryFiles.Count -ne 1 -or
    -not $CanaryFiles[0].Equals($AgentsPath, [StringComparison]::Ordinal)) {
  throw 'Delivery canary is not unique to root AGENTS.md.'
}
$VerifiedHeading = (Select-String -LiteralPath $AgentsPath -Pattern '^## ' -ErrorAction Stop |
  Select-Object -First 1).Line
if ([String]::IsNullOrWhiteSpace($VerifiedHeading)) {
  throw 'Completed row-3 AGENTS.md has no section heading to verify.'
}
```

### Codex — decisive, and documented

**Run in:** `<scratch-project>` · Windows PowerShell 5.1.

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound Codex delivery launch here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$CodexShimInfo = Get-Command codex.cmd -All -CommandType Application `
                            -ErrorAction Stop | Select-Object -First 1
$CodexShim = Get-CanonicalAbsolutePath $CodexShimInfo.Source 'Codex command shim'
Assert-RegularUnlinkedFile $CodexShim 'Codex command shim' | Out-Null
$CodexShimHash = (Get-FileHash -LiteralPath $CodexShim -Algorithm SHA256 `
                              -ErrorAction Stop).Hash
$CodexVendorBin = Join-Path (Split-Path -Parent $CodexShim) `
  'node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin'
$CodexVendorBin = Get-CanonicalAbsolutePath $CodexVendorBin 'Codex vendor bin'
Assert-UnlinkedPathAncestry $CodexVendorBin 'Codex vendor bin' | Out-Null
function Get-CodexVendorManifest {
  $VendorItems = @(Get-ChildItem -LiteralPath $CodexVendorBin -Force -ErrorAction Stop)
  if ($VendorItems.Count -ne 2 -or @($VendorItems | Where-Object {
        $_.PSIsContainer -or (Test-LinkedItem $_)
      }).Count -ne 0) {
    throw 'Codex vendor bin is not the audited two-file unlinked tree.'
  }
  @($VendorItems | ForEach-Object {
    $Digest = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256 `
                            -ErrorAction Stop).Hash
    if ($Digest -cnotmatch '^[0-9A-F]{64}$') {
      throw "Invalid Codex vendor SHA-256: $($_.Name)"
    }
    '{0} {1} {2}' -f $_.Name, $_.Length, $Digest
  } | Sort-Object)
}
$ExpectedCodexVendorManifest = @(
  'codex-code-mode-host.exe 57450288 37C23A542037E1BCFD0FA7EB4A150C697229D7FF31BF675C519D5BFF7226B191',
  'codex.exe 298668336 935A1911ED2556E4FFCEC995F4886AC2AC425863BA26FED264DF62E30272AD9D'
)
$CodexVendorManifestBefore = @(Get-CodexVendorManifest)
$CodexVendorDifference = @(Compare-Object $ExpectedCodexVendorManifest `
  $CodexVendorManifestBefore -CaseSensitive -ErrorAction Stop)
$CodexCommand = Join-Path $CodexVendorBin 'codex.exe'
Assert-RegularUnlinkedFile $CodexCommand 'Codex native executable' | Out-Null
if ($CodexShimHash -cne 'C54DB6755E710C39703F7C37512F9E35ED41042D8080558D2B84B8D2694323C3' -or
    $CodexVendorDifference.Count -ne 0) {
  $CodexVendorDifference
  throw 'Codex native executable tree differs from the audited 0.147.0 delivery host.'
}
$ReceiptBoundary = @(Assert-UatScratchReceipt)
if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
    $ReceiptBoundary[0] -cne $true) { throw 'Pre-Codex-launch receipt was not exactly True.' }
Assert-UnlinkedPathAncestry $Proj 'Codex launch root' | Out-Null
Assert-UnlinkedPathAncestry $CodexVendorBin 'Codex vendor bin' | Out-Null
$CodexVendorManifestAtLaunch = @(Get-CodexVendorManifest)
$CodexLaunchManifestDifference = @(Compare-Object $ExpectedCodexVendorManifest `
  $CodexVendorManifestAtLaunch -CaseSensitive -ErrorAction Stop)
$CodexShimHashAtLaunch = (Get-FileHash -LiteralPath $CodexShim -Algorithm SHA256 `
                                      -ErrorAction Stop).Hash
if ($CodexLaunchManifestDifference.Count -ne 0 -or
    $CodexShimHashAtLaunch -cne
      'C54DB6755E710C39703F7C37512F9E35ED41042D8080558D2B84B8D2694323C3') {
  $CodexLaunchManifestDifference
  throw 'Codex executable bytes changed before the delivery launch.'
}
Set-Location -LiteralPath $Proj -ErrorAction Stop
$CodexLaunchRoot = (Get-Location).ProviderPath.TrimEnd('\')
if (-not $CodexLaunchRoot.Equals($Proj, [StringComparison]::Ordinal)) {
  throw 'Codex launch root does not match the validated scratch project.'
}
$PromptCanaryFound = $false
$PromptHeadingFound = $false
& $CodexCommand debug prompt-input | ForEach-Object {
  $PromptLine = [string]$_
  if ($PromptLine.Contains($DeliveryCanary)) { $PromptCanaryFound = $true }
  if ($PromptLine.Contains($VerifiedHeading)) { $PromptHeadingFound = $true }
}
$CodexExit = $LASTEXITCODE
$PromptCanaryFound
$PromptHeadingFound
if ($CodexExit -ne 0 -or -not $PromptCanaryFound -or -not $PromptHeadingFound) {
  throw "Codex delivery probe failed (exit $CodexExit)."
}
$CodexVendorManifestAfter = @(Get-CodexVendorManifest)
$CodexVendorPostDifference = @(Compare-Object $CodexVendorManifestBefore `
  $CodexVendorManifestAfter -CaseSensitive -ErrorAction Stop)
$CodexShimHashAfter = (Get-FileHash -LiteralPath $CodexShim -Algorithm SHA256 `
                                   -ErrorAction Stop).Hash
if ($CodexVendorPostDifference.Count -ne 0 -or
    $CodexShimHashAfter -cne $CodexShimHash) {
  $CodexVendorPostDifference
  throw 'Codex executable bytes changed during the delivery probe.'
}
```

**Expect:** `True`, `True` — the collision-proof canary and one real row-3 section heading. This
is the probe form this repository already documents at
`documentation/codex-instruction-delivery.md`, and it is decisive because it tests the bytes
actually delivered rather than the model's answer. The random token was proved absent before it
was added and unique to this project's `AGENTS.md`, so a base, global or ancestor instruction file
cannot satisfy the search accidentally.

**What Step 108 did and did not verify here.** The two-boolean stream predicate was exercised in
Windows PowerShell 5.1 against controlled input and requires both strings independently. The
post-merge audit pinned the `codex.cmd` discovery shim and the complete two-file native vendor bin,
then invokes the pinned `codex.exe` directly; Node, `codex.js`, aliases and functions are not in the
execution chain. The full prompt-input command was **deliberately not run**: it is Step 109's
action, it reaches the Codex backend, and Codex-home background churn makes individual cache
changes unattributable. Controlled reproductions observed no project-directory write and no
persisted `-c` override; no per-invocation Codex-home file count is published.

**Record both booleans, the exact heading and the canary — never the full prompt-input dump.** That
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
Issue #153's resolution must supply and negative-test exactly one project-scoped
`InstructionsLoaded` handler with matcher `include`. Its pinned logger must validate the canonical
target root and session-shaped filename, then write one compact JSON record with
`FileMode.CreateNew`; it must never append or overwrite. Pin the logger script and its PowerShell
executable chain. This logger, plus the path guard only when that guard is process-based, is the
complete hook-process allowlist. Prepare the absent log path and launch identity before that
session:

```powershell
throw 'BLOCKED: #153 must commit and verify the contained delivery hook/launch receipt here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
$DeliverySessionId = [Guid]::NewGuid().ToString()
$InstructionsLog = Join-Path $Proj ('.uat-instructions-loaded-' + $DeliverySessionId + '.jsonl')
$ReceiptBoundary = @(Assert-UatScratchReceipt)
if ($ReceiptBoundary.Count -ne 1 -or $ReceiptBoundary[0] -isnot [bool] -or
    $ReceiptBoundary[0] -cne $true) { throw 'Pre-Claude-log receipt was not exactly True.' }
Assert-UnlinkedPathAncestry $Proj 'delivery log root' | Out-Null
if (Test-Path -LiteralPath $InstructionsLog) {
  throw 'Fresh InstructionsLoaded log already exists.'
}
$DeliveryAdditionalArguments = @('--session-id', $DeliverySessionId)
Invoke-ContainedClaude -ExpectedRoot $Proj `
  -AdditionalArguments $DeliveryAdditionalArguments `
  -InstructionsLogPath $InstructionsLog
```

After closing the fresh session, require exactly one newly logged include event with the session
identity, cwd, and import parent all bound to this fixture:

```powershell
throw 'BLOCKED: #153 must commit and verify the receipt-bound Claude delivery grader here.'
$FenceGuardCommand = Get-Command Assert-UatFenceReady -CommandType Function -ErrorAction Stop
$FenceGuardResult = @(& $FenceGuardCommand)
if ($FenceGuardResult.Count -ne 1 -or $FenceGuardResult[0] -isnot [bool] -or
    $FenceGuardResult[0] -cne $true) { throw 'UAT fence guard did not return exactly one True.' }
Assert-UnlinkedPathAncestry $Proj 'delivery log root' | Out-Null
Assert-RegularUnlinkedFile $InstructionsLog 'InstructionsLoaded event log' | Out-Null
$LoggedLines = @(Get-Content -LiteralPath $InstructionsLog -ErrorAction Stop)
if ($LoggedLines.Count -ne 1 -or [String]::IsNullOrWhiteSpace($LoggedLines[0])) {
  throw 'Pinned logger did not create exactly one compact event record.'
}
$LoggedEvent = $LoggedLines[0] | ConvertFrom-Json -ErrorAction Stop
$RequiredEventProperties = @(
  'hook_event_name', 'session_id', 'cwd', 'file_path', 'memory_type',
  'load_reason', 'parent_file_path', 'transcript_path'
)
$EventPropertyNames = @($LoggedEvent.PSObject.Properties | ForEach-Object { $_.Name })
$MissingEventProperties = @($RequiredEventProperties | Where-Object {
  $EventPropertyNames -cnotcontains $_
})
if ($MissingEventProperties.Count -ne 0 -or
    @($RequiredEventProperties | Where-Object {
      $LoggedEvent.$_ -isnot [string] -or [String]::IsNullOrWhiteSpace($LoggedEvent.$_)
    }).Count -ne 0) {
  $MissingEventProperties
  throw 'InstructionsLoaded record is missing a required string field.'
}
$ExpectedAgentsPath = Get-CanonicalAbsolutePath (Join-Path $Proj 'AGENTS.md') `
  'expected AGENTS.md'
$ExpectedClaudePath = Get-CanonicalAbsolutePath (Join-Path $Proj 'CLAUDE.md') `
  'expected CLAUDE.md'
$EventCwd = Get-CanonicalAbsolutePath $LoggedEvent.cwd 'event cwd'
$EventFilePath = Get-CanonicalAbsolutePath $LoggedEvent.file_path 'event file path'
$EventParentPath = Get-CanonicalAbsolutePath $LoggedEvent.parent_file_path `
  'event parent file path'
$EventTranscriptPath = Get-CanonicalAbsolutePath $LoggedEvent.transcript_path `
  'event transcript path'
$ExpectedTranscriptRoot = (Resolve-Path -LiteralPath `
  (Join-Path $ClaudeConfigDir 'projects') -ErrorAction Stop).Path.TrimEnd('\')
Assert-UnlinkedPathAncestry $ExpectedTranscriptRoot 'Claude transcript root' | Out-Null
$EventTranscriptParent = Split-Path -Parent $EventTranscriptPath
Assert-UnlinkedPathAncestry $EventTranscriptParent `
  'Claude transcript parent' | Out-Null
Assert-RegularUnlinkedFile $EventTranscriptPath 'fresh Claude transcript' | Out-Null
$EventCwdFacts = Get-DirectoryHandleFacts $EventCwd 'event cwd'
$ExpectedProjectFacts = Get-DirectoryHandleFacts $Proj 'expected event project'
$ExpectedTranscriptFacts = Get-DirectoryHandleFacts $ExpectedTranscriptRoot `
  'expected Claude transcript root'
$EventTranscriptParentFacts = Get-DirectoryHandleFacts $EventTranscriptParent `
  'event transcript parent'
if ($LoggedEvent.hook_event_name -cne 'InstructionsLoaded' -or
    $LoggedEvent.session_id -cne $DeliverySessionId -or
    $EventCwdFacts.Identity -cne $ExpectedProjectFacts.Identity -or
    -not $EventCwdFacts.FinalPath.Equals(
      $ExpectedProjectFacts.FinalPath, [StringComparison]::Ordinal) -or
    -not $EventCwd.Equals($Proj, [StringComparison]::Ordinal) -or
    -not $EventFilePath.Equals($ExpectedAgentsPath,
      [StringComparison]::Ordinal) -or
    $LoggedEvent.memory_type -cne 'Project' -or
    $LoggedEvent.load_reason -cne 'include' -or
    -not $EventParentPath.Equals($ExpectedClaudePath,
      [StringComparison]::Ordinal) -or
    -not (Test-FinalPathWithin $EventTranscriptParentFacts.FinalPath `
      $ExpectedTranscriptFacts.FinalPath) -or
    [IO.Path]::GetFileName($EventTranscriptPath) -cne ($DeliverySessionId + '.jsonl')) {
  throw 'Fresh Claude session lacks one exactly bound AGENTS.md include event.'
}
'BOUND'
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
