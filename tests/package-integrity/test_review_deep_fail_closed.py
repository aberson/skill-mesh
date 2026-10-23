"""Fail-closed gate for review-deep's deterministic reducer (P-RD-1, variant (a)).

review-deep's `scripts/aggregate.py` is the verdict authority for the deep
review lane: build-step passes its `aggregated_verdict.result` through. Before
this gate, a lens `UNCERTAIN` with no findings, an incomplete or duplicated
lens set, an unknown `overall_verdict`, a SKIPPED required lens and a failed
mechanical check all reduced to `PASS` (review-deep packet D1-D4, D9, D10, D16,
G10). Every case here therefore drives the PRODUCTION entry point -- the CLI,
run as a subprocess exactly as the core's invocation line documents it -- in a
temporary directory outside the repository, with a fresh lens directory and an
explicit `--lint-findings` file per run (the core's run-binding rule).

Variant (a) keeps the sidecar enum `PASS | NEEDS-WORK | DEFERRED-TO-UAT`, so
every garbage case must land on `NEEDS-WORK`. The known-good anchors
(six valid PASS/SKIPPED lenses, with and without passing mechanical results;
a runtime lane with one runtime lens that ran) must still land on `PASS`, so a
reducer that answered NEEDS-WORK for everything fails here too. The sidecar
key order and the `invocation` key set are consumer contracts (build-step's
deep lane and the Codex recipe), so the anchor pins them as well.

Correction cycle 1 adds the false-PASS paths the first review found: a
supplied mechanical record that is not an object (JSON `null`), a runtime lens
record under a recorded runtime downgrade, a prior sidecar or a misnamed file
in the lens dir, and duplicate JSON keys; plus the `--plan-step` grammar
(non-integer step ids accepted, a bare path rejected).

Correction cycle 2 adds the argv-level sibling of the duplicate-key case: a
single-value option given twice used to resolve last-wins, so a second
`--mechanical-results`, `--lens-dir` or `--reviewers` silently replaced the
first (a recorded mechanical `fail`, the current lens dir, or the stricter
lane was dropped and the run gave PASS). Every single-value option given
twice -- in the `--opt value` or the `--opt=value` form -- must exit 2 with no
sidecar, while the same option given once still parses.
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AGGREGATE = REPO_ROOT / "skills" / "review-deep" / "scripts" / "aggregate.py"

TIMESTAMP = "2026-10-12T00-00-00"
CODE_LENSES = ("correctness", "bugs", "security", "test-quality", "style", "plan-conformance")
SIDECAR_KEYS = ["timestamp", "plan_step", "skill_version", "invocation", "lens_verdicts",
                "aggregated_verdict", "model_tiers_used", "deferred_uat_items", "mechanical_results"]
INVOCATION_KEYS = {"reviewers_flag", "model_overrides", "force_runtime", "url", "start_cmd",
                   "runtime_downgraded", "runtime_downgrade_reason"}


def _lens(lens_id, verdict="PASS", findings=None):
    record = {"lens_id": lens_id, "model_tier": "haiku" if lens_id == "style" else "sonnet",
              "authority": lens_id, "coverage_claim": "fixture", "findings": findings or []}
    if verdict is not None:
        record["overall_verdict"] = verdict
    return record


def _six(plan_skipped=True):
    lenses = [_lens(lens_id) for lens_id in CODE_LENSES]
    if plan_skipped:
        lenses[-1]["overall_verdict"] = "SKIPPED"
    return lenses


_ABSENT = object()  # `--mechanical-results` not passed (distinct from a JSON `null` file)


def _run(tmp_path, lenses, *extra, files=None, raw_files=None, lint=None, mechanical=_ABSENT,
         mechanical_raw=None, run_name="run", expect_rc=0):
    """Run the production CLI over a FRESH lens dir; return (sidecar, stdout).

    `files` adds JSON records under explicit file names; `raw_files` and
    `mechanical_raw` write exact text (for inputs `json.dumps` cannot produce,
    such as duplicate keys)."""
    run = tmp_path / run_name
    lens_dir = run / "lenses"
    lens_dir.mkdir(parents=True)
    for record in lenses:
        (lens_dir / f"{record['lens_id']}.json").write_text(json.dumps(record), encoding="utf-8")
    for name, record in (files or {}).items():
        (lens_dir / name).write_text(json.dumps(record), encoding="utf-8")
    for name, text in (raw_files or {}).items():
        (lens_dir / name).write_text(text, encoding="utf-8")
    lint_path = run / "lint-findings.json"
    lint_path.write_text(json.dumps({"timestamp": TIMESTAMP, "tools_run": [], "tools_skipped": [],
                                     "findings": lint or []}), encoding="utf-8")
    args = [sys.executable, str(AGGREGATE), "--lens-dir", str(lens_dir), "--output-dir",
            str(run / "out"), "--lint-findings", str(lint_path), "--timestamp", TIMESTAMP, *extra]
    if mechanical is not _ABSENT or mechanical_raw is not None:
        mech_path = run / "mechanical-results.json"
        text = mechanical_raw if mechanical_raw is not None else json.dumps(mechanical)
        mech_path.write_text(text, encoding="utf-8")
        args += ["--mechanical-results", str(mech_path)]
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(args, cwd=run, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)
    assert proc.returncode == expect_rc, proc.stdout + proc.stderr
    sidecar_path = run / "out" / f"{TIMESTAMP}.json"
    if expect_rc != 0:
        assert not sidecar_path.exists(), "a rejected run must not leave a verdict behind"
        return None, proc.stdout + proc.stderr
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    return sidecar, proc.stdout


def _assert_needs_work(sidecar, stdout, needle):
    result = sidecar["aggregated_verdict"]
    assert result["result"] == "NEEDS-WORK", result
    assert needle in result["rationale"], result["rationale"]
    assert stdout.startswith("# review-deep: NEEDS-WORK\n"), stdout[:200]
    assert result["result"] != "PASS"


# ---------------------------------------------------------------- known-good anchors


def test_g_known_good_six_lens_set_passes(tmp_path):
    sidecar, stdout = _run(tmp_path, _six())
    assert sidecar["aggregated_verdict"]["result"] == "PASS", sidecar["aggregated_verdict"]
    assert stdout.startswith("# review-deep: PASS\n"), stdout[:200]
    assert list(sidecar) == SIDECAR_KEYS
    assert set(sidecar["invocation"]) == INVOCATION_KEYS
    assert sidecar["invocation"]["reviewers_flag"] == "code"
    assert [v["lens_id"] for v in sidecar["lens_verdicts"]] == list(CODE_LENSES)
    assert sidecar["plan_step"] is None
    assert sidecar["mechanical_results"] is None
    assert stdout.rstrip("\n").endswith(f"Audit-trail JSON: .review-deep/{TIMESTAMP}.json")


def test_g_known_good_with_plan_step_and_passing_mechanical_checks(tmp_path):
    mechanical = {"checks": [
        {"check": "pytest", "status": "pass", "command": "python -m pytest", "evidence": "3 passed"},
        {"check": "mypy", "status": "missing-tool", "command": "mypy .", "evidence": "not installed"}]}
    sidecar, stdout = _run(tmp_path, _six(plan_skipped=False), "--plan-step", "plan.md:1",
                           mechanical=mechanical)
    assert sidecar["aggregated_verdict"]["result"] == "PASS", sidecar["aggregated_verdict"]
    assert sidecar["plan_step"] == "plan.md:1"
    assert sidecar["mechanical_results"] == mechanical
    # MISSING-TOOL is listed but non-blocking (core: warn, skip only that check).
    assert "MISSING-TOOL" in sidecar["aggregated_verdict"]["rationale"]
    assert "mypy" in sidecar["aggregated_verdict"]["rationale"]


def test_g_known_good_runtime_lane_with_a_runtime_lens(tmp_path):
    lenses = [_lens(lens_id, "SKIPPED") for lens_id in CODE_LENSES] + [_lens("ui")]
    sidecar, _ = _run(tmp_path, lenses, "--reviewers", "runtime")
    assert sidecar["aggregated_verdict"]["result"] == "PASS", sidecar["aggregated_verdict"]
    assert [v["lens_id"] for v in sidecar["lens_verdicts"]] == [*CODE_LENSES, "ui"]
    assert sidecar["invocation"]["reviewers_flag"] == "runtime"


# ---------------------------------------------------------------- garbage cases (a)-(f)


def test_a_uncertain_lens_without_findings_is_needs_work(tmp_path):
    lenses = _six()
    lenses[0]["overall_verdict"] = "UNCERTAIN"
    sidecar, stdout = _run(tmp_path, lenses)
    _assert_needs_work(sidecar, stdout, "UNCERTAIN")
    assert "correctness" in sidecar["aggregated_verdict"]["rationale"]


def test_a2_needs_clarification_without_block_is_needs_work(tmp_path):
    lenses = _six(plan_skipped=False)
    lenses[-1]["overall_verdict"] = "NEEDS-CLARIFICATION"
    sidecar, stdout = _run(tmp_path, lenses, "--plan-step", "plan.md:9")
    _assert_needs_work(sidecar, stdout, "NEEDS-CLARIFICATION")


def test_b_incomplete_lens_set_is_needs_work(tmp_path):
    sidecar, stdout = _run(tmp_path, _six()[:3])
    _assert_needs_work(sidecar, stdout, "missing required lens")
    for absent in ("test-quality", "style", "plan-conformance"):
        assert absent in sidecar["aggregated_verdict"]["rationale"]


def test_c_duplicate_lens_file_is_needs_work_and_retains_both(tmp_path):
    sidecar, stdout = _run(tmp_path, _six(), files={"correctness-rerun.json": _lens("correctness")})
    _assert_needs_work(sidecar, stdout, "duplicate lens_id: correctness")
    ids = [v["lens_id"] for v in sidecar["lens_verdicts"]]
    assert ids.count("correctness") == 2, ids


def test_c2_extra_lens_is_needs_work(tmp_path):
    sidecar, stdout = _run(tmp_path, _six() + [_lens("ui")])
    _assert_needs_work(sidecar, stdout, "unexpected lens")


@pytest.mark.parametrize("verdict", ["pass", None, "APPROVED"], ids=["lowercase", "missing", "unknown"])
def test_d_unknown_or_missing_verdict_is_needs_work(tmp_path, verdict):
    lenses = _six()
    if verdict is None:
        del lenses[1]["overall_verdict"]
    else:
        lenses[1]["overall_verdict"] = verdict
    sidecar, stdout = _run(tmp_path, lenses)
    _assert_needs_work(sidecar, stdout, "invalid overall_verdict")
    assert "bugs" in sidecar["aggregated_verdict"]["rationale"]


def test_e_skipped_required_lens_is_needs_work(tmp_path):
    lenses = _six()
    lenses[0]["overall_verdict"] = "SKIPPED"
    sidecar, stdout = _run(tmp_path, lenses)
    _assert_needs_work(sidecar, stdout, "required lens SKIPPED: correctness")


def test_e2_plan_conformance_skipped_despite_plan_step_is_needs_work(tmp_path):
    sidecar, stdout = _run(tmp_path, _six(plan_skipped=True), "--plan-step", "plan.md:2")
    _assert_needs_work(sidecar, stdout, "required lens SKIPPED: plan-conformance")


def test_e3_pure_runtime_downgrade_is_needs_work(tmp_path):
    lenses = [_lens(lens_id, "SKIPPED") for lens_id in CODE_LENSES]
    sidecar, stdout = _run(tmp_path, lenses, "--reviewers", "runtime",
                           "--runtime-downgrade-reason", "status_401")
    _assert_needs_work(sidecar, stdout, "no runtime lens ran")
    assert sidecar["invocation"]["runtime_downgraded"] is True
    assert sidecar["invocation"]["runtime_downgrade_reason"] == "status_401"


def test_f_failed_mechanical_check_is_needs_work(tmp_path):
    mechanical = {"checks": [{"check": "pytest", "status": "fail", "command": "python -m pytest",
                              "evidence": "1 failed, 2 passed"}]}
    sidecar, stdout = _run(tmp_path, _six(), mechanical=mechanical)
    _assert_needs_work(sidecar, stdout, "mechanical check failed: pytest")
    assert sidecar["mechanical_results"] == mechanical


@pytest.mark.parametrize("mechanical", [
    {"checks": [{"check": "pytest", "status": "ok"}]},
    {"checks": []},
    {"results": []},
    None,
    [],
    False,
], ids=["unknown-status", "empty-phase", "wrong-shape", "json-null", "json-array", "json-false"])
def test_f2_malformed_mechanical_result_is_needs_work(tmp_path, mechanical):
    """A SUPPLIED record that is not an object -- including JSON `null` -- is
    malformed, not the legacy flag-absent path (cycle-1 F1), and the sidecar
    echo stays distinguishable from flag-absent (`null`)."""
    sidecar, stdout = _run(tmp_path, _six(), mechanical=mechanical)
    _assert_needs_work(sidecar, stdout, "invalid mechanical result")
    assert sidecar["mechanical_results"] is not None
    if not isinstance(mechanical, dict):
        assert sidecar["mechanical_results"] == {"malformed_input": mechanical}


def test_f3_unreadable_mechanical_results_writes_no_verdict(tmp_path):
    lenses_dir = tmp_path / "x"
    lenses_dir.mkdir()
    _, output = _run(tmp_path, _six(), "--mechanical-results", str(lenses_dir / "absent.json"),
                     expect_rc=2)
    assert "mechanical-results" in output


def test_pass_lens_with_block_cannot_be_laundered_by_lint_dedup(tmp_path):
    """A stale lint finding at the same line demotes the Block to FYI (rule 7);
    the self-contradictory PASS record must still be non-passing."""
    lenses = _six()
    lenses[1]["findings"] = [{"severity": "Block", "file_line": "counter.py:3", "excerpt": "count = 1",
                              "rationale": "reset sets the wrong value"}]
    lint = [{"tool": "ruff", "rule": "F841", "file_line": "counter.py:3", "message": "stale"}]
    sidecar, stdout = _run(tmp_path, lenses, lint=lint)
    _assert_needs_work(sidecar, stdout, "PASS lens carries Block/Nit findings: bugs")


def test_malformed_lens_record_writes_no_verdict(tmp_path):
    lenses = _six()
    lenses[0]["findings"] = None
    _, output = _run(tmp_path, lenses, expect_rc=1)
    assert "findings" in output


# ---------------------------------------------------------------- correction cycle 1 (F2-F5)


def _without(*lens_ids, plan_skipped=True):
    return [record for record in _six(plan_skipped) if record["lens_id"] not in lens_ids]


def test_runtime_downgrade_with_a_runtime_lens_record_is_needs_work(tmp_path):
    """F2: under a recorded downgrade runtime lenses were never spawned, so a
    runtime record is stale or fabricated, and `--reviewers runtime` with a
    recorded downgrade is NEEDS-WORK unconditionally (core: On downgrade)."""
    lenses = [_lens(lens_id, "SKIPPED") for lens_id in CODE_LENSES] + [_lens("ui")]
    sidecar, stdout = _run(tmp_path, lenses, "--reviewers", "runtime",
                           "--runtime-downgrade-reason", "status_401")
    _assert_needs_work(sidecar, stdout, "runtime lens record present under a recorded runtime downgrade: ui")
    assert "status_401" in sidecar["aggregated_verdict"]["rationale"]
    assert sidecar["invocation"]["runtime_downgraded"] is True


def test_full_lane_downgrade_with_a_runtime_lens_record_is_needs_work(tmp_path):
    lenses = _six() + [_lens("ui")]
    sidecar, stdout = _run(tmp_path, lenses, "--reviewers", "full",
                           "--runtime-downgrade-reason", "status_401")
    _assert_needs_work(sidecar, stdout, "runtime lens record present under a recorded runtime downgrade: ui")


def test_full_lane_downgrade_without_runtime_records_keeps_its_result(tmp_path):
    """F2 must not change this case: `full` + recorded downgrade + six code
    lenses and no runtime record is computed from the code lenses as before
    (the deferral question is the separate, recorded R-A3 limitation)."""
    sidecar, _ = _run(tmp_path, _six(), "--reviewers", "full",
                      "--runtime-downgrade-reason", "status_401")
    assert sidecar["aggregated_verdict"]["result"] == "PASS", sidecar["aggregated_verdict"]


def test_lens_dir_holding_only_an_old_sidecar_writes_no_verdict(tmp_path):
    """F3: a prior run's audit-trail JSON in --lens-dir is not a lens record;
    it must never fill the six slots (the producer's real sidecar is reused)."""
    old, _ = _run(tmp_path, _six(), run_name="earlier")
    assert old["aggregated_verdict"]["result"] == "PASS"
    _, output = _run(tmp_path, [], files={f"{TIMESTAMP}.json": old}, expect_rc=1)
    assert "sidecar" in output


def test_record_under_another_file_name_cannot_fill_a_slot(tmp_path):
    """F3: five current files plus `zz-prev.json` carrying lens_id correctness."""
    sidecar, stdout = _run(tmp_path, _without("correctness"),
                           files={"zz-prev.json": _lens("correctness")})
    _assert_needs_work(sidecar, stdout, "lens file zz-prev.json holds lens_id 'correctness'")
    assert [v["lens_id"] for v in sidecar["lens_verdicts"]] == list(CODE_LENSES)


def test_swapped_lens_file_names_are_needs_work(tmp_path):
    """F3: `bugs.json` holds correctness and `x.json` holds bugs."""
    sidecar, stdout = _run(tmp_path, _without("correctness", "bugs"),
                           files={"bugs.json": _lens("correctness"), "x.json": _lens("bugs")})
    _assert_needs_work(sidecar, stdout, "lens file bugs.json holds lens_id 'correctness'")
    assert "lens file x.json holds lens_id 'bugs'" in sidecar["aggregated_verdict"]["rationale"]
    assert [v["lens_id"] for v in sidecar["lens_verdicts"]] == list(CODE_LENSES)


def test_duplicate_key_lens_record_writes_no_verdict(tmp_path):
    """F4: `UNCERTAIN` then `PASS` under one key must not resolve last-wins."""
    record = json.dumps(_lens("correctness", verdict=None))[:-1]
    raw = record + ', "overall_verdict": "UNCERTAIN", "overall_verdict": "PASS"}'
    _, output = _run(tmp_path, _without("correctness"), raw_files={"correctness.json": raw},
                     expect_rc=1)
    assert "duplicate JSON key" in output


def test_duplicate_key_mechanical_record_writes_no_verdict(tmp_path):
    """F4: a mechanical `fail` then `pass` under one key must not resolve last-wins."""
    raw = ('{"checks": [{"check": "pytest", "status": "fail", "status": "pass", '
           '"command": "python -m pytest", "evidence": "1 failed"}]}')
    _, output = _run(tmp_path, _six(), mechanical_raw=raw, expect_rc=2)
    assert "duplicate JSON key" in output


@pytest.mark.parametrize("plan_step", [
    "plan.md:22-prep", "plan.md:3a", "plan.md:7-1", "plan.md:D.6", "C:/x/plan.md:12",
])
def test_plan_step_accepts_the_plan_grammar_step_ids(tmp_path, plan_step):
    """F5: the step id is the token after the last colon, not only an integer."""
    sidecar, _ = _run(tmp_path, _six(plan_skipped=False), "--plan-step", plan_step)
    assert sidecar["plan_step"] == plan_step
    assert sidecar["aggregated_verdict"]["result"] == "PASS", sidecar["aggregated_verdict"]


@pytest.mark.parametrize("plan_step", ["C:/x/plan.md", "plan.md", "plan.md:"])
def test_plan_step_without_a_step_id_writes_no_verdict(tmp_path, plan_step):
    _, output = _run(tmp_path, _six(plan_skipped=False), "--plan-step", plan_step, expect_rc=2)
    assert "--plan-step" in output


# ---------------------------------------------------------------- correction cycle 2 (F7): repeated options


def _lens_dir(path, lenses):
    path.mkdir(parents=True)
    for record in lenses:
        (path / f"{record['lens_id']}.json").write_text(json.dumps(record), encoding="utf-8")
    return path


def _lint_file(run):
    path = run / "lint-findings.json"
    path.write_text(json.dumps({"timestamp": TIMESTAMP, "tools_run": [], "tools_skipped": [],
                                "findings": []}), encoding="utf-8")
    return path


def _mechanical_file(run, name, status, check):
    path = run / name
    path.write_text(json.dumps({"checks": [{"check": check, "status": status, "command": check,
                                            "evidence": status}]}), encoding="utf-8")
    return path


def _cli(run, args):
    """Run the production CLI with exactly `args` (nothing injected); return
    (returncode, stdout, stderr, sidecar or None)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, str(AGGREGATE), *[str(a) for a in args]], cwd=run,
                          env=env, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120)
    written = sorted(run.glob("out*/*.json"))
    assert len(written) <= 1, written
    sidecar = json.loads(written[0].read_text(encoding="utf-8")) if written else None
    for path in written:  # each invocation starts from an empty output dir
        path.unlink()
    return proc.returncode, proc.stdout, proc.stderr, sidecar


def _assert_repeat_rejected(outcome, option):
    returncode, stdout, stderr, sidecar = outcome
    assert returncode == 2, stdout + stderr
    assert sidecar is None, "a rejected run must not leave a verdict behind"
    assert f"argument {option}: given more than once" in stderr, stderr
    assert "SELF-TEST" not in stdout and "# review-deep:" not in stdout, stdout


def _result(outcome):
    returncode, stdout, stderr, sidecar = outcome
    assert returncode == 0 and sidecar is not None, stdout + stderr
    return sidecar["aggregated_verdict"]["result"]


def test_j1_repeated_mechanical_results_cannot_drop_a_recorded_fail(tmp_path):
    """Judge J1: a `fail` record then a `pass` record used to give PASS."""
    run = tmp_path / "j1"
    lens_dir = _lens_dir(run / "lenses", _six())
    base = ["--lens-dir", lens_dir, "--output-dir", run / "out", "--lint-findings",
            _lint_file(run), "--timestamp", TIMESTAMP]
    fail = _mechanical_file(run, "fail.json", "fail", "lint_prepass")
    ok = _mechanical_file(run, "ok.json", "pass", "pytest")
    assert _result(_cli(run, [*base, "--mechanical-results", fail])) == "NEEDS-WORK"
    assert _result(_cli(run, [*base, "--mechanical-results", ok])) == "PASS"
    _assert_repeat_rejected(
        _cli(run, [*base, "--mechanical-results", fail, "--mechanical-results", ok]),
        "--mechanical-results")


def test_j2_repeated_lens_dir_cannot_swap_in_a_stale_passing_set(tmp_path):
    """Judge J2: the current UNCERTAIN dir then a stale six-PASS dir used to give PASS."""
    run = tmp_path / "j2"
    current = _six()
    current[0]["overall_verdict"] = "UNCERTAIN"
    current_dir = _lens_dir(run / "lenses-current", current)
    stale_dir = _lens_dir(run / "lenses-stale", _six())
    rest = ["--output-dir", run / "out", "--lint-findings", _lint_file(run), "--timestamp", TIMESTAMP]
    assert _result(_cli(run, ["--lens-dir", current_dir, *rest])) == "NEEDS-WORK"
    assert _result(_cli(run, ["--lens-dir", stale_dir, *rest])) == "PASS"
    _assert_repeat_rejected(
        _cli(run, ["--lens-dir", current_dir, "--lens-dir", stale_dir, *rest]), "--lens-dir")


def test_j3_repeated_reviewers_cannot_swap_the_lane(tmp_path):
    """Judge J3: six SKIPPED code lenses + `ui` PASS under `full` then `runtime`
    used to give PASS (under `full` alone it is NEEDS-WORK)."""
    run = tmp_path / "j3"
    lenses = [_lens(lens_id, "SKIPPED") for lens_id in CODE_LENSES] + [_lens("ui")]
    base = ["--lens-dir", _lens_dir(run / "lenses", lenses), "--output-dir", run / "out",
            "--lint-findings", _lint_file(run), "--timestamp", TIMESTAMP]
    assert _result(_cli(run, [*base, "--reviewers", "full"])) == "NEEDS-WORK"
    assert _result(_cli(run, [*base, "--reviewers", "runtime"])) == "PASS"
    _assert_repeat_rejected(_cli(run, [*base, "--reviewers", "full", "--reviewers", "runtime"]),
                            "--reviewers")


SINGLE_VALUE_OPTIONS = ("--lens-dir", "--output-dir", "--skill-version", "--prior-sidecar",
                        "--lint-findings", "--mechanical-results", "--plan-step", "--reviewers",
                        "--runtime-downgrade-reason", "--timestamp", "--self-test")


def _single_use_invocation(tmp_path, option):
    """A valid invocation that uses `option` once: (run dir, other args, value).

    Defaults are given explicitly where they exist (`--skill-version v3`,
    `--reviewers code`), so an explicit default must still parse."""
    run = tmp_path / "repeat"
    run.mkdir()
    lenses = _six(plan_skipped=option != "--plan-step")
    args = {"--lens-dir": _lens_dir(run / "lenses", lenses), "--output-dir": run / "out",
            "--lint-findings": _lint_file(run), "--timestamp": TIMESTAMP}
    prior = None
    if option in ("--prior-sidecar", "--self-test"):
        earlier, _ = _run(tmp_path, _six(), run_name="earlier")
        prior = run / "prior-sidecar.json"
        prior.write_text(json.dumps(earlier), encoding="utf-8")
    values = {"--skill-version": "v3", "--prior-sidecar": prior,
              "--mechanical-results": _mechanical_file(run, "ok.json", "pass", "pytest"),
              "--plan-step": "plan.md:1", "--reviewers": "code",
              "--runtime-downgrade-reason": "status_401", "--self-test": prior}
    value = args.pop(option) if option in args else values[option]
    other = [token for pair in args.items() for token in pair]
    if option == "--runtime-downgrade-reason":
        other += ["--reviewers", "full"]
    if option == "--self-test":
        other = []
    return run, other, value


@pytest.mark.parametrize("option", SINGLE_VALUE_OPTIONS)
def test_every_single_value_option_given_twice_writes_no_verdict(tmp_path, option):
    """F7: each single-value option is given at most once. Once -- here in the
    `--opt=value` form -- it parses (PASS, or SELF-TEST PASSED); twice, in the
    space form, the `=` form or a mix, with the SAME valid value, it exits 2
    with no sidecar."""
    run, other, value = _single_use_invocation(tmp_path, option)
    returncode, stdout, stderr, sidecar = _cli(run, [*other, f"{option}={value}"])
    assert returncode == 0, stdout + stderr
    if option == "--self-test":
        assert "SELF-TEST PASSED" in stdout, stdout
    else:
        assert sidecar["aggregated_verdict"]["result"] == "PASS", sidecar["aggregated_verdict"]
    for repeated in ([option, value, option, value],
                     [f"{option}={value}", f"{option}={value}"],
                     [option, value, f"{option}={value}"]):
        _assert_repeat_rejected(_cli(run, [*other, *repeated]), option)


# ---------------------------------------------------------------- library + unit-test entry points


def _load_module():
    """Import the production module without writing `__pycache__` into the package."""
    spec = importlib.util.spec_from_file_location("review_deep_aggregate_fail_closed", AGGREGATE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
        sys.modules.pop(spec.name, None)
    return module


def test_load_lens_verdicts_rejects_duplicate_ids(tmp_path):
    module = _load_module()
    for name, record in {"correctness.json": _lens("correctness"), "zz.json": _lens("correctness")}.items():
        (tmp_path / name).write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(module.DuplicateLensError) as excinfo:
        module.load_lens_verdicts(tmp_path)
    assert len(excinfo.value.records) == 2
    assert isinstance(excinfo.value, ValueError)


def test_aggregate_unit_test_mode_passes(tmp_path):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, str(AGGREGATE), "--unit-test"], cwd=tmp_path, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "UNIT TESTS PASSED" in proc.stdout
