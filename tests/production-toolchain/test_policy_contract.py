"""Phase PROD Step 1 declarative-contract regressions."""
from __future__ import annotations

import ast
import builtins
import json
from pathlib import Path

import pytest

from tools import production_record_contract as contract

ROOT = Path(__file__).resolve().parents[2]
POLICY_RAW = (ROOT / "config/production-portfolio-policy.json").read_bytes()
SCHEMAS = {name: json.loads((ROOT / "schemas" / file).read_text()) for name, file in {
    "policy": "production-portfolio-policy-v1.schema.json",
    "bundle": "production-bundle-v1.schema.json",
    "current": "production-current-v1.schema.json",
    "activation": "production-activation-plan-v1.schema.json",
}.items()}
ID = "prod-20260901T093602Z-aaaaaaaaaaaa"
OID = "a" * 40
SHA = "b" * 64
ACTIVE_SLUGS = frozenset((
    "b2_project_goblin", "changed-check", "citation-needed", "dev-observatory",
    "find-again", "heads-up", "measure-twice", "mesh-lens", "on-brand",
    "paper-trail", "same-page", "skill-mesh", "switchboard", "tripwire",
    "utility-project-standard",
))
OWNER_ROWS = {
    "b2_project_goblin": ("b2_project_goblin",), "changed-check": ("changed-check",),
    "citation-needed": ("citation-needed",), "coding-root": ("dev-observatory", "switchboard"),
    "find-again": ("find-again",), "heads-up": ("heads-up",), "measure-twice": ("measure-twice",),
    "mesh-lens": ("mesh-lens",), "on-brand": ("on-brand",), "paper-trail": ("paper-trail",),
    "same-page": ("same-page",), "skill-mesh": ("skill-mesh",), "tripwire": ("tripwire",),
    "utility-project-standard": ("utility-project-standard",),
}
TEST_ACTION_ORDER = ("install", "inspect", "environment", "fresh-process-smoke", "rollback")
DEFERRED = {"code-stencil": "NO_REMOTE_AND_PLACEHOLDER", "jurys-out": "DOCUMENTATION_ONLY", "uat_sentinel": "NO_REMOTE_AND_NOT_IMPLEMENTED"}


def dump(value):
    return json.dumps(value, separators=(",", ":")).encode()


def policy():
    return json.loads(POLICY_RAW)


def registry():
    rows = ["[[project]]\nslug = 'Alpha4Gate'\ncategory = 'flagship'\n"]
    for owner, projects in OWNER_ROWS.items():
        if owner in {"skill-mesh", "utility-project-standard"}:
            continue
        remote = f"https://github.com/aberson/{owner}"
        for slug in projects:
            rows.append(f"[[project]]\nslug = '{slug}'\ncategory = 'utility'\nrepo_url = '{remote}'\n")
    return "\n".join(rows).encode()


def bundle():
    doc = policy()
    repositories = [{"owner_slug": row["owner_slug"], "checkout_relative_path": row["checkout_relative_path"], "canonical_remote_url": row["canonical_remote_url"], "upstream_ref": row["allowed_upstream_ref"], "commit": OID, "tree": OID, "project_slugs": row["project_slugs"]} for row in doc["repository_sources"]]
    return {"schema": "skill-mesh/production-bundle/v1", "bundle_id": ID, "created_utc": "2026-09-01T09:36:02Z", "policy_sha256": SHA, "registry_sha256": SHA, "repositories": repositories, "workspace_relative_path": "workspace", "skill_mesh_release": {"retained_relative_path": "retained-dist", "provider_closures": {"claude": SHA, "gpt": SHA, "codex": SHA}, "checksums_sha256": SHA, "source_commit": OID, "source_tree": OID, "manifest_blob": OID}, "gates": [{"project_slug": slug, "role": "help", "arguments": [slug, "--help"], "exit_code": 0, "evidence_relative_path": f"evidence/{slug}.txt", "sha256": SHA} for slug in sorted(ACTIVE_SLUGS)], "previous_bundle_id": None}


def current():
    root = f"C:/prod/releases/{ID}"
    return {"schema": "skill-mesh/production-current/v1", "active_bundle_id": ID, "previous_bundle_id": None, "active_bundle_path": root, "previous_bundle_path": None, "environment": {"DEV_UTILITIES_ROOT": root + "/workspace", "DEV_WORKSPACE_ROOT": "C:/dev"}, "activated_utc": "2026-09-01T09:36:02Z", "installer_result": {"path": "C:/evidence/installer.json", "sha256": SHA}, "inspector_result": {"path": "C:/evidence/inspector.json", "sha256": SHA}, "active_skill_mesh_distribution": {"path": root + "/retained-dist", "codex_closure_sha256": SHA}}


