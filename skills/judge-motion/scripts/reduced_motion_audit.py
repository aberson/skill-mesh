"""reduced_motion_audit.py - judge-motion Step 8 reduced-motion (a11y) audit.

An ON-DEMAND accessibility audit, never a default mode: reducedMotion:
'reduce' suppresses the very content judge-motion exists to judge, so no
other pipeline stage ever sets it. Two phases per transition, and the audit
NEVER silently passes an ignoring target (SKILL.md "Reduced-motion audit
mode"):

    Phase 1 - CSS DETECTION. Fetch the transition URL's HTML and extract
        the actually-served CSS: inline <style> blocks plus every
        same-origin link[rel=stylesheet] sheet (quoted OR unquoted href -
        unquoted attribute values are valid HTML5). A <style> block living
        INSIDE an HTML comment is not served CSS and is skipped, but the
        legacy <style><!-- css --></style> comment-hiding idiom IS served
        CSS (only the comment markers are dropped); CSS comments are
        stripped before the grep (janky.html's frozen-header HTML comment
        literally contains the string "prefers-reduced-motion" - a mention
        in a comment is not a reference). Every declared CSS source gets a
        per-source status row in the evidence (fetched + bytes /
        skipped-cross-origin / skipped-unparseable-href) and any fetch
        failure is FATAL with a remedy - the scanned corpus never silently
        shrinks (a silently-dropped sheet could fabricate a GAP finding on
        a compliant page). Stated scope limits: @import is not followed
        (single-hop fetch) and purely-JS matchMedia suppression is
        invisible to a CSS grep - both are surfaced in evidence, and a GAP
        on such a page is the operator's cue to look closer, never a
        silent wrong verdict. No reference -> finding
        `reduced-motion-gap`, verdict GAP, phase 2 skipped for that
        transition.

    Phase 2 - SUPPRESSION CHECK (only when referenced). Capture the
        transition TWICE through the production harness
        (capture_motion.mjs; measurement-validity: assemble through the
        production code path) - default context, then
        --context-mode reduced-motion - run select_frames.py on both, and
        assert the reduced run is actually still:
          (a) motion mass suppressed (the PRIMARY conjunct):
              realFrameCount_reduced / realFrameCount_default <=
              SUPPRESSED_MAX_REAL_FRAME_RATIO, and
          (b) a suppressed diff-curve SHAPE - one of:
              - genuinely flat: max adjacent-pair pHash diff <=
                FLAT_MAX_DIFF (and a non-blank settled end state), or
              - instant swap: at most INSTANT_SWAP_MAX_ABOVE_FLOOR_DIFFS
                pair diffs above the flat floor (the one legitimate
                content flip), at most INSTANT_SWAP_MAX_BLANK_FRAMES
                blank/backdrop-only frames and only as the flip's
                immediate predecessor (the swap's own paint gap), and a
                non-blank settled end state. Blankness is measured with
                calibrate.py's white-fraction helper; a blank frame
                anywhere else under reduce is a flash defect, not
                suppression.
        select_frames' params.flatCurve is recorded as EVIDENCE ONLY and
        never gates: at the tiny frame counts a suppressed run produces,
        its median+MAD spike statistic degenerates and defaults to "flat"
        (the small-N artifact the iter-1 correctness review caught).
        Both hold -> SUPPRESSED (PASS); either fails -> NOT-SUPPRESSED
        (FAIL) with the numbers as evidence. The audit is mechanical
        screening only - a suspicious reduced run is escalated by the
        OPERATOR to a manual /judge-motion vision-judge dispatch; it is
        never auto-judged.

Artifacts (audit run root = <out>/<UTC>-reduced-motion-audit/, append-only):
    reduced-motion-audit.json   camelCase machine report
    reduced-motion-audit.md     human report; last line is exactly
                                `REDUCED-MOTION AUDIT: PASS|FINDINGS|FAIL`

Overall verdict: PASS iff every audited transition is PASS; any GAP (and no
FAIL) -> FINDINGS - a GAP is a reported finding, never a silent pass; any
FAIL -> FAIL.

Usage:
    uv run scripts/reduced_motion_audit.py --spec <flow-spec.json>
        [--transition <name>]   audit a single transition from the spec
        [--serve-fixtures]      serve this skill's fixtures/ on loopback
                                :8765 (the self-test path; tree-kill + port
                                verified freed on all exits). Real adapters
                                bring up their own app instead.
        [--out <dir>]           default: this skill's own .judge-motion/

Exit codes:
    0   overall PASS (every audited transition suppressed correctly)
    2   overall FINDINGS (>= 1 reduced-motion-gap, zero FAILs)
    1   overall FAIL (motion not suppressed), any tool/config error, or a
        fixture-server port leak
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "Pillow>=10.1",
# ]
# ///
# Pillow is not used by this module directly - it is calibrate.py's
# import-time dependency, and this script imports calibrate for its shared
# server-lifecycle / subprocess helpers (one source of truth, same dir).

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Shared engine helpers - imported, not re-declared (code-quality: reuse
# before abstracting; calibrate.py owns the server lifecycle + tree-kill +
# subprocess conventions this audit mirrors).
from calibrate import (
    CAPTURE_TIMEOUT_S,
    DEFAULT_OUT_DIR,
    DEFAULT_SERVE_PORT,
    FIXTURES_DIR,
    PIPELINE_STAGE_TIMEOUT_S,
    SCRIPTS_DIR,
    WHITE_FLASH_MIN_FRACTION,
    WHITE_PIXEL_MIN_LEVEL,
    fatal,
    load_json,
    run_cmd,
    start_fixture_server,
    stop_fixture_server,
    utc_now_iso,
    utc_stamp,
    white_fraction,
)

# --------------------------------------------------------------------------
# Suppression thresholds - the constants block (single source of truth;
# SKILL.md cites this module and never restates the values). Deliberately
# NOT imported from select_frames.py: an expectation imported from the
# instrument under test would make the check tautological (same rationale
# as calibrate.py's assertion constants).
# --------------------------------------------------------------------------

FLAT_MAX_DIFF = 10
# Max adjacent-pair pHash Hamming distance (of 64 bits) a genuinely-flat
# reduced run may show. 10 = select_frames' own structural-event floor
# semantics, re-derived independently: JPEG re-encode noise between
# visually identical frames is 0-3 bits, real motion events (flash/FOUC/
# layout jump) flip 15-35 - a curve capped at 10 contains no structural
# motion event. A legitimate INSTANT content swap exceeds this floor on
# its one flip pair (measured 20 on the 2026-07-20 suppressed smooth run),
# so that shape routes through the instant-swap branch below; the floor is
# deliberately NOT raised to cover it - a raised floor would also wave
# through real one-frame flashes. NOTE select_frames' params.flatCurve is
# NOT part of the suppression decision: its median+MAD spike statistic
# degenerates at the 2-4 curve points a suppressed run produces and
# defaults to "flat" (small-N artifact, iter-1 correctness finding) - the
# flag is carried as evidence only.

INSTANT_SWAP_MAX_ABOVE_FLOOR_DIFFS = 1
# The instant-swap suppression shape allows at most this many above-floor
# adjacent-pair diffs: a compliant reduced branch swaps content in ONE
# step (before -> after, one structural flip). Two or more above-floor
# diffs mean the content changed and then changed AGAIN - flash-and-
# restore or residual animation, never a single swap. Measured on the
# suppressed smooth anchor (2026-07-20): exactly 1 above-floor diff (20).

BLANK_MIN_WHITE_FRACTION = WHITE_FLASH_MIN_FRACTION
# A reduced-run frame whose near-white pixel share reaches calibrate.py's
# flash-frame threshold is blank/backdrop-only (a bare stage). Reused, not
# re-declared: calibrate.py owns the white-pixel definition + threshold
# (one source of truth), and the separation holds on reduced-run data too
# - measured 2026-07-20: the bare-stage paint-gap frame scores 0.290
# (identical to the janky flash frame - it is the same visual state) vs
# 0.178-0.196 for content frames.

INSTANT_SWAP_MAX_BLANK_FRAMES = 1
# The instant-swap shape tolerates at most ONE blank frame, and ONLY as
# the flip's immediate predecessor. Why not zero: the known-good smooth
# anchor's reduced run genuinely paints one bare-stage frame between "old
# content removed" and "new content painted" (its navigate() clears the
# old page at click and inserts the new one after the simulated load;
# under transition:none that gap is visible for a single captured frame -
# measured blank at +53ms post-trigger, immediately preceding the one
# above-floor flip, white fraction 0.290). Two or more blank frames, or a
# blank anywhere else (before-anchor, post-flip, settled end), is a real
# blank interval / flash defect - never a swap paint gap.

SUPPRESSED_MAX_REAL_FRAME_RATIO = 0.15
# Max realFrameCount_reduced / realFrameCount_default for "suppressed".
# realFrameCount is the damage-driven temporal-density signal (hold-frame
# padding excluded per SKILL.md's hold-frame contract). Observed on the
# smooth fixture (2026-07-19 runs): reduced 3-4 real frames vs ~184
# default = ratio ~0.02. 0.15 gives ~7x headroom for machine variance in
# bring-up frame counts, while any animation that actually still plays
# produces near-continuous damage frames under 0.1x dilation and drives
# the ratio toward 1.

REDUCED_MOTION_GAP_FINDING = "reduced-motion-gap"
# The finding key emitted for a target whose served CSS never references
# the media query (the plan Step 8 contract's named finding).

DEFAULT_RUN_MIN_REAL_FRAMES = 30
# Below this many damage frames in the DEFAULT run, the suppression ratio
# is weak evidence (a near-motionless default looks "suppressed" by
# construction) and the report says so - informational only, never a
# verdict change. Why 30: fixture bring-up alone measures ~4 real frames,
# while even a short animation dilated at the default 0.1x playback adds
# tens of damage frames (~185 observed for the smooth fixture's 300ms
# crossfade) - 30 sits well above bring-up noise and well below any real
# dilated animation. NOTE the curve-flatness flag is NOT this signal: a
# smooth crossfade is flat by design (no structural spikes) yet full of
# motion; realFrameCount is the temporal-density signal (SKILL.md
# hold-frame contract).

CSS_QUERY_TOKEN = "prefers-reduced-motion"

AUDIT_ROOT_SUFFIX = "-reduced-motion-audit"
AUDIT_JSON_NAME = "reduced-motion-audit.json"
AUDIT_MD_NAME = "reduced-motion-audit.md"

FETCH_TIMEOUT_S = 10
# Loopback/LAN dev servers answer static HTML/CSS in milliseconds; 10s of
# silence means the app is down, not slow.

# --------------------------------------------------------------------------
# Phase 1 - served-CSS collection + detection.
# --------------------------------------------------------------------------

HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.I | re.S)
LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.I)
REL_STYLESHEET_RE = re.compile(r"""rel\s*=\s*["']?stylesheet["']?""", re.I)
# href value: double-quoted, single-quoted, or unquoted. Unquoted attribute
# values are valid HTML5 - the earlier quoted-only pattern silently dropped
# unquoted-href stylesheets, which could fabricate a GAP on a compliant
# page (iter-1 bug review HIGH).
HREF_RE = re.compile(
    r"""href\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'<>`]+))""", re.I
)
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)


