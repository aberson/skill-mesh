"""Lifecycle transitions, black box (Phase CL Step 115, issue #173; Step 116, issue #174).

Shape gates (tests/package-integrity) prove what the catalog looks like. They cannot
prove that a CREATE, a READ and an UPDATE flow through the real generator, verifier,
builder and installer without hidden mutation. This module does, end to end, the way
/skill-crud's core runs them (skills/skill-crud/core.md, gate order 1-8):

    request -> inspect -> canonical edit -> tools/gen_manifest.py (+ --check)
            -> tools/skill_catalog.py verify -> tools/build-distributions.ps1 -Provider all
            -> tools/install-skill-mesh.ps1 into a disposable home

DISPOSABLE ONLY. Every command runs against a synthetic Git repository: a fresh copy
of this checkout's tracked catalog sources (skills/, config/, _shared/, runtime/,
tools/ and the expected-inventory fixture) committed into a temporary directory, so
each tool resolves its repository root from its own copy. Builds go to temporary
build roots and installs to temporary homes. Nothing is written into this checkout or
into a real consumer home; test_the_lifecycle_touches_only_disposable_roots checks it.

ONE BUILD OF THE LIFECYCLE. The PowerShell tools are the slow part, so the `lifecycle`
fixture runs the whole CREATE -> READ -> UPDATE sequence once per module and records
what each stage did; the tests below grade that record. The two refusal scenarios
mutate their own copies of the post-CREATE repository.

INSTALLS USE A ONE-SKILL DISTRIBUTION. A full-profile install takes about a minute
per provider on this floor, so the install stage builds the created skill alone with
the same builder from the synthetic repository (-ManifestPath with the skill's own
regenerated record, the one_skill_dist pattern in tests/distributions), and the
installed bytes are checked against the full all-provider build.

DESTRUCTIVE TRANSITIONS (Step 116). The `destructive` fixture RENAMEs and DELETEs
the created probe from one committed base that also carries a live roster naming it
(must-update), frozen evidence naming it (historical-preserve, listed occurrence by
occurrence) and an unrelated note. Each transition runs the same real gates, then
installs its build over a copy of disposable homes that hold the prior all-provider
artifact plus operator files, so stale cleanup is the installer's own ledger-owned
removal and never a second deletion path. The tests grade the exact new live set,
reference disposition, ledger-owned stale removal, customized-file refusal, rollback
by reinstalling the prior artifact, true no-op refusals, and an injected post-write
failure that stops with CATALOG_MUTATION_INCOMPLETE and is repaired from its left diff.

The synthetic skill, the exact bytes it authors and the destructive inputs have one
owner, tests/fixtures/skill_crud_lifecycle.json.
"""
import contextlib
import copy
import functools
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((REPO_ROOT / "tests" / "fixtures" / "skill_crud_lifecycle.json")
                     .read_text(encoding="utf-8"))
NAME = FIXTURE["skill_name"]

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")

# The tracked sources a synthetic repository needs for every tool in the flow: the
# catalog (skills/, config/), the generator and verifier (tools/), the expected-
# inventory fixture the generator writes, and what the builder and installer load
# (_shared/, runtime/path-guard.ps1, tools/*.ps1). Enumerated with `git ls-files`,
# never hand-listed, so a new tracked source is copied without editing this module.
SOURCE_PATHSPECS = ("skills", "config", "_shared", "runtime", "tools",
                    "tests/package-integrity/expected_inventory.json")
_GIT_IDENTITY = ("-c", "user.email=lifecycle-test@example.invalid", "-c",
                 "user.name=lifecycle-test", "-c", "commit.gpgsign=false")
LEDGER = ".skill-mesh-install.json"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _git(repo, *args):
    # GIT_OPTIONAL_LOCKS=0: a status-style read must not refresh the index, so the
    # test's own reads never show up as a byte change in a repository snapshot.
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=env)
    assert proc.returncode == 0, f"git {args}: {proc.stderr}"
    return proc.stdout


def _commit(repo, message):
    _git(repo, "add", "-A")
    _git(repo, *_GIT_IDENTITY, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD").strip()


def _changed(repo):
    """Paths differing from HEAD, plus untracked files, in porcelain form."""
    out = _git(repo, "status", "--porcelain=v1", "--untracked-files=all", "-z")
    return sorted(entry[3:] for entry in out.split("\0") if entry)


def _snapshot(root):
    """posix-relative path -> SHA-256 of every file under root (.git included)."""
    root = Path(root)
    if not root.exists():
        return {}
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _tree_bytes(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _python(repo, script, *args):
    return subprocess.run([sys.executable, str(repo / script), *args],
                          capture_output=True, text=True)


def _powershell(repo, script, *args):
    return subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File",
                           str(repo / "tools" / script), *args],
                          capture_output=True, text=True)


def _helper(repo, *args):
    """tools/skill_catalog.py as a real process from the repository's own copy."""
    proc = _python(repo, "tools/skill_catalog.py", *args, "--format", "json")
    assert proc.stdout, proc.stderr
    result = json.loads(proc.stdout)
    assert result["exit_code"] == proc.returncode, result
    return proc.returncode, result


def _codes(result):
    return {finding["code"] for finding in result["findings"]}


def _request(operation, base_ref, **fields):
    """The eight-field request of the lifecycle guide's section 6."""
    request = {"operation": operation, "skill_name": NAME, "new_name": None,
               "base_ref": base_ref, "description": None, "capabilities": [],
               "resource_paths": [], "reference_dispositions": []}
    request.update(fields)
    return request


def _verify(repo, request_dir, label, request):
    request_dir.mkdir(parents=True, exist_ok=True)
    path = request_dir / f"{label}.json"
    path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    return _helper(repo, "verify", "--request-file", str(path))


@contextlib.contextmanager
def _no_bytecode():
    saved = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.dont_write_bytecode = saved


def _generator(repo):
    """The repository's own tools/gen_manifest.py, imported without writing bytecode
    into the repository, for its ARTIFACTS constant (the one owner of the three
    generated paths)."""
    spec = importlib.util.spec_from_file_location("gen_manifest_lifecycle",
                                                  repo / "tools" / "gen_manifest.py")
    module = importlib.util.module_from_spec(spec)
    with _no_bytecode():
        spec.loader.exec_module(module)
    return module


def _json(repo, rel):
    return json.loads((repo / rel).read_text(encoding="utf-8"))


