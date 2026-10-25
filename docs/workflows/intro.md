These diagrams summarize the **Skill Mesh v2.0.0** contracts. Use the
[skill reference](../../documentation/skill-reference.md) for a compact table
of all 57 skills, purposes, host coverage and direct diagram links.

Each diagram declares its source and omitted detail. The linked source contract
remains authoritative: a diagram does not authorize an action, bypass a hold,
or establish live qualification. Claude has all 57 packages; Codex and Copilot
have the 54 portable packages. Native capability gates still apply.

This folder uses [show-your-work](https://github.com/aberson/show-your-work).
Edit the hand-authored `.mmd` files or `intro.md`, then regenerate the README
and index. From a workspace containing both project checkouts:

```powershell
uv run --project show-your-work --extra render show-your-work check skill-mesh/docs/workflows --render
```

After a passing check:

```powershell
uv run --project show-your-work show-your-work render skill-mesh/docs/workflows
```

Verify generated output is current:

```powershell
uv run --project show-your-work show-your-work render skill-mesh/docs/workflows --check
```

The renderer is an authoring dependency only. GitHub displays the generated Mermaid
blocks directly; readers and installed skills do not need Show Your Work.