def fetch_text(url: str, what: str) -> tuple[str, int]:
    """Fetch url and return (decoded_text, raw_byte_count). EVERY failure
    is fatal with a remedy - the audit never silently scans a smaller
    corpus than the page declares (a shrunken corpus could fabricate a
    reduced-motion-gap on a compliant page)."""
    try:
        with urllib.request.urlopen(url, timeout=FETCH_TIMEOUT_S) as resp:
            # urlopen raises HTTPError for every non-2xx, so only an odd
            # 2xx (204 No Content, 206 Partial) can land here.
            if resp.status != 200:
                fatal(
                    what + " fetch returned HTTP " + str(resp.status) + ": " + url,
                    "the audit cannot scan CSS it cannot fully fetch - fix "
                    "the server/route before re-running",
                )
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            try:
                text = raw.decode(charset, errors="replace")
            except LookupError:  # server declared an unknown charset label
                text = raw.decode("utf-8", errors="replace")
            return text, len(raw)
    except urllib.error.HTTPError as exc:
        # Distinct from "unreachable": the server is up and answered.
        fatal(
            what + " fetch returned HTTP " + str(exc.code) + ": " + url,
            "the server is up but this URL is broken (bad <link href> or "
            "missing route) - fix it before re-running; the audit never "
            "scans a smaller corpus than the page declares",
        )
    except (urllib.error.URLError, OSError, ValueError) as exc:
        fatal(
            what + " unreachable at " + url + ": " + str(exc),
            "is the app server running? For the fixture self-test path pass "
            "--serve-fixtures; real adapters bring up their own app first",
        )


