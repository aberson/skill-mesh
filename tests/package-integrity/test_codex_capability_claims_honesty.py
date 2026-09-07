"""Sweep gate: no codex adapter may freeze a runtime host capability into a fact.

Phase CL Step 119 (issue #165). Phase IS C0R proved that "Codex has no isolated
fresh-context agent primitive" is FALSE on at least some real Codex hosts: the
active host exposed explicit no-history child dispatch (`fork_turns="none"`) and
caller-scoped parent execution sessions. Host capability is RUNTIME-DEPENDENT, so
an adapter that states it as a provider-wide constant is not describing the
world -- it is publishing a claim the next host falsifies, and it does so in
prose no behavioral test can see.

Step 119 rewrote the offending adapters into one of two honest forms:

  (a) CAPABILITY-CONDITIONED -- the core requires an isolated fresh-context arm
      and a capable host may supply it. The adapter states the capability as a
      runtime property, CITES the separate build-step agent-isolation contract
      rather than restating its mechanics, and keeps a visible fail-closed
      `required_tool_missing` halt for a host that does not pass it.
  (b) HONEST SCOPED REFUSAL -- the wrapper does not map the primitive, so the
      core's own halt (or a fallback the core genuinely documents) is what runs.
      Phrased as a statement about THIS WRAPPER'S MAPPING or about what the CORE
      requires, never as a claim of fact about what the provider lacks.

Form (a) is only correct when the capability the ADAPTER conditions on is the
capability the OWNING CORE actually requires. Two cores in this set need the host
WORKFLOW primitive (`_shared/score_skill.workflow.js`), which an agent-isolation
probe says nothing about; one needs a VISION-capable child in addition to an
isolated one. Those are pinned by name below, because conditioning a mandatory
halt on the wrong axis is invisible to every other gate here.

WHAT THIS GATE IS, AND IS NOT
-----------------------------
It is a LEXICAL deny-sweep over authored English prose, and a lexical deny-sweep
over English prose CANNOT be made evasion-proof. The artifact under contract IS
free prose -- the consumer is the host model reading the wrapper -- so paraphrase
space is unbounded and any must-not-match list can only ever pin the phrasings
already seen plus a bounded neighbourhood around them. Three hardening rounds
have not changed that and a fourth would not either.

So read a green sweep as "no phrasing family this gate knows is present", NEVER
as "no stale provider-wide claim is present". This is a tripwire against
ACCIDENTAL drift-back -- an author paraphrasing the deleted sentences, or
stopping halfway through a rewrite into the conditional register -- not a proof
of honesty. Against a deliberate evasion it is worth nothing, but so is any test
the evader can edit. Human review is the primary control; this gate is beneath
it.

The file's STRONG half is its positive, presence-based obligations: the
manifest-sourced co-located-halt requirement, the contract-citation requirement,
and the fallback-polarity requirement. Presence checks are rewording-robust,
because machinery is hard to drop by accident. The negative sweep is the
structurally weak half. Effort spent widening the deny-list has a floor it
cannot go below; effort spent on the presence checks does not.

THE SCOPE INVARIANT (read before editing any predicate here)
------------------------------------------------------------
Every predicate and every exemption in this file must be scoped to exactly the
grammatical unit that carries the semantic property it tests. All four defects
this file shipped and repaired were the same mistake at different vectors:

  * a check one unit too WIDE is satisfied or excused by unrelated text -- a
    FILE-scoped halt check that universal boilerplate satisfies; a SENTENCE-scoped
    conditional exemption that excuses a main clause the conditional never
    covered (measured: 352 of 352 planted-claim x opener x construction
    combinations escaped);
  * a check one unit too NARROW is escaped by one inserted word -- bare token
    adjacency defeated by `Codex CLI has no ...`; a single literal defeated by
    the synonym `A host satisfying ...`.

Each predicate below therefore states its unit. When you add one, state its unit
too, and add the matching corpus axis in the same edit (see CORPUS CLOSURE).

CORPUS CLOSURE
--------------
Every exemption is attack surface, and a hand-maintained corpus goes blind to the
axis the newest exemption opened -- that is exactly how the sentence-scoped
exemption shipped past a 22-row planted corpus in which ZERO rows began with a
conditional opener. So the conditional corpus is GENERATED, not hand-listed: the
full cross product of every planted claim x every opener x both constructions
(claim in the conditional clause, claim in the main clause). Two independent
reviewers each proposed a one-line repair; each killed only its own reviewer's
construction and left the other's green, which is the proof that hand-adding "one
opener row" would have re-created the blindness at the next construction.

The same blindness then repeated at two further axes of the SAME exemption, and
both are generated now as well:

  * LEADING TABLE CELL -- the exemption graded `_LEAD_RE`-stripped text, so a
    claim whose provider subject sat in a contract table's first cell was
    dropped before grading. EVERY row of the axis escaped: 232 of 232, over the
    29 planted claims that admit a subject-bearing cell inside the strip's bound.
  * CLAUSE TERMINATOR -- the exemption cut the conditional clause at the first
    COMMA, so an author closing the clause with `;`, `:` or an em dash handed the
    claim's own subject to the exempted head. 48 escapes.

Both are cross products over the same seed tuples, sized by `MIN_PLANTED` x
`MIN_OPENERS`, so neither axis can shrink without the corpus floor reding.
Together: 280 escapes of 3067 generated rows, closed to 0, with no verdict
changed on any negative axis.

SIZE IS NOT DISCRIMINATION, and the terminator axis is where that bites. Only a
claim whose subject and lack-verb straddle a comma can expose a mis-placed cut,
so all 2240 of its rows rest on the 2 seed claims that have that shape --
`MIN_COMMA_STRADDLING` floors the PROPERTY, because a row count cannot see it.
The same asymmetry governs which terminators may be added at all: a cut point
`_CLAIM_RE` can reach ACROSS splits claims instead of clauses, so ASCII `--` is
excluded by measurement (8 escapes closed, 208 opened) and the exclusion is
asserted rather than remembered.

STANDING RULE: any new exemption axis in the detector ships a matching generated
transformation axis in the corpus, in the same edit. The corpus itself is
FLOORED, because the axis generators multiply a seed tuple and an empty seed
multiplies to an empty axis that reports a comfortable PASS.

The FALSE-POSITIVE direction is enumerated from the live tree rather than
hand-listed too: every conditional-opener sentence in the shipped adapters must
stay silent, with a floor so the check cannot go vacuous. Read that harvest for
exactly what it is. It is 73 sentence INSTANCES but only 21 distinct strings,
and 71 of the 73 carry no isolation noun at all, so they exit at the topic
filter before any exemption logic runs: 2 distinct rows can reach the claim
predicate and 1 of those also states a lack. "73 live conditionals silent" is a
VACUITY check on the harvest, not 73 independent false-positive rows -- deleting
both discriminating rows still leaves 71 over a floor of 40. The real
false-positive guard is the main sweep, which grades all 1455 non-empty
sentences of all 54 adapters with the identical predicate and of which this
harvest is a strict subset.

THE DETECTOR'S DOCUMENTED BOUNDARY
----------------------------------
`DOCUMENTED_MISSES` below enumerates the shapes this detector deliberately does
NOT catch, so a future reader can tell "considered and descoped" from "never
considered". Three axes, all measured:

  * GAP BOUND -- a subject reaches its lack-verb across at most three intervening
    tokens. Widening measured free today, but every extra token buys reach across
    a clause boundary ("Codex is fine but the host cannot ..."), so the bound
    stays and the cost is recorded instead.
  * INFERENTIAL -- "Codex provides only a single conversational context, so no
    isolated arm exists" states the lack by implication, with no lack-verb
    reaching the provider at all. Catching implication lexically is out of scope.
  * FRONTED PREPOSITIONAL -- "On Codex there is no sub-agent primitive" puts the
    provider before the negation in a prepositional phrase.
  * UNPUNCTUATED CLAUSE BOUNDARY -- the exempted conditional clause is cut at the
    first member of `_CLAUSE_TERMINATORS`. An author who closes the clause with
    punctuation outside that set ("If the lenses fan out (on this host) Codex,
    however, lacks ...") puts the boundary somewhere the cut cannot find, and the
    provider subject stays in the exempted head. Widening the set to chase it was
    measured free on the live tree today, but each extra member moves the cut
    EARLIER in every sentence it matches, so the set stays the five real clause
    terminators and the residual is recorded here instead.

Two OVER-fire bands are accepted for the same reason, both measured at zero live
instances across all 54 adapters:

  * a sentence whose lack-verb and whose isolation noun belong to different
    clauses ("Codex has no Artifact tool, so the isolated reviewer report is
    written by path"). Binding the isolation noun to the verb's object would cost
    more false negatives than it buys;
  * a sentence QUOTING the forbidden claim in order to forbid it ("Never assert
    that Codex has no isolated agent primitive"). Excusing negated frames would
    hand every reintroduction a one-word disguise, which is strictly the worse
    trade -- an author who needs to quote the claim writes it about "the host".

THE SECOND DETECTOR'S BOUNDARY
------------------------------
`_is_capability_conditioned` is the OTHER predicate in this file, and both
unconditionality pins (`review-deep`'s DS-D3 halt, the two workflow-primitive
cores) rest on it returning False. It carries its own measured boundary, in
`DOCUMENTED_CONDITIONING_MISSES` and the over-fire tuple beside it, for exactly
the reason the claim detector carries one: a reader who trusts a docstring over
a measurement is the failure this file exists to prevent.

Its scope is a MODAL permission -- `may map/dispatch/spawn/run` reaching an
isolation noun within 120 characters -- plus the one literal `CAPABILITY_MARKER`.
It does not see three neighbouring registers: a permission verb outside that set
("is permitted to", "is free to", "are allowed to"), a bare declarative with no
modal at all ("Capable hosts map each lens onto a separate no-history child"),
and a fronted conditional whose main clause carries the permission ("If the probe
succeeds, dispatch each lens in its own fresh context"). Twelve measured
rewordings live in the tuple. It also OVER-fires on a prohibition spelled with
the same modal ("No host may dispatch a fresh isolated child ... under DS-D3"),
which is the strongest possible statement of the thing the pin protects. Both
bands are zero-live-instance today: the literal set and the meaning-class set
resolve to the same 10 adapters, symmetric difference empty.

The boundary is RECORDED rather than closed on purpose. Widening this predicate
changes which adapters `_conditioned_adapters` selects, and so which adapters
must carry a cited contract and a co-located halt -- a behavior change to four
gates, bought by appending an alternation nobody measured. Deciding those axes
is its own edit with its own review.

ENUMERATED, NEVER HAND-LISTED
-----------------------------
The adapter roster is walked from the filesystem AND cross-checked against the
manifest's own codex-authored set, because a hand-maintained gate list is a false
green. The subject set for the fail-closed halt gate is likewise taken from the
manifest's `sub-agent` capability field -- NOT from the adapter's own prose. An
earlier draft derived it by regexing each adapter for "no single-context
fallback", which let any adapter drop out of its own gate by softening one
clause; the manifest is an independent source an author has to edit on purpose.

The three skills named individually here are named because they are EXCEPTIONS
whose reasons live outside the manifest: `review-deep` (accepted gap DS-D3),
`skill-evolve` and `skill-iterate` (workflow primitive, not agent isolation),
plus `judge-ui`'s second conjunct.

BYTES ARE NEWLINE-NORMALIZED before anything is matched (CRLF and lone CR -> LF).
Two files in one working tree can carry different checkout-era line endings, so a
raw comparison reds on clone noise rather than content; see
`test_review_deep_scripts_duplication.py` for the incident this rule comes from.
"""

