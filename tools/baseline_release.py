#!/usr/bin/env python3
"""baseline_release.py -- release store + record writer (Phase BR, Step 147).

Turns a PINNED product source commit into an identifiable, reopenable release
using this repository's EXISTING toolchain. It builds nothing of its own: the
toolkit package is produced by `tools/release.ps1` (which itself stages from the
git index and invokes the staged `tools/build-distributions.ps1`), and the source
checks are the project's own `python -m pytest`. This module orchestrates,
records, and retains; it never re-implements a gate and never publishes.

Python standard library only. No new third-party dependency is introduced.

WHAT IT IS NOT
--------------
* It does not publish. No tag is created, nothing is uploaded, no consumer home
  is touched. It prepares a sanitized PUBLIC PUBLICATION PACKET and stops; the
  actual publication is a later, separate operator step.
* It does not certify a workflow. The checks it records are deterministic source
  checks. Native host acceptance (an observed Claude Code / Codex CLI session) is
  a different evidence class and is never inferred from a green suite.
* It does not run, and cannot verify, a cross-family review. The product charter's
  release invariant ("run at least one real representative cross-family review")
  can only be satisfied by attaching that review as evidence through `--proofs`
  AND naming an accountable party with `--attest-reviews`. Absent either, a
  release CANNOT reach QUALIFIED, no matter how green the suites are. See
  A REVIEW IS ATTESTED, NOT VERIFIED, below.

CLI
---
    baseline_release.py {toolkit|lab}
        --source-root <dir> --source-commit <rev> --version <one-path-segment>
        --store <dir> --python-exe <interpreter> [--proofs <json>]
        [--attest-reviews <accountable name>]

`--help` works. Obviously unresolved placeholder values (`$toolkitRoot`,
`<store>`, `%HOME%`, `path/to/x`, empty) are refused rather than acted on.

EXIT CODES
----------
    0  the requested operation completed successfully. The record may still
       contain EXPLICIT missing evidence -- retaining an explicitly INCOMPLETE
       lab archive is a success, and it makes no qualification claim.
    2  bad input or a precondition failure (bad flag, placeholder path, unsafe
       version, unresolvable commit, malformed proofs, release-ID collision).
    1  execution or IO failure -- including a QUALIFICATION FAILURE. Whatever was
       built is RETAINED and NAMED on the way out, in the directory its CONTENTS
       belong in: a COMPLETE payload (a failed qualification, or a build that lost
       its version name) under `.attempts/<uuid>/`, a PARTIAL build under
       `.aborted/<uuid>/`, and if neither move is possible, the staging directory
       under its own name. One of those paths is printed with every such failure.

STORE LAYOUT
------------
    <store>/<product>/<version>/        a retained release ("release ID" =
                                        "<product>/<version>", allocated by the
                                        caller, never by this tool)
        source.zip                      pinned source payload (git-tracked files
                                        of the pinned commit)
        release.json                    the record; schema_version 1
        SHA256SUMS                      raw SHA-256 over every retained file
                                        except itself (so it covers release.json)
        release-notes.md                sanitized, public-safe notes
        verify-artifacts.py             the retained verifier. At the release
                                        ROOT and PUBLISHABLE, because the notes
                                        tell a recipient of the published subset
                                        to run it -- `checks/` is private, so the
                                        verifier cannot live there
        receipt.json                    this operation's argv/time/exit/evidence
        checks/                         raw host run evidence (private)
        reviews/, proofs/               imported evidence (private; never public)
        public/packet.json              what may be published, and what may not
        CHECKSUMS.txt                   toolkit only -- the ORIGINAL normalized
                                        manifest produced by release.ps1
        dist/{claude,gpt,codex}/        toolkit only -- the built profiles
    <store>/.attempts/<uuid>/           a COMPLETE payload that was not published
                                        -- a qualification failure, or a build
                                        that finished and then could not take its
                                        version name. It does NOT reserve the
                                        version name; a retry allocates a new
                                        attempt and never disturbs this one.
                                        Nothing is ever deleted automatically.
    <store>/.aborted/<uuid>/            a PARTIAL build: the run failed before the
                                        payload was finished. NOT a release and
                                        NOT an attempt: it may have no
                                        release.json. Its path is printed with the
                                        failure; nothing is ever deleted
                                        automatically.
    <store>/<product>/.staging-<uuid>/  build scratch, published by ONE rename
    <store>/.work/<uuid>/               disposable checkout + release stage

Which of the two retention directories a failed run lands in is decided by what
the stage CONTAINS (stage_bucket), read off the disk -- never by which exception
was in flight. If neither move is possible the payload keeps its staging path, and
that path is printed with the same description of what it holds.

THREE CHECKSUM CONCEPTS, DELIBERATELY SEPARATE
----------------------------------------------
    CHECKSUMS.txt   NORMALIZED payload checksums produced by release.ps1 over
                    dist/ (CRLF->LF, BOM stripped by the builder). Reproduces
                    across checkouts with different line-ending history.
    SHA256SUMS      RAW whole-file SHA-256 over the retained bytes of this
                    release. Answers "are the retained bytes intact".
    source.zip      Its CONTAINER metadata is not part of the identity and need
                    not reproduce byte-for-byte. Its EXTRACTED MEMBER CONTENTS
                    must, and a repeated request proves exactly that.

REPEATED REQUESTS (this is also the reopen / re-verify path)
------------------------------------------------------------
A second invocation naming an existing release ID never overwrites it. It
re-resolves the commit, re-creates the disposable checkout, and then either
(a) VERIFIES -- recorded inputs match, every artifact hash matches, SHA256SUMS
matches, and source.zip's extracted contents match a fresh checkout of the same
commit -- and exits 0 without rebuilding; or (b) REFUSES as a collision (exit 2)
when the recorded inputs differ, or reports damaged retained bytes (exit 1).

A REVIEW IS ATTESTED, NOT VERIFIED
---------------------------------
GOVERNING INVARIANT, and the one this module is organised around:

    A gate's POSITIVE signal must originate outside the authorship domain of the
    party the gate is applied to. Where no such signal can be obtained, this tool
    RECORDS the claim and NAMES the party accountable for it. It never converts
    one author's self-consistency into a verification.

Every native gate already obeys it: a required gate counts only when THIS process
executed it (`execution == "native"`), an import is hardcoded to
`execution: "imported"` and can never satisfy one, and a measured environment
always beats an imported claim about it.

The cross-family review is the ONE required element this tool cannot execute. The
caller supplies the row through `--proofs` and the evidence document it cites --
so BOTH sides of any text comparison between them are authored by the same party.
A token match across them therefore measures the self-consistency of one author's
story; it is not, and cannot be made into, verification. (Round 1 of review asked
for corroboration, round 2 defeated it with a verbatim transcript of a FAILING
review whose every claimed token was present. The bypass family -- negation,
quotation, rebuttal, a pasted failing transcript -- is unbounded because the
reader is reading bytes the caller wrote. It is a category error, not a bug.)

So qualification rests on a SEPARATE, NAMED ACT instead:

    --attest-reviews "<accountable party>"

a CLI flag, deliberately NOT a `--proofs` field, so that reusing a historical
proofs file can never silently carry the attestation forward. It is recorded on
each imported review row as `attested_by`, and QUALIFIED then means exactly:

    every machine-checkable gate ran here and passed, PLUS a well-formed,
    source-bound, cross-family review claim that a NAMED party stands behind.

That is the same shape the charter already uses for model identity -- observe it
where the host supports it, and otherwise carry a waiver that is "explicit and
named". Without the flag a well-formed review row yields INCOMPLETE naming the
missing act; the archive, the row and its evidence are all still retained.

The text comparison survives, DEMOTED to what it can honestly do: a NEGATIVE-ONLY
tripwire (`evidence_consistency`). Consistency can be locally FALSIFIED, never
locally established. So:

  * `unstated` / `contradicted` / `no-evidence` / `evidence-unreadable` BLOCK
    qualification -- a falsification is a real finding and is fail-closed;
  * `consistent` upgrades NOTHING on its own. It means only "this tripwire did
    not fire", and the record says that rather than "corroborated".

Being negative-only is what makes the tripwire's incompleteness safe: a miss
falls through to the attestation requirement, so it can never manufacture a
QUALIFIED. It is deliberately NOT extended toward completeness -- that is the
whack-a-mole this design exists to end.

What this gives up, stated plainly: a named party can still attest a review that
did not happen. The tool never had the power to catch that; it only had the
appearance of it. The record now says whose name the claim rests on.

RECORDED PATHS ARE RELATIVE OR TOKENIZED
----------------------------------------
release.json is a PUBLIC artifact, so it carries no machine-specific absolute
path. Recorded `cwd` values are relative to the disposable source checkout --
except a gate that verifies the RETAINED release bytes, which necessarily runs in
the release directory and records the `<release-dir>` token instead. Recorded
`argv` entries substitute a token for each machine-specific absolute path
(`<python-exe>`, `<powershell>`, `<source-checkout>`, `<stage-dir>`,
`<release-dir>`, `<source-root>`, `<store>`, `<proofs>`). The tokens are
explained in the record's own `path_tokens` field, and the concrete interpreter
identity survives as a VERSION in `environment`, not as a path. The invocation
still happens with the real absolute paths; only the RECORD is tokenized.

BUILDER IDENTITY IS NOT PRODUCT IDENTITY
----------------------------------------
`builder_commit` is the commit of the repository that owns THIS file. It is
recorded separately from `source_commit` (the product commit being released) and
the two are never conflated -- releasing the toolkit from its own repository
makes them coincidentally equal only when the caller pins this repository's HEAD.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

SCHEMA_VERSION = 1

EXIT_OK = 0
EXIT_EXEC = 1
EXIT_INPUT = 2

#: positional product selector -> the product name written into the record.
PRODUCTS = {"toolkit": "skill-mesh", "lab": "skill-mesh-lab"}

#: profiles a toolkit release must package (`release.ps1 -Provider all`).
TOOLKIT_PROVIDERS = ("claude", "gpt", "codex")

QUALIFICATION_VALUES = ("INCOMPLETE", "BLOCKED", "QUALIFIED")

#: ONE safe path segment. Rejects traversal ('.', '..'), separators, drive
#: letters and leading punctuation by construction.
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
VERSION_MAX_LEN = 96

#: `--attest-reviews` names an accountable party. It lands in a PUBLIC record, so
#: it is bounded like every other caller string that reaches one.
ATTESTATION_MAX_LEN = 120

#: Git object IDs: SHA-1 (40) or SHA-256 (64), full and lowercase.
FULL_OID_RE = re.compile(r"^([0-9a-f]{40}|[0-9a-f]{64})$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

#: Windows device names are unusable as directory names regardless of the
#: character class above.
RESERVED_SEGMENTS = frozenset(
    ["con", "prn", "aux", "nul"]
    + ["com%d" % i for i in range(1, 10)]
    + ["lpt%d" % i for i in range(1, 10)]
)

#: A real absolute user-home path, in the three spellings a machine running this
#: tool can produce: Windows drive-letter (either separator), POSIX
#: `/home/<user>/...`, and macOS `/Users/<name>/...`. Each negative lookahead keeps
#: the documented placeholder form legal.
#:
#: The first alternative is the SAME shape the repository's own committed-path gate
#: uses (tests/package-integrity/test_manifest_contract.py); this is the runtime
#: counterpart that keeps a GENERATED public artifact as clean as a committed one.
#: It is deliberately a SUPERSET of that gate rather than a copy of it: a `lab`
#: release has no `powershell` precondition (only `toolkit` does), so it can
#: legitimately run on a non-Windows machine, where a POSIX home path reaching
#: release.json / release-notes.md / packet.json / receipt.json / attested_by would
#: be exactly the leak the Windows branch exists to stop.
#:
#: The lookbehind is what keeps the POSIX branch off a string that merely CONTAINS
#: the segment: a repo-relative `docs/Users/x` and a URL
#: `https://example.com/Users/octocat` are preceded by a path character, while in
#: every shape this gate has been measured against -- the red set in
#: tests/release/test_baseline_release.py -- a genuinely absolute `/home/...` is
#: preceded by nothing, a quote, a space, a separator or a redirect.
#:
#: KNOWN FALSE POSITIVE, ACCEPTED DELIBERATELY. This tool's own records spell a
#: path as `<token>/tail` (PATH_TOKEN_DOC below) and every token closes with `>`,
#: which is not in the excluded class -- so `<store>/home/x`, a relative tail
#: under a token root, reads here as an absolute POSIX home and is REFUSED. Two
#: exemptions were measured and both buy a false NEGATIVE, which a fail-closed
#: gate may not have:
#:
#:   * adding `>` to the excluded class also exempts the shell-redirect spelling
#:     `>/home/someone/log`;
#:   * substituting the documented tokens out before matching (the shape this
#:     file carried into Step 147's review round 2) exempts a caller-supplied
#:     `<source-checkout>/home/<user>/leak` exactly as readily -- a `--proofs`
#:     field and a tool-emitted argv entry are the SAME BYTES, so no textual rule
#:     can separate them. Measured: 3 real leaks passed, in a red set of 13.
#:
#: A false positive costs one refused run with a legible message; a false
#: negative publishes a machine-specific path and the gate says nothing. So the
#: false positive is KEPT, and the runbook documents it (section 9) with its
#: workaround. Do not close it by exempting a lexeme.
#:
#: APPLY THIS PATTERN THROUGH contains_private_path(), NOT DIRECTLY: that helper
#: is the ONE predicate, and every caller in this module goes through it.
PRIVATE_PATH_RE = re.compile(
    r"[A-Za-z]:[\\/]Users[\\/](?!<)"
    r"|(?<![A-Za-z0-9_.~%-])/(?:home|Users)/(?!<)"
)

#: Obviously unresolved placeholders. An operator who pastes the runbook line
#: without resolving its variables must be refused, never acted on.
PLACEHOLDER_PATTERNS = (
    (re.compile(r"^\s*$"), "is empty"),
    (re.compile(r"[<>]"), "contains '<' or '>' (an unresolved placeholder)"),
    (re.compile(r"(^|[\\/])\$"), "contains an unresolved shell/PowerShell variable"),
    (re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%"), "contains an unresolved %VARIABLE%"),
    (re.compile(r"(?i)\b(placeholder|changeme|your[-_]?path)\b"), "is a placeholder word"),
    (re.compile(r"(?i)(^|[\\/])path[\\/]to([\\/]|$)"), "is a 'path/to/...' placeholder"),
    (re.compile(r"^\.\.\.$"), "is an ellipsis placeholder"),
)

#: Release-relative path PREFIXES that may be published, and the ones that may
#: not. A trailing '/' means "this directory and everything under it".
#: `verify-artifacts.py` is publishable and lives at the release ROOT, not under
#: `checks/`: release-notes.md (publishable) instructs the reader to run it, so a
#: recipient of the published subset must actually receive it. It is written from
#: the hardcoded VERIFY_ARTIFACTS_SOURCE constant below and carries no captured
#: host output, which is what makes `checks/` private in the first place.
PUBLIC_INCLUDE_COMMON = ("source.zip", "release.json", "SHA256SUMS", "release-notes.md",
                         "verify-artifacts.py")
PUBLIC_INCLUDE_TOOLKIT = ("CHECKSUMS.txt", "dist/")
#: The generated public text artifacts the leak scanner covers, release-relative.
#: ONE list: `_build_and_publish` scans exactly these and `build_public_packet`
#: publishes exactly this as `sanitization.scanned`, so the packet can never
#: misdescribe what was actually graded.
PUBLIC_SCANNED_ARTIFACTS = ("release.json", "release-notes.md",
                            "public/packet.json", "receipt.json")
PUBLIC_EXCLUDE = (
    ("checks/", "raw host run records -- captured stdout/stderr carries machine-specific absolute paths"),
    ("reviews/", "imported review evidence -- private review material, kept local"),
    ("proofs/", "imported check evidence -- private run material, kept local"),
    ("receipt.json", "private run record for this operation"),
    ("public/", "the packet description itself is local metadata, not a published artifact"),
)

#: Generous ceilings so a real release is never cut short. Tests never reach them.
TIMEOUT_GIT = 1800
TIMEOUT_SOURCE_PYTEST = 4 * 3600
TIMEOUT_RELEASE_PS1 = 3 * 3600
TIMEOUT_VERIFY = 3600
TIMEOUT_PROBE = 300

#: Bytes read per hashing chunk.
_CHUNK = 1 << 20

#: What _kill_process_tree sends to a timed-out child's PROCESS GROUP on POSIX.
#: SIGKILL wherever it exists, which is every POSIX host; the fallback is here
#: only so this module imports and stays testable on Windows, where the branch
#: that reads it is not taken (`taskkill /T` covers that side).
_GROUP_KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)

PATH_TOKEN_DOC = {
    "<python-exe>": "the interpreter supplied by --python-exe; its VERSION is recorded in environment.python",
    "<powershell>": "the Windows PowerShell 5.1 host; its VERSION is recorded in environment.powershell",
    "<source-checkout>": "the disposable clean checkout of source_commit, discarded after the run",
    "<stage-dir>": "the release stage tools/release.ps1 wrote into, discarded after the run",
    "<release-dir>": "this release's own directory; a gate that verifies the RETAINED bytes runs there, so its recorded cwd is this token rather than a checkout-relative path",
    "<source-root>": "the read-only working source the commit was resolved from",
    "<store>": "the release store root",
    "<proofs>": "the --proofs file supplied by the caller",
}

#: A documented token is NOT exempt from the leak scan. See PRIVATE_PATH_RE's
#: "KNOWN FALSE POSITIVE" note above: the exemption was implemented, measured,
#: and removed because it let a caller-supplied path through the one gate that
#: exists to stop it.

CHECKSUM_SEMANTICS = {
    "artifacts": "raw SHA-256 over each retained file's bytes; excludes release.json and SHA256SUMS to avoid recursive hashing",
    "SHA256SUMS": "raw SHA-256 over every retained file except SHA256SUMS itself, so it covers release.json",
    "CHECKSUMS.txt": "the ORIGINAL normalized payload manifest produced by tools/release.ps1 over dist/ (CRLF->LF, BOM stripped by the builder); a separate concept from raw whole-file hashes",
    "source.zip": "ZIP container metadata is not part of the identity and need not reproduce byte-for-byte; extracted member contents must, and a repeated request verifies exactly that",
}

#: The product charter's release HOSTS are Claude Code and Codex, so
#: "cross-family" means Claude <-> Codex. GitHub Copilot, Gemini and local models
#: are NOT part of this release, and none of them substitutes for either family.
CROSS_FAMILY_TOKENS = ("claude", "codex")

#: The closed vocabulary a review row's `evidence_consistency` field carries.
#: This is a NEGATIVE-ONLY tripwire (see "A REVIEW IS ATTESTED, NOT VERIFIED"):
#: every value except "consistent" BLOCKS qualification -- including the field
#: being absent altogether -- and "consistent" upgrades nothing by itself. The
#: word is "consistent", never "corroborated", because a comparison between two
#: documents the same caller wrote cannot corroborate either one.
EVIDENCE_CONSISTENCY_VALUES = ("consistent", "unstated", "contradicted",
                               "evidence-unreadable", "no-evidence")

#: Clause separators for the negation tripwire. A claim is graded inside the
#: clause that carries it, so an unrelated negation elsewhere in the document
#: ("no blocking defects were found. Verdict: PASS") cannot trip it.
_CLAUSE_SPLIT_RE = re.compile(r"[.;:!?\n\r]+")

#: Negation markers. Kept deliberately SMALL and literal. This list is not, and
#: is not trying to be, a natural-language negation detector -- see the module
#: docstring: a miss falls through to the `--attest-reviews` requirement and can
#: never manufacture a QUALIFIED, so completeness is not what makes it useful.
NEGATION_MARKERS = frozenset((
    "not", "no", "never", "without", "isn", "wasn", "aren", "weren", "doesn",
    "didn", "cannot", "couldn", "failed", "fails", "lacks", "lacking",
    "missing", "absent", "neither", "nor",
))

#: How many words before a claim a negation marker may sit and still be read as
#: negating it. Three covers "was NOT independent", "is NOT PASS",
#: "was not actually independent"; it stops well short of a whole clause.
NEGATION_WINDOW = 3


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #

class InputError(Exception):
    """Bad input or an unmet precondition -- exit 2."""


class ExecutionError(Exception):
    """Execution or IO failure -- exit 1."""


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def md_inline(value, code: bool = False) -> str:
    """Neutralize a string for inline Markdown.

    release-notes.md is a PUBLIC artifact whose table cells and bullets carry
    values that came from `--proofs`. A raw '|' ends a table cell early, a
    newline ends the row or the bullet, and a backtick closes a code span -- all
    three let attested text restructure the published document.

    PLAIN-TEXT MODE (`code=False`) additionally neutralizes the two constructs a
    caller fragment could use to inject rather than merely reformat: raw HTML and
    a forged link. `&`, `<` and `>` become entities and `[`/`]` are escaped. This
    also FIXES fidelity -- a recorded token such as `<release-dir>` is today
    swallowed by a renderer as an unknown HTML tag, and `&lt;release-dir&gt;`
    renders as the literal text.

    Emphasis markers and backticks are deliberately NOT escaped in plain-text
    mode: this path also carries this module's OWN prose, which uses them
    intentionally. So plain-text mode is for AUTHORED prose, tool-set enums and
    VALIDATED machine-typed values (a bool that load_proofs already type-checked)
    -- it carries no free-form caller string today. Read that as a CONVENTION the
    render sites keep, NOT as a mechanism this function enforces: md_inline()
    cannot tell where its argument came from. The mechanism lives one level up,
    and which one applies depends on how a caller value ARRIVES at the sink:

    * md_code() -- the value is still intact and separately addressable when the
      sink sees it (a table cell). A CommonMark renderer escapes a code span's
      whole content.
    * md_untrusted() -- the value was already fused into an authored sentence by
      %-formatting before the sink saw it (the qualification_reasons/known_gaps
      channel). There is no "value" left to wrap, so the whole sentence is
      treated as untrusted.

    CODE-SPAN MODE (`code=True`) escapes nothing except the backtick and the
    pipe, because entity text inside a code span would render as the entity.

    SCOPE: all three of these helpers neutralize MARKDOWN. None of them grades
    whether the text can be ENCODED -- that is reject_unencodable()'s job at the
    caller boundary -- and none of them is a private-path check.
    """
    text = str(value)
    for ws in ("\r\n", "\r", "\n", "\t"):
        text = text.replace(ws, " ")
    if code:
        return text.replace("|", "\\|").replace("`", "'")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("[", "\\[").replace("]", "\\]")
    return text.replace("|", "\\|")


def md_code(value) -> str:
    """A caller-controlled value rendered inside a code span.

    The neutralizer for a caller value that reaches the sink INTACT -- a table
    cell, where the sink still knows which string came from `--proofs`. A
    CommonMark renderer escapes a code span's content, and swapping the backtick
    means the span cannot be broken open to escape it.
    """
    return "`%s`" % md_inline(value, code=True)


#: Everything that can OPEN an inline construct in the untrusted channel once
#: `&`, `<` and `>` have already become entities. CommonMark backslash-escapes
#: any ASCII punctuation, so one backslash neutralizes each of them:
#: '\\' (an escape a caller would otherwise be able to forge), '`' (code span),
#: '*' and '_' (emphasis), '[' and ']' (link/image), '|' (table cell), '~' (GFM
#: strikethrough) and '#' (an ATX heading, reachable only if caller text ever
#: leads a bullet -- cheap insurance rather than a claim that it cannot).
_MD_UNTRUSTED_ESCAPES = frozenset("\\`*_[]|~#")


def md_untrusted(value) -> str:
    """Neutralize a MIXED-TRUST sentence for a Markdown bullet.

    `qualification_reasons` and `known_gaps` are the one channel where authored
    prose and caller-supplied `--proofs` text are FUSED into a single sentence by
    %-formatting, at the producer, long before a sink sees them. By then there is
    no "value" left to route through md_code() -- only a sentence -- so a sink
    physically cannot know which substring the caller wrote. Two earlier
    line-scoped fixes neutralized individual sinks where the value DID still
    arrive intact; the defect kept reappearing because the producer set is
    open-ended and every new reason or gap message silently extends it.

    So this answers at the channel instead: the WHOLE sentence is untrusted.
    Everything md_inline() plain mode does, plus a backslash escape on every
    character that could open an inline construct. No per-site judgment is left
    to get wrong, and a producer added later is covered the day it is written.

    THE CHANNEL'S CONTRACT, stated once, here: a qualification reason or a known
    gap is PLAIN TEXT. Markdown formatting is not available in it -- an authored
    backtick or asterisk in one of these messages renders as that literal
    character, so write them with plain quotes. That cost is the safe direction:
    over-escaping puts a cosmetic backslash in the SOURCE and renders correctly,
    while under-escaping is the defect itself -- caller text restructuring the
    "why this release is not QUALIFIED" disclosure that this tool exists to
    publish honestly.

    WHAT IT DOES NOT DO: it neutralizes Markdown STRUCTURE. It does not shorten,
    redact or sanitize the text's CONTENT, it does not check the text for a
    machine-specific path (contains_private_path and the end-of-run scan do
    that), and it does not check that the text is encodable (reject_unencodable
    does that, at the caller boundary).
    """
    text = str(value)
    for ws in ("\r\n", "\r", "\n", "\t"):
        text = text.replace(ws, " ")
    # Entities first, and in this order: raw HTML, autolinks and a leading
    # blockquote marker are all neutralized, and a recorded token such as
    # <release-dir> renders as its literal text instead of being swallowed as an
    # unknown tag. The '&' introduced by '&lt;'/'&gt;' must not be re-encoded.
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # ONE pass over the characters, never chained replaces: a second pass would
    # re-escape the backslashes the first one wrote, turning '\[' into a literal
    # backslash followed by a LIVE '['.
    out = []
    for ch in text:
        if ch in _MD_UNTRUSTED_ESCAPES:
            out.append("\\")
        out.append(ch)
    return "".join(out)


def _kill_process_tree(proc) -> None:
    """Terminate a timed-out child AND its descendants. Best effort, never raises.

    `subprocess.run(timeout=...)` kills only the process it started. `release.ps1`
    spawns `python -m pytest` as a GRANDchild, so killing the powershell host on
    timeout can leave that grandchild alive, holding open file handles inside the
    disposable checkout that `remove_disposable_workspace` then cannot clear --
    its retry/chmod loop cannot force-close a handle a live process still holds.

    One mechanism per platform, because only a `toolkit` run requires PowerShell
    and a `lab` run can legitimately be cut on a non-Windows machine:

      * Windows -- `taskkill /T /F`, which walks the child's descendant tree;
      * POSIX -- SIGKILL to the child's PROCESS GROUP. run() starts every child
        in a new session there, so the child leads a group of its own and that
        group holds the descendants it did not itself detach.

    BOUNDED on both, and deliberately not claimed as total: a descendant that has
    left the tree (Windows) or called setsid/setpgid for itself (POSIX) is
    outside what either mechanism reaches. Nothing in a retained release depends
    on this working -- remove_disposable_workspace warns rather than failing when
    scratch survives.
    """
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                           capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(os.getpgid(proc.pid), _GROUP_KILL_SIGNAL)
        except (OSError, AttributeError):
            pass
    try:
        proc.kill()
    except OSError:
        pass
    try:
        proc.wait(timeout=30)
    except (OSError, subprocess.SubprocessError):
        pass


def run(argv, cwd=None, timeout=None):
    """Run an argument ARRAY. Never a shell string, never shell=True.

    `errors="backslashreplace"` rather than `"replace"`: captured gate output is
    the diagnostic trail a BLOCKED or INCOMPLETE record depends on, and neither
    `powershell.exe` nor a child `python.exe` reliably writes UTF-8 to a captured
    pipe on Windows. U+FFFD DESTROYS the offending byte; `\\xNN` keeps it
    recoverable, so a mis-decoded accented path or localized git error can still
    be read back out of the evidence file. The declared encoding stays UTF-8 on
    purpose -- guessing the console codepage instead would silently mojibake
    genuinely-UTF-8 output, trading a visible escape for an invisible corruption.

    On POSIX the child is started in a NEW SESSION so it leads its own process
    group, which is what gives _kill_process_tree a group to signal on a timeout.
    The kwarg is POSIX-only and is not passed on Windows at all, so Windows
    behaviour here is byte-for-byte what it was; `taskkill /T` covers that side.
    """
    session = {} if os.name == "nt" else {"start_new_session": True}
    proc = subprocess.Popen(
        [str(a) for a in argv],
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="backslashreplace",
        **session
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_process_tree(proc)
        try:
            proc.communicate(timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass
        raise
    return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)


def is_reparse_point(path: Path) -> bool:
    """True for a Windows junction/symlink or a POSIX symlink."""
    try:
        st = path.lstat()
    except OSError:
        return False
    attrs = getattr(st, "st_file_attributes", None)
    if attrs is not None:
        return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    return path.is_symlink()


def assert_no_linked_ancestor(path: Path, label: str) -> None:
    """Refuse an output location whose real identity a link could redirect.

    Checked over the path itself and every EXISTING ancestor: a junction three
    levels up redirects the leaf just as effectively as one on the leaf.
    """
    seen = []
    p = path
    while True:
        seen.append(p)
        if p.parent == p:
            break
        p = p.parent
    for candidate in seen:
        if candidate.exists() or candidate.is_symlink():
            if is_reparse_point(candidate):
                raise InputError(
                    "%s resolves through a link/reparse point at '%s' -- refusing. "
                    "Point %s at a real directory." % (label, candidate, label)
                )


def reject_unencodable(value, label: str) -> str:
    """Refuse caller text that UTF-8 cannot encode. Returns the value.

    Every artifact this tool writes is written as UTF-8, so a string UTF-8
    cannot encode is not a rendering problem -- it is a value that CANNOT be
    published. The reachable case is a lone UTF-16 surrogate: `json.loads`
    accepts a `\\udNNN` escape in any `--proofs` string field and materializes a
    real lone-surrogate `str`, and on POSIX `sys.argv` produces one for any
    undecodable argument byte (surrogateescape). Neither md_untrusted(),
    md_code() nor md_inline() removes it -- they neutralize MARKDOWN, not
    encodability -- so without this the value reaches `write_text` and the
    UnicodeEncodeError escapes as a traceback, taking the documented {0,1,2}
    exit-code contract with it.

    Refusing at the boundary rather than transcoding at the sink is the honest
    choice: this tool RECORDS what the caller supplied, and silently replacing a
    character with U+FFFD would publish something the caller did not write.

    SCOPE, stated exactly: the two CALLER boundaries call this -- every element
    of the invocation argv, and every string in the `--proofs` document. Text
    this tool captures rather than receives cannot carry a surrogate (`run()`
    decodes with `errors="backslashreplace"`, which emits ASCII, and every file
    read is strict UTF-8). Text the FILESYSTEM supplies is not covered: a
    filename can carry a surrogate on either platform, and that case is handled
    only by main()'s UnicodeError clause -- exit 1 with a message, not a
    traceback.
    """
    try:
        str(value).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InputError(
            "%s carries a character UTF-8 cannot encode at position %d (%s). Every "
            "artifact this tool writes is UTF-8, so the value could not be published "
            "as given; supply text this tool can record verbatim."
            % (label, exc.start, exc.reason))
    return value


def reject_placeholder(value: str, label: str) -> str:
    """Refuse an obviously unresolved placeholder value. Returns the value.

    An operator who pastes a runbook line without resolving its variables must be
    refused rather than acted on -- PLACEHOLDER_PATTERNS names each shape and the
    message says which one fired. This grades the literal spelling only; it makes
    no claim that a value which passes is usable.
    """
    for pattern, why in PLACEHOLDER_PATTERNS:
        if pattern.search(value or ""):
            raise InputError(
                "%s %r %s. Resolve it before invoking; this tool refuses "
                "placeholder values rather than acting on them." % (label, value, why)
            )
    return value


def validate_version(version: str) -> str:
    """Refuse a `--version` that is not ONE safe path segment. Returns it.

    The value becomes a directory name under the store, so it is held to
    VERSION_RE (which rejects traversal, separators, drive letters and leading
    punctuation by construction), a length ceiling, and the Windows reserved
    device names that are unusable as a directory name whatever their spelling.
    """
    reject_placeholder(version, "--version")
    if len(version) > VERSION_MAX_LEN:
        raise InputError("--version is longer than %d characters" % VERSION_MAX_LEN)
    if not VERSION_RE.match(version):
        raise InputError(
            "--version %r is not ONE safe path segment. Required: %s -- which by "
            "construction rejects traversal ('.', '..'), path separators and drive "
            "letters." % (version, VERSION_RE.pattern)
        )
    if version.lower() in RESERVED_SEGMENTS:
        raise InputError("--version %r is a reserved Windows device name" % version)
    return version


def reject_absolute(rel: str, label: str) -> str:
    """A recorded path must never be machine-specific. '.' and '..' are allowed."""
    text = str(rel).replace("\\", "/").strip()
    if not text:
        raise InputError("%s is empty" % label)
    if text.startswith("/") or text.startswith("//") or (len(text) > 1 and text[1] == ":"):
        raise InputError("%s %r is absolute; recorded paths are relative" % (label, rel))
    return text


def safe_relative(rel: str) -> str:
    """Normalize a contained relative path; refuse absolute or escaping forms."""
    text = reject_absolute(rel, "relative path")
    parts = [p for p in text.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise InputError("path %r escapes its root" % rel)
    if not parts:
        raise InputError("path %r resolves to nothing" % rel)
    return "/".join(parts)


def rel_posix(path: Path, base: Path) -> str:
    """`path` expressed relative to `base`, POSIX separators. May start '../'."""
    return os.path.relpath(str(path), str(base)).replace("\\", "/")


def iter_files(root: Path):
    """Every regular file under `root`, as sorted POSIX-relative paths."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = Path(dirpath) / name
            out.append(rel_posix(full, root))
    out.sort()
    return out


