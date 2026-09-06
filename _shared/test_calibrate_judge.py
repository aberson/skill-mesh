"""Pytest sibling tests for calibrate_judge.py.

Covers the Phase-2 calibration matrix with inline fixtures via tmp_path:
- Cohen's kappa hand-computed fixture (known 2x2 -> kappa == 0.40);
- compute_agreement edge cases (empty -> ValueError; perfect-chance degenerate);
- position-consistency (basic + empty -> 1.0);
- calibrate(ci) PASS on a healthy seed;
- mislabeled-gold FAIL (agreement check);
- stale-snapshot FAIL (freshness check, injected `now`);
- bad>=good discrimination FAIL (discrimination teeth);
- calibrate(mode="full") raises NotImplementedError;
- verify_discrimination makes NO LLM call (pure function of recorded scores).

Plus the `--skill` resolution surface added for issue #177:
- skill_candidates / resolve_skill_dir ordering, fallback and fail-closed;
- the CLI / `main()` surface (selector validation, mutual exclusion, the
  --skill-dir escape hatch, and the --unit-test/--self-test short-circuits);
- OUT-OF-PROCESS runs in a child interpreter: a foreign cwd, the legacy
  `<root>/_shared` deployment shape, and `main()`'s stdout restore;
- repository-corpus integration: `--skill review-deep` against the committed
  `skills/review-deep/evals/golden/` corpus, and that corpus's freshness.

Pure stdlib + pytest. The unit matrix is built inline under tmp_path; the
resolution / CLI integration tests additionally read the committed
`skills/review-deep/evals/golden/` corpus from the checkout, and some of them
spawn a subprocess. Mirrors the sibling-import convention from
test_score_skill_absolute.py.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

# Sibling import - same dir as the module under test.
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from calibrate_judge import (  # noqa: E402  (sys.path tweak above)
    FRESHNESS_MAX_AGE_DAYS,
    _parse_iso_date,
    _write_synthetic_skill,
    calibrate,
    check_freshness,
    compute_agreement,
    compute_position_consistency,
    load_gold,
    main,
    resolve_skill_dir,
    skill_candidates,
    verify_discrimination,
)

# This file lives in <repo>/_shared, so the repo root is its parent's parent --
# the same root calibrate_judge resolves --skill against.
REPO_ROOT = THIS_DIR.parent

MODULE_PATH = THIS_DIR / "calibrate_judge.py"


# ---------------------------------------------------------------------------
# Cohen's kappa
# ---------------------------------------------------------------------------


def _kappa_lists() -> tuple[list[str], list[str]]:
    """50-pair lists matching the hand-computed fixture.

    both-YES=20, both-NO=15, judged-YES/gold-NO=5, judged-NO/gold-YES=10.
    -> p_o = 0.70, p_e = 0.50, kappa = 0.40.
    """
    judged = ["YES"] * 20 + ["NO"] * 15 + ["YES"] * 5 + ["NO"] * 10
    gold = ["YES"] * 20 + ["NO"] * 15 + ["NO"] * 5 + ["YES"] * 10
    return judged, gold


def test_kappa_hand_computed_fixture_is_0_40() -> None:
    judged, gold = _kappa_lists()
    out = compute_agreement(judged, gold)
    assert abs(out["agreement_pct"] - 0.70) < 1e-9
    assert abs(out["cohen_kappa"] - 0.40) < 1e-9


def test_compute_agreement_empty_raises() -> None:
    with pytest.raises(ValueError):
        compute_agreement([], [])


def test_compute_agreement_unequal_length_raises() -> None:
    with pytest.raises(ValueError):
        compute_agreement(["PASS"], ["PASS", "PASS"])


def test_compute_agreement_perfect_chance_degenerate() -> None:
    # Single category on both sides: p_e == 1.0, (1 - p_e) == 0. Convention:
    # kappa == 1.0 when observed agreement is also perfect.
    out = compute_agreement(["PASS", "PASS"], ["PASS", "PASS"])
    assert out["agreement_pct"] == 1.0
    assert out["cohen_kappa"] == 1.0


def test_compute_agreement_perfect_real_agreement() -> None:
    # Two categories, all-equal -> p_o == 1.0, kappa == 1.0 (non-degenerate).
    out = compute_agreement(["PASS", "NEEDS-WORK"], ["PASS", "NEEDS-WORK"])
    assert out["agreement_pct"] == 1.0
    assert abs(out["cohen_kappa"] - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# position consistency
# ---------------------------------------------------------------------------


def test_position_consistency_basic() -> None:
    assert compute_position_consistency([("PASS", "PASS"), ("PASS", "PASS")]) == 1.0
    assert compute_position_consistency([("PASS", "PASS"), ("PASS", "FAIL")]) == 0.5
    assert compute_position_consistency([("PASS", "FAIL")]) == 0.0


def test_position_consistency_empty_is_one() -> None:
    assert compute_position_consistency([]) == 1.0


# ---------------------------------------------------------------------------
# freshness
# ---------------------------------------------------------------------------


def test_check_freshness_fresh_and_stale() -> None:
    now = date(2026, 6, 22)
    # 10 days old -> fresh.
    assert check_freshness("2026-06-12T00:00:00Z", now=now) is True
    # Exactly at the boundary -> fresh (age <= max).
    boundary = date(2026, 6, 22).toordinal() - FRESHNESS_MAX_AGE_DAYS
    assert check_freshness(date.fromordinal(boundary).isoformat(), now=now) is True
    # Well past the boundary -> stale.
    assert check_freshness("2023-01-01", now=now) is False


# ---------------------------------------------------------------------------
# load_gold
# ---------------------------------------------------------------------------


def test_load_gold_round_trip(tmp_path: Path) -> None:
    _write_synthetic_skill(tmp_path)
    gold = load_gold(tmp_path)
    fixtures = {g["fixture"] for g in gold}
    assert fixtures == {"good.md", "bad_1.md", "bad_2.md"}
    good = next(g for g in gold if g["fixture"] == "good.md")
    assert good["verdict"] == "PASS"


def test_load_gold_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gold(tmp_path)  # no evals/golden/verdicts.jsonl


# ---------------------------------------------------------------------------
# calibrate(ci) -- the gate matrix
# ---------------------------------------------------------------------------


def test_calibrate_ci_pass_on_healthy_seed(tmp_path: Path) -> None:
    _write_synthetic_skill(tmp_path)
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is True
    assert res["reasons"] == []
    assert res["checks"]["freshness"]["passed"] is True
    assert res["checks"]["discrimination"]["passed"] is True
    assert res["checks"]["agreement"]["passed"] is True
    # A correct seed yields perfect agreement -> kappa 1.0 by construction.
    assert res["checks"]["agreement"]["cohen_kappa"] == 1.0


def test_calibrate_ci_mislabeled_gold_fails(tmp_path: Path) -> None:
    _write_synthetic_skill(tmp_path)
    gold_path = tmp_path / "evals" / "golden" / "verdicts.jsonl"
    lines = gold_path.read_text(encoding="utf-8").splitlines()
    flipped = []
    for line in lines:
        obj = json.loads(line)
        if obj["fixture"] == "good.md":
            obj["verdict"] = "NEEDS-WORK"  # flip away from recorded PASS
        flipped.append(json.dumps(obj))
    gold_path.write_text("\n".join(flipped) + "\n", encoding="utf-8")

    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    assert res["checks"]["agreement"]["passed"] is False
    assert res["checks"]["agreement"]["agreement_pct"] < 1.0


def test_calibrate_ci_stale_fails(tmp_path: Path) -> None:
    _write_synthetic_skill(tmp_path, generated_at="2023-01-01T00:00:00Z")
    res = calibrate(tmp_path, mode="ci", now=date(2026, 6, 22))
    assert res["passed"] is False
    assert res["checks"]["freshness"]["passed"] is False


def test_calibrate_ci_bad_ge_good_discrimination_fails(tmp_path: Path) -> None:
    _write_synthetic_skill(
        tmp_path,
        good_score=0.5,
        bad_scores={"bad_1.md": 0.6, "bad_2.md": 0.2},
    )
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    disc = res["checks"]["discrimination"]
    assert disc["passed"] is False
    assert "bad_1.md" in disc["sycophantic_bads"]


def test_calibrate_ci_missing_artifacts_fail_closed(tmp_path: Path) -> None:
    # No evals/golden at all -> fail closed, no uncaught crash.
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    assert res["reasons"]  # at least one reason recorded


def test_calibrate_full_raises_not_implemented(tmp_path: Path) -> None:
    _write_synthetic_skill(tmp_path)
    with pytest.raises(NotImplementedError):
        calibrate(tmp_path, mode="full")


def test_calibrate_unknown_mode_raises(tmp_path: Path) -> None:
    _write_synthetic_skill(tmp_path)
    with pytest.raises(ValueError):
        calibrate(tmp_path, mode="bogus")


# ---------------------------------------------------------------------------
# calibrate(ci) -- fail-closed paths (the contract's central promise: a
# malformed / missing / surprising artifact never crashes; it returns
# passed:False with a recorded reason).
# ---------------------------------------------------------------------------


def test_calibrate_ci_malformed_verdicts_jsonl_fail_closed(tmp_path: Path) -> None:
    # An invalid JSON line in verdicts.jsonl -> json.JSONDecodeError during
    # load_gold -> caught by the artifact-load guard -> passed False, no crash.
    _write_synthetic_skill(tmp_path)
    gold_path = tmp_path / "evals" / "golden" / "verdicts.jsonl"
    gold_path.write_text(
        '{"fixture": "good.md", "verdict": "PASS"}\n{not valid json\n',
        encoding="utf-8",
    )
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    assert any("artifact load failed" in r for r in res["reasons"])


def test_calibrate_ci_malformed_recorded_scores_fail_closed(tmp_path: Path) -> None:
    # Invalid JSON in recorded_scores.json -> json.JSONDecodeError during load
    # -> caught -> passed False, no crash.
    _write_synthetic_skill(tmp_path)
    rec_path = tmp_path / "evals" / "golden" / "recorded_scores.json"
    rec_path.write_text("{ this is not json", encoding="utf-8")
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    assert any("artifact load failed" in r for r in res["reasons"])


def test_calibrate_ci_missing_generated_at_fail_closed(tmp_path: Path) -> None:
    # recorded_scores.json without 'generated_at' -> KeyError inside the
    # freshness check -> caught there -> passed False, no uncaught crash.
    _write_synthetic_skill(tmp_path)
    rec_path = tmp_path / "evals" / "golden" / "recorded_scores.json"
    recorded = json.loads(rec_path.read_text(encoding="utf-8"))
    del recorded["generated_at"]
    rec_path.write_text(json.dumps(recorded), encoding="utf-8")
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    assert res["checks"]["freshness"]["passed"] is False
    assert "error" in res["checks"]["freshness"]


def test_calibrate_ci_scores_not_dict_fail_closed(tmp_path: Path) -> None:
    # FIX #1 REGRESSION GUARD (the most important new test): 'scores' is a list
    # (could equally be null). Without the structural validation, the
    # discrimination lambda would raise TypeError INSIDE verify_goldens and
    # escape uncaught. With the guard, calibrate fails closed at artifact load.
    _write_synthetic_skill(tmp_path)
    rec_path = tmp_path / "evals" / "golden" / "recorded_scores.json"
    recorded = json.loads(rec_path.read_text(encoding="utf-8"))
    recorded["scores"] = ["good.md", "bad_1.md"]  # a list, not a dict
    rec_path.write_text(json.dumps(recorded), encoding="utf-8")
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    assert any(
        "malformed recorded_scores" in r for r in res["reasons"]
    ), res["reasons"]

    # Also exercise the null variant -> same fail-closed path, no crash.
    recorded["scores"] = None
    rec_path.write_text(json.dumps(recorded), encoding="utf-8")
    res_null = calibrate(tmp_path, mode="ci")
    assert res_null["passed"] is False
    assert any(
        "malformed recorded_scores" in r for r in res_null["reasons"]
    ), res_null["reasons"]


def test_calibrate_ci_missing_fixture_in_scores_fail_closed(tmp_path: Path) -> None:
    # good.md exists on disk but is absent from the 'scores' map. The
    # discrimination lambda raises KeyError inside verify_goldens -> caught by
    # the broadened discrimination except -> passed False, no uncaught crash.
    _write_synthetic_skill(tmp_path)
    rec_path = tmp_path / "evals" / "golden" / "recorded_scores.json"
    recorded = json.loads(rec_path.read_text(encoding="utf-8"))
    del recorded["scores"]["good.md"]  # on disk but missing from scores map
    rec_path.write_text(json.dumps(recorded), encoding="utf-8")
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    assert res["checks"]["discrimination"]["passed"] is False
    assert "error" in res["checks"]["discrimination"]


def test_calibrate_ci_empty_verdicts_fail_closed(tmp_path: Path) -> None:
    # verdicts.jsonl with only blank lines -> load_gold returns [] -> the
    # agreement check calls compute_agreement([], []) which raises ValueError
    # -> caught by the agreement except -> passed False, no crash.
    _write_synthetic_skill(tmp_path)
    gold_path = tmp_path / "evals" / "golden" / "verdicts.jsonl"
    gold_path.write_text("\n   \n\n", encoding="utf-8")
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    assert res["checks"]["agreement"]["passed"] is False
    assert "error" in res["checks"]["agreement"]


def test_check_freshness_future_dated_fails() -> None:
    # FIX #2 GUARD: a future generated_at yields negative age_days; treat it as
    # NOT fresh. Both the unit (check_freshness) and the integrated path
    # (calibrate(ci) with a future-dated seed -> freshness fails).
    now = date(2026, 6, 22)
    future = date(2026, 7, 22).isoformat()  # ~30 days in the future
    assert check_freshness(future, now=now) is False


def test_calibrate_ci_future_dated_seed_fails_freshness(tmp_path: Path) -> None:
    _write_synthetic_skill(tmp_path, generated_at="2026-07-22T00:00:00Z")
    res = calibrate(tmp_path, mode="ci", now=date(2026, 6, 22))
    assert res["passed"] is False
    assert res["checks"]["freshness"]["passed"] is False


def test_calibrate_ci_bad_equals_good_tie_fails(tmp_path: Path) -> None:
    # Exact tie bad_score == good_score: verify_goldens uses strict `<`, so a
    # tie is NOT discriminated -> discrimination fails (the strict-< teeth).
    _write_synthetic_skill(
        tmp_path,
        good_score=0.5,
        bad_scores={"bad_1.md": 0.5, "bad_2.md": 0.2},  # bad_1 ties good
    )
    res = calibrate(tmp_path, mode="ci")
    assert res["passed"] is False
    disc = res["checks"]["discrimination"]
    assert disc["passed"] is False
    assert "bad_1.md" in disc["sycophantic_bads"]


# ---------------------------------------------------------------------------
# verify_discrimination is pure (no LLM / network / subprocess)
# ---------------------------------------------------------------------------


def test_verify_discrimination_pure_no_llm(tmp_path: Path, monkeypatch) -> None:
    """verify_discrimination's verdict is a pure function of recorded scores.

    Construction proof: the discrimination outcome is fully determined by the
    injected recorded scores and the fixture files on disk. We assert this two
    ways:

    1. Hard-fail any attempt to open a network socket or spawn a subprocess
       during the call (if the path secretly invoked an LLM, it would need
       one of these and the test would error).
    2. Mutating ONLY the recorded-scores dict (no file/LLM change) flips the
       verdict deterministically -- proving the function reads nothing but its
       inputs.
    """
    import socket
    import subprocess

    def _no_network(*_a, **_k):
        raise AssertionError("verify_discrimination opened a socket -- not pure")

    def _no_subprocess(*_a, **_k):
        raise AssertionError("verify_discrimination spawned a subprocess -- not pure")

    # The RIGOROUS proof of purity is part 2 below: mutating ONLY the injected
    # `scores` dict (no file/LLM/disk change) deterministically flips the
    # verdict, which is only possible if the function reads nothing but its
    # inputs. These socket/subprocess monkeypatches are cheap belt-and-
    # suspenders: they add no value against the current pure implementation but
    # would catch a FUTURE verify_goldens that regressed into a network or
    # subprocess (e.g. live-LLM) call.
    monkeypatch.setattr(socket.socket, "connect", _no_network)
    monkeypatch.setattr(subprocess, "Popen", _no_subprocess)

    _write_synthetic_skill(tmp_path)

    # Discriminating recorded scores -> status "ok".
    good_scores = {
        "scores": {"good.md": 0.9, "bad_1.md": 0.3, "bad_2.md": 0.2},
    }
    status_ok = verify_discrimination(tmp_path, good_scores)
    assert status_ok.status == "ok"
    assert status_ok.sycophantic_bads == []

    # Same files on disk; ONLY the injected scores change -> verdict flips.
    syco_scores = {
        "scores": {"good.md": 0.5, "bad_1.md": 0.6, "bad_2.md": 0.2},
    }
    status_bad = verify_discrimination(tmp_path, syco_scores)
    assert status_bad.status == "harness-error"
    assert "bad_1.md" in status_bad.sycophantic_bads


# ---------------------------------------------------------------------------
# --skill resolution (root-aware candidate search) + --skill-dir escape hatch
#
# Regression cover for the defect where `--skill <name>` resolved ONLY to
# `<root>/<name>`. In this repository that is the LEGACY top-level package,
# which has scripts/ but no evals/ -- so the canonical `skills/review-deep`
# package could never calibrate in-repo. Resolution is now an ORDERED search:
# `<root>/skills/<name>` first, `<root>/<name>` second (which is what keeps the
# historical `.claude/skills/_shared` layout working unchanged).
# ---------------------------------------------------------------------------


def _fresh_today() -> str:
    """A `generated_at` that is fresh whenever the suite runs.

    The synthetic-seed default is a fixed 2026-06-01 stamp, which would age past
    FRESHNESS_MAX_AGE_DAYS and turn these tests red for a reason that has
    nothing to do with resolution. Anchoring to today keeps them stable.

    Used by the tests that drive `main()` (in-process or as a subprocess), where
    the module's `now=` injection point is not reachable: `_run_cli` calls
    `calibrate(skill_dir, mode=args.mode)` and no CLI flag reaches `now=`.
    """
    return date.today().isoformat()


def test_skill_candidates_order_is_canonical_then_legacy(tmp_path: Path) -> None:
    assert skill_candidates("demo", root=tmp_path) == [
        tmp_path / "skills" / "demo",
        tmp_path / "demo",
    ]


def test_skill_candidates_rejects_a_path_shaped_name(tmp_path: Path) -> None:
    """--skill takes a NAME; a path escapes <root> via pathlib join semantics.

    An absolute right operand DISCARDS the base, and `..` walks out of it, so
    without this guard `--skill` silently does `--skill-dir`'s job and the
    fail-closed error names the same path twice.
    """
    for bad in ("", "   ", "..", "sub/dir", "sub\\dir", "C:/Windows", "/etc"):
        with pytest.raises(ValueError) as excinfo:
            skill_candidates(bad, root=tmp_path)
        assert "--skill-dir" in str(excinfo.value), (bad, str(excinfo.value))

    # The guard is narrow: ordinary names with dots and dashes still resolve.
    assert skill_candidates("review-deep.v2", root=tmp_path)[0] == (
        tmp_path / "skills" / "review-deep.v2")


def test_resolve_skill_dir_prefers_canonical_when_both_exist(tmp_path: Path) -> None:
    # (a) CANONICAL-FIRST: both trees present -> the skills/ one wins.
    (tmp_path / "skills" / "demo").mkdir(parents=True)
    (tmp_path / "demo").mkdir()
    assert resolve_skill_dir("demo", root=tmp_path) == tmp_path / "skills" / "demo"


def test_resolve_skill_dir_falls_back_to_legacy_layout(tmp_path: Path) -> None:
    # (b) BACKWARD COMPAT: the historical `.claude/skills/_shared` shape, where
    # <root> IS the skills root and no <root>/skills/ directory exists at all.
    (tmp_path / "demo").mkdir()
    assert not (tmp_path / "skills").exists()
    assert resolve_skill_dir("demo", root=tmp_path) == tmp_path / "demo"


def test_resolve_skill_dir_ignores_a_non_directory_candidate(tmp_path: Path) -> None:
    # A FILE at the canonical path is not a skill dir; the search continues.
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills" / "demo").write_text("not a directory\n", encoding="utf-8")
    (tmp_path / "demo").mkdir()
    assert resolve_skill_dir("demo", root=tmp_path) == tmp_path / "demo"


def test_resolve_skill_dir_missing_raises_naming_both_candidates(
    tmp_path: Path,
) -> None:
    # (c) NEITHER present -> named error citing BOTH candidate paths.
    with pytest.raises(FileNotFoundError) as excinfo:
        resolve_skill_dir("demo", root=tmp_path)
    msg = str(excinfo.value)
    assert str(tmp_path / "skills" / "demo") in msg, msg
    assert str(tmp_path / "demo") in msg, msg


# ---------------------------------------------------------------------------
# CLI surface (production entry point `main`)
# ---------------------------------------------------------------------------


def _cli_check_states(stdout: str) -> dict[str, str]:
    """Parse main()'s ``  - <name>: <state>`` lines into ``{name: state}``.

    NOTE this makes the literal ``  - <name>: <state>`` line shape a PINNED
    CONTRACT of the CLI (emitted at calibrate_judge.py's report loop): a
    cosmetic reformat reds the tests that use this helper. Accepted
    deliberately -- `main()` returns an int, and `calibrate()`'s report dict
    never leaves `_run_cli`, so stdout is where the per-check states are.
    """
    states: dict[str, str] = {}
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and ": " in stripped:
            name, _, state = stripped[2:].partition(": ")
            states[name.strip()] = state.strip()
    return states


def test_cli_rejects_neither_skill_nor_skill_dir(capsys) -> None:
    # (d) NEITHER SUPPLIED (and no --unit-test/--self-test).
    rc = main([])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--skill" in err and "--skill-dir" in err, err


def test_cli_unresolvable_skill_name_exits_2_naming_both_candidates(capsys) -> None:
    # (c) via the CLI: non-zero exit, both candidate paths named.
    name = "definitely-not-a-real-skill-xyz"
    rc = main(["--skill", name])
    assert rc == 2
    err = capsys.readouterr().err
    assert str(REPO_ROOT / "skills" / name) in err, err
    assert str(REPO_ROOT / name) in err, err


def test_cli_skill_dir_wins_outright(tmp_path: Path, capsys) -> None:
    """(d) --skill-dir is honored, and beats any candidate search.

    The seed lives OUTSIDE the resolution root under a name no candidate search
    could ever reach, so a passing run proves the explicit directory was used.
    """
    seed = tmp_path / "seed-outside-the-root"
    _write_synthetic_skill(seed, generated_at=_fresh_today())
    rc = main(["--skill-dir", str(seed), "--mode", "ci"])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "seed-outside-the-root" in out, out
    assert _cli_check_states(out) == {
        "freshness": "ok",
        "discrimination": "ok",
        "agreement": "ok",
    }, out


def test_cli_rejects_malformed_selector_invocations(tmp_path: Path, capsys) -> None:
    """Three selector shapes that must fail LOUDLY (rc 2), not be absorbed.

    - a path-shaped `--skill` would escape <root> (pathlib join semantics);
    - an empty `--skill-dir` would silently become the CWD (`Path("") ==
      Path(".")`), reporting an empty skill name and a cwd-relative path;
    - a contradictory selector pair alongside `--self-test` must still be
      caught: the mode routing short-circuits, so the exclusivity check has to
      run BEFORE it or the conflict is accepted in silence.
    """
    cases = [
        (["--skill", ".."], "--skill-dir"),
        (["--skill-dir", ""], "non-empty"),
        (["--self-test", str(tmp_path), "--skill", "a", "--skill-dir", "b"],
         "mutually exclusive"),
    ]
    failures = []
    for argv, expected in cases:
        rc = main(argv)
        captured = capsys.readouterr()
        if rc != 2 or expected not in captured.err:
            failures.append(f"{argv} -> rc={rc}, stderr={captured.err!r} "
                            f"(expected rc 2 and {expected!r})")
    assert not failures, "\n".join(failures)


def test_cli_unit_test_flag_still_short_circuits(capsys) -> None:
    # Backward compat: --unit-test needs neither --skill nor --skill-dir.
    rc = main(["--unit-test"])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "UNIT TESTS PASSED" in out


def test_cli_self_test_flag_still_short_circuits(tmp_path: Path, capsys) -> None:
    # Backward compat: --self-test needs neither --skill nor --skill-dir.
    rc = main(["--self-test", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "SELF-TEST PASSED" in out


# ---------------------------------------------------------------------------
# (e) INTEGRATION through the production entry point, OUT OF PROCESS
#
# These run the real script in a child interpreter from a cwd that is NOT the
# repository root. That is not ceremony: pytest runs from the repo root, where
# `Path.cwd()` and the module's own `_THIS_DIR.parent` are the SAME directory
# (measured), so an in-process assertion cannot tell a cwd-derived resolution
# root from a location-derived one. Only a different cwd tells them apart, and
# the documented invocation (`python _shared/calibrate_judge.py --skill
# review-deep --mode ci`, skills/review-deep/core.md) is relative, i.e. it is
# run by an operator standing somewhere.
# ---------------------------------------------------------------------------


def _run_cli_out_of_process(
    args: list[str],
    cwd: Path,
    script: Path = MODULE_PATH,
    extra_pythonpath: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `script` in a child interpreter from `cwd`; return CompletedProcess.

    `extra_pythonpath` lets a RELOCATED copy of the module borrow its sibling
    imports (score_skill_composite and below) from the real `_shared/` tree.
    """
    env = dict(os.environ)
    if extra_pythonpath is not None:
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{extra_pythonpath}{os.pathsep}{existing}" if existing
            else str(extra_pythonpath))
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=300,
    )