import ast
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
NEIGHBOUR_GATE = Path(__file__).with_name("test_codex_agent_isolation_contract.py")

# The roster size is pinned EXPLICITLY, not just floored. A 55th codex skill
# moves this number in the same commit that adds the skill -- deliberate, and
# reviewable. The floor below is the separate guard against a mis-rooted glob
# making every assertion in this module vacuous; both are asserted because they
# fail for different reasons.
EXPECTED_ADAPTERS = 54
MIN_ADAPTERS = 50

# One owner per threshold. Each of these was an inline literal duplicated across
# two tests before Step 119 iteration 3; two hand-maintained copies of one
# threshold drift the first time someone moves one (CLAUDE.md, "One source of
# truth for data-shape constants").
MIN_SUB_AGENT = 12          # manifest `sub-agent` codex skills (live: 16)
MIN_CONDITIONED = 8         # capability-conditioned adapters (live: 10)
MIN_FALLBACK_SENTENCES = 10  # adapters naming a single-context fallback (live: 13)

# A VACUITY floor on the harvest, and nothing more. The 73 live instances are 21
# distinct strings, of which 2 carry an isolation noun and 1 also states a lack;
# the other 71 exit at `_ISOLATION_RE` before any exemption logic runs. Deleting
# both discriminating rows still leaves 71 over this floor, so do not read a
# green here as 73 independent false-positive rows -- see the module docstring.
MIN_LIVE_CONDITIONALS = 40  # conditional-opener sentence INSTANCES (live: 73)

# The calibration corpus, and the two seed tuples every generated axis multiplies.
# `PLANTED_CLAIMS` was the one quantity in this file with no floor at all, so
# `PLANTED_CLAIMS = ()` left all 20 tests green over a corpus of nothing -- after
# which the detector could be narrowed to nothing too and the sweep would still
# report a comfortable PASS over 54 clean adapters. Two reviewers found it
# independently and proved it by source mutation.
MIN_PLANTED = 30            # planted provider-wide claims (live: 34)
# Zero slack, deliberately: this is the one entry here that is really a PIN.
# Losing an opener is safe for the DETECTOR (fewer exemptions means more catches)
# and fatal for the CORPUS, because every generated axis is sized by it. So it
# moves in the same commit that moves `CONDITIONAL_OPENERS`, like
# `EXPECTED_ADAPTERS` above -- deliberate, and reviewable.
MIN_OPENERS = 8             # conditional openers (live: 8)
# Size is not discrimination. The clause-terminator axis generates thousands of
# rows and discriminates only on claims that straddle a comma; at one such row
# the axis had a single point of failure that would have deleted silently.
MIN_COMMA_STRADDLING = 2    # comma-straddling planted claims (live: 2)

# The two boundary RECORDS. Neither had a floor, and an emptied boundary tuple
# passes its own test over nothing -- the same vacuity class as the corpus above,
# and the one that blocked iteration 3. They matter more than most: a boundary
# record is what a future reader consults to tell "considered and descoped" from
# "never considered", so an empty one is worse than absent.
MIN_DOCUMENTED_MISSES = 8       # claim-detector boundary rows (live: 11)
MIN_CONDITIONING_MISSES = 10    # conditioning-predicate misses (live: 12)
MIN_CONDITIONING_OVER_FIRES = 3  # conditioning-predicate over-fires (live: 3)

# --------------------------------------------------------------------------- #
# The provider-wide-claim detector
#
# SCOPE LEDGER -- each predicate, the grammatical unit it is scoped to, and why
# that is the right unit. See THE SCOPE INVARIANT in the module docstring.
#
#   _SUBJECT              noun phrase   the thing a provider-wide claim is ABOUT
#   _GAP                  <= 3 tokens   how far a subject may reach its own verb
#   _LACK_VERB            verb phrase   the assertion of absence itself
#   _TRAILING_CLAIM_RE    bounded span  the mirror order, provider trailing
#   _QUANTIFIED_CLAIM_RE  bounded span  "No Codex host exposes ..." -- negation
#                                       on the SUBJECT, affirmative verb
#   _ISOLATION_RE         sentence      the TOPIC: is this sentence about the
#                                       isolation capability at all? The noun may
#                                       sit either side of the verb, so sentence
#                                       is the unit -- narrower loses the
#                                       "a capability Codex lacks" order.
#   _CONDITIONAL_OPENER   clause head   does this sentence OPEN a runtime
#                                       conditional?
#   the exemption         CLAUSE        exempts the conditional clause ONLY, and
#                                       always grades the remainder. Sentence
#                                       scope here was the iteration-2 defect.
#   _OPENS_ON_PROVIDER    clause head   forfeits the exemption when the PROVIDER
#                                       is the conditional's own subject
#   _CLAUSE_TERMINATORS   clause bound  where the exempted conditional clause
#                                       ENDS. Comma-only was the iteration-3
#                                       defect: it cut inside a comma-bearing
#                                       claim whenever the author closed the
#                                       clause with `;`, `:` or a dash.
#   _LEAD_RE              furniture     used ONLY to FIND the opener. A table's
#                                       first cell is content, so the stripped
#                                       lead is RE-ATTACHED before grading and
#                                       the strip can never remove text the
#                                       grading would have reached.
#   _SENTENCE_RE          sentence      the split unit for the whole sweep
#   _is_capability_conditioned  FILE    the second detector: a modal permission
#                                       to map an isolated arm onto a child.
#                                       File scope because a permission granted
#                                       anywhere in a wrapper is granted. Its
#                                       measured boundary is a tuple, not a
#                                       claim -- see its docstring.
# --------------------------------------------------------------------------- #

# A provider subject, with the qualifiers an author actually reaches for.
# "the host" / "the active host" / "this wrapper" are deliberately NOT here:
# those are the honest subjects and are what the repaired adapters use.
_SUBJECT = (r"(?:(?:the|a|an|this)\s+)?codex"
            r"(?:\s+(?:cli|host|hosts|profile|session|sessions|model|models))?"
            r"|(?:the|this)\s+provider")

# Up to three intervening tokens, commas and TABLE PIPES allowed. This is what
# makes the gate survive "Codex CLI has no ...", "Codex simply has no ...",
# "Codex, however, lacks ...", and `| codex | has no isolated primitive |`. The
# bound is what keeps it from reaching across a clause boundary; it is a
# documented limit, not an oversight (see DOCUMENTED_MISSES).
_GAP = r"(?:[,\s|]+[\w/-]+){0,3}[,\s|]+"

_LACK_VERB = (r"(?:has no|have no|had no|has zero|have zero"
              r"|lacks|lack|omits|omit|cannot|can not"
              r"|does not (?:have|expose|provide|support|implement|offer|supply)"
              r"|do not (?:have|expose|provide|support|implement|offer|supply)"
              r"|offers no|provides no|exposes no|supports no"
              r"|fails to (?:have|expose|provide|support|offer|supply)"
              r"|fail to (?:have|expose|provide|support|offer|supply)"
              r"|has never|have never"
              r"|(?:will |would |can )?never (?:have|had|exposes?|provides?"
              r"|offers?|supplies|supplied|supply)"
              r"|is missing|are missing|is without|are without"
              r"|is unable to|are unable to|is not able to"
              # The modal form. `skill-eval-setup` shipped "because Codex itself
              # could not honor it" through the adjacency-only draft.
              r"|could not(?:\s+\w+)?)")

# The capability class this sweep is about. Tool names (Artifact), tier peers,
# session identity, and window primitives are deliberately absent.
_ISOLATION = (r"(?:isolat\w*|fresh[- ]context|agent primitive"
              r"|workflow primitive|sub-?agent"
              r"|no-history|parent[- ]state|private-parent-state)")

# An adjectival lack, for the mirror order where no verb reaches the provider.
_LACK_ADJ = r"(?:unavailable|not available|absent|impossible|unsupported|missing)"
_PREP = r"(?:in|on|for|from|to|under|with)"

_CLAIM_RE = re.compile(rf"\b(?:{_SUBJECT})\b{_GAP}{_LACK_VERB}\b", re.IGNORECASE)

# The mirror shape, where the provider trails its own claim: "There is no
# isolated fresh-context primitive in Codex", "Sub-agent fan-out is impossible on
# Codex". Bounded the same way.
_TRAILING_CLAIM_RE = re.compile(
    rf"(?:\bno\b(?:[\s,]+[\w/-]+){{0,6}}[\s,]+{_PREP}\s+(?:the\s+)?codex\b"
    rf"|\b{_LACK_ADJ}(?:\s+[\w/-]+){{0,2}}[\s,]+{_PREP}\s+(?:the\s+)?codex\b)",
    re.IGNORECASE)

# The quantified shape: the negation rides the SUBJECT and the verb stays
# affirmative -- "No Codex host exposes an isolated primitive". The gap is one
# token, not three, so "no codex adapter may map ..." (an instruction, not a
# claim) cannot reach a verb.
_QUANTIFIED_CLAIM_RE = re.compile(
    rf"\bno\s+(?:{_SUBJECT})\b(?:[,\s|]+[\w/-]+){{0,1}}[,\s|]+"
    r"(?:has|have|exposes?|provides?|offers?|supplies|supports?|implements?)\b",
    re.IGNORECASE)

_ISOLATION_RE = re.compile(_ISOLATION, re.IGNORECASE)

# The opener set is DATA, not a regex literal, because the generated closure
# corpus below has to iterate exactly the openers the exemption honors. Two
# hand-maintained copies of this list is the drift shape CLAUDE.md forbids, and
# here it would silently shrink the corpus rather than fail.
CONDITIONAL_OPENERS = ("if", "when", "where", "unless", "whenever",
                       "on a host", "for a host", "absent")
_OPENER_ALT = "|".join(CONDITIONAL_OPENERS)

# A sentence that OPENS with a runtime conditional is describing a host at run
# time, not asserting a provider constant. This exemption -- not verb adjacency
# -- is what keeps the exemplar adapters' correct form writable.
_CONDITIONAL_OPENER_RE = re.compile(rf"^(?:{_OPENER_ALT})\b", re.IGNORECASE)

# ... but the exemption is EARNED by using a runtime subject. When the provider
# itself is the conditional's subject ("When Codex, however, lacks ..."), the
# clause is a claim wearing a conditional costume and forfeits the exemption.
# The live exemplar passes because its conditional subject is "the active host",
# with "ordinary Codex CLI" only a predicate complement further in.
_OPENS_ON_PROVIDER_RE = re.compile(rf"^(?:{_OPENER_ALT})\s+(?:{_SUBJECT})\b",
                                   re.IGNORECASE)

