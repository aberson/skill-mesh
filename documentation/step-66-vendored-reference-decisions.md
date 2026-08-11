# Step 66 — vendored workspace references: decisions and sign-offs

Phase 7.5, Step 66 (issue #97). This is the **named in-repo record** the step's Done-when
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
cross-repo phase pointer (`lands as Step 12 of the same phase`) dropped. **Zero doctrinal
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
* **X** — cross-repo issue / step / phase references (`aberson/coding-root` is **private**)
* **M** — account metrics (billing- or usage-share numbers)
* **H** — harness-configuration disclosure (hook libraries, settings files, skill-tree paths)
* **T** — references to tooling skill-mesh does not ship

The scrubs are applied by exact-string replacement with an asserted occurrence count, so a
future source edit that moves a scrub target fails loudly rather than silently shipping the
unscrubbed bytes.

### `step-authoring.md` — **SAFE, no content scrub**
I: none. X: none. M: none. H: none. T: none. Only the two `code-quality.md` links were
de-linked (§4). Verified clean under all six leak patterns, including the new hex-UUID one.

### `task-state-schema.md` — **SCRUBBED (5 edits)**
* **I** — the raw harness session UUID and the private session-transcript path were the two
  highest-value tokens in the whole payload. The source paragraph named a real session UUID
  and then the `~/.claude/projects/<slug>/<uuid>.jsonl` transcript that proved it. Both are
  gone; the paragraph now states the same contract (scratchpad UUID == transcript basename
  == hook `session_id`, no mapping table) with no identifier in it. **This is the
  Done-when's named line, and it is absent from the vendored copy.**
* **X** — `hook wiring lands with Step 5 / issue #295` removed. That issue is in a private
  repository; the sentence now says the wiring is spec until it lands.
* **H** — `.claude/hooks/lib/task-state-derive.ps1` → "the workspace's task-state derive hook
  library"; `.claude/skills/session-wrap/SKILL.md` → "the `session-wrap` skill contract";
  `.claude/settings.json` → "the harness settings file".
* **H, retained deliberately** — `.claude/task-state/…` paths. These are the *subject* of the
  document (they define where the state file lives), removing them would gut the contract,
  and the same paths already appear in five committed skill cores (`user-afterparty`,
  `lesson-harvest`, `plan-expedite`, `session-wrap`, `build-phase`). Not new disclosure.
* **M** — none. **T** — none.

### `skill-pipeline.md` — **SCRUBBED (8 edits)**
* **X** — `(Step 12; lands this phase)` removed; the `## Review routing (post-#227)` heading
  reduced to `## Review routing`. Both pointed into the private coding-root repository.
* **I** — the private cron name `dev-sprint-wrap-monthly` replaced with "the workspace's
  monthly hygiene cron". A named scheduled job on the operator's machine is infrastructure
  disclosure with no reader value.
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

### `intake-engine.md` — **SCRUBBED (4 edits)**
* **X/H** — `.claude/skills/user-gateway/SKILL.md (lands as Step 12 of the same phase)` →
  "the `user-gateway` skill contract".
* Three sibling links re-anchored to `./` form (§4).
* **H, retained deliberately** — `<git-root>/.claude/task-state/intake-*.md`, the ledger path
  formula this document exists to own. Same reasoning as `task-state-schema.md`.
* **I: none. M: none. T: none.**

### `skill-role-taxonomy.md` — **SAFE, no content scrub**
I: none. X: none. M: none. H: none. T: none. The only edit is the vendored self-citation
(§2.2) plus the `code-quality.md` de-link. Clean under all six leak patterns.

### `worktree-hygiene.md` — **SAFE, one structural edit**
I: none. X: none. M: none. H: none. T: none. Its project mentions (`toybox`, `Alpha4Gate`) are
already present in this public tree in many committed files, so they are not new disclosure.
The one structural edit is not a scrub: its workspace YAML frontmatter (`description:`) was
dropped, because a `_shared/` payload file must not open with frontmatter —
`Add-Provenance` would take its frontmatter-first path and
`tests/distributions/test_distributions.py`'s header stripper asserts that premise
explicitly. Nothing downstream of the vendoring reads that block.

### `subagent-economy.md` — **SCRUBBED (2 edits)**
* **M** — `83% of billed tokens are spent above 150k context`, plus the `~43%` / `~18%` /
  `~240k chars` breakdown, is **account cost telemetry**: a share of one operator's bill.
  Replaced with the qualitative claim the rule actually rests on ("the large majority of a
  long window's token cost is incurred at high context", the two leaks named without
  percentages). The rule's prescriptions are unchanged; only the account-level numbers are.
* **X/M** — the `## Source` section named two private investigation documents *and* restated
  the metric. Replaced with a dated, unnamed reference to the two workspace investigations.
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
* **Three tests assert the chain directly.**
  `test_vendored_reference_citations_reach_the_payload` walks all 12 (skill, document) pairs
  in both profiles; `test_shared_references_are_repointed_and_resolve` asserts tree-wide that
  no `<repo>/_shared/` survives outside a provenance header; and
  `test_repo_rooted_shared_citation_is_seeded_and_repointed` is a red-on-garbage anchor on a
  synthetic tree, proving both the seeding edge and the rewrite.

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

`_LEAK_PATTERNS` had five patterns and swept `skills/**/*.md` only. Two gaps, both closed:

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

One exemption, by literal and never by shape: RFC 4122 Appendix A's documentation UUID
`550e8400-…-446655440000`, already used as an illustrative `run_id` in a JSON sample in
`skills/build-step/core.md`. It identifies no session and no person. The anchor asserts both
directions — a session-shaped id reds, the documentation UUID does not — and asserts the
exemption list is still exactly one entry, because a growing exemption list is how a real id
eventually rides in.

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
* **It introduced no `skills/` + `_shared/` path token**, in any file — not merely in the
  two locks that scan `skills/**/*.md`. This record deliberately spells that forbidden path
  in prose only, never as a token, so the claim is literally true and not merely
  gate-satisfying. (The literal does already exist in the tree, in
  `documentation/architecture.md` and in `test_skill_tree.py`'s own lock; both predate this
  step and neither is a citation.)
