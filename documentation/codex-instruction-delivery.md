# Codex instruction delivery

Phase IS, Step 107 of [`instruction-file-symmetry-plan.md`](instruction-file-symmetry-plan.md)
(issue #151).

**What this document is.** The per-host instruction-delivery measurement the instruction-file
symmetry work rests on, vendored **inside this repository** so nothing load-bearing depends on a
document outside it. The wider portfolio proposal that produced the feature lives outside this
checkout and is cited as provenance only
([`instruction-file-symmetry-plan.md`](instruction-file-symmetry-plan.md) §13); everything a
reader needs in order to act on the result — or to re-run it — is below, and none of it requires
an out-of-tree link.

**Which axis this is.** A project's instruction file is **workspace instruction injection**, one
of the three host-loading mechanisms [`host-discovery.md`](host-discovery.md) keeps separate. It
is **not** skill discovery: `CLAUDE.md` or `AGENTS.md` is an instruction adapter, never a skill
registry, and nothing measured here changes which discovery root a host scans or what it finds
there. A reader who takes this page as evidence about an installed profile has crossed the two
axes the authority map exists to keep apart.

## The measurement

Two ways one file can hand a host the contents of another, measured against two hosts. A **prose
pointer** is a sentence of the form *Load and follow X in full*. An **`@`-import** is a line of
the form `@AGENTS.md`. **INERT** means the target file's content never reaches the model's
context — the pointer sentence or the import line is delivered verbatim in its place.
**EXPANDS** means the target's content does reach context.

| Host | Prose pointer ("Load and follow X in full") | `@`-import (`@AGENTS.md`) | Provenance |
|---|---|---|---|
| Claude Code | **INERT** | **EXPANDS** | measured 2026-08-20; **not** re-run since |
| OpenAI Codex CLI | **INERT** | **INERT** — Codex expands no imports at all | re-measured 2026-08-26 against `codex-cli 0.147.0` |

**The consequence, stated plainly: the file Codex reads must *be* the content.** A prose pointer
is inert on both hosts, so it is never the content-bearing half anywhere; and on Codex the import
cell is inert as well, so no redirection of any kind survives — whichever file Codex reads has to
carry the text itself. Exactly one arrangement then serves both hosts from a single copy:
**content in `AGENTS.md`, with a `CLAUDE.md` whose whole body is `@AGENTS.md`.** Claude Code
expands that import and receives the content; Codex reads `AGENTS.md` directly and receives the
same bytes. That rests on one premise no cell above measures — that Claude Code does not itself
read `AGENTS.md`, so a `CLAUDE.md` has to exist to carry the import. Any other pairing either
duplicates the content into two files that will drift, or leaves one of the two hosts with
nothing.

Read the table as three inert cells and one live one, and no further. It says nothing about how
either host *locates* an instruction file, and it is evidence about these two hosts only —
**GitHub Copilot CLI was not measured on this axis**, so no cell above may be read as covering
it.

**Which file each host opens.** Of a project's instruction files, Codex reads `AGENTS.md`, and by
default reads only that: measured below, a project carrying a substantive `CLAUDE.md` and no
`AGENTS.md` delivered none of its content at all. The one-invocation override further down is the
only measured exception, and it is a fallback rather than a redirect. Claude Code reads
`CLAUDE.md`. That asymmetry is exactly what the one-line import bridges.

**Before inverting a project, one consideration this page did not measure.** `CLAUDE.md` is a
Claude-specific filename; `AGENTS.md` is a cross-vendor convention that other agent tooling also
reads. Moving content from the first to the second therefore widens its audience on any machine
where such tooling is installed, so a `CLAUDE.md` holding host-specific or private notes deserves
a read-through before it becomes an `AGENTS.md`. Which tools read `AGENTS.md`, and on which
machine, was not measured here. Whether a given project may be inverted at all is the contract's
question, not this page's — see the owner cited below.

## Version pin

Every Codex figure on this page — both Codex cells above, and every figure in the Reproduction
section below — was measured against **`codex-cli 0.147.0`**, the version string `codex
--version` reports, on the date the table's Provenance column names. The Claude Code row is
carried from the first measurement on 2026-08-20 and was not re-run.

The pin is part of the measurement, not decoration. A different Codex build may expand imports,
or resolve a different fallback filename, and the table above would then be describing a version
nobody is running. This repository already holds that stance for the Codex format research it
depends on — parity targets the *installed* Codex CLI rather than the pinned one, recorded as
D-CP7 in [`codex-parity-delivery-plan.md`](codex-parity-delivery-plan.md) §6 — and it applies
here unchanged: before treating any cell as current, re-run the reproduction below against the
version actually installed.

**This page is not the table's only carrier, and that is deliberate.** The owning core states the
same inert/expands result in two sentences, as the rationale for the shape it defines — the "Why
the inverted shape exists" paragraph of
[`../skills/plan-init/core.md`](../skills/plan-init/core.md). A re-measurement that moves a cell
has to move that paragraph in the same change.

## What the re-run showed

Four scratch projects outside this repository, one arrangement each, every file carrying a unique
sentinel string. Each was run as `codex debug prompt-input` from the project directory and the
printed payload searched for its sentinel. All four exited 0.

| Project arrangement | Project content delivered | Project content not delivered |
|---|---|---|
| `AGENTS.md` substantive; `CLAUDE.md` is exactly `@AGENTS.md` *(the inverted shape)* | `AGENTS.md`'s content | — |
| `AGENTS.md` is exactly `@INNER.md`; `INNER.md` substantive | the literal line `@INNER.md` | `INNER.md`'s content |
| `AGENTS.md` a prose pointer to `CLAUDE.md`; `CLAUDE.md` substantive | the pointer sentence | `CLAUDE.md`'s content |
| `CLAUDE.md` substantive; no `AGENTS.md` | — | `CLAUDE.md`'s content |

To rebuild the table: make four empty directories, write the named files in each with a distinct
sentence of your own in every file, run the Reproduction command below from inside each
directory, and search the printed payload for that sentence. No fixture and no test is involved.

Rows 2 and 3 are the table's two Codex INERT cells shown directly: in both, the redirecting line
arrives verbatim and the thing it points at does not arrive at all. Row 1 is the shape this work
emits, confirmed end to end. Row 4 is why the fallback override below exists, and is also why
"the project has a `CLAUDE.md`" is no evidence that Codex received anything.

## Reproduction

**Read-only with respect to your project — but not side-effect-free, and it should not be
described as though it were.** It writes nothing you author, including the Codex config.

Run this from the project directory you want to test:

```powershell
codex debug prompt-input
```

Re-measured 2026-08-26 against codex-cli 0.147.0 on one Windows host: seven invocations across
two independently designed protocols — one hashing every file, one recording size and mtime —
each bracketed by zero-invocation control intervals to subtract background writes. **No file in
the project directory changed, on any run of either protocol**; on one run the project tree was
completely static, which is why the diagnostic is safe to point at any project.

Under the Codex home the command does write, and not stably: attributable changes ranged from
none to three files per invocation and the two protocols disagreed on the same command, so this
doc publishes no file count. `config.toml`, `auth.json` and every session, skill and plugin file
were unchanged in every manifest, so a `-c` override left nothing on disk; the remote plugin
catalog (`cache/remote_plugin_catalog/<hash>.json`, 15,309,067 B) held a frozen hash, size and
mtime throughout. A snapshot cannot see within-run transients: each invocation creates and
removes its own `<CODEX_HOME>/tmp/` directory inside the run.

The operator-actionable part: **the Codex home churns continuously with no invocation at all.**
Every control interval moved files; one produced exactly the two-files-touched, sizes-unchanged
pattern previously attributed to the command. `models_cache.json` and the `cache/codex_apps_*`
catalogs move on their own — an invocation 64 s after a previous one left the catalogs untouched;
invocations minutes apart found them refreshed. So the Codex home is not a thing to fingerprint
while codex is running; reproducing this needs a machine with no other codex process live.

The JSON it prints is the instruction payload Codex would send. Search that output for a heading
you expect the project's instruction file to carry — `## Stack`, for example. **Absence means the
content never reached the model.**

```powershell
codex debug prompt-input | Select-String -SimpleMatch '## Stack'
```

**Run at *this* repository's root, that search returns nothing — deliberately.** A zero-match
result here is a property of this repository's own arrangement, not a broken recipe; read "This
repository is deliberately not in the inverted shape" below before concluding anything from it.

PowerShell's search verb is `Select-String`, which is why the step is spelled that way above; the
POSIX spelling is `codex debug prompt-input | grep '## Stack'`. Either way it is a presence test
on the bytes actually delivered, which is what makes it decisive where reading a model's answer
is not: a model can answer plausibly with no instruction file delivered at all, so the answer is
not evidence and the prompt payload is.

Treat that payload as a search target, not as an artifact to paste into an issue or a checkpoint.
It is far larger than the project's own file — measured, a project that delivered **no**
instruction content whatsoever still produced roughly 26 KB, because the payload also carries
Codex's base instructions and any global instruction content under the Codex home. Publishing it
verbatim publishes considerably more than the project.

### The one-invocation override, and its quoting

```powershell
codex debug prompt-input -c "project_doc_fallback_filenames=['CLAUDE.md']"
```

**Only one spelling is portable, and the difference is not cosmetic.** The TOML value takes
*single* quotes inside *double* quotes. Both forms were run on the pinned version, in both shells:

| Form | Windows PowerShell 5.1 | bash |
|---|---|---|
| `-c "project_doc_fallback_filenames=['CLAUDE.md']"` | exit 0 | exit 0 |
| `-c 'project_doc_fallback_filenames=["CLAUDE.md"]'` | **exit 1** | exit 0 |

PowerShell strips the inner double quotes, so Codex receives a bare `[CLAUDE.md]` where it expects
a sequence and fails with `invalid type: string "[CLAUDE.md]", expected a sequence`. Windows
PowerShell 5.1 is this repository's floor shell, so the double-outside form is the only one worth
writing down. (Run at this repository's root under that shell, the working form exited 0 and
printed roughly 27 KB — a machine-dependent figure, since the payload carries whatever global
instruction content that machine's Codex home holds.)

**It is a *fallback*, not a redirect — and misreading that produces a confident wrong answer.**
The setting takes effect only where no `AGENTS.md` is found. Measured at this repository's root,
which has one: the payload with the override is exactly as long as the payload without it, and
`## Stack` — a heading this repository's `CLAUDE.md` carries — is absent from both. In a project
with **no** `AGENTS.md`, the same override makes that project's `CLAUDE.md` content appear. So
the override answers "would Codex have found the content under the other filename, had it looked
that far?", and on a project that already has an `AGENTS.md` it answers nothing at all. A reader
who runs it here, sees no change, and concludes the flag is broken has read a null result as a
negative one.

**It does not persist, and it is not to be made persistent.** Measured: the Codex config file's
SHA-256 is identical before and after, and a plain run immediately following an overridden one
delivers nothing from the fallback filename. There is nothing left on disk for a later `codex`
run to inherit, which is what keeps the diagnostic disposable — writing the flag into the Codex
config would trade that away for a standing fallback filename, and the durable fix is the
inverted shape instead.

## The contract this feeds, and its one owner

The measurement decides one thing: which file has to hold the content. It decides nothing about
when a skill may write either file, what an existing file on disk means, or which of the two a
lifecycle skill refreshes — that is a normative contract, it has exactly one owner in this
repository, and this document deliberately restates no part of it. For the state definitions, the
per-writer behavior matrix, and the guarded-write rule,
see the Instruction-file contract in plan-init/core.md
([`../skills/plan-init/core.md`](../skills/plan-init/core.md)).

One thing follows for anyone reading this page as a licence to change files: the shape above is
what a writer *emits* when it is entitled to emit anything at all, and entitlement is the owner's
question, not this page's.

## This repository is deliberately not in the inverted shape

The catalog emits a shape it does not itself adopt, and the cost of that is concrete rather than
theoretical. This repository's `AGENTS.md` is a prose pointer — the Codex row's prose-pointer
cell, INERT — so a Codex session opened here receives the pointer and none of `CLAUDE.md`'s
content. Re-measured at this repository's root on 2026-08-26: the pointer sentence is delivered
once, and `## Stack` appears zero times.

That trade-off is accepted deliberately and assigned to a later phase — decision D5 of
[`instruction-file-symmetry-plan.md`](instruction-file-symmetry-plan.md) §6 — which is what makes
adopting the contract backward-compatible rather than a migration. What that decision freezes,
and the test that holds it there, are stated once in [`architecture.md`](architecture.md) §11 and
are not repeated here.

## Accepted legacy drift

The legacy top-level `<skill>/SKILL.md` packages committed at the repository root are **not**
updated by this work and stay stale against the cores. That is policy-frozen accepted drift, not
a half-finished change: the legacy tree is non-canonical compatibility content in a deprecation
window ([`architecture.md`](architecture.md) §2, §3; [`migration.md`](migration.md) for the
window itself), it is not a build input, and it is never installed — so no consumer tree can
receive its wording.

The deprecation-window *policy*, and the precedent for applying it, are recorded in
[`parity-deltas.md`](parity-deltas.md) under "Step 9 resolution of the F1 `fix` row (2026-08-19)",
in its bullet "Legacy top-level packages deliberately unchanged" — that entry disposes of a
different drift (the autofix marker) in the same words and for the same reasons. This phase's
instance is recorded here, and in no delta ledger. A later diff of the two trees should read the
divergence as policy rather than as an incomplete fix.

## See also

- [`host-discovery.md`](host-discovery.md) — the host-loading authority map: workspace instruction
  injection vs. native skill discovery vs. router dispatch, and where the inverted shape sits
  among them.
- [`architecture.md`](architecture.md) §11 — the package contract, including what the inverted
  shape changes for a core or an adapter that reads or writes a project instruction file.
- [`instruction-file-symmetry-plan.md`](instruction-file-symmetry-plan.md) — the phase that
  produced this measurement, its decisions, and its provenance.
- [`parity-deltas.md`](parity-deltas.md) — the deprecation-window record for the legacy tree.
