# Step 66 — vendored workspace references: decisions and sign-offs

> **Scrub record.** This document's whole subject is private values that were **removed**
> from seven vendored documents, which makes it at least as likely to carry one as the files
> it describes — it did, in three consecutive review rounds. So it is graded by the same
> tier-1 categorical bans as the payload itself
> (`tests/package-integrity/test_skill_tree.py`, `_tier1_graded_docs`), and this line is the
> self-declaration that puts it in that derived set. Every removed value below is named by
> **class and source location only** and is restated nowhere: not in prose, not inside
> quotation marks, and not in a sentence explaining that it was removed. That last one is
> not a hypothetical — it is how this gate came to exist. §7.2 records the two legitimate
> constructs this costs the record, and why neither was answered by loosening a ban.

Phase 7.5, Step 66; the plan's Step 66 block owns the tracking-issue number, and this record
carries no issue-shaped pointer at all — not even to this repository's own issues, for the
reason §7.2 gives. This is the **named in-repo record** the step's Done-when
requires: the reconcile-or-fork decision for each of the three copies that already existed
in `_shared/`, the per-file scrub sign-off for all seven vendored documents, the
disposition of each of the 14 external links they carry, and the citation-form decision
that governs how the ten canonical cores now reach them.

Nothing here is advisory. Each claim below was measured against the bytes actually
committed, not against the plan's 2026-08-09 line numbers, which had already drifted.

---

## 1. Vendor-source contract

The seven source documents live **outside this repository**, in the operator's coding root
under `.claude/references/` (six of them) and `.claude/rules/` (`subagent-economy.md`, which
has no `references/` copy). `skill-mesh/.claude` does not exist, and
`tests/package-integrity/test_manifest_contract.py` gates absolute user paths out of every
committed file because this is a public repository.

So the source root is a **contract, not a path**, exactly as `tools/gen_manifest.py`
already established for the same problem: it is supplied at authoring time through the
`SKILL_MESH_LEGACY_SOURCE` environment variable. The vendoring itself was a one-time
authoring act; what must never land in a commit is the absolute path, and none did.

> **Since Step 67:** `tools/gen_manifest.py` no longer reads that variable at all — its
> generation is hermetic, because the Step 50 cutover overwrote the root it used to scan.
> The decision recorded above is unchanged and still correct for the authoring act it
> describes: a source root that lives outside this repository is named by contract, never
> by a committed path. Only the cited precedent moved on.

`worktree-hygiene.md` was taken from `references/` (6,711 B as measured 2026-08-10, not the
5,901 B the plan recorded — the source was edited after the plan was written). A 672 B stub
of the same name also exists under `rules/`; vendoring the stub would have silently dropped
the seven-landmine content, so it was not used.

---

## 2. The three existing copies — reconcile or fork

All three had diverged from source. The plan (D4) framed the divergence as **stale
doctrine**, and warned that blindly repointing at the existing copies would swap stale
content in while every gate stayed green. Measured, the picture is more specific than that,
and it changes two of the three decisions:

### 2.1 `intake-engine.md` — **RECONCILE**

Measured divergence: 5 hunks, all of them *vendoring adaptations already applied by the
earlier commits* (`8de32f6`, `e55b6a8`) — four external links converted to prose, and one
cross-repo phase pointer (a parenthetical naming a numbered step of a phase in the private
workspace repo, on the `user-gateway` contract link) dropped. **Zero doctrinal
divergence.** The document body is otherwise byte-identical to the current source.

Decision: reconcile to the current source and re-apply the same adaptations mechanically
(see §3 and §4), so the copy is regenerable rather than hand-maintained. The net content
change is nil; the value is that the adaptation is now recorded and repeatable instead of
being an undocumented hand edit whose provenance a later reader cannot reconstruct.

### 2.2 `skill-role-taxonomy.md` — **RECONCILE**

Measured divergence: 1 hunk. The self-citation line was re-anchored from
`../../references/skill-role-taxonomy.md` to `../_shared/skill-role-taxonomy.md`. Again a
vendoring adaptation, not doctrine, and a **correct** one: `../_shared/skill-role-taxonomy.md`
resolves both in this checkout and inside a built profile, and it is one of the in-scope
references the link gate counts as resolving. It is preserved verbatim by the reconcile.

Decision: reconcile to the current source, keeping the re-anchored self-citation.

### 2.3 `skill-pipeline.md` — **RECONCILE** (the one genuine fork, now closed)

Measured divergence: the vendored copy was **8,432 B against a 12,617 B source** and was a
genuine older-and-trimmed fork. It was missing, among other things: the home-context and
window-recycle section (the `[dev-root]` / `[project]` two-repo annotations on the build
rail), the `/repo-wrap` entry, the `/user-afterparty` entry, the `/judge-motion` visual
tier, and the `/user-debug` / `/memory-distill` rename note. Those are live routing
doctrine that `user-gateway` — the one skill that consults this web per fragment — would
have been reading a stale version of.

Decision: reconcile to the current source, then re-apply the public-mirror adaptations as
scrubs (§3). Fork was rejected: this file is the **ONE owner of the rails**, and a mirror
that silently lags the owner is the drift the plan's D4 warned about, just pointed the other
way. Nothing in the trimmed fork was a deliberate correction that the reconcile discards —
every deletion in it is explained by the source simply being newer.

---

## 3. Per-file scrub sign-off

Each of the seven was re-checked **against the bytes actually vendored**, not against the
plan's per-file verdicts, which were measured on 2026-08-09 against files that have since
changed. Five categories were checked on every file:

