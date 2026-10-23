# NOTE: This is the canonical provider-independent contract. Every provider wrapper (Claude, Codex, GPT) loads it in full.

## Provider-neutral host abstractions

- This skill has no supporting scripts or runtime assets; the PowerShell blocks below are the whole procedure.
- It invokes no other skill, spawns no agent and uses no model tier: every step is deterministic work in the invoking session.
- Session identity comes only from the host session-I/O adapter (§ Session identity). A host that cannot supply it gets the identity-unavailable outputs below; it never weakens the identity rule.
- Never expose hidden chain-of-thought. Return only the output lines this contract defines.

# User Project — session-active project pin

The single "eliminate" mechanism of the working-directory model (`.claude/rules/working-directory.md`):
a session-scoped pin naming which **project repo** pipeline work should target, so cwd stops
mattering. When set, boundary skills read it and operate on that repo via `git -C <abs-path>`
regardless of the shell's cwd; when unset, they fall back to the cwd-derived repo.

The pin is **advisory-but-honored**: it never blocks anything — it just tells honoring skills where
"the project" is. It lives in this session's own task-state file, so two windows can pin two
different projects without contention.

## Modes (dispatch on the argument)

| Invocation | Mode | Effect |
|---|---|---|
| `/user-project <name>` | **SET** | Validate `<name>`, resolve its repo path, write the pin. |
| `/user-project` (bare) | **SHOW** | Print the current pin, or "unset — deriving from cwd" + the cwd repo. |
| `/user-project clear` | **CLEAR** | Remove the pin from this session's file. |

Autonomous: never prompt. On a bad name, fail loud (list known slugs) and write nothing.

## Shared resolution (all modes)

Resolve these once, up front. **`$root` is the coding-root (`dev/`), located by MARKER — not bare
`git rev-parse --show-toplevel`.** From inside a nested project repo toplevel is the *project* repo,
whose tree has no `registry.toml`, and callers such as plan-expedite may invoke this skill from
there. Walk up to the directory that owns `.claude/observatory/registry.toml` (a coding-root-only
marker):

```powershell
$d = (Get-Location).Path
while ($d -and -not (Test-Path (Join-Path $d '.claude/observatory/registry.toml'))) {
    $p = Split-Path $d -Parent
    if ($p -eq $d) { $d = $null; break }   # reached filesystem root
    $d = $p
}
if (-not $d) { Write-Error "/user-project: could not locate coding-root (no .claude/observatory/registry.toml at or above $(Get-Location))."; return }
$root = $d
```

- **`$root`** = the coding-root just resolved — used for the registry, the abs-path base, AND the
  session file, so every consumer (statusline, honoring skills) resolves the pin from the SAME
  place regardless of cwd (no split-brain).
- **`$sid`** = this session's stable ID per § Session identity, or *unavailable*.
- **`$sessionFile`** = `$root\.claude\task-state\sessions\$sid.md` — the pin canonically lives in
  **coding-root** task-state.
- **`$registry`** = `$root\.claude\observatory\registry.toml`.

The pin is stored as a single header field, immediately under `**Last written:**`, in this exact
greppable shape (backslash-normalized abs path; the statusline and honoring skills parse it):

```
**Active project:** <slug> (<abs-repo-path>)
```

## Session identity (write authority)

- **Claude:** the parent-dir name of the scratchpad path (`…\<workspace-id>\<UUID>\scratchpad`);
  it equals the hook `session_id` and the transcript basename (task-state schema § Session identity).
- **Codex / GPT:** only a stable per-session ID that this skill's own provider adapter for the
  running host explicitly binds. An adapter that binds none gets the identity-unavailable outputs.
