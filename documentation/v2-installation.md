# Install or upgrade Skill Mesh v3

**v1 is deprecated and must not be reactivated.** Use only v2 or later distributions
for active installations. Historical restoration evidence below describes qualification,
not permission to restore retired v1 skills. Restart host sessions after upgrading.


Use **Windows PowerShell 5.1**. Download the release ZIP and its SHA-256 file,
compare the archive hash with the checksum, then extract into a dedicated directory.
The bundle includes generated distributions; installation needs no source build.

From the directory holding the downloaded archive:

```powershell
Get-FileHash .\skill-mesh-v3.0.4.zip -Algorithm SHA256
```

Choose one host profile and an explicit consumer home:

| Provider flag | Host | Discovery root under the chosen home |
|---|---|---|
| `claude` | Claude Code | `.claude/skills/` |
| `gpt` | GitHub Copilot CLI | `.github/skills/` |
| `codex` | OpenAI Codex CLI | `.agents/skills/` |

From the extracted bundle root, replacing the example home:

```powershell
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider claude -Home C:\path\to\consumer-home -DistDir .\dist
```

For Codex use `-Provider codex`; first resolve its effective home with the
read-only [probe](../tools/probe-codex-skills.ps1) and
[Codex guide](providers/codex.md). `-Provider gpt` installs the old Copilot profile, which is no longer supported.

**GitHub Copilot (GPT) is no longer supported.** Skill Mesh supports Claude Code and the OpenAI Codex CLI. The v3.0.x release zips still carry the old GPT profile, unchanged and no longer maintained or qualified; the GPT adapters, the `.github/skills` install target and the GPT build are removed in v4. If you used the GPT profile, move to Claude Code or Codex.

Start a fresh host session after installation. Installing does not authenticate
the host or supply missing native capabilities. Codex uses its own adapter and
authenticated host, not the GPT/Copilot transport.

## Companion tools (`-Companions`)

The skills call a few small public tools, the companion members listed in
[`config/companions.json`](../config/companions.json) (owned by the
[core companion plan](core-companion-plan.md), sections 3 and 4). The installer can
install them after the skills:

```powershell
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider claude -Home C:\path\to\consumer-home -DistDir .\dist -Companions core
```

| `-Companions` | Installs |
|---|---|
| `none` (default for now) | skills only, exactly as before |
| `core` | the core ring |
| `all` | the core and optional rings, then prints each optional member's setup steps (never runs them) |

The README's [members table](../README.md#companion-tools) lists each member with
its ring, pinned tag and the skills that call it; it is generated from the
manifest. `-Companions all` adds Find Again, the one optional member. A tool
joins the companion only when a skill or hook in a released Skill Mesh calls it,
it installs from a public repository at a tag that passed Skill Mesh's checks for
it, and it meets the utility project standard.

Tripwire's hook is advisory: it checks a shell command before it runs and adds a
note when it finds a problem, and it never blocks a command.

The hooks follow `-Provider`, the same way the member skills do:

- `-Provider claude` registers tripwire's `PreToolUse` hook, and passing-notes'
  `Stop` hook, in `<home>\.claude\settings.json`.
- `-Provider codex` registers tripwire's `PreToolUse` hook (matcher `^Bash$`,
  5-second timeout) in Codex's user-level hook file, `<home>\.codex\hooks.json`.
  Use the Codex `-Home`, the folder that holds `.codex` (normally your user
  profile). The step never writes `config.toml`. If your `config.toml` already
  defines hooks, the Codex hook is skipped with one note, because Codex should
  read hooks from one file per layer, not two. The `[hooks.state]` entries Codex
  writes when you trust a hook are not hook definitions and do not cause a skip.
- `-Provider gpt` installs no hooks.

Either way, the step copies the packaged hook file to
`<home>\.<host>\hooks\companions\tripwire-pretool.ps1` and adds one entry that
runs it. Everything else in the file stays as it was. A file that is not valid
JSON is left untouched, and the hook is skipped. A re-run with nothing to change
writes nothing. The Codex entry's command starts with `powershell.exe`, never with
a quoted path, because Codex runs hook commands through PowerShell and a leading
quoted path would not parse.

**Trust the Codex hook.** Codex runs a new or changed hook only after you trust
it. After a Codex install, the step prints one line naming the entry. Open
`/hooks` in Codex and trust the tripwire `PreToolUse` entry. Skill Mesh never
writes a trust record for you. When the hook is removed during uninstall, any
Codex hook entries listed after it in the same event move up one place. The
step says so, because Codex may ask you to trust those again.

