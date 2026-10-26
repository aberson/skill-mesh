"""Document output contract (v2.0.1): operator-facing documents are saved as files under
docs/<skill>/ in the project repository on every provider, never published as a hosted
Claude Artifact and never defaulted to documentation/<slug>-proposal.html.

Owner: _shared/document-output.md. These assertions pin the two consuming cores and their
provider wrappers so a later edit cannot silently reintroduce either retired form.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "_shared" / "document-output.md"
CONSUMERS = ("plan-redline", "repo-update")
PROVIDERS = ("claude", "gpt", "codex")


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _consumer_files():
    for skill in CONSUMERS:
        yield f"skills/{skill}/core.md"
        for provider in PROVIDERS:
            yield f"skills/{skill}/providers/{provider}.md"


def test_contract_exists_and_names_both_consumers():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "docs/<skill-name>/" in text
    assert "Never publish, update, or mint a hosted Artifact" in text
    for skill in CONSUMERS:
        assert f"`{skill}`" in text, f"contract table lacks a row for {skill}"
    assert "docs/plan-redline/<plan-slug>-proposal.html" in text
    assert "docs/repo-update/<project-slug>-<phase-or-version>.html" in text


def test_every_consumer_file_cites_the_contract():
    for rel in _consumer_files():
        assert "_shared/document-output.md" in _read(rel), f"{rel} does not cite the contract"


def test_plan_redline_writes_proposal_under_docs_on_every_provider():
    for rel in ("skills/plan-redline/core.md", *(f"skills/plan-redline/providers/{p}.md" for p in PROVIDERS)):
        text = _read(rel)
        assert "docs/plan-redline/<plan-slug>-proposal.html" in text, rel
        assert "documentation/<plan-slug>-proposal.html" not in text.replace(
            "pre-v2.0.1 `documentation/<plan-slug>-proposal.html`", ""
        ), f"{rel} still defaults the proposal to documentation/"


def test_repo_update_writes_tour_under_docs_on_every_provider():
    core = _read("skills/repo-update/core.md")
    assert "docs/repo-update/<project-slug>-<phase-or-version>.html" in core
    assert "Tour: docs/repo-update/" in core
    assert "<Artifact URL>" not in core
    for p in PROVIDERS:
        text = _read(f"skills/repo-update/providers/{p}.md")
        assert "docs/repo-update/" in text or "document output contract path" in text, p


_PUBLISH_AS_ARTIFACT = re.compile(
    r"publish(?:ed|es)? (?:it |the \w+ )?(?:with|as|to) (?:the |a |an )?(?:native |private )?Artifact",
    re.IGNORECASE,
)


def test_no_consumer_instructs_publishing_a_hosted_artifact():
    """Every remaining mention of the Artifact tool in a consumer must be a prohibition
    (never / no / unavailable / retired), not an instruction to publish through it."""
    allowed = ("never", "no artifact tool", "no provider", "unavailable", "retired", "stale")
    for rel in _consumer_files():
        for n, line in enumerate(_read(rel).splitlines(), 1):
            stripped = line.replace("artifact-design", "")
            if "Artifact" not in stripped:
                continue
            low = stripped.lower()
            prohibited = re.search(r"\b(never|not|no)\b", low) is not None
            if _PUBLISH_AS_ARTIFACT.search(line) and not prohibited:
                raise AssertionError(f"{rel}:{n} instructs publishing as an Artifact: {line.strip()[:120]}")
            assert any(a in low for a in allowed), (
                f"{rel}:{n} mentions the Artifact tool without prohibiting it: {line.strip()[:140]}"
            )


def test_claude_wrappers_do_not_route_to_artifact_url_locators():
    for skill in CONSUMERS:
        text = _read(f"skills/{skill}/providers/claude.md")
        assert "Use its URL as the stable Proposal locator" not in text
        assert "pass the recorded Artifact URL" not in text
