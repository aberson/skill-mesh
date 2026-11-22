"""Tests for the companion installer (core companion plan Step 9, issue #288).

The production entry point is `tools/install-skill-mesh.ps1 -Companions core|all`,
which runs `tools/install-companions.ps1` after the skill install. Every test runs
in a disposable home under tmp_path with a PATH built from scratch: fake `uv`,
`git` and `python` shims (each records its argv and working directory to a log
file and never touches the network), a fake uv tool bin directory, and the
Windows system directories. No real installed tool is reached.

Member data is never restated here: the fixture manifest is the real
config/companions.json with pinned tags filled in, and the expected member lists
are read back from it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "config" / "companions.json"
INSTALL_SKILL_MESH = REPO_ROOT / "tools" / "install-skill-mesh.ps1"
INSTALL_COMPANIONS = REPO_ROOT / "tools" / "install-companions.ps1"
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"

SYSTEM_ROOT = Path(os.environ.get("SystemRoot", r"C:\Windows"))
POWERSHELL = SYSTEM_ROOT / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
SYSTEM_PATH = [
    SYSTEM_ROOT / "System32",
    SYSTEM_ROOT / "System32" / "WindowsPowerShell" / "v1.0",
]

TAG = "v9.9.9"
NEW_TAG = "v9.9.10"
COMPANION_LEDGER = ".skill-mesh-companions.json"
SKILL_LEDGER = ".skill-mesh-install.json"
CACHE_DIR = ".skill-mesh-companions"
# The member skill installer's --host values for each Skill Mesh provider, and the
# skills folder under the home that each host's install is pointed at.
SKILL_ROOTS = {"claude": ".claude/skills", "codex": ".agents/skills"}

# One fake for every external command. argv[1] names the role.
FAKE_TOOL = r"""
import json, os, sys
from pathlib import Path

role, args = sys.argv[1], sys.argv[2:]
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"tool": role, "argv": args, "cwd": os.getcwd()}) + "\n")
fail = set(filter(None, os.environ.get("FAKE_FAIL", "").split(",")))
bindir = Path(os.environ["FAKE_TOOL_BIN"])
tooldir = Path(os.environ["FAKE_TOOL_DIR"])
here = Path(__file__).resolve()

def shim(path, target_role):
    path.write_text('@"%s" "%s" %s %%*\r\n@exit /b %%ERRORLEVEL%%\r\n'
                    % (sys.executable, here, target_role), encoding="ascii")

if role == "uv":
    if args[:2] == ["tool", "install"]:
        spec = args[-1]
        repo, tag = spec[len("git+"):].rsplit("@", 1)
        slug = repo.rsplit("/", 1)[1]
        if "uv-install:" + slug in fail:
            sys.stderr.write("error: fake install failure for %s\n" % slug)
            sys.exit(1)
        target = bindir / (slug + ".cmd")
        if target.exists() and "--force" not in args:
            print("`%s` is already installed" % slug)
            sys.exit(0)
        shim(target, "cli:" + slug)
        (bindir / (slug + ".tag")).write_text(tag, encoding="ascii")
        if slug == "tripwire":
            hook = tooldir / slug / "hooks" / "claude" / "tripwire-pretool.ps1"
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_text(f"# fake packaged tripwire hook {tag}\n", encoding="ascii")
        sys.exit(0)
    if args[:2] == ["tool", "uninstall"]:
        slug = args[2]
        target = bindir / (slug + ".cmd")
        if not target.exists():
            sys.stderr.write("error: `%s` is not installed\n" % slug)
            sys.exit(2)
        target.unlink()
        (bindir / (slug + ".tag")).unlink()
        sys.exit(0)
    if args == ["tool", "dir", "--bin"]:
        print(bindir)
        sys.exit(0)
    if args == ["tool", "dir"]:
        print(tooldir)
        sys.exit(0)
    if args[:1] == ["run"]:
        slug = Path.cwd().name
        if "uv-run:" + slug in fail:
            sys.stderr.write("refused: fake skill installer failure\n")
            sys.exit(1)
        command = args[3]
        root = Path(args[args.index("--root") + 1])
        skill = root / ("fake-" + slug + "-skill")
        if command == "install":
            skill.mkdir(parents=True, exist_ok=True)
            (skill / "SKILL.md").write_text("fake " + slug, encoding="ascii")
        elif command == "uninstall":
            if (skill / "SKILL.md").exists():
                (skill / "SKILL.md").unlink()
                skill.rmdir()
        sys.exit(0)
    sys.exit(2)

if role == "git":
    if "clone" in args:
        dest = Path(args[-1])
        branch = args[args.index("--branch") + 1]
        if "git-clone:" + args[-2].rsplit("/", 1)[1] in fail:
            sys.stderr.write("fatal: fake clone failure\n")
            sys.exit(128)
        dest.mkdir(parents=True)
        (dest / "CLONED_FROM").write_text(args[-2] + "@" + branch, encoding="ascii")
        (dest / ".git").mkdir()
        pack = dest / ".git" / "pack.idx"
        pack.write_text("read-only like a real git pack", encoding="ascii")
        os.chmod(pack, 0o444)
        sys.exit(0)
    sys.exit(2)

