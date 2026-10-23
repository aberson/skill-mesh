#!/usr/bin/env python3
"""review-deep multi-lens verdict aggregator.

Reads per-lens verdict JSON files from --lens-dir (one file per lens, named
<lens_id>.json), applies the seven aggregator rules, writes the audit-trail
JSON sidecar to <--output-dir>/<timestamp>.json, and prints the human-readable
markdown summary to stdout.

Canonical prose: SKILL.md (Aggregation section). This module is the executable
implementation of the contract summarized there. Schema fields, severity
semantics, lens ordering, and M-numbering rules are all sourced from SKILL.md;
the two sites are joint owners of the schema. Renames or shape changes MUST
touch both sites in the same diff (producer-consumer-drift prevention; see
dev/.claude/rules/code-quality.md).

Aggregator rules implemented (each as apply_rule_N_<desc>):

1. Severity dominance: Block outweighs any Nit count; the aggregated verdict
   is driven by the highest-severity finding across lenses, not finding count.
2. Lens owns its dimension: when two lenses disagree on the same file_line,
   the lens whose Scope covers that dimension wins; the other is demoted to
   FYI. Catalog Lens-routing fields drive primary/secondary selection.
3. SKIPPED handling: an ALLOWED SKIPPED lens is informational and does NOT
   contribute to NEEDS-WORK. SKIPPED is allowed only for plan-conformance
   without a plan step, or for the six code lenses under --reviewers runtime;
   any other SKIPPED is a required lens skipped (NEEDS-WORK, see below).
4. FAILED handling: a FAILED lens (model overloaded after retry) maps to
   NEEDS-WORK at the aggregated level; the failure_reason surfaces in the
   aggregated rationale.
5. NO-EVIDENCE handling: NO-EVIDENCE means the lens could not see diff
   content (inputs-gathering bug). Maps to NEEDS-WORK so the operator notices
   and fixes the input rather than accepting a vacuous PASS.
6. Persistent disagreement: when --prior-sidecar is supplied AND the current
   run flags the same finding identity (file_line + anti_pattern + severity)
   that a prior run demoted under rule 2, escalate the severity by one tier
   and annotate the rationale.
7. Absence-of-thing dedup AND lint-finding dedup: two independent paths in
   the same rule. (a) Absence path: when multiple lenses surface findings
   about the same absence (no concrete file_line anchor in the diff), dedup
   by (anti_pattern, summary fuzzy-match) and demote duplicates to FYI;
   primary lens is the catalog Lens-routing target or first-emit order.
   (b) Lint path: when lint-findings.json is supplied (via --lint-findings
   or auto-discovered at <output-dir>/lint-findings.json), any lens finding
   sharing a concrete file_line with a lint finding demotes to FYI with
   rationale prefixed "Cited-by-linter: <tool> <rule>" and an
   also_flagged_by_linter annotation.

Default-deny PASS (P-RD-1 variant (a); the sidecar result enum stays
PASS | NEEDS-WORK | DEFERRED-TO-UAT). The aggregated result is PASS only when
every required lens is present exactly once with overall_verdict PASS (or an
allowed SKIPPED, rule 3), zero Block, aggregated Nit < 3, no failed or invalid
mechanical result and no deferral. Everything else is NEEDS-WORK with an
explicit rationale, including: a lens UNCERTAIN (abstention -- escalate to the
operator, never PASS), NEEDS-CLARIFICATION, an unknown or missing
overall_verdict, a missing / duplicate / unexpected lens, a lens file whose
name is not <lens_id>.json, a required lens SKIPPED, no runtime lens under
--reviewers runtime (or full without a recorded downgrade), a recorded runtime
downgrade under --reviewers runtime, a runtime lens record under a recorded
downgrade, a SKIPPED lens carrying findings, a PASS lens carrying Block/Nit
findings, an invalid finding severity, and a mechanical check whose status is
"fail" or a malformed mechanical record -- including a supplied record that is
not a JSON object, such as null ("missing-tool" is listed in the rationale and
does not block). A structurally malformed lens record (not an object, no string
lens_id, findings not a list), a sidecar-shaped file in --lens-dir, or a
duplicate JSON key in a lens file is rejected with ValueError; the CLI exits
non-zero and writes no sidecar (a duplicate key in --mechanical-results
likewise exits 2).

CLI:

    python aggregate.py \\
      --lens-dir <path>            # required; FRESH dir holding only this run's lens files
      --output-dir <path>          # required; sidecar lands here
      --skill-version <v>          # default "v3"
      --prior-sidecar <path>       # optional; enables rule 6
      --lint-findings <path>       # optional; enables rule 7's lint-dedup path
      --mechanical-results <path>  # optional; {"checks":[{check,status,command,evidence}]}
      --plan-step <path>:<step-id> # optional; id after the last colon; recorded as plan_step
      --reviewers code|runtime|full  # default code; drives lens-set completeness
      --force-runtime              # optional; recorded in invocation
      --runtime-downgrade-reason <token>  # optional; recorded in invocation
      [--timestamp <ISO>]          # optional override (for round-trip tests)
      [--self-test <m1-sidecar>]   # round-trip test against an M1 sidecar

Each option is given at most once: repeating an option that takes a value
(as `--opt value` or `--opt=value`) exits 2 and writes no sidecar.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """A single finding from one lens.

    Fields:
        severity: 'Block' | 'Nit' | 'FYI' (one of three exact strings, per the
            universal severity rubric at SKILL.md top of "Reviewer lenses").
        file_line: Source location, e.g. 'src/foo.py:42' or 'src/foo.py:42-45'.
            For absence-of-thing findings, this may describe the missing
            artifact ('(absence -- no integration test for X)') rather than a
            concrete path:line.
        excerpt: Exact text being cited (diff line, surrounding context, or
            plan excerpt for plan-conformance). Empty excerpt demotes the
            finding one severity tier per universal evidence discipline.
        rationale: 1-3 sentence explanation citing primary-source evidence,
            referencing the lens's coverage claim, the dev's intent, the named
            plan step, or an anti-pattern from the catalog.
        anti_pattern: OPTIONAL kebab-case name from the seven-entry catalog
            (silent-wiring, producer-consumer-drift, codifying-test-diff,
            silent-fallthrough-in-loop, silent-fallthrough-in-hot-path,
            duplicate-shape-constants, create-table-without-migration). Plus
            the reserved wire-format marker 'scope-boundary-deferral' (NOT
            a defect; signals operator UAT hand-off).

    Post-aggregation annotations (NOT dataclass attributes; applied via dict
    mutation in apply_rule_7_absence_dedup; documented here so a future
    maintainer reading a sidecar does not treat them as stray keys):
        also_flagged_by: Optional list of lens_id strings -- populated by
            rule 7's absence-dedup path when a finding clusters with sibling
            findings from other lenses at the same conceptual absence.
            Post-aggregation annotation only; not in raw lens output.
        also_flagged_by_linter: Optional ``{tool, rule}`` dict -- populated by
            rule 7's lint-dedup path when a lint finding's file_line overlaps
            the lens finding's file_line. Post-aggregation annotation only;
            not in raw lens output.
    """

    severity: str
    file_line: str
    excerpt: str
    rationale: str
    anti_pattern: str | None = None


@dataclass(frozen=True)
class LensVerdict:
    """One lens's verdict block.

    Six standing code lenses (correctness, bugs, security, test-quality, style,
    plan-conformance) plus optional runtime lenses (ui, backend, frontend).

    Fields:
        lens_id: Lens identifier; one of 'correctness' | 'bugs' | 'security' |
            'test-quality' | 'style' | 'plan-conformance' (code lenses) or
            a runtime lens id ('ui' | 'backend' | 'frontend').
        model_tier: Tier the lens actually ran on after --model-override
            resolution: 'haiku' | 'sonnet' | 'opus'. For SKIPPED lenses,
            reports the tier that WOULD have been used (no nulls).
        authority: One-line summary of what this lens owns (from the lens's
            Scope section). Used by the markdown summary and the
            "lens owns its dimension" aggregator rule.
        coverage_claim: What this lens promises to detect (from the lens's
            Coverage claim section).
        findings: List of Finding dicts; MUST be an empty list (not None) when
            overall_verdict == 'PASS' / 'SKIPPED'.
        overall_verdict: One of 'PASS' | 'NEEDS-WORK' | 'UNCERTAIN' |
            'NO-EVIDENCE' | 'FAILED' | 'SKIPPED' | 'NEEDS-CLARIFICATION'
            (LENS_VERDICTS). See SKILL.md Model strategy section's enum
            table for the canonical set. Only PASS and an allowed SKIPPED
            can contribute to an aggregated PASS; every other value,
            including an unknown or missing one, aggregates to NEEDS-WORK.
        failure_reason: OPTIONAL; present only when overall_verdict == FAILED.
            Current allowed values: 'model_overloaded'. Cross-step contract
            with SKILL.md Model strategy section -- adding a value requires
            updating both sites in the same diff.
    """

    lens_id: str
    model_tier: str
    authority: str
    coverage_claim: str
    findings: list
    overall_verdict: str
    failure_reason: str | None = None


# Fixed code-lens spawn order, used by aggregator rule 7 primary-lens selection
# and by the markdown summary's lens-verdicts subsection. The 'security' lens is
# promoted out of 'bugs' (SKILL.md Security lens) and slots after it so a
# security-class defect both Bugs and Security flag routes to Security as primary
# (via ANTI_PATTERN_PRIMARY below, not spawn order, but the position keeps the
# documented order coherent). Cross-step contract with SKILL.md "Standing lens
# list" + Aggregation section -- a rename or reorder MUST touch both sites.
CODE_LENS_ORDER = [
    "correctness",
    "bugs",
    "security",
    "test-quality",
    "style",
    "plan-conformance",
]

# Anti-pattern catalog Lens-routing table -- the (primary, secondary) pair per
# catalog entry as documented in SKILL.md Anti-pattern catalog section. Used by
# aggregator rules 2 and 7 to resolve cross-lens primaries. The three
# security-class defect classes (injection-as-data, secret-dump,
# unsafe-config-without-startup-guard, per .claude/rules/security.md) route to
# the Security lens as PRIMARY OWNER -- a finding both Bugs and Security flag at
# the same file_line is owned by Security and the Bugs copy demotes to FYI
# (SKILL.md Aggregation § rule 2: "Security is the registered PRIMARY OWNER of
# security findings").
ANTI_PATTERN_PRIMARY = {
    "silent-wiring": "bugs",
    "producer-consumer-drift": "bugs",
    "codifying-test-diff": "test-quality",
    "silent-fallthrough-in-loop": "bugs",
    "silent-fallthrough-in-hot-path": "bugs",
    "duplicate-shape-constants": "bugs",
    "create-table-without-migration": "bugs",
    "injection-as-data": "security",
    "secret-dump": "security",
    "unsafe-config-without-startup-guard": "security",
}

# Severity ordinals for monotonic comparison / demotion / escalation.
SEVERITY_ORDER = {"FYI": 0, "Nit": 1, "Block": 2}

# Complete per-lens overall_verdict enum (SKILL.md "Per-lens overall_verdict
# enum"). Cross-step contract: a new value MUST touch both sites.
LENS_VERDICTS = (
    "PASS",
    "NEEDS-WORK",
    "UNCERTAIN",
    "NO-EVIDENCE",
    "FAILED",
    "SKIPPED",
    "NEEDS-CLARIFICATION",
)

# Default-deny: the ONLY lens verdicts that may contribute to an aggregated
# PASS. SKIPPED counts only where rule 3 allows it (check_lens_set).
PASSING_LENS_VERDICTS = ("PASS", "SKIPPED")

# Runtime lens ids (SKILL.md Flag selection); appended after CODE_LENS_ORDER.
RUNTIME_LENS_IDS = ("ui", "backend", "frontend")

# --reviewers lanes (SKILL.md Flag selection); drives lens-set completeness.
REVIEWERS_FLAGS = ("code", "runtime", "full")

# Mechanical-check statuses accepted in --mechanical-results. "fail" is itself
# a verdict (NEEDS-WORK); "missing-tool" is listed but never blocks.
MECHANICAL_STATUSES = ("pass", "fail", "missing-tool")

# Auth-gate probe reason tokens (SKILL.md Auth-gated runtime downgrade).
_RUNTIME_DOWNGRADE_RE = re.compile(
    r"^(?:status_401|login_form_in_200_body|timeout|redirect_to_login:.+)$"
)
# --plan-step <plan-file-path>:<step-id>. The step id is the token after the
# LAST colon -- the <step-id> of a `### Step <step-id>:` heading or the first
# column of a table-format row (12, 5a, 22-prep, 7-1, D.6) -- so a Windows
# drive path keeps its colon. A bare path with no step id is rejected.
_PLAN_STEP_RE = re.compile(r"^.+:[A-Za-z0-9][A-Za-z0-9._-]*$")


def default_invocation(
    reviewers_flag: str = "code",
    *,
    force_runtime: bool = False,
    runtime_downgrade_reason: str | None = None,
) -> dict:
    """The sidecar ``invocation`` object with its fixed seven-key set.

    The key set and order are a cross-step contract (SKILL.md Audit-trail JSON
    sidecar schema; build-step and the Codex recipe validate it). Fields the
    CLI cannot observe (model_overrides, url, start_cmd) keep their legacy
    defaults.
    """
    return {
        "reviewers_flag": reviewers_flag,
        "model_overrides": {},
        "force_runtime": force_runtime,
        "url": None,
        "start_cmd": None,
        "runtime_downgraded": runtime_downgrade_reason is not None,
        "runtime_downgrade_reason": runtime_downgrade_reason,
    }


# ---------------------------------------------------------------------------
# I/O: per-lens verdict loading
# ---------------------------------------------------------------------------


class LensSetError(ValueError):
    """The files in one --lens-dir do not bind one-to-one to lens records.

    Raised by load_lens_verdicts when a file's lens_id differs from its file
    name stem (a record under another name, e.g. a stale ``zz-prev.json``,
    must never fill a slot) or when two records share a lens_id. ``records``
    carries EVERY record in deterministic order and ``problems`` the
    file-binding problems, so the CLI can still reduce them: the problems join
    check_lens_set's and the aggregated verdict is NEEDS-WORK with all
    evidence kept.
    """

    def __init__(self, message: str, records: list[dict], problems: list[str] | None = None):
        super().__init__(message)
        self.records = records
        self.problems = list(problems or [])


class DuplicateLensError(LensSetError):
    """Two lens records in one --lens-dir share a lens_id.

    load_lens_verdicts never lets a later record overwrite an earlier one
    (that silently hid duplicates and let a stale file fill a slot). It raises
    this error instead; ``records`` carries EVERY record in deterministic
    order so the CLI can still reduce them -- check_lens_set then reports the
    duplicate and the aggregated verdict is NEEDS-WORK with all evidence kept.
    """


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    """json object_pairs_hook: a repeated key is an error, never last-wins.

    Parity with the Codex recipe's ``unique_object``: an ambiguous record such
    as ``"overall_verdict": "UNCERTAIN", "overall_verdict": "PASS"`` must not
    reduce as PASS on one host and be rejected on the other.
    """
    obj: dict = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key {key!r}")
        obj[key] = value
    return obj


def load_json_strict(path: Path) -> object:
    """Parse one JSON input file, rejecting duplicate keys (ValueError)."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=_reject_duplicate_keys)


