# Codex instruction delivery

Phase IS, Step 107 of [`instruction-file-symmetry-plan.md`](instruction-file-symmetry-plan.md)
(issue #151). Measurement taken 2026-08-20; the Codex row re-run 2026-08-26 against the same
pinned version.

**What this document is.** The measurement the instruction-file symmetry work rests on, vendored
**inside this repository** so that nothing load-bearing depends on a document outside it. The
wider portfolio proposal that produced the feature lives outside this checkout and is cited as
provenance only ([`instruction-file-symmetry-plan.md`](instruction-file-symmetry-plan.md) §13);
everything a reader needs in order to act on the result — or to re-run it — is below, and none of
it requires an out-of-tree link.

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
context; **EXPANDS** means it does.

| Host | Prose pointer ("Load and follow X in full") | `@`-import (`@AGENTS.md`) |
|---|---|---|
| Claude Code | **INERT** — the target's content does not reach context | **EXPANDS** — the target's content reaches context |
| OpenAI Codex CLI | **INERT** | **INERT** — Codex expands no imports at all |

**The consequence, stated plainly: the file Codex reads must *be* the content.** A prose pointer
is inert on both hosts, so it is never the content-bearing half anywhere; and on Codex the import
cell is inert as well, so no redirection of any kind survives — whichever file Codex reads has to
carry the text itself. Exactly one arrangement then serves both hosts from a single copy:
**content in `AGENTS.md`, with a `CLAUDE.md` whose whole body is `@AGENTS.md`.** Claude Code
expands that import and receives the content; Codex reads `AGENTS.md` directly and receives the
same bytes. Any other pairing either duplicates the content into two files that will drift, or
leaves one of the two hosts with nothing.

Read the table as three inert cells and one live one, and no further. It says nothing about how
either host *locates* an instruction file, and it is evidence about these two hosts only.

**Before inverting a project, note who else then reads the content.** `CLAUDE.md` is a
Claude-specific filename; `AGENTS.md` is a cross-vendor convention that other agent tooling also
reads. Moving content from the first to the second therefore widens its audience on any machine
where such tooling is installed. A `CLAUDE.md` holding host-specific or private notes deserves a
read-through before it becomes an `AGENTS.md`. Whether a given project may be inverted at all is
the contract's question, not this page's — see the owner cited below.

## Version pin

Measured **2026-08-20** against **`codex-cli 0.147.0`** — the version string `codex --version`
reported on the measuring machine. The Codex row was re-run on 2026-08-26 against that same
version, in a scratch project outside this repository: an `AGENTS.md` whose whole body was an
`@`-import delivered the import line verbatim and none of the imported file's content, and a
project carrying only a `CLAUDE.md` delivered none of it.

The pin is part of the measurement, not decoration. A different Codex build may expand imports,
or resolve a different fallback filename, and the table above would then be describing a version
nobody is running. This repository already holds that stance for the Codex format research it
depends on — parity targets the *installed* Codex CLI rather than the pinned one, recorded as
D-CP7 in [`codex-parity-delivery-plan.md`](codex-parity-delivery-plan.md) §6 — and it applies
here unchanged: before treating any Codex cell as current, re-run the reproduction below against the
version actually installed.

## Reproduction

**Read-only with respect to your project.** It starts no model session, writes nothing in the
project directory, and changes no file you author — including the Codex config. It is not
side-effect-free, and should not be described that way: it refreshes Codex's own caches under the
Codex home (model catalog, app-server info) and reaches the backend to do so. Measured over one
run in a scratch project: zero project files touched, three files under the Codex home re-stamped.

```powershell
cd <project-dir>
codex debug prompt-input
```

The JSON it prints is the instruction payload Codex would send. Search that output for a heading
you expect the project's instruction file to carry — `## Stack`, for example. **Absence means the
content never reached the model.**

```powershell
codex debug prompt-input | Select-String -SimpleMatch '## Stack' -Quiet
```

`grep` is not on `PATH` by default in Windows PowerShell, this repository's floor shell, so the
search step is spelled `Select-String` above; the POSIX spelling is
`codex debug prompt-input | grep '## Stack'`. Either way it is a presence test on the bytes
actually delivered, which is what makes it decisive where reading a model's answer is not: a model
can answer plausibly with no instruction file delivered at all, so the answer is not evidence and
the prompt payload is.

Treat that payload as a grep target, not as an artifact to paste into an issue or a checkpoint. It
is much larger than the project's own file — it also carries Codex's base instructions and any
global instruction content under the Codex home — so publishing it verbatim publishes more than
the project.

A one-invocation config override, which does **not** persist:

```powershell
codex debug prompt-input -c "project_doc_fallback_filenames=['CLAUDE.md']"
```

**Quoting matters here, and only one spelling is portable.** The TOML value uses *single* quotes
inside *double* quotes, and that form runs unchanged in Windows PowerShell and in bash. The
reverse — a double-quoted TOML string wrapped in single quotes — fails in PowerShell: the shell
strips the inner quotes, Codex receives a bare string where it expects a sequence, and the command
exits 1 with `invalid type: string "[CLAUDE.md]", expected a sequence`. Both forms were run on the
pinned version at Windows PowerShell 5.1; only the form printed above exited 0.

The override applies to the invocation it is passed to and to nothing else: measured, the Codex
config file is byte-identical (SHA-256) before and after, so there is nothing on disk for a later
`codex` run to inherit. Use it to answer "would Codex have found the content under the other
filename?" without editing a config, which is what keeps the diagnostic disposable.

## The contract this feeds, and its one owner

The measurement decides one thing: which file has to hold the content. It decides nothing about
when a skill may write either file, what an existing file on disk means, or which of the two a
lifecycle skill refreshes — that is a normative contract, it has exactly one owner in this
repository, and this document deliberately restates no part of it. For the states, the per-writer
behavior, and the guarded-write rule, see the Instruction-file contract in plan-init/core.md
([`../skills/plan-init/core.md`](../skills/plan-init/core.md)).

Two things follow for anyone reading this page as a licence to change files. First, the shape
above is what a writer *emits* when it is entitled to emit anything at all; entitlement is the
owner's question, not this page's.

Second, this repository is deliberately not put into the inverted shape itself, and the cost is
concrete rather than theoretical. Its `AGENTS.md` is a prose pointer — the Codex row's
prose-pointer cell, INERT — so a Codex session opened in this repository receives the pointer and
none of `CLAUDE.md`'s content. Re-measured at this repository's root on 2026-08-26: the pointer
sentence is delivered; `CLAUDE.md`'s section headings are not. That trade-off is accepted
deliberately and assigned to a later phase (decision D5 of the plan cited above). Not being
inverted is not the same as being outside the contract, and which of the two this pair is — with
everything that follows for a writer meeting it — is the owner's to state, not this page's.

## Accepted legacy drift

The legacy top-level `<skill>/SKILL.md` packages committed at the repository root are **not**
updated by this work and stay stale against the cores. That is policy-frozen accepted drift (the
plan's D7), not a
half-finished change: the legacy tree is non-canonical, is not a build input, and is never
installed, so no consumer tree can receive its wording
([`architecture.md`](architecture.md) §2, §3; [`migration.md`](migration.md) for the
deprecation window itself). The deprecation-window record — the disposition this repository
already applied, in the same words, when the autofix marker was given a single owner — is
[`parity-deltas.md`](parity-deltas.md), under "Step 9 resolution of the F1 `fix` row (2026-08-19)"
in its bullet "Legacy top-level packages deliberately unchanged". A later diff of the two trees
should read the divergence as policy rather than as an incomplete fix.

## See also

- [`host-discovery.md`](host-discovery.md) — the host-loading authority map: workspace instruction
  injection vs. native skill discovery vs. router dispatch, and where the inverted shape sits
  among them.
- [`architecture.md`](architecture.md) — the package contract, including what the inverted shape
  changes for a core or an adapter that reads or writes a project instruction file.
- [`instruction-file-symmetry-plan.md`](instruction-file-symmetry-plan.md) — the phase that
  produced this measurement, its decisions, and its provenance.
- [`parity-deltas.md`](parity-deltas.md) — the deprecation-window record for the legacy tree.