def activation():
    root = f"C:/prod/releases/{ID}"
    new = {"DEV_UTILITIES_ROOT": root + "/workspace", "DEV_WORKSPACE_ROOT": "C:/dev"}
    old = {"DEV_UTILITIES_ROOT": None, "DEV_WORKSPACE_ROOT": None}
    actions = [{"name": name, "program": "declarative", "script_role": role, "script_sha256": None if role == "none" else SHA, "arguments": [name], "working_directory": root} for name, role in zip(TEST_ACTION_ORDER, ("installer", "inspector", "none", "none", "installer"))]
    return {"schema": "skill-mesh/production-activation-plan/v1", "bundle_id": ID, "bundle_path": root, "bundle_sha256": SHA, "provider": "codex", "active_home": "C:/active-home", "environment": {"old_process": old, "old_user": old, "new_process": new, "new_user": new}, "retained_distribution_path": root + "/retained-dist", "codex_closure_sha256": SHA, "installer": {"path": root + "/workspace/skill-mesh/tools/install.ps1", "sha256": SHA}, "inspector": {"path": root + "/workspace/skill-mesh/tools/inspect.ps1", "sha256": SHA}, "backup_root": "C:/backup", "rollback_distribution": {"path": "C:/backup/previous", "codex_closure_sha256": SHA}, "actions": actions, "created_utc": "2026-09-01T09:36:02Z"}


def assert_code(code, function, *args):
    with pytest.raises(contract.ContractError) as raised:
        function(*args)
    assert raised.value.code == code


def test_release_one_literals_match_policy_and_mixed_registry():
    checked = contract.check_policy(POLICY_RAW, registry(), SCHEMAS["policy"])
    assert {slug for row in checked["repository_sources"] for slug in row["project_slugs"]} == ACTIVE_SLUGS
    assert {row["owner_slug"]: tuple(row["project_slugs"]) for row in checked["repository_sources"]} == OWNER_ROWS
    assert checked["embedded_inactive_projects"] == ["pocket-relay"]
    assert {row["slug"]: row["reason_code"] for row in checked["deferred_projects"]} == DEFERRED
    assert next(row for row in checked["repository_sources"] if row["owner_slug"] == "measure-twice")["allowed_upstream_ref"] == "origin/master"


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":{"y":1,"y":2}}'], ids=["root", "nested"])
def test_duplicate_json_member_reason_code(raw):
    assert_code("DUPLICATE_JSON_MEMBER", contract.parse_json, raw)


@pytest.mark.parametrize("mutation,code", [
    (lambda p: p.__setitem__("registry_categories", ["utility", "extra"]), "SCHEMA_INVALID"),
    (lambda p: p["deferred_projects"].append({"slug": "code-stencil", "reason_code": "NO_REMOTE_AND_PLACEHOLDER", "evidence": "duplicate"}), "DEFERRED_SLUG_DUPLICATE"),
    (lambda p: p["deferred_projects"][0].__setitem__("reason_code", "DOCUMENTATION_ONLY"), "DISPOSITION_REASON"),
    (lambda p: p.__setitem__("embedded_inactive_projects", ["skill-mesh"]), "DISPOSITION_OVERLAP"),
    (lambda p: p["repository_overrides"].__setitem__("switchboard", "switchboard"), "REPOSITORY_OVERRIDE_DRIFT"),
], ids=["category-drift", "duplicate-deferred", "wrong-reason", "disposition-overlap", "override-drift"])
def test_policy_negative_reason_codes(mutation, code):
    doc = policy(); mutation(doc)
    assert_code(code, contract.check_policy, dump(doc), registry(), SCHEMAS["policy"])


def test_missing_utility_reason_code():
    raw = registry().replace(b"slug = 'citation-needed'\ncategory = 'utility'\nrepo_url = 'https://github.com/aberson/citation-needed'\n", b"")
    assert_code("MEMBERSHIP_MISSING_UTILITY", contract.check_policy, POLICY_RAW, raw, SCHEMAS["policy"])


