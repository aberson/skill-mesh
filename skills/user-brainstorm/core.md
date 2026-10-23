# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, GPT, Codex) must load it in full.

## Provider-neutral host abstractions

- This skill has no runtime scripts or assets. Its offline evals stay with the compatibility launcher at `.claude/skills/user-brainstorm/evals/`.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# user-brainstorm

Help the user explore and document an arbitrary topic — engineering pattern, architectural concern, product question, design space — by producing a tiered reference set.

The activity has two phases: **interactive ideation** (seed → gap-fill → tier, with the user in the loop) and **parallel investigation** (one background sub-agent per topic writes a templated reference file). The output is a self-contained, navigable doc set the user can grep later.

## When to use

- User wants to ideate comprehensively on a topic.
- User asks "what are the considerations for X" or similar open-ended exploration.
- User wants a reference doc set produced from a back-and-forth, not a one-shot answer.
- After running, the user has a folder of cross-referenced investigations they can refer back to.

## When NOT to use

- Single specific question with a single specific answer — just answer it.
- Topic is already covered by an existing doc set — point at that instead.
- Topic is too narrow (one concern, not a space of concerns).

## Inputs, writes and re-runs

- **Input:** the topic (argument, or asked for in Step 1). There are no flags; a bare invocation asks for the topic and writes nothing until the user confirms a write (Step 5's "Proceed?", or a resume's "Proceed?").
- **Writes:** only inside the confirmed output directory. The orchestrator writes `topics.md`, `plan.md` and `README.md`; each sub-agent writes only its one assigned `NN-<slug>.md`. Every write is create-only: immediately before writing `topics.md`, `plan.md` or `README.md`, confirm that file is absent; if it is present, write nothing more, report it, and re-run the directory check below. Nothing is deleted, renamed or overwritten, no git operation runs, and nothing is published.
- **Complete directory inspection is a prerequisite to writing.** Inspect all direct entries,
  including hidden entries and empty sub-directories. A file-only glob or recursive file list
  cannot establish that a directory is empty or contains only the permitted files. If the
  host cannot complete this check, report `required_tool_missing` with the missing inspection
  capability and write nothing. A denied or failed inspection also stops before writing;
  report the actual failure. Do not assume the unseen entries are absent, defer the check
  until after a write, or treat an operator's description of the directory as inspection.
