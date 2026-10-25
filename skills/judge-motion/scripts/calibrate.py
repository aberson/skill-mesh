# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "Pillow>=10.1",
# ]
# ///
"""calibrate.py - judge-motion Step 7 mechanical calibration engine.

Orchestrates the FULL production pipeline over the two frozen fixtures
(fixtures/smooth.html + fixtures/janky.html) and evaluates the MECHANICAL
half of the calibration contract (SKILL.md "Calibration"):

    1. verify the fixture port is free, then serve fixtures/ itself
       (subprocess http.server; killed + port verified freed on exit,
       even on error)
    2. capture_motion.mjs on fixtures/fixtures-flow.json, one
       single-transition run per fixture (smooth-swap, then janky-swap) -
       the production entry point, never a bench-only sibling
       (measurement-validity: assemble through the production code path)
    3. select_frames.py + gate_signals.py on both captures
    4. the mechanical assertion battery (constants below - the single
       source of truth for calibration expectations)
    5. the order-shuffle transform: <janky-run>/janky-swap/filmstrip-shuffled/
       = the selected filmstrip copied in a FIXED, non-monotonic
       presentation order with the burned-in chips UNTOUCHED, plus a
       filmstrip-shuffled.json manifest. A judge reading these frames in
       presentation order sees chip timestamps that go backwards - it must
       either answer differently than on the true order or flag the
       temporal inconsistency; either satisfies calibration (SKILL.md).
    6. calibration-mechanical.json at the calibration root, including
       ready-to-instantiate judgeInputs for the vision tier

The VISION half (three judge dispatches, acceptance matrix,
calibration-report.md) is agentic and lives in SKILL.md
"The --calibrate procedure" - a script cannot dispatch sub-agents.

Usage:
    uv run scripts/calibrate.py
        [--serve-port 8765]   fixture server port; the flow spec's URLs are
                              rewritten into a copy when non-default
        [--out <dir>]         default: this skill's own .judge-motion/
                              (SKILL.md: calibration runs live there)
        [--skip-capture <smooth-run-dir>,<janky-run-dir>]
                              reuse two existing capture run dirs (no
                              server, no capture); select/gate stages run
                              only where their outputs are missing
        [--garbage-anchor]    red-on-garbage self-test: serve a TEMP COPY
                              of fixtures/ whose smooth.html is replaced by
                              janky content (the frozen fixtures are never
                              touched). The smooth-anchor assertions MUST
                              fail; this mode ALWAYS exits nonzero.

Exit codes:
    0   default mode, all mechanical assertions PASS
    1   assertion failure (FAILED-CALIBRATION), tool failure, or - in
        --garbage-anchor mode - the expected red
    2   --garbage-anchor mode only: every assertion PASSED against the
        defect-injected anchor, i.e. the instrument cannot fail garbage.
        Never trust a calibration while this state exists.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

from PIL import Image

# --------------------------------------------------------------------------
# Paths + pipeline identity.
# --------------------------------------------------------------------------

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = SKILL_DIR / "fixtures"
FLOW_SPEC_NAME = "fixtures-flow.json"

DEFAULT_SERVE_PORT = 8765
# The port SKILL.md's inventory declares for the fixture server (checked
# against `observatory ports`); fixtures-flow.json hardcodes it in its URLs,
# which is why a non-default --serve-port triggers a spec rewrite.

DEFAULT_OUT_DIR = SKILL_DIR / ".judge-motion"
# SKILL.md "Run artifacts": calibration runs write under this skill's OWN
# .judge-motion/ (gitignored), never under a target project's.

SMOOTH_TRANSITION = "smooth-swap"
JANKY_TRANSITION = "janky-swap"
# Transition names as defined in fixtures/fixtures-flow.json.

# --------------------------------------------------------------------------
# Mechanical assertion constants - the calibration expectations.
# Sourced from fixtures/README.md's defect inventory; deliberately NOT
# imported from the pipeline scripts (an anchor expectation imported from
# the instrument under test would make the check tautological - the audit
# must call production but assert independently).
# --------------------------------------------------------------------------

EXPECTED_JANKY_FAIL_GATES = frozenset(
    {"cls", "focus-retained", "spinner-timing", "duration-in-range"}
)
# The gate names janky.html's injected defects must trip, mapped from
# fixtures/README.md's defect inventory: layout shift -> cls, focus dropped
# to body -> focus-retained, 80ms spinner flash -> spinner-timing,
# setTimeout-stepped animation -> duration-in-range. Duration nuance: the
# gate fires on the RAW wall-clock reading (janky measures ~1100ms+ > the
# rubric's 900ms max) - timer-driven content does not dilate under slow-mo,
# so no normalization rescues it. The white flash is a vision-tier defect
# (diff-spike + judge, no mechanical gate); scroll-restored has no injected
# defect in v1 (single-viewport fixtures). All four gates fired in every
# recorded real run (e.g. .judge-motion/20260720-040717-fixtures-flow).

JANKY_ALWAYS_FAIL_GATES = frozenset({"cls", "spinner-timing"})
# The two most machine-invariant janky failures: the layout shift registers
# on any real-time run, and the 80ms spinner cycle always violates both
# spinner thresholds. These MUST be present in the failing set.

JANKY_MIN_EXPECTED_FAIL_COUNT = 3
# Of the 4 expected gate failures, at least 3 must fire (must include the 2
# above). Tolerates one machine-variance dropout on focus-retained /
# duration-in-range without letting the janky anchor drift green.

WHITE_PIXEL_MIN_LEVEL = 252
# A pixel counts as "white" only when ALL THREE channels are >= this level.
# The flash frame's bare stage is pure #fff, which survives JPEG q80 at
# ~253-255; faded-but-present content (mid-fade frames) is white-TINTED, so
# at least one channel dips below. Measured on real runs: at 252 the flash
# frame scores 0.290 while every other selected frame stays <= 0.202.

WHITE_FLASH_MIN_FRACTION = 0.25
# A selected janky frame whose white fraction exceeds this is accepted as
# the captured white-flash frame. Measured separation (runs
# 20260720-040717 + 20260720-024621, identical values): flash frame 0.290;
# max non-flash janky frame 0.207; max smooth frame 0.196. 0.25 splits the
# 0.207-0.290 gap with margin on both sides.

WHITE_DOWNSCALE_FACTOR = 2
# Frames are box-filter downscaled (Image.reduce) by this factor before
# counting - cheap, and reduce() averages real pixels rather than
# interpolating new edge values the way resize() can.

SMOOTH_MAX_SELECTED_FRAMES = 7
# The Step 4 contract ("smooth fixture selects <= 7 frames with a flat diff
# curve" - plan Step 4 Done-when, restated in SKILL.md's run loop). An
# independent re-assertion of the contract number, NOT an import of
# select_frames.FLAT_MAX_SELECTED - see the tautology note above.

# --------------------------------------------------------------------------
# Order-shuffle transform.
# --------------------------------------------------------------------------

SHUFFLED_DIR_NAME = "filmstrip-shuffled"
SHUFFLED_MANIFEST_NAME = "filmstrip-shuffled.json"

# The fixed permutation is ends-interleave: presentation position k shows
# original index n-1, 0, n-2, 1, n-3, 2, ... (settle/after frames first,
# the before-anchor second, converging inward). Fully deterministic for any
# n (workspace rule: no randomness in calibration instruments), guaranteed
# non-monotonic for n >= 3, and it destroys adjacency structure rather than
# merely reversing it (a pure reversal still reads as a coherent backwards
# animation; interleaving does not).


def ends_interleave_permutation(n: int) -> list[int]:
    order: list[int] = []
    lo, hi = 0, n - 1
    take_hi = True
    while lo <= hi:
        if take_hi:
            order.append(hi)
            hi -= 1
        else:
            order.append(lo)
            lo += 1
        take_hi = not take_hi
    return order


# --------------------------------------------------------------------------
# Timeouts (seconds).
# --------------------------------------------------------------------------

SERVER_READY_TIMEOUT_S = 15
# http.server serves static files within ms of binding; 15s of silence
# means it never came up (port fight, firewall prompt), not slowness.

PORT_FREE_TIMEOUT_S = 10
# After kill, the OS releases the listening socket near-instantly; poll a
# little longer for TIME_WAIT stragglers before declaring a leak.

CAPTURE_TIMEOUT_S = 240
# One capture run = browser launch + 15s dilated budget + encode/teardown;
# real runs finish in well under a minute. 4 minutes means hung, not slow.

PIPELINE_STAGE_TIMEOUT_S = 420
# select_frames pHashes ~100 frames and composites overlays; gate_signals
# is instant. 7 minutes covers a cold uv environment resolve on top.


# --------------------------------------------------------------------------
# Fail-loud helpers (style mirrors the sibling scripts: FATAL + Remedy).
# --------------------------------------------------------------------------

def fatal(message: str, remedy: str | None = None) -> NoReturn:
    print("FATAL: " + message, file=sys.stderr)
    if remedy:
        print("Remedy: " + remedy, file=sys.stderr)
    sys.exit(1)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def load_json(path: Path, what: str) -> dict:
    if not path.is_file():
        fatal(
            what + " not found at " + str(path),
            "the pipeline stage that produces it did not run or failed - "
            "check the logs/ dir under the calibration root",
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fatal(what + " unreadable at " + str(path) + ": " + str(exc))


def child_env() -> dict:
    # Strip VIRTUAL_ENV so nested `uv run` invocations resolve their own
    # PEP 723 environments without a mismatch warning.
    import os

    env = dict(os.environ)
    env.pop("VIRTUAL_ENV", None)
    return env


def tree_kill(proc: subprocess.Popen) -> None:
    """Kill a subprocess AND its whole descendant tree. On Windows a bare
    terminate()/kill() reaches only the immediate child (e.g. node.exe),
    leaking any Playwright/Chromium tree it spawned - use taskkill /T /F
    (workspace convention: feedback_subprocess_tree_kill_windows).
    Best-effort: never raises."""
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            proc.kill()
        except OSError:
            pass
    try:
        proc.wait(timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def run_cmd(
    cmd: list[str],
    log_path: Path,
    timeout_s: int,
    what: str,
) -> subprocess.CompletedProcess:
    started = time.monotonic()
    try:
        popen = subprocess.Popen(
            cmd,
            cwd=str(SKILL_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=child_env(),
        )
    except FileNotFoundError:
        fatal(
            what + " launcher not found: " + cmd[0],
            "ensure '" + cmd[0] + "' is on PATH",
        )
    try:
        stdout, stderr = popen.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        # A plain kill would orphan the grandchildren (Playwright/Chromium
        # under node.exe) - kill the whole tree, then drain what we got.
        tree_kill(popen)
        out, err = "", ""
        try:
            out, err = popen.communicate(timeout=10)
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
        try:
            log_path.write_text(
                "$ " + " ".join(cmd) + "\n\n[timed out after " + str(timeout_s)
                + "s; process tree killed]\n\n=== stdout ===\n" + (out or "")
                + "\n=== stderr ===\n" + (err or ""),
                encoding="utf-8",
            )
        except OSError:
            pass
        fatal(
            what + " timed out after " + str(timeout_s) + "s: " + " ".join(cmd)
            + " (process tree killed)",
            "check " + str(log_path) + " for partial output; a hung browser "
            "or a blocked port are the usual causes",
        )
    proc = subprocess.CompletedProcess(cmd, popen.returncode, stdout, stderr)
    log_path.write_text(
        "$ " + " ".join(cmd) + "\n\n=== stdout ===\n" + proc.stdout
        + "\n=== stderr ===\n" + proc.stderr,
        encoding="utf-8",
    )
    elapsed = time.monotonic() - started
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout + "\n" + proc.stderr).strip().splitlines()[-15:])
        fatal(
            what + " exited " + str(proc.returncode) + " (" + f"{elapsed:.0f}"
            + "s). Output tail:\n" + tail,
            "full log: " + str(log_path),
        )
    print("  [ok] " + what + " (" + f"{elapsed:.0f}" + "s, log: " + log_path.name + ")")
    return proc


# --------------------------------------------------------------------------
# Fixture server lifecycle.
# --------------------------------------------------------------------------

def port_in_use(port: int) -> bool:
    for family, addr in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(0.25)
                s.connect((addr, port))
                return True
        except OSError:
            continue
    return False


def http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def start_fixture_server(serve_dir: Path, port: int, log_path: Path):
    if port_in_use(port):
        fatal(
            "port " + str(port) + " is already in use - refusing to serve fixtures",
            "stop whatever holds it (a leftover 'python -m http.server "
            + str(port) + "'?) or pass --serve-port <free-port>",
        )
    log_handle = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        # --bind 127.0.0.1: loopback-only - never expose the fixture server
        # on all interfaces.
        [
            sys.executable, "-m", "http.server", str(port),
            "--bind", "127.0.0.1", "--directory", str(serve_dir),
        ],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        cwd=str(serve_dir),
    )
    deadline = time.monotonic() + SERVER_READY_TIMEOUT_S
    base = "http://localhost:" + str(port)
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            log_handle.close()
            fatal(
                "fixture server exited immediately (code " + str(proc.returncode) + ")",
                "see " + str(log_path),
            )
        if http_ok(base + "/smooth.html") and http_ok(base + "/janky.html"):
            print("  [ok] fixture server ready on " + base + " (serving " + str(serve_dir) + ")")
            return proc, log_handle
    tree_kill(proc)
    log_handle.close()
    fatal(
        "fixture server did not become ready within "
        + str(SERVER_READY_TIMEOUT_S) + "s",
        "see " + str(log_path),
    )


def stop_fixture_server(proc, log_handle, port: int) -> bool:
    """Kill the server (tree-kill: same treatment as every other subprocess,
    so a hypothetical child can never outlive it) and verify the port is
    actually freed. Returns True when freed; False = leak (caller must force
    a nonzero exit)."""
    try:
        tree_kill(proc)
    finally:
        try:
            log_handle.close()
        except OSError:
            pass
    deadline = time.monotonic() + PORT_FREE_TIMEOUT_S
    while time.monotonic() < deadline:
        if not port_in_use(port):
            print("  [ok] fixture server stopped, port " + str(port) + " freed")
            return True
        time.sleep(0.25)
    print(
        "ERROR: fixture server killed but port " + str(port)
        + " still in use after " + str(PORT_FREE_TIMEOUT_S) + "s - port leak",
        file=sys.stderr,
    )
    return False


# --------------------------------------------------------------------------
# Pipeline stages.
# --------------------------------------------------------------------------

def run_capture(node: str, spec: Path, transition: str, out_dir: Path, logs: Path) -> Path:
    proc = run_cmd(
        [
            node,
            str(SCRIPTS_DIR / "capture_motion.mjs"),
            "--spec", str(spec),
            "--transition", transition,
            "--out", str(out_dir),
        ],
        logs / ("capture-" + transition + ".log"),
        CAPTURE_TIMEOUT_S,
        "capture " + transition,
    )
    # The harness prints "[capture] done: <abs-run-dir>" as its final line.
    match = None
    for line in proc.stdout.splitlines():
        m = re.match(r"\[capture\] done: (.+)$", line.strip())
        if m:
            match = m.group(1).strip()
    if not match:
        fatal(
            "could not parse the run dir from capture output for " + transition,
            "expected a '[capture] done: <dir>' line; see "
            + str(logs / ("capture-" + transition + ".log")),
        )
    run_dir = Path(match)
    if not (run_dir / transition).is_dir():
        fatal(
            "capture reported run dir " + str(run_dir)
            + " but " + transition + "/ is missing inside it"
        )
    return run_dir


def ensure_stage(
    uv: str, script: str, tdir: Path, produced: str, logs: Path, force: bool
) -> None:
    if not force and (tdir / produced).is_file():
        print("  [ok] " + script + " on " + tdir.name + " - reusing existing " + produced)
        return
    run_cmd(
        [uv, "run", str(SCRIPTS_DIR / script), str(tdir)],
        logs / (script.replace(".py", "") + "-" + tdir.name + ".log"),
        PIPELINE_STAGE_TIMEOUT_S,
        script + " on " + tdir.name,
    )


# --------------------------------------------------------------------------
# White-fraction heuristic (the Step-2 checker approach, ported: the flash
# frame is the one whose near-white pixel share dominates).
# --------------------------------------------------------------------------

def white_fraction(frame_path: Path) -> float:
    with Image.open(frame_path) as im:
        rgb = im.convert("RGB").reduce(WHITE_DOWNSCALE_FACTOR)
    data = rgb.tobytes()
    total = rgb.width * rgb.height
    lvl = WHITE_PIXEL_MIN_LEVEL
    count = 0
    for i in range(0, len(data), 3):
        if data[i] >= lvl and data[i + 1] >= lvl and data[i + 2] >= lvl:
            count += 1
    return count / total if total else 0.0


# --------------------------------------------------------------------------
# Order-shuffle transform.
# --------------------------------------------------------------------------

def build_shuffled_filmstrip(janky_tdir: Path, filmstrip: dict) -> dict:
    selected = filmstrip.get("selected", [])
    if len(selected) < 3:
        fatal(
            "janky filmstrip has only " + str(len(selected))
            + " selected frames - too few to order-shuffle meaningfully",
            "re-run the pipeline; a janky capture should select 5-9 frames",
        )
    perm = ends_interleave_permutation(len(selected))
    out_dir = janky_tdir / SHUFFLED_DIR_NAME
    # Deterministic regeneration: content is a pure function of
    # filmstrip.json + the fixed permutation, so recreating in place is a
    # byte-equivalent rewrite, not a violation of the append-only contract.
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    rows = []
    for pos, orig_idx in enumerate(perm, start=1):
        entry = selected[orig_idx]
        src = janky_tdir / entry["file"]
        if not src.is_file():
            fatal("selected filmstrip frame missing: " + str(src))
        # OPAQUE names on purpose: the judge sees these paths in its prompt,
        # and an original-filename suffix (index + elapsed-ms) would leak the
        # true chronology through the PATHS, weakening the order-sensitivity
        # check. The ONLY true-order substrate the judge may use is the
        # burned-in chips; the original-file mapping lives ONLY in the
        # filmstrip-shuffled.json manifest below.
        dest = out_dir / ("shuffled-" + f"{pos:02d}" + src.suffix)
        shutil.copy2(src, dest)
        rows.append(
            {
                "position": pos,
                "file": SHUFFLED_DIR_NAME + "/" + dest.name,
                "originalFile": entry["file"],
                "originalIndex": entry["index"],
                "originalElapsedMs": entry["elapsedMs"],
                "originalReason": entry["reason"],
            }
        )
    manifest = {
        "createdUtc": utc_now_iso(),
        "sourceFilmstrip": "filmstrip.json",
        "permutation": perm,
        "permutationScheme": "ends-interleave (fixed, deterministic; see calibrate.py)",
        "note": (
            "Presentation order is scrambled; burned-in chips keep their "
            "ORIGINAL #index/+ms labels, so the presented sequence is "
            "temporally non-monotonic on purpose. A judge reading these in "
            "presentation order must answer differently than on the true "
            "order or flag the inconsistency (SKILL.md calibration "
            "procedure, dispatch (c))."
        ),
        "framesInPresentationOrder": rows,
    }
    (janky_tdir / SHUFFLED_MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


# --------------------------------------------------------------------------
# The mechanical assertion battery.
# --------------------------------------------------------------------------

def make_assertion(name: str, ok: bool, evidence: list[str]) -> dict:
    return {"name": name, "verdict": "PASS" if ok else "FAIL", "evidence": evidence}


def evaluate_assertions(
    smooth_tdir: Path,
    smooth_gates: dict,
    smooth_fs: dict,
    janky_tdir: Path,
    janky_gates: dict,
    janky_fs: dict,
    shuffled_manifest: dict,
) -> list[dict]:
    assertions: list[dict] = []

    # 1. Smooth anchor: production gates PASS with zero fails.
    s_sum = smooth_gates.get("summary", {})
    ok = s_sum.get("verdict") == "PASS" and s_sum.get("failCount") == 0
    assertions.append(
        make_assertion(
            "smooth-gates-pass",
            ok,
            [
                "smooth-swap gates.json summary: verdict "
                + str(s_sum.get("verdict")) + ", "
                + str(s_sum.get("passCount")) + " pass / "
                + str(s_sum.get("failCount")) + " fail / "
                + str(s_sum.get("skipCount")) + " skip"
            ]
            + (
                []
                if ok
                else [
                    "failing gates: "
                    + ", ".join(
                        g["name"] for g in smooth_gates.get("gates", [])
                        if g.get("verdict") == "FAIL"
                    )
                ]
            ),
        )
    )

    # 2. Janky anchor: summary must be FAIL-mechanical.
    j_sum = janky_gates.get("summary", {})
    ok = j_sum.get("verdict") == "FAIL-mechanical"
    assertions.append(
        make_assertion(
            "janky-gates-fail-mechanical",
            ok,
            [
                "janky-swap gates.json summary: verdict "
                + str(j_sum.get("verdict")) + ", "
                + str(j_sum.get("passCount")) + " pass / "
                + str(j_sum.get("failCount")) + " fail / "
                + str(j_sum.get("skipCount")) + " skip"
            ],
        )
    )

    # 3. Janky anchor: the RIGHT defect classes fired.
    observed_fails = {
        g["name"] for g in janky_gates.get("gates", []) if g.get("verdict") == "FAIL"
    }
    expected_hits = observed_fails & EXPECTED_JANKY_FAIL_GATES
    missing_required = JANKY_ALWAYS_FAIL_GATES - observed_fails
    unexpected = observed_fails - EXPECTED_JANKY_FAIL_GATES
    ok = not missing_required and len(expected_hits) >= JANKY_MIN_EXPECTED_FAIL_COUNT
    evidence = [
        "observed FAIL gates: " + (", ".join(sorted(observed_fails)) or "(none)"),
        "intersection with expected " + str(sorted(EXPECTED_JANKY_FAIL_GATES))
        + " = " + str(sorted(expected_hits))
        + " (need >= " + str(JANKY_MIN_EXPECTED_FAIL_COUNT)
        + ", always including " + str(sorted(JANKY_ALWAYS_FAIL_GATES)) + ")",
    ]
    if missing_required:
        evidence.append("MISSING required gate(s): " + ", ".join(sorted(missing_required)))
    if unexpected:
        evidence.append(
            "unexpected FAIL gate(s) outside the defect inventory: "
            + ", ".join(sorted(unexpected)) + " (surfaced, not gated)"
        )
    assertions.append(make_assertion("janky-expected-defect-classes", ok, evidence))

    # 4. Janky filmstrip contains the white-flash frame (max white-fraction
    # heuristic over the selected SOURCE frames).
    fractions = []
    for entry in janky_fs.get("selected", []):
        src = janky_tdir / entry["sourceFrame"]
        frac = white_fraction(src) if src.is_file() else -1.0
        fractions.append((frac, entry))
    best_frac, best_entry = max(fractions, key=lambda t: t[0]) if fractions else (-1.0, None)
    ok = best_frac >= WHITE_FLASH_MIN_FRACTION
    assertions.append(
        make_assertion(
            "janky-flash-frame-selected",
            ok,
            [
                "max white fraction "
                + f"{best_frac:.3f}"
                + (
                    " at #" + str(best_entry["index"]) + " +"
                    + str(best_entry["elapsedMs"]) + "ms (" + best_entry["reason"] + ")"
                    if best_entry
                    else ""
                )
                + " vs threshold " + str(WHITE_FLASH_MIN_FRACTION)
                + " (white pixel = all channels >= " + str(WHITE_PIXEL_MIN_LEVEL) + ")",
                "per-frame: "
                + ", ".join(
                    "#" + str(e["index"]) + "=" + f"{f:.3f}" for f, e in fractions
                ),
            ],
        )
    )

    # 5. Smooth filmstrip stays sparse and flat.
    s_selected = smooth_fs.get("selected", [])
    s_flat = bool(smooth_fs.get("params", {}).get("flatCurve"))
    ok = len(s_selected) <= SMOOTH_MAX_SELECTED_FRAMES and s_flat
    assertions.append(
        make_assertion(
            "smooth-filmstrip-sparse-flat",
            ok,
            [
                "smooth-swap selected " + str(len(s_selected)) + " frames (max "
                + str(SMOOTH_MAX_SELECTED_FRAMES) + "), flatCurve="
                + str(s_flat).lower()
            ],
        )
    )

    # 6. Shuffled filmstrip really scrambles time: the presented chip
    # timestamps must NOT be monotonically non-decreasing.
    presented = [r["originalElapsedMs"] for r in shuffled_manifest["framesInPresentationOrder"]]
    ok = any(a > b for a, b in zip(presented, presented[1:]))
    assertions.append(
        make_assertion(
            "shuffled-order-nonmonotonic",
            ok,
            [
                "presented elapsed-ms sequence: " + str(presented),
                "permutation (0-based original indices): "
                + str(shuffled_manifest["permutation"]),
            ],
        )
    )

    return assertions


# --------------------------------------------------------------------------
# Judge inputs (ready-to-instantiate; SKILL.md's procedure consumes these).
# --------------------------------------------------------------------------

def template_order_frames(tdir: Path, filmstrip: dict) -> list[str]:
    """Absolute image paths in the Vision-judge dispatch template order:
    grid composite, then per-spike triplets, then the before-anchor."""
    files: list[str] = []
    grid = tdir / "filmstrip" / "grid.jpg"
    if grid.is_file():
        files.append(str(grid))
    for spike in filmstrip.get("spikes", []):
        for rel in spike.get("tripletFiles", []):
            files.append(str(tdir / rel))
    selected = filmstrip.get("selected", [])
    if selected:
        files.append(str(tdir / selected[0]["file"]))
    return files


def build_judge_inputs(
    smooth_tdir: Path,
    smooth_gates: dict,
    smooth_fs: dict,
    janky_tdir: Path,
    janky_gates: dict,
    janky_fs: dict,
    shuffled_manifest: dict,
) -> dict:
    shuffled_frames = [
        str(janky_tdir / row["file"])
        for row in shuffled_manifest["framesInPresentationOrder"]
    ]
    return {
        "smoothProduction": {
            "transitionDir": str(smooth_tdir),
            "framesInOrder": template_order_frames(smooth_tdir, smooth_fs),
            "gatesPath": str(smooth_tdir / "gates.json"),
            "filmstripPath": str(smooth_tdir / "filmstrip.json"),
            "rubric": smooth_gates.get("rubric", {}),
        },
        "jankyTrueOrder": {
            "transitionDir": str(janky_tdir),
            "framesInOrder": template_order_frames(janky_tdir, janky_fs),
            "gatesPath": str(janky_tdir / "gates.json"),
            "filmstripPath": str(janky_tdir / "filmstrip.json"),
            "rubric": janky_gates.get("rubric", {}),
        },
        "jankyShuffled": {
            "transitionDir": str(janky_tdir),
            "framesInOrder": shuffled_frames,
            "gatesPath": str(janky_tdir / "gates.json"),
            "shuffleManifestPath": str(janky_tdir / SHUFFLED_MANIFEST_NAME),
            "rubric": janky_gates.get("rubric", {}),
        },
    }


# --------------------------------------------------------------------------
# Garbage-anchor preparation.
# --------------------------------------------------------------------------

def prepare_garbage_fixtures() -> tuple[Path, Path]:
    """Copy fixtures/ to a temp dir and replace smooth.html with janky
    content (title adjusted). The frozen fixtures are never modified."""
    tmp_root = Path(tempfile.mkdtemp(prefix="judge-motion-garbage-anchor-"))
    garbage_dir = tmp_root / "fixtures"
    shutil.copytree(FIXTURES_DIR, garbage_dir)
    janky_text = (garbage_dir / "janky.html").read_text(encoding="utf-8")
    doctored = re.sub(
        r"<title>.*?</title>",
        "<title>GARBAGE ANCHOR - janky content served as smooth.html</title>",
        janky_text,
        count=1,
        flags=re.S,
    )
    (garbage_dir / "smooth.html").write_text(doctored, encoding="utf-8")
    print(
        "  [ok] garbage anchor prepared at " + str(garbage_dir)
        + " (smooth.html replaced by janky content; frozen fixtures untouched)"
    )
    return tmp_root, garbage_dir


def prepare_spec(serve_dir: Path, port: int, calib_root: Path) -> Path:
    spec_src = serve_dir / FLOW_SPEC_NAME
    if not spec_src.is_file():
        fatal("flow spec not found at " + str(spec_src))
    if port == DEFAULT_SERVE_PORT:
        return spec_src
    rewritten = calib_root / ("fixtures-flow.port" + str(port) + ".json")
    rewritten.write_text(
        spec_src.read_text(encoding="utf-8").replace(
            "localhost:" + str(DEFAULT_SERVE_PORT), "localhost:" + str(port)
        ),
        encoding="utf-8",
    )
    return rewritten


# --------------------------------------------------------------------------
# Main.
# --------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="judge-motion mechanical calibration engine (Step 7)"
    )
    parser.add_argument("--serve-port", type=int, default=DEFAULT_SERVE_PORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--skip-capture",
        metavar="SMOOTH_RUN,JANKY_RUN",
        help="comma-separated pair of existing capture run dirs",
    )
    parser.add_argument("--garbage-anchor", action="store_true")
    args = parser.parse_args(argv)
    if args.skip_capture and args.garbage_anchor:
        parser.error("--garbage-anchor requires a fresh capture; drop --skip-capture")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    mode = "garbage-anchor" if args.garbage_anchor else "default"

    uv = shutil.which("uv")
    if not uv:
        fatal("'uv' not found on PATH", "install uv (https://docs.astral.sh/uv/)")

    out_dir = args.out if args.out.is_absolute() else (Path.cwd() / args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    calib_root = out_dir / (utc_stamp() + "-calibration")
    n = 2
    while calib_root.exists():  # append-only: never overwrite a prior run
        calib_root = out_dir / (utc_stamp() + "-calibration-" + str(n))
        n += 1
    calib_root.mkdir(parents=True)
    logs = calib_root / "logs"
    logs.mkdir()

    print("== judge-motion mechanical calibration ==")
    print("mode: " + mode)
    print("calibration root: " + str(calib_root))

    server_leak = False
    fresh_capture = args.skip_capture is None

    if fresh_capture:
        node = shutil.which("node")
        if not node:
            fatal("'node' not found on PATH", "install Node.js (the capture harness needs it)")
        tmp_root: Path | None = None
        try:
            if args.garbage_anchor:
                tmp_root, serve_dir = prepare_garbage_fixtures()
            else:
                serve_dir = FIXTURES_DIR
            spec = prepare_spec(serve_dir, args.serve_port, calib_root)
            server_proc, server_log = start_fixture_server(
                serve_dir, args.serve_port, logs / "http-server.log"
            )
            try:
                smooth_run = run_capture(node, spec, SMOOTH_TRANSITION, calib_root, logs)
                janky_run = run_capture(node, spec, JANKY_TRANSITION, calib_root, logs)
            finally:
                if not stop_fixture_server(server_proc, server_log, args.serve_port):
                    server_leak = True
        finally:
            if tmp_root is not None:
                shutil.rmtree(tmp_root, ignore_errors=True)
    else:
        parts = [p.strip() for p in args.skip_capture.split(",")]
        if len(parts) != 2:
            fatal(
                "--skip-capture expects exactly two comma-separated run dirs "
                "(smooth first, janky second)"
            )
        smooth_run, janky_run = (Path(p).resolve() for p in parts)
        for run, transition in ((smooth_run, SMOOTH_TRANSITION), (janky_run, JANKY_TRANSITION)):
            if not (run / transition).is_dir():
                fatal(
                    str(run) + " has no " + transition + "/ subdir",
                    "--skip-capture order is <smooth-run>,<janky-run>",
                )

    smooth_tdir = smooth_run / SMOOTH_TRANSITION
    janky_tdir = janky_run / JANKY_TRANSITION

    for tdir in (smooth_tdir, janky_tdir):
        ensure_stage(uv, "select_frames.py", tdir, "filmstrip.json", logs, fresh_capture)
        ensure_stage(uv, "gate_signals.py", tdir, "gates.json", logs, fresh_capture)

    smooth_gates = load_json(smooth_tdir / "gates.json", "smooth gates.json")
    smooth_fs = load_json(smooth_tdir / "filmstrip.json", "smooth filmstrip.json")
    janky_gates = load_json(janky_tdir / "gates.json", "janky gates.json")
    janky_fs = load_json(janky_tdir / "filmstrip.json", "janky filmstrip.json")

    shuffled_manifest = build_shuffled_filmstrip(janky_tdir, janky_fs)
    print("  [ok] shuffled filmstrip: " + str(janky_tdir / SHUFFLED_DIR_NAME))

    assertions = evaluate_assertions(
        smooth_tdir, smooth_gates, smooth_fs,
        janky_tdir, janky_gates, janky_fs,
        shuffled_manifest,
    )
    all_pass = all(a["verdict"] == "PASS" for a in assertions)

    report = {
        "timestampUtc": utc_now_iso(),
        "mode": mode,
        "servePort": args.serve_port,
        "calibrationRoot": str(calib_root),
        "smoothRun": str(smooth_run),
        "jankyRun": str(janky_run),
        "mechanicalAssertions": assertions,
        "shuffledFilmstrip": {
            "dir": str(janky_tdir / SHUFFLED_DIR_NAME),
            "permutation": shuffled_manifest["permutation"],
        },
        "judgeInputs": build_judge_inputs(
            smooth_tdir, smooth_gates, smooth_fs,
            janky_tdir, janky_gates, janky_fs,
            shuffled_manifest,
        ),
        "overallMechanical": "PASS" if all_pass else "FAIL",
    }
    report_path = calib_root / "calibration-mechanical.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print()
    for a in assertions:
        print("[" + a["verdict"] + "] " + a["name"])
        for line in a["evidence"]:
            print("        " + line)
    print()
    print("calibration-mechanical.json: " + str(report_path))

    failed = [a for a in assertions if a["verdict"] == "FAIL"]

    if args.garbage_anchor:
        if all_pass:
            print()
            print("=" * 70)
            print("GARBAGE-ANCHOR ERROR: every mechanical assertion PASSED against a")
            print("defect-injected smooth anchor. The instrument cannot fail garbage -")
            print("do NOT trust any calibration until this is diagnosed and fixed")
            print("(measurement-validity: calibrate with anchors).")
            print("=" * 70)
            return 2
        print()
        print("=" * 70)
        print("FAILED-CALIBRATION (mechanical tier)")
        print("Failed assertions:")
        for a in failed:
            print("  - " + a["name"] + ": " + a["evidence"][0])
        print()
        print("garbage-anchor mode: this red is the EXPECTED outcome - the")
        print("instrument correctly fails a defect-injected smooth anchor.")
        print("=" * 70)
        return 1

    if server_leak:
        print()
        print("FAILED-CALIBRATION: pipeline completed but the fixture server port")
        print("was not freed (see ERROR above) - the capture environment is not")
        print("clean, so this calibration cannot be trusted. Free the port and rerun.")
        return 1

    if not all_pass:
        print()
        print("=" * 70)
        print("FAILED-CALIBRATION (mechanical tier)")
        print("Failed assertions:")
        for a in failed:
            print("  - " + a["name"] + ": " + a["evidence"][0])
        print()
        print("Real verdicts are BLOCKED until a clean calibration (SKILL.md")
        print("'Calibration' - fail loud, never warn-and-proceed).")
        print("=" * 70)
        return 1

    print()
    print("CALIBRATION MECHANICAL: PASS")
    print("Next: dispatch the three vision judges per SKILL.md 'The --calibrate")
    print("procedure' using judgeInputs in calibration-mechanical.json, then write")
    print("calibration-report.md at the calibration root.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
