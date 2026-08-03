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
`.github/skills` root for GPT, the `.claude/skills` root for Claude — never from
the fact that a model produced a plausible answer.

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

- **Claude Code discovers each skill at `<install-home>/.claude/skills/<skill>/SKILL.md`.**
- **GitHub Copilot CLI discovers each skill at `<install-home>/.github/skills/<skill>/SKILL.md`** —
  the target this package installs the GPT profile to.

**GitHub Copilot CLI's native project discovery roots** are `.github/skills/`,
`.agents/skills/`, and `.claude/skills/`; its **personal** root is
`~/.copilot/skills/`. Step 43 (#58) proved this against a live Copilot CLI v1.0.77.
This package installs the GPT profile to the conventional project root
`.github/skills/`. Note that `.claude/skills/` is **also** a Copilot discovery
root, so a consumer with both profiles installed exposes each skill to Copilot at
both `.claude/skills` and `.github/skills` — that both-profile collision is proven
and resolved in the cutover plan's Step 45 before any live both-profile migration.

**Every generated `SKILL.md` must lead with a YAML frontmatter block** containing at
least `name` and `description`; GitHub Copilot CLI rejects a `SKILL.md` without it
(`missing or malformed YAML frontmatter`). The builder emits the GPT `SKILL.md` with
that frontmatter first — `name` and `description` sourced from the single per-skill
`description` field in [`../config/skill-manifest.json`](../config/skill-manifest.json)
— and places the provenance header immediately after the closing `---`.

The **retired** project-relative `.copilot/skills` target (the originally-assumed GPT
root, before the Step 43 proof) is **NOT** a GitHub Copilot CLI discovery root: a
planted skill there returned `NOT REGISTERED`. It has been retired; no current
install writes to it, and a pre-retarget `.copilot/skills` install is treated only as
a legacy wrong-target to migrate off, never as a live discovery root.

The two install targets are provider-specific and are never swapped: a Claude install
populates `.claude/skills`, and a GPT install populates `.github/skills`. See the
per-host guides [`providers/claude.md`](providers/claude.md) and
[`providers/gpt.md`](providers/gpt.md). This table matches the discovery-location
table in the repository [`README.md`](../README.md) ("Providers & installation") and
the installer's own target map (`install-skill-mesh.ps1`: `claude -> .claude/skills`,
`gpt -> .github/skills`).

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
  (`.claude/skills`, `.github/skills`) above.
- The installer proves this structurally: it writes skill trees **only** under the
  install targets (`<Home>/.claude/skills/<skill>/…`, `<Home>/.github/skills/<skill>/…`)
  and never writes a `CLAUDE.md` or `AGENTS.md`. Instruction files and skill
  implementations are produced and located by different mechanisms.
- A host that runtime-injects a `CLAUDE.md` (for example a Copilot CLI that exposes
  a host-side skill registry from it) is exhibiting *host integration*, not native
  skill installation. That behavior is data about instruction loading, never proof
  that a `.github/skills` profile is installed (cutover plan §2, §8).

The public package owns these *mechanics* only; it never ships the *contents* of a
private `CLAUDE.md` or a personalized `AGENTS.md` (cutover plan §6, "Public package
owns mechanics; consumer owns private instructions"). No private workspace paths or
policies belong in this document.

## Router dispatch — explicit, not implicit

**The router is explicit, not implicit.** `runtime/skill-router.ps1`
([`../runtime/skill-router.ps1`](../runtime/skill-router.ps1)) is an **explicit
cross-provider and headless execution path — not the prerequisite for native skill
invocation** (cutover plan §6, "Host binding is the normal path"; architecture.md
§5). Two independent mechanisms select which adapter executes, and binding is
primary:

- **Host-native binding (primary).** When a host discovers a skill through its own
  scan of `.claude/skills` / `.github/skills`, the bound adapter is already
  correct and **no router runs** (architecture.md §5.1, and §6: "host-native
  discovery (no router) → Loads the bound adapter directly → primary path").
- **Router dispatch (secondary, explicit).** The router is reached only for
  explicit cross-provider selection (`-Provider claude|gpt|local`) or headless
  execution (architecture.md §5.2). It is a deliberate, named invocation — never an
  implicit precondition that native discovery silently depends on.

Treating the router as a prerequisite for native invocation is rejected precisely
because it obscures which provider adapter executed and is not a portable
installation contract (cutover plan §6, "Host binding is the normal path").

## Why the separation matters (summary)

| Question | Answered by | **Not** answered by |
|---|---|---|
| Which model produced the text? | the running model | the discovery root, the instruction file, or the router |
| Which skill tree was discovered? | the captured `SKILL.md` path (`.claude/skills` for Claude, `.github/skills` for GPT) | the model's output |
| Are workspace instructions loaded? | the host's instruction-file convention (`CLAUDE.md` / `AGENTS.md`) | the presence of a skill implementation |
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
  [`providers/README.md`](providers/README.md) — per-host binding, discovery root, capabilities.
- [`host-native-discovery-cutover-plan.md`](host-native-discovery-cutover-plan.md) §2, §6, §8 — the design authority for this map.
- [`../config/skill-manifest.json`](../config/skill-manifest.json) — the single source of truth for which skills are published and each skill's frontmatter `description`.