def load_lens_verdicts(lens_dir: Path) -> list[dict]:
    """Read per-lens JSON files from lens_dir.

    Expects one file per lens, named <lens_id>.json, in a FRESH directory that
    holds only this run's lens records (SKILL.md Aggregator rules). Returns a
    list of dicts sorted by the canonical CODE_LENS_ORDER prefix, then any
    other (runtime) lenses by lens_id.

    Only the bare lens-verdict object shape is accepted. A sidecar-shaped file
    (``lens_verdicts`` or ``aggregated_verdict`` key -- a prior run's
    audit-trail JSON) is rejected with ValueError, as is any other shape and
    a file with a duplicate JSON key. Raises LensSetError (a ValueError) when
    a record's lens_id differs from its file name stem, and its subclass
    DuplicateLensError when two records share a lens_id; both carry every
    record. A stale same-name ``<lens_id>.json`` in a reused directory is
    NOT detectable here (records carry no run token); the fresh-directory
    rule owns that case.
    """
    records: list[tuple[str, dict]] = []
    binding_problems: list[str] = []
    for child in sorted(lens_dir.iterdir()):
        if not child.is_file() or child.suffix != ".json":
            continue
        try:
            data = load_json_strict(child)
        except ValueError as e:
            raise ValueError(f"{child}: {e}") from e
        if isinstance(data, dict) and ("lens_verdicts" in data or "aggregated_verdict" in data):
            raise ValueError(
                f"{child}: a review-deep sidecar (audit-trail JSON), not a lens "
                f"record; --lens-dir must be a fresh directory holding only this "
                f"run's <lens_id>.json files"
            )
        if not (isinstance(data, dict) and "lens_id" in data):
            raise ValueError(
                f"{child}: not a recognized lens-verdict shape "
                f"(expected an object with 'lens_id')"
            )
        records.append((child.name, data))
        if data["lens_id"] != child.stem:
            binding_problems.append(
                f"lens file {child.name} holds lens_id {data['lens_id']!r} "
                f"(each record must be in <lens_id>.json)"
            )

    def _order(item: tuple[str, dict]) -> tuple:
        lens_id = item[1]["lens_id"]
        if lens_id in CODE_LENS_ORDER:
            return (0, CODE_LENS_ORDER.index(lens_id), "")
        # Any other lens is a runtime lens; append in deterministic order.
        return (1, 0, str(lens_id))

    # sorted() is stable, so duplicates keep their filename order.
    ordered = [record for _source, record in sorted(records, key=_order)]
    sources: dict[str, list[str]] = {}
    for source, record in records:
        sources.setdefault(str(record["lens_id"]), []).append(source)
    duplicates = {k: v for k, v in sources.items() if len(v) > 1}
    if duplicates:
        detail = "; ".join(f"{k} ({', '.join(v)})" for k, v in sorted(duplicates.items()))
        raise DuplicateLensError(
            f"duplicate lens_id in {lens_dir}: {detail}"
            + "".join(f"; {p}" for p in binding_problems),
            ordered,
            binding_problems,
        )
    if binding_problems:
        raise LensSetError(
            f"lens files in {lens_dir} do not bind to their records: "
            + "; ".join(binding_problems),
            ordered,
            binding_problems,
        )
    return ordered


# ---------------------------------------------------------------------------
# Aggregator rules
# ---------------------------------------------------------------------------


def apply_rule_1_severity_dominance(lens_verdicts: list[dict]) -> dict:
    """Rule 1 -- severity dominates count.

    A single Block finding outweighs any number of Nit findings. The
    aggregated verdict is determined by the highest-severity finding across
    all lenses, not by total finding count.

    Returns a dict with:
        block_count: total Block findings across all non-SKIPPED lenses
        nit_count:   total Nit findings
        fyi_count:   total FYI findings
        max_severity: highest severity present ('Block' | 'Nit' | 'FYI' | None)
    """
    block_count = 0
    nit_count = 0
    fyi_count = 0
    for lv in lens_verdicts:
        if lv.get("overall_verdict") == "SKIPPED":
            continue
        for f in lv.get("findings", []):
            sev = f.get("severity")
            if sev == "Block":
                block_count += 1
            elif sev == "Nit":
                nit_count += 1
            elif sev == "FYI":
                fyi_count += 1
    if block_count > 0:
        max_severity: str | None = "Block"
    elif nit_count > 0:
        max_severity = "Nit"
    elif fyi_count > 0:
        max_severity = "FYI"
    else:
        max_severity = None
    return {
        "block_count": block_count,
        "nit_count": nit_count,
        "fyi_count": fyi_count,
        "max_severity": max_severity,
    }


def apply_rule_2_lens_owns_dimension(lens_verdicts: list[dict]) -> list[dict]:
    """Rule 2 -- lens owns its dimension.

    When two lenses surface findings at the same file_line, the lens with
    authority over that dimension wins; the other lens's finding is demoted
    to FYI. For catalog anti-pattern findings, the primary lens per the
    catalog's Lens-routing field wins.

    Mutates a deep copy of lens_verdicts in place; the demoted finding's
    rationale is prefixed with 'Demoted per rule 2:' so rule 6 can detect
    persistent disagreement on a re-run.
    """
    # Group findings by file_line across lenses.
    by_file_line: dict[str, list[tuple[str, dict]]] = {}
    for lv in lens_verdicts:
        if lv.get("overall_verdict") == "SKIPPED":
            continue
        for f in lv.get("findings", []):
            file_line = f.get("file_line", "")
            if not file_line:
                continue
            by_file_line.setdefault(file_line, []).append((lv["lens_id"], f))

    for _file_line, entries in by_file_line.items():
        if len(entries) < 2:
            continue
        # Find primary -- prefer anti-pattern catalog routing.
        primary_idx = None
        for i, (_lens_id, f) in enumerate(entries):
            ap = f.get("anti_pattern")
            if ap and ANTI_PATTERN_PRIMARY.get(ap) == entries[i][0]:
                primary_idx = i
                break
        if primary_idx is None:
            # Fall back to first-emit-order by CODE_LENS_ORDER.
            primary_idx = min(
                range(len(entries)),
                key=lambda i: (
                    CODE_LENS_ORDER.index(entries[i][0])
                    if entries[i][0] in CODE_LENS_ORDER
                    else 999
                ),
            )
        # Demote all non-primary findings to FYI with annotated rationale.
        for i, (_lens_id, f) in enumerate(entries):
            if i == primary_idx:
                continue
            if f.get("severity") != "FYI":
                f["severity"] = "FYI"
                rationale = f.get("rationale", "")
                if not rationale.startswith("Demoted per rule 2:"):
                    f["rationale"] = f"Demoted per rule 2: {rationale}"
    return lens_verdicts


def apply_rule_3_skipped_handling(lens_verdicts: list[dict]) -> list[str]:
    """Rule 3 -- SKIPPED lenses do not count toward NEEDS-WORK.

    Returns the list of SKIPPED lens_ids so the markdown summary and
    aggregated rationale can note the skips explicitly. The aggregated
    verdict computation in build_aggregated_verdict() ignores SKIPPED
    entries.
    """
    return [
        lv["lens_id"]
        for lv in lens_verdicts
        if lv.get("overall_verdict") == "SKIPPED"
    ]


def apply_rule_4_failed_handling(lens_verdicts: list[dict]) -> list[dict]:
    """Rule 4 -- FAILED lenses surface explicitly and block PASS.

    A FAILED lens (model overloaded after one retry) MUST NOT receive a
    clean PASS at the aggregated level. Returns a list of (lens_id,
    failure_reason) entries for inclusion in the aggregated rationale.
    """
    return [
        {"lens_id": lv["lens_id"], "failure_reason": lv.get("failure_reason")}
        for lv in lens_verdicts
        if lv.get("overall_verdict") == "FAILED"
    ]


def apply_rule_5_no_evidence_handling(lens_verdicts: list[dict]) -> list[str]:
    """Rule 5 -- NO-EVIDENCE lenses also surface explicitly and block PASS.

    NO-EVIDENCE means the lens could not see diff content (almost always an
    inputs-gathering bug). Returns list of NO-EVIDENCE lens_ids.
    """
    return [
        lv["lens_id"]
        for lv in lens_verdicts
        if lv.get("overall_verdict") == "NO-EVIDENCE"
    ]


def apply_rule_6_persistent_disagreement(
    lens_verdicts: list[dict], prior_sidecar: dict | None
) -> list[dict]:
    """Rule 6 -- persistent disagreement escalates severity.

    When --prior-sidecar is supplied AND a current finding matches a prior
    finding's identity (file_line + anti_pattern + severity) that was demoted
    per rule 2, escalate the current finding's severity by one tier
    (FYI -> Nit, Nit -> Block) and prefix its rationale with
    "Persistent disagreement: ".

    When prior_sidecar is None, this rule is a no-op (first invocation).
    """
    if prior_sidecar is None:
        return lens_verdicts
    # Index prior findings by (file_line, anti_pattern) identity. We include
    # BOTH rule-2 demotions ("Demoted per rule 2:") AND prior persistent-
    # disagreement escalations ("Persistent disagreement:") so the chain
    # FYI -> Nit -> Block continues across runs (severity is excluded from
    # the identity key because it changes each round).
    prior_demoted: set[tuple[str, str | None]] = set()
    for lv in prior_sidecar.get("lens_verdicts", []):
        for f in lv.get("findings", []):
            rationale = f.get("rationale", "")
            if rationale.startswith("Demoted per rule 2:") or rationale.startswith(
                "Persistent disagreement:"
            ):
                prior_demoted.add(
                    (
                        f.get("file_line", ""),
                        f.get("anti_pattern"),
                    )
                )
    # Walk current findings; escalate matches by one tier from current severity.
    for lv in lens_verdicts:
        for f in lv.get("findings", []):
            key = (
                f.get("file_line", ""),
                f.get("anti_pattern"),
            )
            if key in prior_demoted:
                current_sev = f.get("severity", "FYI")
                if current_sev == "FYI":
                    f["severity"] = "Nit"
                elif current_sev == "Nit":
                    f["severity"] = "Block"
                rationale = f.get("rationale", "")
                if not rationale.startswith("Persistent disagreement:"):
                    f["rationale"] = f"Persistent disagreement: {rationale}"
    return lens_verdicts


_CONCRETE_FILE_LINE_RE = re.compile(r"^[\w./\\:-]+:\d+(?:-\d+)?$")

# Matches '<path>:<line>' or '<path>:<start>-<end>' (capturing path + start +
# optional end). The path group is non-greedy so it stops at the LAST ':' that
# precedes a digit run — preserves Windows drive letters like 'C:\foo\bar:42'.
_FILE_LINE_RE = re.compile(r"^(.+):(\d+)(?:-(\d+))?$")


