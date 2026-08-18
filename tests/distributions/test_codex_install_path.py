"""The codex install path: temp-home round trip, refusal parity, and the migration
vocabulary/discovery-root coupling (Phase CP Step 5, #122).

WHAT THIS FILE IS FOR
---------------------
Step 5 made codex INSTALLABLE. Three things had to become true together, and each of
them is a separate failure this module pins:

1. **The pipeline smoke gate.** An automated round trip through the REAL components --
   `build-distributions.ps1 -Provider codex`, `install-skill-mesh.ps1 -Provider codex`,
   `inspect-host-install.ps1`, `probe-codex-skills.ps1`, then `-Uninstall` -- against a
   DISPOSABLE home, with a path guard proving zero writes outside it. No mocks, no
   stubs, no model calls, and no invocation of the `codex` CLI. This is the test that
   would catch a codex install path that escapes its home.

2. **Refusal parity.** The write-ahead-hardened installer refuses to delete on a
   missing / malformed / inconsistent `owned_file_hashes`. Adding a provider must not
   create a lane where that refusal is weaker, so the codex lane is held to the same
   refusals its claude/gpt siblings are.

3. **The sequencing guard.** The manifest's top-level `providers.codex` vocabulary key
   and codex's entry in `tools/skill-mesh-discovery.ps1` MUST land together: the
   migrator loads the vocabulary into `$script:KnownProviders` and `New-MigrationPlan`
   emits a hard `UNKNOWN_PROVIDER_ROOT` blocker (exit 2, whole migration refused) for
   any declared provider the discovery map has no root for. Step 3 deferred the key for
   exactly this reason. `test_migration_plan_has_no_unknown_provider_root_blocker_for
   _codex` is the regression guard, and it ships with a red-on-garbage anchor that
   plants an undeclared provider in a COPY of the repo and proves the blocker still
   fires -- otherwise a future refactor could delete the guard and leave this green.

NO REAL HOME IS EVER TOUCHED. Every install/inspect/uninstall here targets a
`tmp_path` home via `-Home`. `_real_home_fingerprint` additionally records whether the
operator's own `~/.agents/skills` and `~/.skill-mesh-install.json` exist, before and
after, so an escape would fail loudly rather than be argued about. It reads no content
and echoes no absolute path.

Style matches its siblings in this directory: shell out to powershell.exe via
subprocess, use tmp_path, skipif cleanly when powershell is not on PATH.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"
INSTALL_SCRIPT = REPO_ROOT / "tools" / "install-skill-mesh.ps1"
INSPECT_SCRIPT = REPO_ROOT / "tools" / "inspect-host-install.ps1"
MIGRATE_SCRIPT = REPO_ROOT / "tools" / "migrate-legacy-install.ps1"
PROBE_SCRIPT = REPO_ROOT / "tools" / "probe-codex-skills.ps1"
DISCOVERY_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-discovery.ps1"
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"

PROVIDER = "codex"
# The codex discovery root, home-relative POSIX. Spelled once here and immediately
# cross-checked against the shared owner by test_codex_root_is_read_from_the_one_owner,
# so this constant can never silently disagree with the map the tools use.
CODEX_ROOT = ".agents/skills"
LEDGER_NAME = ".skill-mesh-install.json"

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


# TWO detectors, because the two invocation shapes need OPPOSITE treatment of quotes.
#
# CODEX_EXECUTABLE runs against text whose STRING LITERALS ARE INTACT: `& 'codex.exe'`
# is a call whose target exists only inside a quoted span, and nothing in this
# repository legitimately writes an executable file name in prose or a report label.
CODEX_EXECUTABLE = re.compile(r"codex\.(exe|cmd|bat|ps1)", re.I)
# CODEX_INVOCATION runs against text whose string literals are BLANKED: the bare token
# in command position. Blanking is what separates a call from `"codex discovery root"`,
# and a gate that cries wolf on report labels is a gate that gets deleted.
# Command position = start of text/line, a statement separator, a pipeline or grouping
# opener, an assignment (`$v = codex ...` IS a call), or an explicit launcher. A
# `$codex` VARIABLE never matches: `$` is not one of the leads and is not skippable.
CODEX_INVOCATION = re.compile(
    r"(?:\A|[\n;|(&{=]|\bStart-Process\s+|\bInvoke-Expression\s+|\biex\s+)"
    r"\s*&?\s*codex\b",
    re.I)


def _looks_like_codex_call(line):
    """True when `line` invokes the codex CLI, in either shape above."""
    return bool(CODEX_EXECUTABLE.search(line) or
                CODEX_INVOCATION.search(_strip_ps_strings(line)))


def _strip_ps_strings(text):
    """Blank out PowerShell string literals, leaving structure intact.

    Double-quoted first (honoring the backtick escape), then single-quoted (honoring
    the doubled-quote escape). Order matters: a single quote inside a double-quoted
    string is ordinary text, and blanking the double-quoted spans first stops it from
    opening a spurious single-quoted span."""
    text = re.sub(r'"(?:`.|[^"`])*"', '""', text)
    return re.sub(r"'(?:''|[^'])*'", "''", text)


# --------------------------------------------------------------------------- #
# Invocation helpers
# --------------------------------------------------------------------------- #

def _run(script, args, env=None):
    full_env = None
    if env is not None:
        full_env = dict(os.environ)
        full_env.update(env)
    return subprocess.run(
        [PWSH, "-NoProfile", "-NonInteractive", "-File", str(script), *args],
        capture_output=True, text=True, env=full_env)


def _build(out_dir, provider):
    r = _run(BUILD_SCRIPT, ["-OutputDir", str(out_dir), "-Provider", provider])
    assert r.returncode == 0, f"build {provider} failed:\n{r.stdout}\n{r.stderr}"
    return out_dir


def _install(home, dist_dir, uninstall=False, provider=PROVIDER):
    args = ["-Home", str(home), "-Provider", provider, "-DistDir", str(dist_dir)]
    if uninstall:
        args = ["-Home", str(home), "-Provider", provider, "-Uninstall"]
    return _run(INSTALL_SCRIPT, args)


def _inspect_json(home):
    r = _run(INSPECT_SCRIPT, ["-Home", str(home), "-Format", "json"])
    assert r.returncode == 0, f"inspect failed:\n{r.stdout}\n{r.stderr}"
    return json.loads(r.stdout)


def _probe_json(home=None, env=None):
    args = ["-Format", "json"]
    if home is not None:
        args = ["-Home", str(home), *args]
    r = _run(PROBE_SCRIPT, args, env=env)
    return r


def _migrate_plan(home, backup, dist, script=MIGRATE_SCRIPT):
    r = _run(script, ["-Home", str(home), "-BackupDir", str(backup),
                      "-DistDir", str(dist), "-Format", "json"])
    return r


def _ledger(home):
    p = Path(home) / LEDGER_NAME
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Snapshot helpers (the path guard)
# --------------------------------------------------------------------------- #

def _sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def _tree_snapshot(root, exclude=None):
    """rel-posix-path -> sha256, for every file under `root`, skipping `exclude`.

    Content hashes, not mtimes: a write that happens to preserve a timestamp is still
    a write, and this is the guard that has to see it."""
    root = Path(root)
    exclude = Path(exclude).resolve() if exclude is not None else None
    out = {}
    if not root.is_dir():
        return out
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if exclude is not None:
            try:
                p.resolve().relative_to(exclude)
                continue
            except ValueError:
                pass
        out[p.relative_to(root).as_posix()] = _sha256(p)
    return out


def _real_home_fingerprint():
    """Existence-only fingerprint of the paths a codex install could create in the
    OPERATOR's real home. Deliberately not a content or mtime read:

    * content would mean reading the operator's files, which this suite has no
      business doing, and
    * mtime is touched by unrelated tools and would make the guard flaky, which is
      how a real guard gets deleted.

    Existence flips only when something creates or removes these paths -- exactly the
    escape being guarded. The absolute path is never echoed: failures name the
    home-relative label only, so this file stays free of any user path.
    """
    home = Path.home()
    watched = {
        "~/" + CODEX_ROOT: home / Path(*CODEX_ROOT.split("/")),
        "~/" + LEDGER_NAME: home / LEDGER_NAME,
    }
    return {label: p.exists() for label, p in watched.items()}


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def codex_dist(tmp_path_factory):
    """The real codex profile, built once for the module."""
    return _build(tmp_path_factory.mktemp("cdist"), PROVIDER)


@pytest.fixture(scope="module")
def both_dist(tmp_path_factory):
    """`-Provider both` = claude + gpt, deliberately WITHOUT codex.

    Still `release.ps1`'s default and the shape every existing consumer home was built
    from -- and, since codex joined the declared provider vocabulary, no longer a legal
    legacy migration source: the migrator binds every DECLARED provider and refuses an
    artifact that omits one. That refusal is the design, not a gap (see
    `documentation/migration.md`), so this fixture is the negative input the
    completeness cases below are built on.
    """
    return _build(tmp_path_factory.mktemp("bdist"), "both")


@pytest.fixture(scope="module")
def all_dist(tmp_path_factory):
    """`-Provider all` = claude + gpt + codex."""
    return _build(tmp_path_factory.mktemp("adist"), "all")


# --------------------------------------------------------------------------- #
# The map has one owner, and this file agrees with it
# --------------------------------------------------------------------------- #

def test_codex_root_is_read_from_the_one_owner():
    """`CODEX_ROOT` above is the only place this module spells the root. Prove it
    equals what tools/skill-mesh-discovery.ps1 -- the sole owner -- actually returns,
    so every assertion below is anchored to the production value rather than to a
    local guess that could drift."""
    script = ". '" + str(DISCOVERY_SCRIPT).replace("'", "''") + "'\n" \
             "(Get-SkillMeshDiscoveryRoot 'codex')"
    r = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-Command", script],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == CODEX_ROOT


def test_codex_is_a_declared_installable_provider():
    """The vocabulary half of the coupling. Without this key the inspector reports no
    codex provider and the ledger's codex install key is `unrecognized`."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert PROVIDER in manifest["providers"], \
        "config/skill-manifest.json does not declare codex as an installable provider"


