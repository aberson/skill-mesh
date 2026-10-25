/**
 * capture_motion.mjs - judge-motion Step 3 capture harness.
 *
 * Captures a slow-motion Playwright screencast of each UI transition in a
 * flow spec, with in-page signal collectors injected before the trigger.
 * Writes, per transition:
 *
 *   <out>/<run-id>/<transition>/frames/<elapsed-ms-padded>.jpg
 *   <out>/<run-id>/<transition>/signals.json
 *   <out>/<run-id>/<transition>/meta.json
 *
 * <run-id> = YYYYMMDD-HHMMSS-<flow-slug> (UTC), per SKILL.md's run-artifact
 * contract. Frame filenames are elapsed ms since screencast start (7-digit
 * zero-padded); signals.json carries triggerOffsetMs so downstream scripts
 * (select_frames.py, Step 4) can align frames to the trigger without reading
 * this script. The screencast starts BEFORE navigation (load render + the
 * settled "before" baseline are real capture content), and a static-screen
 * keepalive re-writes the last frame during damage-free spans (see
 * makeFrameSink; hold frames are listed in signals.json holdFrames).
 *
 * Navigation-triggered transitions (real <a href> / MPA routes) are
 * first-class: collectors are installed on EVERY document via
 * context.addInitScript, and signals.json carries
 * collectorScope: "same-document" | "post-navigation" (post-navigation
 * signals cover the new document only - baselines reset with it).
 *
 * Per-transition failure isolation: one transition's failure writes
 * <transition>/error.json and the run continues to the next transition;
 * the process exits nonzero at the end if any transition failed.
 *
 * Usage:
 *   node scripts/capture_motion.mjs --spec <flow-spec.json>
 *       [--out <dir>]                 default: .judge-motion/ under cwd
 *       [--playback-rate <r>]         default: 0.1 (CDP Animation.setPlaybackRate)
 *       [--context-mode default|reduced-motion]
 *       [--latency-ms <n>]            fixed per-request latency via page.route
 *       [--record-video]              lossy fallback (VP8 video -> ffmpeg frames)
 *       [--transition <name>]         run a single transition from the spec
 *
 * Flow-spec schema (tolerant of extra fields such as rubric/readback):
 *   { "flow": "<slug>", "baseUrl"?: "...", "transitions": [
 *       { "name": "<kebab>", "url": "...",
 *         "trigger": { "selector": "<css>" },
 *         "loading"?: ["<css>", ...],       // selectors watched for show/hide
 *         "budgetMs"?: 1500 } ] }           // real-content capture budget
 *
 * Capture-budget contract: a FIXED playback-rate-aware budget - base budget
 * (spec budgetMs or DEFAULT_BUDGET_MS) divided by the playback rate when
 * dilating (< 1). The harness NEVER stops on an app/fixture completion
 * signal: Step 2 review established completion signals cannot be trusted
 * across slow-mo dilation (timer-driven paths fire ~90% early).
 *
 * Determinism prep per SKILL.md: fresh context per transition, fixed
 * viewport, document.fonts.ready await, CDP Animation.setPlaybackRate,
 * optional fixed-latency network pinning, context-mode parameter
 * (default vs reducedMotion:'reduce').
 *
 * Pre-flight fails loud (with remedy, never auto-downloads): pinned-playwright
 * Chromium cache check; spec-URL reachability probe (probe localhost, not
 * 127.0.0.1 - Vite binds IPv6-only on Windows).
 */

import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const PLAYWRIGHT_VERSION = require("playwright/package.json").version;

