# Baseline release runbook

Operator procedure for `tools/baseline_release.py` — the release store and record
writer introduced by Phase BR, Step 147. It turns a **pinned product source commit**
into an identifiable, reopenable release using this repository's existing toolchain.

**Every path in this document is a placeholder.** Resolve them before invoking. The
tool refuses obviously unresolved values (`$toolkitRoot`, `<store>`, `%USERPROFILE%`,
`path/to/x`, empty) rather than acting on them.

## 1. What this tool does, and what it deliberately does not

It orchestrates, records, and retains. It builds nothing of its own:

- the toolkit package is produced by the existing [`tools/release.ps1`](../tools/release.ps1),
  which itself stages from the git index and invokes the staged
  [`tools/build-distributions.ps1`](../tools/build-distributions.ps1);
- the source checks are the product's own `python -m pytest`.

It does **not**:

- **publish.** No tag is created, nothing is uploaded. It prepares a sanitized public
  publication packet and stops. Tagging and upload are a separate, later operator step.
- **install or change a consumer home.** No live install is read or written.
- **run, or verify, a review.**
  It **does not run, and cannot verify, a cross-family review.**
  The product charter's release invariant — at least one real
  representative cross-family review — is satisfied by attaching that review through
  `--proofs` **and** naming an accountable party with `--attest-reviews`. A review in
  a record is **ATTESTED, not verified**. See section 4.1 and
  [`product-charter.md`](product-charter.md).
- **certify a workflow.** The recorded gates are deterministic source checks. Native
  host acceptance (an observed Claude Code or Codex CLI session) is a different
  evidence class and is never inferred from a green suite.
- **write to the working source.** The source root is read-only to this tool. It
  fingerprints HEAD plus `git status --porcelain` before and after the run and warns
  loudly if that fingerprint moved.
- **delete anything.** Not ever, not automatically.

## 2. Preconditions

| Requirement | Why |
|---|---|
| Windows PowerShell 5.1 on `PATH` as `powershell` | the toolkit release runs the existing `.ps1` release entry; there is no POSIX path. A `toolkit` run without it is refused up front (exit 2). Not required for `lab`. |
| `git` on `PATH` | commit/tree resolution and staging are git-driven. |
| A Python 3 interpreter for `--python-exe` | runs the product's own gates. This repository pins no interpreter — supply the one whose result you intend to record. |
| `pytest`, PyYAML, markdown-it-py, jsonschema installed **for that interpreter** | the toolkit's own gates need them; their measured versions are recorded in `environment`. See the environment requirements in [`../CLAUDE.md`](../CLAUDE.md). |
| The product commit exists in `--source-root` | any rev `git` can resolve is accepted; the tool records the resolved FULL object id. |
| A store directory outside the source root, with no junction/symlink on any ancestor | the working source is read-only, and a link on an output ancestor is refused outright. |

The tool itself needs **no third-party package** — Python standard library only.

## 3. Allocate the release ID

The release ID is `<product>/<version>` and the **caller allocates it**. The tool never
invents one.

- `--version` must be **one safe path segment** matching `[A-Za-z0-9][A-Za-z0-9._-]*`.
  Traversal, path separators, drive letters, leading punctuation and Windows device
  names are refused.
- Phase BR's planning defaults are `v0.1.0-baseline.1` (toolkit) and
  `v0.1.0-experimental.1` (lab). They are names, not tags — nothing is tagged here.
- A release ID is allocated **once**. A repeated request either verifies or refuses; it
  never overwrites. See section 7.

## 4. Run it

Resolve the placeholders, then run. Read the exit code and the printed paths after each
block before continuing.

### Toolkit

```powershell
$toolkitRoot = '<toolkit-repository-root>'
$releaseStore = '<release-store-root>'
$pythonExe = '<interpreter>'
$sourceCommit = '<full-or-short-rev>'
```

```powershell
python tools/baseline_release.py toolkit --source-root $toolkitRoot --source-commit $sourceCommit --version v0.1.0-baseline.1 --store $releaseStore --python-exe $pythonExe
```

