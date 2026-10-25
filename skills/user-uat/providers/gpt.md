# user-uat - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The tier partition (never auto-PASS a non-mechanical check on your own judgment), the side-effect confirmation gate, the operator-actor prerequisite rule, and stop-on-`AUTO-FAIL` stay exactly as the core states them.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json` and the capabilities the current host actually exposes.
- Map `--deep` to a fresh-context GPT action/task at the lens capability tier. After a visual judge's corroborated PASS, map the strong-final gate to a different fresh-context action/task at the strongest configured gate tier. Child actions do not spawn other graders; this parent invocation owns dispatch and deterministic mapping. If isolated actions or the required tier are unavailable, emit the core's `required_tool_missing` escalation instead of assessing inline or accepting the visual PASS.
- Human-in-the-loop normalization: return exactly the core's stop/hold message when input,
  prerequisite or capability resolution halts; otherwise return the complete step-5 report —
  first the exact classification line for every grounded step, including grounded steps left
  unexecuted after a stop, then one verdict/evidence line only for each processed step, any
  `Still running:` line, the exact `Needs you` heading, and the closing what's-left line. Never
  invent a verdict for an unexecuted step. Under `--dry-run`, return exactly the core's step-2
  listing. Add no other result headings (no separate `Done` section), no speculative advice,
  and no verbose internal deliberation; stop after the operator ask.
- `--ui` delegates through named-skill dispatch to `/judge-ui` / `/judge-motion`. `judge-motion` is Claude-native and absent from the GPT profile; if a needed judge is unavailable or fails its own capability contract on this host, report the step `ESCALATED` with `required_tool_missing: <judge>` and list it in `Needs you` - never view the screen and render a visual verdict yourself.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, provider failure, parse failure, or missing required adapter, use the core's fail-closed escalation and name the missing capability. Never silently omit a core gate or rationalize a side-effectful step as read-only to skip confirmation.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
