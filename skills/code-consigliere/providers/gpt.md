# code-consigliere - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting and preserve its target resolution, evidence labels,
  signoff boundary, private/public split, helper discovery order, and seed handoff.
- Use structured filesystem and shell actions for reads and helper calls. This core requires no
  isolated action child and no model-tier resolution.
- Ask for the target only when the core's ordered resolution leaves a coding root or multiple
  plausible projects. Do not inspect the toolkit checkout as a silent default.

## Known GPT limitations

- Claude session state and Claude-only tools are unavailable. Use only this host session's own
  explicit project pin, when present.
- If the optional helper is unavailable, use the core's read-only orientation path. Never
  simulate persistent collection or install the helper.

## Output normalization

Return only the core's attended findings, questions, durable artifact locators, and closing
report. Preserve the four evidence-status labels exactly and reject missing evidence rather
than inferring success.