# Markdown furniture to strip before testing the opener: list bullets, and the
# ONE short leading field-name cell of a contract-table row (the exemplars'
# conditionals live in `| \`missing-capability\` | If the host lacks ... |`).
# Bounded to a 40-char first cell on purpose: a greedy "strip every cell" form
# blanks the whole row, which silently exempts contract tables from the gate.
#
# The strip's ONLY job is to find the opener. It is not a grading decision, and
# `_asserts_provider_wide` RE-ATTACHES the stripped lead before grading. The
# earlier spelling claimed the same thing in this comment while the code did the
# opposite -- `graded` was a slice of the STRIPPED body -- so every claim whose
# subject sat in a leading cell was dropped: `| Codex | If the lenses fan out,
# has no isolated fresh-context agent primitive. |` measured silent, and so was
# every other row of the generated table axis: 232 of 232. The re-attachment,
# not this comment, is what makes this true now.
_LEAD_RE = re.compile(r"^\s*(?:[-*+]\s+|>\s*|#+\s+)*(?:\|\s*[^|\n]{0,40}\|\s*)?")

# Where a fronted conditional clause ENDS. DATA, not a regex literal, because the
# generated corpus axis below has to iterate exactly the terminators the split
# honors -- the same one-source-of-truth reason `CONDITIONAL_OPENERS` is a tuple.
#
# `body.partition(",")` was the earlier spelling, and a comma is only the most
# common terminator, not the only one. When the author closed the clause with a
# semicolon, a colon or a dash, the cut landed at the first comma INSIDE the
# claim instead, handing the claim's own provider subject to the exempted head:
# `If the lenses fan out; Codex, however, lacks an isolated agent primitive.`
# measured silent, 48 escapes across the three. The em dash (U+2014) is here because
# an author pasting from a document editor produces one, and it escapes at the
# identical rate; it is spelled as an escape so this file stays ASCII, which
# `tests/package-integrity` gates and every adapter in the tree already is.
#
# ASCII `--` is DELIBERATELY ABSENT, and this is the load-bearing part of the
# tuple. A cut point is only safe if `_CLAIM_RE` cannot reach ACROSS it, because
# cutting inside a claim splits it: neither the exempted head nor the graded
# remainder then carries a whole one. `_GAP`'s token class `[\w/-]+` matches the
# token `--`, so a claim CAN span it -- `;`, `:` and U+2014 sit in neither
# `[,\s|]` nor `[\w/-]` and cannot be spanned. Adding `--` was measured net
# NEGATIVE: it closed 8 `--`-closed-clause escapes and opened 208 of 224
# grammatical spaced-dash appositives that the comma-only spelling had caught
# (`If the lenses fan out and the tier is Codex -- which has no isolated
# fresh-context agent primitive -- serialize the lenses.`). The residual it
# leaves is recorded in `DOCUMENTED_MISSES`, and the invariant that keeps a
# future author from re-adding it is asserted, not written down here.
#
# The comma is the ONE spannable member, kept because the live exemplar this
# whole exemption exists for straddles its own comma in exactly that shape
# (`ALLOWED_ROWS[3]`). Forfeiting the exemption on a split claim was measured and
# rejected for that reason: it over-fires on that row and on the shipped
# `user-debug` adapter.
_CLAUSE_TERMINATORS = (",", ";", ":", "\u2014")
_CLAUSE_END_RE = re.compile(
    r"\s*(?:%s)\s*" % "|".join(re.escape(t) for t in _CLAUSE_TERMINATORS))

# Sentence split. Coarse on purpose: the isolation noun may sit on EITHER side of
# the verb ("a private-parent-state capability Codex lacks" put it first), so the
# scope has to be the sentence rather than a forward window.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n")


def _normalized(raw):
    """Decode file bytes with CRLF and lone CR read as LF."""
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode("utf-8")


def _states_a_lack(text):
    """Does this SPAN assert a provider lacking something? Three orders, one
    predicate, so every caller grades all three and none can drift.
    """
    return bool(_CLAIM_RE.search(text)
                or _TRAILING_CLAIM_RE.search(text)
                or _QUANTIFIED_CLAIM_RE.search(text))


def _lead_and_body(sentence):
    """(markdown furniture, the rest of the sentence).

    ONE owner for the strip. The detector and the live-conditional harvest must
    agree on where the opener starts, or the harvest grades a set the detector
    never sees -- two copies of one split rule is the drift shape CLAUDE.md
    forbids. Returned as a pair rather than substituted away because the lead is
    content the detector has to grade, not text it may discard.
    """
    lead = _LEAD_RE.match(sentence).group(0)
    return lead, sentence[len(lead):]


def _split_conditional_clause(body):
    """(the fronted conditional clause, everything after it).

    The clause ends at the FIRST member of `_CLAUSE_TERMINATORS`. An unterminated
    body is all clause and no remainder, which is the safe direction: the whole
    body then has to survive `_states_a_lack` for the exemption to be granted.
    """
    end = _CLAUSE_END_RE.search(body)
    if not end:
        return body, ""
    return body[:end.start()], body[end.end():]


def _asserts_provider_wide(sentence):
    """The detector. Exemption scoped to the CLAUSE; grading scoped to the rest.

    The iteration-2 defect was returning False for the whole sentence on an
    opener match, which let `When the lenses fan out, <any planted claim>` ship
    clean. The repair exempts exactly the conditional clause and ALWAYS grades
    the remainder, and forfeits the exemption entirely when the clause itself
    carries the claim -- in either of the two constructions two reviewers
    measured separately.

    Iteration 3 closed the two ways that repair still LOST text. `graded` was a
    slice of the `_LEAD_RE`-stripped body, so a claim whose subject sat in a
    table row's leading cell was never graded (232 of 232 such rows silent); and
    the clause was cut at the first COMMA rather than at a clause terminator, so
    a `;`/`:`/em-dash-closed clause swallowed the subject of a comma-bearing
    claim (48 in all). Both are the same mistake in the SCOPE INVARIANT's terms:
    the exemption removed more than the clause. It now removes exactly the
    clause -- the lead is re-attached, and the cut is at the real boundary -- so
    every character of the sentence that is not the conditional clause is
    graded. Measured together: 280 escapes of 3067 generated rows closed to 0,
    with no verdict changed on any negative axis -- and, after the dash finding
    below, none lost on the spaced-dash appositive register either (264 caught
    before, 264 after).
    """
    lead, body = _lead_and_body(sentence)
    graded = sentence
    if _CONDITIONAL_OPENER_RE.match(body):
        head, tail = _split_conditional_clause(body)
        if not _states_a_lack(head) and not _OPENS_ON_PROVIDER_RE.match(body):
            # The lead is furniture for FINDING the opener and CONTENT for
            # grading it, so it goes back on. Dropping it is what exempted a
            # whole contract table's first column from this gate.
            graded = lead + tail
    # Topic filter: sentence-scoped, on the UNSTRIPPED sentence.
    if not _ISOLATION_RE.search(sentence):
        return False
    return _states_a_lack(graded)


def _claim_sentences(text):
    """Every sentence asserting a provider-wide isolation capability."""
    return [sentence.strip()
            for sentence in _SENTENCE_RE.split(text)
            if _asserts_provider_wide(sentence)]


# --------------------------------------------------------------------------- #
# Roster (enumerated, never hand-listed)
# --------------------------------------------------------------------------- #

def _adapter_paths():
    """{skill name -> codex adapter path}, walked from the filesystem."""
    return {path.parents[1].name: path
            for path in REPO_ROOT.glob("skills/*/providers/codex.md")}


def _manifest_skills():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["skills"]


def _manifest_codex_names():
    return {s["name"] for s in _manifest_skills() if "codex" in s["providers"]}


def _manifest_sub_agent_codex_names():
    """The `sub-agent` capability set, intersected with the codex roster.

    INDEPENDENT of the adapter prose on purpose (see the module docstring). The
    floor lives HERE so every consumer inherits it -- one gate used to read this
    set with no floor of its own and went vacuously green under four measured
    manifest-degradation scenarios.
    """
    names = {s["name"] for s in _manifest_skills()
             if "codex" in s["providers"]
             and "sub-agent" in s.get("capabilities", [])}
    assert len(names) >= MIN_SUB_AGENT, (
        f"only {len(names)} codex adapters declare the `sub-agent` capability "
        f"({sorted(names)}) -- every gate keyed on this set would be "
        "near-vacuous. Check the manifest field before relaxing this floor.")
    return names


def _adapter_texts():
    """Every codex adapter, newline-normalized, with the vacuity floor applied.

    The floor lives HERE so every consumer inherits it: a mis-rooted glob must
    not let a tree-walking gate report a comfortable PASS over nothing. Same
    placement as `test_review_deep_scripts_duplication.py`'s `MIN_LEAVES`.
    """
    texts = {name: _normalized(path.read_bytes())
             for name, path in _adapter_paths().items()}
    assert len(texts) >= MIN_ADAPTERS, (
        f"only {len(texts)} codex adapters found under skills/*/providers/ -- "
        "every assertion in this module would be near-vacuous. Check the glob "
        "root before relaxing this floor.")
    return texts


def test_adapter_roster_is_enumerated_and_agrees_with_the_manifest():
    """The swept set is derived twice and the two derivations must agree.

    A codex.md on disk with no manifest row ships nothing; a manifest row with no
    codex.md declares a package that does not exist. Either way the sweep would
    be grading a set that is not the shipped one.
    """
    on_disk = set(_adapter_paths())
    declared = _manifest_codex_names()
    assert len(on_disk) == EXPECTED_ADAPTERS, (
        f"the codex adapter roster is {len(on_disk)}, not {EXPECTED_ADAPTERS}. "
        "If a skill was added or removed, move this pin in the same commit; if "
        "it was not, the glob is finding the wrong tree.")
    assert on_disk == declared, (
        "the codex adapter roster disagrees with the manifest:\n"
        f"  on disk only: {sorted(on_disk - declared)}\n"
        f"  declared only: {sorted(declared - on_disk)}")
    assert _manifest_sub_agent_codex_names() <= declared, (
        "the manifest declares a `sub-agent` codex skill with no codex adapter")


# --------------------------------------------------------------------------- #
# The sweep gate
# --------------------------------------------------------------------------- #

def test_no_adapter_asserts_a_provider_wide_isolation_capability():
    """The gate proper: zero provider-wide host-capability assertions."""
    defects = []
    for name, text in sorted(_adapter_texts().items()):
        for sentence in _claim_sentences(text):
            defects.append(f"{name}: {sentence}")
    assert not defects, (
        "a codex adapter states a runtime-variable host capability as a "
        "provider-wide fact. Phase IS C0R proved this class of claim FALSE on "
        "real hosts. Rewrite it as a runtime capability condition (citing the "
        "build-step agent-isolation contract) or as an honest statement about "
        "THIS WRAPPER'S mapping / what the CORE requires:\n  "
        + "\n  ".join(defects))