# --------------------------------------------------------------------------- #
# THE SMOKE GATE: temp-home round trip with a path guard
# --------------------------------------------------------------------------- #

def test_codex_temp_home_round_trip_writes_only_inside_the_temp_home(codex_dist, tmp_path):
    """install -> inspect -> probe -> uninstall against a disposable home, with real
    components throughout, proving (a) every distribution file lands byte-identical at
    its codex discovery path, (b) the ledger indexes exactly those files with real
    hashes, (c) uninstall removes all of them, and (d) NOTHING outside the temp home
    changed.

    The sandbox holds decoy trees at the OTHER providers' roots and at a plain
    sibling directory, so "wrote to the wrong provider's root" and "escaped the home
    entirely" are distinguishable failures rather than one vague one.
    """
    sandbox = tmp_path / "sb"
    home = sandbox / "home"
    outside = sandbox / "outside"
    home.mkdir(parents=True)
    # Decoys OUTSIDE the home: an install that resolves a root against the wrong base
    # would land here, and the snapshot below would see it.
    for rel in (Path(".claude") / "skills" / "decoy", Path(".github") / "skills" / "decoy",
                Path(*CODEX_ROOT.split("/")) / "decoy", Path("plain")):
        d = outside / rel
        d.mkdir(parents=True)
        (d / "operator.md").write_text("consumer bytes, never ours\n", encoding="utf-8")

    real_home_before = _real_home_fingerprint()
    outside_before = _tree_snapshot(outside)
    sandbox_before = _tree_snapshot(sandbox, exclude=home)
    assert outside_before, "the decoy tree is empty -- the path guard would be vacuous"

    # -- phase 0: the probe reports a clean pre-install home ------------------
    pre = _probe_json(home)
    assert pre.returncode == 0, f"{pre.stdout}\n{pre.stderr}"
    pre = json.loads(pre.stdout)
    assert pre["root"]["state"] == "absent"
    assert pre["ledger"]["state"] == "absent"
    assert pre["codex_cli_invoked"] is False

    # -- phase 1: install -----------------------------------------------------
    r = _install(home, codex_dist)
    assert r.returncode == 0, f"install failed:\n{r.stdout}\n{r.stderr}"

    profile = Path(codex_dist) / PROVIDER
    expected = {p.relative_to(profile).as_posix(): _sha256(p)
                for p in sorted(profile.rglob("*")) if p.is_file()}
    assert expected, "the built codex profile is empty -- the round trip would prove nothing"

    installed_root = home / Path(*CODEX_ROOT.split("/"))
    actual = _tree_snapshot(installed_root)
    assert actual == expected, "installed tree differs from the built codex profile"

    # The OTHER providers' roots inside the home must stay untouched: a codex install
    # writes into its own discovery domain and nowhere else.
    assert not (home / Path(".claude") / "skills").exists()
    assert not (home / Path(".github") / "skills").exists()

    # -- phase 2: the ledger indexes exactly what was installed ---------------
    led = _ledger(home)
    assert led is not None and PROVIDER in led["installs"], "no codex ledger entry"
    entry = led["installs"][PROVIDER]
    assert entry["provider"] == PROVIDER
    assert entry["discovery_subdir"] == CODEX_ROOT
    expected_rels = sorted(f"{CODEX_ROOT}/{rel}" for rel in expected)
    assert sorted(entry["owned_files"]) == expected_rels
    hashes = entry["owned_file_hashes"]
    assert sorted(hashes) == expected_rels, "owned_file_hashes is not a bijection with owned_files"
    for rel, digest in hashes.items():
        assert re.fullmatch(r"[0-9a-f]{64}", digest), (rel, digest)
        assert digest == _sha256(home / Path(*rel.split("/"))), \
            f"the recorded hash for {rel} is not the installed bytes"

    # -- phase 3: the inspector verifies every file and the ledger ------------
    d = _inspect_json(home)
    prof = d["profiles"][PROVIDER]
    assert prof["state"] == "present"
    assert prof["discovery_root"] == CODEX_ROOT
    assert prof["unowned_count"] == 0
    names = {s["name"] for s in prof["skills"]}
    assert names == {p.name for p in installed_root.iterdir() if p.is_dir()}
    assert prof["owned_count"] == len(names), \
        "the inspector found a directory it does not recognize as generated"
    for s in prof["skills"]:
        assert s["owned"] is True, s
        assert s["eligibility"] in {"managed", "shared-payload"}, s
    assert prof["adapter_sample"]["profile_header"] == PROVIDER, \
        "the installed launchers do not identify themselves as the codex profile"
    assert d["ledger"]["state"] == "valid"
    assert d["ledger"]["providers"] == [PROVIDER]
    assert d["ledger"]["unrecognized_provider_count"] == 0, \
        "codex is not in the manifest's provider vocabulary -- the ledger key was dropped"
    assert d["profiles"]["claude"]["state"] == "absent"
    assert d["profiles"]["gpt"]["state"] == "absent"
    assert [w for w in d["warnings"] if w["code"] == "MANAGED_PATH_UNOWNED"] == []

    # -- phase 4: the probe agrees with the inspector -------------------------
    post = _probe_json(home)
    assert post.returncode == 0, f"{post.stdout}\n{post.stderr}"
    post = json.loads(post.stdout)
    assert post["root"]["state"] == "present"
    assert post["root"]["entry_count"] == len(names)
    assert post["root"]["owned_count"] == len(names)
    assert post["ledger"]["state"] == "valid"
    assert post["ledger"]["codex_installed"] is True
    assert post["ledger"]["codex_owned_files"] == len(expected)
    assert post["ledger"]["discovery_subdir_matches_map"] is True
    assert post["codex_cli_invoked"] is False

    # -- phase 5: uninstall removes cleanly -----------------------------------
    r = _install(home, codex_dist, uninstall=True)
    assert r.returncode == 0, f"uninstall failed:\n{r.stdout}\n{r.stderr}"
    assert _tree_snapshot(installed_root) == {}, "uninstall left files behind"
    assert _ledger(home) is None, "uninstall left the ledger behind"
    # Directories legitimately remain: `created_dirs` is audit data, not durable
    # deletion authority, and the installer NEVER removes directories.
    after = _inspect_json(home)
    assert after["profiles"][PROVIDER]["owned_count"] == 0
    assert after["ledger"]["state"] == "absent"

    # -- phase 6: THE PATH GUARD ---------------------------------------------
    assert _tree_snapshot(outside) == outside_before, \
        "the round trip wrote outside the temp home (decoy tree changed)"
    assert _tree_snapshot(sandbox, exclude=home) == sandbox_before, \
        "the round trip wrote outside the temp home (sandbox changed)"
    assert _real_home_fingerprint() == real_home_before, \
        "the round trip created or removed a skill-mesh path in the REAL user home"


