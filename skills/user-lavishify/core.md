# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, GPT, Codex) must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/user-lavishify/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# user-lavishify

Take the artifact-shaped content just delivered in this conversation and turn it into a **Lavish Editor** review surface: a self-contained HTML page opened in the operator's own browser, where they annotate elements / text ranges / Mermaid nodes and the feedback returns here structured. This is the **inverse** of building in Lavish from the start — normal delivery is plain chat; this escalates a specific output to Lavish only when spatial annotation beats typing.

`$ARGUMENTS`

If the argument is non-empty, render THAT (a named plan file, a section, "the comparison you just showed"). If empty, render the **last substantial assistant output** — a plan, comparison, table, diagram, report, or a list of proposed changes. If the last output was short or conversational, ask what to render instead of guessing.

## Contract

- **Invocation.** Operator-invoked only: an on-demand escalation, never a default. No other skill or default output path invokes it. The scoped default artifacts elsewhere (the `/repo-update` guided tour, durable records) are read surfaces, not this annotate loop.
- **Artifact location.** One self-contained HTML file under `.lavish/` in the host's session scratchpad; on a host without a session scratchpad, under a durable host-local temporary directory's `.lavish/` folder, reported by path. Never inside any repo tree.
- **Allowed writes.** The artifact and its revisions; at End, only the edits and issue filings/comments that carry decisions the operator made in this session back to their source of truth (step 8). Issue filings/comments go only to the checked operator-owned repository, named explicitly on every write (step 8). No global install; no writes by `lavish-axi` into agent config or hooks (never `setup hooks`); hook or settings changes that carry a decision go through their owning path (`update-config`), and on a host without that path they are listed under "anything not propagated and why" (`owning path unavailable`), never edited directly; no commit or push; and no publishing of the artifact.
- **Side effects.** `npx -y` fetches `lavish-axi` from the npm registry and stores it in the npm cache (`_npx`); a detached `lavish-axi` server listens on loopback (127.0.0.1); the tool may keep its own session state for queued feedback (location not verified); the operator's browser opens the session URL and loads the CDN snippets the artifact references; at End, issue filings/comments through the host's GitHub tool, only in the checked operator-owned repository, named explicitly (step 8). Telemetry is off on every command (Guardrails).
- **Outputs.** The session URL at Open (step 5); the closing summary at End (step 8).
- **Held states.** Report the reason, stay in chat and write nothing further; if step 5 already started the server, run `npx -y lavish-axi stop` first. Never relax a Guardrail to get past one.
  - Empty argument and a short or conversational last output: ask what to render.
  - Feedback that is naturally textual: say chat is the better call (Notes).
  - `node` missing or older than 22: stop before any `lavish-axi` command and report the version found.
  - `npx -y lavish-axi` cannot be fetched or started: report the error; no global install or alternate runner.
  - The operator's browser cannot reach the loopback server (remote, cloud or headless host): stop. Never make the server reachable beyond the host's loopback by any means: no `lavish-axi share`, no non-loopback `LAVISH_AXI_HOST` (wildcard or specific address), and no tunnel, relay or port-forward.
  - A required host capability is missing: `required_tool_missing`.
- **Resume.** The artifact file persists. If the harness killed the poll, re-run `npx -y lavish-axi poll <file>` (step 6; queued feedback is never lost in that case). If the server is no longer running, re-open with `npx -y lavish-axi <file>` (step 5), then poll; feedback from before the server stopped is not assumed to survive. Both commands carry the step 2 telemetry prefix. Propagation is not idempotent: after an interruption, check whether a destination already reflects a decision before applying it again.

## When to use vs. not

- **Use** when the just-delivered content is dense/structured and the operator would otherwise have to quote many things to fix — multi-step plans, option comparisons, diagrams, big tables, a long list of proposed edits, or a UI/design mock.
- **Don't** for short or conversational replies — chat is faster and zero context-switch (thinking-as-you-type is the default). Lavish costs a browser context-switch + artifact-authoring effort; only spend it when element-level annotation genuinely pays.

## Workflow

