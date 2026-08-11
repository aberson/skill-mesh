"""Link-resolution gate for the canonical tree and the built host profiles (Step 63).

WHY THIS FILE EXISTS
--------------------
Nothing in this repository resolved a *relative* reference the way a host does.
`test_skill_tree.py:_ref_defect` resolves markdown links against the REPO root and
returns `None` outright for any relative backtick/bare token -- so a `core.md` could
cite `../../_shared/judge-core.md`, have it resolve inside this checkout by pure
repo-layout coincidence, and ship into a consumer profile where nothing exists above
the discovery root. That is exactly how this defect class shipped green.

This gate resolves every in-scope reference the way the SHIPPED tree resolves it, and
freezes today's failures so they can only shrink. Landed BEFORE any repair (D7): a
detector written alongside its fix is a test written to pass.

**This step repairs nothing.** Steps 64 and 66 delete entries from KNOWN_DANGLING;
the burn-down is the evidence that their fixes worked.

RESOLUTION MODEL (the load-bearing idea)
----------------------------------------
Every scanned file has a *root* -- the directory that becomes the host discovery root
once the file ships. A reference is DANGLING when, resolved relative to the citing
file's own directory, it either escapes that root (nothing can exist above a discovery
root in a consumer home) or names a path that does not exist.

  scanned tree      root                 why
  skills/**/*.md    skills/              each skills/<name>/ becomes <discovery-root>/<name>/
  _shared/**/*.md   <repo root>          _shared/ ships AT the discovery root, as a sibling
                                         of the skill dirs, which is the same shape the repo
                                         root has today (repo-root <skill>/ mirrors
                                         <discovery-root>/<skill>/)
  dist/<p>/**/*.md  dist/<p>/            the profile IS the discovery root

Consequence, and it is the point: `../../_shared/x` in `skills/<n>/core.md` resolves
inside this checkout but ESCAPES `skills/`, so it is dangling here even though
`test_skill_tree.py` calls it fine. It is dangling for every consumer.

That root mapping is the ONE parameter no count floor can see. Re-rooting `skills/`
at the repo root makes 21 canonical entries resolve while `files_scanned`,
`refs_extracted` and every per-form count stay byte-identical -- a fully green,
fully documented burn-down with zero references repaired. It is pinned by
`CANONICAL_ROOTS` + `test_resolution_roots_are_pinned` and, more importantly, by
`test_escaping_reference_is_dangling_even_though_it_resolves`, which reproduces the
re-root on a synthetic tree and asserts the two verdicts differ.

The `_shared/` root is the repo root, and the repo root also carries `tools/`,
`config/`, `runtime/`, `documentation/`, `tests/` and the legacy `<skill>/scripts/`
subtrees -- none of which reach a discovery root. `ships_into_discovery_root` therefore
constrains what a repo-root-rooted reference may be credited with resolving TO:
`<skill>/SKILL.md`, `<skill>/core.md`, or anything under `_shared/`, which is exactly
what `build-distributions.ps1` emits (plus the `_shared/` tree Step 64 adds). Without
it, `_shared/score-skill.md`'s citation of `../skill-eval-setup/scripts/...` resolves
against a repo-only directory and the gate calls a genuinely broken reference fine.

COROLLARY FOR STEP 64 (say it here, because this docstring is where the later steps
read their contract)
-------------------------------------------------------------------------------------
Under `root = skills/`, NO spelling of a reference from `skills/<n>/core.md` reaches
`_shared/`: `_shared/x` -> `skills/<n>/_shared/x` (absent), `../_shared/x` ->
`skills/_shared/x` (absent), `../../_shared/x` -> escapes. So the canonical
`shared_anchored` and `shared_bare` entries CANNOT be repaired by rewriting the
citation. They leave the allowlist only by the citation being deleted or converted to
prose, or by `skills/_shared/` coming to exist. A build-time repoint clears the
`dist/**` entries and none of the canonical ones. A step that finds itself widening
`scan_canonical_trees`'s root to make them resolve is performing the fake burn-down
`test_escaping_reference_is_dangling_even_though_it_resolves` exists to stop.

REFERENCE SCOPE (stated once; narrowing it reds the detector-scope matrix)
--------------------------------------------------------------------------
Three forms are extracted -- markdown `link`, `backtick`, and bare prose `bare` -- and
a reference is IN SCOPE when it is anchored somewhere this tree owns:

  * explicitly relative (`./`, `../`) in LINK form            -- always; a link is a
    clickable promise that the target ships next to the citing file
  * explicitly relative in backtick/bare form                 -- when its first named
    segment is an owned documentation namespace: `_shared`, `references`, `rules`, `docs`
  * `_shared/`-rooted token in any form                       -- this repo's own shared
    asset namespace (the class the plan calls "bare non-anchored `_shared/` tokens")

Namespace membership is CASE-INSENSITIVE (`is_owned_namespace`), and so is the retirement
proof's token-presence test. This host's filesystem is case-insensitive, so
`../../References/x.md` still opens locally while dangling on every case-sensitive
consumer home -- the exact class `resolve_reference`'s "case does not match the on-disk
name" branch exists to report. Case-SENSITIVE membership dropped that citation out of
scope, so the detector never saw it AND assertion 4 read its frozen token as gone: one
character retired an entry fully green with the broken citation still shipping. Measured
when this was widened: 0 live mis-cased tokens, 0 entries added or removed, ceiling
unmoved.

A backtick span may carry SEVERAL path cores (`python ../../_shared/x.py --flag`), and
every whitespace-separated token in it is considered. Keeping only the first token used
to drop the reference entirely AND leave `refs_extracted` unchanged, so neither the
assertions nor any count floor could see the loss -- while the identical text
inside a fenced block was detected.

OUT OF SCOPE, deliberately:

  * host-home-anchored refs (`<dot>claude/...`, `~/...`, `<drive>:/...`). The repo
    already has ONE owner for that policy -- `test_skill_tree.py:_EXT_PREFIXES` declares
    them external-and-allowed, and `_STRANDED_RE` there catches the pathological
    stranded forms. A second owner rendering the opposite verdict would be a split
    contract, and freezing ~500 permanently-residual workspace citations would bury the
    two classes that actually burn down. The escape hatch this opens -- "fix" a
    `../../references/x` citation by re-anchoring it to a home path -- is NARROWED (not
    sealed) by `test_home_anchored_doc_citations_do_not_grow` below: that test is a
    TOTAL ceiling, so deleting one home citation elsewhere still buys one re-anchor.
    What it does guarantee is that the population cannot grow, in any spelling that
    puts an owned namespace anywhere inside a home- or drive-anchored path.
  * unanchored `references/`, `rules/`, `docs/` prose tokens. They name workspace
    documents the HOST resolves, not tree-internal targets.
  * a NON-LINK token that ENDS at an owned namespace (`_shared/`, `../references/`).
    That is the namespace being named in prose -- `# _shared/` is the H1 of
    `_shared/README.md` -- not a reference to a path, and it can never be repaired.
    Scoped to non-link forms deliberately: a link DESTINATION is never prose, so
    `[references](../../references/)` stays IN scope. Were links narrowed too, a step
    could retire a `references_anchored` entry by truncating its link to the bare
    namespace -- a de-scoping, not a repair. Measured when this was written: zero live
    references in either tree carry a namespace tail in ANY form, so the form gate moved
    no count and no entry; it is hardening, not a live behavior change.
  * `*.py` / `*.js` / `*.ps1` bodies. Markdown is what ships as skill prose; the
    non-markdown assets are covered by the distribution suite.

ENTRY SHAPE + KEY
-----------------
`source` (repo-relative citing file), `raw` (the reference token), `target` (its
normalized resolution, relative to the file's root), `form`, `class`, `line`.
The key is `(source, raw, form)`. **`line` is excluded from the key** -- an entry keyed
on a line number turns every unrelated edit above a citation into a spurious "new
dangling ref", and the burn-down would measure churn instead of repair.

`raw` is the token reduced to its path core: surrounding wrapper punctuation, a
`#fragment`, a `::symbol` suffix and trailing sentence punctuation removed, backslashes
normalized to `/`. Recorded here because "exactly as written" would make the key
unstable under insignificant punctuation, and would split one citation into two
entries over a trailing comma.

THE FOUR ASSERTIONS
-------------------
A bare "monotonic shrink" over a literal each step edits is a tautology, so:

  1. `set(detected) <= set(KNOWN_DANGLING)`  -- any NEW dangling ref hard-fails.
  2. `set(KNOWN_DANGLING) <= set(FROZEN_BASELINE)` where FROZEN_BASELINE is
     `link_baseline.json`, a separate committed file whose bytes are digest-pinned
     here. It is the only comparand a step does not also author; without it
     "shrink-only" compares a literal against itself.
  3. every KNOWN_DANGLING entry STILL DANGLES, and still dangles for the SAME recorded
     `target`/`reason`/`class` -- kills rewrite-to-a-normalized-spelling instead of
     delete, and catches a resolution model that changed underneath the frozen record.
     (1)+(3) together pin `detected == KNOWN_DANGLING`.
  4. RETIREMENT PROOF -- every entry in FROZEN_BASELINE that is no longer in
     KNOWN_DANGLING was actually DISPOSED OF, proven from the current tree. The next
     section is why this exists and what it replaced.

(1)-(3) are one pure function, `evaluate_gate`, table-driven against each gaming vector
by `test_gate_arithmetic_reds_on_each_gaming_vector` -- so the arithmetic Steps 64 and 66
are graded by has been observed to fire, rather than only ever evaluating an empty-set
difference over data generated to make it empty. (4) has its own red-on-garbage anchor,
`test_retirement_proof_reds_on_an_undisposed_entry`.

WHY ASSERTION 4 EXISTS, AND WHAT IT REPLACED
--------------------------------------------
Two earlier revisions of this file tried to catch a DETECTOR NARROWING with a floor under
`refs_extracted`. Both were defeated, in opposite directions:

  * a RAW floor equal to today's measurement is a tripwire on any edit, not on narrowing.
    D-63-A sanctions "converted to prose, or dropped" as dispositions and both mechanically
    decrement `refs_extracted`, so the sanctioned burn-down path reds with no legal remedy.
  * a BUDGETED floor (`frozen - retired_occurrences`, the budget granted for frozen
    entries no longer in KNOWN_DANGLING) is worse: the budget is derived FROM
    KNOWN_DANGLING, which the step itself edits. Narrow the detector, delete the entries
    the narrowing hid, and the budget grows by exactly the amount the count fell.
    Demonstrated on a real run: dropping ONE alternation from `_BARE_RE` plus deleting the
    six entries it hid removed an entire reference FORM from both sides, and the suite
    stayed green.

Counting references cannot distinguish "a reference was legitimately removed" from "the
detector stopped seeing it" -- both reduce the count, and both permit deleting the entry.
So the primary control is not a count. It is a disposition proof, re-derived from the
CURRENT tree for every entry the allowlist claims to have retired:

  An entry may leave KNOWN_DANGLING only if, for its FROZEN `source` + `raw`, either
    (a) REPAIRED -- re-resolving `raw` from `source` now RESOLVES to a FILE, or
    (b) REMOVED  -- `raw` is no longer CITED in `source`, or `source` itself is gone
        (the sanctioned prose-conversion / deletion disposition).

Both branches are re-derived from `link_baseline.json` -- immutable, and it retains every
original entry -- and NEITHER routes through `extract_references`, `candidate_cores` or
`is_reference_in_scope`, the extraction/scope predicates a narrowing edits. Were the proof
to consult those, narrowing them would hide the evidence too. A narrowing satisfies
neither branch: the token is still sitting in the source file, and it still does not
resolve. So the narrowing attack reds here regardless of what any counter says.

Branch (b) asks "is this reference still CITED here", not "do these bytes appear anywhere
in the file" -- `_citation_occurrences`, which is self-contained (a `re` boundary test
plus the frozen record) precisely so the independence above survives. The bytes question
was the wrong one in both directions:

  * it FALSE-RED the most natural sanctioned disposition. 23 of the 149 frozen entries
    have a `raw` that is a strict substring of another frozen `raw` in the same file --
    the house style writes ``[`_shared/judge-core.md`](../../_shared/judge-core.md)`` --
    so fixing the LABEL left the short token's bytes inside the destination and the proof
    said "you retired an entry without repairing it". There was no legal remedy: the step
    cannot delete a substring belonging to a citation it is not disposing of.
  * it FALSE-GREEN a case flip. `../../references/x.md` -> `../../References/x.md` made
    the bytes "absent" while the broken citation shipped.

An occurrence is discounted ONLY when all three of (i) it is not delimited the way a
citation is, (ii) it lies entirely inside an occurrence of a LONGER `raw` frozen for the
same source -- another frozen entry, carrying its own assertion-3/4 obligation, already
accounts for those bytes -- and (iii) THAT LONGER SIBLING DID NOT GAIN OCCURRENCES: its
current cited count is `<=` the `cited_occurrences` frozen for it.

(iii) exists because (i)+(ii) alone are NOT the bound the first revision claimed. They
were justified as "a link label was shortened", but RE-SPELLING the short citation into
the long one satisfies them identically and repairs nothing. Measured on
`skills/skill-iterate/core.md`: rewriting 7 bare `` `_shared/score-skill.md` `` citations
as `` `../../_shared/score-skill.md` `` (which dangles too) retired 3 entries with 0
references repaired, suite fully green -- and the same shape was available on all 23
substring-sibling entries, i.e. the burn-down metric that IS the evidence Steps 64/66
worked could be driven 149 -> 126 by re-spelling alone.

Occurrence provenance separates the two cases and is already in the frozen record.
Shortening a LABEL leaves the destination citation alone, so the longer sibling's count
does not move. Re-spelling MOVES occurrences INTO the longer sibling, so its count rises
(14 -> 21 in the measured attack). A sibling that grew is not accounting for those bytes;
it swallowed them, so it buys no discount and the entry reds.

This is PER-ENTRY PROVENANCE, not a count budget: nothing is summed across entries, no
global floor moves, and retiring an entry grants no slack anywhere. The defeated budget
described above is not being reintroduced. Named as the narrowing it still is -- bytes
that used to count no longer do -- now bounded to the three-clause conjunction, with both
the sibling set and the comparand count read from the digest-pinned record, which a step
may not author.

What assertion 4 does NOT give you, stated plainly rather than claimed away:

  * It uses `resolve_reference` and the pinned root map, because re-resolving IS the
    proof. Widening those is a DIFFERENT attack, caught by `test_resolution_roots_are_pinned`,
    `test_escaping_reference_is_dangling_even_though_it_resolves` and
    `test_shipped_shape_predicate_is_pinned` -- not by this.
  * It cannot tell a sanctioned prose conversion from an unsanctioned deletion of a
    citation: both are branch (b). That distinction is a review judgement, and D-63-A is
    where it lives. What (b) does establish mechanically is that the citation is GONE from
    the shipped prose -- which is exactly the claim a retirement makes.
  * It is a proof about the entries the frozen record already holds. It says nothing about
    references that were never frozen; assertion 1 and the floors below cover those.
  * Re-spelling a citation into a form that is neither stand-alone nor covered by a frozen
    sibling still counts as CITED, so it reds here -- but a re-spelling that lands OUT of
    scope entirely (a `<template>` segment) removes the token by branch (b)'s own
    definition, exactly as prose conversion does. That is the disclosed limit of (b), not
    a new one.
  * The sibling gate is `<=`, so it catches growth, not flatness. An edit that re-spells
    one short citation INTO the long form while also DELETING one pre-existing long
    citation in the same file holds the long count level and still retires the short
    entry. That is a strictly two-sided edit which additionally destroys a citation the
    step is not disposing of -- the long entry's own assertion-3 obligation has to answer
    for that -- so it is harder, not impossible. The class is narrowed, NOT closed.

THE REMAINING FLOORS (deliberately few)
---------------------------------------
With assertion 4 carrying the anti-narrowing load, the counting controls are cut back to
the two that are INVARIANT under every sanctioned disposition:

  * `files_scanned`, per side and per profile -- a RAW floor. Repairing a reference never
    deletes a markdown file, converting one to prose never deletes a markdown file, and
    both later steps ADD files (Step 64 emits `_shared/` into each profile; Step 66
    vendors seven docs into `_shared/`). A drop here is always a narrowed walk.
  * `refs_resolving`, per side -- a RAW floor on the in-scope references that currently
    RESOLVE. This is the population the burn-down cannot move downward: a prose conversion
    or a drop removes a DANGLING reference, leaving it unchanged, and a repair moves one
    INTO it (+1). A narrowing that stops seeing references which resolve reds here; a
    narrowing that stops seeing DANGLING references reds on assertion 3 (entry kept) or
    assertion 4 (entry deleted).
    Residual: legitimately DELETING a reference that currently resolves reds this floor,
    and a step that repairs N references buys N units of slack against it. The first is a
    signal worth reading rather than a false green; the second is bounded by sanctioned
    work, not a constant.

Deleted along with the budget: the per-form `refs_extracted` floors. Their job -- "a regex
that quietly stops matching one form must red" -- is done strictly better by
`test_detector_scope_matrix_is_pinned`, which plants a reference for every FORM x every
in-scope CLASS x every ANCHOR SPELLING (`./`, `../`, unanchored -- a full 9-cell grid with
form) x each declared surrounding CONTEXT, and asserts each is detected, plus every
documented out-of-scope form and asserts each is rejected. That control is a fixed
fixture: it cannot be satisfied by deleting an entry, it does not move when the burn-down
moves, and dropping any alternation from any of the three extraction regexes reds it
directly.

The anchor and context axes were added after six ONE-LINE detector narrowings were each
demonstrated still-green against the (form x class) version: `./` killed in scope and in
`_BARE_RE`, empty link text, a `(` in `_BARE_RE`'s lookbehind, `clean_ref` no longer
stripping parens, and stripping HTML comments before extraction. Every one has an EMPTY
live population today, so assertion 1 has nothing to red on and assertion 4 -- which only
ever proves things about FROZEN entries -- has nothing to prove; the matrix is the only
control that can see them, which is why its completeness is itself asserted by
`test_scope_matrix_covers_every_form_and_class`. That completeness proof is honest about
its own limit: forms, classes and anchors are enumerated from code, CONTEXT is a
hand-maintained floor because no code object enumerates "syntaxes a citation can sit in".
`counts.refs_extracted_by_form` stays in the frozen record as provenance of the scan. It
is NOT read as a floor, and nothing should start reading it as one.

TAMPER-EVIDENCE, AND EXACTLY WHAT IT DOES NOT BUY
--------------------------------------------------
`link_baseline.json` is written by this file's own `--emit`. Re-running it absorbs any
new dangling reference into the frozen record while `note`, `generated_by` and
`decisions` stay byte-identical, so every prose-checking assertion survives the
regeneration. Prose inside a file cannot protect that file.

So `BASELINE_SHA256` below pins its bytes (CRLF->LF normalized, BOM stripped -- the
same normalization `tools/release.ps1` checksums with, so the digest is stable across
clones). What this buys, precisely:

  * GUARANTEED: the frozen record cannot change without also changing a 64-hex constant
    in a different file. Absorbing a new dangling reference now takes three coordinated
    edits ACROSS TWO FILES -- the baseline, plus the `KNOWN_DANGLING` literal and the
    digest, which both live here -- and the digest edit is unmistakable in a review diff.
    Silent absorption is impossible.
  * NOT GUARANTEED: the record is not unwritable. A step that makes all three edits gets
    a green gate. Nothing inside this repository can prevent that. The control is
    tamper-EVIDENT, not tamper-proof; review is what stops it, and this makes review
    able to see it.
  * `--emit` additionally REFUSES to write into `tests/package-integrity/` unless the
    operator passes `--widen-frozen-record`, so the one-command regeneration is no
    longer the documented happy path.

TWO DECISIONS THIS STEP RECORDS (also carried in link_baseline.json `decisions`, where
`test_recorded_decisions_are_carried_in_the_frozen_baseline` machine-checks them)
-----------------------------------------------------------------------------------
D-63-A -- **Allowlist REPLACEMENT is NOT permitted.** Step 66 asks whether any of the
14 external links inherited from the seven vendored reference docs may be dispositioned
as an "approved allowlist replacement". They may not. An entry may LEAVE the allowlist;
none may enter it, so Step 66's 14 links must each be vendored, converted to prose, or
dropped. Enforcement is the pair above -- assertion 2 against the frozen record, plus
the digest pin that makes editing that record visible -- which is tamper-EVIDENT and
nothing stronger. It is NOT the case that a replacement entry is mechanically
impossible; it is the case that adding one cannot be done quietly. The only sanctioned
way to widen the record is an explicit operator decision recorded in the plan, which
sits above a step.

D-63-B -- **The 46 legacy top-level `<skill>/SKILL.md` packages are OUT of scope.**
Section 8's risk table asks for them to be "logged in KNOWN_DANGLING as a distinct
class". They are not, for three measured reasons. (i) The form that row names -- the
one-level anchored `../_shared/` citation -- RESOLVES today: a legacy package sits at
`<repo>/<skill>/SKILL.md`, so `../_shared/x` lands on `<repo>/_shared/x`, which exists.
The requested distinct class would be EMPTY, and the row's real concern is surface
DIVERGENCE after this phase, not danglingness.
`test_legacy_packages_anchored_shared_refs_still_resolve` pins that measurement, so if
it ever stops being true the decision is forced open again rather than silently
inherited. (The same files also carry bare `_shared/x` tokens that DO dangle -- but
those are class `shared_bare`, already frozen as permanent residual for `skills/`, so
more of them would add no signal and no burn-down.) (ii) They are a frozen
compatibility surface for the deprecation window -- "NOT canonical, not updated by the
migration" -- and no step in this phase edits them, so entries could never burn down.
(iii) D7 forbids KNOWN_DANGLING from growing, so ~220 permanently-frozen entries would
inflate the only comparand the later steps are measured against.

FILE ENUMERATION
----------------
Trees inside the work tree are enumerated with `git ls-files`, matching this repository's
convention for anything that must reflect TRACKED state -- the git INDEX, so a staged but
uncommitted file IS scanned (CLAUDE.md on release staging; the Step 46 `git ls-files` gate
added after committed fixtures polluted real discovery paths). During Step 63's own review
an untracked scratch probe under `skills/` polluted three `--emit` runs and would have
hard-failed the gate on a file git has never seen. `dist/` is gitignored, so the profile
scan legitimately falls back to a filesystem walk -- the enumeration is a hybrid by
design, not by omission.

Three ways that hybrid silently produced a ZERO-file scan, all now closed and all
regression-tested against a synthetic git repo in `tmp_path` (`markdown_files` takes an
explicit `repo_root` so those tests never touch this checkout):

  * git answered with NOTHING. An empty `git ls-files` result is not an answer, it is the
    absence of one -- a gitignored or scratch tree INSIDE the work tree returns `[]`, and
    treating `[]` as authoritative scanned zero files while 97 markdown files sat on disk.
    Measured live trap: `_emit`'s own refusal message recommends emitting to a scratch
    directory, and a scratch directory inside the repo produced 56 entries instead of 151
    with no error -- counts that read like a 95-entry burn-down. Now: a non-empty tracked
    result wins; anything else falls back to the walk.
  * the repo root was not this tree's root. `tools/release.ps1` stages into
    `<repo>\release-stage` and runs this suite from there, so `REPO_ROOT` is the STAGE
    while `git -C <stage>` still answers for the OUTER repository, whose paths do not
    exist under the stage. Reproduced as 3 failed / 26 passed. Now: `git rev-parse
    --show-toplevel` must equal `REPO_ROOT` or the git path is not used at all.
  * git's `-z` bytes were locale-decoded. `-z` exists so paths arrive as raw UTF-8 bytes;
    `text=True` decoded them as cp1252 on the supported host and `errors="replace"` turned
    the resulting `UnicodeDecodeError` into a silently wrong path. Now decoded as UTF-8
    explicitly.

`git ls-files` reads the index, so a worktree deletion that has not been staged yet leaves
a path in the enumeration that is no longer on disk. That is reported as a WORDED failure
naming the paths, never filtered out: silently dropping absent paths would swallow the
decode bug above and narrow the scan invisibly, which is the exact shape everything here
exists to prevent.

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone with
`--emit <dir>`, which regenerates the frozen baseline and the KNOWN_DANGLING literal
from a real scan. The committed baseline was produced that way -- never hand-counted,
which is how the plan's earlier "59" went wrong.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).resolve().parent / "link_baseline.json"
SKILLS_DIR = REPO_ROOT / "skills"
SHARED_DIR = REPO_ROOT / "_shared"
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"
PROFILES = ("claude", "gpt")

# SHA-256 of link_baseline.json, CRLF->LF normalized and BOM stripped. This lives in a
# DIFFERENT file from the one it protects, on purpose: `--emit` rewrites the baseline in
# place and every prose-checking assertion survives that regeneration byte-identical.
# See "TAMPER-EVIDENCE" in the module docstring for what this does and does not buy.
BASELINE_SHA256 = "cd786bf964a06a321b72297a4832c11ce17fbdcc17d8e0f7c1646b0ea70fb14a"

# powershell, never pwsh: PowerShell 7 is not installed on the supported host and
# every `pwsh` invocation fails outright (CLAUDE.md, Key commands).
PWSH = shutil.which("powershell")
GIT = shutil.which("git")

# Documentation namespaces this repository owns or is vendoring into `_shared/`.
OWNED_NAMESPACES = ("_shared", "references", "rules", "docs")

# Namespace membership is CASE-INSENSITIVE everywhere -- always through this predicate,
# never through a bare `in OWNED_NAMESPACES`. This host is Windows with a
# case-insensitive filesystem, so `../../References/task-state-schema.md` still opens
# locally while dangling on every case-sensitive consumer home: the exact host-parity
# class `resolve_reference`'s "case does not match the on-disk name" branch exists to
# catch. A case-SENSITIVE membership test dropped that citation out of scope entirely,
# so the detector never saw it AND the retirement proof read its frozen token as gone --
# a one-character edit that retired an entry fully green while shipping the broken
# citation. Measured when this was widened: 0 live mis-cased owned-namespace tokens in
# either tree, 0 scope-verdict changes, 0 entries added or removed, and the
# home-anchored ceiling unmoved at 144 -- so this is hardening, not a behavior change.
_OWNED_LOWER = frozenset(n.lower() for n in OWNED_NAMESPACES)


def is_owned_namespace(segment):
    """True when `segment` names an owned documentation namespace, in ANY casing."""
    return segment.lower() in _OWNED_LOWER

# Assembled, never spelled, so tests/router/test_no_claude_dependency.py stays green.
# Same constant name and casing as the package-integrity siblings that hoist it
# (test_skill_tree.py, test_cutover_handoff.py, test_host_discovery.py).
_DOTCLAUDE = "." + "claude"

# The leaf FILENAMES a built host profile contains per skill dir. Not a guess and not a
# hand-maintained list of two: `build-distributions.ps1` writes SKILL.md and core.md AND
# `build_step_verdict.py` into the consumer skill dir (repointing the core body's
# `../../_shared/build_step_verdict.py` citation to match). An earlier revision claimed
# "exactly these two leaves", which was false, and would have called a `_shared/**`
# citation of `../build-step/build_step_verdict.py` dangling even though it ships.
# `test_shipped_leaves_matches_a_real_build` compares this against a real build instead of
# asserting the literal against itself.
SHIPPED_LEAVES = ("SKILL.md", "core.md", "build_step_verdict.py")

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
_BACKTICK_RE = re.compile(r"`([^`\n]+)`")
# A bare (non-link, non-backtick) token anchored relatively or at the `_shared/` root.
# IGNORECASE affects exactly one thing in this pattern -- the literal `_shared` -- so a
# `_Shared/x.md` prose token is extracted rather than silently skipped; the character
# classes are already case-complete. See `is_owned_namespace` for why casing matters.
_BARE_RE = re.compile(
    r"(?<![\w`/\\.-])((?:\.{1,2}[\\/]|_shared[\\/])[\w./\\-]*)", re.IGNORECASE)

# Host-home-anchored citations into an owned namespace. Out of the resolution scope
# above, but COUNTED: re-anchoring `../../references/x` to a home path would otherwise
# retire a class-(b) entry without repairing anything. The owned namespace may sit
# ANYWHERE inside the home-anchored path -- requiring it as the second segment left
# `<dot>claude/skills/_shared/judge-core.md`, the most natural re-anchoring of a
# `_shared` citation for a Claude consumer home, evading the ceiling entirely.
_HOME_DOC_CITATION_RE = re.compile(
    r"(?:" + re.escape(_DOTCLAUDE) + r"|~|[A-Za-z]:)[\\/][^\s`)\]]*?(?:"
    + "|".join(OWNED_NAMESPACES) + r")[\\/]", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Pure reference-extraction / resolution helpers (the red-on-garbage anchors
# below call these directly on synthetic inputs)
# --------------------------------------------------------------------------- #

def clean_ref(raw):
    """Reduce a raw candidate token to its path core (see module docstring)."""
    tok = raw.strip()
    if not tok:
        return ""
    tok = tok.strip("`\"'<>()[]")
    parts = tok.split()
    tok = parts[0] if parts else ""
    tok = tok.split("#")[0].split("::")[0]
    tok = tok.replace("\\", "/")
    return tok.rstrip(".,;:)\"'`")


def candidate_cores(raw, form):
    """Every path core a raw token carries.

    A backtick span is frequently a COMMAND (`python ../../_shared/x.py --flag`), so it
    can carry a reference in any position. Keeping only the first token dropped such a
    reference AND left `refs_extracted` unchanged, hiding the loss from the
    assertions and from every count floor alike -- while the identical text inside a
    fenced block was detected as a bare reference. Link and bare tokens cannot contain
    whitespace by construction, so this is a no-op for them.
    """
    if form != "backtick":
        core = clean_ref(raw)
        return [core] if core else []
    out, seen = [], set()
    for tok in raw.split():
        core = clean_ref(tok)
        if core and core not in seen:
            seen.add(core)
            out.append(core)
    return out


def first_named_segment(core):
    """First segment that names something -- `.`, `..`, `~` and a drive skipped."""
    for seg in core.split("/"):
        if seg in ("", ".", "..", "~") or re.fullmatch(r"[A-Za-z]:", seg):
            continue
        return seg
    return ""


def names_a_namespace_only(core):
    """True when the token ENDS at an owned namespace directory.

    `# _shared/` is the H1 of `_shared/README.md`; "a `_shared/` entry" is prose naming
    the directory. Neither is a reference to a path, and neither can ever be repaired,
    so freezing them would put two permanently unrepairable entries in the allowlist.

    Applied to NON-LINK forms only -- see the caller. A link destination is never prose.
    """
    tail = core.rstrip("/").split("/")[-1]
    return is_owned_namespace(tail)


def is_reference_in_scope(core, form):
    """True when `core` is a reference this gate must resolve. See module docstring."""
    if not core or any(c in core for c in "<>*"):
        return False  # template / glob placeholder
    if form != "link" and names_a_namespace_only(core):
        # The namespace named in prose, not a path reference. NOT applied to links: a
        # link DESTINATION is never prose, and de-scoping links here would let a step
        # retire `[step authoring](../../references/step-authoring.md)` by truncating it
        # to `[references](../../references/)` instead of repairing it. Measured when
        # this gate was written: no live reference in either tree has a namespace tail in
        # any form, so the form gate moved no count and no entry.
        return False
    if core.startswith(("./", "../")):
        if form == "link":
            return True
        return is_owned_namespace(first_named_segment(core))
    if core.lower().startswith("_shared/"):
        return True
    return False


def extract_references(text):
    """Every candidate reference as (raw_token, form, offset).

    Bare matches falling inside a link or backtick span are dropped, so each
    occurrence is attributed to exactly one form.
    """
    out, covered = [], []
    for m in _LINK_RE.finditer(text):
        covered.append(m.span())
        out.append((m.group(1), "link", m.start(1)))
    for m in _BACKTICK_RE.finditer(text):
        covered.append(m.span())
        out.append((m.group(1), "backtick", m.start(1)))
    for m in _BARE_RE.finditer(text):
        start = m.start(1)
        if any(a <= start < b for a, b in covered):
            continue
        out.append((m.group(1), "bare", start))
    return out


def ships_into_discovery_root(target):
    """Does `target` (root-relative POSIX) name something a built profile contains?

    Only applied where the root is the REPO ROOT, which additionally carries `tools/`,
    `config/`, `runtime/`, `documentation/`, `tests/` and the legacy `<skill>/scripts/`
    subtrees -- none of which reach a discovery root. Without this,
    `_shared/score-skill.md -> ../skill-eval-setup/scripts/generate_bad_examples.py`
    resolves against repo content and the gate calls a reference that dangles in every
    consumer home fine. `_shared/**` counts as shipping: Step 64 emits it into both
    profiles, which is also when a profile-side cross-check becomes possible.
    """
    parts = target.split("/")
    if parts[0] == "_shared":
        return True
    return len(parts) == 2 and parts[1] in SHIPPED_LEAVES


def resolve_reference(file_dir, root, core, shipped_only=False):
    """Resolve `core` from `file_dir`; return (target, dangle_reason_or_None).

    `target` is the resolution relative to `root`, POSIX-normalized, machine
    independent (it carries `..` segments when the reference escapes the root, so a
    dist tree built under any temp directory produces identical bytes).
    """
    resolved = (Path(file_dir) / core).resolve()
    root = Path(root).resolve()
    target = Path(os.path.relpath(str(resolved), str(root))).as_posix()
    try:
        resolved.relative_to(root)
    except ValueError:
        return target, "escapes the discovery root"
    if not resolved.exists():
        return target, "no such path in the tree"
    if not resolved.is_file():
        # `exists()` accepts ANY filesystem node, so `mkdir _shared/judge-core.md`
        # satisfied it. That was cosmetic while this only fed the dangling report; it is
        # now the EVIDENCE for assertion 4's `repaired` verdict, so a directory named
        # after the target would prove a repair that repairs nothing -- and would move
        # `refs_resolving` UP, buying slack against the one remaining refs floor.
        # Measured before narrowing this: all 112 canonical resolving references and
        # every profile-side one resolve to a FILE, 0 to a directory, so this moved no
        # count and no entry. A reader clicking the citation needs a document.
        return target, "resolves to a directory, not a file"
    # Windows `exists()` is case-insensitive, and `Path.resolve()` rewrites the result
    # to the on-disk casing -- so a mis-cased citation resolves on the build host and
    # dangles on every case-sensitive consumer home (Linux/macOS Claude Code and
    # Copilot CLI). That is the exact host-parity class this phase exists to repair.
    # Only reported when the two spellings differ by case ALONE, so a junction or
    # symlink resolving elsewhere cannot be mistaken for a casing defect.
    requested = os.path.normpath(os.path.join(str(Path(file_dir)), core))
    if (requested != str(resolved)
            and os.path.normcase(requested) == os.path.normcase(str(resolved))):
        return target, "case does not match the on-disk name"
    if shipped_only and not ships_into_discovery_root(target):
        return target, "resolves only against repo content that does not ship"
    return target, None


def classify_reference(core):
    """The plan's class enum, plus `profile_layout` (see below)."""
    # Case-folded for the same reason scope membership is: a mis-cased `_Shared/x.md` is
    # the same citation, and classifying it into the residual bucket instead would let a
    # case flip move an entry's recorded `class` (assertion 3's drift check).
    seg = first_named_segment(core).lower()
    relative = core.startswith(("./", "../"))
    if seg == "_shared":
        return "shared_anchored" if relative else "shared_bare"
    if seg == "references":
        return "references_anchored"
    if seg == "rules":
        return "rules_anchored"
    if seg == "docs":
        # Named for the plan's enum. NOT the same concept as _HOME_DOC_CITATION_RE
        # above, which matches a literal host-home prefix; these are relative tokens
        # escaping toward the workspace's docs/ tree.
        return "home_anchored"
    # SIXTH class, added to the plan's five by measurement, and the residual bucket:
    # a relative reference to a SIBLING path that exists in this repository's layout
    # but not in a shipped one. Six entries / seven occurrences today -- five
    # profile-side (three judge-motion/SKILL.md depth-3 sibling links plus the two
    # `../context-slim/providers/claude.md` links, which break because a profile
    # flattens providers/ into SKILL.md and has nothing above its root) and one
    # canonical (`_shared/score-skill.md` citing `../<skill>/scripts/...`, a repo-only
    # subtree no profile contains -- see `ships_into_discovery_root`). The per-entry
    # `reason` distinguishes them; this class does not. Reported, not repaired, here.
    return "profile_layout"


