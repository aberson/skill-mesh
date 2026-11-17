# Acceptance workspace (fixture)

A disposable workspace for the user-afterparty acceptance run. Nothing in it is real
project state, and every path in it is created fresh in a temporary directory.

## Commands

Commands are spelled `powershell` (Windows PowerShell 5.1). PowerShell 7 (`pwsh`) is not
installed on the acceptance machine, so a command spelled `pwsh` fails there.

## Layout

- `demo-project/` - the current project for the acceptance session.
- `second-project/` - a second active project, used only by the `--all-projects` case.
- `docs/lessons-learned.md` - the long-form lessons file.
- `routing/installed-offload-config.json` - the installed routing settings that
  tier-drift compares its fresh proposal against.
