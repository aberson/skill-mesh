# Codex Provider Guide

OpenAI Codex CLI host binding, transport, and capabilities for skill-mesh. See
[`../architecture.md`](../architecture.md) for the full package contract.

## Host binding (primary)

A Codex installation binds the `codex` adapter of every portable skill into the
Codex CLI's discovery layout:

```powershell
powershell -File tools\install-skill-mesh.ps1 -Provider codex -Home <install-home>
```

Every command in this guide is spelled `powershell`: Windows PowerShell 5.1 is the
floor all `.ps1` tooling targets and the executable the test suites shell out to.
Where PowerShell 7+ is also installed `pwsh` may be substituted, but the substitution
never runs the other way — `pwsh` is absent on a 5.1-only machine
([`../../README.md`](../../README.md), "Prerequisites").

Each installed skill resolves `skills/<name>/providers/codex.md`, which references
the shared `skills/<name>/core.md`. Codex is a third provider on the existing rails,
not a separate system (design decision D-CP1): the same manifest, the same generator,
and byte-identical ledger, refusal, containment, and uninstall semantics to the other
two profiles, because all three derive from the discovery subdirectory rather than
spelling a root per provider.

Only the 54 portable skills have a Codex adapter. The 3 Claude-native exclusions —
`claude-oauth-auth`, `context-slim`, and `judge-motion` — carry `core: null` in
`config/skill-manifest.json` and are absent from a Codex profile entirely; no
misleading stub is emitted for a provider that cannot support them.

### Native discovery root and SKILL.md format

The generated Codex discovery tree is written to
`<install-home>/.agents/skills/<skill>/`, with the shared support payload beside it
at `<install-home>/.agents/skills/_shared/<asset>` so every generated `../_shared/`
reference resolves inside the root a consumer home actually has. A codex install
populates only `.agents/skills`, never another provider's root. A discovered
`SKILL.md` path under that root proves the tree exists but not which host wrote it —
GitHub Copilot reads the same root (D-CP6, below), so a captured path is proof of an
installed Codex profile only together with the identity of the host that reported it.
The running model never selects the tree.

`tools/skill-mesh-discovery.ps1` is the ONE owner of that mapping (`'codex' =
'.agents/skills'`), enforced by a test that fails if any other tracked `.ps1` spells
a root literal in executable code. For a live Codex install the base it resolves
against is `$CODEX_EFFECTIVE_HOME`, and `tools/probe-codex-skills.ps1` is the ONE
resolver for that value.

**Every generated Codex `SKILL.md` must lead with a YAML frontmatter block**
containing `name` and `description`, exactly like the GPT profile. The canonical
`providers/codex.md` adapters carry no frontmatter of their own, so the builder
synthesizes it from the single per-skill `description` field in
`config/skill-manifest.json` — never re-authored per host — and places the provenance
header immediately after the closing `---`.

A root `AGENTS.md` is the **instruction adapter, not a skill registry**: it does not
contain or enumerate skill implementations. Instruction loading and skill discovery
are separate mechanisms — see the host-loading authority map
[`../host-discovery.md`](../host-discovery.md). The inspector and the bring-up probe
both refuse to correlate the two, so "codex root present but `AGENTS.md` absent" is
not a defect and is not warned about.

### The install target is also a Copilot discovery root (D-CP6)

Two distinct facts about `.agents/skills`, and collapsing them into one is the
misreading this section exists to prevent:

1. It is skill-mesh's **codex install target** — the root this package writes into
   when `-Provider codex` is given (`tools/skill-mesh-discovery.ps1`).
