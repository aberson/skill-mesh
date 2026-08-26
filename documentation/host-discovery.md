# Host-Loading Authority Map

How a host finds and runs a skill-mesh skill involves **three separate mechanisms**.
They are **distinct and not interchangeable**: satisfying one does not satisfy
another, and evidence of one is never evidence of another. Conflating them is the
exact failure this document exists to kill — a GPT model that answers a prompt
"correctly" is routinely mistaken for a correctly installed GPT profile, when in
fact model output proves nothing about which skill tree, if any, was discovered.

The three mechanisms are:

| Mechanism | What it is | What it is **not** |
|---|---|---|
| Workspace instruction injection | The host loads a root instruction file (`CLAUDE.md` / `AGENTS.md`) as an **instruction adapter**. | It is **not** a skill registry — it does not contain or enumerate skill implementations. |
| Host-native skill discovery | The host scans its own discovery root and finds each installed skill's generated `SKILL.md`. | It is **not** decided by which model runs — the host and its installed adapter select the discovery root. |
| Router dispatch | An **explicit** cross-provider / headless execution path invoked as `runtime/skill-router.ps1`. | It is **not** the prerequisite for native skill invocation; native discovery runs with no router. |

Because these three are separate, they must be proven separately. The rest of this
document states each precisely and grounds it in the package's own behavior.

## Model choice does not select a skill tree

