"""Single-owner guard for the instruction-file contract (Phase IS Step 106, issue #150).

`skills/plan-init/core.md` section "## Instruction-file contract" is the ONE owner
of that contract -- the three-valued state definition, the five-row behavior matrix
each lifecycle writer implements, and the guarded-write rule. Every other core or
adapter that must act on the contract cites the owner and restates no part of the
definition. Modeled on test_autofix_marker_single_owner.py, this repository's proven
pattern for a shared prose constant: the link gate covers a cited path's existence,
but it cannot see the definition re-duplicated into a second file, the definition
leaving the cited section, a renamed owner heading, or a citation deleted outright.
Those four are exactly what the assertions below add.

This gate is the AUTHORING axis -- which file owns the contract text. It says
nothing about the installer axis (which discovery root each host reads), which is a
different contract with its own home and is deliberately not restated here.

THE USE / MENTION RULE -- the self-collision this gate had to decide, stated in
plain language.

`documentation/instruction-file-symmetry-plan.md` is the document that DESIGNATES
the two probe literals below, and it quotes both of them verbatim. It also lives
under one of the swept trees, so a naive substring sweep would red on the very plan
that specifies the sweep. The rule adopted here:

    An occurrence wrapped in a backtick code span is a MENTION -- a document
    quoting the literal -- and is permitted anywhere. A BARE occurrence is a USE --
    a file actually carrying the marker -- and is forbidden outside the owner.

That is a derived rule, not a path exemption: it names no file, and it keeps holding
for any future document that quotes the contract. (A hand-maintained exemption list
is a false green waiting to happen, so a general rule is preferred wherever one can
be made to hold -- and this one holds with nothing hard-coded. The owner's own two
occurrences are bare: the sentinel is a bare HTML comment and the sentence is
bolded, not backticked. The designating plan's are both inside backticks.)

Two deliberate edges of the rule:

  - Text inside a fenced code block counts as a USE, not a mention. A fence in a
    skill core is emitted content -- bytes the skill writes out -- so a literal
    sitting in one is being carried, not quoted.
  - At a CITE site the rule does not apply at all: a citer must carry neither probe
    literal in any form. That is D11's bounded cite-site minimum verbatim, and a
    skill surface applying the contract has no reason to quote it.

SCOPE (plan D5): the swept trees are skills/, _shared/ and documentation/. This
repository's own root CLAUDE.md / AGENTS.md pair is deliberately outside every sweep
here. That pair is frozen by test_recovery_plan_hygiene.py, and this gate must never
be the reason it moves.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

OWNER = "skills/plan-init/core.md"
OWNER_HEADING = re.compile(r"^## Instruction-file contract\s*$", re.MULTILINE)

# The two designated probe literals, as prose bytes used only as plain substring
# probes. Their one home is the owner section; they exist so a gate can tell a
# legal citation from a silent re-duplication of the contract.
PROBE_LITERALS = (
    "<!-- instruction-file-contract: owner -->",
    "Instruction-file states are three-valued",
)

CITE_PHRASE = "see the Instruction-file contract in plan-init/core.md"
CANONICAL_MARKER = "CLAUDE.md or AGENTS.md"

# D8's emitted pointer bytes. Keyed on the BYTES, with the fence's info string
# left free ("text", "markdown", or nothing at all): the info string carries no
# contract meaning, so pinning it would red on a rewording that changed nothing.
POINTER_BLOCK_RE = re.compile(r"```[a-zA-Z]*\n@AGENTS\.md\n```")

# A floor, not a list. Hand-listing the citer paths is the failure mode this
# repository has already shipped once, so the citers are discovered by sweep and
# only their COUNT is pinned -- which is what makes a deleted citation visible.
CITER_FLOOR = 4

_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def _code_span_ranges(line):
    """Half-open [start, end) column ranges covered by inline code spans.

    Backtick runs pair with the next run of the same width, as in CommonMark, so
    each span yields one range and an unpaired run opens nothing.
    """
    runs = [(m.start(), m.end()) for m in re.finditer(r"`+", line)]
    ranges = []
    index = 0
    while index < len(runs):
        start, after_open = runs[index]
        width = after_open - start
        closer = index + 1
        while closer < len(runs) and (runs[closer][1] - runs[closer][0]) != width:
            closer += 1
        if closer == len(runs):
            index += 1
            continue
        ranges.append((after_open, runs[closer][0]))
        index = closer + 1
    return ranges


def _scan(text, needle):
    """Return (uses, mentions) as 1-based line numbers -- the use/mention rule."""
    uses = []
    mentions = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if needle not in line:
            continue
        spans = [] if in_fence else _code_span_ranges(line)
        for hit in re.finditer(re.escape(needle), line):
            quoted = any(
                start <= hit.start() and hit.end() <= end for start, end in spans
            )
            (mentions if quoted else uses).append(number)
    return uses, mentions


def _relative(path):
    return path.relative_to(REPO_ROOT).as_posix()


def _normalized(text):
    """Whitespace-collapsed text: every run of spaces and newlines becomes one
    space. Used only by the coarse arm at the bottom of this file and by the
    owner-section canaries, never by the use/mention logic."""
    return re.sub(r"\s+", " ", text)


# Build artifacts, never authored and never published. `.pyc` files are BINARY,
# and this repository's own repo-root pytest run creates `_shared/__pycache__/`
# because `_shared/` is one of its test roots -- so the sweep below meets them on
# any developer machine that has run the DONE gate. They are filtered out of the
# enumeration rather than decoded leniently, mirroring test_skill_tree.py's
# `_LEAK_SWEEP_SKIP_DIRS`: a filtered enumeration keeps the non-vacuity guard
# honest (transient caches must not be able to satisfy it on their own), while a
# lenient decoder would silently accept whatever else lands in the tree.
_SKIP_DIRS = ("__pycache__",)
_SKIP_SUFFIXES = (".pyc", ".pyo")


def _authored(paths):
    """Drop build artifacts, and anything resolving outside the repository.

    The containment check is the second half: `glob("**/*")` walks Windows
    directory junctions, and a junction reports `is_symlink() == False`, so
    pathlib's `recurse_symlinks=False` default does not contain it (measured:
    default, False and True all returned the same escaped files). Without this,
    out-of-repo bytes would be read and then REPORTED under an in-repo path, and
    an escaped file would inflate the CITER_FLOOR denominator, which has no
    headroom. Latent rather than live -- git cannot create a junction, so a CI
    checkout cannot have one -- but this repository has junction history (#138).
    One resolve() per file, no more.
    """
    kept = []
    for path in paths:
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _SKIP_SUFFIXES:
            continue
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved.is_relative_to(REPO_ROOT):
            kept.append(path)
    return kept


def _markdown_arms():
    """The three swept trees, one place. Both sweeps below read this, so the
    enumeration set cannot drift between them."""
    return {
        "skills/**/*.md": _authored(sorted(REPO_ROOT.glob("skills/**/*.md"))),
        "_shared/**/*.md": _authored(sorted(REPO_ROOT.glob("_shared/**/*.md"))),
        "documentation/**/*.md": _authored(
            sorted(REPO_ROOT.glob("documentation/**/*.md"))),
    }


def _owner_section():
    """The owner file's '## Instruction-file contract' section, or a loud fail.

    Both owner-side tests below read the section through this, so neither can
    drift on where it starts and ends: the named heading, up to the next `##`.
    """
    owner_path = REPO_ROOT / OWNER
    assert owner_path.is_file(), (
        f"the instruction-file contract's owner is {OWNER} and it is not there -- "
        f"if the owner moved, re-point this gate and every citation to it in the "
        f"same change")

    text = owner_path.read_text(encoding="utf-8")
    heading = OWNER_HEADING.search(text)
    assert heading, (
        f"the '## Instruction-file contract' heading was renamed or removed from "
        f"{OWNER}; every citation to it now dangles. Rename the citations in the "
        f"same change or revert")

    end = text.find("\n## ", heading.end())
    return text[heading.start(): end if end != -1 else len(text)]


def test_the_instruction_file_contract_has_one_named_owner_section():
    # Bind the definition to the section the citations name: both probe literals
    # must live INSIDE that section, not merely somewhere in the owner file.
    section = _owner_section()
    for literal in PROBE_LITERALS:
        uses, _ = _scan(section, literal)
        assert uses, (
            f"probe literal {literal!r} is not USED inside the "
            f"'## Instruction-file contract' section of {OWNER}. Either it left "
            f"the section the citations name, or it is now quoted in backticks "
            f"there -- the owner must carry it bare, because a quoted occurrence "
            f"is a mention and every other file is allowed one")

def test_the_owner_section_still_carries_the_contract_it_defines():
    """Structural canaries: the section still holds the contract, not just its markers.

    The two probe literals are MARKERS, not the contract. An editor can delete
    the contract and leave both strings behind, and every sweep in this file
    stays green -- measured: the section cuts from 106 lines to 3, or loses the
    matrix or the guarded-write rule outright, and every SWEEP still passes.
    These canaries are what red on it, which is why they exist. The precedent
    gate pins extra phrases for the same reason (test_autofix_marker_single_owner
    binds the Format bullet to the section as well as the regex).

    Each canary is keyed on what the contract MEANS and on something a citer is
    graded against -- never on styling or on an incidental sentence a future
    editor would reword innocently -- and every one is a string the owner section
    already carries, so nothing here required editing the owner.
    """
    section = _owner_section()
    flat = _normalized(section)

    # D8's three-valued state definition: the vocabulary every writer branches
    # on and every citer defers to. Keyed on the bullets that DEFINE the states
    # -- not on the wording of the definitions, and not on the bullet's styling:
    # the marker character and the bold markers are free, because neither
    # carries contract meaning.
    for state in ("ABSENT", "POINTER", "SUBSTANTIVE"):
        assert re.search(rf"^[-*] +\*{{0,2}}{state}\b", section, re.MULTILINE), (
            f"the '{state}' state definition left the owner section of "
            f"{OWNER}. The three states are the vocabulary every writer "
            f"branches on and every citer defers to; a citer resolving a state "
            f"the owner no longer defines is acting on nothing")

    # D8's emitted pointer bytes, exact. Prose is the ONLY place these bytes are
    # specified, and a writer emitting anything else produces a file the other
    # host cannot follow.
    assert POINTER_BLOCK_RE.search(section), (
        f"the exact pointer-byte block left the owner section of {OWNER} -- "
        f"those are the bytes two rows of the matrix write, and this section "
        f"is the only place they are specified")

    # D10's behavior matrix, checked STRUCTURALLY rather than row by row: the
    # header must still name both writer columns and five data rows must
    # survive. A deleted row is the realistic regression -- a writer silently
    # stops handling a case -- and this catches it without pinning any row's
    # prose, which would be the fragile way to do it.
    table = [line for line in section.splitlines() if line.lstrip().startswith("|")]
    assert table and "plan-init" in table[0] and "repo-update" in table[0], (
        f"the behavior matrix's header row left the owner section of {OWNER}, "
        f"or no longer names both writer columns -- each writer step "
        f"implements its own column of that table")
    body = [
        row for row in table[1:]
        if not set(row.replace("|", "").strip()) <= set("-: ")
    ]
    assert len(body) >= 5, (
        f"the behavior matrix in {OWNER} is down to {len(body)} data row(s). "
        f"The contract defines five state pairs and every writer walks all "
        f"five; a dropped row is a case some writer silently stops handling")

    # D11's guarded-write rule and its one canonical marker: the distinction a
    # write-surface gate keys on, and the marker this file's own citer test
    # grades every citer against.
    for half in ("Legal (guarded)", "Illegal (unguarded)"):
        assert half in section, (
            f"the {half} half of the guarded-write rule left the owner section "
            f"of {OWNER} -- that rule is the whole distinction between a legal "
            f"CLAUDE.md write and an illegal one, and half a distinction is "
            f"not a rule")
    assert CANONICAL_MARKER in section, (
        f"the canonical marker {CANONICAL_MARKER!r} left the owner section of "
        f"{OWNER}, the one place its spelling is fixed -- a surface using a "
        f"variant is invisible to every gate keying on the marker")

    # D11's bounded cite-site minimum -- the clause the citer test below grades
    # against. Read off the whitespace-collapsed section because the owner wraps
    # this sentence mid-phrase.
    assert CITE_PHRASE in flat, (
        f"the bounded cite-site minimum's phrase {CITE_PHRASE!r} left the "
        f"owner section of {OWNER}; every citer is graded against that exact "
        f"phrase and this section is where it is fixed")
    assert re.search(r"(neither|not carry either|never carries either) probe "
                     r"literal", flat), (
        f"the cite-site minimum's 'neither probe literal' clause left the "
        f"owner section of {OWNER} -- that clause is what makes a legal "
        f"citation distinguishable from a re-duplication")


def test_no_second_file_uses_a_probe_literal():
    # Enumerated by glob, never hand-listed: a hand-maintained list cannot see a
    # new file re-duplicating the definition. The legacy top-level */SKILL.md
    # packages stay out of scope for the same reason the autofix-marker gate keeps
    # them out -- they are policy-frozen deprecation-window copies, not canonical
    # and not a build input.
    arms = _markdown_arms()
    for pattern, files in arms.items():
        assert files, (
            f"the {pattern} arm of the sweep matched nothing -- an enumeration "
            f"that reaches zero files passes vacuously and proves nothing (#142). "
            f"Fix the glob; do not delete the arm")

    sources = sorted({path for files in arms.values() for path in files})
    assert (REPO_ROOT / OWNER) in sources, (
        f"{OWNER} is missing from the sweep -- the owner must be one of the files "
        f"this gate reads, or the gate is checking a tree the contract does not "
        f"live in")

    duplicates = []
    for path in sources:
        if path == REPO_ROOT / OWNER:
            continue
        text = path.read_text(encoding="utf-8")
        for literal in PROBE_LITERALS:
            uses, _ = _scan(text, literal)
            for line_number in uses:
                duplicates.append(f"{_relative(path)}:{line_number} {literal!r}")

    assert not duplicates, (
        f"a designated probe literal is USED (carried bare) outside {OWNER}: "
        f"{duplicates}. Those two strings exist so this gate can tell a legal "
        f"citation from a silent re-duplication of the contract, so a second "
        f"carrier means the definition now has two owners that will drift. Cite "
        f"the owner section instead of copying it. A document that must QUOTE a "
        f"literal may do so inside a backtick code span -- that is a mention, and "
        f"this sweep permits it")


def test_every_citer_carries_only_the_bounded_cite_site_minimum():
    citers = []
    for path in _authored(sorted(REPO_ROOT.glob("skills/**/*.md"))):
        if path == REPO_ROOT / OWNER:
            # The owner is exempt by construction, mirroring the identical guard
            # in the sweep above: it DEFINES the cite phrase -- the bounded
            # cite-site minimum quotes it -- so it is not a citation of itself,
            # and it carries both probe literals by design. Without this guard a
            # harmless re-wrap of that one paragraph (the phrase currently
            # breaks mid-sentence, which is the only reason the line-based scan
            # misses it) would put the owner into `citers` and fail the
            # probe-literal assertion with a message telling the maintainer to
            # delete the contract from its own owner file.
            continue
        text = path.read_text(encoding="utf-8")
        uses, _ = _scan(text, CITE_PHRASE)
        if uses:
            citers.append((_relative(path), text))

    names = [name for name, _ in citers]
    assert len(citers) >= CITER_FLOOR, (
        f"only {len(citers)} file(s) under skills/ carry the bounded cite phrase "
        f"{CITE_PHRASE!r}; the floor is {CITER_FLOOR}, the count derived by this "
        f"same sweep at the commit that introduced the gate. Found: {names}. A "
        f"drop means a citation was deleted, or reworded off the one canonical "
        f"phrase, and that surface now acts on the contract with nothing binding "
        f"it to the owner. Raising the floor when a new citer lands is correct; "
        f"lowering it needs a stated reason")

    for name, text in citers:
        for literal in PROBE_LITERALS:
            uses, mentions = _scan(text, literal)
            assert not uses and not mentions, (
                f"{name} cites the owner AND carries the probe literal "
                f"{literal!r} (lines {sorted(uses + mentions)}). The bounded "
                f"cite-site minimum is the cite phrase plus, where the surface "
                f"must act, the canonical marker {CANONICAL_MARKER!r} -- and "
                f"neither probe literal in any form. Delete the copy and cite "
                f"{OWNER}")
        if "AGENTS.md" in text:
            assert CANONICAL_MARKER in text, (
                f"{name} cites the owner and names AGENTS.md, but never in the "
                f"one canonical spelling {CANONICAL_MARKER!r}. A variant spelling "
                f"is invisible to any gate keying on the marker, so the surface "
                f"would read as if it had never considered both files")


def test_no_shared_file_carries_the_contract():
    """The _shared/ arm, and why it is not redundant with the sweep above.

    Step 100's Done-when carries the clause "no `_shared/` file was created" --
    D6 forbids a shared home for this contract, because a third instruction-
    authoring surface would sit outside both enumeration globs the writers' gates
    use, and a provider adapter could not cite it in any legal spelling. This
    sweep is the ONLY mechanical enforcement of that clause anywhere in the
    repository. It overlaps the _shared/**/*.md arm above on purpose and is
    stricter in two ways -- every file extension, not just markdown, and no
    use/mention allowance, because a shared file has no reason to quote the
    contract either. Do not delete it as redundant.
    """
    files = _authored(
        [path for path in sorted(REPO_ROOT.glob("_shared/**/*")) if path.is_file()])
    assert files, (
        "the _shared/ sweep matched no authored files at all -- it cannot "
        "enforce anything in that state (#142); fix the glob, do not delete "
        "the check")

    carriers = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for literal in PROBE_LITERALS:
            if literal in text:
                carriers.append(f"{_relative(path)} {literal!r}")

    assert not carriers, (
        f"a file under _shared/ carries a designated probe literal: {carriers}. "
        f"The instruction-file contract has deliberately no shared home (D6): its "
        f"one owner is {OWNER}, which every core and adapter cites. Delete the "
        f"shared copy and cite the owner")


def test_no_probe_literal_hides_across_a_line_break():
    """Coarse second arm: a literal broken across a newline.

    Every assertion above is line-based, so a copy-paste that wrapped
    mid-sentence is invisible to all of them -- and that is the likeliest
    ACCIDENTAL duplication shape here, since probe literal 2 is 40 characters
    and these files wrap near column 100. This arm collapses every run of
    whitespace to one space and looks again, reporting what the precise arm
    could not see (counted, so a wrapped second copy beside a visible first one
    still surfaces).

    Deliberately kept OUT of the use/mention logic rather than entangled with
    it: a code span can itself be wrapped, so this arm cannot tell a use from a
    mention. It therefore asks a human to look instead of returning a verdict,
    and its message is worded so it cannot be mistaken for the precise arm's.
    """
    sources = sorted({path for files in _markdown_arms().values() for path in files})
    assert sources, (
        "the whitespace-normalized sweep matched no files at all -- it can "
        "find nothing in that state (#142); fix the globs in _markdown_arms, "
        "do not delete the arm")

    hidden = []
    for path in sources:
        if path == REPO_ROOT / OWNER:
            # Exempt for the same reason as the sweeps above: the owner's own
            # two literals are graded by the owner-section test, which already
            # reds if either stops being carried there.
            continue
        text = path.read_text(encoding="utf-8")
        flat = _normalized(text)
        for literal in PROBE_LITERALS:
            collapsed = flat.count(literal)
            if not collapsed:
                continue
            if "`" + literal + "`" in flat:
                # Margin. The one non-owner file carrying either literal today
                # is the designating plan, whose quote is backticked and sits
                # at collapsed == mentions == 1 -- zero headroom, so a single
                # innocent reflow of that quote would fire this arm. A file
                # whose collapsed text still shows the literal wrapped in
                # backticks is quoting it, which is exactly what the precise
                # arm permits, so this arm stays quiet about it. A BARE wrapped
                # copy -- the accidental-duplication shape this arm exists for
                # -- has no backticks and is still reported.
                continue
            uses, mentions = _scan(text, literal)
            if collapsed > len(uses) + len(mentions):
                hidden.append(f"{_relative(path)} {literal!r}")

    assert not hidden, (
        f"a designated probe literal appears in {hidden} ONLY after whitespace "
        f"normalization -- it is broken across a line, so the precise "
        f"use/mention arm above could not see it at all. This arm cannot tell "
        f"a use from a mention (a code span can itself be wrapped), so it is a "
        f"finding to read rather than a verdict: open the file. If it is a "
        f"re-duplication of the contract, delete it and cite {OWNER}. If it is "
        f"a quotation, put it on one line inside a backtick code span so the "
        f"precise arm can classify it")
