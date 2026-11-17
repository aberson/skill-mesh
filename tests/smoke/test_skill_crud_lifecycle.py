"""Nondestructive lifecycle transitions, black box (Phase CL Step 115, issue #173).

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

The synthetic skill and the exact bytes it authors have one owner,
tests/fixtures/skill_crud_lifecycle.json.
"""
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
import shutil
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


def _install_one_skill(repo, work, label, homes):
    """Build the created skill alone, with the repository's own builder and its own
    regenerated record, and install it into every disposable home."""
    manifest = _json(repo, "config/skill-manifest.json")
    records = [r for r in manifest["skills"] if r["name"] == NAME]
    assert len(records) == 1, records
    one = work / f"one-skill-{label}.json"
    one.write_text(json.dumps({"portable_provider_contract":
                               manifest["portable_provider_contract"],
                               "skills": records}), encoding="utf-8")
    dist = _build(repo, work / f"install-dist-{label}", "-ManifestPath", str(one))
    for provider, home in homes.items():
        proc = _powershell(repo, "install-skill-mesh.ps1", "-Provider", provider,
                           "-Home", str(home), "-DistDir", str(dist))
        assert proc.returncode == 0, f"{provider} install failed:\n{proc.stdout}\n{proc.stderr}"
    return dist


def _installed(home, filename):
    """The one installed copy of the created skill's `filename` in a home. Found by
    walking, so this module does not restate the provider -> discovery-root map
    (tools/skill-mesh-discovery.ps1 owns it)."""
    found = sorted(Path(home).rglob(f"{NAME}/{filename}"))
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

def _state(lc, repo, build_root):
    """Hashes of the repository, the build root and every disposable home, flattened
    to one map keyed by a root label, so a failure names the paths that moved."""
    state = {f"repo/{rel}": sha for rel, sha in _snapshot(repo).items()}
    state.update({f"build/{rel}": sha for rel, sha in _snapshot(build_root).items()})
    for provider, home in lc.homes.items():
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