if role.startswith("cli:"):
    slug = role[4:]
    if args == ["--version"]:
        if "health:" + slug in fail:
            sys.exit(3)
        tag_file = bindir / (slug + ".tag")
        print(slug, tag_file.read_text() if tag_file.exists() else "?")
    if args[:1] == ["apply"] and "setup-write:" + slug in fail:
        sys.stderr.write("refused: fake writer failure\n")
        sys.exit(1)
    if slug == "tripwire" and args == ["hook", "path", "--host", "claude"]:
        override = os.environ.get("FAKE_HOOK_LOCATE")
        if override is not None:
            sys.stdout.write(override)
        else:
            print(tooldir / slug / "hooks" / "claude" / "tripwire-pretool.ps1")
        sys.exit(0)
    if slug == "passing-notes" and args[:2] == ["hook", "install"]:
        settings = Path(args[args.index("--settings") + 1])
        data = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
        groups = data.get("hooks", {}).get("Stop", [])
        installed = any(
            item.get("command") == "passing-notes hook stop"
            for group in groups if isinstance(group, dict)
            for item in group.get("hooks", []) if isinstance(item, dict)
        )
        if "--check" in args:
            print(("installed: " if installed else "missing: ") + str(settings))
            sys.exit(0)
        if "hook-install:passing-notes" in fail:
            sys.stderr.write("refused: fake member hook install failure\n")
            sys.exit(1)
        if not installed:
            data.setdefault("hooks", {}).setdefault("Stop", []).append(
                {"hooks": [{"type": "command", "command": "passing-notes hook stop", "timeout": 10}]}
            )
            settings.parent.mkdir(parents=True, exist_ok=True)
            settings.write_text(json.dumps(data), encoding="utf-8")
        print("installed: " + str(settings))
        sys.exit(0)
    if slug == "passing-notes" and args[:2] == ["hook", "uninstall"]:
        settings = Path(args[args.index("--settings") + 1])
        data = json.loads(settings.read_text(encoding="utf-8"))
        groups = data.get("hooks", {}).get("Stop", [])
        kept = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                kept.append(group)
                continue
            group["hooks"] = [
                item for item in group["hooks"]
                if not (
                    isinstance(item, dict)
                    and item.get("type") == "command"
                    and item.get("command") == "passing-notes hook stop"
                )
            ]
            if group["hooks"] or set(group) - {"hooks", "matcher"}:
                kept.append(group)
        data["hooks"]["Stop"] = kept
        settings.write_text(json.dumps(data), encoding="utf-8")
        print("uninstalled: " + str(settings))
        sys.exit(0)
    sys.exit(0)

