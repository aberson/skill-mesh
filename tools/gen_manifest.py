"""Generate config/skill-manifest.json and tests/package-integrity/expected_inventory.json.

Authoritative structural data (names, status, local_capable, capabilities) is
encoded here as checked-in constants derived from evidence in the READ-ONLY legacy
source (.claude/references/model-mapping.md and each skill's SKILL contract).

Skill-local support-asset lists are scanned from the legacy source at generation
time and baked statically into the committed manifest + fixture, so the published
package tests never need the private source to run. Re-run only when the legacy
source or the authoritative constants change.

Usage:
    $env:SKILL_MESH_LEGACY_SOURCE = "<coding-root>"   # e.g. the operator checkout
    python tools/gen_manifest.py
  or:
    python tools/gen_manifest.py --legacy-source <coding-root>

No absolute private path is embedded: the legacy source root must be supplied via
--legacy-source or the SKILL_MESH_LEGACY_SOURCE environment variable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---- Authoritative structural constants (evidence-grounded) ----------------

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

# local-capable=Y rows of .claude/references/model-mapping.md (authoritative table).
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
VISION = {"judge-ui", "judge-motion"}

# Per-skill one-line `description`, the SINGLE source of truth for the SKILL.md
# frontmatter description the builder emits (GitHub Copilot CLI requires every
# generated SKILL.md to LEAD with a YAML frontmatter block carrying at least
# `name` + `description`; Step 44). Encoded here as a checked-in, evidence-grounded
# constant exactly like PORTABLE / NATIVE / LOCAL_CAPABLE above -- the evidence is
# each skill's own SKILL contract (its legacy `.claude/skills/<name>/SKILL.md`
# description and canonical core.md purpose). Baking it in (rather than re-reading
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

# Directory names never migrated (build output / cache / scratch).
ASSET_EXCLUDE_DIRS = {"node_modules", ".pytest_cache", "__pycache__", "tmp",
                      ".judge-motion"}


def scan_skill_assets(legacy_root: Path, name: str):
    """Return (source, dest) support-asset pairs for one skill.

    source is coding-root-relative; dest is the canonical package path.
    """
    assets = []
    for tree in ("skills", "skills-gpt"):
        base = legacy_root / ".claude" / tree / name
        if not base.is_dir():
            continue
        for entry in sorted(base.iterdir(), key=lambda p: p.name):
            if entry.is_file():
                if entry.name.startswith("SKILL") and entry.suffix == ".md":
                    continue
                rel = entry.name
                assets.append({
                    "source": f".claude/{tree}/{name}/{rel}",
                    "dest": f"skills/{name}/{rel}",
                })
            elif entry.is_dir():
                if entry.name in ASSET_EXCLUDE_DIRS or entry.name.startswith("."):
                    continue
                assets.append({
                    "source": f".claude/{tree}/{name}/{entry.name}/",
                    "dest": f"skills/{name}/{entry.name}/",
                })
    return assets


def build(legacy_root: Path):
    # Fail loud if a skill lacks a frontmatter description: the builder needs one
    # for every published skill, and a silently-missing entry would ship an
    # incomplete SKILL.md frontmatter to a Copilot host.
    missing_desc = sorted(set(PORTABLE + NATIVE) - set(DESCRIPTIONS))
    if missing_desc:
        raise KeyError(f"DESCRIPTIONS missing entries for: {missing_desc}")
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
            "support_assets": scan_skill_assets(legacy_root, name),
        })

    counts = {
        "total": len(skills),
        "portable": sum(1 for s in skills if s["status"] == "portable"),
        "provider_native": sum(1 for s in skills if s["status"] == "provider-native"),
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy-source",
                    default=os.environ.get("SKILL_MESH_LEGACY_SOURCE"))
    args = ap.parse_args()
    if not args.legacy_source:
        sys.exit("error: set SKILL_MESH_LEGACY_SOURCE or pass --legacy-source "
                 "(the READ-ONLY coding-root checkout)")
    legacy_root = Path(args.legacy_source)
    manifest, fixture = build(legacy_root)

    (REPO_ROOT / "config" / "skill-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (REPO_ROOT / "tests" / "package-integrity" / "expected_inventory.json").write_text(
        json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print(f"counts: {manifest['counts']}")
    print("wrote config/skill-manifest.json and "
          "tests/package-integrity/expected_inventory.json")


if __name__ == "__main__":
    main()