def test_codex_reinstall_over_itself_is_idempotent(codex_dist, tmp_path):
    """A rerun must converge without -Force: the installed bytes are already ours and
    already recorded, so the second run is a no-op on both the tree and the ledger."""
    home = tmp_path / "home"
    home.mkdir()
    assert _install(home, codex_dist).returncode == 0
    root = home / Path(*CODEX_ROOT.split("/"))
    tree_after_first = _tree_snapshot(root)
    ledger_after_first = _ledger(home)
    r = _install(home, codex_dist)
    assert r.returncode == 0, f"reinstall failed:\n{r.stdout}\n{r.stderr}"
    assert _tree_snapshot(root) == tree_after_first
    assert _ledger(home) == ledger_after_first


# --------------------------------------------------------------------------- #
# Refusal parity: codex must not be a weaker lane than claude/gpt
# --------------------------------------------------------------------------- #

def _tamper_ledger(home, mutate):
    led = _ledger(home)
    mutate(led["installs"][PROVIDER])
    (Path(home) / LEDGER_NAME).write_text(json.dumps(led), encoding="utf-8")


@pytest.mark.parametrize("label,mutate", [
    ("missing", lambda e: e.pop("owned_file_hashes")),
    ("malformed", lambda e: e["owned_file_hashes"].update(
        {k: "not-a-sha256" for k in list(e["owned_file_hashes"])[:1]})),
    ("inconsistent", lambda e: e["owned_file_hashes"].pop(
        sorted(e["owned_file_hashes"])[0])),
    ("extra_key", lambda e: e["owned_file_hashes"].update(
        {CODEX_ROOT + "/ghost.md": "0" * 64})),
])
def test_codex_uninstall_refuses_a_non_authoritative_hash_map(codex_dist, tmp_path,
                                                              label, mutate):
    """`Get-ValidOwnedHashMap` is all-or-nothing: `owned_files` and
    `owned_file_hashes` must be an exact bijection of 64-hex digests, or the entry
    grants NO destructive authority. Adding a provider must not open a lane where that
    is softer, so each of the four ways the map stops being authority is exercised on
    the codex entry and must leave every installed file on disk."""
    home = tmp_path / "home"
    home.mkdir()
    assert _install(home, codex_dist).returncode == 0
    root = home / Path(*CODEX_ROOT.split("/"))
    before = _tree_snapshot(root)
    assert before, "nothing installed -- the refusal would be vacuous"

    _tamper_ledger(home, mutate)
    r = _install(home, codex_dist, uninstall=True)
    assert r.returncode != 0, f"[{label}] uninstall did NOT refuse:\n{r.stdout}"
    assert "REFUSING uninstall" in (r.stdout + r.stderr), f"[{label}] {r.stdout}\n{r.stderr}"
    assert _tree_snapshot(root) == before, f"[{label}] a refused uninstall deleted files"


