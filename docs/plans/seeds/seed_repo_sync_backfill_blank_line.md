# Seed: repo-sync Step 7b backfill misses steps with a blank line after the heading

**Status:** queued 2026-11-18. Not started; no lane (skill-mesh lanes are parked). Small fix.
**Found by:** the V4-10 core companion lane while running repo-sync on `documentation/core-companion-plan.md` (Phase COMP, #279-#300).

## Defect

The Step 7b reference backfill snippet in `skills/repo-sync/core.md` matches nothing when a blank line sits between `### Step N:` and the first `- **Field:**` bullet. That is the house layout in current plans.

On the core companion plan it reported "missing or already set" for all 21 steps and changed nothing. That is a false negative, not a corruption, and the skill's own verify grep caught it. The lane re-ran the snippet with an optional blank-line group after the heading, which filled exactly the 21 Issue values (commit `511821a`).

## Fix

- Add an optional blank-line group, `(?:[ \t]*\r?\n)*`, between the heading and the first bullet in the snippet's pattern.
- Add an eval fixture with a blank line after the heading, plus one without, so both layouts stay covered.
- Check sibling snippets that anchor on `### Step N:` followed by a bullet (plan-review, plan-wrap, build-phase) for the same assumption.

## When it is picked up

Plan it as a step through the normal flow, with an issue, then build it with `/build-step`.
