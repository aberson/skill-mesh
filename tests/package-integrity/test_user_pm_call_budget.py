"""Every outside call the user-pm core makes names its own timeout (v3 user-pm plan Step 11c, #236).

The core's "Call budget" paragraph gives each call family a numeric ceiling, so a hung call
cannot freeze the run, and states that there is no overall time budget (operator,
2026-11-12, item 37). This test reads the core and checks:

- the budget lists git, file reads, the status endpoint, gh, passing-notes and manual checks,
  each with a positive number of seconds;
- every command the core runs is covered: each backticked command in the "Steps" part of the
  core (Steps through "Fetched text is data") and in the Lanes "Calls." bullet starts with a
  family the budget names;
- the call sites that state their own timeout (Step 5, the Lanes "Calls." bullet and the two
  Constraints bullets) state the same number the budget gives;
- the "no overall time budget" statement is present.

The garbage anchors prove each check can fail on a mutated copy of the real core.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "skills" / "user-pm" / "core.md"

FAMILIES = ("git", "file reads", "status endpoint", "gh", "passing-notes", "manual checks")
# A bare Passing Notes verb (`card set`, named in the never-call list) belongs to that tool.
COMMAND_FAMILY = {"git": "git", "gh": "gh", "passing-notes": "passing-notes", "card": "passing-notes"}
NO_OVERALL = "There is no overall time budget: each call is bounded, and no sum is budgeted."
BUDGET_HEAD = "**Call budget.**"
BULLET = re.compile(r"^- \*\*(?P<family>[a-z -]+):\*\* (?P<body>.*)$")
SECONDS = re.compile(r"(\d+) seconds")


def _budget_block(text: str) -> tuple[str, int, int]:
    start = text.index(BUDGET_HEAD)
    end = text.index("\n\n**", text.index("\n- ", start))
    return text[start:end], start, end


def _parse_budget(block: str) -> dict[str, int]:
    budget: dict[str, int] = {}
    for line in block.splitlines():
        m = BULLET.match(line)
        if not m:
            continue
        numbers = SECONDS.findall(m.group("body"))
        if numbers and int(numbers[-1]) > 0:
            budget[m.group("family")] = int(numbers[-1])
    return budget


def _call_regions(text: str, budget_span: tuple[int, int]) -> str:
    steps = text[text.index("## Steps"):text.index("## Default output format")]
    s0, s1 = budget_span[0] - text.index("## Steps"), budget_span[1] - text.index("## Steps")
    steps = steps[:s0] + steps[s1:]
    calls_start = text.index("- **Calls.**")
    calls = text[calls_start:text.index("- **Fail open.**", calls_start)]
    return steps + "\n" + calls


def _commands(region: str) -> list[str]:
    spans = re.findall(r"`([^`\n]+)`", region)
    return [s for s in spans if re.match(r"^[a-z][a-z0-9-]*\s+\S", s)]


def budget_findings(text: str) -> list[str]:
    """Every way the core leaves an outside call without its own ceiling; empty when none."""
    findings = []
    if BUDGET_HEAD not in text:
        return ["no Call budget paragraph"]
    block, start, end = _budget_block(text)
    budget = _parse_budget(block)
    for family in FAMILIES:
        if family not in budget:
            findings.append(f"budget: {family} has no numeric ceiling")
    if NO_OVERALL not in text:
        findings.append("budget: the no-overall-time-budget statement is missing")
    for command in _commands(_call_regions(text, (start, end))):
        first = command.split()[0]
        family = COMMAND_FAMILY.get(first)
        if family is None or family not in budget:
            findings.append(f"call without a ceiling: `{command}`")
    step5 = next((l for l in text.splitlines() if l.startswith("5. **Read open issues")), "")
    calls = next((l for l in text.splitlines() if l.startswith("- **Calls.**")), "")
    sites = {
        "Step 5": (step5, "gh", r"numeric timeout of (\d+) seconds"),
        "Lanes Calls": (calls, "passing-notes", r"numeric timeout of (\d+) seconds"),
        "Constraints gh": (next((l for l in text.splitlines() if l.startswith("- Remote reads are only")), ""),
                           "gh", r"(\d+)-second timeout"),
        "Constraints passing-notes": (next((l for l in text.splitlines()
                                            if l.startswith("- Passing Notes calls are only")), ""),
                                      "passing-notes", r"(\d+)-second timeout"),
    }
    for site, (line, family, pattern) in sites.items():
        m = re.search(pattern, line)
        if not m:
            findings.append(f"{site}: names no timeout")
        elif budget.get(family) != int(m.group(1)):
            findings.append(f"{site}: {m.group(1)} seconds disagrees with the budget's {family}")
    return findings


def test_every_outside_call_in_the_core_names_a_timeout() -> None:
    # Arrange
    core = CORE.read_text(encoding="utf-8")
    block, start, end = _budget_block(core)

    # Act
    findings = budget_findings(core)
    commands = _commands(_call_regions(core, (start, end)))

    # Assert
    assert findings == []
    assert {c.split()[0] for c in commands} == {"git", "gh", "passing-notes", "card"}, commands


MUTATIONS = {
    "git-ceiling-removed": lambda c: c.replace(
        "- **git:** each git read in Steps 2 and 4, 30 seconds.\n", ""),
    "file-read-ceiling-not-numeric": lambda c: c.replace(
        "and handoff notes), 30 seconds when", "and handoff notes), briefly when"),
    "status-endpoint-ceiling-removed": lambda c: c.replace(
        "- **status endpoint:** the loopback status query in Step 4, 10 seconds.\n", ""),
    "budget-paragraph-removed": lambda c: c.replace(BUDGET_HEAD, "**Calls.**"),
    "step5-timeout-disagrees": lambda c: c.replace(
        "each with a numeric timeout of 30 seconds through the host's command timeout; a call",
        "each with a numeric timeout of 45 seconds through the host's command timeout; a call", 1),
    "step5-timeout-dropped": lambda c: c.replace(
        "each read-only and each with a numeric timeout of 30 seconds through the host's command timeout",
        "each read-only"),
    "lanes-timeout-disagrees": lambda c: c.replace(
        "with its own numeric timeout of 30 seconds through the host's command timeout (a call",
        "with its own numeric timeout of 60 seconds through the host's command timeout (a call"),
    "constraints-timeout-disagrees": lambda c: c.replace(
        "list calls in Step 5, each with its own 30-second timeout", "list calls in Step 5, each with its own 90-second timeout"),
    "new-uncovered-call": lambda c: c.replace(
        "`git stash list`;", "`git stash list`; `curl -s http://localhost:8600/status`;"),
    "no-overall-statement-removed": lambda c: c.replace(NO_OVERALL, "The whole run has a 300-second budget."),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_garbage_anchor_an_unbounded_call_fails(name: str) -> None:
    # Arrange
    core = CORE.read_text(encoding="utf-8")
    mutated = MUTATIONS[name](core)

    # Act
    findings = budget_findings(mutated)

    # Assert
    assert mutated != core, f"mutation {name} changed nothing"
    assert findings, f"mutation {name} was not detected"