def test_cli_skill_review_deep_resolves_canonical_from_a_foreign_cwd(
    tmp_path: Path,
) -> None:
    """Production-caller integration: `--skill review-deep` in THIS repository.

    Two things at once, both unreachable from a unit test of
    :func:`resolve_skill_dir`:

    1. WIRING -- a resolver that works but is never called by ``main`` (the
       `code-quality.md` silent-wiring failure) reverts to `<root>/<name>`, the
       legacy package, which carries no `evals/`; the run then aborts at
       artifact load.
    2. CWD-INDEPENDENCE -- the run happens from `tmp_path`, so a root derived
       from `Path.cwd()` instead of the module's own location finds neither
       candidate and exits 2.

    The outcome is asserted SUBSTANTIVELY (the corpus was found, both replay
    checks are ok, the process exited 0), never by comparing the CLI against
    its own output. Freshness has its own dedicated test below, which is where
    the actionable "re-snapshot the corpus" message lives.
    """
    canonical = REPO_ROOT / "skills" / "review-deep"
    legacy = REPO_ROOT / "review-deep"

    # Precondition: this repo has the discriminating shape -- BOTH trees exist
    # and ONLY the canonical one carries the calibration corpus. If that stops
    # holding, the assertions below stop proving canonical-first, so assert it.
    assert canonical.is_dir(), canonical
    assert legacy.is_dir(), (
        f"{legacy} is missing. This test depends on the LEGACY top-level "
        f"review-deep package for its discriminating shape -- if that package "
        f"was retired, delete this precondition here and the gate in "
        f"tests/package-integrity/test_review_deep_scripts_duplication.py in "
        f"the same change, rather than recreating the directory")
    assert (canonical / "evals" / "golden" / "recorded_scores.json").is_file()
    assert not (legacy / "evals").exists(), "legacy tree gained an evals/ tree"

    assert tmp_path.resolve() != REPO_ROOT, "the foreign cwd must not be the root"
    proc = _run_cli_out_of_process(
        ["--skill", "review-deep", "--mode", "ci"], cwd=tmp_path)
    out = proc.stdout + proc.stderr

    # ASSET RESOLUTION PROOF: the corpus was found and loaded. Resolving to the
    # legacy tree instead would abort at artifact load ("recorded scores not
    # found") and emit no per-check lines at all.
    assert "artifact load failed" not in out, out
    states = _cli_check_states(proc.stdout)
    assert set(states) == {"freshness", "discrimination", "agreement"}, out
    assert states["discrimination"] == "ok", out
    assert states["agreement"] == "ok", out
    assert proc.returncode == 0, (
        f"`--skill review-deep --mode ci` exited {proc.returncode}, expected 0. "
        f"If freshness is the only FAIL, the committed corpus aged out -- see "
        f"test_review_deep_corpus_is_within_the_freshness_window for the "
        f"remedy.\n{out}")


