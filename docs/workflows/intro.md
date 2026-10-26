These diagrams summarize the **Skill Mesh v2.0.1** contracts. Use the
[skill reference](../../documentation/skill-reference.md) for a compact table
of all 57 skills, purposes, host coverage and direct diagram links.

Each diagram declares its source and omitted detail. The linked source contract
remains authoritative: a diagram does not authorize an action, bypass a hold,
or establish live qualification. Claude has all 57 packages; Codex and Copilot
have the 54 portable packages. Native capability gates still apply.

These diagrams use the same rounded cards, monospace labels, and blue connectors
as the overview graphics. Blue-bordered **GATE** cards mark decisions; connector
labels preserve their outcomes. Open a diagram at full size to inspect larger flows.
Light and dark variants follow your display preference.

The `.mmd` files remain the editable graph sources. [Show Your Work](https://github.com/aberson/show-your-work)
checks their metadata and builds the source index; the repository's presentation
script lays out those graphs and publishes native SVG cards. It preserves every
node, connector, and source reference. Readers need no rendering tools.

From a workspace containing both project checkouts:

```powershell
uv run --project show-your-work --extra render python skill-mesh/tools/render-workflow-cards.py
```

Verify all generated output is current without writing:

```powershell
uv run --project show-your-work --extra render python skill-mesh/tools/render-workflow-cards.py --check
```

Run the original source/render validation when changing a graph:

```powershell
uv run --project show-your-work --extra render show-your-work check skill-mesh/docs/workflows --render
```

Use the presentation script above instead of plain `show-your-work render`, which
produces the default Mermaid README rather than this SVG gallery.