// ---------------------------------------------------------------------------
// Constants (single place - do not scatter below).
// ---------------------------------------------------------------------------
const HARNESS_VERSION = "1.1.0";
const DEFAULT_PLAYBACK_RATE = 0.1; // 10x slow-mo: dilates a 300ms transition to ~3s so the screencast catches every visual step
const DEFAULT_BUDGET_MS = 1500; // real-content time; converted to wall time by dividing by the playback rate (see budgetOf)
const DEFAULT_OUT_DIR = ".judge-motion";
const VIEWPORT = { width: 1280, height: 720 }; // plan D1 full-viewport res; ALSO passed as screencast size - omitting it makes CDP silently downscale to 800x450
const JPEG_QUALITY = 80; // diff-pipeline sweet spot: pHash-stable, no visible banding, ~30-60KB/frame
const FRAME_PAD = 7; // frames/<elapsed-ms padded to 7 digits>.jpg
const HOLD_FRAME_INTERVAL_MS = 1000; // static-screen keepalive cadence (see makeFrameSink)
const HOLD_CHECK_INTERVAL_MS = 250; // poll 4x per hold interval so a hold frame lands within 250ms of a span going static
const PROBE_TIMEOUT_MS = 3000; // localhost servers answer in ms - 3s of silence means down, not slow
const TRIGGER_TIMEOUT_MS = 10000; // trigger element should exist right after load; 10s allows a slow first render under dilation
const NAV_TIMEOUT_MS = 15000; // upper bound for a local page load; also caps the document.fonts.ready wait (font-hang guard)
const VIDEO_FPS = 25; // recordVideo fallback: VP8 pads/dedupes to 25fps
const MAX_TIMEOUT_MS = 2147483647; // Node setTimeout 32-bit signed clamp: larger delays fire at ~1ms, silently gutting the budget

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Fail-loud helper: every fatal path names a remedy. PRE-LAUNCH ONLY (CLI
// parsing, spec validation, preflight): process.exit bypasses finally-blocks,
// so while a browser/context is live, THROW a normal Error instead -
// captureTransition's finally and main()'s per-transition catch handle
// cleanup + error.json.
// ---------------------------------------------------------------------------
function fatal(message, remedy) {
  console.error("FATAL: " + message);
  if (remedy) console.error("Remedy: " + remedy);
  process.exit(1);
}

// ---------------------------------------------------------------------------
// CLI parsing.
// ---------------------------------------------------------------------------
function parseArgs(argv) {
  const args = {
    spec: null,
    out: DEFAULT_OUT_DIR,
    playbackRate: DEFAULT_PLAYBACK_RATE,
    contextMode: "default",
    latencyMs: null,
    recordVideo: false,
    transition: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => {
      if (i + 1 >= argv.length) {
        fatal("Missing value for " + a,
          "Every flag takes one value, e.g. '--playback-rate 0.1'; see the usage block at the top of scripts/capture_motion.mjs.");
      }
      return argv[++i];
    };
    switch (a) {
      case "--spec": args.spec = next(); break;
      case "--out": args.out = next(); break;
      case "--playback-rate": args.playbackRate = Number(next()); break;
      case "--context-mode": args.contextMode = next(); break;
      case "--latency-ms": args.latencyMs = Number(next()); break;
      case "--record-video": args.recordVideo = true; break;
      case "--transition": args.transition = next(); break;
      default:
        fatal("Unknown argument: " + a,
          "See the usage block at the top of scripts/capture_motion.mjs.");
    }
  }
  if (!args.spec) {
    fatal("--spec <flow-spec.json> is required.",
      "Example: node scripts/capture_motion.mjs --spec fixtures/fixtures-flow.json");
  }
  if (!Number.isFinite(args.playbackRate) || args.playbackRate <= 0) {
    fatal("--playback-rate must be a positive number (got: " + args.playbackRate + ").",
      "Example: --playback-rate 0.1 (10x slow-mo); 1 = real time; > 1 fast-forwards.");
  }
  if (!["default", "reduced-motion"].includes(args.contextMode)) {
    fatal("--context-mode must be 'default' or 'reduced-motion' (got: " + args.contextMode + ").",
      "Use --context-mode reduced-motion only for the a11y audit mode; omit the flag otherwise.");
  }
  if (args.latencyMs !== null && (!Number.isFinite(args.latencyMs) || args.latencyMs < 0)) {
    fatal("--latency-ms must be a non-negative number (got: " + args.latencyMs + ").",
      "Example: --latency-ms 200 pins every request at a fixed 200ms.");
  }
  return args;
}

// ---------------------------------------------------------------------------
// Spec loading + validation (tolerant of extra fields: rubric, readback, ...).
// ---------------------------------------------------------------------------
const TRANSITION_NAME_RE = /^[a-z0-9][a-z0-9-]*$/; // kebab-case per SKILL.md; the name is used verbatim as a directory name

function loadSpec(specPath, onlyTransition) {
  if (!fs.existsSync(specPath)) {
    fatal("Flow spec not found: " + specPath,
      "Pass a path to a flow-spec JSON, e.g. --spec fixtures/fixtures-flow.json.");
  }
  let spec;
  try {
    spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
  } catch (err) {
    fatal("Flow spec is not valid JSON: " + specPath + " (" + err.message + ")",
      "Fix the JSON syntax; fixtures/fixtures-flow.json is a valid example.");
  }
  if (!Array.isArray(spec.transitions) || spec.transitions.length === 0) {
    fatal("Flow spec has no transitions[] array: " + specPath,
      "Schema: { \"flow\": \"<slug>\", \"transitions\": [{ \"name\", \"url\", \"trigger\": { \"selector\" } }] } - see fixtures/fixtures-flow.json.");
  }
  for (const t of spec.transitions) {
    if (!t.name || typeof t.name !== "string") {
      fatal("A transition is missing a string 'name' in " + specPath,
        "Every transition needs \"name\": \"<kebab-case>\" - see fixtures/fixtures-flow.json.");
    }
    if (!TRANSITION_NAME_RE.test(t.name)) {
      // The name becomes the transition's output DIRECTORY verbatim - reject
      // anything that is not plain kebab (path separators, dots, spaces, ...).
      fatal("Transition name '" + t.name + "' is not kebab-case (must match " +
        TRANSITION_NAME_RE + ") in " + specPath,
        "Rename it to e.g. '" + (kebab(t.name) || "my-transition") +
        "'; the name is used verbatim as the run's directory name.");
    }
    if (!t.url || typeof t.url !== "string") {
      fatal("Transition '" + t.name + "' is missing 'url' in " + specPath,
        "Add \"url\": \"http://localhost:<port>/...\" (absolute, or relative with spec.baseUrl).");
    }
    if (!t.trigger || typeof t.trigger.selector !== "string") {
      fatal("Transition '" + t.name + "' is missing trigger.selector in " + specPath,
        "Add \"trigger\": { \"selector\": \"#some-element\" } - see fixtures/fixtures-flow.json.");
    }
  }
  let transitions = spec.transitions;
  if (onlyTransition) {
    transitions = transitions.filter((t) => t.name === onlyTransition);
    if (transitions.length === 0) {
      fatal("--transition '" + onlyTransition + "' not found in spec. Available: " +
        spec.transitions.map((t) => t.name).join(", "),
        "Pick one of the listed names, or drop --transition to run all.");
    }
  }
  return { spec, transitions };
}

function resolveUrl(t, spec) {
  try {
    return spec.baseUrl ? new URL(t.url, spec.baseUrl).href : new URL(t.url).href;
  } catch {
    fatal("Transition '" + t.name + "' has an unresolvable url: " + t.url +
      (spec.baseUrl ? " (baseUrl: " + spec.baseUrl + ")" : ""),
      "Use an absolute http://localhost:<port>/... url, or set spec.baseUrl.");
  }
}

function loadingSelectorsOf(t) {
  const sel = t.loading ?? t.loadingSelectors ?? [];
  return Array.isArray(sel) ? sel : [sel];
}

function kebab(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function utcRunId(flowSlug) {
  const d = new Date();
  const p = (n, w = 2) => String(n).padStart(w, "0");
  return (
    "" + d.getUTCFullYear() + p(d.getUTCMonth() + 1) + p(d.getUTCDate()) +
    "-" + p(d.getUTCHours()) + p(d.getUTCMinutes()) + p(d.getUTCSeconds()) +
    "-" + flowSlug
  );
}

// ---------------------------------------------------------------------------
// Pre-flight 1: cached Chromium matches the playwright pin. Playwright's own
// registry encodes the pinned browser build into executablePath(); if that
// path is absent, the pin has no cached browser. NEVER auto-download mid-run.
// ---------------------------------------------------------------------------
function preflightChromium() {
  let exe;
  try {
    exe = chromium.executablePath();
  } catch (err) {
    exe = null;
  }
  if (!exe || !fs.existsSync(exe)) {
    fatal(
      "No cached Chromium matches playwright@" + PLAYWRIGHT_VERSION +
      (exe ? " (expected at: " + exe + ")" : "") +
      ". This harness never downloads a browser mid-run.",
      "Run once from the skill dir: npx playwright install chromium"
    );
  }
  return exe;
}

// ---------------------------------------------------------------------------
// Pre-flight 2: every spec URL answers HTTP. Probe exactly the URL the run
// will use - on Windows, Vite binds IPv6-only, so specs must say 'localhost'
// (which resolves to ::1), never 127.0.0.1.
// ---------------------------------------------------------------------------
async function preflightUrls(urls) {
  for (const url of urls) {
    let res;
    try {
      const ac = new AbortController();
      const timer = setTimeout(() => ac.abort(), PROBE_TIMEOUT_MS);
      res = await fetch(url, { signal: ac.signal, redirect: "follow" });
      clearTimeout(timer);
    } catch (err) {
      // Derive the serve hint from the FAILING url - no hardcoded port here
      // (SKILL.md owns the fixtures' canonical port).
      const u = new URL(url);
      const port = u.port || (u.protocol === "https:" ? "443" : "80");
      fatal(
        "Spec URL is not reachable: " + url + " (" + err.message + ")",
        "Serve the app first: e.g. 'python -m http.server " + port + "' from the directory " +
        "serving this app (fixtures: run it from the fixtures dir). " +
        "On Windows probe/spec 'localhost', not 127.0.0.1 - Vite binds IPv6-only."
      );
    }
    if (!res.ok) {
      fatal(
        "Spec URL answered HTTP " + res.status + ": " + url,
        "Fix the url/path in the flow spec, or serve the right directory."
      );
    }
  }
}

// ---------------------------------------------------------------------------
// recordVideo fallback ffmpeg guard: any ffmpeg use resolves from PATH and
// hard-fails if the resolved binary is Playwright's --disable-everything
// build (SKILL.md two-ffmpeg pitfall - fail loud on fallback config).
// ---------------------------------------------------------------------------
function resolveRealFfmpeg() {
  let exe;
  try {
    const cmd = process.platform === "win32" ? "where" : "which";
    exe = execFileSync(cmd, ["ffmpeg"], { encoding: "utf8" }).split(/\r?\n/)[0].trim();
  } catch {
    fatal("--record-video needs ffmpeg on PATH to extract frames; none found.",
      "Install a full ffmpeg build (e.g. gyan.dev full) and put it on PATH, " +
      "or drop --record-video and use the default screencast capture.");
  }
  let version = "";
  try {
    version = execFileSync(exe, ["-version"], { encoding: "utf8" });
  } catch (err) {
    fatal("Resolved ffmpeg failed to run: " + exe + " (" + err.message + ")",
      "Reinstall a full ffmpeg build (e.g. gyan.dev full) and make sure it is first on PATH.");
  }
  if (/ms-playwright/i.test(exe) || /playwright/i.test(version)) {
    fatal(
      "PATH ffmpeg resolves to Playwright's bundled --disable-everything build (" + exe +
      "); it cannot extract/filter frames.",
      "Put a full ffmpeg build (e.g. gyan.dev full) ahead of it on PATH."
    );
  }
  return exe;
}

// ---------------------------------------------------------------------------
// In-page signal collectors. Installed TWICE, idempotently (window.__jm
// guard): (1) context.addInitScript, so collectors exist at document start of
// EVERY document the context creates - this is what keeps a
// navigation-triggered transition (real <a href> / MPA route) from losing its
// collectors when the pre-trigger document is destroyed; (2) a pre-trigger
// page.evaluate on the current document as belt-and-suspenders. Everything
// lands on window.__jm; times are performance.now() so they share a timebase
// with layout-shift startTime.
// ---------------------------------------------------------------------------
function focusLabel() {
  const a = document.activeElement;
  return a ? a.tagName + (a.id ? "#" + a.id : "") : "none";
}

const INSTALL_COLLECTORS = (loadingSelectors) => {
  if (window.__jm) return; // double-install guard: addInitScript AND the pre-trigger evaluate both call this
  const jm = {
    t0: null, // set at trigger time in the PRE-trigger document; still null at readback = this document was created by a post-trigger navigation
    layoutShiftEntries: [], // {value, startTime} - hadRecentInput excluded (Chrome's rule; see layoutShiftEntriesInputExcluded)
    layoutShiftEntriesInputExcluded: [], // same shape, hadRecentInput=true - kept so a pop-in-on-click is not silently cls=0
    loading: {}, // selector -> [{atMs (performance.now), visible}]
    errors: [],
  };
  window.__jm = jm;

  try {
    new PerformanceObserver((list) => {
      for (const e of list.getEntries()) {
        const rec = { value: e.value, startTime: e.startTime };
        if (e.hadRecentInput) jm.layoutShiftEntriesInputExcluded.push(rec);
        else jm.layoutShiftEntries.push(rec);
      }
    }).observe({ type: "layout-shift", buffered: false });
  } catch (err) {
    jm.errors.push("layout-shift observer unavailable: " + err.message);
  }

  // Loading-selector watchers need the DOM. Via addInitScript this function
  // runs at document start (no <body> yet), so defer the attach to
  // DOMContentLoaded; via the pre-trigger evaluate the DOM already exists.
  const attachLoadingWatchers = () => {
    const isVisible = (el) => {
      const cs = getComputedStyle(el);
      return cs.display !== "none" && cs.visibility !== "hidden" && Number(cs.opacity) !== 0;
    };
    for (const selector of loadingSelectors) {
      const el = document.querySelector(selector);
      if (!el) {
        jm.errors.push("loading selector not found: " + selector);
        continue;
      }
      const log = [{ atMs: performance.now(), visible: isVisible(el) }];
      jm.loading[selector] = log;
      new MutationObserver(() => {
        const visible = isVisible(el);
        if (log[log.length - 1].visible !== visible) {
          log.push({ atMs: performance.now(), visible });
        }
      }).observe(el, { attributes: true, attributeFilter: ["class", "style"], childList: true, subtree: true });
    }
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachLoadingWatchers, { once: true });
  } else {
    attachLoadingWatchers();
  }
};

// Derive show/hide CYCLES (times relative to trigger t0) from the raw log.
// Handles the two shapes a first-show-only scan misses: (a) a selector
// already visible at watcher-install that hides post-trigger - the
// loading->content-swap shape - reported as a cycle with showAtMs null
// (visibility predates observation, so its true start and visibleForMs are
// unknowable); (b) multiple show/hide cycles (spinner flicker). The
// first-cycle convenience fields (showAtMs/hideAtMs/visibleForMs) and the
// raw events are kept.
function deriveLoadingTimings(rawLoading, t0) {
  const out = {};
  for (const [selector, log] of Object.entries(rawLoading)) {
    const events = log.map((e) => ({
      atMs: Math.round((e.atMs - t0) * 10) / 10,
      visible: e.visible,
    }));
    const wasVisibleAtInstall = events.length > 0 && events[0].visible;
    const cycles = [];
    let open = wasVisibleAtInstall
      ? { showAtMs: null, hideAtMs: null, visibleForMs: null }
      : null;
    for (let i = 1; i < events.length; i++) {
      const e = events[i];
      if (e.visible && open === null) {
        open = { showAtMs: e.atMs, hideAtMs: null, visibleForMs: null };
      } else if (!e.visible && open !== null) {
        open.hideAtMs = e.atMs;
        open.visibleForMs = open.showAtMs !== null
          ? Math.round((open.hideAtMs - open.showAtMs) * 10) / 10
          : null;
        cycles.push(open);
        open = null;
      }
    }
    if (open !== null) cycles.push(open); // still visible at capture end: hideAtMs stays null
    const first = cycles.length > 0 ? cycles[0] : null;
    out[selector] = {
      events,
      cycles,
      wasVisibleAtInstall,
      showAtMs: first ? first.showAtMs : null,
      hideAtMs: first ? first.hideAtMs : null,
      visibleForMs: first ? first.visibleForMs : null,
    };
  }
  return out;
}

// Budget scaling: the base budget is REAL-CONTENT time; dividing by the
// playback rate converts it to capture wall time for BOTH dilation (rate < 1
// scales up) and fast-forward (rate > 1 scales down). Overflow vs the 32-bit
// setTimeout clamp (tiny rates) is validated pre-launch in main().
function budgetOf(t, playbackRate) {
  const baseMs = Number.isFinite(t.budgetMs) && t.budgetMs > 0 ? t.budgetMs : DEFAULT_BUDGET_MS;
  const effectiveMs = Math.max(1, Math.round(baseMs / playbackRate));
  return { baseMs, effectiveMs };
}

// ---------------------------------------------------------------------------
// Frame sink: writes frames/<elapsed-ms-padded>.jpg. Elapsed is wall ms since
// screencast start (onFrame timestamps are frameSwapWallTime, epoch ms).
// Collisions (sub-ms bursts) bump by 1ms so no frame is ever dropped.
//
// Static-screen keepalive ("hold" frames): CDP screencast is damage-driven -
// a static screen sends nothing, so a transition whose defects are abrupt
// timer events (the janky fixture by design) yields very few frames. While
// the screencast is live, if no damage frame has arrived for
// HOLD_FRAME_INTERVAL_MS the sink re-writes the LAST RECEIVED frame at the
// current elapsed time. This is honest sampling of a genuinely static screen
// (the screen shows exactly that content at that time) with ZERO page
// perturbation - nothing is injected or polled in the renderer (unlike the
// forbidden page.screenshot() polling). Hold frames are listed in
// signals.json holdFrames and excluded from measuredDurationMs.
// ---------------------------------------------------------------------------
function makeFrameSink(framesDir, captureStartWallMs) {
  const used = new Set();
  const state = {
    realCount: 0,
    holdCount: 0,
    lastRealElapsedMs: 0,
    holdFrames: [],
    closed: false, // set by close() after screencast.stop(); late frames are counted, never written
    lateFrames: 0,
  };
  let lastBuffer = null;
  let lastActivityWallMs = 0;
  let timer = null;

  const writeFrame = (elapsedRaw, data) => {
    let elapsed = Math.max(0, Math.round(elapsedRaw));
    while (used.has(elapsed)) elapsed += 1;
    used.add(elapsed);
    fs.writeFileSync(
      path.join(framesDir, String(elapsed).padStart(FRAME_PAD, "0") + ".jpg"),
      data
    );
    return elapsed;
  };

  const onFrame = ({ data, timestamp }) => {
    if (state.closed) {
      // Straggler CDP frame after screencast.stop(): writing it would leave
      // an untracked file the counts/holdFrames in signals.json never saw.
      state.lateFrames += 1;
      return;
    }
    const elapsed = writeFrame(timestamp - captureStartWallMs, data);
    state.realCount += 1;
    if (elapsed > state.lastRealElapsedMs) state.lastRealElapsedMs = elapsed;
    lastBuffer = data;
    lastActivityWallMs = Date.now();
  };

  const startKeepalive = () => {
    timer = setInterval(() => {
      if (state.closed || !lastBuffer) return; // closed sink or nothing painted yet
      const now = Date.now();
      if (now - lastActivityWallMs >= HOLD_FRAME_INTERVAL_MS) {
        const elapsed = writeFrame(now - captureStartWallMs, lastBuffer);
        state.holdCount += 1;
        state.holdFrames.push(elapsed);
        lastActivityWallMs = now;
      }
    }, HOLD_CHECK_INTERVAL_MS);
  };
  const stopKeepalive = () => {
    if (timer) clearInterval(timer);
    timer = null;
  };
  const close = () => { state.closed = true; };

  return { onFrame, state, startKeepalive, stopKeepalive, close };
}

// ---------------------------------------------------------------------------
// recordVideo fallback frame extraction (documented lossy: 800x800 default
// downscale avoided by passing the viewport size, but VP8 re-encode + 25fps
// duplicate-frame padding remain). Frame timestamps are index/fps
// approximations, not paint times.
// ---------------------------------------------------------------------------
function extractVideoFrames(ffmpeg, videoPath, framesDir) {
  const tmpPattern = path.join(framesDir, "vtmp_%06d.jpg");
  execFileSync(ffmpeg, [
    "-hide_banner", "-loglevel", "error",
    "-i", videoPath,
    "-vf", "fps=" + VIDEO_FPS,
    "-q:v", "2",
    tmpPattern,
  ]);
  const frameMs = 1000 / VIDEO_FPS;
  let count = 0, lastElapsedMs = 0;
  for (const f of fs.readdirSync(framesDir).filter((f) => f.startsWith("vtmp_")).sort()) {
    const idx = Number(f.slice(5, 11)) - 1; // ffmpeg numbering starts at 1
    const elapsed = Math.round(idx * frameMs);
    fs.renameSync(
      path.join(framesDir, f),
      path.join(framesDir, String(elapsed).padStart(FRAME_PAD, "0") + ".jpg")
    );
    count += 1;
    if (elapsed > lastElapsedMs) lastElapsedMs = elapsed;
  }
  return { count, lastElapsedMs };
}

// ---------------------------------------------------------------------------
// One transition capture.
// ---------------------------------------------------------------------------
async function captureTransition({ browser, t, url, budget, args, runDir, flowSlug, chromiumExe, ffmpeg }) {
  const transitionDir = path.join(runDir, t.name);
  const framesDir = path.join(transitionDir, "frames");
  fs.mkdirSync(framesDir, { recursive: true });

  const contextOptions = {
    viewport: VIEWPORT,
    deviceScaleFactor: 1,
    reducedMotion: args.contextMode === "reduced-motion" ? "reduce" : "no-preference",
  };
  if (args.recordVideo) {
    contextOptions.recordVideo = { dir: transitionDir, size: VIEWPORT };
  }

  const context = await browser.newContext(contextOptions);
  // Collectors must survive real navigations (<a href> / MPA routes are
  // first-class transitions): install them at document start of EVERY
  // document this context creates. The pre-trigger evaluate below covers the
  // already-loaded document; the window.__jm guard makes both idempotent.
  await context.addInitScript(INSTALL_COLLECTORS, loadingSelectorsOf(t));
  const page = await context.newPage();

  let sink = null; // hoisted so the finally below can stop the keepalive on the ERROR path too
  try {
    if (args.latencyMs !== null) {
      const latency = args.latencyMs;
      await page.route("**/*", async (route) => {
        await new Promise((r) => setTimeout(r, latency));
        await route.continue();
      });
    }

    // Screencast availability check (playwright >= 1.59) - fail loud, name
    // the fallback chain, never degrade silently.
    const screencastAvailable = page.screencast && typeof page.screencast.start === "function";
    if (!args.recordVideo && !screencastAvailable) {
      // Throw, not fatal(): a browser is live here and process.exit would
      // strand it past the finally-cleanup.
      throw new Error(
        "page.screencast is unavailable on playwright@" + PLAYWRIGHT_VERSION + " (needs >= 1.59). " +
        "Fallback chain: (1) raw CDP Page.startScreencast - not implemented in this harness; " +
        "(2) re-run with --record-video (lossy). Preferred: 'npm install' in the skill dir " +
        "to get the pinned playwright@^1.61.1."
      );
    }

    // Start the screencast BEFORE navigation: the load render + settled
    // "before" baseline are real capture content (Step 4's selection wants
    // genuine before-frames, and FOUT/FOIT during load is itself a target
    // defect class). Frames are timestamped relative to this start;
    // signals.json's triggerOffsetMs marks where the trigger fired.
    const captureStartWallMs = Date.now();
    const startedUtc = new Date(captureStartWallMs).toISOString();
    sink = makeFrameSink(framesDir, captureStartWallMs);
    if (!args.recordVideo) {
      // size must be passed explicitly: without it CDP silently downscales
      // every frame to 800x450 regardless of the viewport.
      await page.screencast.start({ onFrame: sink.onFrame, quality: JPEG_QUALITY, size: VIEWPORT });
      sink.startKeepalive();
    }

    await page.goto(url, { waitUntil: "load", timeout: NAV_TIMEOUT_MS });
    // Never bypass fonts.ready: FOUT/FOIT is a target defect class. But a
    // hung font request stalls it forever, so cap the wait and fail loud
    // (throw - a browser is live) naming the hang.
    let fontsTimer = null;
    try {
      await Promise.race([
        page.evaluate(() => document.fonts.ready),
        new Promise((_resolve, reject) => {
          fontsTimer = setTimeout(() => reject(new Error(
            "document.fonts.ready did not resolve within " + NAV_TIMEOUT_MS + "ms on " + url +
            " - a font load is hanging. Fix or self-host the hanging @font-face source " +
            "(check the page's font request URLs in devtools/network)."
          )), NAV_TIMEOUT_MS);
        }),
      ]);
    } finally {
      clearTimeout(fontsTimer);
    }
    await page.evaluate(INSTALL_COLLECTORS, loadingSelectorsOf(t)); // idempotent no-op where the init script already installed

    // Slow-motion lever: CDP Animation.setPlaybackRate covers CSS
    // transitions/animations + WAAPI (Playwright's Clock API does not).
    const cdp = await context.newCDPSession(page);
    await cdp.send("Animation.enable");
    await cdp.send("Animation.setPlaybackRate", { playbackRate: args.playbackRate });

    await page.waitForSelector(t.trigger.selector, { state: "visible", timeout: TRIGGER_TIMEOUT_MS });

    const focusBefore = await page.evaluate(focusLabel);
    const scrollYBefore = await page.evaluate(() => window.scrollY);

    // Mark t0 in the page's performance.now() timebase, then fire the trigger.
    await page.evaluate(() => { window.__jm.t0 = performance.now(); });
    const triggerWallMs = Date.now();
    await page.click(t.trigger.selector);

    // PLAYBACK-RATE-AWARE FIXED BUDGET; no completion-signal stop (see header).
    await new Promise((r) => setTimeout(r, budget.effectiveMs));

    if (!args.recordVideo) {
      sink.stopKeepalive();
      await page.screencast.stop();
      sink.close(); // straggler CDP frames after this are counted (lateFrames), never written
    }

    const focusAfter = await page.evaluate(focusLabel);
    const scrollYAfter = await page.evaluate(() => window.scrollY);
    const collected = await page.evaluate(() => window.__jm ?? null);
    if (collected === null) {
      // Fail loud, naming the cause: the trigger destroyed the pre-trigger
      // document and the context.addInitScript install did not take effect on
      // the new one (or the page clobbered window.__jm). Without collectors
      // there are no signals to report - this transition is a capture failure.
      throw new Error(
        "In-page collectors (window.__jm) are missing from the post-trigger document for '" +
        t.name + "'. Cause: the pre-trigger document was replaced and the addInitScript " +
        "re-install did not run (or the page overwrote window.__jm). Re-run; if it persists, " +
        "check whether the target app assigns to window.__jm."
      );
    }

    // Navigation detection: t0 is written into the PRE-trigger document just
    // before the click, so a surviving document reads it back non-null. A real
    // navigation (<a href> / MPA route) replaces the document, and the
    // re-installed collectors start with t0 = null - that null IS the
    // navigation signature. (A 'framenavigated' listener would false-positive
    // on SPA pushState routes, which keep the document - and t0 - alive.)
    const navigated = collected.t0 === null;
    const collectorScope = navigated ? "post-navigation" : "same-document";
    // Post-navigation: the pre-navigation collected state is destroyed with
    // its document before it can be read, and CLS/mutation baselines reset.
    // Signals therefore cover the post-navigation document only. Its
    // performance.now() timebase starts at navigationStart (post-trigger), so
    // t0 = 0 scopes "everything this document did" - honest, and flagged via
    // collectorScope so gate/judge consumers know the coverage.
    const effectiveT0 = navigated ? 0 : collected.t0;
    for (const e of collected.errors) {
      console.warn("[capture] " + t.name + " collector warning: " + e);
    }

    // recordVideo mode: close context first so the video file is flushed.
    let videoFrames = null;
    let videoPath = null;
    if (args.recordVideo) {
      videoPath = await page.video().path();
      await context.close();
      videoFrames = extractVideoFrames(ffmpeg, videoPath, framesDir);
    }

    const entriesAfterTrigger = collected.layoutShiftEntries.filter(
      (e) => e.startTime >= effectiveT0
    );
    const excludedAfterTrigger = (collected.layoutShiftEntriesInputExcluded || []).filter(
      (e) => e.startTime >= effectiveT0
    );
    const cls = entriesAfterTrigger.reduce((sum, e) => sum + e.value, 0);
    const shiftShape = (e) => ({
      value: Math.round(e.value * 1e6) / 1e6,
      startTime: Math.round(e.startTime * 10) / 10,
      afterTriggerMs: Math.round((e.startTime - effectiveT0) * 10) / 10,
    });
    const realFrameCount = args.recordVideo ? videoFrames.count : sink.state.realCount;
    const holdFrameCount = args.recordVideo ? 0 : sink.state.holdCount;
    const frameCount = realFrameCount + holdFrameCount;
    const lastRealElapsedMs = args.recordVideo ? videoFrames.lastElapsedMs : sink.state.lastRealElapsedMs;
    const triggerOffsetMs = triggerWallMs - captureStartWallMs;
    const measuredDurationMs = Math.max(0, lastRealElapsedMs - triggerOffsetMs);

    const signals = {
      transition: t.name,
      collectorScope, // "same-document" | "post-navigation" (see navigation detection above)
      collectorScopeNote: navigated
        ? "trigger navigated to a new document; CLS/mutation baselines reset with it - " +
          "signals cover the post-navigation document only, times relative to its navigationStart"
        : null,
      cls: Math.round(cls * 1e6) / 1e6,
      clsNote: "cls excludes shifts Chrome marks hadRecentInput=true (any shift within 500ms " +
        "REAL time of the trigger click, regardless of playback rate) - a visible " +
        "pop-in-on-click can therefore read cls=0; reconcile against " +
        "layoutShiftEntriesInputExcluded and the frames",
      layoutShiftEntries: entriesAfterTrigger.map(shiftShape),
      layoutShiftEntriesInputExcluded: excludedAfterTrigger.map(shiftShape), // input-excluded shifts, same shape, kept for honesty
      focusBefore,
      focusAfter,
      scrollYBefore,
      scrollYAfter,
      loadingSelectorTimings: deriveLoadingTimings(collected.loading, effectiveT0),
      measuredDurationMs, // last DAMAGE paint relative to the trigger (hold frames excluded)
      frameCount, // total frames written = realFrameCount + holdFrameCount
      realFrameCount, // damage-driven screencast frames - the temporal-density signal
      holdFrameCount, // static-screen keepalive re-writes (see makeFrameSink)
      holdFrames: args.recordVideo ? [] : sink.state.holdFrames, // elapsed-ms of hold frames
      lateFrames: args.recordVideo ? 0 : sink.state.lateFrames, // straggler CDP frames after sink close - counted, never written
      playbackRate: args.playbackRate,
      contextMode: args.contextMode,
      triggerOffsetMs, // frames are stamped relative to screencast start; trigger = this offset
      collectorWarnings: collected.errors,
    };
    fs.writeFileSync(
      path.join(transitionDir, "signals.json"),
      JSON.stringify(signals, null, 2) + "\n"
    );

    const meta = {
      harnessVersion: HARNESS_VERSION,
      playwrightVersion: PLAYWRIGHT_VERSION,
      captureMode: args.recordVideo
        ? "recordVideo (LOSSY fallback: VP8 re-encode, " + VIDEO_FPS + "fps padding, " +
          "frame times are index/fps approximations, not paint times)"
        : "page.screencast",
      spec: {
        file: path.resolve(args.spec),
        flow: flowSlug,
        transition: t, // full echo, extra fields included
      },
      url,
      viewport: VIEWPORT,
      jpegQuality: args.recordVideo ? null : JPEG_QUALITY,
      playbackRate: args.playbackRate,
      contextMode: args.contextMode,
      latencyMs: args.latencyMs,
      budget: { baseMs: budget.baseMs, effectiveMs: budget.effectiveMs },
      startedUtc,
      chromiumExecutable: chromiumExe,
      videoPath,
      machine: {
        platform: os.platform(),
        release: os.release(),
        arch: os.arch(),
        node: process.version,
        cpuCount: os.cpus().length,
      },
    };
    fs.writeFileSync(
      path.join(transitionDir, "meta.json"),
      JSON.stringify(meta, null, 2) + "\n"
    );

    console.log(
      "[capture] " + t.name + ": frames=" + frameCount +
      " (real=" + realFrameCount + " hold=" + holdFrameCount + ")" +
      " cls=" + signals.cls +
      " focus=" + focusBefore + "->" + focusAfter +
      " measuredDurationMs=" + measuredDurationMs +
      " scope=" + collectorScope +
      " -> " + transitionDir
    );
  } finally {
    if (sink) {
      // Idempotent on the success path; load-bearing on the ERROR path - a
      // still-running keepalive setInterval would pin the event loop and hang
      // the process after main() finishes.
      sink.stopKeepalive();
      sink.close();
    }
    try { await context.close(); } catch { /* already closed in the recordVideo path */ }
  }
}

// ---------------------------------------------------------------------------
// Main.
// ---------------------------------------------------------------------------
async function main() {
  const args = parseArgs(process.argv.slice(2));
  const { spec, transitions } = loadSpec(args.spec, args.transition);

  const chromiumExe = preflightChromium();
  const ffmpeg = args.recordVideo ? resolveRealFfmpeg() : null;

  // Resolve every URL + budget BEFORE launching the browser so their failures
  // stay on the pre-launch fatal() path (fatal is forbidden once a browser is
  // live - it bypasses finally-cleanup).
  const resolved = transitions.map((t) => ({
    t,
    url: resolveUrl(t, spec),
    budget: budgetOf(t, args.playbackRate),
  }));
  for (const { t, budget } of resolved) {
    if (!Number.isFinite(budget.effectiveMs) || budget.effectiveMs > MAX_TIMEOUT_MS) {
      fatal(
        "Transition '" + t.name + "': budget " + budget.baseMs + "ms / playback rate " +
        args.playbackRate + " overflows the 32-bit setTimeout limit (" + MAX_TIMEOUT_MS + "ms).",
        "Use a larger --playback-rate or a smaller budgetMs."
      );
    }
  }
  await preflightUrls([...new Set(resolved.map((r) => r.url))]);

  const flowSlug = kebab(spec.flow || spec.name || path.basename(args.spec, ".json"));
  let runId = utcRunId(flowSlug);
  let runDir = path.resolve(args.out, runId);
  for (let n = 2; fs.existsSync(runDir); n++) {
    runDir = path.resolve(args.out, runId + "-" + n); // append-only: never overwrite a prior run
  }
  fs.mkdirSync(runDir, { recursive: true });

  console.log("[capture] run " + path.basename(runDir) +
    " (playbackRate=" + args.playbackRate + ", contextMode=" + args.contextMode +
    ", transitions=" + transitions.map((t) => t.name).join(",") + ")");

  const browser = await chromium.launch({ headless: true });
  const failed = [];
  try {
    for (const { t, url, budget } of resolved) {
      try {
        await captureTransition({
          browser, t, url, budget, args, runDir, flowSlug, chromiumExe, ffmpeg,
        });
      } catch (err) {
        // Failure isolation: record this transition's failure and keep going -
        // one broken transition must not silently discard the rest of the run.
        failed.push(t.name);
        const transitionDir = path.join(runDir, t.name);
        fs.mkdirSync(transitionDir, { recursive: true });
        fs.writeFileSync(
          path.join(transitionDir, "error.json"),
          JSON.stringify({
            transition: t.name,
            error: String((err && err.message) || err),
            stack: (err && err.stack) || null,
            atUtc: new Date().toISOString(),
          }, null, 2) + "\n"
        );
        console.error("[capture] TRANSITION FAILED: " + t.name + " - " + ((err && err.message) || err));
      }
    }
  } finally {
    await browser.close();
  }
  if (failed.length > 0) {
    console.error(
      "[capture] " + failed.length + "/" + resolved.length + " transition(s) failed: " +
      failed.join(", ") + " (error.json in each failed transition's dir)"
    );
    process.exitCode = 1;
  }
  console.log("[capture] done: " + runDir);
}

main().catch((err) => {
  fatal("Unhandled error: " + (err && err.stack ? err.stack : err));
});
