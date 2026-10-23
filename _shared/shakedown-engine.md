# Shakedown engine â€” the shared UAT ledger contract

> Vendored shared contract for the Skill Mesh v2 intake and acceptance callers.
> Workspace-only rule links are plain references; task-state dependency uses the packaged
> shared path. Canonical-plan discovery and ledger identity follow current workspace rules.
> Fixture results below are historical until explicitly rerun for the candidate.

Single source of truth for the **shakedown ledger**: the append-only status table that
`/user-walkthrough` (attended, operator-driven) and `/user-shakedown` (autonomous closure)
both read and write, and that a `/goal` condition mechanically checks each turn. Both skills
**cite this file**; neither redefines the grammar below. Three consumers must agree on the
ledger â€” two skills plus the `/goal` zero-open check â€” so the grammar, slug rule, and check
command live here **once** (per `code-quality.md Â§ "One source of truth for data-shape
constants"`). When any grammar below changes, grep both skills +
this file before landing.

Cited by: `.claude/skills/user-walkthrough/SKILL.md`, `.claude/skills/user-shakedown/SKILL.md`.

---

## 1. Ledger file contract

### Path formula

```
<git-root>/.claude/task-state/shakedown-<feature-slug>.md
```

`<git-root>` is ALWAYS resolved via `git rev-parse --show-toplevel` â€” **never** cwd-relative.
A ledger written from inside a `/build-step` worktree with a relative path is silently lost on
worktree cleanup (the task-state-schema gotcha, `<repo>/_shared/task-state-schema.md`).
The small-fix path below therefore never enters a worktree.

### Deterministic feature-slug rule

`<feature-slug>` = **kebab-case of the invocation argument**: lowercase, spaces and
underscores â†’ single hyphens, strip any character that is not `[a-z0-9-]`, collapse repeated
hyphens, trim leading/trailing hyphens. The result must be nonempty before any ledger
path is resolved or read. If normalization removes the entire argument, ask for an explicit
nonempty ASCII topic/feature slug and confirm its intended scope; write nothing meanwhile.
Never resolve `shakedown-.md` or `intake-.md`, invent a replacement, or reuse another topic's
ledger to compensate. Apply the same validation to a replacement argument. Examples:

| Invocation argument | `<feature-slug>` | Ledger file |
|---|---|---|
| `user-walkthrough` | `user-walkthrough` | `shakedown-user-walkthrough.md` |
| `Export Button` | `export-button` | `shakedown-export-button.md` |
| `pta_finance M1` | `pta-finance-m1` | `shakedown-pta-finance-m1.md` |

This rule is **stated once here** so BOTH skills resolve the **same** file for the same
feature â€” that file identity is exactly what lets a `/user-walkthrough` hand a half-filled
ledger to `/user-shakedown` mid-stream. If the two skills computed different slugs, the handoff
would silently start a fresh ledger.

**Invoke both skills with the same argument.** The slug keys off the raw argument, so a near-miss
(`"Export Button"` vs `"the export button"` â†’ `export-button` vs `the-export-button`) would
silently start a second ledger. Safety net for the derive path: before deriving a fresh
ledger, glob `<git-root>/.claude/task-state/shakedown-*.md`. Load an exact slug match first.
A similar filename or a lone ledger is not proof of feature identity. Inspect scope before
reusing a near match; a different feature gets a new ledger. If identity is ambiguous or
multiple ledgers plausibly match, clarify before writing rather than choosing arbitrarily.

---

## 2. Row schema (machine-checkable)

The ledger contains one declared markdown table, with one data row per UAT item. Prose headings
and context may appear before or after it; they are outside the table's structural check.

```
| id | source | status | evidence |
```

