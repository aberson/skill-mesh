# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""gate_signals.py - judge-motion Step 5 mechanical pre-gate evaluator.

Input: one captured transition dir (from capture_motion.mjs + select_frames.py)
containing signals.json (required), meta.json (rubric source; optional if
--rubric is given), filmstrip.json (optional; supplementary evidence only).

Evaluates the deterministic defect classes BEFORE any vision spend:

    cls               layout instability during the transition
    focus-retained    focus dropped to <body>/<html> after the transition
    scroll-restored   scroll position lost across a route change
    spinner-timing    loading-indicator flash / missing delay-before-show
    duration-in-range measured duration (normalized to real time by
                      playbackRate) vs the rubric's expectedDurationMs

Output (default: gates.json into the transition dir, or --out): per-gate
verdict PASS|FAIL|SKIP with threshold + observed + evidence, a summary whose
verdict is "FAIL-mechanical" on any gate FAIL (the vision judge is then
skipped for this transition, per SKILL.md run-loop stage 5), and an echo of
the effective thresholds.

GATE-THRESHOLD SINGLE SOURCE OF TRUTH: every gate threshold lives in the
constants block below and nowhere else - SKILL.md and fixtures/README.md
point here rather than restating gate values. (The fixture files' own
behavior constants - each fixture's T = {...} timing block - are
legitimately described in the fixture docs; the rationale comments below
cite that observed fixture behavior without making the fixture docs a
threshold source.)

Exit code reflects TOOL health, not gate verdicts: a completed evaluation
exits 0 even when the summary is FAIL-mechanical; malformed/missing inputs
exit 1 via fatal() with a remedy.

Usage:
    uv run scripts/gate_signals.py <transition-dir> [--out <path>]
                                   [--rubric <inline-json-or-path>]

