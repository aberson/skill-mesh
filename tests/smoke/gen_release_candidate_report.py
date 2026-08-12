"""
Regenerate documentation/release-candidate-report.md from a REAL hermetic smoke
run of the neutral router (Step 40 of
documentation/provider-neutral-skill-mesh-plan.md).

Runnable standalone:

    python tests/smoke/gen_release_candidate_report.py

Also imported by tests/smoke/test_release_candidate_report.py, which
regenerates the report into memory and diffs it against the committed file --
so the committed report can never silently go stale relative to what a real
run of runtime/skill-router.ps1 actually does.

Per-column provenance (post-review honesty fix -- see the preamble text this
module writes into the report itself): "Adapter Selected", "Transport",
"Verdict", "Exit Code", and "Fallback Disclosure" are captured directly from a
real subprocess invocation of the router for that row (dry-run rows invoke
with `-DryRun`; live rows perform a real, hermetic invocation). "Core SHA-256"
is NOT read from a subprocess call -- it is a client-side fingerprint of the
single canonical core.md that tests/smoke/_scenarios.canonical_core()
independently confirms BOTH the Claude and GPT provider adapters reference (by
parsing each adapter's own DECLARED core reference out of its real file
content -- not a positional guess and not a bare substring-presence check --
resolving it relative to that adapter's own directory, and asserting the two
resolved paths match); a skill whose two adapters disagreed would raise there
before this report could even be regenerated. No path in the generated report
references coding-root's
private legacy `.claude` layout or an operator-local absolute path -- every
path is repo-relative.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _scenarios as sc  # noqa: E402

REPORT_PATH = sc.REPO_ROOT / "documentation" / "release-candidate-report.md"

COLUMNS = [
    "Family",
    "Skill",
    "Scenario",
    "Adapter Selected",
    "Core SHA-256",
    "Transport",
    "Verdict",
    "Exit Code",
    "Fallback Disclosure",
]

# Single source of truth for "how many scenario rows per representative skill"
# -- shared with tests/smoke/test_release_candidate_report.py so the row-count
# gate there can never silently drift from what this generator actually emits.
SCENARIO_FUNCS = [
    sc.claude_dry_run,
    sc.gpt_dry_run,
    sc.claude_live_run,
    sc.gpt_copilot_live,
    sc.gpt_fallback_to_claude,
    sc.gpt_auth_failure_secret_redaction,
]
SCENARIOS_PER_SKILL = len(SCENARIO_FUNCS)


def _repo_relative(path_str):
    try:
        return Path(path_str).resolve().relative_to(sc.REPO_ROOT).as_posix()
    except (ValueError, TypeError):
        return "n/a"


def _row_to_cells(family, row):
    return [
        family,
        row["skill"],
        row["scenario"],
        _repo_relative(row["adapter"]) if row["adapter"] else "n/a",
        row["core_hash"] or "n/a",
        row["transport"],
        row["verdict"],
        str(row["exit_code"]),
        row["fallback"],
    ]


def collect_rows():
    """Run every Step-40 scenario for every representative skill and return
    [(family, row_dict), ...] in a stable (family, scenario) order."""
    families = sc.load_representative_skills()
    rows = []
    for family, skill in sorted(families.items()):
        for scenario_fn in SCENARIO_FUNCS:
            rows.append((family, scenario_fn(skill)))
    return rows


def generate():
    rows = collect_rows()
    lines = [
        "<!-- GENERATED FILE - DO NOT EDIT BY HAND -->",
        "<!-- Regenerate: python tests/smoke/gen_release_candidate_report.py -->",
        "<!-- Source: tests/fixtures/representative_skills.json + a real hermetic "
        "smoke run of runtime/skill-router.ps1 (tests/smoke/_scenarios.py) -->",
        "",
        "# Release Candidate Report",
        "",
        "One representative skill per skill family (planning, review, "
        "build-orchestration, session -- see "
        "`tests/fixtures/representative_skills.json`) is run through the neutral "
        "router (`runtime/skill-router.ps1`) in a hermetic environment: a fake "
        "Copilot token (no real `gh auth token` call), loopback-only mock "
        "transports, and no real network call (see `tests/smoke/_scenarios.py`).",
        "",
        "**Column provenance.** `Adapter Selected`, `Transport`, `Verdict`, "
        "`Exit Code`, and `Fallback Disclosure` are captured directly from a "
        "real subprocess invocation of the router for that row (dry-run rows "
        "invoke with `-DryRun` and can only prove adapter *resolution*; the "
        "`claude live invocation` / `gpt live invocation via Copilot` rows are "
        "real, non-dry-run calls asserted from a provider-conditioned signal "
        "and are the genuine provider-*selection* proof). `Core SHA-256` is "
        "**not** read from a subprocess call -- it is a client-side fingerprint "
        "of the single canonical `core.md` that both the Claude and GPT "
        "provider adapters are independently confirmed to reference: each "
        "adapter's own declared `Core:` (or markdown-link) reference is parsed "
        "out of that adapter's real file content, resolved relative to that "
        "adapter's own directory, and the two resolved paths are asserted "
        "equal; a skill whose two adapters disagreed -- including a decoy "
        "`../core.md` substring surviving elsewhere in the file while the real "
        "declared reference pointed elsewhere -- would fail that check before "
        "this report could be regenerated. The fingerprint is taken over "
        "CONTENT, not over one checkout's byte representation: CRLF is "
        "normalized to LF and a BOM is stripped before hashing, the same rule "
        "the release tooling applies to the generated tree. Without that, the "
        "hash records the line-ending configuration of whichever clone last "
        "regenerated this file, and the gate goes red on an identical git blob.",
        "",
        "| " + " | ".join(COLUMNS) + " |",
        "|" + "|".join(["---"] * len(COLUMNS)) + "|",
    ]
    for family, row in rows:
        lines.append("| " + " | ".join(_row_to_cells(family, row)) + " |")
    lines.append("")
    return "\n".join(lines) + "\n"


def main():
    text = generate()
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
