# Unmeasured positive fixture: apply boundary

Input is `docs/plan.md#M2`. The file is readable and contains exactly one `## M2 — Checkout UAT`
heading. I saved its exact bytes before refinement. The replaceable draft is the trailing UAT
step list under that heading; the preceding status field, the later `## Manual UAT` section, and
the following `## M3` section are outside the span.

Findings: the draft's “works correctly” expectation is ambiguous. The chat refinement uses
`### Step 1: Checkout`; the written span renders that as `##### UAT step 1: Checkout`, while a
literal `# example output` inside its fenced shell block remains untouched. Immediately before
writing, I re-read `docs/plan.md`; its bytes match the saved input. I preserve BOM, line endings,
and every byte outside the span, then replace that one span.

No clarifying questions — refined UAT above is final. Written back to `docs/plan.md:42-58`.
The outside-span hash is unchanged. Re-rendering the same refinement produces bytes equal to the
current span, so the rerun makes no write and reports `no change`.