- **`id`** â€” `M<N>` for a row seeded from the plan's `## Manual UAT` / `Type: operator`
  M-steps (reuse the plan's own M-numbering); `D<N>` (sequential from `D1`) for a derived row.
- **`source`** â€” `M<N>` (a plan M-step reference) or `derived` (no plan M-step; expectation
  synthesised from the feature).
- **`status`** â€” the status column is exactly one of four words: `open`, `satisfied`, `fixed`, `logged`.
  Their meanings: `open` = not yet exercised; `satisfied` = behaviour verified with evidence;
  `fixed` = a defect was found and repaired in-tree with evidence; `logged` = too big to fix
  inline, recorded with a one-line diagnosis for a follow-up issue.
- **`evidence`** â€” concrete proof (command output, observed result, `file:line`, or the
  one-line diagnosis for a `logged` row). Never a bare status flip with no evidence.

### Pinned cell grammar

The status word stands **alone in its cell**, pipe-and-space delimited: the literal three-token
sequence `| open |` (pipe, space, word, space, pipe). This exact grammar is what makes the
zero-open check a deterministic grep that cannot be fooled by the word "open" appearing inside
evidence prose (evidence is the **last** cell, after the fourth pipe).

A **well-formed data row** matches, in full:

```
^\| *(M[0-9]+ *\| *M[0-9]+|D[0-9]+ *\| *derived) *\| *(open|satisfied|fixed|logged) *\|.*[^|[:space:]].*$
```

(row starts with an `M<n>` id and `M<n>` source, or a `D<n>` id and `derived` source; its status
cell holds exactly one of the four words, followed by the **evidence cell**.) The evidence cell is the **terminal**
cell and may itself contain pipes â€” command output routinely does (`pytest | tail -1`,
`grep -E 'a|b'`) â€” so it is matched with `.*[^|[:space:]].*$`, never restricted to `[^|]*`. Pinning it as pipe-free would
miscount a genuinely-`satisfied` row whose evidence is a piped command as malformed â†’ `open`,
which would make the zero-open `/goal` **unreachable** even on a clean ledger.

---

## 3. Zero-open check + well-formedness fail-safe

A terminal outcome must contain at least one character other than whitespace or the table delimiter. A bare closing pipe does not count as evidence.

The `/goal` condition is agent-completable only because "zero open" is a deterministic check.
The check counts **open-status rows PLUS malformed data rows** â€” a malformed row is treated as
`open` (fail-safe), so a broken row can never make the goal read as satisfied.

```bash
LEDGER="$(git rev-parse --show-toplevel)/.claude/task-state/shakedown-<feature-slug>.md"
[ -f "$LEDGER" ] && [ -r "$LEDGER" ] || { echo "ABORT: ledger missing or unreadable: $LEDGER" >&2; exit 1; }
STATUS='open|satisfied|fixed|logged'   # the four status words â€” canonical list, defined once, reused below

HEADER=$(grep -cE '^\| *id *\| *source *\| *status *\| *evidence *\|[[:space:]]*$' "$LEDGER") || [ "$?" -eq 1 ] || { echo "ABORT: ledger read failed" >&2; exit 1; }
[ "$HEADER" -eq 1 ] || { echo "ABORT: expected one ledger header" >&2; exit 1; }
SEP=$(grep -cE '^\|[-:| ]*-[-:| ]*[[:space:]]*$' "$LEDGER") || [ "$?" -eq 1 ] || { echo "ABORT: ledger read failed" >&2; exit 1; }
[ "$HEADER" -eq 1 ] && [ "$SEP" -eq 1 ] || { echo "ABORT: expected one complete header and separator" >&2; exit 1; }
HEADER_MATCH=$(grep -nE '^\| *id *\| *source *\| *status *\| *evidence *\|[[:space:]]*$' "$LEDGER") || { echo "ABORT: ledger read failed" >&2; exit 1; }
HEADER_LINE=${HEADER_MATCH%%:*}
SEPARATOR_LINE=$(sed -n "$(( HEADER_LINE + 1 ))p" "$LEDGER") || { echo "ABORT: ledger read failed" >&2; exit 1; }
printf '%s\n' "$SEPARATOR_LINE" | grep -qE '^\|[[:space:]]*:?-+:?[[:space:]]*\|[[:space:]]*:?-+:?[[:space:]]*\|[[:space:]]*:?-+:?[[:space:]]*\|[[:space:]]*:?-+:?[[:space:]]*\|[[:space:]]*$' || { echo "ABORT: four-column separator must follow header" >&2; exit 1; }
# The declared data region starts after the separator and ends at the first blank line or heading.
# Count every nonblank line in that region so a row that loses or indents its leading pipe cannot disappear.
DATA_TAIL=$(sed -n "$(( HEADER_LINE + 2 )),\$p" "$LEDGER") || { echo "ABORT: ledger read failed" >&2; exit 1; }
DATA_REGION=$(printf '%s\n' "$DATA_TAIL" | sed -n '/^[[:space:]]*$/q; /^[[:space:]]*#/q; p')
DATA=$(printf '%s\n' "$DATA_REGION" | grep -cE '[^[:space:]]') || [ "$?" -eq 1 ] || { echo "ABORT: ledger read failed" >&2; exit 1; }
# well-formed rows = data rows whose status cell holds exactly one status word.
# Evidence is the TERMINAL cell (matched with a required nonblank, non-pipe character) so it may contain pipes â€” command output does.
WELL=$(printf '%s\n' "$DATA_REGION" | grep -cE "^\| *(M[0-9]+ *\| *M[0-9]+|D[0-9]+ *\| *derived) *\| *($STATUS) *\|.*[^|[:space:]].*$") || [ "$?" -eq 1 ] || { echo "ABORT: ledger read failed" >&2; exit 1; }
# open-status rows (status cell is exactly `open`)
OPEN=$(printf '%s\n' "$DATA_REGION" | grep -cE '^\| *(M[0-9]+ *\| *M[0-9]+|D[0-9]+ *\| *derived) *\| *open *\|.*[^|[:space:]].*$') || [ "$?" -eq 1 ] || { echo "ABORT: ledger read failed" >&2; exit 1; }
# Four-cell records elsewhere are orphans, independent of every cell value. The shared bounded
# grammar accepts either a leading pipe (including an empty first cell) or a nonblank first cell
# with its leading pipe missing, and requires three more cell separators. The strict separator
# guard guarantees that ALL contains exactly the guarded header and separator before data rows.
ROWLIKE='^([[:space:]]*\|[^|]*\|[^|]*\|[^|]*\|.*|[[:space:]]*[^|[:space:]][^|]*\|[^|]*\|[^|]*\|.*)$'
STRUCTURAL_ALL=$(grep -cE "$ROWLIKE" "$LEDGER") || [ "$?" -eq 1 ] || { echo "ABORT: ledger read failed" >&2; exit 1; }
STRUCTURAL_DATA=$(printf '%s\n' "$DATA_REGION" | grep -cE "$ROWLIKE") || [ "$?" -eq 1 ] || { echo "ABORT: ledger read failed" >&2; exit 1; }

MALFORMED=$(( DATA - WELL ))
ORPHAN=$(( STRUCTURAL_ALL - STRUCTURAL_DATA - 2 ))
UNSATISFIED=$(( OPEN + MALFORMED + ORPHAN ))
echo "$UNSATISFIED"     # 0 => ledger clean (goal satisfied); >0 => still work to do
```

Only `UNSATISFIED == 0` printed with exit 0 is the mechanical termination condition.
Missing/unreadable files, missing or duplicate headers, and read errors abort with exit 1;
an abort is never a clean ledger. A genuine header-only ledger has zero rows and prints 0.
Data rows are counted structurally within the declared table region, so surrounding prose is
ignored while a missing or indented leading pipe, corrupted ID, invalid source, invalid status, or empty
evidence still counts as malformed rather than disappearing. Any malformed row makes it non-zero
even if no cell literally says `open`, so a typo can never silently close the goal. Any four-cell
record outside that region counts as an orphan regardless of its ID or other cell values and also
keeps the result non-zero; headings and ordinary context remain outside the bounded row grammar.

### Canonical /goal string

Defined here once; `/user-walkthrough` emits it at wrap, `/user-shakedown` terminates on it:

```
/goal "shakedown ledger for <feature-slug> has zero open items"
```

The condition is checkable every turn by running the block above and asserting `UNSATISFIED == 0`.

---

## 4. Checklist derivation (idempotent â€” load before derive)

**If the ledger file already exists, LOAD it as-is. Never re-seed.** A `/user-shakedown` must be
able to pick up a `/user-walkthrough`'s ledger, and re-derivation would duplicate rows. Derive
**only when the file is absent**:

1. **Locate the feature's canonical entry plan:** prefer `docs/plans/master_plan.md`.
   For an unmigrated project, check root `plan.md` then `master_plan.md`, followed by those
   names and `*-plan.md` / `*_plan.md` under `plans/`, `docs/` and `documentation/`.
   Skip archive, brainstorm, template and draft paths. If candidates disagree about the
   intended feature, resolve that scope before seeding; never silently switch features.
2. **Seed from the plan when M-steps exist.** For each `### M<N>:` item under the plan's
   `## Manual UAT` section (or each `Type: operator` step), create a row with `id = M<N>`,
   `source = M<N>`, `status = open`.
3. **Derive a lightweight expectation set when no plan M-steps exist** (e.g. post-`/user-debug`,
   or a feature with no `## Manual UAT` block): synthesise a small set of behaviours to exercise
   from the feature/plan, each a row with `id = D<N>` (from `D1`), `source = derived`,
   `status = open`.

---

## 5. Small-fix path (in-tree, uncommitted)

When a turn surfaces a small, unambiguous defect:

1. Edit the working tree **in place, uncommitted**. Do **NOT** spin a `/build-step` worktree â€”
   an on-the-spot fix during attended UAT must be visible to the running tool immediately, and
   worktree setup cost dwarfs the fix.
2. Run the **narrowest** test that covers the change.
3. Mark the row `fixed` with the evidence (the test result / observed behaviour).
4. **Batch-commit at wrap** for one reviewable diff, using scoped `git add <paths>` of only the
   files this activity touched â€” never `git add -A` (per CLAUDE.md commit discipline; a live-tree
   fix must not sweep a parallel session's work).

Big fixes are excluded from this path entirely â€” that is what `logged` is for.

## 6. Big-issue path (log, do not rabbit-hole)

When an item is too large to fix inline: append the row as `logged` with a **one-line
diagnosis** in evidence; do NOT rabbit-hole. At wrap, each `logged` row becomes a GitHub sibling
issue (via `gh` with `--body-file`) that feeds `/plan-feature` or `/build-step` â€” this is the
no-guess escape hatch that keeps zero-open reachable without fabricating a verdict.

## 7. Coverage marking (evidence mandatory)

When any turn exercises a behaviour matching a ledger row, mark it `satisfied` with **concrete
evidence** (command output, observed result, `file:line`) â€” never a bare status flip. A status
change with no evidence cell content is a contract violation.

---

## 8. Calibration fixtures (run, not read)

Two frozen ledgers anchor the zero-open check per `measurement-validity.md Â§ "Calibrate with
anchors before comparing candidates"`: a known-good (all
closed) that must score `0`, and a known-garbage (one open) that must score `1`. Extract either
fixture to a file and run the Â§3 check against it.

### Fixture A â€” all-closed (must yield `0`)

```
| id | source | status | evidence |
|----|--------|--------|----------|
| M1 | M1 | satisfied | `pytest -k csv | tail -1` â†’ 3 passed |
| M2 | M2 | fixed | date-filter off-by-one repaired; narrowest test green |
| D1 | derived | logged | export button 500s on empty set â€” filed #999 |
```

Fixture A's `M1` evidence deliberately contains a pipe (`| tail -1`) â€” a genuinely-`satisfied`
row whose evidence is a piped command. It must still score `0`; a check that pins the evidence
cell as pipe-free would wrongly count it malformed â†’ `open` and yield `1` (regression guard for
the terminal-cell `.*$` grammar in Â§2).

### Fixture B â€” one-open (must yield `1`)

```
| id | source | status | evidence |
|----|--------|--------|----------|
| M1 | M1 | satisfied | `pytest tests/test_export.py -k csv` â†’ 3 passed |
| M2 | M2 | open | not yet exercised |
| D1 | derived | fixed | empty-set guard added; test green |
```

Running the Â§3 check against Fixture A yields `0` (all rows `satisfied`/`fixed`/`logged`, none
`open`, none malformed); against Fixture B yields `1` (the single `M2 | ... | open` row). These
are historical workspace observations, not a fresh run against this release candidate.
