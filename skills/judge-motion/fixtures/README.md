# judge-motion calibration fixtures

**FROZEN CALIBRATION ANCHORS — do not casually edit `smooth.html` or `janky.html`.**
`/judge-motion --calibrate` (SKILL.md § Calibration) asserts against the exact defect
behaviors and timings in these files: janky must FAIL with the correct defect classes
named, smooth must never FAIL. Any edit changes what "correctly calibrated" means and
requires re-validating the calibration contract. Timing constants live in ONE `T = {...}`
block at the top of each file's script — that block is the entire timing surface.

Per `measurement-validity.md` § Calibrate with
anchors: these are the frozen known-good (`smooth.html`) and known-garbage (`janky.html`)
inputs the pipeline must separate before any real verdict is trusted.

## How to serve

From this directory (PowerShell):

```powershell
python -m http.server 8765
```

(`py -m http.server 8765` if `python` is not on PATH.)

- **Port 8765** is the port SKILL.md's inventory declares for these fixtures. Check it
  before first use: `uv run --project dev-observatory observatory ports` (as of Step 2 the
  map lists 8765 under Alpha4Gate with no collision flagged; the fixture server is
  transient, stop it when done).
- **HTTP serving is mandatory — `file://` breaks PerformanceObserver.** The layout-shift
  (`layout-shift` entry type) observer that the CLS defect must register against does not
  deliver entries on a `file://` origin. Always go through `http://localhost:8765/...`.

## The fixtures

Both files are self-contained static HTML/CSS/JS: zero external dependencies, zero network
fetches, no build step. Both render the same two-"page" app (Home / Detail) swapped by a
button click, expose `window.__cls` (accumulated layout-instability score, real
`layout-shift` entries with `hadRecentInput` excluded), and log each shift entry to the
console. The color divergence between the files (blue/green smooth vs rust/purple janky)
is intentional — a tell-the-fixtures-apart affordance, not defect-related.

### smooth.html — known-good anchor

The clean reference swap. Behavior contract:

- Single **300ms eased CSS transition** (opacity + translateY only — compositor
  properties, no layout thrash) crossfading Home and Detail.
- **Properly-delayed loading skeleton**: simulated load time is `?delay=<ms>` (default 0 —
  fast enough that no skeleton ever shows). The skeleton appears only after the fixture's
  skeleton delay and, once shown, stays for its minimum display time — the exact values are
  smooth.html's `T` constants; the corresponding GATE thresholds live in
  `scripts/gate_signals.py`. Skeleton
  blocks are deliberately unanimated so its screenshots are deterministic.
- **Focus preserved sensibly**: after the swap settles, focus moves to the new page's
  heading (`tabindex="-1"` + `.focus()`, the standard accessible route-change pattern).
  Completion is **transition-driven**: the focus move + `busy` release fire on the
  incoming page's opacity `transitionend` — immediately under reduced motion (where
  `transition: none` means the event never fires), with a fallback-only safety timeout
  (`SWAP_SAFETY_MS`, 6000ms) backstopping a missed event. Headings show a dashed outline
  when focused, so correct focus is visible in screenshots.
- **No layout shift**: pages are absolutely positioned in a fixed-height stage; the
  skeleton is an overlay. `window.__cls` stays 0.
- **Genuine `prefers-reduced-motion: reduce` branch**: a media-query block suppresses the
  swap transition entirely. Step 8's `--reduced-motion` audit greps the served CSS for
  this query and expects a flat diff curve under `reducedMotion:'reduce'`.

Query params: `?delay=<ms>` (simulated load), `?freeze=<state>`, `?auto=1`, `?debug=1`
(all below).

### janky.html — known-garbage anchor

Same two-page swap with five injected defects. **All default ON**; each is independently
disabled with its query param (`?flash=0&spinner=0...` compose). No
`prefers-reduced-motion` branch exists in this file (it is the garbage anchor).