# --------------------------------------------------------------------------- #
# File enumeration -- git-tracked inside the work tree, filesystem walk outside it
# --------------------------------------------------------------------------- #

def is_markdown_name(name):
    """ONE markdown predicate, shared by both enumeration halves.

    `.lower().endswith(".md")`, not `rglob("*.md")` and not `Path(...).suffix`: pathlib
    compiles glob patterns case-insensitively on Windows and case-sensitively on POSIX, so
    a `NOTES.MD` would change `files_scanned` by platform and could red the frozen floor
    on a POSIX runner -- and `Path(".md").suffix` is `""`, so the two halves disagreed
    about a file named exactly `.md`. Two spellings of one predicate is two answers.
    """
    return name.lower().endswith(".md")


def decode_ls_files(stdout_bytes, repo_root):
    """Markdown paths from a `git ls-files -z` byte stream.

    `-z` exists so paths arrive as raw, unquoted bytes, and git's path encoding is UTF-8.
    Decoding them with the locale codec (`text=True` -> cp1252 on the supported host)
    mojibakes a non-ASCII filename into a path that is not on disk, and `errors="replace"`
    makes it worse: for the five bytes undefined in cp1252 it substitutes U+FFFD instead
    of raising, turning a loud UnicodeDecodeError into a silently wrong path. Decode as
    UTF-8, explicitly, and let a genuinely undecodable stream raise.
    """
    return [repo_root / rel for rel in
            (chunk.decode("utf-8") for chunk in stdout_bytes.split(b"\0") if chunk)
            if is_markdown_name(rel)]


_PYTEST_TMP_OWNER_RE = re.compile(r"pytest-of-[^\\/]+")


