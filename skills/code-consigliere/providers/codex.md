# code-consigliere - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and preserve its target resolution, evidence labels,
  signoff boundary, private/public split, helper discovery order, and seed handoff.
- Use Codex structured filesystem and shell calls for reads and helper commands. This core
  requires no isolated fresh-context agent, no model-tier resolution, and no router hop.
- Ask for the target only when the core's ordered resolution leaves a coding root or multiple
  plausible projects. Do not inspect the Skill Mesh or helper checkout as a silent default.
- Continue from available project evidence when helper discovery fails, while reporting
  persistent collection as unavailable.

## Known Codex limitations

- Claude session JSONL, Artifact actions, Claude Agent/Workflow tools, and Claude-only deep
  links are unavailable and are never simulated.
- On a tool failure, preserve the actual error and mark dependent claims unverified. Do not
  switch providers or claim a private event was recorded without helper success.

## Output normalization

Return only the core's attended findings, questions, durable artifact locators, and closing
report. Preserve the four evidence-status labels exactly and reject missing evidence rather
than inferring success.