def stylesheet_href(link_tag: str) -> str | None:
    """The href value from one <link> tag, or None when no usable href can
    be parsed from it (attribute missing, empty, or malformed)."""
    m = HREF_RE.search(link_tag)
    if not m:
        return None
    value = next((g for g in m.groups() if g is not None), "")
    return value.strip() or None


def url_origin(u: urllib.parse.ParseResult) -> tuple[str, str, int | None]:
    """(scheme, host, port) with default ports normalized, so an explicit
    :80/:443 in markup still compares same-origin (iter-1 bug review)."""
    scheme = u.scheme.lower()
    port = u.port if u.port is not None else {"http": 80, "https": 443}.get(scheme)
    return (scheme, (u.hostname or "").lower(), port)


def collect_served_css(url: str) -> tuple[str, list[dict]]:
    """Fetch the page and return (combined_css_text, sources). EVERY CSS
    source the page declares gets exactly one status row {kind, name,
    status, bytes} with status in {fetched, skipped-cross-origin,
    skipped-unparseable-href} - a declared source is never silently
    dropped, and a failed fetch is fatal (see fetch_text)."""
    html, _ = fetch_text(url, "transition page")

    sources: list[dict] = []
    css_parts: list[str] = []

    # A <style> block INSIDE an HTML comment is not served CSS (janky.html's
    # frozen header comment must never count) - but comments are NOT
    # stripped out of <style> CONTENT: the legacy
    # <style><!-- css --></style> hiding idiom is real served CSS, so only
    # the comment markers are dropped there (iter-1 bug review MEDIUM:
    # wholesale stripping deleted such rules before extraction).
    comment_spans = [m.span() for m in HTML_COMMENT_RE.finditer(html)]

    def in_html_comment(pos: int) -> bool:
        return any(start <= pos < end for start, end in comment_spans)

    k = 0
    for match in STYLE_BLOCK_RE.finditer(html):
        if in_html_comment(match.start()):
            continue
        k += 1
        block = match.group(1).replace("<!--", "").replace("-->", "")
        css_parts.append(block)
        sources.append(
            {
                "kind": "inline-style",
                "name": "inline <style> #" + str(k),
                "status": "fetched",
                "bytes": len(block.encode("utf-8")),
            }
        )

    # Link tags ARE taken from comment-stripped HTML (a <link> inside a
    # comment is not served); stripping cannot damage them because a tag
    # has no inner content.
    html_no_comments = HTML_COMMENT_RE.sub("", html)
    page_origin = url_origin(urllib.parse.urlparse(url))
    for tag in LINK_TAG_RE.findall(html_no_comments):
        if not REL_STYLESHEET_RE.search(tag):
            continue
        href = stylesheet_href(tag)
        if href is None:
            # Never a silent drop: a stylesheet link whose href cannot be
            # parsed is recorded so the evidence shows the corpus may be
            # incomplete.
            sources.append(
                {
                    "kind": "stylesheet",
                    "name": tag[:120],
                    "status": "skipped-unparseable-href",
                    "bytes": 0,
                }
            )
            continue
        sheet_url = urllib.parse.urljoin(url, href)
        if url_origin(urllib.parse.urlparse(sheet_url)) != page_origin:
            sources.append(
                {
                    "kind": "stylesheet",
                    "name": sheet_url,
                    "status": "skipped-cross-origin",  # out of audit scope
                    "bytes": 0,
                }
            )
            continue
        css, nbytes = fetch_text(sheet_url, "stylesheet")
        css_parts.append(css)
        sources.append(
            {
                "kind": "stylesheet",
                "name": sheet_url,
                "status": "fetched",
                "bytes": nbytes,
            }
        )

    return "\n".join(css_parts), sources