sys.exit(2)
"""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def real_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def ring_slugs(manifest, rings):
    return [m["slug"] for m in manifest["members"] if m["ring"] in rings]


def member(manifest, slug):
    return next(m for m in manifest["members"] if m["slug"] == slug)


def skill_member(manifest, rings=("core",)):
    """The first selected member that ships skills (passing-notes today)."""
    return next(m for m in manifest["members"] if m["ring"] in rings and m["skills"])


def plain_member(manifest, rings=("core",)):
    """The first selected member without skills or a writer (tripwire today)."""
    return next(
        m
        for m in manifest["members"]
        if m["ring"] in rings and not m["skills"] and not m["setup_write"]
    )


def writer_member(manifest, rings=("core",)):
    """The first selected member with a setup_write (switchboard today)."""
    return next(
        m for m in manifest["members"] if m["ring"] in rings and m["setup_write"]
    )


def pinned_manifest(tmp_path, edit=None, name="companions.json"):
    """The real manifest with every core and optional member pinned to TAG."""
    manifest = real_manifest()
    for row in manifest["members"]:
        if row["ring"] in ("core", "optional"):
            row["tag"] = TAG
    if edit:
        edit(manifest)
    path = tmp_path / name
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path, manifest


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Env:
    """A disposable home, fake tools and a scratch PATH."""

    def __init__(self, tmp_path, tools=("uv", "git", "python")):
        self.root = tmp_path
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.log = tmp_path / "fake.log"
        self.tool_bin = tmp_path / "uv-tool-bin"
        self.tool_bin.mkdir()
        self.tool_dir = tmp_path / "uv-tool-dir"
        self.tool_dir.mkdir()
        self.fake = tmp_path / "fake_tool.py"
        self.fake.write_text(FAKE_TOOL, encoding="utf-8")
        self.dirs = {}
        for tool in ("uv", "git", "python"):
            d = tmp_path / ("bin-" + tool)
            d.mkdir()
            self.dirs[tool] = d
        self.write_shim("uv", "uv")
        self.write_shim("git", "git")
        (self.dirs["python"] / "python.cmd").write_text(
            '@"%s" %%*\r\n@exit /b %%ERRORLEVEL%%\r\n' % sys.executable,
            encoding="ascii",
        )
        self.extra = []
        self.tools = list(tools)
        self.fail = []
        # Extra environment (set) and inherited names to drop (None), and the cwd.
        self.overrides = {}
        self.cwd = None

    def write_shim(self, name, role):
        (self.dirs[name] / (name + ".cmd")).write_text(
            '@"%s" "%s" %s %%*\r\n@exit /b %%ERRORLEVEL%%\r\n'
            % (sys.executable, self.fake, role),
            encoding="ascii",
        )

    def env(self):
        path = [str(self.dirs[t]) for t in self.tools]
        path += [str(p) for p in self.extra]
        path += [str(self.tool_bin)] + [str(p) for p in SYSTEM_PATH]
        env = dict(os.environ)
        env["PATH"] = os.pathsep.join(path)
        env["FAKE_LOG"] = str(self.log)
        env["FAKE_TOOL_BIN"] = str(self.tool_bin)
        env["FAKE_TOOL_DIR"] = str(self.tool_dir)
        env["FAKE_FAIL"] = ",".join(self.fail)
        for name, value in self.overrides.items():
            if value is None:
                env.pop(name, None)
            else:
                env[name] = value
        return env

    def calls(self):
        if not self.log.exists():
            return []
        return [
            json.loads(line)
            for line in self.log.read_text(encoding="utf-8").splitlines()
        ]

    def reset_log(self):
        if self.log.exists():
            self.log.unlink()

    def run(self, script, *args, timeout=300):
        return subprocess.run(
            [
                str(POWERSHELL),
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                *args,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self.env(),
            cwd=self.cwd,
            timeout=timeout,
        )

    def companions(self, *args, provider="claude", manifest=None, timeout=300):
        extra = ["-Provider", provider, "-Home", str(self.home)]
        if manifest is not None:
            extra += ["-Manifest", str(manifest)]
        return self.run(INSTALL_COMPANIONS, *extra, *args, timeout=timeout)

    def ledger(self):
        path = self.home / COMPANION_LEDGER
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def statuses(stdout):
    """slug -> status from the 'install-companions: <slug>: <status>' lines."""
    out = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("install-companions: ") or line.startswith(
            "install-companions: note:"
        ):
            continue
        rest = line[len("install-companions: ") :]
        slug, sep, status = rest.partition(": ")
        if sep and " " not in slug:
            assert slug not in out, "two status lines for %s:\n%s" % (slug, stdout)
            out[slug] = status
    return out


def status_order(stdout):
    return list(statuses(stdout))


def uv_installs(calls):
    return [
        c for c in calls if c["tool"] == "uv" and c["argv"][:2] == ["tool", "install"]
    ]


def install_spec(slug, manifest, tag=TAG):
    return "git+%s@%s" % (member(manifest, slug)["repo"], tag)


@pytest.fixture(scope="module")
def mini_dist(tmp_path_factory):
    """A one-skill claude profile cut from a real build, so a skill install is fast."""
    full = tmp_path_factory.mktemp("dist-full")
    r = subprocess.run(
        [
            str(POWERSHELL),
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(BUILD_SCRIPT),
            "-OutputDir",
            str(full),
            "-Provider",
            "claude",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    mini = tmp_path_factory.mktemp("dist-mini")
    skill = sorted(
        p for p in (full / "claude").iterdir() if p.is_dir() and p.name != "_shared"
    )[0]
    target = mini / "claude" / skill.name
    target.mkdir(parents=True)
    for f in skill.iterdir():
        (target / f.name).write_bytes(f.read_bytes())
    return mini


def skill_install(env, dist, *extra, timeout=300):
    return env.run(
        INSTALL_SKILL_MESH,
        "-Provider",
        "claude",
        "-Home",
        str(env.home),
        "-DistDir",
        str(dist),
        *extra,
        timeout=timeout,
    )


# --------------------------------------------------------------------------- #
# Production entry point: install-skill-mesh.ps1 -Companions
# --------------------------------------------------------------------------- #


def test_skill_installer_companions_core_installs_core_members(tmp_path, mini_dist):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    r = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(path)
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "install-skill-mesh: installed 'claude'" in r.stdout
    assert (env.home / SKILL_LEDGER).is_file()

    core = ring_slugs(manifest, ("core",))
    optional = ring_slugs(manifest, ("optional",))
    assert core and optional, (
        "the manifest no longer has both rings; the test is vacuous"
    )
    got = statuses(r.stdout)
    assert status_order(r.stdout) == core, r.stdout
    assert all(got[s] == "installed" for s in core), r.stdout
    # The companion step ran after the skill install finished.
    assert r.stdout.index("install-skill-mesh: installed") < r.stdout.index(
        "install-companions:"
    )

    calls = env.calls()
    assert [c["argv"][-1] for c in uv_installs(calls)] == [
        install_spec(s, manifest) for s in core
    ]
    for slug in optional:
        assert not any(slug in json.dumps(c) for c in calls), slug
    for slug in core:
        health = member(manifest, slug)["health"]
        assert any(
            c["tool"] == "cli:" + health[0] and c["argv"] == health[1:] for c in calls
        )

    pn = skill_member(manifest)
    runs = [c for c in calls if c["tool"] == "uv" and c["argv"][:1] == ["run"]]
    assert len(runs) == 1
    expected = pn["skills"]["installer"][1:] + [
        "--host",
        "claude",
        "--root",
        str(env.home / ".claude" / "skills"),
    ]
    assert runs[0]["argv"] == expected
    assert Path(runs[0]["cwd"]) == env.home / CACHE_DIR / "src" / pn["slug"]
    clones = [c for c in calls if c["tool"] == "git"]
    assert len(clones) == 1
    assert clones[0]["argv"][-4:] == [
        TAG,
        "--",
        pn["repo"],
        str(env.home / CACHE_DIR / "src" / pn["slug"]),
    ]
    assert "--depth" in clones[0]["argv"]

    ledger = env.ledger()
    assert ledger["schema_version"] == 1
    assert sorted(ledger["members"]) == sorted(core)
    for slug in core:
        entry = ledger["members"][slug]
        assert entry["tag"] == TAG and entry["tool"] == "installed"
        assert entry["setup_write"] is bool(member(manifest, slug)["setup_write"])
        if not member(manifest, slug)["hooks"]:
            assert entry["hooks"] == []
        assert entry["skills"] is bool(member(manifest, slug)["skills"])
    assert ledger["members"][pn["slug"]]["skills_hosts"] == ["claude"]
    assert ledger["opt_outs"] == {"no_hooks": False, "skip_hook": []}


def test_skill_installer_default_is_none(tmp_path, mini_dist):
    path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    r = skill_install(env, mini_dist, "-CompanionsManifest", str(path))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "install-companions" not in r.stdout
    assert env.calls() == []
    assert not (env.home / COMPANION_LEDGER).exists()


@pytest.mark.parametrize("missing", ["uv", "git", "python", "old-python"])
def test_missing_prerequisite_skips_every_member_and_skill_install_completes(
    tmp_path, mini_dist, missing
):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    expected = {
        "uv": "uv",
        "git": "git",
        "python": "Python 3.12",
        "old-python": "Python 3.12",
    }[missing]
    if missing == "old-python":
        (env.dirs["python"] / "python.cmd").write_text(
            "@echo 3.11\r\n", encoding="ascii"
        )
    else:
        env.tools.remove(missing)
    r = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(path)
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "install-skill-mesh: installed 'claude'" in r.stdout
    assert (env.home / SKILL_LEDGER).is_file()
    got = statuses(r.stdout)
    core = ring_slugs(manifest, ("core",))
    assert got == {s: "skipped: missing " + expected for s in core}, r.stdout
    assert not [
        c
        for c in env.calls()
        if c["tool"] in ("uv", "git") or c["tool"].startswith("cli:")
    ]
    assert not (env.home / COMPANION_LEDGER).exists()


def test_companion_failure_never_fails_the_skill_install(tmp_path, mini_dist):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    env.fail = ["uv-install:" + s for s in ring_slugs(manifest, ("core",))]
    r = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(path)
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "install-skill-mesh: installed 'claude'" in r.stdout
    assert "companion step reported a problem (exit 1)" in r.stdout


def test_skill_installer_companions_round_trip_leaves_the_skill_ledger_alone(
    tmp_path, mini_dist
):
    """-Companions core and -Uninstall -Companions core, both through the entry point."""
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    core = ring_slugs(manifest, ("core",))
    pn = skill_member(manifest)
    fake_skill = (
        env.home / ".claude" / "skills" / ("fake-" + pn["slug"] + "-skill") / "SKILL.md"
    )
    r = skill_install(env, mini_dist)
    assert r.returncode == 0, r.stdout + r.stderr
    skill_ledger = env.home / SKILL_LEDGER
    before = skill_ledger.read_bytes()

    r = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(path)
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout) == {s: "installed" for s in core}, r.stdout
    assert fake_skill.is_file()
    # The companion step, run by the production entry point, never moved the
    # Skill Mesh skill ledger.
    assert skill_ledger.read_bytes() == before

    env.reset_log()
    r = skill_install(
        env,
        mini_dist,
        "-Uninstall",
        "-Companions",
        "core",
        "-CompanionsManifest",
        str(path),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "install-skill-mesh: uninstalled 'claude'" in r.stdout
    assert statuses(r.stdout) == {s: "uninstalled" for s in core}, r.stdout
    # The companion step ran after the skill uninstall finished.
    assert r.stdout.index("install-skill-mesh: uninstalled") < r.stdout.index(
        "install-companions:"
    )
    removed = [
        c["argv"][2] for c in env.calls() if c["argv"][:2] == ["tool", "uninstall"]
    ]
    assert removed == list(reversed(core))
    assert not fake_skill.exists()
    assert env.ledger() is None
    assert not (env.home / CACHE_DIR).exists()
    assert [p.name for p in env.tool_bin.iterdir()] == []


# --------------------------------------------------------------------------- #
# Idempotency and the skill ledger
# --------------------------------------------------------------------------- #


def test_install_reinstall_uninstall_are_idempotent(tmp_path, mini_dist):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    r = skill_install(env, mini_dist)
    assert r.returncode == 0, r.stdout + r.stderr
    skill_ledger = env.home / SKILL_LEDGER
    before = skill_ledger.read_bytes()
    core = ring_slugs(manifest, ("core",))
    pn = skill_member(manifest)
    fake_skill = (
        env.home / ".claude" / "skills" / ("fake-" + pn["slug"] + "-skill") / "SKILL.md"
    )

    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert set(statuses(r.stdout).values()) == {"installed"}
    assert fake_skill.is_file()
    ledger_bytes = (env.home / COMPANION_LEDGER).read_bytes()

    env.reset_log()
    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout) == {s: "already current" for s in core}, r.stdout
    calls = env.calls()
    assert not uv_installs(calls)
    assert not [c for c in calls if c["tool"] == "git" or c["argv"][:1] == ["run"]]
    assert (env.home / COMPANION_LEDGER).read_bytes() == ledger_bytes

    env.reset_log()
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout) == {s: "uninstalled" for s in core}, r.stdout
    assert status_order(r.stdout) == list(reversed(core))
    calls = env.calls()
    uninstall_run = [c for c in calls if c["argv"][:1] == ["run"]]
    assert uninstall_run[0]["argv"] == pn["skills"]["uninstaller"][1:] + [
        "--host",
        "claude",
        "--root",
        str(env.home / ".claude" / "skills"),
    ]
    removed = [c["argv"][2] for c in calls if c["argv"][:2] == ["tool", "uninstall"]]
    assert removed == list(reversed(core))
    assert not fake_skill.exists()
    assert not (env.home / COMPANION_LEDGER).exists()
    assert not (env.home / CACHE_DIR).exists()
    assert [p.name for p in env.tool_bin.iterdir()] == []

    env.reset_log()
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout) == {
        s: "skipped: not installed by Skill Mesh" for s in core
    }
    assert env.calls() == []

    # The Skill Mesh skill ledger never moved.
    assert skill_ledger.read_bytes() == before


def test_new_tag_upgrades_in_place(tmp_path):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    assert env.companions(manifest=path).returncode == 0
    pn = skill_member(manifest)

    def bump(m):
        member(m, pn["slug"])["tag"] = NEW_TAG

    path2, _ = pinned_manifest(tmp_path, bump, name="companions-2.json")
    env.reset_log()
    r = env.companions(manifest=path2)
    assert r.returncode == 0, r.stdout + r.stderr
    got = statuses(r.stdout)
    assert got[pn["slug"]] == "installed"
    assert got[plain_member(manifest)["slug"]] == "already current"
    calls = env.calls()
    assert [c["argv"] for c in uv_installs(calls)] == [
        ["tool", "install", "--force", install_spec(pn["slug"], manifest, NEW_TAG)]
    ]
    assert [c for c in calls if c["argv"][:1] == ["run"]], (
        "the member skill installer re-ran"
    )
    entry = env.ledger()["members"][pn["slug"]]
    assert entry["tag"] == NEW_TAG and entry["skills_hosts"] == ["claude"]


@pytest.mark.parametrize("failure", ["health", "git-clone", "uv-run", "setup-write"])
def test_failed_upgrade_is_reattempted_by_the_next_run(tmp_path, failure):
    """Round-1 Block: a failed step after an upgrade's uv install must stay owed."""
    pn_slug = skill_member(real_manifest())["slug"]

    def add_writer(m):
        member(m, pn_slug)["setup_write"] = {
            "install": [pn_slug, "apply", "--write", "--home", "{home}"],
            "uninstall": [pn_slug, "apply", "--remove", "--home", "{home}"],
        }

    path, manifest = pinned_manifest(tmp_path, add_writer)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    entry = env.ledger()["members"][pn_slug]
    assert entry["skills_hosts"] == ["claude"] and entry["setup_write"] is True

    def bump(m):
        add_writer(m)
        member(m, pn_slug)["tag"] = NEW_TAG

    path2, _ = pinned_manifest(tmp_path, bump, name="companions-2.json")
    env.fail = ["%s:%s" % (failure, pn_slug)]
    r = env.companions(manifest=path2)
    assert r.returncode == 1, r.stdout + r.stderr
    assert statuses(r.stdout)[pn_slug].startswith("skipped: "), r.stdout
    # The ledger still records the old tag: the upgrade is owed.
    assert env.ledger()["members"][pn_slug]["tag"] == TAG

    env.fail = []
    env.reset_log()
    r = env.companions(manifest=path2)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout)[pn_slug] == "installed", r.stdout
    calls = env.calls()
    assert [c["argv"] for c in uv_installs(calls)] == [
        ["tool", "install", "--force", install_spec(pn_slug, manifest, NEW_TAG)]
    ]
    clones = [c["argv"] for c in calls if c["tool"] == "git"]
    assert len(clones) == 1 and clones[0][clones[0].index("--branch") + 1] == NEW_TAG
    assert [c for c in calls if c["argv"][:1] == ["run"]], "skill installer re-ran"
    assert [
        c["argv"]
        for c in calls
        if c["tool"] == "cli:" + pn_slug and c["argv"][:1] == ["apply"]
    ] == [["apply", "--write", "--home", str(env.home)]]
    entry = env.ledger()["members"][pn_slug]
    assert entry["tag"] == NEW_TAG
    assert entry["skills_hosts"] == ["claude"] and entry["setup_write"] is True

    env.reset_log()
    r = env.companions(manifest=path2)
    assert statuses(r.stdout)[pn_slug] == "already current", r.stdout
    assert not uv_installs(env.calls())