def test_codex_uninstall_refuses_when_installed_bytes_changed(codex_dist, tmp_path):
    """Destructive authority is the RECORDED CURRENT-BYTE hash, not the marker and not
    the path. An operator edit to an installed file must survive an uninstall."""
    home = tmp_path / "home"
    home.mkdir()
    assert _install(home, codex_dist).returncode == 0
    root = home / Path(*CODEX_ROOT.split("/"))
    victim = sorted(p for p in root.rglob("SKILL.md"))[0]
    edited = victim.read_text(encoding="utf-8") + "\noperator addition\n"
    victim.write_text(edited, encoding="utf-8")

    r = _install(home, codex_dist, uninstall=True)
    assert r.returncode != 0, f"uninstall did NOT refuse:\n{r.stdout}"
    assert victim.read_text(encoding="utf-8") == edited, "the edited file was deleted"


def test_codex_install_refuses_a_foreign_collision(codex_dist, tmp_path):
    """A pre-existing non-marker file at a codex target refuses the WHOLE install, and
    the refusal is a true no-op (validate-before-mutate)."""
    home = tmp_path / "home"
    root = home / Path(*CODEX_ROOT.split("/")) / "plan-review"
    root.mkdir(parents=True)
    foreign = root / "SKILL.md"
    foreign.write_text("# hand-authored by the operator\n", encoding="utf-8")
    before = _tree_snapshot(home)

    r = _install(home, codex_dist)
    assert r.returncode != 0, f"install did NOT refuse a foreign collision:\n{r.stdout}"
    assert _tree_snapshot(home) == before, "a refused install mutated the home"
    assert _ledger(home) is None


