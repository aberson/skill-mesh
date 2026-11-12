# user-build-route - Codex entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full and preserve its route criteria and output contract.
- Use native read-only file and shell tools for the core's bounded inspection.
- This skill spawns no agents, invokes no skills and starts no goal. Commands in
  the response are recommendations for the operator only.
- Render a plain-language next prompt unless this host's invocation syntax is
  verified. Do not assume Claude's `/goal` command exists on another host.
- If required context cannot be read, disclose it and ask only if it changes the
  route. Never fabricate evidence or use a legacy skill as a fallback.

## Output normalization

Return only the core-defined decision, brief rationale, next step and copy block.
Do not reveal hidden chain-of-thought. Do not create durable artifacts.