The toolkit run is **slow**: it runs the pinned source's full `python -m pytest` and
then `release.ps1 -Provider all`, which re-runs the package-integrity gate inside the
staged tree. `phase-75-baseline.md` owns this repository's measured wall clock.

**That command alone cannot reach `QUALIFIED`**, and it is not meant to — it records the
gates it executed. The charter's cross-family review is attached with `--proofs` and
attested with `--attest-reviews`; section 4.1 has the full command line and explains why
the attestation is a separate act. Run this bare form only if you want the gates recorded
before the review evidence exists: it exits `1`, its `INCOMPLETE` record is retained
whole under `<store>/.attempts/<uuid>/`, and it does **not** reserve the version name —
so the real run can still use it.

### Lab

```powershell
$labRoot = '<lab-repository-root>'
$labPython = '<lab-interpreter>'
$labCommit = '<full-or-short-rev>'
```

```powershell
python tools/baseline_release.py lab --source-root $labRoot --source-commit $labCommit --version v0.1.0-experimental.1 --store $releaseStore --python-exe $labPython
```

The lab archive is **source-only**: `providers` is empty, no `dist/` and no
`CHECKSUMS.txt` are produced, and the lab repository is never edited — not its code,
its index, its plan, or its acceptance records.

### Attaching existing evidence with `--proofs`

`--proofs <json>` imports attributable existing check and review evidence. It uses the
**same `checks` / `reviews` / `environment` shapes as `release.json`**. Evidence paths
are resolved **relative to the proofs file's own directory** and copied into the
release for local recovery.

```json
{
  "checks": [],
  "reviews": [
    {
      "source_commit": "<full-source-commit>",
      "requested_model": "<requested-model-id>",
      "resolved_model": "<observed-model-id-or-null>",
      "resolution_status": "observed",
      "identity_waiver": null,
      "conversation_id": "<conversation-id>",
      "independent": true,
      "verdict": "PASS",
      "evidence": "review-0001.md",
      "cross_family": true
    }
  ]
}
```

Rules the import enforces, and why:

- **A proofs document may not carry an absolute user path.** `release.json` is a public
  artifact. Use relative evidence paths and the documented argv placeholder tokens.
  A violation is exit 2. A leading token is **not** an exemption: a token followed
  immediately by a `home/` or `Users/` segment is refused too, for the reason given
  in section 9.
- **A proofs document may not carry text UTF-8 cannot encode.** A `\udNNN` escape in
  any string field survives `json.loads` as a lone surrogate, which no artifact this
  tool writes can hold. It is refused by name and position at exit 2 rather than
  silently transcoded — this tool records what you supplied, verbatim or not at all.
- **A structurally malformed document is exit 2** (bad JSON, unknown top-level key,
  missing required row field, wrong type). That is bad input, not missing evidence.
- **A row whose evidence file cannot be resolved, or whose `source_commit` does not
  bind to this release's source, is still RECORDED** — marked with an `import_status`
  and listed in `known_gaps`. It never counts toward qualification and is never
  silently dropped. Historical proof is never relabelled as current-source proof.
- **An import binds its own source and environment.** It never implies that anything
  executed natively during this run.
- `cross_family` must be explicitly `true` for a review to satisfy the charter
  invariant. The tool will not assert cross-family on the evidence author's behalf.
- **`attested_by` is NOT a proofs field.** Writing one into a `--proofs` row is ignored,
  by construction — see section 4.1. The attestation is a CLI act so that reusing a
  historical proofs file can never carry it forward silently.
- **A review row is graded by a negative-only tripwire against its evidence file's
  content.** See section 4.1 — together with the missing `--attest-reviews` act, this is
  what most often turns an otherwise complete `--proofs` file into an `INCOMPLETE`
  release.

## 4.1 A review is ATTESTED, not verified

**Read this before reading a `QUALIFIED` record.** It is the one place where what the
tool establishes is narrower than an operator might assume.

### What the tool cannot do, stated plainly

