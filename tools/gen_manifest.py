"""Generate the manifest, expected fixture, and public skill inventory.

HERMETIC (Step 67). Generation reads nothing outside this repository. Every input is
either a checked-in constant below or the committed skills/<name>/ tree, so

    python tools/gen_manifest.py

reproduces all three committed artifacts with NO environment set and no argument passed.

WHY hermetic. This generator used to SCAN an external legacy root for each skill's
support assets (<coding-root>/.claude/{skills,skills-gpt}/<name>). The Step 50
consumer cutover overwrote that root with this package's OWN installed output, so a
regeneration fed skill-mesh's build product back into skill-mesh's manifest: 47 of
50 skills drifted, gaining 47 bogus `.claude/skills/<name>/core.md` sources and
losing `.claude/skills-gpt/judge-ui/calibration-notes.md`. An input that a
consumer-side install can mutate is not a generator input.

LINE ENDINGS. Generation emits UTF-8 LF on every host. Regeneration checks normalize
older checkout artifacts (strip BOM, then CRLF/CR -> LF), as release tooling does.

Authoritative structural data (names, status, local_capable, capabilities,
descriptions, support assets, provenance) is encoded here as checked-in constants.
Four of those sets are NON-DERIVABLE BY DESIGN and each states why at its own
definition: LOCAL_CAPABLE, SUB_AGENT, VISION, DESCRIPTIONS -- and so are the two
provenance sets, LEGACY_SPLIT and LEGACY_SINGLE_FILE. PORTABLE and NATIVE ARE derivable from the committed tree; they stay
spelled out as anti-silent-addition guards and are CHECKED against the tree by
`derived_skill_sets()` on every run. Codex membership is NOT a third roster (Phase CL
Step 111, decision CL-D14): every portable skill carries an adapter for every
provider in REQUIRED_PROVIDERS, so Codex membership is PORTABLE by construction.

TWO MODES, ONE PIPELINE. Both modes build all three payloads in memory and validate
them (`render_artifacts()` -> `validate_payloads()`) before anything else happens.

    python tools/gen_manifest.py            # regenerate: replace each file safely
    python tools/gen_manifest.py --check    # compare in memory; never writes

The normal mode then replaces the three files one at a time, each through a temporary
sibling and an atomic rename, so an interruption can never leave a truncated artifact.
It does NOT claim a cross-file transaction: an interruption between two replacements
leaves some files new and some old, and the next `--check` reports the old ones as
drift. `--check` exits 0 when all three match (line endings normalized) and 1 naming
each drifted file.

Re-run only when one of the constants below changes. There is no legacy-source
argument and no environment variable: an external source root is precisely what this
generator no longer reads. `--check` is a mode switch, not an input.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"

# ---- Authoritative structural constants (evidence-grounded) ----------------
#
# PORTABLE / NATIVE are the ONLY two roster sets here that the committed tree can also
# produce (a skill dir carrying core.md plus an adapter for every REQUIRED_PROVIDERS
# entry is portable; one with no core.md is provider-native). They are kept spelled out
# because the manifest's skill ORDER and the fixture's `portable` / `provider_native`
# arrays are this list verbatim, because a reader should be able to see the roster
# without walking a directory, and because a spelled roster is the anti-silent-addition
# guard: a skill directory that appears without being named here raises.
# `derived_skill_sets()` re-derives both from disk on every run and `build()` raises on
# inequality, so the spelled-out copy cannot drift away from the tree.

PORTABLE = [
    "build-phase", "build-queue", "build-step",
    "code-consigliere",
    "judge-ui",
    "lesson-harvest", "memory-distill", "plan-expedite",
    "plan-feature", "plan-init", "plan-merge", "plan-redline", "plan-review",
    "plan-wrap", "repo-init", "repo-sync", "repo-update",
    "repo-wrap", "research-prospect", "review-deep", "review-gauntlet",
    "review-proof", "review-uat", "session-wrap", "skill-eval-setup",
    "skill-evolve", "skill-iterate", "task-handoff", "test-prune",
    "tier-escalate", "tier-offload", "user-afterparty", "user-brainstorm",
    "user-build-route", "user-debug", "user-dr", "user-draft", "user-fermize",
    "user-gateway", "user-learn",
    "user-pm", "user-uat",
    "user-walkthrough", "user-wrap",
]

NATIVE = ["claude-oauth-auth", "context-slim"]

# THE INSTALLABLE-PROVIDER VOCABULARY, in manifest order. `codex` was added here at
# Phase CP Step 5, in the SAME commit as its discovery root. Read this before adding
# the next key -- the coupling below is a hard ordering constraint, not a style note.
#
# This block is not a list of providers the BUILDER can emit; the builder never reads
# it (tools/build-distributions.ps1 resolves each skill's adapter from the per-skill
# `providers` dict). It is the vocabulary that the INSTALL-side tools read to decide
# which discovery roots a home binds:
#   * tools/migrate-legacy-install.ps1 loads it into $script:KnownProviders and
#     New-MigrationPlan then requires a discovery root for EVERY name in it -- a
#     provider with no root is a hard UNKNOWN_PROVIDER_ROOT block that refuses the
#     whole migration (exit 2), in every consumer home.
#   * tools/inspect-host-install.ps1 loads the same vocabulary.
#
# THE RULE, which Step 3 deferred this key to obey: a name added here MUST land in the
# same commit as its entry in tools/skill-mesh-discovery.ps1
# (Get-SkillMeshDiscoveryRoots), the sole owner of the provider -> root map. Declaring
# a provider whose root that map lacks does not add a capability, it BREAKS the
# migrator until the map catches up. The regression guard for that exact sequencing
# defect is a TEST, not this comment: tests/distributions/test_codex_install_path.py ::
# test_migration_plan_has_no_unknown_provider_root_blocker_for_codex, with a
# red-on-garbage anchor that plants an undeclared provider and proves the blocker still
# fires.
#
# Insertion order is load-bearing: it is the key order of every record's emitted
# `providers` dict (json.dumps preserves insertion order), so the committed bytes read
# claude, gpt, codex. The builder reads adapters by name, never by position.
PROVIDERS = {
    "claude": {"host": "Claude Code", "transport_default": "host-native"},
    "gpt": {"host": "GitHub Copilot / GPT", "transport_default": "copilot"},
    "codex": {"host": "OpenAI Codex CLI", "transport_default": "host-native"},
}

# THE REQUIRED-PROVIDER SET, emitted as `portable_provider_contract.required` (Phase CL
# Step 111, decision CL-D4 as amended 2026-11-14 by operator decision). A portable
# skill carries an adapter for EVERY provider named here, in this order; a core with
# only some of them is an incomplete change and `derived_skill_sets()` raises on it.
# Widening the set is an explicit provider-rollout decision, never a side effect of
# adding a key to PROVIDERS above, which is why the two are separate constants.
#
# CODEX MEMBERSHIP IS DERIVED FROM THIS, NOT SPELLED (decision CL-D14). Until Step 111
# a separate CODEX roster listed the skills carrying providers/codex.md. Once codex is
# mandatory for every portable skill that list could only ever equal PORTABLE, and a
# second list for an equality the contract requires is a second authority that can
# disagree with the first. A skill is codex-capable because it is portable.
#
# GPT IS OPTIONAL. GitHub Copilot is no longer a supported host; V4-7 removes its
# adapters. Until then an existing providers/gpt.md is emitted as a `gpt` provider
# entry, and a portable skill without one carries no `gpt` key -- that is not drift.
REQUIRED_PROVIDERS = ("claude", "codex")
OPTIONAL_PROVIDERS = tuple(p for p in PROVIDERS if p not in REQUIRED_PROVIDERS)

# PROVENANCE: where each package came from (Phase CL Step 111, decision CL-D8).
#
# NON-DERIVABLE BY DESIGN. Provenance is history, and the history it records -- the
# retired workspace `.claude/skills` and `.claude/skills-gpt` trees this package was
# migrated out of -- no longer exists: the Step 50 consumer cutover overwrote it with
# this package's own installed output. Nothing in skills/<name>/ says where a package
# came from, so these sets are the record.
#
# BOTH SETS ARE CLOSED. No future skill can be migrated from a tree that is gone, so
# neither set may ever grow; a DELETE removes the name, and `build()` raises on a name
# no longer in the roster. Every skill NOT named in either set is `origin: canonical`
# with `migration: null` -- authored directly in Skill Mesh. That default is the
# truthful one for every CREATE from here on, and it is why a new skill cannot
# silently inherit fabricated legacy paths.
#
# Measured, not assumed, at Step 111 (2026-11-17): each legacy path the manifest named
# was looked up in the coding root's Git history. Every path below existed there before
# the cutover. For code-consigliere, user-build-route, user-dr and user-fermize the
# manifest used to name the same four legacy paths, and none of them had ever existed
# except as Skill Mesh's own install output, so those four are canonical.
#
# LEGACY_SPLIT: migrated from the GPT-era split layout -- a shared core at
# .claude/skills-gpt/<name>/SKILL-core.md, a Claude compatibility launcher at
# .claude/skills/<name>/SKILL.md, the substantive Claude adapter at
# .claude/skills/<name>/SKILL-claude.md, and a GPT package at
# .claude/skills-gpt/<name>/SKILL-gpt.md.
LEGACY_SPLIT = frozenset({
    "build-phase", "build-queue", "build-step",
    "judge-ui",
    "lesson-harvest", "memory-distill", "plan-expedite",
    "plan-feature", "plan-init", "plan-merge", "plan-redline", "plan-review",
    "plan-wrap", "repo-init", "repo-sync", "repo-update",
    "research-prospect", "review-deep", "review-gauntlet",
    "review-proof", "review-uat", "session-wrap", "skill-eval-setup",
    "skill-evolve", "skill-iterate", "task-handoff", "test-prune",
    "tier-escalate", "tier-offload", "user-afterparty", "user-brainstorm",
    "user-debug", "user-draft",
    "user-gateway", "user-learn",
    "user-pm", "user-uat",
    "user-walkthrough", "user-wrap",
})

# LEGACY_SINGLE_FILE: migrated from ONE Claude skill file,
# .claude/skills/<name>/SKILL.md, which was the substantive skill (no shared core, no
# launcher/adapter split, no GPT package). The two provider-native skills, plus
# repo-wrap: a workspace-custom Claude skill that Phase CP Step 10 (#127) promoted to a
# portable package, authoring its core and other adapters in the canonical tree.
LEGACY_SINGLE_FILE = frozenset({"claude-oauth-auth", "context-slim", "repo-wrap"})

ORIGIN_LEGACY = "legacy-migrated"
ORIGIN_CANONICAL = "canonical"
MIGRATION_KEYS = ("legacy_core", "legacy_claude_launcher",
                  "legacy_claude_adapter", "legacy_gpt")


def provenance(name: str) -> tuple[str, dict | None]:
    """Return (origin, migration) for one skill -- the ONE place both are decided."""
    if name in LEGACY_SPLIT:
        return ORIGIN_LEGACY, {
            "legacy_core": f".claude/skills-gpt/{name}/SKILL-core.md",
            "legacy_claude_launcher": f".claude/skills/{name}/SKILL.md",
            "legacy_claude_adapter": f".claude/skills/{name}/SKILL-claude.md",
            "legacy_gpt": f".claude/skills-gpt/{name}/SKILL-gpt.md",
        }
    if name in LEGACY_SINGLE_FILE:
        return ORIGIN_LEGACY, {
            "legacy_core": None,
            "legacy_claude_launcher": None,
            "legacy_claude_adapter": f".claude/skills/{name}/SKILL.md",
            "legacy_gpt": None,
        }
    return ORIGIN_CANONICAL, None


# local-capable=Y rows of .claude/references/model-mapping.md (authoritative table).
#
# NON-DERIVABLE BY DESIGN. Membership is a SEMANTIC judgment -- "this skill's work
# reduces to a bounded judge/grader single-call slice a local text-only model can
# serve" -- and nothing on disk states it. No file in skills/<name>/ carries the
# flag, and it is not implied by the tree's shape: it is merely DISJOINT from the
# sub-agent and vision sets, which is a consequence of the judgment, not a definition
# of it. Enumerating skills/ can therefore only reproduce this set by reading it from
# here. Phase 8 Step 55 (provider-expansion-plan.md) treats this set as its single
# source of truth; changing its membership or its shape belongs to that step.
#
# THE SEVEN PHASE CP STEP 10 PROMOTIONS ARE DELIBERATELY ABSENT, and their absence is
# a decision rather than an oversight. The stated evidence for membership is a
# local-capable=Y row in the legacy model-mapping table; none of the seven
# workspace-custom skills ever had a row there, so declaring any of them local-capable
# would be asserting a capability nothing measured. Absence here means "not yet
# assessed", which is also the safe reading -- local_capable=false costs a routing
# opportunity, while a wrong true costs a wrong host. Step 55 owns the assessment.
# (The citation sweep skill, since moved to the Citation Needed repository, was
# additionally excluded by construction: it was in SUB_AGENT, and sub-agent implies
# local_capable=false.)
LOCAL_CAPABLE = {
    "memory-distill", "plan-feature",
    "plan-init", "plan-merge", "plan-review", "plan-wrap",
    "repo-init", "repo-sync", "repo-update", "review-proof", "review-uat",
    "skill-eval-setup", "user-draft", "user-gateway",
    "user-pm", "user-walkthrough",
    "user-wrap",
}

# Skills whose core contract explicitly dispatches isolated fresh-context
# sub-agents / provider action children (Agent/Task primitive or Workflow
# agent() call) -- NOT merely a named-skill dispatch. Evidence: each skill's
# legacy SKILL-core.md / SKILL.md (see documentation/architecture.md sec 4).
#
# NON-DERIVABLE BY DESIGN. The distinction this set encodes -- an ISOLATED
# fresh-context agent versus an ordinary named-skill dispatch (`/other-skill`) -- is
# a reading of what each core MEANS, and the two are spelled with the same
# vocabulary in prose. A grep over skills/<name>/core.md cannot separate them, which
# is exactly why capability_semantics["sub-agent"] has to say so in words. The
# per-entry evidence quote stays beside each name so the judgment is auditable.
SUB_AGENT = {
    "build-step",        # "Spawn a sub-agent"; "Step 6 -- Spawn reviewer agents"
    "context-slim",      # "Spawn three parallel subagents using the Agent tool"
    "judge-ui",          # "dispatches an independent vision-judge sub-agent"
    "lesson-harvest",    # fresh strong reviewer gates public surfaces/dispositions
    "research-prospect", # "Fan out parallel Explore agents"
    "review-deep",       # "spawns six fresh-context sub-agents, one per lens"
    "review-gauntlet",   # "one fresh-context reviewer invocation for each lens"
    "skill-evolve",      # independent agent trials per variant
    "skill-iterate",     # "Dispatch ONE sub-agent" via fresh-context task
    "test-prune",        # "dispatch this phase as parallel Explore agents"
    "tier-escalate",     # fresh-context fan-out arms
    "tier-offload",      # fresh-context task API required
    "user-brainstorm",   # "One background sub-agent per investigation file"
    "user-debug",        # Step 2 and Option 4 require independent fresh-context arms
    "user-learn",        # "One background sub-agent per file"
    "user-uat",          # isolated deep assessor and strong final visual judge
}

# Skills with a documented native-vision dependency.
#
# NON-DERIVABLE BY DESIGN. "Requires a native image/vision capability" is a claim
# about the HOST capability a skill needs, not about any artifact in skills/<name>/.
# Several skills mention screenshots without needing to SEE one; judge-ui cannot
# render a verdict without it. Nothing on disk marks that difference.
#
# Unchanged by Phase CP Step 10: none of the seven promoted skills reads an image.
# The portfolio-block proposer rendered TOML from text sources, the citation family (since
# moved to the Citation Needed repository) grades prose,
# the goblin sweep wrapper (since retired) parsed JSON, and repo-wrap runs git -- all
# text-only end to end.
VISION = {"judge-ui"}

# Per-skill one-line `description`, the SINGLE source of truth for the SKILL.md
# frontmatter description the builder emits (GitHub Copilot CLI requires every
# generated SKILL.md to LEAD with a YAML frontmatter block carrying at least
# `name` + `description`; Step 44). Encoded here as a checked-in, evidence-grounded
# constant exactly like PORTABLE / NATIVE / LOCAL_CAPABLE above -- the evidence is
# each skill's own SKILL contract (its legacy `.claude/skills/<name>/SKILL.md`
# description and canonical core.md purpose).
#
# NON-DERIVABLE BY DESIGN, and measurably so: all committed
# skills/<name>/providers/claude.md files carry a `description:` that is LAUNCHER
# boilerplate ("Claude provider entry point for <name>; loads the canonical shared
# core."), which is not what the manifest publishes; and skills/<name>/providers/
# gpt.md carries no YAML frontmatter at all. Reading these values off disk would
# replace every published description with wrapper boilerplate. Deleting this
# constant additionally reds
# tests/distributions/test_distributions.py::test_manifest_description_matches_gen_manifest_source_of_truth,
# which pins the manifest against it.
#
# Baking it in (rather than re-reading
# the READ-ONLY legacy source) keeps the generator runnable WITHOUT that source and
# makes the committed manifest byte-reproducible: `config/skill-manifest.json`'s
# `description` field equals `DESCRIPTIONS[name]` for every record, so a regen never
# wipes a hand-tuned value. ASCII-only, one line, no newlines (kept safe for a YAML
# scalar; the builder still double-quotes when it emits the frontmatter).
DESCRIPTIONS = {
    "build-phase": "Run every step of a plan phase through build-step in order, gating quality between steps.",
    "build-queue": "Run pending phase plans unattended, each in its own worktree; halts become issues.",
    "build-step": "Run one build step: an agent writes it, isolated reviewers gate it, it merges.",
    "code-consigliere": "Investigate a project's workflows and rationale, agree a change, hand off a build seed.",
    "claude-oauth-auth": "How to authenticate with Claude using a subscription OAuth token instead of an API key.",
    "context-slim": "Audit a project's auto-loaded context files and produce a prioritized progressive-disclosure plan to cut per-turn token cost.",
    "judge-ui": "Drive a web UI through a flow, screenshot it, and have a vision judge give a verdict.",
    "lesson-harvest": "Find un-codified regressions in git history and notes; output an independently reviewed preview.",
    "memory-distill": "Review recent feedback memories one at a time and surface the principles they point at.",
    "plan-expedite": "Chain plan-review, plan-wrap, repo-sync, and task-handoff into one prep step before build.",
    "plan-feature": "Plan a new feature or phase for an existing project by reading its code and docs.",
    "plan-init": "Guide creation of a new project plan through a structured conversation about stack and tooling.",
    "plan-merge": "Merge plans into one resolving overlap and sequencing; --trim proposes and applies cuts.",
    "plan-redline": "Render a plan as an operator proposal, marking each choice operator- or agent-picked.",
    "plan-review": "Review a plan for gaps, open decisions and risks, checking claims against the code.",
    "plan-wrap": "Check whether a plan is self-contained for a fresh model with no conversation history.",
    "repo-init": "Publish a local project to GitHub: git init, create remote, README, issues.",
    "repo-sync": "Sync GitHub issues to match a plan's structure with rich, fresh-context bodies.",
    "repo-update": "Post-phase docs and git update: refresh README and plan, commit, and push.",
    "repo-wrap": "Close out any repo by ownership class: owned project, coding root, third-party clone, backup.",
    "research-prospect": "Scan active projects and surface high-value research topics per project for hand-off.",
    "review-deep": "Six-lens code review (correctness, bugs, security, tests, style, plan fit) with evidence.",
    "review-gauntlet": "Lean multi-lens profile over review-deep's engine emitting a terse PASS/NEEDS-WORK verdict.",
    "review-proof": "Require primary-source verification before any claim in an answer.",
    "review-uat": "Refine a UAT script so every step is unambiguous and only real human checks stay human.",
    "session-wrap": "Session-transition front door: triage context, task state, and git, then act on the verdict.",
    "skill-eval-setup": "Generate an evaluation framework for a skill from its contract, plus a self-improvement loop.",
    "skill-evolve": "A/B-test skill variants in parallel worktrees and push the winner for review.",
    "skill-iterate": "Serial hill-climb every scorable skill autonomously, capped by wall-clock or iterations.",
    "task-handoff": "Checkpoint library: save session state and rebuild the current-task rollup.",
    "test-prune": "Audit a suite for redundant, trivial, or mock-theater tests; relocate sole-coverage ones.",
    "tier-escalate": "Find which load-bearing seed-artifact phase warrants a higher-tier model, and emit a map.",
    "tier-offload": "Find sub-tasks safe to offload to a local model; emit an inventory and router config.",
    "user-afterparty": "Milestone hygiene front door chaining the hygiene skills into one report plus cleanup.",
    "user-brainstorm": "Brainstorm a topic through gap-fill rounds, then write a reference doc set per topic.",
    "user-build-route": "Recommend pipeline, bounded goal, or direct task with rationale and a pasteable prompt; advice only.",
    "user-debug": "Diagnose and fix a bug end-to-end with forced primary-source investigation first.",
    "user-dr": "Theme-grouped decision register across plans and seeds; checks conflicts and records answers.",
    "user-fermize": "Weigh one complex build decision: a smaller useful milestone, what can wait, what to prove.",
    "user-draft": "Refine rough thoughts into a polished prompt or a ready-to-paste goal condition.",
    "user-gateway": "Turn an operator vent into routed, ledger-backed work with a seed per row.",
    "user-learn": "Scaffold a learning ramp: knowledge base, notebooks, exercises, progress tracker.",
    "user-pm": "PM-lens project overview: what shipped, what is planned, what is next, what could be cut.",
    "user-uat": "Run an already-clear UAT block, executing steps and auto-judging the mechanical checks.",
    "user-walkthrough": "Attended acceptance of a just-built tool: answer from primary source, fix small things live.",
    "user-wrap": "Return-moment front door: orient, get a keep-going-or-wrap verdict, and act on it.",
}

# Per-skill support assets, BAKED IN as a checked-in constant -- the same rationale
# DESCRIPTIONS above already gives, applied to the input that actually broke.
#
# These are the committed manifest's `support_assets` values verbatim, captured from
# the legacy source at Step 33. They are NOT re-derivable from the committed
# skills/<name>/ tree: 65 of the 66 dests do not exist there yet (the per-skill asset
# migration is a later step), so enumerating skills/<name>/ would silently ERASE 65
# declarations instead of reproducing them. That is why this is a constant and not a
# scan -- and scanning the ONE root that did hold them is what Step 67 removed,
# because the Step 50 cutover overwrote it.
#
# Encoded as (legacy_tree, relative_path) pairs so the two emitted fields have ONE
# source and cannot drift apart on the relative path they share:
#     source = .claude/<legacy_tree>/<name>/<rel>     (provenance into the retired
#              legacy layout, which the manifest's `legacy_migration_root` documents)
#     dest   = skills/<name>/<rel>                    (canonical package path)
# A trailing "/" on <rel> marks a directory asset, exactly as the committed manifest
# spells it. `legacy_tree` is "skills" for every entry but one: judge-ui's
# calibration-notes.md lived ONLY in the legacy GPT tree, and Step 62 vendored it to
# skills/judge-ui/calibration-notes.md, so that entry now resolves to a real tracked
# file (tests/package-integrity/test_manifest_contract.py asserts it is still here).
#
# Order within a skill is the committed order and is load-bearing for byte-identity.
# Phase CP Step 10's seven promotions were captured the same way, from the legacy
# .claude/skills/<name>/ tree each was promoted out of: the portfolio-block proposer's
# three scaffold assets (gone with that skill, v3 catalog cleanup Step 4) and
# the goblin sweep wrapper's evals/ directory (gone with it, v3 catalog cleanup Step 14),
# and an explicit empty list for the five that
# genuinely ship no assets.
# All skills carry a key -- an empty list where a skill has no assets -- so adding
# a skill without deciding its assets is a loud KeyError, never a silent empty record.
SUPPORT_ASSETS = {
    "build-phase": [("skills", "evals/")],
    "build-queue": [("skills", "evals/")],
    "build-step": [
        ("skills", "evals/"),
        ("skills", "scripts/"),
    ],
    "code-consigliere": [],
    "claude-oauth-auth": [("skills", "evals/")],
    "context-slim": [("skills", "evals/")],
    "judge-ui": [
        ("skills", "evals/"),
        ("skills-gpt", "calibration-notes.md"),
    ],
    "lesson-harvest": [("skills", "evals/")],
    "memory-distill": [("skills", "evals/")],
    "plan-expedite": [
        ("skills", "evals/"),
        ("skills", "test-fixtures/"),
    ],
    "plan-feature": [("skills", "evals/")],
    "plan-init": [("skills", "evals/")],
    "plan-merge": [("skills", "evals/")],
    "plan-redline": [
        ("skills", "evals/"),
        ("skills", "reference-proposal.html"),
    ],
    "plan-review": [("skills", "evals/")],
    "plan-wrap": [("skills", "evals/")],
    "repo-init": [("skills", "evals/")],
    "repo-sync": [("skills", "evals/")],
    "repo-update": [("skills", "evals/")],
    "repo-wrap": [],
    "research-prospect": [("skills", "evals/")],
    "review-deep": [
        ("skills", "evals/"),
        ("skills", "scripts/"),
    ],
    "review-gauntlet": [("skills", "evals/")],
    "review-proof": [("skills", "evals/")],
    "review-uat": [("skills", "evals/")],
    "session-wrap": [("skills", "evals/")],
    "skill-eval-setup": [
        ("skills", "evals/"),
        ("skills", "scripts/"),
    ],
    "skill-evolve": [("skills", "evals/")],
    "skill-iterate": [
        ("skills", "evals/"),
        ("skills", "scripts/"),
    ],
    "task-handoff": [],
    "test-prune": [("skills", "evals/")],
    "tier-escalate": [
        ("skills", "evals/"),
        ("skills", "sample-escalate-map.md"),
    ],
    "tier-offload": [
        ("skills", "sample-inventory.md"),
        ("skills", "sample-offload-config.json"),
        ("skills", "test_sample_config_loads.py"),
        ("skills", "test_taxonomy_osot.py"),
    ],
    "user-afterparty": [("skills", "scripts/")],
    "user-brainstorm": [("skills", "evals/")],
    "user-build-route": [],
    "user-debug": [("skills", "evals/")],
    "user-dr": [],
    "user-fermize": [],
    "user-draft": [("skills", "evals.seed/")],
    "user-gateway": [("skills", "evals/")],
    "user-learn": [("skills", "evals/")],
    "user-pm": [("skills", "evals/")],
    "user-uat": [("skills", "evals/")],
    "user-walkthrough": [("skills", "evals/")],
    "user-wrap": [("skills", "evals/")],
}

def skill_support_assets(name: str):
    """Return the (source, dest) support-asset records for one skill.

    Built from the single (legacy_tree, rel) pair in SUPPORT_ASSETS, so `source` and
    `dest` cannot disagree about the relative path they share.
    """
    return [{"source": f".claude/{tree}/{name}/{rel}",
             "dest": f"skills/{name}/{rel}"}
            for tree, rel in SUPPORT_ASSETS[name]]


class SkillSets(NamedTuple):
    """What the committed skills/ tree says, each list sorted.

    `optional` maps every OPTIONAL_PROVIDERS name to the portable skills that carry
    that adapter. There is deliberately no codex member: codex is required, so the
    codex-capable set IS `portable` (decision CL-D14).
    """
    portable: list
    native: list
    optional: dict


def derived_skill_sets(skills_dir: Path | None = None) -> SkillSets:
    """Enumerate the COMMITTED skills/ tree into a SkillSets.

    A skill directory carrying core.md is portable, and must carry an adapter for every
    provider in REQUIRED_PROVIDERS; one missing any of them is an incomplete change and
    raises. A directory with no core.md is provider-native, which means Claude-only: it
    must carry providers/claude.md and no other provider's adapter. Optional adapters
    (OPTIONAL_PROVIDERS: gpt) are recorded where present and never required. These are
    the only roster facts the tree can answer for -- LOCAL_CAPABLE, SUB_AGENT, VISION,
    DESCRIPTIONS and the provenance sets are non-derivable by design and each says so at
    its definition.

    The walk is gated on `p.is_dir()`, so skills/inventory.json (a generated artifact,
    not a skill) is skipped rather than counted. `_shared` is excluded because it is the
    cross-skill payload namespace, not a skill: it does not exist under skills/ today,
    and the exclusion is here so the step that eventually creates it cannot silently
    turn it into a provider-native record.
    """
    if skills_dir is None:
        skills_dir = SKILLS_DIR  # read at call time, so a test can point it elsewhere
    portable, native = [], []
    optional = {provider: [] for provider in OPTIONAL_PROVIDERS}
    partial, native_extra, native_bare = [], [], []
    for p in sorted(skills_dir.iterdir()):
        if not p.is_dir() or p.name == "_shared":
            continue
        adapters = {provider for provider in PROVIDERS
                    if (p / "providers" / f"{provider}.md").is_file()}
        if (p / "core.md").is_file():
            missing = [provider for provider in REQUIRED_PROVIDERS
                       if provider not in adapters]
            if missing:
                partial.append(f"{p.name} (missing {', '.join(missing)})")
                continue
            portable.append(p.name)
            for provider in OPTIONAL_PROVIDERS:
                if provider in adapters:
                    optional[provider].append(p.name)
        else:
            native.append(p.name)
            if "claude" not in adapters:
                native_bare.append(p.name)
            extra = sorted(adapters - {"claude"})
            if extra:
                native_extra.append(f"{p.name} ({', '.join(extra)})")
    # `raise`, not `assert`, is deliberate here and in build(): the plan asks for a
    # GUARD, and `python -O` / PYTHONOPTIMIZE strips every assert, which would let a
    # drifted tree regenerate the manifest silently -- the exact failure this guard
    # exists to prevent. A raise is the same guard that survives -O. Do not "restore"
    # the assert form.
    #
    # The shape guards run before the count guards because they name the defect; a
    # partial package also moves the counts, and "expected 44, found 43" would hide why.
    if partial:
        raise ValueError(
            "portable skills (core.md present) must carry an adapter for every "
            f"required provider {list(REQUIRED_PROVIDERS)}; incomplete: {partial}")
    # A provider-native skill is Claude-only BY DEFINITION -- that is what the status
    # means, and tools/release_checks.py rejects a gpt adapter on one for the same
    # reason. Any other provider's adapter in a native skill's providers/ dir is a
    # contradiction in the tree, caught here rather than shipped into a profile.
    if native_extra:
        raise ValueError(
            "provider-native skills are Claude-only and must not carry another "
            f"provider's adapter: {native_extra}")
    if native_bare:
        raise ValueError(
            "a skill directory with no core.md is provider-native and must carry "
            f"providers/claude.md: {native_bare}")
    # The expected counts are DERIVED from the spelled roster rather than typed (Phase
    # CL Step 111: "fixed totals become relationships derived from that roster and
    # exact native set"), and read at call time so a roster change cannot leave a stale
    # number behind. The roster stays the anti-silent-addition guard; the counts follow
    # it. tests/package-integrity/test_manifest_contract.py still pins the partition
    # (46/44/2) and the names independently.
    expected_portable, expected_native = len(PORTABLE), len(NATIVE)
    expected_total = expected_portable + expected_native
    if len(portable) + len(native) != expected_total:
        raise ValueError(
            f"expected {expected_total} skill directories under {skills_dir}, found "
            f"{len(portable) + len(native)}: {sorted(portable + native)}")
    if len(portable) != expected_portable:
        raise ValueError(
            f"expected {expected_portable} portable skills (core.md plus every "
            f"required provider adapter), found {len(portable)}")
    if len(native) != expected_native:
        raise ValueError(
            f"expected {expected_native} provider-native skills (no core.md), "
            f"found {len(native)}: {native}")
    return SkillSets(portable, native, optional)


def _check_roster_constants() -> None:
    """The spelled constants must agree with each other before any record is built."""
    roster = PORTABLE + NATIVE
    if len(set(roster)) != len(roster):
        raise ValueError(f"PORTABLE/NATIVE repeat a name: {sorted(roster)}")
    # Fail loud if a skill lacks a frontmatter description: the builder needs one
    # for every published skill, and a silently-missing entry would ship an
    # incomplete SKILL.md frontmatter to a host.
    missing_desc = sorted(set(roster) - set(DESCRIPTIONS))
    if missing_desc:
        raise KeyError(f"DESCRIPTIONS missing entries for: {missing_desc}")
    if REQUIRED_PROVIDERS[:1] != ("claude",) or not set(REQUIRED_PROVIDERS) <= set(PROVIDERS):
        raise ValueError(
            "REQUIRED_PROVIDERS must lead with claude and name only PROVIDERS "
            f"vocabulary: {REQUIRED_PROVIDERS}")
    # Provenance sets are CLOSED history (see LEGACY_SPLIT): they may only shrink, and
    # a name the roster no longer carries is a DELETE that forgot its provenance.
    if LEGACY_SPLIT & LEGACY_SINGLE_FILE:
        raise ValueError(
            f"a skill has two legacy layouts: {sorted(LEGACY_SPLIT & LEGACY_SINGLE_FILE)}")
    stale = sorted((LEGACY_SPLIT | LEGACY_SINGLE_FILE) - set(roster))
    if stale:
        raise ValueError(f"legacy provenance names a skill not in the roster: {stale}")
    # The split layout had a shared core, so only a portable skill can come from it.
    split_native = sorted(LEGACY_SPLIT & set(NATIVE))
    if split_native:
        raise ValueError(f"a provider-native skill cannot have split provenance: {split_native}")
    # Provider-native identities are grandfathered: a new one needs an operator
    # architecture plan (PROVIDER_NATIVE_REVIEW_REQUIRED), never a canonical CREATE.
    native_canonical = sorted(set(NATIVE) - LEGACY_SINGLE_FILE)
    if native_canonical:
        raise ValueError(
            f"provider-native skills must carry legacy provenance: {native_canonical}")
    # A support-asset `source` is a legacy path, so a canonical skill has none to name.
    canonical_assets = sorted(n for n in roster
                              if provenance(n)[0] == ORIGIN_CANONICAL and SUPPORT_ASSETS[n])
    if canonical_assets:
        raise ValueError(
            "a canonical skill cannot declare legacy-sourced support assets: "
            f"{canonical_assets}")


def build():
    _check_roster_constants()
    # GUARD, not a rewrite: the two rosters the committed tree can also answer for
    # must equal the spelled-out constants. It catches a roster edited in one place
    # only, without deleting the readable list or the non-derivable sets beside it.
    # `raise`, not `assert`, for the -O reason spelled out in derived_skill_sets().
    derived = derived_skill_sets()
    if derived.portable != sorted(PORTABLE):
        raise ValueError(f"skills/ tree != PORTABLE: {derived.portable}")
    if derived.native != sorted(NATIVE):
        raise ValueError(f"skills/ tree != NATIVE: {derived.native}")
    skills = []
    for name in sorted(PORTABLE + NATIVE):
        native = name in NATIVE
        caps = ["filesystem"]
        if name in SUB_AGENT:
            caps.append("sub-agent")
        if name in VISION:
            caps.append("vision")
        caps = sorted(set(caps))
        if native:
            providers = {"claude": f"skills/{name}/providers/claude.md"}
            core = None
        else:
            # Every required provider, plus each optional adapter the tree carries, in
            # PROVIDERS order (claude, gpt, codex) -- the committed key order. An absent
            # optional adapter is an absent key rather than a null, so
            # `Get-Prop $providersObj '<provider>'` stays the single absence test the
            # builder uses.
            providers = {
                provider: f"skills/{name}/providers/{provider}.md"
                for provider in PROVIDERS
                if provider in REQUIRED_PROVIDERS or name in derived.optional[provider]
            }
            core = f"skills/{name}/core.md"
        origin, migration = provenance(name)
        skills.append({
            "name": name,
            "status": "provider-native" if native else "portable",
            "description": DESCRIPTIONS[name],
            "core": core,
            "providers": providers,
            "capabilities": caps,
            "local_capable": name in LOCAL_CAPABLE,
            "origin": origin,
            "migration": migration,
            "support_assets": skill_support_assets(name),
        })

    counts = {
        "total": len(skills),
        "portable": sum(1 for s in skills if s["status"] == "portable"),
        "provider_native": sum(1 for s in skills if s["status"] == "provider-native"),
        # Per-provider adapter tallies. `claude` is every skill and
        # `gpt` equals `portable` TODAY -- both are spelled out anyway so the codex
        # tally is read on the same axis as its siblings rather than being the one
        # count with no peer, and so a future divergence between "is portable" and
        # "has a gpt adapter" shows up as two different numbers instead of hiding
        # behind a shared one.
        "claude": sum(1 for s in skills if "claude" in s["providers"]),
        "gpt": sum(1 for s in skills if "gpt" in s["providers"]),
        "codex": sum(1 for s in skills if "codex" in s["providers"]),
        "local_capable": sum(1 for s in skills if s["local_capable"]),
        "sub_agent": sum(1 for s in skills if "sub-agent" in s["capabilities"]),
        "vision": sum(1 for s in skills if "vision" in s["capabilities"]),
        "filesystem": len(skills),
    }

    global_assets = [
        {"source": ".claude/lib/skill-router.ps1", "dest": "runtime/skill-router.ps1",
         "note": "provider-neutral router (lands Step 34)"},
        {"source": ".claude/lib/telemetry/", "dest": "runtime/telemetry/",
         "note": "telemetry writer/summary + invocations log (Step 34)"},
        {"source": ".claude/lib/calibration/", "dest": "tests/calibration/",
         "note": "existing pytest calibration suite (Step 34)"},
        {"source": ".claude/references/model-mapping.md", "dest": "config/model-mapping.json",
         "note": "capability/local mapping, transformed md -> json (Step 34)"},
        {"source": ".claude/references/model-tier-map.json", "dest": "config/model-tier-map.json",
         "note": "Claude-tier to GPT-peer mapping (Step 34)"},
        {"source": ".claude/skills/_shared/", "dest": "skills/_shared/",
         "note": "cross-skill grader/scoring assets + judge-core.md; only skills/_shared exists (no skills-gpt/_shared)"},
        {"source": "documentation/multi-model/", "dest": "documentation/providers/ + documentation/architecture.md",
         "note": "existing operator guides; coding-root-relative (sibling of .claude, NOT under it)"},
    ]

    manifest = {
        "schema_version": 1,
        "description": (
            "Canonical source-of-truth for the skill-mesh package: one record per "
            "published skill. Consumed by distribution, installation, integrity, "
            "and README-count generation."
        ),
        "legacy_migration_root": (
            "coding-root (aberson/coding-root at the operator's checkout, READ-ONLY "
            "during Steps 33-40). Every 'source'/'legacy_*' path in this manifest is "
            "relative to that root: the '.claude/...' trees and 'documentation/"
            "multi-model/...' are both direct children of coding-root."
        ),
        "capability_vocabulary": ["filesystem", "sub-agent", "vision"],
        "capability_semantics": {
            "filesystem": (
                "The skill reads and/or writes workspace files as an intrinsic part "
                "of its contract (plan docs, state files, reports, evals, or source "
                "edits). True for every skill in this package."
            ),
            "sub-agent": (
                "The skill's core workflow requires dispatching one or more isolated "
                "fresh-context sub-agents -- the host Agent/Task primitive, a Workflow "
                "agent() call, or provider action children (e.g. parallel judge/"
                "reviewer fan-out or a separate vision-judge). A named-skill dispatch "
                "(/other-skill) does NOT count. A local text-only model cannot satisfy "
                "this, so sub-agent implies local_capable=false."
            ),
            "vision": (
                "The skill requires a native image/vision capability (screenshot or "
                "filmstrip judging). Implies local_capable=false."
            ),
        },
        "host_metadata_sources": {
            "description": (
                "Approved trustworthy host-identity environment variables the neutral "
                "router (-Provider auto) may consult in Step 37. Explicit host-set "
                "environment metadata ONLY: no executable-name guessing, and "
                "credential variables are excluded because a credential can be "
                "exported in any environment and does not identify the active host."
            ),
            "claude": {
                "markers": [
                    {"var": "CLAUDECODE", "expected": "1"},
                    {"var": "CLAUDE_CODE_ENTRYPOINT", "expected": "<non-empty>"},
                ],
                "rule": "present if any listed marker is set with its expected value",
            },
            "gpt": {
                "markers": [
                    {"var": "COPILOT_CLI", "expected": "<non-empty>"},
                    {"var": "COPILOT_AGENT_SESSION_ID", "expected": "<non-empty>"},
                ],
                "rule": "present if any listed marker is set with its expected value",
            },
            "excluded_non_identity": [
                "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
                "GITHUB_TOKEN",
            ],
            "precedence": [
                "If exactly one provider's markers are present -> select it.",
                "If BOTH providers' markers are present -> ambiguous: error (exit 2), never default to Claude.",
                "If NEITHER is present -> unset/unsupported: error (exit 2) instructing an explicit -Provider claude|gpt.",
            ],
        },
        # The installable-provider vocabulary. Its coupling to the discovery-root map is
        # documented at PROVIDERS, which is the one definition.
        "providers": {provider: dict(meta) for provider, meta in PROVIDERS.items()},
        "portable_provider_contract": {
            "description": (
                "Ordered set of providers every portable skill carries an adapter for. "
                "A provider in `providers` but not in `required` is optional: its "
                "adapter is listed where one is authored, and its absence is not "
                "drift. Widening `required` is an explicit provider-rollout decision."
            ),
            "required": list(REQUIRED_PROVIDERS),
        },
        "counts": counts,
        "global_support_assets": global_assets,
        "skills": skills,
    }

    fixture = {
        "note": (
            "Authoritative expected inventory for package-integrity tests. Committed "
            "so the public package tests need no private/legacy source. Regenerate "
            "with tools/gen_manifest.py."
        ),
        "counts": counts,
        "portable": PORTABLE,
        "provider_native": NATIVE,
        # Read off the generated records, NOT a spelled roster: codex is required, so
        # this equals `portable` by construction (decision CL-D14). It stays in the
        # fixture as the expected per-record outcome the contract test compares the
        # manifest's `providers` dicts against.
        "codex": sorted(s["name"] for s in skills if "codex" in s["providers"]),
        "local_capable": sorted(LOCAL_CAPABLE),
        "sub_agent": sorted(SUB_AGENT),
        "vision": sorted(VISION),
        "skills": [
            {
                "name": s["name"],
                "status": s["status"],
                "local_capable": s["local_capable"],
                "capabilities": s["capabilities"],
                "origin": s["origin"],
                "migration": s["migration"],
                "support_assets": s["support_assets"],
            }
            for s in skills
        ],
        "global_support_assets": global_assets,
    }
    return manifest, fixture


def serialize(doc) -> str:
    """The ONE serializer for all three artifacts: UTF-8, no BOM, 2-space indent, trailing
    newline. Returns TEXT with "\\n" separators; the writer emits UTF-8 LF."""
    return json.dumps(doc, indent=2) + "\n"


# The three generated artifacts, relative to the tree they are written into, in the
# order they are replaced.
ARTIFACTS = ("config/skill-manifest.json",
             "tests/package-integrity/expected_inventory.json",
             "skills/inventory.json")


def _build_inventory(manifest: dict) -> dict:
    """Load and reuse the established inventory projection without running its
    retired legacy-tree CLI."""
    import importlib.util

    path = REPO_ROOT / "tools" / "gen_skill_tree.py"
    spec = importlib.util.spec_from_file_location("gen_skill_tree_inventory", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_inventory(manifest)


def _norm(data: bytes) -> bytes:
    """Strip a UTF-8 BOM, then fold CRLF/CR to LF -- the comparison rule release tooling
    and the regeneration tests already apply, because a checkout's line endings are a
    property of the clone, not of the content."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def validate_payloads(payloads: dict) -> None:
    """Validate all three serialized payloads together. Raises ValueError, writes nothing.

    Reads the BYTES back rather than trusting the in-memory documents, so what is
    checked is what would be written. Every check here is a relationship between the
    three artifacts or between an artifact and the contract constants; a failure means
    the generator itself is wrong, and no file may be replaced.
    """
    problems = []
    if tuple(payloads) != ARTIFACTS:
        raise ValueError(f"payloads must be exactly {ARTIFACTS}, in order: {tuple(payloads)}")
    docs = {}
    for rel, data in payloads.items():
        if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or not data.endswith(b"\n"):
            problems.append(f"{rel}: not UTF-8 LF without a BOM and a trailing newline")
        try:
            docs[rel] = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError(f"{rel}: payload does not parse: {exc}") from exc
    manifest, fixture, inventory = (docs[rel] for rel in ARTIFACTS)

    records = manifest["skills"]
    names = [s["name"] for s in records]
    if names != sorted(PORTABLE + NATIVE):
        problems.append("manifest skill names are not the sorted PORTABLE + NATIVE roster")
    contract = manifest.get("portable_provider_contract", {})
    if contract.get("required") != list(REQUIRED_PROVIDERS):
        problems.append(f"portable_provider_contract.required != {list(REQUIRED_PROVIDERS)}")
    vocabulary = list(manifest["providers"])
    for s in records:
        name, prov = s["name"], s["providers"]
        if not set(prov) <= set(vocabulary):
            problems.append(f"{name}: provider outside the vocabulary: {sorted(prov)}")
        if list(prov) != [p for p in vocabulary if p in prov]:
            problems.append(f"{name}: providers not in vocabulary order: {list(prov)}")
        if s["status"] == "portable":
            if s["core"] != f"skills/{name}/core.md":
                problems.append(f"{name}: portable record without its core")
            missing = [p for p in REQUIRED_PROVIDERS if p not in prov]
            if missing:
                problems.append(f"{name}: portable record missing required {missing}")
        elif s["status"] == "provider-native":
            if s["core"] is not None or list(prov) != ["claude"]:
                problems.append(f"{name}: provider-native record is not Claude-only")
        else:
            problems.append(f"{name}: unknown status {s['status']!r}")
        if s["origin"] == ORIGIN_CANONICAL:
            if s["migration"] is not None or s["support_assets"]:
                problems.append(f"{name}: canonical record carries legacy provenance")
        elif s["origin"] == ORIGIN_LEGACY:
            mig = s["migration"]
            if not isinstance(mig, dict) or tuple(mig) != MIGRATION_KEYS:
                problems.append(f"{name}: legacy record without the four migration keys")
            elif not all(v is None or (isinstance(v, str) and v.startswith(".claude/"))
                         for v in mig.values()):
                problems.append(f"{name}: legacy path not coding-root-relative")
            elif mig["legacy_claude_adapter"] is None:
                problems.append(f"{name}: legacy record names no Claude source")
        else:
            problems.append(f"{name}: unknown origin {s['origin']!r}")
        for provider, path in prov.items():
            if path != f"skills/{name}/providers/{provider}.md":
                problems.append(f"{name}: {provider} adapter path {path!r}")

    counts = manifest["counts"]
    recount = {
        "total": len(records),
        "portable": sum(1 for s in records if s["status"] == "portable"),
        "provider_native": sum(1 for s in records if s["status"] == "provider-native"),
        **{p: sum(1 for s in records if p in s["providers"]) for p in vocabulary},
    }
    for key, value in recount.items():
        if counts.get(key) != value:
            problems.append(f"manifest counts[{key!r}] = {counts.get(key)} != {value}")

    if fixture["counts"] != counts:
        problems.append("fixture counts != manifest counts")
    if (fixture["portable"], fixture["provider_native"]) != (PORTABLE, NATIVE):
        problems.append("fixture portable/provider_native != the spelled roster")
    if fixture["codex"] != sorted(s["name"] for s in records if s["status"] == "portable"):
        problems.append("fixture codex roster != the portable records")
    fixture_view = [{k: s[k] for k in ("name", "status", "origin", "migration",
                                       "support_assets")} for s in records]
    if [{k: f[k] for k in ("name", "status", "origin", "migration", "support_assets")}
            for f in fixture["skills"]] != fixture_view:
        problems.append("fixture per-skill records disagree with the manifest")

    inv = inventory["skills"]
    if [r["name"] for r in inv] != names:
        problems.append("inventory skill names != manifest skill names")
    for r, s in zip(inv, records):
        if r["status"] != s["status"] or r["core"] != bool(s["core"]):
            problems.append(f"{r['name']}: inventory status/core disagree with the manifest")
        for provider, present in r["providers"].items():
            if present != (provider in s["providers"]):
                problems.append(f"{r['name']}: inventory {provider} flag disagrees")
    for key in ("total", "portable", "provider_native", "codex"):
        if inventory["counts"].get(key) != counts[key]:
            problems.append(f"inventory counts[{key!r}] != manifest counts[{key!r}]")

    if problems:
        raise ValueError("generated payloads failed validation; nothing was written:\n  "
                         + "\n  ".join(problems))