def test_interrupted_fresh_install_stays_ledger_owned(tmp_path):
    """Ownership is written ahead of uv: a crash after uv installed the tool
    leaves a ledger-owned entry, never a 'pre-existing' one."""
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    tw = plain_member(manifest)
    # The state a crash right after `uv tool install` leaves behind: the tool is
    # in uv's bin directory and the write-ahead entry is in the ledger.
    shim = env.tool_bin / (tw["cli"] + ".cmd")
    shim.write_text(
        '@"%s" "%s" cli:%s %%*\r\n@exit /b %%ERRORLEVEL%%\r\n'
        % (sys.executable, env.fake, tw["slug"]),
        encoding="ascii",
    )
    (env.tool_bin / (tw["slug"] + ".tag")).write_text(TAG, encoding="ascii")
    (env.home / COMPANION_LEDGER).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "members": {
                    tw["slug"]: {
                        "tag": TAG,
                        "tool": "installed",
                        "skills": False,
                        "skills_hosts": [],
                        "setup_write": False,
                        "hooks": [],
                    }
                },
                "opt_outs": {"no_hooks": False, "skip_hook": []},
            }
        ),
        encoding="utf-8",
    )
    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "pre-existing" not in statuses(r.stdout)[tw["slug"]]
    assert env.ledger()["members"][tw["slug"]]["tool"] == "installed"
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not shim.exists()