def _neutralize_machine_paths(text, out_dir=None):
    """Strip machine-local absolute paths out of text bound for a pytest report.

    An exact `str.replace` was not enough: PowerShell can echo the same directory in a
    spelling that does not match byte for byte (different casing, an extended-length
    `\\\\?\\` prefix, a forward-slash form), and the SYSTEM temp root also reaches the
    report through paths this one substitution never covered.

    `out_dir` is optional because this is not only the builder's echo: the enumeration's
    index-vs-worktree failure below composes ABSOLUTE paths and fires in the ordinary
    edit-then-test loop -- i.e. routinely, in exactly the Steps 64/66 workflow -- so its
    message is one an operator pastes into a public issue. `REPO_ROOT` and the system
    temp root are therefore always probed, longest spelling first so a nested directory
    is replaced by the more specific placeholder rather than being half-substituted.
    `pytest-of-<user>` is scrubbed separately: it sits BELOW the temp root, so
    neutralizing the root alone would leave the account name behind.
    """
    probes = [(str(REPO_ROOT), "<repo>"), (str(Path(REPO_ROOT).resolve()), "<repo>"),
              (tempfile.gettempdir(), "<tmp>"),
              (str(Path(tempfile.gettempdir()).resolve()), "<tmp>")]
    if out_dir is not None:
        probes += [(str(out_dir), "<tmp>"), (str(Path(out_dir).resolve()), "<tmp>")]
    spellings = [(s, placeholder) for probe, placeholder in probes if probe
                 for s in (probe, probe.replace("\\", "/"))]
    for spelling, placeholder in sorted(spellings, key=lambda p: -len(p[0])):
        text = re.sub(re.escape(spelling), placeholder, text, flags=re.IGNORECASE)
    return _PYTEST_TMP_OWNER_RE.sub("pytest-of-<user>", text)


def require_present_in_worktree(paths):
    """`git ls-files` reads the INDEX; fail loudly when the worktree disagrees.

    Delete a markdown file and run the gate before staging the deletion -- the ordinary
    edit-then-test loop, and precisely what D-63-A's "dropped" disposition looks like --
    and the index still lists it. Left alone, `scan_file` dies inside `read_text` with a
    bare FileNotFoundError instead of any of the worded messages this module composes.

    Filtering the absent paths out instead would ALSO swallow a mis-decoded path
    (`decode_ls_files` above), silently narrowing the scan to whatever still resolved --
    a narrowing with no signal, which is the one outcome this file exists to prevent. So:
    report, never filter.
    """
    missing = [p for p in paths if not p.is_file()]
    if missing:
        raise AssertionError(
            f"{len(missing)} path(s) are in the git index but not in the worktree, so "
            "the scan cannot enumerate what it is supposed to grade. Stage your "
            "deletions before running the gate (this is not filtered out on purpose -- "
            "dropping absent paths would hide a narrowed or mis-decoded enumeration):\n"
            # These are `repo_root / rel`, i.e. ABSOLUTE, and this message lands in a
            # pytest report headed for a public issue in a public repository.
            + "\n".join(_neutralize_machine_paths(str(p)) for p in missing[:10]))
    return paths


def _tracked_markdown(base_dir, repo_root):
    """git-tracked *.md under `base_dir`, or None when git did not answer for THIS tree.

    Returns None -- meaning "fall back to the filesystem walk" -- for every case that is
    not a positive, non-empty answer about `repo_root`'s own index:

      * git is unavailable, or the subprocess failed/timed out. Degrades toward the WIDER
        walk, which can never silently narrow the scan: an untracked file then shows up
        as a NEW dangling reference rather than vanishing.
      * `base_dir` is outside `repo_root` (a built profile, a synthetic fixture).
      * `git rev-parse --show-toplevel` is not `repo_root`. `tools/release.ps1` stages
        into `<repo>\\release-stage` and runs this suite from there, so `REPO_ROOT` is the
        stage while git still answers for the OUTER repository -- whose paths do not exist
        under the stage, zeroing the canonical scan.
      * git answered with nothing. An empty result is the ABSENCE of an answer, not an
        answer of "no files": a gitignored `dist/` or an in-repo scratch tree returns `[]`
        while its markdown sits on disk. `[]` was previously accepted as authoritative.
    """
    if GIT is None:
        return None
    repo_root = Path(repo_root).resolve()
    try:
        rel = Path(base_dir).resolve().relative_to(repo_root)
    except ValueError:
        return None
    try:
        toplevel = subprocess.run(
            [GIT, "-C", str(repo_root), "rev-parse", "--show-toplevel"],
            capture_output=True, timeout=60, check=True).stdout
        if Path(toplevel.decode("utf-8").strip()).resolve() != repo_root:
            return None
        out = subprocess.run(
            [GIT, "-C", str(repo_root), "ls-files", "-z", "--", rel.as_posix()],
            capture_output=True, timeout=60, check=True).stdout
    except (OSError, ValueError, UnicodeDecodeError, subprocess.SubprocessError):
        return None
    files = decode_ls_files(out, repo_root)
    if not files:
        return None
    return sorted(require_present_in_worktree(files), key=lambda p: p.as_posix())


def markdown_files(base_dir, repo_root=REPO_ROOT):
    """Every markdown file this gate scans under `base_dir`.

    `repo_root` is a parameter so the enumeration's failure modes can be regression-tested
    against a synthetic git repository in `tmp_path` without planting anything in this
    checkout -- a stray file at a real discovery path is its own defect class here.
    """
    tracked = _tracked_markdown(base_dir, repo_root)
    if tracked is not None:
        return tracked
    return sorted((p for p in Path(base_dir).rglob("*")
                   if p.is_file() and is_markdown_name(p.name)),
                  key=lambda p: p.as_posix())


def scan_file(md_path, root, source_rel, shipped_only=False):
    """(entries, in_scope_refs_by_form, resolving_count) for one markdown file."""
    text = md_path.read_text(encoding="utf-8-sig", errors="replace")
    entries, in_scope, resolving = [], {"link": 0, "backtick": 0, "bare": 0}, 0
    for raw, form, offset in extract_references(text):
        for core in candidate_cores(raw, form):
            if not is_reference_in_scope(core, form):
                continue
            in_scope[form] += 1
            target, reason = resolve_reference(md_path.parent, root, core,
                                               shipped_only=shipped_only)
            if reason is None:
                resolving += 1
                continue
            entries.append({
                "source": source_rel,
                "raw": core,
                "target": target,
                "form": form,
                "class": classify_reference(core),
                "line": text.count("\n", 0, offset) + 1,
                "reason": reason,
            })
    return entries, in_scope, resolving


def scan_tree(base_dir, root, source_prefix, shipped_only=False, repo_root=REPO_ROOT):
    """Scan every markdown file under `base_dir`. Returns a dict of scan results.

    `source_prefix` is prepended to each path relative to `base_dir`, so a profile
    built into a throwaway directory still records `dist/<provider>/...`.

    `refs_resolving` is the floored count -- in-scope references that RESOLVE. See "THE
    REMAINING FLOORS" in the module docstring for why the floor is on this population and
    not on `refs_extracted`, which every sanctioned disposition decrements.
    """
    base_dir = Path(base_dir)
    files = markdown_files(base_dir, repo_root=repo_root)
    entries = []
    by_form = {"link": 0, "backtick": 0, "bare": 0}
    resolving = 0
    for md in files:
        rel = md.relative_to(base_dir).as_posix()
        found, counts, ok = scan_file(md, root, source_prefix + rel,
                                      shipped_only=shipped_only)
        entries.extend(found)
        resolving += ok
        for form, n in counts.items():
            by_form[form] += n
    return {"entries": entries, "files_scanned": len(files),
            "refs_extracted": sum(by_form.values()), "forms_extracted": by_form,
            "refs_resolving": resolving}


def entry_key(entry):
    """(source, raw, form) -- `line` is deliberately NOT part of the key."""
    return (entry["source"], entry["raw"], entry["form"])


def dedupe(entries):
    """Collapse repeat occurrences of one key; keep the first line, count the rest."""
    out = {}
    for e in entries:
        key = entry_key(e)
        if key in out:
            out[key]["occurrences"] += 1
            continue
        rec = dict(e)
        rec["occurrences"] = 1
        out[key] = rec
    return [out[k] for k in sorted(out)]


# --------------------------------------------------------------------------- #
# PINNED RESOLUTION ROOTS. `(base_dir, root, source_prefix, shipped_only)`.
# The one parameter no count floor can see -- see the module docstring's resolution
# model and `test_escaping_reference_is_dangling_even_though_it_resolves`.
#
# ALSO the single source of the `source_prefix` -> (root, shipped_only) map that
# assertion 4 re-resolves a retired entry through (`frozen_source_spec`). One map, so a
# retirement can never be proven against a root the live scan does not use.
#
# "canonical" is this repository's word for the non-profile side (CLAUDE.md: "the
# canonical skills/ source tree") and is the only spelling used here, including in the
# frozen record's floor keys.
# --------------------------------------------------------------------------- #

CANONICAL_ROOTS = (
    (SKILLS_DIR, SKILLS_DIR, "skills/", False),
    (SHARED_DIR, REPO_ROOT, "_shared/", True),
)


def profile_scan_root(dist_root, provider):
    """(base_dir, root, source_prefix, shipped_only) for one built profile.

    The profile IS the discovery root: a consumer home has nothing above it, so the
    root can never be widened past the profile directory itself.
    """
    profile = Path(dist_root) / provider
    return profile, profile, "dist/" + provider + "/", False


def _merge_scans(parts):
    return {
        "entries": dedupe([e for p in parts for e in p["entries"]]),
        "files_scanned": sum(p["files_scanned"] for p in parts),
        "refs_extracted": sum(p["refs_extracted"] for p in parts),
        "refs_resolving": sum(p["refs_resolving"] for p in parts),
        "forms_extracted": {f: sum(p["forms_extracted"][f] for p in parts)
                            for f in ("link", "backtick", "bare")},
    }


def scan_canonical_trees():
    """skills/ and _shared/ -- always available, never skipped."""
    return _merge_scans([scan_tree(*spec) for spec in CANONICAL_ROOTS])


def build_profiles(out_dir):
    """Build both host profiles into `out_dir` via the production builder."""
    result = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(BUILD_SCRIPT),
         "-OutputDir", str(out_dir), "-Provider", "both"],
        capture_output=True, text=True, errors="replace", timeout=600)
    if result.returncode != 0:
        # Bounded and path-neutralized: this text lands in a pytest report an operator
        # pastes into a public issue, and -OutputDir is a machine-local temp path.
        tail = "\n".join((result.stdout + "\n" + result.stderr).splitlines()[-20:])
        raise AssertionError(
            "build-distributions.ps1 failed, so profile-side link coverage would "
            f"vanish (rc={result.returncode}); last 20 lines:\n"
            + _neutralize_machine_paths(tail, out_dir))
    return Path(out_dir)


def scan_profiles(dist_root):
    """Both built profiles, keyed `dist/<provider>/...` regardless of build location."""
    parts, per_profile = [], {}
    for provider in PROFILES:
        spec = profile_scan_root(dist_root, provider)
        assert spec[0].is_dir(), f"profile not built: {provider}"
        r = scan_tree(*spec)
        parts.append(r)
        per_profile[provider] = r["files_scanned"]
    merged = _merge_scans(parts)
    merged["per_profile_files"] = per_profile
    return merged


def count_home_anchored_doc_citations():
    """Occurrences of a host-home-anchored citation into an owned namespace."""
    total = 0
    for base in (SKILLS_DIR, SHARED_DIR):
        for md in markdown_files(base):
            total += len(_HOME_DOC_CITATION_RE.findall(
                md.read_text(encoding="utf-8-sig", errors="replace")))
    return total


# --------------------------------------------------------------------------- #
# The frozen baseline (link_baseline.json) -- digest-pinned, see TAMPER-EVIDENCE
# --------------------------------------------------------------------------- #

def normalized_baseline_bytes():
    """Baseline bytes with the BOM stripped and CRLF collapsed to LF.

    Same normalization `tools/release.ps1` checksums with, so the digest is identical
    on a CRLF working tree and on a fresh POSIX clone.
    """
    data = BASELINE_PATH.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.replace(b"\r\n", b"\n")


def load_baseline():
    with open(BASELINE_PATH, encoding="utf-8-sig") as f:
        return json.load(f)


def baseline_keys(baseline):
    return {(e["source"], e["raw"], e["form"]) for e in baseline["entries"]}


def baseline_entries_by_key(baseline):
    return {(e["source"], e["raw"], e["form"]): e for e in baseline["entries"]}


def is_profile_key(key):
    return key[0].startswith("dist/")


# --------------------------------------------------------------------------- #
# ASSERTION 4 -- the retirement proof. See "WHY ASSERTION 4 EXISTS" in the module
# docstring. This is the primary anti-narrowing control; the floors are secondary.
#
# The presence half is DELIBERATELY self-contained: `_citation_occurrences` below uses
# nothing but `re` and the frozen record. It does NOT call `extract_references`,
# `candidate_cores`, `clean_ref`, `names_a_namespace_only` or `is_reference_in_scope` --
# those are exactly the predicates a detector narrowing edits, and routing the proof
# through them would let one edit hide both the reference and the evidence that it is
# still there. That independence is the property this control rests on, so the two
# boundary regexes below are duplicated on purpose rather than shared with `_BARE_RE`.
# --------------------------------------------------------------------------- #

# A character that CONTINUES a path token. If one of these sits immediately before an
# occurrence, that occurrence is part of a longer path, not a citation in its own right.
_PATH_CHAR_BEFORE = re.compile(r"[\w./\\~-]")
# ...and immediately after. `.`, `#`, `:` and `)` are NOT here: `raw` is the token
# reduced to its path core, so a real citation is routinely followed by a `#fragment`,
# a `::symbol`, a closing paren, or a sentence period.
_PATH_CHAR_AFTER = re.compile(r"[\w/\\-]")


def _occurrence_spans(text, token):
    """(start, end) of every occurrence of `token` in `text`, in both slash spellings.

    CASE-INSENSITIVE, for the reason `is_owned_namespace` gives: re-casing a citation
    changes no byte a reader can act on, it just breaks the citation on a case-sensitive
    consumer home. A case-sensitive test read `../../References/x.md` as proof that
    `../../references/x.md` had been removed, which retired the entry while the broken
    citation shipped.
    """
    spans = set()
    for spelling in (token, token.replace("/", "\\")):
        for m in re.finditer(re.escape(spelling), text, flags=re.IGNORECASE):
            spans.add(m.span())
    return sorted(spans)


def _stands_alone(text, span):
    """True when the occurrence at `span` is delimited the way a citation is.

    A link destination (`](...)`), a backtick span, and a bare prose token all end at a
    non-path character on both sides; a substring of a LONGER path does not.
    """
    start, end = span
    if start and _PATH_CHAR_BEFORE.match(text[start - 1]):
        return False
    if end < len(text) and _PATH_CHAR_AFTER.match(text[end]):
        return False
    return True


def _citation_occurrences(text, raw, frozen_siblings=()):
    """How many times `raw` is still CITED in `text` -- not how many times its bytes appear.

    A plain substring test answers the wrong question, and answers it wrongly in the one
    direction that obstructs sanctioned work. 23 of the 149 frozen entries have a `raw`
    that is a strict substring of ANOTHER frozen `raw` in the SAME file, because the
    repository's own house style writes the short token as the label of the long one:

        [`_shared/judge-core.md`](../../_shared/judge-core.md)
         ^ frozen shared_bare entry     ^ frozen shared_anchored entry, contains the first

    Fixing the LABEL and leaving the destination alone is the minimal correct repair for
    the bare one -- and under a substring test its bytes are still "present" (inside the
    destination), so the proof reported UNDISPOSED, i.e. "you deleted an entry without
    repairing it", which was provably false and had NO legal remedy: the step cannot
    remove a substring that belongs to a different citation it is not disposing of.

    An occurrence is therefore discounted only when ALL THREE of these hold:
      * it is not delimited like a citation (`_stands_alone`), and
      * it lies entirely inside an occurrence of a LONGER `raw` frozen for the same
        source -- i.e. some other frozen entry already accounts for those bytes, and
        that entry carries its own assertion-3 or assertion-4 obligation, and
      * THAT LONGER SIBLING DID NOT GAIN OCCURRENCES. Its CURRENT cited count must be
        `<=` the `cited_occurrences` frozen for it in the digest-pinned record.

    The third clause is the RE-SPELLING GATE, and it is here because the first two are
    not the bound an earlier revision of this docstring claimed. Absorbing a short raw
    into a longer frozen sibling was framed as "a link label was shortened"; it is
    satisfied just as exactly by RE-SPELLING the short citation into the long one --
    `` `_shared/score-skill.md` `` -> `` `../../_shared/score-skill.md` `` -- which
    repairs nothing (the anchored form dangles too) yet made every occurrence of the
    short raw non-stand-alone and covered, so the entry retired fully green. Measured on
    `skills/skill-iterate/core.md`: 7 re-spellings retired 3 entries and repaired 0
    references, and the same shape was available on all 23 substring-sibling entries.

    Occurrence provenance separates the two. Shortening a LABEL leaves the destination
    citation untouched, so the longer sibling's count does not move. RE-SPELLING MOVES
    OCCURRENCES INTO the longer sibling, so its count goes UP -- in the measured attack,
    14 -> 21. A sibling that grew is not "already accounting for" those bytes; it just
    swallowed them. So it buys no discount, the short raw still counts as cited, and the
    entry reds as UNDISPOSED.

    This is a per-entry PROVENANCE check, not a count budget: nothing here is summed
    across entries, no global floor moves, and burning an entry down never grants slack
    anywhere else. (The budget that WAS tried and defeated is described in the module
    docstring; it is not being reintroduced.)

    Stated as the narrowing it still is, because it IS one: bytes discounted here were
    counted before, and what it gives up is now bounded to the three-clause conjunction.
    Re-spelling a citation so it is no longer stand-alone WITHOUT a containing frozen
    sibling -- `<x>/../../_shared/j.md`, or one more `../` -- still counts as present and
    still reds. `frozen_siblings` is read from the digest-pinned frozen record, which a
    step may not author, so neither the sibling set NOR the comparand count can be
    manufactured.

    What this does NOT close, plainly: the gate is `<=`, so a sibling whose count is
    unchanged still grants the discount. An edit that re-spells one short citation into
    the long form AND removes one pre-existing long citation in the same file holds the
    long count flat and would still retire the short entry. That is a strictly harder,
    two-sided edit which also destroys a citation the step is not disposing of (leaving
    the long entry's own assertion-3 obligation to answer for it), but it is not
    mechanically impossible and it is not claimed to be.

    `frozen_siblings` is a MAPPING `{frozen raw -> frozen cited_occurrences}`. A sibling
    with no frozen count grants no discount -- unknown provenance is treated as growth,
    which errs toward UNDISPOSED rather than toward a silent retirement.
    """
    if frozen_siblings and not isinstance(frozen_siblings, dict):
        raise TypeError(
            "frozen_siblings must be a mapping {frozen raw -> frozen cited_occurrences}. "
            "A bare collection of raws cannot answer 'did this sibling GAIN occurrences', "
            "which is the whole re-spelling gate, and accepting one silently would "
            "reopen the hole this parameter exists to close.")
    covering = []
    for sib in frozen_siblings:
        if len(sib) <= len(raw):
            continue
        spans = _occurrence_spans(text, sib)
        if not spans:
            continue
        frozen = frozen_siblings.get(sib)
        # Recursion terminates: a covering sibling is STRICTLY longer, and the sibling
        # set is finite, so each level draws from a strictly shorter candidate list.
        if frozen is None or _citation_occurrences(text, sib, frozen_siblings) > frozen:
            continue
        covering.extend(spans)
    total = 0
    for start, end in _occurrence_spans(text, raw):
        if _stands_alone(text, (start, end)):
            total += 1
        elif not any(a <= start and end <= b for a, b in covering):
            total += 1
    return total