* **I** — operator identifiers (username, home path, session-dir slug, raw session UUIDs)
* **X** — cross-repo issue / step / phase references (the operator's workspace repo, which
  these documents are vendored *from*, is **private**)
* **M** — account metrics (billing- or usage-share numbers)
* **H** — harness-configuration disclosure (hook libraries, settings files, skill-tree paths)
* **T** — references to tooling skill-mesh does not ship

The scrubs are applied by exact-string replacement with an asserted occurrence count, so a
future source edit that moves a scrub target fails loudly rather than silently shipping the
unscrubbed bytes.

**Who certifies a class, and who merely enforces a shape** (added in iteration 3, after the
gate was found over-claiming twice). This per-file sign-off is the **only class-level
authority** in Step 66. The committed gates in `tests/package-integrity/test_skill_tree.py`
make two strictly narrower claims, and neither is a certification:

* **Categorical bans** over the seven vendored documents *and this record* forbid whole
  categories outright. `_VENDORED_PAYLOAD_BANS` is the one owner of which categories those
  are; this record does not keep a second copy of that list. What such a rule claims *is*
  the category it names, so the claim is decidable and cannot over-reach.
* **Tripwires** over the open roots recognise shapes that have actually escaped into this
  tree. They say nothing at all about the shapes that have not.

Class-level absence is a judgment no shape rule reproduces. The verdicts below keep a public
project name, drop a machine-local branch name, and deliberately keep a state-directory path
— three different outcomes for tokens no regex can tell apart — and a pointer spelled "Step
12 of the same phase" carries no decidable token whatsoever. So a green test run is evidence
that the enumerated categories and the known shapes are absent; **the five per-file verdicts
below are the only evidence that the classes are.** A reader who needs the stronger claim
must read the sign-off, not the gate.

### `step-authoring.md` — **SAFE, no content scrub**
I: none. X: none. M: none. H: none. T: none. Only the two `code-quality.md` links were
de-linked (§4). Verified clean under all six leak patterns, including the new hex-UUID one.

### `task-state-schema.md` — **SCRUBBED (5 edits)**
* **I** — the raw harness session UUID and the private session-transcript path were the two
  highest-value tokens in the whole payload. The source paragraph named a real session UUID
  and then the per-session `.jsonl` transcript path under the harness projects directory
  that proved it. Both are
  gone; the paragraph now states the same contract (scratchpad UUID == transcript basename
  == hook `session_id`, no mapping table) with no identifier in it. **This is the
  Done-when's named line, and it is absent from the vendored copy.**
* **X** — a sentence tying the hook wiring to a numbered step and an issue number in the
  private workspace repo was removed. Neither the step number nor the issue number is
  reachable by a reader of this repository; the sentence now says the wiring is spec until
  it lands.
* **H** — `.claude/hooks/lib/task-state-derive.ps1` → "the workspace's task-state derive hook
  library"; `.claude/skills/session-wrap/SKILL.md` → "the `session-wrap` skill contract";
  `.claude/settings.json` → "the harness settings file".
* **H, retained deliberately** — `.claude/task-state/…` paths. These are the *subject* of the
  document (they define where the state file lives), removing them would gut the contract,
  and the same paths already appear in five committed skill cores (`user-afterparty`,
  `lesson-harvest`, `plan-expedite`, `session-wrap`, `build-phase`). Not new disclosure.
* **M** — none. **T** — none.

### `skill-pipeline.md` — **SCRUBBED (8 edits)**
* **X** — a parenthetical naming a numbered step of the current phase was removed, and the
  `## Review routing` heading lost a trailing parenthetical that pinned it to an issue
  number. Both pointed into the private workspace repository.
* **I** — the private cron name (a specific scheduled-job identifier on the operator's
  machine) replaced with "the workspace's monthly hygiene cron". A named scheduled job is
  infrastructure disclosure with no reader value.
* **H** — three `.claude/references/…` and one `.claude/rules/…` link **labels** rewritten to
  the plain document name. These mattered twice over: they are harness paths, and each was
  also an occurrence counted by the link gate's home-anchored ceiling, which this step must
  not grow.
* **T** — `/goblin-sweep` removed from the `do` rail. It is the one tool named here that
  skill-mesh does not ship and that appears nowhere else in this tree.
* **T, retained deliberately** — the rails table names workspace skill slugs throughout
  (`/repo-wrap`, `/deep-research`, `/goal`, …). Those are routing doctrine, not
  infrastructure disclosure: a slug in a routing table tells a reader which rail a fragment
  belongs on, and stripping them would leave the web incoherent. The distinction drawn here
  is *named private infrastructure* (a cron job, a settings file, a private repo's issue
  numbers) versus *a skill's public name*.
* **M** — none.
* **H — UNCOVERED. Found 2026-08-12, after this sign-off, and NOT part of it.** The
  `investigate` rail's dispatch cell names a harness workflow *registration* name, forbids the
  host's built-in fallback, and cites a rule document that does not ship here. By the
  distinction this row itself draws one bullet above, that is named private infrastructure
  rather than a skill's public name, so it warranted either a scrub or a deliberate retention
  with a stated reason; it received neither, and no other class row covers it. Left in place:
  the fix is a behavioural change to the rail (a consumer has no such registration and the
  documented fallback is prohibited), not a wording edit, so it belongs to its own issue rather
  than to a correction pass. The same identifier is already published in a canonical core
  outside this vendoring's charter, so this is a coverage gap in the sign-off, not a new
  disclosure. The vendor header carried by all seven payload files was corrected the same day
  to stop asserting that this class is exhaustively removed.

