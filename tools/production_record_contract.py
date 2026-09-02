"""Pure Phase PROD declaration grammar and consistency checks.

This module deliberately does not read paths, run Git, inspect a profile, or
authenticate declared bytes.  Callers provide every declaration and schema.
"""
from __future__ import annotations

from datetime import datetime
import json
import re
import tomllib
from typing import Any


SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")
OID = re.compile(r"\A[0-9a-f]{40}\Z")
BUNDLE_ID = re.compile(r"\Aprod-(\d{8}T\d{6}Z)-([0-9a-f]{12})\Z")
SLUG = re.compile(r"\A[a-z][a-z0-9_-]*\Z")
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
EXPECTED_OWNERS = {
    "b2_project_goblin": ("b2_project_goblin",), "changed-check": ("changed-check",),
    "citation-needed": ("citation-needed",), "coding-root": ("dev-observatory", "switchboard"),
    "find-again": ("find-again",), "heads-up": ("heads-up",), "measure-twice": ("measure-twice",),
    "mesh-lens": ("mesh-lens",), "on-brand": ("on-brand",), "paper-trail": ("paper-trail",),
    "same-page": ("same-page",), "skill-mesh": ("skill-mesh",), "tripwire": ("tripwire",),
    "utility-project-standard": ("utility-project-standard",),
}
ACTION_ORDER = ("install", "inspect", "environment", "fresh-process-smoke", "rollback")


