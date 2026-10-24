---
name: context-slim
description: Audit all auto-loaded Claude Code context files (the CLAUDE.md or AGENTS.md chain, .claude/rules/*.md, MEMORY.md) for a project and produce a prioritized progressive-disclosure improvement report — what to stub, extract, or prune to reduce per-turn token cost. Run bare for a report only; add --apply to implement high-confidence changes (rules stubbing, stale memory pruning) autonomously.
user-invocable: true
argument: "Optional flags: --project <name-or-path> (default: innermost project with a CLAUDE.md); --apply (implement high-confidence changes after the report)"
---

# context-slim

Measures every file that auto-loads on every Claude Code conversation turn for a project, classifies each section as always-needed vs task-specific vs stale, and produces a prioritized improvement plan. With `--apply`, implements the high-confidence mechanical changes without requiring judgment calls.

## When to use

- Sessions are burning 30-50%+ of the context window before substantive work begins.
- After a multi-phase project has accumulated months of CLAUDE.md or AGENTS.md narrative and stale memory blocks.
- Before starting a new build phase to ensure context overhead is lean.
- Periodic maintenance (monthly, or after any major phase ships).

## Phase 1 — Bootstrap: discover and measure

Parse args. Resolve `--project` to an absolute path: if it's a bare name (e.g. `void_furnace`), look for `<dev-root>/<name>/CLAUDE.md`; if it's a relative or absolute path, resolve directly. Default to the innermost ancestor directory of cwd that contains a `CLAUDE.md`.

Walk from the resolved project directory up to the `dev/` root (stop at the first directory whose parent has no `CLAUDE.md`). Collect:
- The content instruction file at each level of the walk — CLAUDE.md or AGENTS.md, whichever carries the content there (project-level, then each parent up to dev/). Collect the content file, not the pointer beside it.
- Every `.claude/rules/*.md` at each level of the walk. A rules file whose frontmatter declares `paths:` loads only when matching files are in play: list it as `(path-scoped)`, keep it out of the per-turn TOTAL and the savings figures, and do not send it to Agent B — it is never a STUB or MOVE OUT candidate, so Phase 4 never changes it.
- The project's memory index: glob `<workspace-memory>/MEMORY.md`, where `<workspace-memory>` is the invoking session's own auto-memory directory, and take the first match; if none, try the encoded form, `<claude-home>/projects/<encoded project path>/memory/MEMORY.md`, where `<claude-home>` is the host's Claude configuration directory and every character of the resolved project path other than a letter or digit becomes `-` (so `_`, `\` and `.` → `-`, `:\` → `--`; compare case-insensitively). When `--project` is passed, use only that encoded form — never the invoking session's own memory index, which belongs to a different project whenever the session runs elsewhere (`/user-afterparty --all-projects` invokes `--project <p>` once per project and expects one distinct audit per project). If no memory index resolves, record `MEMORY.md — none found` and skip Agent C and H2 for this run.

**The walk's anchor is not the file it reads.** Keep the resolution above anchored on `CLAUDE.md` — an inverted project still has one, and `/user-afterparty` pins its own "current project" to this same resolution, so re-anchoring it would silently break that parity. What changes once a directory resolves is only which file is opened there: the content instruction file, CLAUDE.md or AGENTS.md. On a normal project that is `CLAUDE.md` and nothing here behaves differently. On an inverted project the `CLAUDE.md` defers to `AGENTS.md` and its `@AGENTS.md` import expands to the sibling, so the bytes that actually load every turn are `AGENTS.md`'s — collect, measure and classify that file, and never bill the deferring file itself as that level's context cost. If BOTH names carry content at a level — the drift state — the content file is `CLAUDE.md`, because that is the one this host auto-loads; carry the drift as a non-blocking advisory printed beside whatever this run reports or applies at that level — never in a skipped or not-changed list, and never as a reason to stop. For the state definitions that decide which name is the content file, see the Instruction-file contract in plan-init/core.md; this adapter applies it by citation and restates no part of it.

For each collected file, record its **line count** (use the Read tool or PowerShell `(Get-Content <path>).Count`).

Also scan each collected content file — CLAUDE.md or AGENTS.md — for `.claude/rules/<filename>.md` link references (grep for `rules/.*\.md`). Verify each target file exists. Record any missing targets in the discovery table as `rules/<name>.md  (MISSING — referenced but not found)`.

Print the discovery table before any analysis:

```text
context-slim — <resolved project path>

Auto-loaded files:
  File                                   Lines
  ─────────────────────────────────────────────
  CLAUDE.md  (dev/)                        100
  AGENTS.md  (void_furnace/)                72
  rules/code-quality.md (dev)               78
  rules/plan-and-issue-flow.md (dev)       115
  rules/windows-shell.md (dev)              58
  ... (all discovered rules files)
  MEMORY.md                                225
  ─────────────────────────────────────────────
  TOTAL                                   ~N lines  (~X est. tokens)
```

Each row names the file actually collected at that level — CLAUDE.md or AGENTS.md — so an inverted project's row reads `AGENTS.md`, as `void_furnace/` does above. The `MEMORY.md` row also prints the resolved memory index path (or `none found`), so a wrong target is visible before any analysis.

Estimated tokens = lines × 15 (rough average for dense prose/markdown).

## Phase 2 — Parallel analysis

Spawn three parallel subagents using the Agent tool, each with explicit `model: sonnet` (classification arms; they must not inherit an escalated session — tier policy, CLAUDE.md model paragraph). Each receives its target file(s) as a prompt with the full contents inline (use Read to fetch them first). Collect all three results before Phase 3.

If the Agent tool is unavailable (for example, when this skill runs inside a sub-agent), print the Phase 1 discovery table, report `required_tool_missing: Agent`, and stop: never classify in the orchestrating session instead, and never run Phase 4.

**Optional local-classifier offload (switchboard, INERT BY DEFAULT).** This three-way file-classifier fan-out is the one role this skill may route to a local model (tier-offload task_class `context-slim-classifier`; Switchboard Decision 9 — a cheap, low-stakes parallel classification array). It is **off unless switchboard offload is enabled for this slice**. When offload is enabled, route each classifier's per-section judgment through the switchboard judge entrypoint (`python -m switchboard judge --site context-slim-classifier --prompt-file <section-prompt-file>`, prints one JSON object, always exits 0): use a **verdict** as the local classifier's advisory call, and on a **defer** (`{"defer": true, ...}`) fall back to the normal Claude classification subagent. When offload is OFF (the default), the entrypoint returns a defer immediately with NO network call, so this skill spawns the three Claude classifier subagents **exactly as before**. The KEEP/EXTRACT/COMPRESS classification is advisory only — Phase 3 synthesis and any `--apply` change stays on Claude. **A local verdict never makes a change apply-eligible:** when `--apply` is passed, skip the local route and spawn the three Claude classifier subagents, so every STUB, MOVE OUT, DELETE, ARCHIVE or COMPRESS that Phase 4 writes rests on a Claude classification (local judges advise; they never gate a write).

### Agent A — the instruction-file chain (CLAUDE.md or AGENTS.md)

For each content file in the chain — CLAUDE.md or AGENTS.md, whichever Phase 1 collected — classify every section:

- **KEEP** — structural facts, critical safety rules, always-needed orientation (stack, commands, core gotchas, governance invariants).
- **EXTRACT** — status narrative, phase history, large reference tables, content only needed for specific task types. For each EXTRACT, name the destination file (e.g. `.claude/phase-status.md`) and write the 1-3 line pointer that replaces it.
- **COMPRESS** — sections that repeat content already in rules files, or that could be a single sentence instead of a paragraph.

Produce a table: Section → Verdict → Destination (if EXTRACT) → Lines before → Lines after.
State the estimated slim line count for each file.

### Agent B — Rules files

For each rules file, classify:

- **KEEP AS-IS** — always-relevant safety or quality rules; small enough to justify full auto-load (under ~40 lines). Do not stub `code-quality.md` or `security.md` regardless of size.
- **STUB** — relevant on some turns but over-detailed; replace the rules file with a 3-8 line summary stub, move the full content to `.claude/references/<filename>`. Write the exact stub text. The stub keeps the rule's trigger condition and every safety-critical fact — nothing else — and links its references copy (the workspace inline-stub rule: the knowledge-placement reference, § The inline stub, where present).
- **MOVE OUT** — only needed on rare task types; remove from rules/ entirely, add a pointer line in the nearest content instruction file — CLAUDE.md or AGENTS.md, never a pointer file. State the exact pointer line; like a stub, it keeps the trigger condition and any safety-critical fact and names the references copy.

Produce a per-file table: File → Verdict → Lines → Est. tokens → Post-change est. tokens.
Include the full stub text for every STUB recommendation.
State the total token reduction.

### Agent C — Memory index (MEMORY.md)

Classify every section. Today's date is available from the system context (`currentDate`).

- **INDEX LINE** — one-liner pointer to a detail file. Keep as-is.
- **INLINE DETAIL** — multi-paragraph narrative that belongs in its referenced detail file, not the index. Recommend moving.
- **ACTIVE STATUS** — project status less than 3 days old. Keep. Status 3 to 5 days old is also kept: it is neither active nor stale, so it is never apply-eligible.
- **STALE STATUS (ARCHIVE)** — dated more than 5 days ago, superseded by newer blocks, but contains hard facts (commit hashes, test counts, run IDs, cost figures) worth keeping for forensic use. Move to `MEMORY-ARCHIVE.md`.
- **STALE STATUS (DELETE)** — dated more than 5 days ago, pre-build planning sessions or intermediate checkpoints whose outcome is already captured in index entries. Delete outright.
- **COMPRESS** — a block that can be reduced to a single sentence without losing load-bearing facts.

Produce a table: Section (first line) → Date → Verdict → Reason → Lines.
State the projected MEMORY.md line count after all changes.
Flag if current MEMORY.md is at or above the 200-line truncation cap.

## Phase 3 — Report

Before writing the report, do these four passes using the collected agent results:

**Stub → MEMORY cross-reference:** For each file Agent B marks STUB, scan Agent C's INDEX LINE verdicts for MEMORY.md entries whose core rule is now directly expressed in the stub text. When the stub carries the behavioral directive ("run X before Y", "use Z not W"), the MEMORY.md pointer may add little recall value — it's a pointer-to-a-pointer. Mark these as **STUB-REDUNDANT (review)** — separate from Agent C's stale-status finds so the origin is clear. These are **NOT apply-safe** and always go in Needs-review: a MEMORY index line is the recall path to its topic file's long-form (the "why" + incident), which the always-loaded stub does not carry — deleting the index line orphans that long-form. The operator confirms each before deletion.

**Broken reference check:** For any `rules/<name>.md  (MISSING)` entries found in Phase 1, include them in the report under a dedicated "Broken rule references" section. These are never apply-safe (creating a new rules file requires correct content, not a placeholder); always go in Needs-review.

**References-conflict check:** For each STUB or MOVE OUT, check whether its destination references file (same filename, that level's references directory) already exists. If it exists and is not identical to the rules file's current content (compare after normalizing line endings), the change is **NOT apply-safe** and goes in Needs-review: Phase 4 never overwrites that copy, so stubbing or deleting the rule would leave its current text nowhere. An identical existing copy stays apply-safe.

**Reversibility:** A STUB, MOVE OUT or ARCHIVE keeps the moved content in its preserved copy. A DELETE or COMPRESS discards text, so mark it `irreversible (no clean git copy)` unless its target file is tracked by version control and has no uncommitted changes (`git -C <dir> ls-files --error-unmatch <file>` and `git -C <dir> diff --quiet HEAD -- <file>` both exit 0); git cannot restore uncommitted bytes of a tracked file either. A MEMORY.md in the host's per-project memory directory is normally untracked, so its DELETE and COMPRESS edits are normally irreversible.

Synthesize all three agents' outputs into a single report. Print in full; do not truncate.

```markdown
## context-slim report — <project> — <date>

### Current auto-load cost
| File | Lines | Est. tokens |
|---|---|---|
| ... | ... | ... |
| TOTAL | N | ~X |

### Recommended changes (ranked by tokens saved, largest first)
| # | File | Action | Saves | Effort | Apply-safe? |
|---|---|---|---|---|---|
| 1 | rules/plan-and-issue-flow.md | STUB | ~1,900 tok | Low | Yes |
| 2 | rules/worktree-hygiene.md | STUB | ~1,350 tok | Low | Yes |
| 3 | MEMORY.md | Prune 9 stale blocks | ~1,100 tok | Low | Yes |

### Stub-redundant MEMORY.md index lines (cross-reference pass — Needs-review)
Entries whose rule is now directly in a stub. Surfaced for operator confirmation, NOT auto-deleted (the index line is the recall path to its topic file's long-form):
- MEMORY.md: "<entry text>" — rule now in <stub-file>.md stub
...
(Omit section if none found.)

### Broken rule references
| File referenced | In | Status |
|---|---|---|
| rules/python.md | dev/CLAUDE.md | MISSING — create to fix broken link |
(Omit section if none found.)

### High-confidence (--apply will implement these)
<bulleted list — STUBs, stale-status MEMORY deletes, MEMORY.md COMPRESS blocks; each marked `irreversible (no clean git copy)` where the reversibility pass found it so>

### Needs operator review (--apply skips these)
<bulleted list — CLAUDE.md or AGENTS.md splits and COMPRESS sections (Phase 4 has no step that rewrites a content file's sections); missing rules files (need correct content, not placeholder); stub-redundant MEMORY index-line deletions (each orphans a topic file's long-form — confirm first); references conflicts (an existing references copy differs from the rule)>

### Projected savings
Before: N lines / ~X tokens per turn
After:  M lines / ~Y tokens per turn  (~Z% reduction)
```

End the report with this exact standalone line (no surrounding text):

`Run \`/context-slim --apply\``

(Omit this line if --apply was already passed.)

## Phase 4 — Apply (skip entirely if --apply was not passed)

Implement only the high-confidence changes. These are mechanical. Moved content (STUB, MOVE OUT, ARCHIVE) leaves its original place only after its preserved copy is in place and identical to the original's current content: a failed, conflicting or no-longer-identical copy leaves the original untouched and lists the item under `Files NOT changed`. Stale-status DELETE and COMPRESS discard text with no copy; Phase 3 marked each `irreversible (no clean git copy)` where no version control can restore it.

**Identical** in this phase means equal after removing carriage returns, checked from both files as they are on disk at that moment — never from an earlier read held in context (PowerShell: `((Get-Content -Raw -LiteralPath <a>) -replace '\r','') -ceq ((Get-Content -Raw -LiteralPath <b>) -replace '\r','')`).

### H1 — Rules file changes

**For each STUB recommendation:**
1. `Glob` or confirm `.claude/references/` exists at the appropriate level; create it if not (PowerShell: `New-Item -ItemType Directory -Force <path>`).
2. If `.claude/references/<filename>` already exists, keep it when it is identical to the rules file; otherwise skip this STUB, leave the rules file unchanged, and list it under `Files NOT changed` as a references conflict. If it does not exist, create a byte-for-byte copy without overwrite (PowerShell: `[System.IO.File]::Copy(<rules file>, <references file>, $false)`) — never rewrite it from the Phase 2 read. If that create-new copy reports that the destination now exists, treat it as a references conflict and skip the STUB.
3. Immediately before touching the rules file, check that the references copy is identical to the rules file; if the copy failed or they differ (for example, the rule was edited after step 2), skip this STUB the same way.
4. Replace the rules file with the stub text Agent B produced (use the Write tool).
5. Verify: stub is under 10 lines and links its references copy; report any failure in H3.

**For each MOVE OUT recommendation:**
1. Identify the content instruction file at that level — CLAUDE.md or AGENTS.md, whichever Phase 1 collected.
2. If no content file resolves there, skip this MOVE OUT entirely — copy nothing, delete nothing — and list it under `Files NOT changed`.
3. If both names carry content (drift), the target is `CLAUDE.md`; note the drift beside this change in the H3 applied list.
4. Make `.claude/references/<filename>` hold the rules file's current content: copy it there byte for byte if absent (as in STUB step 2); keep an existing copy only when it is identical. If a differing copy exists or the copy fails, skip this MOVE OUT entirely — append nothing, delete nothing — and list it under `Files NOT changed`.
5. Append the `## Topic-specific guidance` section to the target file, never to a pointer, with Agent B's pointer line (or add to an existing one); if that exact pointer line is already there (a re-run finishing a partial MOVE OUT), append nothing.
6. Immediately before deleting, check that the references copy is identical to the rules file. Delete the original from `.claude/rules/` (PowerShell: `Remove-Item -LiteralPath <rules file>`) only if it is and step 5's pointer line is in place; otherwise keep the rules file and list it under `Files NOT changed`, noting any pointer line already appended.

### H2 — Memory pruning

Process Agent C's recommendations in order from bottom of file to top (so line numbers stay valid):

**DELETE blocks** (from Agent C's stale-status findings only): Remove those lines from MEMORY.md directly using the Edit tool. (Phase 3 stub-redundant cross-reference finds are NOT deleted here — they go to Needs-review for operator confirmation, since deleting an index line orphans its topic file's long-form.)

**ARCHIVE blocks:** 
1. Check if `MEMORY-ARCHIVE.md` exists in the same directory; if not, create it with a `# Archived status blocks` header.
2. Append the block content to `MEMORY-ARCHIVE.md` with a `## <original section heading>` separator — unless that exact heading-plus-block substring is already there after carriage-return normalization. Confirm that exact match from the archive file on disk at that moment, not from an earlier read; when it matches, append nothing.
3. Remove the block from MEMORY.md using the Edit tool — only after step 2's append succeeded or found the block already archived; otherwise leave the block in place and list it under `Files NOT changed`.

**COMPRESS blocks:** Replace with the one-liner Agent C produced using the Edit tool.

After all pruning: read the new MEMORY.md line count. If still above 150, report which sections remain large and why they were not pruned (never auto-prune INDEX LINES or ACTIVE STATUS).

### H3 — Verify and report

Print a before/after summary:

```text
Applied changes:

  rules/plan-and-issue-flow.md   → stubbed (115 → 6 lines); full content at .claude/references/plan-and-issue-flow.md
  rules/worktree-hygiene.md      → stubbed (90 → 7 lines); full content at .claude/references/worktree-hygiene.md (existing identical copy — not overwritten)
  MEMORY.md                      → pruned (225 → 108 lines; 9 stale blocks removed, 3 archived) — irreversible (no clean git copy)
  ...

  Total auto-load reduction: N lines / ~X tokens per turn  (was Y, now Z — A% smaller)

Files NOT changed (need operator review):
  AGENTS.md (void_furnace/) — Phase OMR extract proposed; see report above
  ...
```

For each line: format is `rules/<file> → stubbed (N → M lines); full content at .claude/references/<file>`. If an identical references file already existed, add `(existing identical copy — not overwritten)` after the path; a differing existing copy is a conflict, so that rule appears under `Files NOT changed`, never as stubbed. Append `— irreversible (no clean git copy)` to every applied line Phase 3 marked so. A `Files NOT changed` entry names the content instruction file the change would have touched — CLAUDE.md or AGENTS.md, whichever Phase 1 collected at that level.

## Limitations

- Only audits files that auto-load every turn; context loaded manually or via IDE settings is not analyzed. A file that a content file merely tells the reader to load (for example "Load and follow X in full") is not collected, and `@`-imports other than the inverted project's `@AGENTS.md` are not expanded.
- Does not commit changes — operator reviews and commits in-repo files after `--apply`. MEMORY.md and MEMORY-ARCHIVE.md in the host's per-project memory directory are normally outside any repository: unless that directory is itself in a Git worktree, their edits take effect at once and are never committed.

## Constraints

- Never stub or modify `code-quality.md` or `security.md` — these are always-load safety files regardless of size.
- Never auto-apply CLAUDE.md or AGENTS.md splits or COMPRESS edits — those always go in Needs-review.
- Never delete MEMORY.md INDEX LINES or ACTIVE STATUS blocks. Stub-redundant index lines (rules now directly carried by a stub) are surfaced in Needs-review for operator confirmation, never auto-deleted — the index line is the recall path to its topic file's long-form.
- Never overwrite a `.claude/references/` file that already exists — report the conflict and skip the whole change: the rules file stays unchanged unless the existing copy is identical to it.
- Never append to a pointer instruction file. Every append lands in the content file — CLAUDE.md or AGENTS.md, whichever carries the content at that level, and `CLAUDE.md` when both do; a `## Topic-specific guidance` section written into a pointer would leave a malformed hybrid that is neither.
- Missing rules files (referenced in CLAUDE.md or AGENTS.md but not found on disk) always go in Needs-review — creating them requires correct content, not a placeholder stub.
- If any Write or Edit fails, report the failure and continue with remaining changes; do not abort the whole apply run. A failed, conflicting or no-longer-identical references copy, or a failed archive append, cancels the removal that depended on it.
- Do not commit. Leave in-repo changes in the working tree for operator review before committing; memory-directory edits have no working tree to review unless that directory is itself in a Git worktree.