def walk_strings(obj):
    """Every string value inside a parsed JSON document."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from walk_strings(value)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from walk_strings(item)


def contains_private_path(text) -> bool:
    """True when `text` carries a machine-specific absolute user path.

    THE one predicate: PRIVATE_PATH_RE applied directly, with no exemption and
    no normalization. Every caller in this module goes through here, so "does
    this text leak" has one owner and one answer.

    FAIL-CLOSED, and what that costs. A string of the form `<token>/home/...` or
    `<token>/Users/...` reds, even though this tool's own tokenizer can emit
    exactly that shape for a product whose top-level directory is named `home`
    or `Users`. That is a known false positive, accepted deliberately: the SAME
    bytes are how a `--proofs` field smuggles a real absolute path past a gate
    that exempts the token, so there is no textual rule that admits one and
    refuses the other. See PRIVATE_PATH_RE's "KNOWN FALSE POSITIVE" note for the
    measurement, and runbook section 9 for the operator-facing workaround.

    What this does NOT establish: it grades the ABSOLUTE-USER-PATH shapes in
    PRIVATE_PATH_RE and nothing else. It is not a general sanitizer, and a
    machine-specific string that is not one of those shapes passes it.
    """
    return PRIVATE_PATH_RE.search(str(text)) is not None


#: The locator suffix that marks an artifact this gate could not READ, as
#: opposed to one it read and found a path in. ONE definition: scan_private_paths
#: writes it and _build_and_publish partitions on it, so the two can never drift
#: into describing a fault as a leak.
UNGRADED_MARK = ":<unreadable>"


def scan_private_paths(paths):
    """Return ['<label>:<lineno>'] for every machine-specific absolute path found.

    A JSON document is scanned twice: line by line, and again over its PARSED
    string values. The second pass is not redundant -- JSON escapes a backslash,
    so `C:\\Users\\...` reads as `C:\\\\Users` in the raw bytes and a line scan
    alone would miss exactly the Windows spelling this gate exists to catch.

    FAILS CLOSED ON AN UNREADABLE FILE, AND SAYS SO. This is the last gate before
    a release is retained, and every file it is handed was written moments
    earlier by this same process, so one that cannot be read is a FAULT.
    Returning it as clean would let a real leak inside a transiently locked file
    (an antivirus handle, a disk hiccup) through the one check that exists to
    stop it. It is therefore returned in the same list -- but with the
    UNGRADED_MARK suffix rather than a line number, because "a path leaked" and
    "a file could not be read back" are different faults with different operator
    responses, and the caller reports them as different sentences.

    An UNPARSABLE `.json` is deliberately NOT a hit. Only the second pass is
    lost, the raw line scan still graded the same bytes, and these documents are
    written by `json.dumps` -- so the reachable case is not a corrupt artifact
    but a caller handing this function a file that was never JSON.
    """
    hits = []
    for label, path in paths:
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            hits.append("%s%s" % (label, UNGRADED_MARK))
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if contains_private_path(line):
                hits.append("%s:%d" % (label, lineno))
        if str(path).lower().endswith(".json"):
            try:
                document = json.loads(text)
            except ValueError:
                continue
            for value in walk_strings(document):
                if contains_private_path(value):
                    hits.append("%s:<json-value>" % label)
                    break
    return hits


def describe_scan_findings(findings):
    """One failure message for a public-artifact scan, or None when it passed.

    TWO DIFFERENT FAULTS, SAID AS TWO DIFFERENT SENTENCES. Both are fail-closed
    and both abort the run, but they send an operator to different places: "a
    path leaked" means read the record and fix what produced the value, while "an
    artifact could not be read back" means a lock or an IO fault and the record
    is very likely fine. Naming a lock as a leak points them at the wrong cause,
    and the second is a realistic Windows occurrence right after a multi-hundred
    file copy.
    """
    if not findings:
        return None
    ungraded = [hit for hit in findings if hit.endswith(UNGRADED_MARK)]
    leaks = [hit for hit in findings if not hit.endswith(UNGRADED_MARK)]
    parts = []
    if leaks:
        parts.append("a machine-specific absolute path reached a PUBLIC artifact (%s)"
                     % ", ".join(leaks))
    if ungraded:
        parts.append("a PUBLIC artifact written moments ago could not be read back and "
                     "graded (%s) -- that is a FAULT, not a leak finding, and this gate "
                     "treats an ungraded artifact as failing"
                     % ", ".join(hit[:-len(UNGRADED_MARK)] for hit in ungraded))
    return "; ".join(parts) + "; refusing to retain this build"


# --------------------------------------------------------------------------- #
# Argv/path tokenization -- keeps the PUBLIC record free of machine paths
# --------------------------------------------------------------------------- #

class PathTokenizer:
    """Substitutes a stable token for each machine-specific absolute path.

    The real invocation always uses the real paths; only the RECORD is
    tokenized. Longest path first, so '<work>/checkout/tools' never wins over
    '<work>/checkout'.
    """

    def __init__(self):
        self._entries = []

    def bind(self, token: str, path) -> None:
        if path is None:
            return
        text = str(path)
        if not text:
            return
        self._entries.append((token, os.path.normcase(os.path.abspath(text))))
        self._entries.sort(key=lambda e: len(e[1]), reverse=True)

    def tokenize(self, value: str) -> str:
        raw = str(value)
        normed = os.path.normcase(os.path.abspath(raw)) if _looks_like_path(raw) else None
        if normed is not None:
            for token, bound in self._entries:
                if normed == bound:
                    return token
                if normed.startswith(bound + os.sep):
                    tail = normed[len(bound) + 1:].replace("\\", "/")
                    return "%s/%s" % (token, tail)
        return raw

    def tokenize_argv(self, argv):
        return [self.tokenize(a) for a in argv]


def _looks_like_path(value: str) -> bool:
    """True for the ABSOLUTE spellings PathTokenizer is willing to normalize.

    A cheap pre-filter, not a path validator: `os.path.abspath` on a relative
    argv entry would resolve it against this process's cwd and invent a machine
    path that was never in the argument. So only a drive letter, a leading `/`
    and a UNC `\\\\` are considered; everything else is left exactly as given.
    """
    if len(value) > 1 and value[1] == ":":
        return True
    return value.startswith("/") or value.startswith("\\\\")


# --------------------------------------------------------------------------- #
# Git
# --------------------------------------------------------------------------- #

def git_exe() -> str:
    """The resolved `git` executable. Raises InputError when it is not on PATH.

    A precondition failure, not an execution failure: commit resolution and
    release staging are both git-driven, so a missing git means the request
    cannot be attempted at all.
    """
    found = shutil.which("git")
    if not found:
        raise InputError("git is not on PATH; source resolution and staging require it")
    return found


def git(args, cwd, *, check=True, timeout=TIMEOUT_GIT):
    """Run one git command under TIMEOUT_GIT. Returns the CompletedProcess.

    With `check=True` (the default) a nonzero exit raises ExecutionError naming
    the command, the directory, the code and the first 400 characters of its
    output. With `check=False` the result is returned unjudged and the caller
    reads `returncode` itself. A timeout raises subprocess.TimeoutExpired, which
    main() converts to exit 1 -- this wrapper does not convert it.
    """
    result = run([git_exe(), *args], cwd=cwd, timeout=timeout)
    if check and result.returncode != 0:
        raise ExecutionError(
            "git %s failed in '%s' (exit %d): %s"
            % (" ".join(str(a) for a in args), cwd, result.returncode,
               (result.stderr or result.stdout).strip()[:400])
        )
    return result


def git_out(args, cwd, *, timeout=TIMEOUT_GIT) -> str:
    """git() for a command read for its OUTPUT: the stripped stdout string.

    Always checked -- a caller that wants the text wants it only when the command
    succeeded -- so this raises ExecutionError on a nonzero exit rather than
    returning an empty string that reads like a legitimate answer.
    """
    return git(args, cwd, timeout=timeout).stdout.strip()


def assert_work_tree(root: Path, label: str) -> None:
    result = run([git_exe(), "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                 timeout=TIMEOUT_GIT)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise InputError("%s '%s' is not a git working tree" % (label, root))


def resolve_object(root: Path, rev: str, suffix: str, label: str) -> str:
    result = run([git_exe(), "-C", str(root), "rev-parse", "--verify", "--end-of-options",
                  "%s^{%s}" % (rev, suffix)], timeout=TIMEOUT_GIT)
    if result.returncode != 0:
        raise InputError(
            "cannot resolve %s from --source-commit %r in '%s': %s"
            % (label, rev, root, (result.stderr or result.stdout).strip()[:200])
        )
    oid = result.stdout.strip().lower()
    if not FULL_OID_RE.match(oid):
        raise ExecutionError("git returned a non-full %s object id %r" % (label, oid))
    return oid


def worktree_fingerprint(root: Path) -> str:
    """A digest of HEAD plus porcelain status -- the read-only source guard.

    Taken before and after all work. This tool treats the working source as
    read-only, and this is how it PROVES that rather than asserting it.
    """
    head = run([git_exe(), "-C", str(root), "rev-parse", "HEAD"], timeout=TIMEOUT_GIT)
    status = run([git_exe(), "-C", str(root), "status", "--porcelain"], timeout=TIMEOUT_GIT)
    return sha256_bytes(("%s\n%s" % (head.stdout, status.stdout)).encode("utf-8"))


def make_disposable_checkout(source_root: Path, commit: str, dest: Path) -> None:
    """A CLEAN, DISPOSABLE checkout of the pinned commit.

    Cloned with --shared so a commit that is not reachable from any ref is still
    checkoutable, and with core.autocrlf disabled so the checkout carries the
    index blobs' own bytes. The working source is only ever READ.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = run([git_exe(), "-c", "core.autocrlf=false", "clone", "--quiet",
                  "--no-checkout", "--shared", "--", str(source_root), str(dest)],
                 timeout=TIMEOUT_GIT)
    if result.returncode != 0:
        raise ExecutionError(
            "could not create a disposable checkout of '%s' (exit %d): %s"
            % (source_root, result.returncode, (result.stderr or result.stdout).strip()[:400])
        )
    git(["-c", "core.autocrlf=false", "checkout", "--force", "--detach", commit], cwd=dest)


