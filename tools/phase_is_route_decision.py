"""Strict validator for the immutable Phase IS C2V route-decision input.

This module deliberately owns only C2V's closed route-decision record and its
authenticated GitHub REST reread. It neither resolves the route (C2A) nor
creates any Step-108P implementation input.
"""

from __future__ import annotations

import argparse
import datetime as datetime
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import parse_qs, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION = REPO_ROOT / "documentation/findings/phase-is-route-decision.json"
DEFAULT_SELECTOR = REPO_ROOT / "documentation/findings/phase-is-route-decision.selector"

SCHEMA = "skill-mesh/phase-is-route-decision/v1"
ISSUE = 153
C2_COMMENT_ID = 5457823134
C2_COMMENT_URL = "https://github.com/aberson/skill-mesh/issues/153#issuecomment-5457823134"
C2_COMMENT_CREATED_UTC = "2026-08-28T21:13:52.0000000Z"
C2_COMMENT_BODY_SHA256 = "1c0739a1e9038f8438cc94432678e95c4d8073a6d1afdc640356fa76820b17c1"
C2_SELECTED_ROUTE = "core-uat-mode"
C2_PLAN_AMENDMENT_REQUIRED = False
ROUTE_HEADER = "PHASE_IS_ROUTE_RECORD_V1"
ROUTES = ("core-uat-mode", "operator-subsection-override")
ROUTE_MARKERS = {f"PHASE_IS_ROUTE={route}": route for route in ROUTES}
REQUIRED_KEYS = frozenset(
    {
        "comment_body_sha256",
        "comment_created_utc",
        "comment_id",
        "comment_url",
        "issue",
        "plan_amendment_required",
        "schema",
        "selected_route",
        "verified_utc",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ROUND_TRIP_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{7}Z$")
GITHUB_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
TOKEN_RE = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]")


class RouteDecisionError(ValueError):
    """A C2V validation failure that must stop the route pipeline."""


@dataclass(frozen=True)
class RouteEnumeration:
    """The complete, duplicate-free result of one manual REST pagination pass."""

    comments: Mapping[int, Mapping[str, Any]]
    pages: int
    selected: Mapping[str, Any]


@dataclass(frozen=True)
class StagedRouteDecision:
    """The C2V decision decoded directly from its staged Git blob objects."""

    decision: Mapping[str, Any]
    decision_blob: str
    selector_blob: str


def _duplicate_key_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RouteDecisionError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(token: str) -> None:
    raise RouteDecisionError(f"non-finite JSON token is forbidden: {token}")


def canonical_decision_bytes(decision: Mapping[str, Any]) -> bytes:
    """Serialize a validated decision as C2V's one canonical byte sequence."""
    return (
        json.dumps(
            decision,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _parse_round_trip_utc(value: Any, field: str) -> datetime.datetime:
    if not isinstance(value, str) or not ROUND_TRIP_UTC_RE.fullmatch(value):
        raise RouteDecisionError(f"{field} must be a UTC round-trip ('o') timestamp")
    try:
        return datetime.datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=datetime.timezone.utc
        )
    except ValueError as error:
        raise RouteDecisionError(f"{field} is not a valid UTC timestamp") from error


def _parse_github_utc(value: Any) -> datetime.datetime:
    if not isinstance(value, str) or not GITHUB_UTC_RE.fullmatch(value):
        raise RouteDecisionError("GitHub comment created_at is not a UTC timestamp")
    try:
        return datetime.datetime.fromisoformat(value[:-1] + "+00:00").astimezone(
            datetime.timezone.utc
        )
    except ValueError as error:
        raise RouteDecisionError("GitHub comment created_at is not parseable") from error


def _format_round_trip_utc(value: datetime.datetime) -> str:
    utc = value.astimezone(datetime.timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S") + f".{utc.microsecond:06d}0Z"


def validate_decision(decision: Any) -> Mapping[str, Any]:
    """Validate the closed semantic schema before any route is consumed."""
    if not isinstance(decision, dict):
        raise RouteDecisionError("route decision must be a JSON object")
    actual_keys = frozenset(decision)
    if actual_keys != REQUIRED_KEYS:
        missing = sorted(REQUIRED_KEYS - actual_keys)
        extra = sorted(actual_keys - REQUIRED_KEYS)
        raise RouteDecisionError(
            f"route decision keys differ; missing={missing}, extra={extra}"
        )
    if decision["schema"] != SCHEMA:
        raise RouteDecisionError("route decision schema mismatch")
    if type(decision["issue"]) is not int or decision["issue"] != ISSUE:
        raise RouteDecisionError(f"issue must be integer {ISSUE}")
    if type(decision["comment_id"]) is not int or decision["comment_id"] <= 0:
        raise RouteDecisionError("comment_id must be a positive integer")
    if decision["comment_id"] != C2_COMMENT_ID:
        raise RouteDecisionError("comment_id does not bind C2's returned source comment ID")
    comment_url = decision["comment_url"]
    if not isinstance(comment_url, str) or not comment_url.isascii():
        raise RouteDecisionError("comment_url must be an ASCII HTTPS URL")
    parsed_url = urlparse(comment_url)
    if (
        parsed_url.scheme != "https"
        or not parsed_url.netloc
        or parsed_url.username is not None
        or parsed_url.password is not None
    ):
        raise RouteDecisionError("comment_url must be an absolute HTTPS URL")
    if comment_url != C2_COMMENT_URL:
        raise RouteDecisionError("comment_url does not bind C2's returned source comment URL")
    created = _parse_round_trip_utc(decision["comment_created_utc"], "comment_created_utc")
    if decision["comment_created_utc"] != C2_COMMENT_CREATED_UTC:
        raise RouteDecisionError("comment_created_utc does not bind C2's returned source timestamp")
    verified = _parse_round_trip_utc(decision["verified_utc"], "verified_utc")
    if verified < created:
        raise RouteDecisionError("verified_utc predates comment_created_utc")
    body_hash = decision["comment_body_sha256"]
    if not isinstance(body_hash, str) or not SHA256_RE.fullmatch(body_hash):
        raise RouteDecisionError("comment_body_sha256 must be 64 lowercase hexadecimal characters")
    if body_hash != C2_COMMENT_BODY_SHA256:
        raise RouteDecisionError("comment_body_sha256 does not bind C2's returned source body")
    selected_route = decision["selected_route"]
    if not isinstance(selected_route, str) or selected_route not in ROUTES:
        raise RouteDecisionError("selected_route is not one of the two closed route enums")
    if selected_route != C2_SELECTED_ROUTE:
        raise RouteDecisionError("selected_route does not bind C2's selected route")
    expected_amendment = selected_route == "operator-subsection-override"
    if type(decision["plan_amendment_required"]) is not bool:
        raise RouteDecisionError("plan_amendment_required must be a JSON Boolean")
    if decision["plan_amendment_required"] is not expected_amendment:
        raise RouteDecisionError("plan_amendment_required disagrees with selected_route")
    if decision["plan_amendment_required"] is not C2_PLAN_AMENDMENT_REQUIRED:
        raise RouteDecisionError("plan_amendment_required does not bind C2's selected route")
    return decision


def decode_decision_bytes(raw: bytes) -> Mapping[str, Any]:
    """Strictly decode and canonicalize the committed decision JSON bytes."""
    if not isinstance(raw, bytes):
        raise RouteDecisionError("decision input must be bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RouteDecisionError("decision JSON must not carry a UTF-8 BOM")
    if b"\r" in raw:
        raise RouteDecisionError("decision JSON must be LF-only")
    if raw.count(b"\n") != 1 or not raw.endswith(b"\n"):
        raise RouteDecisionError("decision JSON must have exactly one terminal LF")
    try:
        text = raw[:-1].decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        raise RouteDecisionError("decision JSON is not strict UTF-8") from error
    decoder = json.JSONDecoder(
        object_pairs_hook=_duplicate_key_object,
        parse_constant=_reject_json_constant,
    )
    try:
        decision, end = decoder.raw_decode(text)
    except (json.JSONDecodeError, RouteDecisionError) as error:
        raise RouteDecisionError(f"decision JSON is malformed: {error}") from error
    if end != len(text):
        raise RouteDecisionError("decision JSON carries trailing tokens")
    validate_decision(decision)
    if canonical_decision_bytes(decision) != raw:
        raise RouteDecisionError("decision JSON is not sorted, compact canonical bytes")
    return decision


def validate_selector_bytes(raw: bytes, selected_route: str) -> None:
    """Require the exact route selector bytes and agreement with the JSON enum."""
    if selected_route not in ROUTES:
        raise RouteDecisionError("selector cannot validate an unknown route")
    expected = selected_route.encode("utf-8") + b"\n"
    if raw != expected:
        raise RouteDecisionError("selector must be exact UTF-8 route bytes plus one LF")


def load_route_decision(
    decision_path: Path = DEFAULT_DECISION,
    selector_path: Path = DEFAULT_SELECTOR,
) -> Mapping[str, Any]:
    decision = decode_decision_bytes(decision_path.read_bytes())
    validate_selector_bytes(selector_path.read_bytes(), decision["selected_route"])
    return decision


def _git_index_blob(path: Path) -> tuple[str, bytes]:
    """Read one tracked stage-0 blob directly from Git, never from the worktree."""
    try:
        relative_path = path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError as error:
        raise RouteDecisionError("staged route artifact must remain under the repository root") from error
    listing = subprocess.run(
        ["git", "ls-files", "-s", "--", relative_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if listing.returncode != 0:
        message = listing.stderr.decode("utf-8", "replace").strip()
        raise RouteDecisionError(f"cannot inspect staged Git blob for {relative_path}: {message}")
    entries = listing.stdout.decode("utf-8", "strict").splitlines()
    if len(entries) != 1:
        raise RouteDecisionError(f"staged Git index does not have exactly one entry for {relative_path}")
    fields = entries[0].split(maxsplit=3)
    if (
        len(fields) != 4
        or fields[2] != "0"
        or fields[3] != relative_path
        or not re.fullmatch(r"[0-9a-f]{40,64}", fields[1])
    ):
        raise RouteDecisionError(f"staged Git index entry is malformed for {relative_path}")
    blob = fields[1]
    object_read = subprocess.run(
        ["git", "cat-file", "blob", blob],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    index_read = subprocess.run(
        ["git", "show", f":{relative_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if object_read.returncode != 0 or index_read.returncode != 0:
        raise RouteDecisionError(f"cannot read staged Git blob for {relative_path}")
    if object_read.stdout != index_read.stdout:
        raise RouteDecisionError(f"staged Git blob/object bytes differ for {relative_path}")
    return blob, object_read.stdout


def load_staged_route_decision(
    decision_path: Path = DEFAULT_DECISION,
    selector_path: Path = DEFAULT_SELECTOR,
) -> StagedRouteDecision:
    """Validate the exact staged artifacts that will become the C2V commit."""
    decision_blob, decision_raw = _git_index_blob(decision_path)
    selector_blob, selector_raw = _git_index_blob(selector_path)
    decision = decode_decision_bytes(decision_raw)
    validate_selector_bytes(selector_raw, decision["selected_route"])
    return StagedRouteDecision(
        decision=decision,
        decision_blob=decision_blob,
        selector_blob=selector_blob,
    )


def _parse_link_header(value: str) -> list[tuple[str, Mapping[str, str]]]:
    """Parse Link strictly enough to fail closed on unexpected pagination syntax."""
    if not isinstance(value, str) or not value:
        raise RouteDecisionError("Link header is empty or not text")
    position = 0
    entries: list[tuple[str, Mapping[str, str]]] = []
    while position < len(value):
        while position < len(value) and value[position] in " \t":
            position += 1
        if position >= len(value) or value[position] != "<":
            raise RouteDecisionError("Link header lacks an opening URL delimiter")
        close = value.find(">", position + 1)
        if close <= position + 1:
            raise RouteDecisionError("Link header has an empty or unterminated URL")
        url = value[position + 1 : close]
        if any(character in url for character in "<> \t\r\n"):
            raise RouteDecisionError("Link header URL is malformed")
        position = close + 1
        params: dict[str, str] = {}
        while True:
            while position < len(value) and value[position] in " \t":
                position += 1
            if position >= len(value) or value[position] == ",":
                break
            if value[position] != ";":
                raise RouteDecisionError("Link header parameter separator is malformed")
            position += 1
            while position < len(value) and value[position] in " \t":
                position += 1
            start = position
            while position < len(value) and TOKEN_RE.fullmatch(value[position]):
                position += 1
            name = value[start:position].lower()
            if not name:
                raise RouteDecisionError("Link header parameter name is missing")
            while position < len(value) and value[position] in " \t":
                position += 1
            if position >= len(value) or value[position] != "=":
                raise RouteDecisionError("Link header parameter value is missing")
            position += 1
            while position < len(value) and value[position] in " \t":
                position += 1
            if position < len(value) and value[position] == '"':
                position += 1
                start = position
                while position < len(value) and value[position] != '"':
                    if value[position] in "\r\n":
                        raise RouteDecisionError("quoted Link parameter is malformed")
                    position += 1
                if position >= len(value):
                    raise RouteDecisionError("quoted Link parameter is unterminated")
                parameter_value = value[start:position]
                position += 1
            else:
                start = position
                while position < len(value) and value[position] not in " \t;,":
                    position += 1
                parameter_value = value[start:position]
                if not parameter_value:
                    raise RouteDecisionError("Link header parameter is empty")
            if name in params:
                raise RouteDecisionError(f"duplicate Link parameter: {name}")
            params[name] = parameter_value
        entries.append((url, params))
        if position >= len(value):
            break
        position += 1
        if position >= len(value):
            raise RouteDecisionError("Link header has a trailing comma")
    return entries


def _next_link(headers: Mapping[str, list[str]]) -> str | None:
    next_urls: list[str] = []
    for name, values in headers.items():
        if name.lower() != "link":
            continue
        for value in values:
            for url, params in _parse_link_header(value):
                if "next" in params.get("rel", "").split():
                    next_urls.append(url)
    if len(next_urls) > 1 or len(set(next_urls)) != len(next_urls):
        raise RouteDecisionError("Link headers name more than one rel=next URL")
    return next_urls[0] if next_urls else None


def _validate_next_url(url: str, owner: str, repository: str, issue: int) -> None:
    parsed = urlparse(url)
    expected_path = f"/repos/{owner}/{repository}/issues/{issue}/comments"
    if (
        parsed.scheme != "https"
        or parsed.netloc != "api.github.com"
        or parsed.path != expected_path
        or parsed.fragment
    ):
        raise RouteDecisionError("rel=next Link leaves the expected GitHub comments endpoint")
    try:
        query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError as error:
        raise RouteDecisionError("rel=next Link query is malformed") from error
    if set(query) != {"page", "per_page"} or query["per_page"] != ["100"]:
        raise RouteDecisionError("rel=next Link does not preserve the required per_page=100")
    if len(query["page"]) != 1 or not query["page"][0].isdigit() or int(query["page"][0]) < 1:
        raise RouteDecisionError("rel=next Link has an invalid page number")


def _parse_http_response(raw: bytes) -> tuple[dict[str, list[str]], Any]:
    if b"\r\n\r\n" in raw:
        header_bytes, body = raw.split(b"\r\n\r\n", 1)
    elif b"\n\n" in raw:
        header_bytes, body = raw.split(b"\n\n", 1)
    else:
        raise RouteDecisionError("GitHub response has no HTTP header/body separator")
    # `gh api --include` currently emits an LF after its HTTP status line and
    # CRLF after subsequent headers on Windows.  Accept only those two normal
    # line endings, including that mixed form; a bare CR stays in a line and
    # fails the strict status/header checks below.
    lines = [line.decode("iso-8859-1") for line in re.split(br"\r?\n", header_bytes)]
    if not lines or not re.fullmatch(r"HTTP/\d(?:\.\d)?\s+[1-5]\d\d\s+.*", lines[0]):
        raise RouteDecisionError("GitHub response has a malformed HTTP status line")
    status = int(lines[0].split()[1])
    if not 200 <= status < 300:
        raise RouteDecisionError(f"GitHub REST status is {status}")
    headers: dict[str, list[str]] = {}
    for line in lines[1:]:
        if not line or line[0] in " \t" or ":" not in line:
            raise RouteDecisionError("GitHub response has a malformed HTTP header")
        name, value = line.split(":", 1)
        if not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name):
            raise RouteDecisionError("GitHub response has an invalid HTTP header name")
        headers.setdefault(name.lower(), []).append(value.strip())
    try:
        payload = json.loads(
            body.decode("utf-8", "strict"),
            object_pairs_hook=_duplicate_key_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RouteDecisionError) as error:
        raise RouteDecisionError(f"GitHub response is not strict JSON: {error}") from error
    return headers, payload


def _gh_fetch(endpoint: str) -> tuple[dict[str, list[str]], Any]:
    process = subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "GET",
            "--include",
            "--header",
            "Accept: application/vnd.github+json",
            endpoint,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        message = process.stderr.decode("utf-8", "replace").strip()
        raise RouteDecisionError(f"authenticated GitHub REST request failed: {message}")
    return _parse_http_response(process.stdout)


Fetch = Callable[[str], tuple[Mapping[str, list[str]], Any]]


def enumerate_issue_comments(
    fetch: Fetch,
    *,
    owner: str = "aberson",
    repository: str = "skill-mesh",
    issue: int = ISSUE,
) -> RouteEnumeration:
    """Follow every explicit rel=next link and select the maximal route marker."""
    initial = f"/repos/{owner}/{repository}/issues/{issue}/comments?per_page=100&page=1"
    endpoint = initial
    visited = {"https://api.github.com" + initial}
    comments: dict[int, Mapping[str, Any]] = {}
    pages = 0
    while True:
        headers, payload = fetch(endpoint)
        pages += 1
        if not isinstance(payload, list):
            raise RouteDecisionError("GitHub comments response is not an array")
        for record in payload:
            if not isinstance(record, dict):
                raise RouteDecisionError("GitHub comments response carries a non-object record")
            comment_id = record.get("id")
            if type(comment_id) is not int or comment_id <= 0:
                raise RouteDecisionError("GitHub comment ID is not a positive numeric integer")
            if comment_id in comments:
                raise RouteDecisionError(f"duplicate GitHub comment ID: {comment_id}")
            comments[comment_id] = record
        next_url = _next_link(headers)
        if next_url is None:
            break
        _validate_next_url(next_url, owner, repository, issue)
        if next_url in visited:
            raise RouteDecisionError(f"repeated GitHub page URL: {next_url}")
        visited.add(next_url)
        endpoint = next_url
    candidates: list[tuple[datetime.datetime, int, Mapping[str, Any]]] = []
    for record in comments.values():
        body = record.get("body")
        if isinstance(body, str) and body.split("\n", 1)[0] == ROUTE_HEADER:
            candidates.append((_parse_github_utc(record.get("created_at")), record["id"], record))
    if not candidates:
        raise RouteDecisionError("no exact-header Phase IS route record exists")
    selected = max(candidates, key=lambda candidate: (candidate[0], candidate[1]))[2]
    return RouteEnumeration(comments=comments, pages=pages, selected=selected)


def _validate_remote_selected(
    record: Mapping[str, Any], decision: Mapping[str, Any]
) -> None:
    required = ("id", "html_url", "created_at", "body")
    if any(key not in record for key in required):
        raise RouteDecisionError("GitHub route record is missing a required field")
    if type(record["id"]) is not int or record["id"] <= 0:
        raise RouteDecisionError("GitHub route record has an invalid ID")
    if record["id"] != decision["comment_id"]:
        raise RouteDecisionError("selected GitHub comment ID differs from the C2V record")
    if record["html_url"] != decision["comment_url"]:
        raise RouteDecisionError("selected GitHub comment URL differs from the C2V record")
    if _format_round_trip_utc(_parse_github_utc(record["created_at"])) != decision[
        "comment_created_utc"
    ]:
        raise RouteDecisionError("selected GitHub timestamp differs from the C2V record")
    if not isinstance(record["body"], str):
        raise RouteDecisionError("selected GitHub route body is not text")
    try:
        raw_body = record["body"].encode("utf-8", "strict")
    except UnicodeEncodeError as error:
        raise RouteDecisionError("selected GitHub route body is not strict UTF-8") from error
    if (
        raw_body.count(b"\n") != 1
        or b"\r" in raw_body
        or raw_body.endswith(b"\n")
    ):
        raise RouteDecisionError("selected GitHub route body has invalid LF/CR shape")
    lines = record["body"].split("\n")
    route_lines = [line for line in lines if line.startswith("PHASE_IS_ROUTE=")]
    unknown_route_lines = [line for line in route_lines if line not in ROUTE_MARKERS]
    expected_marker = f"PHASE_IS_ROUTE={decision['selected_route']}"
    if (
        lines != [ROUTE_HEADER, expected_marker]
        or sum(line == ROUTE_HEADER for line in lines) != 1
        or route_lines != [expected_marker]
        or unknown_route_lines
    ):
        raise RouteDecisionError("selected GitHub route body has invalid marker grammar")
    body_hash = hashlib.sha256(raw_body).hexdigest()
    if body_hash != decision["comment_body_sha256"]:
        raise RouteDecisionError("selected GitHub route body hash differs from the C2V record")


def validate_remote_route(
    decision: Mapping[str, Any], fetch: Fetch = _gh_fetch
) -> RouteEnumeration:
    """Perform C2V's complete paginated selection and separate direct reread."""
    validate_decision(decision)
    enumeration = enumerate_issue_comments(fetch, issue=decision["issue"])
    _validate_remote_selected(enumeration.selected, decision)
    _, reread = fetch(
        f"/repos/aberson/skill-mesh/issues/comments/{decision['comment_id']}"
    )
    if not isinstance(reread, dict):
        raise RouteDecisionError("GitHub direct route reread is not an object")
    _validate_remote_selected(reread, decision)
    for field in ("id", "html_url", "created_at", "body"):
        if reread[field] != enumeration.selected[field]:
            raise RouteDecisionError("GitHub direct route reread differs from pagination")
    return enumeration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Phase IS C2V route decision and optional remote reread."
    )
    parser.add_argument("--decision", type=Path, default=DEFAULT_DECISION)
    parser.add_argument("--selector", type=Path, default=DEFAULT_SELECTOR)
    parser.add_argument(
        "--check-staged",
        action="store_true",
        help="validate the exact stage-0 Git blobs instead of mutable worktree bytes",
    )
    parser.add_argument(
        "--check-remote",
        action="store_true",
        help="manually follow authenticated GitHub REST Link pagination and reread the source comment",
    )
    args = parser.parse_args(argv)
    try:
        staged = None
        if args.check_staged:
            staged = load_staged_route_decision(args.decision, args.selector)
            decision = staged.decision
        else:
            decision = load_route_decision(args.decision, args.selector)
        print(
            "local route decision: "
            f"issue={decision['issue']} comment_id={decision['comment_id']} "
            f"route={decision['selected_route']}"
        )
        if staged is not None:
            print(
                "staged route decision: "
                f"decision_blob={staged.decision_blob} selector_blob={staged.selector_blob}"
            )
        if args.check_remote:
            enumeration = validate_remote_route(decision)
            print(
                "remote route decision: "
                f"pages={enumeration.pages} comments={len(enumeration.comments)} "
                f"selected_id={enumeration.selected['id']} reread=match"
            )
    except (OSError, RouteDecisionError) as error:
        print(f"C2V validation failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