# Historical spellings the sweep removed, PLUS every reworded reintroduction two
# independent reviewers demonstrated against this file's first draft. The
# rewordings are the point: a gate that only recognizes yesterday's exact strings
# proves nothing, because the strings no longer exist to be recognized.
#
# This tuple is the SEED for every generated corpus axis below. Adding one row
# here adds rows to all three -- 16 conditional, 8 table-row (if the claim admits
# a subject-bearing leading cell), and 8 per clause terminator; that is the
# intended coupling, and it is why the tuple is floored rather than trusted.
PLANTED_CLAIMS = (
    # The three dominant historical spellings.
    "Codex has no isolated fresh-context agent primitive.",
    "Codex has no Agent/Workflow primitive: use the single-context fallback.",
    "Codex lacks any isolated-agent capability.",
    # Isolation noun BEFORE the verb (the sentence scope, not a forward window).
    "It halts when it reaches work requiring a private-parent-state capability "
    "Codex lacks.",
    # Other verb branches.
    "Codex cannot dispatch a no-history child.",
    "Codex does not support sub-agent fan-out.",
    "The provider offers no fresh-context dispatch.",
    "This provider provides no isolated agent primitive.",
    "Codex exposes no no-history dispatch mode.",
    # Reworded reintroductions -- one qualifying noun, one adverb, one comma,
    # one determiner. Every one of these defeated the adjacency-only draft.
    "Codex CLI has no isolated fresh-context agent primitive.",
    "The Codex CLI lacks an isolated agent primitive.",
    "Codex simply has no isolated fresh-context agent primitive.",
    "Codex, however, lacks an isolated agent primitive.",
    # A SECOND comma-straddling row, and not decoration: the clause-terminator
    # axis discriminates only on claims whose subject and lack-verb sit on
    # opposite sides of a comma, because the cut has to land INSIDE the claim to
    # hide it. With one such row the whole 2240-row axis rested on that row, and
    # deleting it would have left the axis green and inert. Floored below.
    "Codex, in practice, has no isolated fresh-context agent primitive.",
    "Codex currently has no fresh-context dispatch.",
    "Codex today has no isolated fresh-context agent primitive.",
    "The Codex host has no isolated fresh-context agent primitive.",
    "Codex hosts have no isolated agent primitive.",
    "Codex never exposes an isolated fresh-context primitive.",
    "Codex is missing an isolated agent primitive.",
    "Codex has never had a fresh-context agent primitive.",
    # The modal form, which shipped in `skill-eval-setup` until this step.
    "It must not soften the fresh-context-grader wording because Codex itself "
    "could not honor it.",
    # The provider trailing its own claim.
    "There is no isolated fresh-context agent primitive in Codex.",
    # Verb spellings a third review round demonstrated against the iteration-2
    # detector, one per branch added to `_LACK_VERB` / `_TRAILING_CLAIM_RE` /
    # `_QUANTIFIED_CLAIM_RE`.
    "Codex does not implement isolated fresh-context dispatch.",
    "Codex fails to provide an isolated agent primitive.",
    "Codex will never have an isolated agent primitive.",
    "Codex is without an isolated fresh-context agent primitive.",
    "Codex omits any no-history child dispatch.",
    "Codex has zero support for isolated fresh-context children.",
    "Sub-agent fan-out is impossible on Codex.",
    "A fresh-context agent primitive is absent from Codex.",
    "Isolated fresh-context dispatch is unavailable on Codex.",
    "No Codex host exposes an isolated fresh-context agent primitive.",
    # The table-row order, whose subject sits in a short first cell. Grading the
    # STRIPPED body hid this one entirely.
    "| Codex has no isolated agent primitive | dispatch is serialized |",
    "| codex | has no isolated fresh-context agent primitive |",
)


def _corpus():
    """(planted claims, conditional openers), with the vacuity floor applied.

    The floor lives HERE so every consumer inherits it, the same placement as
    `MIN_ADAPTERS` inside `_adapter_texts` and `MIN_SUB_AGENT` inside
    `_manifest_sub_agent_codex_names`. These two tuples ARE the calibration
    corpus and every generated axis is their cross product, so an empty seed
    multiplies to an empty axis that reports a comfortable PASS: measured,
    `PLANTED_CLAIMS = ()` left all 20 tests in this file green, and
    `CONDITIONAL_OPENERS = ("if",)` shrank the closure corpus from 544 rows to
    68 with no test noticing. That was the third instance of the vacuous-pass
    class in this step, and the first two were fixed by exactly this placement.

    The two seeds fail DIFFERENTLY and so are asserted separately. An empty
    claims tuple is vacuity -- there is nothing left to catch. A short opener
    tuple is not: the axes stay populated and every row is still caught, so the
    honest complaint is that a PIN moved, not that a gate went vacuous.

    Scope note, because the earlier spelling of this docstring overstated it:
    these were not the only unfloored quantities in the file. `DOCUMENTED_MISSES`
    and `CONDITIONING_OVER_FIRES` were unfloored too and are floored now;
    `ALLOWED_ROWS` still is not, deliberately -- its test also grades the
    floored live harvest, so emptying it cannot take the whole check to nothing.
    """
    assert len(PLANTED_CLAIMS) >= MIN_PLANTED, (
        f"the planted-claim corpus is {len(PLANTED_CLAIMS)} rows, under the "
        f"floor of {MIN_PLANTED}. Every generated axis is a cross product of "
        "this tuple, so all of them shrink with it and an empty one reports a "
        "comfortable PASS over nothing. Add corpus rows; do not lower the floor.")
    assert len(CONDITIONAL_OPENERS) >= MIN_OPENERS, (
        f"`CONDITIONAL_OPENERS` is {len(CONDITIONAL_OPENERS)}, under the pin of "
        f"{MIN_OPENERS}. The axes stay populated and still catch every row, so "
        "this is not vacuity -- it is a PIN moving. Losing an opener is safe "
        "for the detector and fatal for the corpus, so it moves in the same "
        "commit that moves the tuple, like `EXPECTED_ADAPTERS`.")
    return PLANTED_CLAIMS, CONDITIONAL_OPENERS


def test_claim_detector_reds_on_every_planted_provider_wide_claim():
    """Red-on-garbage anchor, reported as one list so no miss hides.

    Without this the detector could be narrowed to nothing and the gate above
    would still report a comfortable PASS over 54 clean files. The reworded rows
    are load-bearing: the shape is what must be caught, not the string.
    """
    claims, _ = _corpus()
    missed = [claim for claim in claims if not _claim_sentences(claim)]
    assert not missed, (
        f"the detector missed {len(missed)} of {len(claims)} planted "
        "provider-wide claims -- a one-word reintroduction would ship:\n  "
        + "\n  ".join(repr(m) for m in missed))


# A filler clause per opener, so the generated conditional reads as English for
# the clause openers. The three phrase openers get their own filler; the
# claim-in-clause construction is mechanical for them and is meant to be -- a
# detector must not depend on the grammaticality of what it grades.
_OPENER_FILLER = {"on a host": "of this kind",
                  "for a host": "of this kind",
                  "absent": "a capable child"}


def _conditional_forms(opener, claim):
    """The two constructions an opener can put a claim into.

    CLAIM-IN-MAIN: the conditional clause is innocent filler and the claim is the
    main clause -- the construction the tests reviewer measured.
    CLAIM-IN-CLAUSE: the claim IS the conditional clause and the main clause is
    innocent -- the construction the bug reviewer measured, live, on disk.

    Each reviewer's proposed one-line repair killed one of these and left the
    other green. Both are generated here for every claim x every opener, which
    is what a hand-added "one opener row" could not have done.
    """
    lead = opener[0].upper() + opener[1:]
    filler = _OPENER_FILLER.get(opener, "the lenses fan out")
    stem = claim.rstrip(".")
    return (f"{lead} {filler}, {claim}",
            f"{lead} {stem[0].lower() + stem[1:]}, "
            "serialize the lenses in this session.")


def test_claim_detector_reds_on_the_generated_conditional_closure_set():
    """Close the corpus under the exemption's own transformation.

    The conditional-opener exemption is the widest mechanism in the detector, and
    the hand-maintained corpus had ZERO rows exercising it -- so a sentence-scoped
    exemption shipped with every planted claim escaping behind any opener. This
    test generates the closure rather than sampling it: hand-adding one opener row
    re-creates the blindness at the next construction, which is precisely what the
    two reviewers' non-overlapping measurements demonstrated.

    Separate from the bare-corpus test above on purpose: they fail for different
    reasons. That one reds when the detector is narrowed; this one reds when the
    exemption is widened back.
    """
    claims, openers = _corpus()
    missed = []
    for claim in claims:
        for opener in openers:
            for form in _conditional_forms(opener, claim):
                if not _claim_sentences(form):
                    missed.append(form)
    total = len(claims) * len(openers) * 2
    assert not missed, (
        f"{len(missed)} of {total} conditional-prefixed planted claims escape "
        "the detector. A conditional opener exempts the conditional CLAUSE, "
        "never the main clause, and never a clause whose own subject is the "
        "provider:\n  " + "\n  ".join(repr(m) for m in missed[:20]))


# Compiled exactly as `_CLAIM_RE` uses it, word boundaries included. Without the
# `\b` anchors this is a DIFFERENT predicate from the detector's, so the corpus
# generator below would split claims at a subject the detector does not
# recognize -- two spellings of one pattern, which is the drift this file forbids
# four separate times.
_SUBJECT_RE = re.compile(rf"\b(?:{_SUBJECT})\b", re.IGNORECASE)


def _table_row_split(claim):
    """Split a planted claim after its provider subject, or None if it will not
    reach the escape.

    The escape needs the SUBJECT in the leading cell and the lack-verb after the
    cell boundary, which is the shape a contract table actually produces. A cell
    wider than `_LEAD_RE`'s own bound is never stripped, so such a claim cannot
    demonstrate the escape and is excluded rather than asserted -- a corpus row
    that passes for the wrong reason proves nothing.

    Eligibility is decided by running `_LEAD_RE` against the generated row, not
    by re-deriving its 40-character bound here. Two copies of one bound drift,
    and the padding spaces count toward it, which a re-derivation gets wrong.
    """
    subject = _SUBJECT_RE.search(claim)
    if not subject:
        return None
    cell = claim[:subject.end()].strip().strip("|").strip()
    rest = claim[subject.end():].strip()
    if not cell or not rest:
        return None
    if not _LEAD_RE.match(f"| {cell} | x |").group(0):
        return None
    return cell, rest


def _table_row_forms(claim, opener):
    """A planted claim split ACROSS a table-row cell boundary.

    The conditional sits in the second cell, so the exemption fires and the
    leading cell -- carrying the claim's subject -- is what the old code dropped.
    The control is the same split with no conditional at all: it must be caught,
    which is what proves the split kept the claim intact rather than destroying
    it. A row that escapes because the split broke the sentence would be a
    corpus that tests nothing.
    """
    split = _table_row_split(claim)
    if split is None:
        return ()
    cell, rest = split
    lead = opener[0].upper() + opener[1:]
    filler = _OPENER_FILLER.get(opener, "the lenses fan out")
    return (f"| {cell} | {lead} {filler}, {rest} |",)


def _comma_straddling_claims(claims):
    """Planted claims whose subject and lack-verb sit on opposite sides of a comma.

    These are the only rows the clause-terminator axis actually discriminates on:
    a cut has to land INSIDE a claim to hide it, so a claim with nothing on the
    far side of its first comma cannot expose a mis-placed cut no matter how many
    rows it generates. Derived from the detector's own predicate, so it stays
    true if `_CLAIM_RE` changes.
    """
    return [claim for claim in claims
            if "," in claim and _states_a_lack(claim)
            and not _states_a_lack(claim.partition(",")[2])]


