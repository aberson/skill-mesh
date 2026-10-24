# citation-sweep - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full. The invoking parent owns every artifact's OPEN, PREPARE, and COMMIT; never create per-artifact action workers.
- Resolve one exact judge id through citation-review's current GPT rule and pass it unchanged. After OPEN ALL, map each vote to one fresh depth-1 action/task child with no prior conversation or child-spawn authority.
- Prove that capability before opening. Missing or inconclusive isolation returns required_tool_missing; there is no in-context voting fallback.
- Preserve project-filtered readiness lists, global field labels, ordered barrier, exact run ids, frozen evidence, k=3/5/7, and all partial states. Provider errors are reported and never trigger implicit replacement or calibration.

## Known GPT limitations

Claude-only session and Artifact surfaces are unavailable. Use only core-authorized durable forms.

## Output normalization

Return only the core's scope, per-path states, queue results, failures, and next actions.