def frozen_siblings_for(baseline, source_rel):
    """`{frozen raw -> frozen cited_occurrences}` for every entry against `source_rel`.

    Both halves of the discount above -- the attribution set AND the growth comparand --
    read from the same digest-pinned record, so a step cannot manufacture either.

    `cited_occurrences` is a property of (source, raw), not of a frozen KEY: two entries
    that differ only in `form` cite the SAME token, and `_citation_occurrences` counts
    the token, so both carry the same number. Collapsing them here is that identity, not
    a dedup that loses information.
    """
    out = {}
    for e in baseline["entries"]:
        if e["source"] == source_rel:
            out[e["raw"]] = e.get("cited_occurrences")
    return out


def cited_occurrences_for_text(text, raws):
    """`{raw -> cited count}` for one file, resolved longest-first.

    The FREEZE-TIME half of the growth gate, and the definition `cited_occurrences` in
    the frozen record means. Longest-first is what makes it self-consistent: when `raw`
    is measured, every strictly longer sibling already has its count in `counts`, so the
    gate compares each sibling against the value just computed for it, passes, and the
    discount applies exactly as it does with no gate at all. Re-running this over an
    UNCHANGED tree therefore reproduces the frozen numbers -- the property that lets a
    later `>` mean "this sibling gained occurrences" and nothing else.
    """
    counts = {}
    for raw in sorted(set(raws), key=len, reverse=True):
        counts[raw] = _citation_occurrences(text, raw, counts)
    return counts


def frozen_source_spec(source_rel, dist_root=None, canonical_roots=None):
    """(file_path, root, shipped_only) for a FROZEN entry's `source`, or None.

    Derived from `CANONICAL_ROOTS` / `profile_scan_root` -- the same pinned map the live
    scan uses, so a retirement can never be proven against a root the scan does not use.
    `canonical_roots` is injectable ONLY so the red-on-garbage anchor can point the proof
    at a synthetic tree; production callers pass nothing.
    """
    for base, root, prefix, shipped in (canonical_roots or CANONICAL_ROOTS):
        if source_rel.startswith(prefix):
            return Path(base) / source_rel[len(prefix):], root, shipped
    if dist_root is not None:
        for provider in PROFILES:
            base, root, prefix, shipped = profile_scan_root(dist_root, provider)
            if source_rel.startswith(prefix):
                return Path(base) / source_rel[len(prefix):], root, shipped
    return None


def annotate_cited_occurrences(entries, dist_root=None, canonical_roots=None):
    """Stamp each entry with `cited_occurrences` -- its citation count AT FREEZE TIME.

    The comparand the re-spelling gate needs, and the one number that cannot be derived
    later: once a step has edited the tree, "how many times was this token cited before"
    is unrecoverable. It is recorded per entry rather than as a total precisely so the
    check stays per-entry provenance and never becomes a budget.

    It is NOT the same number as `occurrences`, and the difference is load-bearing.
    `occurrences` is a SCAN count keyed `(source, raw, form)`; `cited_occurrences` is a
    `_citation_occurrences` count keyed `(source, raw)`, so it sums across forms. On
    `skills/skill-iterate/core.md`, `../../_shared/score-skill.md` is frozen twice --
    `backtick` 7 and `link` 7 -- and is cited 14 times. Gating growth against the
    per-form 7 would report a 14 > 7 "gain" on an untouched file and false-RED every
    label fix in that file. The count must be measured by the same predicate that later
    re-measures it.

    Read through `frozen_source_spec`, the same pinned root map assertion 4 proves
    retirements against, so the freeze and the re-measurement can never disagree about
    which file a `source` names.
    """
    by_source = {}
    for e in entries:
        by_source.setdefault(e["source"], []).append(e)
    for source, group in sorted(by_source.items()):
        spec = frozen_source_spec(source, dist_root, canonical_roots)
        if spec is None:
            raise SystemExit(
                f"no pinned resolution root covers {source!r}, so its entries would be "
                "frozen with no citation count and every sibling discount in that file "
                "would be denied for want of a comparand.")
        text = spec[0].read_text(encoding="utf-8-sig", errors="replace")
        counts = cited_occurrences_for_text(text, [e["raw"] for e in group])
        for e in group:
            e["cited_occurrences"] = counts[e["raw"]]
    return entries


def disposition_of(entry, dist_root=None, canonical_roots=None, frozen_siblings=()):
    """(verdict, detail) for a frozen entry the allowlist claims to have RETIRED.

    Verdicts: `repaired` | `removed` | `UNDISPOSED` | `UNKNOWN_ROOT`.

    Re-derived from the frozen `source` + `raw` against the CURRENT tree, deliberately
    NOT through `extract_references` / `candidate_cores` / `is_reference_in_scope`: those
    are the predicates a detector narrowing edits, and routing the proof through them
    would let the same edit hide both the reference and the evidence.

    The token-presence half is `_citation_occurrences` -- self-contained, boundary-aware
    and case-insensitive. `raw` is the token reduced to its path core, so it is asked
    "is this specific reference still CITED here", not "do these bytes appear anywhere in
    the file"; the difference is what separates a fixed link label from a deleted entry.
    `frozen_siblings` maps the other frozen `raw`s recorded for the same source to their
    frozen `cited_occurrences` (from the digest-pinned record, never from a live scan) --
    the attribution set AND the re-spelling gate, both in `_citation_occurrences`.
    """
    spec = frozen_source_spec(entry["source"], dist_root, canonical_roots)
    if spec is None:
        return "UNKNOWN_ROOT", "no pinned resolution root covers this source prefix"
    md, root, shipped = spec
    if not md.is_file():
        return "removed", "the citing file no longer exists"
    text = md.read_text(encoding="utf-8-sig", errors="replace")
    raw = entry["raw"]
    if not _citation_occurrences(text, raw, frozen_siblings):
        return "removed", "the token is no longer cited in the citing file"
    target, reason = resolve_reference(md.parent, root, raw, shipped_only=shipped)
    if reason is None:
        return "repaired", f"now resolves to {target}"
    return "UNDISPOSED", reason


def undisposed_retirements(baseline, known, profile_side, dist_root=None):
    """Frozen entries claimed retired that were neither repaired nor removed."""
    live = set(known)
    bad = []
    for key, e in sorted(baseline_entries_by_key(baseline).items()):
        if is_profile_key(key) != profile_side or key in live:
            continue
        verdict, detail = disposition_of(
            e, dist_root, frozen_siblings=frozen_siblings_for(baseline, e["source"]))
        if verdict not in ("repaired", "removed"):
            bad.append(f"  {e['source']}  {e['raw']}  ({e['form']}) -- {verdict}: {detail}")
    return bad


# --------------------------------------------------------------------------- #
# The gate arithmetic, as ONE pure function. Table-driven below against every
# gaming vector, so the three assertions Steps 64/66 are graded by have actually
# been observed to fire rather than only ever differencing empty sets.
# --------------------------------------------------------------------------- #

def evaluate_gate(detected, known, frozen):
    """Non-empty failure classes for one side. An empty dict is green."""
    return {name: keys for name, keys in (
        ("new", sorted(set(detected) - set(known))),
        ("grown", sorted(set(known) - set(frozen))),
        ("stale", sorted(set(known) - set(detected)))) if keys}


# --------------------------------------------------------------------------- #
# KNOWN_DANGLING -- today's dangling references, frozen at Step 63 and SHRINK ONLY.
#
# Emitted by this file's own `--emit` run against a real scan; never hand-counted.
# Steps 64 and 66 DELETE lines from this tuple as their fixes land -- the burn-down
# is the evidence the fix worked. Nothing may be ADDED (D7): a new key is absent from
# the frozen baseline and hard-fails assertion 2, and widening the baseline to match
# breaks the digest pin.
# --------------------------------------------------------------------------- #

# --- BEGIN GENERATED KNOWN_DANGLING ---
KNOWN_DANGLING = (
    ('_shared/judge-core.md', '_shared/calibrate_judge.py', 'backtick'),
    ('_shared/judge-core.md', '_shared/grader_prompt.py', 'backtick'),
    ('dist/claude/judge-motion/SKILL.md', '../../build-step/core.md', 'link'),
    ('dist/claude/judge-motion/SKILL.md', '../../judge-ui/core.md', 'link'),
    ('dist/claude/judge-motion/SKILL.md', '../../user-uat/core.md', 'link'),
    ('dist/claude/judge-motion/SKILL.md', '_shared/judge-core.md', 'backtick'),
    ('dist/claude/judge-ui/core.md', '_shared/judge-core.md', 'backtick'),
    ('dist/claude/review-deep/core.md', '_shared/calibrate_judge.py', 'bare'),
    ('dist/claude/review-deep/core.md', '_shared/judge-core.md', 'backtick'),
    ('dist/claude/review-gauntlet/core.md', '_shared/judge-core.md', 'backtick'),
    ('dist/claude/review-proof/core.md', '_shared/judge-core.md', 'backtick'),
    ('dist/claude/skill-eval-setup/core.md', '_shared/score-skill.md', 'backtick'),
    ('dist/claude/skill-eval-setup/core.md', '_shared/score_skill_composite.py', 'backtick'),
    ('dist/claude/skill-iterate/core.md', '../../../docs/investigations/skill-iterate-hill-climbing/06-adversarial-mutation-grader-discrimination-tests.md', 'backtick'),
    ('dist/claude/skill-iterate/core.md', '../../../docs/investigations/skill-iterate-hill-climbing/07-failed-assertion-targeted-brainstorm-prompts.md', 'backtick'),
    ('dist/claude/skill-iterate/core.md', '_shared/grader_prompt.py', 'backtick'),
    ('dist/claude/skill-iterate/core.md', '_shared/score-skill.md', 'backtick'),
    ('dist/claude/skill-iterate/core.md', '_shared/score_skill.workflow.js', 'bare'),
    ('dist/claude/skill-iterate/core.md', '_shared/score_skill_absolute.py', 'backtick'),
    ('dist/claude/user-afterparty/core.md', '../../../docs/seeds/seed_sprint_wrap.md', 'backtick'),
    ('dist/claude/user-afterparty/core.md', '../context-slim/providers/claude.md', 'link'),
    ('dist/claude/user-uat/core.md', '_shared/judge-core.md', 'backtick'),
    ('dist/gpt/judge-ui/core.md', '_shared/judge-core.md', 'backtick'),
    ('dist/gpt/review-deep/core.md', '_shared/calibrate_judge.py', 'bare'),
    ('dist/gpt/review-deep/core.md', '_shared/judge-core.md', 'backtick'),
    ('dist/gpt/review-gauntlet/core.md', '_shared/judge-core.md', 'backtick'),
    ('dist/gpt/review-proof/core.md', '_shared/judge-core.md', 'backtick'),
    ('dist/gpt/skill-eval-setup/core.md', '_shared/score-skill.md', 'backtick'),
    ('dist/gpt/skill-eval-setup/core.md', '_shared/score_skill_composite.py', 'backtick'),
    ('dist/gpt/skill-iterate/core.md', '../../../docs/investigations/skill-iterate-hill-climbing/06-adversarial-mutation-grader-discrimination-tests.md', 'backtick'),
    ('dist/gpt/skill-iterate/core.md', '../../../docs/investigations/skill-iterate-hill-climbing/07-failed-assertion-targeted-brainstorm-prompts.md', 'backtick'),
    ('dist/gpt/skill-iterate/core.md', '_shared/grader_prompt.py', 'backtick'),
    ('dist/gpt/skill-iterate/core.md', '_shared/score-skill.md', 'backtick'),
    ('dist/gpt/skill-iterate/core.md', '_shared/score_skill.workflow.js', 'bare'),
    ('dist/gpt/skill-iterate/core.md', '_shared/score_skill_absolute.py', 'backtick'),
    ('dist/gpt/user-afterparty/core.md', '../../../docs/seeds/seed_sprint_wrap.md', 'backtick'),
    ('dist/gpt/user-afterparty/core.md', '../context-slim/providers/claude.md', 'link'),
    ('dist/gpt/user-uat/core.md', '_shared/judge-core.md', 'backtick'),
    ('skills/build-phase/core.md', '../../_shared/build_step_verdict.py', 'backtick'),
    ('skills/build-phase/core.md', '../../_shared/judge-core.md', 'link'),
    ('skills/build-step/core.md', '../../_shared/build_step_verdict.py', 'backtick'),
    ('skills/build-step/core.md', '../../_shared/judge-core.md', 'link'),
    ('skills/judge-motion/providers/claude.md', '../../../_shared/judge-core.md', 'link'),
    ('skills/judge-motion/providers/claude.md', '_shared/judge-core.md', 'backtick'),
    ('skills/judge-ui/calibration-notes.md', '../../_shared/judge-core.md', 'link'),
    ('skills/judge-ui/core.md', '../../_shared/judge-core.md', 'link'),
    ('skills/judge-ui/core.md', '_shared/judge-core.md', 'backtick'),
    ('skills/review-deep/core.md', '../../_shared/judge-core.md', 'link'),
    ('skills/review-deep/core.md', '_shared/calibrate_judge.py', 'bare'),
    ('skills/review-deep/core.md', '_shared/judge-core.md', 'backtick'),
    ('skills/review-gauntlet/core.md', '../../_shared/judge-core.md', 'link'),
    ('skills/review-gauntlet/core.md', '_shared/judge-core.md', 'backtick'),
    ('skills/review-proof/core.md', '../../_shared/judge-core.md', 'link'),
    ('skills/review-proof/core.md', '_shared/judge-core.md', 'backtick'),
    ('skills/skill-eval-setup/core.md', '_shared/score-skill.md', 'backtick'),
    ('skills/skill-eval-setup/core.md', '_shared/score_skill_composite.py', 'backtick'),
    ('skills/skill-evolve/core.md', '../../_shared/score-skill.md', 'backtick'),
    ('skills/skill-evolve/core.md', '../../_shared/score-skill.md', 'link'),
    ('skills/skill-evolve/core.md', '../../_shared/score_skill.workflow.js', 'backtick'),
    ('skills/skill-evolve/core.md', '../../_shared/score_skill.workflow.js', 'link'),
    ('skills/skill-iterate/core.md', '../../../docs/investigations/skill-iterate-hill-climbing/06-adversarial-mutation-grader-discrimination-tests.md', 'backtick'),
    ('skills/skill-iterate/core.md', '../../../docs/investigations/skill-iterate-hill-climbing/07-failed-assertion-targeted-brainstorm-prompts.md', 'backtick'),
    ('skills/skill-iterate/core.md', '../../_shared/score-skill.md', 'backtick'),
    ('skills/skill-iterate/core.md', '../../_shared/score-skill.md', 'link'),
    ('skills/skill-iterate/core.md', '../../_shared/score_skill.workflow.js', 'backtick'),
    ('skills/skill-iterate/core.md', '../../_shared/score_skill.workflow.js', 'link'),
    ('skills/skill-iterate/core.md', '../../_shared/score_skill_composite.py', 'backtick'),
    ('skills/skill-iterate/core.md', '../../_shared/score_skill_composite.py', 'link'),
    ('skills/skill-iterate/core.md', '_shared/grader_prompt.py', 'backtick'),
    ('skills/skill-iterate/core.md', '_shared/score-skill.md', 'backtick'),
    ('skills/skill-iterate/core.md', '_shared/score_skill.workflow.js', 'bare'),
    ('skills/skill-iterate/core.md', '_shared/score_skill_absolute.py', 'backtick'),
    ('skills/user-afterparty/core.md', '../../../docs/seeds/seed_sprint_wrap.md', 'backtick'),
    ('skills/user-uat/core.md', '../../_shared/judge-core.md', 'link'),
    ('skills/user-uat/core.md', '_shared/judge-core.md', 'backtick'),
)
# --- END GENERATED KNOWN_DANGLING ---

KNOWN_CANONICAL = tuple(k for k in KNOWN_DANGLING if not is_profile_key(k))
KNOWN_PROFILE = tuple(k for k in KNOWN_DANGLING if is_profile_key(k))


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def canonical_scan():
    return scan_canonical_trees()


@pytest.fixture(scope="module")
def dist_root(tmp_path_factory):
    """Both profiles, built OUTSIDE the work tree, via the production builder."""
    if PWSH is None:
        pytest.skip(
            "powershell is not on PATH, so the two built profiles cannot be "
            "generated and PROFILE-SIDE LINK COVERAGE VANISHES for this run "
            f"({len(KNOWN_PROFILE)} frozen profile entries go unchecked). This "
            "repository declares Windows + PowerShell as a hard environment "
            "requirement; a run without it is not a full gate.")
    return build_profiles(tmp_path_factory.mktemp("link-dist"))


@pytest.fixture(scope="module")
def profile_scan(dist_root):
    return scan_profiles(dist_root)


# --------------------------------------------------------------------------- #
# The frozen comparand itself
# --------------------------------------------------------------------------- #

def test_frozen_baseline_exists_and_declares_itself_immutable():
    assert BASELINE_PATH.is_file(), f"missing frozen baseline: {BASELINE_PATH}"
    b = load_baseline()
    note = b.get("note", "")
    assert "no step may edit" in note.lower(), (
        "the frozen baseline must say so INSIDE itself -- it is the comparand a step "
        "does not author, and a file that does not announce that gets edited")
    assert b["generated_by"].endswith("test_link_resolution.py --emit"), b["generated_by"]
    assert isinstance(b["entries"], list) and b["entries"]
    assert len(baseline_keys(b)) == len(b["entries"]), "duplicate key in frozen baseline"


def test_frozen_baseline_is_tamper_evident():
    """`--emit` rewrites link_baseline.json in place and EVERY other assertion above
    survives the regeneration byte-identical -- measured: `note`, `generated_by` and
    `decisions` are unchanged while `entries` silently absorbs a new dangling reference
    and `scope_floor` moves. Prose inside a file cannot protect that file.

    This digest lives in a different file, so absorbing a new dangling reference takes
    three coordinated edits and the hash edit is unmistakable in review. It is
    tamper-EVIDENT, not tamper-proof: it cannot stop a step that makes all three edits,
    only stop it happening quietly.
    """
    b = load_baseline()
    assert b["counts"]["entries"] == len(b["entries"]), (
        "the frozen baseline's own counts.entries disagrees with len(entries) -- the "
        "file was hand-edited rather than regenerated")
    digest = hashlib.sha256(normalized_baseline_bytes()).hexdigest()
    assert digest == BASELINE_SHA256, (
        f"link_baseline.json changed (sha256 {digest}, pinned {BASELINE_SHA256}). It "
        "is the comparand this step's shrink-only design rests on; regenerating it "
        "retroactively legalizes any new dangling reference. Widening the frozen "
        "record is an explicit operator decision recorded in the plan (D-63-A), never "
        "a step making itself pass.")