def detect_css_reference(url: str) -> tuple[bool, list[str], list[dict]]:
    """Phase 1 verdict for one transition URL. Returns
    (css_referenced, evidence_lines, sources)."""
    combined, sources = collect_served_css(url)
    # CSS comments stripped before the grep: a commented-out media query is
    # not a live reduced-motion branch.
    scannable = CSS_COMMENT_RE.sub("", combined)
    referenced = CSS_QUERY_TOKEN in scannable.lower()
    fetched = [s for s in sources if s["status"] == "fetched"]
    total_bytes = sum(s["bytes"] for s in fetched)

    def source_label(s: dict) -> str:
        if s["status"] == "fetched":
            return s["name"] + " (fetched, " + str(s["bytes"]) + " bytes)"
        return s["name"] + " (" + s["status"] + ")"

    scanned = (
        str(total_bytes) + " bytes scanned across " + str(len(fetched))
        + " fetched source(s); per-source status: "
        + ("; ".join(source_label(s) for s in sources) or "(none)")
    )
    if referenced:
        evidence = [CSS_QUERY_TOKEN + " referenced in served CSS (" + scanned + ")"]
    else:
        evidence = [
            "no " + CSS_QUERY_TOKEN + " reference in served CSS (" + scanned + ")"
        ]
    if "@import" in scannable.lower():
        evidence.append(
            "NOTE: @import rule(s) present in the served CSS - imports are "
            "not followed (single-hop scope), so a reduced-motion branch "
            "reachable only through an @import is invisible to this phase"
        )
    if not fetched:
        evidence.append(
            "WARNING: zero CSS sources fetched from the page - if styling "
            "is JS-injected the audit cannot see it"
        )
    return referenced, evidence, sources


# --------------------------------------------------------------------------
# Phase 2 - capture x2 through the production harness + suppression check.
# --------------------------------------------------------------------------

CAPTURE_DONE_RE = re.compile(r"\[capture\] done: (.+)$")