# --------------------------------------------------------------------------- #
# Rings and tags
# --------------------------------------------------------------------------- #


def test_core_never_installs_optional_and_all_does(tmp_path):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    core = ring_slugs(manifest, ("core",))
    optional = ring_slugs(manifest, ("optional",))
    candidates = ring_slugs(manifest, ("candidate",))

    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert set(statuses(r.stdout)) == set(core)
    assert "setup for optional member" not in r.stdout

    env.reset_log()
    r = env.companions("-Companions", "all", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    got = statuses(r.stdout)
    assert status_order(r.stdout) == ring_slugs(manifest, ("core", "optional"))
    assert all(got[s] == "installed" for s in optional)
    assert all(got[s] == "already current" for s in core)
    assert not any(s in got for s in candidates)
    calls = env.calls()
    assert [c["argv"][-1] for c in uv_installs(calls)] == [
        install_spec(s, manifest) for s in optional
    ]
    for slug in optional:
        for line in member(manifest, slug)["setup"]:
            assert line in r.stdout
        # Printed, never run: the only call the member's command saw is its health check.
        assert [c["argv"] for c in calls if c["tool"] == "cli:" + slug] == [
            member(manifest, slug)["health"][1:]
        ]

    # Uninstall core leaves the optional member; uninstall all removes it.
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert sorted(env.ledger()["members"]) == sorted(optional)
    r = env.companions("-Uninstall", "-Companions", "all", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert env.ledger() is None
    assert [p.name for p in env.tool_bin.iterdir()] == []


def test_null_tag_is_skipped_unreleased(tmp_path):
    pn_slug = skill_member(real_manifest())["slug"]

    def unpin(m):
        member(m, pn_slug)["tag"] = None

    path, manifest = pinned_manifest(tmp_path, unpin)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout)[pn_slug] == "skipped: unreleased"
    assert not any(pn_slug in json.dumps(c) for c in env.calls())
    assert pn_slug not in env.ledger()["members"]


def test_real_manifest_today_reports_every_core_member_unreleased(tmp_path):
    """The shipped manifest (no -Manifest): every core tag is still null."""
    manifest = real_manifest()
    core = ring_slugs(manifest, ("core",))
    if any(member(manifest, s)["tag"] for s in core):
        pytest.skip("a core member is pinned now; covered by the fixture tests")
    env = Env(tmp_path)
    r = env.companions()
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout) == {s: "skipped: unreleased" for s in core}
    assert not [c for c in env.calls() if c["tool"] in ("uv", "git")]
    assert env.ledger() is None