def test_duplicate_utility_reason_code():
    raw = registry() + b"\n[[project]]\nslug='tripwire'\ncategory='utility'\nrepo_url='https://github.com/aberson/tripwire'\n"
    assert_code("REGISTRY_DUPLICATE", contract.check_policy, POLICY_RAW, raw, SCHEMAS["policy"])


def test_unknown_utility_reason_code():
    raw = registry() + b"\n[[project]]\nslug='unknown-tool'\ncategory='utility'\nrepo_url='https://github.com/aberson/unknown-tool'\n"
    assert_code("MEMBERSHIP_UNKNOWN_UTILITY", contract.check_policy, POLICY_RAW, raw, SCHEMAS["policy"])


@pytest.mark.parametrize("field,value,code", [
    ("owner_slug", "tripwire", "SOURCE_OWNER_DUPLICATE"),
    ("checkout_relative_path", "workspace/b2_project_goblin", "SOURCE_CHECKOUT_DUPLICATE"),
    ("canonical_remote_url", "https://github.com/attacker/x.git", "SOURCE_REMOTE_DRIFT"),
    ("allowed_upstream_ref", "origin/main", "SOURCE_REF_DRIFT"),
], ids=["owner-duplicate", "checkout-duplicate", "remote-drift", "measure-twice-ref"])
def test_source_allowlist_negative_reason_codes(field, value, code):
    doc = policy(); index = 6 if field == "allowed_upstream_ref" else 1 if field == "checkout_relative_path" else 0; doc["repository_sources"][index][field] = value
    assert_code(code, contract.check_policy, dump(doc), registry(), SCHEMAS["policy"])


def test_duplicate_project_reason_code():
    doc = policy(); doc["repository_sources"][-1]["project_slugs"] = ["tripwire"]
    assert_code("SOURCE_PROJECT_DUPLICATE", contract.check_policy, dump(doc), registry(), SCHEMAS["policy"])


def test_bundle_wrong_repository_sharing_reason_code():
    doc = bundle(); doc["repositories"][0]["project_slugs"] = ["tripwire"]
    assert_code("SOURCE_PROJECT_SHARING", contract.check_bundle, dump(doc), SCHEMAS["bundle"], policy())


@pytest.mark.parametrize("field,value,code", [("commit", "g" * 40, "SCHEMA_INVALID"), ("tree", "a" * 39, "SCHEMA_INVALID"), ("created_utc", "2026-99-01T00:00:00Z", "GRAMMAR_TIMESTAMP")], ids=["commit", "tree", "timestamp"])
def test_bundle_grammar_negative_reason_codes(field, value, code):
    doc = bundle(); (doc.__setitem__(field, value) if field == "created_utc" else doc["repositories"][0].__setitem__(field, value))
    assert_code(code, contract.check_bundle, dump(doc), SCHEMAS["bundle"], policy())


@pytest.mark.parametrize("path", ["workspace/../escape", "workspace\\mixed", "workspace/a\x01", "workspace/con", "workspace/alias."], ids=["escape", "mixed", "control", "reserved", "alias"])
def test_bundle_lexical_path_reason_code(path):
    doc = bundle(); doc["repositories"][0]["checkout_relative_path"] = path
    assert_code("LEXICAL_PATH", contract.check_bundle, dump(doc), SCHEMAS["bundle"], policy())


def test_bundle_source_suffix_reason_code():
    doc = bundle(); doc["skill_mesh_release"]["source_commit"] = "b" * 40
    assert_code("BUNDLE_SOURCE_SUFFIX", contract.check_bundle, dump(doc), SCHEMAS["bundle"], policy())


def test_bundle_shell_evaluation_reason_code():
    doc = bundle(); doc["gates"][0]["arguments"] = ["$(bad)"]
    assert_code("SHELL_EVALUATION_SHAPE", contract.check_bundle, dump(doc), SCHEMAS["bundle"], policy())


@pytest.mark.parametrize("field", ["active_bundle_path", "previous_bundle_path", "installer_result", "inspector_result", "active_skill_mesh_distribution"], ids=["active", "previous", "installer-result", "inspector-result", "distribution"])
def test_current_path_fields_reject_lexical_escape(field):
    doc = current()
    if field == "previous_bundle_path": doc["previous_bundle_id"] = "prod-20260901T093601Z-bbbbbbbbbbbb"; doc[field] = "C:/prod/../old"
    elif field in {"installer_result", "inspector_result"}: doc[field]["path"] = "C:/evidence/../bad.json"
    elif field == "active_skill_mesh_distribution": doc[field]["path"] = "C:/prod/../bad"
    else: doc[field] = "C:/prod/../bad"
    assert_code("LEXICAL_PATH", contract.check_current, dump(doc), SCHEMAS["current"])


