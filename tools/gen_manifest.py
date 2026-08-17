"""Generate config/skill-manifest.json and tests/package-integrity/expected_inventory.json.

HERMETIC (Step 67). Generation reads nothing outside this repository. Every input is
either a checked-in constant below or the committed skills/<name>/ tree, so

    python tools/gen_manifest.py

reproduces both committed artifacts with NO environment set and no argument passed.

WHY hermetic. This generator used to SCAN an external legacy root for each skill's
support assets (<coding-root>/.claude/{skills,skills-gpt}/<name>). The Step 50
consumer cutover overwrote that root with this package's OWN installed output, so a
regeneration fed skill-mesh's build product back into skill-mesh's manifest: 47 of
50 skills drifted, gaining 47 bogus `.claude/skills/<name>/core.md` sources and
losing `.claude/skills-gpt/judge-ui/calibration-notes.md`. An input that a
consumer-side install can mutate is not a generator input.

LINE ENDINGS. This repository has no .gitattributes and core.autocrlf=true, so ONE
git blob is CRLF in a Windows checkout and LF in a POSIX one. `write_artifacts`
therefore writes the PLATFORM line ending, matching whatever the checkout produced,
and the raw bytes of a regenerated artifact are a property of the CLONE rather than
of its content. Any comparison against a committed copy must normalize (strip a
UTF-8 BOM, then CRLF/CR -> LF) on BOTH sides -- the same rule the release tooling
already applies to `dist/`. The regeneration gate in
tests/package-integrity/test_manifest_contract.py does exactly that, so it cannot
pass in a worktree and fail in the main checkout.

Authoritative structural data (names, status, local_capable, capabilities,
descriptions, support assets) is encoded here as checked-in constants. Four of those
sets are NON-DERIVABLE BY DESIGN and each states why at its own definition:
LOCAL_CAPABLE, SUB_AGENT, VISION, DESCRIPTIONS. PORTABLE, NATIVE and CODEX are the
three sets that ARE derivable from the committed tree; they stay spelled out for
readability and are CHECKED against the tree by `derived_skill_sets()` on every run.

Usage:
    python tools/gen_manifest.py

Re-run only when one of the constants below changes. There is no legacy-source
argument and no environment variable: an external source root is precisely what this
generator no longer reads.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"

# ---- Authoritative structural constants (evidence-grounded) ----------------
#
# PORTABLE / NATIVE are the ONLY two sets here that the committed tree can also
# produce (a skill dir carrying providers/gpt.md is portable; one without it is
# provider-native). They are kept spelled out because the manifest's skill ORDER and
# the fixture's `portable` / `provider_native` arrays are this list verbatim, and
# because a reader should be able to see the roster without walking a directory.
# `derived_skill_sets()` re-derives both from disk on every run and `build()` raises on
# inequality, so the spelled-out copy cannot drift away from the tree.

PORTABLE = [
    "build-phase", "build-queue", "build-step", "goblin-do", "goblin-suggest",
    "judge-ui", "lesson-harvest", "memory-distill", "observatory-doctor",
    "plan-expedite", "plan-feature", "plan-init", "plan-merge", "plan-redline",
    "plan-review", "plan-trim", "plan-wrap", "repo-init", "repo-sync",
    "repo-update", "research-prospect", "review-deep", "review-gauntlet",
    "review-proof", "review-uat", "session-wrap", "skill-eval-setup",
    "skill-evolve", "skill-iterate", "task-handoff", "test-prune",
    "tier-escalate", "tier-offload", "user-afterparty", "user-brainstorm",
    "user-debug", "user-draft", "user-gateway", "user-lavishify", "user-learn",
    "user-orient", "user-pm", "user-project", "user-shakedown", "user-uat",
    "user-walkthrough", "user-wrap",
]

NATIVE = ["claude-oauth-auth", "context-slim", "judge-motion"]

# Skills carrying a Codex provider adapter (skills/<name>/providers/codex.md).
#
# CODEX IS AN ORTHOGONAL AXIS, NOT A THIRD BUCKET. PORTABLE/NATIVE partition the
# roster on the GPT axis (`providers/gpt.md` present or absent), and that partition is
# what `status`, `counts["portable"]`, `counts["provider_native"]` and the README's
# GPT-capable line all mean. A codex adapter is ADDITIVE on top of a record that is
# already portable-or-native: it never moves a skill between those two buckets, so
# EXPECTED_TOTAL / EXPECTED_PORTABLE / EXPECTED_NATIVE stay 50/47/3 and every existing
# count keeps its exact meaning. Modelling codex as a third status instead would
# redefine `portable` for all 50 records and invalidate every committed tally.
#
# Derivable from the tree exactly like PORTABLE/NATIVE, and CHECKED against it by
# `derived_skill_sets()` on every run, so the spelled-out copy cannot drift.
#
# EMPTY BY DESIGN AT THIS STEP. Phase CP Step 3 builds the generation SURFACE; the
# pilot five adapters land in Step 4 and the cohorts in Steps 6-8. An empty list is
# therefore the correct committed state, and `-Provider codex` legitimately emits an
# empty profile until the first adapter is authored.
CODEX = []

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
LOCAL_CAPABLE = {
    "lesson-harvest", "memory-distill", "observatory-doctor", "plan-feature",
    "plan-init", "plan-merge", "plan-review", "plan-trim", "plan-wrap",
    "repo-init", "repo-sync", "repo-update", "review-proof", "review-uat",
    "skill-eval-setup", "user-debug", "user-draft", "user-gateway",
    "user-orient", "user-pm", "user-shakedown", "user-uat", "user-walkthrough",
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
    "goblin-do",         # runs /build-step via a Workflow agent() call
    "goblin-suggest",    # "fan out --n-judges judge agent calls IN PARALLEL"
    "judge-motion",      # "separate sub-agent per transition" via Agent tool
    "judge-ui",          # "dispatches an independent vision-judge sub-agent"
    "research-prospect", # "Fan out parallel Explore agents"
    "review-deep",       # "spawns six fresh-context sub-agents, one per lens"
    "review-gauntlet",   # "one fresh-context reviewer invocation for each lens"
    "skill-evolve",      # independent agent trials per variant
    "skill-iterate",     # "Dispatch ONE sub-agent" via fresh-context task
    "test-prune",        # "dispatch this phase as parallel Explore agents"
    "tier-escalate",     # fresh-context fan-out arms
    "tier-offload",      # fresh-context task API required
    "user-brainstorm",   # "One background sub-agent per investigation file"
    "user-learn",        # "One background sub-agent per file"
}

# Skills with a documented native-vision dependency.
#
# NON-DERIVABLE BY DESIGN. "Requires a native image/vision capability" is a claim
# about the HOST capability a skill needs, not about any artifact in skills/<name>/.
# Several skills mention screenshots without needing to SEE one; these two cannot
# render a verdict without it. Nothing on disk marks that difference.
VISION = {"judge-ui", "judge-motion"}

# Per-skill one-line `description`, the SINGLE source of truth for the SKILL.md
# frontmatter description the builder emits (GitHub Copilot CLI requires every
# generated SKILL.md to LEAD with a YAML frontmatter block carrying at least
# `name` + `description`; Step 44). Encoded here as a checked-in, evidence-grounded
# constant exactly like PORTABLE / NATIVE / LOCAL_CAPABLE above -- the evidence is
# each skill's own SKILL contract (its legacy `.claude/skills/<name>/SKILL.md`
# description and canonical core.md purpose).
#
# NON-DERIVABLE BY DESIGN, and measurably so: all 50 committed
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
    "build-phase": "Orchestrate a multi-step build phase end-to-end: run each plan step through build-step in order, gate quality between steps, and report progress.",
    "build-queue": "Queue and run multiple pending phase plans unattended, isolating each in its own worktree and parking any halt as a GitHub issue.",
    "build-step": "Execute one build step end-to-end: a developer agent writes the change, isolated reviewers gate it, and the result merges.",
    "claude-oauth-auth": "How to authenticate with Claude using a subscription OAuth token instead of an API key.",
    "context-slim": "Audit a project's auto-loaded context files and produce a prioritized progressive-disclosure plan to cut per-turn token cost.",
    "goblin-do": "Single front door for a chosen goblin atom: execute a small suggestion or safe UAT task via build-step, or hand a big one to the plan rail.",
    "goblin-suggest": "Produce a grounded, ranked improvement shortlist for a project and persist it as goblin suggestion atoms.",
    "judge-motion": "Capture a UI transition as a slow-motion filmstrip and have a vision-judge render a PASS/FAIL/ESCALATE verdict on motion defects.",
    "judge-ui": "Drive a web UI through a flow, capture screenshots plus a structured read-back, and have an independent vision-judge render PASS/FAIL/UNCERTAIN.",
    "lesson-harvest": "Scan recent git history and run-logs for un-codified regressions and draft codification candidates as a review-ready PR.",
    "memory-distill": "Review recent feedback memories one at a time and surface the latent principles several of them point at.",
    "observatory-doctor": "Health-check every launcher button on the dev-observatory dashboard and report which project verbs actually work.",
    "plan-expedite": "Chain plan-review, plan-wrap, repo-sync, and task-handoff into one autonomous prep step before build-phase.",
    "plan-feature": "Plan a new feature or phase for an existing project by reading its code and docs, then producing a scoped plan document.",
    "plan-init": "Guide creation of a new project plan through a structured up-front conversation about stack, storage, auth, and tooling.",
    "plan-merge": "Merge two overlapping plan documents into one coherent plan, resolving sequencing and deleting subsumed phases.",
    "plan-redline": "Render a just-authored plan into an operator-facing proposal with every choice labeled operator-picked or agent-defaulted.",
    "plan-review": "Review a plan for gaps, missing pieces, unresolved decisions, and risks, validating claims against existing code.",
    "plan-trim": "Investigate a project's state and propose plan items to cut or fold together, then execute the trim once confirmed.",
    "plan-wrap": "Check whether a plan or document is self-contained for a fresh model with no prior conversation history.",
    "repo-init": "Publish a local project to GitHub: initialize git, create the remote, add a README, and convert the plan into issues.",
    "repo-sync": "Sync GitHub issues to match a plan's structure with rich, fresh-context issue bodies.",
    "repo-update": "End-to-end docs and git update after a phase: refresh README and plan, run plan-wrap, update memory, commit, and push.",
    "research-prospect": "Scan active projects and surface high-value research topic strings per project for hand-off to separate windows.",
    "review-deep": "Six-lens code review (correctness, bugs, security, tests, style, plan-conformance) with severity, evidence, and a JSON audit trail.",
    "review-gauntlet": "Lean multi-lens code-review profile over review-deep's engine that emits a terse PASS/NEEDS-WORK verdict.",
    "review-proof": "Enforce evidence-based responses by requiring primary-source verification before making any claim.",
    "review-uat": "Refine a UAT script so every step is unambiguous and only the checks that genuinely need a human stay on the human.",
    "session-wrap": "The session-transition front door: triage context, task state, and git, then continue, recycle, or close the window.",
    "skill-eval-setup": "Auto-generate an evaluation framework for a skill by reading its contract, then output a ready-to-run self-improvement loop.",
    "skill-evolve": "A/B-test several variant mutations of a skill in parallel worktrees and compare, pushing the winner for review.",
    "skill-iterate": "Serial hill-climb every scorable skill autonomously, capped per skill by wall-clock or iteration budget.",
    "task-handoff": "Checkpoint library that orchestrators call to save session state and regenerate the derived current-task rollup.",
    "test-prune": "Audit a test suite for redundant, trivial, or mock-theater tests, relocating sole-coverage ones and deleting the rest.",
    "tier-escalate": "Scan skills to find which single load-bearing seed-artifact phase warrants escalating a session to a higher-tier model, and emit a map.",
    "tier-offload": "Scan skills to find which sub-tasks are safe to offload to a local model, and emit an offload inventory plus a router config.",
    "user-afterparty": "Milestone workspace-hygiene front door that chains the hygiene skills into one report and walks the operator through cleanup.",
    "user-brainstorm": "Brainstorm a topic end-to-end, gap-fill through rounds, then dispatch one sub-agent per topic to write a reference doc set.",
    "user-debug": "Diagnose and fix a bug end-to-end with forced primary-source investigation before any code change.",
    "user-draft": "Refine rough thoughts into a polished prompt or a ready-to-paste goal condition, checkpointing state along the way.",
    "user-gateway": "Pre-work intake gateway that converts an operator vent into routed, ledger-backed work with a ready-to-paste seed per row.",
    "user-lavishify": "Escalate the last output into a richer, more thorough on-demand deliverable without changing the default chat-first style.",
    "user-learn": "Scaffold a hands-on learning ramp for a topic with a knowledge base, runnable notebooks, exercises, and a progress tracker.",
    "user-orient": "Re-orient on the session axis with a verified status snapshot of what we were doing and what is left.",
    "user-pm": "Tight PM-lens overview on the project axis: what shipped, what is planned, what is next, and what could be cut.",
    "user-project": "Pin the session's active project so pipeline skills target the right repo regardless of the current directory.",
    "user-shakedown": "Shake down a just-built tool or feature to surface rough edges before formal acceptance.",
    "user-uat": "Run an already-clear UAT block for the operator, executing steps and auto-judging the mechanically checkable ones.",
    "user-walkthrough": "Attended, operator-driven acceptance of a just-built tool where the agent answers from primary source and fixes small things in place.",
    "user-wrap": "The return-moment front door for sitting back down: orient, get a keep-going-or-wrap verdict, and act on it.",
}

# Per-skill support assets, BAKED IN as a checked-in constant -- the same rationale
# DESCRIPTIONS above already gives, applied to the input that actually broke.
#
# These are the committed manifest's `support_assets` values verbatim, captured from
# the legacy source at Step 33. They are NOT re-derivable from the committed
# skills/<name>/ tree: 61 of the 62 dests do not exist there yet (the per-skill asset
# migration is a later step), so enumerating skills/<name>/ would silently ERASE 61
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
# All 50 skills carry a key -- an empty list where a skill has no assets -- so adding
# a skill without deciding its assets is a loud KeyError, never a silent empty record.
SUPPORT_ASSETS = {
    "build-phase": [("skills", "evals/")],
    "build-queue": [("skills", "evals/")],
    "build-step": [
        ("skills", "evals/"),
        ("skills", "scripts/"),
    ],
    "claude-oauth-auth": [("skills", "evals/")],
    "context-slim": [("skills", "evals/")],
    "goblin-do": [
        ("skills", "evals/"),
        ("skills", "goblin_do.workflow.js"),
    ],
    "goblin-suggest": [
        ("skills", "evals/"),
        ("skills", "goblin_suggest.workflow.js"),
    ],
    "judge-motion": [
        ("skills", "fixtures/"),
        ("skills", "package-lock.json"),
        ("skills", "package.json"),
        ("skills", "scripts/"),
        ("skills", "tests/"),
    ],
    "judge-ui": [
        ("skills", "evals/"),
        ("skills-gpt", "calibration-notes.md"),
    ],
    "lesson-harvest": [("skills", "evals/")],
    "memory-distill": [("skills", "evals/")],
    "observatory-doctor": [],
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
    "plan-trim": [("skills", "evals/")],
    "plan-wrap": [("skills", "evals/")],
    "repo-init": [("skills", "evals/")],
    "repo-sync": [("skills", "evals/")],
    "repo-update": [("skills", "evals/")],
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
    "user-afterparty": [],
    "user-brainstorm": [("skills", "evals/")],
    "user-debug": [("skills", "evals/")],
    "user-draft": [("skills", "evals.seed/")],
    "user-gateway": [("skills", "evals/")],
    "user-lavishify": [],
    "user-learn": [("skills", "evals/")],
    "user-orient": [("skills", "evals/")],
    "user-pm": [("skills", "evals/")],
    "user-project": [],
    "user-shakedown": [("skills", "evals/")],
    "user-uat": [("skills", "evals/")],
    "user-walkthrough": [("skills", "evals/")],
    "user-wrap": [("skills", "evals/")],
}

# Spelled-out expectations for the tree enumeration below. The same three numbers are
# asserted independently by tests/package-integrity/test_manifest_contract.py.
EXPECTED_TOTAL, EXPECTED_PORTABLE, EXPECTED_NATIVE = 50, 47, 3


def skill_support_assets(name: str):
    """Return the (source, dest) support-asset records for one skill.

    Built from the single (legacy_tree, rel) pair in SUPPORT_ASSETS, so `source` and
    `dest` cannot disagree about the relative path they share.
    """
    return [{"source": f".claude/{tree}/{name}/{rel}",
             "dest": f"skills/{name}/{rel}"}
            for tree, rel in SUPPORT_ASSETS[name]]


def derived_skill_sets(skills_dir: Path = SKILLS_DIR):
    """Enumerate the COMMITTED skills/ tree -> (portable, native, codex), each sorted.

    A skill directory carrying providers/gpt.md is portable; one without it is
    provider-native. A directory carrying providers/codex.md is additionally codex-
    capable -- an ORTHOGONAL axis that does not move the skill between the first two
    buckets (see CODEX above). These are the only three roster sets the tree can answer
    for -- LOCAL_CAPABLE, SUB_AGENT, VISION and DESCRIPTIONS are non-derivable by
    design and each says so at its definition.

    The walk is gated on `p.is_dir()`, so skills/inventory.json (a generated artifact,
    not a skill) is skipped rather than counted as a 51st entry. `_shared` is excluded
    because it is the cross-skill payload namespace, not a skill: it does not exist
    under skills/ today, and the exclusion is here so the step that eventually creates
    it cannot silently turn it into a provider-native record.
    """
    portable, native, codex = [], [], []
    for p in sorted(skills_dir.iterdir()):
        if not p.is_dir() or p.name == "_shared":
            continue
        (portable if (p / "providers" / "gpt.md").is_file() else native).append(p.name)
        if (p / "providers" / "codex.md").is_file():
            codex.append(p.name)
    # `raise`, not `assert`, is deliberate here and in build(): the plan asks for a
    # GUARD, and `python -O` / PYTHONOPTIMIZE strips every assert, which would let a
    # drifted tree regenerate the manifest silently -- the exact failure this guard
    # exists to prevent. A raise is the same three-line guard that survives -O. Do not
    # "restore" the assert form.
    if len(portable) + len(native) != EXPECTED_TOTAL:
        raise ValueError(
            f"expected {EXPECTED_TOTAL} skill directories under {skills_dir}, found "
            f"{len(portable) + len(native)}: {sorted(portable + native)}")
    if len(portable) != EXPECTED_PORTABLE:
        raise ValueError(
            f"expected {EXPECTED_PORTABLE} portable skills (providers/gpt.md present), "
            f"found {len(portable)}")
    if len(native) != EXPECTED_NATIVE:
        raise ValueError(
            f"expected {EXPECTED_NATIVE} provider-native skills (no providers/gpt.md), "
            f"found {len(native)}: {native}")
    # A provider-native skill is Claude-only BY DEFINITION -- that is what the status
    # means, and tools/release_checks.py rejects a gpt adapter on one for the same
    # reason. A codex.md sitting in a native skill's providers/ dir is therefore a
    # contradiction in the tree, caught here rather than shipped into a profile.
    native_codex = sorted(set(codex) & set(native))
    if native_codex:
        raise ValueError(
            "provider-native skills are Claude-only and must not carry "
            f"providers/codex.md: {native_codex}")
    return portable, native, codex


def build():
    # Fail loud if a skill lacks a frontmatter description: the builder needs one
    # for every published skill, and a silently-missing entry would ship an
    # incomplete SKILL.md frontmatter to a Copilot host.
    missing_desc = sorted(set(PORTABLE + NATIVE) - set(DESCRIPTIONS))
    if missing_desc:
        raise KeyError(f"DESCRIPTIONS missing entries for: {missing_desc}")
    # GUARD, not a rewrite: the two rosters the committed tree can also answer for
    # must equal the spelled-out constants. Deliberately three lines -- it catches a
    # roster edited in one place only, without deleting the readable list or the four
    # non-derivable sets beside it. `raise`, not `assert`, for the -O reason spelled
    # out in derived_skill_sets().
    derived_portable, derived_native, derived_codex = derived_skill_sets()
    if derived_portable != sorted(PORTABLE):
        raise ValueError(f"skills/ tree != PORTABLE: {derived_portable}")
    if derived_native != sorted(NATIVE):
        raise ValueError(f"skills/ tree != NATIVE: {derived_native}")
    if derived_codex != sorted(CODEX):
        raise ValueError(f"skills/ tree != CODEX: {derived_codex}")
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
            migration = {
                "legacy_core": None,
                "legacy_claude_launcher": None,
                "legacy_claude_adapter": f".claude/skills/{name}/SKILL.md",
                "legacy_gpt": None,
            }
            core = None
        else:
            providers = {
                "claude": f"skills/{name}/providers/claude.md",
                "gpt": f"skills/{name}/providers/gpt.md",
            }
            # Codex is additive and OPTIONAL per skill: the key is present only for
            # skills whose adapter is authored. Key ORDER is load-bearing for the
            # committed bytes -- codex sorts after claude/gpt here because json.dumps
            # preserves insertion order, and the builder reads by name, never by
            # position. A skill with no codex.md carries no codex key at all rather
            # than a null, so `Get-Prop $providersObj 'codex'` stays the single
            # absence test the builder already uses for gpt on a native skill.
            if name in CODEX:
                providers["codex"] = f"skills/{name}/providers/codex.md"
            migration = {
                "legacy_core": f".claude/skills-gpt/{name}/SKILL-core.md",
                "legacy_claude_launcher": f".claude/skills/{name}/SKILL.md",
                "legacy_claude_adapter": f".claude/skills/{name}/SKILL-claude.md",
                "legacy_gpt": f".claude/skills-gpt/{name}/SKILL-gpt.md",
            }
            core = f"skills/{name}/core.md"
        skills.append({
            "name": name,
            "status": "provider-native" if native else "portable",
            "description": DESCRIPTIONS[name],
            "core": core,
            "providers": providers,
            "capabilities": caps,
            "local_capable": name in LOCAL_CAPABLE,
            "migration": migration,
            "support_assets": skill_support_assets(name),
        })

    counts = {
        "total": len(skills),
        "portable": sum(1 for s in skills if s["status"] == "portable"),
        "provider_native": sum(1 for s in skills if s["status"] == "provider-native"),
        # Per-provider adapter tallies. `claude` is every skill (all 50 carry one) and
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
        # THE INSTALLABLE-PROVIDER VOCABULARY -- deliberately NOT extended with codex
        # at Phase CP Step 3. Read this before adding a key.
        #
        # This block is not a list of providers the BUILDER can emit; the builder never
        # reads it (tools/build-distributions.ps1 resolves each skill's adapter from the
        # per-skill `providers` dict). It is the vocabulary that the INSTALL-side tools
        # read to decide which discovery roots a home binds:
        #   * tools/migrate-legacy-install.ps1:562-570 loads it into $script:KnownProviders
        #     and New-MigrationPlan (:907-915) then requires a discovery root for EVERY
        #     name in it -- a provider with no root is a hard UNKNOWN_PROVIDER_ROOT block
        #     that refuses the whole migration.
        #   * tools/inspect-host-install.ps1:349-356,602 loads the same vocabulary.
        #
        # tools/skill-mesh-discovery.ps1 is the sole owner of the provider -> root map
        # and knows only claude/gpt. Declaring `codex` HERE while that map lacks it
        # would not add a capability, it would BREAK the migrator for every consumer
        # home until the map catches up -- so the two must land in the same commit.
        # That commit is Phase CP Step 5, which owns skill-mesh-discovery.ps1 and the
        # installer; and Step 5 is the earliest it CAN land, because D-CP6 defers the
        # `.agents/skills` root policy (that root is currently Copilot's never-install
        # active alternate) to M1 evidence rather than pre-building it.
        #
        # Step 3's own surface -- per-skill `providers.codex` paths, the codex counts
        # above, `-Provider codex` emission -- needs none of this, so the generation
        # rails ship now and the install vocabulary follows in Step 5.
        "providers": {
            "claude": {"host": "Claude Code", "transport_default": "host-native"},
            "gpt": {"host": "GitHub Copilot / GPT", "transport_default": "copilot"},
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
        # The codex roster, on the same footing as the two above. Orthogonal to them:
        # every name here is ALSO in `portable` (see CODEX / derived_skill_sets).
        "codex": sorted(CODEX),
        "local_capable": sorted(LOCAL_CAPABLE),
        "sub_agent": sorted(SUB_AGENT),
        "vision": sorted(VISION),
        "skills": [
            {
                "name": s["name"],
                "status": s["status"],
                "local_capable": s["local_capable"],
                "capabilities": s["capabilities"],
                "migration": s["migration"],
                "support_assets": s["support_assets"],
            }
            for s in skills
        ],
        "global_support_assets": global_assets,
    }
    return manifest, fixture


def serialize(doc) -> str:
    """The ONE serializer for both artifacts: UTF-8, no BOM, 2-space indent, trailing
    newline. Returns TEXT with "\\n" separators; the writer below decides the bytes."""
    return json.dumps(doc, indent=2) + "\n"


# The two generated artifacts, relative to the tree they are written into.
ARTIFACTS = ("config/skill-manifest.json",
             "tests/package-integrity/expected_inventory.json")


def write_artifacts(out_root: Path):
    """Build and write both artifacts under `out_root`. Returns the manifest.

    `out_root` is a parameter so the regeneration gate can drive the REAL production
    write path into a temporary tree instead of over the committed files.

    LINE ENDINGS -- deliberate, and the reason every comparison against these files
    normalizes. `write_text` emits the PLATFORM line ending, which is the same
    convention git's checkout applies here: this repository has no .gitattributes and
    core.autocrlf=true, so the committed copies are CRLF in a Windows checkout and LF
    in a POSIX one. Matching the platform is what keeps `git status` clean after a
    regeneration on either. It also means the raw bytes of a regenerated artifact are
    a property of the CHECKOUT, never of the content -- so a gate that compares them
    raw passes in one clone and fails in another. Normalize (strip a UTF-8 BOM, then
    CRLF/CR -> LF) on BOTH sides, exactly as the release tooling already does for
    `dist/`.
    """
    manifest, fixture = build()
    for rel, doc in zip(ARTIFACTS, (manifest, fixture)):
        path = out_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialize(doc), encoding="utf-8")
    return manifest


def main():
    # No arguments, no environment: generation is hermetic. The parser is kept with an
    # empty argument set on purpose, so a stale invocation still carrying the retired
    # --legacy-source flag fails loudly ("unrecognized arguments") instead of being
    # silently accepted and ignored.
    argparse.ArgumentParser(description="Regenerate the skill manifest + fixture "
                                        "from this repository alone.").parse_args()
    manifest = write_artifacts(REPO_ROOT)
    print(f"counts: {manifest['counts']}")
    print("wrote " + " and ".join(ARTIFACTS))


if __name__ == "__main__":
    main()