- Accept `$sid` only as one path segment (no `\`, `/` or `..`).
- **Never** take the freshest `sessions/*.md` or the `current.md` rollup as this session's file, and
  never fabricate, guess or borrow an ID: not another host's session variable, not an environment
  variable the running host's adapter does not name (for example `COPILOT_AGENT_SESSION_ID` while no
  adapter of this skill binds it), not a launching environment's ID, and never the router's
  `SKILL_ROUTER_SESSION_ID` (a spend-ledger key, auto-generated per invocation when unset; it names
  no session). Those files belong to other windows: writing one silently re-targets another
  window's pipeline and statusline. Without an identity the rollup is orientation only, never write
  authority (`docs/lessons-learned.md` § task-state-needs-session-identity).
- **`$sid` unavailable:** SET (after name validation) and CLEAR write nothing and print exactly
  `Active project not changed: required_tool_missing (session identity). Honoring skills fall back to the plan/argument or cwd repo.`
  SHOW prints its identity-unavailable line. This is an advisory result, never a halt for a caller.

## SET — `/user-project <name>`

1. **Validate `<name>` against the registry, matching `slug` OR `path` (exact, no substring).** The
   registry is an array of `[[project]]` tables, each with an explicit `slug` and `path` field (see
   `descriptor-contract.md` §2); do NOT rely on `repo_url` (several owned entries lack it). Read only
   each entry's own keys — the text before its first sub-table header (`[[project.wiring]]`,
   `[project.launch.*]`, … carry their own `path` keys). Parse PS-5.1-safe (no ternary/`&&`):

   ```powershell
   $reg = [System.IO.File]::ReadAllText($registry)
   $entries = foreach ($blk in ($reg -split '(?m)^\s*\[\[project\]\]\s*$')) {
       $head = ($blk -split '(?m)^\s*\[', 2)[0]   # the entry's own keys end at its first sub-table header, including a legally indented one
       $slug = [regex]::Match($head, '(?m)^\s*slug\s*=\s*"([^"]+)"').Groups[1].Value
       if (-not $slug) { continue }
       $path = [regex]::Match($head, '(?m)^\s*path\s*=\s*"([^"]+)"').Groups[1].Value
       if (-not $path) { $path = $slug }
       $owned = [regex]::Match($head, '(?m)^\s*owned\s*=\s*(true|false)').Groups[1].Value
       [pscustomobject]@{ slug = $slug; path = $path; owned = $owned }
   }
   $match = $entries | Where-Object { $_.slug -eq $name -or $_.path -eq $name } | Select-Object -First 1
   ```

   If `$match` is `$null`, **fail loud** and STOP (write nothing):
   `/user-project: unknown project '<name>'. Known slugs: ` + `(($entries.slug | Sort-Object) -join ', ')`.

2. **Resolve the abs repo path** = `$root\<match.path>`, **normalized to backslashes** so the pin
   value is consistent for the statusline to parse:

   ```powershell
   $abs = [System.IO.Path]::GetFullPath((Join-Path $root $match.path))   # yields C:\...\<path>
   ```

   - If `$match.owned -eq 'false'` (third-party, e.g. tinstar) still allow the pin (it is advisory),
     but append ` [third-party]` to the confirmation line so it's visible the target is outside
     coding-root ownership.

3. **Identity check.** If `$sid` is unavailable, print the identity-unavailable line and STOP.

4. **Write the pin** (read-merge-write; never `git add -A` after — the file is gitignored):
   - **If `$sessionFile` exists:** set-or-replace its `**Active project:**` line — overwrite in
     place if present, else insert directly after the `**Last written:**` line. If a (malformed)
     file lacks that anchor, insert after the last `**…:**` header line preceding the first `##`
     section. Refresh `**Last written:**` (UTC ISO-8601) and `**Session SHA:**`
     (`git rev-parse --short HEAD`). **Preserve every other line verbatim.** Use a surgical in-place
     edit (Claude: the Edit tool) or .NET IO for a full rewrite (`[System.IO.File]::WriteAllText`,
     UTF-8 **no BOM** — matches sibling session files; never `Set-Content -Encoding utf8`, which adds
     a BOM).
   - **If `$sessionFile` is absent** (rare — normally `task-handoff` has already created it): create
     a minimal file: a `# Task State — user-project <UTC date>` title; `**Task:** (no task yet — project pinned via /user-project)`;
     `**Status:** IN_PROGRESS`; `**Session SHA:**`; `**Last written:**`; the `**Active project:**`
     line; and `## Next Action` whose body is `(none recorded)` (the placeholder the resume hook
     prints for an empty Next Action), never a runnable command. That placeholder deliberately
     departs from the schema's one-exact-command Next Action form, but it is not a fresh,
     operator-authorized plain action and the schema's resume backstop cannot execute it. The next
     `task-handoff` checkpoint replaces it. A later real
     `task-handoff` write supersedes Task (a same-session task IS a change, so the schema's
     "overwrite Task only when task changes" rule replaces it) while
     **preserving `**Active project:**`** per § Persistence.

5. **Confirm** in one line: `Pinned active project: <slug> (<abs-repo-path>). Pipeline skills will target it via git -C regardless of cwd.` (append ` [third-party]` per 2 if applicable).

## SHOW — bare `/user-project`

Read-only in every case. If `$sid` is unavailable, print
`Active project: unknown (session identity unavailable); honoring skills fall back to the plan/argument or cwd repo.`
and the cwd line below; never read another session's file in its place.

Otherwise read `$sessionFile`. If it exists and has an `**Active project:**` line, print it:
`Active project: <slug> (<abs-repo-path>) — honored by pipeline skills via git -C.`

Otherwise print `Active project: unset — deriving from cwd.` and show what cwd resolves to, so the
operator sees the fallback the honoring skills use:

```powershell
$cwdRepo = git rev-parse --show-toplevel   # the repo cwd currently sits in
```

`cwd repo: <$cwdRepo>` (note: from `dev/` this is coding-root; from inside a nested project it is
that project's repo).

## CLEAR — `/user-project clear`

If `$sid` is unavailable, print the identity-unavailable line and write nothing. Otherwise read
`$sessionFile`. Remove the `**Active project:**` line if present (refresh `**Last written:**` and
`**Session SHA:**`), preserving all other lines. Print
`Active project cleared — reverting to cwd-derived repo.` If no file or no pin exists, print
`Active project already unset.` and write nothing.

## Writes, failures and re-runs

- **Only write:** this session's `$sessionFile` — the `**Active project:**`, `**Last written:**` and
  `**Session SHA:**` lines, or the minimal file in SET 4. Never `current.md`, another session's
  file, the registry, or the git index (no `git add` or commit).
- **Failures write nothing:** no coding-root marker (the error line above); unknown name (fail loud);
  identity unavailable (the identity-unavailable line).
- **Idempotent:** re-running SET with the same name rewrites the same line (only `Last written` and
  `Session SHA` change); a second CLEAR prints `Active project already unset.`

## How honoring skills consume the pin (contract)

A skill that targets a project repo resolves the target in this precedence:

1. The `**Active project:**` pin in this session's `sessions/<id>.md`, if set → use its `<abs-repo-path>` as `git -C <path>`.
2. Else the plan/argument's project (e.g. a `--plan measure-twice/docs/archived-plans/plan.md` → `measure-twice`).
3. Else the cwd-derived repo (`git rev-parse --show-toplevel`).

Readers locate `sessions/<id>.md` at the coding-root (`$root` above), with their own session ID
only; a reader without its own ID treats the pin as unset. The pin is never a hard gate.
`.claude/references/transition-directory-contract.md` applies this precedence to next-step
directories and the project-switch message; `/repo-wrap` lets an explicit positional target
outrank the pin (a deviation that contract records).

## Persistence

The `**Active project:**` field is a documented header field in the task-state schema
(`.claude/references/task-state-schema.md`, vendored as
`<repo>/_shared/task-state-schema.md`; File-format header + Field-definitions table): overwrite
on re-pin, **preserve verbatim across every other write**, remove only on `/user-project clear`.
Consequences:

- **`task-handoff --loop`** is read-merge-write and carries the field over verbatim because the
  schema documents it; without that entry the pin would evaporate on the next checkpoint. It writes
  `<git-root>/.claude/task-state/sessions/<id>.md`; from inside a nested project repo that is the
  project's file, not the coding-root file holding the pin, which it then leaves untouched. The
  coding-root file stays the pin's only source either way.
- **The derived rollup** (`task-state-derive.ps1` `Write-DerivedRollup`) copies the freshest
  session file's body wholesale, so `current.md` shows the *freshest* session's pin. That is
  orientation only, never another session's pin source. The field is a `**...**` header, not a
  `## section`, so it does not touch `$TaskStateSectionPrefixes` or its one-source-of-truth test.

## Relationship to other skills

| Skill / file | Role |
|---|---|
| `.claude/rules/working-directory.md` (+ reference) | The two-repo model this pin implements the "eliminate" half of; its wrong-directory guard (`.claude/hooks/lib/wrong-dir-guard.ps1`) compares the resolved target with the commit repo and suggests `/user-project clear`. |
| context statusline (`.claude/statusline/context-statusline.ps1`, `.sh`) | Reads this session's pin (stdin `session_id`, coding-root file) to show the active project. |
| plan-expedite | Auto-pins a registered nested project at the plan→repo boundary by calling `/user-project <slug>`. |
| `transition-directory-contract.md` citers (plan-review, repo-init, repo-sync, build-phase, build-step, repo-update, user-uat, session-wrap, user-wrap) | Name the resolved target directory in next-step lines; the switch message is silent when pinned. |
| repo-wrap | Honors the pin for bare invocations; resolves a slug argument the way SET step 1 does. |
| task-handoff `--loop` | Must preserve the pin across checkpoints (schema contract). |
