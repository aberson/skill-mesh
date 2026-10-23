# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, Codex, GPT) must load it in full.

## Provider-neutral host abstractions

- This skill ships no scripts. `evals/` is support material that stays with the compatibility launcher at `.claude/skills/user-learn/evals/`. Project paths such as `scripts/run_all_notebooks.sh` resolve against the output project root (default `applied_learning/`), never against the skill directory.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# user-learn

Turn a topic into a self-contained, **hands-on** learning folder. The method is applied learning — **70% hands-on, 20% mentoring, 10% coursework** — and that ratio is made physical in the folder layout (`70-handson/`, `20-mentoring/`, `10-coursework/`).

Two phases: a short **interactive setup** (get topic, confirm scope, ground in the user's real projects), then **parallel authoring** (one background sub-agent per file; notebook agents author AND execute their own notebook until it runs clean).

Default output root is the `applied_learning/topics/<slug>/` repo. The skill is topic-agnostic and reusable for any future concept.

## Contract

- **Input:** `<topic>` (required), optional depth `maximal` (default) or `lite`, optional output project root (default `applied_learning/` under the dev workspace root). Bare invocation: ask once for the topic; write nothing until it is answered.
- **Output:** the topic folder (Output layout), its `README.md` and `20-mentoring/progress.md`, and the Step 7 report in chat.
- **Allowed writes** (project-visible writes; tool-managed caches such as the uv, Jupyter and matplotlib caches are excluded): only inside `<root>/topics/<slug>/`, plus three pre-existing project mechanics: one `uv sync --project <root> --locked --inexact` of the output project (it may create `<root>/.venv/` or install declared packages into it; it never rewrites `<root>/uv.lock` and keeps undeclared packages, except one uv must replace because it conflicts with a declared dependency), new dataset files in the shared `<root>/data/` cache (existing entries are never deleted or overwritten), and each notebook agent's own `NN`-unique temp files (deleted after use). Never edit another topic, the project's `pyproject.toml`, `uv.lock`, scripts or plan, or goblin's source. Every Step 4 arm prompt carries this boundary (the BOUNDARY lines in the templates).
- **No git:** the skill never stages, commits or pushes. The new folder is left uncommitted for the operator.
- **Setup writes nothing:** Steps 1-3 only read and ask.
- **Stops (write nothing):** the topic folder already exists; `<root>/pyproject.toml` is missing; the host cannot dispatch the Step 4 isolated arms (`required_tool_missing`, reported after setup, before any preflight write). A failed preflight `uv sync` (including a missing or stale `<root>/uv.lock`, which `--locked` refuses to rewrite) or dataset pre-fetch also stops the run before any arm is dispatched: no topic file is written, and the report names any `.venv/` or `data/` change already made.
- **Re-runs:** a second run for the same slug hits the existing-topic guard, so a partial folder from an interrupted run is never overwritten; the operator extends or removes it.

## When to use

- The user wants to ramp on a concept (an ML technique, an engineering pattern, a tool) by doing.
- The user wants runnable examples + a small reading list + ideas for applying it, not a one-shot explanation.

## When NOT to use

- A single specific question — just answer it.
- The topic already has a folder under `topics/` — point at it (or offer to extend it).

## Steps

### 1. Get the topic

Required argument; if invoked bare, ask once for the topic and do nothing else until answered. Derive a kebab-case slug and the output path (default `applied_learning/topics/<slug>/` relative to the dev workspace root). Check that the output project root has a `pyproject.toml`; if not, stop and say so.

**Existing-topic guard:** Before proceeding, check whether `<root>/topics/<slug>/` already exists. If it does, stop immediately: tell the user the folder exists, offer to extend it or open it, and do NOT recreate it. Extending is a separate explicit request; this run writes nothing. Re-apply the guard if Step 2 changes the path or slug.

### 2. Confirm scope

Show the user: the output path, the folder layout (below), the planned notebook list (3-5 titles), and the depth (default: knowledge base + 4 notebooks + examples + exercises + seed-ideas). Ask "Proceed?" and wait. (This skill is interactive/user-facing — a confirm here is expected; it is NOT a build-pipeline skill.)

Depth knob: `maximal` = full KB + 4-5 notebooks + standalone examples + full exercise set. `lite` = KB + 3 notebooks (skip standalone examples and full exercise set). Default `maximal`.

### 3. Ground

Before dispatching, gather the inputs the agents need:

- **Canonical-papers list.** Assemble a vetted list of real, well-known papers for the topic. Format: `Author, Year` only. Include an arXiv ID only if you are absolutely certain of it AND mark it explicitly as `(verified)` — e.g. `Kingma & Welling, 2013 (verified: arxiv:1312.6114)`. If uncertain, omit the ID entirely. The seminal-papers agent gets this verbatim so it never fabricates citations.
- **Project applications.** Read the instruction file (CLAUDE.md or AGENTS.md) of the user's active workspace projects relevant to the topic (e.g. Alpha4Gate, toybox, sandtable, void_furnace, b2_project_goblin). The seed-ideas agent gets these paths + your notes so applications are concrete and real.
- **Notebook plan.** Decide the 3-5 notebooks: order them toy/intuition (numpy-only, always runs) -> from-scratch -> realistic-but-tiny -> advanced concept. Write a one-line spec per notebook (what it shows, what graphic it produces, whether it needs torch).

### 4. Dispatch sub-agents in waves

**Preflight, before the first wave** (the run's first writes):

1. Re-check that `<root>/pyproject.toml` exists and `<root>/topics/<slug>/` does not; otherwise stop and write nothing (Step 2 may have changed the path, and another session may have created the folder since Step 1).
2. Confirm the host can dispatch isolated arms (the provider wrapper decides); if not, return `required_tool_missing` naming this step, report the setup results, and stop.
3. Record SHA-256 hashes of `<root>/pyproject.toml` and `<root>/uv.lock`, and recursively list `<root>/data/` (if it exists), for the Step 7 outside-topic line.
4. Run `uv sync --project <root> --locked --inexact` once so torch and the notebook tooling are installed before any agent runs; concurrent first-time installs from parallel agents race. `--locked` fails rather than rewrite the tracked `uv.lock`; `--inexact` keeps packages the project does not declare. Keep the sync's summary line for Step 7. If it fails, stop and report the error.
5. Pre-fetch any SHARED dataset once (e.g. `torchvision.datasets.MNIST(...download=True)`) into the single repo-root `data/` dir; concurrent first-downloads to the same dir race and corrupt. If it fails, stop and report the error and any `data/` change.

One background sub-agent (`run_in_background: true`) per file, each with explicit `model: sonnet` (authorship fan-out arms run the Sonnet tier by default under the workspace model-tiering policy), in waves of ~6-10 (a single mega-batch has triggered 529 cascades). Authorship arms stay on the orchestrator's primary provider. Every arm prompt includes its template's BOUNDARY lines unabbreviated. One agent each for:

- every `10-coursework/*.md` and `20-mentoring/*.md` file except `progress.md` (the seminal-papers + seed-ideas agents get the grounding from step 3),
- every notebook in `70-handson/notebooks/` (each authors + self-validates its own notebook — see the notebook template),
- every `70-handson/examples/*.py` and `exercises.md`; the `exercises.md` arm uses the Knowledge-base / mentoring template, including its BOUNDARY.

Retry a failed dispatch (529, timeout, no reply) once as a fresh single dispatch, but only after the original arm has terminated (its completion arrived or you stopped it); a still-running background arm is not a failed dispatch. If the retry also fails, record that file as not written and continue. An agent that replies it could not get its notebook or script green is not retried; Step 5 records the result.

### 5. Verify, then write README + progress

After agents complete:

1. Glob the folder to confirm every planned file exists; list any that do not.
2. **Re-check notebooks and examples.** Resolve `<ABS-ROOT>` as the absolute output project root. Re-execute each notebook of THIS topic yourself, one at a time, with the same command the notebook agent used (`uv run --project <ABS-ROOT> jupyter nbconvert --to notebook --execute --inplace "<nb>"`), and run each example script of THIS topic once from its own directory (`uv run --project <ABS-ROOT> python <name>.py`). Your observed exit code is the result; an agent's "exit 0" claim alone is not. Do not run the project's all-topics `scripts/run_all_notebooks.sh` / `.ps1`: they re-execute every topic's notebooks in place.
3. **Check relative links** in this topic's markdown files. Parallel agents link to sibling files that may not exist. Repoint each broken link to an existing file in this topic, or reduce it to plain text, and note each fix.
4. Write `topics/<slug>/README.md` (index + suggested learning path, tier-ordered: skim coursework essentials -> work the notebooks in order -> do the exercises -> read seed-ideas) and `20-mentoring/progress.md` (a checklist derived from the ACTUAL notebooks + exercises produced). A notebook or example whose re-check failed stays in place and is marked `(does not run: <one-line error>)` wherever either file lists it; never list a file that was not written.

### 6. Goblin hook

`applied_learning` is already a `b2_project_goblin` target (it has a `CLAUDE.md` + `plan.md`). End by noting `uv run goblin suggest applied_learning` (from the goblin repo) as the "what should I learn/do next" nudge — goblin ranks next steps grounded in the topic folders. This skill does not run it. Do not modify goblin's source. If the output root is not `applied_learning`, add that the nudge covers `applied_learning` only.

### 7. Report

Files written, files not written, any agent retries, notebook and example-script results from your Step 5 re-check (per file: exit 0 or the error), link fixes, changes outside the topic folder (the preflight `uv sync` summary, meaning packages installed into `<root>/.venv/` or none; any recursively listed `<root>/data/` paths added since preflight; and whether the re-hashed `pyproject.toml` and `uv.lock` are unchanged or changed), that nothing was committed, and one suggested next action (open the README, run a notebook, run `goblin suggest`, or commit the folder).

## Output layout

```text
topics/<slug>/
├── README.md
├── 10-coursework/
│   ├── essentials.md          # core concepts + math prereqs, intuition-first
│   ├── papers-seminal.md      # foundational papers (from the vetted list — no fabricated ids)
│   ├── papers-frontier.md     # interesting/applied/recent papers tuned to the user's projects
│   ├── related-topics.md      # adjacency map; each entry 2-3 line explainer + link
│   └── courses-resources.md   # courses, lectures, blogs, textbooks
├── 20-mentoring/
│   ├── seed-ideas.md          # concrete applications in the user's REAL projects (grounded)
│   ├── open-questions.md      # discussion prompts to work through with a mentor / Claude
│   └── progress.md            # self-tracking checklist (written by the orchestrator in step 5)
└── 70-handson/
    ├── notebooks/             # NN-*.ipynb, runnable, executed-in-place (graphics embedded)
    ├── examples/              # standalone runnable .py scripts
    └── exercises.md           # graded exercises with hints + solution pointers
```

## Sub-agent prompt templates

### Knowledge-base / mentoring file agent

**Every KB agent prompt must include the 300–700 word hard limit from the CONSTRAINTS block below. Do not abbreviate or omit it for any file in the batch.**

```text
Write ONE markdown file at <ABS-PATH>/<FILE>.

Topic: "<TOPIC>". This file is the <ROLE> (e.g. "essentials", "seminal papers", "seed ideas").

READ for grounding (don't invent): <repo CLAUDE.md or AGENTS.md; for seed-ideas, the listed project instruction-file paths (CLAUDE.md or AGENTS.md); for seminal-papers, USE THE VETTED LIST BELOW VERBATIM>.

<for papers-seminal.md: VETTED CANONICAL PAPERS (use these, do not add ids you are unsure of):
- <Author Year — Title — arxiv id if certain> ...>

<for seed-ideas.md: TARGET PROJECTS + ANGLE:
- <project>: <one-line of how the topic could apply, grounded in what you read> ...>

CONTENT: <what this specific file should contain — see Output layout comments>.

CONSTRAINTS:
- Terse, reference tone, written to be grepped later. **300–700 words (hard limit).**
- No emojis. No padding (one honest line beats a filler paragraph).
- No fabricated citations or arXiv ids. Author+year is always safe; link arxiv.org/abs/<id> only when certain.
- Markdown links relative from the file's location.
- BOUNDARY: write only <ABS-PATH>/<FILE>. Run no project script or notebook, and never modify any other file, another topic, or the project's pyproject.toml, uv.lock, scripts or plan.

Write with the Write tool. Reply: "Wrote <FILE>" + notes.
```

### Notebook agent (authors AND self-validates)

**Every notebook agent prompt must include the full BOUNDARY and SELF-VALIDATE blocks below. Do not abbreviate or omit them for any notebook in the batch.**

```text
Author ONE Jupyter notebook at <ABS-PATH>/70-handson/notebooks/<NN>-<slug>.ipynb, then make it run clean.

Topic: "<TOPIC>". This notebook: <one-line spec — what it teaches + the graphic it produces>.

REQUIREMENTS:
- Valid nbformat v4 JSON. Most reliable: write a small builder script using `nbformat` (assemble markdown+code cells, then `nbf.write(...)`), run it, then delete it. If you use a builder or any temp file, give it a UNIQUE name that includes this notebook's `NN-` prefix (e.g. `_build_<NN>.py`) and delete it immediately after — parallel sibling notebook agents run concurrently in the SAME notebooks dir and collide on shared temp filenames. (Alternatively write the `.ipynb` directly via the Write tool or NotebookEdit.)
- Markdown cells explain the intuition before each code cell. Code cells are small and readable.
- MUST produce at least one matplotlib figure (the graphic).
- MUST run headless on CPU in seconds: tiny models (small nets, few epochs), dataset SUBSETS, set a seed. <if numpy-only: do NOT import torch>.
- ASCII only in any print()/string (Windows cp1252).
- Use only deps declared in the repo pyproject.toml (numpy, matplotlib, scikit-learn, torch CPU, torchvision). Datasets go in the single repo-root data/ dir (walk up to pyproject.toml; gitignored), never a per-notebook copy; the orchestrator pre-fetched any shared dataset there.

BOUNDARY (required):
- Write only <ABS-PATH-TO-NB>, your own `NN`-unique temp files including `_build_<NN>.py` (all deleted after use), and new dataset files under <APPLIED-LEARNING-ROOT>/data/. Never delete or overwrite an existing entry under data/.
- Run only your own builder and your own notebook (with the SELF-VALIDATE command below). Never run scripts/run_all_notebooks.* (it re-executes every topic in place), and never execute or modify another topic's files or the project's pyproject.toml, uv.lock, scripts or plan.

SELF-VALIDATE (required — do not reply until green):
  uv run --project <APPLIED-LEARNING-ROOT> jupyter nbconvert --to notebook --execute --inplace "<ABS-PATH-TO-NB>"
Run it. If it errors, fix the notebook and re-run until exit 0. Execution embeds the figures into the committed file.

Reply: "Wrote + executed <NN>-<slug>.ipynb (exit 0)" + wall-clock + any caveat. If you cannot get it green after reasonable effort, leave the notebook in place and say so explicitly with the error — do NOT claim success.
```

### Example-script agent

**Every example agent prompt must include the BOUNDARY line below.**

```text
Write ONE standalone script at <ABS-PATH>/70-handson/examples/<name>.py — a minimal, self-contained, runnable distillation of the core idea of "<TOPIC>".

CONSTRAINTS: runs headless on CPU in seconds (tiny); ASCII-only print(); only declared deps; a top docstring saying what it does and how to run it (`uv run python <name>.py`). `<APPLIED-LEARNING-ROOT>` is the absolute output project root. Datasets go in its single repo-root data/ dir (walk up to pyproject.toml), never a per-script copy; write any runtime output next to the script (`Path(__file__).parent`), never relative to the working directory. Validate by running it once from its own directory (`uv run --project <APPLIED-LEARNING-ROOT> python <name>.py`, exit 0). Reply with the result; if it does not reach exit 0, leave the script in place and say so with the error.

BOUNDARY (required): write only this script, its runtime outputs next to it, and new dataset files under <APPLIED-LEARNING-ROOT>/data/; never delete or overwrite an existing entry under data/. Run no file other than this script. Never run scripts/run_all_notebooks.*, and never execute or modify another topic's files or the project's pyproject.toml, uv.lock, scripts or plan.
```

## Constraints

- **Runnable code only** — no pseudocode in notebooks/examples. The execute-in-place gate is the proof.
- **No fabricated references.** Seed the seminal-papers agent with a vetted list; instruct author+year over uncertain ids.
- **Tiny + fast** — everything runs headless on CPU in seconds, or it is marked `(does not run: <one-line error>)` (Step 5).
- **70/20/10 layout** — always the numeric-prefix folders.
- **Ground seed-ideas in real projects** — read their CLAUDE.md or AGENTS.md; generic "you could use this for X" is the failure mode.
- **No emojis. Terse reference tone.**

## Limitations

- Dispatching all agents in one mega-message has hit 529 cascades — wave them (~6-10).
- Notebook agents that can't reach exit 0 must say so, not fake success — the orchestrator re-checks this topic's notebooks and examples in Step 5. The project's `scripts/run_all_notebooks.sh` / `.ps1` remain the operator's all-topics gate; this skill does not run them.
- Skipping the grounding step produces generic blog-post content and hand-wavy seed ideas.
- The Step 4 preflight (`uv sync`, shared-dataset pre-fetch) must finish before notebook agents run, or every execute fails or races.