1. **Pick the content.** The last substantial output (or `$ARGUMENTS`). Keep the substance identical — this is a re-presentation, not a rewrite.
2. **Preflight.** Confirm `node --version` is ≥22. Every `lavish-axi` command in this skill MUST be prefixed with `LAVISH_AXI_TELEMETRY=0` (PowerShell: `$env:LAVISH_AXI_TELEMETRY='0';`). No global install — always `npx -y lavish-axi`. The command forms in this skill omit the prefix for brevity; every one still carries it. A failed preflight is a held state (Contract).
3. **Consult playbooks.** Run `npx -y lavish-axi playbook <id>` for each matching type (`plan`, `comparison`, `diagram`, `table`, `code`, `input`, `slides`) and `npx -y lavish-axi design` for the DaisyUI+Tailwind CDN snippet, the Mermaid CDN snippet, and the copy-paste layout-safety CSS. Open every matching playbook before writing HTML.
4. **Author the artifact.** Write a self-contained HTML file to the artifact location (Contract; never into the repo tree). Design-system priority: (1) a look the operator named; (2) the *subject project's* design system if one exists; (3) the Lavish DaisyUI `luxury` fallback. Paste the layout-safety CSS. Use Mermaid for flow/architecture/dependency graphs, not hand-built div boxes. Prevent horizontal overflow at every nesting level.
5. **Open.** `npx -y lavish-axi <file>` — spawns the detached loopback server (127.0.0.1) and opens the operator's browser. Print the session URL.
6. **Poll (background).** `npx -y lavish-axi poll <file>` as a background task — it long-polls silently for annotations, queued prompts, and browser-reported `layout_warnings`; never kill it, and just re-run it if the harness kills it (queued feedback is never lost). Fix fresh error-severity `layout_warnings` and re-check before involving the operator; surface persistent/low-severity ones with a note.
7. **Loop.** Apply each element-pinned change to the artifact (the browser live-reloads), then `npx -y lavish-axi poll <file> --agent-reply "<message>"` to reply in the browser and keep waiting. Repeat until the operator ends the session (in the browser, or by saying so in chat).
8. **End + PROPAGATE.** On end, run `npx -y lavish-axi end <file>` then `npx -y lavish-axi stop`. Then do the step the loop does NOT do for you: **propagate the decisions back to the real source of truth** — the plan doc, the issues, the code — because the annotations landed on a throwaway artifact, not on canonical state. Grep every downstream consumer of a changed decision before claiming it's done, and file/​comment issues for any real delta. Summarize what changed and where. Propagate only decisions the operator made in this session; edits stay in the working tree for the normal wrap path. The summary names the artifact path, each decision with its destination (file path or issue link), anything not propagated and why, and any layout warning left unresolved.
   - **Issue destination (fail closed).** File or comment issues only in an operator-owned repository. Resolve the project's repository with the working-directory rule; that rule picks the repository layer, not ownership. Before any issue write, resolve the target once: the `owner/name` of the `origin` GitHub remote of that repository's git root. With no such remote, file and comment nothing, and list the delta under "anything not propagated and why" as `no GitHub remote`. The target is operator-owned only if (a) at least one entry in the workspace registry (`.claude/observatory/registry.toml`; `owned` follows the workspace descriptor contract) matches the git root, by a `repo_url` that names any of its remotes (https or ssh form, with or without `.git`, compared case-insensitively) or by a `path` that, resolved against the dev coding-root, is the same directory as the git root (normalized absolute paths; separator- and case-insensitive on Windows), every matching entry says `owned = true`, and either a matching `repo_url` names the target or the target's owner equals the authenticated `gh` login; (b) the git root is the dev coding-root repository; or (c) no entry matches and the target's owner equals the authenticated `gh` login (case-insensitive, exact). Otherwise, or when the check cannot complete, file and comment nothing there, and list the delta under "anything not propagated and why" as `repository not operator-owned (<owner/name>)`.
   - **Issue writes.** Every issue filing or comment names the checked target explicitly (`gh issue create --repo <owner/name>`, `gh issue comment <number> --repo <owner/name>`, or the host GitHub tool's explicit `owner/name`); never rely on the tool's default repository. Comment on a linked issue only when the link's `owner/name` equals the checked target; otherwise list that delta as `not the checked target (<owner/name>)`, naming the link's `owner/name`.
   - **Issue content.** Issue bodies and comments carry the decision and its rationale, never the artifact file, its session URL or its bulk content.

## Guardrails (workspace-specific, non-negotiable)

- **Telemetry off** on every command (`LAVISH_AXI_TELEMETRY=0`) — the published CLI is opt-out and phones home to a third-party analytics host otherwise.
- **Loopback only** — never set `LAVISH_AXI_HOST` to a wildcard (`0.0.0.0`/`::`); the server is unauthenticated and would serve local files to the LAN.
- **Never run `lavish-axi share`** — it publishes the artifact to a third-party host (`ht-ml.app`), public by default. This is an outward egress action; do not invoke it, even if it looks convenient.
- **Never run `lavish-axi setup hooks`** — it writes SessionStart hooks into agent config dirs, bypassing this workspace's `update-config`-managed hooks and junction-based skills.
- **Artifacts live in the scratchpad**, never committed to a project tree.
- **Poll runs in the background** (the harness limits foreground command duration).
- **Windows note:** consumed via `npx -y` (Node ≥22, no install). The CLI's port self-heal is POSIX-only, so if port 4387 is stuck, set `LAVISH_AXI_PORT` or `npx -y lavish-axi stop` — don't expect it to reclaim the port itself.

## Notes

- lavish-axi is a third-party tool (register `--not-owned` if ever formalized in the observatory registry). It is invoked on demand via `npx`; nothing is installed into any project.
- The value is *spatial* feedback (click the wrong cell, select the wrong phrase, mark a Mermaid node). If the operator's feedback is naturally textual, staying in chat is the better call — say so rather than forcing the artifact.