def run_capture_mode(
    node: str, spec: Path, transition: str, out_root: Path, logs: Path, mode: str
) -> Path:
    """One production-harness capture. mode is 'default' or
    'reduced-motion'; the latter adds --context-mode reduced-motion."""
    cmd = [
        node,
        str(SCRIPTS_DIR / "capture_motion.mjs"),
        "--spec", str(spec),
        "--transition", transition,
        "--out", str(out_root),
    ]
    if mode == "reduced-motion":
        cmd += ["--context-mode", "reduced-motion"]
    proc = run_cmd(
        cmd,
        logs / ("capture-" + transition + "-" + mode + ".log"),
        CAPTURE_TIMEOUT_S,
        "capture " + transition + " (" + mode + ")",
    )
    run_dir = None
    for line in proc.stdout.splitlines():
        m = CAPTURE_DONE_RE.match(line.strip())
        if m:
            run_dir = Path(m.group(1).strip())
    if run_dir is None:
        fatal(
            "could not parse the run dir from capture output for "
            + transition + " (" + mode + ")",
            "expected a '[capture] done: <dir>' line; see "
            + str(logs / ("capture-" + transition + "-" + mode + ".log")),
        )
    if not (run_dir / transition).is_dir():
        fatal(
            "capture reported run dir " + str(run_dir) + " but "
            + transition + "/ is missing inside it"
        )
    return run_dir


def run_select(uv: str, tdir: Path, transition: str, mode: str, logs: Path) -> None:
    run_cmd(
        [uv, "run", str(SCRIPTS_DIR / "select_frames.py"), str(tdir)],
        logs / ("select-" + transition + "-" + mode + ".log"),
        PIPELINE_STAGE_TIMEOUT_S,
        "select_frames " + transition + " (" + mode + ")",
    )


def real_frame_count(tdir: Path, label: str) -> int:
    signals = load_json(tdir / "signals.json", label + " signals.json")
    count = signals.get("realFrameCount")
    if not isinstance(count, int) or count <= 0:
        fatal(
            label + " signals.json has no positive realFrameCount (got "
            + repr(count) + ")",
            "a capture with zero damage frames failed - re-run the audit "
            "and check the capture log",
        )
    return count


def max_curve_diff(filmstrip: dict) -> int:
    diffs = [e.get("diff", 0) for e in filmstrip.get("diffCurve", [])]
    return max(diffs) if diffs else 0


def audited_reduced_frames(tdir: Path, filmstrip: dict) -> list[dict]:
    """Every distinct frame the reduced run's filmstrip evidence touches
    (selected[].sourceFrame union diffCurve[].frame - the before-anchor
    and settled end are always in selected by select_frames' contract), in
    elapsed-time order: [{rel, elapsedMs, path}]. Missing files are fatal
    - the blank-frame screen cannot run on artifacts it cannot open."""
    by_rel: dict[str, int] = {}
    for entry in filmstrip.get("selected", []):
        rel, ms = entry.get("sourceFrame"), entry.get("elapsedMs")
        if rel and isinstance(ms, int) and rel not in by_rel:
            by_rel[rel] = ms
    for entry in filmstrip.get("diffCurve", []):
        rel, ms = entry.get("frame"), entry.get("elapsedMs")
        if rel and isinstance(ms, int) and rel not in by_rel:
            by_rel[rel] = ms
    frames = [
        {"rel": rel, "elapsedMs": ms, "path": tdir / rel}
        for rel, ms in sorted(by_rel.items(), key=lambda kv: (kv[1], kv[0]))
    ]
    if not frames:
        fatal(
            "reduced filmstrip.json names no frames (empty selected + "
            "diffCurve) under " + str(tdir),
            "re-run the audit and check the select_frames log",
        )
    for f in frames:
        if not f["path"].is_file():
            fatal(
                "reduced-run frame missing on disk: " + str(f["path"]),
                "the capture/select artifacts are incomplete - re-run the "
                "audit",
            )
    return frames