def test_every_frozen_entry_carries_its_freeze_time_citation_count():
    """`cited_occurrences` is the re-spelling gate's comparand, so it may not be absent.

    A missing count is not a crash, it is a SILENT LOSS of the gate for that file: the
    sibling discount is denied, which errs safe, but the entry stops being able to prove
    a legitimate label fix. Either way the record is no longer what the gate assumes, so
    the shape is asserted rather than trusted.

    Also asserts the identity `frozen_siblings_for` relies on: two entries differing only
    in `form` cite the SAME token and therefore carry the SAME count. That is why the
    per-form `occurrences` field cannot stand in for this one -- on
    `skills/skill-iterate/core.md` the anchored score-skill raw is frozen twice at 7 and
    cited 14 times, so gating growth on `occurrences` would report a phantom gain on an
    untouched file.
    """
    entries = load_baseline()["entries"]
    missing = [f"{e['source']}  {e['raw']}" for e in entries
               if not isinstance(e.get("cited_occurrences"), int)
               or e["cited_occurrences"] < 1]
    assert not missing, (
        f"{len(missing)} frozen entr(ies) carry no usable cited_occurrences, so the "
        "re-spelling gate has no comparand for them:\n" + "\n".join(missing[:20]))
    by_token = {}
    for e in entries:
        by_token.setdefault((e["source"], e["raw"]), set()).add(e["cited_occurrences"])
    split = [k for k, v in by_token.items() if len(v) > 1]
    assert not split, (
        "cited_occurrences must be a property of (source, raw), not of the frozen key -- "
        f"these tokens carry more than one count: {split[:5]}")


def _normalized(text):
    """Case-folded, whitespace-collapsed -- so a line wrap is not a difference."""
    return " ".join(text.split()).lower()


def test_recorded_decisions_are_carried_in_the_frozen_baseline():
    """The two decisions Step 63 owes downstream steps, machine-checked in BOTH copies.

    Content, not prose length: an assertion that someone wrote 81 characters cannot fail
    without an edit that the digest pin already catches. And an earlier revision claimed
    to check "the two copies -- this module's docstring and the frozen record" while
    reading only the JSON, so the docstring half could drift freely. It reads both now,
    whitespace-normalized because the docstring line-wraps every phrase.

    In the steady state the digest pin reds first, so these cannot fire. Their real job
    is the one path the digest deliberately allows through: after an operator-blessed
    regeneration plus a digest update, `_emit` hardcodes this text, and these are what
    stops a restored overclaim riding along.
    """
    d = load_baseline()["decisions"]
    doc = _normalized(__doc__)
    replacement = d["D-63-A_allowlist_replacement"]
    assert replacement["permitted"] is False
    legacy = d["D-63-B_legacy_top_level_packages"]
    assert legacy["in_scope"] is False
    # short, load-bearing phrases -- a long exact sentence costs an iteration the first
    # time a later step legitimately rewords it
    for phrase, record in (("none may enter", replacement),
                           ("tamper-evident", replacement),
                           ("would be empty", legacy),
                           ("resolves today", legacy)):
        assert phrase in _normalized(record["reason"]), (
            f"the frozen record no longer carries {phrase!r}. D-63-A must state its "
            "ENFORCEMENT honestly -- an earlier revision claimed the control was "
            "mechanical, which was false while `--emit` could rewrite the record.")
        assert phrase in doc, (
            f"this module's docstring no longer carries {phrase!r}, so the two copies "
            "of the decision have drifted. The frozen record is not the only place a "
            "later step reads this contract.")


# --------------------------------------------------------------------------- #
# Assertion 2 -- KNOWN_DANGLING may only ever SHRINK
# --------------------------------------------------------------------------- #

def test_known_dangling_is_a_subset_of_the_frozen_baseline():
    frozen = baseline_keys(load_baseline())
    # detected == known isolates the "grown" class; the other two are covered by their
    # own tests against a real scan.
    grown = evaluate_gate(KNOWN_DANGLING, KNOWN_DANGLING, frozen).get("grown", [])
    assert not grown, (
        f"{len(grown)} allowlist entr(ies) are NOT in the frozen baseline -- the "
        "allowlist may only shrink (D7). Replacement is not permitted (D-63-A); "
        "repair the reference instead:\n" + "\n".join(map(str, grown[:20])))


def test_known_dangling_has_no_duplicate_keys():
    assert len(set(KNOWN_DANGLING)) == len(KNOWN_DANGLING), \
        "duplicate key in KNOWN_DANGLING -- deleting one copy would look like repair"


# --------------------------------------------------------------------------- #
# Assertions 1 + 3 -- no NEW dangling ref; every allowlisted entry STILL dangles,
# for the SAME recorded target/reason/class.
# --------------------------------------------------------------------------- #

def _describe(entries, keys):
    by_key = {entry_key(e): e for e in entries}
    return "\n".join(
        f"  {k[0]}:{by_key[k]['line']}  {k[1]}  ({k[2]}, {by_key[k]['class']}, "
        f"{by_key[k]['reason']})" for k in sorted(keys) if k in by_key)


def _record_drift(scan, known):
    """Allowlisted entries that still dangle but no longer match the frozen record."""
    frozen = baseline_entries_by_key(load_baseline())
    detected = {entry_key(e): e for e in scan["entries"]}
    fields = ("target", "reason", "class")
    out = []
    for key in sorted(set(known) & set(detected)):
        now = tuple(detected[key][f] for f in fields)
        then = tuple(frozen[key][f] for f in fields)
        if now != then:
            out.append(f"  {key[0]}  {key[1]}  {then} -> {now}")
    return out


def test_no_new_dangling_reference_in_the_canonical_tree(canonical_scan):
    detected = {entry_key(e) for e in canonical_scan["entries"]}
    new = evaluate_gate(detected, KNOWN_CANONICAL, KNOWN_CANONICAL).get("new", [])
    assert not new, (
        f"{len(new)} NEW dangling reference(s) in skills/ or _shared/. Fix the "
        "reference -- do not add it to KNOWN_DANGLING (D7, D-63-A):\n"
        + _describe(canonical_scan["entries"], new))


def test_no_new_dangling_reference_in_the_built_profiles(profile_scan):
    detected = {entry_key(e) for e in profile_scan["entries"]}
    new = evaluate_gate(detected, KNOWN_PROFILE, KNOWN_PROFILE).get("new", [])
    assert not new, (
        f"{len(new)} NEW dangling reference(s) in a built host profile. A profile "
        "reference must resolve INSIDE the profile -- a consumer home has nothing "
        "above the discovery root:\n" + _describe(profile_scan["entries"], new))


def test_every_allowlisted_canonical_entry_still_dangles(canonical_scan):
    detected = {entry_key(e) for e in canonical_scan["entries"]}
    stale = evaluate_gate(detected, KNOWN_CANONICAL, KNOWN_CANONICAL).get("stale", [])
    assert not stale, (
        f"{len(stale)} KNOWN_DANGLING entr(ies) no longer dangle. If the reference "
        "was repaired, DELETE the entry in the same commit -- a stale allowlist "
        "hides the next regression:\n" + "\n".join(map(str, stale[:20])))
    drifted = _record_drift(canonical_scan, KNOWN_CANONICAL)
    assert not drifted, (
        f"{len(drifted)} allowlisted entr(ies) still dangle but with a DIFFERENT "
        "target/reason/class than the frozen record -- the resolution model changed "
        "underneath the baseline, which is how a re-root fakes a burn-down:\n"
        + "\n".join(drifted[:20]))


def test_every_allowlisted_profile_entry_still_dangles(profile_scan):
    detected = {entry_key(e) for e in profile_scan["entries"]}
    stale = evaluate_gate(detected, KNOWN_PROFILE, KNOWN_PROFILE).get("stale", [])
    assert not stale, (
        f"{len(stale)} profile-side KNOWN_DANGLING entr(ies) no longer dangle -- "
        "delete them in the commit that repaired them:\n"
        + "\n".join(map(str, stale[:20])))
    drifted = _record_drift(profile_scan, KNOWN_PROFILE)
    assert not drifted, (
        f"{len(drifted)} profile-side entr(ies) drifted from the frozen record:\n"
        + "\n".join(drifted[:20]))


def test_gate_arithmetic_reds_on_each_gaming_vector():
    """The three assertions, exercised against data designed to make them FIRE.

    Every production use above evaluates a difference over data generated to be empty,
    so none of them had ever been observed to go red in the committed suite. Row 2 is
    the one Steps 64 and 66 cannot proceed without: a reference repaired AND its entry
    deleted in the same commit must be clean.
    """
    a = ("skills/x/core.md", "../../_shared/a.md", "link")
    b = ("skills/y/core.md", "_shared/b.py", "backtick")
    c = ("skills/z/core.md", "../../_shared/c.md", "link")
    frozen = {a, b}
    cases = (
        ({a, b}, {a, b}, None),        # steady state
        ({b}, {b}, None),              # repaired AND entry deleted -> Steps 64/66 exit
        ({b}, {a, b}, "stale"),        # repaired but entry kept (rewrite-not-delete)
        ({a, b}, {b}, "new"),          # entry deleted, ref NOT repaired -> fake burn-down
        ({a, b, c}, {a, b, c}, "grown"),  # replacement entry appended (D-63-A)
    )
    for detected, known, expect in cases:
        result = evaluate_gate(detected, known, frozen)
        assert sorted(result) == ([expect] if expect else []), (detected, known, result)


# --------------------------------------------------------------------------- #
# ASSERTION 4 -- the retirement proof. An entry leaves KNOWN_DANGLING only by being
# DISPOSED OF, and the disposition is re-derived from the immutable frozen record
# against the current tree. This is the primary anti-narrowing control: a narrowing
# leaves the token in the file AND leaves it unresolvable, satisfying neither branch.
# See "WHY ASSERTION 4 EXISTS" in the module docstring.
# --------------------------------------------------------------------------- #

_RETIREMENT_FAILURE = (
    "frozen entr(ies) have left KNOWN_DANGLING without being disposed of. A retirement "
    "must be PROVABLE: either the reference now RESOLVES (repaired), or its token is "
    "gone from the citing file (converted to prose, or dropped -- D-63-A). Each entry "
    "below still has its token sitting in the source AND still does not resolve, which "
    "is what a NARROWED DETECTOR looks like, not what a burn-down looks like. Restore "
    "the entry, or disposition the reference for real:\n")


def test_every_retired_canonical_entry_was_actually_disposed_of():
    """Nothing has been retired yet, so this population is EMPTY until Step 64 lands.

    Said out loud because an assertion that has only ever differenced empty sets is not
    known to work. Two anchors below run this same machinery over data engineered to make
    it fire: `test_retirement_proof_reds_on_an_undisposed_entry` (each verdict, synthetic
    tree) and `test_retirement_proof_fires_over_the_real_frozen_record` (this exact
    function, real entries).
    """
    bad = undisposed_retirements(load_baseline(), KNOWN_DANGLING, profile_side=False)
    assert not bad, f"{len(bad)} canonical " + _RETIREMENT_FAILURE + "\n".join(bad[:20])


def test_every_retired_profile_entry_was_actually_disposed_of(dist_root):
    """Empty until Step 64 retires a profile entry -- see the canonical twin above."""
    bad = undisposed_retirements(load_baseline(), KNOWN_DANGLING, profile_side=True,
                                 dist_root=dist_root)
    assert not bad, f"{len(bad)} profile-side " + _RETIREMENT_FAILURE + "\n".join(bad[:20])


def test_retirement_proof_fires_over_the_real_frozen_record():
    """The production aggregator, on REAL entries, engineered to fire.

    Claiming an EMPTY live allowlist says every frozen canonical entry was retired. The
    ones still IN KNOWN_DANGLING all still dangle (assertion 3) with their tokens still in
    their files, so every one of them must come back UNDISPOSED -- the exact shape of
    "narrow the detector, then delete what it stopped seeing", at full scale.

    The comparand is the LIVE allowlist, not the frozen total, on purpose: an exact count
    against the frozen record would red every time Steps 64/66 legitimately dispose of an
    entry, which is the tripwire-on-sanctioned-work mistake the budgeted floor made. This
    invariant follows the burn-down down instead -- a retired entry leaves both sides.
    """
    live = [k for k in KNOWN_DANGLING if not is_profile_key(k)]
    assert live, "no live canonical entries left -- this anchor now proves nothing"
    bad = undisposed_retirements(load_baseline(), (), profile_side=False)
    assert len(bad) == len(live), (
        f"claiming everything is retired reported {len(bad)} undisposed canonical "
        f"entries, but {len(live)} are still in KNOWN_DANGLING and every one of those "
        "still dangles, so every one must be caught")
    assert all("UNDISPOSED" in line for line in bad), bad[:5]


def test_retirement_proof_fires_over_the_real_frozen_profile_record(dist_root):
    """The canonical twin above, PROFILE side -- and the only anchor on that branch.

    `frozen_source_spec` has a second half that maps a `dist/<provider>/...` source
    through `profile_scan_root` into a freshly built profile. In the steady state
    `test_every_retired_profile_entry_was_actually_disposed_of` differences an EMPTY set,
    so no passing test executed that branch on a real entry: the whole profile half of
    the retirement proof was unexercised until the first profile retirement, which is
    Step 64. This drives it over every frozen profile entry, against a real build.
    """
    live = [k for k in KNOWN_DANGLING if is_profile_key(k)]
    assert live, "no live profile entries left -- this anchor now proves nothing"
    baseline = load_baseline()
    frozen = baseline_entries_by_key(baseline)
    for key in live:
        spec = frozen_source_spec(frozen[key]["source"], dist_root=dist_root)
        assert spec is not None, (
            f"no pinned root covers {frozen[key]['source']!r} -- the profile half of "
            "the retirement proof would credit every entry under it as UNKNOWN_ROOT")
        md, root, shipped = spec
        assert md.is_file(), (
            f"{frozen[key]['source']} does not exist in the built profile, so its "
            "disposition would be proven against a missing file")
        assert Path(root) == Path(dist_root) / frozen[key]["source"].split("/")[1], (
            "a profile IS its own discovery root; proving a retirement against a wider "
            "root would credit references a consumer home cannot resolve")
    bad = undisposed_retirements(baseline, (), profile_side=True, dist_root=dist_root)
    assert len(bad) == len(live), (
        f"claiming everything is retired reported {len(bad)} undisposed profile "
        f"entries, but {len(live)} are still in KNOWN_DANGLING and every one of those "
        "still dangles, so every one must be caught")
    assert all("UNDISPOSED" in line for line in bad), bad[:5]


def test_retirement_proof_reds_on_an_undisposed_entry(tmp_path):
    """The three dispositions and the one forgery, on a synthetic tree.

    A control never observed to fire is not known to work, and this one is now the
    load-bearing half of the gate. Each case is run through the production
    `disposition_of`, against real files, with the frozen `source`/`raw` the allowlist
    would have carried.
    """
    root = tmp_path / "skills"
    (root / "alpha").mkdir(parents=True)
    (root / "beta").mkdir()
    (root / "beta" / "core.md").write_text("beta\n", encoding="utf-8")
    here = root / "alpha"
    frozen = {"source": "skills/alpha/core.md", "raw": "../gamma/core.md",
              "form": "link"}
    roots = ((root, root, "skills/", False),)

    def disposition(entry, siblings=()):
        return disposition_of(entry, canonical_roots=roots, frozen_siblings=siblings)[0]

    # FORGERY: the citation is untouched and still dangles, but the entry was deleted --
    # exactly what "narrow the detector, then delete what it stopped seeing" leaves behind.
    (here / "core.md").write_text("see [g](../gamma/core.md)\n", encoding="utf-8")
    assert disposition(frozen) == "UNDISPOSED"

    # REPAIRED: the reference now resolves.
    (here / "core.md").write_text("see [b](../beta/core.md)\n", encoding="utf-8")
    assert disposition(dict(frozen, raw="../beta/core.md")) == "repaired"

    # REMOVED (prose conversion): the token is gone from the file.
    (here / "core.md").write_text("see the gamma core, next to this one\n",
                                  encoding="utf-8")
    assert disposition(frozen) == "removed"

    # REMOVED (file dropped).
    (here / "core.md").unlink()
    assert disposition(frozen) == "removed"

    # A source prefix no pinned root covers is never silently credited as disposed.
    assert disposition(dict(frozen, source="nowhere/core.md")) == "UNKNOWN_ROOT"

    # A DIRECTORY at the target is not a repair. `exists()` accepted any filesystem
    # node, so `mkdir` alone turned this entry fully green while the citation still
    # pointed at a directory in every consumer home -- and moved `refs_resolving` UP.
    (root / "gamma").mkdir()
    (root / "gamma" / "core.md").mkdir()
    (here / "core.md").write_text("see [g](../gamma/core.md)\n", encoding="utf-8")
    assert disposition(frozen) == "UNDISPOSED"
    # ...and the real thing at the same path IS a repair, so the case above is not
    # passing for some unrelated reason.
    (root / "gamma" / "core.md").rmdir()
    (root / "gamma" / "core.md").write_text("gamma\n", encoding="utf-8")
    assert disposition(frozen) == "repaired"