# --------------------------------------------------------------------------- #
# Failures, pre-existing tools, hosts, member writers, refusals
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("failure", ["uv-install", "health", "uv-run"])
def test_failed_member_does_not_stop_the_others(tmp_path, failure):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    pn = skill_member(manifest)["slug"]
    env.fail = ["%s:%s" % (failure, pn)]
    r = env.companions(manifest=path)
    assert r.returncode == 1, r.stdout + r.stderr
    got = statuses(r.stdout)
    want = {
        "uv-install": "uv tool install failed",
        "health": "health check failed",
        "uv-run": "member skill install failed",
    }[failure]
    assert got[pn].startswith("skipped: " + want), got[pn]
    others = [s for s in ring_slugs(manifest, ("core",)) if s != pn]
    assert others and all(got[s] == "installed" for s in others), r.stdout
    assert "1 member(s) failed" in r.stdout
    ledger = env.ledger()
    if failure == "uv-install":
        assert pn not in ledger["members"]
    else:
        # The tool is ledger-owned, so a later uninstall still removes it.
        assert ledger["members"][pn]["tool"] == "installed"
        assert ledger["members"][pn]["skills_hosts"] == []
    env.fail = []
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert env.ledger() is None
    assert [p.name for p in env.tool_bin.iterdir()] == []


def test_pre_existing_tool_is_reported_and_left_alone(tmp_path):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    tw = plain_member(manifest)
    pre = tmp_path / "pre-existing"
    pre.mkdir()
    own = pre / (tw["cli"] + ".cmd")
    own.write_text("@echo hand-installed\r\n", encoding="ascii")
    own_bytes = own.read_bytes()
    env.extra = [pre]

    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    status = statuses(r.stdout)[tw["slug"]]
    assert (
        status.startswith("skipped: pre-existing " + tw["cli"])
        and "left alone" in status
    )
    assert not [c for c in uv_installs(env.calls()) if tw["slug"] in c["argv"][-1]]
    assert env.ledger()["members"][tw["slug"]]["tool"] == "pre-existing"

    env.reset_log()
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "left alone" in statuses(r.stdout)[tw["slug"]]
    assert not [
        c
        for c in env.calls()
        if c["argv"][:2] == ["tool", "uninstall"] and c["argv"][2] == tw["slug"]
    ]
    assert own.read_bytes() == own_bytes
    assert env.ledger() is None


@pytest.mark.parametrize("provider", ["claude", "codex", "gpt"])
def test_member_skill_installer_runs_with_the_right_host(tmp_path, provider):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    for root in SKILL_ROOTS.values():
        (env.home / root).mkdir(parents=True)
    r = env.companions(manifest=path, provider=provider)
    assert r.returncode == 0, r.stdout + r.stderr
    pn = skill_member(manifest)
    runs = [c for c in env.calls() if c["argv"][:1] == ["run"]]
    entry = env.ledger()["members"][pn["slug"]]
    if provider == "gpt":
        assert runs == []
        assert "no host for provider gpt" in r.stdout
        assert entry["skills"] is False and entry["skills_hosts"] == []
        return
    root = env.home / Path(SKILL_ROOTS[provider])
    assert [c["argv"] for c in runs] == [
        pn["skills"]["installer"][1:] + ["--host", provider, "--root", str(root)]
    ]
    assert entry["skills_hosts"] == [provider]


def test_both_hosts_in_one_home_are_tracked_and_reversed(tmp_path):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    for root in SKILL_ROOTS.values():
        (env.home / root).mkdir(parents=True)
    assert env.companions(manifest=path, provider="claude").returncode == 0
    r = env.companions(manifest=path, provider="codex")
    assert r.returncode == 0, r.stdout + r.stderr
    pn = skill_member(manifest)
    assert statuses(r.stdout)[pn["slug"]] == "installed"
    assert env.ledger()["members"][pn["slug"]]["skills_hosts"] == ["claude", "codex"]
    env.reset_log()
    assert env.companions("-Uninstall", manifest=path).returncode == 0
    hosts = [
        c["argv"][c["argv"].index("--host") + 1]
        for c in env.calls()
        if c["argv"][:1] == ["run"]
    ]
    assert hosts == ["codex", "claude"]


def test_setup_write_runs_after_skills_and_is_reversed_first(tmp_path):
    slug = plain_member(real_manifest())["slug"]

    def add_writer(m):
        member(m, slug)["setup_write"] = {
            "install": [slug, "apply", "--write", "--home", "{home}"],
            "uninstall": [slug, "apply", "--remove", "--home", "{home}"],
        }

    path, manifest = pinned_manifest(tmp_path, add_writer)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    writes = [c["argv"] for c in env.calls() if c["tool"] == "cli:" + slug]
    health_argv = member(manifest, slug)["health"][1:]
    assert writes == [
        health_argv,
        ["apply", "--write", "--home", str(env.home)],
        ["hook", "path", "--host", "claude"],
    ]
    assert env.ledger()["members"][slug]["setup_write"] is True

    env.reset_log()
    r = env.companions(manifest=path)
    assert statuses(r.stdout)[slug] == "already current"
    assert [c["argv"] for c in env.calls() if c["tool"] == "cli:" + slug] == [
        health_argv,
        ["hook", "path", "--host", "claude"],
    ]

    env.reset_log()
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    sequence = [
        c
        for c in env.calls()
        if c["tool"] == "cli:" + slug
        or (c["argv"][:2] == ["tool", "uninstall"] and c["argv"][2] == slug)
    ]
    assert [c["argv"] for c in sequence] == [
        ["apply", "--remove", "--home", str(env.home)],
        ["tool", "uninstall", slug],
    ]