def _make_repo(dest):
    listed = subprocess.run(["git", "ls-files", "-z", "--", *SOURCE_PATHSPECS],
                            cwd=REPO_ROOT, capture_output=True, check=True).stdout
    rels = [rel for rel in listed.decode("utf-8").split("\0") if rel]
    assert rels, "git ls-files listed no catalog source"
    for rel in rels:
        src, dst = REPO_ROOT / rel, dest / rel
        assert src.is_file(), f"tracked source missing from the checkout: {rel}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
    (dest / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
    _git(dest, "init", "-q")
    _git(dest, "config", "core.autocrlf", "false")
    return _commit(dest, "synthetic catalog")


def _copy_repo(src, dest):
    """A private copy of a synthetic repository for a scenario that mutates it.

    A copied tree carries index stat data that no longer matches its files, and
    `git diff` (which tools/skill_catalog.py runs) rewrites a stat-stale .git/index
    even with GIT_OPTIONAL_LOCKS=0. Refreshing the copy's index here, before any
    snapshot, makes the copy equivalent to the repository it came from, so a hash
    change after a gate is the gate's write and not the copy's leftover."""
    shutil.copytree(src, dest)
    _git(dest, "update-index", "-q", "--refresh")
    return dest


def _insert_in_block(text, opener, closer, line):
    """Insert `line` as the last entry of the top-level block that starts with the
    `opener` line and ends at the first following `closer` line."""
    lines = text.split("\n")
    starts = [i for i, item in enumerate(lines) if item == opener]
    assert len(starts) == 1, f"{opener!r} occurs {len(starts)} times in gen_manifest.py"
    end = lines.index(closer, starts[0] + 1)
    lines.insert(end, line)
    return "\n".join(lines)


def _write_text(path, text):
    """Write LF text, or CRLF when the file already uses CRLF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and b"\r\n" in path.read_bytes():
        text = text.replace("\n", "\r\n")
    path.write_bytes(text.encode("utf-8"))


def _author_create(repo, providers):
    """Stage 3 of /skill-crud for CREATE: one neutral core, one adapter per provider
    in `providers`, the generator's authoring constants, and the model-mapping row."""
    package = repo / "skills" / NAME
    _write_text(package / "core.md", FIXTURE["core"])
    for provider in providers:
        _write_text(package / "providers" / f"{provider}.md", FIXTURE["adapters"][provider])
    gen = repo / "tools" / "gen_manifest.py"
    text = gen.read_bytes().decode("utf-8").replace("\r\n", "\n")
    text = _insert_in_block(text, "PORTABLE = [", "]", f'    "{NAME}",')
    text = _insert_in_block(text, "DESCRIPTIONS = {", "}",
                            f'    "{NAME}": {json.dumps(FIXTURE["manifest_description"])},')
    text = _insert_in_block(text, "SUPPORT_ASSETS = {", "}", f'    "{NAME}": [],')
    _write_text(gen, text)
    mapping_path = repo / "config" / "model-mapping.json"
    mapping = _json(repo, "config/model-mapping.json")
    mapping["skills"][NAME] = FIXTURE["model_mapping_row"]
    _write_text(mapping_path, json.dumps(mapping, indent=2) + "\n")


def _create_request(base):
    return _request("CREATE", base, description=FIXTURE["manifest_description"],
                    capabilities=FIXTURE["capabilities"])


def _build(repo, out, *extra):
    proc = _powershell(repo, "build-distributions.ps1", "-Provider", "all",
                       "-OutputDir", str(out), *extra)
    assert proc.returncode == 0, f"build failed:\n{proc.stdout}\n{proc.stderr}"
    return out


def _build_subset(repo, work, label, names):
    """Build only `names`, with the repository's own builder and its own regenerated
    records, for every provider (-Provider all)."""
    manifest = _json(repo, "config/skill-manifest.json")
    records = [r for r in manifest["skills"] if r["name"] in names]
    assert sorted(r["name"] for r in records) == sorted(names), records
    subset = work / f"subset-{label}.json"
    subset.write_text(json.dumps({"portable_provider_contract":
                                  manifest["portable_provider_contract"],
                                  "skills": records}), encoding="utf-8")
    return _build(repo, work / f"install-dist-{label}", "-ManifestPath", str(subset))


def _install_into(repo, dist, provider, home):
    """One real install of `dist`'s `provider` profile into a disposable home."""
    return _powershell(repo, "install-skill-mesh.ps1", "-Provider", provider,
                       "-Home", str(home), "-DistDir", str(dist))


def _install_dist(repo, dist, homes):
    for provider, home in homes.items():
        proc = _install_into(repo, dist, provider, home)
        assert proc.returncode == 0, f"{provider} install failed:\n{proc.stdout}\n{proc.stderr}"
    return dist


def _install_one_skill(repo, work, label, homes):
    """Build the created skill alone, with the repository's own builder and its own
    regenerated record, and install it into every disposable home."""
    return _install_dist(repo, _build_subset(repo, work, label, (NAME,)), homes)


def _installed(home, filename, name=NAME):
    """The one installed copy of a skill's `filename` in a home. Found by walking, so
    this module does not restate the provider -> discovery-root map
    (tools/skill-mesh-discovery.ps1 owns it)."""
    found = sorted(Path(home).rglob(f"{name}/{filename}"))
    assert len(found) == 1, f"{home}: {found}"
    return found[0]


def _without(doc, name):
    """A JSON document with every mention of `name` (a list item equal to it, or a
    record whose name is it) and the `counts` block removed."""
    if isinstance(doc, dict):
        return {k: _without(v, name) for k, v in doc.items() if k != "counts"}
    if isinstance(doc, list):
        return [_without(item, name) for item in doc
                if item != name and not (isinstance(item, dict) and item.get("name") == name)]
    return doc


# --------------------------------------------------------------------------- #
# The lifecycle, run once
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def lifecycle(tmp_path_factory):
    real_status = _git(REPO_ROOT, "status", "--porcelain=v1", "-z")
    work = tmp_path_factory.mktemp("skill-crud-lifecycle")
    repo = work / "repo"
    requests = work / "requests"
    base = _make_repo(repo)
    gen = _generator(repo)
    required = _json(repo, "config/skill-manifest.json")["portable_provider_contract"]["required"]
    assert set(FIXTURE["adapters"]) == set(required), (
        "the fixture must author exactly the required adapters", required)
    lc = SimpleNamespace(work=work, repo=repo, base=base, required=required,
                         artifacts=tuple(gen.ARTIFACTS), real_status=real_status,
                         homes={p: work / f"home-{p}" for p in required})
    lc.base_docs = {rel: _json(repo, rel) for rel in
                    lc.artifacts + ("config/model-mapping.json",)}
    lc.base_dist = _build(repo, work / "build-base")

    # CREATE: preflight, edit, regenerate, verify, build, install.
    lc.create_inspect = _helper(repo, "inspect", "--operation", "CREATE", "--name", NAME,
                                "--base-ref", base)
    _author_create(repo, required)
    lc.create_regen = _python(repo, "tools/gen_manifest.py")
    lc.create_check = _python(repo, "tools/gen_manifest.py", "--check")
    lc.create_verify = _verify(repo, requests, "create", _create_request(base))
    lc.create_changed = _changed(repo)
    lc.create_docs = {rel: _json(repo, rel) for rel in lc.base_docs}
    lc.create_dist = _build(repo, work / "build-create")
    lc.create_install_dist = _install_one_skill(repo, work, "create", lc.homes)
    lc.homes_after_create = {p: _tree_bytes(h) for p, h in lc.homes.items()}
    lc.created = _commit(repo, f"CREATE {NAME}")
    # A frozen post-CREATE copy for the refusal scenarios, which mutate their own copy.
    lc.repo_at_create = work / "repo-at-create"
    shutil.copytree(repo, lc.repo_at_create)

    # READ: inspect + verify + the generator's read-only check, hashed around.
    repo_before, homes_before = _snapshot(repo), {p: _snapshot(h) for p, h in lc.homes.items()}
    lc.read_inspect = _helper(repo, "inspect", "--operation", "READ", "--name", NAME)
    lc.read_verify = _verify(repo, requests, "read", _request("READ", None))
    lc.read_check = _python(repo, "tools/gen_manifest.py", "--check")
    lc.read_repo = (repo_before, _snapshot(repo))
    lc.read_homes = (homes_before, {p: _snapshot(h) for p, h in lc.homes.items()})

    # UPDATE: shared behavior changes in the core only.
    lc.update_inspect = _helper(repo, "inspect", "--operation", "UPDATE", "--name", NAME,
                                "--base-ref", lc.created)
    core = repo / "skills" / NAME / "core.md"
    anchor, added = FIXTURE["update"]["anchor"], FIXTURE["update"]["added_behavior"]
    text = core.read_bytes().decode("utf-8")
    assert text.count(anchor) == 1, text
    _write_text(core, text.replace(anchor, anchor + added))
    lc.update_regen = _python(repo, "tools/gen_manifest.py")
    lc.update_check = _python(repo, "tools/gen_manifest.py", "--check")
    lc.update_verify = _verify(repo, requests, "update", _request("UPDATE", lc.created))
    lc.update_changed = _changed(repo)
    lc.update_dist = _build(repo, work / "build-update")
    lc.update_dist_again = _build(repo, work / "build-update-again")
    lc.update_install_dist = _install_one_skill(repo, work, "update", lc.homes)
    lc.homes_after_update = {p: _tree_bytes(h) for p, h in lc.homes.items()}
    return lc


# --------------------------------------------------------------------------- #
# CREATE
# --------------------------------------------------------------------------- #

def test_create_passes_every_gate(lifecycle):
    lc = lifecycle
    rc, result = lc.create_inspect
    assert (rc, result["verdict"], result["findings"]) == (0, "PASS", []), result
    assert lc.create_regen.returncode == 0, lc.create_regen.stderr
    assert lc.create_check.returncode == 0, lc.create_check.stderr
    rc, result = lc.create_verify
    assert (rc, result["verdict"], result["findings"]) == (0, "PASS", []), result


def test_create_writes_exactly_the_canonical_and_generated_surfaces(lifecycle):
    """One core, exactly the required adapters, the two authoring files, and the
    three generated inventories -- no other path in the repository changed."""
    lc = lifecycle
    package = {f"skills/{NAME}/core.md"} | {f"skills/{NAME}/providers/{p}.md"
                                            for p in lc.required}
    expected = package | {"tools/gen_manifest.py", "config/model-mapping.json",
                          *lc.artifacts}
    assert set(lc.create_changed) == expected, sorted(set(lc.create_changed) ^ expected)
    assert set(lc.create_verify[1]["changed_paths"]) == expected
    files = sorted(p.relative_to(lc.repo / "skills" / NAME).as_posix()
                   for p in (lc.repo / "skills" / NAME).rglob("*") if p.is_file())
    assert files == sorted(["core.md"] + [f"providers/{p}.md" for p in lc.required]), files
    assert lc.required == ["claude", "codex"], lc.required


def test_create_records_the_locked_metadata_and_mapping_row(lifecycle):
    lc = lifecycle
    manifest = lc.create_docs["config/skill-manifest.json"]
    records = [r for r in manifest["skills"] if r["name"] == NAME]
    assert records == [{
        "name": NAME, "status": "portable",
        "description": FIXTURE["manifest_description"],
        "core": f"skills/{NAME}/core.md",
        "providers": {p: f"skills/{NAME}/providers/{p}.md" for p in lc.required},
        "capabilities": FIXTURE["capabilities"], "local_capable": False,
        "origin": "canonical", "migration": None, "support_assets": [],
    }], records
    assert list(records[0]["providers"]) == lc.required
    mapping = lc.create_docs["config/model-mapping.json"]
    assert mapping["skills"][NAME] == FIXTURE["model_mapping_row"]
    assert mapping["skills"][NAME]["gpt"] is False, "no GPT adapter ships"
    rest = copy.deepcopy(mapping)
    del rest["skills"][NAME]
    assert rest == lc.base_docs["config/model-mapping.json"], "the mapping changed beyond the row"


def test_create_adds_the_skill_to_all_three_generated_inventories_and_nothing_else(
        lifecycle):
    lc = lifecycle
    for rel in lc.artifacts:
        before, after = lc.base_docs[rel], lc.create_docs[rel]
        assert NAME not in json.dumps(before), rel
        assert NAME in json.dumps(after), f"{rel} does not carry {NAME}"
        assert _without(after, NAME) == _without(before, NAME), (
            f"{rel} changed beyond the new skill and its counts")
        bumped = {"total", "portable", *lc.required, *FIXTURE["capabilities"]}
        for key, value in after["counts"].items():
            delta = 1 if key in bumped else 0
            assert value == before["counts"][key] + delta, (rel, key)
    inventory = [s for s in lc.create_docs["skills/inventory.json"]["skills"]
                 if s["name"] == NAME]
    assert len(inventory) == 1 and inventory[0]["status"] == "portable", inventory
    expected = lc.create_docs["tests/package-integrity/expected_inventory.json"]
    assert NAME in expected["portable"] and NAME in expected["codex"]
    assert NAME not in expected["provider_native"]


def test_create_build_adds_only_the_new_skill_to_the_required_profiles(lifecycle):
    """Base build vs post-CREATE build of every provider: the only difference is the
    created skill's launcher and core in each required profile. GPT is optional and
    no GPT adapter was authored, so the GPT profile does not change."""
    lc = lifecycle
    before, after = _tree_bytes(lc.base_dist), _tree_bytes(lc.create_dist)
    assert set(before) <= set(after)
    added = set(after) - set(before)
    assert added == {f"{p}/{NAME}/{leaf}" for p in lc.required
                     for leaf in ("SKILL.md", "core.md")}, sorted(added)
    changed = [rel for rel in before if before[rel] != after[rel]]
    assert not changed, f"a CREATE changed existing build output: {changed[:5]}"
    assert not (lc.create_dist / "gpt" / NAME).exists()


def test_create_installs_the_built_bytes_into_every_required_home(lifecycle):
    """Graded on the homes as the CREATE install left them (the fixture records them
    before the UPDATE reinstalls over the same homes)."""
    lc = lifecycle
    for provider, installed in lc.homes_after_create.items():
        assert LEDGER in installed, provider
        for leaf in ("SKILL.md", "core.md"):
            copies = [rel for rel in installed if rel.endswith(f"/{NAME}/{leaf}")]
            assert len(copies) == 1, (provider, leaf, copies)
            built = (lc.create_dist / provider / NAME / leaf).read_bytes()
            assert installed[copies[0]] == built, (provider, leaf)


# --------------------------------------------------------------------------- #
# READ
# --------------------------------------------------------------------------- #

def test_read_passes_and_changes_no_byte(lifecycle):
    lc = lifecycle
    for rc_result in (lc.read_inspect, lc.read_verify):
        rc, result = rc_result
        assert (rc, result["verdict"], result["findings"]) == (0, "PASS", []), result
    assert lc.read_check.returncode == 0, lc.read_check.stderr
    before, after = lc.read_repo
    assert before and after == before, "a READ changed a byte of the repository"
    homes_before, homes_after = lc.read_homes
    for provider in lc.required:
        assert homes_before[provider], f"the {provider} home was empty before the READ"
        assert homes_after[provider] == homes_before[provider], (
            f"a READ changed a byte of the {provider} home")


# --------------------------------------------------------------------------- #
# UPDATE
# --------------------------------------------------------------------------- #

def test_update_passes_every_gate_and_touches_only_the_core(lifecycle):
    lc = lifecycle
    rc, result = lc.update_inspect
    assert (rc, result["verdict"], result["findings"]) == (0, "PASS", []), result
    assert lc.update_regen.returncode == 0, lc.update_regen.stderr
    assert lc.update_check.returncode == 0, lc.update_check.stderr
    rc, result = lc.update_verify
    assert (rc, result["verdict"], result["findings"]) == (0, "PASS", []), result
    assert lc.update_changed == [f"skills/{NAME}/core.md"], lc.update_changed
    assert result["changed_paths"] == [f"skills/{NAME}/core.md"]


def test_update_propagates_into_the_claude_and_codex_builds(lifecycle):
    """The new core behavior reaches each required profile's core, and nothing else
    in any profile moves: launchers, other skills and the shared payload keep their
    bytes."""
    lc = lifecycle
    marker = FIXTURE["update"]["added_behavior"].strip()
    before, after = _tree_bytes(lc.create_dist), _tree_bytes(lc.update_dist)
    assert set(after) == set(before)
    changed = {rel for rel in before if before[rel] != after[rel]}
    assert changed == {f"{p}/{NAME}/core.md" for p in lc.required}, sorted(changed)
    for provider in lc.required:
        assert marker not in before[f"{provider}/{NAME}/core.md"].decode("utf-8")
        assert marker in after[f"{provider}/{NAME}/core.md"].decode("utf-8"), provider


def test_update_propagates_into_the_claude_and_codex_installs(lifecycle):
    """Reinstalling over the post-CREATE homes replaces exactly the core (and the
    ledger's record of it) with the updated build's bytes."""
    lc = lifecycle
    marker = FIXTURE["update"]["added_behavior"].strip()
    for provider, home in lc.homes.items():
        core = _installed(home, "core.md")
        assert core.read_bytes() == (lc.update_dist / provider / NAME / "core.md").read_bytes()
        assert marker in core.read_text(encoding="utf-8"), provider
        assert _installed(home, "SKILL.md").read_bytes() == (
            lc.update_dist / provider / NAME / "SKILL.md").read_bytes()
        before, after = lc.homes_after_create[provider], lc.homes_after_update[provider]
        assert set(after) == set(before), provider
        core_rel = core.relative_to(home).as_posix()
        moved = {rel for rel in before if before[rel] != after[rel]}
        assert moved <= {core_rel, LEDGER} and core_rel in moved, (provider, sorted(moved))


def test_a_gpt_profile_still_builds_cleanly(lifecycle):
    """GPT is optional while it exists: the all-provider build (which exited 0) still
    emits the GPT profile for the skills that carry a gpt adapter, and the created
    skill, which carries none, is simply absent from it."""
    lc = lifecycle
    manifest = _json(lc.repo, "config/skill-manifest.json")
    gpt = sorted(r["name"] for r in manifest["skills"] if "gpt" in r.get("providers", {}))
    assert gpt, "the catalog no longer declares a GPT adapter; drop this check with V4-7"
    emitted = sorted(d.name for d in (lc.update_dist / "gpt").iterdir()
                     if d.is_dir() and d.name != "_shared")
    assert emitted == gpt
    assert NAME not in emitted


def test_repeated_all_provider_builds_are_byte_identical(lifecycle):
    lc = lifecycle
    first, second = _tree_bytes(lc.update_dist), _tree_bytes(lc.update_dist_again)
    assert {rel.split("/", 1)[0] for rel in first} >= {"claude", "codex", "gpt"}
    assert set(first) == set(second), sorted(set(first) ^ set(second))[:5]
    differ = [rel for rel in first if first[rel] != second[rel]]
    assert not differ, f"non-deterministic build output: {differ[:5]}"


# --------------------------------------------------------------------------- #
# Refusals are true no-ops
# --------------------------------------------------------------------------- #

def _state(lc, repo, build_root, homes=None):
    """Hashes of the repository, the build root and every disposable home, flattened
    to one map keyed by a root label, so a failure names the paths that moved."""
    state = {f"repo/{rel}": sha for rel, sha in _snapshot(repo).items()}
    state.update({f"build/{rel}": sha for rel, sha in _snapshot(build_root).items()})
    for provider, home in (lc.homes if homes is None else homes).items():
        state.update({f"home-{provider}/{rel}": sha for rel, sha in _snapshot(home).items()})
    return state


def _moved(before, after):
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


def test_a_missing_required_adapter_is_a_true_noop(lifecycle, tmp_path):
    """An UPDATE that drops the created skill's codex adapter runs the public gates:
    the generator refuses to regenerate, --check reports a validation failure, the
    verifier reports MISSING_REQUIRED_ADAPTER, and the builder -- the Step 112 gate,
    reached here through the real regenerated manifest rather than a planted one --
    refuses the whole build. None of them writes a byte to the repository, to the
    build root holding the last good build, or to either installed home."""
    lc = lifecycle
    repo = _copy_repo(lc.repo_at_create, tmp_path / "repo")
    build_root = tmp_path / "build"
    shutil.copytree(lc.create_dist, build_root)
    adapter = repo / "skills" / NAME / "providers" / "codex.md"
    adapter.unlink()
    before = _state(lc, repo, build_root)
    for provider in lc.homes:
        assert any(k.startswith(f"home-{provider}/") for k in before), provider

    regen = _python(repo, "tools/gen_manifest.py")
    check = _python(repo, "tools/gen_manifest.py", "--check")
    rc, result = _verify(repo, tmp_path / "requests", "missing-adapter",
                         _request("UPDATE", lc.created))
    build = _powershell(repo, "build-distributions.ps1", "-Provider", "all",
                        "-OutputDir", str(build_root))

    assert regen.returncode != 0 and NAME in regen.stderr, regen.stderr
    assert check.returncode == 3 and "validation failed" in check.stderr, check.stderr
    assert rc == 3 and "MISSING_REQUIRED_ADAPTER" in _codes(result), result
    assert any(NAME in (f["path"] or "") for f in result["findings"]
               if f["code"] == "MISSING_REQUIRED_ADAPTER"), result
    output = build.stdout + build.stderr
    assert build.returncode != 0, f"the builder accepted a skill without codex:\n{output}"
    assert "every required provider" in output and NAME in output, output
    after = _state(lc, repo, build_root)
    assert after == before, ("a refused gate changed a byte: " + str(_moved(before, after)))


def test_a_create_without_a_required_adapter_stops_at_regeneration(lifecycle, tmp_path):
    """The same defect in a CREATE: the run stops at stage 4 (the generator refuses
    and writes none of the three inventories) and the verifier, run to report the
    finding, writes nothing either. The flow never reaches the builder or a home."""
    lc = lifecycle
    repo = _copy_repo(lc.repo_at_create, tmp_path / "repo")
    base = _git(repo, "rev-parse", "HEAD").strip()
    name = f"{NAME}-partial"
    package = repo / "skills" / name
    _write_text(package / "core.md", FIXTURE["core"].replace(NAME, name))
    _write_text(package / "providers" / "claude.md",
                FIXTURE["adapters"]["claude"].replace(NAME, name))
    gen = repo / "tools" / "gen_manifest.py"
    text = gen.read_bytes().decode("utf-8").replace("\r\n", "\n")
    text = _insert_in_block(text, "PORTABLE = [", "]", f'    "{name}",')
    text = _insert_in_block(text, "DESCRIPTIONS = {", "}", f'    "{name}": "Partial.",')
    text = _insert_in_block(text, "SUPPORT_ASSETS = {", "}", f'    "{name}": [],')
    _write_text(gen, text)
    build_root = tmp_path / "build"
    shutil.copytree(lc.create_dist, build_root)
    before = _state(lc, repo, build_root)

    regen = _python(repo, "tools/gen_manifest.py")
    rc, result = _verify(repo, tmp_path / "requests", "create-partial",
                         {**_request("CREATE", base, description="Partial.",
                                     capabilities=["filesystem"]), "skill_name": name})

    assert regen.returncode != 0 and f"{name} (missing codex)" in regen.stderr, regen.stderr
    assert rc == 3 and "MISSING_REQUIRED_ADAPTER" in _codes(result), result
    after = _state(lc, repo, build_root)
    assert after == before, ("a refused gate changed a byte: " + str(_moved(before, after)))


def test_a_create_collision_is_a_true_noop(lifecycle, tmp_path):
    """A second CREATE of the created name is refused at preflight, before any write,
    by both the inspection and the verifier."""
    lc = lifecycle
    repo = _copy_repo(lc.repo_at_create, tmp_path / "repo")
    base = _git(repo, "rev-parse", "HEAD").strip()
    build_root = tmp_path / "build"
    shutil.copytree(lc.create_dist, build_root)
    before = _state(lc, repo, build_root)

    rc_inspect, inspected = _helper(repo, "inspect", "--operation", "CREATE", "--name", NAME,
                                    "--base-ref", base)
    rc_verify, verified = _verify(repo, tmp_path / "requests", "collision",
                                  _create_request(base))

    for rc, result in ((rc_inspect, inspected), (rc_verify, verified)):
        assert rc == 2 and result["verdict"] == "INVALID_REQUEST", result
        assert "CREATE_COLLISION" in _codes(result), result
    after = _state(lc, repo, build_root)
    assert after == before, ("a refused CREATE changed a byte: " + str(_moved(before, after)))


# --------------------------------------------------------------------------- #
# Destructive transitions: RENAME and DELETE (Phase CL Step 116, issue #174)
# --------------------------------------------------------------------------- #

DESTRUCTIVE = FIXTURE["destructive"]
NEW_NAME = DESTRUCTIVE["new_name"]
COMPANION = DESTRUCTIVE["companion_skill"]
LIVE_DOC = DESTRUCTIVE["live_document"]["path"]
HISTORY_DOC = DESTRUCTIVE["historical_document"]["path"]


@functools.lru_cache(maxsize=None)
def _catalog_module():
    """This checkout's tools/skill_catalog.py, imported without writing bytecode, for
    its old-name token pattern: the one owner of what counts as an occurrence."""
    spec = importlib.util.spec_from_file_location("skill_catalog_lifecycle",
                                                  REPO_ROOT / "tools" / "skill_catalog.py")
    module = importlib.util.module_from_spec(spec)
    with _no_bytecode():
        spec.loader.exec_module(module)
    return module


def _token(name):
    return _catalog_module()._token_patterns(name)[0]


def _swap(text, old, new):
    return _token(old).sub(new, text)


def _read_text(path):
    return Path(path).read_bytes().decode("utf-8").replace("\r\n", "\n")


def _entries(root):
    """The exact state of a disposable home: every file (SHA-256) and directory."""
    root = Path(root)
    return {p.relative_to(root).as_posix():
            "<dir>" if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*"))}


def _skill_files(state, name):
    """The installed files of skill `name` in an `_entries` state."""
    return {rel for rel, sha in state.items()
            if sha != "<dir>" and name in rel.split("/")[:-1]}


def _plant_operator_files(home):
    """Operator files the installer never wrote: one beside the installed skills, one
    at the home root. Every destructive transition must leave them byte-unchanged."""
    spec = DESTRUCTIVE["operator_home_files"]
    root = _installed(home, "SKILL.md", COMPANION).parent.parent
    for path in (root / spec["in_discovery_root"], Path(home) / spec["at_home_root"]):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(spec["text"], encoding="utf-8")


def _dispositions(references):
    """One explicit record per occurrence the inspection reported: the frozen
    evidence document's occurrences are historical-preserve, listed one by one;
    every other occurrence is a live consumer and must-update."""
    records = []
    for ref in references:
        historical = ref["path"] == HISTORY_DOC
        records.append({
            "path": ref["path"], "line": ref["line"], "column": ref["column"],
            "before_sha256": ref["before_sha256"],
            "class": "historical-preserve" if historical else "must-update",
            "rationale": ("Frozen synthetic evidence; its bytes stay unchanged." if historical
                          else "A live consumer of the old name."),
        })
    return records


def _remove_package(repo, name):
    """Remove a canonical package file by file, the core last, then its now-empty
    directories. A directory move is never a rename; this is the removal half."""
    package = repo / "skills" / name
    files = sorted((p for p in package.rglob("*") if p.is_file()),
                   key=lambda p: (p.name == "core.md", p.as_posix()))
    for path in files:
        path.unlink()
    for directory in sorted((p for p in package.rglob("*") if p.is_dir()), reverse=True):
        directory.rmdir()
    package.rmdir()


def _author_rename(repo, old, new):
    """Stage 3 of /skill-crud for RENAME: create the new identity, apply every
    must-update disposition (the generator's constants, the mapping row, the live
    document), then remove the old identity. The generated inventories are left to
    the generator."""
    package = repo / "skills" / old
    for src in sorted(p for p in package.rglob("*") if p.is_file()):
        _write_text(repo / "skills" / new / src.relative_to(package),
                    _swap(_read_text(src), old, new))
    gen = repo / "tools" / "gen_manifest.py"
    text = _read_text(gen)
    assert len(_token(old).findall(text)) == 3, "the probe should sit in three constants"
    _write_text(gen, _swap(text, old, new))
    mapping = _json(repo, "config/model-mapping.json")
    mapping["skills"] = {(new if key == old else key): row
                         for key, row in mapping["skills"].items()}
    _write_text(repo / "config" / "model-mapping.json", json.dumps(mapping, indent=2) + "\n")
    live = repo / LIVE_DOC
    _write_text(live, _swap(_read_text(live), old, new))
    _remove_package(repo, old)


def _author_delete(repo, old):
    """Stage 3 of /skill-crud for DELETE: remove the package, its roster entries and
    its mapping row, and apply the must-update disposition of the live document."""
    _remove_package(repo, old)
    gen = repo / "tools" / "gen_manifest.py"
    lines = _read_text(gen).split("\n")
    kept = [line for line in lines if not _token(old).search(line)]
    assert len(lines) - len(kept) == 3, "the probe should sit in three constants"
    _write_text(gen, "\n".join(kept))
    mapping = _json(repo, "config/model-mapping.json")
    del mapping["skills"][old]
    _write_text(repo / "config" / "model-mapping.json", json.dumps(mapping, indent=2) + "\n")
    live = repo / LIVE_DOC
    _write_text(live, "\n".join(line for line in _read_text(live).split("\n")
                                if not _token(old).search(line)))


def _rename_targets(artifacts):
    """The /skill-crud stage 2 target-path set of the RENAME: both identities, the
    two authoring files, the three generated artifacts and the live consumer the
    reference search found."""
    return [f"skills/{NAME}/", f"skills/{NEW_NAME}/", "config/model-mapping.json",
            "tools/gen_manifest.py", *artifacts, LIVE_DOC]


def _touches(path, targets):
    return any(path == t or (t.endswith("/") and path.startswith(t)) for t in targets)


def _live_hits(repo, name):
    """Every tracked or untracked-not-ignored file that still names `name`."""
    listed = _git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted(rel for rel in listed.split("\0")
                  if rel and (repo / rel).is_file()
                  and _token(name).search((repo / rel).read_bytes().decode("utf-8", "replace")))


def _catalog_names(repo):
    return sorted(r["name"] for r in _json(repo, "config/skill-manifest.json")["skills"])


@pytest.fixture(scope="module")
def destructive(lifecycle):
    """RENAME and DELETE of the created probe, each from the same committed base, each
    through the real request, inspector, generator, verifier, builder and installer.

    THE BASE is the post-CREATE catalog plus three committed documents: a live
    roster naming the probe (must-update), frozen evidence naming it three times
    (historical-preserve), and an unrelated note.

    THE PRIOR ARTIFACT is the base's all-provider build of the probe and a companion
    skill, installed into fresh disposable homes that also hold operator files. Each
    transition installs its own build over a copy of those homes."""
    lc = lifecycle
    work = lc.work / "destructive"
    work.mkdir()
    dx = SimpleNamespace(work=work, requests=work / "requests")
    dx.base_repo = _copy_repo(lc.repo_at_create, work / "base-repo")
    for key in ("live_document", "historical_document", "unrelated_tracked"):
        _write_text(dx.base_repo / DESTRUCTIVE[key]["path"], DESTRUCTIVE[key]["text"])
    dx.base = _commit(dx.base_repo, "live, historical and unrelated consumers")
    dx.base_names = _catalog_names(dx.base_repo)
    assert NAME in dx.base_names and COMPANION in dx.base_names
    assert NEW_NAME not in dx.base_names
    dx.base_docs = {rel: _json(dx.base_repo, rel)
                    for rel in lc.artifacts + ("config/model-mapping.json",)}
    dx.base_build = _build(dx.base_repo, work / "build-base")

    dx.prior_dist = _build_subset(dx.base_repo, work, "prior", (NAME, COMPANION))
    dx.prior_homes = {p: work / f"prior-home-{p}" for p in lc.required}
    _install_dist(dx.base_repo, dx.prior_dist, dx.prior_homes)
    for home in dx.prior_homes.values():
        _plant_operator_files(home)
    dx.prior_state = {p: _entries(h) for p, h in dx.prior_homes.items()}

    def homes_from_prior(label):
        homes = {p: work / f"{label}-home-{p}" for p in lc.required}
        for provider, home in homes.items():
            shutil.copytree(dx.prior_homes[provider], home)
        return homes

    # RENAME
    repo = dx.rename_repo = _copy_repo(dx.base_repo, work / "rename-repo")
    dx.rename_inspect = _helper(repo, "inspect", "--operation", "RENAME", "--name", NAME,
                                "--new-name", NEW_NAME, "--base-ref", dx.base)
    dx.rename_request = _request("RENAME", dx.base, new_name=NEW_NAME,
                                 reference_dispositions=_dispositions(
                                     dx.rename_inspect[1]["references"]))
    _author_rename(repo, NAME, NEW_NAME)
    dx.rename_regen = _python(repo, "tools/gen_manifest.py")
    dx.rename_check = _python(repo, "tools/gen_manifest.py", "--check")
    dx.rename_verify = _verify(repo, dx.requests, "rename", dx.rename_request)
    dx.rename_build = _build(repo, work / "build-rename")
    dx.rename_dist = _build_subset(repo, work, "rename", (NEW_NAME, COMPANION))
    dx.rename_homes = homes_from_prior("rename")
    _install_dist(repo, dx.rename_dist, dx.rename_homes)
    dx.rename_state = {p: _entries(h) for p, h in dx.rename_homes.items()}

    # DELETE
    repo = dx.delete_repo = _copy_repo(dx.base_repo, work / "delete-repo")
    dx.delete_inspect = _helper(repo, "inspect", "--operation", "DELETE", "--name", NAME,
                                "--base-ref", dx.base)
    dx.delete_request = _request("DELETE", dx.base, reference_dispositions=_dispositions(
        dx.delete_inspect[1]["references"]))
    _author_delete(repo, NAME)
    dx.delete_regen = _python(repo, "tools/gen_manifest.py")
    dx.delete_check = _python(repo, "tools/gen_manifest.py", "--check")
    dx.delete_verify = _verify(repo, dx.requests, "delete", dx.delete_request)
    dx.delete_build = _build(repo, work / "build-delete")
    dx.delete_dist = _build_subset(repo, work, "delete", (COMPANION,))
    dx.delete_homes = homes_from_prior("delete")
    _install_dist(repo, dx.delete_dist, dx.delete_homes)
    dx.delete_state = {p: _entries(h) for p, h in dx.delete_homes.items()}
    dx.delete_ledgers = {p: json.loads((h / LEDGER).read_text(encoding="utf-8"))
                         for p, h in dx.delete_homes.items()}

    # DELETE over a customized installed copy of the deleted skill.
    dx.customized_homes = homes_from_prior("customized")
    dx.customized_before, dx.customized_runs, dx.customized_after = {}, {}, {}
    for provider, home in dx.customized_homes.items():
        core = _installed(home, "core.md")
        core.write_bytes(core.read_bytes() + DESTRUCTIVE["customization"].encode("utf-8"))
        dx.customized_before[provider] = _entries(home)
        dx.customized_runs[provider] = _install_into(repo, dx.delete_dist, provider, home)
        dx.customized_after[provider] = _entries(home)

    # Rollback: reinstall the prior all-provider artifact over the post-DELETE homes.
    _install_dist(dx.base_repo, dx.prior_dist, dx.delete_homes)
    dx.rollback_state = {p: _entries(h) for p, h in dx.delete_homes.items()}
    return dx


def _assert_gates_pass(inspected, regen, check, verified):
    rc, result = inspected
    assert (rc, result["verdict"], result["findings"]) == (0, "PASS", []), result
    assert result["references"] and all(r["class"] is None for r in result["references"])
    assert regen.returncode == 0, regen.stderr
    assert check.returncode == 0, check.stderr
    rc, result = verified
    assert (rc, result["verdict"], result["findings"]) == (0, "PASS", []), result


def _assert_history_preserved(dx, repo, request):
    """Every listed historical-preserve occurrence is byte-unchanged; the frozen
    document is the only file that still names the old identity."""
    historical = [d for d in request["reference_dispositions"]
                  if d["class"] == "historical-preserve"]
    assert len(historical) == 3, historical
    assert {d["path"] for d in historical} == {HISTORY_DOC}
    current = (repo / HISTORY_DOC).read_bytes()
    assert current == (dx.base_repo / HISTORY_DOC).read_bytes()
    for record in historical:
        assert hashlib.sha256(current).hexdigest() == record["before_sha256"], record
    assert _live_hits(repo, NAME) == [HISTORY_DOC]


# RENAME ------------------------------------------------------------------------

def test_rename_passes_every_gate(destructive):
    dx = destructive
    _assert_gates_pass(dx.rename_inspect, dx.rename_regen, dx.rename_check, dx.rename_verify)


def test_rename_dispositions_every_occurrence_and_leaves_only_history(destructive):
    """Every must-update occurrence of the old name is absent from the candidate, and
    every listed historical-preserve occurrence is byte-unchanged."""
    dx = destructive
    must = [d for d in dx.rename_request["reference_dispositions"] if d["class"] == "must-update"]
    assert {d["path"] for d in must} == {
        f"skills/{NAME}/core.md", *(f"skills/{NAME}/providers/{p}.md" for p in ("claude", "codex")),
        "tools/gen_manifest.py", LIVE_DOC, *dx.base_docs}, sorted({d["path"] for d in must})
    for record in must:
        path = dx.rename_repo / record["path"]
        assert not path.exists() or not _token(NAME).search(_read_text(path)), record
    _assert_history_preserved(dx, dx.rename_repo, dx.rename_request)
    assert NEW_NAME in _read_text(dx.rename_repo / LIVE_DOC)


def test_rename_yields_the_exact_new_live_set(destructive, lifecycle):
    """The catalog, every generated inventory, the mapping, the source tree and every
    provider build name exactly the base set with the old identity swapped for the
    new one; no other byte of any build moves."""
    dx, lc = destructive, lifecycle
    assert _catalog_names(dx.rename_repo) == sorted(set(dx.base_names) - {NAME} | {NEW_NAME})
    for rel in lc.artifacts:
        before, after = dx.base_docs[rel], _json(dx.rename_repo, rel)
        assert not _token(NAME).search(json.dumps(after)), rel
        assert _without(after, NEW_NAME) == _without(before, NAME), rel
    mapping = _json(dx.rename_repo, "config/model-mapping.json")
    base_mapping = copy.deepcopy(dx.base_docs["config/model-mapping.json"])
    assert mapping["skills"].pop(NEW_NAME) == base_mapping["skills"].pop(NAME)
    assert mapping == base_mapping, "the RENAME changed the mapping beyond the row's key"
    tree = sorted(d.name for d in (dx.rename_repo / "skills").iterdir() if d.is_dir())
    base_tree = sorted(d.name for d in (dx.base_repo / "skills").iterdir() if d.is_dir())
    assert tree == sorted(set(base_tree) - {NAME} | {NEW_NAME})

    before, after = _tree_bytes(dx.base_build), _tree_bytes(dx.rename_build)

    def renamed(rel):
        parts = rel.split("/")
        return "/".join(NEW_NAME if part == NAME else part for part in parts)

    assert set(after) == {renamed(rel) for rel in before}, sorted(
        set(after) ^ {renamed(rel) for rel in before})
    moved = {rel for rel in before if renamed(rel) != rel}
    assert moved == {f"{p}/{NAME}/{leaf}" for p in lc.required
                     for leaf in ("SKILL.md", "core.md")}, sorted(moved)
    for rel in before:
        expected = before[rel]
        if rel in moved:
            expected = _swap(expected.decode("utf-8"), NAME, NEW_NAME).encode("utf-8")
        assert after[renamed(rel)] == expected, rel


def test_rename_install_replaces_the_old_identity_in_every_home(destructive):
    """Installing the post-RENAME build over the prior homes removes every installed
    file of the old identity (unchanged, ledger-owned), installs the new identity's
    built bytes, and leaves the companion skill and the operator files unchanged."""
    dx = destructive
    for provider, after in dx.rename_state.items():
        before = dx.prior_state[provider]
        old_files = _skill_files(before, NAME)
        assert old_files and not _skill_files(after, NAME), provider
        new_files = _skill_files(after, NEW_NAME)
        assert {rel.split("/")[-1] for rel in new_files} == {"SKILL.md", "core.md"}, new_files
        for rel in new_files:
            built = dx.rename_dist / provider / NEW_NAME / rel.split("/")[-1]
            assert after[rel] == hashlib.sha256(built.read_bytes()).hexdigest(), rel
        kept = {rel for rel, sha in before.items() if sha != "<dir>"} - old_files - {LEDGER}
        assert {rel: after.get(rel) for rel in kept} == {rel: before[rel] for rel in kept}, (
            provider, sorted(rel for rel in kept if after.get(rel) != before[rel]))
        assert set(before) - set(after) == old_files, provider
        assert set(after) - set(before) == new_files | {
            rel for rel in after if after[rel] == "<dir>" and NEW_NAME in rel.split("/")}


# DELETE ------------------------------------------------------------------------

def test_delete_passes_every_gate(destructive):
    dx = destructive
    _assert_gates_pass(dx.delete_inspect, dx.delete_regen, dx.delete_check, dx.delete_verify)


def test_delete_removes_the_identity_and_preserves_history(destructive):
    dx = destructive
    assert _catalog_names(dx.delete_repo) == sorted(set(dx.base_names) - {NAME})
    assert not (dx.delete_repo / "skills" / NAME).exists()
    for rel in dx.base_docs:
        assert not _token(NAME).search(json.dumps(_json(dx.delete_repo, rel))), rel
    _assert_history_preserved(dx, dx.delete_repo, dx.delete_request)
    before, after = _tree_bytes(dx.base_build), _tree_bytes(dx.delete_build)
    removed = {rel for rel in before if NAME in rel.split("/")}
    assert removed and set(after) == set(before) - removed, sorted(set(after) ^ set(before))
    assert all(after[rel] == before[rel] for rel in after), "a DELETE changed other build bytes"


def test_delete_install_removes_only_unchanged_ledger_owned_stale_files(destructive):
    """The post-DELETE install drops exactly the deleted skill's installed files --
    each one ledger-owned, with a recorded hash its bytes still matched -- changes no
    other file but the ledger, and the ledger forgets exactly those rows.
    Directories are never removed."""
    dx = destructive
    for provider, after in dx.delete_state.items():
        before = dx.prior_state[provider]
        stale = _skill_files(before, NAME)
        assert stale, provider
        prior_entry = json.loads((dx.prior_homes[provider] / LEDGER).read_text(
            encoding="utf-8"))["installs"][provider]
        for rel in stale:
            assert prior_entry["owned_file_hashes"][rel] == before[rel], rel
        assert set(before) - set(after) == stale, (provider, sorted(set(before) - set(after)))
        assert set(after) <= set(before), provider
        moved = {rel for rel in after if after[rel] != before[rel]}
        assert moved == {LEDGER}, (provider, sorted(moved))
        entry = dx.delete_ledgers[provider]["installs"][provider]
        kept = sorted(set(prior_entry["owned_files"]) - stale)
        assert kept and sorted(entry["owned_files"]) == kept, (provider, entry["owned_files"])
        assert entry["owned_file_hashes"] == {rel: prior_entry["owned_file_hashes"][rel]
                                              for rel in kept}, provider


def test_delete_refuses_a_customized_installed_file_as_a_true_noop(destructive):
    dx = destructive
    for provider, proc in dx.customized_runs.items():
        output = proc.stdout + proc.stderr
        assert proc.returncode != 0, f"{provider} deleted a customized file:\n{output}"
        assert "REFUSING stale removal" in output, output
        before, after = dx.customized_before[provider], dx.customized_after[provider]
        assert after == before, (provider, _moved(before, after))
        core = _installed(dx.customized_homes[provider], "core.md")
        assert DESTRUCTIVE["customization"].encode("utf-8") in core.read_bytes()


def test_reinstalling_the_prior_artifact_restores_the_prior_home_state(destructive):
    """Reinstalling the prior all-provider build over the post-DELETE homes restores
    every file, every byte and every directory, the ledger included."""
    dx = destructive
    for provider, restored in dx.rollback_state.items():
        assert dx.delete_state[provider] != dx.prior_state[provider], "nothing to restore"
        assert restored == dx.prior_state[provider], (
            provider, _moved(dx.prior_state[provider], restored))


# Refusals and recovery ------------------------------------------------------------

def _copy_homes(dx, tmp_path):
    homes = {p: tmp_path / f"home-{p}" for p in dx.prior_homes}
    for provider, home in homes.items():
        shutil.copytree(dx.prior_homes[provider], home)
    return homes


def test_a_rename_name_collision_is_a_true_noop(destructive, lifecycle, tmp_path):
    """A RENAME onto an existing catalog name is refused before any write, by the
    inspection and by the verifier."""
    dx, lc = destructive, lifecycle
    repo = _copy_repo(dx.base_repo, tmp_path / "repo")
    build_root = tmp_path / "build"
    shutil.copytree(dx.base_build, build_root)
    homes = _copy_homes(dx, tmp_path)
    before = _state(lc, repo, build_root, homes)

    rc_inspect, inspected = _helper(repo, "inspect", "--operation", "RENAME", "--name", NAME,
                                    "--new-name", COMPANION, "--base-ref", dx.base)
    rc_verify, verified = _verify(repo, tmp_path / "requests", "collision", {
        **dx.rename_request, "new_name": COMPANION})

    for rc, result in ((rc_inspect, inspected), (rc_verify, verified)):
        assert rc == 2 and result["verdict"] == "INVALID_REQUEST", result
        assert "RENAME_DESTINATION_COLLISION" in _codes(result), result
    after = _state(lc, repo, build_root, homes)
    assert after == before, ("a refused RENAME changed a byte: " + str(_moved(before, after)))


@pytest.mark.parametrize("defect", ["unclassified", "stale"])
def test_an_unclassified_or_stale_disposition_is_a_true_noop(destructive, lifecycle,
                                                             tmp_path, defect):
    """The completed RENAME candidate, verified with a request that leaves one
    occurrence unclassified or carries a stale before_sha256. The verifier refuses,
    so the run stops at stage 5 and never builds or installs; the gate itself writes
    no byte to the repository, the build root or a home."""
    dx, lc = destructive, lifecycle
    repo = _copy_repo(dx.rename_repo, tmp_path / "repo")
    build_root = tmp_path / "build"
    shutil.copytree(dx.base_build, build_root)
    homes = _copy_homes(dx, tmp_path)
    records = copy.deepcopy(dx.rename_request["reference_dispositions"])
    if defect == "unclassified":
        dropped = next(i for i, r in enumerate(records) if r["path"] == LIVE_DOC)
        del records[dropped]
        expected = "have no disposition"
    else:
        target = next(r for r in records if r["class"] == "historical-preserve")
        target["before_sha256"] = hashlib.sha256(b"not the preimage").hexdigest()
        expected = "stale before_sha256"
    before = _state(lc, repo, build_root, homes)

    rc, result = _verify(repo, tmp_path / "requests", defect,
                         {**dx.rename_request, "reference_dispositions": records})

    assert rc != 0 and result["verdict"] != "PASS", result
    assert any(f["code"] == "REFERENCE_DISPOSITION_INVALID" and expected in f["detail"]
               for f in result["findings"]), result
    after = _state(lc, repo, build_root, homes)
    assert after == before, ("a refused gate changed a byte: " + str(_moved(before, after)))


def test_an_injected_post_write_failure_is_incomplete_and_repairable(destructive, lifecycle,
                                                                     tmp_path):
    """A RENAME whose removal of the old identity fails after the first write (the
    old core is made read-only, so deleting it raises). Per the recovery rule the run
    stops with CATALOG_MUTATION_INCOMPLETE, lists the changed paths and cleans
    nothing up; the verifier independently reports the same stop. Unrelated dirty
    work survives untouched, and the left diff alone repairs the tree, after which
    the same RENAME completes and passes."""
    dx, lc = destructive, lifecycle
    repo = _copy_repo(dx.base_repo, tmp_path / "repo")
    unrelated = {DESTRUCTIVE["unrelated_tracked"]["path"]:
                 DESTRUCTIVE["unrelated_tracked"]["dirty_text"],
                 DESTRUCTIVE["unrelated_untracked"]["path"]:
                 DESTRUCTIVE["unrelated_untracked"]["text"]}
    for rel, text in unrelated.items():
        _write_text(repo / rel, text)
    unrelated_bytes = {rel: (repo / rel).read_bytes() for rel in unrelated}

    rc, inspected = _helper(repo, "inspect", "--operation", "RENAME", "--name", NAME,
                            "--new-name", NEW_NAME, "--base-ref", dx.base)
    assert (rc, inspected["findings"]) == (0, []), inspected
    assert inspected["changed_paths"] == sorted(unrelated), "unrelated work is reported"
    targets = _rename_targets(lc.artifacts)
    request = _request("RENAME", dx.base, new_name=NEW_NAME,
                       reference_dispositions=_dispositions(inspected["references"]))

    core = repo / "skills" / NAME / "core.md"
    os.chmod(core, stat.S_IREAD)
    try:
        try:
            _author_rename(repo, NAME, NEW_NAME)
            failure = None
        except OSError as exc:
            failure = exc
    finally:
        os.chmod(core, stat.S_IREAD | stat.S_IWRITE)
    assert failure is not None, "the injected removal failure did not fire"

    # Stage 8: stop, list the changed paths, and clean nothing up.
    status = _changed(repo)
    report = {"verdict": "CATALOG_MUTATION_INCOMPLETE",
              "changed": [p for p in status if _touches(p, targets)],
              "unrelated_preserved": [p for p in status if not _touches(p, targets)]}
    assert report["changed"] == sorted([
        f"skills/{NAME}/providers/claude.md", f"skills/{NAME}/providers/codex.md",
        f"skills/{NEW_NAME}/core.md", f"skills/{NEW_NAME}/providers/claude.md",
        f"skills/{NEW_NAME}/providers/codex.md", "config/model-mapping.json",
        "tools/gen_manifest.py", LIVE_DOC]), report
    assert report["unrelated_preserved"] == sorted(unrelated), report
    assert core.is_file(), "the old identity's core was removed despite the failure"

    rc, verified = _verify(repo, tmp_path / "requests", "incomplete", request)
    assert rc == 3 and verified["verdict"] == "DRIFT", verified
    assert any(f["code"] == "CATALOG_MUTATION_INCOMPLETE" and f["path"] == f"skills/{NAME}"
               for f in verified["findings"]), verified
    assert set(verified["changed_paths"]) == set(report["changed"]) | set(unrelated)
    assert {rel: (repo / rel).read_bytes() for rel in unrelated} == unrelated_bytes

    # Repair from the left diff alone: reverse the tracked hunks it lists, and remove
    # the untracked files it lists.
    untracked = set(_git(repo, "ls-files", "-z", "--others", "--exclude-standard").split("\0"))
    tracked = [p for p in report["changed"] if p not in untracked]
    left = subprocess.run(["git", "diff", "--binary", dx.base, "--", *tracked], cwd=repo,
                          capture_output=True, check=True).stdout
    assert left, "the left diff is empty"
    patch = tmp_path / "left.diff"
    patch.write_bytes(left)
    _git(repo, "apply", "-R", "--binary", str(patch))
    for rel in report["changed"]:
        if rel in untracked:
            (repo / rel).unlink()
    for directory in sorted((repo / "skills" / NEW_NAME).rglob("*"), reverse=True):
        directory.rmdir()
    (repo / "skills" / NEW_NAME).rmdir()
    assert _changed(repo) == sorted(unrelated), "the repair left a target path changed"
    assert {rel: (repo / rel).read_bytes() for rel in unrelated} == unrelated_bytes
    rc, again = _helper(repo, "inspect", "--operation", "RENAME", "--name", NAME,
                        "--new-name", NEW_NAME, "--base-ref", dx.base)
    assert (rc, again["findings"]) == (0, []), again

    _author_rename(repo, NAME, NEW_NAME)
    regen = _python(repo, "tools/gen_manifest.py")
    assert regen.returncode == 0, regen.stderr
    rc, completed = _verify(repo, tmp_path / "requests", "completed", request)
    assert (rc, completed["verdict"], completed["findings"]) == (0, "PASS", []), completed
    assert {rel: (repo / rel).read_bytes() for rel in unrelated} == unrelated_bytes


def test_the_destructive_transitions_touch_only_disposable_roots(destructive, lifecycle):
    dx, lc = destructive, lifecycle
    roots = [dx.base_repo, dx.rename_repo, dx.delete_repo, dx.base_build, dx.rename_build,
             dx.delete_build, dx.prior_dist, dx.rename_dist, dx.delete_dist,
             *dx.prior_homes.values(), *dx.rename_homes.values(),
             *dx.delete_homes.values(), *dx.customized_homes.values()]
    for root in roots:
        resolved = Path(root).resolve()
        assert lc.work.resolve() in resolved.parents, resolved
        assert REPO_ROOT.resolve() not in resolved.parents, resolved
        assert resolved != Path.home().resolve(), resolved
    assert _git(REPO_ROOT, "status", "--porcelain=v1", "-z") == lc.real_status, (
        "the destructive transitions changed this checkout")


# --------------------------------------------------------------------------- #
# Disposable roots only
# --------------------------------------------------------------------------- #

def test_the_lifecycle_touches_only_disposable_roots(lifecycle):
    lc = lifecycle
    top = Path(_git(lc.repo, "rev-parse", "--show-toplevel").strip()).resolve()
    assert top == lc.repo.resolve(), "the synthetic repository is not its own Git root"
    roots = [lc.repo, lc.repo_at_create, lc.base_dist, lc.create_dist, lc.update_dist,
             lc.update_dist_again, lc.create_install_dist, lc.update_install_dist,
             *lc.homes.values()]
    for root in roots:
        resolved = Path(root).resolve()
        assert lc.work.resolve() in resolved.parents, resolved
        assert REPO_ROOT.resolve() not in resolved.parents, resolved
        assert resolved != Path.home().resolve(), resolved
    assert _git(REPO_ROOT, "status", "--porcelain=v1", "-z") == lc.real_status, (
        "the lifecycle changed this checkout")
