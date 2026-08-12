# Step 69 — residual doc reconciliation: decisions and rationale

Phase 7.5, Step 69 of [`host-parity-repair-plan.md`](host-parity-repair-plan.md) (issue #100).
This is the **named in-repo record** that step's Done-when requires. It owns two decisions that
must survive review rounds without being re-litigated — why a retired README assertion stays
retired, and how the one surviving banned phrase is enforced — plus the citation corrections
folded into the same pass.

Every claim below was measured against the bytes in the tree, not against the plan's line
numbers, several of which had already drifted (§4).

---

## 1. KEEP RETIRED — the README anti-overclaim loop stays retired

### 1.1 What actually happened

Commit `8e8589c` did **not** delete a gate. The earlier "deleted gate" framing was wrong and is
corrected here. It **renamed and rewrote in place**:

| | |
|---|---|
| Before | `test_readme_points_at_the_handoff_without_claiming_acceptance` |
| After | `test_readme_points_at_the_handoff_with_the_completed_cutover_status` |
| Location today | [`tests/package-integrity/test_cutover_handoff.py`](../tests/package-integrity/test_cutover_handoff.py) |

The rewrite **retired** a four-phrase anti-overclaim loop — `host acceptance passed`,
`acceptance is complete`, `cutover is complete`, `steps 48-50 are done` — plus a `steps 49`
assertion, and **added** four completion assertions (`documentation/coding-root-cutover-handoff.md`,
`phase 7 complete`, `issues #62` / `#63 closed`, `step 48 is done`). One anti-overclaim assertion
survived: the phrase `what remains is operator-only` is still banned. §2 is about that survivor.

Net: **five assertions retired, four added, one carried forward.** Nothing was silently dropped
to make a red gate green — the rewrite tracked a status change that had genuinely occurred.

### 1.2 The decision

**KEEP RETIRED.** The retirement stands. This is recorded as a decision, not as an open
"restore or justify" question, because the latter phrasing invites a reviewer to demand
restoration — and restoration would make a **truthful** README fail.

### 1.3 Why restoring would be wrong, not merely inconvenient

Two independent reasons, either sufficient on its own.

**(a) The retired `steps 49` assertion is false against today's README.** It required the README
to speak of Step 49 as work still ahead. Steps 49 and 50 were accepted on 2026-08-09 (#62 and #63
closed), and the README now records the completed result. Reinstating that assertion would red
the suite on a README that is simply correct. A gate enforcing a stale claim is the exact
anti-pattern `plan_step_48_status()` in the same module was already rewritten to avoid — its
docstring says so outright: it "originally pinned 'in progress' as an invariant, which meant the
merge of Step 48 could not be written into the docs without turning the gate red."

**(b) The four banned phrases forbid prose that is now simply true.** `host acceptance passed`
and `cutover is complete` were banned when they would have been overclaims — before any host had
been observed. Both hosts have since resolved a generated `plan-review` profile from their own
discovery root, and the live consumer was cut over with an external backup retained. A ban on
saying so is a ban on accuracy. The concern those four phrases encoded — *static tests must never
be presented as host evidence* — is not abandoned; it is **relocated to where it is still true**
and enforced by the assertions listed in §1.4.

### 1.4 What still protects the original concern

Retiring the four phrases does not leave the static-vs-operator boundary unguarded. These are all
live in `test_cutover_handoff.py` today:

- `test_handoff_defers_host_acceptance_to_the_operator_steps` — the handoff must state that host
  acceptance is `operator evidence`, not a test result, and must make the `parked-work handshake`
  an explicit gate. Four tokens, all still asserted.
- The module docstring's own standing disclaimer: this gate "never asserts that host acceptance
  passed. That is operator evidence from Steps 43, 45, 49, and 50; a green suite is a
  precondition, never a substitute."
- `test_this_gate_executes_nothing` — the gate cannot manufacture host evidence even by accident.
- [`host-native-discovery-cutover-plan.md`](host-native-discovery-cutover-plan.md) §"Static gates
  prove structure; operator evidence proves host behavior", which is the doctrine all of the above
  implement.

The distinction the four phrases defended is therefore intact. What changed is that the events
they described have happened, so banning their *names* no longer defends anything.

### 1.5 If a future reviewer disagrees

Reopening this needs an operator decision recorded here, not a review finding. A reviewer who
believes the retirement was wrong should say so as a finding against **this record**, with the
specific true statement the restored assertions would still permit the README to make. Absent
that, the assertions stay retired.

---

## 2. The `what remains is operator-only` ban — DECIDED: widen the scope, exempt citations

### 2.1 The problem, measured

The one surviving anti-overclaim assertion bans one literal phrase
(`what remains is operator-only`), and it scanned **`README.md` only**. The README never carried
that phrase. It lived at
[`host-native-discovery-cutover-plan.md`](host-native-discovery-cutover-plan.md)`:679`, in a
roll-up preamble the README gate does not read.

So the ban's scope excluded the site of the only real instance. That is a ban in name only, and
the step exists to settle it rather than leave it to luck.

> **Authoring rule for this record: a code span must not be wrapped across a line break.** The
> gate strips single-line backtick spans only, so a citation split by a markdown wrap reads as
> prose and reds — which is exactly what happened on this record's first draft, at the sentence
> immediately above. That is the Step 66 lesson repeating: a document whose subject is a banned
> phrase is the likeliest place to carry one. The gate caught it, not review (§2.5). Keep every
> citation of a banned phrase on one line.

Measured across the tree at authoring time, the phrase appeared in **three** places, not one:

| Site | Role |
|---|---|
| `host-native-discovery-cutover-plan.md:679` | A stale status **claim** — the actual defect |
| `host-parity-repair-plan.md:132` | The impact table, **naming** the string to be fixed |
| `host-parity-repair-plan.md:411` (Step 69's own `Done when`) | **Quoting** the phrase to specify the ban |

The third site is the trap. A naive "widen the gate to scan `documentation/`" goes red on the plan
document that *specifies* the ban, and on the very step implementing it. Deciding this by
accident would have produced either an unsatisfiable gate or a hand-cut hole.

### 2.2 Options weighed

1. **Remove the string at `:679`; leave the gate scanning `README.md`.** Cheapest, and the
   `:679` removal is required anyway. Rejected as *sufficient*: it repairs the instance and
   leaves the coverage gap exactly as found — the next stale claim in any document other than
   `README.md` ships green, which is precisely how this one shipped.
2. **Widen to `documentation/**` with a derived exclusion for the plan document.** Step 66 set
   this precedent: its tier-1 categorical bans grade a surface derived from a self-declared
   marker and deliberately exclude the plan, recorded as a decision rather than a hole
   ([`step-66-vendored-reference-decisions.md`](step-66-vendored-reference-decisions.md) §7.2).
   Workable, but excluding a whole file by name is coarser than the problem: only the *quoting
   lines* need exemption, not every claim the plan makes.
3. **ADOPTED — widen to the whole status-bearing markdown surface with NO file excluded, and
   exempt backticked CITATIONS.**

### 2.3 The adopted decision

The gate now scans **`README.md` + `CLAUDE.md` + `documentation/**/*.md`, with no file excluded —
not even a plan** — and exempts single-line backtick code spans. A backticked phrase is a *citation of a
token*; prose is a *claim about status*. That distinction is derived from the markup, so any
future document that quotes the phrase correctly is covered by construction and nobody has to
remember to add it to a list.

Consequences, all deliberate:

- `host-parity-repair-plan.md:132` was **reworded to backtick** the phrase, which the impact
  table should have done anyway — every other token on that row is already a code span. This is
  markup matching meaning, not a ban being loosened.
- Step 69's `Done when` already backticked it and needed no change.
- The sibling `scanned_docs()` helper skips `*-plan.md`, and that exclusion was **not** reused.
  Its reason is about path tokens (a plan legitimately names artifacts it has not built yet) and
  does not transfer to status prose, where a plan is one of the likeliest places for a stale
  claim to sit. Reusing it would have re-created the hole being closed.
- The old `README.md`-scoped assertion was **kept**, not replaced. It is now redundant with the
  wider sweep; deleting it would be a narrowing, and this phase does not narrow.

### 2.4 What the gate claims — and what it does not

This phase has hit the over-claiming-gate defect three times (a red-on-garbage anchor whose
docstring overstated its coverage; the fix for that docstring still overstating it; and an anchor
whose mechanism turned the regression it hunted into a silent skip). So the claim is stated
before it is believed:

**CAN decide.** Every phrase in `_STALE_CUTOVER_STATUS_PHRASES` is absent from the prose of every
`README.md`, `CLAUDE.md`, and `documentation/**/*.md` file. A literal-string question, fully
decidable.

**CANNOT decide.** Whether any document presents completed Phase 7 cutover-path work (Steps
42-50) as outstanding. That is a **semantic** class; a literal matcher decides a **syntactic**
one, and paraphrase defeats any fixed list. Human review owns the class — the same tier-3
conclusion Step 66 reached after three rounds of fitting one more pattern to the instance that
had just escaped. The phrase list is a **tripwire** for one spelling that has actually shipped
stale here, maintained by adding the next spelling that actually does.

**Also cannot see:** a stale claim written inside backticks. Accepted blind spot, stated rather
than hidden — prose does not get written in code spans, and it is the price of excluding no file
by name.

### 2.5 Anchors — watched to fail before being believed

Not asserted; observed. Each was planted, the suite run, and the failure read:

| Planted defect | Result |
|---|---|
| The exact stale sentence appended to `architecture.md` — a document the old `README.md`-scoped gate could never read | RED, naming the file and the phrase |
| The original sentence restored at its original site in `host-native-discovery-cutover-plan.md` (a `*-plan.md`) | RED — proof the widened scope would have caught the real instance |
| `status_scanned_docs()` narrowed by reintroducing the `*-plan.md` exclusion | RED on the scope floor |
| A backticked citation of the phrase | GREEN, as intended |
| Prose surrounding a code span on the same line | RED — stripping does not swallow neighbouring prose |

One further data point, unplanned and worth more than the planted ones: **this record's own first
draft reds the gate.** §2.1 cited the banned phrase inside a code span that a markdown line wrap
split across two lines, which the single-line strip cannot see, so it read as prose. Neither the
author nor a line-based grep noticed; the gate did, naming the file and the phrase. That is the
Step 66 finding reproducing itself — the document describing a ban is the likeliest place to
violate it — and it is the reason the whitespace normalization happens **after** stripping rather
than before.

The scope floor is pinned at **20** — `README.md`, `CLAUDE.md`, and the 18 documents under
`documentation/` that existed before this record was added. It is deliberately the *pre-existing* surface rather
than the post-step count: [`../tools/release.ps1`](../tools/release.ps1) runs this suite from
inside a `git ls-files` stage, where a file not yet in the index is simply absent, and a floor
that assumed otherwise would red for a reason having nothing to do with coverage.

---

## 3. Scoping the "no outstanding work" clause — Step 47b stays PENDING

The Done-when is scoped to the **cutover path, Steps 42-50**, and that wording is load-bearing.
**Step 47b (containment-gate hardening) legitimately remains PENDING** and is deliberately off
that path. An unscoped "no doc claims work outstanding" would contradict the cutover plan's own
table row for 47b, one line below the roll-up this step corrects.

Verified after the edits **by enumeration**, not by a remembered count — a hardcoded occurrence
count drifts the moment any document adds a mention, so the check greps every occurrence of `47b`
across `documentation/` and `README.md` and reads its sense. All retain PENDING; no document
anywhere claims 47b is done, complete, landed or merged. None was reworded, and no edit in this
step touched a line describing it. The corrected roll-up preamble now names 47b explicitly as the one Phase 7 step still
pending, which strengthens the distinction rather than blurring it.

---

## 4. Stale claims corrected in the same pass

Doc reconciliation is this step's charter, so three measured-false claims were folded in. Each was
verified against the code, not inferred.

### 4.1 `provider-expansion-plan.md` — the dead `SKILL_MESH_LEGACY_SOURCE` premise

Two statements (the plan-review preamble, and the Step 55 source-of-truth bullet) claimed that
generation requires the `SKILL_MESH_LEGACY_SOURCE` environment variable, and that a clean
`/build-phase` worktree therefore **cannot** regenerate. Both are false as of Phase 7.5 **Step
67**, which made [`../tools/gen_manifest.py`](../tools/gen_manifest.py) hermetic: the variable
name appears nowhere in the file, it reads nothing outside this repository, and it reproduces
both committed artifacts byte-identically.

Both statements of the dead premise are removed. The **surviving** reason is untouched and
carries the decision on its own: the contract and drift tests read the committed artifacts and
never regenerate, so the hand-edit path stands. **Step 55 is not re-scoped** — its Files,
Produces, Done-when and hand-edit path are exactly as they were; only a factual claim changed.
Phase 8 is BUILD-READY and stays that way.

Line citations in that bullet were re-measured against the post-Step-67 file and corrected in the
same pass, because four of five had drifted from the same cause and leaving them would have made
a reader trust the rest:

| Cited | Actual | What is there |
|---|---|---|
| `gen_manifest.py:51` | `:88` | `LOCAL_CAPABLE = {` |
| `:229` | `:440` | `"local_capable": name in LOCAL_CAPABLE,` |
| `:238` | `:449` | the count |
| `:344` | `:555` | the sorted member list |
| `:369` | — | now a roster `raise` guard, not an exit; no longer cited |

Five `test_manifest_contract.py` anchors in the same step had drifted by a uniform **+3** — the same
cause as §4.3, Step 67 adding three imports above them. Each was corrected after reading the target
line, not by applying an offset:

| Cited | Actual | Assertion there |
|---|---|---|
| `:105` | `:108` | `assert derived["local_capable"] == 24` |
| `:129` | `:132` | exact set vs the fixture |
| `:153` | `:156` | per-skill `local_capable` |
| `:175` | `:178` | `set(prov.keys()) == {"claude", "gpt"}` (cited three times) |
| `:210` | `:213` | `test_vision_or_subagent_implies_not_local` |

This is more than tidiness: Step 55 **hand-edits against these anchors**, and stale `:105` points at
`assert derived["total"] == 50` — a builder following it edits the wrong assertion in a BUILD-READY
plan. A blind numeric replace was explicitly avoided: the `:129` on the `model-tier-map.json` impact
row is a `runtime/skill-router.ps1` citation, not this file, and would have been corrupted by one.
`expected_inventory.json:7,66` were re-measured and are correct as written.

### 4.2 `host-parity-repair-plan.md` Step 68 — a citation matching nothing

The "Do NOT quote every scalar" bullet cited `test_distributions.py:328-337` as asserting "key
presence only". Those lines are a `# Fixtures` section header and the `dist_root` fixture — the
citation matched nothing. The assertion the sentence describes is
`test_claude_skill_md_not_given_synthesized_frontmatter` at `:1071-1080`, whose
`assert "user-invocable" in fm` is presence-only with no value check. The sibling citation for
`_parse_leading_frontmatter` in the same sentence had drifted too (`:260-276` → `:1003-1026`) and
was corrected with it. **The claims were true and are unchanged; only the anchors moved.**

### 4.3 `host-parity-repair-plan.md` — `test_manifest_contract.py:279`

The assertion is intact but now sits at `:282` (three imports were added earlier in the file). The
plan cited `:279` in **five** places — Step 67's DECIDED bullet, two in Step 62, Step 67's Problem
bullet, and the risk table. All five were corrected; fixing one of five would have left a reader
trusting four stale anchors. Same-cause sweep, no semantic change.

One more of the same class was found and corrected while sweeping: Step 67's Problem bullet cited
`test_distributions.py:346` for the DESCRIPTIONS assertion, which is now
`test_manifest_description_matches_gen_manifest_source_of_truth` at `:1083-1102`; `:346` is an
unrelated `assert INSTALL_SCRIPT.is_file()`.

---

## 5. What this step deliberately did NOT do

- **It did not re-litigate the retirement.** §1 records the reason; it does not reopen the
  question. That is the whole point of writing it down.
- **It did not add a semantic "outstanding work" detector.** Such a gate cannot decide the class
  it would name (§2.4). The Done-when is satisfied by reconciliation plus human verification, and
  the one literal phrase that actually shipped stale is enforced mechanically.
- **It did not rewrite `47b`'s status anywhere.** 47b is pending; every document saying so is
  correct (§3).
- **It did not re-scope Phase 8.** Only false statements in
  [`provider-expansion-plan.md`](provider-expansion-plan.md) were corrected (§4.1).
- **It did not narrow or delete any assertion.** The `README.md`-scoped ban was kept alongside the
  wider sweep, and the sweep added assertions without removing one.