Full-run timeline with all defects on: click → spinner 0–80ms → swap starts at 100ms →
4 fade-out steps at 190/280/370/460ms (old page fully hidden at 460ms) → white gap of
exactly `FLASH_MS` (34ms, both pages hidden 460–494ms) → 4 fade-in steps at
494/584/674/764ms (the FIRST fade-in step lands at exactly the end of the gap) → settle
≈ 764ms → layout shift at ≈ 1064ms. With `?flash=0` the gap is zero: the fade-in's first
step runs in the same timer flush as the fade-out's final hide (fade-out timers register
first), so no blank frame is ever painted — settle ≈ 730ms, shift ≈ 1030ms. The flash
and step defects are therefore independently toggleable. Measured (iter-2 rAF-sampled
real-time CDP run, paint times quantized to the next frame): with flash on, exactly 2
both-pages-hidden frames at 466.6ms and 483.3ms after the click — a ~33.5ms blank window
— first fade-in paint ~500ms, fade-in complete ~784ms; with `?flash=0`, exactly 0
both-hidden frames (the final fade-out hide and first fade-in reveal paint in the same
frame), fade-in complete ~747ms.

## Defect inventory

Gate names below are cited from SKILL.md's run loop (mechanical pre-gates: CLS, focus
retention, scroll restoration, spinner min-display/delay-before-show, duration-in-range)
and vision-judge question battery. **Threshold values are NOT stated here** — the single
source of truth is `scripts/gate_signals.py` (Step 5).

| Defect | Query param | What it looks like | Which gate / vision question should catch it |
|---|---|---|---|
| White flash mid-swap | `?flash=0` disables | Both pages hidden for exactly `FLASH_MS` (34ms ≈ 2 frames at 60fps); the bare white stage shows between old and new content. With `?flash=0` the blank window is zero (no both-hidden frame is ever painted) | Vision judge: "white flash between labeled frames?" (flicker/flash residual). The frame pipeline's diff-spike selection must surface the flash frame (local-maximum diff) — uniform sampling would miss it |
| Layout shift on settle | `?shift=0` disables | ~300ms after the swap "completes", a yellow banner pops open above the card and all content jumps down 64px; registers as real `layout-shift` entries (`window.__cls` > 0) | Mechanical gate: **CLS** (layout-shift PerformanceObserver signal). Vision backup: "element jump?" |
| Spinner flash | `?spinner=0` disables | Spinner overlay appears immediately on click (no delay-before-show) and vanishes after ~80ms (no min-display) | Mechanical gate: **spinner min-display/delay-before-show** (loading-selector MutationObserver timestamps). Vision backup: spinner-flash feel / "skeleton absent/flashed?" |
| setTimeout-stepped animation | `?step=0` disables (falls back to a smooth 300ms CSS crossfade) | The swap moves in 4 discrete opacity jumps at 90ms intervals instead of one eased transition | Mechanical gate: **duration-in-range** against the motion rubric; diff-curve shape shows staircase spikes instead of a smooth hump. Vision judge: jank residual |
| Focus dropped to body | `?focus=0` disables (focuses the new heading instead) | After the swap, `document.activeElement` is `<body>`; no focus outline anywhere (invisible in a plain screenshot — see `?debug=1`) | Mechanical gate: **focus retention** (activeElement collector) |

(The remaining mechanical gate, scroll restoration, has no injected defect in v1 — the
fixtures are single-viewport and never scroll.)

## Freeze mode (`?freeze=<state>`) — verification-only

Time-based defects cannot be seen in a single static screenshot, so each fixture can HOLD
a named state statically: the freeze branch applies the state before first paint, attaches
**no timers and no handlers**, and returns — so it cannot alter normal timing when the
param is absent. Frozen pages also pause animations (`animation-play-state: paused`) for
deterministic screenshots. Freeze states generate no layout-shift entries of their own
(styles land before first paint).