2. It is **also** one of GitHub Copilot CLI's native project discovery roots — a root
   Copilot scans whether or not skill-mesh ever wrote there (proven against a live
   Copilot CLI v1.0.77 in Step 43, #58).

The same literal string serves both, deliberately: design decision **D-CP6** kept one
root and accepted the collision rather than minting a second path or pre-building a
guard, and that decision is gated against the code in `tests/distributions/`.

The consequence, stated plainly: **a codex install is enumerable by GitHub Copilot
whenever the codex home is also the directory Copilot treats as its project** — and
that is expected behavior rather than a collision defect. The condition is
load-bearing: `.agents/skills` is one of Copilot's *project* discovery roots and its
personal root is `~/.copilot/skills`, so a codex home Copilot never treats as a
project is not enumerated. It is measured, not assumed, and both measurements ran
with the install home as Copilot's project cwd — Copilot CLI 1.0.77 enumerated all 5
pilot codex packages from the shared root, and the re-check on Copilot CLI 1.0.80
still enumerated all 47 packages installed at that time, exact-set match. Only that
outcome is proven: no scan-order guarantee has been established for the shared root,
so a skill name present in more than one installed profile has no proven winner, and
each observation is bound to the Copilot version it was measured against and
re-checked on the next upgrade.

Because two hosts meet at one path, **the presence of `.agents/skills` is not
evidence of which host wrote it.** A reader who learns only that Copilot scans that
root has stopped one fact short.

## Transport / authentication

| Transport | When | Requirement |
|---|---|---|
| Host-native execution | default inside the Codex CLI | none — the host provides the model |

`config/skill-manifest.json` records codex as `"host": "OpenAI Codex CLI"` with
`"transport_default": "host-native"` — the same transport class as Claude, and not
GPT's `"copilot"`. There is no second transport and no transport credential: **no
`OPENAI_API_KEY` is used or needed**, and none is attached to codex anywhere in this
package. `OPENAI_API_KEY` appears here only as the GPT router's optional
direct-OpenAI fallback and in the manifest's `excluded_non_identity` list, where a
credential is explicitly held to identify a *transport* and never the *active host*
(see [`../architecture.md`](../architecture.md) section 5).

Codex-side sign-in is between the operator and their Codex CLI; this package neither
performs it nor depends on it. The tooling **never invokes the codex CLI** — not to
detect a version, not to confirm a path. `tools/probe-codex-skills.ps1` is filesystem
+ environment only and its report carries `codex_cli_invoked = $false`, so bring-up
is safe on a machine where Codex is not installed.

## Bring-up

Read-only first. The probe resolves the effective home and reports root state, ledger
state, and instruction-file evidence class without writing anything:

```powershell
powershell -File tools\probe-codex-skills.ps1
```

Its only parameters are `-Home` (aliases `-Destination`, `-CodexHome`), `-Format
text|json`, and `-AbsolutePaths`; there is no `-Provider` and no write mode at all.
Exit 0 means the home resolved and the report is complete; exit 2 means resolution
stopped — `HOME`/`USERPROFILE` disagreement, neither set, a non-absolute value, or an
unusable `-Home`. It never prompts and never mutates.

Rehearse the install against a disposable home before touching a consumer home:

```powershell
powershell -File tools\install-skill-mesh.ps1 -Provider codex -Home <rehearsal-home>
```

```powershell
powershell -File tools\inspect-host-install.ps1 -Home <rehearsal-home>
```

`install-skill-mesh.ps1` takes `-Provider`/`-Profile` (`claude|gpt|codex`, mandatory)
and `-Home`/`-Destination` (mandatory), plus `-DistDir`, `-Force`, `-ForceShared`,
`-BackupDir`, and `-Uninstall`. A codex install into a clean or already
skill-mesh-owned root needs no `-Force`: `-Force` (or the payload-scoped
`-ForceShared`) is what takes ownership of a pre-existing *foreign* file at a
colliding target path, and either one additionally **requires `-BackupDir`** — a
take-ownership run without it is refused before anything is written. Because
`.agents/skills` is a shared root, a foreign collision there is likelier than in a
private one, and the installer's answer to one is a refusal that leaves prior state
unchanged, never a silent overwrite.

`inspect-host-install.ps1` takes `-Home`/`-Destination` (required), `-Format
text|json`, and `-AbsolutePaths` — it has **no** `-Provider` parameter, and it reports
provenance-header shape, per-root owned/foreign counts, and ledger state without
comparing installed bytes to generated bytes.

To build the profile explicitly rather than letting the installer stage one:

```powershell
powershell -File tools\build-distributions.ps1 -Provider codex
```

`-Provider` there accepts `claude|gpt|codex|both|all`, and **`both` — the default —
still means exactly claude + gpt**. A pre-built `-DistDir` intended to serve a codex
install must therefore have been built with `-Provider codex` or `-Provider all`.

## Capabilities

A Codex adapter loads the core in full and maps host abstractions onto it; it never
weakens a gate the core defines. The mapping is capability-conditioned because Codex
hosts do not all expose the same orchestration surface. Five recurring host-binding
questions separate it from its Claude and GPT siblings:

- **Host-conditioned agent dispatch.** An embedded Codex host can expose explicit
  fresh-context dispatch even though an ordinary CLI host does not. Support is proven
  from the active callable schema plus a non-mutating no-inheritance probe, never from
  the provider or function name. A core with no single-context fallback runs only when
  its adapter maps that proven primitive; otherwise it halts `required_tool_missing`.
  Shared filesystem/tools are compatible with conversational isolation and do not
  claim an OS security boundary. Where a phase verdict is authenticated, fresh child
  dispatch, opaque parent key retention, and a host-caller-scoped, strict JSON-lines
  parent-only sign/write service are separately probed capability gates.
- **No Artifact tool.** Every artifact a core asks to publish is written as a FILE
  under the repository (or the operator-named output path) and reported by path.
- **No Codex tier peer.** `config/model-tier-map.json` maps Claude tier names onto
  GPT peers and declares no Codex entry, so a tier resolves to the closest capability
  the configured Codex model actually provides — never by weakening a gate to fit a
  smaller model.
- **No guaranteed stable session identity.** Session identity comes from Codex's own
  conventions through the abstract session-I/O layer; where the host exposes none,
  the adapter follows the documented schema fallback and never fabricates one.
- **No Claude-Code window primitives.** `/goal`, `/clear`, and Stop hooks have no
  Codex equivalent. An adapter emits the core's continue-command block verbatim as
  operator text for a window that supports it and never claims a hook is armed; the
  durable task-state writes (`current.md`, the rendered `handoff-prompt.md`) are the
  cross-host handoff, and a closure loop simply keeps driving in-session until its
  own termination check passes.

**Where the active Codex host or the skill's adapter lacks a primitive the core
requires and documents no fallback, the adapter halts visibly with
`required_tool_missing`.** The authoring rule of record is that such wrappers halt at
the isolated dispatch instead of weakening the producer-never-grades-itself gate.
Documenting a single-context fallback for one of those cores would be a CORE change
with its own review, never a wrapper edit. An unavailable or unproven capability is
its own reported result, never a silently degraded one.

## Known limitations

- **Agent-dependent behavior varies by host and adapter.** On an ordinary CLI host
  without fresh-context dispatch, the 13 previously enumerated paths still halt at
  their required isolated arm. On a capable embedded host, `build-step` runs only
  after its explicit no-history probe passes; `build-phase` additionally requires a
  fresh per-step opaque parent HMAC state and a usable caller-scoped parent-only verdict
  service. The other 12 adapters from that historical set
  (`review-deep`, `review-gauntlet`, `skill-iterate`, `skill-evolve`, `test-prune`,
  `tier-escalate`, `tier-offload`, `judge-ui`, `research-prospect`, `user-brainstorm`,
  `user-debug`, and `user-learn`) retain their current mappings pending their own
  capability audits. This repair does not silently generalize one proven mapping.
- **Visual verdicts are unreachable, so `--ui` degrades downstream.** `judge-motion`
  is Claude-native and absent from this profile, and `judge-ui` halts at its
  vision-judge dispatch, so `user-uat --ui` surfaces `required_tool_missing` naming
  the judge and lands the step in `Needs you` — never a self-viewed visual verdict.
  `review-uat` delegates `--exec` to `/user-uat` and `--ui` to `/judge-ui` and halts
  visibly with `required_tool_missing` naming whichever downstream skill is
  unavailable, rather than executing its steps inline or dropping the flag.
  `skill-eval-setup` authors natively; where the corpus generator script's sub-agent
  backend is absent it uses the core's documented non-dispatch modes (`--dry-run`,
  `--verify-only`, hand-crafted examples) and reports which mode ran, with the
  script-deterministic verification gate unchanged in every mode.