def test_retirement_proof_accepts_a_link_label_fix_and_still_reds_a_re_spelling(tmp_path):
    """The disposition Step 64 will reach for first, and the evasion next to it.

    23 of the 149 frozen entries have a `raw` that is a strict substring of another
    frozen `raw` in the SAME file, written as its link label:

        [`_shared/judge-core.md`](../../_shared/judge-core.md)

    Under a plain substring presence test, fixing the LABEL -- the minimal correct edit,
    and the spelling the repository already uses elsewhere -- left the short token's
    bytes inside the destination, so the proof reported UNDISPOSED with NO legal remedy.
    That is a tripwire on sanctioned work, and it is the reason `_citation_occurrences`
    exists. The rest of this test is what keeps that fix from becoming a hole: the same
    non-stand-alone shape WITHOUT a containing frozen sibling still reds, and -- the
    case the first revision of the discount missed -- so does RE-SPELLING the short
    citation INTO the long one, which satisfies "not stand-alone" and "inside a frozen
    sibling" exactly while repairing nothing.
    """
    root = tmp_path / "skills"
    (root / "alpha").mkdir(parents=True)
    here = root / "alpha"
    roots = ((root, root, "skills/", False),)
    short = {"source": "skills/alpha/core.md", "raw": "_shared/judge-core.md",
             "form": "backtick"}
    long_ = {"source": "skills/alpha/core.md", "raw": "../../_shared/judge-core.md",
             "form": "link"}
    # The frozen record's shape: each raw with the count it was CITED at freeze time,
    # measured on the BEFORE text below (one label citation, one destination citation).
    siblings = {short["raw"]: 1, long_["raw"]: 1}

    def disposition(entry):
        return disposition_of(entry, canonical_roots=roots, frozen_siblings=siblings)[0]

    # BEFORE: both are cited, so neither may be retired. This is also the text the
    # frozen counts above were measured on -- assert that, so the two cannot drift.
    before = "See [`_shared/judge-core.md`](../../_shared/judge-core.md).\n"
    (here / "core.md").write_text(before, encoding="utf-8")
    assert cited_occurrences_for_text(before, siblings) == siblings
    assert disposition(short) == "UNDISPOSED"
    assert disposition(long_) == "UNDISPOSED"

    # AFTER the label fix: the bare citation is gone; the anchored one is untouched and
    # must STILL be undisposed. One entry retires, the other does not.
    (here / "core.md").write_text(
        "See [`judge-core.md`](../../_shared/judge-core.md).\n", encoding="utf-8")
    assert disposition(short) == "removed"
    assert disposition(long_) == "UNDISPOSED"

    # THE RE-SPELLING HOLE, closed. Rewrite the bare citation AS the anchored one. Every
    # occurrence of the short raw is now non-stand-alone AND inside a frozen sibling, so
    # the first two clauses of the discount are satisfied exactly -- and nothing is
    # repaired: the anchored spelling escapes the discovery root and dangles too. Under
    # the two-clause discount this retired the entry fully green (measured at scale:
    # 7 re-spellings in skills/skill-iterate/core.md retired 3 entries, repaired 0
    # references, suite green). The third clause catches it, because the re-spelling
    # MOVED those occurrences INTO the long form: its count goes 1 -> 2, and a sibling
    # that GAINED occurrences is not accounting for the bytes, it swallowed them.
    respelled = "See [`../../_shared/judge-core.md`](../../_shared/judge-core.md).\n"
    (here / "core.md").write_text(respelled, encoding="utf-8")
    assert cited_occurrences_for_text(respelled, siblings)[long_["raw"]] == 2
    assert disposition(short) == "UNDISPOSED"
    assert disposition(long_) == "UNDISPOSED"

    # ...and the gate turns on GROWTH, not on the shape. Same bytes, but with a frozen
    # record that had already recorded two citations of the long form, the sibling has
    # not grown and the discount applies again. Stated out loud because it IS the
    # disclosed residual: the gate is `<=`, so an edit that re-spells one short citation
    # while deleting one pre-existing long one holds the count flat and still retires.
    # That is a two-sided edit which also destroys a citation it is not disposing of; it
    # is harder, not impossible, and `_citation_occurrences` says so.
    assert disposition_of(short, canonical_roots=roots,
                          frozen_siblings={short["raw"]: 1, long_["raw"]: 2},
                          )[0] == "removed"
    (here / "core.md").write_text(
        "See [`judge-core.md`](../../_shared/judge-core.md).\n", encoding="utf-8")

    # THE BOUND. Discounting an occurrence needs BOTH "not stand-alone" AND "inside an
    # occurrence of a longer FROZEN sibling". Re-spelling the anchored citation with one
    # more `../` makes it non-stand-alone but nothing frozen contains it, so it still
    # counts as cited and the entry still cannot be retired. (Belt: the new spelling is
    # itself in scope and still dangles, so assertion 1 reds on it as a NEW key too.)
    (here / "core.md").write_text(
        "See [core](../../../_shared/judge-core.md).\n", encoding="utf-8")
    assert disposition(long_) == "UNDISPOSED"
    # ...and a template-prefixed re-spelling, the other non-stand-alone shape.
    (here / "core.md").write_text(
        "See `<dev-root>/../../_shared/judge-core.md` for it.\n", encoding="utf-8")
    assert disposition(long_) == "UNDISPOSED"

    # A CASE FLIP is not a disposition either. `../../References/x.md` still opens on
    # this case-insensitive host and breaks on every case-sensitive consumer home, so
    # reading it as "the token is gone" retired an entry while shipping the defect.
    cased = {"source": "skills/alpha/core.md",
             "raw": "../../references/task-state-schema.md", "form": "backtick"}
    (here / "core.md").write_text(
        "Read `../../References/task-state-schema.md` first.\n", encoding="utf-8")
    assert disposition_of(cased, canonical_roots=roots,
                          frozen_siblings={cased["raw"]: 1})[0] == "UNDISPOSED"
    # ...and a genuine prose conversion of the same citation still retires cleanly.
    (here / "core.md").write_text("Read the task-state schema first.\n", encoding="utf-8")
    assert disposition_of(cased, canonical_roots=roots,
                          frozen_siblings={cased["raw"]: 1})[0] == "removed"


def test_citation_presence_is_boundary_aware_and_case_folded():
    """`_citation_occurrences` as a unit -- the one predicate assertion 4 turns on.

    Kept independent of `extract_references` / `candidate_cores` /
    `is_reference_in_scope` on purpose (see the section comment above it), so it needs
    its own anchor rather than inheriting the detector's.
    """
    short, long_ = "_shared/judge-core.md", "../../_shared/judge-core.md"
    labelled = "See [`_shared/judge-core.md`](../../_shared/judge-core.md).\n"
    fixed = "See [`judge-core.md`](../../_shared/judge-core.md).\n"
    respelled = "See [`../../_shared/judge-core.md`](../../_shared/judge-core.md).\n"
    # the frozen record, measured on `labelled`: one label citation, one destination one
    both = {short: 1, long_: 1}
    assert cited_occurrences_for_text(labelled, both) == both
    # the label is a stand-alone citation; the copy inside the destination is not
    assert _citation_occurrences(labelled, short, both) == 1
    assert _citation_occurrences(fixed, short, both) == 0
    assert _citation_occurrences(labelled, long_, both) == 1
    # THE RE-SPELLING GATE. Both occurrences of `short` are now non-stand-alone and
    # inside an occurrence of the longer frozen sibling -- but that sibling GAINED
    # occurrences (1 -> 2), so it buys no discount and the short raw is still cited.
    assert _citation_occurrences(respelled, long_, both) == 2
    assert _citation_occurrences(respelled, short, both) == 2
    # ...turning on GROWTH, not on shape: with 2 frozen for the sibling, it discounts.
    assert _citation_occurrences(respelled, short, {short: 1, long_: 2}) == 0
    # a sibling with no frozen count is treated as grown -- unknown provenance never
    # buys a discount, so the failure direction is UNDISPOSED, not a silent retirement
    assert _citation_occurrences(fixed, short, {short: 1, long_: None}) == 1
    # a bare collection of raws cannot answer the growth question, so it is refused
    # rather than silently accepted with the gate switched off
    with pytest.raises(TypeError):
        _citation_occurrences(fixed, short, (short, long_))
    # without a containing frozen sibling, a non-stand-alone occurrence still counts
    assert _citation_occurrences(fixed, short, {short: 1}) == 1
    assert _citation_occurrences("see `<x>/../../_shared/judge-core.md` ok\n",
                                 long_, {long_: 1}) == 1
    # case-insensitive, both slash spellings, and a longer path is not a match
    assert _citation_occurrences("Read `../../References/x.md`.\n",
                                 "../../references/x.md") == 1
    assert _citation_occurrences("Read `..\\..\\references\\x.md`.\n",
                                 "../../references/x.md") == 1
    assert _citation_occurrences("Read `../../references/x.markdown`.\n",
                                 "../../references/x.md") == 0
    # a fragment, a `::symbol` and a sentence period all still leave a real citation
    for tail in ("#anchor", "::Section", ".", ")", "`"):
        assert _citation_occurrences("see ../../references/x.md" + tail + "\n",
                                     "../../references/x.md") == 1, tail


# --------------------------------------------------------------------------- #
# The two remaining floors, both RAW. Narrowing the WALK, or narrowing the detector
# in a way that stops it seeing references which RESOLVE, must go red -- and neither
# floor may move when a sanctioned disposition burns an entry down. The precedent for
# the narrowing risk is real and in this repo: test_skill_tree.py's `_ref_defect`
# returns None for every relative non-link token, which is exactly how this defect
# class shipped green. See "THE REMAINING FLOORS" in the module docstring.
# --------------------------------------------------------------------------- #

def _floor_message(label, kind, n, floor):
    return (
        f"the {label} scan reports {n} {kind}, below the frozen floor of {floor}. "
        "Neither floor moves for a burn-down: repairing a reference never deletes a "
        "markdown file and ADDS to the resolving population, and converting one to "
        "prose or dropping it removes a DANGLING reference, which is not counted here. "
        "So a drop means the DETECTOR OR THE WALK WAS NARROWED. Widening the frozen "
        "record is an operator decision recorded in the plan, never a side effect of "
        "a step.")


def test_canonical_scope_floor(canonical_scan):
    floor = load_baseline()["scope_floor"]
    assert canonical_scan["files_scanned"] >= floor["canonical_files_scanned"], (
        _floor_message("canonical", "markdown files",
                       canonical_scan["files_scanned"],
                       floor["canonical_files_scanned"]))
    assert canonical_scan["refs_resolving"] >= floor["canonical_refs_resolving"], (
        _floor_message("canonical", "in-scope references that RESOLVE",
                       canonical_scan["refs_resolving"],
                       floor["canonical_refs_resolving"]))


def test_profile_scope_floor(profile_scan):
    floor = load_baseline()["scope_floor"]
    assert profile_scan["files_scanned"] >= floor["profile_files_scanned"], (
        _floor_message("profile", "markdown files", profile_scan["files_scanned"],
                       floor["profile_files_scanned"]))
    assert profile_scan["refs_resolving"] >= floor["profile_refs_resolving"], (
        _floor_message("profile", "in-scope references that RESOLVE",
                       profile_scan["refs_resolving"],
                       floor["profile_refs_resolving"]))


def test_both_profiles_are_actually_scanned(profile_scan):
    """A floor on a TOTAL cannot see one profile going missing."""
    floor = load_baseline()["scope_floor"]["per_profile_files"]
    per_profile = profile_scan["per_profile_files"]
    assert set(per_profile) == set(PROFILES), per_profile
    assert set(floor) == set(PROFILES), floor
    for provider, n in per_profile.items():
        assert n >= floor[provider], (
            f"profile {provider} contributed {n} files, below the frozen floor of "
            f"{floor[provider]} -- that profile is being built short or not at all")


def test_home_anchored_doc_citations_do_not_grow():
    """Narrows the escape hatch the scope decision opens.

    Host-home-anchored citations are out of the resolution scope, so a
    `../../references/x` entry could be retired by RE-ANCHORING it to a home path
    instead of repairing it. Re-anchoring increases this count, so it reds. It is a
    TOTAL ceiling, so deleting one home citation elsewhere still buys one re-anchor --
    stated rather than claimed away.

    Heads-up for Step 66: the count covers `_shared/**` too, so vendoring a workspace
    doc that itself cites a home path imports those citations and reds this. That is
    the intended signal -- skill-mesh must not ship a doc pointing at the operator's
    home -- and the fix is the scrub that step already owes.
    """
    ceiling = load_baseline()["scope_floor"]["home_anchored_doc_citation_ceiling"]
    now = count_home_anchored_doc_citations()
    assert now <= ceiling, (
        f"host-home-anchored citations into an owned namespace grew {ceiling} -> "
        f"{now}. Re-anchoring a citation to the operator's home is not a repair; "
        "vendor it or convert it to prose (Step 66).")


# --------------------------------------------------------------------------- #
# D-63-B -- the measurement the legacy-package scope decision rests on
# --------------------------------------------------------------------------- #

def test_legacy_packages_anchored_shared_refs_still_resolve():
    """The measurement D-63-B rests on. If it stops holding, re-decide the scope.

    Section 8's risk row names the ANCHORED one-level `../_shared/` form. Measured:
    every one of those resolves, because a legacy package sits at
    `<repo>/<skill>/SKILL.md`. The bare `_shared/x` tokens in the same files DO
    dangle, but they are class `shared_bare` -- already frozen as permanent residual
    for `skills/`, so logging them would add no signal and no burn-down.
    """
    legacy = sorted(p for p in REPO_ROOT.glob("*/SKILL.md"))
    assert len(legacy) >= 40, f"legacy compatibility surface vanished: {len(legacy)}"
    anchored, dangling = 0, []
    for md in legacy:
        text = md.read_text(encoding="utf-8-sig", errors="replace")
        # One-level only: `"../../_shared/x".count("../_shared/")` is 1, so a plain
        # substring count lets depth-2 citations satisfy a guard about depth-1 ones.
        anchored += len(re.findall(r"(?<!\.\./)\.\./_shared/", text))
        entries, _, _ = scan_file(md, REPO_ROOT, md.relative_to(REPO_ROOT).as_posix())
        dangling += [e for e in entries if e["class"] == "shared_anchored"]
    assert anchored >= 40, (
        f"only {anchored} anchored one-level `../_shared/` citations left in the "
        "legacy packages -- the measurement below would pass vacuously")
    assert not dangling, (
        "a legacy top-level package now carries a DANGLING anchored `_shared` "
        "reference, so D-63-B's 'the distinct class would be empty' measurement no "
        "longer holds -- re-decide the scope:\n"
        + "\n".join(f"  {e['source']}:{e['line']}  {e['raw']}" for e in dangling[:20]))


# --------------------------------------------------------------------------- #
# RED-ON-GARBAGE ANCHORS. A gate never observed to go red is not known to work.
# Pure-function calls on synthetic inputs, in the style of
# test_skill_tree.py:test_reachability_reds_on_planted_defects.
# --------------------------------------------------------------------------- #

def _extracted_in_scope(text):
    return {(core, form) for raw, form, _ in extract_references(text)
            for core in candidate_cores(raw, form)
            if is_reference_in_scope(core, form)}


def _anchor_spelling(core):
    """How a token is anchored -- derived from the token, never declared per row."""
    if core.startswith("./"):
        return "./"
    if core.startswith("../"):
        return "../"
    return "unanchored"


# CONTEXT labels: the surrounding syntax a citation sits in. Unlike forms (three, fixed
# by `extract_references`) and classes (enumerated from `classify_reference`), the set of
# surrounding syntaxes is NOT mechanically enumerable from this module, so this tuple is
# a hand-maintained FLOOR and is stated as one -- it proves the listed contexts are
# covered, it does not prove no context is missing. Each entry here exists because a
# ONE-LINE detector narrowing that kills it was demonstrated still-green: `./`-anchored
# tokens (`startswith(("./","../"))` -> `startswith("../")`, and `_BARE_RE`'s
# `\.{1,2}` -> `\.\.`), empty link text (`\[[^\]]*\]` -> `\[[^\]]+\]`), a parenthesized
# token (`_BARE_RE`'s lookbehind gaining `(`, and `clean_ref` no longer stripping
# parens), a reference inside an HTML comment (stripping comments before extraction), a
# whitespace-bearing command span (`_BACKTICK_RE` rejecting whitespace, which reddened
# exactly ONE test before this), and a mis-cased namespace segment.
_REQUIRED_CONTEXTS = ("plain", "empty-link-text", "parenthesized", "html-comment",
                      "command-span", "mis-cased-namespace")

# (planted line, expected (core, form), context). Every FORM x every in-scope CLASS x
# every ANCHOR SPELLING, including `_shared`-rooted tokens in all three forms -- the
# combination a one-alternation edit to `_BARE_RE` removed while the budgeted floor
# granted itself the matching budget.
_IN_SCOPE_MATRIX = (
    ("See [the core](../../_shared/judge-core.md).",
     ("../../_shared/judge-core.md", "link"), "plain"),
    ("See [refs](../../references/step-authoring.md).",
     ("../../references/step-authoring.md", "link"), "plain"),
    ("See [rules](../../rules/subagent-economy.md).",
     ("../../rules/subagent-economy.md", "link"), "plain"),
    ("See [sibling](../context-slim/providers/claude.md).",
     ("../context-slim/providers/claude.md", "link"), "plain"),
    ("See [bare-shared](_shared/judge-core.md).",
     ("_shared/judge-core.md", "link"), "plain"),
    ("See [namespace](../../references/).", ("../../references/", "link"), "plain"),
    ("See [dot-slash sibling](./providers/claude.md).",
     ("./providers/claude.md", "link"), "plain"),
    ("Run `../../_shared/calibrate_judge.py` first.",
     ("../../_shared/calibrate_judge.py", "backtick"), "plain"),
    ("Run `_shared/score_skill_absolute.py` first.",
     ("_shared/score_skill_absolute.py", "backtick"), "plain"),
    ("Read `../../references/step-authoring.md` first.",
     ("../../references/step-authoring.md", "backtick"), "plain"),
    ("Read `../../rules/code-quality.md` first.",
     ("../../rules/code-quality.md", "backtick"), "plain"),
    ("Read `../../../docs/seeds/seed_sprint_wrap.md` first.",
     ("../../../docs/seeds/seed_sprint_wrap.md", "backtick"), "plain"),
    ("Run `./_shared/calibrate_judge.py` first.",
     ("./_shared/calibrate_judge.py", "backtick"), "plain"),
    ("Design source: ../../../docs/investigations/x.md is the record.",
     ("../../../docs/investigations/x.md", "bare"), "plain"),
    ("Design source: _shared/score_skill.workflow.js is the record.",
     ("_shared/score_skill.workflow.js", "bare"), "plain"),
    ("Design source: ../../_shared/grader_prompt.py is the record.",
     ("../../_shared/grader_prompt.py", "bare"), "plain"),
    ("Design source: ../../rules/code-quality.md is the record.",
     ("../../rules/code-quality.md", "bare"), "plain"),
    ("Design source: ./_shared/grader_prompt.py is the record.",
     ("./_shared/grader_prompt.py", "bare"), "plain"),
    # A link with NO link text is still a link, and `[](...)` is how a bare-URL-style
    # citation is written; `\[[^\]]*\]` -> `\[[^\]]+\]` drops the whole class.
    ("See [](../../_shared/judge-core.md).",
     ("../../_shared/judge-core.md", "link"), "empty-link-text"),
    # Parenthesized prose. Two separate one-line narrowings kill these two rows.
    ("see (../../_shared/judge-core.md) here",
     ("../../_shared/judge-core.md", "bare"), "parenthesized"),
    ("Read `(../../_shared/judge-core.md)` first.",
     ("../../_shared/judge-core.md", "backtick"), "parenthesized"),
    # A citation inside an HTML comment still SHIPS -- the file is copied verbatim into
    # the consumer home -- so "strip comments before extracting" is a silent narrowing.
    ("<!-- See [core](../../_shared/judge-core.md) here. -->",
     ("../../_shared/judge-core.md", "link"), "html-comment"),
    # A backtick span is frequently a COMMAND; `_BACKTICK_RE` must accept whitespace.
    ("Run `python ../../_shared/calibrate_judge.py --mode ci` now.",
     ("../../_shared/calibrate_judge.py", "backtick"), "command-span"),
    # Mis-cased namespace segments. Case-SENSITIVE membership dropped these out of scope
    # entirely, which on this case-insensitive host is a citation that still opens
    # locally and dangles on every consumer home -- and it let a one-character edit
    # retire a frozen entry green.
    ("Read `../../References/task-state-schema.md` first.",
     ("../../References/task-state-schema.md", "backtick"), "mis-cased-namespace"),
    ("Design source: _Shared/score_skill.workflow.js is the record.",
     ("_Shared/score_skill.workflow.js", "bare"), "mis-cased-namespace"),
)

