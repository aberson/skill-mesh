# Skill Mesh v1 — retired archive

**Deprecated. Do not load, install, dispatch, or fall back to these skills.**
Skill Mesh v2 is the supported release line. Use the [v2 installation guide](../../documentation/v2-installation.md).

`legacy-source.zip` preserves the 46 legacy top-level skill launchers and their
tracked supporting files as they existed at the commit recorded in `manifest.json`.
The manifest records every archived file's SHA-256 and the ZIP checksum. This is
the retained legacy source collection, not a claim that a v1 release tag existed.

The old `<skill>/SKILL.md` files have been removed from the live source tree.
Keeping the archive compressed prevents recursive skill discovery from finding
its launchers. Do not extract it into a repository or host skill-discovery root.
Any offline historical inspection must stay outside active discovery paths.

Some top-level helper scripts and tests remain because current tooling still
uses them. Their presence does not reactivate the removed v1 launchers. Canonical
v2 sources live under `skills/`; generated host profiles come from the versioned
v2 distribution. Archives and historical instructions are never an execution fallback.

Deprecation cannot revoke copies on other machines, immutable historical releases,
or instructions already loaded in an open host session. Upgrade each consumer and
start a fresh session. Preserve local edits privately before upgrading; never put
private installed-profile backups in this public archive.
