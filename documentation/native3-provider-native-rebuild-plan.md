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
`judge-motion`. That stage may ship only the closed runtime package approved for it:
the named scripts, JSON files, HTML fixtures, package metadata, and fixture README. Legacy
tests, dependency directories, caches, and run output remain excluded.

Markerless ownership is limited to the approved JSON paths and requires both an ownership
ledger entry and matching current bytes. It is not a general markerless-file rule. Foreign
files and unowned neighbors remain untouched. Downgrade requires uninstalling with the
Native3 installer first or using the backed force route; an older installer must not infer
ownership of these files.

Stage B also permits only the reviewed source-shape corrections: moving Python metadata
comments below the module docstring without changing the executable syntax tree, and
replacing the broken fixture README link with prose. Its builder, installer, resource
copies, package row, and tests land together only after their own implementation review.
Nothing in Stage A claims that package has landed or works.

## Qualification boundary

Static source and distribution checks establish package shape and documented safety
boundaries. They do not establish live OAuth, browser capture, calibration quality,
destructive cleanup behavior, installation into a real home, rollback, or publication.
Those observations belong to release qualification against the exact integrated release
candidate.