# Documented OUT of scope, each for the reason named in the module docstring.
_OUT_OF_SCOPE_MATRIX = (
    ("Read `" + _DOTCLAUDE + "/references/model-tiering.md`.", "host-home anchored"),
    ("Read `~/dev/rules/code-quality.md`.", "host-home anchored"),
    ("Read `rules/code-quality.md`.", "unanchored workspace document"),
    ("Read `../worktree_foo/x.md`.", "not an owned namespace"),
    ("Read `<dev-root>/_shared/x.js`.", "template placeholder"),
    ("See [ext](https://example.invalid/x).", "external URL"),
    ("Read `_shared/` for the shared assets.", "namespace named in prose"),
    ("The _shared/ directory holds them.", "namespace named in prose"),
    # the namespace named in prose stays prose in any casing, or the case-folding above
    # would have quietly WIDENED the record instead of only hardening it
    ("Read `_Shared/` for the shared assets.", "namespace named in prose"),
    ("Read `../../References/` for the workspace docs.", "namespace named in prose"),
)


def test_detector_scope_matrix_is_pinned():
    """Every form x class x anchor x context the detector must see, and every form it must not.

    This replaced the per-form `refs_extracted` floors. A count floor cannot tell "a
    reference was legitimately removed" from "the regex stopped matching it", and the
    budgeted version of that floor granted itself exactly the budget a narrowing needed.
    A fixed fixture has neither problem: it does not move when the burn-down moves, it
    cannot be satisfied by deleting an allowlist entry, and dropping any alternation from
    `_LINK_RE`, `_BACKTICK_RE` or `_BARE_RE` -- or any branch of `is_reference_in_scope`
    -- reds it directly.
    """
    for line, expected, context in _IN_SCOPE_MATRIX:
        found = _extracted_in_scope(line + "\n")
        assert expected in found, (
            f"the detector no longer extracts {expected[1]} form {expected[0]!r} from "
            f"{line!r} ({context}) -- extraction was NARROWED. Found: {sorted(found)}")
    for line, why in _OUT_OF_SCOPE_MATRIX:
        assert not _extracted_in_scope(line + "\n"), (
            f"{line!r} is documented out of scope ({why}) but is now extracted -- the "
            "detector WIDENED, which grows the frozen record instead of shrinking it")


def test_scope_matrix_covers_every_form_and_class():
    """The matrix above is only a control if it is complete -- so prove what is provable.

    A hand-written list of cases is the workspace's "hand-maintained gate lists are false
    greens" shape unless something enumerates what it must cover. Three of the four axes
    ARE enumerable and are enumerated here: the three extraction forms, the ANCHOR
    SPELLINGS (derived from the token by `_anchor_spelling`, crossed with form into a
    full 9-cell grid), and `classify_reference`'s class enum. Covering only (form x
    class) is what left six one-line narrowings green: each killed an anchor spelling or
    a surrounding syntax, not a form or a class, so the matrix had nothing to say.

    The fourth axis, CONTEXT, is not enumerable from this module -- there is no code
    object that lists the syntaxes a citation can sit inside -- so `_REQUIRED_CONTEXTS`
    is a hand-maintained floor and this test says only that each listed context appears.
    It does NOT prove the context axis is complete. Stated rather than implied.
    """
    covered_forms = {form for _, (_, form), _c in _IN_SCOPE_MATRIX}
    assert covered_forms == {"link", "backtick", "bare"}, covered_forms
    covered_classes = {classify_reference(core) for _, (core, _), _c in _IN_SCOPE_MATRIX}
    assert covered_classes == {"shared_anchored", "shared_bare", "references_anchored",
                               "rules_anchored", "home_anchored",
                               "profile_layout"}, covered_classes
    # ANCHOR x FORM, as a full grid rather than a set union: `./` was in scope by the
    # module docstring and covered by nothing, so `startswith(("./","../"))` ->
    # `startswith("../")` and `_BARE_RE`'s `\.{1,2}` -> `\.\.` were both still green.
    grid = {(_anchor_spelling(core), form)
            for _, (core, form), _c in _IN_SCOPE_MATRIX}
    required = {(anchor, form) for anchor in ("./", "../", "unanchored")
                for form in ("link", "backtick", "bare")}
    assert required <= grid, (
        "the scope matrix does not plant every anchor spelling in every form; missing "
        f"{sorted(required - grid)}. A narrowing that kills one anchor spelling in one "
        "form is a one-line edit with no live instances to red assertion 1.")
    # and every in-scope class is planted in more than one form where the form matters:
    # `_shared`-rooted tokens are the pair a one-alternation `_BARE_RE` edit removed.
    shared_bare_forms = {form for _, (core, form), _c in _IN_SCOPE_MATRIX
                         if classify_reference(core) == "shared_bare"}
    assert shared_bare_forms == {"link", "backtick", "bare"}, shared_bare_forms
    covered_contexts = {context for _, _e, context in _IN_SCOPE_MATRIX}
    assert set(_REQUIRED_CONTEXTS) <= covered_contexts, (
        f"contexts declared but not planted: {sorted(set(_REQUIRED_CONTEXTS) - covered_contexts)}")


def test_a_backticked_command_does_not_hide_its_reference():
    """An inline backtick span may be a command; the reference can sit in any token.

    Keeping only the first token produced ZERO entries and ZERO extracted refs, so the
    loss was invisible to the assertions AND to every count floor -- while the
    identical text inside a fenced block was detected as a bare reference. Both paths
    must agree.
    """
    inline = "Run `python ../../_shared/nope.py --mode ci` now.\n"
    fenced = "```\npython ../../_shared/nope.py --mode ci\n```\n"
    for label, text in (("inline", inline), ("fenced", fenced)):
        cores = {core for raw, form, _ in extract_references(text)
                 for core in candidate_cores(raw, form)
                 if is_reference_in_scope(core, form)}
        assert "../../_shared/nope.py" in cores, (label, cores)
    # and the tokenization contract itself; the end-to-end proof (where it must also
    # COUNT) is test_backticked_command_is_detected_by_the_whole_scan below.
    assert candidate_cores("python ../../_shared/nope.py --mode ci", "backtick") == \
        ["python", "../../_shared/nope.py", "--mode", "ci"]


def test_backticked_command_is_detected_by_the_whole_scan(tmp_path):
    tree = tmp_path / "skills"
    (tree / "alpha").mkdir(parents=True)
    (tree / "alpha" / "core.md").write_text(
        "Run `python ../../_shared/nope.py --mode ci` now.\n", encoding="utf-8")
    result = scan_tree(tree, tree, "skills/")
    assert result["refs_extracted"] == 1, result
    assert {entry_key(e) for e in result["entries"]} == \
        {("skills/alpha/core.md", "../../_shared/nope.py", "backtick")}


def test_resolver_reds_on_planted_defects(tmp_path):
    root = tmp_path / "skills"
    (root / "alpha").mkdir(parents=True)
    (root / "beta").mkdir()
    (root / "beta" / "core.md").write_text("x", encoding="utf-8")
    (tmp_path / "_shared").mkdir()
    (tmp_path / "_shared" / "judge-core.md").write_text("x", encoding="utf-8")
    here = root / "alpha"

    # RED: escapes the discovery root even though it resolves inside the checkout --
    # this is the blind spot that let the whole defect class ship green.
    target, reason = resolve_reference(here, root, "../../_shared/judge-core.md")
    assert reason == "escapes the discovery root", (target, reason)
    assert (here / "../../_shared/judge-core.md").resolve().is_file(), \
        "the planted target must really exist, or the anchor proves nothing"
    # RED: inside the root but absent.
    assert resolve_reference(here, root, "_shared/score-skill.md")[1] == \
        "no such path in the tree"
    assert resolve_reference(here, root, "../beta/nope.md")[1] == \
        "no such path in the tree"
    # RED: inside the root and EXISTS, but is a directory. `exists()` accepted any
    # filesystem node, so `mkdir` at the target proved `repaired` to assertion 4 and
    # moved `refs_resolving` up. A citation must name a document a reader can open.
    (root / "beta" / "notes.md").mkdir()
    assert resolve_reference(here, root, "../beta/notes.md")[1] == \
        "resolves to a directory, not a file"
    # GREEN: a real sibling inside the root.
    assert resolve_reference(here, root, "../beta/core.md")[1] is None


def test_resolver_reds_on_a_mis_cased_reference(tmp_path):
    """A citation that resolves on Windows and dangles on a case-sensitive host.

    `exists()` is case-insensitive on Windows and `Path.resolve()` rewrites the target
    to the on-disk casing, so both the verdict AND the recorded evidence used to hide
    the mismatch. Skipped where the filesystem is case-sensitive, since there the miss
    is already reported as a plain absent path.
    """
    root = tmp_path / "skills"
    (root / "alpha").mkdir(parents=True)
    (root / "beta").mkdir()
    (root / "beta" / "core.md").write_text("x", encoding="utf-8")
    here = root / "alpha"
    if not (root / "BETA" / "CORE.MD").exists():
        pytest.skip("case-sensitive filesystem: a mis-cased reference already dangles")
    assert resolve_reference(here, root, "../BETA/CORE.MD")[1] == \
        "case does not match the on-disk name"
    assert resolve_reference(here, root, "../beta/core.md")[1] is None


def test_shipped_shape_predicate_is_pinned():
    """What a repo-root-rooted reference may be credited with resolving to.

    `_shared/**` is rooted at the repo root, which also holds tools/, tests/,
    documentation/ and the legacy `<skill>/scripts/` subtrees. None of those reach a
    discovery root, so crediting them is a false green -- and there is no profile-side
    cross-check until Step 64 emits `_shared/` into `dist/`.
    """
    assert ships_into_discovery_root("judge-ui/core.md")
    assert ships_into_discovery_root("plan-review/SKILL.md")
    assert ships_into_discovery_root("_shared/judge-core.md")
    assert ships_into_discovery_root("_shared/scripts/x.py")
    assert not ships_into_discovery_root(
        "skill-eval-setup/scripts/generate_bad_examples.py")
    assert not ships_into_discovery_root("tools/build-distributions.ps1")
    assert not ships_into_discovery_root("documentation/architecture.md")
    assert not ships_into_discovery_root("judge-ui/providers/claude.md")
    # the third leaf the builder emits, which an earlier two-item SHIPPED_LEAVES denied
    assert ships_into_discovery_root("build-step/build_step_verdict.py")


def test_resolution_roots_are_pinned():
    """The one parameter no floor can see; changing it must be a visible diff here."""
    assert CANONICAL_ROOTS == (
        (SKILLS_DIR, SKILLS_DIR, "skills/", False),
        (SHARED_DIR, REPO_ROOT, "_shared/", True)), (
        "the canonical root mapping changed. skills/<n>/ ships AS "
        "<discovery-root>/<n>/, so skills/ IS the root; re-rooting it at the repo "
        "root resolves the canonical _shared entries and fakes their burn-down with "
        "every scope-floor input byte-identical. Changing this is an operator "
        "decision, not a cleanup.")
    assert profile_scan_root(Path("d"), "claude") == \
        (Path("d/claude"), Path("d/claude"), "dist/claude/", False), \
        "a built profile IS the discovery root; its root may never be widened"
    # the production scan really behaves that way, against a target that EXISTS.
    # `_shared/README.md` rather than a doc this phase may vendor or move: a roots
    # pin must not red for a reason unrelated to roots.
    assert (REPO_ROOT / "_shared" / "README.md").is_file(), \
        "the anchor proves nothing unless the real target exists"
    assert resolve_reference(SKILLS_DIR / "judge-ui", SKILLS_DIR,
                             "../../_shared/judge-core.md")[1] == \
        "escapes the discovery root"


def test_escaping_reference_is_dangling_even_though_it_resolves(tmp_path):
    """The fake burn-down this gate exists to stop, reproduced end to end.

    Re-rooting `skills/` at the repo root is a one-token edit that reads as a plausible
    "fix the root" cleanup. It makes the canonical `shared_anchored` entries resolve
    while `files_scanned`, `refs_extracted` and every per-form count stay byte-identical,
    and it moves `refs_resolving` UP -- so no floor can see it (a floor only reds on a
    drop), and assertion 3 then actively instructs the step to DELETE those entries.
    Assertion 4 cannot see it either: a re-rooted entry genuinely resolves, so it reports
    `repaired`. That is exactly why the roots are PINNED rather than floored, and why
    this anchor asserts the two rootings disagree with the pinned one being the escaping
    verdict.
    """
    repo = tmp_path / "repo"
    (repo / "skills" / "alpha").mkdir(parents=True)
    (repo / "_shared").mkdir()
    (repo / "_shared" / "judge-core.md").write_text("x", encoding="utf-8")
    (repo / "skills" / "alpha" / "core.md").write_text(
        "See [core](../../_shared/judge-core.md).\n", encoding="utf-8")
    assert (repo / "_shared" / "judge-core.md").is_file(), \
        "the planted target must really exist inside the checkout, or this proves nothing"

    pinned = scan_tree(repo / "skills", repo / "skills", "skills/")
    assert [e["reason"] for e in pinned["entries"]] == ["escapes the discovery root"]
    assert {entry_key(e) for e in pinned["entries"]} == \
        {("skills/alpha/core.md", "../../_shared/judge-core.md", "link")}

    rerooted = scan_tree(repo / "skills", repo, "skills/")
    assert rerooted["entries"] == [], (
        "the re-root must make the entry vanish -- if it does not, this anchor is no "
        "longer measuring the vector it was written for")
    assert (rerooted["files_scanned"], rerooted["refs_extracted"],
            rerooted["forms_extracted"]) == \
        (pinned["files_scanned"], pinned["refs_extracted"], pinned["forms_extracted"]), \
        "every count floor's input is identical under both rootings -- that is why the " \
        "roots must be pinned rather than floored"
    assert rerooted["refs_resolving"] > pinned["refs_resolving"], (
        "the re-root moves refs_resolving UP, so the one remaining refs floor is blind "
        "to it by construction -- a floor reds on a drop, never on a rise")

    assert CANONICAL_ROOTS[0][1] == SKILLS_DIR, (
        "scan_canonical_trees must root skills/ at skills/, never at the repo root")


def test_scope_and_class_anchors():
    # in scope
    assert is_reference_in_scope("../../_shared/judge-core.md", "link")
    assert is_reference_in_scope("../../_shared/judge-core.md", "backtick")
    assert is_reference_in_scope("_shared/score-skill.md", "bare")
    assert is_reference_in_scope("../../references/step-authoring.md", "backtick")
    assert is_reference_in_scope("../../rules/subagent-economy.md", "backtick")
    assert is_reference_in_scope("../context-slim/providers/claude.md", "link")
    # out of scope, each for a stated reason
    assert not is_reference_in_scope(_DOTCLAUDE + "/references/model-tiering.md",
                                     "backtick")          # host-home anchored
    assert not is_reference_in_scope("rules/code-quality.md", "backtick")  # unanchored
    assert not is_reference_in_scope("../worktree_foo/x.md", "backtick")   # not owned
    assert not is_reference_in_scope("<dev-root>/_shared/x.js", "backtick")  # template
    assert not is_reference_in_scope("https://example.invalid/x", "link")
    assert not is_reference_in_scope("_shared/", "bare")        # the namespace in prose
    assert not is_reference_in_scope("../../references/", "backtick")
    # ...but a LINK destination is never prose, so the namespace-tail narrowing does
    # NOT apply to links -- otherwise truncating a link to its namespace would
    # de-scope the citation and read as a retirement.
    assert is_reference_in_scope("../../references/", "link")
    # CASE-ONLY variants are the SAME citation, in scope and in the same class. A
    # case-sensitive membership test dropped them out of scope, so a one-character edit
    # simultaneously hid the citation from the detector and read its frozen token as
    # gone -- retiring the entry fully green while the broken citation shipped.
    assert is_reference_in_scope("../../References/task-state-schema.md", "backtick")
    assert is_reference_in_scope("_Shared/score-skill.md", "bare")
    assert is_reference_in_scope("../../RULES/code-quality.md", "bare")
    assert not is_reference_in_scope("_Shared/", "bare")   # still prose, any casing
    assert classify_reference("_Shared/score-skill.md") == "shared_bare"
    assert classify_reference("../../References/x.md") == "references_anchored"
    # classes
    assert classify_reference("../../_shared/judge-core.md") == "shared_anchored"
    assert classify_reference("_shared/score-skill.md") == "shared_bare"
    assert classify_reference("../../references/step-authoring.md") == \
        "references_anchored"
    assert classify_reference("../../rules/subagent-economy.md") == "rules_anchored"
    assert classify_reference("../../../docs/investigations/x.md") == "home_anchored"
    assert classify_reference("../context-slim/providers/claude.md") == "profile_layout"


def test_home_anchor_ceiling_catches_a_deep_re_anchoring():
    """The evasion that motivated widening `_HOME_DOC_CITATION_RE`.

    Requiring the owned namespace as the SECOND segment let a citation be re-anchored
    to `<dot>claude/skills/_shared/judge-core.md` -- a natural spelling for a Claude
    consumer home -- and slip the ceiling, `is_reference_in_scope`, and
    `test_skill_tree.py:_ref_defect` alike.
    """
    for spelling in (_DOTCLAUDE + "/references/model-tiering.md",
                     _DOTCLAUDE + "/skills/_shared/judge-core.md",
                     "~/dev/skill-mesh/_shared/judge-core.md",
                     # a drive-anchored spelling, deliberately NOT under a home
                     # directory: tests/package-integrity/test_manifest_contract.py
                     # sweeps every committed file for absolute private paths.
                     "D:/dev/skill-mesh/rules/code-quality.md"):
        assert _HOME_DOC_CITATION_RE.search(spelling), spelling
    for spelling in ("../../_shared/judge-core.md", "_shared/judge-core.md",
                     _DOTCLAUDE + "/settings.json"):
        assert not _HOME_DOC_CITATION_RE.search(spelling), spelling


def test_whole_detector_reds_on_a_synthetic_tree(tmp_path):
    """Full scan_tree round trip: exactly the planted defect is reported."""
    tree = tmp_path / "skills"
    (tree / "alpha").mkdir(parents=True)
    (tree / "beta").mkdir()
    (tree / "beta" / "core.md").write_text("beta\n", encoding="utf-8")
    (tree / "alpha" / "core.md").write_text(
        "ok: [beta](../beta/core.md)\n"
        "broken: [shared](../../_shared/judge-core.md)\n"
        "ignored: `" + "." + "claude/rules/code-quality.md`\n",
        encoding="utf-8")
    result = scan_tree(tree, tree, "skills/")
    assert result["files_scanned"] == 2
    assert result["refs_extracted"] == 2       # the home-anchored token is out of scope
    keys = {entry_key(e) for e in result["entries"]}
    assert keys == {("skills/alpha/core.md", "../../_shared/judge-core.md", "link")}, keys
    assert result["entries"][0]["class"] == "shared_anchored"


def test_line_is_not_part_of_the_entry_key():
    """An edit ABOVE a citation must not read as a new dangling ref."""
    a = {"source": "skills/x/core.md", "raw": "../../_shared/j.md", "form": "link",
         "line": 7}
    b = dict(a, line=4001)
    assert entry_key(a) == entry_key(b)
    assert len(dedupe([a, b])) == 1