def test_current_predecessor_null_pair_reason_code():
    doc = current(); doc["previous_bundle_path"] = "C:/prod/releases/old"
    assert_code("PREDECESSOR_NULL_PAIR", contract.check_current, dump(doc), SCHEMAS["current"])


def test_current_predecessor_self_reference_reason_code():
    doc = current(); doc["previous_bundle_id"] = ID; doc["previous_bundle_path"] = doc["active_bundle_path"]
    assert_code("PREDECESSOR_SELF_REFERENCE", contract.check_current, dump(doc), SCHEMAS["current"])


@pytest.mark.parametrize("field", ["DEV_UTILITIES_ROOT", "DEV_WORKSPACE_ROOT"], ids=["utility-active", "workspace-active"])
def test_current_active_root_collapse_reason_code(field):
    doc = current(); doc["environment"][field] = doc["active_bundle_path"]
    assert_code("ROOT_COLLAPSE", contract.check_current, dump(doc), SCHEMAS["current"])


def test_current_environment_root_collapse_reason_code():
    doc = current(); doc["environment"]["DEV_WORKSPACE_ROOT"] = doc["environment"]["DEV_UTILITIES_ROOT"]
    assert_code("ROOT_COLLAPSE", contract.check_current, dump(doc), SCHEMAS["current"])


def test_current_utility_root_relationship_reason_code():
    doc = current(); doc["environment"]["DEV_UTILITIES_ROOT"] = "C:/other/workspace"
    assert_code("UTILITY_ROOT_MISMATCH", contract.check_current, dump(doc), SCHEMAS["current"])


