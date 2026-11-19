"""Tests for the core companion manifest and its checker (core companion plan Step 1).

The manifest is config/companions.json; its checker is tools/companions.py; its
JSON Schema description is schemas/companions.schema.json. The shape is owned by
documentation/core-companion-plan.md section 4 and the membership rule by
section 3.

Every verdict here comes from the production entry point: the tool is run as
`python tools/companions.py ...` in a child process. The module is imported only
to compare its declared constants with the schema, with bytecode writing off so
the import leaves nothing in the tree.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "companions.py"
MANIFEST = REPO_ROOT / "config" / "companions.json"
SCHEMA = REPO_ROOT / "schemas" / "companions.schema.json"


def _load_tool_module():
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("skill_mesh_companions", TOOL)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


companions = _load_tool_module()


def run_tool(*args, cwd=None):
    proc = subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        timeout=60,
    )
    return proc


def run_json(*args, cwd=None):
    proc = run_tool(*args, cwd=cwd)
    assert proc.stderr == b"", proc.stderr.decode("utf-8", "replace")
    return proc.returncode, json.loads(proc.stdout.decode("ascii")), proc.stdout


def real_manifest():
    with open(MANIFEST, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def member(manifest, slug):
    return next(row for row in manifest["members"] if row["slug"] == slug)


def write_manifest(tmp_path, manifest, name="companions.json"):
    path = tmp_path / name
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return path


# --- The real manifest -------------------------------------------------------


def test_real_manifest_verifies():
    code, payload, _ = run_json("verify")
    assert code == 0, payload
    assert payload["ok"] is True
    assert payload["findings"] == []
    assert payload["members"] == 8
    assert payload["release"] is False
    assert payload["manifest"] == "config/companions.json"


def test_real_manifest_holds_the_eight_rows_at_their_plan_time_rings():
    manifest = real_manifest()
    assert manifest["schema_version"] == 1
    rings = {row["slug"]: row["ring"] for row in manifest["members"]}
    assert rings == {
        "passing-notes": "core",
        "tripwire": "core",
        "find-again": "optional",
        "drift-ranger": "candidate",
        # Plan Step 16 (#295) promoted switchboard's registry and apply to core.
        "switchboard": "core",
        "changed-check": "candidate",
        "paper-trail": "candidate",
        "mesh-lens": "candidate",
    }
    slugs = [row["slug"] for row in manifest["members"]]
    assert slugs == sorted(slugs)
    # Tags are not asserted here: Step 9's build fills them. The null-tag
    # behaviour is tested on planted manifests below.
    # heads-up and same-page are dropped (CC-D13); dev-observatory stays private (CC-D8).
    assert not {"heads-up", "same-page", "dev-observatory"} & set(rings)


def test_real_manifest_hook_entries_match_the_plan():
    manifest = real_manifest()
    (stop,) = member(manifest, "passing-notes")["hooks"]
    assert (
        stop["kind"] == "member"
        and stop["event"] == "Stop"
        and stop["host"] == "claude"
    )
    assert stop["install"] == [
        "passing-notes",
        "hook",
        "install",
        "--settings",
        "{settings}",
    ]
    assert stop["uninstall"] == [
        "passing-notes",
        "hook",
        "uninstall",
        "--settings",
        "{settings}",
    ]
    (pretool,) = member(manifest, "tripwire")["hooks"]
    assert pretool["kind"] == "file" and pretool["event"] == "PreToolUse"
    assert pretool["matcher"] == "Bash|PowerShell"
    assert pretool["locate"] == ["tripwire", "hook", "path", "--host", "claude"]
    assert member(manifest, "tripwire")["callers"] == [
        "member:hooks/claude/tripwire-pretool.ps1"
    ]


def test_real_skill_mesh_callers_actually_name_their_tool():
    """A caller of record must call the member, not merely exist (plan section 3, point 1)."""
    names = {
        "passing-notes": ("passing-notes",),
        "drift-ranger": ("tool_resolve.py resolve --tool drift-ranger",),
        "find-again": ("find-again",),
        # V4-10 Step 5: every switchboard caller resolves it through the shared resolver.
        "switchboard": ("tool_resolve.py resolve --tool switchboard",),
    }
    seen = 0
    for row in real_manifest()["members"]:
        for caller in row["callers"]:
            if caller.startswith("member:"):
                continue
            text = (REPO_ROOT / caller).read_text(encoding="utf-8")
            assert any(name in text for name in names[row["slug"]]), (
                row["slug"],
                caller,
            )
            seen += 1
    assert seen >= 8


def with_null_tags(manifest):
    """Plant today's pre-Step-9 state (every tag null) whatever the real tags are."""
    for row in manifest["members"]:
        row["tag"] = None
    return manifest


def with_installed_tags(manifest, tag="v0.1.0"):
    for row in manifest["members"]:
        row["tag"] = tag if row["ring"] in ("core", "optional") else None
    return manifest