def _terminator_forms(claim, opener, terminator):
    """The two constructions again, with the clause closed by `terminator`.

    Same pair as `_conditional_forms`, which is the comma case of this one. The
    separator is what decides where the clause ends, so it is an axis of the
    exemption and gets generated coverage like every other one.
    """
    lead = opener[0].upper() + opener[1:]
    filler = _OPENER_FILLER.get(opener, "the lenses fan out")
    stem = claim.rstrip(".")
    return (f"{lead} {filler}{terminator} {claim}",
            f"{lead} {stem[0].lower() + stem[1:]}{terminator} "
            "serialize the lenses in this session.")


# The comma is the one member `_CLAIM_RE` can reach across, and it is kept for a
# named reason (`ALLOWED_ROWS[3]`). Every other member must be UNSPANNABLE, or
# adding it silently trades catches for escapes -- which is exactly what `--`
# did. Listed rather than derived because it pins a DECISION, and asserted below
# so the decision cannot be reversed by appending one character to the tuple.
SPANNABLE_TERMINATORS_BY_DESIGN = (",",)


def test_the_corpus_generator_uses_the_detectors_own_subject_pattern():
    """The splitter and the detector must recognize the SAME provider subjects.

    `_table_row_split` cuts a planted claim after its subject so the subject
    lands in the leading cell. Compiling `_SUBJECT` differently from the way
    `_CLAIM_RE` embeds it would split the corpus at a subject the detector does
    not recognize -- a second spelling of one pattern, which is the drift this
    file forbids everywhere else by asserting the relation rather than trusting
    it.

    This is asserted precisely BECAUSE it is behavior-preserving today: with and
    without the word boundaries the axis is the same 29 claims and the same 232
    rows, so no corpus test reds if the two spellings drift apart. A structural
    invariant is the only thing that can see it.
    """
    assert _CLAIM_RE.pattern.startswith(_SUBJECT_RE.pattern), (
        "`_SUBJECT_RE` is not how `_CLAIM_RE` spells the same subject, so the "
        "corpus generator and the detector disagree about what a provider "
        "subject is:\n"
        f"  _SUBJECT_RE: {_SUBJECT_RE.pattern!r}\n"
        f"  _CLAIM_RE:   {_CLAIM_RE.pattern[:len(_SUBJECT_RE.pattern) + 24]!r}...")
    assert _SUBJECT_RE.flags == _CLAIM_RE.flags, (
        f"the two compilations disagree on flags ({_SUBJECT_RE.flags} vs "
        f"{_CLAIM_RE.flags}), so one can match a subject the other does not")


def test_no_clause_terminator_but_the_comma_can_be_spanned_by_a_claim():
    """A cut point a claim can reach ACROSS splits claims instead of clauses.

    This is the invariant that governs `_CLAUSE_TERMINATORS`, and it is the one
    an author widening that tuple will not think to check: adding a spannable
    terminator LOOKS like pure gain (it closes the escapes where the clause ends
    there) while silently opening every claim that straddles it. `--` was
    measured at 8 closed against 208 opened before this test existed.

    The probe is built from the detector's own predicate, so it cannot drift from
    what `_CLAIM_RE` actually does.
    """
    spannable = [t for t in _CLAUSE_TERMINATORS
                 if t not in SPANNABLE_TERMINATORS_BY_DESIGN
                 and _states_a_lack(f"Codex CLI{t} has no isolated primitive.")]
    assert not spannable, (
        f"these clause terminators can be spanned by `_CLAIM_RE`: {spannable}. "
        "Cutting the conditional clause there splits a claim that straddles it, "
        "so the exempted head keeps the subject and the graded remainder keeps "
        "the lack-verb, and a sentence the detector caught before goes silent. "
        "Either drop the terminator, or add it to "
        "`SPANNABLE_TERMINATORS_BY_DESIGN` with the live row that requires it "
        "and the measured cost -- as the comma has.")
    for term in SPANNABLE_TERMINATORS_BY_DESIGN:
        assert term in _CLAUSE_TERMINATORS, (
            f"{term!r} is recorded as a by-design spannable terminator but is "
            "no longer a terminator at all; drop the exception with it.")


def test_the_table_row_controls_are_caught_before_the_axis_is_trusted():
    """Precondition for the axis below: every split preserves its claim.

    Without this the table axis could go green because the splits produced
    ungradeable fragments rather than because the detector reads the leading
    cell. Floored too, so a `_table_row_split` that starts returning None for
    everything reds here instead of silently emptying the axis.
    """
    claims, _ = _corpus()
    eligible = [c for c in claims if _table_row_split(c) is not None]
    assert len(eligible) >= 24, (
        f"only {len(eligible)} of {len(claims)} planted claims admit a "
        "subject-bearing leading cell -- the table axis would be near-vacuous. "
        "Check `_table_row_split` before relaxing this floor.")
    uncaught = [f"| {a} | {b} |" for a, b in map(_table_row_split, eligible)
                if not _claim_sentences(f"| {a} | {b} |")]
    assert not uncaught, (
        "a table-row control escaped, so the split destroyed the claim rather "
        "than moving its subject into the leading cell. The axis below would be "
        "measuring the split, not the detector:\n  "
        + "\n  ".join(repr(u) for u in uncaught))


def test_claim_detector_reds_on_the_generated_table_row_closure_set():
    """The lead-strip axis, closed under the same cross product.

    `_LEAD_RE` strips a short leading table cell to find the opener, and the
    iteration-3 defect graded the STRIPPED text, so every claim whose subject sat
    in that cell was silently exempt -- 232 of 232 rows, and the corpus could not
    see it because no generated axis put a claim in a table cell. The exemption's
    third axis, generated for the same reason as its first two.
    """
    claims, openers = _corpus()
    missed = [form for claim in claims for opener in openers
              for form in _table_row_forms(claim, opener)
              if not _claim_sentences(form)]
    total = sum(len(_table_row_forms(c, o)) for c in claims for o in openers)
    assert not missed, (
        f"{len(missed)} of {total} table-row planted claims escape the "
        "detector. A conditional opener exempts the conditional CLAUSE; the "
        "markdown lead is furniture for FINDING that clause and content for "
        "grading it, so it must be re-attached:\n  "
        + "\n  ".join(repr(m) for m in missed[:20]))


def test_claim_detector_reds_on_the_generated_clause_terminator_closure_set():
    """The clause-boundary axis, closed under the same cross product.

    Cutting the clause at the first COMMA rather than at a clause terminator let
    a `;`/`:`/dash-closed conditional swallow the subject of a comma-bearing
    claim -- 48 escapes, invisible to a corpus in which every
    generated conditional was comma-closed. The comma case is the closure test
    above; this covers the rest of `_CLAUSE_TERMINATORS`, and iterates that
    tuple rather than a second copy of it so a terminator cannot be added to the
    detector without arriving here in the same edit.
    """
    claims, openers = _corpus()
    assert len(_CLAUSE_TERMINATORS) >= 4, (
        f"only {len(_CLAUSE_TERMINATORS)} clause terminators -- this axis is "
        "sized by that tuple and would shrink with it silently.")
    # SIZE is not DISCRIMINATION. Only a claim whose subject and lack-verb
    # straddle a comma can expose a comma-partition cut, so the axis's whole
    # power against the defect it was landed to close lives in those rows, not
    # in the other thousands. One such row is a single point of failure that
    # deletes silently -- the axis stays 2240 rows and stays green.
    straddling = _comma_straddling_claims(claims)
    assert len(straddling) >= MIN_COMMA_STRADDLING, (
        f"only {len(straddling)} planted claims put a comma between the "
        f"provider subject and the lack-verb ({straddling}) -- this axis would "
        "keep every one of its rows and lose almost all of its discrimination. "
        "Add a comma-straddling claim; do not lower this floor.")
    missed = [form for claim in claims for opener in openers
              for term in _CLAUSE_TERMINATORS
              for form in _terminator_forms(claim, opener, term)
              if not _claim_sentences(form)]
    total = len(claims) * len(openers) * len(_CLAUSE_TERMINATORS) * 2
    assert not missed, (
        f"{len(missed)} of {total} terminator-closed planted claims escape the "
        "detector. The exemption covers the conditional clause up to its own "
        "boundary, and a comma is only the most common spelling of that "
        "boundary:\n  " + "\n  ".join(repr(m) for m in missed[:20]))


# The other half of calibration. Four rows, one per axis that could over-fire;
# rows that were two axes away from firing were dropped as decoration, and the
# rows every adapter carries are already proven un-flagged by the live sweep.
ALLOWED_ROWS = (
    # A Claude-host-specific TOOL, not a runtime-variable host capability.
    "Codex has no Artifact tool: the plan is written as a FILE and reported by "
    "path.",
    # A statement about what the SKILL needs, not about what the host has.
    "Codex needs no Agent/Workflow primitive here: the skill is single-context "
    "reading plus one script call, so there is no isolated-agent fallback to "
    "document.",
    # The exemplars' runtime-conditional form, non-provider subject.
    "If the host lacks the required fresh-context primitive or the probe is "
    "inconclusive, halt visibly with `required_tool_missing`.",
    # The exemplars' runtime-conditional form WITH a provider mention inside it.
    # This is the row the conditional-opener exemption exists for, and the one a
    # future widening is most likely to break. The conditional's SUBJECT is
    # "the active host"; "ordinary Codex CLI" is a predicate complement.
    "If the active host is ordinary Codex CLI, lacks an explicit no-history "
    "primitive, or the non-mutating probe is absent, stop visibly.",
    # An instruction ABOUT claims, which must not itself read as one.
    "No codex adapter may map an isolated fresh-context arm it has not proven.",
)


def _live_conditional_sentences(texts):
    """Every conditional-opener sentence in the shipped tree, with its adapter."""
    found = []
    for name, text in sorted(texts.items()):
        for sentence in _SENTENCE_RE.split(text):
            _, body = _lead_and_body(sentence)
            if _CONDITIONAL_OPENER_RE.match(body):
                found.append((name, sentence.strip()))
    return found


def test_claim_detector_stays_silent_on_accurate_rows_and_live_conditionals():
    """A detector that fires on the correct answer gets relaxed within a week.

    Two corpora, one direction. The hand-written rows carry this test's
    DISCRIMINATION: one axis each -- the tool-name exemption, the
    skill-requirement exemption, both spellings of the runtime conditional, and
    an instruction about claims.

    The live rows are ENUMERATED from the tree, because the surface the
    exemption protects is whatever the adapters currently say rather than what
    someone remembered to transcribe. But read that half honestly, because its
    headline number is much larger than its evidence. The 73 harvested
    instances are 21 distinct strings; 71 of the 73 carry no isolation noun, so
    they exit `_asserts_provider_wide` at the topic filter before any exemption
    logic runs; 2 distinct rows reach the claim predicate and 1 also states a
    lack. Deleting both discriminating rows leaves 71 over a floor of 40 and
    this test still passes. So the live half is a VACUITY guard -- it proves the
    harvest still runs and that the exemption did not start over-firing on the
    adapters' own conditional register -- and it is a strict subset of the main
    sweep, which grades every sentence of all 54 adapters with the identical
    predicate. The main sweep is the real false-positive control; this half
    cannot fail unless that one already has.
    """
    live = _live_conditional_sentences(_adapter_texts())
    assert len(live) >= MIN_LIVE_CONDITIONALS, (
        f"only {len(live)} conditional-opener sentences found in the shipped "
        "adapters -- the false-positive half of this test would be near-vacuous. "
        "Check the harvest before relaxing this floor.")
    over_fired = [repr(row) for row in ALLOWED_ROWS if _claim_sentences(row)]
    over_fired += [f"{name}: {sentence}" for name, sentence in live
                   if _asserts_provider_wide(sentence)]
    # Derived, never transcribed: the honest strength of the live half is how
    # many DISTINCT rows can reach the claim predicate at all, and a figure
    # written into this message by hand is one that goes stale silently.
    reaching = {s for _, s in live if _ISOLATION_RE.search(s)}
    assert not over_fired, (
        "the detector fired on prose that is accurate and must stay writable "
        f"({len(live)} live conditional sentence instances graded, of which "
        f"{len(reaching)} distinct rows carry an isolation noun and can reach "
        "the claim predicate at all):\n  "
        + "\n  ".join(over_fired))