def verify_checkout_agreement(checkout: Path, commit: str, tree: str) -> None:
    """index == tree == HEAD, and HEAD is the commit that was asked for."""
    head = git_out(["rev-parse", "HEAD"], checkout).lower()
    if head != commit:
        raise ExecutionError(
            "disposable checkout HEAD %s does not match the pinned source commit %s"
            % (head, commit))
    head_tree = git_out(["rev-parse", "HEAD^{tree}"], checkout).lower()
    if head_tree != tree:
        raise ExecutionError(
            "disposable checkout tree %s does not match the resolved source tree %s"
            % (head_tree, tree))
    unmerged = git_out(["ls-files", "-u"], checkout)
    if unmerged:
        raise ExecutionError("disposable checkout index carries unmerged entries")
    porcelain = git_out(["status", "--porcelain"], checkout)
    if porcelain:
        raise ExecutionError(
            "disposable checkout is not clean; index/tree/HEAD disagree:\n%s"
            % porcelain[:800])
    diff = run([git_exe(), "-C", str(checkout), "diff-index", "--quiet", "HEAD", "--"],
               timeout=TIMEOUT_GIT)
    if diff.returncode != 0:
        raise ExecutionError("disposable checkout index disagrees with HEAD")


def tracked_files(checkout: Path):
    raw = git(["ls-files", "-z"], checkout).stdout
    return sorted(p for p in raw.split("\0") if p)


