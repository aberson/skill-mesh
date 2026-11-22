# Release notes template

Copy this into the GitHub release body for a new Skill Mesh release, then fill in each item in
angle brackets from the tree. Keep it plain: what changed for the reader, what they do, and which
checks ran. Every number comes from the tree or a check record, never from memory.

The companion set table below is generated. Before a release, regenerate it with
`python tools/companions.py table --kind release` and paste the output between the markers. The
command refuses (and prints why) if a core or optional member has no pinned tag, so a release
never lists an untagged tool. A test fails when this copy differs from the manifest.

---

**Skill Mesh <version>: <one-line summary>**

<One paragraph: what this release is, what it builds on, and the catalog size: <N> skills,
<P> portable (Claude and Codex) and <C> Claude-only.>

**What changed for you**
- **<Change>.** <What it does for the reader, in one or two sentences.>

**Companion set**

`-Companions core` installs the core members below, and `-Companions all` adds the optional ones.
Each installs from its own public repository at the tag shown.

<!-- companions-table:release:begin -->
| Member | Ring | Tag | Installs from |
|---|---|---|---|
| [passing-notes](https://github.com/aberson/passing-notes) | core | `v0.1.0` | `git+https://github.com/aberson/passing-notes@v0.1.0` |
| [switchboard](https://github.com/aberson/switchboard) | core | `v0.1.1` | `git+https://github.com/aberson/switchboard@v0.1.1` |
| [tripwire](https://github.com/aberson/tripwire) | core | `v0.1.1` | `git+https://github.com/aberson/tripwire@v0.1.1` |
| [find-again](https://github.com/aberson/find-again) | optional | `v0.1.0` | `git+https://github.com/aberson/find-again@v0.1.0` |
<!-- companions-table:release:end -->

**Upgrading**
Install the Claude and Codex profiles from the zip with the installer, then restart your
sessions.

**Checks run**
- <Each named suite or pack and its real summary line. Anything that did not complete says so.>

**Download:** `skill-mesh-<version>.zip` (<file count> files), with its SHA-256 in
`skill-mesh-<version>.sha256`. Restart host sessions after upgrading.
