# review-uat - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json` and the capabilities the current host actually exposes.
- Human-in-the-loop normalization: the core's only operator asks are the draft request (Inputs) and the numbered **Clarifying questions** list (Step 6). End exactly as Step 6 specifies; do not append a `Done` / `Needs you` section of your own, and never add speculative advice or verbose internal deliberation. When `--exec` relays `/user-uat`'s report, its `Needs you` section and its AUTO-PASS / AUTO-FAIL / ESCALATED lines pass through verbatim. Preserve PASS/FAIL/UNCERTAIN or escalation enums exactly.
- Apply `judge-core.md` unchanged: independent judge context, evidence on every retained verdict, deterministic aggregation, mechanical gates first, and UNCERTAIN/escalation rather than an unsupported PASS. review-uat is judge-core's critic role (section 1); for its own Blocker/Gap/Minor findings the invariants apply as follows, and none is dropped: it never certifies its own refined UAT (the operator accepts it); every finding carries evidence - the grounded `file:line` with its excerpt, the quoted draft text for a finding about the draft's own wording, ordering or numbering, or for **Blocker: cannot ground** and coverage-gap findings the scope searched - and a finding with none of these is dropped, while the draft step it concerns stays in the Refined UAT (core: Do not delete coverage); every visual check is paired with a read-back (core Step 3); uncertainty becomes a numbered Clarifying question or a Blocker, never an invented pass criterion; and the findings are advice to the operator, never an approval gate, whichever model produced them (invariant 7). Mechanical gates and aggregation of executed results belong to `/user-uat` and its vision judges on `--exec`; relay their results verbatim and never re-judge them.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, provider failure, parse failure, or missing required adapter, return the core's failure result and name the missing capability. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
