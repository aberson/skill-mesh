"""
calibrate.py -- Skill-mesh calibration harness (neutral home).

Runs a skill against both Claude and GPT, records quality metrics,
and produces a calibration-baseline.json entry.

Re-homed from the legacy .claude/lib/calibration/ tree into tests/calibration/
(Step 34). It has NO dependency on a .claude source root: the router it drives is
runtime/skill-router.ps1 and all paths resolve relative to the repository root.

Usage:
    python calibrate.py --skill plan-init --input prompts/plan-init.json --spec specs/plan-init.json
    python calibrate.py --pilot          # Run all 3 pilot skills (plan-init, build-step, review-gauntlet)
    python calibrate.py --list           # List available pilot specs

Requirements:
    ANTHROPIC_API_KEY and OPENAI_API_KEY must be set in the environment for real
    (non-stub) measurement. See documentation/providers/ for key conventions.

Output:
    tests/calibration/calibration-baseline.json (created or updated; gitignored)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Repository root is 2 levels up from tests/calibration/.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_DIR = Path(__file__).resolve().parent
BASELINE_PATH = CALIBRATION_DIR / "calibration-baseline.json"
PILOTS_DIR = CALIBRATION_DIR / "pilots"

# ---------------------------------------------------------------------------
# Quality assessment
# ---------------------------------------------------------------------------


def assess_deterministic(actual: str, expected_spec: dict[str, Any]) -> dict[str, Any]:
    """
    Deterministic quality check: diff actual output against expected_spec.
    Used for structured JSON output, exit codes, counts.

    expected_spec fields:
        required_keys: list of JSON keys that must exist in actual (if output is JSON)
        forbidden_strings: list of strings that must NOT appear in actual
        required_strings: list of strings that must appear in actual
        min_length: minimum character length of actual output
    """
    result = {"mode": "deterministic", "pass": True, "findings": []}

    # Check required_strings
    for s in expected_spec.get("required_strings", []):
        if s not in actual:
            result["pass"] = False
            result["findings"].append(f"MISSING required string: {s!r}")

    # Check forbidden_strings
    for s in expected_spec.get("forbidden_strings", []):
        if s in actual:
            result["pass"] = False
            result["findings"].append(f"FOUND forbidden string: {s!r}")

    # Check min_length
    min_len = expected_spec.get("min_length", 0)
    if len(actual) < min_len:
        result["pass"] = False
        result["findings"].append(f"Output too short: {len(actual)} < {min_len}")

    # Check required_keys (if output is JSON)
    required_keys = expected_spec.get("required_keys", [])
    if required_keys:
        try:
            parsed = json.loads(actual)
            for key in required_keys:
                if key not in parsed:
                    result["pass"] = False
                    result["findings"].append(f"MISSING required JSON key: {key!r}")
        except json.JSONDecodeError as exc:
            result["pass"] = False
            result["findings"].append(f"Output is not valid JSON: {exc}")

    return result


def assess_rubric(actual: str, expected_spec: dict[str, Any]) -> dict[str, Any]:
    """
    Section-coverage rubric check for prose outputs (plans, reviews).
    Used for plan-init, review-gauntlet, etc.

    expected_spec fields:
        required_sections: list of section heading strings that must appear in actual
        optional_sections: list of section headings that improve coverage if present
        min_section_count: minimum number of required_sections that must be present
    """
    result = {"mode": "rubric", "pass": True, "findings": [], "coverage": {}}

    required = expected_spec.get("required_sections", [])
    optional = expected_spec.get("optional_sections", [])
    min_count = expected_spec.get("min_section_count", len(required))

    found_required = []
    missing_required = []
    found_optional = []

    for section in required:
        if section.lower() in actual.lower():
            found_required.append(section)
        else:
            missing_required.append(section)

    for section in optional:
        if section.lower() in actual.lower():
            found_optional.append(section)

    coverage_pct = len(found_required) / len(required) * 100 if required else 100.0
    result["coverage"] = {
        "required_found": found_required,
        "required_missing": missing_required,
        "optional_found": found_optional,
        "coverage_pct": round(coverage_pct, 1),
    }

    if len(found_required) < min_count:
        result["pass"] = False
        result["findings"].append(
            f"Section coverage {len(found_required)}/{len(required)} below minimum {min_count}: "
            f"missing {missing_required}"
        )

    return result


# ---------------------------------------------------------------------------
# Model invocation stubs
# ---------------------------------------------------------------------------


def invoke_model(model: str, skill: str, prompt: str) -> dict[str, Any]:
    """
    Invoke a skill on the specified model.
    Returns: {output: str, tokens_prompt: int, tokens_completion: int,
              latency_ms: int, cost_usd: float, error: str|None}

    Claude is invoked natively via the host skill pipeline; GPT invocation requires
    OPENAI_API_KEY. Both remain stubs here -- real measurement requires live
    credentials and a running provider.
    """
    start = time.monotonic()

    if model == "claude":
        return {
            "output": f"[STUB] Claude output for skill={skill}. Run inside Claude session to capture real output.",
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "latency_ms": int((time.monotonic() - start) * 1000),
            "cost_usd": 0.0,
            "error": "STUB: requires live Claude session for real measurement",
        }

    elif model == "gpt":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {
                "output": "",
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "latency_ms": 0,
                "cost_usd": 0.0,
                "error": "OPENAI_API_KEY not set. Configure credentials before running GPT calibration.",
            }
        return {
            "output": "",
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "latency_ms": 0,
            "cost_usd": 0.0,
            "error": f"GPT variant for skill={skill} not yet wired for live calibration.",
        }

    else:
        return {
            "output": "",
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "latency_ms": 0,
            "cost_usd": 0.0,
            "error": f"Unknown model: {model!r}",
        }


# ---------------------------------------------------------------------------
# Calibration run
# ---------------------------------------------------------------------------


def run_calibration(
    skill: str,
    prompt: str,
    spec: dict[str, Any],
    models: list[str] | None = None,
    session_tier: str | None = None,
) -> dict[str, Any]:
    """
    Run calibration for a skill on all requested models.
    Returns a calibration record suitable for calibration-baseline.json.
    """
    if models is None:
        models = ["claude", "gpt"]

    record: dict[str, Any] = {
        "skill": skill,
        "timestamp": _utcnow(),
        "prompt_length": len(prompt),
        "spec_mode": spec.get("mode", "rubric"),
        "models": {},
    }
    if session_tier is not None:
        record["session_tier"] = session_tier

    for model in models:
        invocation = invoke_model(model, skill, prompt)
        if invocation.get("error"):
            quality = {
                "mode": spec.get("mode", "rubric"),
                "pass": False,
                "findings": [f"Invocation error: {invocation['error']}"],
            }
        elif spec.get("mode") == "deterministic":
            quality = assess_deterministic(invocation["output"], spec)
        else:
            quality = assess_rubric(invocation["output"], spec)

        record["models"][model] = {
            "tokens_prompt": invocation["tokens_prompt"],
            "tokens_completion": invocation["tokens_completion"],
            "latency_ms": invocation["latency_ms"],
            "cost_usd": invocation["cost_usd"],
            "verdict": "PASS" if quality["pass"] else "FAIL",
            "quality": quality,
            "error": invocation.get("error"),
        }

    return record


# ---------------------------------------------------------------------------
# Baseline JSON management
# ---------------------------------------------------------------------------


def load_baseline() -> dict[str, Any]:
    """Load existing calibration-baseline.json, or return a fresh skeleton."""
    if BASELINE_PATH.exists():
        with open(BASELINE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {
        "schema_version": "1.0",
        "description": (
            "Calibration baseline: quality metrics for skill outputs on Claude vs GPT. "
            "Generated by tests/calibration/calibrate.py"
        ),
        "quality_methodology": {
            "deterministic": (
                "Structured/JSON outputs: diff actual against required_keys, "
                "required_strings, forbidden_strings, min_length thresholds."
            ),
            "rubric": (
                "Prose outputs (plans, reviews): section-coverage rubric -- "
                "required_sections must appear; coverage_pct >= min_section_count/total."
            ),
        },
        "pilots": {},
    }


def save_baseline(baseline: dict[str, Any]) -> None:
    """Save calibration-baseline.json (UTF-8, no BOM)."""
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(baseline, f, indent=2)
        f.write("\n")


def update_baseline(skill: str, record: dict[str, Any]) -> None:
    """Upsert a calibration record into the baseline JSON."""
    baseline = load_baseline()
    baseline.setdefault("pilots", {})[skill] = record
    save_baseline(baseline)
    print(f"calibrate: baseline updated for {skill!r} -> {BASELINE_PATH}")


# ---------------------------------------------------------------------------
# Pilot specs
# ---------------------------------------------------------------------------

PILOT_SPECS: dict[str, dict[str, Any]] = {
    "plan-init": {
        "mode": "rubric",
        "description": "plan-init produces a plan.md for a greenfield project.",
        "prompt": (
            "Create a plan for a new CLI tool that tracks daily TODO items in a SQLite database. "
            "The tool should support add/list/done/delete commands. "
            "Use Python 3.12, uv for dependency management, and pytest for testing."
        ),
        "spec": {
            "mode": "rubric",
            "required_sections": [
                "## Phase", "Goal", "Stack", "Step", "Done when"
            ],
            "optional_sections": [
                "## Manual UAT", "Risk", "Testing"
            ],
            "min_section_count": 4,
        },
    },
    "build-step": {
        "mode": "deterministic",
        "description": "build-step produces a verdict.json with result field.",
        "prompt": (
            "Add a --verbose flag to the CLI that prints each SQL query before executing it. "
            "Files: src/cli.py. Tests: tests/test_cli.py."
        ),
        "spec": {
            "mode": "deterministic",
            "required_keys": ["result", "halt"],
            "min_length": 10,
            "required_strings": [],
            "forbidden_strings": [],
        },
    },
    "review-gauntlet": {
        "mode": "rubric",
        "description": "review-gauntlet produces a PASS/NEEDS-WORK verdict with findings.",
        "prompt": (
            "Review this diff: "
            "```python\n"
            "-def add_todo(db, text):\n"
            "+def add_todo(db, text, priority=None):\n"
            "     db.execute('INSERT INTO todos (text) VALUES (?)', (text,))\n"
            "```"
        ),
        "spec": {
            "mode": "rubric",
            "required_sections": ["PASS", "NEEDS-WORK", "Verdict", "Finding"],
            "min_section_count": 1,
            "optional_sections": ["Security", "Test", "Correctness"],
        },
    },
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Skill-mesh calibration harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--skill", help="Skill name to calibrate (e.g. plan-init)")
    parser.add_argument("--input", help="Path to JSON file with prompt field")
    parser.add_argument("--spec", help="Path to JSON file with quality spec")
    parser.add_argument(
        "--pilot", action="store_true",
        help="Run all 3 pilot skills (plan-init, build-step, review-gauntlet)"
    )
    parser.add_argument("--list", action="store_true", help="List available pilot specs")
    parser.add_argument(
        "--models", default="claude,gpt",
        help="Comma-separated list of models to run (default: claude,gpt)"
    )
    parser.add_argument(
        "--session-tier",
        help="Optional active Claude tier hint to record in baseline metadata",
    )
    args = parser.parse_args(argv)

    if args.list:
        print("Available pilot specs:")
        for name, spec in PILOT_SPECS.items():
            print(f"  {name}: {spec['description']}")
        return 0

    models = [m.strip() for m in args.models.split(",")]

    if args.pilot:
        print(f"Running calibration for all 3 pilot skills on models: {models}")
        for skill_name, pilot in PILOT_SPECS.items():
            print(f"\n  Calibrating {skill_name!r}...")
            record = run_calibration(
                skill_name,
                pilot["prompt"],
                pilot["spec"],
                models,
                session_tier=args.session_tier,
            )
            update_baseline(skill_name, record)
            for model in models:
                m_result = record["models"].get(model, {})
                verdict = m_result.get("verdict", "N/A")
                error = m_result.get("error", "")
                err_note = f" [{error}]" if error else ""
                print(f"    {model}: {verdict}{err_note}")
        print(f"\nBaseline written to: {BASELINE_PATH}")
        return 0

    if args.skill:
        # Load prompt and spec
        if args.input:
            with open(args.input, encoding="utf-8") as f:
                data = json.load(f)
            prompt = data.get("prompt", "")
        elif args.skill in PILOT_SPECS:
            prompt = PILOT_SPECS[args.skill]["prompt"]
        else:
            print(f"ERROR: --input required for non-pilot skill {args.skill!r}", file=sys.stderr)
            return 1

        if args.spec:
            with open(args.spec, encoding="utf-8") as f:
                spec = json.load(f)
        elif args.skill in PILOT_SPECS:
            spec = PILOT_SPECS[args.skill]["spec"]
        else:
            print(f"ERROR: --spec required for non-pilot skill {args.skill!r}", file=sys.stderr)
            return 1

        record = run_calibration(
            args.skill,
            prompt,
            spec,
            models,
            session_tier=args.session_tier,
        )
        update_baseline(args.skill, record)

        for model in models:
            m_result = record["models"].get(model, {})
            print(f"  {model}: {m_result.get('verdict', 'N/A')}")
            if m_result.get("error"):
                print(f"    Error: {m_result['error']}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