- **Orchestrator outcome follows the three capability gates.** `build-phase` can run a
  code step on a host that proves fresh build-step children, fresh per-step opaque
  parent key retention, and a parent-only verdict service. It halts `required_tool_missing` before dispatch when any is
  absent or inconclusive. `build-queue` retains its own park-not-abort behavior for
  downstream halts.
- **`user-afterparty` sweeps with holes.** `context-slim` is Claude-native and absent
  from the codex profile; `test-prune` and the tier-drift pair halt. Each lands in
  the one report as its reason code rather than being reimplemented inline.
- **`goblin-do` and `goblin-suggest` need the `claude` CLI.** Their Workflow session
  path is unavailable, so they ride their cores' documented CLI fallback; absent the
  `claude` CLI or its OAuth token they halt `required_tool_missing` rather than
  degrading to an unreviewed edit or a self-judged generation.
- **`citation-sweep` degrades serially instead of halting.** Of the 15 codex-eligible
  `sub-agent` skills it is the only one whose adapter substitutes an in-session serial
  rail: it runs the per-artifact reviews sequentially under the core's unchanged terse
  per-artifact return contract, on the wrapper's stated reading that boundedness, not
  judge independence, is what this particular fan-out buys.
- **No router dispatch and no host auto-detection** — see the two sections below.
- **The whole-catalog listing budget is the binding constraint.** Codex's initial
  skill list is capped at 2% of the selected model's context, or 8,000 characters
  when the context size is unknown, and that budget covers the whole catalog
  including paths. Exceeding it risks skills being silently omitted or truncated from
  the listing, which no test of the emitted bytes would notice. Paying for the Step
  10 promotions required trimming manifest descriptions catalog-wide;
  `tests/package-integrity/test_codex_budgets.py` asserts the estimate with bounded
  headroom, and a live Codex CLI has listed 47 skills without truncation but has not
  been re-measured at 54.
