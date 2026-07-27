# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/user-project/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

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
`git rev-parse --show-toplevel`.** From inside a nested project repo (measure-twice, Alpha4Gate, …
each have their own `.git`) toplevel is the *project* repo, whose tree has no `registry.toml`; and
Step 4 (plan-expedite) invokes this skill after `cd`-ing into the project, so bare toplevel would
break there. Walk up to the directory that owns `.claude/observatory/registry.toml` (a
coding-root-only marker):

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
- **`$sid`** = this session's UUID = the **parent-dir name of your scratchpad path**
  (`…\<workspace-id>\<UUID>\scratchpad`; schema doc § Session identity). If no scratchpad path
  is visible, fall back to the freshest `sessions/*.md` (same fallback the hooks use).
- **`$sessionFile`** = `$root\.claude\task-state\sessions\$sid.md` — the pin canonically lives in
  **coding-root** task-state.
- **`$registry`** = `$root\.claude\observatory\registry.toml`.

The pin is stored as a single header field, immediately under `**Last written:**`, in this exact
greppable shape (backslash-normalized abs path; the statusline and honoring skills parse it):

```
**Active project:** <slug> (<abs-repo-path>)
```

## SET — `/user-project <name>`

1. **Validate `<name>` against the registry, matching `slug` OR `path` (exact, no substring).** The
   registry is an array of `[[project]]` tables, each with an explicit `slug` and `path` field (see
   `descriptor-contract.md` §2); do NOT rely on `repo_url`
   (several owned entries lack it). Parse the entries PS-5.1-safe (no ternary/`&&`):

   ```powershell
   $reg = [System.IO.File]::ReadAllText($registry)
   $entries = foreach ($blk in ($reg -split '(?m)^\s*\[\[project\]\]\s*$')) {
       $slug = [regex]::Match($blk, '(?m)^\s*slug\s*=\s*"([^"]+)"').Groups[1].Value
       if (-not $slug) { continue }
       $path = [regex]::Match($blk, '(?m)^\s*path\s*=\s*"([^"]+)"').Groups[1].Value
       if (-not $path) { $path = $slug }
       $owned = [regex]::Match($blk, '(?m)^\s*owned\s*=\s*(true|false)').Groups[1].Value
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

3. **Write the pin** (read-merge-write; never `git add -A` after — the file is gitignored):
   - **If `$sessionFile` exists:** set-or-replace its `**Active project:**` line — overwrite in
     place if present, else insert directly after the `**Last written:**` line. If a (malformed)
     file lacks that anchor, insert after the last `**…:**` header line preceding the first `##`
     section. Refresh `**Last written:**` (UTC ISO-8601) and `**Session SHA:**`
     (`git rev-parse --short HEAD`). **Preserve every other line verbatim.** Use the Edit tool for a
     surgical replace, or .NET IO for a full rewrite (`[System.IO.File]::WriteAllText`, UTF-8
     **no BOM** — matches sibling session files; never `Set-Content -Encoding utf8`, which adds a
     BOM).
   - **If `$sessionFile` is absent** (rare — normally `task-handoff` has already created it): create
     a minimal schema-valid file — Task/Status/Session SHA/Last written + the `**Active project:**`
     line + `## Next Action`. Set Task to `(no task yet — project pinned via /user-project)` so a
     later real `task-handoff` write plainly supersedes it (a same-session task IS a change, so the
     schema's "overwrite Task only when task changes" rule replaces it) while **preserving
     `**Active project:**`** per § Persistence.

4. **Confirm** in one line: `Pinned active project: <slug> (<abs-repo-path>). Pipeline skills will target it via git -C regardless of cwd.` (append ` [third-party]` per 2 if applicable).

## SHOW — bare `/user-project`

Read `$sessionFile`. If it exists and has an `**Active project:**` line, print it:
`Active project: <slug> (<abs-repo-path>) — honored by pipeline skills via git -C.`

Otherwise print `Active project: unset — deriving from cwd.` and show what cwd resolves to, so the
operator sees the fallback the honoring skills use:

```powershell
$cwdRepo = git rev-parse --show-toplevel   # the repo cwd currently sits in
```

`cwd repo: <$cwdRepo>` (note: from `dev/` this is coding-root; from inside a nested project it is
that project's repo).

## CLEAR — `/user-project clear`

Read `$sessionFile`. Remove the `**Active project:**` line if present (refresh `**Last written:**`),
preserving all other lines. Print `Active project cleared — reverting to cwd-derived repo.` If no
file or no pin exists, print `Active project already unset.` and write nothing.

## How honoring skills consume the pin (contract)

A skill that targets a project repo resolves the target in this precedence:

1. The `**Active project:**` pin in this session's `sessions/<id>.md`, if set → use its `<abs-repo-path>` as `git -C <path>`.
2. Else the plan/argument's project (e.g. a `--plan measure-twice/plan.md` → `measure-twice`).
3. Else the cwd-derived repo (`git rev-parse --show-toplevel`).

Consumers are wired in the transition-message + wrong-directory-guard steps of the
project-context-clarity feature (plan-expedite, repo-sync, build-phase, build-step, repo-update).
The pin is never a hard gate.

## Persistence

The `**Active project:**` field is a documented header field in
`.claude/references/task-state-schema.md` (File-format
header + Field-definitions table). Consequences, all verified against the real per-session model:

- It **survives the derived rollup** — `task-state-derive.ps1`'s `Write-DerivedRollup` copies the
  freshest session file's body wholesale, so the header field lands in `current.md` unchanged. It is
  a `**...**` header field, not a `## section`, so it does **not** touch `$TaskStateSectionPrefixes`
  or its one-source-of-truth test.
- It **must survive `task-handoff --loop`** — that writer is read-merge-write and defers field
  semantics to the schema doc; because the field is documented there (with "preserve across every
  other write" semantics), the writer carries it over. This is the load-bearing persistence
  contract: without the schema-doc entry the pin would evaporate on the next checkpoint.

## Relationship to other skills

| Skill / file | Role |
|---|---|
| `.claude/rules/working-directory.md` | The two-repo model this pin implements the "eliminate" half of. |
| context statusline (`.claude/statusline/context-statusline.ps1`) | Reads the pin to show the active project in the status line. |
| plan-expedite, repo-sync, build-phase, build-step, repo-update | Honor the pin when targeting a project repo. |
| task-handoff `--loop` | Must preserve the pin across checkpoints (schema-doc contract). |