def test_setup_write_without_uninstall_is_reported_left_in_place(tmp_path):
    slug = plain_member(real_manifest())["slug"]

    def add_writer(m):
        member(m, slug)["setup_write"] = {
            "install": [slug, "apply", "--write"],
            "uninstall": None,
        }

    path, _ = pinned_manifest(tmp_path, add_writer)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    assert env.companions(manifest=path).returncode == 0
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "no uninstall command; left in place" in r.stdout
    assert statuses(r.stdout)[slug] == "uninstalled"


def test_corrupt_companion_ledger_is_refused_and_untouched(tmp_path):
    path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    ledger = env.home / COMPANION_LEDGER
    ledger.write_bytes(b"{not json")
    for args in ([], ["-Uninstall"]):
        r = env.companions(*args, manifest=path)
        assert r.returncode == 3, r.stdout + r.stderr
        assert "refusing" in r.stderr
        assert ledger.read_bytes() == b"{not json"
    assert not [c for c in env.calls() if c["tool"] in ("uv", "git")]


def test_manifest_failing_verify_is_refused(tmp_path):
    def break_it(m):
        m["members"].reverse()  # verify refuses unsorted members

    path, _ = pinned_manifest(tmp_path, break_it)
    env = Env(tmp_path)
    r = env.companions(manifest=path)
    assert r.returncode == 3, r.stdout + r.stderr
    assert "failed tools/companions.py verify" in r.stderr
    assert not [c for c in env.calls() if c["tool"] in ("uv", "git")]
    assert env.ledger() is None


def test_uninstall_also_refuses_a_manifest_failing_verify(tmp_path):
    good, _ = pinned_manifest(tmp_path)

    def break_it(m):
        m["members"].reverse()

    bad, _ = pinned_manifest(tmp_path, break_it, name="companions-bad.json")
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    assert env.companions(manifest=good).returncode == 0
    ledger_bytes = (env.home / COMPANION_LEDGER).read_bytes()
    env.reset_log()
    r = env.companions("-Uninstall", manifest=bad)
    assert r.returncode == 3, r.stdout + r.stderr
    assert "failed tools/companions.py verify" in r.stderr
    assert env.calls() == []
    assert (env.home / COMPANION_LEDGER).read_bytes() == ledger_bytes


def test_uninstall_with_the_skills_folder_gone_still_reverses_the_member(tmp_path):
    path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    skills = env.home / ".claude" / "skills"
    skills.mkdir(parents=True)
    assert env.companions(manifest=path).returncode == 0
    pn = skill_member(manifest)
    for p in sorted(skills.rglob("*"), reverse=True):
        p.unlink() if p.is_file() else p.rmdir()
    skills.rmdir()

    env.reset_log()
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout)[pn["slug"]] == "uninstalled", r.stdout
    assert "the claude skills folder is gone" in r.stdout
    assert not [c for c in env.calls() if c["argv"][:1] == ["run"]]
    assert env.ledger() is None
    assert [p.name for p in env.tool_bin.iterdir()] == []


# --------------------------------------------------------------------------- #
# A member writer in the core ring: switchboard (plan Step 16, issue #295)
# --------------------------------------------------------------------------- #

# The judge offload's switch. Only the operator writes it; the companion never does.
OFFLOAD_CONFIG = Path(".switchboard") / "config.json"


def expand_argv(argv, home):
    """argv after its command, with {home} replaced as install-companions.ps1 does."""
    return [item.replace("{home}", str(home)) for item in argv[1:]]


def tree_snapshot(root, skip=()):
    """Every file under root but skip: relative POSIX path -> (bytes, mtime)."""
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.relative_to(root).as_posix() not in skip
    }


def test_writer_member_runs_apply_once_and_never_touches_the_offload_config(tmp_path):
    """The installer's side of the writer contract, with fake tools.

    The fake switchboard writes nothing, so the offload-config assertions here guard
    the real installer (it must neither write the file nor pass it to the member).
    That the real member leaves it alone is checked by the online
    test_core_install_writes_the_pinned_switchboard_role_files_once below.
    """
    path, manifest = pinned_manifest(tmp_path)
    sb = writer_member(manifest)
    assert sb["setup_write"]["uninstall"] is None, (
        "switchboard v0.1.1 has no removal command; this test pins the reporting path"
    )
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    config = env.home / OFFLOAD_CONFIG
    config.parent.mkdir()
    config.write_bytes(b'{"synthetic": "operator-owned offload config"}\n')
    before = config.read_bytes()

    def writer_calls():
        return [
            c["argv"]
            for c in env.calls()
            if c["tool"] == "cli:" + sb["slug"] and c["argv"] != sb["health"][1:]
        ]

    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout)[sb["slug"]] == "installed", r.stdout
    assert writer_calls() == [expand_argv(sb["setup_write"]["install"], env.home)]
    assert env.ledger()["members"][sb["slug"]]["setup_write"] is True
    assert config.read_bytes() == before
    assert not any("config.json" in json.dumps(c) for c in env.calls())

    env.reset_log()
    r = env.companions(manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout)[sb["slug"]] == "already current", r.stdout
    assert writer_calls() == []
    assert config.read_bytes() == before

    env.reset_log()
    r = env.companions("-Uninstall", manifest=path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout)[sb["slug"]] == "uninstalled", r.stdout
    assert (
        "install-companions: note: %s: its setup_write output has no uninstall "
        "command; left in place" % sb["slug"]
    ) in r.stdout
    assert writer_calls() == []
    assert config.read_bytes() == before


