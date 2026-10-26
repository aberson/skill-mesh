# Install or upgrade Skill Mesh v2

**v1 is deprecated and must not be reactivated.** Use only v2 distributions for
active installations. Historical restoration evidence below describes qualification,
not permission to restore retired v1 skills. Restart host sessions after upgrading.


Use **Windows PowerShell 5.1**. Download the release ZIP and its SHA-256 file,
compare the archive hash with the checksum, then extract into a dedicated directory.
The bundle includes generated distributions; installation needs no source build.

From the directory holding the downloaded archive:

```powershell
Get-FileHash .\skill-mesh-v2.0.1.zip -Algorithm SHA256
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
[Codex guide](providers/codex.md). For Copilot use `-Provider gpt`.
Start a fresh host session after installation. Installing does not authenticate
the host or supply missing native capabilities. Codex uses its own adapter and
authenticated host, not the GPT/Copilot transport.

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
