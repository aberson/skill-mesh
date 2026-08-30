"""C2V byte/schema/remote-drift coverage for the Phase IS route decision."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools/phase_is_route_decision.py"
SPEC = importlib.util.spec_from_file_location("phase_is_route_decision", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
route = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = route
SPEC.loader.exec_module(route)

DECISION_PATH = REPO_ROOT / "documentation/findings/phase-is-route-decision.json"
SELECTOR_PATH = REPO_ROOT / "documentation/findings/phase-is-route-decision.selector"
SOURCE_ID = 5457823134
SOURCE_URL = "https://github.com/aberson/skill-mesh/issues/153#issuecomment-5457823134"
SOURCE_CREATED = "2026-08-28T21:13:52Z"
SOURCE_BODY = "PHASE_IS_ROUTE_RECORD_V1\nPHASE_IS_ROUTE=core-uat-mode"
SOURCE_SHA256 = "1c0739a1e9038f8438cc94432678e95c4d8073a6d1afdc640356fa76820b17c1"


def _decision():
    return copy.deepcopy(route.load_route_decision(DECISION_PATH, SELECTOR_PATH))


def _source_record(**changes):
    record = {
        "id": SOURCE_ID,
        "html_url": SOURCE_URL,
        "created_at": SOURCE_CREATED,
        "body": SOURCE_BODY,
    }
    record.update(changes)
    return record


def _fetcher(pages, reread=None):
    calls = []

    def fetch(endpoint):
        calls.append(endpoint)
        if endpoint in pages:
            return pages[endpoint]
        if endpoint == f"/repos/aberson/skill-mesh/issues/comments/{SOURCE_ID}":
            return {}, reread if reread is not None else _source_record()
        raise AssertionError(f"unexpected REST endpoint: {endpoint}")

    return fetch, calls


def _single_page(record=None, headers=None):
    endpoint = "/repos/aberson/skill-mesh/issues/153/comments?per_page=100&page=1"
    return {endpoint: (headers or {}, [record if record is not None else _source_record()])}


def test_committed_c2v_artifacts_bind_the_exact_operator_record():
    decision = _decision()
    assert decision["schema"] == route.SCHEMA
    assert decision["issue"] == 153
    assert decision["comment_id"] == SOURCE_ID
    assert decision["comment_url"] == SOURCE_URL
    assert decision["comment_created_utc"] == "2026-08-28T21:13:52.0000000Z"
    assert decision["comment_body_sha256"] == SOURCE_SHA256
    assert decision["selected_route"] == "core-uat-mode"
    assert decision["plan_amendment_required"] is False
    assert SELECTOR_PATH.read_bytes() == b"core-uat-mode\n"


def test_committed_json_is_exact_canonical_utf8_bytes():
    raw = DECISION_PATH.read_bytes()
    decision = _decision()
    assert raw == route.canonical_decision_bytes(decision)
    assert raw.endswith(b"\n")
    assert raw.count(b"\n") == 1
    assert b"\r" not in raw
    assert not raw.startswith(b"\xef\xbb\xbf")


def test_staged_loader_validates_the_exact_index_blobs_not_worktree_bytes(monkeypatch):
    if os.environ.get("SKILL_MESH_SOURCE_ROOT"):
        pytest.skip("normal-loader worktree-read proof runs only outside a git-less release stage")
    original_read_bytes = Path.read_bytes

    def reject_route_artifact_worktree_reads(path):
        if path in {DECISION_PATH, SELECTOR_PATH}:
            raise AssertionError("staged validation must not read mutable worktree artifact bytes")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", reject_route_artifact_worktree_reads)
    staged = route.load_staged_route_decision(DECISION_PATH, SELECTOR_PATH)
    assert staged.decision["comment_id"] == SOURCE_ID
    assert staged.decision["selected_route"] == "core-uat-mode"
    assert staged.decision_blob == subprocess.check_output(
        ["git", "rev-parse", f":{DECISION_PATH.relative_to(REPO_ROOT).as_posix()}"], text=True
    ).strip()
    assert staged.selector_blob == subprocess.check_output(
        ["git", "rev-parse", f":{SELECTOR_PATH.relative_to(REPO_ROOT).as_posix()}"], text=True
    ).strip()


def test_staged_release_loader_uses_explicit_source_authority_when_configured():
    """A release's git-less stage may use only its deliberately supplied root."""
    source_root = Path(os.environ.get("SKILL_MESH_SOURCE_ROOT", REPO_ROOT))
    staged = route.load_staged_release_route_decision(
        source_root, DECISION_PATH, SELECTOR_PATH
    )
    assert staged.decision["selected_route"] == "core-uat-mode"
    assert staged.decision_blob == subprocess.check_output(
        ["git", "-C", str(source_root), "rev-parse",
         f":{DECISION_PATH.relative_to(REPO_ROOT).as_posix()}"], text=True
    ).strip()