- **Existing output directory** (checked in Step 1 before the path is confirmed, and again at each write gate, after Step 5's or a resume's "Proceed?" and before anything is written; if the state differs from the one the user confirmed, write nothing and offer the outcome for the new state):
  - Absent, or empty (no entries at all: no files, no sub-directories, hidden entries included): a new set.
  - Holds `topics.md` and `plan.md`, no `README.md`, every investigation link in `topics.md` resolves to a direct child `<dir>/NN-<slug>.md`, and otherwise only investigation files named in `topics.md`: an interrupted set (a session that ended, or a host that stopped at Step 7). Offer to resume it, stating how many of the files listed in `topics.md` are missing and that a set another live session is still writing looks the same, so the user should confirm no other session is working on it; then ask "Proceed?". On explicit confirmation, run Step 7 for the missing files only, then Step 8. A declined resume is treated as an existing set (below), but suggest only a sibling path such as `<slug>-2`: creating a sub-directory inside the interrupted set would block a later resume. A resume never rewrites `topics.md`, `plan.md` or an existing investigation file. Ideation bullets are not on disk: in a new session, brief the missing files from `topics.md`, `plan.md` and the per-agent grounding, and say so in the end report.
  - Anything else: an existing set. Never write a file into it. Point the user at it (see "When NOT to use") and ask for a different path, suggesting `<slug>-2` beside it, or a new sub-directory inside it that does not exist yet (only that new sub-directory is written; the set's own files are never touched). The new path gets the same check.

## Steps

### 1. Get the topic

Required argument. If not provided, ask: "What topic do you want to brainstorm?" Derive a kebab-case slug from the topic. Check the target directory (see "Inputs, writes and re-runs") and confirm the output path with the user (default: `docs/investigations/<slug>/` relative to CWD); a different path the user picks gets the same check.

### 2. Seed 10 topics

Generate **exactly 10** topics related to the subject. Each is a short noun phrase (3-8 words) describing a concern, pattern, failure mode, or design decision. Output as a numbered list. No commentary — let the user react.

### 3. Gap-fill loop

Ask the user: "Are there any topics not mentioned that are really important?" Take any user additions verbatim, then add 5-10 more topics that the user's additions imply or that round out coverage. Re-present the running list (or just the additions) and repeat the question.

Stop when:
- User says no new topics surface, or
- The next round produces only low-value / redundant additions.

Typical: **3-4 rounds total** (1 seed + 2-3 gap-fills); the cap is **4 rounds** (1 seed + 3 gap-fills). Do not loop indefinitely. If after round 3 the user is still adding meaningful topics, the topic was probably wider than expected — say so and ask whether to keep going (round 4, the last) or split into sub-topics. After round 4, run no further round: take any user additions verbatim without generating more, say the subject is too broad for one set, and ask whether to keep going to tiering with the current list or split into sub-topics. On a split, propose the sub-topics; this run continues to Step 4 with the topics of the one the user picks, under its own slug (Step 1's directory check again), and the end report names the rest as separate later runs.

### 4. Aggregate + tier

Combine all surfaced topics into one list. De-duplicate. Then organize into four tiers:

- **Tier 1 — Load-bearing.** Foundational; the system / approach breaks without these. Often includes a meta-principle that several other Tier 1 topics are special cases of.
- **Tier 2 — High-leverage.** Shape outcomes significantly. Calibration, integration, scope decisions.
- **Tier 3 — Optimization.** Matter at scale or in edge cases. Cost discipline, specialized lenses, performance refinements.
- **Tier 4 — Hygiene.** Worth doing but rarely the bottleneck. Long-term system health, polish.

Present the tiered list to the user and ask: "Tiering look right? Any topics to move, merge, or cut?" Adjust based on response.

### 5. Confirm structure

Before writing anything, show the user:
- The output path (e.g., `docs/investigations/<slug>/`).
- The file structure that will be created (see "Output layout" below).
- The total number of investigation files (one per surfaced topic).
- Approximate per-file size (350-600 words).
- On a host whose provider wrapper already reports that it cannot dispatch isolated sub-agents, a note that only `topics.md` and `plan.md` will be written now. Where the wrapper decides this only at Step 7 (an isolation check that runs before the first isolated arm), a note that the investigation files may not be written on this host.

Ask: "Proceed?" Wait for explicit confirmation before any file write.

### 6. Write meta files

After the write-gate directory check ("Inputs, writes and re-runs"), write two meta files into the output directory before dispatching agents. Each write is create-only:

- **`topics.md`** — flat list of all topics, tier-organized, each line a markdown link to the eventual investigation file (`NN-<slug>.md`). Brief provenance note at top (how many rounds, how the set was assembled).
- **`plan.md`** — investigation methodology. Goal, scope, common template (verbatim), execution model (sub-agent-per-file dispatch), output structure, done criteria.

The links in `topics.md` name planned files. Never report a file as written until Step 8 confirms it exists.

### 7. Dispatch sub-agents

One background sub-agent per investigation file, each dispatched with explicit
`model: sonnet` (authorship fan-out arms run Sonnet by default — workspace
model-tiering policy). Each agent is briefed with:

- File path to write (`docs/investigations/<slug>/NN-<topic-slug>.md`).
- Topic title and tier.
- Workspace context files to read for grounding (see "Per-agent grounding" below).
- Topic-specific bullets (the angle, related workspace incidents, key references the agent should weave in — gathered during the ideation phase).
- Likely cross-references (slugs of related sibling investigations).
- The investigation file template (verbatim — see below).
- Constraints (length, tone, no invented references).

**Dispatch in waves of ~10-12 background agents per message.** A single mega-message dispatching all agents has been observed to trigger `529 Overloaded` cascades; waves keep concurrent load manageable. Use `run_in_background: true` so completions arrive as task-notifications.

If any agent fails (529, timeout, refusal) or completes without writing its file, retry that single file once in a fresh sub-agent dispatch, but only after the original arm has terminated (its completion arrived or you stopped it). A timed-out or otherwise unknown arm is not safe to retry while it may still be running: report that file as pending and assign no second writer until termination is confirmed. A file still missing after its retry is reported as missing, never dropped silently; retry it again only if the user asks.

If the host cannot dispatch isolated sub-agents, stop with `required_tool_missing`, naming this step. Never author the investigation files in the orchestrator's own context instead; `topics.md` and `plan.md` stay on disk for a resume on a capable host.

### 8. Write README

After all agents have completed, glob the output directory to confirm every `NN-<slug>.md` listed in `topics.md` exists. If any is still missing, do not write `README.md`: report the missing files and that re-invoking with the same topic and path resumes the set. Also list any entry other than `topics.md`, `plan.md` and the investigation files named in `topics.md` (sub-directories and hidden entries included); such an entry blocks a resume until the user resolves it, and the skill never deletes or renames it. Otherwise write `README.md`, create-only. If `README.md` is already present, write nothing, report that another writer produced the index, and finish with the normal end report without offering a new path.

- Intro paragraph stating the topic and scope.
- Tier-organized list of links to each investigation file with a one-line hook per topic.
- Provenance section (how many rounds, how many topics, dispatch pattern).
- "See also" pointers to any workspace rules, memories, or skills the agents commonly referenced.

End the activity with a summary message to the user: total files written, location, any agents that needed retry, and what to do next (browse the README, grep for keywords).

## Output layout

```text
docs/investigations/<topic-slug>/
├── README.md           # tier-organized index, links to every file
├── topics.md           # flat list with tier headers
├── plan.md             # methodology that produced this set
└── NN-<slug>.md        # one per topic, numbered 01..NN
```

## Investigation file template

Every investigation file uses this exact structure:

```markdown
# <Topic Title>

**Tier:** <1 | 2 | 3 | 4>
**Status:** Investigated
**Related:** [[other-slug]], [[other-slug]]

## What it is
<1–2 paragraphs. State the concept directly.>

## Why it matters
<Failure modes. Workspace incidents if applicable. What goes wrong without this.>

## When to apply
<Trigger conditions — bullet list when natural.>

## How to apply
<Concrete patterns, decisions, snippets, checklists.>

## References
<Pointers to actual files in the workspace. Only cite ones the agent verified by reading. Common shapes:
- Rule: `<file>.md § <section>` (relative path)
- Memory: `<memory-file>.md`
- Skill: `<skill-name>`
- Incident: <project> <phase or step>>

## Open questions
<What's not settled. What to investigate further.>
```

## Per-agent grounding

Each sub-agent's prompt instructs it to read (whatever exists in the workspace):

- Project root instruction file (CLAUDE.md or AGENTS.md) if present.
- Rule files under `.claude/rules/*.md` if the project has them.
- Workspace memory index (typically at `<workspace-memory>/MEMORY.md`) and any `feedback_*.md` / `project_*.md` files it points to that look topic-relevant.
- `SKILL.md` files under `.claude/skills/<name>/` for skills clearly relevant to the topic.
- The `topics.md` file in the output directory (for the canonical cross-reference slug list).

Agents must only cite files they actually verified by reading. Inventing references defeats the point. Never read a secret-bearing file (credentials, tokens, `.env`, private keys).

## Sub-agent prompt template

The orchestrator constructs each agent's prompt by filling this template:

```text
Write ONE markdown file at <ABSOLUTE-PATH>/<NN>-<SLUG>.md.

Topic: "<TITLE>" (Tier <N>). One of <TOTAL> reference files about <SUBJECT>.

READ for grounding (don't invent references):
- <list of workspace files relevant to the topic, per "Per-agent grounding">

TOPIC CONTEXT (build on these — don't regurgitate):
- <3-5 bullets surfaced during the ideation phase: the angle, workspace incidents that anchor the topic, key memories/rules to weave in>

LIKELY CROSS-REFERENCES: [[other-slug]], [[other-slug]], ...

TEMPLATE (exact structure):
<verbatim template from above>

CONSTRAINTS:
- 350-600 words.
- No emojis.
- Reference tone — terse, factual.
- Markdown links use relative paths from the file's location.
- Cross-references via [[slug]].
- No padding. Honest-line is fine ("No prior incident in this workspace; pattern recommended on first-principles grounds").
- No invented references.
- Write only this one file. If it already exists, do not overwrite it; reply "Exists <NN>-<SLUG>.md".
- Never read secret-bearing files (credentials, tokens, .env, private keys).

Write the file with the Write tool. Reply: "Wrote <NN>-<SLUG>.md" plus any notes.
```

Topic-specific bullets come from the ideation phase: as the user surfaces topics and reacts, note any workspace incidents, related rules, or angles they mention. These become the per-topic grounding for the relevant agent.

## Constraints

- **350-600 words per investigation.** Concrete beats comprehensive.
- **No emojis.**
- **Reference tone** — terse, factual, written to be grepped later.
- **Cross-references via `[[slug]]`** — slug = the file's `<slug>` part (without the `NN-` prefix or `.md` extension).
- **No padding.** A section with nothing real says one honest line, not a paragraph of filler.
- **No invented references.** Agents only cite files they verified by reading.
- **No naming specific other skills or projects** in the body unless the topic is explicitly about them or the name identifies a verified source (a cited rule, memory, skill or incident). The skill is topic-agnostic; each investigation stays on its topic. The References section and the README's "See also" may cite any file the agent verified by reading.

## Limitations

- **Dispatching all agents in one mega-message.** Hit a 529 cascade once. Wave them in batches of ~10-12.
- **Skipping the tier confirmation.** Tiering decisions shape the README's organization and the user's mental model. Always confirm before writing.
- **Letting gap-fill loop forever.** Cap at 4 rounds. If the user keeps adding meaningful topics past that, the subject is too broad — surface this and ask whether to keep going to tiering with the current list or split (Step 3).
- **Writing meta files before tier confirmation.** Cheap to revise verbally, expensive to revise after files exist.
- **Producing generic content because the agents weren't grounded.** Per-agent bullets and workspace context reads are what make the output useful. Skipping them produces hand-wavy reference docs that read like generic blog posts.
- **Writing into an existing set.** Other documents cite investigation files by path; overwriting or renumbering one breaks them. Use a new path, or resume an interrupted set ("Inputs, writes and re-runs").

## End-of-activity report

Final message to the user includes:
- Output directory path.
- File count produced (and any that needed retry, plus any still missing with the resume instruction and any unlisted file that blocks the resume).
- Total topics by tier (e.g., "9 Tier 1, 12 Tier 2, 11 Tier 3, 3 Tier 4").
- Any notes the agents flagged in their completion replies (e.g., "agent 14 noted an existing inconsistency in <rule>; worth a follow-up").
- Any sub-topics deferred by a split, as separate later runs.
- One suggested next action — usually "browse the README" or "grep for <topic-keyword>".

Keep it short. Two or three sentences plus the file count.