# The detector's boundary, written down rather than left to be re-derived. Every
# row here is a real evasion that this gate deliberately does NOT catch, grouped
# by the axis that lets it through (the axes are argued in the module docstring).
#
# This tuple pins a DECISION, not a capability. If you widen the detector, move
# the rows it now catches OUT of this tuple in the same edit and update the
# docstring's boundary section -- the test below reds until you do. That is the
# point: the boundary moves deliberately or not at all.
DOCUMENTED_MISSES = (
    # Axis 1 -- the subject reaches its lack-verb across more than three tokens.
    "Codex, which this wrapper targets, has no isolated fresh-context agent "
    "primitive.",
    "Codex, as of the current release, has no isolated fresh-context agent "
    "primitive.",
    "Codex CLI, as of this writing, ships without an isolated agent primitive.",
    "Codex, as shipped today in every profile we have seen, has no isolated "
    "agent primitive.",
    # Axis 2 -- inferential: the lack is implied, never asserted of the provider.
    "Codex provides only a single conversational context, so no isolated arm "
    "exists.",
    "Codex is single-context only, so run the lenses serially.",
    "Codex agents run in a shared conversational context, so there is no "
    "isolated child to dispatch.",
    "Because the provider gives us no fresh-context child, the lenses run "
    "serially.",
    # Axis 3 -- fronted prepositional phrase puts the provider before the
    # negation, so neither claim order matches.
    "On Codex there is no sub-agent primitive.",
    # Axis 4 -- the conditional clause is closed by punctuation outside
    # `_CLAUSE_TERMINATORS`, so the cut lands at the next real terminator and the
    # provider subject stays inside the exempted head. Widening the terminator
    # set to reach this was measured free on the live tree, but every extra
    # member moves the cut EARLIER in every sentence it matches, so the set stays
    # the five real clause terminators and the residual is recorded here.
    "If the lenses fan out (on this host) Codex, however, lacks an isolated "
    "agent primitive.",
    # Axis 5 -- the clause is closed by ASCII `--`, which is deliberately NOT a
    # terminator: `_GAP` can span it, so cutting there would split every claim
    # that straddles a dash. Closing this row was measured at 8 escapes closed
    # against 208 opened, so the trade is refused and the residual recorded.
    # See `SPANNABLE_TERMINATORS_BY_DESIGN` and the test that pins it.
    "If the lenses fan out -- Codex, however, lacks an isolated agent primitive.",
)


def test_the_documented_detector_boundary_still_holds():
    """The known holes stay known: a reader can tell descoped from unconsidered.

    An overclaiming gate is its own defect class -- the next reviewer trusts the
    docstring. This makes the boundary a measured, reviewable list instead of a
    sentence nobody can check, and makes any widening a deliberate edit rather
    than an accident nobody notices.
    """
    assert len(DOCUMENTED_MISSES) >= MIN_DOCUMENTED_MISSES, (
        f"only {len(DOCUMENTED_MISSES)} recorded boundary rows -- this test "
        "passes over an empty tuple, and an empty boundary record is worse than "
        "no boundary record: it reads as 'nothing was descoped'.")
    now_caught = [row for row in DOCUMENTED_MISSES if _claim_sentences(row)]
    assert not now_caught, (
        "the detector now catches rows recorded as its documented boundary. "
        "That is an improvement -- move them into PLANTED_CLAIMS and update the "
        "docstring's boundary section in the same edit:\n  "
        + "\n  ".join(repr(r) for r in now_caught))


# --------------------------------------------------------------------------- #
# Authority boundaries
# --------------------------------------------------------------------------- #

# Literal, AFFIRMATIVE reversals of the producer / reviewer / parent separation.
# Affirmative on purpose: a token that could also appear inside a correctly
# NEGATED guard ("never infer isolation from the provider name") would false-red
# the right answer, and a gate that false-reds gets relaxed. FILE scope is the
# right unit here for the same reason -- an affirmative reversal is a defect
# wherever it appears, so no clause-level scoping is needed or wanted.
#
# This set is a strict SUPERSET of the one inside
# `test_codex_agent_isolation_contract.py::_adapter_defects`, and the superset
# relation is asserted below rather than assumed -- two hand-maintained copies of
# one data-shape constant drift the first time someone adds a token to one of
# them (CLAUDE.md, "One source of truth for data-shape constants"). The scopes
# genuinely differ: that gate reads two files, this one reads all 54.
FORBIDDEN_WEAKENINGS = {
    # A producer gaining reviewer authority.
    "producer may spawn the reviewer": "producer-owned reviewer",
    "the producer may grade its own": "producer grading itself",
    # A reviewer gaining final-verdict authority.
    "reviewer calls write_verdict": "reviewer-owned signing",
    "reviewer calls classify_verdict": "reviewer-owned final classification",
    # A child gaining the parent's private state, history, or verdict key.
    'fork_turns="all"': "inherited-history child dispatch",
    "reused child is allowed": "reused producer/reviewer context",
    "may be passed to children": "child-visible verdict channel",
    "children may receive the key": "child-visible HMAC key",
    "while emitting its value": "emitted HMAC key",
    "inside the repository and producer worktree": "worktree verdict sidecar",
    # Filesystem/tool sharing mistaken for conversational or authority isolation.
    "they are os isolation": "filesystem mistaken for OS isolation",
    "shared filesystem access proves isolation": "filesystem read as isolation",
}


def _weakening_defects(name, text):
    lowered = text.lower()
    return [f"{name}: {label} ({token!r})"
            for token, label in FORBIDDEN_WEAKENINGS.items()
            if token.lower() in lowered]


def test_no_adapter_weakens_an_authority_boundary():
    """Producer / reviewer / parent-verdict authority stays separate."""
    defects = []
    for name, text in sorted(_adapter_texts().items()):
        defects.extend(_weakening_defects(name, text))
    assert not defects, (
        "a codex adapter weakens an authority boundary a core defines. A "
        "wrapper may never grant a producer reviewer authority, a reviewer "
        "final-verdict authority, or a child the parent's private state:\n  "
        + "\n  ".join(defects))


def test_the_weakening_gate_reds_on_a_real_adapter_with_a_planted_reversal():
    """Anchor: mutate a REAL adapter and assert the REAL predicate fires.

    The gate above had no witness at all -- nine tautological
    `assert token in f"...{token}..."` tests were correctly deleted and nothing
    replaced them, so no test in the file demonstrated that the weakening
    detector can fire. One mutation of a real adapter is the whole fix.
    """
    original = _adapter_texts()["tier-offload"]
    assert not _weakening_defects("tier-offload", original), (
        "anchor precondition failed: tier-offload already trips the detector")
    mutated = original + '\n- Children are dispatched with fork_turns="all".\n'
    defects = _weakening_defects("tier-offload", mutated)
    assert len(defects) == 1 and "inherited-history" in defects[0], defects