def load_contract_suite():
    """The contract suite module: its online gate (SKILL_MESH_CONTRACTS_OFFLINE, then
    a probe) and its reader of switchboard's own role-file folders."""
    spec = importlib.util.spec_from_file_location(
        "companion_contract_suite", Path(__file__).with_name("test_contracts.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_directory(git):
    """The PATH folder for the real git.

    Git for Windows' mingw64/bin/git.exe on a minimal PATH fails uv's checkout clone
    ("destination path already exists"); its cmd/git.exe launcher sets up the
    environment git expects, so it is preferred when it sits beside it.
    """
    exe = Path(git).resolve()
    if exe.parent.name.lower() == "bin" and exe.parent.parent.name.lower() == "mingw64":
        launcher = exe.parent.parent.parent / "cmd" / "git.exe"
        if launcher.is_file():
            return launcher.parent
    return exe.parent


def test_core_install_writes_the_pinned_switchboard_role_files_once(
    tmp_path, mini_dist
):
    """Step 16 done-when, end to end: install-skill-mesh.ps1 -Companions core with
    the REAL uv and git installs the pinned switchboard tag from GitHub, and its
    apply writes the role files of the registry that tag ships.

    The fake-tool harness above cannot produce real role files, so this one test
    uses real tools behind the contract suite's online gate
    (SKILL_MESH_CONTRACTS_OFFLINE=1 skips it). Everything it writes is disposable:
    the home, uv's tool, bin and cache folders, and HOME/USERPROFILE.
    """
    contracts = load_contract_suite()
    contracts.require_online()
    uv, git = shutil.which("uv"), shutil.which("git")
    assert uv and git, "the online switchboard install needs uv and git"
    manifest = real_manifest()
    sb = writer_member(manifest)
    assert sb["tag"], "switchboard has no pinned tag"
    path = tmp_path / "switchboard-only.json"
    path.write_text(
        json.dumps({"schema_version": manifest["schema_version"], "members": [sb]}),
        encoding="utf-8",
    )

    env = Env(tmp_path, tools=("uv", "python"))
    (env.dirs["uv"] / "uv.cmd").write_text(
        '@"%s" %%*\r\n@exit /b %%ERRORLEVEL%%\r\n' % uv, encoding="ascii"
    )
    env.extra = [git_directory(git)]
    user = tmp_path / "user"
    user.mkdir()
    tools_dir = tmp_path / "uv-tools"
    env.cwd = tmp_path
    env.overrides = {
        "UV_TOOL_DIR": str(tools_dir),
        "UV_TOOL_BIN_DIR": str(env.tool_bin),
        "UV_CACHE_DIR": str(tmp_path / "uv-cache"),
        "UV_NO_CONFIG": "1",
        "UV_PYTHON": sys.executable,
        "UV_PYTHON_DOWNLOADS": "never",
        "HOME": str(user),
        "USERPROFILE": str(user),
        "GIT_TERMINAL_PROMPT": "0",
        "SWITCHBOARD_REGISTRY": None,
    }

    def install():
        return skill_install(
            env,
            mini_dist,
            "-Companions",
            "core",
            "-CompanionsManifest",
            str(path),
            timeout=1200,
        )

    r = install()
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout) == {sb["slug"]: "installed"}, r.stdout
    entry = env.ledger()["members"][sb["slug"]]
    assert entry["tag"] == sb["tag"] and entry["tool"] == "installed"
    assert entry["setup_write"] is True

    # The role files are exactly the pinned tag's packaged registry, ledger-owned.
    registries = sorted(tools_dir.rglob("_registry/models.json"))
    assert len(registries) == 1, registries
    roles = json.loads(registries[0].read_text(encoding="utf-8"))["roles"]
    assert roles, "the pinned registry has no roles"
    # Each host's folder and suffix as the installed tag's own package states them.
    role_files = contracts.switchboard_role_files(
        contracts.tool_python(tools_dir, sb["cli"]),
        cwd=tmp_path,
        env=contracts.isolated_env(tmp_path / "probe-home"),
    )
    expected = {
        Path(p).relative_to(env.home).as_posix()
        for p in contracts.role_file_paths(env.home, role_files, roles)
    }
    written = {
        p.relative_to(env.home).as_posix()
        for parts, _ in role_files.values()
        for p in env.home.joinpath(*parts).iterdir()
    }
    assert written == expected
    owned = json.loads(
        (env.home / ".switchboard" / "generated.json").read_text(encoding="utf-8")
    )["files"]
    assert set(owned) == expected
    for key, item in owned.items():
        assert item["sha256"] == sha(env.home / key), key
    for base in (env.home, user):
        assert not (base / OFFLOAD_CONFIG).exists(), base

    # A re-install through the same entry point writes nothing. The skill step
    # rewrites its own ledger on every run; every other file, role files and the
    # companion ledger included, keeps its bytes and mtime.
    before = tree_snapshot(env.home, skip=(SKILL_LEDGER,))
    r = install()
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout) == {sb["slug"]: "already current"}, r.stdout
    assert tree_snapshot(env.home, skip=(SKILL_LEDGER,)) == before
    for base in (env.home, user):
        assert not (base / OFFLOAD_CONFIG).exists(), base

    # Uninstall removes the tool and reports the role files left in place.
    r = env.companions("-Uninstall", manifest=path, timeout=1200)
    assert r.returncode == 0, r.stdout + r.stderr
    assert statuses(r.stdout) == {sb["slug"]: "uninstalled"}, r.stdout
    assert "no uninstall command; left in place" in r.stdout
    after = tree_snapshot(env.home)
    for key in expected | {".switchboard/generated.json"}:
        assert after[key] == before[key], key
    assert not list(env.tool_bin.glob(sb["cli"] + ".*"))