def test_release_refuses_every_installed_member_with_a_null_tag(tmp_path):
    manifest = with_null_tags(real_manifest())
    path = write_manifest(tmp_path, manifest)
    code, payload, _ = run_json("verify", "--release", "--manifest", str(path))
    assert code == companions.EXIT_RELEASE_TAG == 19
    flagged = sorted(item["member"] for item in payload["findings"])
    assert flagged == sorted(
        row["slug"]
        for row in manifest["members"]
        if row["ring"] in ("core", "optional")
    )
    assert {item["check"] for item in payload["findings"]} == {"release-tag"}


# --- Planted fixtures: one violation each, one exit code each ---------------


def _core_member_without_caller(m):
    member(m, "passing-notes")["callers"] = []


def _caller_path_missing(m):
    member(m, "find-again")["callers"].append("skills/plan-feature/no-such-core.md")


def _repo_not_github(m):
    member(m, "tripwire")["repo"] = "https://gitlab.com/aberson/tripwire"


def _tag_not_semver(m):
    member(m, "find-again")["tag"] = "1.0"


def _duplicate_slug(m):
    m["members"].append(copy.deepcopy(member(m, "tripwire")))


def _unsorted_members(m):
    m["members"].reverse()


def _newer_schema_version(m):
    m["schema_version"] = 2


def _member_hook_missing_uninstall(m):
    del member(m, "passing-notes")["hooks"][0]["uninstall"]


def _argv_unknown_token(m):
    member(m, "find-again")["health"] = ["find-again", "--root", "{root}", "--version"]


PLANTED = [
    ("core-member-no-caller", _core_member_without_caller, 13, "no-caller"),
    ("caller-path-missing", _caller_path_missing, 14, "caller-path"),
    ("repo-not-github", _repo_not_github, 15, "repo"),
    ("tag-not-semver", _tag_not_semver, 16, "tag"),
    ("duplicate-slug", _duplicate_slug, 11, "duplicate-slug"),
    ("unsorted-members", _unsorted_members, 12, "unsorted-members"),
    ("newer-schema-version", _newer_schema_version, 10, "newer-schema-version"),
    ("member-hook-missing-uninstall", _member_hook_missing_uninstall, 17, "hook-entry"),
    ("argv-unknown-token", _argv_unknown_token, 18, "argv-token"),
]


@pytest.mark.parametrize(
    "name, plant, code, check", PLANTED, ids=[p[0] for p in PLANTED]
)
def test_planted_fixture_fails_with_its_own_exit_code(
    tmp_path, name, plant, code, check
):
    manifest = real_manifest()
    plant(manifest)
    path = write_manifest(tmp_path, manifest)
    exit_code, payload, _ = run_json("verify", "--manifest", str(path))
    assert exit_code == code, payload
    assert payload["ok"] is False
    assert {item["code"] for item in payload["findings"]} == {code}, payload["findings"]
    assert {item["check"] for item in payload["findings"]} == {check}
    # The same fixture, release or not, never passes.
    assert run_tool("verify", "--release", "--manifest", str(path)).returncode != 0


def test_null_tag_fails_only_under_release(tmp_path):
    manifest = with_installed_tags(real_manifest())
    member(manifest, "tripwire")["tag"] = None
    path = write_manifest(tmp_path, manifest)
    assert run_tool("verify", "--manifest", str(path)).returncode == 0
    code, payload, _ = run_json("verify", "--release", "--manifest", str(path))
    assert code == 19
    assert [(item["check"], item["member"]) for item in payload["findings"]] == [
        ("release-tag", "tripwire")
    ]


def test_planted_exit_codes_are_distinct():
    codes = [p[2] for p in PLANTED] + [companions.EXIT_RELEASE_TAG]
    assert len(codes) == len(set(codes)) == 10
    assert 0 not in codes


def test_release_passes_once_every_member_is_tagged(tmp_path):
    """Green anchor for the release check: valid tags are accepted."""
    manifest = real_manifest()
    for row in manifest["members"]:
        if row["ring"] in ("core", "optional"):
            row["tag"] = "v0.1.0"
    member(manifest, "mesh-lens")["tag"] = "v12.0.3"
    path = write_manifest(tmp_path, manifest)
    code, payload, _ = run_json("verify", "--release", "--manifest", str(path))
    assert code == 0, payload


@pytest.mark.parametrize(
    "tag", ["v1.2", "1.2.3", "v1.2.3-rc1", "v1.2.3\n", "V1.2.3", "v01.2.x", "", 3]
)
def test_tag_shapes_refused(tmp_path, tag):
    manifest = real_manifest()
    member(manifest, "tripwire")["tag"] = tag
    code, _, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 16


@pytest.mark.parametrize(
    "repo",
    [
        "http://github.com/aberson/tripwire",
        "https://github.com/aberson/tripwire.git",
        "https://github.com/aberson/someone-else",
        "git@github.com:aberson/tripwire",
        "https://github.com.evil.example/aberson/tripwire",
        None,
    ],
)
def test_repo_shapes_refused_for_core(tmp_path, repo):
    manifest = real_manifest()
    member(manifest, "tripwire")["repo"] = repo
    code, _, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 15