### `intake-engine.md` — **SCRUBBED (4 edits)**
* **X/H** — a harness skill-tree path for the `user-gateway` contract, carrying a
  parenthetical that pinned it to a numbered step of the same private-repo phase →
  "the `user-gateway` skill contract".
* Three sibling links re-anchored to `./` form (§4).
* **H, retained deliberately** — `<git-root>/.claude/task-state/intake-*.md`, the ledger path
  formula this document exists to own. Same reasoning as `task-state-schema.md`.
* **I: none. M: none. T: none.**

### `skill-role-taxonomy.md` — **SAFE, no content scrub**
I: none. X: none. M: none. H: none. T: none. The only edit is the vendored self-citation
(§2.2) plus the `code-quality.md` de-link. Clean under all six leak patterns.

### `worktree-hygiene.md` — **SCRUBBED (1 edit), plus one structural edit**
X: none. M: none. H: none. T: none. Its project mentions (`toybox`, `Alpha4Gate`) are
already present in this public tree in many committed files, so they are not new disclosure.

**I — the one item, called out by line rather than covered by a blanket verdict.** §3's
last bullet ("Every check above is about COMMITS") anchors its lesson on a **dated
private-workspace incident from the day before this vendoring**: it named a specific stale
worktree branch (a `build-step-*` name with its creation epoch), the source file that was
being rewritten, and exact uncommitted line counts. Iteration 1 rated this file a blanket
SAFE without addressing it, which was the wrong shape of sign-off even if the verdict had
been right — a reader cannot tell a considered "acceptable" from an unnoticed item.

Assessed on its own: the branch name is a machine-local artifact identifier with an epoch
in it, which is *infrastructure detail about the operator's working copy* and has no reader
value — the lesson holds identically without it. The rest (a module rewrite, a rough line
count, the two-defect outcome) is the evidence the bullet rests on and is
stylistically identical to the already-public anchor incidents in this tree.
Unlike those anchors, however, this one is **T-1 day fresh**, so it describes work still in
flight rather than a settled, published outcome. **Decision: abstract the branch name, the
file name and the exact counts; keep the incident, the date framing ("a recent case") and
the lesson.** Erring toward abstraction costs the reader nothing here, because none of the
removed tokens is load-bearing for the rule.

The remaining structural edit is not a scrub: its workspace YAML frontmatter (`description:`) was
dropped, because a `_shared/` payload file must not open with frontmatter —
`Add-Provenance` would take its frontmatter-first path and
`tests/distributions/test_distributions.py`'s header stripper asserts that premise
explicitly. Nothing downstream of the vendoring reads that block.

### `subagent-economy.md` — **SCRUBBED (3 edits)**
* **M** — the rule's opening sentence carried a measured share-of-spend figure for one
  operator's account, together with a three-part breakdown (two further shares and a
  character-count magnitude for a typical sub-agent return). That is **usage telemetry for
  a specific account**, and the figures are restated nowhere in this record on purpose.
  Replaced with the qualitative claim the rule actually rests on ("the large majority of a
  long window's token cost is incurred at high context", the two leaks named without
  numbers). The rule's prescriptions are unchanged; only the account-level numbers are.
* **X/M** — the `## Source` section named two private investigation documents *and* restated
  the metric. Replaced with a dated, unnamed reference to the two workspace investigations.