**Model choice does not select a skill tree.** The host and its installed adapter
select the discovery root; the model does not. Provider selection ("which adapter
executed") and the model that ran it are distinct axes — the cutover plan defines
*provider adapter identity* as "which provider wrapper executed a skill … as
distinct from the model that ran it"
([host-native-discovery-cutover-plan.md](host-native-discovery-cutover-plan.md) §2).

The practical consequence: **a GPT model answering correctly is not evidence of a
correctly installed GPT profile.** A GPT model can invoke skills through host
runtime injection even when a native `.github/skills` tree is absent (see the
"Runtime registry masks missing GPT install" risk in the cutover plan §8). Native
proof therefore comes only from capturing the discovered `SKILL.md` path — the
`.github/skills` root for GPT, the `.claude/skills` root for Claude, the
`.agents/skills` root for Codex — never from the fact that a model produced a
plausible answer. Codex sharpens that rule rather than relaxing it: `.agents/skills`
is a root two different hosts read (below), so a captured path names the tree and not
the host — the capture is proof only together with the identity of the host that
reported it.

## Host-native skill discovery — the install-target and discovery roots

Normal installation writes exactly one provider adapter into each host's own
discovery layout, and the host discovers the skill directly from that root with no
runtime provider decision (architecture.md §5.1). The installer
([`../tools/install-skill-mesh.ps1`](../tools/install-skill-mesh.ps1)) writes each
provider to a provider-specific **install target**:

| Provider | Host | Native install target |
|---|---|---|
| Claude | Claude Code | `<install-home>/.claude/skills/<skill>/` |
| GPT | GitHub Copilot CLI | `<install-home>/.github/skills/<skill>/` |
| Codex | OpenAI Codex CLI | `<install-home>/.agents/skills/<skill>/` |

- **Claude Code discovers each skill at `<install-home>/.claude/skills/<skill>/SKILL.md`.**
- **GitHub Copilot CLI discovers each skill at `<install-home>/.github/skills/<skill>/SKILL.md`** —
  the target this package installs the GPT profile to.
- **OpenAI Codex CLI discovers each skill at `<install-home>/.agents/skills/<skill>/SKILL.md`** —
  the target this package installs the codex profile to. For a live Codex install the
  `-Home` to pass is the effective Codex home resolved by
  [`../tools/probe-codex-skills.ps1`](../tools/probe-codex-skills.ps1), the one resolver
  for that value, never spelled by hand.

**GitHub Copilot CLI's native project discovery roots** are `.github/skills/`,
`.agents/skills/`, and `.claude/skills/`; its **personal** root is
`~/.copilot/skills/`. Step 43 (#58) proved this against a live Copilot CLI v1.0.77.
This package installs the GPT profile to the conventional project root
`.github/skills/`. Note that `.claude/skills/` is **also** a Copilot discovery
root, so a consumer with the Claude and GPT profiles both installed exposes each
skill to Copilot at both `.claude/skills` and `.github/skills`.
Step 45 (#67) resolved that collision against a live
GitHub Copilot CLI v1.0.77: `copilot skill list` dedups by name, and `.github/skills` precedes
`.claude/skills` in Copilot's discovery order, so the GPT profile is a stable ordering-based winner
and is never shadowed by the Claude profile. Installing both of those profiles is therefore safe.
One M1 observation qualifies the `.claude/skills` half of that reach rather than the ordering
proof: from the same codex install home, Copilot did **not** enumerate a junction-backed
`.claude/skills` tree, and the mechanism was not established — recorded as an observation only
([`parity-deltas.md`](parity-deltas.md)).

`.agents/skills` carries **two distinct roles, and they are never the same claim**:

- **(a) It is this package's codex install target.** A codex install writes the
  generated codex profile there (`install-skill-mesh.ps1`: `codex -> .agents/skills`),
  and [`../tools/skill-mesh-discovery.ps1`](../tools/skill-mesh-discovery.ps1)'s
  `Get-SkillMeshDiscoveryRoots` is the sole owner of that mapping.
- **(b) It is also one of GitHub Copilot CLI's native project discovery roots** —
  listed above, and scanned by Copilot as an active alternate long before this
  package ever wrote to it.

Both roles hold of the **same literal string**, deliberately: design decision
**D-CP6** ([`codex-parity-delivery-plan.md`](codex-parity-delivery-plan.md) §6) left
the two names resolving to one directory and deferred any guard to measured evidence
rather than pre-building one. Two consequences follow, and **both are expected
behavior, not a collision defect**. First, a codex install **is** enumerable by
Copilot whenever the codex home is also the directory Copilot treats as its project
— measured rather than assumed (all 5 pilot packages on Copilot CLI v1.0.77, and all
47 then installed on v1.0.80, exact-set-matched; [`parity-deltas.md`](parity-deltas.md)
— the codex catalog has since grown to 54 and has not been re-measured at that scale),
which is the evidence the D-CP6 `accept` rests on and why no collision guard is built.
Second, the **presence** of an `.agents/skills` tree is never evidence of which host
wrote it; that question is answered by the generated files' provenance marker and the
installer's ownership ledger
([`../tools/inspect-host-install.ps1`](../tools/inspect-host-install.ps1)), never by
the root's name. Note also that the Step 45 ordering proof above covers only
`.github/skills` versus `.claude/skills`: where `.agents/skills` falls in Copilot's
discovery order is not part of that proof and is stated here as unproven.

**Every generated `SKILL.md` must lead with a YAML frontmatter block** containing at
least `name` and `description`; GitHub Copilot CLI rejects a `SKILL.md` without it
(`missing or malformed YAML frontmatter`), and skill-mesh's 0.147.0-pinned Codex format
research records the same unit shape for Codex — a skill directory whose `SKILL.md`
leads with one ([`codex-parity-delivery-plan.md`](codex-parity-delivery-plan.md) §2);
unlike Copilot, Codex has not been measured rejecting a frontmatter-less `SKILL.md`.
One synthesizer in the builder emits that frontmatter first for **both** the GPT and
the codex `SKILL.md` (neither canonical adapter carries frontmatter of its own) —
`name` from the manifest record's `name` and `description` from its single per-skill
`description` field in [`../config/skill-manifest.json`](../config/skill-manifest.json)
— and places the provenance header immediately after the closing `---`.

The **retired** project-relative `.copilot/skills` target (the originally-assumed GPT
root, before the Step 43 proof) is **NOT** a GitHub Copilot CLI discovery root: a
planted skill there returned `NOT REGISTERED`. It has been retired; no current
install writes to it, and a pre-retarget `.copilot/skills` install is treated only as
a legacy wrong-target to migrate off, never as a live discovery root.

The install targets are provider-specific and are never swapped: a Claude install
populates `.claude/skills`, a GPT install populates `.github/skills`, and a codex
install populates `.agents/skills`. See the per-host guides
[`providers/claude.md`](providers/claude.md), [`providers/gpt.md`](providers/gpt.md),
and [`providers/codex.md`](providers/codex.md). This table matches the
discovery-location table in the repository [`README.md`](../README.md) ("Providers &
installation") and the installer's own target map (`install-skill-mesh.ps1`:
`claude -> .claude/skills`, `gpt -> .github/skills`, `codex -> .agents/skills`), whose
single owner is `skill-mesh-discovery.ps1`.

The GPT root (`.github/skills`) plus the YAML-frontmatter format is the assumption
every later cutover step depends on; the cutover plan proved it against a live GitHub
Copilot CLI session (discovered via `copilot skill list` and invoked end-to-end)
before any inspection or migration tooling was built on it (cutover plan §6, "Host
binding is the normal path").

## Workspace instruction injection — `CLAUDE.md` and `AGENTS.md` roles

`CLAUDE.md` and `AGENTS.md` are **instruction adapters, not skill registries**
(cutover plan §6, "`AGENTS.md` and `CLAUDE.md` are instruction adapters, not skill
registries"). Concretely:

- **Neither file enumerates or embeds skill implementations.** A workspace
  instruction file carries workspace conventions and points a host at its
  behavior; it **does not contain skill implementations**, and it is not scanned as
  a skill catalog. Skills live only in the provider discovery directories
  (`.claude/skills`, `.github/skills`, `.agents/skills`) above.
- The installer proves this structurally: it writes skill trees **only** under the
  install targets (`<Home>/.claude/skills/<skill>/…`, `<Home>/.github/skills/<skill>/…`,
  `<Home>/.agents/skills/<skill>/…`), with the shared support payload landing inside
  those same roots as a sibling of the skill dirs
  (`<Home>/.claude/skills/_shared/<asset>`, and so on for the other two), and never
  writes a `CLAUDE.md` or an `AGENTS.md` — the only file it writes outside a discovery
  root is its own ownership ledger, `<Home>/.skill-mesh-install.json`. Instruction
  files and skill implementations are produced and located by different mechanisms.
- A host that runtime-injects a `CLAUDE.md` (for example a Copilot CLI that exposes
  a host-side skill registry from it) is exhibiting *host integration*, not native
  skill installation. That behavior is data about instruction loading, never proof
  that a `.github/skills` profile is installed (cutover plan §2, §8).

The public package owns these *mechanics* only; it never ships the *contents* of a
private `CLAUDE.md` or a personalized `AGENTS.md` (cutover plan §6, "Public package
owns mechanics; consumer owns private instructions"). No private workspace paths or
policies belong in this document.

### The inverted shape — content in `AGENTS.md`, `CLAUDE.md` as a one-line import

A project may keep its instruction content in `AGENTS.md` and reduce `CLAUDE.md` to
a single line, `@AGENTS.md`. This is a rearrangement **within** workspace
instruction injection and nothing more: both files stay instruction adapters, neither
gains a skill implementation or an enumeration of one, and no discovery root is
affected. A project in the inverted shape is discovered exactly as before — the shape
decides which file carries the prose, never which tree a host scans.

Which file each of the two measured hosts opens differs, and that is the part this map
owns: Claude Code reads `CLAUDE.md`, OpenAI Codex CLI reads `AGENTS.md`. Both
reach the same content, by different routes, from one copy of it.

Which delivery form actually carries content on which host — and therefore why the
content sits in `AGENTS.md` rather than behind a pointer — is the measurement, not this
map's to state. It is owned by
[`codex-instruction-delivery.md`](codex-instruction-delivery.md), together with the
version pin it was taken against and the read-only `codex debug prompt-input`
reproduction, and is deliberately not restated here: a second carrier of those verdicts
would silently keep the old answer the day a host changes.

**GitHub Copilot CLI is not covered by that measurement.** It appears throughout this
document as a discovery host, and this map's design authority records its
instruction-loading behavior as version-dependent
([`host-native-discovery-cutover-plan.md`](host-native-discovery-cutover-plan.md) §8),
which is why the runtime-injection note above is worded as a possibility rather than a
finding. Its behavior on this axis was not measured — so no claim about what it loads
from the inverted shape may be read off this page.

Whether a given project may be *put* into the shape, and which of the two files a
lifecycle skill is permitted to write, is a separate normative contract with its own
single owner: see the Instruction-file contract in plan-init/core.md
([`../skills/plan-init/core.md`](../skills/plan-init/core.md)).

Two axes stay apart across the whole arrangement, in the exact sense the top of this
document sets out:

- **A skill is still never found through an instruction file.** An inverted `AGENTS.md`
  is a longer instruction adapter, not a registry; the discovery roots above remain the
  only places a `SKILL.md` is found.
- **The two are proven by different evidence, and neither substitutes for the other.**
  That a project's instruction content reached a host is proven by the host's prompt
  payload (on Codex, the JSON from `codex debug prompt-input`). That a skill tree was
  discovered is proven by the captured `SKILL.md` path. A host that loaded the content
  may have no profile installed, and an installed profile says nothing about whether
  the content was delivered.

## Router dispatch — explicit, not implicit

**The router is explicit, not implicit.** `runtime/skill-router.ps1`
([`../runtime/skill-router.ps1`](../runtime/skill-router.ps1)) is an **explicit
cross-provider and headless execution path — not the prerequisite for native skill
invocation** (cutover plan §6, "Host binding is the normal path"; architecture.md
§5). Two independent mechanisms select which adapter executes, and binding is
primary:

- **Host-native binding (primary).** When a host discovers a skill through its own
  scan of `.claude/skills` / `.github/skills` / `.agents/skills`, the bound adapter
  is already correct and **no router runs** (architecture.md §5.1, and §6:
  "host-native discovery (no router) → Loads the bound adapter directly → primary
  path").
- **Router dispatch (secondary, explicit).** The router is reached only for
  explicit cross-provider selection (`-Provider claude|gpt|local`) or headless
  execution (architecture.md §5.2). It is a deliberate, named invocation — never an
  implicit precondition that native discovery silently depends on.

The router's provider vocabulary is closed at `claude|gpt|local` (plus the `auto`
default) — the `-Provider` validation set in
[`../runtime/skill-router.ps1`](../runtime/skill-router.ps1). **Codex is an
install-and-discovery provider, not a router provider**: the router exposes no
`-Provider codex`, so a codex-bound skill always runs through host-native binding,
the primary path, and never through router dispatch. That asymmetry is the three
mechanisms being distinct, not a gap in the codex profile.

Treating the router as a prerequisite for native invocation is rejected precisely
because it obscures which provider adapter executed and is not a portable
installation contract (cutover plan §6, "Host binding is the normal path").

## Why the separation matters (summary)

| Question | Answered by | **Not** answered by |
|---|---|---|
| Which model produced the text? | the running model | the discovery root, the instruction file, or the router |
| Which skill tree was discovered? | the captured `SKILL.md` path (`.claude/skills` for Claude, `.github/skills` for GPT, `.agents/skills` for Codex) | the model's output |
| Which host wrote a discovered tree? | the generated file's provenance marker and the installer's ownership ledger (`inspect-host-install.ps1`) | the root's name — `.agents/skills` is the codex install target **and** a Copilot discovery root |
| Are workspace instructions loaded? | the host's instruction-file convention (`CLAUDE.md` / `AGENTS.md`) | the presence of a skill implementation |
| Did the project's instruction content actually reach the model? | the host's prompt payload (on Codex, `codex debug prompt-input`) — the row above says which file is read, only the payload says what arrived | a plausible model answer, or the file merely existing on disk |
| Was a skill run cross-provider / headless? | an explicit `runtime/skill-router.ps1` invocation | native host discovery |

A correct GPT model answer proves only the first row. A correctly installed GPT
profile is proven only by the second row's `.github/skills` path capture (with a
valid leading YAML frontmatter). Keeping these mechanisms distinct — and never
interchangeable — is what prevents a running model from being mistaken for a
correctly installed profile.

## See also

- [`README.md`](../README.md) — the top-level discovery-location table and install matrix.
- [`architecture.md`](architecture.md) §5 — host-native binding vs. runtime auto-detection.
- [`providers/claude.md`](providers/claude.md), [`providers/gpt.md`](providers/gpt.md),
  [`providers/codex.md`](providers/codex.md),
  [`providers/README.md`](providers/README.md) — per-host binding, discovery root, capabilities.
- [`codex-instruction-delivery.md`](codex-instruction-delivery.md) — the vendored measurement behind the inverted instruction-file shape: the per-host delivery table, the version pin it was taken against, and the read-only reproduction.
- [`host-native-discovery-cutover-plan.md`](host-native-discovery-cutover-plan.md) §2, §6, §8 — the design authority for this map.
- [`../config/skill-manifest.json`](../config/skill-manifest.json) — the single source of truth for which skills are published and each skill's frontmatter `description`.