@pytest.mark.parametrize(
    "caller",
    [
        "../skill-mesh/skills/plan-feature/core.md",
        "/skills/plan-feature/core.md",
        "C:/skills/plan-feature/core.md",
        "skills\\plan-feature\\core.md",
        "skills/plan-feature",
        "skills/./plan-feature/core.md",
        "member:",
        "member:../escape.ps1",
        # A ':' after the prefix: an NTFS alternate data stream or a drive.
        "skills/plan-feature/core.md:stream",
        # The default NTFS stream: on Windows this opens core.md itself, so
        # only the ':' rule refuses it.
        "skills/plan-feature/core.md::$DATA",
        "skills/plan-feature:x/core.md",
        "member:hooks/claude/tripwire-pretool.ps1:stream",
        "member:C:/escape.ps1",
        # Control characters.
        "skills/plan-feature/core.md\n",
        "skills/plan\tfeature/core.md",
        "member:hooks/a\x00b.ps1",
    ],
)
def test_malformed_or_escaping_caller_paths_refused(tmp_path, caller):
    manifest = real_manifest()
    member(manifest, "find-again")["callers"] = [caller]
    code, _, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 14


def test_member_callers_are_not_resolved_in_the_tree(tmp_path):
    """member: entries are left to the Step 11 contract suite."""
    manifest = real_manifest()
    member(manifest, "find-again")["callers"] = ["member:src/find_again/not-here.py"]
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 0, payload


def test_candidate_may_have_no_caller_and_no_repo(tmp_path):
    manifest = real_manifest()
    member(manifest, "mesh-lens")["repo"] = None
    assert member(manifest, "mesh-lens")["callers"] == []
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 0, payload


@pytest.mark.parametrize(
    "argv",
    [
        ["tripwire", "hook", "path", "--host", "{host}"],
        ["tripwire", "{home"],
        ["tripwire", "home}"],
        ["tripwire", "{{home}}"],
        ["tripwire", "{}"],
    ],
)
def test_argv_tokens_other_than_home_and_settings_refused(tmp_path, argv):
    manifest = real_manifest()
    member(manifest, "tripwire")["hooks"][0]["locate"] = argv
    code, _, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 18


def test_home_and_settings_tokens_accepted(tmp_path):
    manifest = real_manifest()
    member(manifest, "tripwire")["hooks"][0]["locate"] = [
        "tripwire",
        "hook",
        "path",
        "--home",
        "{home}",
        "--settings",
        "x{settings}y",
    ]
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 0, payload


@pytest.mark.parametrize("missing", ["install", "uninstall", "check", "event", "host"])
def test_member_hook_missing_any_command_refused(tmp_path, missing):
    manifest = real_manifest()
    del member(manifest, "passing-notes")["hooks"][0][missing]
    code, _, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 17


@pytest.mark.parametrize(
    "mutate",
    [
        lambda h: h.pop("locate"),
        lambda h: h.update(kind="script"),
        lambda h: h.update(timeout=0),
        lambda h: h.update(name="Pre Tool"),
        lambda h: h.update(extra=True),
    ],
    ids=["no-locate", "unknown-kind", "zero-timeout", "bad-name", "extra-field"],
)
def test_file_hook_shape_refused(tmp_path, mutate):
    manifest = real_manifest()
    mutate(member(manifest, "tripwire")["hooks"][0])
    code, _, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 17


def test_member_hook_without_settings_flag_refused(tmp_path):
    manifest = real_manifest()
    member(manifest, "passing-notes")["hooks"][0]["check"] = [
        "passing-notes",
        "hook",
        "check",
    ]
    code, _, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 17


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: member(m, "tripwire").update(ring="default"),
        lambda m: member(m, "tripwire").pop("cli"),
        lambda m: member(m, "tripwire").update(surprise=1),
        lambda m: member(m, "tripwire").update(contract=None),
        lambda m: member(m, "tripwire").update(health=[]),
        lambda m: member(m, "tripwire").update(candidate_note="not a candidate"),
        lambda m: member(m, "mesh-lens").update(candidate_note=None),
        lambda m: member(m, "passing-notes")["skills"].update(names=[]),
        lambda m: member(m, "paper-trail").update(slug="paper_trail"),
        lambda m: m.update(schema_version=0),
        lambda m: m.update(extra=[]),
    ],
    ids=[
        "bad-ring",
        "no-cli",
        "unknown-field",
        "core-without-contract",
        "core-empty-health",
        "note-on-core",
        "candidate-without-note",
        "empty-skill-names",
        "bad-slug",
        "older-than-1",
        "unknown-top-level",
    ],
)
def test_other_shape_violations_exit_20(tmp_path, mutate):
    manifest = real_manifest()
    mutate(manifest)
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 20, payload