def evaluate_suppression(
    default_tdir: Path, reduced_tdir: Path
) -> tuple[str, list[str], dict]:
    """Returns (verdict PASS|FAIL, evidence_lines, metrics).

    PASS requires ratio_ok (the PRIMARY conjunct) AND a suppressed curve
    SHAPE: genuinely flat, or a single instant swap with at most one blank
    paint-gap frame immediately before the flip and a non-blank settled
    end. params.flatCurve never gates (evidence only - see the constants
    block: it defaults to "flat" at tiny frame counts)."""
    default_fs = load_json(default_tdir / "filmstrip.json", "default filmstrip.json")
    reduced_fs = load_json(reduced_tdir / "filmstrip.json", "reduced filmstrip.json")

    reduced_flat_flag = bool(reduced_fs.get("params", {}).get("flatCurve"))
    reduced_max = max_curve_diff(reduced_fs)
    above_floor = [
        e for e in reduced_fs.get("diffCurve", [])
        if e.get("diff", 0) > FLAT_MAX_DIFF
    ]

    rf_default = real_frame_count(default_tdir, "default")
    rf_reduced = real_frame_count(reduced_tdir, "reduced")
    ratio = rf_reduced / rf_default
    ratio_ok = ratio <= SUPPRESSED_MAX_REAL_FRAME_RATIO

    frames = audited_reduced_frames(reduced_tdir, reduced_fs)
    fracs = {f["rel"]: white_fraction(f["path"]) for f in frames}
    blanks = [f for f in frames if fracs[f["rel"]] >= BLANK_MIN_WHITE_FRACTION]
    end_frame = frames[-1]
    end_blank = fracs[end_frame["rel"]] >= BLANK_MIN_WHITE_FRACTION

    branch: str | None = None
    shape_problems: list[str] = []
    if end_blank:
        shape_problems.append(
            "settled end frame " + end_frame["rel"]
            + " is blank/backdrop-only (white fraction "
            + f"{fracs[end_frame['rel']]:.3f}" + " >= "
            + str(BLANK_MIN_WHITE_FRACTION) + ") - the reduced run ends "
            "without content; that is a defect, not suppression"
        )
    elif reduced_max <= FLAT_MAX_DIFF:
        branch = "flat"
    elif len(above_floor) > INSTANT_SWAP_MAX_ABOVE_FLOOR_DIFFS:
        shape_problems.append(
            str(len(above_floor)) + " pair diffs above the flat floor "
            + str(FLAT_MAX_DIFF) + " (max "
            + str(INSTANT_SWAP_MAX_ABOVE_FLOOR_DIFFS) + " for an instant "
            "swap) - the content changed more than once: flash-and-restore "
            "or residual animation, not a single swap"
        )
    else:
        # Instant-swap candidate: exactly one flip. A single blank frame
        # is tolerated ONLY as the flip's immediate predecessor (the
        # swap's own paint gap, measured on the known-good smooth anchor);
        # any other blank is a flash defect.
        if len(blanks) > INSTANT_SWAP_MAX_BLANK_FRAMES:
            shape_problems.append(
                str(len(blanks)) + " blank/backdrop-only frames (max "
                + str(INSTANT_SWAP_MAX_BLANK_FRAMES) + ") - a persisting "
                "blank interval is a flash defect, not a swap paint gap"
            )
        elif blanks:
            flip_rel = above_floor[0].get("frame")
            flip_idx = next(
                (i for i, f in enumerate(frames) if f["rel"] == flip_rel),
                None,
            )
            pred_rel = (
                frames[flip_idx - 1]["rel"]
                if flip_idx is not None and flip_idx > 0
                else None
            )
            if blanks[0]["rel"] != pred_rel:
                shape_problems.append(
                    "blank frame " + blanks[0]["rel"] + " (white fraction "
                    + f"{fracs[blanks[0]['rel']]:.3f}" + ") is not the "
                    "flip's immediate predecessor - a blank outside the "
                    "swap instant is a flash defect, not suppression"
                )
        if not shape_problems:
            branch = "instant-swap"
    shape_ok = branch is not None

    default_flat = bool(default_fs.get("params", {}).get("flatCurve"))
    default_max = max_curve_diff(default_fs)

    evidence = [
        "reduced run diff curve: max pHash diff " + str(reduced_max) + ", "
        + str(len(above_floor)) + " pair diff(s) above the flat floor "
        + str(FLAT_MAX_DIFF) + "; flatCurve="
        + str(reduced_flat_flag).lower()
        + " (evidence only, never gates: the spike statistic defaults to "
        "flat at tiny frame counts)",
        "reduced-frame blank screen (blank = white fraction >= "
        + str(BLANK_MIN_WHITE_FRACTION) + "; white pixel = all channels >= "
        + str(WHITE_PIXEL_MIN_LEVEL) + "): " + str(len(blanks)) + " of "
        + str(len(frames)) + " frames blank - "
        + ", ".join(f["rel"] + "=" + f"{fracs[f['rel']]:.3f}" for f in frames),
        "suppression shape: "
        + (
            branch + " -> ok"
            if shape_ok
            else "VIOLATED - " + "; ".join(shape_problems)
        ),
        "real-frame ratio (primary): reduced " + str(rf_reduced)
        + " / default " + str(rf_default) + " = " + f"{ratio:.4f}"
        + " (suppressed when <= " + str(SUPPRESSED_MAX_REAL_FRAME_RATIO)
        + ") -> " + ("ok" if ratio_ok else "VIOLATED"),
        "default run for contrast: flatCurve=" + str(default_flat).lower()
        + ", max pHash diff " + str(default_max),
    ]
    if rf_default < DEFAULT_RUN_MIN_REAL_FRAMES:
        evidence.append(
            "NOTE: the default run produced only " + str(rf_default)
            + " real frame(s) (< " + str(DEFAULT_RUN_MIN_REAL_FRAMES)
            + ") - a near-motionless default makes the suppression ratio "
            "weak evidence; verify the default capture actually exercised "
            "the animation"
        )
    if branch == "instant-swap" and blanks:
        evidence.append(
            "NOTE: this PASS relied on tolerating one paint-gap blank frame ("
            + blanks[0]["rel"] + ", white fraction "
            + f"{fracs[blanks[0]['rel']]:.3f}" + ") immediately before the "
            "content flip - at this instrument's frame granularity a "
            "hypothetical single-frame flash defect is mechanically "
            "indistinguishable from this anchor's own paint gap; escalate to "
            "a manual /judge-motion vision-judge dispatch if suspicious"
        )
    verdict = "PASS" if (ratio_ok and shape_ok) else "FAIL"
    evidence.append(
        "suppression verdict: "
        + (
            "SUPPRESSED (PASS) via " + str(branch) + " branch"
            if verdict == "PASS"
            else "NOT-SUPPRESSED (FAIL)"
        )
    )
    metrics = {
        "reducedFlatCurve": reduced_flat_flag,
        "reducedMaxDiff": reduced_max,
        "flatMaxDiff": FLAT_MAX_DIFF,
        "aboveFloorDiffCount": len(above_floor),
        "instantSwapMaxAboveFloorDiffs": INSTANT_SWAP_MAX_ABOVE_FLOOR_DIFFS,
        "auditedFrameCount": len(frames),
        "blankFrameCount": len(blanks),
        "blankMinWhiteFraction": BLANK_MIN_WHITE_FRACTION,
        "whiteFractions": {f["rel"]: round(fracs[f["rel"]], 3) for f in frames},
        "settledEndBlank": end_blank,
        "suppressionBranch": branch,
        "defaultFlatCurve": default_flat,
        "defaultMaxDiff": default_max,
        "defaultRealFrameCount": rf_default,
        "reducedRealFrameCount": rf_reduced,
        "realFrameRatio": round(ratio, 4),
        "realFrameRatioMax": SUPPRESSED_MAX_REAL_FRAME_RATIO,
    }
    return verdict, evidence, metrics


