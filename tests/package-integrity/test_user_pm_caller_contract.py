"""The user-pm core keeps the contract its one production caller depends on (v3 user-pm plan Step 11b, #236).

dev-observatory's review path is user-pm's only production caller. It sends `/user-pm` or
`/user-pm --goal|--outstanding|--cut`, adds one `Context: review the project '<slug>'.` line,
and shows the prose reply as text, title first. Its own test (in the coding root,
`dev-observatory/tests/test_review_user_pm_contract.py`) drives that path; this test keeps the
canonical core from drifting away from it:

- bare mode and the three topic flags are documented, each in the topic-flag list and with
  its own per-topic bullet;
- non-flag text after the command is context that never changes the mode or the project;
- the header rule holds: the default template opens with the title line and then
  `**What it is:**`, the topic template opens with the title line, and the notes line sits
  directly under the title so the title and `**What it is:**` stay at the top.

The garbage anchors prove each check can fail on a mutated copy of the real core.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "skills" / "user-pm" / "core.md"

CALLER_FLAGS = ("--goal", "--outstanding", "--cut")
TOPIC_LINE = re.compile(r"^- \*\*Topic-focused \(one of (?P<flags>[^)]*)\)\.\*\*", re.M)
CONTEXT_RULE = (
    "Text after the command that is not a flag is context (for example "
    "`Context: review the project '<slug>'.`): it may focus the overview but never changes "
    "the mode or the project."
)
NOTES_RULE = "together on ONE line directly under the title line"
TOP_RULE = "so the title and `**What it is:**` stay at the top"


def _fenced_blocks_after(text: str, heading: str) -> str:
    """Return the first ```markdown block that follows `heading`."""
    start = text.index(heading)
    match = re.search(r"```markdown\n(.*?)```", text[start:], re.S)
    assert match, f"no markdown template after {heading!r}"
    return match.group(1)


def caller_contract_findings(text: str) -> list[str]:
    """Every way the core breaks what the review caller relies on; empty when it holds."""
    findings = []
    if "**Default (no flag).**" not in text:
        findings.append("bare mode: no '**Default (no flag).**' entry")
    topic = TOPIC_LINE.search(text)
    listed = set(re.findall(r"`(--[a-z][a-z-]*)`", topic.group("flags"))) if topic else set()
    for flag in CALLER_FLAGS:
        if flag not in listed:
            findings.append(f"{flag}: not in the topic-flag list")
        if not re.search(rf"^- \*\*`{re.escape(flag)}`\*\*", text, re.M):
            findings.append(f"{flag}: no per-topic bullet")
    if CONTEXT_RULE not in text:
        findings.append("context rule: non-flag text no longer only focuses the overview")
    if NOTES_RULE not in text or TOP_RULE not in text:
        findings.append("header rule: the notes line no longer keeps the title and What it is on top")
    try:
        default = [l for l in _fenced_blocks_after(text, "## Default output format").splitlines() if l.strip()]
        topic_t = [l for l in _fenced_blocks_after(text, "### Shared three-part shape").splitlines() if l.strip()]
    except (AssertionError, ValueError) as exc:
        findings.append(f"header rule: template missing ({exc})")
        return findings
    if default[:1] != ["# <project> — at a glance"] or not default[1:2] or not default[1].startswith("**What it is:**"):
        findings.append("header rule: the default template no longer opens with the title then **What it is:**")
    if topic_t[:1] != ["# <project> — <topic>"]:
        findings.append("header rule: the topic template no longer opens with its title line")
    return findings


def test_core_keeps_the_review_callers_modes_context_and_header_rule() -> None:
    # Arrange
    core = CORE.read_text(encoding="utf-8")

    # Act
    findings = caller_contract_findings(core)

    # Assert
    assert findings == []


def _drop_flag(core: str, flag: str) -> str:
    return core.replace(f" / `{flag}`", "")


MUTATIONS = {
    "goal-dropped-from-list": lambda c: _drop_flag(c, "--goal"),
    "outstanding-dropped-from-list": lambda c: _drop_flag(c, "--outstanding"),
    "cut-bullet-dropped": lambda c: "\n".join(
        l for l in c.splitlines() if not l.startswith("- **`--cut`**")),
    "bare-mode-dropped": lambda c: c.replace("**Default (no flag).**", "**Default.**"),
    "context-changes-mode": lambda c: c.replace(
        "never changes the mode or the project", "may change the mode"),
    "notes-line-above-title": lambda c: c.replace(NOTES_RULE, "together on ONE line above the title line"),
    "what-it-is-moved-down": lambda c: c.replace(
        "# <project> — at a glance\n\n**What it is:** <one sentence — the elevator pitch from the plan>\n",
        "# <project> — at a glance\n\n## Status\n\n**What it is:** <one sentence — the elevator pitch from the plan>\n"),
    "topic-title-renamed": lambda c: c.replace("# <project> — <topic>", "## <topic> for <project>"),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_garbage_anchor_a_broken_caller_contract_fails(name: str) -> None:
    # Arrange
    core = CORE.read_text(encoding="utf-8")
    mutated = MUTATIONS[name](core)

    # Act
    findings = caller_contract_findings(mutated)

    # Assert
    assert mutated != core, f"mutation {name} changed nothing"
    assert findings, f"mutation {name} was not detected"