def _only_candidate(slug):
    """A one-member manifest (so sort order cannot add a finding)."""
    manifest = real_manifest()
    row = member(manifest, "mesh-lens")
    row.update(slug=slug, repo=None)
    manifest["members"] = [row]
    return manifest


@pytest.mark.parametrize("slug", ["-mesh-lens", "--help", "-", ""])
def test_slug_must_start_with_a_letter_or_digit(tmp_path, slug):
    path = write_manifest(tmp_path, _only_candidate(slug))
    code, payload, _ = run_json("verify", "--manifest", str(path))
    assert code == 20, payload
    assert [item["field"] for item in payload["findings"]] == ["slug"]


def test_one_member_green_anchor(tmp_path):
    """The helper above is valid with an ordinary slug, so the 20s are the slug's."""
    path = write_manifest(tmp_path, _only_candidate("mesh-lens"))
    code, payload, _ = run_json("verify", "--manifest", str(path))
    assert code == 0, payload


@pytest.mark.parametrize("cli", ["-x", "--help", ".", "..", ".tripwire", "a/b", ""])
def test_cli_must_be_a_bare_command_name(tmp_path, cli):
    manifest = real_manifest()
    member(manifest, "tripwire")["cli"] = cli
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 20, payload
    assert [item["field"] for item in payload["findings"]] == ["cli"]


@pytest.mark.parametrize("cli", ["tripwire", "x.exe", "A9_b-c", "a.."])
def test_cli_bare_names_accepted(tmp_path, cli):
    manifest = real_manifest()
    member(manifest, "tripwire")["cli"] = cli
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 0, payload


def test_skill_names_and_hook_names_must_start_with_a_letter_or_digit(tmp_path):
    manifest = real_manifest()
    member(manifest, "passing-notes")["skills"]["names"] = ["-lane-open"]
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest, "a.json"))
    )
    assert code == 20 and [f["field"] for f in payload["findings"]] == ["skills.names"]
    manifest = real_manifest()
    member(manifest, "tripwire")["hooks"][0]["name"] = "-pretool"
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest, "b.json"))
    )
    assert code == 17 and [f["field"] for f in payload["findings"]] == ["hooks[0].name"]


def _set_health(argv):
    return lambda m: member(m, "tripwire").update(health=argv)


def _set_locate(argv):
    return lambda m: member(m, "tripwire")["hooks"][0].update(locate=argv)


def _set_member_hook(key, argv):
    return lambda m: member(m, "passing-notes")["hooks"][0].update({key: argv})


def _set_installer(key, argv):
    return lambda m: member(m, "passing-notes")["skills"].update({key: argv})


def _set_setup_write(install):
    return lambda m: member(m, "switchboard").update(
        setup_write={"install": install, "uninstall": None}
    )


UNSAFE_COMMANDS = [
    ("health-leading-hyphen", _set_health(["-tripwire", "--version"]), "health[0]"),
    ("health-double-hyphen", _set_health(["--version"]), "health[0]"),
    ("health-relative-path", _set_health(["../tripwire", "--version"]), "health[0]"),
    ("health-absolute-path", _set_health(["C:/bin/tripwire.exe"]), "health[0]"),
    ("health-token", _set_health(["{home}/tripwire"]), "health[0]"),
    ("health-dot", _set_health(["."]), "health[0]"),
    ("locate", _set_locate(["--help"]), "hooks[0].locate[0]"),
    (
        "member-hook-install",
        _set_member_hook("install", ["-x", "--settings", "{settings}"]),
        "hooks[0].install[0]",
    ),
    (
        "member-hook-check",
        _set_member_hook("check", ["sh -c", "--settings", "{settings}"]),
        "hooks[0].check[0]",
    ),
    ("installer", _set_installer("installer", ["-uv", "run"]), "skills.installer[0]"),
    (
        "uninstaller",
        _set_installer("uninstaller", ["..", "run"]),
        "skills.uninstaller[0]",
    ),
    (
        "setup-write",
        _set_setup_write(["-switchboard", "apply", "--write"]),
        "setup_write.install[0]",
    ),
]


@pytest.mark.parametrize(
    "mutate, field",
    [(p[1], p[2]) for p in UNSAFE_COMMANDS],
    ids=[p[0] for p in UNSAFE_COMMANDS],
)
def test_argv_command_must_be_a_bare_command_name(tmp_path, mutate, field):
    manifest = real_manifest()
    mutate(manifest)
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == companions.EXIT_COMMAND == 21, payload
    assert [(item["check"], item["field"]) for item in payload["findings"]] == [
        ("command", field)
    ]


def test_setup_write_with_a_bare_command_is_accepted(tmp_path):
    """Green anchor for the setup-write row above."""
    manifest = real_manifest()
    _set_setup_write(["switchboard", "apply", "--write"])(manifest)
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 0, payload


