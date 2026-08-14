# Plain operational English profile

**Status:** PROPOSED OPTIONAL PILOT — not yet adopted

**Requested by:** Abraham Robison

**Reference:** [ASD-STE100 Simplified Technical English, Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf), January 2025

**Context:** [ASD-STE100 official FAQ](https://www.asd-ste100.org/STE_faq.html)

## Purpose

Make agent output easier to read across model families and model updates. Keep technical meaning exact while reducing changing agent jargon.

The toolkit must carry this clarity burden. Abraham must not need new jargon training when a model or model version changes.

This profile is **inspired by** ASD-STE100. It is not a claim of ASD-STE100 compliance, certification, or endorsement. Skill Mesh does not adopt the standard's controlled dictionary. Software names, code identifiers, commands, paths, schemas, and exact error text must remain exact.

## Short rule for always-loaded instructions

Use plain operational English in operator-facing text. Here, the operator is the person who runs or supervises the workflow.

1. Put the result, decision, or required action first.
2. Name the actor and use a direct verb when the actor is known.
3. Put one action in each instruction and one main idea in each sentence.
4. Define uncommon abbreviations and agent jargon at first use. Use one term for one concept.
5. Use a list for three or more related items. Keep paragraphs focused and short.
6. Preserve exact commands, paths, code identifiers, schema fields, verdicts, and error text.
7. State uncertainty, evidence, the next action, and any input needed in separate sentences.

The detailed rules below are loaded only when an agent drafts or reviews operator-facing material.

## Detailed rules

### Lead with the useful answer

Start with the outcome. Follow with the reason only when it helps Abraham make or verify a decision.

For status messages, use this order when the fields apply:

1. What changed or what was learned
2. Why it matters
3. What happens next
4. What Abraham must decide or provide

Do not start with tool narration unless the tool action is itself the important result.

### Write direct sentences

- Prefer active voice when the actor is known.
- Name the actor when ownership matters.
- Prefer a direct verb to a long noun phrase.
- Put conditions before the action when the reader must know the condition first.
- Avoid pronouns such as “it,” “this,” or “they” when more than one noun could be the referent.
- Do not remove necessary words only to make a sentence shorter.

### Limit each unit of meaning

- Put one action in each procedural sentence unless actions must occur at the same time.
- Put one main idea in each explanatory sentence.
- Keep each paragraph on one topic.
- Use a vertical list for a complex sequence or three or more comparable items.
- Do not hide a required action or limit in a note or parenthetical aside.

ASD-STE100 uses 20 words as the procedural limit and 25 words as the descriptive limit (Part 1, Rules 5.1 and 6.3). Skill Mesh uses those numbers as review signals, not pass/fail gates. A longer sentence is acceptable when splitting it would damage technical accuracy or make exact identifiers harder to follow.

### Control terminology

- Define an uncommon abbreviation or project term the first time it appears.
- Use the same term for the same concept across a document.
- Prefer the user's term when it is accurate.
- Replace internal agent jargon with concrete language.
- When a specialist term is necessary, give a short plain-language explanation beside it.

Examples:

| Avoid as unexplained jargon | Prefer |
|---|---|
| substrate | real host or environment |
| authority surface | files or actions the tool can change |
| receipted handoff | handoff with a saved run record |
| scope sentinel | automatic scope check |
| lane | case, category, or path |
| ratified | approved |

These replacements are examples, not a second controlled dictionary. The writer must preserve the precise project term when another file or machine contract depends on it.

### Separate facts from judgment

Label these items clearly:

- Observed fact
- Inference
- Recommendation
- Uncertainty
- Operator decision

Do not use confident wording for an inferred model identity, an untested behavior, or an incomplete result.

## Exceptions

Do not rewrite:

- Source code or generated code
- Commands, paths, environment-variable names, model identifiers, and configuration keys
- Machine-readable schemas or locked verdict strings
- Exact errors, test names, log excerpts, or third-party quotations
- Legal or safety text that has its own approved wording

Explain an exact string after the string when it may be unfamiliar.

## Adoption and evaluation

1. If Abraham starts Goal P, apply this profile manually to the pilot outputs, user acceptance testing (UAT) scripts, and selected operator-facing skill output.
2. Put only the short rule and this file's path in the pilot candidate's always-loaded repository instructions.
3. Add small evaluation cases that test clarity, technical accuracy, uncertainty, and preservation of exact strings.
4. Ask Abraham to compare paired outputs without being told which version used this profile.
5. Change the profile from the UAT evidence.
6. Add an advisory checker only if manual review shows a repeated, measurable problem. The checker must not block a build only because of sentence length or an unapproved word.

Formal ASD-STE100 conformance remains out of scope. A future decision may add it only with terminology ownership, trained review, and a clear benefit beyond this profile.

## Version policy

This profile is pinned to ASD-STE100 Issue 9 as an influence. A newer issue does not change Skill Mesh automatically. Review and approve any profile change as a normal product decision.