def _init_git_repo(root):
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=root, check=True)


def _release_authority_fixture(tmp_path, monkeypatch):
    source = tmp_path / "source"
    stage = tmp_path / "stage"
    decision_rel = Path("documentation/findings/phase-is-route-decision.json")
    selector_rel = Path("documentation/findings/phase-is-route-decision.selector")
    _init_git_repo(source)
    for root in (source, stage):
        (root / decision_rel).parent.mkdir(parents=True)
        (root / decision_rel).write_bytes(DECISION_PATH.read_bytes())
        (root / selector_rel).write_bytes(SELECTOR_PATH.read_bytes())
    subprocess.run(["git", "add", "-A"], cwd=source, check=True)
    monkeypatch.setattr(route, "REPO_ROOT", stage)
    return source, stage, stage / decision_rel, stage / selector_rel


def test_gitless_staged_release_loader_accepts_matching_explicit_authority(tmp_path, monkeypatch):
    source, stage, decision, selector = _release_authority_fixture(tmp_path, monkeypatch)
    assert not (stage / ".git").exists()
    staged = route.load_staged_release_route_decision(source, decision, selector)
    assert staged.decision["selected_route"] == "core-uat-mode"


@pytest.mark.parametrize("artifact", ("decision", "selector"))
def test_staged_release_loader_rejects_altered_stage_before_decode(tmp_path, monkeypatch, artifact):
    source, _, decision, selector = _release_authority_fixture(tmp_path, monkeypatch)
    target = decision if artifact == "decision" else selector
    target.write_bytes(b"tampered-before-decode\n")
    with pytest.raises(route.RouteDecisionError, match="do not match the source Git index"):
        route.load_staged_release_route_decision(source, decision, selector)


@pytest.mark.parametrize("kind", ("missing", "not-git", "partial", "unmerged"))
def test_staged_release_loader_rejects_missing_invalid_partial_or_unmerged_authority(
    tmp_path, monkeypatch, kind
):
    source, _, decision, selector = _release_authority_fixture(tmp_path, monkeypatch)
    if kind == "missing":
        authority = tmp_path / "missing"
    elif kind == "not-git":
        authority = tmp_path / "not-git"
        authority.mkdir()
    elif kind == "partial":
        selector_path = source / "documentation/findings/phase-is-route-decision.selector"
        subprocess.run(["git", "rm", "--cached", str(selector_path.relative_to(source))],
                       cwd=source, check=True)
        authority = source
    else:
        conflict = source / "unmerged-authority.txt"
        conflict.write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=source, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=source, check=True)
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=source,
                                capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "checkout", "-qb", "conflicting-authority"],
                       cwd=source, check=True)
        conflict.write_text("other\n", encoding="utf-8")
        subprocess.run(["git", "add", "unmerged-authority.txt"], cwd=source, check=True)
        subprocess.run(["git", "commit", "-qm", "other"], cwd=source, check=True)
        subprocess.run(["git", "checkout", "-q", branch], cwd=source, check=True)
        conflict.write_text("current\n", encoding="utf-8")
        subprocess.run(["git", "add", "unmerged-authority.txt"], cwd=source, check=True)
        subprocess.run(["git", "commit", "-qm", "current"], cwd=source, check=True)
        merge = subprocess.run(["git", "merge", "conflicting-authority"], cwd=source,
                               capture_output=True, text=True, check=False)
        assert merge.returncode != 0
        authority = source
    with pytest.raises(route.RouteDecisionError):
        route.load_staged_release_route_decision(authority, decision, selector)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.pop("issue"),
        lambda value: value.update(extra=True),
        lambda value: value.update(selected_Route=value.pop("selected_route")),
        lambda value: value.update(issue=True),
        lambda value: value.update(comment_id=SOURCE_ID + 1),
        lambda value: value.update(comment_url="https://github.com/aberson/skill-mesh/issues/153"),
        lambda value: value.update(comment_created_utc="2026-08-28T21:13:53.0000000Z"),
        lambda value: value.update(selected_route="different-route"),
        lambda value: value.update(plan_amendment_required=True),
        lambda value: value.update(comment_body_sha256="F" * 64),
        lambda value: value.update(comment_body_sha256="f" * 64),
        lambda value: value.update(comment_created_utc="2026-08-28T21:13:52Z"),
    ],
)
def test_strict_record_validation_rejects_schema_and_token_mutations(mutate):
    decision = _decision()
    mutate(decision)
    with pytest.raises(route.RouteDecisionError):
        route.decode_decision_bytes(route.canonical_decision_bytes(decision))


