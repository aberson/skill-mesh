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

import legacy_install_fixtures as fx

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

    This is the shape every existing consumer home and every default release artifact
    is built from, so it is the shape the migration-vocabulary guard must be green on.
    """
    return _build(tmp_path_factory.mktemp("bdist"), "both")


@pytest.fixture(scope="module")
def all_dist(tmp_path_factory):
    """`-Provider all` = claude + gpt + codex."""
    return _build(tmp_path_factory.mktemp("adist"), "all")


@pytest.fixture(scope="module")
def claude_only_dist(tmp_path_factory):
    """A SINGLE-profile distribution: claude, deliberately without gpt and codex.

    Only a legal input since Step 5 (see "THE ONE DELIBERATE DESIGN CHANGE" in
    `New-MigrationPlan`) -- before it, the completeness rule refused any distribution
    that omitted a declared provider. It is also the shape that made the scan/bind
    conflation reachable, so it is the input every case in the section below is built
    on: two of the three known roots are UNBOUND for this dist.
    """
    return _build(tmp_path_factory.mktemp("cldist"), "claude")


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
    therefore break the legacy migrator everywhere.

    Asserted for BOTH distribution shapes on purpose: the `both` (claude+gpt) shape is
    what every existing consumer home and default release artifact is built from, and
    the `all` shape is the one that actually binds codex. The blocker must be absent
    either way, and the guard itself must still be live -- see the red anchor below.
    """
    dist = request.getfixturevalue(dist_fixture)
    home = tmp_path / "h"
    home.mkdir()
    r = _migrate_plan(home, tmp_path / "b", dist)
    assert r.returncode == 0, f"dry run blocked ({r.returncode}):\n{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert _blockers(plan, "UNKNOWN_PROVIDER_ROOT") == [], plan["blocked"]
    assert plan["blocked"] == [], plan["blocked"]
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


def test_migration_binds_exactly_the_profiles_the_distribution_ships(
        both_dist, all_dist, tmp_path):
    """Phase CP Step 5's scoping rule, pinned.

    `-Provider both` still means claude+gpt and codex must be asked for by name, so
    "declared provider" and "shipped profile" stopped being the same set. A migration
    binds the SHIPPED set: otherwise every migration from a `both` distribution would
    fail MISSING_PROFILE on each codex-declaring skill, and would write an empty codex
    entry into the consumer's ledger claiming a binding that never happened."""
    for dist, expected in ((both_dist, {"claude", "gpt"}),
                           (all_dist, {"claude", "gpt", "codex"})):
        home = tmp_path / ("h-" + "-".join(sorted(expected)))
        home.mkdir()
        r = _migrate_plan(home, tmp_path / ("b-" + str(len(expected))), dist)
        assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
        plan = json.loads(r.stdout)
        assert set(plan["provider_roots"]) == expected, plan["provider_roots"]
        assert plan["ledger_json"], "the plan carries no ledger"
        assert set(json.loads(plan["ledger_json"])["installs"]) == expected
    # The codex root the plan records is the map's value, not a re-spelling.
    home = tmp_path / "h-all2"
    home.mkdir()
    plan = json.loads(_migrate_plan(home, tmp_path / "b-all2", all_dist).stdout)
    assert plan["provider_roots"]["codex"] == CODEX_ROOT


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