# --------------------------------------------------------------------------- #
# The retained verifier -- reopen a release without this tool
# --------------------------------------------------------------------------- #

VERIFY_ARTIFACTS_SOURCE = '''#!/usr/bin/env python3
"""verify-artifacts.py -- verify a '<sha256>  <relpath>' manifest against a tree.

Retained inside every baseline release so the retained bytes can be reopened and
re-verified with nothing but a Python 3 interpreter.

    python verify-artifacts.py <manifest> <root> [--require-dir PREFIX]...

Exit 0 when every listed path exists and hashes as recorded; exit 1 on any
missing file, hash mismatch, malformed manifest line, unsafe manifest path, or
missing required directory. Blank lines and '#' comment lines are skipped, so it
reads both this release's SHA256SUMS and the release.ps1 CHECKSUMS.txt manifest.
"""
import argparse
import hashlib
import os
import sys


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh.read().splitlines(), 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            digest, sep, rel = line.partition("  ")
            digest = digest.strip().lower()
            rel = rel.strip()
            if not sep or len(digest) != 64 or not rel:
                raise SystemExit("verify-artifacts: malformed manifest line %d" % lineno)
            posix = rel.replace(chr(92), "/")
            unsafe = (posix.startswith("/") or ".." in posix.split("/")
                      or (len(posix) > 1 and posix[1] == ":"))
            if unsafe:
                raise SystemExit("verify-artifacts: unsafe manifest path on line %d: %s"
                                 % (lineno, rel))
            rows.append((digest, posix))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="verify a sha256 manifest against a tree")
    ap.add_argument("manifest")
    ap.add_argument("root")
    ap.add_argument("--require-dir", action="append", default=[],
                    help="a directory prefix that must exist under root and be non-empty")
    args = ap.parse_args(argv)

    rows = parse_manifest(args.manifest)
    if not rows:
        print("verify-artifacts: FAIL manifest lists no files")
        return 1

    problems = []
    for digest, rel in rows:
        target = os.path.join(args.root, *rel.split("/"))
        if not os.path.isfile(target):
            problems.append("MISSING  " + rel)
            continue
        actual = sha256_file(target)
        if actual != digest:
            problems.append("MISMATCH " + rel)

    for prefix in args.require_dir:
        target = os.path.join(args.root, *prefix.split("/"))
        if not os.path.isdir(target):
            problems.append("NO-DIR   " + prefix)
            continue
        if not any(files for _, _, files in os.walk(target)):
            problems.append("EMPTY    " + prefix)

    for line in problems:
        print("verify-artifacts: " + line)
    print("verify-artifacts: %d entr(ies) checked, %d problem(s)" % (len(rows), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
'''


# --------------------------------------------------------------------------- #
# Environment capture
# --------------------------------------------------------------------------- #

_PROBE_SOURCE = (
    "import json, sys\n"
    "out = {'python': sys.version.split()[0]}\n"
    "for mod, label in (('pytest', 'pytest'), ('yaml', 'pyyaml'),\n"
    "                   ('markdown_it', 'markdown-it-py'), ('jsonschema', 'jsonschema')):\n"
    "    try:\n"
    "        out[label] = getattr(__import__(mod), '__version__', 'unknown')\n"
    "    except Exception:\n"
    "        out[label] = 'not installed'\n"
    "print(json.dumps(out))\n"
)


def capture_environment(python_exe: str, powershell_exe) -> dict:
    """Every value a STRING. Unknown is spelled out, never silently omitted."""
    env = {
        "os": platform.platform(),
        "powershell": "not available",
        "git": "not available",
        "python": "unknown",
        "pytest": "unknown",
        "pyyaml": "unknown",
        "markdown-it-py": "unknown",
        "jsonschema": "unknown",
    }
    if powershell_exe:
        result = run([powershell_exe, "-NoProfile", "-NonInteractive", "-Command",
                      "$PSVersionTable.PSVersion.ToString()"], timeout=TIMEOUT_PROBE)
        if result.returncode == 0 and result.stdout.strip():
            env["powershell"] = result.stdout.strip().splitlines()[0]
    git_version = run([git_exe(), "--version"], timeout=TIMEOUT_PROBE)
    if git_version.returncode == 0:
        env["git"] = git_version.stdout.strip()
    probe = run([python_exe, "-c", _PROBE_SOURCE], timeout=TIMEOUT_PROBE)
    if probe.returncode == 0:
        try:
            env.update({k: str(v) for k, v in json.loads(probe.stdout).items()})
        except (ValueError, AttributeError):
            pass
    return env


# --------------------------------------------------------------------------- #
# Proof imports
# --------------------------------------------------------------------------- #

_CHECK_KEYS = ("argv", "exit_code", "cwd", "source_commit", "evidence")
_REVIEW_KEYS = ("source_commit", "requested_model", "resolved_model", "resolution_status",
                "identity_waiver", "conversation_id", "independent", "verdict", "evidence")


def _require_mapping(value, what):
    if not isinstance(value, dict):
        raise InputError("--proofs: %s must be a JSON object" % what)
    return value


