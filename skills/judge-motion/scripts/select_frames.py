# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "Pillow>=10.1",
#     "imagehash>=4.3",
# ]
# ///
"""select_frames.py - judge-motion Step 4 frame pipeline (diff-spike selection + filmstrip).

Input: one captured transition dir (from capture_motion.mjs) containing
frames/<elapsed-ms-7-digit>.jpg + signals.json. Output (into the transition
dir, or --out): filmstrip/ (burned-in overlaid copies of the selected frames,
grid.jpg composite, per-spike full-res triplets) + filmstrip.json manifest.

Hold frames (signals.json.holdFrames, elapsed-ms values; byte-identical
frame-count-floor padding per SKILL.md's hold-frame contract) are excluded
from candidate selection entirely. Pre-trigger frames are excluded from the
diff curve, but the LAST pre-trigger frame is kept as the explicit `before`
anchor (the true resting state; see collect_candidates).

Pure PIL + imagehash - no ffmpeg, no scipy/skimage. SSIM is intentionally
skipped; the secondary diff signal is a pure-PIL channel-aware MSE proxy
(max over per-channel R/G/B MSE; see constants below), which covers pHash's
blind spots (pure global luminance shifts AND same-luminance hue swaps)
without new deps.

Usage:
    uv run scripts/select_frames.py <transition-dir> [--max-frames 9]
                                    [--grid-cells 6] [--out <dir>]
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import NoReturn

from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat
import imagehash

# --------------------------------------------------------------------------
# Tunable constants. Spike thresholds are RELATIVE to the curve's own robust
# statistics (median + K * scaled-MAD); the only absolute numbers are floors
# that guard degenerate curves, each with its rationale.
# --------------------------------------------------------------------------

PHASH_HASH_SIZE = 8
# 64-bit pHash (8x8 DCT). Standard size; adjacent-frame Hamming distance
# ranges 0..64. Re-encode noise between visually identical JPEGs is 0-3 bits;
# a structural event (white flash, FOUC, layout jump) flips 15-35 bits.

SPIKE_K = 4.0
# A frame is a spike when its diff exceeds median + K * scaled-MAD. 4 robust
# sigmas: gradual slow-motion animation (many small, similar deltas) stays
# in-band; one-frame structural events do not. MAD (median absolute
# deviation) over mean/std because a single huge flash frame would inflate
# std enough to hide itself.

MAD_TO_SIGMA = 1.4826
# Standard consistency constant: scaled-MAD = 1.4826 * MAD estimates sigma
# for normally-distributed data, making SPIKE_K read as "K sigmas".

PHASH_MIN_SPIKE_DELTA = 10
# Floor (hash bits above median) for the pHash threshold. Guards MAD == 0
# curves - a mostly-static capture yields median 0 / MAD 0, where any 1-bit
# JPEG-noise wobble would otherwise count as a spike. 10 bits (~16% of the
# hash) sits well above re-encode noise (0-3) and well below real
# flash/FOUC events (15-35).

MSE_PROXY_SIZE = (64, 64)
# Both frames of a pair are downscaled to this size (RGB, kept per-channel)
# before the MSE proxy; small enough to be nearly free per pair, large
# enough that a region flash still moves the mean.

MSE_MIN_SPIKE_DELTA = 400.0
# Floor (0-255 per-channel MSE above median) for the MSE proxy. The proxy is
# CHANNEL-AWARE: MSE is computed per channel (R, G, B) and the MAX channel
# taken, so a same-luminance hue swap registers on whichever channel moved -
# empirically, a red<->green solid swap scores phash 0 AND grayscale MSE ~36
# (invisible to both), but ~14000 on the red channel. 400 = a 20-level
# average per-pixel deviation on the strongest channel, a clearly visible
# change; JPEG re-encode noise on identical content stays under ~50. Same
# MAD == 0 degenerate-curve rationale as PHASH_MIN_SPIKE_DELTA.

FLAT_MAXIMA_MIN_DELTA = 3
# Flat-curve (no-spike) mode: a "mild maximum" earns a filmstrip slot only
# if it clears the median by >= 3 hash bits - just above JPEG re-encode
# noise, so a perfectly flat curve selects only first/mid/last.

FLAT_MAX_SELECTED = 7
# Flat-curve selections stay sparse (SKILL.md: smooth fixture must select
# <= 7): first/mid/last + at most (7 - 3) mild maxima.

MIN_SELECTED = 5
# Spike-mode selection floor (the 5-9 contract). Padded with evenly-spaced
# baseline frames when spike roles alone come in under it; only fewer when
# the capture itself has fewer candidate frames.

MAX_SELECTED = 9
# Selection-budget ceiling (the other half of the 5-9 contract). More frames
# dilute the vision judge's per-frame attention and blow the image-token
# budget the D4 judge protocol is sized for; --max-frames is clamped to it.

REASON_VOCABULARY = ["before", "baseline", "peak", "onset", "settle", "after"]
# Every reason string this script can emit in selected[].reason (and in the
# filmstrip filenames). Written into filmstrip.json params.reasonVocabulary
# so the judge-prompt author (Step 6) reads the actual emitted vocabulary
# from data instead of assuming the plan's taxonomy. "before" = the explicit
# last-pre-trigger resting-state anchor AND the last stable frame ahead of a
# spike; "baseline" = flat-curve / evenly-spaced representative picks.

BLOCK_GRID = 16
# Diff-localization granularity: the spike frame vs its predecessor is
# compared on a 16x16 grid of mean-abs-diff blocks. Coarse on purpose - the
# box tells the vision judge WHERE to look, not the exact pixels.

BLOCK_ABS_FLOOR = 12.0
# A block counts as "changed" only above 12 gray levels of mean abs diff -
# above JPEG blocking noise, low enough to keep genuine content changes.

BLOCK_REL_FRAC = 0.30
# ... and above 30% of the strongest block's diff, so the box hugs the
# dominant change region instead of swallowing faint global shimmer.

BOX_COLOR = (255, 40, 40)
# Saturated red rectangle: high contrast against both light and dark UI.

BOX_LINE_MIN_WIDTH = 3
BOX_LINE_WIDTH_DIVISOR = 300
# Box outline width = max(BOX_LINE_MIN_WIDTH, frame_width // DIVISOR):
# ~4px on a 1280px frame, scaling up on larger captures so the rectangle
# survives the grid downscale, never thinner than 3px.

BBOX_INSET = 3
# Diff bboxes are pulled in from the frame edge by this many px so a
# full-frame change still renders a visible rectangle (an edge-flush box
# disappears against the image border).

CHIP_FONT_SIZE = 16
GRID_FONT_SIZE = 14
CHIP_PAD = 6
# PIL's default embedded font (no font-file deps) via load_default(size=),
# guaranteed by the Pillow>=10.1 pin (older Pillows silently fell back to
# the tiny fixed-size bitmap font). CHIP_PAD = px of black padding around
# the chip text so glyphs never touch the chip edge.

GRID_CELL_WIDTH = 400
# Grid cells are downscaled to this width - the grid is a gestalt scan, the
# full-res filmstrip/triplet copies carry the detail.

GRID_LABEL_HEIGHT = 24
GRID_MAX_CELLS = 6
# D4 judge-protocol constraint: the composite never exceeds 6 cells.

GRID_MAX_COLS = 3
# Grid column cap: 3 x GRID_CELL_WIDTH + padding stays near 1200px wide, a
# comfortable single-glance width for the vision judge at API image sizes.

GRID_PAD = 8
# Px of dark gutter between grid cells so adjacent frames read as separate.

JPEG_QUALITY = 90
# Filmstrip copies are judge evidence; keep re-encode loss low.

GRID_JPEG_QUALITY = 85
# The grid composite is a gestalt scan, not judge-grade evidence (the
# full-res filmstrip/triplet copies above carry that) - a slightly lower
# quality keeps the multi-cell composite small for vision-token budgets.


# --------------------------------------------------------------------------
# Fail-loud helpers (style mirrors capture_motion.mjs: FATAL + Remedy, exit 1)
# --------------------------------------------------------------------------

def fatal(message: str, remedy: str | None = None) -> NoReturn:
    print("FATAL: " + message, file=sys.stderr)
    if remedy:
        print("Remedy: " + remedy, file=sys.stderr)
    sys.exit(1)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    # load_default(size=) is guaranteed by the Pillow>=10.1 pin (PEP 723
    # header); no bitmap-font fallback - it silently rendered tiny labels.
    return ImageFont.load_default(size=size)


# --------------------------------------------------------------------------
# Input loading
# --------------------------------------------------------------------------

def load_signals(transition_dir: Path) -> dict:
    signals_path = transition_dir / "signals.json"
    if not signals_path.is_file():
        fatal(
            "signals.json not found at " + str(signals_path),
            "Pass a transition dir produced by capture_motion.mjs "
            "(.judge-motion/<run-id>/<transition>/).",
        )
    try:
        with open(signals_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as err:
        fatal(
            "signals.json unreadable at " + str(signals_path) + ": " + str(err),
            "Re-run the capture for this transition; a truncated signals.json "
            "means the capture failed mid-write.",
        )


def hold_frame_ms_set(signals: dict) -> set[int]:
    """holdFrames on disk is a list of elapsed-ms ints; accept filename
    strings too (strip extension) in case the field shape ever shifts."""
    raw = signals.get("holdFrames") or []
    out: set[int] = set()
    for entry in raw:
        if isinstance(entry, int):
            out.add(entry)
        elif isinstance(entry, str):
            stem = entry.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            try:
                out.add(int(stem))
            except ValueError:
                fatal(
                    "Unparseable holdFrames entry: " + repr(entry),
                    "holdFrames must be elapsed-ms integers or "
                    "<elapsed-ms>.jpg filenames (capture_motion.mjs contract).",
                )
        else:
            fatal(
                "Unexpected holdFrames entry type: " + repr(entry),
                "holdFrames must be elapsed-ms integers (capture_motion.mjs "
                "contract).",
            )
    return out


def collect_candidates(
    frames_dir: Path, hold_ms: set[int], trigger_ms: int
) -> tuple[list[tuple[int, Path]], int, int, tuple[int, Path] | None]:
    """Time-ordered (elapsed_ms, path) candidates with hold frames AND
    pre-trigger frames excluded. Returns (candidates, hold_excluded,
    pre_trigger_excluded, before_frame).

    Pre-trigger exclusion rationale: the judged unit is the TRANSITION, which
    starts at signals.triggerOffsetMs. Frames captured before it are page
    bring-up noise - most damagingly the blank pre-first-paint frame followed
    by the initial content render, which manufactures a huge fake diff spike
    (observed: blank@44ms -> render@338ms = 31/64 hash bits) that is not a
    defect of the transition under judgment.

    before_frame is the LAST pre-trigger (non-hold) frame: the true resting
    state. It is returned separately so main() can select it as the explicit
    `before` anchor while keeping it OUT of the diff curve / spike statistics
    entirely - it has no adjacent-pair partner across the trigger boundary,
    and the first POST-trigger frame is NOT a safe substitute (a synchronous
    on-click effect, e.g. the janky fixture's undilated spinner, is already
    in progress by the first post-trigger paint, so anchoring there hands
    the judge a defect-in-progress as 'what it looked like before')."""
    if not frames_dir.is_dir():
        fatal(
            "frames dir not found at " + str(frames_dir),
            "Run capture_motion.mjs first; it writes frames/*.jpg into the "
            "transition dir.",
        )
    entries: list[tuple[int, Path]] = []
    hold_excluded = 0
    pre_trigger_excluded = 0
    before_frame: tuple[int, Path] | None = None
    for path in sorted(frames_dir.glob("*.jpg")):
        try:
            elapsed = int(path.stem)
        except ValueError:
            fatal(
                "Frame filename does not follow the <elapsed-ms-padded>.jpg "
                "convention: " + path.name,
                "The frames dir must contain only capture_motion.mjs output; "
                "remove stray files from " + str(frames_dir) + ".",
            )
        if elapsed in hold_ms:
            hold_excluded += 1  # hold-frame contract: byte-identical padding, never a candidate
            continue
        if elapsed < trigger_ms:
            pre_trigger_excluded += 1  # excluded from the curve (see docstring)
            before_frame = (elapsed, path)  # sorted glob: ends as the LAST one
            continue
        entries.append((elapsed, path))
    if not entries:
        fatal(
            "Zero candidate frames in " + str(frames_dir)
            + " after excluding " + str(hold_excluded) + " hold frame(s) and "
            + str(pre_trigger_excluded) + " pre-trigger frame(s).",
            "Verify the capture succeeded (frames/*.jpg present), that "
            "signals.json holdFrames is not claiming every frame, and that "
            "triggerOffsetMs is not later than every frame timestamp.",
        )
    return entries, hold_excluded, pre_trigger_excluded, before_frame


# --------------------------------------------------------------------------
# Diff curve
# --------------------------------------------------------------------------

def compute_curve(candidates: list[tuple[int, Path]]) -> list[dict]:
    """Adjacent-pair diff curve. Entry i-1 describes the change arriving at
    candidate i: {idx, frame, elapsedMs, diff (pHash Hamming), mse (max
    per-channel MSE - see MSE_MIN_SPIKE_DELTA)}. Streams: each image is
    opened once; only its hash + small RGB copy stay in memory."""
    prev_hash = None
    prev_small = None
    curve: list[dict] = []
    for i, (elapsed, path) in enumerate(candidates):
        try:
            with Image.open(path) as img:
                rgb = img.convert("RGB")
        except OSError as err:
            fatal(
                "Unreadable frame " + str(path) + ": " + str(err),
                "Re-run the capture; a truncated JPEG means the capture "
                "process was killed mid-write.",
            )
        h = imagehash.phash(rgb, hash_size=PHASH_HASH_SIZE)
        small = rgb.resize(MSE_PROXY_SIZE, Image.Resampling.BILINEAR)
        if prev_hash is not None:
            diff_img = ImageChops.difference(small, prev_small)
            # channel-aware: max per-channel MSE, so a same-luminance hue
            # swap (grayscale-invisible) registers on the channel it moved
            rms_per_channel = ImageStat.Stat(diff_img).rms  # [R, G, B]
            mse = max(r * r for r in rms_per_channel)
            curve.append(
                {
                    "idx": i,  # candidate index this entry lands on
                    "frame": "frames/" + path.name,
                    "elapsedMs": elapsed,
                    "diff": int(h - prev_hash),
                    "mse": round(mse, 2),
                }
            )
        prev_hash, prev_small = h, small
    return curve


def robust_threshold(values: list[float], min_delta: float) -> tuple[float, float, float]:
    """(median, scaled_mad, threshold) with threshold = median +
    max(SPIKE_K * scaled_mad, min_delta). The floor guards MAD == 0 curves."""
    med = statistics.median(values)
    mad = statistics.median([abs(v - med) for v in values])
    scaled = MAD_TO_SIGMA * mad
    return med, scaled, med + max(SPIKE_K * scaled, min_delta)


def detect_spikes(curve: list[dict]) -> tuple[list[dict], dict]:
    """Group consecutive above-threshold curve points into spikes.
    Returns (spikes, stats). Each spike: {i0, i1, peak_ci, peak_diff}
    where i0/i1/peak_ci are CANDIDATE indices (curve entry idx)."""
    diffs = [float(e["diff"]) for e in curve]
    mses = [float(e["mse"]) for e in curve]
    d_med, d_mad, d_thr = robust_threshold(diffs, PHASH_MIN_SPIKE_DELTA)
    m_med, m_mad, m_thr = robust_threshold(mses, MSE_MIN_SPIKE_DELTA)
    stats = {
        "phashMedian": d_med,
        "phashScaledMad": round(d_mad, 3),
        "phashThreshold": round(d_thr, 3),
        "mseMedian": round(m_med, 2),
        "mseScaledMad": round(m_mad, 2),
        "mseThreshold": round(m_thr, 2),
    }
    mask = [
        (e["diff"] > d_thr) or (e["mse"] > m_thr) for e in curve
    ]  # OR: MSE backstops pHash's global-luminance + same-luminance-hue blind spots
    spikes: list[dict] = []
    run_start = None
    for k in range(len(curve) + 1):
        active = k < len(curve) and mask[k]
        if active and run_start is None:
            run_start = k
        elif not active and run_start is not None:
            group = curve[run_start:k]
            peak = max(group, key=lambda e: (e["diff"], e["mse"]))
            spikes.append(
                {
                    "i0": group[0]["idx"],
                    "i1": group[-1]["idx"],
                    "peak_ci": peak["idx"],
                    "peak_diff": peak["diff"],
                    "peak_mse": peak["mse"],
                }
            )
            run_start = None
    stats["spikeMask"] = mask
    return spikes, stats


# --------------------------------------------------------------------------
# Selection
# --------------------------------------------------------------------------

def local_maxima(curve: list[dict]) -> list[dict]:
    """Curve entries that are local maxima AND clear the median by
    FLAT_MAXIMA_MIN_DELTA (above JPEG re-encode noise), strongest first."""
    med = statistics.median([e["diff"] for e in curve])
    out = []
    for k, e in enumerate(curve):
        left = curve[k - 1]["diff"] if k > 0 else -1
        right = curve[k + 1]["diff"] if k + 1 < len(curve) else -1
        if e["diff"] > left and e["diff"] >= right and e["diff"] >= med + FLAT_MAXIMA_MIN_DELTA:
            out.append(e)
    out.sort(key=lambda e: (e["diff"], e["mse"]), reverse=True)
    return out


def select_frames_for(
    candidates: list[tuple[int, Path]],
    curve: list[dict],
    spikes: list[dict],
    max_frames: int,
    reserved_slots: int = 0,
) -> tuple[dict[int, str], bool]:
    """Returns ({candidate_idx: reason}, flat_curve_flag).

    reserved_slots = filmstrip slots already consumed OUTSIDE the curve (the
    explicit pre-trigger before-anchor), so the 5-9 budget, the MIN_SELECTED
    padding floor, and the FLAT_MAX_SELECTED cap all count the TOTAL strip,
    not just the curve-based picks."""
    m = len(candidates)
    budget = max(1, max_frames - reserved_slots)
    selected: dict[int, str] = {}

    def add(ci: int, reason: str) -> None:
        if 0 <= ci < m and ci not in selected and len(selected) < budget:
            selected[ci] = reason

    if not curve:
        # 1 candidate: nothing to diff; ship what exists.
        add(0, "baseline")
        return selected, True

    global_peak = max(curve, key=lambda e: (e["diff"], e["mse"]))

    if spikes:
        # ALWAYS include the global-maximum diff frame (contract), first so
        # the budget can never squeeze it out.
        add(global_peak["idx"], "peak")
        by_strength = sorted(spikes, key=lambda s: (s["peak_diff"], s["peak_mse"]), reverse=True)
        for rank, sp in enumerate(by_strength):
            add(sp["peak_ci"], "peak")
            # before = last stable frame, after = first post-spike frame
            add(sp["i0"] - 1, "before")
            add(sp["i1"] + 1, "after")
            if rank == 0:
                # full role set for the strongest spike only; weaker spikes
                # get peak + flanks so the budget spreads across events
                add(sp["i0"], "onset")
                add(sp["i1"], "settle")
        # resting-state anchors if budget allows
        add(0, "baseline")
        add(m - 1, "baseline")
        # 5-9 contract floor (minus slots the before-anchor already holds):
        # pad with evenly-spaced baselines
        want = min(MIN_SELECTED - reserved_slots, m)
        if len(selected) < want:
            probes = want * 2  # more probes than slots so collisions skip
            for k in range(probes):
                if len(selected) >= want:
                    break
                add(round(k * (m - 1) / max(1, probes - 1)), "baseline")
            ci = 0
            while len(selected) < want and ci < m:  # dense-collision fallback
                add(ci, "baseline")
                ci += 1
        # Remaining budget goes to the strongest SUB-threshold local maxima:
        # mild repeated steps (stepped/janky animation) live below the spike
        # threshold yet are exactly what the vision judge needs to see.
        if len(selected) < budget:
            for e in local_maxima(curve):
                if len(selected) >= budget:
                    break
                add(e["idx"], "peak")
        return selected, False

    # Flat curve: sparse representative set, <= FLAT_MAX_SELECTED total
    # (including any reserved before-anchor slot).
    cap = min(FLAT_MAX_SELECTED - reserved_slots, budget)
    add(0, "baseline")
    add(m // 2, "baseline")
    add(m - 1, "baseline")
    # strongest first, so "always include the max-diff frame" holds whenever
    # the curve is not perfectly uniform
    for e in local_maxima(curve):
        if len(selected) >= cap:
            break
        add(e["idx"], "peak")
    return selected, True


# --------------------------------------------------------------------------
# Rendering: overlays, boxes, grid, triplets
# --------------------------------------------------------------------------

def draw_chip(img: Image.Image, text: str) -> None:
    """White-on-black label chip, top-left corner (high contrast against any
    frame content; corner placement stays out of most UI action)."""
    draw = ImageDraw.Draw(img)
    font = load_font(CHIP_FONT_SIZE)
    pad = CHIP_PAD
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rectangle([0, 0, w + 2 * pad, h + 2 * pad], fill=(0, 0, 0))
    draw.text((pad - bbox[0], pad - bbox[1]), text, fill=(255, 255, 255), font=font)


def block_diff_bbox(cur_path: Path, prev_path: Path) -> tuple[int, int, int, int] | None:
    """Coarse BLOCK_GRID x BLOCK_GRID mean-abs-diff between a spike frame and
    its predecessor; returns a pixel-space bbox around changed blocks, or
    None when nothing clears the floor (box not computable)."""
    with Image.open(cur_path) as ci, Image.open(prev_path) as pi:
        cur = ci.convert("L")
        prev = pi.convert("L")
        if prev.size != cur.size:
            prev = prev.resize(cur.size, Image.Resampling.BILINEAR)
        # BOX-resampling the abs-difference image to the grid IS the
        # per-block mean-abs-diff
        blocks = ImageChops.difference(cur, prev).resize(
            (BLOCK_GRID, BLOCK_GRID), Image.Resampling.BOX
        )
        px = list(blocks.tobytes())  # mode L: one byte per block mean
        width, height = cur.size
    peak = max(px)
    if peak < BLOCK_ABS_FLOOR:
        return None
    thr = max(BLOCK_ABS_FLOOR, BLOCK_REL_FRAC * peak)
    rows, cols = [], []
    for k, v in enumerate(px):
        if v >= thr:
            rows.append(k // BLOCK_GRID)
            cols.append(k % BLOCK_GRID)
    if not rows:
        return None
    cell_w = width / BLOCK_GRID
    cell_h = height / BLOCK_GRID
    x0 = int(min(cols) * cell_w)
    y0 = int(min(rows) * cell_h)
    x1 = int((max(cols) + 1) * cell_w) - 1
    y1 = int((max(rows) + 1) * cell_h) - 1
    # inset so a full-frame box stays visible at the edges
    inset = BBOX_INSET
    return (
        max(x0, inset),
        max(y0, inset),
        min(x1, width - 1 - inset),
        min(y1, height - 1 - inset),
    )


def render_frame_copy(
    src: Path,
    dest: Path,
    chip_text: str,
    bbox: tuple[int, int, int, int] | None,
) -> None:
    """Overlaid copy: never mutates the original."""
    with Image.open(src) as img:
        out = img.convert("RGB")
    if bbox is not None:
        line = max(BOX_LINE_MIN_WIDTH, out.width // BOX_LINE_WIDTH_DIVISOR)
        ImageDraw.Draw(out).rectangle(list(bbox), outline=BOX_COLOR, width=line)
    draw_chip(out, chip_text)
    out.save(dest, "JPEG", quality=JPEG_QUALITY)


def render_grid(
    cell_sources: list[tuple[Path, str]], dest: Path
) -> None:
    """<= GRID_MAX_CELLS downscaled labeled cells; labels are drawn at native
    size on a bar UNDER each cell so downscaling never shrinks the text."""
    font = load_font(GRID_FONT_SIZE)
    cells = []
    for path, label in cell_sources:
        with Image.open(path) as img:
            scale = GRID_CELL_WIDTH / img.width
            cell = img.convert("RGB").resize(
                (GRID_CELL_WIDTH, max(1, int(img.height * scale))),
                Image.Resampling.LANCZOS,
            )
        cells.append((cell, label))
    cell_h = max(c.height for c, _ in cells)
    cols = min(GRID_MAX_COLS, len(cells))
    rows = math.ceil(len(cells) / cols)
    pad = GRID_PAD
    tile_h = cell_h + GRID_LABEL_HEIGHT
    canvas = Image.new(
        "RGB",
        (cols * GRID_CELL_WIDTH + (cols + 1) * pad, rows * tile_h + (rows + 1) * pad),
        (24, 24, 24),
    )
    draw = ImageDraw.Draw(canvas)
    for k, (cell, label) in enumerate(cells):
        r, c = divmod(k, cols)
        x = pad + c * (GRID_CELL_WIDTH + pad)
        y = pad + r * (tile_h + pad)
        canvas.paste(cell, (x, y))
        bar_y = y + cell.height
        draw.rectangle([x, bar_y, x + GRID_CELL_WIDTH, bar_y + GRID_LABEL_HEIGHT], fill=(0, 0, 0))
        draw.text((x + 6, bar_y + 4), label, fill=(255, 255, 255), font=font)
    canvas.save(dest, "JPEG", quality=GRID_JPEG_QUALITY)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="judge-motion frame pipeline: diff-spike selection + filmstrip"
    )
    ap.add_argument("transition_dir", help="captured transition dir (frames/ + signals.json)")
    ap.add_argument("--max-frames", type=int, default=MAX_SELECTED,
                    help="selection budget (default 9; the 5-9 contract)")
    ap.add_argument("--grid-cells", type=int, default=GRID_MAX_CELLS,
                    help="grid composite cells (default 6, max 6)")
    ap.add_argument("--out", default=None, help="output dir (default: the transition dir)")
    args = ap.parse_args(argv)
    if not (MIN_SELECTED <= args.max_frames <= MAX_SELECTED):
        fatal(
            "--max-frames must be " + str(MIN_SELECTED) + ".." + str(MAX_SELECTED)
            + " (got " + str(args.max_frames) + ").",
            "The 5-9 selection contract bounds the filmstrip: at least "
            + str(MIN_SELECTED) + " slots, at most " + str(MAX_SELECTED)
            + " (more dilutes the vision judge's attention).",
        )
    if not (1 <= args.grid_cells <= GRID_MAX_CELLS):
        fatal(
            "--grid-cells must be 1.." + str(GRID_MAX_CELLS)
            + " (got " + str(args.grid_cells) + ").",
            "The judge-protocol grid composite is capped at "
            + str(GRID_MAX_CELLS) + " cells (plan D4).",
        )
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    transition_dir = Path(args.transition_dir).resolve()
    if not transition_dir.is_dir():
        fatal(
            "Transition dir not found: " + str(transition_dir),
            "Pass a capture_motion.mjs output dir, e.g. "
            ".judge-motion/<run-id>/<transition>/.",
        )
    out_dir = Path(args.out).resolve() if args.out else transition_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    signals = load_signals(transition_dir)
    hold_ms = hold_frame_ms_set(signals)
    trigger_ms = signals.get("triggerOffsetMs")
    if not isinstance(trigger_ms, (int, float)):
        print(
            "[select] WARNING: signals.json triggerOffsetMs missing or "
            "malformed (" + repr(trigger_ms) + "); pre-trigger filtering "
            "DISABLED (trigger treated as 0ms - bring-up frames may enter "
            "the diff curve)."
        )
        trigger_ms = 0
    candidates, excluded, pre_excluded, before_frame = collect_candidates(
        transition_dir / "frames", hold_ms, int(trigger_ms)
    )
    if before_frame is None:
        print(
            "[select] WARNING: no pre-trigger frame exists; the before-anchor "
            "falls back to the first post-trigger frame, which may already "
            "show the transition (or a defect) in progress."
        )

    real_expected = signals.get("realFrameCount")
    if isinstance(real_expected, int) and real_expected - pre_excluded != len(candidates):
        print(
            "[select] WARNING: candidate count " + str(len(candidates))
            + " != signals.realFrameCount " + str(real_expected)
            + " minus " + str(pre_excluded) + " pre-trigger"
            + " (frames dir is the ground truth; proceeding)."
        )

    curve = compute_curve(candidates)
    if curve:
        spikes, stats = detect_spikes(curve)
    else:
        spikes, stats = [], {"spikeMask": []}
    spike_mask = stats.pop("spikeMask")
    selection, flat = select_frames_for(
        candidates, curve, spikes, args.max_frames,
        reserved_slots=1 if before_frame is not None else 0,
    )

    # filmstrip/ is fully derived from frames/ + this script; wipe stale jpgs
    # so a re-run never leaves a mixed old/new strip (run dirs themselves stay
    # append-only per SKILL.md - this only refreshes the derived stage).
    strip_dir = out_dir / "filmstrip"
    strip_dir.mkdir(parents=True, exist_ok=True)
    for stale in strip_dir.glob("*.jpg"):
        stale.unlink()

    ordered = sorted(selection.keys())
    curve_by_ci = {e["idx"]: e for e in curve}

    # Unified render list: the explicit before-anchor (last pre-trigger
    # frame) first, then curve-selected candidates in time order. The
    # before-anchor bypasses the diff curve entirely (no adjacent-pair
    # partner across the trigger boundary), so it carries no diff value and
    # never gets a spike bbox.
    render_entries: list[dict] = []
    if before_frame is not None:
        render_entries.append(
            {"ci": None, "elapsed": before_frame[0], "src": before_frame[1],
             "reason": "before"}
        )
    for ci in ordered:
        elapsed, src = candidates[ci]
        render_entries.append(
            {"ci": ci, "elapsed": elapsed, "src": src, "reason": selection[ci]}
        )

    selected_manifest = []
    for index, ent in enumerate(render_entries, start=1):
        ci, elapsed, src, reason = ent["ci"], ent["elapsed"], ent["src"], ent["reason"]
        curve_entry = curve_by_ci.get(ci) if ci is not None else None
        diff_val = curve_entry["diff"] if curve_entry else None
        # bbox only for frames that are above-threshold spike members
        # (curve entry idx ci maps to spike_mask position ci - 1)
        bbox = None
        if ci is not None and 1 <= ci and ci - 1 < len(spike_mask) and spike_mask[ci - 1]:
            bbox = block_diff_bbox(src, candidates[ci - 1][1])
        chip = "#" + str(index) + " +" + str(elapsed) + "ms " + reason
        dest_name = f"{index:02d}-{elapsed:07d}-{reason}.jpg"
        render_frame_copy(src, strip_dir / dest_name, chip, bbox)
        selected_manifest.append(
            {
                "file": "filmstrip/" + dest_name,
                "sourceFrame": "frames/" + src.name,
                "elapsedMs": elapsed,
                "index": index,
                "diff": diff_val,
                "reason": reason,
            }
        )

    # per-spike full-res sequential triplets (immediate neighbors of the peak)
    spikes_manifest = []
    for n, sp in enumerate(sorted(spikes, key=lambda s: s["peak_ci"]), start=1):
        triplet_files = []
        for slot, ci in (
            ("before", sp["peak_ci"] - 1),
            ("spike", sp["peak_ci"]),
            ("after", sp["peak_ci"] + 1),
        ):
            if not (0 <= ci < len(candidates)):
                continue  # spike at the sequence edge: skip the missing side
            elapsed, src = candidates[ci]
            bbox = None
            if slot == "spike" and ci >= 1:
                bbox = block_diff_bbox(src, candidates[ci - 1][1])
            dest_name = "triplet-" + str(n) + "-" + slot + ".jpg"
            render_frame_copy(
                src, strip_dir / dest_name,
                "T" + str(n) + " " + slot + " +" + str(elapsed) + "ms", bbox,
            )
            triplet_files.append("filmstrip/" + dest_name)
        spikes_manifest.append(
            {
                "index": n,
                "peakFrame": "frames/" + candidates[sp["peak_ci"]][1].name,
                "peakDiff": sp["peak_diff"],
                "startMs": candidates[sp["i0"]][0],
                "endMs": candidates[sp["i1"]][0],
                "tripletFiles": triplet_files,
            }
        )

    # grid composite: <= grid-cells cells, spike peaks first, then anchors
    # (positions index render_entries, so the before-anchor competes as the
    # first anchor and appears whenever the cell budget allows)
    pos_by_ci = {e["ci"]: k for k, e in enumerate(render_entries) if e["ci"] is not None}
    n_entries = len(render_entries)
    if n_entries <= args.grid_cells:
        grid_positions = list(range(n_entries))
    else:
        keep: list[int] = []
        for sp in sorted(spikes, key=lambda s: (s["peak_diff"], s["peak_mse"]), reverse=True):
            pos = pos_by_ci.get(sp["peak_ci"])
            if pos is not None and pos not in keep:
                keep.append(pos)
            if len(keep) >= args.grid_cells:
                break
        for anchor in (0, n_entries - 1):  # before-anchor + settled end state
            if len(keep) < args.grid_cells and anchor not in keep:
                keep.append(anchor)
        for pos in range(n_entries):
            if len(keep) >= args.grid_cells:
                break
            if pos not in keep:
                keep.append(pos)
        grid_positions = sorted(keep)
    cell_sources = []
    for pos in grid_positions:
        ent = render_entries[pos]
        index = pos + 1
        dest_name = f"{index:02d}-{ent['elapsed']:07d}-{ent['reason']}.jpg"
        label = "#" + str(index) + " +" + str(ent["elapsed"]) + "ms " + ent["reason"]
        cell_sources.append((strip_dir / dest_name, label))
    render_grid(cell_sources, strip_dir / "grid.jpg")

    diffs = [e["diff"] for e in curve]
    manifest = {
        "transition": signals.get("transition", transition_dir.name),
        "selected": selected_manifest,
        "spikes": spikes_manifest,
        "diffCurve": [
            {"frame": e["frame"], "elapsedMs": e["elapsedMs"], "diff": e["diff"], "mse": e["mse"]}
            for e in curve
        ],
        "excludedHoldFrames": excluded,
        "params": {
            "maxFrames": args.max_frames,
            "gridCells": args.grid_cells,
            "reasonVocabulary": REASON_VOCABULARY,
            "spikeK": SPIKE_K,
            "phashHashSize": PHASH_HASH_SIZE,
            "phashMinSpikeDelta": PHASH_MIN_SPIKE_DELTA,
            "mseMinSpikeDelta": MSE_MIN_SPIKE_DELTA,
            "flatMaximaMinDelta": FLAT_MAXIMA_MIN_DELTA,
            "blockGrid": BLOCK_GRID,
            "blockAbsFloor": BLOCK_ABS_FLOOR,
            "blockRelFrac": BLOCK_REL_FRAC,
            "flatCurve": flat,
            "candidateCount": len(candidates),
            "triggerOffsetMs": int(trigger_ms),
            "excludedPreTriggerFrames": pre_excluded,
            **stats,
        },
    }
    manifest_path = out_dir / "filmstrip.json"
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")

    curve_max = max(diffs) if diffs else 0
    curve_mean = round(sum(diffs) / len(diffs), 3) if diffs else 0.0
    print(
        "[select] " + manifest["transition"] + ": "
        + str(len(candidates)) + " candidates (" + str(excluded) + " hold + "
        + str(pre_excluded) + " pre-trigger excluded), "
        + "curve max/mean " + str(curve_max) + "/" + str(curve_mean) + ", "
        + ("flat curve" if flat else str(len(spikes)) + " spike(s)") + ", "
        + "selected " + str(len(render_entries))
        + (" (incl. explicit before-anchor)" if before_frame is not None else "")
        + " -> " + str(strip_dir)
    )
    print("[select] manifest: " + str(manifest_path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