def _normalize_path(path_str: str) -> str:
    """Normalize a file path component for cross-source equality.

    Lowercases on Windows (case-insensitive FS); converts backslashes to
    forward slashes; strips leading './' (possibly repeated) and surrounding
    whitespace. Preserves absolute paths and drive letters — we don't try to
    resolve relative-vs-absolute equivalence here; the goal is normalizing
    the cosmetic mismatches between lens output and lint output that share
    the same logical anchor.
    """
    p = path_str.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    if sys.platform == "win32":
        p = p.lower()
    return p


def _file_line_overlaps(lens_fl: str, lint_fl: str) -> bool:
    """True iff a lens file_line overlaps a lint file_line.

    Both sides are ``path:line`` or ``path:start-end``. After path
    normalization (forward slashes, leading './' stripped, lowercased on
    Windows), paths must match exactly; the line ranges overlap iff
    ``max(starts) <= min(ends)``. The lint side is always a single line per
    ``lint_prepass.sh``'s contract, but we accept ranges on either side
    defensively so a future lint integration that emits ranges still slots
    in cleanly.
    """
    m_lens = _FILE_LINE_RE.match(lens_fl or "")
    m_lint = _FILE_LINE_RE.match(lint_fl or "")
    if not (m_lens and m_lint):
        return False
    if _normalize_path(m_lens.group(1)) != _normalize_path(m_lint.group(1)):
        return False
    lens_start = int(m_lens.group(2))
    lens_end = int(m_lens.group(3) or m_lens.group(2))
    lint_start = int(m_lint.group(2))
    lint_end = int(m_lint.group(3) or m_lint.group(2))
    return max(lens_start, lint_start) <= min(lens_end, lint_end)


def _is_absence_finding(finding: dict) -> bool:
    """Heuristic for rule 7: 'absence-of-thing' findings have no concrete
    path:line anchor. A concrete file_line matches the regex; anything else
    (an "(absence -- ...)" placeholder, an empty string, a free-form
    description) is treated as absence."""
    file_line = finding.get("file_line", "")
    if not file_line:
        return True
    return _CONCRETE_FILE_LINE_RE.match(file_line) is None


def _summary_tokens(rationale: str) -> set[str]:
    """Fuzzy-match support: tokenize a rationale into a lowercase token set
    for set-overlap comparison."""
    return {w.lower() for w in re.findall(r"\w+", rationale) if len(w) > 3}


def apply_rule_7_absence_dedup(
    lens_verdicts: list[dict],
    lint_findings: list[dict] | None = None,
) -> list[dict]:
    """Rule 7 -- absence-of-thing dedup AND lint-finding dedup.

    Two independent dedup paths share this rule because both deflate
    cross-source double-counting at the same SKILL.md contract layer:

    1. **Absence path.** When multiple lenses surface findings about the same
       absence (no concrete file_line anchor in the diff), dedup by
       (anti_pattern, summary fuzzy-match) and demote duplicates to FYI.
       Primary lens is determined by catalog Lens-routing or first-emit-order
       in CODE_LENS_ORDER.
    2. **Lint path.** When ``lint_findings`` is supplied (the orchestrator
       loaded ``lint-findings.json`` written by ``scripts/lint_prepass.sh``),
       any lens finding sharing a concrete file_line with a lint finding is
       demoted to FYI with rationale prefixed
       ``Cited-by-linter: <tool> <rule>`` and annotated with
       ``also_flagged_by_linter: {tool, rule}``. The lint findings themselves
       are NOT added to lens_verdicts -- they're already in the linter's
       output and the aggregator does not republish them. ``scope-boundary-
       deferral`` findings are excluded from the lint path (they're an
       operator hand-off, not a defect signal).

    Both passes mutate findings in place. The lint path runs FIRST so an
    already-cited-by-linter lens finding is not also targeted by absence-path
    clustering (its concrete file_line keeps it out of the absence cluster
    anyway, but the order makes the contract auditable).

    Fires BEFORE rule 6 in the pipeline; persistent-disagreement escalation
    in rule 6 then applies only to the surviving primary.
    """
    # --- Lint path -------------------------------------------------------
    # Keep lint findings as a list and iterate per lens finding using the
    # path-normalized + range-aware ``_file_line_overlaps`` matcher. A plain
    # dict-by-file_line lookup misses ranges (``src/foo.py:42-45`` vs
    # ``src/foo.py:43``) and cosmetic mismatches (``./src/foo.py`` vs
    # ``src/foo.py``, ``src\foo.py`` vs ``src/foo.py``); both shapes are
    # known producers (lint_prepass.sh emits single-line; lens prompts may
    # emit ranges) so the iteration cost is paid intentionally.
    lint_candidates: list[dict] = []
    if lint_findings:
        for lf in lint_findings:
            fl = lf.get("file_line", "")
            if not fl:
                continue
            lint_candidates.append(lf)
    if lint_candidates:
        for lv in lens_verdicts:
            if lv.get("overall_verdict") == "SKIPPED":
                continue
            for f in lv.get("findings", []):
                if f.get("anti_pattern") == "scope-boundary-deferral":
                    continue
                lens_fl = f.get("file_line", "")
                if not lens_fl:
                    continue
                # Find the FIRST lint finding whose file_line overlaps; the
                # lint_prepass.sh output ordering is the deterministic
                # tie-breaker when multiple lint findings fall within a lens
                # range.
                hit = None
                for lf in lint_candidates:
                    if _file_line_overlaps(lens_fl, lf.get("file_line", "")):
                        hit = lf
                        break
                if hit is None:
                    continue
                # ``or`` short-circuits on falsy values (None, "") so an
                # explicit ``{"rule": null}`` in lint-findings.json still
                # falls through to the default rather than producing a
                # 'Cited-by-linter: ruff None' rationale.
                tool = hit.get("tool") or "linter"
                rule = hit.get("rule") or ""
                # Demote to FYI and annotate.
                if f.get("severity") != "FYI":
                    f["severity"] = "FYI"
                f["also_flagged_by_linter"] = {"tool": tool, "rule": rule}
                rationale = f.get("rationale", "")
                prefix = f"Cited-by-linter: {tool} {rule}".rstrip()
                if not rationale.startswith("Cited-by-linter:"):
                    f["rationale"] = f"{prefix}: {rationale}" if rationale else prefix

    # --- Absence path ----------------------------------------------------
    # Collect absence findings across lenses with (lens_id, finding) tuples.
    # scope-boundary-deferral is reserved wire-format (operator UAT hand-off,
    # NOT a defect) and is processed by extract_deferred_items; rule 7 must
    # skip it so it does not cluster with real absence findings and demote
    # unrelated ones alongside it.
    absences: list[tuple[str, dict]] = []
    for lv in lens_verdicts:
        if lv.get("overall_verdict") == "SKIPPED":
            continue
        for f in lv.get("findings", []):
            if f.get("anti_pattern") == "scope-boundary-deferral":
                continue
            if _is_absence_finding(f):
                absences.append((lv["lens_id"], f))

    # Group by (anti_pattern, fuzzy-match cluster).
    clusters: list[list[tuple[str, dict]]] = []
    for lens_id, f in absences:
        ap = f.get("anti_pattern")
        toks = _summary_tokens(f.get("rationale", ""))
        placed = False
        for cluster in clusters:
            c_ap = cluster[0][1].get("anti_pattern")
            c_toks = _summary_tokens(cluster[0][1].get("rationale", ""))
            # Same anti_pattern (or both None) AND >=50% token overlap.
            ap_match = ap == c_ap
            overlap = (
                len(toks & c_toks) / max(1, min(len(toks), len(c_toks)))
                if toks and c_toks
                else 0
            )
            if ap_match and overlap >= 0.5:
                cluster.append((lens_id, f))
                placed = True
                break
        if not placed:
            clusters.append([(lens_id, f)])

    # For each cluster of size >= 2, pick primary and demote others.
    for cluster in clusters:
        if len(cluster) < 2:
            continue
        ap = cluster[0][1].get("anti_pattern")
        primary_idx = None
        if ap and ap in ANTI_PATTERN_PRIMARY:
            target = ANTI_PATTERN_PRIMARY[ap]
            for i, (lens_id, _f) in enumerate(cluster):
                if lens_id == target:
                    primary_idx = i
                    break
        if primary_idx is None:
            # First-emit-order by CODE_LENS_ORDER.
            primary_idx = min(
                range(len(cluster)),
                key=lambda i: (
                    CODE_LENS_ORDER.index(cluster[i][0])
                    if cluster[i][0] in CODE_LENS_ORDER
                    else 999
                ),
            )
        # Annotate primary; demote others.
        primary_lens, primary_f = cluster[primary_idx]
        also_flagged_by = [lens_id for lens_id, _ in cluster if lens_id != primary_lens]
        if also_flagged_by:
            primary_f["also_flagged_by"] = also_flagged_by
        for i, (_lens_id, f) in enumerate(cluster):
            if i == primary_idx:
                continue
            if f.get("severity") != "FYI":
                f["severity"] = "FYI"
                rationale = f.get("rationale", "")
                if not rationale.startswith("Demoted per rule 7:"):
                    f["rationale"] = f"Demoted per rule 7: {rationale}"
    return lens_verdicts


def load_lint_findings(lint_findings_path: Path | None) -> list[dict]:
    """Load lint findings from a lint-findings.json sidecar.

    The schema matches scripts/lint_prepass.sh output:
    ``{timestamp, tools_run[], tools_skipped[], findings[{tool, rule, file_line, message}]}``.
    Returns the ``findings`` array (empty list when the path is None or the
    file does not exist). A non-readable / non-JSON file at the given path
    raises -- that's an orchestrator configuration error worth surfacing.
    """
    if lint_findings_path is None:
        return []
    if not lint_findings_path.exists():
        return []
    with lint_findings_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    findings = data.get("findings") or []
    if not isinstance(findings, list):
        return []
    return findings


# ---------------------------------------------------------------------------
# Default-deny input contract: lens records, lens-set completeness, mechanical
# results
# ---------------------------------------------------------------------------


def validate_lens_records(lens_verdicts: list[dict]) -> None:
    """Reject lens records the rules cannot reduce safely.

    Raises ValueError when a record is not an object, has no non-empty string
    ``lens_id``, has no ``findings`` list, or holds a finding that is not an
    object or whose ``severity`` / ``file_line`` / ``excerpt`` / ``rationale``
    / ``anti_pattern`` has a non-string value. No verdict is produced for such
    input (fail-closed: the caller reports the error, never a PASS).
    """
    for i, lv in enumerate(lens_verdicts, start=1):
        if not isinstance(lv, dict):
            raise ValueError(f"lens record #{i}: not a JSON object")
        lens_id = lv.get("lens_id")
        if not isinstance(lens_id, str) or not lens_id.strip():
            raise ValueError(f"lens record #{i}: lens_id must be a non-empty string")
        findings = lv.get("findings")
        if not isinstance(findings, list):
            raise ValueError(
                f"lens {lens_id!r}: findings must be a list (empty when none)"
            )
        for j, f in enumerate(findings, start=1):
            if not isinstance(f, dict):
                raise ValueError(f"lens {lens_id!r} finding #{j}: not a JSON object")
            for key in ("severity", "file_line", "excerpt", "rationale"):
                if key in f and not isinstance(f[key], str):
                    raise ValueError(
                        f"lens {lens_id!r} finding #{j}: {key} must be a string"
                    )
            if f.get("anti_pattern") is not None and not isinstance(f["anti_pattern"], str):
                raise ValueError(
                    f"lens {lens_id!r} finding #{j}: anti_pattern must be a string or null"
                )


