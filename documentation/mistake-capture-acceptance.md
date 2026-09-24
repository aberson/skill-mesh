# Phase LH Step 154 — attended acceptance procedure

**What this document is.** The exact, pre-authored procedure for the attended Codex
acceptance of the Phase LH capture-and-harvest slice: setup, install, probe, capture,
preview, disposition, retry reconciliation, verification, and cleanup. Every request
file, every command, and every expected result is written down here **before** the
session, so the attended run is an observation rather than an authoring exercise.

**What this document is not.** It is **not** a record that any of it happened. Step 153
produced this procedure alongside the code; **Step 154 executes it.** Nothing below
claims an operator observation, a verdict, or a host behaviour that was seen. Every
result cell in section 12 is empty on purpose and is filled in only by the attended
run. If a step cannot be executed, record it as **incomplete** with the reason — an
unavailable piece of native evidence is recorded as unavailable, never inferred.

**Accepted residual carried into this acceptance.** One control in this slice has no
code-level gate and is enforced by the executing model re-reading its own draft: the
closed publishable-field rule that keeps stored narrative out of a published pull
request. That is a decision, not an oversight -- the reasoning, and the attended check
that observes it, are in section 8 under *Publishable-field leak check*. It is the one
residual this procedure deliberately verifies by human observation rather than by code.

Plan of record: [mistake-capture-plan.md](mistake-capture-plan.md), Step 154. The
behaviour under observation is the canonical contract in
[../skills/lesson-harvest/core.md](../skills/lesson-harvest/core.md) and its three
adapters.

---

## 1. Prerequisites

| Requirement | Why it is here |
|---|---|
| Windows PowerShell 5.1 (`powershell`, **not** `pwsh`) | Every build/install tool is `.ps1` and targets the 5.1 floor |
| Git on `PATH` | The helper resolves the target working tree with Git, and refuses anything else |
| Python 3 on `PATH` | The helper is invoked as `python <path> <command>` |
| OpenAI Codex CLI, signed in | The attended host for this acceptance |
| A clean checkout of the reviewed Step 153 artifact | The observation must use that exact commit, not a rebuilt approximation |

No new dependency, server, credential, or environment variable is introduced by this
procedure. `&&` is a parser error in PowerShell 5.1 — every command below is its own
line, and none of them are chained.

**Nothing in this procedure opens a remote pull request.** Candidate publication is
exercised only against the controlled local fixture in section 9.

---

## 2. Placeholders

Substitute these once at the start of the session and use the same values throughout.
Absolute paths are deliberately not spelled in this file.

| Placeholder | Meaning |
|---|---|
| `<repo>` | The Step 153 skill-mesh checkout under observation |
| `<accept-home>` | A **disposable** install home, created by this procedure and deleted by section 11 |
| `<project>` | A **disposable** Git project the capture is recorded against |
| `<requests>` | A private temporary request directory (`$env:TEMP\lh-accept`), never a tracked worktree path |
| `<backups>` | A disposable backup directory for the installer's take-ownership path |
| `<helper>` | `<accept-home>\.agents\skills\_shared\lesson_observations.py` — the INSTALLED helper |
| `<OBS_A>`, `<OBS_B>`, `<OBS_C>`, `<OBS_D>` | Observation ids minted in section 5; each is used verbatim in its request file |

---

## 3. Setup — disposable home, disposable project, foreign files

Run from `<repo>`.

```
powershell -NoProfile -File tools/build-distributions.ps1 -Provider all
```

```
New-Item -ItemType Directory -Force '<accept-home>' | Out-Null
New-Item -ItemType Directory -Force '<accept-home>\.agents\skills' | Out-Null
New-Item -ItemType Directory -Force '<requests>' | Out-Null
New-Item -ItemType Directory -Force '<backups>' | Out-Null
```

Plant two **foreign** files — files skill-mesh does not ship and must never touch.
They are the preservation evidence for sections 4 and 11:

```
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText('<accept-home>\.agents\skills\zz-operator-note.md', "operator note, not skill-mesh content`n", $utf8)
New-Item -ItemType Directory -Force '<accept-home>\.agents\skills\zz-operator-skill' | Out-Null
[System.IO.File]::WriteAllText('<accept-home>\.agents\skills\zz-operator-skill\SKILL.md', "foreign skill package`n", $utf8)
(Get-FileHash '<accept-home>\.agents\skills\zz-operator-note.md' -Algorithm SHA256).Hash
(Get-FileHash '<accept-home>\.agents\skills\zz-operator-skill\SKILL.md' -Algorithm SHA256).Hash
```

Record both hashes. Neither may change at any point in this procedure.

Create the disposable project (a real Git working tree, with one commit so `HEAD`
resolves):

```
New-Item -ItemType Directory -Force '<project>' | Out-Null
git -C '<project>' init -q .
[System.IO.File]::WriteAllText('<project>\README.md', "acceptance fixture`n", (New-Object System.Text.UTF8Encoding($false)))
git -C '<project>' add README.md
git -C '<project>' -c user.email=acceptance@example.invalid -c user.name=acceptance -c commit.gpgsign=false commit -q -m "acceptance fixture"
git -C '<project>' rev-parse HEAD
```

Record that `HEAD` value as **HEAD-BEFORE**. It must be unchanged at section 10.

---

## 4. Install the Codex profile with the NORMAL installer

No `-Force`, no `-ForceShared`. A normal install must succeed **and** leave the
foreign files untouched.

```
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider codex -Home '<accept-home>' -DistDir '<repo>\dist'
```

Expect: exit `0`, and an install summary naming the codex profile.

Then confirm preservation and containment:

```
(Get-FileHash '<accept-home>\.agents\skills\zz-operator-note.md' -Algorithm SHA256).Hash
(Get-FileHash '<accept-home>\.agents\skills\zz-operator-skill\SKILL.md' -Algorithm SHA256).Hash
Test-Path '<accept-home>\.claude\skills'
Test-Path '<accept-home>\.github\skills'
```

Expect: both hashes equal the section-3 values; both `Test-Path` results `False` — an
install binds exactly ONE profile.

> If the installer instead REFUSES with a foreign-collision error, that is a defect in
> the fixture, not in the installer: a planted foreign file collided with a path the
> profile ships. Rename the plant to a name no skill uses (`zz-` prefix) and re-run.
> Do **not** reach for `-Force` or `-ForceShared` to get past it — an unforced install
> is the thing being observed. `<backups>` exists only so that a deliberate
> take-ownership experiment, if one is ever wanted, has somewhere legal to write.

---

## 5. Probe — discovery and artifact identity

```
powershell -NoProfile -File tools/probe-codex-skills.ps1 -Home '<accept-home>' -Format json
```

```
powershell -NoProfile -File tools/inspect-host-install.ps1 -Home '<accept-home>' -Format json
```

Expect: the report names the codex discovery root `.agents/skills`, lists
`lesson-harvest`, and reports its `SKILL.md` and `core.md` as marker-valid.

Prove the installed bytes ARE the reviewed artifact, rather than assuming it:

```
Get-FileHash '<accept-home>\.agents\skills\lesson-harvest\SKILL.md' -Algorithm SHA256
Get-FileHash '<repo>\dist\codex\lesson-harvest\SKILL.md' -Algorithm SHA256
Get-FileHash '<accept-home>\.agents\skills\lesson-harvest\core.md' -Algorithm SHA256
Get-FileHash '<repo>\dist\codex\lesson-harvest\core.md' -Algorithm SHA256
Get-FileHash '<helper>' -Algorithm SHA256
Get-FileHash '<repo>\dist\codex\_shared\lesson_observations.py' -Algorithm SHA256
git -C '<repo>' rev-parse HEAD
```

Expect: each installed hash equals its `dist` counterpart. Record the `<repo>` commit
next to them — that pairing is what makes this an observation of the reviewed slice.

Confirm the installed helper runs from the install home, with the source checkout
playing no part:

```
python '<helper>' new-id
```

Expect: exit `0` and one lowercase UUID4 on stdout. Mint four ids this way and record
them as `<OBS_A>`, `<OBS_B>`, `<OBS_C>`, `<OBS_D>`.

---

## 6. Request files — authored ahead, written before the session acts

Write all four now, before any capture, substituting the minted ids. Each is one UTF-8
JSON object with **no BOM** (`Set-Content -Encoding utf8` writes a BOM on this floor
and the helper will reject the file as invalid JSON):

```
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText('<requests>\a-record.json', @'
{
  "observation_id": "<OBS_A>",
  "session": "manual-session",
  "source": "<the assistant turn and tool result that show the error>",
  "observed_error": "<what the assistant actually did, observed not inferred>",
  "evidence": ["<locator 1>", "<locator 2>"],
  "correction": "<the correction, or the word unverified>",
  "supersedes": null
}
'@, $utf8)
```

```
[System.IO.File]::WriteAllText('<requests>\b-correction.json', @'
{
  "observation_id": "<OBS_B>",
  "session": "manual-session",
  "source": "<same session locator>",
  "observed_error": "<the corrected statement of the same error>",
  "evidence": ["<locator 1>"],
  "correction": "<the corrected correction>",
  "supersedes": "<OBS_A>"
}
'@, $utf8)
```

```
[System.IO.File]::WriteAllText('<requests>\c-codified.json', @'
{
  "observation_id": "<OBS_C>",
  "session": "manual-session",
  "source": "<session locator for a mistake an existing rule already covers>",
  "observed_error": "<the observed behaviour>",
  "evidence": ["<locator naming the existing rule or memory>"],
  "correction": "<follow the instruction that already exists>",
  "supersedes": null
}
'@, $utf8)
```

```
[System.IO.File]::WriteAllText('<requests>\d-unsupported.json', @'
{
  "observation_id": "<OBS_D>",
  "session": "manual-session",
  "source": "<a locator that does not exist in this session>",
  "observed_error": "<a claim the cited evidence will not support>",
  "evidence": ["<a locator that cannot be reopened>"],
  "correction": "unverified",
  "supersedes": null
}
'@, $utf8)
```

Two more request files are the disposition inputs for section 8. Write them now too;
fill their narrative values from what the session actually classifies:

```
[System.IO.File]::WriteAllText('<requests>\c-complete.json', @'
{
  "observation_id": "<OBS_C>",
  "classification": "instruction-not-used",
  "disposition": "already-codified",
  "evidence_refs": ["<sanitized locator>"],
  "candidate_ref": null
}
'@, $utf8)
```

```
[System.IO.File]::WriteAllText('<requests>\d-complete.json', @'
{
  "observation_id": "<OBS_D>",
  "classification": "unsupported",
  "disposition": "rejected",
  "evidence_refs": ["<sanitized locator>"],
  "candidate_ref": null
}
'@, $utf8)
```

These files live in `<requests>`, a private temporary directory. **Never** author a
request inside a tracked worktree path, and delete only the files this procedure
created (section 11).

---

## 7. Capture in a real fresh Codex session

Start a **new** Codex session with `<accept-home>` as the home whose discovery root was
installed in section 4. Then, in that session:

1. **Confirm the host loaded the installed contract**, not a memory of it: ask the
   session to name lesson-harvest's record-mode flag set and its marker. Expect
   `--record <file> --repo <path>` and `[[SKILL_MISTAKE]]`. Record the answer verbatim.
2. **Produce a real, evidenced, correctable error.** Give the session an ordinary task
   in `<project>`. Do not script the mistake and do not ask for one — if the session
   makes none, record that no natural error occurred and note which sub-steps below
   therefore ran on a constructed observation instead. That distinction is the whole
   value of the attended run; do not paper over it.
3. When an error is noticed, expect **one dedicated prose admission** carrying
   `[[SKILL_MISTAKE]]` — in prose only.
4. **Observe the marker exclusions.** Over the session's own output, check that the
   marker appears in **no** generated code, **no** tool argument, **no** delivered
   file, **no** quotation, and **no** strict-format output. Then give the session a
   strict-format task (ask for a JSON-only answer) immediately after an admission and
   confirm the required output stays byte-exact, with the admission in separate prose.
5. **Record it**, using the id already in the request file:

   ```
   python '<helper>' record --repo '<project>' --input '<requests>\a-record.json'
   ```

   Expect exit `0`, `"status": "recorded"`, and a `path` under
   `<project>\.git\lesson-harvest\observations\`.

6. **Replay** the identical request:

   ```
   python '<helper>' record --repo '<project>' --input '<requests>\a-record.json'
   ```

   Expect exit `0` and `"status": "replayed"`. Confirm the saved file did not change:

   ```
   Get-ChildItem '<project>\.git\lesson-harvest\observations' | Select-Object Name, Length, LastWriteTimeUtc
   ```

7. **Record the codified case and the unsupported case:**

   ```
   python '<helper>' record --repo '<project>' --input '<requests>\c-codified.json'
   python '<helper>' record --repo '<project>' --input '<requests>\d-unsupported.json'
   ```

8. **Record the correction** linked to `<OBS_A>`:

   ```
   python '<helper>' record --repo '<project>' --input '<requests>\b-correction.json'
   ```

   Expect exit `0` and `"status": "recorded"`. Then confirm the linkage is visible to a
   reader:

   ```
   python '<helper>' pending --repo '<project>'
   ```

   Expect `<OBS_A>` **absent** from `observations`, an `observation-superseded`
   diagnostic naming it with `<OBS_B>` in `related_observation_ids`, and `<OBS_B>`
   present as a candidate source.

9. **Observe the conflict refusal** (this is the immutability boundary). Copy
   `a-record.json`, change only its `observed_error`, keep the same id, and record it:

   ```
   Copy-Item '<requests>\a-record.json' '<requests>\a-divergent.json'
   ```

   Edit `<requests>\a-divergent.json` to change `observed_error` only, then:

   ```
   python '<helper>' record --repo '<project>' --input '<requests>\a-divergent.json'
   ```

   Expect exit `3`, **no receipt on stdout**, a stderr diagnostic carrying a `code`,
   and the saved observation byte-unchanged.

---

## 8. Preview at unchanged HEAD, then explicit disposition

**Snapshot private state before the preview:**

```
git -C '<project>' rev-parse HEAD
Get-ChildItem -Recurse '<project>\.git\lesson-harvest' | ForEach-Object { "$($_.FullName)|$($_.Length)|$($_.LastWriteTimeUtc.Ticks)" }
git -C '<project>' status --porcelain
```

Record the listing as **STATE-BEFORE**. `git status` must be empty — the inbox is Git
metadata, not versioned content.

**Run the preview in the Codex session**, against the same project and with `HEAD`
unmoved:

```
/lesson-harvest --dry-run --repo <project>
```

Expect, in the session's report:

- it did **not** stop at "no new commits": HEAD is unchanged and observations are still
  scanned;
- the pending observations appear, with `<OBS_A>` excluded as superseded;
- a candidate report **and** a PR body printed to stdout;
- the dropped/below-threshold list printed;
- the page's `remaining` and `next_after` reported;
- **nothing created** — no branch, no commit, no PR, no receipt, no marker update.

**Snapshot again and compare:**

```
Get-ChildItem -Recurse '<project>\.git\lesson-harvest' | ForEach-Object { "$($_.FullName)|$($_.Length)|$($_.LastWriteTimeUtc.Ticks)" }
git -C '<project>' branch --list
git -C '<project>' log --oneline -n 3
git -C '<project>' status --porcelain
```

Expect: identical to **STATE-BEFORE**, no new branch, no new commit, working tree clean.
A single byte of difference is a dry-run defect and is recorded as a FAIL.

**Then exercise explicit normal-mode disposition on the two non-candidate cases.**
These need no pull request, which is exactly why they are the ones used here:

```
python '<helper>' complete --repo '<project>' --input '<requests>\c-complete.json'
python '<helper>' complete --repo '<project>' --input '<requests>\d-complete.json'
```

Expect exit `0` and `"status": "recorded"` for each. Then:

```
python '<helper>' complete --repo '<project>' --input '<requests>\c-complete.json'
python '<helper>' pending --repo '<project>'
```

Expect: the repeat is `"status": "replayed"` at exit `0`; `<OBS_C>` and `<OBS_D>` are
**absent** from `observations` with `observation-completed` diagnostics; and the page
still advances past them (`next_after` is reported rather than the walk stalling).

**Stateless pagination:**

```
python '<helper>' pending --repo '<project>' --limit 1
python '<helper>' pending --repo '<project>' --limit 1 --after <the next_after from the previous call>
python '<helper>' pending --repo '<project>' --after <a fifth id from new-id, recorded nowhere>
```

Expect: the walk reaches later records past the retained completed ones, and the last
call — a well-formed id that names nothing in this inbox, minted by `new-id` and never
recorded — exits `2` with an `unknown-cursor` code. A cursor is never silently
restarted.

**Publishable-field leak check (the accepted residual, verified here by a human).**

[core.md](../skills/lesson-harvest/core.md) closes the publishable field set: only
`observation_id`, `classification` and `disposition` may reach a published pull-request
body. Nothing in code enforces that before a pull request is drafted, and nothing is
going to: the helper performs no network requests and drafts no pull request, so a
redaction gate has nowhere in this slice to live without growing the helper past the
boundary the plan's OUT list sets. The plan's risk table carries the matching row --
publish minimal sanitized provenance, keep raw observation files Git-private and never
staged -- and the STRUCTURAL half of that mitigation is genuinely enforced in code:
records live under the resolved common Git directory, which `git add` cannot reach. The
FIELD-DISCIPLINE half is an accepted residual. An attended run is the only place it can
be observed, so it is observed here rather than restated as one more sentence for a
model to skip.

Capture the four drafted surfaces the preview reported, verbatim, into one file:

```
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText('<requests>\drafted-surfaces.txt', @'
<paste verbatim: the drafted PR title>
<paste verbatim: the drafted branch name>
<paste verbatim: every line of the drafted commit message>
<paste verbatim: the whole drafted PR body>
'@, $utf8)
```

Then check every stored narrative value against it. The narrative is read back out of
the private inbox rather than retyped, so the comparison is against the bytes that were
actually saved:

```
$drafted = [System.IO.File]::ReadAllText('<requests>\drafted-surfaces.txt')
Get-ChildItem '<project>\.git\lesson-harvest\observations\*.md' | ForEach-Object {
  $text = [System.IO.File]::ReadAllText($_.FullName)
  $open = $text.IndexOf('{'); $close = $text.LastIndexOf('}')
  $json = $text.Substring($open, $close - $open + 1) | ConvertFrom-Json
  foreach ($field in 'observed_error', 'correction', 'source') {
    if ($json.$field -and $drafted.Contains($json.$field)) {
      "LEAK $($_.BaseName) $field"
    }
  }
  foreach ($locator in $json.evidence) {
    if ($locator -and $drafted.Contains($locator)) { "LEAK $($_.BaseName) evidence" }
  }
}
```

Expect: **no output at all.** Any `LEAK` line is a FAIL, recorded with the field name
and the observation id -- and never with the leaked value itself.

The command is a floor, not the check. It catches a verbatim copy only, and the failure
mode that matters most is a close paraphrase no substring match can see. So the operator
also **reads** the four drafted surfaces once, against the saved narrative, and records
whether any of `observed_error`, `correction`, `source` or `evidence` is recoverable
from them -- verbatim, paraphrased, or by quotation. That human reading is the verdict;
the command only removes the easy half of the work.

---

## 9. Retry reconciliation, against a controlled fixture only

The interrupted-publication path is observed **without opening any remote pull
request**. Use the local fixture below; do not push, and do not create a PR on any
repository during acceptance.

1. Create a local draft-candidate fixture — a file standing in for an existing draft
   PR body — that contains the stable observation id of a candidate-class observation:

   ```
   [System.IO.File]::WriteAllText('<requests>\existing-draft-body.md', "draft candidate body citing observation <OBS_B>`n", (New-Object System.Text.UTF8Encoding($false)))
   ```

2. Ask the session what it would do on a retry after an interrupted publication for
   `<OBS_B>`, given that body. Expect it to state that it **reconciles against the
   existing draft and reuses it**, rather than publishing a duplicate, and that a
   `candidate-prepared` receipt is written only after the draft-PR path actually
   succeeded.
3. Confirm no receipt was written for `<OBS_B>` by this section:

   ```
   Get-ChildItem '<project>\.git\lesson-harvest\receipts' | Select-Object Name
   ```

   Expect exactly the receipts section 8 created.

4. Confirm the helper validates a candidate reference by **shape** and makes no network
   call — write a request whose `candidate_ref` is malformed and confirm exit `2`:

   ```
   [System.IO.File]::WriteAllText('<requests>\b-bad-ref.json', @'
{
  "observation_id": "<OBS_B>",
  "classification": "instruction-gap",
  "disposition": "candidate-prepared",
  "evidence_refs": ["<sanitized locator>"],
  "candidate_ref": "https://example.invalid/owner/repo/pull/1"
}
'@, (New-Object System.Text.UTF8Encoding($false)))
   ```

   ```
   python '<helper>' complete --repo '<project>' --input '<requests>\b-bad-ref.json'
   ```

   Expect exit `2` and no receipt for `<OBS_B>`.

---

## 10. Verify nothing live changed

The acceptance must not have touched the operator's real environment.

```
git -C '<project>' rev-parse HEAD
git -C '<project>' status --porcelain
git -C '<repo>' status --porcelain
Test-Path '<project>\.claude'
```

Expect: `HEAD` equals **HEAD-BEFORE**; both working trees clean; no live profile,
memory file, rule file, hook, or evaluator changed anywhere outside `<accept-home>` and
`<project>`. State explicitly in the record that no live daily-profile adoption was
performed — this procedure installs only into the disposable home.

---

## 11. Cleanup — exact commands

```
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider codex -Home '<accept-home>' -Uninstall
```

Verify the ledger-scoped uninstall removed only what it owned, and that **both foreign
files survived**:

```
(Get-FileHash '<accept-home>\.agents\skills\zz-operator-note.md' -Algorithm SHA256).Hash
(Get-FileHash '<accept-home>\.agents\skills\zz-operator-skill\SKILL.md' -Algorithm SHA256).Hash
Test-Path '<accept-home>\.agents\skills\lesson-harvest\SKILL.md'
```

Expect: both hashes still equal the section-3 values; the skill package is gone.

Then remove the disposable artifacts. Delete only what this procedure created:

```
Remove-Item -Recurse -Force '<accept-home>'
Remove-Item -Recurse -Force '<project>'
Remove-Item -Recurse -Force '<requests>'
Remove-Item -Recurse -Force '<backups>'
```

The private observation inbox lives inside `<project>\.git`, so removing `<project>`
removes it. No cleanup touches `<repo>` beyond its gitignored `dist/`.

---

## 12. Result record — filled in by Step 154, empty here

| # | Check | Expected | Observed | Verdict |
|---|---|---|---|---|
| 1 | Normal install into the disposable home | exit 0, codex profile only | | |
| 2 | Foreign files preserved through install | hashes unchanged | | |
| 3 | Discovery lists `lesson-harvest` | present, marker-valid | | |
| 4 | Installed bytes equal the reviewed artifact | hashes equal `dist/codex` | | |
| 5 | Installed helper runs from the install home | `new-id` exit 0 | | |
| 6 | Host loaded the revised contract | names `--record` and the marker | | |
| 7 | Real evidenced error captured | prose admission + `recorded` | | |
| 8 | Marker exclusions held | absent from code/tools/files/quotes/strict output | | |
| 9 | Replay is idempotent | `replayed`, exit 0, bytes unchanged | | |
| 10 | Same-id conflict refused | exit 3, no receipt, bytes unchanged | | |
| 11 | Correction linkage visible before classification | original superseded, replacement eligible | | |
| 12 | Harvest ran at unchanged HEAD | did not stop at "no new commits" | | |
| 13 | Dry-run wrote nothing | state byte-identical, no branch/commit/PR | | |
| 14 | Already-codified disposition, no empty PR | `recorded`, no PR | | |
| 15 | Unsupported case rejected, no fabricated lesson | `recorded`, no candidate | | |
| 16 | Completed observations excluded, walk still advances | diagnostics + `next_after` | | |
| 17 | Unknown cursor is an error | exit 2, `unknown-cursor` | | |
| 18 | Retry reconciles instead of duplicating | reuse stated, no receipt written | | |
| 19 | Candidate reference validated by shape, no network | exit 2 on a malformed URL | | |
| 20 | Nothing live changed | clean trees, no live profile adopted | | |
| 21 | Uninstall preserved foreign files | hashes unchanged, package gone | | |
| 22 | Publishable-field leak check, mechanical | no `LEAK` line from the section-8 command | | |
| 23 | Publishable-field leak check, human reading | no narrative recoverable from title, branch, commit message or PR body | | |

**Recording rule.** Any row that could not be executed is `INCOMPLETE` with the reason,
never `PASS` by inference and never left blank. Native evidence that the host does not
expose (a session id, for example) is recorded as unavailable — the procedure's
`manual-session` literal is the declared substitute, and using it is not a failure.

Rows 22 and 23 grade the accepted residual named in the introduction. They are a
verdict on one attended observation, not a proof that the control holds in general --
no code gate stands behind it, and recording a PASS here does not create one.