* **M, the third edit — found in iteration 3, and the reason the count above reads 3 rather
  than 2.** The same measured magnitude was restated a *second*, independent time in the
  body of Rule 1 (vendored copy line 22, one sentence below the rule's two bullets), where
  it survived the first two edits untouched. The bullet above claimed that magnitude
  "Replaced with the qualitative claim"; that was true of the opening sentence and false of
  this one, so **this row certified a class handled while a member of the certified-removed
  set sat in the file verbatim.** Two things let it through, and both are worth naming: the
  scrub was executed against a line list inherited from what an earlier review happened to
  find, rather than re-derived from the class; and the occurrence carried no share figure
  and no billing vocabulary, so no committed pattern of the day had a shape for it either.
  **The inaccurate certification was the defect, not the fragment** — stripped of the
  billing linkage the opening scrub removed, a bare magnitude is in kind with the
  open-ended turn-count magnitude that stood beside it in the same sentence, which the same
  edit removed; neither is restated here, and an earlier draft of this very row restating
  one of them is the third round the block narrative describes. Both halves are now fixed:
  the sentence makes its point in the file's own Rule-1 vocabulary with no magnitude in it,
  and this row states what was actually done. A member of this class can no longer survive
  here unnoticed — §7's tier 1 bans scaled and open-ended magnitudes *outright*, across all
  seven vendored documents **and across this record**, which is what a bounded surface buys
  and an open root cannot.
* **I: none. H: none. T: none.**

---

## 4. Disposition of all 19 outbound links (14 external + 5 internal)

D-63-A settled the question the plan left open: **allowlist replacement is not permitted —
an entry may leave `KNOWN_DANGLING`, none may enter.** So every external link had exactly
two options, vendor or convert to prose. **All 14 were converted to prose (de-linked); zero
were vendored.**

Vendoring any of them was rejected for one reason stated once: each target carries its own
outbound links, so vendoring `code-quality.md` alone would pull in a second wave, and the
payload — which ships into *both* host profiles — would grow without bound for documents no
skill core cites directly. De-linking keeps the sentence readable and the claim attributable
while removing a promise the tree cannot keep.

De-linking is mechanical: the markdown link's destination is dropped and its bracketed
label is kept as plain text. Where that label was itself a
relative path it was reduced to the plain document name first — otherwise the de-link would
have handed the link gate a fresh `rules_anchored` dangling reference, which is what
happened on the first pass with `working-directory.md` and is why that case is called out.

| # | Source file | Target | Occurrences | Disposition |
|---|---|---|---|---|
| 1–2 | `step-authoring.md` | `../rules/code-quality.md` | 2 | de-linked |
| 3 | `intake-engine.md` | `../rules/code-quality.md` | 1 | de-linked |
| 4 | `skill-role-taxonomy.md` | `../rules/code-quality.md` | 1 | de-linked |
| 5–6 | `intake-engine.md` | `../rules/measurement-validity.md` | 2 | de-linked |
| 7 | `intake-engine.md` | `../rules/knowledge-placement.md` | 1 | de-linked |
| 8–9 | `intake-engine.md` | `shakedown-engine.md` | 2 | de-linked |
| 10 | `skill-pipeline.md` | `shakedown-engine.md` | 1 | de-linked (label `.claude/references/shakedown-engine.md` reduced to the plain name first) |
| 11 | `skill-pipeline.md` | `../rules/working-directory.md` | 1 | de-linked (label was itself the relative path; reduced to `working-directory.md` first) |
| 12 | `skill-pipeline.md` | `../rules/descriptor-contract.md` | 1 | de-linked (label `.claude/rules/descriptor-contract.md` reduced to the plain name first) |
| 13 | `worktree-hygiene.md` | `windows-shell.md` | 1 | de-linked |
| 14 | `task-state-schema.md` | `../../docs/current-md-race-fix-plan.md` | 1 | de-linked |

The five **internal** links — the ones whose targets ARE in this payload — went the other
way and were strengthened, from a bare filename to an explicit `./` form:

| # | Source file | Target | Occurrences | Disposition |
|---|---|---|---|---|
| 15–17 | `intake-engine.md` | `./skill-pipeline.md` | 3 | re-anchored `./` |
| 18 | `intake-engine.md` | `./task-state-schema.md` | 1 | re-anchored `./` |
| 19 | `skill-pipeline.md` | `./intake-engine.md` | 1 | re-anchored `./` |

`./` is not cosmetic: a bare `x.md` link destination is **out of the link gate's reference
scope**, so it would ship unvalidated, while `./x.md` is in scope and must resolve — in this
checkout and in every built profile. One further link was created by a scrub
(`skill-pipeline.md` → `./task-state-schema.md`, replacing a `.claude/references/…` backtick
token), for the same reason.

Every vendored file's own outbound relative links therefore either resolve or are prose.
Measured over the seven after vendoring: **0 dangling, 7 in-scope references resolving.**

---

## 5. Citation form — why the ten cores cite `<repo>/_shared/<leaf>`

The plan's D5 says "repoint as markdown links, never backticks", and the plan's own
Done-when says `KNOWN_DANGLING` shrinks to **zero** for the `references_anchored` and
`rules_anchored` classes. **Those two requirements are jointly unsatisfiable**, and the
reason is structural rather than a matter of effort. It is worth stating precisely, because
the obvious repoint is the one that breaks the gate:

1. The link gate resolves a `skills/<n>/core.md` reference against **`skills/`**, because
   that is the directory that becomes the host discovery root. Measured, every spelling of
   a `_shared` citation from a core is therefore dangling: `../../_shared/x` **escapes** the
   root, `../_shared/x` resolves to an absent `_shared` directory *under* `skills/`, and
   `_shared/x` resolves
   to the absent `skills/<n>/_shared/x`. `test_link_resolution.py`'s own module docstring
   states this as the corollary for Step 64.
2. A `_shared` directory under `skills/` cannot be created —
   `test_skill_tree.py::test_shared_dest_divergence_is_intentional`
   asserts it does not exist, and Step 64 recorded the rejection of that path.
3. The allowlist is **shrink-only** (D7 / D-63-A). So repointing the 18 citations to
   a markdown link whose destination is `../../_shared/x.md` — the D5 form, and the
   spelling `Repoint-SharedReference`
   already rewrites — would retire 12 keys and introduce **12 new dangling canonical keys**,
   which assertion 1 hard-fails. It is not a partial burn-down; it is a red gate.

The resolution keeps Step 64's recorded doctrine — *the canonical tree is a build input, not
a discovery root; the builder translates at emit time and the profile-side scan is the
authoritative check* — and applies it to a token that carries no dangling obligation:

> Canonical cores cite `<repo>/_shared/<leaf>`. `Repoint-SharedReference` rewrites it to
> `../_shared/<leaf>` when the file is emitted, alongside the existing `../../_shared/` and
> `../../../_shared/` rewrites.

`<repo>/_shared/<leaf>` is **not a spelling invented for this step**. It is the spelling
this builder already uses for exactly this problem: `Get-SharedCanonicalLabel` emits
`Canonical source: <repo>/_shared/<leaf>` into every payload file's provenance header,
repo-rooted on purpose so the header does not become a reference that resolves from the
emitting file's own directory. The angle-bracket segment is a **documented template
placeholder** in both gates (`is_reference_in_scope` and `_ref_defect` each return early on
`<`, `>`, `*`), so the citation carries no resolution obligation in the canonical tree,
where none could be met.

What replaces the validation D5 wanted — and it is stronger, not weaker:

* **A mistyped filename throws the build.** `$SHARED_REF_RE` has no lookbehind, so the
  `_shared/<leaf>` substring inside `<repo>/_shared/<leaf>` is harvested as a closure seed;
  a leaf that does not exist raises `shared asset source missing: _shared/<leaf>` in
  `Get-SharedClosure`. D5's stated worry ("a typo ships green") is closed at build time.
* **The emitted reference is positively gated.** `../_shared/<leaf>` in
  `dist/<p>/<skill>/core.md` **is** in the link gate's scope and **must** resolve; if the
  repoint were dropped or the asset never shipped, the profile scan reports a new dangling
  reference and assertion 1 fails.
* **Four tests assert the chain directly, and one of them is the negative case.**
  `test_vendored_reference_citations_reach_the_payload` walks all 12 (skill, document) pairs
  in both profiles; `test_shared_references_are_repointed_and_resolve` asserts tree-wide that
  no `<repo>/_shared/` survives outside a provenance header;
  `test_repo_rooted_shared_citation_is_seeded_and_repointed` is a red-on-garbage anchor on a
  synthetic tree, proving both the seeding edge and the rewrite; and
  `test_mistyped_repo_rooted_shared_citation_throws_the_build` plants a citation whose leaf
  does not exist and asserts the build **fails**, naming the missing leaf. That last one was
  added in iteration 2 and it is the load-bearing one: the first three all exercise the
  positive path, so without it the single mechanism this section names as D5's replacement —
  the `Get-SharedClosure` throw — had no proof it fires. Unlike the other three shared-
  reference spellings, `<repo>/_shared/x` is exempt from BOTH link gates by the
  template-placeholder rule, so for this spelling the throw is not a second line of defense,
  it is the only one.

**Recorded finding for the orchestrator:** D5's literal instruction — markdown-link form —
is *not* satisfied in the canonical tree, and cannot be by any step operating under the
frozen allowlist. Angle-bracket destinations are also not valid CommonMark link
destinations, so even a link-form placeholder would render literally. D5's *rationale* is
satisfied by the three mechanisms above. Reopening the literal form would require an
operator decision widening the frozen record, which D-63-A places above a step.

---

## 6. Measured burn-down

Run with the Step 63 detector (`python tests/package-integrity/test_link_resolution.py
--emit <scratch>`), against the staged tree, both profiles built by the production builder.

| | before | after |
|---|---|---|
| `KNOWN_DANGLING` total | 112 | **75** |
| `references_anchored` | 33 (11 canonical + 22 profile) | **0** |
| `rules_anchored` | 4 (2 canonical + 2 profile) | **0** |
| `shared_anchored` | 21 | 21 (Step 64's recorded canonical residual) |
| `shared_bare` | 40 | 40 |
| `home_anchored` | 9 | 9 |
| `profile_layout` | 5 | 5 |

Both target classes reached zero. The plan's class arithmetic was again off: it described
`rules_anchored` as one canonical citation, but the class was **4 keys with 2 canonical
members** — `skills/user-afterparty/core.md` *and* `_shared/skill-role-taxonomy.md`'s
`../rules/code-quality.md` link, which is retired here by the de-link in §4.

Detector-scope floors, all satisfied and none touched:

| floor | frozen minimum | measured after |
|---|---|---|
| `canonical_files_scanned` | 152 | 156 |
| `canonical_refs_resolving` | 112 | 118 |
| `profile_files_scanned` | 191 | 209 |
| `profile_refs_resolving` | 62 | 202 |
| `per_profile_files.claude` | 97 | 106 |
| `per_profile_files.gpt` | 94 | 103 |
| `home_anchored_doc_citation_ceiling` (a ceiling) | 144 | 142 |

`canonical_files_scanned` rises by 4, not 7: three of the seven documents already existed in
`_shared/` and were reconciled in place (§2). The detector's roots were **not** touched —
re-rooting `skills/` at the repo root is the exact mutation Step 63 froze as an attack, and
`test_escaping_reference_is_dangling_even_though_it_resolves` reds on it.

`link_baseline.json` and `BASELINE_SHA256` are **unchanged**. This step only deleted lines
from the `KNOWN_DANGLING` literal, which is the whole shape D7 asked for.

---

## 7. Leak-sweep extension

`_LEAK_PATTERNS` had five patterns and swept `skills/**/*.md` only. Four gaps, closed as far
as a mechanical gate can close them — the last two only after iteration 1's review found
that the extended gate still could not see the class its own sign-off record was an instance
of. A **fifth** defect, in what those closures were said to *prove*, is recorded in §7.1;
read this list with that correction in hand.

* **Nothing scanned `_shared/`** — the tree this step writes into, and a payload that ships
  into *both* host profiles. The sweep now walks `skills/` and `_shared/`, enumerated once in
  `_LEAK_SWEEP_ROOTS`, and it walks **every file**, not just markdown: `_shared/` ships `.py`,
  `.js` and `.svg`, and a private path in a docstring is published exactly as widely as one
  in prose. `test_leak_sweep_covers_the_shared_payload` asserts the breadth so a later
  narrowing reds instead of quietly grading a smaller tree.
* **A raw session UUID tripped none of the five patterns** — all five key on a drive letter,
  a home path, or the username. The new `raw harness session UUID` pattern closes it. The
  red-on-garbage anchor plants a synthetic session id and asserts the sweep flags it (the
  planted value is synthetic on purpose; pasting a real session id into a committed anchor
  would be the disclosure the pattern exists to stop).
* **Nothing scanned `documentation/`, and no pattern had a shape for the two classes the
  scrub itself is about.** All six patterns key on an *identifier* — a drive letter, a home
  path, the username, a session UUID. Neither of the two disclosure classes this step spent
  most of its scrub budget on had any coverage at all: **X**, a pointer into the private
  workspace repo's issue namespace, and **M**, account-level cost/usage telemetry. The proof
  that the gap was inert rather than theoretical is iteration 1's own commit, which extended
  the sweep *and* landed fresh instances of both classes in `documentation/` — entirely
  unscanned, because `documentation/` was not a swept root. Both were given shape-based
  coverage in `_DISCLOSURE_PATTERNS`, and `documentation/` joins `skills/` and `_shared/` in
  `_LEAK_SWEEP_ROOTS`. **Read the three sub-bullets as descriptions of what each pattern
  matches, not as coverage of the class it is named for** — presenting them as the latter
  was itself the next defect, corrected in §7.1:
  * **X, all roots** — an issue/PR pointer within a ~220-character window of a token naming
    the private workspace repo, in either order. It is deliberately **not** a bare `#\d+`:
    this repository carries hundreds of legitimate references to its *own* issues, so the
    disclosure is not the number, it is the number *bound to another, private repo*. The
    canonical `owner/repo#N` cross-repo spelling is matched on its own, needing no window.
  * **X, vendored payload only** — inside a vendored `_shared/` document, ANY issue-shaped
    pointer (`issue #N`, `post-#N`, `GH-N`, …) is a defect, with no proximity condition,
    because every one of those documents is copied wholesale out of the private workspace
    repo, so any issue number in one is foreign by construction. This is the rule that would
    have caught the two real instances *at their source*, where they appeared bare and no
    proximity rule could see them. The vendored set is **derived** from the `Vendored into
    skill-mesh` banner each carries, never hand-listed, and floored at seven so an emptied
    derivation cannot pass vacuously.
  * **M, all roots** — a share figure bound to billing/spend vocabulary inside a short
    window, plus two bare phrasings that attribute a quantity to an account's bill with no
    number present at all (a token count described as billed; a stated fractional slice of
    what an operator was charged). Neither literal is restated here, for the same reason the
    items in §3 are not. A number alone is not the shape
    (`session-wrap`'s context-utilisation table is full of legitimate share figures); a
    *number attributed to a bill* is.

One exemption, by literal and never by shape: RFC 4122 Appendix A's documentation UUID
`550e8400-…-446655440000`, already used as an illustrative `run_id` in a JSON sample in
`skills/build-step/core.md`. It identifies no session and no person. The anchor asserts both
directions — a session-shaped id reds, the documentation UUID does not — and asserts the
exemption list is still exactly one entry, because a growing exemption list is how a real id
eventually rides in.

### 7.1 The claim the gate makes — decided in iteration 3, after two rounds of over-claiming

**The decision, stated once so it stops being re-litigated one patch at a time:** X and M are
*semantic* classes ("a pointer into a private namespace", "a number drawn from a private
measurement set"); a regex decides a *syntactic* one; and the gap between the two is
unbounded. So **no pattern list in this repository certifies either class**, and none of them
is written as if it does.

The evidence that this needed deciding rather than patching: two consecutive review rounds
raised the same finding-shape, each time against a fresh instance outside the patterns' reach,
and each time the answer was one more shape fitted to the escape that had just been observed.
Three escapes are reproducible against the iteration-2 regexes — a *paraphrase* (the repo's
name used as a common noun between "private" and "repository", which is the phrasing that
actually shipped historically), a *distance* (roughly 230 characters of separation clears a
220-character window), and a *vocabulary substitution* (the third M-class occurrence in §3's
`subagent-economy.md` row, which carries neither a share figure nor billing vocabulary). Those
are the three ways a syntactic approximation of a semantic class always fails; a fourth round
of fitting would have produced a fourth. **An over-claiming gate is worse than no gate,
because the team stops looking** — which is the failure this whole phase exists to remove, and
the same rationale §9 gives for refusing to narrow a gate around an inconvenient finding.

The gate now makes three clearly separated claims, and the code says which is which:

| Tier | Surface | Claim | Enforced by |
|---|---|---|---|
| 1 | the seven vendored `_shared/*.md` documents (derived from the vendor banner) **and every scrub record** (derived from its own marker) — never hand-listed | whole **categories** are absent; `_VENDORED_PAYLOAD_BANS` is the one owner of which categories, and this table keeps no second copy of them | `test_vendored_payload_carries_no_banned_category` (+ the retained `…_no_issue_pointer`) |
| 2 | the open roots `skills/`, `_shared/`, `documentation/` | no **known escaped shape** is present. Not a class claim. | `_DISCLOSURE_PATTERNS`, relabelled as tripwires |
| 3 | every vendored file | the **classes** are absent | the per-file human sign-off, §3 |

Why the split falls there: a categorical ban is only affordable where a false positive is
cheap. Across a handful of files it is answered by rewording one sentence and recording the
adaptation here. Across `documentation/` as a whole it would red on hundreds of legitimate
issue numbers and share figures, and a gate that does that is one somebody switches off inside
a week — so the bans are scoped to bounded surfaces by design, and pointing them at an open
root would undo them.

Three things were **considered and rejected**, recorded so they are not re-proposed:

1. **A third round of pattern-fitting as the fix.** Rejected on the argument above. The one
   widening that did land — `_PRIVATE_REPO_TOKEN` now admits up to two interposed word tokens,
   which covers the real historical phrasing — is labelled in the source as tripwire
   *maintenance* against an observed shape, explicitly not as closing the class. It is a pure
   widening: every string the previous form matched still matches, and it adds no new finding
   anywhere in the swept tree.
2. **Raising `_CROSS_REPO_WINDOW` past the ~230-character defeat.** Rejected: any finite window
   is defeated at window+1, so raising it moves the defeat point while widening the
   false-positive surface across three open roots, and buys no claim either way. The bound is
   now documented in the source as accepted-and-permeable, which is the honest form. On the
   surface where a miss is expensive — the vendored payload — tier 1 applies no proximity
   condition at all, so the window is not load-bearing there.
3. **Diffing each vendored file against its upstream source** (or shipping a scrub manifest).
   Rejected as the answer to *this* defect: it is structurally blind to it, because the
   surviving sentence was byte-identical to its source, so "vendored == source minus approved
   edits" passes with the fragment in place. It also cannot run in ordinary CI — the source
   root is an environment-variable contract (`tools/gen_manifest.py`), not a committed path —
   and a plaintext scrub manifest would republish the very strings §9 removed. An env-gated
   *digest* drift check remains worth considering for D4's stale-copy problem; it answers "did
   the copy drift", never "is the class absent".

A fourth was rejected inside tier 1 itself: a categorical ban on bare `owner/repo` tokens.
Measured over the current payload it matches 36 times and all 36 are false — `P/D`,
`open/close`, `plan-review/plan-wrap` and their kin are ordinary prose in these documents — and
a ban whose first run is entirely false positives is a ban that gets deleted. The canonical
`owner/repo#N` spelling is already a tier-2 pattern; an unadorned foreign repo slug is left to
tier 3, and is named in the source so the omission is a recorded decision rather than an
unexamined hole.

**What did NOT change:** no pattern, root, window or assertion was narrowed or removed, in
either direction. Iteration 3 adds a tier-1 test, widens one token, and rewrites what the
comments and this record *claim*; `test_vendored_payload_carries_no_issue_pointer` is retained
unchanged and shares the same compiled object with the new table's first row — and that
sharing is **asserted with `is`, not merely commented**, so re-declaring the shape as a second
copy reds instead of drifting, per this workspace's one-source-of-truth rule for shape
constants. (Iteration 3 asserted that identity for the *first* row only — which left the two
rows that actually closed the escape deletable with the whole suite still green, since the
anchors exercise the compiled objects directly and never assert the table still carries them.
Iteration 4 extends the check to every row and floors the table's length; see §7.2.)

### 7.2 Widening tier 1 to this record — the iteration-4 scope change

Tier 1 was right and its **scope** was too small. Iteration 3 shipped it over the seven
vendored documents only, and then this record — the document whose entire subject is the
values those seven no longer carry — restated one, in the sentence explaining that such values
are restated nowhere. That was the third round in a row in which a fix for one named instance
introduced the next, and it is the whole argument for the change: a scrub record is *payload*,
not commentary on payload, and it is at least as likely to carry a removed value as the files
it describes, because those values are its subject matter.

So iteration 4 changed **scope, not mechanism**. The same `_VENDORED_PAYLOAD_BANS` rows, the
same compiled objects, one additional bounded surface (`_tier1_graded_docs`). No pattern was
added, nothing was fitted to the observed instance, and no ban was pointed at an open root —
which is what made a fourth round different in kind from rounds 1–3 rather than one more patch.

**The set is derived, not this file's name.** The hazard belongs to the genre, so any document
opening with a `**Scrub record.**` banner line is graded, present or future — a banner, not a
mention, for the reason item 3 below gives. The derivation carries the same honest limit as
the vendor banner it copies: an author who omits the banner is not graded, and tier 3 owns
that gap.

**The plan is deliberately excluded.** `host-parity-repair-plan.md` narrates this scrub in one
section but is not a record *of* it, and it legitimately carries this repository's own issue
numbers and plain open-ended counts throughout — measured against the plan as it stands, the
three rows red on 12 tokens there and all 12 are false (6 issue numbers this repository or
Phase 8 owns, 5 plain counts, 1 category noun). That is the false-positive flood that gets a
gate switched off, so
the plan's scrub narrative stays under the tier-3 sign-off. Recorded here so the omission is a
decision rather than an unexamined hole, exactly as the rejected `owner/repo` row is — and,
unlike that row, **pinned**: `TIER1_UNGRADED_DOCS` names the plan and the reason, and the test
reds if the plan is ever pulled into the graded set, if this record ever drops out of it, or if
the excluded path stops existing and the exclusion goes vacuous. A scope decision that lives
only in a comment is the same defect one layer up, so this one does not.

**Two legitimate constructs tripped the bans, and neither was answered by loosening a row** —
the alternative was checked against the compiled patterns rather than assumed:

* **This repository's own issue pointer**, in the record's opening line. Kept nowhere: the
  plan's Step 66 block is the one owner of that number, and this record now reaches it through
  the plan. The ban costs one hop and buys a decidable rule, because on *this* document "is
  this issue number ours, or lifted from the private source?" is precisely the judgment that
  failed in round 1 — so the document does not get to make it inline. Every other tracked file
  is unaffected; the ban is scoped to tier-1 surfaces.
* **The category noun the share row matches** — used here to *name* a category, never to
  state a value; the row cannot tell those apart, and on this document that is the correct
  answer rather than a limitation. The record writes "share figure" instead, and cites
  `_VENDORED_PAYLOAD_BANS` as the owner of the category list
  rather than re-spelling it. This one is a strict improvement independent of the gate: the
  list had been copied into prose in three places, and a duplicated shape constant is drift
  waiting to happen. Narrowing the row to admit the bare noun was rejected — it would have
  re-opened the one row that mechanically catches a bare share figure in the document most
  likely to quote one.

**Three smaller things landed in the same pass, and none of them narrows anything:**

1. **The ban table's wiring is now asserted row by row.** Only the first row's compiled
   object was checked with `is`, so the share and magnitude rows could be deleted with the
   whole suite green — verified by deleting them, not assumed. Every row is checked now, and
   the table's length is floored so a fourth row must arrive with its two anchors.
2. **The sibling comment that illustrated the magnitude shape with two real private values**
   is now three invented ones. A comment in a public repository is published bytes like any
   other, and illustrating a banned shape with the real removed value inside the file that
   bans it is the same mistake one layer down.
3. **The marker is anchored to a banner line, not matched as a bare substring.** As a
   substring it selected the plan on its first run — the plan describes this mechanism and
   quotes the marker — and a self-declaration that any *citation* of it can trigger is not a
   self-declaration. The vendor banner can be matched loosely because no other document
   quotes it; this marker is quoted by design, and both directions are anchored in the test.

---

## 8. What this step deliberately did NOT do

* **It did not touch `documentation/phase-75-baseline.md`.** That table predates Step 64 and
  is stale, but reconciling it is Step 69's territory and editing it here would collide.
* **It did not change `config/skill-manifest.json` or `expected_inventory.json`.** The plan
  allowed for `global_support_assets` moving; it did not have to. The manifest already
  declares the whole shared directory as ONE asset (one legacy source mapped to one
  canonical dest), so seven new files inside it move no manifest entry and no consumer of
  `global_support_assets` (`test_manifest_contract.py:156,258-271,534`;
  `test_skill_tree.py:238,263,312`; `expected_inventory.json:1204`) sees any change. Verified
  by running both suites.
* **It did not update the 46 legacy top-level `<skill>/SKILL.md` packages.** D-63-B puts them
  out of scope: they are a frozen compatibility surface for the deprecation window, not
  canonical, and not updated by the migration.
* **It did not scrub anything in `documentation/` beyond the two files named in §9.** The
  widened sweep grades the whole directory; those two are all it found.
* **It introduced no `skills/` + `_shared/` path token**, in any file — not merely in the
  two locks that scan `skills/**/*.md`. This record deliberately spells that forbidden path
  in prose only, never as a token, so the claim is literally true and not merely
  gate-satisfying. (The literal does already exist in the tree, in
  `documentation/architecture.md` and in `test_skill_tree.py`'s own lock; both predate this
  step and neither is a citation.)

---

## 9. Widening the sweep to `documentation/` — the two pre-existing instances

Bringing `documentation/` into `_LEAK_SWEEP_ROOTS` (§7) turns the gate on a directory that
has never been graded. It found exactly two instances, both in
`documentation/host-parity-repair-plan.md`, both **already committed and pushed to the
public origin**, and both belonging to this step's own specification:

| # | Location | Class | What it was |
|---|---|---|---|
| 1 | `host-parity-repair-plan.md`, the Step 66 *"The scrub is NOT one line"* bullet | X + M | the per-file scrub spec, which named each item to be removed **by quoting its literal value** — the two private-repo issue pointers, the private scheduled-job name, and the share-of-spend figure |
| 2 | `host-parity-repair-plan.md`, the Step 66 `Done when:` bullet | I | the harness projects-directory transcript path, spelled literally (with placeholders for the identifying segments, so it disclosed a shape and not a value) |

There were three possible responses, and only two of them were legitimate. **Narrowing the
gate — the patterns, the roots, or the window — so that these simply are not seen was
rejected outright**: it converts a real finding into a false green, and it is precisely the
failure mode this phase exists to prevent (a gate that grades a smaller tree while reading
as if it graded the whole one; see the `KNOWN_DANGLING` re-rooting attack Step 63 froze).

**Decision: scrub both, do not allowlist either.** Reasons, in order of weight:

1. **Instance 1 is a live disclosure, not a historical one.** It sits on the default branch
   of a public repository, and it republishes the exact strings the step spends its whole
   scrub budget removing from `_shared/`. Leaving it allowlisted would mean the vendored
   copies are clean and the specification that describes cleaning them is not — a distinction
   with no value to anyone reading either.
2. **Scrubbing costs the plan nothing.** The vendoring work is done; the literal values in
   the spec are no longer instructions anyone will act on, only a liability. Each item is
   now named by class and source line, which is what a reviewer verifying the scrub actually
   needs — the same abstraction pattern §3 applies to the session-UUID item.
3. **An allowlist entry is a permanent hole with a maintenance cost.** The exemption list
   for the UUID pattern is capped at one entry and asserted (§7) for exactly this reason.
   Adding a file-scoped exemption for a document that is *in this repository and editable*
   would spend that budget on the cheapest possible fix.

**Was the plan's prose locked by a committed test?** Checked before editing, and **no**.
Two gates read `documentation/`, and neither locks this text: `test_release_gates.py`'s
`_doc_paths()` feeds `find_broken_local_links()`, which grades markdown link *targets* (no
link was added or removed here), and `test_cutover_handoff.py`'s token/flag sweep explicitly
skips any document whose name ends in `-plan.md`, on the stated grounds that a plan
legitimately names artifacts it has not built yet. `test_cutover_handoff.py` locks the text
of `coding-root-cutover-handoff.md`, `migration.md` and
`provider-neutral-skill-mesh-plan.md` — none of which this step touches. No test update was
required, and none was made.

Instance 2's rewrite is deliberately *not* a narrowing of the identifier pattern that caught
it. That pattern is correct: a harness projects-directory path is a strong disclosure signal
wherever it appears, and the fact that this occurrence carried placeholders rather than a
real slug is a property of this occurrence, not of the shape. The prose now describes the
path instead of spelling it, which keeps the `Done when:` verifiable — the vendored copy is
still checked against source line 32 — without carrying the token.

**One consequence worth stating plainly:** the plan document and this record are now
*inside* the sweep, so any future edit to either that restates a private value goes RED in
`test_no_private_leak_in_migrated_tree`. That is the intended end state. The gate now covers
the writer of the record, not only the payload the record describes.