class ContractError(ValueError):
    """A deterministic, non-authoritative declaration error."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("DUPLICATE_JSON_MEMBER", key)
        result[key] = value
    return result


def parse_json(raw: bytes | str, label: str = "JSON") -> Any:
    """Parse a caller-supplied JSON declaration, rejecting every duplicate key."""
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if not isinstance(text, str):
            raise TypeError("not text")
        return json.loads(text, object_pairs_hook=_pairs)
    except ContractError:
        raise
    except (UnicodeDecodeError, TypeError, json.JSONDecodeError) as exc:
        raise ContractError("MALFORMED_JSON", label) from exc


def _jsonschema() -> Any:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise RuntimeError(
            "jsonschema is required when production declaration schema validation is called; "
            "install it with `pip install jsonschema` (see CLAUDE.md)."
        ) from exc
    return Draft202012Validator, FormatChecker


def validate_schema(schema: Any, declaration: Any, label: str = "declaration") -> Any:
    """Meta-validate and validate caller-supplied values using Draft 2020-12."""
    validator_type, checker_type = _jsonschema()
    try:
        validator_type.check_schema(schema)
    except Exception as exc:
        raise ContractError("INVALID_SCHEMA", label) from exc
    errors = sorted(validator_type(schema, format_checker=checker_type()).iter_errors(declaration), key=str)
    if errors:
        raise ContractError("SCHEMA_INVALID", f"{label}: {errors[0].message}")
    return declaration


def parse_registry(raw: bytes | str) -> list[dict[str, Any]]:
    """Parse only the real registry's singular repeated ``[[project]]`` shape."""
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        data = tomllib.loads(text)
    except (UnicodeDecodeError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise ContractError("MALFORMED_REGISTRY", "TOML") from exc
    projects = data.get("project")
    if set(data) != {"project"} or not isinstance(projects, list):
        raise ContractError("REGISTRY_SHAPE", "expected singular [[project]] records")
    if any(not isinstance(row, dict) for row in projects):
        raise ContractError("REGISTRY_SHAPE", "project record")
    return projects


def _path(value: Any, *, absolute: bool) -> str:
    if not isinstance(value, str) or not value or any(ord(ch) < 32 for ch in value):
        raise ContractError("LEXICAL_PATH", "empty or control")
    has_slash = "/" in value
    has_backslash = "\\" in value
    if (has_slash and has_backslash) or "//" in value or "\\\\" in value:
        raise ContractError("LEXICAL_PATH", "mixed or doubled separator")
    if not absolute and has_backslash:
        raise ContractError("LEXICAL_PATH", "relative path separator")
    canonical = value.replace("\\", "/")
    if ".." in canonical.split("/") or "/./" in f"/{canonical}/":
        raise ContractError("LEXICAL_PATH", "traversal")
    if absolute:
        if not re.fullmatch(r"[A-Za-z]:/[A-Za-z0-9._/-]+", canonical):
            raise ContractError("LEXICAL_PATH", "absolute Windows path")
        parts = canonical[3:].split("/")
    else:
        if canonical.startswith("/") or ":" in canonical:
            raise ContractError("LEXICAL_PATH", "relative path")
        parts = canonical.split("/")
    for part in parts:
        if not part or part.endswith((".", " ")) or part.split(".")[0].casefold() in RESERVED:
            raise ContractError("LEXICAL_PATH", "Windows alias")
    return canonical.casefold()

def _github_remote(value: Any) -> str:
    match = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?", value if isinstance(value, str) else "")
    if not match:
        raise ContractError("SOURCE_REMOTE_DRIFT", "GitHub remote")
    return f"github.com/{match.group(1).casefold()}/{match.group(2).casefold()}"


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _same(left: str, right: str) -> bool:
    return left == right


def _descendant(child: str, parent: str) -> bool:
    """Return whether canonical ``child`` sits strictly below canonical ``parent``."""
    return child.startswith(parent + "/")


def _overlap(left: str, right: str) -> bool:
    """Lexical overlap with a separator boundary; ``foo`` and ``foobar`` differ."""
    return _same(left, right) or _descendant(left, right) or _descendant(right, left)


def _root_graph(
    roles: dict[str, str | None],
    *,
    aliases: frozenset[frozenset[str]] = frozenset(),
    containments: frozenset[frozenset[str]] = frozenset(),
) -> None:
    """Default-deny supplied-string root overlap, except declared role relationships.

    Equal values first collapse into an explicitly permitted alias group.  Every
    remaining ancestor/descendant relationship must be a declared containment.
    This deliberately knows nothing about the filesystem or active state.
    """
    groups: dict[str, list[str]] = {}
    for role, path in roles.items():
        if path is not None:
            groups.setdefault(path, []).append(role)
    collapsed = list(groups.items())
    for _, names in collapsed:
        for index, left in enumerate(names):
            for right in names[index + 1:]:
                if frozenset((left, right)) not in aliases:
                    raise ContractError("ROOT_COLLAPSE", f"{left}={right}")
    for index, (left_path, left_names) in enumerate(collapsed):
        for right_path, right_names in collapsed[index + 1:]:
            if not _overlap(left_path, right_path):
                continue
            if not any(
                frozenset((left, right)) in containments
                for left in left_names for right in right_names
            ):
                raise ContractError("ROOT_COLLAPSE", f"{left_names[0]}~{right_names[0]}")


def _environment_roots(environment: dict[str, Any], *, nullable: bool) -> tuple[str | None, str | None]:
    utility = environment["DEV_UTILITIES_ROOT"]
    workspace = environment["DEV_WORKSPACE_ROOT"]
    if nullable:
        utility_path = None if utility is None else _path(utility, absolute=True)
        workspace_path = None if workspace is None else _path(workspace, absolute=True)
    else:
        utility_path = _path(utility, absolute=True)
        workspace_path = _path(workspace, absolute=True)
    return utility_path, workspace_path

def _timestamp(value: Any) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value):
        raise ContractError("GRAMMAR_TIMESTAMP", "UTC RFC3339 seconds")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ContractError("GRAMMAR_TIMESTAMP", "impossible timestamp") from exc


def _bundle_id(value: Any) -> tuple[str, str]:
    match = BUNDLE_ID.fullmatch(value if isinstance(value, str) else "")
    if not match:
        raise ContractError("GRAMMAR_BUNDLE_ID", "bundle ID")
    try:
        datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ")
    except ValueError as exc:
        raise ContractError("GRAMMAR_BUNDLE_ID", "impossible timestamp") from exc
    return match.group(1), match.group(2)


def _unique(values: list[str], code: str) -> None:
    if len(values) != len(set(values)):
        raise ContractError(code)