| URL | Held state |
|---|---|
| `smooth.html?freeze=home` | Home settled (same as default load, explicit) |
| `smooth.html?freeze=detail` | Detail settled, post-swap |
| `smooth.html?freeze=skeleton` | Loading skeleton visible, pages hidden |
| `janky.html?freeze=home` | Home settled |
| `janky.html?freeze=flash` | Mid-swap white flash: both pages hidden, white stage |
| `janky.html?freeze=step2` | Stepped-animation mid-state: fade-out step 2 of 4 — outgoing Home held at the discrete opacity 0.5, Detail not yet shown |
| `janky.html?freeze=spinner` | Spinner held visible over Home (rotation paused) |
| `janky.html?freeze=detail` | Detail settled BEFORE the layout shift — the unshifted baseline to diff `freeze=shifted` against |
| `janky.html?freeze=shifted` | Post-layout-shift: banner expanded, content pushed down 64px |

## Debug helpers (verification-only, off by default)

- `?debug=1` — fixed-position corner badge showing `focus:<TAG#id>` (live, via
  focusin/focusout) and `cls:<accumulated score>`. Fixed size/position so it never
  contributes layout shift. Lets a screenshot prove the focus defect (badge reads
  `focus:BODY` on janky, `focus:H1#detail-title` on smooth) and the CLS defect
  (`cls:` > 0).
- `?auto=1` — auto-triggers the Home → Detail navigation 50ms after load, for driverless
  capture (e.g. headless `--virtual-time-budget=<ms> --screenshot`). The programmatic
  trigger is NOT user input, so the shift defect's entries stay `hadRecentInput=false`
  and count toward `window.__cls` regardless of timing.

Note on CLS timing: `layout-shift` entries within 500ms of real user input are flagged
`hadRecentInput` and excluded. Janky's `SHIFT_AFTER_MS` places the shift well past 500ms
after a real click, so the defect registers even under human driving.

Note on virtual-time capture: under headless `--virtual-time-budget` runs, layout-shift
observer entries are NOT delivered (the badge reads `cls:0.0000` even when the shift is
visually present). Read CLS from a real-time run instead. The CLS magnitude is
viewport-dependent — Step 2 measured janky ~0.0197 at its capture window; the iter-2
re-probe at the default headless viewport measured janky ~0.1201 — but the gate reads
only `> 0` vs `= 0`: smooth is exactly 0 in every real-time run, janky `?shift=0`
exactly 0. Step 3's Playwright collectors run in real time and are unaffected. Also: virtual-time budgets do not reliably drive CSS-transition
visual progress the way wall-clock time does, so the Step 2 `smooth-midswap-normal.png`
vs reduced-motion pair is **differential evidence only** — it shows the reduced-motion
branch fires (the two shots differ), NOT a calibrated mid-transition opacity sample.

## Slow-mo capture asymmetry (for the Step 3 harness)

Step 3 captures under CDP `Animation.setPlaybackRate 0.1`, which dilates CSS
transitions/animations/WAAPI but **not** JavaScript timers. By design:

- **Dilates under slow-mo (CSS-driven):** smooth.html's 300ms crossfade; janky.html's
  `?step=0` fallback crossfade; the spinner's cosmetic rotation.
- **Does NOT dilate (setTimeout/rAF-driven, stays real-time short):** the white flash
  (34ms), the spinner's appear/vanish (80ms), the stepped animation's 90ms jumps, the
  skeleton delay/min-display timing, and the layout-shift timing.

**Completion signals dilate correctly.** In the paths that have CSS transitions —
smooth.html's swap and janky.html's `?step=0` fallback — the JS-observable completion
(smooth's focus move + `busy` release; janky-`?step=0`'s settle) is driven by
`transitionend` on the incoming page's opacity, so under slow-mo it stretches with the
visuals instead of firing ~90% early on a real-time timer. Under reduced motion smooth
completes immediately (no transition, no event). Each path carries a fallback-only
safety timeout (`SWAP_SAFETY_MS`, 6000ms) that fires only if the event is missed.

That asymmetry is intentional and is exactly what makes janky janky: a slow-mo screencast
stretches the smooth fixture's transition into many gently-differing frames, while janky's
timer-driven defects remain abrupt one-or-two-frame events the diff-spike selector must
catch.