# --------------------------------------------------------------------------- #
# The sequencing guard: providers.codex + its discovery root, together
# --------------------------------------------------------------------------- #

def _blockers(plan_json, code):
    return [b for b in plan_json.get("blocked", []) if b["code"] == code]


@pytest.mark.parametrize("dist_fixture", ["both_dist", "all_dist"])
def test_migration_plan_has_no_unknown_provider_root_blocker_for_codex(
        request, dist_fixture, tmp_path):
    """THE regression guard for the defect Step 3's deferral avoided.

    `tools/migrate-legacy-install.ps1` loads the manifest's top-level `providers` block
    into `$script:KnownProviders`; `New-MigrationPlan` then emits a hard
    `UNKNOWN_PROVIDER_ROOT` blocker -- exit 2, refusing the WHOLE migration in every
    consumer home -- for any declared provider `tools/skill-mesh-discovery.ps1` has no
    root for. Declaring `providers.codex` without the discovery-map entry would
    therefore break the legacy migrator everywhere. This is Step 5's done-when,
    asserted rather than inspected.

    Asserted for BOTH distribution shapes on purpose, because the guard is about the
    VOCABULARY and not about what a given artifact ships: `UNKNOWN_PROVIDER_ROOT` must
    be absent either way. What differs downstream is asserted here too, so the two
    blockers can never be read as one another -- an `all` dist plans completely clean,
    while a `both` dist is refused by the pre-existing completeness rule
    (`MISSING_PROFILE`): a KNOWN root with no shipped profile, never an unknown root.
    The guard itself must still be live; see the red-on-garbage anchor below.
    """
    dist = request.getfixturevalue(dist_fixture)
    home = tmp_path / "h"
    home.mkdir()
    r = _migrate_plan(home, tmp_path / "b", dist)
    plan = json.loads(r.stdout)
    assert _blockers(plan, "UNKNOWN_PROVIDER_ROOT") == [], plan["blocked"]
    if dist_fixture == "all_dist":
        assert r.returncode == 0, f"dry run blocked ({r.returncode}):\n{r.stdout}\n{r.stderr}"
        assert plan["blocked"] == [], plan["blocked"]
    else:
        assert r.returncode == 2, (
            "a `both` dist must be refused while codex is declared -- see "
            f"documentation/migration.md:\n{r.stdout}\n{r.stderr}")
        codes = sorted({b["code"] for b in plan["blocked"]})
        assert codes == ["MISSING_PROFILE"], plan["blocked"]
    # Non-vacuity: codex really is in the vocabulary this run loaded. Without this the
    # test would pass just as happily if the key had never been added.
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert PROVIDER in manifest["providers"]


