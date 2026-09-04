# Phase RD Step 1 package-asset authority decision

**Status:** DECIDED on 2026-09-03 and narrowed on 2026-09-04 by
`documentation/phase-rd-force-boundary-decision.md`. Together those records are the execution
authority for the remaining integration boundary in Phase RD Step 1/#178. They do not authorize a
new implementation window, active-profile change, or host mutation.

## 1. What This Is

The pending write-ahead-log (WAL) raw-junction defect is no longer the active boundary. The latest
preserved candidate recorded a controlled destructive RED and a repaired two-test GREEN, then passed
static checks and built exact all-provider output counts `169/166/166`. Its focused suite stopped at
`180 passed, 3 failed` because the older whole-corpus provenance tests knew only generated headers,
while the new raw package leaves are intentionally markerless and index-owned. The third failure is
the installer legacy hash self-seed path lacking that same package-index authority.

Primary evidence is the registered worktree for branch
`build-step-rd178-wal-20260831195206`, file `.build-step/dev-report.md`, SHA-256
`5DB921387C23DE9CBE0A636C2948D160D6DDE8891B28ED1144DFB338A441941F`, especially its repaired
gate and terminal sections. That report is diagnostic evidence, never acceptance evidence.

## 2. Locked ownership model

| Artifact class | Provenance signal | Normal installed ownership |
|---|---|---|
| Generated file, including `package-assets.index.md` | Valid anchored generated header | Provider-domain path plus ledger path/hash, current byte hash, and valid header |
| Raw `package_assets` leaf | Exact membership in a valid provider/skill/path/hash-bound package index | Provider-domain path plus ledger path/hash, current byte hash, live ledger-owned index/hash binding, and literal non-reparse path |
| Pending raw leaf | WAL v2 exact raw/index tuple | Force-free exact-same-source retry only; never force, changed-source, or uninstall authority |

Index membership makes the generated and raw classes disjoint. `review-deep/scripts/README.md` is a
raw derivative. It remains markerless because prepending a generated header would change the byte
hash bound by the canonical manifest and provenance ledger.

`Test-SkillMeshProvenance` remains a content-only generated-header parser. It must not infer
contextual ownership from markerless contents. Whole-corpus checks instead classify emitted files by
the union of:

1. anchored-header provenance for files not named by a package index; and
2. strict parsed index/hash provenance for indexed raw leaves.

Every emitted file has exactly one class. Orphaned, doubly classified, duplicate, unsafe, escaping,
provider-misbound, skill-misbound, path-misbound, or hash-mismatched files fail closed.
The shared raw-authority descriptor remains:

```text
relative path + raw SHA-256 + skill + index relative path + index SHA-256
```

Source, installed, pending-WAL, and the narrow legacy producer all normalize to that shape. The
shape is internal evidence, not caller-constructible authority.

Force never expands this table. A transaction that would need `-Force` or `-ForceShared` to adopt,
overwrite, remove, uninstall, or recover a raw package leaf refuses before mutation with the stable
prefix `install-skill-mesh: RAW_PACKAGE_FORCE_UNSUPPORTED --`. Existing generated-file force-backup
behavior on main remains unchanged. The excluded candidate-only force/WAL persistence fields and the
per-path classification rule are owned by the force-boundary decision. The pre-existing general
forced stale-path reparse hardening is separately tracked by #192.

## 3. Legacy exact-incoming self-seed

Missing `owned_file_hashes` may be reconstructed only as a ledger-only, whole-profile no-op when all
of these predicates are true:

- no pending WAL exists;
- the normal ledger parses and has the expected version and tool identity;
- provider and discovery-subdirectory identity match exactly;
- `owned_file_hashes` is absent; present-null, malformed, partial, extra, or invalid maps are not
  legacy authority;
- `owned_files` is a real array of unique, nonempty, provider-contained paths whose set equals the
  complete incoming profile set;
- every incoming target already exists as a regular file and is byte-identical to its source, so
  the transaction needs zero payload writes and zero stale removals;
- every generated target has valid anchored provenance;
- every raw leaf and its generated index are both named by `owned_files`;
- the installed index is regular and non-reparse, has a valid generated header, is byte/hash-equal
  to the incoming index, and binds the exact provider, skill, path set, and raw hashes;