def test_cli_legacy_root_resolves_through_main_in_a_relocated_deployment(
    tmp_path: Path,
) -> None:
    """Backward compat for the historical `<root>/_shared` layout, THROUGH main.

    The legacy arm is otherwise only ever reached by injecting `root=` into the
    helper: every top-level legacy package in this repository also exists under
    `skills/`, so the canonical candidate always wins and no in-repo run
    exercises `<root>/<name>` end-to-end. This
    reconstructs the real deployment instead -- a COPY of the module in
    `<root>/_shared/`, a skill directly under `<root>`, and no `<root>/skills/`
    at all -- and drives it through the production entry point with the DEFAULT
    root derivation (no `root=` injection, foreign cwd).

    Only the module under test is copied; its sibling imports are borrowed from
    the real `_shared/` via PYTHONPATH, since the dependency chain reaches
    outside `_shared/` and copying it wholesale would test the copy, not the
    resolution.
    """
    root = tmp_path / "skills_root"
    shared = root / "_shared"
    shared.mkdir(parents=True)
    relocated = shared / MODULE_PATH.name
    shutil.copy2(MODULE_PATH, relocated)

    _write_synthetic_skill(root / "demo", generated_at=_fresh_today())
    assert not (root / "skills").exists(), "the legacy layout has no skills/ dir"

    proc = _run_cli_out_of_process(
        ["--skill", "demo", "--mode", "ci"],
        cwd=tmp_path,
        script=relocated,
        extra_pythonpath=THIS_DIR,
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
    assert _cli_check_states(proc.stdout) == {
        "freshness": "ok",
        "discrimination": "ok",
        "agreement": "ok",
    }, out


def test_main_restores_the_stdout_configuration_it_mutates(tmp_path: Path) -> None:
    """main()'s win32 stdout reconfiguration must not leak to later callers.

    `sys.stdout.reconfigure` mutates a PROCESS-GLOBAL object, and `_shared/`
    runs in the same pytest session as `tests/` during the repo-root gate, so an
    unrestored tweak hands every later suite UTF-8-with-replacement stdout: a
    genuine UnicodeEncodeError becomes a silent '?'.

    Out of process because a child interpreter has a REAL stdout -- the
    configuration a production operator has, rather than pytest's capture
    object. Against a `main()` with the `finally` removed the child prints
    `2 False ('utf-8', 'surrogateescape') ('utf-8', 'replace')`; against the
    real one, `2 True`.
    """
    probe = (
        "import sys;"
        f"sys.path.insert(0, {str(THIS_DIR)!r});"
        "from calibrate_judge import main;"
        "before=(sys.stdout.encoding, sys.stdout.errors);"
        "rc=main([]);"
        "after=(sys.stdout.encoding, sys.stdout.errors);"
        "print(rc, before == after, before, after)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    out = proc.stdout + proc.stderr
    assert proc.stdout.startswith("2 True"), (
        f"main() leaked its stdout reconfiguration (expected '2 True ...'): {out}")


def test_review_deep_corpus_is_within_the_freshness_window() -> None:
    """The committed corpus must not age out of the gate in silence.

    `--skill review-deep --mode ci` is this step's acceptance criterion and the
    invocation review-deep's core.md documents. Its freshness check is the
    ANTI-COAST guard: past FRESHNESS_MAX_AGE_DAYS the shipped command starts
    exiting 1. Without this test that day arrives with the suite still green,
    and the criterion stops holding without anything saying so.
    """
    golden = REPO_ROOT / "skills" / "review-deep" / "evals" / "golden"
    recorded = json.loads(
        (golden / "recorded_scores.json").read_text(encoding="utf-8-sig"))
    generated_at = recorded["generated_at"]
    expires = _parse_iso_date(generated_at) + timedelta(days=FRESHNESS_MAX_AGE_DAYS)

    assert check_freshness(generated_at), (
        f"the committed review-deep golden corpus went STALE on "
        f"{expires.isoformat()} (generated_at={generated_at}, "
        f"FRESHNESS_MAX_AGE_DAYS={FRESHNESS_MAX_AGE_DAYS}).\n"
        f"ACTION: re-run review-deep's judge calibration and re-import the "
        f"regenerated skills/review-deep/evals/golden/recorded_scores.json "
        f"(with verdicts.jsonl) from that run.\n"
        f"Do NOT widen the window, inject a `now`, or soften this assertion: "
        f"freshness is the anti-coast guard, and softening it re-arms exactly "
        f"the silent decay this test exists to make loud.")


def test_review_deep_golden_corpus_loads_from_the_canonical_package() -> None:
    """The committed corpus is complete enough for the gate to be meaningful.

    Guards a truncated import: gold labels, recorded scores, and recorded
    verdicts must all cover the same fixture set that is on disk.
    """
    skill_dir = resolve_skill_dir("review-deep")
    gold = load_gold(skill_dir)
    golden_dir = skill_dir / "evals" / "golden"
    on_disk = {p.name for p in golden_dir.glob("*.md")}

    assert "good.md" in on_disk
    bads = {n for n in on_disk if n.startswith("bad_")}
    assert len(bads) >= 2, on_disk

    gold_fixtures = {g["fixture"] for g in gold}
    assert gold_fixtures == on_disk, gold_fixtures ^ on_disk

    recorded = json.loads(
        (golden_dir / "recorded_scores.json").read_text(encoding="utf-8-sig")
    )
    assert on_disk <= set(recorded["scores"]), on_disk - set(recorded["scores"])
    assert on_disk <= set(recorded["recorded_verdicts"]), (
        on_disk - set(recorded["recorded_verdicts"])
    )