The cross-family review is the **only** required element this tool cannot execute. The
caller supplies both the `--proofs` row **and** the evidence document it cites, so both
sides of any text comparison between them are written by the same party. A token match
across them measures **the self-consistency of one author's story**. It is not, and
cannot be made into, verification: a presence-only matcher is defeated by a verbatim
paste of a *failing* review's transcript, in which every claimed word is present and
every one of them is negated — and the bypass family (negation, quotation, rebuttal,
sarcasm) is unbounded, because the reader is reading bytes the caller wrote.

So the tool does not pretend. It **records** the claim, **binds** it to this release's
source, **names** the party accountable for it, and refuses to launder any of that into
a verification.

### The named act: `--attest-reviews`

```powershell
python tools/baseline_release.py toolkit --source-root $toolkitRoot --source-commit $sourceCommit --version v0.1.0-baseline.1 --store $releaseStore --python-exe $pythonExe --proofs $proofsJson --attest-reviews '<accountable party>'
```

- It is a **CLI flag, never a `--proofs` field**, so re-running a historical proofs
  document cannot silently re-attest it.
- It is recorded on **every imported review row** as `attested_by`, and published in
  `release-notes.md` beside that row.
- It is required for **any** review to count toward `QUALIFIED`. Without it a
  well-formed review row yields `INCOMPLETE`, naming the missing act — while the
  archive, the row and its evidence document are all still retained and marked.
- It names a party, not a narrative: at most 120 characters, and placeholder values are
  refused. Passing it **without** `--proofs` is exit 2 — there is no review to attest.
- Giving it **needs `--proofs`**; it is ignored on a repeated request that only verifies
  an already-retained release, because a retained record is never rewritten.

`QUALIFIED` therefore means exactly this, and nothing wider:

> every machine-checkable gate ran **here** and passed, **plus** a well-formed,
> source-bound, cross-family review claim that a **named party stands behind**.

That is the same shape the charter already uses for model identity — observe it where
the host supports it, otherwise carry a waiver that is "explicit and named".

What this gives up, stated plainly:
**a named party can still attest a review that did not happen.**
The tool never had the power to catch that; it only had the appearance of it. The record
now says whose name the claim rests on, so a reader can go and ask them.

### The evidence-consistency tripwire — negative-only

The text comparison survives, demoted to what it can honestly do. Consistency can be
locally **falsified**; it can never be locally established. The result is recorded as
`evidence_consistency` — a deliberately narrow word, because the record must not assert
more than the comparison can support:

| Value | Meaning | Effect on qualification |
|---|---|---|
| `consistent` | the tripwire did not fire | **none** — it upgrades nothing on its own |
| `unstated` | the document omits a claim the row makes | blocks |
| `contradicted` | the document **denies** a claim the row makes | blocks |
| `no-evidence` | no document was imported for the row | blocks |
| `evidence-unreadable` | the document is not UTF-8 text | blocks |

An absent or unrecognised value blocks too — the check is fail-closed. Every blocking
outcome is named in `known_gaps` and `qualification_reasons`, and, as with every other
missing proof, the row is still retained, the archive is still kept, and the release is
`INCOMPLETE` rather than `QUALIFIED`.

The claims the tripwire grades:

| The row claims | The document must state, and must not deny |
|---|---|
| `source_commit` | that full commit id, verbatim |
| `conversation_id` | that id, verbatim |
| `verdict` | that verdict as its own word (`passed` does not satisfy `PASS`) |
| `resolved_model`, or `identity_waiver` when the model was not resolved | that model id, or that waiver text |
| `independent: true` | the word `independent` |
| `cross_family: true` | **both** host families — `Claude` **and** `Codex`. The charter's release hosts are Claude Code and Codex, so a document naming only one has not evidenced a cross-family review. |