# --------------------------------------------------------------------------
# Spec loading (tolerant of extra fields, like the capture harness).
# --------------------------------------------------------------------------

def load_transitions(spec_path: Path, only: str | None) -> tuple[str, list[dict]]:
    spec = load_json(spec_path, "flow spec")
    flow = spec.get("flow", spec_path.stem)
    transitions = spec.get("transitions")
    if not isinstance(transitions, list) or not transitions:
        fatal(
            "flow spec has no transitions[] list: " + str(spec_path),
            "pass a capture_motion.mjs flow spec, e.g. "
            "fixtures/fixtures-flow.json",
        )
    for t in transitions:
        if not isinstance(t, dict) or not t.get("name") or not t.get("url"):
            fatal(
                "every transition needs name + url; offending entry: " + repr(t),
                "see the flow-spec schema in scripts/capture_motion.mjs",
            )
    if only is not None:
        names = [t["name"] for t in transitions]
        transitions = [t for t in transitions if t["name"] == only]
        if not transitions:
            fatal(
                "--transition '" + only + "' not found in the spec",
                "available: " + ", ".join(names),
            )
    return flow, transitions


# --------------------------------------------------------------------------
# Reports.
# --------------------------------------------------------------------------

def overall_verdict(rows: list[dict]) -> str:
    if any(r["verdict"] == "FAIL" for r in rows):
        return "FAIL"
    if any(r["verdict"] == "GAP" for r in rows):
        return "FINDINGS"
    return "PASS"


def write_reports(audit_root: Path, flow: str, spec_path: Path, rows: list[dict]) -> str:
    overall = overall_verdict(rows)
    report = {
        "timestampUtc": utc_now_iso(),
        "flow": flow,
        "spec": str(spec_path),
        "auditRoot": str(audit_root),
        "transitions": rows,
        "overall": overall,
    }
    (audit_root / AUDIT_JSON_NAME).write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Reduced-motion audit - " + flow,
        "",
        "- timestampUtc: " + report["timestampUtc"],
        "- spec: " + str(spec_path),
        "- audit root: " + str(audit_root),
        "- transitions audited: " + str(len(rows)),
        "",
    ]
    for r in rows:
        lines.append("## " + r["name"] + " - " + r["verdict"])
        lines.append("")
        lines.append("- url: " + r["url"])
        lines.append("- cssReferenced: " + str(r["cssReferenced"]).lower())
        if r["finding"]:
            lines.append("- finding: " + r["finding"])
        for e in r["evidence"]:
            lines.append("- " + e)
        if r["defaultRun"]:
            lines.append("- default run: " + r["defaultRun"])
        if r["reducedRun"]:
            lines.append("- reduced run: " + r["reducedRun"])
        lines.append("")
    lines.append("REDUCED-MOTION AUDIT: " + overall)
    (audit_root / AUDIT_MD_NAME).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return overall