def check_lens_set(
    lens_verdicts: list[dict],
    *,
    plan_step: str | None = None,
    invocation: dict | None = None,
) -> list[str]:
    """Lens-set contract problems; any problem makes the result NEEDS-WORK.

    Runs on the RAW lens records, before rules 7/2/6 mutate severities, so a
    stale lint file or a dedup demotion cannot launder a self-contradictory
    record. "Required" follows ``invocation.reviewers_flag``:

    - every code lens in CODE_LENS_ORDER appears exactly once (the stable
      six-element prefix), on every lane;
    - ``code``: no other lens id; ``runtime`` / ``full``: other ids must be
      RUNTIME_LENS_IDS;
    - SKIPPED is allowed only for plan-conformance when ``plan_step`` is None,
      or for any code lens under ``runtime``; a SKIPPED lens carries no
      findings;
    - ``runtime`` needs at least one runtime lens that ran, and a recorded
      runtime downgrade under ``runtime`` is NEEDS-WORK unconditionally (the
      runtime lenses were dropped and the code lenses were not selected);
      ``full`` needs one unless ``invocation.runtime_downgraded`` records the
      downgrade;
    - under a recorded downgrade (``invocation.runtime_downgraded is True``)
      runtime lenses are never spawned, so ANY runtime lens record is stale or
      fabricated and is a problem;
    - a PASS lens carries no Block/Nit finding, and every finding severity is
      Block, Nit or FYI.

    Unknown or missing overall_verdict values are handled by
    build_aggregated_verdict (default-deny), not here.
    """
    problems: list[str] = []
    inv = default_invocation() if invocation is None else invocation
    reviewers = inv.get("reviewers_flag") if isinstance(inv, dict) else None
    if reviewers not in REVIEWERS_FLAGS:
        problems.append(
            f"invalid invocation.reviewers_flag {reviewers!r} "
            f"(expected one of {', '.join(REVIEWERS_FLAGS)})"
        )
    downgraded = isinstance(inv, dict) and inv.get("runtime_downgraded") is True

    ids = [lv["lens_id"] for lv in lens_verdicts]
    duplicates = [x for x in dict.fromkeys(ids) if ids.count(x) > 1]
    if duplicates:
        problems.append("duplicate lens_id: " + ", ".join(duplicates))
    missing = [x for x in CODE_LENS_ORDER if x not in ids]
    if missing:
        problems.append("missing required lens: " + ", ".join(missing))
    allowed_extra = RUNTIME_LENS_IDS if reviewers in ("runtime", "full") else ()
    unexpected = [
        x for x in dict.fromkeys(ids)
        if x not in CODE_LENS_ORDER and x not in allowed_extra
    ]
    if unexpected:
        problems.append(
            f"unexpected lens for --reviewers {reviewers}: " + ", ".join(unexpected)
        )

    for lv in lens_verdicts:
        lens_id = lv["lens_id"]
        verdict = lv.get("overall_verdict")
        findings = lv["findings"]
        if verdict == "SKIPPED":
            allowed = (lens_id in CODE_LENS_ORDER and reviewers == "runtime") or (
                lens_id == "plan-conformance" and plan_step is None
            )
            if not allowed:
                problems.append(f"required lens SKIPPED: {lens_id}")
            if findings:
                problems.append(f"SKIPPED lens carries findings: {lens_id}")
        bad = [f.get("severity") for f in findings if f.get("severity") not in SEVERITY_ORDER]
        if bad:
            problems.append(
                f"invalid finding severity in {lens_id}: "
                + ", ".join(repr(s) for s in bad)
            )
        if verdict == "PASS" and any(
            f.get("severity") in ("Block", "Nit") for f in findings
        ):
            problems.append(f"PASS lens carries Block/Nit findings: {lens_id}")

    reason = (inv.get("runtime_downgrade_reason") or "reason not recorded") if downgraded else None
    if downgraded:
        present = [x for x in dict.fromkeys(ids) if x in RUNTIME_LENS_IDS]
        if present:
            problems.append(
                "runtime lens record present under a recorded runtime downgrade: "
                + ", ".join(present)
                + f" (runtime downgrade: {reason}; runtime lenses were not "
                "spawned, so the record is stale or fabricated)"
            )
    if reviewers in ("runtime", "full"):
        ran = [
            lv["lens_id"] for lv in lens_verdicts
            if lv["lens_id"] in RUNTIME_LENS_IDS and lv.get("overall_verdict") != "SKIPPED"
        ]
        if reviewers == "runtime" and (downgraded or not ran):
            problems.append(
                "no runtime lens ran under --reviewers runtime"
                + (f" (runtime downgrade: {reason})" if downgraded else "")
            )
        elif reviewers == "full" and not ran and not downgraded:
            problems.append(
                "no runtime lens ran under --reviewers full and no runtime "
                "downgrade was recorded"
            )
    return problems


def _json_type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def evaluate_mechanical_results(
    mechanical_results: object,
    *,
    supplied: bool = False,
) -> dict | None:
    """Summarize the mechanical-check phase for the verdict.

    Input shape (SKILL.md Tools; the parent writes it after the mechanical
    phase): ``{"checks": [{"check", "status", "command", "evidence"}]}`` with
    ``status`` one of MECHANICAL_STATUSES. Returns None only when no results
    were supplied (legacy callers: ``mechanical_results`` is None and
    ``supplied`` is False), else ``{passed, failed, missing_tool, invalid}``
    lists. A SUPPLIED value that is not an object -- including JSON ``null``
    read from a ``--mechanical-results`` file (``supplied=True``) -- is
    malformed, never the legacy path. A ``fail`` status or any malformed
    entry makes the aggregated result NEEDS-WORK; ``missing-tool`` is listed
    and never blocks.
    """
    if mechanical_results is None and not supplied:
        return None
    summary: dict[str, list[str]] = {
        "passed": [], "failed": [], "missing_tool": [], "invalid": [],
    }
    if not isinstance(mechanical_results, dict):
        summary["invalid"].append(
            "expected an object with a 'checks' list, got JSON "
            + _json_type_name(mechanical_results)
        )
        return summary
    checks = mechanical_results.get("checks")
    if not isinstance(checks, list):
        summary["invalid"].append("expected an object with a 'checks' list")
        return summary
    if not checks:
        # The mechanical-check phase is mandatory (the lint pre-pass always
        # runs), so a supplied record with zero checks means it was skipped.
        summary["invalid"].append("no mechanical check recorded")
        return summary
    for i, entry in enumerate(checks, start=1):
        if not isinstance(entry, dict):
            summary["invalid"].append(f"check #{i} is not an object")
            continue
        name = entry.get("check")
        status = entry.get("status")
        if not isinstance(name, str) or not name.strip():
            summary["invalid"].append(f"check #{i} has no 'check' name")
            continue
        if any(k in entry and not isinstance(entry[k], str) for k in ("command", "evidence")):
            summary["invalid"].append(f"{name}: command/evidence must be strings")
            continue
        if status == "pass":
            summary["passed"].append(name)
        elif status == "fail":
            summary["failed"].append(name)
        elif status == "missing-tool":
            summary["missing_tool"].append(name)
        else:
            summary["invalid"].append(f"{name}: status {status!r}")
    return summary


# ---------------------------------------------------------------------------
# Aggregated verdict assembly + sidecar
# ---------------------------------------------------------------------------


def build_aggregated_verdict(
    lens_verdicts: list[dict],
    severity_counts: dict,
    skipped: list[str],
    failed: list[dict],
    no_evidence: list[str],
    deferred_items: list[dict],
    *,
    lens_set_problems: list[str] | None = None,
    mechanical: dict | None = None,
) -> dict:
    """Compute aggregated_verdict.result and rationale from the rule outputs.

    Default-deny rules from SKILL.md "Aggregated-verdict output ladder" (the
    result enum stays PASS | NEEDS-WORK | DEFERRED-TO-UAT):
      PASS              -- every lens verdict is PASS or an allowed SKIPPED;
                           zero Block; Nit < 3; no lens-set problem
                           (check_lens_set); no failed or invalid mechanical
                           result; no deferral
      NEEDS-WORK        -- any Block; OR any lens verdict other than PASS /
                           SKIPPED (NEEDS-WORK, FAILED, NO-EVIDENCE, UNCERTAIN,
                           NEEDS-CLARIFICATION, or an unknown/missing value);
                           OR any lens-set problem; OR a mechanical check with
                           status "fail" or a malformed mechanical result;
                           OR aggregated Nit count >= 3
      DEFERRED-TO-UAT   -- structurally un-evaluable parts (Step 7 trigger);
                           deferral over PASS but NOT over NEEDS-WORK
    UNCERTAIN and NEEDS-CLARIFICATION are abstentions: the rationale names the
    lens so the operator escalates; they never become PASS.
    """
    lens_set_problems = list(lens_set_problems or [])
    needs_work_lenses = [
        lv["lens_id"]
        for lv in lens_verdicts
        if lv.get("overall_verdict") == "NEEDS-WORK"
    ]
    uncertain = [
        lv["lens_id"] for lv in lens_verdicts if lv.get("overall_verdict") == "UNCERTAIN"
    ]
    clarification = [
        lv["lens_id"]
        for lv in lens_verdicts
        if lv.get("overall_verdict") == "NEEDS-CLARIFICATION"
    ]
    invalid_verdicts = [
        f"{lv['lens_id']}="
        + (repr(lv["overall_verdict"]) if "overall_verdict" in lv else "missing")
        for lv in lens_verdicts
        if lv.get("overall_verdict") not in LENS_VERDICTS
    ]
    # Default-deny catch-all: anything but PASS / SKIPPED is non-passing.
    non_passing = [
        lv["lens_id"]
        for lv in lens_verdicts
        if lv.get("overall_verdict") not in PASSING_LENS_VERDICTS
    ]
    mech_failed = list((mechanical or {}).get("failed", []))
    mech_invalid = list((mechanical or {}).get("invalid", []))
    mech_missing = list((mechanical or {}).get("missing_tool", []))
    mech_passed = list((mechanical or {}).get("passed", []))
    block_count = severity_counts["block_count"]
    nit_count = severity_counts["nit_count"]

    # Hardest verdict wins for gating: NEEDS-WORK > DEFERRED > PASS.
    hard_needs_work = (
        block_count > 0
        or nit_count >= 3
        or bool(needs_work_lenses)
        or bool(failed)
        or bool(no_evidence)
        or bool(non_passing)
        or bool(lens_set_problems)
        or bool(mech_failed)
        or bool(mech_invalid)
    )
    has_deferral = bool(deferred_items)

    if hard_needs_work:
        result = "NEEDS-WORK"
    elif has_deferral:
        result = "DEFERRED-TO-UAT"
    else:
        result = "PASS"

    # Compose a human-readable one-line rationale.
    parts = []
    if block_count:
        parts.append(f"{block_count} Block finding{'s' if block_count != 1 else ''}")
    if nit_count:
        parts.append(f"{nit_count} Nit finding{'s' if nit_count != 1 else ''}")
    if needs_work_lenses:
        parts.append(f"lenses NEEDS-WORK: {', '.join(needs_work_lenses)}")
    if failed:
        parts.append(
            "FAILED: "
            + ", ".join(
                f"{e['lens_id']} ({e.get('failure_reason') or 'unknown'})"
                for e in failed
            )
        )
    if no_evidence:
        parts.append(f"NO-EVIDENCE: {', '.join(no_evidence)}")
    if uncertain:
        parts.append(
            "UNCERTAIN (lens abstained; escalate to the operator, never PASS): "
            + ", ".join(uncertain)
        )
    if clarification:
        parts.append(
            "NEEDS-CLARIFICATION (inputs could not be resolved): "
            + ", ".join(clarification)
        )
    if invalid_verdicts:
        parts.append("invalid overall_verdict: " + ", ".join(invalid_verdicts))
    parts.extend(f"lens set: {p}" for p in lens_set_problems)
    if mech_failed:
        parts.append("mechanical check failed: " + ", ".join(mech_failed))
    if mech_invalid:
        parts.append("invalid mechanical result: " + "; ".join(mech_invalid))
    if mech_missing:
        parts.append(
            "MISSING-TOOL (warning; that check did not run): " + ", ".join(mech_missing)
        )
    if mech_passed:
        parts.append("mechanical checks passed: " + ", ".join(mech_passed))
    if skipped:
        parts.append(f"SKIPPED: {', '.join(skipped)}")
    if has_deferral:
        parts.append(
            f"{len(deferred_items)} deferred UAT item"
            f"{'s' if len(deferred_items) != 1 else ''}"
        )
    rationale = ("; ".join(parts) if parts else "Zero findings; all lenses PASS") + "."

    return {"result": result, "rationale": rationale}


def extract_deferred_items(lens_verdicts: list[dict]) -> list[dict]:
    """Extract scope-boundary deferrals from lens findings.

    Lenses signal a deferral via a Block-severity finding with
    anti_pattern == 'scope-boundary-deferral'. Each matching finding becomes
    a deferred_uat_items[] entry and the original is demoted to FYI.

    The Step 6 auth-gate downgrade path also produces deferred items, but
    that's an orchestrator-level concern handled outside this aggregator.
    """
    deferred: list[dict] = []
    counter = 1
    for lv in lens_verdicts:
        for f in lv.get("findings", []):
            if f.get("anti_pattern") == "scope-boundary-deferral":
                deferred.append(
                    {
                        "reason": f.get("rationale", ""),
                        "covered_lenses": [
                            other["lens_id"]
                            for other in lens_verdicts
                            if other["lens_id"] != lv["lens_id"]
                            and other.get("overall_verdict")
                            not in ("SKIPPED", "FAILED", "NO-EVIDENCE")
                        ],
                        "needs_verification": f.get("excerpt", ""),
                        "recommended_commands": [],
                        "uat_id": f"M{counter}",
                    }
                )
                counter += 1
                # Demote the original finding to FYI.
                if f.get("severity") != "FYI":
                    f["severity"] = "FYI"
    return deferred


def assign_m_numbers(deferred_items: list[dict]) -> list[dict]:
    """Assign M1, M2, ... uat_id values to deferred items in emission order.

    M-numbering convention (SKILL.md "M<N> numbering convention"):

    - Within a single review-deep invocation: items are numbered starting at
      M1 in the order the aggregator emits them. Emission order is
      (a) the order each lens reported them in its findings, then (b) the
      lens-spawn order CODE_LENS_ORDER (correctness, bugs, security,
      test-quality, style, plan-conformance) followed by any runtime lenses.
    - Across invocations: review-deep does NOT track prior invocations'
      M-numbers. Each invocation restarts at M1. Persistence is the plan.md's
      job per /build-phase's "Deferred-UAT bundling" rules; operators who
      want review-deep's deferrals merged into the plan-level M-series copy
      them by hand into the plan's Manual section, re-numbering at the open
      slot.
    - Operator-facing cue: the markdown summary's final pre-sidecar line
      reads "Please run <lowest M-number> next." -- an explicit ask, not
      buried prose.

    Edge cases:
      - empty list -> returns []
      - same source step contributing 2 items -> two consecutive M-numbers
      - existing uat_id values on input -> overwritten (this function is
        canonical)
    """
    out: list[dict] = []
    for i, item in enumerate(deferred_items, start=1):
        new_item = dict(item)
        new_item["uat_id"] = f"M{i}"
        out.append(new_item)
    return out