Matching is case-insensitive and anchored on token boundaries. Denial is graded inside
the **clause** carrying the claim, so ordinary review prose ("no blocking defects were
found. Verdict: PASS") does not trip the wire.

**The tripwire is not a natural-language negation detector, and is deliberately not
being grown into one.** It catches a literal, nearby denial and nothing more. A miss is
safe precisely because `consistent` upgrades nothing on its own: it falls through to the
`--attest-reviews` requirement, so the tripwire can never manufacture a `QUALIFIED`.

A minimal document that satisfies every row above:

```text
# Representative cross-family review

Source commit reviewed : <full-source-commit>
Conversation id        : <conversation-id>
Reviewing host family  : Codex CLI
Counterpart host family: Claude Code
Resolved model identity: <observed-model-id>
Resolution status      : observed

This review was conducted independent of the implementation.

Verdict: PASS
```

## 5. Exit codes

| Code | Meaning | What to do |
|---|---|---|
| `0` | The requested operation completed. The record may still contain **explicit missing evidence** — retaining an explicitly `INCOMPLETE` lab archive is a success and makes no qualification claim. | Read `qualification` in the printed record. |
| `2` | **Bad input or precondition failure.** Placeholder path, unsafe `--version`, unresolvable commit, store inside the source root, junction on an output ancestor, malformed `--proofs`, or a **release-ID collision** (the ID is retained with different recorded inputs). | Fix the input, or allocate a new version. No retained release is created or changed. Every such refusal happens before anything is built, with one exception: a collision that surfaces only while publishing keeps its **complete** payload under `.attempts/<uuid>/` and prints that path. |
| `1` | **Execution or IO failure — including qualification failure.** Whatever was built is retained and its path printed, in the directory its **contents** belong in: a **complete** payload (a qualification failure, a build that finished and lost its version name, or a leak-gate refusal — the scan runs last, after the record is written) under `.attempts/<uuid>/`; a **partial** build (a gate exceeded its ceiling or could not be launched, the pinned source has no `release.ps1`, the retained manifest is not a faithful copy) under `.aborted/<uuid>/`; and if neither move is possible, the staging directory under its own name. Also covers damaged retained bytes found while verifying, and text this tool cannot encode as UTF-8. | Go to section 8. |

Qualification values: `QUALIFIED`, `INCOMPLETE` (a required gate or proof is missing),
`BLOCKED` (a gate ran and failed). A missing or failed gate **can never** produce
`QUALIFIED`, and in every case the source archive is still retained.

Toolkit `QUALIFIED` requires all four of: the exact-source root `python -m pytest`, the
staged `release.ps1 -Provider all`, artifact verification of the **retained** bytes
against the manifest `release.ps1` produced, and a real representative cross-family
review with model-resolution evidence that **a named party attests** through
`--attest-reviews` and whose cited evidence document does not trip the consistency
tripwire. The first three are executed here; the fourth is attested, not verified —
section 4.1.

## 6. What is retained

```
<store>/<product>/<version>/     a retained release
  source.zip                     git-tracked files of the pinned commit
  release.json                   the record, schema_version 1
  SHA256SUMS                     raw SHA-256 of every retained file except itself
  PUBLIC-SHA256SUMS              raw SHA-256 of the publishable files except itself
  release-notes.md               sanitized, public-safe notes
  receipt.json                   this operation's argv / time / exit / evidence
  verify-artifacts.py            the retained verifier (publishable; the notes tell
                                 a consumer to run it, so it is NOT under checks/)
  checks/                        raw host run evidence (private; never published)
  reviews/  proofs/              imported evidence (private; never published)
  public/packet.json             what may be published, and what may not
  CHECKSUMS.txt                  toolkit only: release.ps1's ORIGINAL normalized manifest
  dist/{claude,gpt,codex}/       toolkit only: the built profiles
<store>/.attempts/<uuid>/        a retained COMPLETE payload that was not published
                                 (a qualification failure, or a build that lost its
                                 version name to another process)
<store>/.aborted/<uuid>/         a retained PARTIAL build from a run that failed
                                 before the payload was finished; it may have no
                                 release.json
<store>/.work/<uuid>/            scratch; removed once the payload is safely retained
```

The payload is built in a unique sibling staging directory and published by **one
rename of the complete directory**, so a release directory is never observed half-built.

Three checksum concepts are deliberately separate, and `release.json`'s
`checksum_semantics` field restates them beside the data:

- `CHECKSUMS.txt` — **normalized payload checksums** produced by `release.ps1` over
  `dist/` (CRLF→LF, BOM stripped by the builder).
- `SHA256SUMS` and `release.json`'s `artifacts` — **raw whole-file SHA-256** over the
  retained bytes. `artifacts` excludes `release.json`, `SHA256SUMS`, and
  `PUBLIC-SHA256SUMS` to avoid a hash cycle; `SHA256SUMS` covers both the record
  and the public manifest and excludes only itself. `PUBLIC-SHA256SUMS` covers
  every publishable file except itself.
- `source.zip` — its **container metadata** is not part of the identity and need not
  reproduce byte-for-byte. Its **extracted member contents** must.

`release.json` carries no machine-specific absolute path: recorded `cwd` values are
relative to the disposable checkout — except `artifact-verification`, which verifies the
**retained** bytes and therefore runs in the release directory and records
`<release-dir>` — and recorded `argv` entries substitute a token
(`<python-exe>`, `<powershell>`, `<source-checkout>`, `<stage-dir>`, `<release-dir>`,
`<source-root>`, `<store>`, `<proofs>`) for each machine path. The tokens are explained in the record's
own `path_tokens` field, and the concrete interpreter identity survives as a **version**
in `environment`, not as a path. The invocation itself always uses the real paths.

`builder_commit` is the commit of the repository that owns the helper. It is recorded
**separately** from `source_commit`, the product commit being released, and the two are
never conflated.

## 7. Reopen and re-verify a retained release

**Cheap check — hashes only.** From the release directory, with any Python 3
interpreter. This is also how a consumer verifies a copy:

```powershell
python verify-artifacts.py SHA256SUMS .
```

For a toolkit release, the normalized payload manifest is a separate check:

```powershell
python verify-artifacts.py CHECKSUMS.txt . --require-dir dist/claude
```

Exit 0 means every listed path exists and hashes as recorded; exit 1 prints one
`MISSING` / `MISMATCH` line per problem.

**Full check — hashes plus a rebuilt source comparison.** Re-run the ORIGINAL command
verbatim. A repeated request never overwrites and never rebuilds the distribution; it
re-resolves the commit, re-creates the disposable checkout, and then:

```powershell
python tools/baseline_release.py toolkit --source-root $toolkitRoot --source-commit $sourceCommit --version v0.1.0-baseline.1 --store $releaseStore --python-exe $pythonExe
```

- **exit 0, `VERIFIED`** — recorded inputs, every artifact hash, `SHA256SUMS`, and
  `source.zip`'s extracted contents all match a fresh checkout of the same commit.
  Nothing was written.
- **exit 2, `COLLISION`** — the release ID is already retained with different recorded
  inputs. The retained release is untouched. Allocate a new version.
- **exit 1, `do not verify`** — the retained bytes are damaged, or the archive's
  extracted contents no longer match the pinned commit. The message names each
  offending path. Do not repair in place: keep the damaged directory as evidence and
  cut a new release ID from the same commit.

`--proofs` is ignored (with a printed note) when verifying an already-retained release.

## 8. Recover from a failed attempt

A qualification failure is retained whole at `<store>/.attempts/<uuid>/` — the same
layout as a release, including `source.zip`, `release.json`, `release-notes.md`,
`receipt.json` and every `checks/` evidence file. The run prints that directory before
exiting nonzero.

1. **The version name is NOT reserved.** A failed attempt never creates
   `<store>/<product>/<version>/`.
2. **Read `qualification_reasons` in the attempt's `release.json`.** Each reason names
   the gate or the missing proof.
3. **Read the named evidence file** under `checks/`. It carries the gate's full argv,
   cwd, exit code and captured stdout/stderr.
4. **Fix the cause at its source** — repair the product, or obtain the missing review —
   and re-run. A retry allocates a **new** attempt directory and preserves the previous
   one untouched.
5. **Nothing is deleted automatically, ever.** Prune attempts by hand, deliberately,
   and only after their evidence has been read.

### A run that aborted mid-build

A qualification failure produces a **complete** payload. A run that aborts before it
gets that far — a gate exceeded its time ceiling or could not be launched, the
pinned source has no `tools/release.ps1`, the retained `CHECKSUMS.txt` is not a
faithful copy of the manifest `release.ps1` wrote — has no such payload. Whatever had
been built is moved to `<store>/.aborted/<uuid>/`, and **that path is printed with
the failure**.

A **leak-gate** refusal is not in that list, and this is worth knowing before you go
looking in the wrong directory: the scan is the last thing that runs, after the
record, the notes, the receipt and `SHA256SUMS` are all written, so its payload is
COMPLETE and lands under `.attempts/` — with everything you need to read to find the
offending value.

The split is about what the directory **contains**, not which error routed it there,
and the tool decides it by looking for `release.json` on disk rather than by reading
the error in flight. So a build that finished and then lost a race for its version
directory — another process created `<store>/<product>/<version>` while this run was
staging — is a COMPLETE payload, and is filed under `.attempts/`.

If **neither** move is possible — the store subdirectory is itself unwritable, or a
leftover directory already holds this run's id — nothing is discarded: the payload
keeps its own `<store>/<product>/.staging-<uuid>/` path, and that path is printed
with the same description of what it holds. A complete payload is therefore reported
accurately in all three cases rather than being announced as a partial build.

Read an `.aborted/` directory as **partial**, not as an attempt. It may have no `release.json`, no
`release-notes.md` and no `SHA256SUMS` — those are written last. What it does carry
is `source.zip` and every `checks/` evidence file the run had already produced, which
is the part the error message alone cannot give you. Nothing is deleted, no version
name is reserved, and the fix is the same as for an attempt: repair the cause at its
source and re-run.

Common causes, in the order they usually appear:

| Symptom | Cause |
|---|---|
| `qualification=BLOCKED`, `source-pytest` exit nonzero | the pinned source's own suite is red. The archive is still retained. |
| `qualification=BLOCKED`, `staged-release` exit nonzero | `release.ps1` aborted — usually its package-integrity phase. Its evidence file carries the failing output. |
| `qualification=INCOMPLETE`, all gates exit 0 | no qualifying cross-family review is attached. Attach one with `--proofs`. |
| exit `1`, no `qualification=` line, an `.aborted/<uuid>` path printed | the run failed before the payload was finished. Read `checks/` inside that directory. |
| exit `1`, `a machine-specific absolute path reached a PUBLIC artifact` | the leak gate found a path in a generated artifact. The message names the artifact and line. Section 9, including the token false positive. |
| exit `1`, `could not be read back and graded` | the leak gate could **not read** an artifact this run had just written — a lock or an IO fault, **not** a leak finding. Retry; if it repeats, the store path is the suspect. |
| exit `2`, `carries a character UTF-8 cannot encode` | a `--proofs` string, or an argument, holds a lone surrogate. Fix the value; nothing was built. |
| `qualification=INCOMPLETE`, a review IS attached, `attested_by` is `null` | `--attest-reviews` was not given. Re-run with it, naming the accountable party. Section 4.1. |
| `qualification=INCOMPLETE`, a review IS attached, `evidence_consistency` is `unstated` | the evidence document omits a claim the row makes. `known_gaps` names each one; fix the document, not the JSON. Section 4.1. |
| `qualification=INCOMPLETE`, a review IS attached, `evidence_consistency` is `contradicted` | the evidence document **denies** a claim the row makes. Read the document — the row and the review disagree about what happened. No flag overrides this. Section 4.1. |
| `not a git working tree` | `--source-root` is not a checkout. |
| `inside --source-root` | point `--store` outside the working source. |
| `reparse point` | a junction or symlink on the store path or an ancestor. |

## 9. The public publication packet

`public/packet.json` describes what may be published and what may not. It is a
description, not an action: `publication_status` is always `NOT_PUBLISHED`.

- **Publishable**: `release.json`, `PUBLIC-SHA256SUMS`, `release-notes.md`,
  `verify-artifacts.py`, and, when built, `CHECKSUMS.txt` and `dist/` for the toolkit.
- **Never publishable**: the exact retained `source.zip` (its member contents are
  not inspected here), `SHA256SUMS` (it names private files), `checks/` (captured run output carries machine-specific
  absolute paths), `reviews/` and `proofs/` (imported private evidence), `receipt.json`
  (a private run record), and `public/` itself.
- `verify-artifacts.py` sits at the release **root**, not under `checks/`, precisely so
  the publishable set stays self-consistent: `release-notes.md` is publishable and tells
  its reader to run the verifier, so the verifier has to be in the set the reader
  receives. It is generated from a hardcoded constant and carries no captured host
  output, which is the only reason `checks/` is private. Private consumer backups and raw host
  records are out of scope entirely — they are never inputs.
- `release.json` publishes the release-relative **locator** of every evidence file. The
  evidence **bytes** stay local.
- **Secrets and credentials are never inputs and are never recorded.** Dependency names
  and authentication prerequisites are all the release notes carry — for the toolkit,
  that is `gh auth login` for GitHub Copilot CLI, with no `OPENAI_API_KEY` used or
  needed.

Before retaining anything, the tool scans the offered generated text files, including
each `dist/` file, the verifier, the public manifest, and the packet metadata, for
machine-specific absolute paths — a Windows drive-letter home path in either
separator, and the POSIX `/home/<user>/…` and `/Users/<name>/…` spellings, because
only a `toolkit` run requires PowerShell and a `lab` run can therefore be cut off
Windows — and refuses to retain the release if one is found. The documented
placeholder forms (`/home/<user>/…`, `C:/Users/<user>/…`) stay legal.

The same scan runs over a `--proofs` document at ingestion, where a hit is exit 2.

**This gate fails closed, and that has a price. Read this before filing a bug
against it.** An artifact the tool cannot read back counts as a failure — it is the
last gate before a release is kept, so an ungraded file is never treated as clean.
The run says which of the two happened: a path that leaked, or a file that could not
be read. And a documented argv token is **not** an exemption:

| String | Verdict |
|---|---|
| `<source-checkout>/tools/release.ps1` | clean — no `home`/`Users` segment |
| `<store>/home/<app>/main.py` | **refused** — an honest relative tail under a token root |
| `<source-checkout>/home/<someone>/leak` | **refused** — a real path spelled with a token prefix |

(Rows 2 and 3 are written with a placeholder in the third segment so that *this
document* passes the same scan. Replace the placeholder with a concrete segment and
the two are indistinguishable: a `--proofs` field and a tool-emitted `argv` entry are
the same bytes once written.)

So no rule that admits row 2 can refuse row 3 — and admitting row 3 publishes a
machine-specific path while the gate reports the release clean. A release refused for
row 2 costs one run and prints why; a release published for row 3 costs the leak this
tool exists to prevent. So row 2 is refused deliberately.

**Known limitation, and the workaround.** If the product being released has a
top-level directory named `home` or `Users`, a recorded `argv`/`cwd` entry pointing
into it — a token followed immediately by that segment — reads as a leak and aborts
the run at exit 1, and a historical `--proofs` document carrying that spelling is
refused at exit 2.
Neither is a defect report. Either rewrite that one recorded entry to a form that
does not begin the tail with `home/` or `Users/` (a `--proofs` document is yours to
edit — it is evidence you are attaching, not a retained record), or, if the entry is
generated rather than supplied, invoke the gate from a directory layout that does not
produce it. Do **not** "fix" this by exempting the token: that exemption existed, was
measured, and let 3 of 13 real leaks through.

Archive member contents are not re-scanned here; the exact pinned archive stays
private. The scan recognizes the specified absolute user-path shapes, not arbitrary
secrets or other private data. On a published subset, run
`python verify-artifacts.py PUBLIC-SHA256SUMS .`; on the complete retained release,
run `python verify-artifacts.py SHA256SUMS .`.

The lab baseline stays local. Publication of the toolkit packet to its existing remote
is a subsequent, exact-packet operator step, and is out of this runbook's scope.

## 10. Related documents

- [`baseline-releases-plan.md`](baseline-releases-plan.md) — the approved Phase BR plan;
  section 6.1 owns this tool's contract.
- [`product-charter.md`](product-charter.md) — the release invariants, including the
  cross-family review requirement.
- [`../CLAUDE.md`](../CLAUDE.md) — key commands, environment requirements, and the
  DONE-gate rule for this repository's own suite.