def test_migration_blocks_rather_than_orphaning_a_ledger_provider_the_dist_omits(
        codex_dist, both_dist, tmp_path):
    """The consequence of scoping the bound set, caught by auditing the WIRE SHAPE of
    the thing the change feeds: the rewritten ledger.

    `New-LedgerJson` builds the replacement ledger from the bound provider set alone,
    and the `ledger` action REPLACES the consumer's file wholesale. So a home that
    already has codex installed, migrated from a claude+gpt distribution, would have its
    codex ownership record silently dropped -- 11 files left on disk that
    `install-skill-mesh -Uninstall` could then never remove, because it would report
    codex "not installed".

    Before Step 5 this was impossible by construction (the bound set was every declared
    provider). Scoping made it reachable, so it is now an explicit pre-mutation block
    with two named exits."""
    home = tmp_path / "h"
    home.mkdir()
    assert _install(home, codex_dist).returncode == 0
    root = home / Path(*CODEX_ROOT.split("/"))
    before = _tree_snapshot(root)
    assert before, "nothing installed -- the block would be vacuous"

    r = _migrate_plan(home, tmp_path / "b", both_dist)
    assert r.returncode == 2, f"the ledger orphan was NOT blocked:\n{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    hits = _blockers(plan, "LEDGER_PROVIDER_NOT_IN_DISTRIBUTION")
    assert len(hits) == 1, plan["blocked"]
    assert PROVIDER in hits[0]["message"]
    # Pre-mutation: the block costs the home nothing.
    assert _tree_snapshot(root) == before
    assert _ledger(home) is not None and PROVIDER in _ledger(home)["installs"]