def build_sidecar(
    lens_verdicts: list[dict],
    aggregated_verdict: dict,
    deferred_items: list[dict],
    timestamp: str,
    skill_version: str,
    plan_step: str | None,
    invocation: dict,
    mechanical_results: dict | None = None,
) -> dict:
    """Assemble the JSON sidecar in the canonical key order.

    Schema declared in SKILL.md "Audit-trail JSON sidecar schema". The key
    order here matches the schema example block (timestamp, plan_step,
    skill_version, invocation, lens_verdicts, aggregated_verdict,
    model_tiers_used, deferred_uat_items, mechanical_results) so a sidecar
    diff against the schema is alignable. ``mechanical_results`` echoes the
    supplied --mechanical-results object verbatim, or null when none was
    supplied.
    """
    model_tiers_used = {lv["lens_id"]: lv.get("model_tier") for lv in lens_verdicts}
    return {
        "timestamp": timestamp,
        "plan_step": plan_step,
        "skill_version": skill_version,
        "invocation": invocation,
        "lens_verdicts": lens_verdicts,
        "aggregated_verdict": aggregated_verdict,
        "model_tiers_used": model_tiers_used,
        "deferred_uat_items": deferred_items,
        "mechanical_results": mechanical_results,
    }


def write_sidecar(sidecar: dict, output_dir: Path) -> Path:
    """Write the audit-trail JSON sidecar.

    Filename: <timestamp>.json (ISO-8601 with filesystem-safe characters,
    e.g. '2026-05-24T08-15-30.json'). Schema: matches SKILL.md
    Audit-trail JSON sidecar schema. Returns the path to the written file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = output_dir / f"{sidecar['timestamp']}.json"
    with sidecar_path.open("w", encoding="utf-8") as f:
        json.dump(sidecar, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return sidecar_path


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


# Escape markdown metacharacters in inline (non-fenced) text. Findings'
# rationales and excerpts may contain `|`, `*`, `_`, backtick, `<`, etc. that
# corrupt the rendered markdown when surfaced into a GitHub PR comment or any
# markdown consumer. Do NOT apply inside triple-backtick code-fence blocks --
# those are verbatim by markdown rules.
_MD_ESCAPE_RE = re.compile(r"([\\`*_{}\[\]()#+\-.!|])")


def _escape_md(s: str) -> str:
    return _MD_ESCAPE_RE.sub(r"\\\1", s)


def _safe_fence_length(text: str) -> int:
    """Compute a code-fence backtick run that is strictly longer than any
    backtick run inside *text*, with a floor of 3. Prevents premature fence
    closure when the excerpt itself contains triple-backtick sequences."""
    longest = 0
    cur = 0
    for c in text:
        if c == "`":
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    return max(3, longest + 1)


def render_markdown(sidecar: dict) -> str:
    """Render the human-readable markdown summary.

    Shape: matches SKILL.md "Markdown output shape" section. Sections in
    order: header line, a "Rationale: <aggregated rationale>" line,
    ## Lens verdicts, ## Findings (by severity), and
    ## Deferred to operator UAT (when applicable). Final line is the
    "Please run M<N> next." cue when deferrals exist, followed by
    "Audit-trail JSON: <path>".
    """
    out: list[str] = []
    agg = sidecar["aggregated_verdict"]
    deferred = sidecar.get("deferred_uat_items", [])

    # Header line.
    if agg["result"] == "NEEDS-WORK" and deferred:
        out.append("# review-deep: NEEDS-WORK + DEFERRED-TO-UAT")
    else:
        out.append(f"# review-deep: {agg['result']}")
    out.append("")
    # The rationale names every default-deny reason (abstaining lens, lens-set
    # problem, failed mechanical check) the per-lens lines cannot show.
    out.append(f"Rationale: {_escape_md(str(agg.get('rationale', '')))}")
    out.append("")

    # Lens verdicts.
    out.append("## Lens verdicts")
    out.append("")
    for lv in sidecar["lens_verdicts"]:
        finding_count = len(lv.get("findings", []))
        verdict = lv.get("overall_verdict", "<missing>")
        tier = lv.get("model_tier", "?")
        if verdict == "SKIPPED" and lv["lens_id"] == "plan-conformance":
            out.append(
                f"- {lv['lens_id']}: SKIPPED (no --plan-step argument, model: {tier})"
            )
        else:
            out.append(
                f"- {lv['lens_id']}: {verdict} ({finding_count} findings, model: {tier})"
            )
    if sidecar["invocation"].get("runtime_downgraded"):
        out.append(
            f"- Runtime downgrade: {sidecar['invocation'].get('runtime_downgrade_reason')}"
        )
    out.append("")

    # Findings grouped by severity.
    by_sev: dict[str, list[tuple[str, dict]]] = {"Block": [], "Nit": [], "FYI": []}
    for lv in sidecar["lens_verdicts"]:
        for f in lv.get("findings", []):
            sev = f.get("severity", "FYI")
            by_sev.setdefault(sev, []).append((lv["lens_id"], f))
    if any(by_sev[s] for s in ("Block", "Nit", "FYI")):
        out.append("## Findings")
        out.append("")
        for sev in ("Block", "Nit", "FYI"):
            entries = by_sev.get(sev, [])
            if not entries:
                continue
            out.append(f"### {sev}")
            out.append("")
            for lens_id, f in entries:
                ap = f.get("anti_pattern")
                tag = f", anti-pattern: {ap}" if ap else ""
                file_line = _escape_md(str(f.get("file_line", "?")))
                rationale = _escape_md(str(f.get("rationale", "")))
                out.append(
                    f"- **{file_line}** ({lens_id}{tag}): "
                    f"{rationale}"
                )
                excerpt = f.get("excerpt", "")
                if excerpt:
                    excerpt_str = str(excerpt)
                    fence = "`" * _safe_fence_length(excerpt_str)
                    out.append("")
                    out.append(f"  {fence}")
                    for line in excerpt_str.splitlines() or [excerpt_str]:
                        out.append(f"  {line}")
                    out.append(f"  {fence}")
            out.append("")

    # Deferred to operator UAT (only when present).
    if deferred:
        out.append("## Deferred to operator UAT")
        out.append("")
        for item in deferred:
            reason = _escape_md(str(item.get("reason", "")))
            needs_verification = _escape_md(str(item.get("needs_verification", "")))
            out.append(f"### {item['uat_id']}: {reason}")
            out.append("")
            covered = item.get("covered_lenses") or []
            out.append(
                f"- **Covered lenses:** {', '.join(covered) if covered else 'none'}"
            )
            out.append(
                f"- **Needs verification:** {needs_verification}"
            )
            out.append("- **Commands to run:**")
            out.append("")
            cmds = item.get("recommended_commands", [])
            cmds_joined = "\n".join(str(c) for c in cmds)
            fence = "`" * _safe_fence_length(cmds_joined)
            out.append(f"  {fence}powershell")
            for cmd in cmds:
                out.append(f"  {cmd}")
            out.append(f"  {fence}")
            out.append("")
        # Explicit run-next ask line.
        lowest = min(
            (item["uat_id"] for item in deferred),
            key=lambda x: int(re.sub(r"\D", "", x) or "0"),
        )
        out.append(f"Please run {lowest} next.")
        out.append("")

    # Audit-trail pointer (final line).
    out.append(f"Audit-trail JSON: .review-deep/{sidecar['timestamp']}.json")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def aggregate(
    lens_verdicts: list[dict],
    *,
    prior_sidecar: dict | None = None,
    timestamp: str,
    skill_version: str,
    plan_step: str | None = None,
    invocation: dict | None = None,
    lint_findings: list[dict] | None = None,
    mechanical_results: dict | None = None,
    mechanical_results_supplied: bool = False,
    lens_file_problems: list[str] | None = None,
) -> dict:
    """Run all seven aggregator rules and assemble the sidecar dict.

    Rule order: 7 (absence-dedup + lint-dedup) runs first, then 2 (cross-lens
    demotion), then 6 (persistent disagreement re-escalation), then 1/3/4/5
    are counting passes used to compose the aggregated verdict.

    ``lint_findings`` is the parsed ``findings`` array from
    ``lint-findings.json`` (see ``load_lint_findings``). When supplied, rule 7's
    lint path demotes lens findings that share a file_line with a linter
    finding to FYI with rationale prefixed ``Cited-by-linter: <tool> <rule>``.

    Default-deny: validate_lens_records raises ValueError for records the
    rules cannot reduce; check_lens_set (on the raw records, before any rule
    mutates them) and evaluate_mechanical_results feed build_aggregated_verdict,
    which returns PASS only when nothing is missing, duplicated, abstaining,
    unknown, skipped-while-required or mechanically failed.
    ``mechanical_results`` (``{"checks": [...]}``) is optional for legacy
    callers; when supplied it is echoed into the sidecar. A caller that read
    it from a file passes ``mechanical_results_supplied=True`` so a JSON
    ``null`` (or any non-object) is reduced as a malformed record and echoed
    as ``{"malformed_input": <value>}``, never as the flag-absent ``null``.
    ``lens_file_problems`` carries load_lens_verdicts' file-binding problems
    (LensSetError.problems); each is a lens-set problem (NEEDS-WORK).
    """
    if invocation is None:
        invocation = default_invocation()
    supplied = mechanical_results_supplied or mechanical_results is not None
    mechanical = evaluate_mechanical_results(mechanical_results, supplied=supplied)
    if not supplied:
        mechanical_echo = None
    elif isinstance(mechanical_results, dict):
        mechanical_echo = json.loads(json.dumps(mechanical_results))
    else:
        mechanical_echo = {"malformed_input": json.loads(json.dumps(mechanical_results))}
    # Guardrail: empty lens-verdict input is virtually always an orchestrator
    # failure (load_lens_verdicts returned [] because the dir was empty or
    # contained no .json files). Surface as NEEDS-WORK rather than a vacuous
    # PASS so the operator notices.
    if len(lens_verdicts) == 0:
        return build_sidecar(
            lens_verdicts=[],
            aggregated_verdict={
                "result": "NEEDS-WORK",
                "rationale": (
                    "no lens verdicts found in --lens-dir "
                    "(orchestrator failure or empty input)."
                ),
            },
            deferred_items=[],
            timestamp=timestamp,
            skill_version=skill_version,
            plan_step=plan_step,
            invocation=invocation,
            mechanical_results=mechanical_echo,
        )
    # Default-deny input contract, on the RAW records (before rules mutate).
    validate_lens_records(lens_verdicts)
    lens_set_problems = check_lens_set(
        lens_verdicts, plan_step=plan_step, invocation=invocation
    ) + list(lens_file_problems or [])
    # Rule 7 first: dedup absences across lenses + lint-finding dedup.
    lens_verdicts = apply_rule_7_absence_dedup(lens_verdicts, lint_findings)
    # Rule 2: cross-lens dimension demotion at the same file_line.
    lens_verdicts = apply_rule_2_lens_owns_dimension(lens_verdicts)
    # Rule 6: persistent-disagreement re-escalation (only when prior given).
    lens_verdicts = apply_rule_6_persistent_disagreement(lens_verdicts, prior_sidecar)
    # Rules 3/4/5: surface skipped, failed, no-evidence lenses.
    skipped = apply_rule_3_skipped_handling(lens_verdicts)
    failed = apply_rule_4_failed_handling(lens_verdicts)
    no_evidence = apply_rule_5_no_evidence_handling(lens_verdicts)
    # Rule 1 last: severity-count pass for the aggregated verdict ladder.
    severity_counts = apply_rule_1_severity_dominance(lens_verdicts)
    # Deferred items extracted from scope-boundary-deferral markers, then
    # M-numbered.
    raw_deferred = extract_deferred_items(lens_verdicts)
    deferred = assign_m_numbers(raw_deferred)
    aggregated_verdict = build_aggregated_verdict(
        lens_verdicts,
        severity_counts,
        skipped,
        failed,
        no_evidence,
        deferred,
        lens_set_problems=lens_set_problems,
        mechanical=mechanical,
    )
    return build_sidecar(
        lens_verdicts,
        aggregated_verdict,
        deferred,
        timestamp=timestamp,
        skill_version=skill_version,
        plan_step=plan_step,
        invocation=invocation,
        mechanical_results=mechanical_echo,
    )


# ---------------------------------------------------------------------------
# Self-test: round-trip a v2 M1 sidecar through the aggregator
# ---------------------------------------------------------------------------


def run_self_test(m1_sidecar_path: Path) -> int:
    """Round-trip an M1 baseline sidecar through the aggregator.

    Reads the M1 sidecar, feeds its lens_verdicts[] into aggregate(), and
    compares the resulting sidecar against the original. Returns 0 on
    byte-identity (modulo timestamp + skill_version) and prints
    "SELF-TEST PASSED"; returns 1 on diff and prints the differing fields.
    """
    with m1_sidecar_path.open("r", encoding="utf-8") as f:
        baseline = json.load(f)
    # Strip prior-rule-2 annotations so we don't accidentally re-apply them.
    lens_verdicts_in = json.loads(json.dumps(baseline["lens_verdicts"]))
    regenerated = aggregate(
        lens_verdicts_in,
        prior_sidecar=None,
        timestamp=baseline["timestamp"],
        skill_version=baseline["skill_version"],
        plan_step=baseline.get("plan_step"),
        invocation=baseline.get("invocation"),
    )
    # Compare structural keys. We tolerate aggregated_verdict.rationale prose
    # drift (the v2 prose is hand-crafted; ours is mechanical) and any extra
    # fields the baseline had that v3 doesn't emit (e.g. approximate_token_count).
    diffs: list[str] = []
    legitimate_diffs: list[str] = []
    for k in (
        "timestamp",
        "plan_step",
        "model_tiers_used",
        "deferred_uat_items",
    ):
        if baseline.get(k) != regenerated.get(k):
            diffs.append(f"  - field {k!r} differs")
    # skill_version is a legitimate v1->v3 drift; do NOT flag.
    if baseline.get("skill_version") != regenerated.get("skill_version"):
        legitimate_diffs.append(
            f"  - skill_version: v1->v3 (expected; --skill-version override "
            f"would force-match)"
        )
    # invocation may legitimately drift if v3 adds new fields; compare keys
    # present in BOTH dicts.
    bi = baseline.get("invocation", {})
    ri = regenerated.get("invocation", {})
    shared = set(bi) & set(ri)
    for key in shared:
        if bi[key] != ri[key]:
            diffs.append(f"  - invocation[{key!r}] differs")
    # lens_verdicts: rule 2 demotes some Nit findings to FYI when multiple
    # lenses share a file_line. The v1 M1 baseline did NOT enforce rule 2, so
    # demotions are legitimate v1->v3 drift -- detect and surface separately.
    bl = baseline.get("lens_verdicts", [])
    rl = regenerated.get("lens_verdicts", [])
    if len(bl) != len(rl):
        diffs.append(
            f"  - lens_verdicts length: baseline={len(bl)}, regenerated={len(rl)}"
        )
    else:
        for bv, rv in zip(bl, rl):
            if bv.get("lens_id") != rv.get("lens_id"):
                diffs.append(f"  - lens_id order differs at one entry")
                continue
            if bv.get("overall_verdict") != rv.get("overall_verdict"):
                diffs.append(
                    f"  - {bv['lens_id']}.overall_verdict: "
                    f"{bv.get('overall_verdict')!r} -> {rv.get('overall_verdict')!r}"
                )
            bf = bv.get("findings", [])
            rf = rv.get("findings", [])
            if len(bf) != len(rf):
                diffs.append(
                    f"  - {bv['lens_id']}.findings length: "
                    f"baseline={len(bf)}, regenerated={len(rf)}"
                )
                continue
            for i, (bb, rr) in enumerate(zip(bf, rf)):
                if bb.get("severity") != rr.get("severity"):
                    rationale_demoted = rr.get("rationale", "").startswith(
                        ("Demoted per rule 2:", "Demoted per rule 7:")
                    )
                    if rationale_demoted:
                        legitimate_diffs.append(
                            f"  - {bv['lens_id']}.findings[{i}].severity: "
                            f"{bb.get('severity')!r} -> {rr.get('severity')!r} "
                            f"(rule 2/7 demotion, expected for v1->v3)"
                        )
                    else:
                        diffs.append(
                            f"  - {bv['lens_id']}.findings[{i}].severity: "
                            f"{bb.get('severity')!r} -> {rr.get('severity')!r}"
                        )
    # aggregated_verdict.result must match; rationale prose is allowed to drift.
    if baseline["aggregated_verdict"]["result"] != regenerated["aggregated_verdict"]["result"]:
        diffs.append(
            f"  - aggregated_verdict.result: baseline="
            f"{baseline['aggregated_verdict']['result']!r}, "
            f"regenerated={regenerated['aggregated_verdict']['result']!r}"
        )
    if diffs:
        sys.stdout.write("SELF-TEST FAILED:\n")
        for d in diffs:
            sys.stdout.write(d + "\n")
        if legitimate_diffs:
            sys.stdout.write("Legitimate v1->v3 drift (not failures):\n")
            for d in legitimate_diffs:
                sys.stdout.write(d + "\n")
        return 1
    sys.stdout.write("SELF-TEST PASSED\n")
    if legitimate_diffs:
        sys.stdout.write("Legitimate v1->v3 drift (not failures):\n")
        for d in legitimate_diffs:
            sys.stdout.write(d + "\n")
    return 0


# ---------------------------------------------------------------------------
# Unit tests (invoked via --unit-test)
# ---------------------------------------------------------------------------


def run_unit_tests() -> int:
    """In-process unit tests for the rules Step 4 builds on.

    Mandatory coverage per plan: rule 6 escalation chain (Test 1), rule 7
    absence dedup-demote (Test 2), rule 7 scope-boundary-deferral exclusion
    in absence path (Test 3), empty lens dir -> NEEDS-WORK (Test 4),
    render_markdown Unicode smoke (Test 5), rule 7 lint-finding dedup
    (Test 6) with normalization + range sub-case (Test 6b),
    load_lint_findings I/O round-trip (Test 7), rule 7
    scope-boundary-deferral exclusion in the lint path (Test 8), rule 2
    Security-as-primary-owner for a Bugs+Security secret-dump co-flag (Test 9),
    and the default-deny PASS cases (Test 10): (a) UNCERTAIN with no findings,
    (b) incomplete set, (c) duplicate lens id (load_lens_verdicts rejects it),
    (d) unknown verdict, (e) SKIPPED required lens, (f) failed mechanical
    check -- each NEEDS-WORK -- and (g) the known-good six-lens anchor -> PASS.
    Prints
    UNIT TESTS PASSED + returns 0 on success; prints UNIT TEST FAILED:
    <reason> + returns 1 on first failure.
    """
    try:
        # Test 1: rule 6 escalation chain FYI -> Nit -> Block across 3 runs.
        def _mk_lv(severity: str, rationale: str) -> list[dict]:
            return [
                {
                    "lens_id": "correctness",
                    "model_tier": "sonnet",
                    "authority": "a",
                    "coverage_claim": "c",
                    "findings": [
                        {
                            "severity": severity,
                            "file_line": "x.py:42",
                            "excerpt": "e",
                            "rationale": rationale,
                            "anti_pattern": "silent-wiring",
                        }
                    ],
                    "overall_verdict": "NEEDS-WORK",
                },
                {
                    "lens_id": "bugs",
                    "model_tier": "sonnet",
                    "authority": "a",
                    "coverage_claim": "c",
                    "findings": [
                        {
                            "severity": "Nit",
                            "file_line": "x.py:42",
                            "excerpt": "e",
                            "rationale": "bugs lens at same line",
                            "anti_pattern": "silent-wiring",
                        }
                    ],
                    "overall_verdict": "NEEDS-WORK",
                },
            ]

        # Run 1: correctness emits Nit; rule 2 demotes correctness to FYI
        # because bugs is primary for silent-wiring.
        run1 = aggregate(
            _mk_lv("Nit", "original correctness rationale"),
            prior_sidecar=None,
            timestamp="2026-01-01T00-00-00",
            skill_version="v3",
        )
        c1 = run1["lens_verdicts"][0]["findings"][0]
        assert c1["severity"] == "FYI", (
            f"run 1: expected FYI after rule-2 demotion, got {c1['severity']!r}"
        )
        assert c1["rationale"].startswith("Demoted per rule 2:"), (
            f"run 1: expected Demoted prefix, got {c1['rationale'][:40]!r}"
        )

        # Run 2: same finding shape; rule 6 escalates current FYI to Nit.
        run2 = aggregate(
            _mk_lv("Nit", "original correctness rationale"),
            prior_sidecar=run1,
            timestamp="2026-01-02T00-00-00",
            skill_version="v3",
        )
        c2 = run2["lens_verdicts"][0]["findings"][0]
        assert c2["severity"] == "Nit", (
            f"run 2: expected Nit after rule-6 escalation (chain step 1), "
            f"got {c2['severity']!r}"
        )
        assert c2["rationale"].startswith("Persistent disagreement:"), (
            f"run 2: expected Persistent prefix, got {c2['rationale'][:40]!r}"
        )

        # Run 3: chain continues; rule 6 escalates from current FYI -> Nit
        # (because rule 2 demoted again), then matches prior's Persistent
        # entry, but identity-key now matches and current sev was Nit before
        # rule 2 ran first. Walk: rule 7 runs first (no-op), rule 2 demotes
        # correctness Nit -> FYI, rule 6 looks up (x.py:42, silent-wiring) in
        # prior (which is run 2's Persistent finding) -> matches -> escalates
        # current FYI -> Nit. To reach Block we feed run 2 as prior again with
        # input severity already Nit; rule 2 demotes Nit -> FYI -> rule 6
        # escalates FYI -> Nit. So Block requires that rule 2 NOT demote
        # (i.e., bugs lens absent OR not at the same file_line).
        # Adjusted: drop bugs lens for run 3 so rule 2 leaves Nit alone; rule
        # 6 then escalates Nit -> Block.
        run3_input = _mk_lv("Nit", "original correctness rationale")[:1]  # only correctness
        run3 = aggregate(
            run3_input,
            prior_sidecar=run2,
            timestamp="2026-01-03T00-00-00",
            skill_version="v3",
        )
        c3 = run3["lens_verdicts"][0]["findings"][0]
        assert c3["severity"] == "Block", (
            f"run 3: expected Block at chain step 2 (Nit -> Block), got "
            f"{c3['severity']!r}"
        )
        assert c3["rationale"].startswith("Persistent disagreement:"), (
            f"run 3: expected Persistent prefix, got {c3['rationale'][:40]!r}"
        )

        # Test 2: rule 7 dedup-demote with also_flagged_by annotation.
        def _abs_lv(lens_id: str, rationale: str) -> dict:
            return {
                "lens_id": lens_id,
                "model_tier": "sonnet",
                "authority": "a",
                "coverage_claim": "c",
                "findings": [
                    {
                        "severity": "Nit",
                        "file_line": "(absence -- no integration test)",
                        "excerpt": "",
                        "rationale": rationale,
                        "anti_pattern": "silent-wiring",
                    }
                ],
                "overall_verdict": "NEEDS-WORK",
            }

        lvs = [
            _abs_lv(
                "correctness",
                "missing integration test through production caller for handler",
            ),
            _abs_lv(
                "bugs",
                "missing integration test through production caller for handler",
            ),
        ]
        out = aggregate(
            lvs,
            prior_sidecar=None,
            timestamp="2026-01-01T00-00-00",
            skill_version="v3",
        )
        # bugs is primary for silent-wiring per ANTI_PATTERN_PRIMARY.
        bugs_lv = next(lv for lv in out["lens_verdicts"] if lv["lens_id"] == "bugs")
        corr_lv = next(
            lv for lv in out["lens_verdicts"] if lv["lens_id"] == "correctness"
        )
        bugs_f = bugs_lv["findings"][0]
        corr_f = corr_lv["findings"][0]
        assert bugs_f["severity"] == "Nit", (
            f"rule 7: bugs (primary) expected Nit, got {bugs_f['severity']!r}"
        )
        assert bugs_f.get("also_flagged_by") == ["correctness"], (
            f"rule 7: expected also_flagged_by=['correctness'], got "
            f"{bugs_f.get('also_flagged_by')!r}"
        )
        assert corr_f["severity"] == "FYI", (
            f"rule 7: secondary expected FYI, got {corr_f['severity']!r}"
        )
        assert corr_f["rationale"].startswith("Demoted per rule 7:"), (
            f"rule 7: expected Demoted prefix, got "
            f"{corr_f['rationale'][:40]!r}"
        )

        # Test 3: rule 7 scope-boundary-deferral exclusion.
        def _scope_lv() -> dict:
            return {
                "lens_id": "correctness",
                "model_tier": "sonnet",
                "authority": "a",
                "coverage_claim": "c",
                "findings": [
                    {
                        "severity": "Block",
                        "file_line": "(absence -- operator UAT required)",
                        "excerpt": "manual check needed",
                        "rationale": (
                            "missing integration test through production caller "
                            "for handler boundary scope"
                        ),
                        "anti_pattern": "scope-boundary-deferral",
                    }
                ],
                "overall_verdict": "NEEDS-WORK",
            }

        scope_and_real = [
            _scope_lv(),
            _abs_lv(
                "bugs",
                "missing integration test through production caller for handler",
            ),
        ]
        out2 = aggregate(
            scope_and_real,
            prior_sidecar=None,
            timestamp="2026-01-01T00-00-00",
            skill_version="v3",
        )
        # scope-boundary-deferral converts to deferred_uat_items; its severity
        # is demoted to FYI by extract_deferred_items, NOT by rule 7. Verify
        # rule 7 didn't ALSO demote the bugs absence as a "duplicate" of the
        # scope finding (i.e., bugs should still be at Nit, no rule-7 prefix).
        bugs_lv2 = next(lv for lv in out2["lens_verdicts"] if lv["lens_id"] == "bugs")
        bugs_f2 = bugs_lv2["findings"][0]
        assert not bugs_f2["rationale"].startswith("Demoted per rule 7:"), (
            f"rule 7 must skip scope-boundary-deferral when clustering: "
            f"bugs finding wrongly demoted: {bugs_f2['rationale'][:80]!r}"
        )
        # Also verify the scope-boundary-deferral became a deferred item.
        assert len(out2["deferred_uat_items"]) == 1, (
            f"expected 1 deferred item from scope-boundary-deferral, got "
            f"{len(out2['deferred_uat_items'])}"
        )

        # Test 4: empty lens dir -> NEEDS-WORK.
        out3 = aggregate(
            [],
            prior_sidecar=None,
            timestamp="2026-01-01T00-00-00",
            skill_version="v3",
        )
        assert out3["aggregated_verdict"]["result"] == "NEEDS-WORK", (
            f"empty lens-dir: expected NEEDS-WORK, got "
            f"{out3['aggregated_verdict']['result']!r}"
        )

        # Test 5: render_markdown Unicode + metachar smoke (no crash).
        smoke_sidecar = {
            "timestamp": "2026-01-01T00-00-00",
            "plan_step": None,
            "skill_version": "v3",
            "invocation": {
                "reviewers_flag": "code",
                "model_overrides": {},
                "force_runtime": False,
                "url": None,
                "start_cmd": None,
                "runtime_downgraded": False,
                "runtime_downgrade_reason": None,
            },
            "lens_verdicts": [
                {
                    "lens_id": "correctness",
                    "model_tier": "sonnet",
                    "authority": "a",
                    "coverage_claim": "c",
                    "findings": [
                        {
                            "severity": "Nit",
                            "file_line": "x.py:1",
                            "excerpt": "code with ``` triple backtick run",
                            "rationale": (
                                "Em-dash — smart “quote” and "
                                "`backtick` plus | pipe"
                            ),
                            "anti_pattern": None,
                        }
                    ],
                    "overall_verdict": "NEEDS-WORK",
                }
            ],
            "aggregated_verdict": {
                "result": "NEEDS-WORK",
                "rationale": "smoke test — em-dash.",
            },
            "model_tiers_used": {"correctness": "sonnet"},
            "deferred_uat_items": [],
        }
        rendered = render_markdown(smoke_sidecar)
        assert "## Lens verdicts" in rendered, (
            "render_markdown smoke: missing '## Lens verdicts' header"
        )
        assert "## Findings" in rendered, (
            "render_markdown smoke: missing '## Findings' header"
        )
        assert "Audit-trail JSON:" in rendered, (
            "render_markdown smoke: missing 'Audit-trail JSON:' footer"
        )

        # Test 6: rule 7 lint-finding dedup. A Bugs lens finding at
        # src/foo.py:12 ("unused import") and a lint finding at the same
        # file_line should demote the lens finding to FYI with rationale
        # prefixed "Cited-by-linter: ruff F401" and an
        # also_flagged_by_linter annotation.
        bugs_with_unused_import = [
            {
                "lens_id": "bugs",
                "model_tier": "sonnet",
                "authority": "a",
                "coverage_claim": "c",
                "findings": [
                    {
                        "severity": "Nit",
                        "file_line": "src/foo.py:12",
                        "excerpt": "import os",
                        "rationale": (
                            "unused import 'os' adds noise and can mask "
                            "future genuine usage"
                        ),
                        "anti_pattern": None,
                    }
                ],
                "overall_verdict": "NEEDS-WORK",
            }
        ]
        lint_findings_in = [
            {
                "tool": "ruff",
                "rule": "F401",
                "file_line": "src/foo.py:12",
                "message": "'os' imported but unused",
            }
        ]
        out4 = aggregate(
            bugs_with_unused_import,
            prior_sidecar=None,
            timestamp="2026-01-01T00-00-00",
            skill_version="v3",
            lint_findings=lint_findings_in,
        )
        bugs_lv4 = next(lv for lv in out4["lens_verdicts"] if lv["lens_id"] == "bugs")
        bugs_f4 = bugs_lv4["findings"][0]
        assert bugs_f4["severity"] == "FYI", (
            f"rule 7 lint-dedup: expected FYI after demote, got "
            f"{bugs_f4['severity']!r}"
        )
        assert bugs_f4["rationale"].startswith("Cited-by-linter: ruff F401"), (
            f"rule 7 lint-dedup: expected 'Cited-by-linter: ruff F401' "
            f"prefix, got {bugs_f4['rationale'][:60]!r}"
        )
        assert bugs_f4.get("also_flagged_by_linter") == {
            "tool": "ruff",
            "rule": "F401",
        }, (
            f"rule 7 lint-dedup: expected also_flagged_by_linter annotation, "
            f"got {bugs_f4.get('also_flagged_by_linter')!r}"
        )

        # Test 6b: HIGH normalization fix. Lens emits a RANGE with leading
        # './' (./src/foo.py:42-45); lint emits a single line (src/foo.py:43)
        # that lies WITHIN the range. The pre-fix raw-string compare missed
        # both the './' mismatch and the range case; the post-fix
        # _file_line_overlaps + _normalize_path catches it. The lens finding
        # must demote.
        bugs_with_range = [
            {
                "lens_id": "bugs",
                "model_tier": "sonnet",
                "authority": "a",
                "coverage_claim": "c",
                "findings": [
                    {
                        "severity": "Nit",
                        "file_line": "./src/foo.py:42-45",
                        "excerpt": "block of code with unused import",
                        "rationale": (
                            "range covers an unused import the linter also "
                            "flagged inside"
                        ),
                        "anti_pattern": None,
                    }
                ],
                "overall_verdict": "NEEDS-WORK",
            }
        ]
        lint_single_line_inside_range = [
            {
                "tool": "ruff",
                "rule": "F401",
                "file_line": "src/foo.py:43",
                "message": "'os' imported but unused",
            }
        ]
        out4b = aggregate(
            bugs_with_range,
            prior_sidecar=None,
            timestamp="2026-01-01T00-00-00",
            skill_version="v3",
            lint_findings=lint_single_line_inside_range,
        )
        bugs_lv4b = next(
            lv for lv in out4b["lens_verdicts"] if lv["lens_id"] == "bugs"
        )
        bugs_f4b = bugs_lv4b["findings"][0]
        assert bugs_f4b["severity"] == "FYI", (
            f"rule 7 normalize: range './src/foo.py:42-45' vs single-line "
            f"'src/foo.py:43' must demote, got {bugs_f4b['severity']!r}"
        )
        assert bugs_f4b["rationale"].startswith("Cited-by-linter: ruff F401"), (
            f"rule 7 normalize: expected 'Cited-by-linter: ruff F401' prefix, "
            f"got {bugs_f4b['rationale'][:60]!r}"
        )

        # Test 7: load_lint_findings I/O round-trip + missing-file graceful.
        tmpdir = Path(tempfile.mkdtemp(prefix="agg-test7-"))
        try:
            lint_path = tmpdir / "lint-findings.json"
            payload = {
                "timestamp": "2026-01-01T00-00-00",
                "tools_run": ["ruff"],
                "tools_skipped": [],
                "findings": [
                    {
                        "tool": "ruff",
                        "rule": "F401",
                        "file_line": "src/foo.py:12",
                        "message": "'os' imported but unused",
                    },
                    {
                        "tool": "mypy",
                        "rule": "assignment",
                        "file_line": "src/bar.py:7",
                        "message": "Incompatible types in assignment",
                    },
                ],
            }
            lint_path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = load_lint_findings(lint_path)
            assert len(loaded) == 2, (
                f"load_lint_findings: expected 2 findings, got {len(loaded)}"
            )
            assert loaded[0]["tool"] == "ruff", (
                f"load_lint_findings: entry 0 tool expected 'ruff', "
                f"got {loaded[0].get('tool')!r}"
            )
            assert loaded[1]["file_line"] == "src/bar.py:7", (
                f"load_lint_findings: entry 1 file_line expected "
                f"'src/bar.py:7', got {loaded[1].get('file_line')!r}"
            )
            # Missing-file path: graceful empty list.
            missing = load_lint_findings(tmpdir / "does-not-exist.json")
            assert missing == [], (
                f"load_lint_findings: missing file expected [], got {missing!r}"
            )
        finally:
            for child in tmpdir.iterdir():
                child.unlink()
            tmpdir.rmdir()

        # Test 8: scope-boundary-deferral exclusion in the LINT path. Test 3
        # already covers the ABSENCE path; this verifies the lint path also
        # skips scope-boundary-deferral findings (they're operator hand-offs,
        # not defects, and a lint co-citation must not "demote" them).
        scope_lens = [
            {
                "lens_id": "correctness",
                "model_tier": "sonnet",
                "authority": "a",
                "coverage_claim": "c",
                "findings": [
                    {
                        "severity": "Block",
                        "file_line": "src/foo.py:12",
                        "excerpt": "manual check needed",
                        "rationale": (
                            "scope-boundary deferral at this line; operator "
                            "must verify in UAT"
                        ),
                        "anti_pattern": "scope-boundary-deferral",
                    }
                ],
                "overall_verdict": "NEEDS-WORK",
            }
        ]
        lint_at_same_line = [
            {
                "tool": "ruff",
                "rule": "F401",
                "file_line": "src/foo.py:12",
                "message": "'os' imported but unused",
            }
        ]
        out5 = aggregate(
            scope_lens,
            prior_sidecar=None,
            timestamp="2026-01-01T00-00-00",
            skill_version="v3",
            lint_findings=lint_at_same_line,
        )
        # scope-boundary-deferral converts to a deferred_uat_item; rule 7's
        # lint path must NOT have demoted it OR added an
        # also_flagged_by_linter annotation. Locate the lens finding inside
        # the surviving lens_verdicts (extract_deferred_items removes the
        # finding from lens_verdicts, so the lens_verdicts findings list is
        # expected empty; the deferred item carries the audit trail). The
        # assertion is that no Cited-by-linter rationale prefix or
        # also_flagged_by_linter annotation leaked onto the deferred item.
        corr_lv5 = next(
            lv for lv in out5["lens_verdicts"] if lv["lens_id"] == "correctness"
        )
        # Either the finding was extracted to deferred_uat_items (empty
        # findings list) OR it survived in findings -- in both cases the
        # rule-7 lint path must have skipped it.
        for f in corr_lv5.get("findings", []):
            assert "also_flagged_by_linter" not in f, (
                f"rule 7 lint path: scope-boundary-deferral wrongly "
                f"annotated, got {f.get('also_flagged_by_linter')!r}"
            )
            assert not f.get("rationale", "").startswith("Cited-by-linter:"), (
                f"rule 7 lint path: scope-boundary-deferral wrongly cited, "
                f"got {f['rationale'][:60]!r}"
            )
        for item in out5.get("deferred_uat_items", []):
            assert "also_flagged_by_linter" not in item, (
                f"rule 7 lint path: deferred item wrongly annotated, "
                f"got {item.get('also_flagged_by_linter')!r}"
            )

        # Test 9: Security is the PRIMARY OWNER of security findings (rule 2).
        # A Security lens and a Bugs lens both flag the same security-class
        # defect (anti_pattern 'secret-dump') at the SAME file_line. Per
        # ANTI_PATTERN_PRIMARY['secret-dump'] == 'security', Security keeps its
        # Block and the Bugs copy demotes to FYI with the rule-2 prefix. Also
        # asserts 'security' sits AFTER 'bugs' in CODE_LENS_ORDER so the
        # documented spawn order stays coherent (SKILL.md Standing lens list).
        assert "security" in CODE_LENS_ORDER, "security must be a code lens"
        assert CODE_LENS_ORDER.index("security") == CODE_LENS_ORDER.index("bugs") + 1, (
            "CODE_LENS_ORDER: 'security' must immediately follow 'bugs', got "
            f"{CODE_LENS_ORDER!r}"
        )
        assert ANTI_PATTERN_PRIMARY.get("secret-dump") == "security", (
            "ANTI_PATTERN_PRIMARY['secret-dump'] must route to 'security', got "
            f"{ANTI_PATTERN_PRIMARY.get('secret-dump')!r}"
        )

        def _sec_coflag_lv(lens_id: str, rationale: str) -> dict:
            return {
                "lens_id": lens_id,
                "model_tier": "sonnet",
                "authority": "a",
                "coverage_claim": "c",
                "findings": [
                    {
                        "severity": "Block",
                        "file_line": "scripts/debug_env.sh:3",
                        "excerpt": "cat /etc/void_furnace/secrets.env",
                        "rationale": rationale,
                        "anti_pattern": "secret-dump",
                    }
                ],
                "overall_verdict": "NEEDS-WORK",
            }

        sec_coflag = [
            _sec_coflag_lv(
                "bugs",
                "stdout round-trip of a secrets-bearing file leaks secrets",
            ),
            _sec_coflag_lv(
                "security",
                "secret-dump per security.md; use stat/wc/file metadata check",
            ),
        ]
        out6 = aggregate(
            sec_coflag,
            prior_sidecar=None,
            timestamp="2026-01-01T00-00-00",
            skill_version="v3",
        )
        sec_lv6 = next(
            lv for lv in out6["lens_verdicts"] if lv["lens_id"] == "security"
        )
        bugs_lv6 = next(
            lv for lv in out6["lens_verdicts"] if lv["lens_id"] == "bugs"
        )
        sec_f6 = sec_lv6["findings"][0]
        bugs_f6 = bugs_lv6["findings"][0]
        # (a) Security is the primary owner -> keeps its Block.
        assert sec_f6["severity"] == "Block", (
            f"rule 2 security-primary: Security must keep Block, got "
            f"{sec_f6['severity']!r}"
        )
        assert not sec_f6["rationale"].startswith("Demoted per rule 2:"), (
            f"rule 2 security-primary: Security must NOT be demoted, got "
            f"{sec_f6['rationale'][:40]!r}"
        )
        # (b) The Bugs copy demotes to FYI per rule 2.
        assert bugs_f6["severity"] == "FYI", (
            f"rule 2 security-primary: Bugs co-flag must demote to FYI, got "
            f"{bugs_f6['severity']!r}"
        )
        assert bugs_f6["rationale"].startswith("Demoted per rule 2:"), (
            f"rule 2 security-primary: Bugs copy must carry rule-2 prefix, got "
            f"{bugs_f6['rationale'][:40]!r}"
        )
        # The aggregated verdict stays NEEDS-WORK (the surviving Block).
        assert out6["aggregated_verdict"]["result"] == "NEEDS-WORK", (
            f"rule 2 security-primary: expected NEEDS-WORK (1 surviving Block), "
            f"got {out6['aggregated_verdict']['result']!r}"
        )

        # Test 10: default-deny PASS (P-RD-1 variant (a)). Each garbage case
        # (a)-(f) must aggregate to NEEDS-WORK; the known-good anchor (g)
        # must still PASS, so a reducer that always says NEEDS-WORK fails too.
        def _six() -> list[dict]:
            lenses = [
                {
                    "lens_id": lens_id,
                    "model_tier": "haiku" if lens_id == "style" else "sonnet",
                    "authority": "a",
                    "coverage_claim": "c",
                    "findings": [],
                    "overall_verdict": "PASS",
                }
                for lens_id in CODE_LENS_ORDER
            ]
            lenses[-1]["overall_verdict"] = "SKIPPED"
            return lenses

        def _result(lenses: list[dict], **kwargs) -> str:
            return aggregate(
                lenses, timestamp="2026-01-01T00-00-00", skill_version="v3", **kwargs
            )["aggregated_verdict"]["result"]

        assert _result(_six()) == "PASS", "(g) known-good six-lens anchor must PASS"
        case_a = _six()
        case_a[0]["overall_verdict"] = "UNCERTAIN"
        assert _result(case_a) == "NEEDS-WORK", "(a) UNCERTAIN must not PASS"
        assert _result(_six()[:3]) == "NEEDS-WORK", "(b) incomplete set must not PASS"
        case_c = _six() + [_six()[0]]
        assert _result(case_c) == "NEEDS-WORK", "(c) duplicate lens must not PASS"
        case_d = _six()
        case_d[1]["overall_verdict"] = "pass"
        assert _result(case_d) == "NEEDS-WORK", "(d) unknown verdict must not PASS"
        case_e = _six()
        case_e[0]["overall_verdict"] = "SKIPPED"
        assert _result(case_e) == "NEEDS-WORK", "(e) SKIPPED required lens must not PASS"
        failing = {"checks": [{"check": "pytest", "status": "fail"}]}
        assert _result(_six(), mechanical_results=failing) == "NEEDS-WORK", (
            "(f) failed mechanical check must not PASS"
        )
        missing_tool = {"checks": [{"check": "mypy", "status": "missing-tool"}]}
        assert _result(_six(), mechanical_results=missing_tool) == "PASS", (
            "(f') missing-tool is listed but non-blocking"
        )
        dup_dir = Path(tempfile.mkdtemp(prefix="agg-test10-"))
        try:
            for name in ("correctness.json", "correctness-stale.json"):
                (dup_dir / name).write_text(json.dumps(_six()[0]), encoding="utf-8")
            try:
                load_lens_verdicts(dup_dir)
            except DuplicateLensError as dup:
                assert len(dup.records) == 2, "(c) duplicate records must be kept"
            else:
                raise AssertionError("(c) load_lens_verdicts must reject duplicates")
        finally:
            for child in dup_dir.iterdir():
                child.unlink()
            dup_dir.rmdir()

    except AssertionError as e:
        sys.stdout.write(f"UNIT TEST FAILED: {e}\n")
        return 1
    except Exception as e:  # noqa: BLE001 - any other crash is a test failure
        sys.stdout.write(f"UNIT TEST FAILED: unexpected exception: {e!r}\n")
        return 1
    sys.stdout.write("UNIT TESTS PASSED\n")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class _StoreOnce(argparse.Action):
    """`store` that refuses a second occurrence of the same option.

    argparse's default `store` keeps the LAST occurrence silently, so a repeated
    single-value option resolved last-wins: `--mechanical-results fail.json
    --mechanical-results ok.json` dropped a recorded fail, and a repeated
    `--lens-dir` or `--reviewers` swapped in another lens set or lane. A second
    occurrence, in the `--opt value` or the `--opt=value` form, is a usage error
    (parser.error: exit 2, no sidecar). Occurrences are tracked per parse.
    """

    SEEN = "_store_once_seen"

    def __call__(self, parser, namespace, values, option_string=None):
        seen = getattr(namespace, self.SEEN, None)
        if seen is None:
            seen = set()
            setattr(namespace, self.SEEN, seen)
        if self.dest in seen:
            parser.error(
                f"argument {'/'.join(self.option_strings)}: given more than once; "
                "each option is given at most once"
            )
        seen.add(self.dest)
        setattr(namespace, self.dest, values)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="review-deep multi-lens verdict aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--lens-dir",
        action=_StoreOnce,
        type=Path,
        help="Directory containing per-lens JSON verdict files (one per lens)",
    )
    parser.add_argument(
        "--output-dir",
        action=_StoreOnce,
        type=Path,
        help="Directory where the sidecar JSON will be written",
    )
    parser.add_argument(
        "--skill-version",
        action=_StoreOnce,
        default="v3",
        help="Skill version string to embed in the sidecar (default: v3)",
    )
    parser.add_argument(
        "--prior-sidecar",
        action=_StoreOnce,
        type=Path,
        default=None,
        help="Path to a prior sidecar JSON to enable rule 6 (persistent disagreement)",
    )
    parser.add_argument(
        "--lint-findings",
        action=_StoreOnce,
        type=Path,
        default=None,
        help=(
            "Path to a lint-findings.json from scripts/lint_prepass.sh; "
            "enables rule 7's lint dedup path. Defaults: search "
            "<--output-dir>/lint-findings.json, then .review-deep/lint-findings.json"
        ),
    )
    parser.add_argument(
        "--mechanical-results",
        action=_StoreOnce,
        type=Path,
        default=None,
        help=(
            "Path to this run's mechanical-check results JSON "
            '({"checks": [{"check", "status": "pass|fail|missing-tool", '
            '"command", "evidence"}]}); a "fail" or malformed entry is '
            "NEEDS-WORK, missing-tool is listed and non-blocking"
        ),
    )
    parser.add_argument(
        "--plan-step",
        action=_StoreOnce,
        default=None,
        help=(
            "<plan-file-path>:<step-id> the review was run against (the step "
            "id is the token after the last colon, e.g. 12, 5a, 22-prep, D.6); "
            "recorded as plan_step and makes a SKIPPED plan-conformance lens "
            "NEEDS-WORK"
        ),
    )
    parser.add_argument(
        "--reviewers",
        action=_StoreOnce,
        choices=REVIEWERS_FLAGS,
        default="code",
        help="Review lane that ran (default: code); drives lens-set completeness",
    )
    parser.add_argument(
        "--force-runtime",
        action="store_true",
        help="Record that the auth-gate probe was skipped by --force-runtime",
    )
    parser.add_argument(
        "--runtime-downgrade-reason",
        action=_StoreOnce,
        default=None,
        help=(
            "Auth-gate probe reason token when runtime lenses were downgraded "
            "(status_401 | redirect_to_login:<url> | login_form_in_200_body | timeout)"
        ),
    )
    parser.add_argument(
        "--timestamp",
        action=_StoreOnce,
        default=None,
        help="ISO-8601 timestamp override (filesystem-safe; default: now)",
    )
    parser.add_argument(
        "--self-test",
        action=_StoreOnce,
        type=Path,
        default=None,
        help="Round-trip self-test against an M1 baseline sidecar; exits after",
    )
    parser.add_argument(
        "--unit-test",
        action="store_true",
        help="Run in-process unit tests for aggregator rules 6/7 + smoke checks; exits after",
    )
    args = parser.parse_args(argv)
    vars(args).pop(_StoreOnce.SEEN, None)
    if args.plan_step is not None and not _PLAN_STEP_RE.fullmatch(args.plan_step):
        parser.error("--plan-step must be <plan-file-path>:<step-id>")
    if args.runtime_downgrade_reason is not None:
        if not _RUNTIME_DOWNGRADE_RE.match(args.runtime_downgrade_reason):
            parser.error("--runtime-downgrade-reason is not an auth-gate probe reason token")
        if args.reviewers == "code" or args.force_runtime:
            parser.error(
                "--runtime-downgrade-reason needs --reviewers runtime|full "
                "and excludes --force-runtime"
            )
    return args


def main(argv: list[str] | None = None) -> int:
    # Reconfigure stdout to UTF-8 with replacement on Windows so non-ASCII
    # rationale/excerpt content (em-dashes, smart quotes) does not crash the
    # process under cp1252. errors="replace" keeps downstream pipes (`| less`,
    # `> file.md` under exotic locales) from tripping too.
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass  # Python < 3.7 lacks reconfigure

    args = _parse_args(argv)

    if args.unit_test:
        return run_unit_tests()

    if args.self_test is not None:
        return run_self_test(args.self_test)

    if args.lens_dir is None or args.output_dir is None:
        sys.stderr.write(
            "error: --lens-dir and --output-dir are required (or pass --self-test)\n"
        )
        return 2

    lens_file_problems: list[str] = []
    try:
        lens_verdicts = load_lens_verdicts(args.lens_dir)
    except LensSetError as e:
        # Never overwrite a duplicate and never let a record under another
        # file name fill a slot: reduce every record so the lens-set checks
        # report it and the verdict is NEEDS-WORK with all evidence kept.
        sys.stderr.write(f"warning: {e}; the lens set is non-passing\n")
        lens_verdicts = e.records
        lens_file_problems = e.problems
    except (OSError, ValueError) as e:
        sys.stderr.write(
            f"error: lens input rejected: {e}. No sidecar written; this run "
            f"has no verdict and is non-passing.\n"
        )
        return 1

    mechanical_results = None
    if args.mechanical_results is not None:
        try:
            # Duplicate keys rejected (a "fail" then "pass" status must not
            # resolve last-wins); a JSON null is reduced as malformed below.
            mechanical_results = load_json_strict(args.mechanical_results)
        except (OSError, ValueError) as e:
            sys.stderr.write(
                f"error: --mechanical-results unreadable: {e}. No sidecar "
                f"written; this run has no verdict and is non-passing.\n"
            )
            return 2

    prior_sidecar = None
    if args.prior_sidecar is not None:
        with args.prior_sidecar.open("r", encoding="utf-8") as f:
            prior_sidecar = json.load(f)

    # Resolve --lint-findings: explicit flag wins; otherwise search
    # <output-dir>/lint-findings.json, then .review-deep/lint-findings.json.
    lint_findings_path: Path | None = args.lint_findings
    if lint_findings_path is None:
        candidate = args.output_dir / "lint-findings.json"
        if candidate.exists():
            lint_findings_path = candidate
        else:
            fallback = Path(".review-deep") / "lint-findings.json"
            if fallback.exists():
                lint_findings_path = fallback
    lint_findings = load_lint_findings(lint_findings_path)

    timestamp = args.timestamp or datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    invocation = default_invocation(
        args.reviewers,
        force_runtime=args.force_runtime,
        runtime_downgrade_reason=args.runtime_downgrade_reason,
    )
    try:
        sidecar = aggregate(
            lens_verdicts,
            prior_sidecar=prior_sidecar,
            timestamp=timestamp,
            skill_version=args.skill_version,
            plan_step=args.plan_step,
            invocation=invocation,
            lint_findings=lint_findings,
            mechanical_results=mechanical_results,
            mechanical_results_supplied=args.mechanical_results is not None,
            lens_file_problems=lens_file_problems,
        )
    except ValueError as e:
        sys.stderr.write(
            f"error: lens input rejected: {e}. No sidecar written; this run "
            f"has no verdict and is non-passing.\n"
        )
        return 1

    sidecar_path = write_sidecar(sidecar, args.output_dir)
    sys.stderr.write(f"Sidecar written: {sidecar_path}\n")
    sys.stdout.write(render_markdown(sidecar))
    return 0


if __name__ == "__main__":
    sys.exit(main())