def test_shipped_leaves_matches_a_real_build(dist_root):
    """The hand-written leaf list, compared against a REAL build instead of itself.

    `SHIPPED_LEAVES` is the workspace's "hand-maintained gate lists are false greens"
    shape: a list of what a build produces, previously pinned only by a test that
    asserted the literal against the literal. It had already drifted -- it claimed
    `build-distributions.ps1` "emits exactly these two leaves" while the builder also
    writes `build_step_verdict.py` into the consumer skill dirs, so a `_shared/**`
    citation of `../build-step/build_step_verdict.py` would have been called dangling
    even though it ships.

    AMENDED for Step 64. `SHIPPED_LEAVES` is documented above as "the leaf FILENAMES a
    built host profile contains PER SKILL DIR", and Step 64 adds a directory that is not
    a skill dir: `dist/<p>/_shared/`, the shared payload, which D1 places at the profile
    root as a SIBLING of the skill dirs. Its leaves are asset names (judge-core.md,
    score_skill.workflow.js, ...), not per-skill leaves, and `ships_into_discovery_root`
    never consults SHIPPED_LEAVES for them -- it returns True for any `_shared/**` target
    on its own first branch, ahead of the two-segment leaf test. Folding those names into
    SHIPPED_LEAVES would therefore change nothing about `_shared` resolution while
    WIDENING what counts as shipping for `<skill>/<leaf>` paths, e.g. crediting a
    citation of `<skill>/grader_prompt.py`, which no profile contains. So `_shared` is
    excluded from the per-skill loop, and asserted present separately below so the
    exclusion cannot become a hole that hides the payload not shipping at all.
    """
    shared_seen = {}
    seen = set()
    for provider in PROFILES:
        for skill_dir in sorted((Path(dist_root) / provider).iterdir()):
            if not skill_dir.is_dir():
                continue
            if skill_dir.name == "_shared":
                shared_seen[provider] = {p.name for p in skill_dir.rglob("*")
                                         if p.is_file()}
                continue
            names = {p.name for p in skill_dir.rglob("*") if p.is_file()}
            unlisted = sorted(names - set(SHIPPED_LEAVES))
            assert not unlisted, (
                f"{provider}/{skill_dir.name} contains {unlisted}, which SHIPPED_LEAVES "
                "does not list -- `ships_into_discovery_root` would call a citation of "
                "it dangling even though it ships. Add it (and correct the prose).")
            seen |= names
    assert seen == set(SHIPPED_LEAVES), (
        f"SHIPPED_LEAVES lists {sorted(set(SHIPPED_LEAVES) - seen)}, which no built "
        "profile actually contains -- the list drifted the other way")
    # The exclusion above is only sound while the payload is actually there. Both
    # profiles must carry a non-empty `_shared/`, or `ships_into_discovery_root`'s
    # unconditional "`_shared/**` ships" branch is crediting a tree that does not exist.
    assert set(shared_seen) == set(PROFILES), (
        f"the shared payload is missing from {sorted(set(PROFILES) - set(shared_seen))} "
        "-- `ships_into_discovery_root` credits every `_shared/**` target as shipping, "
        "so an absent payload makes this gate green over references that dangle in "
        "every consumer home")
    for provider, names in sorted(shared_seen.items()):
        assert names, f"{provider}/_shared/ is empty"


# --------------------------------------------------------------------------- #
# FILE ENUMERATION. `markdown_files` decides what the whole gate can SEE, and three
# separate defects made it silently return ZERO files. Exercised against a synthetic
# git repository under tmp_path, never against this checkout: a stray file planted at
# a real discovery path is its own defect class here (#83-#86).
# --------------------------------------------------------------------------- #

def _synthetic_repo(tmp_path):
    """A real git work tree with one tracked markdown file under `skills/`."""
    if GIT is None:
        pytest.skip("git is not on PATH, so the enumeration cannot be exercised")
    repo = tmp_path / "repo"
    (repo / "skills" / "alpha").mkdir(parents=True)
    (repo / "skills" / "alpha" / "core.md").write_text("core\n", encoding="utf-8")
    for args in (["init", "-q"], ["add", "skills"]):
        subprocess.run([GIT, "-C", str(repo)] + args, check=True, capture_output=True,
                       timeout=60)
    return repo


def test_enumeration_prefers_the_index_over_an_untracked_scratch_file(tmp_path):
    """The behavior git enumeration was adopted FOR (Step 63's own review)."""
    repo = _synthetic_repo(tmp_path)
    (repo / "skills" / "alpha" / "zz-scratch.md").write_text("x", encoding="utf-8")
    found = markdown_files(repo / "skills", repo_root=repo)
    assert [p.name for p in found] == ["core.md"], found


def test_an_untracked_tree_falls_back_to_the_filesystem_walk(tmp_path):
    """An EMPTY `git ls-files` answer is the absence of an answer, not "no files".

    `dist/` is gitignored, so this is the profile scan's normal path -- and Step 64
    emits `_shared/` into `dist/`. Treating `[]` as authoritative scanned zero files
    while 97 markdown files sat on disk, and turned `--emit` into a scratch directory
    inside the repo into a silent 95-entry phantom burn-down.
    """
    repo = _synthetic_repo(tmp_path)
    dist = repo / "dist" / "claude" / "plan-review"
    dist.mkdir(parents=True)
    (dist / "SKILL.md").write_text("x", encoding="utf-8")
    found = markdown_files(repo / "dist", repo_root=repo)
    assert found == [dist / "SKILL.md"], (
        "an untracked tree inside the work tree must fall back to the walk", found)


def test_a_stage_directory_inside_the_repo_is_still_scanned(tmp_path):
    """`tools/release.ps1` stages into `<repo>\\release-stage` and runs pytest there.

    `REPO_ROOT` is then the STAGE while git still answers for the OUTER repository, so
    `git -C <stage> ls-files -- skills` resolves its pathspec against an untracked
    directory and exits 0 with empty output. The canonical scan was zeroed and assertion
    1 passed vacuously; reproduced as 3 failed / 26 passed before the fix.
    """
    repo = _synthetic_repo(tmp_path)
    stage = repo / "release-stage"
    (stage / "skills" / "beta").mkdir(parents=True)
    (stage / "skills" / "beta" / "core.md").write_text("core\n", encoding="utf-8")
    found = markdown_files(stage / "skills", repo_root=stage)
    assert found == [stage / "skills" / "beta" / "core.md"], found


def test_an_outer_repo_tracking_the_same_relative_paths_cannot_narrow_the_scan(tmp_path):
    """The case the EMPTY-ANSWER guard cannot see, and the only one `--show-toplevel` catches.

    `git ls-files` prints paths relative to git's working directory, so a stage sitting
    inside a FOREIGN work tree that happens to track the same relative layout answers
    with a plausible, on-disk, WRONG subset. Non-empty, so `if not files: return None`
    never fires; every returned path exists, so `require_present_in_worktree` cannot
    object either. The scan is then silently narrowed to whatever the outer index holds
    -- the one outcome this module exists to prevent.

    Written because the two guards were argued to be independently load-bearing while
    only ONE of them had a test that reds on its removal: the stage fixture above is
    rescued by the empty-answer guard, so deleting the `--show-toplevel` equality left
    the suite fully green. Measured on this fixture: guard removed -> 2 of 3 files,
    silently; as shipped -> 3, via the walk.
    """
    if GIT is None:
        pytest.skip("git is not on PATH, so the enumeration cannot be exercised")
    outer = tmp_path / "outer"
    stage = outer / "release-stage"
    for name in ("alpha", "beta", "gamma"):
        (stage / "skills" / name).mkdir(parents=True)
        (stage / "skills" / name / "core.md").write_text("core\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(outer), "init", "-q"], check=True,
                   capture_output=True, timeout=60)
    # the OUTER repo tracks two of the three, at the SAME relative paths the stage uses
    subprocess.run([GIT, "-C", str(outer), "add", "--",
                    "release-stage/skills/alpha", "release-stage/skills/beta"],
                   check=True, capture_output=True, timeout=60)
    found = markdown_files(stage / "skills", repo_root=stage)
    assert sorted(p.parent.name for p in found) == ["alpha", "beta", "gamma"], (
        "the scan was narrowed to the OUTER repository's index -- git answered for a "
        "tree that is not this one, with paths that happen to exist here", found)


def test_ls_files_bytes_are_decoded_as_utf8_not_the_locale_codec(tmp_path):
    """`-z` emits raw UTF-8 path bytes; the locale codec mangles them into non-paths.

    `text=True` decoded them as cp1252 on the supported host, and `errors="replace"`
    substituted U+FFFD for the five bytes cp1252 leaves undefined -- so a loud
    UnicodeDecodeError became a silently wrong path, and the gate died later inside
    `read_text`. Exposure today is 0 non-ASCII markdown filenames; Step 66 vendors seven
    new documents into `_shared/`.
    """
    name = "zz-\u00e9\u00e7.md"   # escaped, so this source file stays ASCII on disk
    decoded = decode_ls_files(("skills/alpha/" + name).encode("utf-8") + b"\0", tmp_path)
    assert decoded == [tmp_path / "skills" / "alpha" / name], decoded
    # end to end, against what git really writes
    repo = _synthetic_repo(tmp_path)
    try:
        (repo / "skills" / "alpha" / name).write_text("x", encoding="utf-8")
    except (OSError, UnicodeError):
        pytest.skip("this filesystem cannot hold a non-ASCII filename")
    subprocess.run([GIT, "-C", str(repo), "add", "skills"], check=True,
                   capture_output=True, timeout=60)
    found = markdown_files(repo / "skills", repo_root=repo)
    assert sorted(p.name for p in found) == sorted(["core.md", name]), found
    assert all(p.is_file() for p in found), (
        "a decoded path that is not on disk is the mojibake signature", found)


def test_an_unstaged_worktree_deletion_is_reported_not_silently_dropped(tmp_path):
    """`git ls-files` reads the INDEX; the edit-then-test loop disagrees with it.

    Deliberately NOT filtered out: dropping absent paths would also swallow a mis-decoded
    path and narrow the scan with no signal. D-63-A's "dropped" disposition means deleting
    a markdown file, so this fires in exactly the workflow Steps 64/66 are about -- it
    must be a worded failure, not a bare FileNotFoundError from inside `read_text`.
    """
    repo = _synthetic_repo(tmp_path)
    (repo / "skills" / "alpha" / "core.md").unlink()
    with pytest.raises(AssertionError) as excinfo:
        markdown_files(repo / "skills", repo_root=repo)
    assert "git index but not in the worktree" in str(excinfo.value)


def test_the_markdown_predicate_has_one_spelling():
    """Two spellings of one predicate is two answers.

    The tracked half filtered `.lower().endswith(".md")` and the walk half filtered
    `Path(...).suffix.lower() == ".md"`, and `Path(".md").suffix` is `""` -- so the two
    halves disagreed about a file named exactly `.md`.
    """
    assert is_markdown_name("core.md")
    assert is_markdown_name("NOTES.MD")
    assert is_markdown_name(".md")
    assert not is_markdown_name("core.markdown")
    assert not is_markdown_name("build_step_verdict.py")


# --------------------------------------------------------------------------- #
# Standalone emit: regenerates the frozen baseline + the KNOWN_DANGLING literal
# from a real scan. The committed pair was produced by this path.
# --------------------------------------------------------------------------- #

_WIDEN_FLAG = "--widen-frozen-record"


def _emit(out_dir, allow_repo_write=False):
    out_dir = Path(out_dir)
    if PWSH is None:
        raise SystemExit(
            "powershell is not on PATH, so the profile half of the baseline cannot be "
            "generated and the emitted record would be silently short by every "
            "dist/** entry. This repository declares Windows + PowerShell a hard "
            "environment requirement.")
    if out_dir.resolve() == BASELINE_PATH.parent and not allow_repo_write:
        raise SystemExit(
            "refusing to regenerate the committed frozen baseline in place. That is "
            "the one command that absorbs a new dangling reference into the record "
            "invisibly; BASELINE_SHA256 makes the result visible, and this guard makes "
            "it deliberate. Emit to a scratch directory and diff, or pass "
            f"{_WIDEN_FLAG} if an operator decision recorded in the plan says the "
            "frozen record is to be widened (D-63-A).")
    out_dir.mkdir(parents=True, exist_ok=True)
    src = scan_canonical_trees()
    dist_root = build_profiles(out_dir / "dist")
    prof = scan_profiles(dist_root)
    entries = sorted(src["entries"] + prof["entries"], key=entry_key)
    annotate_cited_occurrences(entries, dist_root=dist_root)
    baseline = {
        "note": (
            "FROZEN at Step 63 (Phase 7.5). NO STEP MAY EDIT THIS FILE -- not to add "
            "an entry, not to delete one, not to adjust a floor. It is the comparand "
            "the shrink-only assertion compares KNOWN_DANGLING against; a file both "
            "sides may edit proves nothing. Its bytes are digest-pinned by "
            "BASELINE_SHA256 in test_link_resolution.py (CRLF->LF normalized, BOM "
            "stripped), so an edit here cannot be silent -- but the pin is "
            "tamper-evident, not tamper-proof, and it is review that stops a "
            "coordinated two-file edit. Steps 64 and 66 shrink KNOWN_DANGLING in "
            "test_link_resolution.py instead. Widening this record requires an "
            "explicit operator decision recorded in the plan."),
        "generated_by": "tests/package-integrity/test_link_resolution.py --emit",
        "phase": "7.5",
        "step": 63,
        "decisions": {
            "D-63-A_allowlist_replacement": {
                "permitted": False,
                "reason": (
                    "Step 66 asks whether the 14 external links inherited from the "
                    "seven vendored reference docs may be dispositioned as an "
                    "'approved allowlist replacement'. They may not. An entry may "
                    "LEAVE the allowlist; none may enter it, so each of the 14 links "
                    "must be vendored, converted to prose, or dropped. State the "
                    "enforcement honestly: it is TAMPER-EVIDENT, not tamper-proof. "
                    "The shrink-only assertion compares KNOWN_DANGLING against this "
                    "frozen file, and this file's bytes are digest-pinned by "
                    "BASELINE_SHA256 in test_link_resolution.py -- a different file. "
                    "So a replacement entry cannot be added QUIETLY: it takes three "
                    "coordinated edits ACROSS TWO FILES (this record, plus the "
                    "KNOWN_DANGLING literal and a 64-hex constant, which both live in "
                    "the test), and the hash edit is unmistakable in a review "
                    "diff. It is NOT mechanically impossible; nothing in the "
                    "repository can make it so, because --emit writes this file. The "
                    "only sanctioned way to widen the record is an explicit operator "
                    "decision recorded in the plan, which sits above a step, and is "
                    "never a step editing this file to make itself pass."),
            },
            "D-63-B_legacy_top_level_packages": {
                "in_scope": False,
                "reason": (
                    "The 46 legacy top-level <skill>/SKILL.md packages stay OUT of "
                    "this detector's scope. Measured: the form section 8's risk row "
                    "names -- the one-level anchored ../_shared/ citation -- RESOLVES "
                    "today, because a legacy package sits at <repo>/<skill>/SKILL.md "
                    "so ../_shared/x lands on <repo>/_shared/x. "
                    "The requested 'distinct class' would be empty, and that row's "
                    "real concern is surface divergence after this phase, not "
                    "danglingness. The same files carry bare _shared/x tokens that "
                    "do dangle, but those are class shared_bare, already frozen as "
                    "permanent residual for skills/, so more of them add no signal and "
                    "no burn-down. They are also a frozen compatibility surface "
                    "nothing in this phase edits, so entries could never burn down, "
                    "and adding roughly 220 permanent entries would inflate the only "
                    "comparand the later steps are measured against. "
                    "test_legacy_packages_anchored_shared_refs_still_resolve pins the "
                    "measurement so the decision is re-opened rather than silently "
                    "inherited if it stops holding."),
            },
        },
        "scope_floor": {
            "rule": (
                "EXACTLY the keys in this object are enforced as floors, and all of "
                "them are RAW -- there is no budget arithmetic. A budgeted floor was "
                "tried and defeated: its budget was derived from KNOWN_DANGLING, which "
                "the step itself edits, so narrowing the detector and deleting the "
                "entries the narrowing hid grew the budget by exactly the amount the "
                "count fell. files_scanned: repairing a reference never deletes a "
                "markdown file, converting one to prose never deletes a markdown file, "
                "and Steps 64/66 only add them. refs_resolving: the in-scope references "
                "that RESOLVE -- a prose conversion or a drop removes a DANGLING "
                "reference and leaves this unchanged, and a repair adds to it, so no "
                "sanctioned disposition can move it down. Detector narrowing is caught "
                "primarily by the RETIREMENT PROOF (assertion 4), not by these floors: "
                "an entry may leave KNOWN_DANGLING only if its frozen source+raw now "
                "resolves, or its token is gone from the citing file. Everything under "
                "counts.* is scan PROVENANCE, not a floor. See THE REMAINING FLOORS and "
                "WHY ASSERTION 4 EXISTS in test_link_resolution.py's module docstring."),
            "canonical_files_scanned": src["files_scanned"],
            "canonical_refs_resolving": src["refs_resolving"],
            "profile_files_scanned": prof["files_scanned"],
            "profile_refs_resolving": prof["refs_resolving"],
            "per_profile_files": prof["per_profile_files"],
            "home_anchored_doc_citation_ceiling": count_home_anchored_doc_citations(),
        },
        "counts": {
            "entries": len(entries),
            "occurrences": sum(e["occurrences"] for e in entries),
            "by_class": {c: sum(1 for e in entries if e["class"] == c)
                         for c in sorted({e["class"] for e in entries})},
            "by_class_occurrences": {
                c: sum(e["occurrences"] for e in entries if e["class"] == c)
                for c in sorted({e["class"] for e in entries})},
            "by_form": {f: sum(1 for e in entries if e["form"] == f)
                        for f in sorted({e["form"] for e in entries})},
            # Scan provenance, NOT floors. The per-form floors that used to read this
            # were deleted with the budget; `test_detector_scope_matrix_is_pinned` does
            # their job without moving when the burn-down moves.
            "refs_extracted_by_form": {
                "canonical": src["forms_extracted"],
                "profile": prof["forms_extracted"],
            },
            "refs_extracted": {"canonical": src["refs_extracted"],
                               "profile": prof["refs_extracted"]},
        },
        "entries": entries,
    }
    (out_dir / "link_baseline.json").write_text(
        json.dumps(baseline, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    lines = ["KNOWN_DANGLING = ("]
    for e in entries:
        lines.append("    (%r, %r, %r)," % entry_key(e))
    lines.append(")")
    (out_dir / "known_dangling.py.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(f"emitted {len(entries)} entries -> {out_dir}")
    print("counts:", json.dumps(baseline["counts"], indent=2))
    print("floor:", json.dumps(baseline["scope_floor"], indent=2))


if __name__ == "__main__":
    if "--emit" in sys.argv:
        _emit(sys.argv[sys.argv.index("--emit") + 1],
              allow_repo_write=_WIDEN_FLAG in sys.argv)
    else:
        print(f"usage: python test_link_resolution.py --emit <out-dir> [{_WIDEN_FLAG}]\n"
              "       (or run the gate: python -m pytest tests/package-integrity)")
