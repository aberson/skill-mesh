# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/observatory-doctor/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# Observatory Doctor — launcher-button health check

One command that answers "are all my dashboard buttons actually going to work?" The dev-observatory
dashboard renders a launcher button per derived `model.Verb` on every surface (Rich CLI table,
static HTML, VS Code tasks, web UI) — this checks that list once and reports which buttons are OK,
which are suspect (WARN), and which are dead (BROKEN).

It is a **thin wrapper**: all logic lives in the `observatory doctor` CLI subcommand
(`dev-observatory/src/dev_observatory/doctor.py`),
which reuses the production launch path (`launch.build_argv` / `launch.observe`) so it measures the
same thing a real click does. The skill runs it, relays the verdict, and frames every break as an
`open-repo`-and-fix action. **It never edits a project to "fix" a button** — per the operator's
workflow, breakage → you open the repo and fix it yourself.

## What it checks (per button)

| Check | BROKEN / WARN | Meaning |
|---|---|---|
| `cwd` exists | BROKEN | the project dir the button runs in is gone |
| runner on PATH | BROKEN | `powershell` / `bash` / `wsl` not resolvable |
| `-File`/script exists | BROKEN | the `.ps1`/`.sh`/… the command names isn't under the cwd |
| leading tool on PATH | WARN | `uv`/`npm`/`git`/`code`/… not found (a subprocess PATH can differ from your shell) |
| `status` live-probe | WARN | `git status` exited non-zero (dir may not be a standalone repo) |
| `--probe <verb>` live-run | BROKEN | you asked it to run this button and it exited non-zero |

Servers, demos, and confirm-gated verbs are **never** auto-run — long-running buttons are validated
statically (does the script/runner/cwd exist), not executed.

## Run it

Default = static checks on every button + a live `status` probe. From the coding root (`dev/`) or
anywhere under it:

```powershell
uv run --project dev-observatory observatory doctor
```

Relay the report. Read the header line (`N buttons across M projects`, `X OK | Y WARN | Z BROKEN`)
and the `BROKEN` / `WARN` sections verbatim — they are already operator-facing and each broken
project ends with its `-> fix: code "<path>"` line.

Flags (pass through to the CLI):

- `--probe <verb>` — also **actually run** this button and check it exits 0 (repeatable). Use for a
  quick functionality button you want to confirm works, e.g. `--probe run-validate`,
  `--probe run-check`. Do **not** probe a demo/server/`run-*` that launches a UI — it will hang the
  timeout. Safe picks are the fast, terminating functionality buttons.
- `--no-probe` — fully static; runs nothing (fastest; use in a hostile/offline env).
- `--json` — structured output (`summary` + `broken` + `warn` + `fix_commands`) for programmatic
  callers; parse this instead of the text when a `/goal` or another skill consumes the result.
- `--strict` — exit 1 when any button is broken (else always exit 0). Use to gate a `/goal` loop.

## Reading the report → fixing

1. **All OK** → report `all N buttons healthy` and stop. Nothing to do.
2. **WARN only** → surface them but don't alarm: a `tool not on PATH` warn usually just means the
   tool lives on the operator's interactive PATH, not the subprocess PATH; a `status` warn means
   that dir isn't its own git repo. Note them and move on unless the operator cares.
3. **BROKEN** → this is the actionable part. For each broken project the report gives one
   `code "<abs-path>"` command. Present those as the fix path:

   > `<slug>` has broken button(s): `<verb>` — `<reason>`. Open the repo to fix:
   > ```powershell
   > code "<workspace>\<slug>"
   > ```

   Common broken causes + where the fix lives:
   - **script not found** → the launcher points at a moved/renamed script. Fix the path in the
     project (if it's a scraped command, in the project's `CLAUDE.md`; if it's a launcher, in the
     registry's `[project.launch]` for that slug), or drop the dead button by adding its verb name
     to that project's `hide_verbs` in `registry.toml`.
   - **cwd missing** → the project moved or the registry `path` is stale.
   - **runner not on PATH** → a `bash`/`wsl` button on a machine without that shell.

Do not auto-apply any of these — hand the operator the `open-repo` command and let them decide.

## Scope + relationship to other pieces

- **Buttons themselves** (add/delete/rearrange) are registry config, not this skill's job: add a
  button via `[project.launch]` (a `name = "command"` becomes a `run-<name>` button, in file order),
  delete one via `hide_verbs = ["<verb>"]`, rearrange by reordering the `[project.launch]` entries.
  See `descriptor-contract.md` §1 and the registry.
- **Priorities** (which section a project sits in) are the `category` field in the registry, not a
  doctor concern.
- This skill only ever **reads** — the one owner of button-health logic is the CLI; this file cites
  it, it does not restate it (`.claude/rules/knowledge-placement.md`).