`-NoHooks` skips every companion hook and `-SkipHook <slug>` (repeatable, for
example `-SkipHook tripwire`) skips one member's hooks, for every host. Both are
remembered in the companion ledger, and a hook installed earlier is removed on
the next run. Uninstall removes only the entries and copied files it installed,
for both hosts. A copied hook file you have edited is kept.

Candidates are never installed. A member whose manifest tag is still null
(unreleased) is reported `skipped: unreleased`. The companion step needs three
things on `PATH`: `uv`, Git and Python 3.12 or later. If any is missing, every
member is reported `skipped: missing <tool>` and nothing is installed. The skill
install has already completed by then and is not affected.

For each selected member, in manifest order, the step runs:

1. `uv tool install "git+<repo>@<tag>"`. If the member's command is already on
   `PATH` (or in uv's tool directory) and Skill Mesh did not install it, the member
   is reported `skipped: pre-existing ...` and left alone. It is never reinstalled
   or uninstalled.
2. The member's health command.
3. The member's own skill installer, when the member ships skills (passing-notes'
   lane skills). The step fetches a tagged source checkout with
   `git clone --depth 1 --branch <tag>` into
   `<home>\.skill-mesh-companions\src\<slug>` and runs the installer from there.
   It appends `--host <host> --root <that host's skills folder in this home>`.
   `-Provider claude` maps to `--host claude` and `-Provider codex` to
   `--host codex`; the old `gpt` profile has no member skill host. The member's
   installer owns those files and keeps its own ledger. Skill Mesh never copies
   or deletes them. The checkout stays in place so uninstall can run the member's
   uninstaller offline.
4. The member's own ledgered writer (`setup_write`), when it has one.

Each member gets one status line: `install-companions: <slug>: installed`,
`already current`, or `skipped: <reason>`. A member that fails is reported, and
the others still run. Re-running with the same manifest reports
`already current` and changes nothing.

When the manifest moves a member to a new tag, the step reinstalls the tool and
re-runs the member's skill installer and writer at the new tag. The ledger keeps
the old tag until every one of those steps has succeeded. If one fails, or the
process is stopped, the next run still sees the old tag and re-attempts the whole
upgrade instead of reporting `already current`. Ownership of a new tool is
recorded before `uv tool install` runs and dropped again if nothing was installed,
so an interrupted install is never mistaken for a pre-existing tool.

The companion step keeps its own ledger, `<home>\.skill-mesh-companions.json`. It
never reads or writes the Skill Mesh skill ledger (`.skill-mesh-install.json`).
The ledger has one entry per member: the tag, `installed` or `pre-existing`, and
which member skill hosts and writers ran. Member tools are installed once per
user (uv's tool directory), and their ledger entry belongs to the home, not to
one provider. So installing the claude and codex profiles into the same home
records both skill hosts on one entry.

With `-Uninstall -Companions core` (or `all`), the companion step runs after the
skill uninstall. It reverses only work its ledger records, in reverse order:
the member writer's uninstall command, the member skill uninstaller for each
recorded host, the source checkout, then `uv tool uninstall <slug>`.
A recorded host whose skills folder no longer exists has nothing left to remove
and is noted and skipped. Uninstall checks the manifest with
`tools/companions.py verify` first, as install does, so it needs Python 3.12;
without it, nothing is uninstalled. Pre-existing tools are never touched. `core` reverses the core-ring entries and
`all` reverses every entry. A companion failure is reported but never changes
the skill install's result.

`tools/install-companions.ps1` can also be run on its own with the same
`-Provider`, `-Home`, `-Companions` and `-Uninstall` parameters. Its exit codes
are 0 (done, skips included), 1 (a member failed), 2 (usage error), 3 (manifest
or companion ledger refused, nothing changed) and 4 (another companion operation
holds this home's lock). Refusals are written to the error stream.

Before upgrading, preserve the previous distribution and back up the target
discovery tree and `.skill-mesh-install.json`. Stop sessions writing those paths.
Run the installer with the new distribution and existing home. It checks
ownership and current bytes; investigate collisions instead of routinely using
`-Force`. Multiple hosts may scan overlapping roots, so directory names alone
do not establish ownership.

<details>
<summary>Uninstall, restoration and legacy installations</summary>

Remove the selected profile's unchanged owned files:

```powershell
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider claude -Home C:\path\to\consumer-home -Uninstall
```

To restore a preserved prior generated profile, uninstall the current profile,
then use the v2 installer with `-DistDir` pointing to that prior distribution.
Qualification covered preserved pre-rebuild bytes with the final installer,
not every historical v1 release or older installer. Modified files may need
explicit resolution. Uninstall does not reconstruct hand-maintained legacy
files; retain a separate backup and follow the
[migration guide](migration.md).

</details>


[Back to the overview](../README.md).