def test_the_same_home_migrates_cleanly_from_a_distribution_that_includes_codex(
        codex_dist, all_dist, tmp_path):
    """The other half of the block above, and what keeps it from being a dead end: the
    operator's first named exit (supply a distribution that ships the profile) works."""
    home = tmp_path / "h"
    home.mkdir()
    assert _install(home, codex_dist).returncode == 0
    r = _migrate_plan(home, tmp_path / "b", all_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert plan["blocked"] == [], plan["blocked"]
    assert set(plan["provider_roots"]) == {"claude", "gpt", "codex"}
    # ...and the rewritten ledger still owns the codex files rather than dropping them.
    assert set(json.loads(plan["ledger_json"])["installs"]) == {"claude", "gpt", "codex"}


def test_a_clean_home_is_unaffected_by_the_orphan_guard(both_dist, tmp_path):
    """Red-on-garbage complement: the guard must be INERT for the ordinary case, or it
    would block every migration in the fleet instead of the one that orphans records."""
    home = tmp_path / "h"
    home.mkdir()
    r = _migrate_plan(home, tmp_path / "b", both_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _blockers(json.loads(r.stdout), "LEDGER_PROVIDER_NOT_IN_DISTRIBUTION") == []


def test_a_distribution_shipping_no_profile_blocks(tmp_path):
    """A dist with no recognized profile directory is a bad input, not a narrower
    migration: it must refuse rather than silently plan a ledger rewrite with no
    installs."""
    empty = tmp_path / "d"
    (empty / "notes").mkdir(parents=True)
    (empty / "notes" / "readme.md").write_text("not a profile\n", encoding="utf-8")
    home = tmp_path / "h"
    home.mkdir()
    r = _migrate_plan(home, tmp_path / "b", empty)
    assert r.returncode == 2, f"an empty distribution did NOT block:\n{r.stdout}"
    plan = json.loads(r.stdout)
    assert _blockers(plan, "NO_PROFILE_IN_DISTRIBUTION"), plan["blocked"]


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
# The home is SCANNED whole, even where this distribution does not WRITE
# --------------------------------------------------------------------------- #
#
# Step 5 scoped the migration's provider set to the profiles `-DistDir` ships. That is
# correct for the WRITE side and wrong for the READ side, and the first draft used ONE
# variable for both -- so a known host root the distribution did not ship was never
# scanned, and content under it could not block anything. Reproduced live against the
# real tool: a claude-only distribution plus foreign and legacy-managed-looking content
# under `.github/skills` exited 0 with `blocked: []`, and the root never appeared in the
# plan at all. The same input refused outright before the scoping change.
#
# The tool now keeps two named sets:
#   $scanProviderRoots  -- every known provider root, unconditionally. What must be
#                          accounted for before the first mutation.
#   $boundProviderRoots -- the profiles this dist ships. What this run writes and owns.
# Every case below is paired with its opposite, so neither a guard that never fires nor
# one that fires on everything can pass.
#
# The OVER-fire direction has a third pairing, and it lives in the sibling file because
# that is where the fixture for it already exists: the block keys on CANONICAL residence,
# not on reachability. Get-RootScan returns canonical home-relative paths, so a junction
# planted under an unbound root surfaces files that physically live under a BOUND root or
# under the retired root -- already accounted for by that root's own scan. Blocking on an
# alias would refuse an input the tool accepted before this step. Pinned by
# test_legacy_migration.py::
# test_active_junction_into_retired_tree_removes_retire_authority[agents-child], which
# aliases `.agents/skills` into `.copilot/skills` and must still exit 0; it went RED on
# the first draft of this guard, which is how the over-fire was found.

def _plant_managed_looking(home, root, skill=None):
    """skill-mesh-managed-LOOKING bytes under `root`: a manifest skill directory holding
    a SKILL.md with a real provenance header. This is what a previous install of that
    profile leaves behind, and what the migrator would orphan if it neither rewrote the
    file nor recorded it in the replacement ledger."""
    skill = skill or fx.MIGRATION_MANAGED[0]
    return fx.write(home, root + "/" + skill + "/SKILL.md",
                    fx.generated_skill_md(skill, "gpt"))


def _apply(home, backup, dist):
    return _run(MIGRATE_SCRIPT, ["-Home", str(home), "-BackupDir", str(backup),
                                 "-DistDir", str(dist), "-Apply", "-Format", "json"])


UNBOUND_MANAGED = "UNBOUND_PROVIDER_ROOT_MANAGED_CONTENT"


def test_foreign_content_under_an_unbound_root_still_blocks(claude_only_dist, tmp_path):
    """The reproduction, half one. `.github/skills` is a known host root that a
    claude-only distribution does not bind; a foreign directory there must refuse the
    whole migration exactly as it does under a bound root. Get-RootScan is the only
    place FOREIGN_FILE comes from, so this passes if and only if the root was scanned."""
    home = tmp_path / "h"
    fx.write(home, fx.GPT_ROOT + "/" + fx.FOREIGN_DIR + "/README.md",
             "# operator notes\n\nNot a skill, not managed.\n")
    r = _migrate_plan(home, tmp_path / "b", claude_only_dist)
    assert r.returncode == 2, f"an unbound root was never scanned:\n{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    hits = _blockers(plan, "FOREIGN_FILE")
    assert hits, plan["blocked"]
    assert any(h["rel_path"].startswith(fx.GPT_ROOT + "/") for h in hits), plan["blocked"]
    # ...and the root really was unbound, or this proves nothing about the scan set.
    assert set(plan["provider_roots"]) == {"claude"}, plan["provider_roots"]


@pytest.mark.parametrize("ledger_state", ["absent", "corrupt", "silent-about-gpt"])
def test_managed_content_under_an_unbound_root_refuses(claude_only_dist, tmp_path,
                                                       ledger_state):
    """The reproduction, half two, in the three ledger states the ledger-driven guard
    cannot see.

    `LEDGER_PROVIDER_NOT_IN_DISTRIBUTION` reads the home's ledger through
    `Get-PriorCreatedDirs`, which by its own documented contract yields an EMPTY map for
    a corrupt or old-shape file. So it covers exactly one case -- an intact ledger that
    already names the omitted provider -- and none of these three: a first-time
    migration with no ledger, a corrupt ledger, and an intact ledger that simply does
    not mention gpt. The filesystem-evidence guard covers all three, which is why both
    exist."""
    home = tmp_path / "h"
    planted = _plant_managed_looking(home, fx.GPT_ROOT)
    if ledger_state == "corrupt":
        fx.write(home, LEDGER_NAME, "{ this is not json")
    elif ledger_state == "silent-about-gpt":
        fx.write(home, LEDGER_NAME, fx.ledger(["claude"]))
    before = _tree_snapshot(home)

    r = _migrate_plan(home, tmp_path / "b", claude_only_dist)
    assert r.returncode == 2, f"managed bytes under an unbound root did NOT refuse:\n{r.stdout}"
    plan = json.loads(r.stdout)
    hits = _blockers(plan, UNBOUND_MANAGED)
    assert len(hits) == 1, plan["blocked"]
    assert hits[0]["rel_path"] == fx.GPT_ROOT, hits[0]
    assert "'gpt'" in hits[0]["message"], hits[0]["message"]
    # The OLD guard is silent here: that is the hole this one fills, and asserting it
    # keeps a future edit from "passing" this test through the ledger path instead.
    assert _blockers(plan, "LEDGER_PROVIDER_NOT_IN_DISTRIBUTION") == [], plan["blocked"]
    # No install action ever targeted the unbound root.
    assert not [a for a in plan["actions"]
                if a["action"] == "install" and a["rel_path"].startswith(fx.GPT_ROOT + "/")]

    # Pre-mutation, through -Apply and not just the dry run: the refusal costs the home
    # nothing, and no transaction directory is created.
    ra = _apply(home, tmp_path / "b2", claude_only_dist)
    assert ra.returncode == 2, ra.stdout
    assert _tree_snapshot(home) == before, "a refused migration mutated the home"
    assert planted.is_file()
    assert not (tmp_path / "b2").exists(), "a refused migration created a backup transaction"


def test_the_same_home_without_the_plant_migrates(claude_only_dist, tmp_path):
    """Red-on-garbage pair for the case above: the ONLY difference is the planted
    directory. A guard that refused every single-profile distribution -- which is what
    reverting the scoping outright would do -- fails here."""
    home = tmp_path / "h"
    home.mkdir()
    r = _migrate_plan(home, tmp_path / "b", claude_only_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert plan["blocked"] == [], plan["blocked"]
    assert set(plan["provider_roots"]) == {"claude"}


def test_the_same_plant_is_installed_over_when_the_distribution_binds_it(both_dist,
                                                                        tmp_path):
    """The other red-on-garbage direction: identical bytes at an identical path, and a
    distribution that DOES ship the profile. The blocker must key on bound-ness, not on
    the content -- otherwise it would refuse the ordinary two-profile migration that
    every consumer home in the fleet runs."""
    home = tmp_path / "h"
    planted = _plant_managed_looking(home, fx.GPT_ROOT)
    rel = planted.relative_to(home).as_posix()
    r = _migrate_plan(home, tmp_path / "b", both_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert _blockers(plan, UNBOUND_MANAGED) == [], plan["blocked"]
    assert rel in [a["rel_path"] for a in plan["actions"] if a["action"] == "install"]


def test_consumer_content_under_an_unbound_root_is_preserved_not_blocked(
        claude_only_dist, tmp_path):
    """The refusal is targeted, and this is the direct evidence that the unbound root
    was READ rather than merely not-blocked.

    A consumer's own skill under `.github/skills` is not skill-mesh's to write and not
    skill-mesh's to orphan. It gets the same accounting a bound root would give it -- a
    `preserve` action, hashed, precondition-checked before mutation and verified after --
    and no block. Refusing here would refuse homes this run cannot harm."""
    home = tmp_path / "h"
    fx.write(home, fx.GPT_ROOT + "/my-own-skill/SKILL.md", fx.consumer_skill_md("my-own-skill"))
    r = _migrate_plan(home, tmp_path / "b", claude_only_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert plan["blocked"] == [], plan["blocked"]
    preserved = [a["rel_path"] for a in plan["actions"] if a["action"] == "preserve"]
    assert fx.GPT_ROOT + "/my-own-skill/SKILL.md" in preserved, plan["actions"]
    # ...while the root itself stays out of the bound set and the rewritten ledger.
    assert set(plan["provider_roots"]) == {"claude"}
    assert set(json.loads(plan["ledger_json"])["installs"]) == {"claude"}


def test_managed_content_under_the_unbound_codex_root_refuses(both_dist, all_dist,
                                                              tmp_path):
    """The same invariant for the root this step ADDED, and the one the fleet meets
    first: `-Provider both` is claude+gpt, so `.agents/skills` is unbound for every
    default release artifact. Managed bytes there refuse rather than being orphaned --
    with no ledger in the home at all, which is the first-time-migration case."""
    home = tmp_path / "h"
    _plant_managed_looking(home, CODEX_ROOT)
    assert not (home / LEDGER_NAME).exists(), "the ledger-driven guard must be out of play"
    r = _migrate_plan(home, tmp_path / "b", both_dist)
    assert r.returncode == 2, f"managed bytes under the codex root did NOT refuse:\n{r.stdout}"
    plan = json.loads(r.stdout)
    hits = _blockers(plan, UNBOUND_MANAGED)
    assert len(hits) == 1, plan["blocked"]
    assert hits[0]["rel_path"] == CODEX_ROOT, hits[0]
    assert "'codex'" in hits[0]["message"], hits[0]["message"]

    # The message's first named exit is real: the SAME home migrates from a
    # distribution that ships the profile, and the file becomes an install target.
    r2 = _migrate_plan(home, tmp_path / "b2", all_dist)
    assert r2.returncode == 0, f"{r2.stdout}\n{r2.stderr}"
    plan2 = json.loads(r2.stdout)
    assert plan2["blocked"] == [], plan2["blocked"]
    assert CODEX_ROOT + "/" + fx.MIGRATION_MANAGED[0] + "/SKILL.md" in \
        [a["rel_path"] for a in plan2["actions"] if a["action"] == "install"]


def test_the_scan_set_is_not_the_bound_set_in_the_source(tmp_path):
    """Structural anchor for the split, so a future edit cannot collapse the two names
    back into one and leave the behavioral cases above passing by accident.

    Not a substitute for the behavior tests -- it is the thing that makes THEM stable:
    the home scan must read the scan set, and the ledger writer must read the bound set.
    """
    src = MIGRATE_SCRIPT.read_text(encoding="utf-8")
    assert "$scanProviderRoots" in src and "$boundProviderRoots" in src, \
        "the migrator no longer separates the scanned roots from the bound roots"
    assert not re.search(r"\$providerRoots\b", src), \
        "the conflated $providerRoots variable is back"
    scan_loop = "foreach ($p in @($scanProviderRoots.Keys)) {\n        $scan = Get-RootScan"
    assert scan_loop in src, "the home scan no longer iterates the SCAN set"
    assert "New-LedgerJson $installs $boundProviderRoots" in src, \
        "the ledger writer no longer takes the BOUND set"


# --------------------------------------------------------------------------- #
# The alias that lives nowhere: reached-through versus resident-under
#
# Get-RootScan classifies a tree LEXICALLY -- by the child directory's name under the
# root it is walking -- and records every file CANONICALLY, so an in-home junction
# SPLITS two properties a per-root loop conflates: which scan reached a file, and which
# root the bytes reside under. A file reached through a scanned root but resident under
# NO known root belongs to no root's loop, and until the Step 5 round-3 rewrite it
# received no disposition at all: not installed, not preserved, not retired, not
# advised, absent from the replacement ledger, exit 0. Those are exactly the orphaned
# bytes UNBOUND_PROVIDER_ROOT_MANAGED_CONTENT exists to prevent, reached by a path that
# guard could not see.
#
# The accounting is now per FILE: one table keyed by canonical rel, one exhaustive
# switch on canonical residence (bound / unbound / retired / resident-nowhere), an
# unmatched-zone arm that BLOCKS, and a totality check that proves the pass consumed
# the whole table. The three cases below pin the two live arms and the safety net.
# --------------------------------------------------------------------------- #

# Deliberately outside every root in the discovery map AND outside the retired root,
# so the aliased content resides in no zone the tool knows.
ALIAS_TARGET_REL = "shared-skills/plan-review"
UNCLASSIFIED = "UNCLASSIFIED_MANAGED_CONTENT"


def _plant_alias_to_nowhere(home, root):
    """A manifest-named directory under `root` that is a JUNCTION to an in-home
    location outside every known discovery root, holding marker-bearing bytes.

    The target stays INSIDE the home, so no UNSAFE_LINK escape fires and the only
    question on the table is the one being asked: what disposition does a managed file
    get when the only root that can reach it is not the root it lives under?"""
    skill = fx.MIGRATION_MANAGED[0]
    victim = fx.write(home, ALIAS_TARGET_REL + "/SKILL.md",
                      fx.generated_skill_md(skill, "gpt"))
    link = Path(home) / Path(*root.split("/")) / skill
    if not fx.make_junction(link, Path(home) / Path(*ALIAS_TARGET_REL.split("/"))):
        pytest.skip("cannot create a Windows junction in this environment")
    assert (link / "SKILL.md").is_file(), "the junction plant did not expose the payload"
    return victim


def _fake_tool_closure(dest):
    """A COPY of the tool closure the migrator resolves at runtime, so a mutation for a
    red-on-garbage anchor never touches a committed file. Mirrors the closure
    test_migration_plan_unknown_provider_root_blocker_still_fires already copies."""
    (dest / "tools").mkdir(parents=True)
    (dest / "runtime").mkdir()
    (dest / "config").mkdir()
    for p in (REPO_ROOT / "tools").glob("*.ps1"):
        shutil.copy2(p, dest / "tools" / p.name)
    shutil.copy2(REPO_ROOT / "runtime" / "path-guard.ps1", dest / "runtime" / "path-guard.ps1")
    shutil.copy2(MANIFEST_PATH, dest / "config" / "skill-manifest.json")
    return dest / "tools" / "migrate-legacy-install.ps1"


def test_managed_content_reachable_only_through_an_unbound_root_refuses(
        claude_only_dist, tmp_path):
    """THE regression for the hole that survived two line-scoped fix rounds.

    `.github/skills` is scanned and unbound for a claude-only distribution. A junction
    there named for a manifest skill, pointing at `shared-skills/plan-review`, makes
    marker-bearing skill-mesh bytes reachable through that root while they reside under
    no known root at all. Nothing in this run will rewrite them and nothing will record
    them in the replacement ledger, so the orphaning harm is identical to content that
    sits under the unbound root directly -- and the refusal must be too.

    The residence filter that closed round 2's over-fire assumed an alias always lands
    in ANOTHER scanned root, where that root's own scan accounts for it. Aliases are
    closed under the HOME, not under the four roots, and this is the negation."""
    home = tmp_path / "h"
    victim = _plant_alias_to_nowhere(home, fx.GPT_ROOT)
    assert not (home / LEDGER_NAME).exists(), "the ledger-driven guard must be out of play"
    before = _tree_snapshot(home)

    r = _migrate_plan(home, tmp_path / "b", claude_only_dist)
    assert r.returncode == 2, (
        f"managed bytes reachable only through an unbound root did NOT refuse:\n"
        f"{r.stdout}\n{r.stderr}")
    plan = json.loads(r.stdout)
    hits = _blockers(plan, UNBOUND_MANAGED)
    assert len(hits) == 1, plan["blocked"]
    assert hits[0]["rel_path"] == fx.GPT_ROOT, hits[0]
    assert "'gpt'" in hits[0]["message"], hits[0]["message"]
    # Filesystem evidence only: the ledger-driven half cannot see a home with no ledger.
    assert _blockers(plan, "LEDGER_PROVIDER_NOT_IN_DISTRIBUTION") == [], plan["blocked"]
    # The internal safety net stayed quiet -- a NAMED arm claimed the file, which is
    # the difference between this fix and a catch-all that blocks on confusion.
    assert _blockers(plan, UNCLASSIFIED) == [], plan["blocked"]

    # Pre-mutation, through -Apply and not just the dry run.
    ra = _apply(home, tmp_path / "b2", claude_only_dist)
    assert ra.returncode == 2, ra.stdout
    assert _tree_snapshot(home) == before, "a refused migration mutated the home"
    assert victim.is_file()
    assert not (tmp_path / "b2").exists(), "a refused migration created a backup transaction"


def test_the_same_alias_under_a_bound_root_is_written_through_not_refused(
        claude_only_dist, tmp_path):
    """The red-on-garbage pair, and the evidence for why the two are not symmetric.

    Byte-identical plant, identical junction, one difference: the root that reaches it
    is BOUND. That root has a write lane -- install targets are built from its LEXICAL
    path and resolve through the very junction -- so the shipped bytes are rewritten and
    the replacement ledger records them under that lexical path, where uninstall can
    still find them. There is no orphan to refuse, and a guard that keyed on "aliased"
    instead of "unaccounted-for" would refuse this ordinary home.

    This is also the empirical anchor for the claim the design comment makes about a
    BOUND alias destination, which until now only the retired-root case had."""
    home = tmp_path / "h"
    victim = _plant_alias_to_nowhere(home, fx.CLAUDE_ROOT)
    lexical = fx.CLAUDE_ROOT + "/" + fx.MIGRATION_MANAGED[0] + "/SKILL.md"

    r = _migrate_plan(home, tmp_path / "b", claude_only_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert plan["blocked"] == [], plan["blocked"]
    assert lexical in [a["rel_path"] for a in plan["actions"] if a["action"] == "install"], \
        "the write lane does not reach the aliased path"
    owned = json.loads(plan["ledger_json"])["installs"]["claude"]["owned_files"]
    assert lexical in owned, "the rewritten ledger would not record the aliased path"
    assert victim.is_file()


def test_a_broken_disposition_arm_refuses_instead_of_exiting_zero(
        claude_only_dist, tmp_path):
    """Red-on-garbage anchor for the totality control itself.

    The two cases above prove the arms behave. They cannot prove the SAFETY NET can
    fire, and a net nobody has seen fire is not a net -- which is precisely how this
    defect reached round 3: every earlier version of this code fell through silently
    when no branch matched.

    So: run a pristine COPY of the tool closure against the orphaning fixture (green
    baseline), then break exactly one token -- the residence zone name the
    resident-nowhere arm matches on -- and run the same fixture again. The switch now
    matches no arm. The tool must REFUSE with the internal-invariant code rather than
    exit 0 with undispositioned bytes on disk, and the count check must agree that the
    pass did not consume the whole table."""
    script = _fake_tool_closure(tmp_path / "repo")
    home = tmp_path / "h"
    _plant_alias_to_nowhere(home, fx.GPT_ROOT)

    baseline = _migrate_plan(home, tmp_path / "b", claude_only_dist, script=script)
    assert baseline.returncode == 2, f"{baseline.stdout}\n{baseline.stderr}"
    base_plan = json.loads(baseline.stdout)
    assert _blockers(base_plan, UNBOUND_MANAGED), base_plan["blocked"]
    assert _blockers(base_plan, UNCLASSIFIED) == [], base_plan["blocked"]

    src = script.read_text(encoding="ascii")
    marker = "kind = 'unrooted'"
    assert src.count(marker) == 1, "the resident-nowhere arm is no longer a single token"
    script.write_bytes(src.replace(marker, "kind = 'unrooted-BROKEN'").encode("ascii"))

    broken = _migrate_plan(home, tmp_path / "b2", claude_only_dist, script=script)
    assert broken.returncode == 2, (
        f"a disposition arm that matches nothing exited {broken.returncode} instead of "
        f"refusing:\n{broken.stdout}\n{broken.stderr}")
    plan = json.loads(broken.stdout)
    hits = _blockers(plan, UNCLASSIFIED)
    assert len(hits) == 2, plan["blocked"]
    # One per-file finding naming the unmatched zone, one totality finding proving the
    # pass did not consume the table. Either alone would still refuse; both together
    # are what make a silent fall-through unrepresentable.
    assert any("no residence zone" in h["message"] for h in hits), hits
    assert any("exactly one disposition" in h["message"] for h in hits), hits


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
