# Provider-native rebuild plan for the existing Claude-only skills

Status: operator-approved architecture decision. Implementation and qualification remain
gated by the stage boundaries below.

## Scope and authority

This plan is the scoped exception required by the catalog lifecycle for the existing
`claude-oauth-auth`, `context-slim`, and `judge-motion` identities. They remain
provider-native and Claude-only. Their manifest status, null core, provider eligibility,
capabilities, inventory membership, and catalog counts do not change.

The approval authorizes only the named adapter and package work in this plan. It does not
create a routine native mutation route, authorize a new provider-native identity, create a
neutral core or another provider adapter, or waive
`PROVIDER_NATIVE_REVIEW_REQUIRED` for later changes. Package resources remain subject to
`PACKAGE_RESOURCE_PLAN_REQUIRED` unless the exact Stage B package described here is being
implemented under its separate review gate.

## Stage A: adapter guidance

Stage A updates only the Claude adapters for `claude-oauth-auth` and `context-slim`, plus
this plan, the lifecycle citation, and the lifecycle contract test. It adds no package
resource, builder rule, installer rule, manifest entry, generated profile, or live-home
change.

The OAuth adapter keeps token acquisition operator-controlled. It states that
`claude setup-token` prints the token, so an agent, CI job, or recorded shell must not run
it. It preserves the non-disclosure, renewal, credential-isolation, and effect-check
boundaries without claiming a live credential test.

The Context Slim adapter preserves current-byte checks before a rules file is changed or
removed. A missing references copy is created with no-overwrite semantics; an existing or
racing destination is a conflict. Deletion uses literal-path semantics after the identity
check. An already archived memory block is accepted only after an exact, carriage-return
normalized on-disk match, and memory paths are described as outside Git only when that is
true for the selected directory.

Stage A source acceptance requires the lifecycle contract gate, package-integrity coverage,
the named distribution checks, separate builds for every provider, a deterministic repeat
of the Claude build, and independent credential and destructive-operation review. It makes
no claim that OAuth, context cleanup, or a real installed home was exercised.

## Stage B: separately gated package work

The same architecture approval permits a later, separately reviewed Stage B for
`judge-motion`. That stage ships only this closed eleven-file runtime package:
`package.json`, `package-lock.json`, `fixtures/fixtures-flow.json`,
`fixtures/janky.html`, `fixtures/smooth.html`, `fixtures/README.md`,
`scripts/calibrate.py`, `scripts/capture_motion.mjs`, `scripts/gate_signals.py`,
`scripts/reduced_motion_audit.py`, and `scripts/select_frames.py`. Legacy tests,
dependency directories, caches, and run output remain excluded. The builder uses an
explicit contained allowlist rather than turning manifest `support_assets` into an emitter;
a missing resource fails before the launcher is written.

Markerless ownership is limited to the Claude discovery paths for
`judge-motion/package.json`, `judge-motion/package-lock.json`, and
`judge-motion/fixtures/fixtures-flow.json`. Outside source-shape preflight, each requires a
valid lowercase ownership-ledger hash equal to the current bytes, plus a regular non-reparse
file no larger than two MiB. A throwing UTF-8 decoder rejects malformed bytes, the first
non-whitespace token must open an object, and the built-in `System.Web.Extensions`
`JavaScriptSerializer.DeserializeObject` result must implement `IDictionary`, with
`MaxJsonLength` fixed to the same two-MiB ceiling. This is an object-shape check, not a claim
that the parser enforces strict JSON. The allowlist is append-only while a released ledger
may own these paths. A marker property was rejected:
the shared provenance parser requires a multiline header at an emitter-legal line start,
a JSON-specific parser branch would also affect inspector and migrator decisions, hash
authority is already independent, and any byte change already invalidates the ledger hash.
This is not a general markerless-file rule. A hashless ledger grants no authority even when
the target bytes equal the incoming JSON. Backed force remains the explicit adoption route;
if an identical foreign JSON is interrupted after adoption, recovery may record it as owned
only because the verified backup certificate already authorized that exact preimage, even
though its pre- and post-hashes are equal. Foreign files and unowned neighbors remain
untouched. Downgrade requires uninstalling with the Native3 installer first or using the
backed force route; an older installer must not infer ownership of these files.

Stage B permits only two canonical source deltas. In `fixtures/README.md`, the broken
measurement-validity link becomes prose and no other content changes. In
`scripts/reduced_motion_audit.py`, the module docstring becomes the first statement and the
PEP 723 comment block moves below it, leaving the future import as the second statement and
the executable syntax tree unchanged. The builder, installer, resource copies, package row,
and tests land together only after their own implementation review. Nothing in Stage A
claims that package has landed or works.

## Qualification boundary

Static source checks, deterministic builds, emitted-package fidelity checks, and
install/reinstall/uninstall tests in disposable homes establish package shape and documented
ownership boundaries. They do not establish live OAuth, npm dependency installation,
Chromium availability, browser capture, uv execution, calibration quality, verdict quality,
destructive cleanup behavior in a real home, rollback, or publication. A supported-host
smoke against the exact integrated release candidate remains required before release
qualification. Until then the strongest claim is that a fresh Claude profile built and
installed by repository tests owns its launcher and the eleven package resources; GPT and
Codex support, runtime behavior, and live-home activation remain unverified.