--rubric fully replaces the rubric read from meta.json (testing hook). A
missing/incomplete rubric never crashes: rubric-dependent checks SKIP with a
reason (the rubric is REQUIRED upstream by the flow-spec contract; refusing
to judge a rubric-less transition is the orchestrator's job, not this
script's).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

# --------------------------------------------------------------------------
# Gate thresholds - THE single source of truth (SKILL.md never restates
# these). Each constant carries its rationale.
# --------------------------------------------------------------------------

CLS_MAX = 0.001
# Maximum accumulated layout-instability score for a single judged
# transition. Core-Web-Vitals' 0.1 "good" budget is a whole-page-lifetime
# budget; ONE sub-second transition should contribute ~zero. The frozen
# fixtures bear this out: smooth.html measures exactly 0 in every real-time
# run, while janky.html's injected shift measures ~0.0187-0.12 depending on
# viewport (fixtures/README.md) - i.e. a real defect can sit far below the
# page-level 0.1. 0.001 is a float-dust epsilon above zero, not a comfort
# margin.

SCROLL_DELTA_MAX_PX = 4
# Max |scrollYAfter - scrollYBefore| in CSS px before scroll restoration is
# considered lost. Sub-pixel rounding and scrollbar re-layout can wobble a
# couple of px on an intact restoration; a genuinely lost position jumps by
# tens-to-hundreds of px (typically resets to 0).

SPINNER_MIN_DISPLAY_MS = 500.0
# A loading indicator visible for less than this reads as a flash (classic
# perceived-performance guidance; the smooth fixture's skeleton, once shown,
# is held >= 500ms by design). Loading-selector timings are JS-timer-driven
# REAL-time milliseconds - they do NOT dilate under slow-mo capture
# (fixtures/README.md "Slow-mo capture asymmetry") - so no playbackRate
# normalization applies to this gate.

SPINNER_DELAY_BEFORE_SHOW_MS = 300.0
# An indicator appearing before this much real time has elapsed punishes
# fast loads with a needless flash; the standard pattern (and the smooth
# fixture) shows a loading state only once the wait exceeds ~300ms. A cycle
# whose showAtMs is below this is a no-delay-before-show defect.

FOCUS_SINK_TAGS = frozenset({"BODY", "HTML"})
# Tags that mean "focus is on nothing". The collector samples focusBefore
# BEFORE the trigger click, and the click itself focuses the trigger
# element - so focusAfter landing on a sink always means focus was dropped
# mid-transition (outgoing DOM unmounted with focus inside it), regardless
# of what the pre-trigger sample read. This is why BODY->BODY still FAILs.

FOCUS_INTENT_SKIP_VALUES = frozenset({"unmanaged", "none", "none-expected"})
# A rubric may declare focusIntent with one of these values to opt a
# transition out of focus management entirely (e.g. a pure hover animation
# where no focus move is expected); the gate then SKIPs instead of judging.

INTENT_TOLERANCE_CONNECTIVE_RE = re.compile(
    r"\b(?:if|unless|only|except|provided)\b"
    r"|must\s+respect|\btolerated\b|\ballowed\b|\bok\s+if\b",
    re.IGNORECASE,
)
# Connectives that make a negative-sounding loadingStateIntent CONDITIONAL
# ("no spinner for an instant load; any spinner shown must respect ...",
# "skeleton only if the load exceeds ..."). If any of these appears
# anywhere in the intent text, observed cycles are tolerated (the
# per-cycle timing checks still apply) - only an UNCONDITIONAL negation
# may classify as none-expected. Checked BEFORE the negation patterns.

INTENT_NONE_EXPECTED_RE = re.compile(
    r"(?:\bnone\s+expected\b)"
    r"|(?:\bnever\s+(?:be\s+)?(?:shown?|appears?|displays?|displayed)\w*)"
    r"|(?:\b(?:must|should|do)\s+not\s+(?:be\s+)?(?:show|appear|display)\w*)"
    r"|(?:\b(?:no|without)\s+(?:\w+\s+){0,3}?"
    r"(?:spinner|skeleton|loading|loader|indicator)s?\b)"
    r"|(?:\b(?:spinner|skeleton|loading|loader|indicator)-free\b)",
    re.IGNORECASE | re.DOTALL,
)
# Deterministic classifier for the rubric's free-text loadingStateIntent.
# UNCONDITIONAL-negation phrasings ("none expected", "spinners must never
# appear", "do not show a spinner") -> mode "none-expected": ANY observed
# cycle is an intent violation on top of the per-cycle timing checks - but
# ONLY when no tolerance connective (above) appears anywhere in the text.
# A BARE indicator negation with no verb ("no spinner, period",
# "without a spinner", "spinner-free") counts: zero-tolerance rubrics are
# often terse, and falling back to the permissive mode would let a
# timing-compliant cycle PASS under them. Anything else (or a missing
# intent) -> mode "cycles-tolerated": cycles pass iff they respect both
# timing thresholds.

GATE_ORDER = (
    "cls",
    "focus-retained",
    "scroll-restored",
    "spinner-timing",
    "duration-in-range",
)
# Fixed evaluation/report order, matching SKILL.md's run-loop stage 5
# listing (CLS, focus retention, scroll restoration, spinner timing,
# duration-in-range). gates.json (and the console echo) always emit in this
# stable order so downstream consumers and diffs can rely on position;
# evaluate() asserts against this tuple to catch accidental reordering.

EFFECTIVE_THRESHOLDS: dict[str, Any] = {
    "clsMax": CLS_MAX,
    "scrollDeltaMaxPx": SCROLL_DELTA_MAX_PX,
    "spinnerMinDisplayMs": SPINNER_MIN_DISPLAY_MS,
    "spinnerDelayBeforeShowMs": SPINNER_DELAY_BEFORE_SHOW_MS,
    "focusSinkTags": sorted(FOCUS_SINK_TAGS),
    "focusIntentSkipValues": sorted(FOCUS_INTENT_SKIP_VALUES),
}


def fatal(message: str, remedy: str | None = None) -> NoReturn:
    print("FATAL: " + message, file=sys.stderr)
    if remedy:
        print("Remedy: " + remedy, file=sys.stderr)
    sys.exit(1)


def load_json_file(path: Path, what: str, required: bool) -> dict | None:
    if not path.is_file():
        if required:
            fatal(
                what + " not found at " + str(path),
                "point this script at a captured transition dir "
                "(capture_motion.mjs writes signals.json + meta.json; "
                "select_frames.py writes filmstrip.json)",
            )
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        fatal(
            what + " at " + str(path) + " is unreadable/malformed: " + str(exc),
            "re-run the capture/frame pipeline for this transition; "
            "do not hand-edit run artifacts",
        )
    if not isinstance(data, dict):
        fatal(
            what + " at " + str(path) + " is not a JSON object "
            "(got " + type(data).__name__ + ")",
            "re-run the capture/frame pipeline for this transition",
        )
    return data


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def as_dict(value: Any, what: str) -> dict:
    """value as a dict; None/absent -> {}. A present-but-not-an-object run
    artifact is corrupt: fatal() with a remedy, never a bare traceback."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        fatal(
            what + " must be a JSON object, got " + type(value).__name__,
            "re-run the capture/frame pipeline for this transition; "
            "do not hand-edit run artifacts",
        )
    return value


def as_list(value: Any, what: str) -> list:
    """value as a list; None/absent -> []. A present-but-not-a-list run
    artifact is corrupt: fatal() with a remedy, never a bare traceback."""
    if value is None:
        return []
    if not isinstance(value, list):
        fatal(
            what + " must be a JSON array, got " + type(value).__name__,
            "re-run the capture/frame pipeline for this transition; "
            "do not hand-edit run artifacts",
        )
    return value


def gate_result(
    name: str,
    verdict: str,
    threshold: Any,
    observed: dict[str, Any],
    evidence: list[str],
) -> dict[str, Any]:
    return {
        "name": name,
        "verdict": verdict,
        "threshold": threshold,
        "observed": observed,
        "evidence": evidence,
    }


def missing_signal_fail(
    name: str, threshold: Any, field: str, value: Any
) -> dict[str, Any]:
    # A gate must never read PASS off a missing/invalid signal
    # (measurement-validity: an instrument that cannot see must fail loud,
    # not silently pass).
    return gate_result(
        name,
        "FAIL",
        threshold,
        {field: value},
        [
            "signal '" + field + "' is missing or invalid "
            "(got " + repr(value) + ") - cannot verify; failing loud, "
            "a missing signal must never read as PASS"
        ],
    )


# --------------------------------------------------------------------------
# Gates
# --------------------------------------------------------------------------


def gate_cls(signals: dict) -> dict[str, Any]:
    """Layout-instability gate: accumulated cls score vs CLS_MAX;
    input-excluded (hadRecentInput=true) entries surface as evidence only,
    never gated."""
    cls = signals.get("cls")
    entries = as_list(
        signals.get("layoutShiftEntries"), "signals.json layoutShiftEntries"
    )
    input_excluded = as_list(
        signals.get("layoutShiftEntriesInputExcluded"),
        "signals.json layoutShiftEntriesInputExcluded",
    )
    caveat = (
        str(len(input_excluded)) + " input-excluded layout-shift entr"
        + ("y" if len(input_excluded) == 1 else "ies")
        + " (hadRecentInput=true, not counted toward cls - the clsNote "
        "caveat); surfaced as evidence only, not gated"
    )
    if not is_number(cls):
        result = missing_signal_fail("cls", CLS_MAX, "cls", cls)
        result["evidence"].append(caveat)
        return result
    observed = {
        "cls": cls,
        "layoutShiftEntryCount": len(entries),
        "layoutShiftEntriesInputExcludedCount": len(input_excluded),
    }
    if cls > CLS_MAX:
        evidence = [
            "cls " + str(cls) + " > threshold " + str(CLS_MAX) + " with "
            + str(len(entries)) + " counted layout-shift entr"
            + ("y" if len(entries) == 1 else "ies")
        ]
        for ent in entries:
            if isinstance(ent, dict):
                evidence.append(
                    "shift value " + str(ent.get("value"))
                    + " at " + str(ent.get("afterTriggerMs"))
                    + "ms after trigger"
                )
        evidence.append(caveat)
        return gate_result("cls", "FAIL", CLS_MAX, observed, evidence)
    return gate_result(
        "cls",
        "PASS",
        CLS_MAX,
        observed,
        ["cls " + str(cls) + " <= threshold " + str(CLS_MAX), caveat],
    )


def focus_tag(value: str) -> str:
    # Collector reports e.g. "H1#detail-title", "BUTTON#nav-to-detail",
    # or bare "BODY".
    return value.split("#", 1)[0].strip().upper()


def gate_focus(signals: dict, rubric: dict) -> dict[str, Any]:
    """Focus-retention gate: FAIL when focusAfter lands on a sink tag
    (BODY/HTML); a rubric focusIntent of unmanaged/none opts the
    transition out of focus management entirely -> SKIP."""
    name = "focus-retained"
    threshold = "focusAfter not in " + "/".join(sorted(FOCUS_SINK_TAGS))
    intent = rubric.get("focusIntent")
    if isinstance(intent, str) and intent.strip().lower() in FOCUS_INTENT_SKIP_VALUES:
        return gate_result(
            name,
            "SKIP",
            threshold,
            {"focusIntent": intent},
            [
                "rubric focusIntent '" + intent + "' opts this transition "
                "out of focus management - gate skipped"
            ],
        )
    before = signals.get("focusBefore")
    after = signals.get("focusAfter")
    if not isinstance(after, str) or not after.strip():
        return missing_signal_fail(name, threshold, "focusAfter", after)
    observed = {"focusBefore": before, "focusAfter": after}
    if focus_tag(after) in FOCUS_SINK_TAGS:
        if isinstance(before, str) and before.strip() and focus_tag(before) not in FOCUS_SINK_TAGS:
            detail = (
                "focus dropped from '" + before + "' to '" + after + "'"
            )
        else:
            detail = (
                "focus never landed on a real element (focusBefore '"
                + str(before) + "', focusAfter '" + after + "'); the "
                "trigger click focuses the trigger element, so ending on a "
                "sink means focus was dropped when the outgoing DOM "
                "unmounted"
            )
        return gate_result(
            name,
            "FAIL",
            threshold,
            observed,
            [
                detail + " - dropped-to-body defect",
                "if the design intends no focus management for this "
                "transition (e.g. a no-click live update, or a "
                "non-focusable trigger element), declare rubric focusIntent "
                "'unmanaged'/'none' to waive this gate (it then SKIPs "
                "instead of failing)",
            ],
        )
    return gate_result(
        name,
        "PASS",
        threshold,
        observed,
        [
            "focusAfter '" + after + "' is a real element "
            "(focusBefore '" + str(before) + "')"
        ],
    )


def gate_scroll(signals: dict) -> dict[str, Any]:
    """Scroll-restoration gate: |scrollYAfter - scrollYBefore| must stay
    within SCROLL_DELTA_MAX_PX (sub-pixel wobble is fine; a lost position
    jumps by tens-to-hundreds of px)."""
    name = "scroll-restored"
    before = signals.get("scrollYBefore")
    after = signals.get("scrollYAfter")
    if not is_number(before):
        return missing_signal_fail(name, SCROLL_DELTA_MAX_PX, "scrollYBefore", before)
    if not is_number(after):
        return missing_signal_fail(name, SCROLL_DELTA_MAX_PX, "scrollYAfter", after)
    delta = abs(after - before)
    observed = {
        "scrollYBefore": before,
        "scrollYAfter": after,
        "deltaPx": delta,
    }
    if delta > SCROLL_DELTA_MAX_PX:
        return gate_result(
            name,
            "FAIL",
            SCROLL_DELTA_MAX_PX,
            observed,
            [
                "scrollY moved from " + str(before) + " to " + str(after)
                + " (delta " + str(delta) + "px > " + str(SCROLL_DELTA_MAX_PX)
                + "px) - scroll position not restored across the transition"
            ],
        )
    return gate_result(
        name,
        "PASS",
        SCROLL_DELTA_MAX_PX,
        observed,
        [
            "scrollY " + str(before) + " -> " + str(after) + " (delta "
            + str(delta) + "px <= " + str(SCROLL_DELTA_MAX_PX) + "px)"
        ],
    )


def classify_loading_intent(intent: Any) -> tuple[str, str]:
    """(mode, evidence-note) for the rubric's free-text loadingStateIntent.

    'none-expected' requires an UNCONDITIONAL negation ("none expected",
    "spinners must never appear", "do not show a spinner") with no
    tolerance connective anywhere in the text; conditional phrasings
    ("no spinner for an instant load; any spinner shown must respect ...")
    classify 'cycles-tolerated' - the per-cycle timing checks still apply.
    The note quotes the classified mode AND the phrase that decided it."""
    if not isinstance(intent, str) or not intent.strip():
        return (
            "cycles-tolerated",
            "no loadingStateIntent in rubric - defaulting to "
            "cycles-tolerated (compliant cycles pass)",
        )
    connective = INTENT_TOLERANCE_CONNECTIVE_RE.search(intent)
    if connective:
        return (
            "cycles-tolerated",
            "loadingStateIntent classified 'cycles-tolerated' (tolerance "
            "connective '" + connective.group(0) + "' makes the intent "
            "conditional) - cycles pass iff compliant with both timing "
            "thresholds",
        )
    match = INTENT_NONE_EXPECTED_RE.search(intent)
    if match:
        return (
            "none-expected",
            "loadingStateIntent classified 'none-expected' (unconditional "
            "negation '" + match.group(0).strip() + "') - ANY observed "
            "cycle is an intent violation",
        )
    return (
        "cycles-tolerated",
        "loadingStateIntent classified 'cycles-tolerated' (no "
        "unconditional-negation phrase matched) - cycles pass iff "
        "compliant with both timing thresholds",
    )


def gate_spinner(signals: dict, rubric: dict) -> dict[str, Any]:
    """Loading-indicator gate: classifies the rubric's loadingStateIntent,
    then checks each observed show/hide cycle for delay-before-show and
    min-display compliance. The collector's already-visible-at-install
    shape (showAtMs null + hideAtMs number) is measurable-in-part, not
    malformed: its unknowable checks skip with a note instead of failing."""
    name = "spinner-timing"
    threshold = {
        "minDisplayMs": SPINNER_MIN_DISPLAY_MS,
        "delayBeforeShowMs": SPINNER_DELAY_BEFORE_SHOW_MS,
    }
    timings = signals.get("loadingSelectorTimings")
    if not isinstance(timings, dict) or not timings:
        return gate_result(
            name,
            "SKIP",
            threshold,
            {"loadingSelectorTimings": timings},
            [
                "no loading selectors instrumented in this capture - "
                "nothing to evaluate (declare the transition's loading "
                "selector(s) in the flow spec to enable this gate)"
            ],
        )
    mode, mode_note = classify_loading_intent(rubric.get("loadingStateIntent"))
    evidence: list[str] = [mode_note]
    violations: list[str] = []
    observed_cycles: list[dict[str, Any]] = []
    for selector, timing in timings.items():
        if not isinstance(timing, dict):
            violations.append(
                "selector '" + str(selector) + "' timing entry is malformed "
                "(got " + type(timing).__name__ + ") - failing loud"
            )
            continue
        if timing.get("wasVisibleAtInstall") is True:
            evidence.append(
                "selector '" + str(selector) + "' was already visible when "
                "the collector installed (wasVisibleAtInstall=true) - its "
                "first cycle's showAtMs may understate how early it appeared"
            )
        cycles = timing.get("cycles")
        if cycles is None:
            cycles = []
        elif not isinstance(cycles, list):
            violations.append(
                "selector '" + str(selector) + "' cycles field is "
                "malformed (got " + type(cycles).__name__
                + ") - failing loud"
            )
            continue
        for idx, cycle in enumerate(cycles, start=1):
            if not isinstance(cycle, dict):
                violations.append(
                    "selector '" + str(selector) + "' cycle " + str(idx)
                    + " is malformed - failing loud"
                )
                continue
            show_at = cycle.get("showAtMs")
            hide_at = cycle.get("hideAtMs")
            visible_for = cycle.get("visibleForMs")
            observed_cycles.append(
                {
                    "selector": selector,
                    "cycle": idx,
                    "showAtMs": show_at,
                    "hideAtMs": hide_at,
                    "visibleForMs": visible_for,
                }
            )
            label = "selector '" + str(selector) + "' cycle " + str(idx)
            if mode == "none-expected":
                violations.append(
                    "intent-violation: " + label + " observed (showAtMs "
                    + str(show_at) + ", visibleForMs " + str(visible_for)
                    + ") where loadingStateIntent expects none"
                )
            if not is_number(show_at) and is_number(hide_at):
                # Collector's DOCUMENTED already-visible shape: the
                # selector was visible when the watcher installed and hid
                # post-trigger. Not malformed, not a violation by itself.
                evidence.append(
                    label + " was already visible at watcher install "
                    "(showAtMs null, hideAtMs " + str(hide_at) + "ms): "
                    "start time predates observation - unknowable, so the "
                    "delay-before-show check is skipped and the "
                    "min-display check is not applicable (visibleForMs "
                    "unknowable); not a violation by itself"
                )
                continue
            if not is_number(show_at):
                # Genuinely malformed: neither endpoint is usable.
                violations.append(
                    label + " has missing/invalid showAtMs AND hideAtMs ("
                    + repr(show_at) + ", " + repr(hide_at)
                    + ") - failing loud"
                )
                continue
            if is_number(visible_for):
                if visible_for < SPINNER_MIN_DISPLAY_MS:
                    violations.append(
                        "spinner-flash: " + label + " visible for "
                        + str(visible_for) + "ms < min-display "
                        + str(SPINNER_MIN_DISPLAY_MS) + "ms"
                    )
            elif is_number(hide_at):
                evidence.append(
                    label + " closed (hideAtMs " + str(hide_at) + "ms) but "
                    "visibleForMs is missing/invalid (" + repr(visible_for)
                    + ") - min-display check not applicable"
                )
            else:
                evidence.append(
                    label + " is unclosed at capture end (hideAtMs null) - "
                    "min-display check not applicable"
                )
            if show_at < SPINNER_DELAY_BEFORE_SHOW_MS:
                violations.append(
                    "no-delay-before-show: " + label + " appeared at "
                    + str(show_at) + "ms < delay-before-show "
                    + str(SPINNER_DELAY_BEFORE_SHOW_MS) + "ms"
                )
    observed = {"intentMode": mode, "cycles": observed_cycles}
    if violations:
        return gate_result(
            name, "FAIL", threshold, observed, violations + evidence
        )
    evidence.append(
        str(len(observed_cycles)) + " cycle(s) observed, all compliant"
        if observed_cycles
        else "0 loading cycles observed"
    )
    return gate_result(name, "PASS", threshold, observed, evidence)


def gate_duration(
    signals: dict, rubric: dict, filmstrip: dict | None
) -> dict[str, Any]:
    """Duration gate: PASS iff EITHER the playbackRate-normalized reading
    OR the raw wall-clock reading falls inside the rubric's
    expectedDurationMs range; FAIL only when BOTH are out of range.

    Normalization (measured * playbackRate) is only valid for content that
    dilates under slow-mo (CSS/WAAPI); timer-driven content stays
    real-time (fixtures/README.md 'Slow-mo capture asymmetry'), so its
    honest reading is the raw wall-clock one - trusting normalization
    alone would false-FAIL compliant timer-driven transitions."""
    name = "duration-in-range"
    rng = rubric.get("expectedDurationMs")
    valid_range = (
        isinstance(rng, (list, tuple))
        and len(rng) == 2
        and is_number(rng[0])
        and is_number(rng[1])
        and rng[0] <= rng[1]
    )
    measured = signals.get("measuredDurationMs")
    rate = signals.get("playbackRate")
    if not valid_range:
        return gate_result(
            name,
            "SKIP",
            None,
            {
                "expectedDurationMs": rng,
                "measuredDurationMs": measured,
                "playbackRate": rate,
            },
            [
                "rubric expectedDurationMs is missing or invalid ("
                + repr(rng) + ") - the motion rubric is REQUIRED upstream "
                "by the flow-spec contract; skipping gracefully here (the "
                "spec-error refusal is the orchestrator's job)"
            ],
        )
    threshold = [rng[0], rng[1]]
    if not is_number(measured):
        return missing_signal_fail(
            name, threshold, "measuredDurationMs", measured
        )
    if not is_number(rate) or rate <= 0:
        result = missing_signal_fail(name, threshold, "playbackRate", rate)
        result["observed"]["measuredDurationMs"] = measured
        result["evidence"].append(
            "cannot normalize wall-clock duration to real-content time "
            "without a positive playbackRate"
        )
        return result
    normalized = round(measured * rate, 3)
    lo, hi = threshold
    norm_in = lo <= normalized <= hi
    raw_in = lo <= measured <= hi
    observed = {
        "measuredDurationMs": measured,
        "playbackRate": rate,
        "normalizedDurationMs": normalized,
        "rawInRange": raw_in,
        "normalizedInRange": norm_in,
    }

    def reading_direction(value: float) -> str:
        if value < lo:
            return "below the rubric minimum"
        if value > hi:
            return "above the rubric maximum"
        return "within the rubric range"

    range_str = " (expected " + str(lo) + "-" + str(hi) + "ms)"
    raw_line = (
        "raw measured " + str(measured) + "ms is "
        + reading_direction(measured) + range_str
        + " - direct wall-clock reading, no dilation assumption "
        "(timer-driven content does not dilate under slow-mo)"
    )
    norm_line = (
        "normalized " + str(normalized) + "ms is "
        + reading_direction(normalized) + range_str
        + " - measured " + str(measured) + "ms x playbackRate " + str(rate)
        + "; valid only for content that dilates under slow-mo (CSS/WAAPI)"
    )
    strip_note = None
    if filmstrip is not None:
        spikes = filmstrip.get("spikes")
        params = as_dict(filmstrip.get("params"), "filmstrip.json params")
        if isinstance(spikes, list):
            strip_note = (
                "filmstrip: " + str(len(spikes)) + " diff spike(s), "
                "flatCurve=" + str(params.get("flatCurve"))
            )
    if not norm_in and not raw_in:
        # Both interpretations are out of range - the raw wall-clock
        # reading is the primary (assumption-free) evidence line.
        evidence = [raw_line, norm_line]
        if normalized < lo and rate < 1:
            evidence.append(
                "content that fails to dilate under slow-mo (JS-timer-"
                "driven motion) reads shorter than real after "
                "normalization - itself a defect signature (stepped/"
                "setTimeout animation instead of a CSS transition)"
            )
        if strip_note:
            evidence.append(strip_note)
        return gate_result(name, "FAIL", threshold, observed, evidence)
    if norm_in:
        evidence = [norm_line, raw_line]
    else:
        evidence = [
            raw_line,
            norm_line + " - out of range while raw is in range: the "
            "content did not dilate (timer-driven), so the raw wall-clock "
            "reading is the honest one",
        ]
    if strip_note:
        evidence.append(strip_note)
    return gate_result(name, "PASS", threshold, observed, evidence)


# --------------------------------------------------------------------------
# Evaluation + CLI
# --------------------------------------------------------------------------


def resolve_rubric(
    meta: dict | None, rubric_override: dict | None
) -> tuple[dict, str]:
    """(rubric, source): a --rubric override wins outright; else meta.json's
    spec.transition.rubric; else ({}, 'absent'). A malformed nested shape
    (non-object spec/transition/rubric) is corrupt input -> fatal() with a
    remedy, never a bare traceback."""
    if rubric_override is not None:
        return rubric_override, "--rubric override"
    if meta is not None:
        spec = as_dict(meta.get("spec"), "meta.json spec")
        transition = as_dict(
            spec.get("transition"), "meta.json spec.transition"
        )
        raw_rubric = transition.get("rubric")
        if raw_rubric is not None:
            return (
                as_dict(raw_rubric, "meta.json spec.transition.rubric"),
                "meta.json",
            )
    return {}, "absent"


def evaluate(
    transition_dir: Path, rubric_override: dict | None = None
) -> dict[str, Any]:
    """Load one transition dir's artifacts, run every gate in GATE_ORDER,
    and return the full gates.json payload (per-gate verdicts + evidence,
    summary with FAIL-mechanical short-circuit signal, threshold echo)."""
    signals = load_json_file(
        transition_dir / "signals.json", "signals.json", required=True
    )
    assert signals is not None  # fatal() exits otherwise
    meta = load_json_file(
        transition_dir / "meta.json", "meta.json", required=False
    )
    filmstrip = load_json_file(
        transition_dir / "filmstrip.json", "filmstrip.json", required=False
    )
    rubric, rubric_source = resolve_rubric(meta, rubric_override)

    gates = [
        gate_cls(signals),
        gate_focus(signals, rubric),
        gate_scroll(signals),
        gate_spinner(signals, rubric),
        gate_duration(signals, rubric, filmstrip),
    ]
    assert tuple(g["name"] for g in gates) == GATE_ORDER

    fail_count = sum(1 for g in gates if g["verdict"] == "FAIL")
    pass_count = sum(1 for g in gates if g["verdict"] == "PASS")
    skip_count = sum(1 for g in gates if g["verdict"] == "SKIP")

    notes: list[str] = []
    if meta is None:
        notes.append("meta.json missing - rubric source fell back to "
                     + rubric_source)
    if filmstrip is None:
        notes.append("filmstrip.json missing - no diff-curve evidence "
                     "attached")
    warnings = signals.get("collectorWarnings")
    if isinstance(warnings, list) and warnings:
        notes.extend("collectorWarning: " + str(w) for w in warnings)

    return {
        "transition": signals.get("transition", transition_dir.name),
        "evaluatedAtUtc": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "rubric": rubric,
        "rubricSource": rubric_source,
        "collectorScope": signals.get("collectorScope"),
        "notes": notes,
        "gates": gates,
        "summary": {
            "failCount": fail_count,
            "passCount": pass_count,
            "skipCount": skip_count,
            "verdict": "FAIL-mechanical" if fail_count > 0 else "PASS",
        },
        "thresholds": EFFECTIVE_THRESHOLDS,
    }


def parse_rubric_arg(raw: str) -> dict:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        path = Path(raw)
        if not path.is_file():
            fatal(
                "--rubric value is neither valid inline JSON nor an "
                "existing file: " + raw,
                "pass a JSON object ('{\"expectedDurationMs\": [250, "
                "900]}') or a path to a JSON file",
            )
        parsed = load_json_file(path, "--rubric file", required=True)
    if not isinstance(parsed, dict):
        fatal(
            "--rubric must be a JSON object, got "
            + type(parsed).__name__,
            "pass the transition's rubric object (expectedDurationMs, "
            "easing, loadingStateIntent, ...)",
        )
    return parsed


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="judge-motion mechanical pre-gate evaluator "
        "(signals.json + rubric -> gates.json)",
    )
    ap.add_argument(
        "transition_dir",
        type=Path,
        help="captured transition dir (contains signals.json etc.)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output path for gates.json "
        "(default: <transition-dir>/gates.json)",
    )
    ap.add_argument(
        "--rubric",
        type=str,
        default=None,
        help="inline JSON object or path to a JSON file; fully replaces "
        "the rubric read from meta.json (testing hook)",
    )
    return ap.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    transition_dir: Path = args.transition_dir
    if not transition_dir.is_dir():
        fatal(
            "transition dir not found: " + str(transition_dir),
            "point at one captured transition dir, e.g. "
            ".judge-motion/<run-id>/<transition>/",
        )
    rubric_override = (
        parse_rubric_arg(args.rubric) if args.rubric is not None else None
    )
    payload = evaluate(transition_dir, rubric_override)

    out_path: Path = args.out if args.out else transition_dir / "gates.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")

    for g in payload["gates"]:
        print(
            "[gates] " + g["name"] + ": " + g["verdict"]
            + " - " + g["evidence"][0]
        )
    summary = payload["summary"]
    print(
        "[gates] " + payload["transition"] + ": "
        + str(summary["passCount"]) + " PASS / "
        + str(summary["failCount"]) + " FAIL / "
        + str(summary["skipCount"]) + " SKIP -> " + summary["verdict"]
    )
    print("[gates] wrote " + str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