def load_proofs(proofs_path: Path) -> dict:
    """Structural validation only. Referential problems are RECORDED, not fatal.

    A malformed proofs FILE is bad input (exit 2). A row whose evidence file is
    missing, or whose source id does not bind to this release's source commit,
    is imported and MARKED -- never silently dropped, and never counted toward
    qualification.
    """
    try:
        raw = proofs_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError("--proofs '%s' cannot be read: %s" % (proofs_path, exc))
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise InputError("--proofs '%s' is not valid JSON: %s" % (proofs_path, exc))
    _require_mapping(data, "the proofs document")
    # The document was decoded as strict UTF-8, but json.loads turns a `\udNNN`
    # escape into a real lone surrogate, which no later sink removes. This is one
    # of the two caller boundaries reject_unencodable() names.
    for index, value in enumerate(walk_strings(data)):
        reject_unencodable(value, "--proofs '%s' (string #%d)" % (proofs_path, index))
    if contains_private_path(raw) or any(
            contains_private_path(value) for value in walk_strings(data)):
        raise InputError(
            "--proofs '%s' carries an absolute user path. release.json is a PUBLIC "
            "artifact, so proof rows must use relative evidence paths -- and note "
            "that a documented argv token is NOT an exemption: a `<token>/home/...` "
            "or `<token>/Users/...` spelling is refused too, because a real leak "
            "written that way is the same bytes. Runbook section 9 has the "
            "workaround." % proofs_path)

    unknown = set(data) - {"checks", "reviews", "environment"}
    if unknown:
        raise InputError(
            "--proofs carries unknown top-level key(s) %s; the document uses the same "
            "checks/reviews/environment shapes as release.json"
            % ", ".join(sorted(unknown)))

    checks = data.get("checks", [])
    reviews = data.get("reviews", [])
    environment = data.get("environment", {})
    if not isinstance(checks, list) or not isinstance(reviews, list):
        raise InputError("--proofs: 'checks' and 'reviews' must be arrays")
    _require_mapping(environment, "'environment'")
    for key, value in environment.items():
        if not isinstance(value, str):
            raise InputError("--proofs: environment[%r] must be a string" % key)

    for index, row in enumerate(checks):
        _require_mapping(row, "checks[%d]" % index)
        missing = [k for k in _CHECK_KEYS if k not in row]
        if missing:
            raise InputError("--proofs: checks[%d] is missing %s"
                             % (index, ", ".join(missing)))
        if not isinstance(row["argv"], list) or not all(isinstance(a, str) for a in row["argv"]):
            raise InputError("--proofs: checks[%d].argv must be an array of strings" % index)
        if row["exit_code"] is not None and not isinstance(row["exit_code"], int):
            raise InputError("--proofs: checks[%d].exit_code must be an integer or null" % index)
        for key in ("cwd", "source_commit", "evidence"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise InputError("--proofs: checks[%d].%s must be a non-empty string"
                                 % (index, key))
        reject_absolute(row["cwd"], "checks[%d].cwd" % index)
        safe_relative(row["evidence"])

    for index, row in enumerate(reviews):
        _require_mapping(row, "reviews[%d]" % index)
        missing = [k for k in _REVIEW_KEYS if k not in row]
        if missing:
            raise InputError("--proofs: reviews[%d] is missing %s"
                             % (index, ", ".join(missing)))
        for key in ("requested_model", "resolved_model", "identity_waiver"):
            if row[key] is not None and not isinstance(row[key], str):
                raise InputError("--proofs: reviews[%d].%s must be a string or null"
                                 % (index, key))
        for key in ("source_commit", "resolution_status", "conversation_id", "verdict", "evidence"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise InputError("--proofs: reviews[%d].%s must be a non-empty string"
                                 % (index, key))
        if not isinstance(row["independent"], bool):
            raise InputError("--proofs: reviews[%d].independent must be a boolean" % index)
        if "cross_family" in row and not isinstance(row["cross_family"], bool):
            raise InputError("--proofs: reviews[%d].cross_family must be a boolean" % index)
        safe_relative(row["evidence"])

    return {"checks": checks, "reviews": reviews, "environment": environment}


def _import_evidence(proofs_dir: Path, rel: str, dest_dir: Path, index: int):
    """Resolve a proof's evidence file and copy it in. Returns (relpath, status)."""
    try:
        normalized = safe_relative(rel)
    except InputError:
        return None, "unsafe-evidence-path"
    source = (proofs_dir / normalized).resolve()
    try:
        source.relative_to(proofs_dir.resolve())
    except ValueError:
        return None, "evidence-escapes-proofs-directory"
    if not source.is_file():
        return None, "missing-evidence"
    dest_dir.mkdir(parents=True, exist_ok=True)
    leaf = "%02d-%s" % (index, source.name)
    shutil.copy2(source, dest_dir / leaf)
    return "%s/%s" % (dest_dir.name, leaf), "imported"


def import_proofs(proofs, proofs_path: Path, release_dir: Path, source_commit: str,
                  environment: dict, attested_by=None):
    """Import proof rows, binding each to this release's source and environment.

    `attested_by` is the named party supplied by the `--attest-reviews` CLI act.
    It is stamped onto every imported REVIEW row and is the only positive signal
    that can qualify one -- see the module docstring's governing invariant. It is
    never read from the proofs document, so a reused historical proofs file can
    never carry an attestation forward on its own.
    """
    gaps = []
    proofs_dir = proofs_path.parent
    checks = []
    for index, row in enumerate(proofs["checks"]):
        evidence, status = _import_evidence(proofs_dir, row["evidence"],
                                            release_dir / "proofs", index)
        if status != "imported":
            gaps.append("imported check %d (%s): evidence %r could not be resolved (%s); "
                        "the row is retained and marked, and it does not count toward "
                        "qualification" % (index, " ".join(row["argv"])[:60],
                                           row["evidence"], status))
        if row["source_commit"].lower() != source_commit:
            status = "source-mismatch" if status == "imported" else status
            gaps.append("imported check %d binds source_commit %s, not this release's %s; "
                        "historical proof is never relabelled as current-source proof"
                        % (index, row["source_commit"][:12], source_commit[:12]))
        checks.append({
            "argv": list(row["argv"]),
            "exit_code": row["exit_code"],
            "cwd": row["cwd"],
            "source_commit": row["source_commit"],
            "evidence": evidence if evidence else row["evidence"],
            "name": row.get("name", "imported-check-%d" % index),
            "execution": "imported",
            "import_status": status,
        })

    reviews = []
    for index, row in enumerate(proofs["reviews"]):
        evidence, status = _import_evidence(proofs_dir, row["evidence"],
                                            release_dir / "reviews", index)
        if status != "imported":
            gaps.append("imported review %d: evidence %r could not be resolved (%s); the "
                        "row is retained and marked, and it does not count toward "
                        "qualification" % (index, row["evidence"], status))
        if row["source_commit"].lower() != source_commit:
            status = "source-mismatch" if status == "imported" else status
            gaps.append("imported review %d binds source_commit %s, not this release's %s; "
                        "historical proof is never relabelled as current-source proof"
                        % (index, row["source_commit"][:12], source_commit[:12]))
        consistency, why = check_evidence_consistency(
            row, (release_dir / evidence) if evidence else None)
        if consistency != "consistent":
            gaps.append("imported review %d FAILED the evidence-consistency tripwire: "
                        "%s. The row is retained and marked; a claim its own cited "
                        "evidence denies or omits never counts toward qualification"
                        % (index, why))
        if not str(attested_by or "").strip():
            gaps.append("imported review %d carries no named attestation. This tool "
                        "cannot verify that a cross-family review happened -- the row "
                        "and its evidence document are both caller-authored -- so a "
                        "review qualifies only through the separate act "
                        "--attest-reviews \"<accountable party>\". The row and its "
                        "evidence are retained regardless" % index)
        reviews.append({
            "source_commit": row["source_commit"],
            "requested_model": row["requested_model"],
            "resolved_model": row["resolved_model"],
            "resolution_status": row["resolution_status"],
            "identity_waiver": row["identity_waiver"],
            "conversation_id": row["conversation_id"],
            "independent": row["independent"],
            "verdict": row["verdict"],
            "evidence": evidence if evidence else row["evidence"],
            "cross_family": row.get("cross_family"),
            "execution": "imported",
            "import_status": status,
            "evidence_consistency": consistency,
            "attested_by": (str(attested_by).strip()
                            if str(attested_by or "").strip() else None),
        })

    for key, value in sorted(proofs["environment"].items()):
        measured = environment.get(key)
        if measured is None:
            gaps.append("imported proof environment declares %r, which this run did not "
                        "measure; the record keeps the MEASURED environment only" % key)
        elif measured != value:
            gaps.append("imported proof environment %r is %r but this run measured %r; an "
                        "import binds its own environment and never implies native "
                        "execution here" % (key, value, measured))
    return checks, reviews, gaps


def _clauses(text_lower: str):
    """The already-lowercased document, split into clauses for the tripwire."""
    return [c for c in _CLAUSE_SPLIT_RE.split(text_lower) if c.strip()]


def _needle_pattern(needle) -> str:
    """Boundary-anchored pattern for a claim token, or '' when there is none."""
    text = str(needle).strip().lower()
    if not text:
        return ""
    pattern = re.escape(text)
    if text[0].isalnum():
        pattern = r"(?<![0-9a-z])" + pattern
    if text[-1].isalnum():
        pattern = pattern + r"(?![0-9a-z])"
    return pattern


def _states(text_lower: str, needle) -> bool:
    """True when an already-lowercased document states `needle` as its own token.

    Boundary-anchored on purpose: plain containment would let 'passed' or
    'bypassed' satisfy a claimed verdict of PASS, and a document discussing
    'review-00012' satisfy a row claiming conversation id 'review-0001'.

    DELIBERATELY NEGATION-BLIND, and left that way. It answers "does this token
    appear", which is all a presence test can answer; the sentence around it is
    graded separately by `_is_negated`. Neither one verifies anything -- see the
    module docstring's governing invariant. Making this function cleverer was the
    move that oscillated twice, and it is not the fix.
    """
    pattern = _needle_pattern(needle)
    return bool(pattern) and re.search(pattern, text_lower) is not None


def _is_negated(text_lower: str, needle) -> bool:
    """True when the clause carrying `needle` negates it, within a small window.

    NEGATIVE-ONLY BY DESIGN. A hit is a real falsification and is fail-closed; a
    MISS is safe, because consistency alone never qualifies a review (the
    `--attest-reviews` act does). That asymmetry is the whole reason this is
    allowed to be incomplete, and the reason it must not grow toward
    completeness: an unbounded chase after quotation, sarcasm and rebuttal is
    exactly the whack-a-mole the attestation design replaced.

    Graded inside the clause carrying the claim, so a negation elsewhere in the
    document ("no blocking defects were found. Verdict: PASS") does not trip it.
    """
    pattern = _needle_pattern(needle)
    if not pattern:
        return False
    for clause in _clauses(text_lower):
        if re.search(pattern, clause) is None:
            continue
        words = re.findall(r"[a-z0-9]+", clause)
        # Where the claim's own words start, so the window looks BEFORE them.
        claim_words = re.findall(r"[a-z0-9]+", str(needle).strip().lower())
        if not claim_words:
            continue
        for index, word in enumerate(words):
            if words[index:index + len(claim_words)] != claim_words:
                continue
            window = words[max(0, index - NEGATION_WINDOW):index]
            if any(w in NEGATION_MARKERS for w in window):
                return True
    return False


def review_claim_needles(row: dict):
    """[(label, needle)] -- the claims a review's evidence document should carry.

    Each needle is a substantive claim the --proofs row makes about itself. A
    bare boolean has no textual footprint, so `independent` is graded as the word
    and `cross_family` as BOTH host families: the charter's release hosts are
    Claude Code and Codex, so cross-family means Claude <-> Codex and a document
    naming only one of them has not evidenced a cross-family review.
    """
    needles = [
        ("the source commit it reviewed", row["source_commit"]),
        ("its conversation id", row["conversation_id"]),
        ("its verdict", row["verdict"]),
    ]
    if row.get("resolved_model"):
        needles.append(("the resolved model identity", row["resolved_model"]))
    elif row.get("identity_waiver"):
        needles.append(("the named identity waiver", row["identity_waiver"]))
    if row.get("independent"):
        needles.append(("its independence", "independent"))
    if row.get("cross_family") is True:
        for family in CROSS_FAMILY_TOKENS:
            needles.append(("the %s host family" % family, family))
    return needles


def check_evidence_consistency(row: dict, evidence_path):
    """(status, reason) -- the NEGATIVE-ONLY tripwire over a row and its evidence.

    Read the module docstring first: both the row and the document are authored by
    the same caller, so comparing them cannot corroborate either. What the
    comparison CAN do is falsify -- catch a row that drifted away from, or is
    flatly contradicted by, the document it cites. So every outcome here except
    "consistent" BLOCKS qualification, and "consistent" upgrades nothing: it
    means only that this tripwire did not fire. `review_qualifies` requires the
    separate `--attest-reviews` act on top of it.

    Order matters: an unreadable or absent document is graded before content, and
    a CONTRADICTED claim is reported ahead of a merely UNSTATED one, because a
    document that denies a claim is a louder finding than one that omits it.
    """
    if not evidence_path or not Path(evidence_path).is_file():
        return "no-evidence", "no evidence document was imported for this review"
    try:
        text = Path(evidence_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ("evidence-unreadable",
                "its evidence document could not be read as UTF-8 text (%s)"
                % exc.__class__.__name__)
    lowered = text.lower()
    needles = review_claim_needles(row)
    denied = [label for label, needle in needles if _is_negated(lowered, needle)]
    if denied:
        return ("contradicted",
                "its evidence document DENIES %s" % ", ".join(denied))
    missing = [label for label, needle in needles if not _states(lowered, needle)]
    if missing:
        return ("unstated",
                "its evidence document does not state %s" % ", ".join(missing))
    return ("consistent",
            "the cited evidence document neither omits nor denies any attested claim "
            "(a tripwire result only -- it establishes nothing on its own)")


def review_qualifies(row: dict, source_commit: str):
    """(bool, reason). The charter invariant, spelled out and never softened.

    The positive signal is `attested_by` -- a named party supplied through the
    `--attest-reviews` CLI act, deliberately separate from the caller-authored
    proofs row. `evidence_consistency` appears here only in its negative
    direction: anything other than "consistent" blocks, and "consistent" on its
    own qualifies nothing.
    """
    if row.get("import_status") not in (None, "imported"):
        return False, "evidence could not be resolved (%s)" % row.get("import_status")
    if row.get("evidence_consistency") != "consistent":
        return False, ("is contradicted by, or not stated by, the evidence it cites "
                       "(%s); a falsified claim is recorded, never counted"
                       % (row.get("evidence_consistency") or "not checked"))
    if not str(row.get("attested_by") or "").strip():
        # Plain quotes, no backticks: this string is a qualification REASON, and
        # that channel is plain text by contract (see md_untrusted).
        return False, ("carries no named attestation. This tool cannot verify that a "
                       "cross-family review happened -- the row and its evidence are "
                       "both caller-authored -- so qualification requires the separate "
                       "act --attest-reviews \"<accountable party>\", recorded as "
                       "attested_by")
    if row["source_commit"].lower() != source_commit:
        return False, "binds a different source commit"
    if not row["independent"]:
        return False, "is not marked independent"
    if str(row["verdict"]).strip().upper() != "PASS":
        return False, "verdict is %r, not PASS" % row["verdict"]
    # `is not True`, NOT `== False`: cross_family is OPTIONAL in the proofs schema,
    # so an OMITTED key arrives here as None and must refuse exactly as an explicit
    # false does. Making no cross-family claim is not a weaker form of making one,
    # and this is the charter's central invariant -- it fails closed on silence.
    if row.get("cross_family") is not True:
        return False, ("does not explicitly claim cross_family: true, so this tool cannot "
                       "assert the charter's cross-family invariant on its behalf")
    if not str(row["resolution_status"]).strip():
        return False, "carries no model resolution_status"
    if not (row["resolved_model"] or row["identity_waiver"]):
        return False, "records neither a resolved_model nor a named identity_waiver"
    if not str(row["conversation_id"]).strip():
        return False, "carries no conversation_id"
    return True, "qualifying"


# --------------------------------------------------------------------------- #
# Payload construction
# --------------------------------------------------------------------------- #

def build_source_zip(checkout: Path, zip_path: Path):
    """Deterministic archive of the pinned commit's git-tracked files."""
    names = tracked_files(checkout)
    if not names:
        raise ExecutionError("the pinned commit has no tracked files -- nothing to archive")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, (checkout / name).read_bytes())
    return names


def zip_content_map(zip_path: Path) -> dict:
    """{member: sha256}. Refuses an unsafe member name (zip-slip guard)."""
    out = {}
    with zipfile.ZipFile(zip_path) as zf:
        for name in sorted(zf.namelist()):
            if name.endswith("/"):
                continue
            safe_relative(name)
            out[name.replace("\\", "/")] = sha256_bytes(zf.read(name))
    return out


def checkout_content_map(checkout: Path) -> dict:
    return {name: sha256_file(checkout / name) for name in tracked_files(checkout)}


def write_evidence(path: Path, name: str, argv, cwd_label: str, result, started: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "# baseline-release check evidence",
        "# gate      : %s" % name,
        "# argv      : %s" % json.dumps(argv),
        "# cwd       : %s" % cwd_label,
        "# started   : %s" % started,
        "# finished  : %s" % utcnow(),
        "# exit_code : %s" % result.returncode,
        "",
        "--- stdout ---",
        result.stdout or "",
        "--- stderr ---",
        result.stderr or "",
    ]
    path.write_text("\n".join(body), encoding="utf-8", newline="\n")


def run_gate(name, argv, cwd: Path, checkout: Path, release_dir: Path,
             tokenizer: PathTokenizer, timeout, cwd_label=None):
    """Run one gate for real, retain its evidence, return its record row.

    `cwd_label` overrides the recorded working directory for a gate that does not
    run inside the disposable checkout -- a gate verifying the RETAINED bytes runs
    in the release directory, and `<release-dir>` is the honest record of that.
    """
    started = utcnow()
    began = time.time()
    try:
        result = run(argv, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ExecutionError("gate %r exceeded its %ds ceiling" % (name, timeout))
    except OSError as exc:
        raise ExecutionError("gate %r could not be launched: %s" % (name, exc))
    evidence_rel = "checks/%s.txt" % name
    token_argv = tokenizer.tokenize_argv(argv)
    if cwd_label is None:
        cwd_label = rel_posix(cwd, checkout)
    write_evidence(release_dir / "checks" / ("%s.txt" % name), name, token_argv,
                   cwd_label, result, started)
    return {
        "argv": token_argv,
        "exit_code": result.returncode,
        "cwd": cwd_label,
        "source_commit": None,          # filled by the caller; one source of truth
        "evidence": evidence_rel,
        "name": name,
        "execution": "native",
        "started_at": started,
        "duration_seconds": round(time.time() - began, 3),
    }


# --------------------------------------------------------------------------- #
# Record, notes, packet
# --------------------------------------------------------------------------- #

def find_predecessor(store: Path, product: str, version: str):
    """The most recent OTHER retained release of the same product, or None."""
    product_dir = store / product
    if not product_dir.is_dir():
        return None
    candidates = []
    for entry in sorted(product_dir.iterdir()):
        if not entry.is_dir() or entry.name == version or entry.name.startswith(".staging-"):
            continue
        record = entry / "release.json"
        if not record.is_file():
            continue
        try:
            data = json.loads(record.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        candidates.append((str(data.get("created_at", "")), entry.name))
    if not candidates:
        return None
    candidates.sort()
    return "%s/%s" % (product, candidates[-1][1])


def hash_release_tree(release_dir: Path, exclude):
    excluded = set(exclude)
    return [
        {"path": rel, "sha256": sha256_file(release_dir / rel)}
        for rel in iter_files(release_dir) if rel not in excluded
    ]


def write_sha256sums(release_dir: Path, rows):
    ordered = sorted(rows, key=lambda row: row["path"])
    body = "".join("%s  %s\n" % (row["sha256"], row["path"]) for row in ordered)
    (release_dir / "SHA256SUMS").write_text(body, encoding="utf-8", newline="\n")


def build_public_packet(release_dir: Path, record: dict, product_key: str, gaps):
    include = list(PUBLIC_INCLUDE_COMMON)
    if product_key == "toolkit":
        include += list(PUBLIC_INCLUDE_TOOLKIT)
    packet = {
        "schema_version": SCHEMA_VERSION,
        "release_id": record["release_id"],
        "product": record["product"],
        "version": record["version"],
        "source_commit": record["source_commit"],
        "qualification": record["qualification"],
        "created_at": record["created_at"],
        "publication_status": "NOT_PUBLISHED",
        "publication_note": (
            "This packet describes what MAY be published to the product's existing "
            "remote. Tagging and upload are a separate, later operator step. This "
            "tool creates no tag, uploads nothing, and installs nothing."),
        "hash_manifest": "SHA256SUMS",
        "include": sorted(include),
        "exclude": [{"path": path, "reason": reason} for path, reason in PUBLIC_EXCLUDE],
        "evidence_locators_are_public": (
            "release.json publishes the release-relative LOCATOR of every check and "
            "review evidence file. The evidence BYTES stay local, because captured run "
            "output carries machine-specific absolute paths."),
        "sanitization": {
            "rule": "no machine-specific absolute user path may appear in a published text artifact",
            "scanned": list(PUBLIC_SCANNED_ARTIFACTS),
            "not_scanned": [
                "source.zip member CONTENTS -- gated upstream by the source repository's "
                "own committed-path gate (tests/package-integrity/test_manifest_contract.py)",
                "dist/ artifact bodies -- generated from those same gated sources",
            ],
        },
        "known_gaps": list(gaps),
    }
    (release_dir / "public").mkdir(parents=True, exist_ok=True)
    (release_dir / "public" / "packet.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return packet


def render_release_notes(record: dict, product_key: str) -> str:
    lines = []
    add = lines.append
    add("# %s %s" % (record["product"], record["version"]))
    add("")
    add("Release ID `%s`. Prepared by `tools/baseline_release.py`; **not published** --"
        % record["release_id"])
    add("no tag was created, nothing was uploaded, and no installation was changed.")
    add("")
    add("## Identity")
    add("")
    add("| Field | Value |")
    add("|---|---|")
    add("| Product | `%s` |" % record["product"])
    add("| Version | `%s` |" % record["version"])
    add("| Source commit | `%s` |" % record["source_commit"])
    add("| Source tree | `%s` |" % record["source_tree"])
    add("| Builder commit | `%s` |" % record["builder_commit"])
    add("| Created (UTC) | `%s` |" % record["created_at"])
    add("| Predecessor | %s |"
        % ("`%s`" % record["predecessor"] if record["predecessor"] else "none"))
    add("| Qualification | **%s** |" % record["qualification"])
    add("| Packaged profiles | %s |"
        % (", ".join("`%s`" % p for p in record["providers"]) if record["providers"]
           else "none -- source-only archive"))
    add("")
    add("The builder commit identifies the packaging implementation. It is recorded")
    add("separately from the source commit and the two are never conflated.")
    add("")
    add("## What QUALIFICATION means here")
    add("")
    add("* `QUALIFIED` -- every required gate for this product ran against THIS source")
    add("  and passed, AND a real representative cross-family review is attached with")
    add("  model-resolution evidence and a NAMED accountable party. The gates were")
    add("  machine-checked here; the review was not. This tool cannot verify that a")
    add("  cross-family review happened, so the review's truth rests on the name in")
    add("  the `Attested by` column below and nothing else.")
    add("* `INCOMPLETE` -- a required gate or proof is missing. The source archive is")
    add("  still retained and verifiable; no qualification claim is made.")
    add("* `BLOCKED` -- a gate ran and FAILED. The source archive is still retained.")
    add("")
    add("No broad workflow claim follows from these checks. Deterministic source checks")
    add("and native host acceptance are separate evidence classes, and this tool")
    add("observes only the former.")
    if record["qualification_reasons"]:
        add("")
        add("Reasons this release is `%s`:" % record["qualification"])
        add("")
        # md_untrusted, NOT md_inline: reasons and gaps are the one MIXED-TRUST
        # channel -- caller `--proofs` text is fused into authored prose at the
        # producer, so provenance is gone by the time it arrives here. See
        # md_untrusted() for the channel's contract.
        for reason in record["qualification_reasons"]:
            add("* %s" % md_untrusted(reason))
    add("")
    add("## Gates recorded")
    add("")
    add("| Gate | Execution | Exit | Evidence (local) |")
    add("|---|---|---|---|")
    for row in record["checks"]:
        add("| %s | %s | %s | %s |"
            % (md_code(row.get("name", "check")), md_inline(row.get("execution", "unknown")),
               "n/a" if row["exit_code"] is None else row["exit_code"],
               md_code(row["evidence"])))
    if not record["checks"]:
        add("| none | - | - | - |")
    add("")
    # Every caller-controlled cell is rendered in a CODE SPAN, not as plain cell
    # text: a code span's content is escaped by any CommonMark renderer, and
    # md_code() swaps the backtick so the span cannot be broken open. `verdict`
    # and `resolution_status` are free-form `--proofs` strings, so plain-text
    # cells let them carry live Markdown or raw HTML into a PUBLIC document.
    add("| Review | Independent | Verdict | Resolution | Evidence tripwire "
        "| Attested by | Evidence (local) |")
    add("|---|---|---|---|---|---|---|")
    for row in record["reviews"]:
        add("| %s | %s | %s | %s | %s | %s | %s |"
            % (md_code(row["conversation_id"]), md_inline(row["independent"]),
               md_code(row["verdict"]), md_code(row["resolution_status"]),
               md_code(row.get("evidence_consistency") or "not checked"),
               md_code(row.get("attested_by") or "NOBODY -- not attested"),
               md_code(row["evidence"])))
    if not record["reviews"]:
        add("| none attached | - | - | - | - | - | - |")
    add("")
    add("`Attested by` names the party accountable for the review claim. This tool")
    add("does not run or verify a cross-family review -- the proofs row and the")
    add("evidence document it cites are both written by the caller -- so a review")
    add("counts toward `QUALIFIED` only when that separate named act is recorded.")
    add("`Evidence tripwire` is a NEGATIVE check only: any value other than")
    add("`consistent` blocks qualification, and `consistent` establishes nothing on")
    add("its own.")
    add("")
    add("Evidence bytes stay local: captured run output carries machine-specific")
    add("absolute paths, so only the LOCATORS above are published.")
    add("")
    add("## External dependencies")
    add("")
    for dependency in record["dependencies"]:
        add("* %s" % md_inline(dependency))
    add("")
    add("No secret or credential is an input to this tool, and none is recorded.")
    add("Dependency names and authentication PREREQUISITES are all that is published.")
    add("")
    add("## Known gaps")
    add("")
    # The same MIXED-TRUST channel as qualification_reasons above -- and it also
    # carries every reason verbatim, because a non-QUALIFIED run extends gaps
    # with them.
    for gap in record["known_gaps"]:
        add("* %s" % md_untrusted(gap))
    add("")
    add("## Verify the retained bytes")
    add("")
    add("`verify-artifacts.py` ships beside this file and is part of the publishable")
    add("set, so a recipient of the published subset can run it. From the release")
    add("directory, with any Python 3 interpreter:")
    add("")
    add("```")
    add("python verify-artifacts.py SHA256SUMS .")
    add("```")
    if product_key == "toolkit":
        add("")
        add("`CHECKSUMS.txt` is a SEPARATE manifest: the normalized payload checksums")
        add("`tools/release.ps1` produced over `dist/`. It is the same manifest the")
        add("`artifact-verification` gate ran against these retained bytes. Verify it")
        add("the same way:")
        add("")
        add("```")
        add("python verify-artifacts.py CHECKSUMS.txt . --require-dir dist/claude")
        add("```")
    add("")
    add("`source.zip` container metadata is not part of the identity; its extracted")
    add("member contents are. Re-running the original command against this same")
    add("release ID re-verifies both, and refuses rather than overwrites.")
    add("")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Verify an already-retained release (a repeated request)
# --------------------------------------------------------------------------- #

def verify_existing(release_dir: Path, product: str, version: str, source_commit: str,
                    source_tree: str, checkout: Path):
    """Either VERIFIED (exit 0) or a refusal. Never overwrites, never rebuilds."""
    record_path = release_dir / "release.json"
    if not record_path.is_file():
        raise InputError(
            "'%s' already exists but carries no release.json. A retained release is "
            "never overwritten; move it aside or allocate a different version."
            % release_dir)
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ExecutionError("retained release.json at '%s' is unreadable: %s"
                             % (record_path, exc))

    for field, expected in (("product", product), ("version", version),
                            ("source_commit", source_commit), ("source_tree", source_tree)):
        actual = record.get(field)
        if str(actual).lower() != str(expected).lower():
            raise InputError(
                "COLLISION: release ID '%s/%s' is already retained with %s=%s, but this "
                "request has %s=%s. A release ID is allocated once; nothing is "
                "overwritten. Allocate a new version."
                % (product, version, field, actual, field, expected))

    problems = []
    for entry in record.get("artifacts", []):
        rel = entry.get("path", "")
        target = release_dir / rel
        if not target.is_file():
            problems.append("MISSING %s" % rel)
            continue
        if sha256_file(target) != entry.get("sha256"):
            problems.append("MISMATCH %s" % rel)
    sums = release_dir / "SHA256SUMS"
    if not sums.is_file():
        problems.append("MISSING SHA256SUMS")
    else:
        for line in sums.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, _, rel = line.partition("  ")
            target = release_dir / rel.strip()
            if not target.is_file():
                problems.append("MISSING %s (SHA256SUMS)" % rel.strip())
            elif sha256_file(target) != digest.strip():
                problems.append("MISMATCH %s (SHA256SUMS)" % rel.strip())
    if problems:
        raise ExecutionError(
            "retained bytes at '%s' do not verify:\n  %s"
            % (release_dir, "\n  ".join(problems[:20])))

    archived = zip_content_map(release_dir / "source.zip")
    fresh = checkout_content_map(checkout)
    if archived != fresh:
        only_archived = sorted(set(archived) - set(fresh))[:5]
        only_fresh = sorted(set(fresh) - set(archived))[:5]
        changed = sorted(k for k in set(archived) & set(fresh) if archived[k] != fresh[k])[:5]
        raise ExecutionError(
            "source.zip EXTRACTED CONTENTS do not match a fresh checkout of %s "
            "(only-in-archive %s, only-in-checkout %s, differing %s). ZIP container "
            "metadata may vary; member contents may not."
            % (source_commit[:12], only_archived, only_fresh, changed))
    return record


# --------------------------------------------------------------------------- #
# The build
# --------------------------------------------------------------------------- #

def dependency_lines(environment: dict, product_key: str):
    lines = [
        "Python %s -- supplied by the caller; this repository pins no interpreter and "
        "commits no lockfile" % environment["python"],
        "pytest %s -- the only automated gate this repository has" % environment["pytest"],
        "PyYAML %s -- test-only; the frontmatter and release YAML gate needs a real "
        "strict parser" % environment["pyyaml"],
        "markdown-it-py %s -- test-only; the catalog-lifecycle contract gate needs a "
        "real CommonMark parser" % environment["markdown-it-py"],
        "jsonschema %s -- call-time only, for the declarative record contract"
        % environment["jsonschema"],
        "%s -- release staging is `git ls-files` driven and fails outside a working tree"
        % environment["git"],
    ]
    if product_key == "toolkit":
        lines += [
            "Windows PowerShell %s -- the 5.1 floor every .ps1 build/install/release tool "
            "targets; there is no POSIX path" % environment["powershell"],
            "`gh` CLI, authenticated -- for issue and PR work (not invoked by this tool)",
            "GitHub Copilot CLI signed in via `gh auth login` -- the prerequisite for any "
            "GPT-side host acceptance. Copilot subscription auth is the transport; no "
            "OPENAI_API_KEY is used or needed.",
        ]
    else:
        lines.append(
            "The lab supplies its own virtual environment and AGENTS.md; this tool pins "
            "neither and imports neither")
    return lines


def baseline_gaps(product_key: str):
    gaps = [
        "No native host acceptance was observed by this tool. A green deterministic "
        "source check is a different evidence class from an observed Claude Code or "
        "Codex CLI session, and neither implies the other.",
        "No broad workflow claim follows from the recorded gates: they cover the "
        "repository's own checks, not every skill, model and host combination.",
        "There is no lint command and no typecheck command in this repository, by "
        "design; pytest is the only automated gate, so no static-analysis evidence "
        "exists to record.",
        "Nothing is published: no tag was created, nothing was uploaded, and no "
        "consumer installation was read or changed.",
        "source.zip member CONTENTS are not re-scanned for machine-specific paths here; "
        "they are gated upstream by the source repository's own committed-path gate.",
    ]
    if product_key == "lab":
        gaps.append(
            "The lab archive is EXPERIMENTAL. Current native acceptance is missing, and "
            "an earlier prepared-task proof remains historical evidence bound to its own "
            "source; it is never relabelled as current-source proof.")
    return gaps


#: The artifact whose presence marks a staged build as a COMPLETE payload. It is
#: written second-to-last (only SHA256SUMS follows), after the notes, the
#: receipt, the packet and every evidence file, so a stage that has it has
#: everything before it too.
STAGE_COMPLETION_MARKER = "release.json"


def stage_bucket(staging: Path):
    """(store subdirectory, kind) that `staging`'s CONTENTS belong in.

    The ONE place the `.attempts/` vs `.aborted/` question is answered, so the
    split describes what a directory CONTAINS rather than which error routed the
    run there:

      * `.attempts/` -- a COMPLETE payload: record, notes, receipt, SHA256SUMS
        and every evidence file;
      * `.aborted/`  -- a PARTIAL build, which may have no release.json at all.

    Read off the disk, not inferred from the exception in flight: an error raised
    AFTER the payload was finished (a failed rename, a collision, an unwritable
    store) leaves a complete payload behind, and filing that under `.aborted/`
    would misdescribe it to the operator who has to read it.
    """
    if (staging / STAGE_COMPLETION_MARKER).is_file():
        return ".attempts", "attempt"
    return ".aborted", "aborted"


def retain_failed_stage(store: Path, operation_id: str, staging: Path):
    """Move a stage this run could not publish into the directory it belongs in.

    Returns `(path, kind)` with `kind` from stage_bucket(). Raises ExecutionError
    when the move itself fails -- use retain_failed_stage_quietly() on an
    already-failing path, where a second error must not replace the first.
    """
    bucket, kind = stage_bucket(staging)
    target = store / bucket / operation_id
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        os.rename(staging, target)
    except OSError as exc:
        raise ExecutionError("could not retain this run's build at '%s': %s"
                             % (target, exc))
    return target, kind


def retain_failed_stage_quietly(store: Path, operation_id: str, staging: Path):
    """retain_failed_stage() for the way OUT of a failure. Never raises.

    Returns `(path, kind)`: the moved directory when the move worked, otherwise
    the staging directory itself -- its own path is still the honest answer, and
    a second failure here must not replace the first one's message. `kind` still
    describes the CONTENTS either way, so the caller can say truthfully what is
    at that path. `(None, None)` when there is nothing left to retain.
    """
    if not staging.is_dir():
        return None, None
    _, kind = stage_bucket(staging)
    try:
        return retain_failed_stage(store, operation_id, staging)
    except ExecutionError:
        return staging, kind


def perform_release(args, ctx) -> int:
    """Build, qualify, retain. Returns the process exit code.

    Owns the staging directory's LIFETIME. Anything that escapes the build is
    retained and PRINTED rather than left behind as an unreferenced scratch
    directory that nothing names -- filed by what the stage CONTAINS
    (stage_bucket), so a failure that strikes after the payload was finished
    still lands in `.attempts/`, not in `.aborted/`.
    """
    store = ctx["store"]
    product = ctx["product"]

    staging = store / product / (".staging-%s" % ctx["operation_id"])
    # The guard in prepare() covers --store and its ancestors, but the real output
    # ancestor is <store>/<product>, which mkdir(parents=True) traverses WITHOUT
    # complaint when it already exists as a junction -- silently redirecting every
    # release of that product. Section 6.1 says "reject linked/reparse-point output
    # ancestors", so grade the actual output ancestor, not just the argument.
    assert_no_linked_ancestor(store / product, "the output directory <store>/%s" % product)
    staging.mkdir(parents=True, exist_ok=False)
    try:
        return _build_and_publish(args, ctx, staging)
    except BaseException:
        kept, kind = retain_failed_stage_quietly(store, ctx["operation_id"], staging)
        if kept is not None:
            print("baseline-release: the run failed before it could publish. What it "
                  "built is kept at '%s' and nothing is deleted automatically. %s"
                  % (kept,
                     "That directory holds a COMPLETE payload -- record, notes, receipt "
                     "and every evidence file -- so it is an ATTEMPT, not an aborted "
                     "partial build." if kind == "attempt" else
                     "That directory holds a PARTIAL build: it is neither a release nor "
                     "an attempt, and it may be missing release.json and everything "
                     "written after the failure."),
                  file=sys.stderr)
        raise


def _build_and_publish(args, ctx, staging: Path) -> int:
    """The build itself. `staging` already exists; its lifetime is the caller's."""
    store = ctx["store"]
    product = ctx["product"]
    product_key = ctx["product_key"]
    checkout = ctx["checkout"]
    work = ctx["work"]
    tokenizer = ctx["tokenizer"]
    source_commit = ctx["source_commit"]
    source_tree = ctx["source_tree"]
    environment = ctx["environment"]

    (staging / "checks").mkdir(parents=True, exist_ok=True)
    (staging / "verify-artifacts.py").write_text(
        VERIFY_ARTIFACTS_SOURCE, encoding="utf-8", newline="\n")

    build_source_zip(checkout, staging / "source.zip")

    checks = []
    gaps = list(baseline_gaps(product_key))
    providers = []

    # ---- gate 1: the product's own root suite, against the EXACT pinned source.
    checks.append(run_gate(
        "source-pytest", [args.python_exe, "-m", "pytest"], checkout, checkout,
        staging, tokenizer, TIMEOUT_SOURCE_PYTEST))

    if product_key == "toolkit":
        stage_dir = work / "stage"
        release_ps1 = checkout / "tools" / "release.ps1"
        if not release_ps1.is_file():
            raise ExecutionError(
                "the pinned source has no tools/release.ps1; a toolkit release is built "
                "by the EXISTING release entry, never re-implemented here")
        # ---- gate 2: the existing release entry, all profiles, staged.
        checks.append(run_gate(
            "staged-release",
            [ctx["powershell_exe"], "-NoProfile", "-NonInteractive", "-File",
             str(release_ps1), "-Provider", "all", "-StageDir", str(stage_dir),
             "-PythonExe", args.python_exe],
            checkout, checkout, staging, tokenizer, TIMEOUT_RELEASE_PS1))

        dist_src = stage_dir / "dist"
        checksums_src = stage_dir / "CHECKSUMS.txt"
        if dist_src.is_dir() and checksums_src.is_file():
            shutil.copytree(dist_src, staging / "dist")
            shutil.copy2(checksums_src, staging / "CHECKSUMS.txt")
            providers = sorted(p.name for p in (staging / "dist").iterdir() if p.is_dir())
            # The manifest is the one thing the gate below cannot grade, because it
            # IS the gate's reference. Prove the retained copy is the manifest
            # release.ps1 actually wrote before trusting it to judge anything else.
            if sha256_file(checksums_src) != sha256_file(staging / "CHECKSUMS.txt"):
                raise ExecutionError(
                    "the retained CHECKSUMS.txt is not a faithful copy of the manifest "
                    "tools/release.ps1 produced; refusing to verify the retained "
                    "artifacts against a manifest that changed in transit")
            # ---- gate 3: the RETAINED artifacts verify against the manifest
            # release.ps1 produced. It runs over `staging` -- the bytes that are
            # actually kept and published -- not over the scratch stage that is
            # deleted at exit. Verifying the scratch original would certify bytes
            # nobody keeps, and would leave a copy fault invisible: `artifacts`
            # and SHA256SUMS are computed FROM the retained copy, so they can only
            # ever agree with it. Manifest paths are stage-relative and all start
            # `dist/`, so the same manifest verifies verbatim against the release
            # root -- which is exactly how a consumer re-runs it later.
            require = []
            for provider in TOOLKIT_PROVIDERS:
                require += ["--require-dir", "dist/%s" % provider]
            checks.append(run_gate(
                "artifact-verification",
                [args.python_exe, "verify-artifacts.py", "CHECKSUMS.txt", ".", *require],
                staging, checkout, staging, tokenizer, TIMEOUT_VERIFY,
                cwd_label="<release-dir>"))
        else:
            gaps.append(
                "The existing release entry produced no dist/ + CHECKSUMS.txt pair, so "
                "no artifact verification could run and no profile was packaged.")

        missing_profiles = [p for p in TOOLKIT_PROVIDERS if p not in providers]
        if missing_profiles:
            # Plain quotes, no backticks: this is a known GAP, and that channel
            # is plain text by contract (see md_untrusted).
            gaps.append("Packaged profiles are %s; %s missing from a '-Provider all' "
                        "release." % (providers or "none", ", ".join(missing_profiles)))

    for row in checks:
        row["source_commit"] = source_commit

    # ---- imported proofs.
    reviews = []
    if ctx["proofs"] is not None:
        imported_checks, reviews, proof_gaps = import_proofs(
            ctx["proofs"], ctx["proofs_path"], staging, source_commit, environment,
            attested_by=args.attest_reviews)
        checks.extend(imported_checks)
        gaps.extend(proof_gaps)

    # ---- qualification. Never softened, never inferred.
    qualification, reasons = compute_qualification(product_key, checks, reviews,
                                                   source_commit)
    if qualification != "QUALIFIED":
        gaps.extend(reasons)

    created_at = utcnow()
    record = {
        "schema_version": SCHEMA_VERSION,
        "product": product,
        "version": args.version,
        "release_id": "%s/%s" % (product, args.version),
        "source_commit": source_commit,
        "source_tree": source_tree,
        "builder_commit": ctx["builder_commit"],
        "builder_worktree": ctx["builder_worktree"],
        "created_at": created_at,
        "predecessor": find_predecessor(store, product, args.version),
        "qualification": qualification,
        "qualification_reasons": reasons,
        "providers": providers,
        "artifacts": [],
        "environment": environment,
        "checks": checks,
        "reviews": reviews,
        "known_gaps": gaps,
        "dependencies": dependency_lines(environment, product_key),
        "path_tokens": dict(PATH_TOKEN_DOC),
        "checksum_semantics": dict(CHECKSUM_SEMANTICS),
        "publication": {
            "status": "NOT_PUBLISHED",
            "packet": "public/packet.json",
            "note": "Tagging and upload are a separate, later operator step.",
        },
        "source_root_unchanged": True,
    }

    exit_code = release_exit_code(product_key, qualification)

    build_public_packet(staging, record, product_key, gaps)
    (staging / "release-notes.md").write_text(
        render_release_notes(record, product_key), encoding="utf-8", newline="\n")
    (staging / "receipt.json").write_text(
        json.dumps({
            "schema_version": SCHEMA_VERSION,
            "operation": "baseline-release",
            "operation_id": ctx["operation_id"],
            "release_id": record["release_id"],
            "argv": tokenizer.tokenize_argv(ctx["invocation_argv"]),
            "started_at": ctx["started_at"],
            "recorded_at": created_at,
            "exit_code": exit_code,
            "qualification": qualification,
            "evidence": sorted({row["evidence"] for row in checks if row["evidence"]}),
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    record["artifacts"] = hash_release_tree(staging, ("release.json", "SHA256SUMS"))
    (staging / "release.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    write_sha256sums(staging, record["artifacts"] + [{
        "path": "release.json", "sha256": sha256_file(staging / "release.json")}])

    problem = describe_scan_findings(scan_private_paths([
        (name, staging.joinpath(*name.split("/"))) for name in PUBLIC_SCANNED_ARTIFACTS
    ]))
    if problem:
        raise ExecutionError(problem)

    # ---- publish: one rename of a COMPLETE directory, or retain as an attempt.
    retain_as_release = (qualification == "QUALIFIED"
                         or (product_key == "lab" and qualification == "INCOMPLETE"))
    if retain_as_release:
        final = store / product / args.version
        try:
            os.rename(staging, final)
        except OSError as exc:
            if final.exists():
                # `staging` holds a COMPLETE payload here -- everything above
                # finished writing before the rename was attempted -- so
                # stage_bucket files it as an ATTEMPT. Moving it also empties
                # `staging`, so perform_release's failure handler finds nothing
                # left to retain and stays silent. If the move itself fails, the
                # stage's own path is the honest answer, and the handler will
                # print it with the right description.
                try:
                    kept, kind = retain_failed_stage(store, ctx["operation_id"], staging)
                except ExecutionError:
                    kept = staging
                else:
                    ctx["result_dir"] = kept
                    ctx["result_kind"] = kind
                raise InputError(
                    "COLLISION: '%s' appeared while this release was being staged; a "
                    "retained release is never overwritten, so this run's COMPLETE "
                    "build (record, notes, receipt and every evidence file) is kept "
                    "at '%s' instead and nothing is deleted." % (final, kept))
            raise ExecutionError("could not publish this run's staged build to '%s': %s"
                                 % (final, exc))
        ctx["result_dir"] = final
        ctx["result_kind"] = "release"
    else:
        # The COMMON path: every INCOMPLETE/BLOCKED release comes through here
        # with a complete payload. A failed move raises, and perform_release's
        # handler then files the payload by its CONTENTS through the same
        # stage_bucket -- so it can never be misfiled as an aborted build.
        kept, kind = retain_failed_stage(store, ctx["operation_id"], staging)
        ctx["result_dir"] = kept
        ctx["result_kind"] = kind

    ctx["record"] = record
    return exit_code


def compute_qualification(product_key: str, checks, reviews, source_commit: str):
    """(qualification, reasons). Source checks are recorded independently of packaging.

    A missing or failed gate can never produce QUALIFIED. A failed gate is BLOCKED;
    a merely absent gate or proof is INCOMPLETE. Both keep the source archive.
    """
    reasons = []
    required = ["source-pytest"]
    if product_key == "toolkit":
        required += ["staged-release", "artifact-verification"]

    by_name = {}
    for row in checks:
        if row.get("execution") == "native":
            by_name[row.get("name")] = row

    failed = [row for row in checks
              if row.get("exit_code") is not None and row.get("exit_code") != 0
              and row.get("import_status") in (None, "imported")]
    for row in failed:
        reasons.append("Gate %r exited %s; see %s."
                       % (row.get("name", "check"), row["exit_code"], row["evidence"]))

    for name in required:
        row = by_name.get(name)
        if row is None:
            reasons.append("Required gate %r did not run against this source." % name)

    qualifying = []
    for index, row in enumerate(reviews):
        ok, why = review_qualifies(row, source_commit)
        if ok:
            qualifying.append(row)
        else:
            reasons.append("Review %d does not satisfy the charter invariant: it %s."
                           % (index, why))
    if not qualifying:
        reasons.append(
            "No real representative cross-family review with model-resolution evidence "
            "is attached AND attested, so the product charter's release invariant is "
            "unmet. Attach one through --proofs and name the accountable party with "
            "--attest-reviews; this tool never runs, infers, or verifies a review.")

    if failed:
        return "BLOCKED", reasons
    if reasons:
        return "INCOMPLETE", reasons
    return "QUALIFIED", []


def release_exit_code(product_key: str, qualification: str) -> int:
    """0 only when the REQUESTED operation succeeded.

    Retaining an explicitly INCOMPLETE lab archive is a success and makes no
    qualification claim. Every other non-QUALIFIED outcome is a qualification
    failure: nonzero, with the diagnostics retained and their paths printed.
    """
    if qualification == "QUALIFIED":
        return EXIT_OK
    if product_key == "lab" and qualification == "INCOMPLETE":
        return EXIT_OK
    return EXIT_EXEC


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="baseline_release.py",
        description=(
            "Turn a pinned product source commit into an identifiable, reopenable "
            "release using this repository's existing toolchain. Builds nothing of its "
            "own, publishes nothing, and never overwrites a retained release."),
        epilog=(
            "Example (placeholders resolved before invocation):\n"
            "  python tools/baseline_release.py toolkit --source-root <toolkit-root> \\\n"
            "      --source-commit <full-or-short-rev> --version v0.1.0-baseline.1 \\\n"
            "      --store <release-store> --python-exe <interpreter>\n\n"
            "Exit codes: 0 requested operation completed (the record may carry explicit "
            "missing evidence); 2 bad input or precondition; 1 execution/IO failure, "
            "including qualification failure (diagnostics are retained and printed)."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("product", choices=sorted(PRODUCTS),
                        help="which product to release")
    parser.add_argument("--source-root", required=True,
                        help="the product's git working tree; read-only to this tool")
    parser.add_argument("--source-commit", required=True,
                        help="the pinned product commit (any rev git can resolve)")
    parser.add_argument("--version", required=True,
                        help="ONE safe path segment, e.g. v0.1.0-baseline.1")
    parser.add_argument("--store", required=True, help="the release store root")
    parser.add_argument("--python-exe", required=True,
                        help="interpreter used for the product's own gates")
    parser.add_argument("--proofs", default=None,
                        help="JSON file of attributable existing check/review evidence, "
                             "using the same checks/reviews/environment shapes as "
                             "release.json")
    parser.add_argument("--attest-reviews", default=None, metavar="NAME",
                        help="name the party accountable for the attached review "
                             "evidence. REQUIRED for any review to count toward "
                             "QUALIFIED: this tool cannot verify that a cross-family "
                             "review happened, because the proofs row and its evidence "
                             "document are both caller-authored, so qualification rests "
                             "on this separate named act. Recorded PUBLICLY on each "
                             "review row as attested_by. Needs --proofs.")
    return parser


def prepare(args, invocation_argv):
    """Validate every input and resolve every precondition. Raises InputError."""
    product_key = args.product
    product = PRODUCTS[product_key]
    # The FIRST caller boundary (load_proofs is the other): the whole invocation
    # argv is recorded in receipt.json, and on POSIX an undecodable argument byte
    # arrives as a lone surrogate. Grade it before anything is built.
    for index, item in enumerate(invocation_argv):
        reject_unencodable(item, "argv[%d]" % index)
    args.version = validate_version(args.version)

    reject_placeholder(args.source_root, "--source-root")
    reject_placeholder(args.source_commit, "--source-commit")
    reject_placeholder(args.store, "--store")
    reject_placeholder(args.python_exe, "--python-exe")
    if args.proofs is not None:
        reject_placeholder(args.proofs, "--proofs")
    if args.attest_reviews is not None:
        reject_placeholder(args.attest_reviews, "--attest-reviews")
        args.attest_reviews = args.attest_reviews.strip()
        if len(args.attest_reviews) > ATTESTATION_MAX_LEN:
            raise InputError("--attest-reviews is longer than %d characters; it names "
                             "an accountable party, not a narrative"
                             % ATTESTATION_MAX_LEN)
        # The name is PUBLISHED on every review row, so it is held to the same
        # standard as a proofs field. The end-of-run leak guard would also catch
        # this, but only after the full slow release -- refuse it up front.
        # One owner for "does this text leak" (reject_placeholder above already
        # refuses '<' and '>' here, so no documented token can reach this call).
        if contains_private_path(args.attest_reviews):
            raise InputError(
                "--attest-reviews carries an absolute user path. It is recorded on a "
                "PUBLIC review row as attested_by, so it must name a party, not a "
                "machine location.")
        if args.proofs is None:
            raise InputError(
                "--attest-reviews was given without --proofs, so there is no review to "
                "attest. The attestation names the party accountable for ATTACHED "
                "review evidence; supply --proofs, or drop the flag.")

    source_root = Path(args.source_root).expanduser()
    if not source_root.is_dir():
        raise InputError("--source-root '%s' is not a directory" % source_root)
    source_root = source_root.resolve()
    assert_work_tree(source_root, "--source-root")

    store = Path(args.store).expanduser()
    assert_no_linked_ancestor(store, "--store")
    store_abs = store.resolve() if store.exists() else Path(os.path.abspath(str(store)))
    store_key = os.path.normcase(str(store_abs))
    source_key = os.path.normcase(str(source_root))
    if store_key == source_key or store_key.startswith(source_key + os.sep):
        raise InputError(
            "--store '%s' is inside --source-root '%s'. The working source is read-only "
            "to this tool; point the store outside it." % (store_abs, source_root))
    try:
        store_abs.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise InputError("--store '%s' cannot be created: %s" % (store_abs, exc))
    assert_no_linked_ancestor(store_abs, "--store")

    python_exe = shutil.which(args.python_exe) or (
        args.python_exe if Path(args.python_exe).is_file() else None)
    if not python_exe:
        raise InputError("--python-exe '%s' was not found" % args.python_exe)
    args.python_exe = str(Path(python_exe).resolve())

    powershell_exe = shutil.which("powershell")
    if product_key == "toolkit" and not powershell_exe:
        raise InputError(
            "a toolkit release runs the existing PowerShell release entry, and "
            "`powershell` is not on PATH. Windows PowerShell 5.1 is the floor; there is "
            "no POSIX path.")

    proofs_path = None
    proofs = None
    if args.proofs is not None:
        proofs_path = Path(args.proofs).expanduser()
        if not proofs_path.is_file():
            raise InputError("--proofs '%s' is not a file" % proofs_path)
        proofs_path = proofs_path.resolve()
        proofs = load_proofs(proofs_path)

    builder_root = Path(__file__).resolve().parent.parent
    assert_work_tree(builder_root, "this tool's own repository")
    builder_commit = resolve_object(builder_root, "HEAD", "commit", "builder commit")
    builder_status = run([git_exe(), "-C", str(builder_root), "status", "--porcelain"],
                         timeout=TIMEOUT_GIT)
    builder_worktree = "dirty" if builder_status.stdout.strip() else "clean"

    source_commit = resolve_object(source_root, args.source_commit, "commit", "source commit")
    source_tree = resolve_object(source_root, args.source_commit, "tree", "source tree")

    tokenizer = PathTokenizer()
    tokenizer.bind("<python-exe>", args.python_exe)
    if powershell_exe:
        tokenizer.bind("<powershell>", powershell_exe)
    tokenizer.bind("<source-root>", source_root)
    tokenizer.bind("<store>", store_abs)
    if proofs_path is not None:
        tokenizer.bind("<proofs>", proofs_path)

    return {
        "product_key": product_key,
        "product": product,
        "source_root": source_root,
        "store": store_abs,
        "powershell_exe": powershell_exe,
        "proofs": proofs,
        "proofs_path": proofs_path,
        "builder_commit": builder_commit,
        "builder_worktree": builder_worktree,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "tokenizer": tokenizer,
        "operation_id": str(uuid.uuid4()),
        "invocation_argv": list(invocation_argv),
        "started_at": utcnow(),
    }


def remove_disposable_workspace(work: Path) -> bool:
    """Delete the scratch workspace. A partial failure is SAID OUT LOUD.

    A git object directory is marked read-only on Windows, and an antivirus or
    indexer handle can hold a file open for seconds after the process that wrote
    it exits. Retry once with the read-only bit cleared, and if debris survives
    that, warn -- silent `ignore_errors=True` leaves it behind forever with no
    operator-visible signal, which is how a 'disposable' directory stops being
    disposable. Nothing in the retained release depends on this succeeding.
    """
    shutil.rmtree(work, ignore_errors=True)
    if work.exists():
        for dirpath, dirnames, filenames in os.walk(work):
            for name in list(dirnames) + list(filenames):
                try:
                    os.chmod(os.path.join(dirpath, name), stat.S_IWRITE)
                except OSError:
                    pass
        shutil.rmtree(work, ignore_errors=True)
    if work.exists():
        print("baseline-release: WARNING: the disposable workspace '%s' could not be "
              "fully removed (a locked or read-only file). It holds only scratch -- the "
              "checkout and the release stage -- and is safe to delete by hand."
              % work, file=sys.stderr)
        return False
    return True


def main(argv=None) -> int:
    invocation_argv = [os.path.basename(sys.argv[0] or "baseline_release.py")] + list(
        sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    work = None
    ctx = None
    try:
        ctx = prepare(args, invocation_argv)
        store = ctx["store"]
        product = ctx["product"]

        fingerprint_before = worktree_fingerprint(ctx["source_root"])

        work = store / ".work" / ctx["operation_id"]
        work.mkdir(parents=True, exist_ok=False)
        checkout = work / "checkout"
        ctx["work"] = work
        ctx["checkout"] = checkout
        ctx["tokenizer"].bind("<source-checkout>", checkout)
        ctx["tokenizer"].bind("<stage-dir>", work / "stage")

        make_disposable_checkout(ctx["source_root"], ctx["source_commit"], checkout)
        verify_checkout_agreement(checkout, ctx["source_commit"], ctx["source_tree"])

        existing = store / product / args.version
        if existing.exists():
            if args.proofs is not None:
                print("baseline-release: note: --proofs (and any --attest-reviews with "
                      "it) is not re-imported when verifying an already-retained "
                      "release; a retained record is never rewritten")
            record = verify_existing(existing, product, args.version, ctx["source_commit"],
                                     ctx["source_tree"], checkout)
            print("baseline-release: VERIFIED %s" % record.get("release_id"))
            print("baseline-release: qualification=%s" % record.get("qualification"))
            print("baseline-release: release_dir=%s" % existing)
            print("baseline-release: recorded inputs, artifact hashes, SHA256SUMS and "
                  "source.zip extracted contents all match; nothing was overwritten")
            return EXIT_OK

        ctx["environment"] = capture_environment(args.python_exe, ctx["powershell_exe"])
        exit_code = perform_release(args, ctx)

        fingerprint_after = worktree_fingerprint(ctx["source_root"])
        if fingerprint_before != fingerprint_after:
            print("baseline-release: WARNING: the working source at '%s' changed during "
                  "this run; it is read-only to this tool, so something else wrote to it"
                  % ctx["source_root"], file=sys.stderr)

        record = ctx["record"]
        print("baseline-release: product=%s version=%s" % (product, args.version))
        print("baseline-release: source_commit=%s" % record["source_commit"])
        print("baseline-release: source_tree=%s" % record["source_tree"])
        print("baseline-release: builder_commit=%s (%s worktree)"
              % (record["builder_commit"], record["builder_worktree"]))
        print("baseline-release: qualification=%s" % record["qualification"])
        print("baseline-release: providers=%s" % (",".join(record["providers"]) or "none"))
        print("baseline-release: %s_dir=%s" % (ctx["result_kind"], ctx["result_dir"]))
        print("baseline-release: receipt=%s" % (ctx["result_dir"] / "receipt.json"))
        print("baseline-release: record=%s" % (ctx["result_dir"] / "release.json"))
        if ctx["result_kind"] == "attempt":
            print("baseline-release: QUALIFICATION FAILED (%s). The archive and its "
                  "diagnostics are retained above; the version name '%s' is NOT reserved, "
                  "so a retry allocates a new attempt and preserves this one. Nothing is "
                  "deleted." % (record["qualification"], args.version), file=sys.stderr)
        return exit_code

    except InputError as exc:
        print("baseline-release: ERROR (input/precondition): %s" % exc, file=sys.stderr)
        return EXIT_INPUT
    except ExecutionError as exc:
        print("baseline-release: ERROR (execution): %s" % exc, file=sys.stderr)
        return EXIT_EXEC
    except KeyboardInterrupt:
        print("baseline-release: interrupted; no directory was published", file=sys.stderr)
        return EXIT_EXEC
    except OSError as exc:
        print("baseline-release: ERROR (io): %s" % exc, file=sys.stderr)
        return EXIT_EXEC
    except UnicodeError as exc:
        # UnicodeEncodeError is a ValueError, NOT an OSError, so without this
        # clause it escapes every handler above as a raw traceback and takes the
        # documented {0,1,2} exit-code contract with it. reject_unencodable()
        # refuses the two CALLER boundaries up front at exit 2; this clause is
        # for what that cannot reach -- a filesystem-supplied name carrying a
        # surrogate. It does not neutralize anything: it makes the failure
        # legible and keeps the exit code honest.
        print("baseline-release: ERROR (encoding): %s. Every artifact this tool "
              "writes is UTF-8; nothing was published." % exc, file=sys.stderr)
        return EXIT_EXEC
    except subprocess.SubprocessError as exc:
        # TimeoutExpired is a SubprocessError, NOT an OSError, so without this
        # clause it escapes every handler above as a raw traceback and takes the
        # documented {0,1,2} exit-code contract with it. run_gate() converts its
        # OWN timeout to an ExecutionError, and nothing else does: capture_
        # environment's powershell/git/python probes and every git() call run
        # under their own ceilings with no conversion. Catching the class once,
        # here, is what stops that from being a thing each new call site has to
        # remember.
        print("baseline-release: ERROR (subprocess): %s" % exc, file=sys.stderr)
        return EXIT_EXEC
    finally:
        if work is not None and work.is_dir():
            remove_disposable_workspace(work)


if __name__ == "__main__":
    sys.exit(main())