def render_artifacts():
    """Build, serialize and validate all three artifacts IN MEMORY.

    Returns (manifest, payloads) where payloads maps each ARTIFACTS path to its exact
    bytes. Both CLI modes start here, so `--check` compares precisely what a
    regeneration would write, and a regeneration replaces nothing unless all three
    payloads exist and passed validation first.
    """
    manifest, fixture = build()
    inventory = _build_inventory(manifest)
    payloads = {rel: serialize(doc).encode("utf-8")
                for rel, doc in zip(ARTIFACTS, (manifest, fixture, inventory))}
    validate_payloads(payloads)
    return manifest, payloads


def _write_payload(handle, data: bytes) -> None:
    """Write one payload into an open temporary file. Kept separate so a test can
    interrupt a write part-way through and prove the target is untouched."""
    handle.write(data)


def _replace_file(path: Path, data: bytes) -> None:
    """Replace ONE file safely: write a temporary sibling, flush it to disk, then
    atomically rename it over the target.

    An interruption before the rename leaves the old file whole and removes the
    temporary; after the rename the new file is whole. No reader can ever see a
    truncated artifact. This is per file only -- see the module docstring.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                                    dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with open(fd, "wb") as handle:
            _write_payload(handle, data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def write_artifacts(out_root: Path):
    """Build, validate, then replace all three artifacts under `out_root`. Returns the
    manifest.

    `out_root` is a parameter so the regeneration gate can drive the REAL production
    write path into a temporary tree instead of over the committed files. Nothing is
    replaced until all three payloads exist and validated (`render_artifacts()`).

    Emit UTF-8 LF consistently on every host. Consumers and regeneration checks
    continue normalizing line endings for older checkout artifacts.
    """
    manifest, payloads = render_artifacts()
    for rel, data in payloads.items():
        _replace_file(out_root / rel, data)
    return manifest


def check_artifacts(root: Path) -> list:
    """Compare the three committed artifacts under `root` with what a regeneration would
    write. Returns the drifted paths (empty when all three match). NEVER writes.

    Line endings are normalized on both sides (`_norm`), so a CRLF checkout of
    byte-identical content is not drift.
    """
    _, payloads = render_artifacts()
    drift = []
    for rel, data in payloads.items():
        path = root / rel
        if not path.is_file():
            drift.append(f"{rel} (missing)")
        elif _norm(path.read_bytes()) != _norm(data):
            drift.append(rel)
    return drift


def build_parser() -> argparse.ArgumentParser:
    """The CLI. One mode switch and no input: generation is hermetic, so no argument
    can name a source, and a stale invocation still carrying the retired
    --legacy-source flag fails loudly ("unrecognized arguments")."""
    parser = argparse.ArgumentParser(description="Regenerate the skill manifest, fixture, "
                                                 "and inventory from this repository alone.")
    parser.add_argument("--check", action="store_true",
                        help="compare the three committed artifacts with a regeneration "
                             "in memory; never write. Exit 1 on drift.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        drift = check_artifacts(REPO_ROOT)
        if drift:
            for rel in drift:
                print(f"drift: {rel}", file=sys.stderr)
            print("generated artifacts are stale; run `python tools/gen_manifest.py`",
                  file=sys.stderr)
            return 1
        print("check: " + ", ".join(ARTIFACTS) + " match a regeneration")
        return 0
    manifest = write_artifacts(REPO_ROOT)
    print(f"counts: {manifest['counts']}")
    print("wrote " + " and ".join(ARTIFACTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