- every indexed raw leaf is complete, unique, regular, literal-path non-reparse, and hash-equal to
  both its index row and incoming source; and
- the complete raw/index closure is reopened and revalidated immediately before atomic ledger
  publication.

Only then may the installer publish a complete `owned_file_hashes` map. It writes no WAL and rewrites
no profile leaf. Any failed predicate is a true no-mutation refusal. This authority never permits an
overwrite, stale removal, uninstall, partial recovery, or arbitrary byte-identical markerless peer.

## 4. Narrow implementation and proof surface

The terminal integration correction is owned by:

- `tools/install-skill-mesh.ps1`: create the strict legacy exact-incoming descriptor only in the
  exact-no-op admission branch and revalidate it before ledger publication;
- `tests/distributions/test_distributions.py`: replace the two stale universal-header assumptions
  with exact-one-class corpus proof, strengthen the legacy positive to cover the whole profile, and
  add the negatives below;
- `documentation/architecture.md` and the installer's contract comment: record the bounded,
  ledger-only legacy exception.

Do not change `tools/skill-mesh-provenance.ps1`. Keep the builder's existing raw/index design.
Re-derive the wider Step 1 candidate on current main, import the 39 calibration paths from Git object
bytes at coding-root commit `3a7ae33d09b9b26edb291e2db0cdaca1022ed643`, reproduce the exact
36-byte-identical plus 3-derivative provenance split, recreate the tier-map snapshot from current
main, and regenerate manifest/inventory output.

Do not add `forced_preimage`, `force_backup_binding`, `write_ahead_force_plan`, or
`write_ahead_expected_ledger_hash`; do not change the external force-backup record; and do not add
production `SKILL_MESH_INSTALL_TEST_*` seams beyond the two present on main at the force-boundary
decision. Add an exact no-mutation negative for every force-dependent raw action and a v1 WAL
StrictMode compatibility regression.

Required planted negatives, each proving the complete directory/byte state and ledger bytes are
unchanged:

- markerless unindexed peer;
- missing, unmarked, changed, provider-misbound, skill-misbound, or path-misbound index;
- missing, changed, or reparse raw leaf;
- raw leaf or index absent from legacy `owned_files`;
- duplicate, extra, escaping, or incomplete legacy `owned_files`;
- present malformed, partial, extra, or invalid `owned_file_hashes`;
- any source/profile set difference requiring a write or stale deletion.

Re-run the existing pending raw-addition and raw-retirement junction tests unchanged before the
broader gate. The strengthened positive snapshots the complete profile's bytes and modification
times and proves that only the ledger is published.

## 5. Salvage and stop rules

The registered `build-step-rd178-wal-20260831195206` worktree is surgical reference only. Its current
installer SHA-256 is `33C914D2AAA28A6CFAC907C24A5B0E135C0954DA8DBE45F01EE6842FEC5CE279`;
its distribution-test SHA-256 is
`4BC617B02D8F679A2CA60F62D34063166BB87C6D7C8EEE3FA68D5EFFAED985E8`.

The later rejected branch `build-step-rd178-step1-20260903150041` is also read-only forensic
evidence. Its identity, excluded force subsystem, missing root-gate evidence, and disposition are
recorded in `documentation/phase-rd-force-boundary-decision.md`; it is not a newer donor.

May be re-derived: the WAL literal-authority refactor, its two junction regressions, package
builder/index concepts, calibration/helpers, and the pinned-object import. Must not be adopted:
stale universal-header tests, incomplete legacy raw-peer refusal, any `.build-step` file as
acceptance, or a whole-branch merge/cherry-pick/copy.

Stop without further patching on dirty/diverged main, evidence-fingerprint drift, provenance or
tier-map mismatch, any solution that stamps raw assets or weakens the anchored parser, any legacy
self-seed payload write/deletion or pending-WAL use, mutation by a planted refusal, WAL regression,
force authority over a raw action, any excluded force/WAL persistence field or new production test
seam, output count other than `169/166/166`, unexplained gate-count regression, failed root gate,
High/Medium review finding, merge conflict, or any need to touch active profiles, sealed Phase IS
artifacts, Phase PROD, certificates, policy, boot, driver, or host security state.