def _sources(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    source_rows = policy["repository_sources"]
    owners = [row["owner_slug"] for row in source_rows]
    _unique(owners, "SOURCE_OWNER_DUPLICATE")
    if tuple(owners) != tuple(EXPECTED_OWNERS):
        raise ContractError("SOURCE_ORDER_DRIFT")
    sources = {row["owner_slug"]: row for row in source_rows}
    if set(sources) != set(EXPECTED_OWNERS) or len(sources) != 14:
        raise ContractError("SOURCE_ALLOWLIST", "exact release-1 owner set")
    _unique([project for row in source_rows for project in row["project_slugs"]], "SOURCE_PROJECT_DUPLICATE")
    _unique([row["checkout_relative_path"].casefold() for row in source_rows], "SOURCE_CHECKOUT_DUPLICATE")
    all_projects: list[str] = []
    checkouts: list[str] = []
    for owner, expected in EXPECTED_OWNERS.items():
        row = sources[owner]
        if tuple(row["project_slugs"]) != expected:
            raise ContractError("SOURCE_PROJECT_SHARING", owner)
        if row["allowed_upstream_ref"] != ("origin/master" if owner == "measure-twice" else "origin/main"):
            raise ContractError("SOURCE_REF_DRIFT", owner)
        expected_checkout = "workspace" if owner == "coding-root" else f"workspace/{owner}"
        if _path(row["checkout_relative_path"], absolute=False) != expected_checkout:
            raise ContractError("SOURCE_CHECKOUT_DRIFT", owner)
        if row["canonical_remote_url"] != f"https://github.com/aberson/{owner}.git":
            raise ContractError("SOURCE_REMOTE_DRIFT", owner)
        checkouts.append(row["checkout_relative_path"].casefold())
        all_projects.extend(row["project_slugs"])
    _unique(checkouts, "SOURCE_CHECKOUT_DUPLICATE")
    _unique(all_projects, "SOURCE_PROJECT_DUPLICATE")
    checkout_roles = {"workspace": "workspace"}
    checkout_roles.update({f"checkout:{owner}": _path(row["checkout_relative_path"], absolute=False) for owner, row in sources.items()})
    _root_graph(
        checkout_roles,
        aliases=frozenset((frozenset(("workspace", "checkout:coding-root")),)),
        containments=frozenset(frozenset(("workspace", f"checkout:{owner}")) for owner in sources if owner != "coding-root"),
    )
    return sources


def check_policy(policy_raw: bytes | str, registry_raw: bytes | str, schema: Any) -> dict[str, Any]:
    """Check policy membership and declarations; does not inspect any repository."""
    policy = validate_schema(schema, parse_json(policy_raw, "policy"), "policy")
    if policy["registry_categories"] != ["utility"]:
        raise ContractError("REGISTRY_CATEGORY_DRIFT")
    sources = _sources(policy)
    active = {slug for row in sources.values() for slug in row["project_slugs"]}
    deferred_slugs = [row["slug"] for row in policy["deferred_projects"]]
    _unique(deferred_slugs, "DEFERRED_SLUG_DUPLICATE")
    deferred = {row["slug"]: row["reason_code"] for row in policy["deferred_projects"]}
    if deferred != {"code-stencil": "NO_REMOTE_AND_PLACEHOLDER", "jurys-out": "DOCUMENTATION_ONLY", "uat_sentinel": "NO_REMOTE_AND_NOT_IMPLEMENTED"}:
        raise ContractError("DISPOSITION_REASON")
    inactive = set(policy["embedded_inactive_projects"])
    if inactive != {"pocket-relay"} or active & (inactive | set(deferred)) or inactive & set(deferred):
        raise ContractError("DISPOSITION_OVERLAP")
    if policy["required_projects"] != ["skill-mesh"] or policy["additional_active_projects"] != ["utility-project-standard"]:
        raise ContractError("MEMBERSHIP_EXPLICIT")
    if policy["repository_overrides"] != {"dev-observatory": "coding-root", "switchboard": "coding-root"}:
        raise ContractError("REPOSITORY_OVERRIDE_DRIFT")
    utilities: set[str] = set()
    seen: set[str] = set()
    for row in parse_registry(registry_raw):
        if row.get("category") != "utility":
            continue
        slug = row.get("slug")
        if not isinstance(slug, str) or not SLUG.fullmatch(slug):
            raise ContractError("REGISTRY_SLUG")
        folded = slug.casefold()
        if folded in seen:
            raise ContractError("REGISTRY_DUPLICATE")
        seen.add(folded)
        if slug not in active:
            raise ContractError("MEMBERSHIP_UNKNOWN_UTILITY", slug)
        owner = next(source for source in sources.values() if slug in source["project_slugs"])
        if _github_remote(row.get("repo_url")) != _github_remote(owner["canonical_remote_url"]):
            raise ContractError("SOURCE_REMOTE_DRIFT", slug)
        utilities.add(slug)
    expected_utilities = active - {"skill-mesh", "utility-project-standard"}
    if utilities != expected_utilities:
        raise ContractError("MEMBERSHIP_MISSING_UTILITY")
    return policy

def _schema_document(raw: bytes | str, schema: Any, label: str) -> dict[str, Any]:
    value = validate_schema(schema, parse_json(raw, label), label)
    if not isinstance(value, dict):
        raise ContractError("SCHEMA_INVALID", label)
    return value


def check_bundle(raw: bytes | str, schema: Any, policy: dict[str, Any]) -> dict[str, Any]:
    bundle = _schema_document(raw, schema, "bundle")
    stamp, suffix = _bundle_id(bundle["bundle_id"])
    _timestamp(bundle["created_utc"])
    if bundle["created_utc"].replace("-", "").replace(":", "") != stamp[:8] + "T" + stamp[9:]:
        raise ContractError("BUNDLE_ID_TIMESTAMP")
    if bundle["previous_bundle_id"] is not None:
        _bundle_id(bundle["previous_bundle_id"])
        if bundle["previous_bundle_id"] == bundle["bundle_id"]:
            raise ContractError("PREDECESSOR_SELF_REFERENCE")
    sources = _sources(policy)
    owners = [row["owner_slug"] for row in bundle["repositories"]]
    _unique(owners, "SOURCE_OWNER_DUPLICATE")
    if tuple(owners) != tuple(EXPECTED_OWNERS):
        raise ContractError("BUNDLE_REPOSITORY_ORDER_DRIFT")
    projects: list[str] = []
    checkouts: list[str] = []
    for row in bundle["repositories"]:
        source = sources.get(row["owner_slug"])
        if source is None:
            raise ContractError("SOURCE_ALLOWLIST")
        _path(row["checkout_relative_path"], absolute=False)
        if row["checkout_relative_path"] != source["checkout_relative_path"]:
            raise ContractError("SOURCE_CHECKOUT_DRIFT")

        if row["canonical_remote_url"] != source["canonical_remote_url"]:
            raise ContractError("SOURCE_REMOTE_DRIFT")
        if row["upstream_ref"] != source["allowed_upstream_ref"]:
            raise ContractError("SOURCE_REF_DRIFT")
        if not OID.fullmatch(row["commit"]) or not OID.fullmatch(row["tree"]):
            raise ContractError("GRAMMAR_GIT_OBJECT")
        if row["project_slugs"] != source["project_slugs"]:
            raise ContractError("SOURCE_PROJECT_SHARING")
        projects.extend(row["project_slugs"]); checkouts.append(row["checkout_relative_path"].casefold())
    if set(owners) != set(sources) or len(projects) != 15:
        raise ContractError("MEMBERSHIP_MISSING_UTILITY")
    _unique(projects, "SOURCE_PROJECT_DUPLICATE"); _unique(checkouts, "SOURCE_CHECKOUT_DUPLICATE")
    skill_mesh = next(row for row in bundle["repositories"] if row["owner_slug"] == "skill-mesh")
    release = bundle["skill_mesh_release"]
    if release["source_commit"] != skill_mesh["commit"] or release["source_tree"] != skill_mesh["tree"] or not release["source_commit"].startswith(suffix):
        raise ContractError("BUNDLE_SOURCE_SUFFIX")
    retained_relative = _path(release["retained_relative_path"], absolute=False)
    if retained_relative == "workspace" or retained_relative.startswith("workspace/"):
        raise ContractError("ROOT_COLLAPSE")
    gate_slugs = [row["project_slug"] for row in bundle["gates"]]
    if set(gate_slugs) != set(projects) or len(gate_slugs) != len(set(gate_slugs)):
        raise ContractError("GATE_MEMBERSHIP")
    if tuple(gate_slugs) != tuple(sorted(projects)):
        raise ContractError("GATE_ORDER_DRIFT")
    for gate in bundle["gates"]:
        _path(gate["evidence_relative_path"], absolute=False)
        if not SHA256.fullmatch(gate["sha256"]):
            raise ContractError("GRAMMAR_SHA256")
        if any(any(mark in arg for mark in ("$(`", "$(", "|", ";", "&&", "\n", "\r")) for arg in gate["arguments"]):
            raise ContractError("SHELL_EVALUATION_SHAPE")
    checkout_roles = {"workspace": _path(bundle["workspace_relative_path"], absolute=False)}
    checkout_roles.update({f"checkout:{row['owner_slug']}": _path(row["checkout_relative_path"], absolute=False) for row in bundle["repositories"]})
    checkout_roles["retained"] = retained_relative
    checkout_roles.update({f"evidence:{row['project_slug']}": _path(row["evidence_relative_path"], absolute=False) for row in bundle["gates"]})
    _root_graph(
        checkout_roles,
        aliases=frozenset((frozenset(("workspace", "checkout:coding-root")),)),
        containments=frozenset(frozenset(("workspace", f"checkout:{owner}")) for owner in sources if owner != "coding-root"),
    )
    return bundle


def check_current(raw: bytes | str, schema: Any) -> dict[str, Any]:
    current = _schema_document(raw, schema, "current")
    _bundle_id(current["active_bundle_id"])
    _timestamp(current["activated_utc"])
    active = _path(current["active_bundle_path"], absolute=True)
    if _basename(active) != current["active_bundle_id"].casefold():
        raise ContractError("BUNDLE_PATH_ID_MISMATCH")
    if (current["previous_bundle_id"] is None) != (current["previous_bundle_path"] is None):
        raise ContractError("PREDECESSOR_NULL_PAIR")
    if current["previous_bundle_id"] is not None:
        _bundle_id(current["previous_bundle_id"])
        previous = _path(current["previous_bundle_path"], absolute=True)
        if current["previous_bundle_id"] == current["active_bundle_id"] or previous == active:
            raise ContractError("PREDECESSOR_SELF_REFERENCE")
        if _basename(previous) != current["previous_bundle_id"].casefold():
            raise ContractError("BUNDLE_PATH_ID_MISMATCH")
    utility, workspace = _environment_roots(current["environment"], nullable=False)
    for field in ("installer_result", "inspector_result"):
        _path(current[field]["path"], absolute=True)
    distribution = _path(current["active_skill_mesh_distribution"]["path"], absolute=True)
    if not distribution.startswith(active + "/"):
        raise ContractError("RETAINED_PATH_MISMATCH")
    if distribution == active + "/workspace" or distribution.startswith(active + "/workspace/"):
        raise ContractError("ROOT_COLLAPSE")
    _root_graph(
        {
            "active_bundle": active,
            "utility_root": utility,
            "live_workspace": workspace,
            "active_distribution": distribution,
            "previous_bundle": previous if current["previous_bundle_path"] is not None else None,
            "installer_result": _path(current["installer_result"]["path"], absolute=True),
            "inspector_result": _path(current["inspector_result"]["path"], absolute=True),
        },
        containments=frozenset((frozenset(("active_bundle", "utility_root")), frozenset(("active_bundle", "active_distribution")))),
    )
    if utility != active + "/workspace":
        raise ContractError("UTILITY_ROOT_MISMATCH")
    return current

def check_activation_plan(raw: bytes | str, schema: Any) -> dict[str, Any]:
    plan = _schema_document(raw, schema, "activation plan")
    _bundle_id(plan["bundle_id"])
    _timestamp(plan["created_utc"])
    bundle_path = _path(plan["bundle_path"], absolute=True)
    if _basename(bundle_path) != plan["bundle_id"].casefold():
        raise ContractError("BUNDLE_PATH_ID_MISMATCH")
    retained = _path(plan["retained_distribution_path"], absolute=True)
    active_home = _path(plan["active_home"], absolute=True)
    backup_root = _path(plan["backup_root"], absolute=True)
    if not _descendant(retained, bundle_path) or retained == bundle_path + "/workspace" or retained.startswith(bundle_path + "/workspace/"):
        raise ContractError("ROOT_COLLAPSE")
    utility_root = bundle_path + "/workspace"
    skill_mesh_checkout = utility_root + "/skill-mesh"
    installer = _path(plan["installer"]["path"], absolute=True)
    inspector = _path(plan["inspector"]["path"], absolute=True)
    for role in ("installer", "inspector"):
        path = _path(plan[role]["path"], absolute=True)
        if not _descendant(path, skill_mesh_checkout):
            raise ContractError("SCRIPT_PATH_MISMATCH")
    rollback = _path(plan["rollback_distribution"]["path"], absolute=True)
    if not rollback.startswith(backup_root + "/"):
        raise ContractError("RETAINED_PATH_MISMATCH")
    for old in ("old_process", "old_user"):
        _environment_roots(plan["environment"][old], nullable=True)
    new_process = _environment_roots(plan["environment"]["new_process"], nullable=False)
    new_user = _environment_roots(plan["environment"]["new_user"], nullable=False)
    old_process = _environment_roots(plan["environment"]["old_process"], nullable=True)
    old_user = _environment_roots(plan["environment"]["old_user"], nullable=True)
    profile_root = active_home + "/.agents/skills"
    ledger = active_home + "/.skill-mesh-install.json"
    write_ahead = active_home + "/.skill-mesh-install.write-ahead.json"
    root_roles = {
        "bundle": bundle_path, "utility_root": utility_root, "retained": retained,
        "skill_mesh_checkout": skill_mesh_checkout, "installer": installer, "inspector": inspector,
        "backup": backup_root, "rollback": rollback, "active_home": active_home,
        "profile_root": profile_root, "ledger": ledger, "write_ahead": write_ahead,
        "old_process_utility": old_process[0], "old_process_workspace": old_process[1],
        "old_user_utility": old_user[0], "old_user_workspace": old_user[1],
        "new_process_utility": new_process[0], "new_process_workspace": new_process[1],
        "new_user_utility": new_user[0], "new_user_workspace": new_user[1],
    }
    utilities = ("old_process_utility", "old_user_utility", "new_process_utility", "new_user_utility")
    workspaces = ("old_process_workspace", "old_user_workspace", "new_process_workspace", "new_user_workspace")
    aliases = {frozenset((left, right)) for family in (utilities, workspaces) for index, left in enumerate(family) for right in family[index + 1:]}
    aliases.update(frozenset(("utility_root", role)) for role in utilities)
    containments = {
        frozenset(("bundle", "utility_root")), frozenset(("bundle", "retained")),
        frozenset(("bundle", "skill_mesh_checkout")), frozenset(("bundle", "installer")), frozenset(("bundle", "inspector")),
        frozenset(("utility_root", "skill_mesh_checkout")), frozenset(("utility_root", "installer")), frozenset(("utility_root", "inspector")),
        frozenset(("skill_mesh_checkout", "installer")), frozenset(("skill_mesh_checkout", "inspector")), frozenset(("backup", "rollback")),
        frozenset(("active_home", "profile_root")), frozenset(("active_home", "ledger")),
        frozenset(("active_home", "write_ahead")),
    }
    for role in (*utilities, *workspaces, "bundle", "backup", "rollback", "utility_root", "retained", "skill_mesh_checkout", "installer", "inspector"):
        containments.add(frozenset(("active_home", role)))
    _root_graph(root_roles, aliases=frozenset(aliases), containments=frozenset(containments))
    for role in (*utilities, *workspaces, "bundle", "backup"):
        path = root_roles[role]
        if path is not None and (_same(active_home, path) or _descendant(active_home, path)):
            raise ContractError("ROOT_COLLAPSE", f"active_home~{role}")
    if new_process != new_user:
        raise ContractError("ENVIRONMENT_DRIFT")
    if new_process[0] != utility_root:
        raise ContractError("UTILITY_ROOT_MISMATCH")
    if [action["name"] for action in plan["actions"]] != list(ACTION_ORDER):
        raise ContractError("ACTION_ORDER_DRIFT")
    action_roles = {
        "install": "installer", "inspect": "inspector", "environment": "none",
        "fresh-process-smoke": "none", "rollback": "installer",
    }
    for action in plan["actions"]:
        expected_role = action_roles[action["name"]]
        if action["script_role"] != expected_role:
            raise ContractError("ACTION_ROLE_MISMATCH")
        declared_sha = action["script_sha256"]
        if expected_role == "none":
            if declared_sha is not None:
                raise ContractError("ACTION_SHA_NULL_MISMATCH")
        elif declared_sha is None:
            raise ContractError("ACTION_SHA_NULL_MISMATCH")
        elif declared_sha != plan[expected_role]["sha256"]:
            raise ContractError("ACTION_SHA_MISMATCH")
        if _path(action["working_directory"], absolute=True) != bundle_path:
            raise ContractError("ACTION_WORKING_DIRECTORY_DRIFT")
        if any(any(mark in arg for mark in ("$(`", "$(", "|", ";", "&&", "\n", "\r")) for arg in action["arguments"]):
            raise ContractError("SHELL_EVALUATION_SHAPE")
    return plan