# --------------------------------------------------------------------------
# Main.
# --------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="judge-motion reduced-motion (a11y) audit engine (Step 8)"
    )
    parser.add_argument("--spec", type=Path, required=True,
                        help="flow-spec JSON (capture_motion.mjs schema)")
    parser.add_argument("--transition", default=None,
                        help="audit a single transition from the spec")
    parser.add_argument("--serve-fixtures", action="store_true",
                        help="serve this skill's fixtures/ on loopback :"
                             + str(DEFAULT_SERVE_PORT) + " (self-test path)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR,
                        help="audit output root (default: the skill's own "
                             ".judge-motion/)")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    uv = shutil.which("uv")
    if not uv:
        fatal("'uv' not found on PATH", "install uv (https://docs.astral.sh/uv/)")

    spec_path = args.spec if args.spec.is_absolute() else (Path.cwd() / args.spec)
    spec_path = spec_path.resolve()
    flow, transitions = load_transitions(spec_path, args.transition)

    out_dir = args.out if args.out.is_absolute() else (Path.cwd() / args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_root = out_dir / (utc_stamp() + AUDIT_ROOT_SUFFIX)
    n = 2
    while audit_root.exists():  # append-only: never overwrite a prior run
        audit_root = out_dir / (utc_stamp() + AUDIT_ROOT_SUFFIX + "-" + str(n))
        n += 1
    audit_root.mkdir(parents=True)
    logs = audit_root / "logs"
    logs.mkdir()

    print("== judge-motion reduced-motion audit ==")
    print("flow: " + flow + " (" + str(len(transitions)) + " transition(s))")
    print("audit root: " + str(audit_root))

    node: str | None = None
    server_proc = None
    server_log = None
    server_leak = False
    rows: list[dict] = []
    try:
        if args.serve_fixtures:
            server_proc, server_log = start_fixture_server(
                FIXTURES_DIR, DEFAULT_SERVE_PORT, logs / "http-server.log"
            )

        for t in transitions:
            name, url = t["name"], t["url"]
            print()
            print("-- " + name + " --")
            referenced, evidence, sources = detect_css_reference(url)
            row = {
                "name": name,
                "url": url,
                "cssReferenced": referenced,
                "verdict": None,
                "finding": None,
                "evidence": evidence,
                "cssSources": sources,
                "defaultRun": None,
                "reducedRun": None,
                "metrics": None,
            }
            if not referenced:
                # The never-silently-pass rule: an ignoring target is a
                # reported finding; phase 2 is skipped (nothing to
                # suppress-check when no branch exists).
                row["verdict"] = "GAP"
                row["finding"] = REDUCED_MOTION_GAP_FINDING
                row["evidence"].append(
                    "phase 2 skipped: no reduced-motion branch to verify"
                )
                print("  [GAP] " + evidence[0])
                rows.append(row)
                continue
            print("  [ok] " + evidence[0])

            if node is None:
                node = shutil.which("node")
                if not node:
                    fatal(
                        "'node' not found on PATH",
                        "install Node.js (the capture harness needs it)",
                    )
            default_run = run_capture_mode(node, spec_path, name, audit_root, logs, "default")
            reduced_run = run_capture_mode(node, spec_path, name, audit_root, logs, "reduced-motion")
            default_tdir = default_run / name
            reduced_tdir = reduced_run / name
            run_select(uv, default_tdir, name, "default", logs)
            run_select(uv, reduced_tdir, name, "reduced-motion", logs)

            verdict, supp_evidence, metrics = evaluate_suppression(
                default_tdir, reduced_tdir
            )
            row["verdict"] = verdict
            row["evidence"] += supp_evidence
            row["defaultRun"] = str(default_run)
            row["reducedRun"] = str(reduced_run)
            row["metrics"] = metrics
            for line in supp_evidence:
                print("  " + ("[ok] " if verdict == "PASS" else "[!!] ") + line)
            rows.append(row)
    finally:
        if server_proc is not None:
            if not stop_fixture_server(server_proc, server_log, DEFAULT_SERVE_PORT):
                server_leak = True

    overall = write_reports(audit_root, flow, spec_path, rows)

    print()
    for r in rows:
        print("[" + r["verdict"] + "] " + r["name"])
    print()
    print(AUDIT_JSON_NAME + ": " + str(audit_root / AUDIT_JSON_NAME))
    print(AUDIT_MD_NAME + ":   " + str(audit_root / AUDIT_MD_NAME))
    print()
    print("REDUCED-MOTION AUDIT: " + overall)

    if server_leak:
        print(
            "ERROR: fixture server port not freed (see above) - the capture "
            "environment is not clean; treating this audit as failed.",
            file=sys.stderr,
        )
        return 1
    return {"PASS": 0, "FINDINGS": 2, "FAIL": 1}[overall]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