- **A `both` distribution does not ship codex.** `both` is still `release.ps1`'s
  default, so shipping codex in a release means asking for it — `-Provider all`, or
  `-Provider codex` for a codex-only artifact. Legacy migration is stricter: the
  migrator binds every *declared* provider and refuses a partial artifact with
  `MISSING_PROFILE` (exit 2), so it requires a `-Provider all` distribution — see
  [`../migration.md`](../migration.md).
- **Every observation is on one Codex CLI version.** Parity targets the *installed*
  CLI (design decision D-CP7), and every recorded milestone ran against codex-cli
  0.147.0 — the same pin the format research came from — so the frontmatter shape,
  the `.agents/skills` placement, and the budget assumptions are confirmed on that
  pin and remain unproven on newer versions. Session mode is a live variable between
  runs too: one milestone was interactive, another was driven through `codex exec`.
- **Daily-use acceptance is not yet proven.** The delivery record carries `M3:
  PENDING` — no real Codex-hosted working sessions have occurred outside the scripted
  milestone runs, so the everyday-quality claim is deliberately left open.

## Host-metadata detection

`-Provider auto` cannot select codex. `config/skill-manifest.json` declares
`host_metadata_sources` markers for `claude` and `gpt` only, and `runtime/providers/`
ships a Claude host adapter and a Copilot host adapter with no codex counterpart, so
codex is chosen explicitly at install time with `-Provider codex`.

## Explicit routing

There is no router dispatch for codex. `runtime/skill-router.ps1` declares
`-Provider` as `auto|claude|gpt|local` and `runtime/` carries no codex reference at
all, so `codex` is not a legal router argument. A codex profile is reached through
host-native discovery instead, which the authority map keeps strictly distinct from
router dispatch.

## See also

[`README.md`](README.md) — this directory's index — for the three-provider capability
and authentication matrices; [`claude.md`](claude.md) and [`gpt.md`](gpt.md) for the
Claude and GPT/Copilot counterparts; [`../host-discovery.md`](../host-discovery.md)
for the host-loading authority map; [`../parity-deltas.md`](../parity-deltas.md) for
the recorded milestone evidence and the per-skill delta rows cited above;
[`../codex-parity-delivery-plan.md`](../codex-parity-delivery-plan.md) for D-CP1,
D-CP6, and D-CP7; [`../migration.md`](../migration.md) for the pre-migration →
provider-neutral transition; and the repository [`../../README.md`](../../README.md)
for the provider and discovery-location overview.