def test_strict_record_validation_rejects_duplicate_keys_and_noncanonical_bytes():
    with pytest.raises(route.RouteDecisionError, match="duplicate JSON key"):
        route.decode_decision_bytes(b'{"issue":153,"issue":153}\n')

    decision = _decision()
    reverse_order = dict(reversed(list(decision.items())))
    noncanonical = (
        json.dumps(reverse_order, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )
    with pytest.raises(route.RouteDecisionError, match="canonical"):
        route.decode_decision_bytes(noncanonical)


@pytest.mark.parametrize(
    "raw",
    [
        b"core-uat-mode",
        b"core-uat-mode\r\n",
        b"core-uat-mode\n\n",
        b"\xef\xbb\xbfcore-uat-mode\n",
        b"operator-subsection-override\n",
    ],
)
def test_selector_requires_exact_bytes_and_json_agreement(raw):
    with pytest.raises(route.RouteDecisionError):
        route.validate_selector_bytes(raw, "core-uat-mode")


def test_http_parser_accepts_ghs_mixed_status_and_header_line_endings():
    raw = b"HTTP/2.0 200 OK\nX-Request-Id: test\r\n\r\n[]"
    headers, payload = route._parse_http_response(raw)
    assert headers == {"x-request-id": ["test"]}
    assert payload == []


def test_local_binding_rejects_positive_but_wrong_comment_id_and_body_hash():
    decision = _decision()
    decision["comment_id"] = SOURCE_ID + 1
    with pytest.raises(route.RouteDecisionError, match="does not bind C2"):
        route.validate_decision(decision)

    decision = _decision()
    decision["comment_body_sha256"] = "f" * 64
    with pytest.raises(route.RouteDecisionError, match="does not bind C2"):
        route.validate_decision(decision)


def test_remote_validation_rejects_marker_grammar_and_direct_reread_drift():
    malformed = _source_record(body="PHASE_IS_ROUTE_RECORD_V1\nPHASE_IS_ROUTE=unknown")
    fetch, _ = _fetcher(_single_page(malformed))
    with pytest.raises(route.RouteDecisionError, match="marker grammar"):
        route.validate_remote_route(_decision(), fetch)

    reread = _source_record(created_at="2026-08-28T21:13:53Z")
    fetch, _ = _fetcher(_single_page(), reread=reread)
    with pytest.raises(route.RouteDecisionError, match="timestamp differs"):
        route.validate_remote_route(_decision(), fetch)


def test_manual_pagination_rejects_duplicate_ids_repeated_urls_and_malformed_links():
    first = "/repos/aberson/skill-mesh/issues/153/comments?per_page=100&page=1"
    second = "https://api.github.com/repos/aberson/skill-mesh/issues/153/comments?per_page=100&page=2"
    duplicate_pages = {
        first: ({"link": [f'<{second}>; rel="next"']}, [_source_record()]),
        second: ({}, [_source_record()]),
    }
    fetch, _ = _fetcher(duplicate_pages)
    with pytest.raises(route.RouteDecisionError, match="duplicate GitHub comment ID"):
        route.enumerate_issue_comments(fetch)

    repeated_pages = _single_page(
        headers={"link": [f'<https://api.github.com{first}>; rel="next"']}
    )
    fetch, _ = _fetcher(repeated_pages)
    with pytest.raises(route.RouteDecisionError, match="repeated GitHub page URL"):
        route.enumerate_issue_comments(fetch)

    malformed_pages = _single_page(headers={"link": ["not a Link header"]})
    fetch, _ = _fetcher(malformed_pages)
    with pytest.raises(route.RouteDecisionError, match="Link header"):
        route.enumerate_issue_comments(fetch)


def test_manual_pagination_follows_the_explicit_next_link_and_remote_rereads():
    first = "/repos/aberson/skill-mesh/issues/153/comments?per_page=100&page=1"
    second = "https://api.github.com/repos/aberson/skill-mesh/issues/153/comments?per_page=100&page=2"
    older = _source_record(
        id=SOURCE_ID - 1,
        html_url="https://github.com/aberson/skill-mesh/issues/153#issuecomment-5457823133",
        created_at="2026-08-28T21:13:51Z",
    )
    pages = {
        first: ({"link": [f'<{second}>; rel="next"']}, [older]),
        second: ({}, [_source_record()]),
    }
    fetch, calls = _fetcher(pages)
    result = route.validate_remote_route(_decision(), fetch)
    assert result.pages == 2
    assert set(result.comments) == {SOURCE_ID - 1, SOURCE_ID}
    assert calls == [first, second, f"/repos/aberson/skill-mesh/issues/comments/{SOURCE_ID}"]