def _neighbour_forbidden_tokens():
    """The token literals inside the neighbour gate's own `forbidden` dict.

    Parsed from source with `ast` rather than imported: this directory has no
    package marker and no test module imports another, so a real import would
    add a fragile sys.path hack to buy the same strings.
    """
    tree = ast.parse(NEIGHBOUR_GATE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "forbidden" not in targets or not isinstance(node.value, ast.Dict):
            continue
        return {k.value for k in node.value.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    return set()


def test_authority_token_set_still_covers_the_neighbour_gates_tokens():
    """One source of truth: this repo-wide set must cover the two-file set.

    `test_codex_agent_isolation_contract.py` grades build-step + build-phase with
    its own literal token list. Adding a boundary token there and not here would
    leave the other 52 adapters ungraded for it -- the exact drift two copies of
    a data-shape constant always produce. This assertion makes that visible at
    the moment the second copy is edited, and is why the tokens here are a
    superset rather than a duplicate.
    """
    neighbour = _neighbour_forbidden_tokens()
    assert len(neighbour) >= 8, (
        "could not parse the neighbour gate's `forbidden` dict "
        f"({NEIGHBOUR_GATE.name}); it resolved to {sorted(neighbour)}. Fix the "
        "parse rather than deleting this check.")
    missing = sorted(t for t in neighbour if t not in FORBIDDEN_WEAKENINGS)
    assert not missing, (
        "the neighbour gate forbids tokens this repo-wide sweep does not, so "
        f"52 adapters go ungraded for them: {missing}")


# --------------------------------------------------------------------------- #
# Fail-closed halts survive the rewrite
# --------------------------------------------------------------------------- #

CAPABILITY_MARKER = "a host that passes"
HALT = "required_tool_missing"
REVIEW_DEEP = "review-deep"
# The two cores whose isolated work runs through the host WORKFLOW primitive
# (`_shared/score_skill.workflow.js`), NOT through isolated agent dispatch. An
# agent-isolation probe establishes nothing about whether that script can run,
# so conditioning their mandatory halts on that contract would convert a core
# halt into an optional path on a host that passes the probe and has no workflow.
WORKFLOW_PRIMITIVE_SKILLS = ("skill-evolve", "skill-iterate")
JUDGE_UI = "judge-ui"


def _is_capability_conditioned(text):
    """A MODAL permission -- `may map/dispatch/spawn/run` reaching an isolation
    noun within 120 characters -- plus the one literal `CAPABILITY_MARKER`.

    That is the whole scope, stated as what it keys on rather than as what it
    means. The earlier docstring said "any permission ... however spelled", which
    is the overclaim `test_the_documented_detector_boundary_still_holds` exists
    to forbid one predicate over: the next reviewer reads the docstring, not the
    regex. Measured, 12 of 15 plausible reopenings escape it, and they are in
    `DOCUMENTED_CONDITIONING_MISSES` below rather than in this sentence.

    What it DOES buy is real and was the iteration-2 repair: the literal alone
    was defeated by the one synonym "A host satisfying the contract may dispatch
    ...", which reproduced a shipped regression with both unconditionality pins
    green. Every gate asking "is this adapter capability-conditioned?" goes
    through here, so no sibling pin can be left on the bare literal again.

    FILE scope, deliberately: a permission granted anywhere in a wrapper is
    granted, so there is no narrower unit to scope it to.
    """
    lowered = text.lower()
    if CAPABILITY_MARKER in lowered:
        return True
    permission = re.compile(
        r"may\s+(?:map|dispatch|spawn|run)\b[^.]{0,120}?"
        r"(?:fresh|isolat\w*|sibling|no-history|child|children)",
        re.IGNORECASE)
    return bool(permission.search(lowered))


# The SECOND detector's boundary, written down for the same reason the claim
# detector's is: both unconditionality pins below rest on this predicate
# returning False, and a pin whose blind spots live only in a docstring adjective
# is a pin the next author defeats by accident.
#
# Three registers, all measured against the real `review-deep` text: appending
# any of the first three to it leaves ALL FIVE DS-D3 assertions green, so the
# gate that exists to stop a descoped track being reopened inside a wrapper edit
# does not see the reopening. Same on `skill-evolve` for the workflow pin.
#
# This tuple pins a DECISION, not a capability -- identical contract to
# `DOCUMENTED_MISSES`. Widening the predicate also changes which adapters
# `_conditioned_adapters` selects, and so which must carry a cited contract and a
# co-located halt: a behavior change to four gates. If you widen it, move the
# rows it now catches OUT of this tuple in the same edit and update the module
# docstring's second-detector section. The test below reds until you do.
DOCUMENTED_CONDITIONING_MISSES = (
    # Register 1 -- a permission verb outside the four modals.
    "A qualifying host is permitted to fan the lenses out to isolated children.",
    "A contract-passing host is free to dispatch the lenses as isolated children.",
    "Hosts that pass the agent-isolation contract are allowed to map the "
    "fan-out onto children.",
    # Register 2 -- bare declarative, no modal at all.
    "Where the host proves no-history dispatch, the lenses run as isolated "
    "siblings.",
    "Hosts proven to expose no-history dispatch run the lenses as separate "
    "children.",
    "Capable hosts map each lens onto a separate no-history child.",
    "Given a proven isolation capability, the lens fan-out is available.",
    "The lens fan-out becomes available as soon as the host proves "
    "fresh-context dispatch.",
    # Register 3 -- fronted conditional, permission in the main clause.
    "If the probe succeeds, dispatch each lens in its own fresh context.",
    "On a host whose probe passes, each lens gets its own fresh child.",
    "When the isolation contract is satisfied, fan the five lenses out to "
    "fresh siblings.",
    "Once the non-mutating probe returns clean, the lenses are dispatched to "
    "fresh contexts.",
)

# The accepted OVER-fire band, asserted rather than described. Every row spells a
# PROHIBITION with the same modal the predicate keys on, so the predicate reads
# it as the permission it forbids -- the first row is the strongest possible
# statement of the thing the DS-D3 pin protects, and it reds three tests.
# Zero live instances across all 54 adapters (the literal set and the meaning
# class resolve to the same 10 adapters, symmetric difference empty), so this is
# forward-looking, and excusing negated frames would hand every real reopening a
# one-word disguise -- the same trade the claim detector already refused.
CONDITIONING_OVER_FIRES = (
    "No host may dispatch a fresh isolated child for these lenses under DS-D3.",
    "The operator may run the isolated arms by hand.",
    "Never claim a host may map the lenses onto fresh siblings.",
)


def test_the_documented_conditioning_boundary_still_holds():
    """Both bands of the second detector stay where they were measured.

    Reported as two lists in one message because they fail for opposite reasons
    and a reader needs to know which. A row moving out of either band is an
    improvement or a regression, never noise -- and either way it is a
    deliberate edit to this tuple plus the module docstring, which is the whole
    point of writing the boundary down instead of asserting it in prose.
    """
    assert len(DOCUMENTED_CONDITIONING_MISSES) >= MIN_CONDITIONING_MISSES, (
        f"only {len(DOCUMENTED_CONDITIONING_MISSES)} recorded conditioning "
        "misses -- this boundary record would be near-vacuous, which is the "
        "defect the corpus floor above exists to prevent.")
    # The over-fire band needs its own floor for the same reason and is easier
    # to miss: it is asserted in the must-still-be-CAUGHT direction, so an empty
    # tuple yields an empty list and the assertion below passes silently.
    assert len(CONDITIONING_OVER_FIRES) >= MIN_CONDITIONING_OVER_FIRES, (
        f"only {len(CONDITIONING_OVER_FIRES)} recorded over-fire rows -- the "
        "narrowing half of this test would grade nothing.")
    now_caught = [r for r in DOCUMENTED_CONDITIONING_MISSES
                  if _is_capability_conditioned(r)]
    now_missed = [r for r in CONDITIONING_OVER_FIRES
                  if not _is_capability_conditioned(r)]
    assert not (now_caught or now_missed), (
        "`_is_capability_conditioned`'s measured boundary moved:\n"
        "  now CAUGHT (widened -- move these into the anchors and update the "
        "module docstring's second-detector section):\n    "
        + "\n    ".join(repr(r) for r in now_caught)
        + "\n  now MISSED (narrowed -- the over-fire band was closed, which "
          "also means a reopening spelled this way now escapes):\n    "
        + "\n    ".join(repr(r) for r in now_missed))


def test_the_conditioning_boundary_is_why_the_pins_are_not_the_whole_control():
    """The recorded misses are recorded because they are LIVE holes in the pins.

    A boundary tuple nobody connects to a consequence gets read as trivia. This
    demonstrates the consequence on the real files: a reopening in any of the
    three registers leaves both unconditionality pins' predicate green, which is
    exactly why `documentation/troubleshooting.md` and the DS-D3 decision record
    -- not this gate -- are the primary control on that track.
    """
    texts = _adapter_texts()
    for name in (REVIEW_DEEP,) + WORKFLOW_PRIMITIVE_SKILLS:
        for reopening in DOCUMENTED_CONDITIONING_MISSES:
            assert not _is_capability_conditioned(texts[name] + "\n" + reopening), (
                f"{name}: this reopening is now SEEN by the predicate, so it is "
                f"no longer a documented miss: {reopening!r}")


def _colocated_halt_lines(text):
    """Lines naming the fail-closed halt AND the isolated capability it guards.

    LINE scope, not file scope. A file-scoped `HALT in text` check is satisfied
    by universal boilerplate -- every adapter carries `required_tool_missing` in
    at least the tier-resolution row, and most carry a missing-adapter row too --
    and neither row names an isolation capability. That was this gate's first
    draft, and deleting an adapter's real fan-out halt sentence passed it clean.

    Adapter bullets and contract-table rows are single unwrapped lines in this
    tree, so a line IS the declaration. Matching is case-insensitive, because the
    sibling gates below lowercase and a case-split predicate would red one gate
    and pass the other on the same bytes.
    """
    return [line for line in text.split("\n")
            if HALT in line.lower() and _ISOLATION_RE.search(line)]


def _halt_defects(texts, subject):
    """Subject adapters that name no fail-closed halt for their isolated arm."""
    return sorted(name for name in sorted(subject)
                  if not _colocated_halt_lines(texts[name]))


def test_every_sub_agent_adapter_keeps_a_colocated_fail_closed_halt():
    """Rewriting a claim must never delete the halt the claim guarded.

    The sweep's failure mode is not "the prose is still wrong" -- it is "the
    prose got friendlier and the halt went with it". The subject set is the
    manifest's `sub-agent` capability field (floored inside its own accessor), so
    an adapter cannot leave its own gate by softening a sentence; the halt must
    sit on the same line as the isolation capability it guards, so the universal
    boilerplate cannot satisfy it.

    Scope note: this gate covers the manifest `sub-agent` set, NOT the whole
    roster. The other adapters are form-(b) scoped refusals with no isolated arm
    to guard, and are covered by the claim sweep alone -- deliberate, and
    reviewable only because the subject set comes from an independent source.
    """
    texts = _adapter_texts()
    missing = _halt_defects(texts, _manifest_sub_agent_codex_names())
    assert not missing, (
        f"a `sub-agent` codex adapter names no `{HALT}` halt on the same line "
        "as the isolated capability it guards -- either the fail-closed "
        "behavior was dropped, or an in-session substitute was invented for a "
        f"core that documents none: {missing}")


def test_the_colocated_halt_gate_reds_on_a_real_adapter_with_its_halt_removed():
    """Anchor: mutate a REAL adapter and assert the REAL predicate fires.

    The first draft anchored on a synthetic two-line roster where file scope and
    sentence scope coincide, so it went green over an inert predicate. This
    mutates the shipped `review-gauntlet` bullet into the precise regression the
    gate exists to prevent -- serialize the lenses in this session instead --
    and additionally asserts that the OLD file-scoped check would still have
    passed on the mutated text, which is what made that draft unfalsifiable.
    """
    texts = _adapter_texts()
    original = texts["review-gauntlet"]
    old = ("halt visibly with `required_tool_missing`, naming the lens dispatch "
           "as the core step that could not run.")
    new = "serialize the five lenses in this session instead."
    assert old in original, f"planted-negative anchor moved: {old!r}"
    mutated = original.replace(old, new, 1)

    assert _halt_defects({"review-gauntlet": mutated}, {"review-gauntlet"}) == \
        ["review-gauntlet"]
    assert HALT in mutated, (
        "the mutated text must still carry the boilerplate halt token -- that "
        "is exactly why a file-scoped check could not see this regression, and "
        "this assertion is what stops a future edit from reverting to one.")


def _conditioned_adapters(texts):
    """Adapters that grant a permission to map an isolated arm, however spelled.

    Selection goes through the MEANING-CLASS predicate, not the literal marker,
    so an adapter cannot leave the citation/halt obligations by rewording its
    permission. Measured behavior-preserving on the live tree: the literal and
    the meaning class resolve to the same 10 adapters, empty symmetric
    difference.
    """
    conditioned = {name for name, text in texts.items()
                   if _is_capability_conditioned(text)}
    assert len(conditioned) >= MIN_CONDITIONED, (
        f"only {len(conditioned)} capability-conditioned adapters found "
        f"({sorted(conditioned)}) -- check the predicate before relaxing this.")
    return conditioned


def test_capability_conditioned_adapters_cite_the_contract_and_keep_a_halt():
    """Capability-conditioning without a cited contract is an open permission.

    "A host that passes ... may map ..." is only honest if the adapter also says
    WHICH contract establishes passing, and what happens when it does not. The
    mechanics of passing (the no-history requirement, the non-mutating probe,
    the never-infer-from-a-name rule, the child topology) have exactly one owner
    -- build-step's `## Agent-isolation capability contract` table -- so this
    gate requires the CITATION and deliberately does NOT require the mechanics'
    words. Requiring them would cement nine verbatim copies of that table into
    the tree (the tenth conditioned adapter, `build-step`, owns the original) and
    make trimming them a test edit.
    """
    texts = _adapter_texts()
    defects = []
    for name in sorted(_conditioned_adapters(texts)):
        lowered = texts[name].lower()
        if not _colocated_halt_lines(texts[name]):
            defects.append(f"{name}: conditioned with no co-located {HALT} halt")
        cites_owner = ("build-step agent-isolation contract" in lowered
                       or "agent-isolation capability contract" in lowered)
        owns_one = "capability contract\n" in lowered or "contract below" in lowered
        if not (cites_owner or owns_one):
            defects.append(f"{name}: cites no named capability contract")
    assert not defects, (
        "a capability-conditioned adapter is missing the machinery that makes "
        "the condition mean something:\n  " + "\n  ".join(defects))


def test_capability_conditioned_adapters_do_not_restate_the_contract_by_path():
    """The citation is by NAME, because no single path resolves in both trees.

    In the repository the contract lives at `skills/build-step/providers/codex.md`;
    in the emitted and installed codex tree the same adapter is `build-step/SKILL.md`
    and that path does not exist. `tools/build-distributions.ps1` rewrites only
    `../core.md` and the three `_shared/` spellings, so a repo-source path ships
    verbatim and points a runtime consumer at nothing. `build-phase` already
    solved this by naming the contract instead ("The separate build-step
    agent-isolation contract"); the sweep follows that precedent.
    """
    offenders = sorted(
        name for name, text in _adapter_texts().items()
        if name != "build-step"
        and "skills/build-step/providers/codex.md" in text)
    assert not offenders, (
        "these adapters cite the agent-isolation contract by a repo-source path "
        "that does not resolve in the emitted codex tree; name it instead: "
        f"{offenders}")


def test_workflow_primitive_cores_are_not_gated_on_the_isolation_contract():
    """A mandatory halt may only be conditioned on the capability its core needs.

    `skill-evolve` core halt #2 is "Workflow unavailable"; `skill-iterate`'s
    Step D delegates the whole render/grade split to
    `_shared/score_skill.workflow.js` through the host workflow primitive.
    Passing an agent-isolation probe says nothing about whether that script can
    execute, so an adapter that defers these halts to build-step's contract tells
    a probe-passing, workflow-less host to proceed exactly where its core demands
    a visible `required_tool_missing`. A wrapper may never weaken a gate its core
    defines, and this is the shape that does it invisibly.

    The test goes through `_is_capability_conditioned`, like the DS-D3 pin next
    to it. Pinning on the bare literal was the iteration-2 defect: one synonym
    ("A host SATISFYING the contract may dispatch ...") reproduced the shipped
    regression with this gate green.
    """
    texts = _adapter_texts()
    defects = []
    for name in WORKFLOW_PRIMITIVE_SKILLS:
        if _is_capability_conditioned(texts[name]):
            defects.append(
                f"{name}: halt conditioned on the agent-isolation contract, but "
                "this core requires the host WORKFLOW primitive")
        if "workflow primitive" not in texts[name].lower():
            defects.append(f"{name}: no longer names the workflow primitive")
        if not _colocated_halt_lines(texts[name]):
            defects.append(f"{name}: no co-located fail-closed halt")
    assert not defects, "\n  ".join(defects)


def test_the_workflow_pin_reds_on_a_reworded_capability_conditioning():
    """Anchor: the workflow pin must survive a rewording, not just a copy-paste.

    Its sibling DS-D3 pin has carried this anchor since iteration 2; this one had
    none, which is how it shipped keyed on a literal. Both rewordings below avoid
    `CAPABILITY_MARKER` entirely, so a revert to the literal reds here.
    """
    texts = _adapter_texts()
    for name in WORKFLOW_PRIMITIVE_SKILLS:
        for reopening in (
                "A host satisfying the separate build-step agent-isolation "
                "contract may dispatch each variant onto a fresh isolated child.",
                "A host supplying an explicit no-history primitive may map the "
                "scoring split onto fresh siblings.",
        ):
            mutated = texts[name] + "\n" + reopening
            assert CAPABILITY_MARKER not in reopening.lower(), (
                "this anchor is only meaningful while the reopening avoids the "
                "literal the pin used to key on")
            assert _is_capability_conditioned(mutated), (
                f"the {name} workflow pin does not see this reopening: "
                f"{reopening!r}")


def test_judge_ui_conditions_on_vision_as_well_as_isolation():
    """`judge-ui`'s core gate is fresh-context AND vision-capable, not one of them.

    `skills/judge-ui/core.md` step 3 requires a "fresh-context vision-capable
    task" that must "(a) *view* each image". Conditioning only on isolation
    directs a host whose children are text-only to dispatch a vision-judge that
    cannot see, and the failure then surfaces as an unsupported verdict rather
    than a visible halt.

    Every assertion is scoped to the CO-LOCATED HALT LINE. The earlier spelling
    tested `HALT in lowered` and `"either" in lowered`, both FILE-scoped -- the
    exact check `_colocated_halt_lines` exists to replace, satisfiable by
    boilerplate `judge-ui` carries on an unrelated line.
    """
    halt_lines = _colocated_halt_lines(_adapter_texts()[JUDGE_UI])
    assert halt_lines, f"{JUDGE_UI} lost its co-located fail-closed halt line"
    joined = "\n".join(halt_lines).lower()
    assert "image-capable" in joined or "vision-capable" in joined, (
        "judge-ui's codex adapter dropped the core's vision conjunct from the "
        "line carrying the halt; a text-only child that passes the isolation "
        "probe would be told to judge screenshots it cannot view.")
    assert "either" in joined, (
        "judge-ui must halt when EITHER conjunct is unmet, and say so on the "
        "same line as the halt.")


# A wrapper may not credit its core with a fallback the core never wrote. The
# unit is the SENTENCE and the property is POLARITY, not word order: every live
# adapter spells this "documents NO single-context fallback", so a gate keyed on
# the inverse word order ("the core's documented single-context fallback")
# matched a string no author in this tree has ever written, while the one-word
# inversion of the shipped sentence -- the likeliest real regression -- was
# invisible. The negation must sit on the noun phrase itself, within two tokens:
# sentence-wide negation is too wide, because the shipped sentences all continue
# "... so on a host that does NOT pass, halt visibly", which would excuse an
# inverted head clause.
_FALLBACK_PHRASE_RE = re.compile(r"single-context\s+(?:fallback|substitute)",
                                 re.IGNORECASE)
_NEGATED_FALLBACK_RE = re.compile(
    r"\b(?:no|not|never|zero)\b(?:\s+[\w/-]+){0,2}\s+"
    r"single-context\s+(?:fallback|substitute)", re.IGNORECASE)


def _fallback_polarity_defects(texts, subject):
    """Sentences crediting a core with a single-context fallback, un-negated."""
    defects = []
    for name in sorted(subject):
        for sentence in _SENTENCE_RE.split(texts[name]):
            if (_FALLBACK_PHRASE_RE.search(sentence)
                    and not _NEGATED_FALLBACK_RE.search(sentence)):
                defects.append(f"{name}: {sentence.strip()}")
    return defects


def test_no_sub_agent_adapter_invents_a_documented_single_context_fallback():
    """A wrapper may not credit its core with a fallback the core never wrote.

    Every `sub-agent` core in this set mandates isolated work; none of them
    documents a single-context fallback. An adapter that says "use the
    single-context fallback the core documents" has granted itself the substitute
    the hard constraint forbids, and has done it in a sentence that reads like a
    citation. (`goblin-do`/`goblin-suggest` are unaffected: their cores document
    an out-of-process `claude -p` CLI rail, which is not a single-context one,
    and they name no single-context fallback at all.)

    The subject-set floor lives in `_manifest_sub_agent_codex_names`; the floor
    here is on the SENTENCES, because a gate over an empty sentence set is the
    same vacuous green one level down.
    """
    texts = _adapter_texts()
    subject = _manifest_sub_agent_codex_names()
    graded = [1 for name in subject
              for sentence in _SENTENCE_RE.split(texts[name])
              if _FALLBACK_PHRASE_RE.search(sentence)]
    assert len(graded) >= MIN_FALLBACK_SENTENCES, (
        f"only {len(graded)} single-context-fallback sentences found across the "
        f"{len(subject)} `sub-agent` adapters -- this gate would be near-vacuous. "
        "Check the phrase before relaxing this floor.")
    defects = _fallback_polarity_defects(texts, subject)
    assert not defects, (
        "a `sub-agent` codex adapter attributes a documented single-context "
        "fallback to a core that documents none -- writing one is a CORE edit "
        "with its own review, never a wrapper's call:\n  " + "\n  ".join(defects))


def test_the_fallback_polarity_gate_reds_on_the_one_word_inversion():
    """Anchor: the three inversions a real author would actually write.

    The shipped sentence is "This core documents NO single-context fallback".
    Its one-word inversion is the single most likely way an adapter grants itself
    a fallback its core forbids, and the previous word-order regex could not see
    it -- it matched only "the core's documented single-context fallback", a
    spelling no adapter in this tree has ever used.
    """
    texts = _adapter_texts()
    anchor = "This core documents NO single-context fallback for that dispatch"
    original = texts["citation-sweep"]
    assert anchor in original, f"planted-negative anchor moved: {anchor!r}"
    assert not _fallback_polarity_defects(
        {"citation-sweep": original}, {"citation-sweep"})
    for inversion in (
            anchor.replace("documents NO", "documents a"),
            "Use the single-context fallback the core documents.",
            "Select the core's documented single-context fallback.",
    ):
        mutated = original.replace(anchor, inversion, 1)
        if inversion not in mutated:
            mutated = original + "\n- " + inversion + "\n"
        assert _fallback_polarity_defects(
            {"citation-sweep": mutated}, {"citation-sweep"}), (
            f"the polarity gate does not see this inversion: {inversion!r}")


# --------------------------------------------------------------------------- #
# The one named exception
# --------------------------------------------------------------------------- #

def test_review_deep_keeps_its_unconditional_ds_d3_halt():
    """`review-deep` is a NAMED accepted gap, not a defect to capability-gate.

    `documentation/descope-2026-09.md` decision DS-D3 accepts the codex deep lane
    as a known gap, and `documentation/troubleshooting.md` documents the halt as
    by design. Step 119 was allowed to correct the halt's stated REASON -- it
    asserted a provider-wide constant -- and nothing else. So this pins both
    directions: the reason no longer claims a host fact, and the halt is still
    unconditional. Reopening a descoped track inside a wrapper edit is exactly
    the change that must not pass silently.
    """
    text = _adapter_texts()[REVIEW_DEEP]
    lowered = text.lower()
    assert _colocated_halt_lines(text), (
        f"{REVIEW_DEEP} lost the fail-closed halt on its lens-dispatch line")
    assert "halt visibly with `required_tool_missing`" in lowered
    assert not _is_capability_conditioned(text), (
        f"{REVIEW_DEEP}'s codex halt was made capability-conditioned. That "
        "reopens the DS-D3 descoped track in a wrapper edit; restoring the codex "
        "deep lane needs its own reviewed plan.")
    assert "ds-d3" in lowered, (
        f"{REVIEW_DEEP}'s halt must name the decision that accepts it, so the "
        "reason stays a statement about the record rather than about the host.")
    assert not _claim_sentences(text), (
        f"{REVIEW_DEEP}'s halt reason drifted back to a provider-wide claim")


def test_the_ds_d3_pin_reds_on_a_reworded_capability_conditioning():
    """Anchor: the DS-D3 pin must survive a rewording, not just a copy-paste.

    Pinning unconditionality on one literal phrase is a gate that any author
    reopening the track defeats by accident. Both spellings below are mutations
    of the real file, run through the real predicate.
    """
    original = _adapter_texts()[REVIEW_DEEP]
    assert not _is_capability_conditioned(original)
    for reopening in (
            "A host that passes the contract may map the deep lenses onto "
            "fresh siblings.",
            "A host supplying an explicit no-history primitive may dispatch "
            "each lens as an isolated child.",
    ):
        assert _is_capability_conditioned(original + "\n" + reopening), (
            f"the DS-D3 pin does not see this reopening: {reopening!r}")
