"""Run the per-change test pack: the quick repo-wide checks the testing rule names.

The testing rule in the root `CLAUDE.md` asks, per change, for the focused tests
for what the change touches plus the quick repo-wide checks, with the command,
the files it selected and its summary line saved to a file that reviewers read
instead of re-running suites. This tool runs the quick repo-wide checks as one
pytest command and writes that evidence file. It runs no test outside its
selection; the focused tests for a change are run separately (``--focused``
prints the lookup of which tests a change needs).

Usage (from anywhere; paths resolve against this checkout):

    python tools/change_pack.py [--roster] [--rc-report] [--evidence FILE]
                                [--list] [--focused] [-- <extra pytest args>]

    --roster     add the codex roster test (a catalog CREATE or DELETE)
    --rc-report  add the release-candidate report test (a representative
                 skill's core.md changed; see tests/fixtures/representative_skills.json)
    --evidence   where to write the evidence file (default: a new file in the
                 system temp directory; the path is printed)
    --list       print the selection as JSON and exit 0 without running pytest
    --focused    print the focused-tests-by-change lookup and exit 0

Everything after ``--`` is passed to pytest (for example ``-- --durations=25``).

Exit code: pytest's exit code (0 to 5). Exit 6, before pytest starts, when a
selected file no longer exists: a missing file fails the pack rather than being
skipped.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The quick repo-wide checks, run on every change. Each entry is a pytest
# target: a file, a folder, or a file::test node id.
QUICK_CHECKS = (
    "tests/router/test_no_claude_dependency.py",
    "tests/distributions/test_path_choke_point.py",
    "tests/distributions/test_legacy_migration.py::test_tracked_powershell_sources_are_ascii_without_bom",
    "tests/distributions/test_legacy_migration.py::test_ascii_gate_reds_on_a_non_ascii_source",
    "tests/package-integrity",
)

# The five behavioural files in tests/package-integrity that are not quick
# checks. They are left out of the pack by this explicit ignore list and run
# per change only when their own script changes (see FOCUSED below).
PACKAGE_INTEGRITY_IGNORES = (
    "tests/package-integrity/test_lesson_observations.py",
    "tests/package-integrity/test_review_deep_fail_closed.py",
    "tests/package-integrity/test_review_deep_lint_prepass_adapter.py",
    "tests/package-integrity/test_build_phase_landed_paths_roundtrip.py",
    "tests/package-integrity/test_shared_ledger_checks.py",
)

# Optional checks, added by option.
ROSTER_CHECK = (
    "tests/distributions/test_distributions.py"
    "::test_codex_profile_holds_exactly_the_declared_cohorts_for_the_committed_manifest"
)
RC_REPORT_CHECK = "tests/smoke/test_release_candidate_report.py"

# Focused tests, by what a change touches. Printed by --focused and after
# every run; the pack does not run these.
FOCUSED = (
    ("a skill's content, docs, generated catalog files",
     "the quick checks only"),
    ("tools/install-skill-mesh.ps1, runtime/path-guard.ps1",
     "the installer security selection in tests/distributions, "
     "tests/router/test_path_guard.py, and the codex install round trip in "
     "tests/distributions/test_codex_install_path.py"),
    ("runtime/skill-router.ps1", "tests/router"),
    ("tools/skill-mesh-transaction.ps1 (the engine the installer uses)",
     "the engine-only and installer-routed tests in "
     "tests/distributions/test_legacy_migration.py"),
    ("tools/migrate-legacy-install.ps1",
     "tests/distributions/test_legacy_migration.py"),
    ("tools/inspect-host-install.ps1",
     "tests/distributions/test_host_inspect.py"),
    ("tools/release.ps1, tools/build-distributions.ps1", "tests/release"),
    ("a skill script with its own behavioural file (lesson observations, "
     "review-deep, build-phase landed paths, shared ledger)",
     "that file (one of the five ignored above)"),
    ("experiments/", "tests/experiments"),
    ("a catalog CREATE or DELETE", "add --roster"),
    ("a representative skill's core.md", "add --rc-report"),
)

SUMMARY_RE = re.compile(
    r"\b\d+ (passed|failed|error|errors|skipped|deselected|xfailed|xpassed)\b"
    r"|no tests ran"
)


def selection(roster=False, rc_report=False):
    targets = list(QUICK_CHECKS)
    if roster:
        targets.append(ROSTER_CHECK)
    if rc_report:
        targets.append(RC_REPORT_CHECK)
    return targets, list(PACKAGE_INTEGRITY_IGNORES)


def missing_paths(targets, ignores):
    missing = []
    for item in list(targets) + list(ignores):
        path = REPO_ROOT / item.split("::", 1)[0]
        if not path.exists():
            missing.append(item)
    return missing


def selected_files(targets, ignores):
    """Expand each target to the test files pytest will import."""
    ignored = {(REPO_ROOT / p).resolve() for p in ignores}
    files = []
    for item in targets:
        path = REPO_ROOT / item.split("::", 1)[0]
        if path.is_dir():
            found = sorted(set(path.rglob("test_*.py")) | set(path.rglob("*_test.py")))
            for f in found:
                if f.resolve() not in ignored:
                    files.append(f.relative_to(REPO_ROOT).as_posix())
        else:
            files.append(item)
    return files


def print_focused(stream=sys.stdout):
    stream.write("Focused tests by what changed (run these as well as the pack):\n")
    for change, run in FOCUSED:
        stream.write("  - %s: %s\n" % (change, run))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    extra = []
    if "--" in argv:
        cut = argv.index("--")
        argv, extra = argv[:cut], argv[cut + 1:]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--roster", action="store_true")
    parser.add_argument("--rc-report", action="store_true")
    parser.add_argument("--evidence")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--focused", action="store_true")
    args = parser.parse_args(argv)

    if args.focused:
        print_focused()
        return 0

    targets, ignores = selection(args.roster, args.rc_report)
    if args.list:
        json.dump({"targets": targets, "ignores": ignores}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    missing = missing_paths(targets, ignores)
    if missing:
        for item in missing:
            sys.stderr.write("change_pack: selected path does not exist: %s\n" % item)
        return 6

    command = [sys.executable, "-m", "pytest"] + targets
    command += ["--ignore=%s" % p for p in ignores]
    command += ["-q", "-p", "no:cacheprovider"] + extra

    if args.evidence:
        evidence = Path(args.evidence)
        evidence.parent.mkdir(parents=True, exist_ok=True)
    else:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        evidence = Path(tempfile.gettempdir()) / ("skill-mesh-change-pack-%s.txt" % stamp)

    started = datetime.datetime.now()
    proc = subprocess.Popen(
        command, cwd=str(REPO_ROOT), stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
    )
    lines = []
    for line in proc.stdout:
        sys.stdout.write(line)
        lines.append(line.rstrip("\n"))
    code = proc.wait()
    ended = datetime.datetime.now()

    summary = next((l for l in reversed(lines) if SUMMARY_RE.search(l)), "(no summary line found)")
    failing = sorted({m.group(1) for l in lines
                      for m in [re.match(r"(?:FAILED|ERROR) (\S+?\.py)", l)] if m})

    with open(evidence, "w", encoding="utf-8", newline="\n") as out:
        out.write("change pack evidence\n")
        out.write("started: %s\n" % started.isoformat(timespec="seconds"))
        out.write("wall_clock_s: %.1f\n" % (ended - started).total_seconds())
        out.write("checkout: %s\n" % REPO_ROOT.name)
        out.write("command: %s\n" % " ".join(
            ["python"] + command[1:]))
        out.write("extra_args: %s\n" % (" ".join(extra) if extra else "none"))
        if extra:
            out.write("note: extra args may narrow the run; 'files selected' is the pack's "
                      "selection, not pytest's collection\n")
        out.write("targets:\n")
        for t in targets:
            out.write("  %s\n" % t)
        out.write("ignored:\n")
        for t in ignores:
            out.write("  %s\n" % t)
        out.write("files selected:\n")
        for f in selected_files(targets, ignores):
            out.write("  %s\n" % f)
        if failing:
            out.write("failing files:\n")
            for f in failing:
                out.write("  %s\n" % f)
        out.write("summary: %s\n" % summary.strip())
        out.write("exit: %d\n" % code)

    sys.stdout.write("\nchange_pack: evidence written to %s\n" % evidence)
    if failing:
        sys.stdout.write("change_pack: failing files: %s\n" % ", ".join(failing))
    sys.stdout.write("change_pack: exit %d\n\n" % code)
    print_focused()
    return code


if __name__ == "__main__":
    sys.exit(main())