def test_every_exit_code_is_documented():
    doc = companions.__doc__
    codes = {
        value
        for name, value in vars(companions).items()
        if name.startswith("EXIT_") and isinstance(value, int)
    }
    assert codes == {0, 2} | set(companions.CHECK_NAMES)
    for code in codes:
        assert re.search(r"^    %d\s+\S" % code, doc, re.MULTILINE), code


def test_unreadable_manifests_exit_3(tmp_path):
    assert (
        run_tool("verify", "--manifest", str(tmp_path / "absent.json")).returncode == 3
    )
    broken = tmp_path / "broken.json"
    broken.write_bytes(b'{"schema_version": 1, "members": [')
    assert run_tool("verify", "--manifest", str(broken)).returncode == 3
    repeated = tmp_path / "repeated.json"
    repeated.write_bytes(b'{"schema_version": 1, "schema_version": 1, "members": []}')
    assert run_tool("verify", "--manifest", str(repeated)).returncode == 3
    bom = tmp_path / "bom.json"
    bom.write_bytes(b"\xef\xbb\xbf" + MANIFEST.read_bytes())
    assert run_tool("verify", "--manifest", str(bom)).returncode == 3


def test_several_findings_exit_with_the_lowest_code(tmp_path):
    manifest = real_manifest()
    _tag_not_semver(manifest)
    _core_member_without_caller(manifest)
    code, payload, _ = run_json(
        "verify", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 13
    assert sorted(item["code"] for item in payload["findings"]) == [13, 16]


# --- inspect -------------------------------------------------------------------


def test_inspect_lists_every_row_by_ring():
    code, payload, _ = run_json("inspect")
    assert code == 0
    assert payload["schema_version"] == 1
    assert payload["rings"] == {
        "candidate": [
            "changed-check",
            "drift-ranger",
            "mesh-lens",
            "paper-trail",
        ],
        "core": ["passing-notes", "switchboard", "tripwire"],
        "optional": ["find-again"],
    }
    rows = {row["slug"]: row for row in payload["members"]}
    assert rows["passing-notes"]["skills"] == [
        "lane-close",
        "lane-handoff",
        "lane-open",
        "lane-status",
    ]


def test_inspect_installable_follows_ring_and_tag(tmp_path):
    manifest = with_null_tags(real_manifest())
    member(manifest, "tripwire")["tag"] = "v0.1.0"
    member(manifest, "mesh-lens")["tag"] = "v0.1.0"
    code, payload, _ = run_json(
        "inspect", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 0, payload
    installable = sorted(
        row["slug"] for row in payload["members"] if row["installable"]
    )
    # A tagged candidate is still not installable; an untagged core member is not.
    assert installable == ["tripwire"]


def test_inspect_refuses_a_newer_schema_version(tmp_path):
    manifest = real_manifest()
    _newer_schema_version(manifest)
    code, payload, _ = run_json(
        "inspect", "--manifest", str(write_manifest(tmp_path, manifest))
    )
    assert code == 10
    assert payload["error"]["check"] == "newer-schema-version"


# Malformed shapes verify reports; inspect must report the same code as JSON
# (round-1 finding: ring [] crashed inspect with a TypeError traceback).
MALFORMED = [
    ("ring-list", lambda m: member(m, "tripwire").update(ring=[])),
    ("ring-object", lambda m: member(m, "tripwire").update(ring={})),
    ("ring-null", lambda m: member(m, "tripwire").update(ring=None)),
    ("slug-list", lambda m: member(m, "tripwire").update(slug=[])),
    ("slug-object", lambda m: member(m, "tripwire").update(slug={"a": 1})),
    ("slug-missing", lambda m: member(m, "tripwire").pop("slug")),
    ("member-number", lambda m: m["members"].append(1)),
    ("member-list", lambda m: m["members"].insert(0, [])),
    ("members-string", lambda m: m.update(members="x")),
    ("members-missing", lambda m: m.pop("members")),
    ("schema-version-string", lambda m: m.update(schema_version="1")),
    ("schema-version-float", lambda m: m.update(schema_version=2.5)),
    ("schema-version-list", lambda m: m.update(schema_version=[])),
    ("hooks-string", lambda m: member(m, "tripwire").update(hooks="x")),
    ("hook-list", lambda m: member(m, "tripwire").update(hooks=[[]])),
    ("hook-kind-list", lambda m: member(m, "tripwire")["hooks"][0].update(kind=[])),
    ("hook-name-list", lambda m: member(m, "tripwire")["hooks"][0].update(name=[])),
    ("hook-host-list", lambda m: member(m, "tripwire")["hooks"][0].update(host=[])),
    ("skills-list", lambda m: member(m, "passing-notes").update(skills=[])),
    (
        "skills-names-nested",
        lambda m: member(m, "passing-notes")["skills"].update(names=[[]]),
    ),
    (
        "skills-installer-object",
        lambda m: member(m, "passing-notes")["skills"].update(installer={}),
    ),
    ("callers-string", lambda m: member(m, "tripwire").update(callers="x")),
    ("caller-list", lambda m: member(m, "tripwire").update(callers=[[]])),
    ("caller-object", lambda m: member(m, "tripwire").update(callers=[{}])),
    ("tag-list", lambda m: member(m, "tripwire").update(tag=[])),
    ("repo-object", lambda m: member(m, "tripwire").update(repo={})),
    ("contract-list", lambda m: member(m, "tripwire").update(contract=[])),
    (
        "contract-fields-wrong-type",
        lambda m: member(m, "tripwire").update(
            contract={"name": [], "schema_version": []}
        ),
    ),
    ("setup-write-list", lambda m: member(m, "tripwire").update(setup_write=[])),
    ("setup-nested", lambda m: member(m, "tripwire").update(setup=[[]])),
    ("health-object", lambda m: member(m, "tripwire").update(health={})),
    ("health-nested", lambda m: member(m, "tripwire").update(health=[["x"]])),
    ("cli-list", lambda m: member(m, "tripwire").update(cli=[])),
    ("note-list", lambda m: member(m, "mesh-lens").update(candidate_note=[])),
]


@pytest.mark.parametrize(
    "mutate", [p[1] for p in MALFORMED], ids=[p[0] for p in MALFORMED]
)
def test_inspect_reports_every_malformed_shape_as_verify_does(tmp_path, mutate):
    manifest = real_manifest()
    mutate(manifest)
    path = write_manifest(tmp_path, manifest)
    verify_code, verify_payload, _ = run_json("verify", "--manifest", str(path))
    inspect_code, inspect_payload, _ = run_json("inspect", "--manifest", str(path))
    assert verify_code in companions.CHECK_NAMES, verify_payload
    assert inspect_code == verify_code, inspect_payload
    assert inspect_payload["exit_code"] == inspect_code
    assert inspect_payload["error"]["code"] == inspect_code
    assert "members" not in inspect_payload
    assert inspect_payload["findings"] == verify_payload["findings"]


@pytest.mark.parametrize(
    "document", [[], "x", None, 1, True], ids=["list", "string", "null", "int", "bool"]
)
def test_a_manifest_that_is_not_an_object_exits_20_for_both(tmp_path, document):
    path = tmp_path / "companions.json"
    path.write_bytes(json.dumps(document).encode("ascii"))
    for command in ("verify", "inspect"):
        code, payload, _ = run_json(command, "--manifest", str(path))
        assert code == 20, (command, payload)


@pytest.mark.parametrize(
    "name, plant, code, check", PLANTED, ids=[p[0] for p in PLANTED]
)
def test_inspect_refuses_every_planted_fixture_with_its_code(
    tmp_path, name, plant, code, check
):
    manifest = real_manifest()
    plant(manifest)
    path = write_manifest(tmp_path, manifest)
    exit_code, payload, _ = run_json("inspect", "--manifest", str(path))
    assert exit_code == code, payload
    assert payload["error"]["check"] == check


# --- Unreadable: every load failure is exit 3 with JSON -----------------------


def _deep_text(depth):
    return "[" * depth + "]" * depth


@pytest.mark.parametrize(
    "text",
    [
        "[" * 100000,
        _deep_text(100000),
        '{"schema_version": 1, "members": ' + _deep_text(5000) + "}",
        '{"schema_version": 1, "members": [], "x": NaN}',
        '{"schema_version": Infinity, "members": []}',
        '{"schema_version": 1, "members": [-Infinity]}',
    ],
    ids=[
        "100000-open-brackets",
        "100000-balanced",
        "5000-deep-members",
        "nan",
        "infinity",
        "minus-infinity",
    ],
)
@pytest.mark.parametrize("command", ["verify", "inspect"])
def test_unparseable_json_exits_3_with_json(tmp_path, text, command):
    path = tmp_path / "companions.json"
    path.write_bytes(text.encode("ascii"))
    code, payload, _ = run_json(command, "--manifest", str(path))
    assert code == companions.EXIT_UNREADABLE == 3, payload
    assert payload["exit_code"] == 3
    findings = payload["findings"]
    assert [item["check"] for item in findings] == ["unreadable"]


def _nested_setup(depth):
    """A manifest whose total nesting is depth (object, members, member, setup...)."""
    manifest = real_manifest()
    value = "x"
    for _ in range(depth - 3):
        value = [value]
    member(manifest, "tripwire")["setup"] = value
    return manifest


@pytest.mark.parametrize("command", ["verify", "inspect"])
def test_nesting_limit_boundary(tmp_path, command):
    limit = companions.MAX_NESTING
    assert companions._nesting_depth(real_manifest()) < limit
    at_limit = write_manifest(tmp_path, _nested_setup(limit), "at.json")
    over_limit = write_manifest(tmp_path, _nested_setup(limit + 1), "over.json")
    # At the limit the manifest loads; setup is still the wrong shape (20).
    assert run_json(command, "--manifest", str(at_limit))[0] == 20
    code, payload, _ = run_json(command, "--manifest", str(over_limit))
    assert code == 3, payload
    assert "nests deeper" in payload["findings"][0]["message"]


@pytest.mark.parametrize("args", [("inspect",), ("verify",), ("verify", "--release")])
def test_output_is_deterministic_json_with_lf(args):
    first = run_tool(*args)
    second = run_tool(*args)
    assert first.stdout == second.stdout
    assert b"\r" not in first.stdout
    assert first.stdout.endswith(b"\n")
    payload = json.loads(first.stdout)
    assert (
        first.stdout.decode("ascii")
        == json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )


# --- read-only -----------------------------------------------------------------


def _tree_hash(root):
    entries = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_dir():
            entries.append((rel, "dir"))
        else:
            entries.append((rel, hashlib.sha256(path.read_bytes()).hexdigest()))
    return entries


def _checkout_state():
    """Hashes of the checkout files the tool reads, plus its tools/ and config/ listings."""
    return (
        [hashlib.sha256(p.read_bytes()).hexdigest() for p in (MANIFEST, SCHEMA, TOOL)],
        sorted(p.name for p in (REPO_ROOT / "tools").iterdir()),
        sorted(p.name for p in (REPO_ROOT / "config").iterdir()),
    )


def test_verify_and_inspect_write_no_byte(tmp_path):
    """Hash a copied tree the tool reads, and the checkout's own tool directory.

    The copied tool runs in the copied tree (default manifest and root), and the
    checkout's tool runs against the copied tree (--manifest, --root), so a write
    beside either tool, into its cwd, or into the tree it reads is caught.
    """
    tree = tmp_path / "tree"
    for rel in ("tools/companions.py", "config/companions.json"):
        (tree / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, tree / rel)
    for row in real_manifest()["members"]:
        for caller in row["callers"]:
            if not caller.startswith("member:"):
                (tree / caller).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO_ROOT / caller, tree / caller)
    before = _tree_hash(tmp_path)
    checkout_before = _checkout_state()
    copied_tool = tree / "tools" / "companions.py"
    pointed = [
        "--manifest",
        str(tree / "config" / "companions.json"),
        "--root",
        str(tree),
    ]
    runs = []
    for args in (["verify"], ["verify", "--release"], ["inspect"]):
        runs.append([str(copied_tool), *args])
        runs.append([str(TOOL), *args, *pointed])
    for argv in runs:
        proc = subprocess.run(
            [sys.executable, *argv],
            cwd=str(tree),
            capture_output=True,
            timeout=60,
        )
        assert proc.returncode in (0, 19), proc.stdout
        assert proc.stdout
    assert _tree_hash(tmp_path) == before
    assert _checkout_state() == checkout_before


def test_tool_uses_only_the_standard_library():
    source = TOOL.read_text(encoding="ascii")
    imported = set(re.findall(r"^(?:from|import) ([a-zA-Z_]+)", source, re.MULTILINE))
    assert imported <= {
        "__future__",
        "argparse",
        "json",
        "re",
        "sys",
        "pathlib",
        "typing",
    }, imported
    assert "open(" not in source.replace('open(path, "rb")', "")


# --- The schema agrees with what verify enforces -------------------------------


def schema():
    with open(SCHEMA, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def test_schema_parses_as_draft_2020_12():
    doc = schema()
    assert doc["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert doc["required"] == list(companions.TOP_LEVEL_KEYS)
    assert doc["additionalProperties"] is False
    assert doc["properties"]["schema_version"] == {"const": companions.SCHEMA_VERSION}


def test_schema_member_fields_match_the_tool():
    defs = schema()["$defs"]
    assert defs["member"]["required"] == list(companions.MEMBER_KEYS)
    assert sorted(defs["member"]["properties"]) == sorted(companions.MEMBER_KEYS)
    assert defs["member"]["properties"]["ring"]["enum"] == list(companions.RINGS)
    assert defs["member"]["if"]["properties"]["ring"]["enum"] == list(
        companions.INSTALLED_RINGS
    )
    assert defs["contract"]["required"] == list(companions.CONTRACT_KEYS)
    assert defs["skills"]["required"] == list(companions.SKILLS_KEYS)
    assert defs["setup_write"]["required"] == list(companions.SETUP_WRITE_KEYS)
    assert defs["file_hook"]["required"] == list(companions.HOOK_KEYS["file"])
    assert defs["member_hook"]["required"] == list(companions.HOOK_KEYS["member"])
    assert defs["file_hook"]["properties"]["host"]["enum"] == list(
        companions.HOOK_HOSTS
    )
    assert (
        defs["file_hook"]["properties"]["timeout"]["maximum"]
        == companions.HOOK_TIMEOUT_MAX
    )
    kinds = [ref["$ref"].rsplit("/", 1)[1] for ref in defs["hook"]["oneOf"]]
    assert [defs[k]["properties"]["kind"]["const"] for k in kinds] == list(
        companions.HOOK_KINDS
    )


def test_schema_patterns_match_the_tool():
    defs = schema()["$defs"]
    props = defs["member"]["properties"]
    assert props["slug"]["pattern"] == companions.SLUG_PATTERN
    assert props["cli"]["pattern"] == companions.CLI_PATTERN
    assert props["repo"]["oneOf"][0]["pattern"] == companions.REPO_PATTERN
    assert props["tag"]["oneOf"][0]["pattern"] == companions.TAG_PATTERN
    assert defs["argv"]["items"]["pattern"] == companions.ARGV_ITEM_PATTERN
    assert props["health"]["items"]["pattern"] == companions.ARGV_ITEM_PATTERN
    # argv[0], the command, follows the cli rule in every argv.
    assert defs["argv"]["prefixItems"] == [
        {"type": "string", "pattern": companions.CLI_PATTERN}
    ]
    assert props["health"]["prefixItems"] == defs["argv"]["prefixItems"]
    assert (
        defs["file_hook"]["properties"]["name"]["pattern"]
        == companions.HOOK_NAME_PATTERN
    )
    assert (
        defs["skills"]["properties"]["names"]["items"]["pattern"]
        == companions.SLUG_PATTERN
    )


@pytest.mark.parametrize(
    "path",
    [
        "skills/plan-feature/core.md",
        "_shared/lane_inbox.py",
        "../x",
        "/x",
        "C:/x",
        "a\\b",
        "a//b",
        "a/./b",
        "a/",
        ".",
        "a:b",
        "a/b.md:stream",
        "memberx:y",
        "a\tb",
        "a\x00b",
        "a\x7fb",
        "member:hooks/claude/tripwire-pretool.ps1",
        "member:",
        "member:/x",
        "member:../x",
        "member:a/../x",
        "member:C:/x",
        "member:a:b",
        "member:a//b",
        "member:a/",
        "member:a\\b",
        "member:a\nb",
    ],
)
def test_schema_caller_pattern_agrees_with_the_tool_on_path_form(path):
    forbidden = schema()["$defs"]["caller"]["not"]["pattern"]
    schema_ok = re.search(forbidden, path) is None
    tool_ok = companions._caller_form_error(path) is None
    assert schema_ok == tool_ok, path


# --- Optional: the schema itself, when jsonschema is installed ---------------


def _validator():
    jsonschema = pytest.importorskip("jsonschema")
    return jsonschema.Draft202012Validator(schema())


def test_schema_accepts_the_real_and_a_tagged_manifest():
    validator = _validator()
    assert list(validator.iter_errors(real_manifest())) == []
    assert list(validator.iter_errors(with_installed_tags(real_manifest()))) == []


# Planted fixtures the schema can express on its own (the rest need verify).
SCHEMA_REFUSES = [
    ("repo-not-github", _repo_not_github),
    ("tag-not-semver", _tag_not_semver),
    ("newer-schema-version", _newer_schema_version),
    ("member-hook-missing-uninstall", _member_hook_missing_uninstall),
    ("argv-unknown-token", _argv_unknown_token),
    ("core-member-no-caller", _core_member_without_caller),
    ("ring-list", lambda m: member(m, "tripwire").update(ring=[])),
    ("slug-leading-hyphen", lambda m: member(m, "tripwire").update(slug="-tripwire")),
    ("cli-dot-dot", lambda m: member(m, "tripwire").update(cli="..")),
    ("health-command-hyphen", _set_health(["-tripwire", "--version"])),
    ("locate-command-hyphen", _set_locate(["--help"])),
    (
        "caller-colon",
        lambda m: member(m, "find-again").update(callers=["skills/a.md:stream"]),
    ),
    ("note-on-core", lambda m: member(m, "tripwire").update(candidate_note="x")),
    (
        "candidate-without-note",
        lambda m: member(m, "mesh-lens").update(candidate_note=None),
    ),
]


@pytest.mark.parametrize(
    "mutate", [p[1] for p in SCHEMA_REFUSES], ids=[p[0] for p in SCHEMA_REFUSES]
)
def test_schema_refuses_what_verify_refuses(tmp_path, mutate):
    validator = _validator()
    manifest = real_manifest()
    mutate(manifest)
    assert list(validator.iter_errors(manifest)), "schema accepted it"
    assert (
        run_tool(
            "verify", "--manifest", str(write_manifest(tmp_path, manifest))
        ).returncode
        != 0
    )


def test_real_manifest_satisfies_the_schema_patterns():
    """A stdlib spot check of the real manifest against the schema's patterns."""
    defs = schema()["$defs"]
    argv_item = re.compile(defs["argv"]["items"]["pattern"])
    for row in real_manifest()["members"]:
        assert set(row) == set(defs["member"]["required"])
        assert re.fullmatch(
            defs["member"]["properties"]["slug"]["pattern"], row["slug"]
        )
        for item in row["health"]:
            assert argv_item.fullmatch(item)
        for hook in row["hooks"]:
            kind = "file_hook" if hook["kind"] == "file" else "member_hook"
            assert set(hook) == set(defs[kind]["required"])