def test_migration_plan_unknown_provider_root_blocker_still_fires(both_dist, tmp_path):
    """Red-on-garbage anchor for the test above. A guard nobody can see fail is not a
    guard, and the assertion "no UNKNOWN_PROVIDER_ROOT" would stay green forever if the
    blocker were deleted.

    The migrator resolves its manifest as `<script dir>/../config/skill-manifest.json`,
    so the plant is made in a COPY of the tool closure with a COPY of the manifest --
    the committed manifest is never touched."""
    fake = tmp_path / "repo"
    (fake / "tools").mkdir(parents=True)
    (fake / "runtime").mkdir()
    (fake / "config").mkdir()
    for p in (REPO_ROOT / "tools").glob("*.ps1"):
        shutil.copy2(p, fake / "tools" / p.name)
    shutil.copy2(REPO_ROOT / "runtime" / "path-guard.ps1", fake / "runtime" / "path-guard.ps1")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["providers"]["notaprovider"] = {"host": "planted", "transport_default": "none"}
    (fake / "config" / "skill-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    home = tmp_path / "h"
    home.mkdir()
    r = _migrate_plan(home, tmp_path / "b", both_dist,
                      script=fake / "tools" / "migrate-legacy-install.ps1")
    assert r.returncode == 2, f"the planted provider did NOT block:\n{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    hits = _blockers(plan, "UNKNOWN_PROVIDER_ROOT")
    assert len(hits) == 1, plan["blocked"]
    assert "notaprovider" in hits[0]["message"]

    # ...and the SAME planted tree, with codex still declared, produces no codex
    # blocker: the guard fires on the undeclared root, not on codex.
    assert "codex" not in hits[0]["message"]


def test_migration_binds_every_declared_provider_not_the_shipped_subset(
        all_dist, both_dist, tmp_path):
    """Option 3, pinned: the bound set is the MANIFEST's provider vocabulary.

    `New-MigrationPlan` builds `$providerRoots` from `$script:KnownProviders` -- every
    provider the manifest declares -- and the both-profile completeness loop then fires
    `MISSING_PROFILE` for a declared adapter the supplied distribution has no profile
    for. So an `all` dist plans clean and binds all three roots, while a `both` dist is
    REFUSED rather than silently narrowed to claude+gpt.

    The rejected alternative narrowed the bound set to the shipped profiles. That is
    what made a declared-but-unshipped root "unbound", the state three review rounds
    found three silent-orphaning defects in. Refusing an incomplete artifact costs the
    operator one build flag; orphaning costs bytes nobody can find. See
    `documentation/migration.md` and issue #138.
    """
    # (a) Every declared provider is bound, and the codex root is the map's value.
    home = tmp_path / "h-all"
    home.mkdir()
    r = _migrate_plan(home, tmp_path / "b-all", all_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert plan["blocked"] == [], plan["blocked"]
    assert set(plan["provider_roots"]) == {"claude", "gpt", "codex"}, plan["provider_roots"]
    assert plan["provider_roots"][PROVIDER] == CODEX_ROOT
    assert plan["ledger_json"], "the plan carries no ledger"
    assert set(json.loads(plan["ledger_json"])["installs"]) == {"claude", "gpt", "codex"}

    # (b) The SAME vocabulary against a dist that omits codex: refused, and the refusal
    # names the missing profile instead of dropping it from the bound set.
    home2 = tmp_path / "h-both"
    home2.mkdir()
    r2 = _migrate_plan(home2, tmp_path / "b-both", both_dist)
    assert r2.returncode == 2, (
        "a `both` dist was accepted while codex was declared -- the bound set was "
        f"narrowed to the shipped profiles:\n{r2.stdout}\n{r2.stderr}")
    plan2 = json.loads(r2.stdout)
    hits = _blockers(plan2, "MISSING_PROFILE")
    assert hits, plan2["blocked"]
    assert all(h["rel_path"].startswith(PROVIDER + "/") for h in hits), hits
    # Non-vacuity: codex is BOUND even though nothing shipped it. That is the entire
    # difference between this design and the rejected one.
    assert PROVIDER in plan2["provider_roots"], plan2["provider_roots"]


def test_an_incomplete_shipped_profile_still_blocks(all_dist, tmp_path):
    """The other half of the scoping rule, and the property it must NOT weaken: a
    profile the distribution DOES ship must be complete. Removing one codex-declaring
    skill from `dist/codex` is a half-built profile nobody chose, and it blocks."""
    broken = tmp_path / "d"
    shutil.copytree(all_dist, broken)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    codex_skills = sorted(s["name"] for s in manifest["skills"] if "codex" in s["providers"])
    assert codex_skills, "no skill declares a codex adapter -- this test would be vacuous"
    shutil.rmtree(broken / PROVIDER / codex_skills[0])

    home = tmp_path / "h"
    home.mkdir()
    r = _migrate_plan(home, tmp_path / "b", broken)
    assert r.returncode == 2, f"an incomplete codex profile did NOT block:\n{r.stdout}"
    plan = json.loads(r.stdout)
    hits = _blockers(plan, "MISSING_PROFILE")
    assert any(h["rel_path"] == f"{PROVIDER}/{codex_skills[0]}" for h in hits), plan["blocked"]


def test_a_home_with_codex_installed_is_not_silently_narrowed_by_a_both_dist(
        codex_dist, both_dist, tmp_path):
    """The wire-shape audit that motivated the rejected guard, re-asked of option 3.

    `New-LedgerJson` builds the replacement ledger from the bound provider set, and the
    `ledger` action REPLACES the consumer's file wholesale. If the bound set were the
    SHIPPED set, a home with codex already installed, migrated from a claude+gpt
    distribution, would have its codex ownership record silently dropped -- files left
    on disk that `install-skill-mesh -Uninstall` could then never remove, because it
    would report codex "not installed".

    Under option 3 that is unreachable without a dedicated guard: codex stays bound, the
    distribution has no codex profile, and `MISSING_PROFILE` refuses the run BEFORE any
    mutation. Same protection, one rule instead of two.
    """
    home = tmp_path / "h"
    home.mkdir()
    assert _install(home, codex_dist).returncode == 0
    root = home / Path(*CODEX_ROOT.split("/"))
    before = _tree_snapshot(root)
    assert before, "nothing installed -- the assertion below would be vacuous"

    r = _migrate_plan(home, tmp_path / "b", both_dist)
    assert r.returncode == 2, f"the narrowing was NOT refused:\n{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert _blockers(plan, "MISSING_PROFILE"), plan["blocked"]
    # Pre-mutation: the refusal costs the home nothing, and the ledger still owns codex.
    assert _tree_snapshot(root) == before
    assert _ledger(home) is not None and PROVIDER in _ledger(home)["installs"]


def test_the_same_home_migrates_cleanly_from_a_distribution_that_includes_codex(
        codex_dist, all_dist, tmp_path):
    """The other half of the refusal above, and what keeps it from being a dead end: the
    operator's named exit -- supply a distribution that ships every declared profile --
    works, and the rewritten ledger still owns the codex files rather than dropping
    them."""
    home = tmp_path / "h"
    home.mkdir()
    assert _install(home, codex_dist).returncode == 0
    r = _migrate_plan(home, tmp_path / "b", all_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert plan["blocked"] == [], plan["blocked"]
    assert set(plan["provider_roots"]) == {"claude", "gpt", "codex"}
    assert set(json.loads(plan["ledger_json"])["installs"]) == {"claude", "gpt", "codex"}


# `test_a_clean_home_is_unaffected_by_the_orphan_guard` and
# `test_a_distribution_shipping_no_profile_blocks` were removed together with the
# rounds-1-2 machinery they anchored: `LEDGER_PROVIDER_NOT_IN_DISTRIBUTION` and
# `NO_PROFILE_IN_DISTRIBUTION` are not blocker codes this tool emits at this tree. The
# inert-for-the-ordinary-case direction they covered is now carried by
# test_migration_plan_has_no_unknown_provider_root_blocker_for_codex[all_dist], which
# asserts `blocked == []` against a clean home. Both are preserved at `aa6c873` for #138.


# --------------------------------------------------------------------------- #
# probe-codex-skills.ps1
# --------------------------------------------------------------------------- #

def test_probe_stops_on_a_home_userprofile_disagreement(tmp_path):
    """The documented resolution rule: HOME and USERPROFILE must name the same
    directory, and a disagreement REPORTS AND STOPS before anything else happens. It
    must never pick a winner -- picking one is how a profile lands in a home the host
    does not read."""
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    before = (_tree_snapshot(a), _tree_snapshot(b))
    r = _probe_json(env={"HOME": str(a), "USERPROFILE": str(b)})
    assert r.returncode == 2, f"a disagreement did NOT stop:\n{r.stdout}\n{r.stderr}"
    assert "HOME_DISAGREEMENT" in r.stderr
    assert r.stdout.strip() == "", "a stopped probe still emitted a report"
    # The stop is BEFORE any read of either candidate, and neither is echoed.
    assert (_tree_snapshot(a), _tree_snapshot(b)) == before
    for path in (str(a), str(b)):
        assert path not in r.stderr, "the probe echoed a candidate home back"


def test_probe_resolves_agreeing_env_without_an_override(tmp_path):
    """Both variables set to the same directory is the ordinary case: it resolves, and
    the report says which variables it came from."""
    home = tmp_path / "h"
    home.mkdir()
    r = _probe_json(env={"HOME": str(home), "USERPROFILE": str(home)})
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    d = json.loads(r.stdout)
    assert d["env_agreement"] == "agree"
    assert d["home_source"] == "HOME+USERPROFILE"
    assert d["home_env_set"] is True and d["userprofile_set"] is True


def test_probe_override_wins_but_still_reports_the_disagreement(tmp_path):
    """-Home is the explicit reviewed override. It silences the STOP, never the
    DIAGNOSIS: a rehearsal report must always say a human chose the home, so it can
    never be mistaken for an unattended resolution."""
    a, b, target = tmp_path / "a", tmp_path / "b", tmp_path / "t"
    for p in (a, b, target):
        p.mkdir()
    r = _probe_json(home=target, env={"HOME": str(a), "USERPROFILE": str(b)})
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    d = json.loads(r.stdout)
    assert d["home_source"] == "override"
    assert d["env_agreement"] == "overridden"
    assert d["env_diagnosis"] == "disagree", \
        "the override hid the disagreement instead of recording it"


def test_probe_reports_a_home_that_does_not_exist_yet(tmp_path):
    """Not a stop: "the home Codex would use is not there yet" is a legitimate
    pre-install answer, and refusing it would make the probe useless on exactly the
    machine it is most needed on."""
    missing = tmp_path / "nope"
    r = _probe_json(home=missing)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    d = json.loads(r.stdout)
    assert d["home_exists"] is False
    assert d["root"]["state"] == "home-absent"
    assert missing.exists() is False, "the probe CREATED the home it was asked about"


def test_probe_is_read_only(codex_dist, tmp_path):
    """Byte-level proof over a populated home: a probe run changes nothing at all."""
    home = tmp_path / "home"
    home.mkdir()
    assert _install(home, codex_dist).returncode == 0
    before = _tree_snapshot(home)
    assert before, "nothing installed -- the read-only proof would be vacuous"
    assert _probe_json(home).returncode == 0
    text = _run(PROBE_SCRIPT, ["-Home", str(home)])
    assert text.returncode == 0, text.stderr
    assert _tree_snapshot(home) == before, "the probe mutated the home"


def test_probe_never_invokes_the_codex_cli():
    """Phase CP Step 5 ships NO codex invocation anywhere. A probe that shelled out to
    the CLI would make its answers depend on a host being installed, and would turn a
    read-only preflight into something that can fail for reasons it cannot report.

    Comments are stripped first so the probe's own prose may keep saying the word; the
    two detectors above then split "mention" from "call" by what quoting means for each
    invocation shape."""
    text = PROBE_SCRIPT.read_text(encoding="utf-8")
    code = re.sub(r"<#.*?#>", "", text, flags=re.S)     # block comments
    code = re.sub(r"#.*", "", code)                     # line comments
    hits = [ln for ln in code.splitlines() if _looks_like_codex_call(ln)]
    assert not hits, f"probe-codex-skills.ps1 appears to invoke the codex CLI: {hits}"

    # Red-on-garbage anchor. The detector must fire on every invocation SHAPE and stay
    # silent on every mention shape, or "no hits" proves nothing about the detector.
    for call in ("$v = & codex --version",
                 "$v = codex exec 'hi'",
                 "Start-Process codex -ArgumentList 'exec'",
                 "$out = & 'codex.exe' skill list",
                 "$json = codex skill list | ConvertFrom-Json"):
        assert _looks_like_codex_call(call), f"detector missed a call: {call}"
    for label in ('$lines.Add("codex discovery root ($x): state=$y")',
                  "$CODEX_ROOT_REL = Get-SkillMeshDiscoveryRoot 'codex'",
                  "$PROVIDER = 'codex'",
                  "$codexRoot = $report.root"):
        assert not _looks_like_codex_call(label), f"detector fired on a mention: {label}"


def test_probe_reports_the_shared_root_without_claiming_which_host_wrote_it():
    """Design decision D-CP6: `.agents/skills` is ALSO a Copilot active-alternate root,
    the collision is real, and the policy is decided on M1 evidence rather than
    pre-built. The probe must therefore report what is THERE and never attribute it, so
    no guard sneaks in ahead of the evidence."""
    text = PROBE_SCRIPT.read_text(encoding="utf-8")
    assert "D-CP6" in text, "the probe does not record why no collision guard exists"
    assert "parity-deltas.md" in text, "the probe does not point at where M1 records the evidence"


# --------------------------------------------------------------------------- #
# Moved to issue #138 (migrator hardening) -- deliberately NOT rewritten here
# --------------------------------------------------------------------------- #
#
# Rounds 1-2 of Phase CP Step 5 scoped the migration's bound provider set to the
# profiles `-DistDir` ships, which made a single-profile distribution a legal migration
# source and created a new state: an "unbound" known root, declared but not shipped.
# Three review rounds found three successive silent-orphaning defects in the accounting
# built on top of it, and the third is OPEN -- `Get-ChildItem -Recurse` does not descend
# a reparse point, so a NESTED junction never enters the inventory at all, and no amount
# of accounting over what was discovered can prove discovery was complete.
#
# Option 3 was ratified 2026-08-18: Phase CP ships ZERO delta to
# tools/migrate-legacy-install.ps1, the pre-existing completeness rule stands
# (`MISSING_PROFILE`; migrating with codex declared needs a `-Provider all` dist), and
# the unbound-root state is unreachable again.
#
# The ten cases that lived here asserted that rejected design -- `$scanProviderRoots` /
# `$boundProviderRoots`, `UNBOUND_PROVIDER_ROOT_MANAGED_CONTENT`,
# `UNCLASSIFIED_MANAGED_CONTENT`. None of those symbols exist in the tool at this tree,
# so the cases cannot pass, and making them pass by editing the migrator would re-land
# exactly what option 3 rejected. They are not deleted work: implementation and tests
# are preserved at commit `aa6c873` (branch `build-step-1786993911`, tag
# `cp-migrator-rounds12`) for #138 to cherry-pick, along with the `Test-RelStrictlyUnderRoot`
# helper that `test_legacy_migration.py` documents but this tree does not define.
#
# Do not re-add a case here that needs an unbound root. The option-3 property -- a
# distribution omitting a declared profile is REFUSED, never silently narrowed -- is
# pinned above by test_migration_binds_every_declared_provider_not_the_shipped_subset
# and test_an_incomplete_shipped_profile_still_blocks.

# --------------------------------------------------------------------------- #
# probe: a FILE where the discovery directory belongs
# --------------------------------------------------------------------------- #

def test_probe_distinguishes_a_file_at_the_root_from_an_empty_root(tmp_path):
    """`Test-Path` without `-PathType Container` reports a plain FILE at
    `<home>/.agents/skills` as present, `Get-Item` hands back a FileInfo with no reparse
    attribute, and `Get-ChildItem -Directory` over it yields nothing -- so the root used
    to render `state=present, link_type=directory, entry_count=0`, byte-identical to a
    genuine empty, install-ready root.

    M1 is the FIRST real-home install and this probe is what the operator runs first to
    decide whether proceeding is safe, so the two states must never render identically.
    The paired empty-directory case below is what keeps this from passing vacuously."""
    home = tmp_path / "h"
    (home / ".agents").mkdir(parents=True)
    (home / ".agents" / "skills").write_text("not a directory\n", encoding="utf-8")
    r = _probe_json(home)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    root = json.loads(r.stdout)["root"]
    assert root["state"] == "not-a-directory", root
    assert root["link_type"] == "not-a-directory", root
    assert root["entry_count"] == 0

    text = _run(PROBE_SCRIPT, ["-Home", str(home)])
    assert text.returncode == 0, text.stderr
    assert "state=not-a-directory" in text.stdout, text.stdout

    # The pair: a real empty root, which IS install-ready, must still read `present`.
    home2 = tmp_path / "h2"
    (home2 / ".agents" / "skills").mkdir(parents=True)
    r2 = _probe_json(home2)
    assert r2.returncode == 0, f"{r2.stdout}\n{r2.stderr}"
    root2 = json.loads(r2.stdout)["root"]
    assert root2["state"] == "present" and root2["link_type"] == "directory", root2
    assert root2["entry_count"] == 0
    # ...and the probe created nothing while answering either question.
    assert (home / ".agents" / "skills").is_file()
    assert not any((home2 / ".agents" / "skills").iterdir())