def test_activation_process_user_drift_reason_code():
    doc = activation(); doc["environment"]["new_user"] = {"DEV_UTILITIES_ROOT": doc["bundle_path"] + "/workspace", "DEV_WORKSPACE_ROOT": "C:/different"}
    assert_code("ENVIRONMENT_DRIFT", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


@pytest.mark.parametrize("shape", ["old_process", "old_user", "new_process", "new_user"], ids=["old-process", "old-user", "new-process", "new-user"])
def test_activation_environment_root_collapse_reason_code(shape):
    doc = activation(); doc["environment"][shape] = {"DEV_UTILITIES_ROOT": "C:/same", "DEV_WORKSPACE_ROOT": "C:/same"}
    assert_code("ROOT_COLLAPSE", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


@pytest.mark.parametrize("field", ["bundle_path", "retained_distribution_path", "active_home", "backup_root", "installer", "inspector", "rollback_distribution"], ids=["bundle", "retained", "home", "backup", "installer", "inspector", "rollback"])
def test_activation_path_fields_reject_lexical_escape(field):
    doc = activation()
    if field in {"installer", "inspector"}: doc[field]["path"] = "C:/prod/../bad.ps1"
    elif field == "rollback_distribution": doc[field]["path"] = "C:/backup/../bad"
    else: doc[field] = "C:/prod/../bad"
    assert_code("LEXICAL_PATH", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


def test_activation_action_order_reason_code():
    doc = activation(); doc["actions"][0], doc["actions"][1] = doc["actions"][1], doc["actions"][0]
    assert_code("ACTION_ORDER_DRIFT", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


def test_activation_shell_evaluation_reason_code():
    doc = activation(); doc["actions"][0]["arguments"] = ["$(bad)"]
    assert_code("SHELL_EVALUATION_SHAPE", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


def test_activation_provider_drift_reason_code():
    doc = activation(); doc["provider"] = "claude"
    assert_code("SCHEMA_INVALID", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


def test_activation_bundle_path_id_reason_code():
    doc = activation(); doc["bundle_path"] = "C:/prod/releases/prod-20260901T093601Z-bbbbbbbbbbbb"
    assert_code("BUNDLE_PATH_ID_MISMATCH", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


@pytest.mark.parametrize("name,make,select,schema_name", [
    ("policy-root", policy, lambda d: d, "policy"), ("policy-deferred", policy, lambda d: d["deferred_projects"][0], "policy"), ("policy-overrides", policy, lambda d: d["repository_overrides"], "policy"), ("policy-source", policy, lambda d: d["repository_sources"][0], "policy"),
    ("bundle-root", bundle, lambda d: d, "bundle"), ("bundle-repository", bundle, lambda d: d["repositories"][0], "bundle"), ("bundle-release", bundle, lambda d: d["skill_mesh_release"], "bundle"), ("bundle-closures", bundle, lambda d: d["skill_mesh_release"]["provider_closures"], "bundle"), ("bundle-gate", bundle, lambda d: d["gates"][0], "bundle"),
    ("current-root", current, lambda d: d, "current"), ("current-environment", current, lambda d: d["environment"], "current"), ("current-installer", current, lambda d: d["installer_result"], "current"), ("current-inspector", current, lambda d: d["inspector_result"], "current"), ("current-distribution", current, lambda d: d["active_skill_mesh_distribution"], "current"),
    ("activation-root", activation, lambda d: d, "activation"), ("activation-environment", activation, lambda d: d["environment"], "activation"), ("activation-old-process", activation, lambda d: d["environment"]["old_process"], "activation"), ("activation-old-user", activation, lambda d: d["environment"]["old_user"], "activation"), ("activation-new-process", activation, lambda d: d["environment"]["new_process"], "activation"), ("activation-new-user", activation, lambda d: d["environment"]["new_user"], "activation"), ("activation-installer", activation, lambda d: d["installer"], "activation"), ("activation-inspector", activation, lambda d: d["inspector"], "activation"), ("activation-rollback", activation, lambda d: d["rollback_distribution"], "activation"), ("activation-action", activation, lambda d: d["actions"][0], "activation"),
], ids=["policy-root", "policy-deferred", "policy-overrides", "policy-source", "bundle-root", "bundle-repository", "bundle-release", "bundle-closures", "bundle-gate", "current-root", "current-environment", "current-installer", "current-inspector", "current-distribution", "activation-root", "activation-environment", "activation-old-process", "activation-old-user", "activation-new-process", "activation-new-user", "activation-installer", "activation-inspector", "activation-rollback", "activation-action"])
def test_schema_boundaries_reject_additional_properties(name, make, select, schema_name):
    document = make(); select(document)["unexpected"] = True
    assert_code("SCHEMA_INVALID", contract.validate_schema, SCHEMAS[schema_name], document, name)

def test_helper_public_surface_has_no_runtime_observation_capabilities():
    tree = ast.parse((ROOT / "tools/production_record_contract.py").read_text())
    banned_modules = {"os", "pathlib", "glob", "shutil", "subprocess", "socket", "urllib", "requests", "importlib"}
    banned_calls = {"open", "__import__", "system", "popen", "run", "call", "check_call", "check_output", "walk", "scandir", "listdir", "stat", "exists", "isfile", "isdir"}
    public = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_")]
    assert not [name for name in public if name.startswith(("Validated", "Authorized"))]
    imports = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert not imports & banned_modules
    calls = {node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else "" for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert not calls & banned_calls

def test_activation_action_role_mismatch_reason_code():
    doc = activation(); doc["actions"][0]["script_role"] = "none"; doc["actions"][0]["script_sha256"] = None
    assert_code("ACTION_ROLE_MISMATCH", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


def test_activation_action_null_sha_mismatch_reason_code():
    doc = activation(); doc["actions"][0]["script_sha256"] = None
    assert_code("ACTION_SHA_NULL_MISMATCH", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


def test_activation_action_declared_sha_mismatch_reason_code():
    doc = activation(); doc["actions"][0]["script_sha256"] = "c" * 64
    assert_code("ACTION_SHA_MISMATCH", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])

def test_current_pure_backslash_paths_are_canonicalized():
    doc = current()
    for key, value in list(doc.items()):
        if key.endswith("path") and isinstance(value, str): doc[key] = value.replace("/", "\\")
    doc["environment"] = {key: value.replace("/", "\\") for key, value in doc["environment"].items()}
    doc["installer_result"]["path"] = doc["installer_result"]["path"].replace("/", "\\")
    doc["inspector_result"]["path"] = doc["inspector_result"]["path"].replace("/", "\\")
    doc["active_skill_mesh_distribution"]["path"] = doc["active_skill_mesh_distribution"]["path"].replace("/", "\\")
    assert contract.check_current(dump(doc), SCHEMAS["current"])["active_bundle_id"] == ID


def test_activation_pure_backslash_paths_are_canonicalized():
    doc = activation()
    for key in ("bundle_path", "active_home", "retained_distribution_path", "backup_root"):
        doc[key] = doc[key].replace("/", "\\")
    for key in ("installer", "inspector", "rollback_distribution"):
        doc[key]["path"] = doc[key]["path"].replace("/", "\\")
    for shape in ("old_process", "old_user", "new_process", "new_user"):
        doc["environment"][shape] = {key: value.replace("/", "\\") if value else value for key, value in doc["environment"][shape].items()}
    for action in doc["actions"]: action["working_directory"] = action["working_directory"].replace("/", "\\")
    assert contract.check_activation_plan(dump(doc), SCHEMAS["activation"])["bundle_id"] == ID


def test_mixed_separator_reason_code():
    doc = current(); doc["active_bundle_path"] = doc["active_bundle_path"].replace("/releases/", "\\releases/")
    assert_code("LEXICAL_PATH", contract.check_current, dump(doc), SCHEMAS["current"])


def test_bundle_retained_workspace_descendant_reason_code():
    doc = bundle(); doc["skill_mesh_release"]["retained_relative_path"] = "workspace/retained-dist"
    assert_code("ROOT_COLLAPSE", contract.check_bundle, dump(doc), SCHEMAS["bundle"], policy())


def test_current_retained_workspace_descendant_reason_code():
    doc = current(); doc["active_skill_mesh_distribution"]["path"] = doc["active_bundle_path"] + "/workspace/retained-dist"
    assert_code("ROOT_COLLAPSE", contract.check_current, dump(doc), SCHEMAS["current"])


def test_activation_retained_workspace_descendant_reason_code():
    doc = activation(); doc["retained_distribution_path"] = doc["bundle_path"] + "/workspace/retained-dist"
    assert_code("ROOT_COLLAPSE", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


@pytest.mark.parametrize("name,mutate", [
    ("bundle-id", lambda d: d.__setitem__("bundle_id", "wrong")),
    ("bundle-previous-id", lambda d: d.__setitem__("previous_bundle_id", "wrong")),
], ids=None)
def test_bundle_id_grammar_reason_codes(name, mutate):
    doc = bundle(); mutate(doc)
    assert_code("SCHEMA_INVALID", contract.check_bundle, dump(doc), SCHEMAS["bundle"], policy())


@pytest.mark.parametrize("name,make,mutate,check", [
    ("bundle-sha", bundle, lambda d: d.__setitem__("policy_sha256", "wrong"), lambda d: contract.check_bundle(dump(d), SCHEMAS["bundle"], policy())),
    ("current-sha", current, lambda d: d["installer_result"].__setitem__("sha256", "wrong"), lambda d: contract.check_current(dump(d), SCHEMAS["current"])),
    ("activation-sha", activation, lambda d: d.__setitem__("bundle_sha256", "wrong"), lambda d: contract.check_activation_plan(dump(d), SCHEMAS["activation"])),
], ids=None)
def test_record_sha_grammar_reason_codes(name, make, mutate, check):
    doc = make(); mutate(doc); assert_code("SCHEMA_INVALID", check, doc)


def test_jsonschema_missing_is_call_time_only(monkeypatch):
    original = builtins.__import__
    def blocked(name, *args, **kwargs):
        if name == "jsonschema": raise ImportError("planted missing dependency")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", blocked)
    assert contract.parse_json(b'{"safe":true}')["safe"] is True
    with pytest.raises(RuntimeError, match="jsonschema is required when production declaration schema validation is called"):
        contract.validate_schema({}, {})


@pytest.mark.parametrize("shape", ["old_process", "old_user", "new_process", "new_user"], ids=["activation-old-process-extra", "activation-old-user-extra", "activation-new-process-extra", "activation-new-user-extra"])
def test_activation_environment_boundaries_reject_additional_properties(shape):
    doc = activation(); doc["environment"][shape]["unexpected"] = True
    assert_code("SCHEMA_INVALID", contract.validate_schema, SCHEMAS["activation"], doc, shape)


@pytest.mark.parametrize("mode", ["equal", "left-child", "right-child", "slash-case"], ids=str)
def test_closed_root_graph_rejects_every_unlisted_overlap_mode(mode):
    left, right = "c:/roots/foo", "c:/roots/bar"
    if mode == "equal": right = left
    elif mode == "left-child": left = right + "/child"
    elif mode == "right-child": right = left + "/child"
    elif mode == "slash-case": right = "C:\\ROOTS\\FOO"
    if mode == "slash-case":
        right = contract._path(right, absolute=True)
    assert_code("ROOT_COLLAPSE", contract._root_graph, {"left": left, "right": right})


def test_closed_root_graph_keeps_separator_boundary_siblings_disjoint():
    contract._root_graph({"foo": "c:/roots/foo", "foobar": "c:/roots/foobar"})


@pytest.mark.parametrize("field", ["active_home", "backup_root"], ids=["home", "backup"])
def test_activation_release_root_descendants_collapse(field):
    doc = activation(); doc[field] = doc["bundle_path"] + "/workspace/child"
    if field == "backup_root": doc["rollback_distribution"]["path"] = doc[field] + "/previous"
    assert_code("ROOT_COLLAPSE", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


def test_current_live_workspace_descendant_collapses():
    doc = current(); doc["environment"]["DEV_WORKSPACE_ROOT"] = doc["active_bundle_path"] + "/workspace/child"
    assert_code("ROOT_COLLAPSE", contract.check_current, dump(doc), SCHEMAS["current"])


def test_activation_derived_profile_target_collision_is_rejected():
    doc = activation(); doc["active_home"] = doc["bundle_path"] + "/retained-dist"
    assert_code("ROOT_COLLAPSE", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


def test_activation_home_may_be_the_common_container_without_profile_collision():
    doc = activation()
    home = "C:" + "/Users/x"
    doc["active_home"] = home
    doc["bundle_path"] = home + "/prod/" + ID
    doc["retained_distribution_path"] = doc["bundle_path"] + "/retained-dist"
    doc["environment"]["new_process"]["DEV_UTILITIES_ROOT"] = doc["bundle_path"] + "/workspace"
    doc["environment"]["new_user"]["DEV_UTILITIES_ROOT"] = doc["bundle_path"] + "/workspace"
    doc["environment"]["new_process"]["DEV_WORKSPACE_ROOT"] = home + "/dev"
    doc["environment"]["new_user"]["DEV_WORKSPACE_ROOT"] = home + "/dev"
    doc["installer"]["path"] = doc["bundle_path"] + "/workspace/skill-mesh/tools/install.ps1"
    doc["inspector"]["path"] = doc["bundle_path"] + "/workspace/skill-mesh/tools/inspect.ps1"
    doc["backup_root"] = home + "/backup"
    doc["rollback_distribution"]["path"] = doc["backup_root"] + "/previous"
    for action in doc["actions"]: action["working_directory"] = doc["bundle_path"]
    assert contract.check_activation_plan(dump(doc), SCHEMAS["activation"])["bundle_id"] == ID


@pytest.mark.parametrize("action", range(5), ids=lambda value: TEST_ACTION_ORDER[value])
def test_activation_action_arguments_are_never_empty(action):
    doc = activation(); doc["actions"][action]["arguments"] = []
    assert_code("SCHEMA_INVALID", contract.check_activation_plan, dump(doc), SCHEMAS["activation"])


@pytest.mark.parametrize("kind", ["policy", "bundle-reverse", "bundle-rotation", "gates-reverse", "gates-rotation"])
def test_canonical_release_order_is_required(kind):
    if kind == "policy":
        doc = policy(); doc["repository_sources"].reverse()
        assert_code("SOURCE_ORDER_DRIFT", contract.check_policy, dump(doc), registry(), SCHEMAS["policy"])
    else:
        doc = bundle()
        if kind.startswith("bundle"):
            rows = doc["repositories"]
            rows.reverse() if kind.endswith("reverse") else rows.append(rows.pop(0))
            assert_code("BUNDLE_REPOSITORY_ORDER_DRIFT", contract.check_bundle, dump(doc), SCHEMAS["bundle"], policy())
        else:
            rows = doc["gates"]
            rows.reverse() if kind.endswith("reverse") else rows.append(rows.pop(0))
            assert_code("GATE_ORDER_DRIFT", contract.check_bundle, dump(doc), SCHEMAS["bundle"], policy())


def test_every_public_record_checker_reaches_the_shared_root_graph():
    tree = ast.parse((ROOT / "tools/production_record_contract.py").read_text())
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert any(isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_root_graph" for node in ast.walk(functions["_sources"]))
    for name in ("check_bundle", "check_current", "check_activation_plan"):
        assert any(isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_root_graph" for node in ast.walk(functions[name]))
