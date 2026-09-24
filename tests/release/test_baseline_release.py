"""Gate for tools/baseline_release.py (Phase BR, Step 147).

HERMETIC AND FAST BY CONSTRUCTION. Every release in this file is cut from a TINY
SYNTHETIC git repository created inside `tmp_path_factory`, carrying its own
two-line `tests/test_ok.py` and -- for the toolkit shape -- its own stand-in
`tools/release.ps1`. Nothing here touches this repository's own git state, its
real `tools/release.ps1`, the real lab checkout, a consumer home, or the
network, and nothing here runs the multi-hour repo-root suite.

Why a stand-in `release.ps1` is the RIGHT fixture rather than a shortcut: the
tool under test invokes `tools/release.ps1` FROM THE DISPOSABLE CHECKOUT OF THE
PINNED COMMIT, never from this repository. So a synthetic source repo that ships
its own `tools/release.ps1` exercises the real producer->consumer relationship
(the tool launches the pinned source's release entry with real flags, and
consumes the `dist/` + `CHECKSUMS.txt` pair it produces) at a cost of about one
second. Wiring the REAL release entry in here would test `release.ps1` -- which
`tests/release/test_release_script.py` already does, end to end -- not the
orchestration this file exists to grade.

Sibling-suite conventions are followed deliberately: shell out via subprocess,
skip cleanly when `powershell`/`git` are absent, and drive the CLI as an
operator would (argument arrays, never a shell string).
"""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
GIT = shutil.which("git")
REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "baseline_release.py"

pytestmark = [
    pytest.mark.skipif(GIT is None, reason="git is not available on PATH"),
]

# Loaded by path rather than `from tools import ...`: this file must grade the
# module regardless of which directory pytest was invoked from.
_spec = importlib.util.spec_from_file_location("baseline_release_under_test", TOOL)
br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(br)


# --------------------------------------------------------------------------- #
# Fixture scaffolding
# --------------------------------------------------------------------------- #

TRIVIAL_TEST = "def test_ok():\n    assert True\n"
FAILING_TEST = "def test_planted_failure():\n    assert False, 'planted'\n"

# A stand-in for the pinned source's own release entry. It mirrors the REAL
# interface (`-StageDir`, `-SourceRoot`, `-Provider`, `-PythonExe`) and the real
# OUTPUT CONTRACT (`<stage>/dist/<profile>/` plus a normalized `CHECKSUMS.txt`
# over dist/), which is the whole surface the tool under test consumes.
# `.Replace([char]92, [char]47)` rather than `-replace` keeps this fixture free
# of regex backslash escaping.
FAKE_RELEASE_PS1 = """[CmdletBinding()]
param(
    [string]$StageDir = '',
    [string]$SourceRoot = '',
    [ValidateSet('claude','gpt','codex','both','all')]
    [string]$Provider = 'both',
    [string]$PythonExe = 'python'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $StageDir -Force | Out-Null
$dist = Join-Path $StageDir 'dist'
$enc = New-Object System.Text.UTF8Encoding($false)
foreach ($p in @('claude','gpt','codex')) {
    $d = Join-Path $dist $p
    New-Item -ItemType Directory -Path $d -Force | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $d 'SKILL.md'), "# fake $p profile", $enc)
}
$lines = New-Object System.Collections.Generic.List[string]
foreach ($f in (Get-ChildItem -LiteralPath $dist -Recurse -File | Sort-Object -Property FullName)) {
    $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $rel = $f.FullName.Substring($StageDir.Length).TrimStart([char]92, [char]47)
    $rel = $rel.Replace([char]92, [char]47)
    $lines.Add("$h  $rel")
}
$body = (([string[]]$lines) -join "`n") + "`n"
[System.IO.File]::WriteAllText((Join-Path $StageDir 'CHECKSUMS.txt'), $body, $enc)
exit 0
"""

FAILING_RELEASE_PS1 = """[CmdletBinding()]
param(
    [string]$StageDir = '',
    [string]$SourceRoot = '',
    [ValidateSet('claude','gpt','codex','both','all')]
    [string]$Provider = 'both',
    [string]$PythonExe = 'python'
)
Write-Error 'planted release failure'
exit 1
"""


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True, check=True)


def _make_repo(root: Path, files):
    root.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    _git(["init", "-q", "-b", "main"], root)
    _git(["config", "user.email", "t@example.com"], root)
    _git(["config", "user.name", "test"], root)
    _git(["config", "core.autocrlf", "false"], root)
    _git(["config", "commit.gpgsign", "false"], root)
    _git(["add", "-A"], root)
    _git(["commit", "-q", "--no-verify", "-m", "init"], root)
    return root, _git(["rev-parse", "HEAD"], root).stdout.strip()


def _cli(*args, timeout=900):
    return subprocess.run(
        [sys.executable, str(TOOL), *[str(a) for a in args]],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )


def _release(product, source_root, commit, version, store, proofs=None, attest=None):
    args = [product, "--source-root", source_root, "--source-commit", commit,
            "--version", version, "--store", store, "--python-exe", sys.executable]
    if proofs is not None:
        args += ["--proofs", proofs]
    if attest is not None:
        args += ["--attest-reviews", attest]
    return _cli(*args)


def _record(release_dir: Path):
    return json.loads((release_dir / "release.json").read_text(encoding="utf-8"))


def _attempt_dirs(store: Path):
    attempts = store / ".attempts"
    return sorted(p for p in attempts.iterdir() if p.is_dir()) if attempts.is_dir() else []


def _review_proof(commit, **overrides):
    row = {
        "source_commit": commit,
        "requested_model": "gpt-5.1-codex",
        "resolved_model": "gpt-5.1-codex",
        "resolution_status": "observed",
        "identity_waiver": None,
        "conversation_id": "review-0001",
        "independent": True,
        "verdict": "PASS",
        "evidence": "review-0001.md",
        "cross_family": True,
    }
    row.update(overrides)
    return row


#: The name an operator passes to --attest-reviews. The attestation is a
#: SEPARATE CLI act, never a --proofs field, so no fixture can carry it forward.
ATTESTING_PARTY = "A. Operator (release owner)"

# The shape of a real review evidence document. Every claim the row makes is
# stated here, so the NEGATIVE-ONLY evidence-consistency tripwire stays silent.
# Silence is not corroboration: it upgrades nothing on its own, and a review
# still qualifies only through the separate --attest-reviews act. A generic
# one-liner is deliberately not even consistent -- see
# test_a_forged_proofs_row_with_unrelated_evidence_never_qualifies.
REVIEW_ATTESTATION = """# Representative cross-family review

Source commit reviewed : {source_commit}
Conversation id        : {conversation_id}
Reviewing host family  : Codex CLI
Counterpart host family: Claude Code
Requested model        : {requested_model}
Resolved model identity: {resolved_model}
Resolution status      : {resolution_status}
Identity waiver        : {identity_waiver}

This review was conducted independent of the implementation.

Verdict: {verdict}
"""

GENERIC_EVIDENCE = "PASS -- representative cross-family review\n"

# The round-2 bypass, VERBATIM. A plausible paste of a FAILING review's
# transcript: every claimed token (commit, conversation id, model, 'independent',
# 'PASS', both host families) is present as a standalone word, so the round-1
# presence-only matcher graded it 'corroborated' and it reached QUALIFIED. It is
# pinned here as the known-garbage anchor for the tripwire and, more importantly,
# as proof that the *attested* design refuses it -- read by a human this document
# plainly says the review failed.
ROUND2_BYPASS_ROW = {
    "conversation_id": "conv-777",
    "requested_model": "gpt-5-codex",
    "resolved_model": "gpt-5-codex",
}
ROUND2_BYPASS_EVIDENCE = (
    "Transcript for conversation conv-777 reviewing commit {source_commit}.\n"
    "Resolved model: gpt-5-codex. Hosts consulted: claude, codex.\n"
    "This review was NOT independent, NOT cross-family, and the verdict is "
    "NOT PASS -- it FAILED.\n"
)


def _attestation(row):
    fields = {key: ("" if row.get(key) is None else row.get(key, ""))
              for key in ("source_commit", "conversation_id", "requested_model",
                          "resolved_model", "resolution_status", "identity_waiver",
                          "verdict")}
    return REVIEW_ATTESTATION.format(**fields)


def _write_proofs(directory: Path, rows, evidence_names=None, body=None):
    """Write one evidence document per review row, plus the proofs.json.

    `evidence_names` overrides which files are written (pass `()` for none, to
    exercise the missing-evidence path); `body` overrides their CONTENT, which is
    how the forgery anchors plant an unrelated document.
    """
    directory.mkdir(parents=True, exist_ok=True)
    if evidence_names is None:
        evidence_names = [row["evidence"] for row in rows]
    for name in evidence_names:
        row = next((r for r in rows if r.get("evidence") == name), None)
        if body is not None:
            text = body
        elif row is not None:
            text = _attestation(row)
        else:
            text = GENERIC_EVIDENCE
        (directory / name).write_text(text, encoding="utf-8", newline="\n")
    path = directory / "proofs.json"
    path.write_text(json.dumps({"checks": [], "reviews": rows}, indent=2),
                    encoding="utf-8", newline="\n")
    return path


# --------------------------------------------------------------------------- #
# Module-scoped fixtures -- each real release is cut exactly once
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def lab_repo(tmp_path_factory):
    return _make_repo(tmp_path_factory.mktemp("lab-src") / "lab",
                      {"README.md": "# lab\n", "tests/test_ok.py": TRIVIAL_TEST})


@pytest.fixture(scope="module")
def kit_repo(tmp_path_factory):
    return _make_repo(tmp_path_factory.mktemp("kit-src") / "kit", {
        "README.md": "# kit\n",
        "tests/test_ok.py": TRIVIAL_TEST,
        "tools/release.ps1": FAKE_RELEASE_PS1,
    })


@pytest.fixture(scope="module")
def lab_release(lab_repo, tmp_path_factory):
    root, commit = lab_repo
    store = tmp_path_factory.mktemp("lab-store")
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store)
    return store, store / "skill-mesh-lab" / "v0.1.0-experimental.1", result, commit


@pytest.fixture(scope="module")
def kit_qualified(kit_repo, tmp_path_factory):
    if PWSH is None:
        pytest.skip("powershell is not available on PATH")
    root, commit = kit_repo
    store = tmp_path_factory.mktemp("kit-store")
    proofs = _write_proofs(tmp_path_factory.mktemp("kit-proofs"), [_review_proof(commit)])
    result = _release("toolkit", root, commit, "v0.1.0-baseline.1", store, proofs=proofs,
                      attest=ATTESTING_PARTY)
    return store, store / "skill-mesh" / "v0.1.0-baseline.1", result, commit


@pytest.fixture(scope="module")
def kit_unqualified(kit_repo, tmp_path_factory):
    """Every gate green, but no cross-family review attached."""
    if PWSH is None:
        pytest.skip("powershell is not available on PATH")
    root, commit = kit_repo
    store = tmp_path_factory.mktemp("kit-store-noreview")
    result = _release("toolkit", root, commit, "v0.1.0-baseline.1", store)
    return store, result, commit


# --------------------------------------------------------------------------- #
# Tooling presence + CLI surface
# --------------------------------------------------------------------------- #

def test_tool_exists():
    assert TOOL.is_file(), "missing %s" % TOOL


def test_help_works_and_documents_the_contract():
    result = _cli("--help", timeout=120)
    assert result.returncode == 0, result.stderr
    for token in ("--source-root", "--source-commit", "--version", "--store",
                  "--python-exe", "--proofs", "--attest-reviews", "toolkit", "lab"):
        assert token in result.stdout, "--help does not mention %s" % token


def test_unknown_product_is_rejected():
    assert _cli("desktop", "--source-root", ".", "--source-commit", "HEAD",
                "--version", "v1", "--store", ".", "--python-exe", sys.executable,
                timeout=120).returncode != 0


def test_missing_required_flag_is_rejected():
    assert _cli("lab", "--source-root", ".", timeout=120).returncode != 0


# --------------------------------------------------------------------------- #
# Input validation (no subprocess work reached)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("version", [
    "v0.1.0-baseline.1", "1", "a_b", "V1.2.3", "x.y-z_0",
])
def test_version_accepts_one_safe_segment(version):
    assert br.validate_version(version) == version


@pytest.mark.parametrize("version", [
    "..", ".", "../evil", "a/b", "a\\b", "C:", ".hidden", "-lead", "", "  ",
    "con", "NUL", "lpt1", "<version>", "$v", "x" * 200,
])
def test_version_rejects_unsafe_or_placeholder_segments(version):
    with pytest.raises(br.InputError):
        br.validate_version(version)


@pytest.mark.parametrize("value", [
    "$toolkitRoot", "${store}", "<release-store>", "%USERPROFILE%", "",
    "path/to/store", "C:/placeholder/store", "...",
])
def test_placeholder_values_are_refused(value):
    with pytest.raises(br.InputError):
        br.reject_placeholder(value, "--store")


def test_products_map_is_exact():
    assert br.PRODUCTS == {"toolkit": "skill-mesh", "lab": "skill-mesh-lab"}


def test_private_path_detector_reds_on_a_planted_path(tmp_path):
    """Red-on-garbage anchor for the public-artifact sanitization gate.

    Built at runtime: this file is itself swept by the repository's committed
    absolute-path gate, so it must not carry a literal instance of the pattern.
    """
    sep = chr(92)
    planted = tmp_path / "record.json"
    planted.write_text('{"argv": ["C:%sUsers%ssomeone%spy.exe"]}\n' % (sep, sep, sep),
                       encoding="utf-8")
    assert br.scan_private_paths([("record.json", planted)]) == ["record.json:1"]
    clean = tmp_path / "clean.json"
    clean.write_text('{"argv": ["<python-exe>", "-m", "pytest"]}\n', encoding="utf-8")
    assert br.scan_private_paths([("clean.json", clean)]) == []


def test_the_private_path_detector_also_catches_posix_home_paths(tmp_path):
    """The Windows drive-letter shape is not the only way a home path leaks.

    Only a `toolkit` run requires `powershell` on PATH; a `lab` run has no such
    precondition and can legitimately be cut from a non-Windows machine, where
    the machine-specific home path in release.json / release-notes.md /
    packet.json / receipt.json is spelled `/home/<user>/...` or, on macOS,
    `/Users/<name>/...`. Both must red the same gate the Windows spelling does.
    """
    posix = tmp_path / "record.json"
    posix.write_text('{"argv": ["/home/someone/bin/python"]}\n', encoding="utf-8")
    assert br.scan_private_paths([("record.json", posix)]) == [
        "record.json:1", "record.json:<json-value>"], (
        "a VALID JSON document is scanned twice -- line by line and again over its "
        "parsed string values -- so a POSIX home path is reported by both passes")

    mac = tmp_path / "mac.json"
    mac.write_text('{"cwd": "/Users/someone/build"}\n', encoding="utf-8")
    assert br.scan_private_paths([("mac.json", mac)]) == [
        "mac.json:1", "mac.json:<json-value>"]

    nested = tmp_path / "nested.json"
    nested.write_text('{"note": "resolved from file:///home/someone/x"}\n',
                      encoding="utf-8")
    assert br.scan_private_paths([("nested.json", nested)]) == [
        "nested.json:1", "nested.json:<json-value>"]


@pytest.mark.parametrize("value", [
    "docs/Users/readme.md",
    "_shared/home/notes.md",
    "https://example.com/Users/octocat",
    "https://example.com/home/index.html",
    "/home/<user>/release-store",
    "/Users/<name>/release-store",
    # ONE representative of the class that carries neither segment at all. The
    # other three this list used to hold ('/etc/profile.d/x.sh',
    # '<source-checkout>/tools/release.ps1', 'dist/claude/SKILL.md') sat at the
    # same distance from the decision boundary and discriminated nothing extra.
    "/opt/build/checkout",
])
def test_the_private_path_detector_does_not_fire_on_a_legitimate_string(tmp_path, value):
    """The false-POSITIVE side of the two-sided measurement.

    Every string here either legitimately CONTAINS `/Users/` or `/home/` without
    being an absolute home path (a repo-relative path, a URL), or is a value a
    real record carries (a documented placeholder form, a POSIX-absolute path
    that is not a home). A detector that reds on one of these would refuse
    honest releases for no safety gain.

    NOTE the shape this list deliberately does NOT contain: `<token>/home/...`.
    That one IS refused, on purpose -- see the red list below and
    test_a_token_prefix_is_not_an_exemption_from_the_leak_gate.
    """
    clean = tmp_path / "clean.json"
    clean.write_text(json.dumps({"value": value}) + "\n", encoding="utf-8")
    assert br.scan_private_paths([("clean.json", clean)]) == [], (
        "the detector fired on a legitimate string")


#: A real Windows home path, assembled at runtime: this file is itself swept by
#: the repository's committed absolute-path gate, so it must carry no literal.
_WIN_LEAK = "C:%sUsers%ssomeone%ssecret.txt" % ((chr(92),) * 3)

# The OTHER side of the same measurement, and the side that decides the design.
# A leak scanner is a FAIL-CLOSED gate: a false positive costs one refused run
# with a legible message, a false negative publishes a machine path while the
# gate reports clean. So every one of these must red, INCLUDING the ones spelled
# with a documented token in front -- a `--proofs` field and a tool-emitted argv
# entry are the same bytes, so no textual rule can admit one and refuse the
# other. Both previously-tried exemptions are pinned here as garbage anchors:
# adding `>` to the lookbehind's excluded class would green rows 1-2, and
# substituting the tokens out (the shape review round 2 found) greens rows 7-10.
@pytest.mark.parametrize("value", [
    ">/home/someone/build.log",
    "2>/Users/someone/err.log",
    "/home/someone/x",
    "/Users/someone/build",
    "resolved from file:///home/someone/x",
    "<not-a-documented-token>/home/someone/x",
    "<source-checkout>/home/attacker/leak",
    "<store>/Users/someone/secret.txt",
    "<proofs>/home/attacker/x",
    "<store>" + _WIN_LEAK,
    _WIN_LEAK,
])
def test_the_private_path_detector_still_reds_on_a_real_leak(tmp_path, value):
    """Red-on-garbage anchor for the leak gate, token-prefixed cases included."""
    planted = tmp_path / "record.json"
    planted.write_text(json.dumps({"value": value}) + "\n", encoding="utf-8")
    assert br.scan_private_paths([("record.json", planted)]), (
        "the detector no longer reds on a real machine-specific path")


def test_a_token_prefix_is_not_an_exemption_from_the_leak_gate():
    """The decision, pinned: no lexeme is exempt from this predicate.

    Review round 1 read `<store>/home/x` as a false positive and round 2 read the
    exemption that closed it as a false negative. They are the SAME STRING SHAPE,
    so the tie is broken by the gate's direction rather than by a cleverer
    pattern: `product-charter.md` treats an uncertain verdict as unable to
    advance, so the scanner refuses. This test fails the moment any exemption --
    a token substitution, a widened character class, a provenance guess -- is
    reintroduced, which is exactly the oscillation it exists to stop.
    """
    for token in br.PATH_TOKEN_DOC:
        assert br.contains_private_path("%s/home/someone/x" % token), (
            "%s/home/... is exempt again; a caller-supplied leak spelled that "
            "way now passes the one gate that exists to stop it" % token)
        assert br.contains_private_path("%s/Users/someone/x" % token), (
            "%s/Users/... is exempt again" % token)
        # A token on its own is not a path and must stay clean, or every record
        # this tool writes would refuse itself.
        assert not br.contains_private_path(token), (
            "%s is itself read as a machine path" % token)
        assert not br.contains_private_path("%s/tools/release.ps1" % token)
    assert not hasattr(br, "_PATH_TOKEN_RE"), (
        "the token-substitution exemption is back; see this test's docstring")


def test_a_tokenized_historical_proof_is_refused_with_a_legible_message(lab_repo, tmp_path):
    """The DOCUMENTED COST of failing closed, asserted rather than hidden.

    A `--proofs` document may carry evidence forward from a prior release's own
    `release.json`, whose `checks[].argv` entries are tokenized. If the pinned
    product has a top-level directory named `home` or `Users`, that spelling is
    indistinguishable from a real absolute path written with a token in front, so
    it is REFUSED at exit 2 -- and the message has to say so well enough for an
    operator to act, because the runbook (section 9) promises exactly that.

    The behaviour is deliberate. If this test ever needs `returncode == 0`, the
    gate has been reopened; read
    test_a_token_prefix_is_not_an_exemption_from_the_leak_gate first.
    """
    root, commit = lab_repo
    proof_dir = tmp_path / "proofs"
    proof_dir.mkdir()
    (proof_dir / "old-run.txt").write_text("historical run output\n", encoding="utf-8")
    (proof_dir / "proofs.json").write_text(json.dumps({
        "checks": [{
            "argv": ["<python-exe>", "-m", "pytest", "<source-checkout>/home/tests"],
            "exit_code": 0,
            "cwd": "<source-checkout>/Users",
            "source_commit": commit,
            "evidence": "old-run.txt",
            "name": "historical-pytest",
        }],
        "reviews": [],
    }), encoding="utf-8")
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store,
                      proofs=proof_dir / "proofs.json")
    assert result.returncode == 2, (
        "a token-prefixed home path must be refused as bad input:\n%s"
        % (result.stdout + result.stderr))
    message = result.stdout + result.stderr
    assert "absolute user path" in message
    assert "NOT an exemption" in message, (
        "the refusal must tell the operator that the token did not exempt it")
    assert "section 9" in message, "the refusal must point at the workaround"
    assert not (store / "skill-mesh-lab").exists(), "nothing may be built on exit 2"


def test_the_leak_gate_fails_closed_on_an_artifact_it_cannot_grade(tmp_path):
    """An unreadable artifact is a FAULT, never a clean one.

    scan_private_paths is the last gate before a release is retained, and every
    file it is handed was written moments earlier by the same process. Skipping
    one that cannot be read would let a real leak inside a transiently locked
    file (an antivirus handle, a disk hiccup) pass the one check that exists to
    stop it -- a silent fail-OPEN on the safety-critical path.
    """
    missing = tmp_path / "gone.json"
    assert br.scan_private_paths([("gone.json", missing)]) == ["gone.json:<unreadable>"]

    # A directory where a file is expected: read_text raises OSError, same class
    # of fault as a lock, without depending on filesystem permissions.
    as_dir = tmp_path / "adir.json"
    as_dir.mkdir()
    assert br.scan_private_paths([("adir.json", as_dir)]) == ["adir.json:<unreadable>"]

    undecodable = tmp_path / "bytes.md"
    undecodable.write_bytes(b"\xff\xfe\x00 not utf-8 \xc3\x28")
    assert br.scan_private_paths([("bytes.md", undecodable)]) == ["bytes.md:<unreadable>"]

    # Scoped deliberately: an UNPARSABLE .json is not a hit. Only the second pass
    # is lost, the raw line scan still graded the same bytes, and the artifacts
    # this gate is handed in production are written by json.dumps.
    broken = tmp_path / "broken.json"
    broken.write_text("{not json at all\n", encoding="utf-8")
    assert br.scan_private_paths([("broken.json", broken)]) == []


def test_a_leak_and_an_ungraded_artifact_are_reported_as_different_faults():
    """Failing closed is right; describing a lock as a leak is not.

    Both outcomes abort the run. They send an operator to different places: a
    leak means read the record and fix what produced the value, an unreadable
    artifact means a lock or an IO fault and the record is probably fine.
    """
    assert br.describe_scan_findings([]) is None

    leak = br.describe_scan_findings(["release.json:12"])
    assert "machine-specific absolute path" in leak
    assert "could not be read back" not in leak

    ungraded = br.describe_scan_findings(["receipt.json" + br.UNGRADED_MARK])
    assert "could not be read back" in ungraded
    assert "FAULT, not a leak finding" in ungraded
    assert "machine-specific absolute path" not in ungraded, (
        "an unreadable artifact was announced to the operator as a leak")
    assert "receipt.json" in ungraded and br.UNGRADED_MARK not in ungraded, (
        "the message should name the artifact, not echo the internal marker")

    both = br.describe_scan_findings(["release.json:12",
                                      "receipt.json" + br.UNGRADED_MARK])
    assert "machine-specific absolute path" in both and "could not be read back" in both


def test_an_ungraded_public_artifact_aborts_the_release_end_to_end(
        lab_repo, tmp_path, monkeypatch, capsys):
    """The same distinction, through the PRODUCTION entry point.

    The scanned-artifact list is the injection point: adding a name the stage
    does not carry makes the REAL scanner hit a REAL unreadable file, so the
    producer -> consumer round trip is exercised rather than stubbed.
    """
    root, commit = lab_repo
    monkeypatch.setattr(br, "PUBLIC_SCANNED_ARTIFACTS",
                        br.PUBLIC_SCANNED_ARTIFACTS + ("public/not-written.json",))
    store = tmp_path / "store"
    code = br.main(["lab", "--source-root", str(root), "--source-commit", commit,
                    "--version", "v0.1.0-experimental.1", "--store", str(store),
                    "--python-exe", sys.executable])
    err = capsys.readouterr().err
    assert code == br.EXIT_EXEC, err
    assert "could not be read back and graded" in err, err
    assert "public/not-written.json" in err, err
    assert "machine-specific absolute path" not in err, (
        "an artifact that could not be read was reported as a leak")
    assert not (store / "skill-mesh-lab" / "v0.1.0-experimental.1").exists(), (
        "the gate must fail closed -- nothing is retained as a release")
    # And where the payload went, because the runbook's exit-1 table says so:
    # the scan is the LAST step, after release.json and SHA256SUMS are written,
    # so its refusal leaves a COMPLETE payload -- an attempt, not an abort.
    attempts = _attempt_dirs(store)
    assert len(attempts) == 1 and (attempts[0] / "release.json").is_file(), (
        "a leak-gate refusal is a complete payload and belongs in .attempts/")
    aborted = store / ".aborted"
    assert not aborted.is_dir() or not list(aborted.iterdir())


def test_the_packet_describes_exactly_the_artifacts_that_were_scanned(lab_release):
    """The packet's `sanitization.scanned` must describe what was really graded.

    Graded end to end against a real release: the published field, the scanner's
    selected files, and the files that actually exist must all agree.
    """
    _, release_dir, _, _ = lab_release
    packet = json.loads((release_dir / "public" / "packet.json").read_text(encoding="utf-8"))
    assert packet["sanitization"]["scanned"] == br.public_scanned_artifacts(
        release_dir, "lab")
    for name in packet["sanitization"]["scanned"]:
        assert (release_dir / name).is_file(), (
            "the packet claims %s was scanned, but the release has no such file" % name)


def test_nonexistent_source_root_is_an_input_error(tmp_path):
    result = _release("lab", tmp_path / "nope", "HEAD", "v1", tmp_path / "store")
    assert result.returncode == 2, result.stdout + result.stderr


def test_non_git_source_root_is_an_input_error(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    result = _release("lab", plain, "HEAD", "v1", tmp_path / "store")
    assert result.returncode == 2
    assert "not a git working tree" in result.stderr


def test_unresolvable_commit_is_an_input_error(lab_repo, tmp_path):
    root, _ = lab_repo
    result = _release("lab", root, "0" * 40, "v1", tmp_path / "store")
    assert result.returncode == 2
    assert "cannot resolve" in result.stderr


def test_store_inside_the_source_root_is_refused(lab_repo, tmp_path):
    """The working source is read-only to this tool, so the store may not live in it."""
    root, commit = lab_repo
    result = _release("lab", root, commit, "v1", root / "releases")
    assert result.returncode == 2
    assert "inside --source-root" in result.stderr
    assert not (root / "releases").exists(), "the refused store was created anyway"


def test_linked_store_ancestor_is_refused(lab_repo, tmp_path):
    """A junction on an output ancestor redirects the leaf; refuse it outright."""
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "linked"
    made = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(real)],
                          capture_output=True, text=True)
    if made.returncode != 0 or not link.exists():
        pytest.skip("could not create a junction on this machine")
    root, commit = lab_repo
    result = _release("lab", root, commit, "v1", link / "store")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "reparse point" in result.stderr


def test_a_linked_product_directory_inside_a_real_store_is_refused(lab_repo, tmp_path):
    """The REAL output ancestor is <store>/<product>, not the --store argument.

    `staging.mkdir(parents=True)` traverses an existing junction at
    <store>/<product> without complaint, so a junction planted there before the
    first release of that product would silently redirect every later one. The
    --store guard cannot see it: --store itself is a real directory here.
    """
    store = tmp_path / "store"
    store.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    link = store / "skill-mesh-lab"
    made = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(elsewhere)],
                          capture_output=True, text=True)
    if made.returncode != 0 or not link.exists():
        pytest.skip("could not create a junction on this machine")
    root, commit = lab_repo
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "reparse point" in (result.stdout + result.stderr)
    assert not any(elsewhere.iterdir()), (
        "the release was written through the junction anyway")


# --------------------------------------------------------------------------- #
# Lab: source-only archive, explicitly INCOMPLETE, exit 0
# --------------------------------------------------------------------------- #

def test_lab_incomplete_archive_is_retained_with_exit_zero(lab_release):
    _, release_dir, result, _ = lab_release
    assert result.returncode == 0, result.stdout + result.stderr
    assert release_dir.is_dir()
    record = _record(release_dir)
    assert record["qualification"] == "INCOMPLETE", (
        "an explicitly incomplete lab archive is a successful retention, and it "
        "makes no qualification claim")
    assert record["product"] == "skill-mesh-lab"
    assert record["providers"] == [], "the lab archive is source-only"


def test_lab_release_layout(lab_release):
    _, release_dir, _, _ = lab_release
    for name in ("source.zip", "release.json", "SHA256SUMS", "release-notes.md",
                 "receipt.json", "public/packet.json", "verify-artifacts.py",
                 "checks/source-pytest.txt"):
        assert (release_dir / name).is_file(), "missing %s" % name
    assert not (release_dir / "dist").exists(), "the lab archive must package no profile"
    assert not (release_dir / "CHECKSUMS.txt").exists()


def test_record_carries_every_required_schema_v1_field(lab_release):
    _, release_dir, _, commit = lab_release
    record = _record(release_dir)
    required = ("schema_version", "product", "version", "source_commit", "source_tree",
                "builder_commit", "created_at", "predecessor", "qualification",
                "providers", "artifacts", "environment", "checks", "reviews",
                "known_gaps", "dependencies")
    missing = [field for field in required if field not in record]
    assert not missing, "release.json is missing %s" % missing
    assert record["schema_version"] == 1
    assert record["qualification"] in br.QUALIFICATION_VALUES
    assert record["predecessor"] is None
    assert record["source_commit"] == commit
    for field in ("source_commit", "source_tree", "builder_commit"):
        assert br.FULL_OID_RE.match(record[field]), "%s is not a full lowercase oid" % field
    assert all(isinstance(v, str) for v in record["environment"].values())
    for key in ("os", "powershell", "git", "python", "pytest", "pyyaml",
                "markdown-it-py", "jsonschema"):
        assert key in record["environment"], "environment lacks %s" % key


def test_builder_commit_is_recorded_separately_from_the_source_commit(lab_release):
    _, release_dir, _, commit = lab_release
    record = _record(release_dir)
    builder = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
                             capture_output=True, text=True, check=True).stdout.strip()
    assert record["builder_commit"] == builder
    assert record["builder_commit"] != record["source_commit"], (
        "the helper's own commit and the product's selected commit are never conflated")
    assert record["source_commit"] == commit


def test_known_gaps_and_dependencies_are_explicit(lab_release):
    _, release_dir, _, _ = lab_release
    record = _record(release_dir)
    assert record["known_gaps"], "known_gaps is empty without inspection"
    assert record["dependencies"], "dependencies is empty without inspection"
    blob = " ".join(record["known_gaps"]).lower()
    assert "native host acceptance" in blob
    assert "cross-family review" in blob
    joined = " ".join(record["dependencies"])
    assert "pytest" in joined and "git" in joined


def test_artifacts_exclude_the_record_and_the_sums_file(lab_release):
    _, release_dir, _, _ = lab_release
    record = _record(release_dir)
    paths = {entry["path"] for entry in record["artifacts"]}
    assert "release.json" not in paths and "SHA256SUMS" not in paths, (
        "the record and SHA256SUMS are excluded to avoid recursive hashing")
    assert "source.zip" in paths
    for entry in record["artifacts"]:
        assert br.SHA256_RE.match(entry["sha256"]), entry
        assert not entry["path"].startswith("/") and ".." not in entry["path"].split("/")
        assert br.sha256_file(release_dir / entry["path"]) == entry["sha256"]


def test_sha256sums_covers_the_record_and_verifies(lab_release):
    _, release_dir, _, _ = lab_release
    lines = (release_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    listed = {line.split("  ", 1)[1] for line in lines if line.strip()}
    assert "release.json" in listed, "SHA256SUMS must cover the record"
    assert "SHA256SUMS" not in listed, "SHA256SUMS must not hash itself"
    for line in lines:
        digest, _, rel = line.partition("  ")
        assert br.sha256_file(release_dir / rel) == digest


def test_retained_verifier_reopens_the_release_and_reds_on_a_flipped_byte(
        lab_release, tmp_path):
    """The reopen path an operator actually runs, plus its red-on-garbage anchor."""
    _, release_dir, _, _ = lab_release
    copy = tmp_path / "reopened"
    shutil.copytree(release_dir, copy)
    verifier = [sys.executable, str(copy / "verify-artifacts.py"),
                "SHA256SUMS", "."]
    good = subprocess.run(verifier, cwd=str(copy), capture_output=True, text=True)
    assert good.returncode == 0, good.stdout + good.stderr

    notes = copy / "release-notes.md"
    notes.write_bytes(notes.read_bytes() + b"tamper\n")
    bad = subprocess.run(verifier, cwd=str(copy), capture_output=True, text=True)
    assert bad.returncode == 1, "the verifier passed over a flipped byte"
    assert "MISMATCH" in bad.stdout


def test_source_zip_extracted_contents_match_the_pinned_tracked_files(
        lab_release, lab_repo):
    """Names AND BYTES. The contract clause is about extracted CONTENTS.

    A name-only assertion cannot see a compression or encoding fault that
    corrupts a member's body while the file list stays perfect, so this compares
    every member's bytes to the pinned source they were archived from -- the full
    producer -> consumer round trip -- and pins the two known bodies literally so
    a bug shared by both sides of the comparison cannot cancel itself out.
    """
    root, _ = lab_repo
    _, release_dir, _, _ = lab_release
    with zipfile.ZipFile(release_dir / "source.zip") as zf:
        names = sorted(n for n in zf.namelist() if not n.endswith("/"))
        assert names == ["README.md", "tests/test_ok.py"]
        assert ".git/config" not in names, "VCS internals must never enter the archive"
        assert zf.read("README.md") == b"# lab\n"
        assert zf.read("tests/test_ok.py") == TRIVIAL_TEST.encode("utf-8")
        for name in names:
            assert zf.read(name) == (root / name).read_bytes(), (
                "archived member %r does not reproduce the pinned file byte-for-byte"
                % name)


def test_public_packet_excludes_private_evidence(lab_release):
    _, release_dir, _, _ = lab_release
    packet = json.loads((release_dir / "public" / "packet.json").read_text(encoding="utf-8"))
    assert packet["publication_status"] == "NOT_PUBLISHED"
    excluded = {row["path"] for row in packet["exclude"]}
    for private in ("source.zip", "SHA256SUMS", "checks/", "reviews/",
                    "proofs/", "receipt.json"):
        assert private in excluded, "%s must not be publishable" % private
    assert "PUBLIC-SHA256SUMS" in packet["include"]
    assert "release.json" in packet["include"]
    assert "source.zip" not in packet["include"]
    assert all(row["reason"].strip() for row in packet["exclude"])


def test_public_subset_keeps_pinned_source_private_and_verifies(tmp_path):
    root, commit = _make_repo(tmp_path / "source", {
        "README.md": "Private path: /home/alice/private\n",
        "tests/test_ok.py": TRIVIAL_TEST,
    })
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v1", store)
    assert result.returncode == 0, result.stdout + result.stderr
    retained = store / "skill-mesh-lab" / "v1"
    packet = json.loads((retained / "public/packet.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(retained / "source.zip") as archive:
        assert b"/home/alice/private" in archive.read("README.md")
    published = tmp_path / "published"
    published.mkdir()
    for name in packet["include"]:
        target = published / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(retained / name, target)
    assert not (published / "source.zip").exists()
    assert b"/home/alice/private" not in b"".join(
        path.read_bytes() for path in published.rglob("*") if path.is_file())
    verified = subprocess.run(
        [sys.executable, "verify-artifacts.py", packet["hash_manifest"], "."],
        cwd=published, capture_output=True, text=True)
    assert verified.returncode == 0, verified.stdout + verified.stderr


def test_every_file_the_notes_tell_a_consumer_to_run_is_publishable(lab_release):
    """The packet may not contradict the notes it publishes alongside.

    release-notes.md is publishable and tells its reader to run a verifier. A
    recipient of the published subset has only what `include` names, so every
    script the notes invoke must be in that set and outside every excluded
    prefix -- otherwise the packet describes an instruction nobody can follow.
    """
    _, release_dir, _, _ = lab_release
    packet = json.loads((release_dir / "public" / "packet.json").read_text(encoding="utf-8"))
    notes = (release_dir / "release-notes.md").read_text(encoding="utf-8")
    invoked = set(re.findall(r"^python (\S+\.py)\b", notes, flags=re.MULTILINE))
    assert invoked, "the notes no longer tell a consumer how to verify anything"
    excluded = [row["path"] for row in packet["exclude"]]
    for script in invoked:
        assert (release_dir / script).is_file(), "the notes invoke a missing %s" % script
        assert script in packet["include"], (
            "release-notes.md tells a consumer to run %s, which the packet does not "
            "publish" % script)
        for prefix in excluded:
            hidden = (script == prefix
                      or (prefix.endswith("/") and script.startswith(prefix)))
            assert not hidden, (
                "%s is invoked by the published notes but hidden by exclude %r"
                % (script, prefix))


def test_caller_controlled_review_text_cannot_restructure_the_public_notes(
        lab_repo, tmp_path):
    """A '|' in attested text may not open a new cell in the published table."""
    root, commit = lab_repo
    row = _review_proof(commit, conversation_id="rev|0002",
                        resolution_status="observed | injected | cells")
    proofs = _write_proofs(tmp_path / "proofs", [row])
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store, proofs=proofs)
    assert result.returncode == 0, result.stdout + result.stderr
    notes = (store / "skill-mesh-lab" / "v0.1.0-experimental.1"
             / "release-notes.md").read_text(encoding="utf-8")
    header = [line for line in notes.splitlines() if line.startswith("| Review |")][0]
    body = [line for line in notes.splitlines() if "injected" in line][0]
    assert "\\|" in body, "a caller-supplied pipe reached the table unescaped"
    unescaped = lambda line: line.count("|") - line.count("\\|")
    assert unescaped(body) == unescaped(header), (
        "attested text changed the table's cell count:\n%s\n%s" % (header, body))


def test_markdown_inlining_neutralizes_cell_and_code_span_breakers():
    assert br.md_inline("a|b") == "a\\|b"
    assert br.md_inline("one\ntwo\r\nthree") == "one two three"
    assert br.md_code("x`y|z") == "`x'y\\|z`"


def test_md_untrusted_escapes_every_inline_construct_opener():
    """The mixed-trust channel's neutralizer, graded character by character.

    `md_inline` plain mode is for AUTHORED prose and deliberately leaves the
    backtick and the emphasis markers live; `md_untrusted` is the path for a
    sentence that has already had caller text fused into it, so nothing that can
    open an inline construct may survive.
    """
    for ch in "\\`*_[]|~#":
        assert br.md_untrusted("a%sb" % ch) == "a\\%sb" % ch, (
            "%r can open an inline construct and was not escaped" % ch)
    assert br.md_untrusted("<b>&amp;</b>") == "&lt;b&gt;&amp;amp;&lt;/b&gt;"
    assert br.md_untrusted("one\ntwo\r\nthree\tfour") == "one two three four"
    # ONE pass, not chained replaces: a second pass over its own output would
    # turn the escape `\[` into a literal backslash followed by a LIVE `[`.
    assert br.md_untrusted("a\\[b") == "a\\\\\\[b"
    # And md_inline is unchanged -- authored prose keeps its formatting.
    assert br.md_inline("a`b*c") == "a`b*c"


#: A token that appears in no authored string, so its presence in a rendered
#: bullet proves the caller's text actually reached the channel.
_MARKER = "zqsentinel"

#: The payload shapes. Split by the CONSTRAINT each field imposes, not by
#: producer: a filename has to be creatable on Windows, an evidence-stated claim
#: has to survive verbatim into the evidence document, and the rest is free.
_PAYLOAD = {
    # Everything CommonMark can act on, on one line.
    "inline": "%s `code` *em* _em_ [l](u) | pipe ~s~ # h <b>raw</b> & amp \\ esc" % _MARKER,
    # The same, plus the line break a bullet must survive.
    "multiline": "%s `code` *em* [l](u) | pipe <b>raw</b>\nsecond line" % _MARKER,
    # Windows-legal filename characters only -- this one is really created.
    "file": "%s-`code`-[l]-~s~-#h-&amp.txt" % _MARKER,
    "file2": "%s-`review`-[l]-~s~.md" % _MARKER,
    # Never created, so it may carry every metacharacter.
    "path": "%s-`missing`-*[gone]*.txt" % _MARKER,
    # A mismatching source id whose FIRST TWELVE characters -- all the message
    # embeds -- already carry a backtick and an emphasis marker.
    "commit": "`%s*_[]0000000000000000000" % _MARKER,
    "envkey": "%s-`key`-*k*" % _MARKER,
    "envval": "%s-`val`-*v*" % _MARKER,
    # Stated verbatim by the evidence document, so it must stay single-line.
    "verdict": "NEEDS-WORK %s `code` *em* [l](u) ~s~ & amp" % _MARKER,
}

#: The control. Same fields, same producers, no Markdown metacharacter anywhere.
_BENIGN = {
    "inline": "%s plain argv text" % _MARKER,
    "multiline": "%s plain gate name" % _MARKER,
    "file": "%s-plain-check.txt" % _MARKER,
    "file2": "%s-plain-review.md" % _MARKER,
    "path": "%s-plain-missing.txt" % _MARKER,
    "commit": "d%s000000000000000000000" % _MARKER,
    "envkey": "%s-plain-key" % _MARKER,
    "envval": "%s-plain-val" % _MARKER,
    "verdict": "NEEDS-WORK %s plain" % _MARKER,
}


def _build_injection_proofs(directory: Path, commit: str, values) -> Path:
    """A proofs document that drives EVERY producer of the reasons/gaps channel.

    One row per producer shape, so the control run and the payload run fire the
    same set of messages and differ only in the caller-supplied characters:

    * a failing check whose evidence RESOLVES -- the failed-gate reason, which
      embeds both `checks[].name` (optional, never type- or content-validated)
      and the evidence locator in one sentence;
    * a check whose evidence does NOT resolve and whose source id mismatches --
      the argv/evidence gap and the source-mismatch gap;
    * a review with the same two problems -- their review-side counterparts;
    * a review that is complete, consistent, attested and bound to this source,
      so `review_qualifies` runs all the way down to the verdict message;
    * an environment key this run did not measure, and a declared value for one
      it did -- the two environment-mismatch gaps.
    """
    directory.mkdir(parents=True, exist_ok=True)
    (directory / values["file"]).write_text("historical run output\n",
                                            encoding="utf-8", newline="\n")
    review_ok = _review_proof(
        commit, verdict=values["verdict"], evidence=values["file2"],
        requested_model="req-%s" % values["inline"],
        resolved_model="res-%s" % values["inline"],
        resolution_status="status-%s" % values["inline"],
        conversation_id="conv-%s" % values["inline"])
    (directory / values["file2"]).write_text(_attestation(review_ok),
                                             encoding="utf-8", newline="\n")
    review_broken = _review_proof(commit, source_commit=values["commit"],
                                  evidence=values["path"],
                                  conversation_id="conv-broken-%s" % values["inline"])
    document = {
        "checks": [
            {"argv": ["<python-exe>", "-m", "pytest", values["inline"]],
             "exit_code": 1, "cwd": ".", "source_commit": commit,
             "evidence": values["file"], "name": values["multiline"]},
            {"argv": [values["inline"], "--flag"], "exit_code": 0, "cwd": ".",
             "source_commit": values["commit"], "evidence": values["path"],
             "name": "second-%s" % values["inline"]},
        ],
        "reviews": [review_broken, review_ok],
        "environment": {values["envkey"]: values["envval"],
                        "python": values["envval"]},
    }
    path = directory / "proofs.json"
    path.write_text(json.dumps(document, indent=2), encoding="utf-8", newline="\n")
    return path


def _notes_from_proofs(root, commit, store: Path, proofs: Path):
    """Cut one real release from `proofs` and return (notes text, record).

    The construction includes a FAILED gate, so the run is BLOCKED and its
    complete payload is retained under `.attempts/` rather than published.
    """
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store,
                      proofs=proofs, attest=ATTESTING_PARTY)
    assert result.returncode in (0, 1), result.stdout + result.stderr
    attempts = _attempt_dirs(store)
    assert len(attempts) == 1, "expected exactly one retained attempt, got %s" % attempts
    return ((attempts[0] / "release-notes.md").read_text(encoding="utf-8"),
            _record(attempts[0]))


def _token_structure(md, text: str):
    """The document's SHAPE: every block token, and every inline child's type.

    Deliberately excludes content. Caller text is allowed to change what a bullet
    says; it may never change which tokens the document is made of.
    """
    shape = []
    for token in md.parse(text):
        shape.append(("block", token.type, token.tag, token.nesting))
        if token.type == "inline":
            for child in token.children or []:
                shape.append(("inline", child.type, child.tag))
    return shape


def test_caller_text_cannot_alter_the_parsed_structure_of_the_public_notes(
        lab_repo, tmp_path):
    """The channel-level regression gate for the reasons/gaps mixed-trust channel.

    THE PREDICATE IS FIELD-AGNOSTIC ON PURPOSE. A sentinel payload carrying every
    Markdown metacharacter is planted in EVERY caller-controlled `--proofs` field,
    arranged to drive every producer that fuses caller text into a qualification
    reason or a known gap; a control run supplies benign values in the same
    fields. Then both `release-notes.md` files are PARSED with markdown-it-py --
    a real CommonMark implementation, because a hand-rolled scanner would only be
    this repository's model of CommonMark -- and the two token structures must be
    identical. Caller text may change what a bullet SAYS; it may never change
    what the document IS.

    That is the property a fourth review round cannot be relied on to re-check:
    a producer added later, embedding a field nobody listed here, reds this test
    without the test naming the site. Two earlier line-scoped fixes did not hold
    precisely because the producer set is open-ended.
    """
    markdown_it = pytest.importorskip(
        "markdown_it",
        reason="markdown-it-py is this repository's pinned CommonMark parser")
    root, commit = lab_repo

    payload_proofs = _build_injection_proofs(tmp_path / "payload", commit, _PAYLOAD)
    benign_proofs = _build_injection_proofs(tmp_path / "benign", commit, _BENIGN)

    notes_payload, record_payload = _notes_from_proofs(
        root, commit, tmp_path / "store-payload", payload_proofs)
    notes_control, _ = _notes_from_proofs(
        root, commit, tmp_path / "store-benign", benign_proofs)

    # ---- the run must not be vacuous: prove the payload really reached the
    # channel, in every producer shape, before grading how it rendered.
    channel = list(record_payload["qualification_reasons"]) + list(
        record_payload["known_gaps"])
    carrying = [text for text in channel if _MARKER in text]
    assert len(carrying) >= 8, (
        "the construction drove only %d producers; the payload never reached the "
        "channel in enough shapes to grade it:\n%s"
        % (len(carrying), "\n".join(channel)))
    for shape in ("could not be resolved", "binds source_commit",
                  "which this run did not measure", "but this run measured",
                  "does not satisfy the charter invariant", "exited 1"):
        assert any(shape in text for text in channel), (
            "no message of the shape %r fired, so that producer is untested:\n%s"
            % (shape, "\n".join(channel)))
    assert any("`" in text for text in carrying), (
        "the payload lost its backtick before reaching the channel")

    # ---- and the notes must still SAY it, escaped rather than dropped.
    assert _MARKER in notes_payload, "the payload was silently dropped from the notes"

    md = markdown_it.MarkdownIt("commonmark").enable("table")
    assert _token_structure(md, notes_payload) == _token_structure(md, notes_control), (
        "caller-controlled --proofs text changed the PARSED structure of the "
        "public release notes")


def test_an_unpaired_caller_backtick_cannot_open_a_code_span_in_the_notes():
    """The narrow, executed repro this gate grew out of, kept as its anchor.

    `compute_qualification`'s failed-gate message embeds TWO caller-controlled
    values -- `checks[].name` (optional, and never type- or content-validated)
    and the evidence locator -- in one sentence. A backtick in each pairs across
    the authored text between them, so the exit code and the evidence path a
    reader needs are swallowed into a code span. Measured before the fix as
    text/code_inline/text against a control's single text token.
    """
    markdown_it = pytest.importorskip("markdown_it")
    md = markdown_it.MarkdownIt("commonmark")

    def structure(name, evidence):
        _, reasons = br.compute_qualification(
            "lab", [{"name": name, "exit_code": 1, "evidence": evidence,
                     "execution": "imported", "import_status": "imported"}], [], "a" * 40)
        bullet = "* %s\n" % br.md_untrusted(reasons[0])
        return [child.type
                for token in md.parse(bullet) if token.type == "inline"
                for child in (token.children or [])]

    assert structure("gate-`x", "proofs/00-`run.txt") == structure(
        "gate-xx", "proofs/00-run.txt") == ["text"], (
        "a caller backtick reopened a code span in a qualification reason")


def test_generated_public_text_carries_no_machine_specific_path(lab_release):
    _, release_dir, _, _ = lab_release
    hits = br.scan_private_paths([
        (name, release_dir / name)
        for name in ("release.json", "release-notes.md", "public/packet.json",
                     "receipt.json")
    ])
    assert hits == [], "a machine-specific absolute path reached a public artifact: %s" % hits


def test_recorded_argv_is_tokenized_and_cwd_is_relative(lab_release):
    _, release_dir, _, _ = lab_release
    record = _record(release_dir)
    gate = [row for row in record["checks"] if row["name"] == "source-pytest"][0]
    assert gate["argv"] == ["<python-exe>", "-m", "pytest"]
    assert gate["cwd"] == "."
    assert gate["exit_code"] == 0
    assert gate["evidence"] == "checks/source-pytest.txt"
    assert gate["execution"] == "native"
    assert "<python-exe>" in record["path_tokens"]


def test_receipt_records_argv_time_exit_and_evidence(lab_release):
    _, release_dir, _, _ = lab_release
    receipt = json.loads((release_dir / "receipt.json").read_text(encoding="utf-8"))
    for field in ("argv", "started_at", "recorded_at", "exit_code", "evidence",
                  "operation_id", "release_id"):
        assert field in receipt, "receipt lacks %s" % field
    assert receipt["exit_code"] == 0
    assert "checks/source-pytest.txt" in receipt["evidence"]


def test_working_source_is_unchanged_by_a_release(lab_release, lab_repo):
    root, commit = lab_repo
    _, release_dir, _, _ = lab_release
    assert _git(["rev-parse", "HEAD"], root).stdout.strip() == commit
    assert _git(["status", "--porcelain"], root).stdout.strip() == "", (
        "the tool wrote into the working source; it is read-only to this tool")
    assert not (root / ".work").exists()


def test_work_directory_is_cleaned_up(lab_release):
    store, _, _, _ = lab_release
    work = store / ".work"
    assert not work.exists() or not any(work.iterdir()), (
        "the disposable checkout/stage workspace was left behind")


# --------------------------------------------------------------------------- #
# Repeated request: verify, or refuse. Never overwrite.
# --------------------------------------------------------------------------- #

def test_repeated_identical_request_verifies_without_overwriting(lab_release, lab_repo):
    store, release_dir, _, commit = lab_release
    root, _ = lab_repo
    before = {rel: br.sha256_file(release_dir / rel)
              for rel in br.iter_files(release_dir)}
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERIFIED" in result.stdout
    after = {rel: br.sha256_file(release_dir / rel)
             for rel in br.iter_files(release_dir)}
    assert before == after, "a repeated request rewrote a retained release"


def test_repeated_request_with_a_different_commit_refuses_as_a_collision(
        lab_release, lab_repo, tmp_path):
    store, release_dir, _, _ = lab_release
    root, _ = lab_repo
    mutated = tmp_path / "mutated"
    shutil.copytree(root, mutated)
    (mutated / "README.md").write_text("# lab changed\n", encoding="utf-8", newline="\n")
    _git(["add", "-A"], mutated)
    _git(["commit", "-q", "--no-verify", "-m", "second"], mutated)
    second = _git(["rev-parse", "HEAD"], mutated).stdout.strip()

    before = br.sha256_file(release_dir / "release.json")
    result = _release("lab", mutated, second, "v0.1.0-experimental.1", store)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "COLLISION" in result.stderr
    assert br.sha256_file(release_dir / "release.json") == before, (
        "a refused collision still modified the retained release")


def test_damaged_retained_bytes_are_reported_as_an_execution_failure(
        lab_release, lab_repo, tmp_path):
    store, release_dir, _, commit = lab_release
    root, _ = lab_repo
    damaged_store = tmp_path / "damaged-store"
    shutil.copytree(store, damaged_store)
    target = damaged_store / "skill-mesh-lab" / "v0.1.0-experimental.1" / "release-notes.md"
    target.write_bytes(target.read_bytes() + b"tamper\n")
    result = _release("lab", root, commit, "v0.1.0-experimental.1", damaged_store)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "do not verify" in result.stderr


def test_tampered_archive_content_is_caught_even_when_every_hash_agrees(
        lab_release, lab_repo, tmp_path):
    """Red-on-garbage anchor for the EXTRACTED-CONTENTS detector itself.

    `test_damaged_retained_bytes_...` trips the SHA256SUMS check and returns
    before the content comparison ever runs, so that detector had no test able to
    make it fail -- and a detector nothing can red is not known to work. Here the
    archive's member body is rewritten and the record plus SHA256SUMS are made
    self-consistent again, so every earlier check passes by construction and the
    ONLY thing left that can fire is the comparison against a fresh checkout.

    The calibration is the retained verifier's own exit 0 on the tampered store:
    it proves the hash layer really is satisfied, so the exit 1 below is
    attributable to the content detector and to nothing else.
    """
    store, _, _, commit = lab_release
    root, _ = lab_repo
    forged_store = tmp_path / "forged-store"
    shutil.copytree(store, forged_store)
    forged = forged_store / "skill-mesh-lab" / "v0.1.0-experimental.1"

    archive = forged / "source.zip"
    with zipfile.ZipFile(archive) as zf:
        members = [(info, zf.read(info.filename)) for info in zf.infolist()]
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for info, data in members:
            if info.filename == "README.md":
                data = b"# lab (content swapped after retention)\n"
            zf.writestr(info, data)
    assert sorted(info.filename for info, _ in members) == [
        "README.md", "tests/test_ok.py"], "the member LIST must be unchanged"

    record = _record(forged)
    for entry in record["artifacts"]:
        entry["sha256"] = br.sha256_file(forged / entry["path"])
    (forged / "release.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    br.write_sha256sums(forged, record["artifacts"] + [
        {"path": "release.json", "sha256": br.sha256_file(forged / "release.json")}])

    calibration = subprocess.run(
        [sys.executable, str(forged / "verify-artifacts.py"), "SHA256SUMS", "."],
        cwd=str(forged), capture_output=True, text=True)
    assert calibration.returncode == 0, (
        "the anchor is miscalibrated: the hash layer is already red, so a failure "
        "below would not be attributable to the content detector\n"
        + calibration.stdout + calibration.stderr)

    result = _release("lab", root, commit, "v0.1.0-experimental.1", forged_store)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "EXTRACTED CONTENTS do not match" in result.stderr, result.stderr
    assert "README.md" in result.stderr, (
        "the message must name the differing member: %s" % result.stderr)


def test_predecessor_names_the_previous_release_of_the_same_product(lab_release, lab_repo):
    store, _, _, commit = lab_release
    root, _ = lab_repo
    result = _release("lab", root, commit, "v0.1.0-experimental.2", store)
    assert result.returncode == 0, result.stdout + result.stderr
    record = _record(store / "skill-mesh-lab" / "v0.1.0-experimental.2")
    assert record["predecessor"] == "skill-mesh-lab/v0.1.0-experimental.1"


# --------------------------------------------------------------------------- #
# Lab: a FAILED gate is BLOCKED and keeps the source archive
# --------------------------------------------------------------------------- #

def test_failed_source_suite_is_blocked_and_still_keeps_the_archive(
        tmp_path_factory, tmp_path):
    root, commit = _make_repo(tmp_path_factory.mktemp("lab-red") / "lab", {
        "README.md": "# lab\n", "tests/test_red.py": FAILING_TEST})
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store)
    assert result.returncode == 1, result.stdout + result.stderr
    assert not (store / "skill-mesh-lab" / "v0.1.0-experimental.1").exists(), (
        "a failed qualification must not reserve the version name")
    attempts = _attempt_dirs(store)
    assert len(attempts) == 1, attempts
    record = _record(attempts[0])
    assert record["qualification"] == "BLOCKED"
    assert (attempts[0] / "source.zip").is_file(), (
        "a failed gate keeps the source archive")
    assert (attempts[0] / "checks" / "source-pytest.txt").is_file()
    assert str(attempts[0]) in result.stdout, (
        "a qualification failure must print its retained diagnostic paths")


def test_a_retry_allocates_a_new_attempt_and_preserves_the_previous_one(
        tmp_path_factory, tmp_path):
    root, commit = _make_repo(tmp_path_factory.mktemp("lab-red2") / "lab", {
        "README.md": "# lab\n", "tests/test_red.py": FAILING_TEST})
    store = tmp_path / "store"
    first = _release("lab", root, commit, "v0.1.0-experimental.1", store)
    assert first.returncode == 1
    kept = _attempt_dirs(store)[0]
    fingerprint = br.sha256_file(kept / "release.json")
    second = _release("lab", root, commit, "v0.1.0-experimental.1", store)
    assert second.returncode == 1
    attempts = _attempt_dirs(store)
    assert len(attempts) == 2, "a retry did not allocate a new attempt"
    assert br.sha256_file(kept / "release.json") == fingerprint, (
        "a retry disturbed the previous attempt's evidence")


# --------------------------------------------------------------------------- #
# An ABORT mid-build is a different path from a gate that ran and failed
# --------------------------------------------------------------------------- #

def test_a_gate_that_exceeds_its_ceiling_is_an_execution_failure(tmp_path):
    """`run_gate`'s timeout branch -- one of the ways a run aborts mid-build.

    Nothing reached this branch before: both failure tests in this file exercise
    a gate that RUNS TO COMPLETION with a nonzero exit code, which is the
    qualification-failure path, not the abort path.
    """
    tokenizer = br.PathTokenizer()
    with pytest.raises(br.ExecutionError) as excinfo:
        br.run_gate("slow-gate", [sys.executable, "-c", "import time; time.sleep(120)"],
                    tmp_path, tmp_path, tmp_path, tokenizer, 2)
    assert "exceeded its 2s ceiling" in str(excinfo.value)
    assert not (tmp_path / "checks").exists(), (
        "a gate that never finished must not leave evidence claiming an exit code")


def test_a_gate_that_cannot_be_launched_is_an_execution_failure(tmp_path):
    """`run_gate`'s launch-failure branch, the other same-shaped abort."""
    tokenizer = br.PathTokenizer()
    with pytest.raises(br.ExecutionError) as excinfo:
        br.run_gate("unlaunchable", [str(tmp_path / "no-such-tool.exe"), "--version"],
                    tmp_path, tmp_path, tmp_path, tokenizer, 60)
    assert "could not be launched" in str(excinfo.value)
    assert not (tmp_path / "checks").exists()


def test_a_run_that_aborts_mid_build_retains_and_names_the_partial_stage(
        tmp_path_factory, tmp_path):
    """Exit 1 from an ABORT must still retain diagnostics and PRINT their path.

    A toolkit source with no `tools/release.ps1` raises out of the middle of the
    build -- after the source gate has already run and written its evidence, and
    before any record, notes or SHA256SUMS exist. There is no complete payload to
    file under `.attempts/`, so the partial build is retained under `.aborted/`
    and named in the output. Left unhandled it was an unreferenced
    `.staging-<uuid>` directory that nothing printed and nothing cleaned, while
    the runbook claimed every exit 1 retains its diagnostics and prints them.
    """
    if PWSH is None:
        pytest.skip("powershell is not available on PATH")
    root, commit = _make_repo(tmp_path_factory.mktemp("kit-no-entry") / "kit", {
        "README.md": "# kit\n", "tests/test_ok.py": TRIVIAL_TEST})
    store = tmp_path / "store"
    result = _release("toolkit", root, commit, "v0.1.0-baseline.1", store)
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert "no tools/release.ps1" in output, output

    aborted = sorted(p for p in (store / ".aborted").iterdir() if p.is_dir())
    assert len(aborted) == 1, aborted
    assert str(aborted[0]) in output, (
        "an unnamed retained directory is a leak, not a diagnostic")
    assert (aborted[0] / "source.zip").is_file(), (
        "the partial build keeps the archive it had already written")
    assert (aborted[0] / "checks" / "source-pytest.txt").is_file(), (
        "the gate evidence produced before the abort is retained")
    assert not (aborted[0] / "release.json").exists(), (
        "a partial build must not be dressed up as a complete one")
    assert not (store / "skill-mesh" / "v0.1.0-baseline.1").exists(), (
        "an aborted run must not reserve the version name")
    assert not _attempt_dirs(store), (
        "an attempt is a COMPLETE payload; a partial build is not one")
    assert not [p for p in (store / "skill-mesh").iterdir()
                if p.name.startswith(".staging-")], (
        "the staging directory was left behind unreferenced")


def test_a_second_aborted_run_preserves_the_first_partial_build(
        tmp_path_factory, tmp_path):
    """Nothing is deleted automatically -- including a previous abort's evidence."""
    if PWSH is None:
        pytest.skip("powershell is not available on PATH")
    root, commit = _make_repo(tmp_path_factory.mktemp("kit-no-entry2") / "kit", {
        "README.md": "# kit\n", "tests/test_ok.py": TRIVIAL_TEST})
    store = tmp_path / "store"
    assert _release("toolkit", root, commit, "v0.1.0-baseline.1", store).returncode == 1
    first = sorted(p for p in (store / ".aborted").iterdir() if p.is_dir())[0]
    fingerprint = br.sha256_file(first / "source.zip")
    assert _release("toolkit", root, commit, "v0.1.0-baseline.1", store).returncode == 1
    kept = sorted(p for p in (store / ".aborted").iterdir() if p.is_dir())
    assert len(kept) == 2, "a retry did not allocate its own aborted directory"
    assert br.sha256_file(first / "source.zip") == fingerprint, (
        "a retry disturbed the previous abort's retained bytes")


def test_a_publish_collision_files_a_complete_payload_as_an_attempt(
        lab_repo, tmp_path, monkeypatch, capsys):
    """`.attempts/` vs `.aborted/` describes the CONTENTS, not the error.

    Losing the race for a version directory happens AFTER the build finished:
    record, notes, receipt, SHA256SUMS and every evidence file are already
    written when the rename is attempted. Filing that under `.aborted/` would
    tell an operator to expect a directory that "may have no release.json" while
    a complete one is sitting there.

    Driven in-process because the race cannot be provoked from outside: the
    version directory has to appear BETWEEN the pre-flight check and the publish
    rename, which is exactly what the patched rename simulates.
    """
    root, commit = lab_repo
    store = tmp_path / "store"
    final = store / "skill-mesh-lab" / "v0.1.0-experimental.1"
    real_rename = br.os.rename

    def racing_rename(src, dst):
        if Path(dst) == final:
            Path(dst).mkdir(parents=True, exist_ok=True)   # the other process won
            raise FileExistsError(17, "simulated concurrent creation", str(dst))
        return real_rename(src, dst)

    monkeypatch.setattr(br.os, "rename", racing_rename)
    code = br.main(["lab", "--source-root", str(root), "--source-commit", commit,
                    "--version", "v0.1.0-experimental.1", "--store", str(store),
                    "--python-exe", sys.executable])
    err = capsys.readouterr().err

    assert code == br.EXIT_INPUT, err
    aborted = store / ".aborted"
    assert not aborted.is_dir() or not list(aborted.iterdir()), (
        "a COMPLETE payload was filed as an aborted partial build")
    attempts = _attempt_dirs(store)
    assert len(attempts) == 1, "the complete payload was not retained as an attempt"
    for name in ("release.json", "release-notes.md", "SHA256SUMS", "source.zip",
                 "receipt.json"):
        assert (attempts[0] / name).is_file(), (
            "the retained attempt is missing %s, so it was not complete" % name)
    assert "COLLISION" in err and "COMPLETE" in err
    assert str(attempts[0]) in err, (
        "the failure message does not name where the complete build was kept")
    assert "partial" not in err.lower(), (
        "the operator is still told to expect a partial build")


def _blocked_lab(tmp_path_factory, name):
    """A lab source whose own suite is red -- so the run takes the ATTEMPT path.

    A green lab release is retained as a release (INCOMPLETE lab is exit 0), so a
    red suite is what routes a run through the non-QUALIFIED retention branch,
    which is the COMMON one: every INCOMPLETE/BLOCKED release comes through it.
    """
    return _make_repo(tmp_path_factory.mktemp(name) / "lab", {
        "README.md": "# lab\n", "tests/test_red.py": FAILING_TEST})


def test_a_failed_attempt_rename_still_files_the_complete_payload_as_an_attempt(
        tmp_path_factory, tmp_path, monkeypatch, capsys):
    """The COMMON retention path, when its move fails once.

    The publish-collision branch was taught to keep a complete payload out of
    `.aborted/`; this is the other, far more frequent branch -- every
    INCOMPLETE/BLOCKED release -- where a transient rename failure (an antivirus
    handle, a stale leftover directory, WinError 183) used to drop the run into
    perform_release's catch-all and file a payload with release.json, notes,
    receipt and SHA256SUMS under `.aborted/`, the one directory documented as
    "may have no release.json at all".

    The fix is the funnel, not the branch: whichever route reaches it, the
    destination is chosen by reading `release.json` off the stage.
    """
    root, commit = _blocked_lab(tmp_path_factory, "lab-attempt-race")
    store = tmp_path / "store"
    real_rename = br.os.rename
    failures = {"n": 0}

    def flaky_rename(src, dst):
        if ".attempts" in str(dst) and failures["n"] == 0:
            failures["n"] += 1
            raise OSError(183, "simulated transient lock on the attempts subtree")
        return real_rename(src, dst)

    monkeypatch.setattr(br.os, "rename", flaky_rename)
    code = br.main(["lab", "--source-root", str(root), "--source-commit", commit,
                    "--version", "v0.1.0-experimental.1", "--store", str(store),
                    "--python-exe", sys.executable])
    err = capsys.readouterr().err

    assert failures["n"] == 1, "the flaky rename never fired; the test proved nothing"
    assert code == br.EXIT_EXEC, err
    aborted = store / ".aborted"
    assert not aborted.is_dir() or not list(aborted.iterdir()), (
        "a COMPLETE payload was filed as an aborted partial build")
    attempts = _attempt_dirs(store)
    assert len(attempts) == 1, "the complete payload was not re-filed as an attempt"
    for name in ("release.json", "release-notes.md", "SHA256SUMS", "source.zip",
                 "receipt.json"):
        assert (attempts[0] / name).is_file(), (
            "the retained attempt is missing %s, so it was not complete" % name)
    assert str(attempts[0]) in err, "the retained payload's path was not printed"
    assert "COMPLETE" in err and "PARTIAL" not in err


def test_a_complete_payload_is_never_announced_as_partial_when_no_move_succeeds(
        tmp_path_factory, tmp_path, monkeypatch, capsys):
    """The harsher case: BOTH moves fail, so nothing can leave the stage.

    Reported honestly rather than quietly: the payload keeps its staging path,
    that path is printed, and it is described as COMPLETE -- because it is. The
    invariant the runbook states is about `.aborted/`, and it holds here too:
    nothing was filed there.
    """
    root, commit = _blocked_lab(tmp_path_factory, "lab-attempt-stuck")
    store = tmp_path / "store"
    real_rename = br.os.rename

    def never_attempts(src, dst):
        if ".attempts" in str(dst):
            raise OSError(183, "simulated persistent lock on the attempts subtree")
        return real_rename(src, dst)

    monkeypatch.setattr(br.os, "rename", never_attempts)
    code = br.main(["lab", "--source-root", str(root), "--source-commit", commit,
                    "--version", "v0.1.0-experimental.1", "--store", str(store),
                    "--python-exe", sys.executable])
    err = capsys.readouterr().err

    assert code == br.EXIT_EXEC, err
    aborted = store / ".aborted"
    assert not aborted.is_dir() or not list(aborted.iterdir()), (
        "a COMPLETE payload was filed as an aborted partial build")
    assert not _attempt_dirs(store), "the attempts move was supposed to keep failing"
    stages = [p for p in (store / "skill-mesh-lab").iterdir()
              if p.name.startswith(".staging-")]
    assert len(stages) == 1, stages
    assert (stages[0] / "release.json").is_file(), "the payload is complete on disk"
    assert str(stages[0]) in err, "the surviving stage's path was not printed"
    assert "COMPLETE" in err and "PARTIAL" not in err, (
        "a complete payload was announced to the operator as a partial build")


def test_the_retention_bucket_is_read_off_the_stage_not_from_the_error(tmp_path):
    """One decision function, so every route into the two directories agrees.

    Field-agnostic on purpose: it grades stage_bucket() by CONTENTS, so a future
    caller that files a stage through some third route inherits the invariant
    without this test naming that route.
    """
    partial = tmp_path / "partial"
    (partial / "checks").mkdir(parents=True)
    assert br.stage_bucket(partial) == (".aborted", "aborted")

    complete = tmp_path / "complete"
    complete.mkdir()
    (complete / br.STAGE_COMPLETION_MARKER).write_text("{}", encoding="utf-8")
    assert br.stage_bucket(complete) == (".attempts", "attempt")


# --------------------------------------------------------------------------- #
# Toolkit: the existing toolchain, all profiles, real artifact verification
# --------------------------------------------------------------------------- #

def test_toolkit_release_runs_the_pinned_sources_release_entry(kit_qualified):
    store, release_dir, result, _ = kit_qualified
    assert result.returncode == 0, result.stdout + result.stderr
    record = _record(release_dir)
    assert record["product"] == "skill-mesh"
    assert record["providers"] == ["claude", "codex", "gpt"], record["providers"]
    for provider in br.TOOLKIT_PROVIDERS:
        assert (release_dir / "dist" / provider).is_dir()
    assert (release_dir / "CHECKSUMS.txt").is_file(), (
        "the ORIGINAL normalized manifest produced by release.ps1 must be retained")
    packet = json.loads((release_dir / "public/packet.json").read_text(encoding="utf-8"))
    assert "dist/" in packet["include"]
    assert "CHECKSUMS.txt" in packet["sanitization"]["scanned"]
    for provider in br.TOOLKIT_PROVIDERS:
        assert "dist/%s/SKILL.md" % provider in packet["sanitization"]["scanned"]


def test_toolkit_qualification_requires_all_four_gates(kit_qualified):
    _, release_dir, _, commit = kit_qualified
    record = _record(release_dir)
    assert record["qualification"] == "QUALIFIED", record["qualification_reasons"]
    names = {row["name"] for row in record["checks"] if row["execution"] == "native"}
    assert {"source-pytest", "staged-release", "artifact-verification"} <= names
    assert all(row["exit_code"] == 0 for row in record["checks"]
               if row["execution"] == "native")
    assert record["reviews"] and record["reviews"][0]["verdict"] == "PASS"
    assert record["reviews"][0]["source_commit"] == commit
    assert record["reviews"][0]["evidence"].startswith("reviews/")
    assert (release_dir / record["reviews"][0]["evidence"]).is_file()


def test_checksums_txt_is_a_separate_manifest_from_the_raw_artifact_hashes(kit_qualified):
    """Normalized payload checksums and raw whole-file hashes are separate concepts.

    CHECKSUMS.txt is the manifest release.ps1 produced over dist/, retained
    verbatim. release.json's `artifacts` is a RAW whole-file hash over every
    retained byte -- a wider set that includes CHECKSUMS.txt itself, which the
    normalized manifest can never cover.
    """
    _, release_dir, _, _ = kit_qualified
    listed = {}
    for line in (release_dir / "CHECKSUMS.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        digest, _, rel = line.partition("  ")
        listed[rel.strip()] = digest.strip()
    assert listed and all(rel.startswith("dist/") for rel in listed), listed
    assert "CHECKSUMS.txt" not in listed, "the normalized manifest never hashes itself"

    record = _record(release_dir)
    artifacts = {entry["path"]: entry["sha256"] for entry in record["artifacts"]}
    assert "CHECKSUMS.txt" in artifacts, (
        "the normalized manifest is itself a raw-hashed retained artifact")
    assert set(listed) < set(artifacts), (
        "every normalized dist/ entry is also raw-hashed, and the raw set is wider")
    for rel, digest in listed.items():
        assert artifacts[rel] == digest, (
            "a dist/ artifact was altered between release.ps1 and retention: %s" % rel)


def test_artifact_verification_grades_the_retained_bytes_not_the_scratch_stage(
        kit_qualified, tmp_path):
    """The gate must verify what is KEPT, against the manifest release.ps1 produced.

    `artifacts` and `SHA256SUMS` are computed FROM the retained copy, so they can
    only ever agree with it -- a fault between the release stage and the retained
    directory is invisible to them, and the stage itself is deleted at exit so
    nothing re-checks it later. Only a gate that re-hashes the RETAINED dist/
    against release.ps1's own CHECKSUMS.txt can see that class of fault.

    So: the recorded gate is pinned to the retained tree, then replayed exactly as
    recorded (green), then replayed against a copy carrying the corruption it
    exists to catch (red). The same command is also what the notes hand a
    consumer, so this grades the published verification path too.
    """
    _, release_dir, _, _ = kit_qualified
    record = _record(release_dir)
    gate = [row for row in record["checks"] if row["name"] == "artifact-verification"][0]
    assert gate["exit_code"] == 0
    assert gate["execution"] == "native"
    assert gate["cwd"] == "<release-dir>", (
        "the gate must run in the retained release, not in the scratch stage that "
        "is rmtree'd at exit: %s" % gate["cwd"])
    assert gate["argv"][1:4] == ["verify-artifacts.py", "CHECKSUMS.txt", "."], gate["argv"]
    assert "<stage-dir>" not in " ".join(gate["argv"]), (
        "verifying the pre-copy stage originals certifies bytes nobody retains")

    replay = [sys.executable] + gate["argv"][1:]
    good = subprocess.run(replay, cwd=str(release_dir), capture_output=True, text=True)
    assert good.returncode == 0, good.stdout + good.stderr

    copy = tmp_path / "copy-fault"
    shutil.copytree(release_dir, copy)
    victim = copy / "dist" / "claude" / "SKILL.md"
    victim.write_bytes(victim.read_bytes() + b"corrupted between stage and store\n")
    bad = subprocess.run(replay, cwd=str(copy), capture_output=True, text=True)
    assert bad.returncode == 1, (
        "the gate passed over a retained artifact that no longer matches the "
        "manifest release.ps1 produced\n" + bad.stdout + bad.stderr)
    assert "MISMATCH" in bad.stdout


def test_toolkit_without_a_cross_family_review_is_never_qualified(kit_unqualified):
    """All gates green is NOT enough: the charter invariant is not softened."""
    store, result, _ = kit_unqualified
    assert result.returncode == 1, result.stdout + result.stderr
    assert not (store / "skill-mesh" / "v0.1.0-baseline.1").exists()
    attempts = _attempt_dirs(store)
    assert len(attempts) == 1
    record = _record(attempts[0])
    assert record["qualification"] == "INCOMPLETE"
    assert any("cross-family review" in reason for reason in record["qualification_reasons"])
    assert all(row["exit_code"] == 0 for row in record["checks"]), (
        "the gates were green; only the review was missing")
    assert (attempts[0] / "source.zip").is_file()
    assert (attempts[0] / "dist" / "claude").is_dir()


def test_failed_release_entry_is_blocked_and_keeps_the_source_archive(
        tmp_path_factory, tmp_path):
    if PWSH is None:
        pytest.skip("powershell is not available on PATH")
    root, commit = _make_repo(tmp_path_factory.mktemp("kit-red") / "kit", {
        "README.md": "# kit\n",
        "tests/test_ok.py": TRIVIAL_TEST,
        "tools/release.ps1": FAILING_RELEASE_PS1,
    })
    store = tmp_path / "store"
    proofs = _write_proofs(tmp_path / "proofs", [_review_proof(commit)])
    result = _release("toolkit", root, commit, "v0.1.0-baseline.1", store, proofs=proofs)
    assert result.returncode == 1, result.stdout + result.stderr
    assert not (store / "skill-mesh" / "v0.1.0-baseline.1").exists()
    attempt = _attempt_dirs(store)[0]
    record = _record(attempt)
    assert record["qualification"] == "BLOCKED", record["qualification_reasons"]
    assert record["providers"] == []
    assert (attempt / "source.zip").is_file(), "a failed gate keeps the source archive"
    assert (attempt / "checks" / "staged-release.txt").is_file()


def test_source_checks_are_recorded_independently_of_packaging_success(
        tmp_path_factory, tmp_path):
    """The root suite result is retained even when packaging never produced a profile."""
    if PWSH is None:
        pytest.skip("powershell is not available on PATH")
    root, commit = _make_repo(tmp_path_factory.mktemp("kit-red2") / "kit", {
        "README.md": "# kit\n",
        "tests/test_ok.py": TRIVIAL_TEST,
        "tools/release.ps1": FAILING_RELEASE_PS1,
    })
    store = tmp_path / "store"
    result = _release("toolkit", root, commit, "v0.1.0-baseline.1", store)
    assert result.returncode == 1
    record = _record(_attempt_dirs(store)[0])
    source_gate = [row for row in record["checks"] if row["name"] == "source-pytest"][0]
    assert source_gate["exit_code"] == 0, (
        "the source check must be recorded even though packaging failed")
    assert source_gate["source_commit"] == commit


# --------------------------------------------------------------------------- #
# Proof imports: bind, mark, never silently drop
# --------------------------------------------------------------------------- #

def test_malformed_proofs_file_is_an_input_error(lab_repo, tmp_path):
    root, commit = lab_repo
    bad = tmp_path / "proofs.json"
    bad.write_text("{not json", encoding="utf-8")
    result = _release("lab", root, commit, "v1", tmp_path / "store", proofs=bad)
    assert result.returncode == 2
    assert "not valid JSON" in result.stderr


def test_proofs_with_an_unknown_top_level_key_is_an_input_error(lab_repo, tmp_path):
    root, commit = lab_repo
    bad = tmp_path / "proofs.json"
    bad.write_text(json.dumps({"reviews": [], "verdicts": []}), encoding="utf-8")
    result = _release("lab", root, commit, "v1", tmp_path / "store", proofs=bad)
    assert result.returncode == 2
    assert "unknown top-level key" in result.stderr


def test_proofs_missing_a_required_review_field_is_an_input_error(lab_repo, tmp_path):
    root, commit = lab_repo
    row = _review_proof(commit)
    del row["conversation_id"]
    proofs = _write_proofs(tmp_path / "proofs", [row])
    result = _release("lab", root, commit, "v1", tmp_path / "store", proofs=proofs)
    assert result.returncode == 2
    assert "is missing conversation_id" in result.stderr


def test_proofs_carrying_an_absolute_user_path_is_an_input_error(lab_repo, tmp_path):
    """release.json is public, so a proof may not smuggle a machine path into it.

    Built at runtime: this file is itself swept by the repository's committed
    absolute-path gate, so it must not carry a literal instance of the pattern.
    """
    drive = "C" + ":"
    root, commit = lab_repo
    row = _review_proof(commit, conversation_id=drive + "/Users/someone/session")
    proofs = _write_proofs(tmp_path / "proofs", [row])
    result = _release("lab", root, commit, "v1", tmp_path / "store", proofs=proofs)
    assert result.returncode == 2
    assert "absolute user path" in result.stderr


@pytest.mark.parametrize("planted", ["/home/someone/session", "/Users/someone/session"])
def test_proofs_carrying_a_posix_home_path_is_an_input_error(lab_repo, tmp_path, planted):
    """The widened detector, reached through the PRODUCTION entry point.

    The unit test above grades `scan_private_paths`; this one proves the same
    widening is what `load_proofs` actually applies when a real invocation hands
    it a document. release.json is public whichever way the host spells a home
    directory, so the refusal is the same.
    """
    root, commit = lab_repo
    row = _review_proof(commit, conversation_id=planted)
    proofs = _write_proofs(tmp_path / "proofs", [row])
    result = _release("lab", root, commit, "v1", tmp_path / "store", proofs=proofs)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "absolute user path" in result.stderr
    assert not (tmp_path / "store" / "skill-mesh-lab").exists(), (
        "a refused proofs document must not leave a product directory behind")


def test_a_lone_surrogate_in_proofs_is_refused_at_the_boundary(lab_repo, tmp_path):
    """Text UTF-8 cannot encode is refused as INPUT, not discovered at a sink.

    `json.loads` turns a `\\udNNN` escape in any `--proofs` string field into a
    real lone surrogate. No markdown neutralizer removes one -- md_untrusted,
    md_code and md_inline escape STRUCTURE, not encodability -- so it used to
    reach `release-notes.md`'s `write_text` and raise UnicodeEncodeError, which
    is a ValueError and therefore caught by none of main()'s handlers: a raw
    traceback, and the documented {0,1,2} exit-code contract gone with it.

    Refused rather than transcoded on purpose: this tool records what the caller
    supplied, and silently substituting U+FFFD would publish something else.
    """
    root, commit = lab_repo
    proof_dir = tmp_path / "proofs"
    proof_dir.mkdir()
    (proof_dir / "review-0001.md").write_text(GENERIC_EVIDENCE, encoding="utf-8")
    # Written as a JSON ESCAPE in the raw bytes -- the file itself stays valid
    # UTF-8, which is exactly why the boundary has to look at the PARSED values.
    (proof_dir / "proofs.json").write_text(
        json.dumps({"checks": [], "reviews": [_review_proof(commit)]}).replace(
            '"PASS"', '"PASS\\ud800"'),
        encoding="utf-8", newline="\n")
    result = _release("lab", root, commit, "v1", tmp_path / "store",
                      proofs=proof_dir / "proofs.json")
    output = result.stdout + result.stderr
    assert result.returncode == 2, output
    assert "UTF-8 cannot encode" in output, output
    assert "Traceback" not in output, "the exit-code contract leaked a traceback"
    assert not (tmp_path / "store" / "skill-mesh-lab").exists()


def test_the_unencodable_boundary_also_covers_the_invocation_argv(
        lab_repo, tmp_path, capsys):
    """The OTHER caller boundary. Driven in-process: a surrogate cannot survive
    a subprocess argument list, which is precisely why the check has to sit in
    `prepare` rather than in the shell.

    On POSIX `sys.argv` yields a lone surrogate for any undecodable argument
    byte (surrogateescape), and the whole invocation argv is recorded in
    `receipt.json`. The refusal names WHICH argument, before anything is built.
    """
    root, commit = lab_repo
    store = tmp_path / "store"
    code = br.main(["lab", "--source-root", str(root), "--source-commit", commit,
                    "--version", "v1", "--store", str(store),
                    "--python-exe", sys.executable,
                    "--attest-reviews", "A. Operator \ud800"])
    err = capsys.readouterr().err
    assert code == br.EXIT_INPUT, err
    assert "UTF-8 cannot encode" in err and "argv[" in err, err
    assert not store.exists() or not any(store.iterdir()), (
        "nothing may be built before the boundary check runs"
    )


def test_the_unencodable_check_is_scoped_honestly():
    """What reject_unencodable() does and does not reach, asserted not assumed.

    It guards the two CALLER boundaries. Text this tool CAPTURES cannot carry a
    surrogate: `run()` decodes with `errors="backslashreplace"`, which emits
    ASCII. Filesystem-supplied names are NOT covered, and nothing claims they
    are -- main()'s UnicodeError clause turns that residue into exit 1 with a
    message instead of a traceback, which is why that clause has to exist.
    """
    with pytest.raises(br.InputError) as caught:
        br.reject_unencodable("ok-\ud800-tail", "argv[7]")
    assert "argv[7]" in str(caught.value)
    assert "UTF-8 cannot encode" in str(caught.value)
    assert br.reject_unencodable("plain ascii", "argv[0]") == "plain ascii"
    assert br.reject_unencodable("café \U0001f600", "argv[1]"), (
        "ordinary non-ASCII text is encodable and must not be refused")
    assert "\\ud800" in "x\ud800".encode("utf-8", "backslashreplace").decode("ascii"), (
        "run()'s decoder emits an ASCII escape, so captured output cannot carry one")
    assert issubclass(UnicodeEncodeError, UnicodeError)
    assert not issubclass(UnicodeEncodeError, OSError), (
        "the dedicated UnicodeError clause in main() is what keeps this exit "
        "code honest; OSError would not catch it")


@pytest.mark.parametrize("cwd", ["/opt/build/checkout", "D" + ":/build/checkout"])
def test_an_absolute_check_cwd_in_proofs_is_an_input_error(lab_repo, tmp_path, cwd):
    """A recorded cwd is relative to the disposable checkout; an absolute one is refused.

    Deliberately NOT a home path: that would be caught one layer earlier by the
    public-artifact scan, and this test targets `reject_absolute` itself. Both
    POSIX-absolute and drive-absolute forms are covered.
    """
    root, commit = lab_repo
    check = {"argv": ["python", "-m", "pytest"], "exit_code": 0,
             "cwd": cwd, "source_commit": commit,
             "evidence": "check-0000.txt"}
    directory = tmp_path / "proofs"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "check-0000.txt").write_text("ok\n", encoding="utf-8", newline="\n")
    path = directory / "proofs.json"
    path.write_text(json.dumps({"checks": [check], "reviews": []}, indent=2),
                    encoding="utf-8", newline="\n")
    result = _release("lab", root, commit, "v1", tmp_path / "store", proofs=path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "checks[0].cwd" in result.stderr


def test_an_unresolvable_python_exe_is_an_input_error(lab_repo, tmp_path):
    root, commit = lab_repo
    result = _cli("lab", "--source-root", root, "--source-commit", commit,
                  "--version", "v1", "--store", tmp_path / "store",
                  "--python-exe", "no-such-interpreter-9f3a", timeout=180)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "was not found" in result.stderr


def test_a_version_directory_without_a_record_is_an_input_error(lab_repo, tmp_path):
    """A half-written or foreign directory is a collision, never a place to write."""
    root, commit = lab_repo
    store = tmp_path / "store"
    squatter = store / "skill-mesh-lab" / "v0.1.0-experimental.1"
    squatter.mkdir(parents=True)
    (squatter / "stray.txt").write_text("not a release\n", encoding="utf-8", newline="\n")
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "carries no release.json" in result.stderr
    assert (squatter / "stray.txt").is_file(), "the foreign directory was disturbed"


def test_missing_proof_evidence_is_recorded_as_incomplete_not_dropped(lab_repo, tmp_path):
    root, commit = lab_repo
    proofs = _write_proofs(tmp_path / "proofs",
                           [_review_proof(commit, evidence="absent.md")],
                           evidence_names=())
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store, proofs=proofs)
    assert result.returncode == 0, result.stdout + result.stderr
    record = _record(store / "skill-mesh-lab" / "v0.1.0-experimental.1")
    assert record["qualification"] == "INCOMPLETE"
    assert len(record["reviews"]) == 1, "the unresolvable row was silently dropped"
    assert record["reviews"][0]["import_status"] == "missing-evidence"
    assert any("could not be resolved" in gap for gap in record["known_gaps"])


def test_proof_bound_to_another_source_commit_is_marked_and_never_relabelled(
        lab_repo, tmp_path):
    root, commit = lab_repo
    other = "b" * 40
    proofs = _write_proofs(tmp_path / "proofs", [_review_proof(commit, source_commit=other)])
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store, proofs=proofs)
    assert result.returncode == 0, result.stdout + result.stderr
    record = _record(store / "skill-mesh-lab" / "v0.1.0-experimental.1")
    assert record["qualification"] == "INCOMPLETE", (
        "historical proof must never be relabelled as current-source proof")
    assert record["reviews"][0]["source_commit"] == other
    assert record["reviews"][0]["import_status"] == "source-mismatch"
    assert any("never relabelled" in gap for gap in record["known_gaps"])


def test_imported_check_evidence_is_copied_in_and_marked_as_imported(lab_repo, tmp_path):
    root, commit = lab_repo
    proof_dir = tmp_path / "proofs"
    proof_dir.mkdir()
    (proof_dir / "old-run.txt").write_text("historical run output\n", encoding="utf-8")
    (proof_dir / "proofs.json").write_text(json.dumps({
        "checks": [{
            "argv": ["<python-exe>", "-m", "pytest"],
            "exit_code": 0,
            "cwd": ".",
            "source_commit": commit,
            "evidence": "old-run.txt",
            "name": "historical-pytest",
        }],
        "reviews": [],
    }), encoding="utf-8")
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store,
                      proofs=proof_dir / "proofs.json")
    assert result.returncode == 0, result.stdout + result.stderr
    release_dir = store / "skill-mesh-lab" / "v0.1.0-experimental.1"
    record = _record(release_dir)
    imported = [row for row in record["checks"] if row["execution"] == "imported"]
    assert len(imported) == 1
    assert imported[0]["import_status"] == "imported"
    assert (release_dir / imported[0]["evidence"]).is_file(), (
        "imported evidence must be copied in for local recovery")
    native = [row for row in record["checks"] if row["execution"] == "native"]
    assert native, "an import must never displace the natively executed gate"


def _qualifying_row(commit, **overrides):
    """A row that has already been imported, cleared the tripwire, AND is attested.

    All three are separately required: `import_status` proves the evidence
    resolved, `evidence_consistency` is the NEGATIVE-ONLY tripwire (its
    "consistent" value upgrades nothing by itself), and `attested_by` is the only
    POSITIVE signal -- the separate `--attest-reviews` act.
    """
    row = _review_proof(commit, **overrides)
    row["import_status"] = "imported"
    row["evidence_consistency"] = "consistent"
    row["attested_by"] = ATTESTING_PARTY
    return row


@pytest.mark.parametrize("override, expectation", [
    ({"independent": False}, "not marked independent"),
    ({"verdict": "FAIL"}, "not PASS"),
    ({"cross_family": False}, "cross_family"),
    ({"resolved_model": None, "identity_waiver": None}, "identity_waiver"),
    ({"resolution_status": " "}, "resolution_status"),
    ({"source_commit": "b" * 40}, "binds a different source commit"),
    ({"conversation_id": "   "}, "carries no conversation_id"),
])
def test_a_review_missing_a_charter_element_does_not_qualify(override, expectation):
    row = _qualifying_row("a" * 40, **override)
    ok, why = br.review_qualifies(row, "a" * 40)
    assert ok is False
    assert expectation in why


def test_a_complete_review_qualifies():
    ok, why = br.review_qualifies(_qualifying_row("a" * 40), "a" * 40)
    assert ok is True, why


def test_a_named_identity_waiver_substitutes_for_an_observed_resolved_model():
    """The charter's 'any waiver is explicit and named' escape hatch, on its TRUE side.

    `review_qualifies` encodes identity as `resolved_model OR identity_waiver`.
    Every other row in this file takes the resolved_model disjunct, so without
    this case the waiver disjunct is 0%-covered on the side that matters: an `or`
    flipped to an `and`, or the waiver branch dropped, would still pass.
    Calibrated against its own neighbours -- BOTH absent must still refuse, so a
    pass here cannot come from the guard having been removed altogether.
    """
    waived = _qualifying_row("a" * 40, resolved_model=None,
                             identity_waiver="waived: host reports no model id (J. Owner)")
    ok, why = br.review_qualifies(waived, "a" * 40)
    assert ok is True, why

    neither = _qualifying_row("a" * 40, resolved_model=None, identity_waiver=None)
    refused, why = br.review_qualifies(neither, "a" * 40)
    assert refused is False and "identity_waiver" in why, (
        "the identity guard must still refuse when neither disjunct is present")


def test_the_named_waiver_is_the_claim_the_tripwire_grades(tmp_path):
    """The waiver branch of `review_claim_needles`, on its TRUE side.

    With no resolved model, the needle set must carry the NAMED WAIVER instead --
    otherwise a waived row would be graded against one claim fewer than it makes.
    """
    row = _review_proof("a" * 40, resolved_model=None,
                        identity_waiver="waived-by-j-owner")
    labels = dict(br.review_claim_needles(row))
    assert labels.get("the named identity waiver") == "waived-by-j-owner"
    assert "the resolved model identity" not in labels

    evidence = tmp_path / "review-0001.md"
    evidence.write_text(_attestation(row), encoding="utf-8", newline="\n")
    assert br.check_evidence_consistency(row, evidence)[0] == "consistent"

    silent = tmp_path / "silent.md"
    silent.write_text(_attestation(row).replace("waived-by-j-owner", ""),
                      encoding="utf-8", newline="\n")
    status, why = br.check_evidence_consistency(row, silent)
    assert status == "unstated" and "the named identity waiver" in why, (
        "a document that never names the waiver must not read as consistent")


@pytest.mark.parametrize("consistency", [None, "unstated", "contradicted", "no-evidence",
                                         "evidence-unreadable"])
def test_a_review_the_tripwire_fired_on_never_qualifies(consistency):
    """Fail-closed, including when the field is absent entirely.

    The tripwire is negative-only, so this is the direction it is allowed to
    decide: any value other than "consistent" -- and an unknown/absent value --
    blocks, even with the attestation present.
    """
    row = _qualifying_row("a" * 40)
    if consistency is None:
        del row["evidence_consistency"]
    else:
        row["evidence_consistency"] = consistency
    assert row["attested_by"], "the attestation is present; the tripwire is what refuses"
    ok, why = br.review_qualifies(row, "a" * 40)
    assert ok is False
    assert "not stated by, the evidence it cites" in why


@pytest.mark.parametrize("attested_by", [None, "", "   "])
def test_a_review_nobody_attested_never_qualifies(attested_by):
    """The positive signal is the NAMED ACT, and nothing else can stand in for it.

    Calibrated: the identical row WITH a name qualifies, so the refusal is
    attributable to the missing attestation and to nothing else in the row.
    """
    row = _qualifying_row("a" * 40)
    assert br.review_qualifies(row, "a" * 40)[0] is True, "green arm of the calibration"

    if attested_by is None:
        del row["attested_by"]
    else:
        row["attested_by"] = attested_by
    ok, why = br.review_qualifies(row, "a" * 40)
    assert ok is False
    assert "--attest-reviews" in why and "attested_by" in why


def test_a_consistent_tripwire_result_upgrades_nothing_on_its_own():
    """The governing invariant, asserted directly.

    "consistent" is the BEST result the text comparison can produce, and it is
    still not a positive signal: a row carrying it, with every charter element
    green, is refused until a named party attests. Anything else would be the
    round-1 design -- one author's self-consistency promoted to verification.
    """
    row = _qualifying_row("a" * 40)
    del row["attested_by"]
    assert row["evidence_consistency"] == "consistent"
    assert br.review_qualifies(row, "a" * 40)[0] is False


def test_an_omitted_cross_family_key_never_qualifies():
    """OMITTED is not a softer FALSE: the charter guard fails closed on SILENCE.

    `cross_family` is OPTIONAL in the proofs schema -- it is absent from
    `_REVIEW_KEYS` and `load_proofs` never requires it -- so a caller who simply
    leaves the field out reaches `review_qualifies` with `None`, not `False`.
    That is the ONLY input on which `is not True` and `== False` differ, and it is
    a plausible operator mistake rather than a contrived one, which is why the
    guard is written the way it is: narrowing the comparison would make the
    charter's central invariant optional-by-omission.

    Calibrated on the key alone -- the identical row WITH `cross_family: True`
    qualifies, so the refusal is attributable to the missing claim and to nothing
    else in the row -- and the explicit-false arm is asserted alongside it so a
    pass here can never come from the guard having been deleted outright.
    """
    green = _qualifying_row("a" * 40)
    assert br.review_qualifies(green, "a" * 40)[0] is True, "green arm of the calibration"

    silent = _qualifying_row("a" * 40)
    del silent["cross_family"]
    assert "cross_family" not in silent, "the key must be ABSENT, not false"
    ok, why = br.review_qualifies(silent, "a" * 40)
    assert ok is False, "a review that makes no cross-family claim qualified anyway"
    assert "cross_family" in why

    explicit = _qualifying_row("a" * 40, cross_family=False)
    assert br.review_qualifies(explicit, "a" * 40)[0] is False, (
        "and an explicit false must keep refusing too")


def test_an_omitted_cross_family_key_leaves_the_tripwire_silent(tmp_path):
    """Proves the omitted row REACHES the charter guard instead of an earlier one.

    `review_claim_needles` grades the two host families only when the row CLAIMS
    them, so a row that omits `cross_family` is graded against one claim fewer
    and its evidence still reads `consistent`. That is exactly what makes the
    test above meaningful: the omission has to be refused by the cross-family
    guard in `review_qualifies`, not incidentally by a tripwire firing for an
    unrelated reason.
    """
    row = _review_proof("a" * 40)
    del row["cross_family"]
    labels = dict(br.review_claim_needles(row))
    for family in br.CROSS_FAMILY_TOKENS:
        assert "the %s host family" % family not in labels

    evidence = tmp_path / "review-0001.md"
    evidence.write_text(_attestation(row), encoding="utf-8", newline="\n")
    assert br.check_evidence_consistency(row, evidence)[0] == "consistent", (
        "the tripwire, not the charter guard, would be doing the refusing")


def test_an_omitted_cross_family_key_is_only_incomplete_end_to_end(lab_repo, tmp_path):
    """The same omission through the PRODUCTION path, CALIBRATED on the key alone.

    Both arms attach a review with `--proofs` and name a party with
    `--attest-reviews`; the ONLY difference is whether the row carries
    `cross_family`. The red arm additionally asserts `attested_by` present and
    `evidence_consistency == "consistent"`, so the INCOMPLETE verdict is provably
    the cross-family guard rather than the attestation requirement or the
    tripwire -- and the record keeps the claim as an explicit `null`.
    """
    root, commit = lab_repo

    silent_row = _review_proof(commit)
    del silent_row["cross_family"]
    silent_store = tmp_path / "silent-store"
    silent_proofs = _write_proofs(tmp_path / "silent-proofs", [silent_row])
    silent = _release("lab", root, commit, "v0.1.0-experimental.1", silent_store,
                      proofs=silent_proofs, attest=ATTESTING_PARTY)
    assert silent.returncode == 0, silent.stdout + silent.stderr
    silent_dir = silent_store / "skill-mesh-lab" / "v0.1.0-experimental.1"
    silent_record = _record(silent_dir)
    review = silent_record["reviews"][0]
    assert review["attested_by"] == ATTESTING_PARTY, "the attestation IS present"
    assert review["evidence_consistency"] == "consistent", "the tripwire IS silent"
    assert review["cross_family"] is None, (
        "an unmade claim must be recorded as null, never defaulted to a claim")
    assert silent_record["qualification"] == "INCOMPLETE", (
        "a review that never claimed cross-family qualified the release")
    assert any("cross_family" in reason
               for reason in silent_record["qualification_reasons"])
    assert (silent_dir / "source.zip").is_file(), "the archive is retained regardless"

    claimed_store = tmp_path / "claimed-store"
    claimed_proofs = _write_proofs(tmp_path / "claimed-proofs", [_review_proof(commit)])
    claimed = _release("lab", root, commit, "v0.1.0-experimental.1", claimed_store,
                       proofs=claimed_proofs, attest=ATTESTING_PARTY)
    assert claimed.returncode == 0, claimed.stdout + claimed.stderr
    claimed_record = _record(claimed_store / "skill-mesh-lab" / "v0.1.0-experimental.1")
    assert claimed_record["qualification"] == "QUALIFIED", (
        "green arm of the calibration: %s" % claimed_record["qualification_reasons"])


# --------------------------------------------------------------------------- #
# The evidence-consistency tripwire -- NEGATIVE ONLY
#
# Both the --proofs row and the document it cites are authored by the same
# caller, so comparing them can FALSIFY a claim and can never establish one.
# Every test below therefore asserts one of two things: that a falsification is
# caught, or that a clean comparison still does not qualify anything.
# --------------------------------------------------------------------------- #

def test_the_tripwire_is_silent_when_the_evidence_states_every_claim(tmp_path):
    row = _review_proof("a" * 40)
    evidence = tmp_path / "review-0001.md"
    evidence.write_text(_attestation(row), encoding="utf-8", newline="\n")
    status, why = br.check_evidence_consistency(row, evidence)
    assert status == "consistent", why
    assert "establishes nothing on its own" in why, (
        "the recorded reason must not read as corroboration")


@pytest.mark.parametrize("drop, missing", [
    ("{source_commit}", "the source commit it reviewed"),
    ("{conversation_id}", "its conversation id"),
    ("Verdict: {verdict}", "its verdict"),
    ("{resolved_model}", "the resolved model identity"),
    ("independent", "its independence"),
    ("Claude Code", "the claude host family"),
    ("Codex CLI", "the codex host family"),
])
def test_a_claim_the_evidence_does_not_state_is_unstated(tmp_path, drop, missing):
    """One claim removed at a time -- each is separately load-bearing.

    Nothing else changes, so a PASS here cannot come from the document being
    broken in general; it comes from exactly the claim that was taken out. The
    model ids are deliberately distinct from each other and from both family
    names, so no axis can be satisfied by another axis's text.
    """
    row = _review_proof("a" * 40, requested_model="requested-model-a",
                        resolved_model="resolved-model-b")
    body = REVIEW_ATTESTATION.replace(drop, "")
    evidence = tmp_path / "review-0001.md"
    evidence.write_text(body.format(**{
        key: ("" if row.get(key) is None else row.get(key, ""))
        for key in ("source_commit", "conversation_id", "requested_model",
                    "resolved_model", "resolution_status", "identity_waiver",
                    "verdict")}), encoding="utf-8", newline="\n")
    status, why = br.check_evidence_consistency(row, evidence)
    assert status == "unstated", why
    assert missing in why


def test_the_generic_placeholder_evidence_is_not_consistent(tmp_path):
    """The exact one-liner a caller would hand-write, refused on its content."""
    row = _review_proof("a" * 40)
    evidence = tmp_path / "review-0001.md"
    evidence.write_text(GENERIC_EVIDENCE, encoding="utf-8", newline="\n")
    status, why = br.check_evidence_consistency(row, evidence)
    assert status == "unstated", why
    assert "the source commit it reviewed" in why


def test_absent_and_unreadable_evidence_are_both_fail_closed(tmp_path):
    row = _review_proof("a" * 40)
    assert br.check_evidence_consistency(row, None)[0] == "no-evidence"
    assert br.check_evidence_consistency(row, tmp_path / "absent.md")[0] == "no-evidence"
    binary = tmp_path / "review-0001.md"
    binary.write_bytes(b"\xff\xfe\x00\x01 not utf-8 text \xff")
    assert br.check_evidence_consistency(row, binary)[0] == "evidence-unreadable"


def test_the_consistency_vocabulary_is_closed_and_every_value_is_reachable(tmp_path):
    """No status escapes the published vocabulary, and none of it is dead wording."""
    row = _review_proof("a" * 40)
    good = tmp_path / "good.md"
    good.write_text(_attestation(row), encoding="utf-8", newline="\n")
    generic = tmp_path / "generic.md"
    generic.write_text(GENERIC_EVIDENCE, encoding="utf-8", newline="\n")
    denied = tmp_path / "denied.md"
    denied.write_text(_attestation(row).replace(
        "This review was conducted independent of the implementation.",
        "This review was NOT independent of the implementation."),
        encoding="utf-8", newline="\n")
    binary = tmp_path / "binary.md"
    binary.write_bytes(b"\xff\xfe\x00\x01")
    observed = {br.check_evidence_consistency(row, path)[0]
                for path in (good, generic, denied, binary, None, tmp_path / "absent.md")}
    assert observed == set(br.EVIDENCE_CONSISTENCY_VALUES), observed
    assert "corroborated" not in br.EVIDENCE_CONSISTENCY_VALUES, (
        "the record must never claim a word the tool cannot earn")


def test_the_tripwire_is_token_matched_not_substring_matched(tmp_path):
    """'bypassed' is not a PASS verdict, and a narrower model id is another model."""
    row = _review_proof("a" * 40, resolved_model="claude-opus-4.5")
    evidence = tmp_path / "review-0001.md"
    body = _attestation(_review_proof("a" * 40, resolved_model="claude-opus-4"))
    evidence.write_text(body.replace("Verdict: PASS", "Verdict: bypassed"),
                        encoding="utf-8", newline="\n")
    status, why = br.check_evidence_consistency(row, evidence)
    assert status == "unstated", why
    assert "its verdict" in why, "'bypassed' must not satisfy a claimed PASS verdict"
    assert "the resolved model identity" in why, (
        "a document naming a different model must not read as consistent with this one")


def test_the_round_2_bypass_document_is_caught_by_the_tripwire(tmp_path):
    """CALIBRATED against the executed round-2 bypass, from ONE fixture.

    Green arm: the row and a document that states its claims -> consistent.
    Red arm: the SAME row, and the verbatim document round 2 used to reach
    QUALIFIED through the presence-only matcher -> contradicted, naming the
    claims the document denies. Nothing but the document body differs, so the
    red arm is attributable to the document and the test is demonstrably able
    to fail.
    """
    row = _review_proof("a" * 40, **ROUND2_BYPASS_ROW)

    green = tmp_path / "green.md"
    green.write_text(_attestation(row), encoding="utf-8", newline="\n")
    assert br.check_evidence_consistency(row, green)[0] == "consistent", (
        "green arm of the calibration: the fixture must be able to pass")

    red = tmp_path / "red.md"
    red.write_text(ROUND2_BYPASS_EVIDENCE.format(source_commit=row["source_commit"]),
                   encoding="utf-8", newline="\n")
    text = red.read_text(encoding="utf-8")
    for token in ("NOT independent", "NOT cross-family", "NOT PASS -- it FAILED"):
        assert token in text, "the pinned bypass document lost %r" % token
    for needle in (row["source_commit"], "conv-777", "gpt-5-codex", "claude",
                   "codex", "independent", "PASS"):
        assert br._states(text.lower(), needle), (
            "the bypass only works because %r IS present as a token; a document "
            "missing it would be caught as merely unstated instead" % needle)

    status, why = br.check_evidence_consistency(row, red)
    assert status == "contradicted", why
    assert "its independence" in why and "its verdict" in why, why


def test_a_negation_elsewhere_in_the_document_does_not_trip_the_wire(tmp_path):
    """The tripwire is clause-scoped, so a clean review does not read as denied.

    Real review prose carries negations ("no blocking defects were found"). Were
    the wire document-scoped it would fire on every honest document, and an
    always-red tripwire is the same as no tripwire.
    """
    row = _review_proof("a" * 40)
    evidence = tmp_path / "review-0001.md"
    evidence.write_text(
        _attestation(row).replace(
            "Verdict: PASS",
            "No blocking defects were found and nothing was waived. Verdict: PASS"),
        encoding="utf-8", newline="\n")
    status, why = br.check_evidence_consistency(row, evidence)
    assert status == "consistent", why


def test_the_tripwire_is_not_claimed_to_be_a_negation_detector():
    """The module says out loud what its own tripwire cannot do.

    An incomplete detector is only safe while nothing treats a miss as a pass.
    That safety rests on the docstring's stated contract plus `review_qualifies`
    requiring the attestation, so the statement is load-bearing and pinned.
    """
    doc = br.__doc__
    assert "NEGATIVE-ONLY" in doc
    assert "upgrades NOTHING on its own" in doc
    assert "falls through to the attestation requirement" in doc
    assert "a named party can still attest a review that" in doc, (
        "the module must state plainly what it gives up")


def test_a_forged_proofs_row_with_unrelated_evidence_never_qualifies(lab_repo, tmp_path):
    """The evidence-forgery scenario, end to end -- WITH the attestation present.

    A hand-written proofs row that claims independence, a PASS verdict,
    cross-family coverage and a resolved model -- pointed at a file that says
    none of it, and attested by a named party anyway. The attestation is the
    POSITIVE signal, but it cannot outrank a falsification: the tripwire fires,
    the row is still RECORDED and marked (never silently dropped), it is named in
    known_gaps, and it cannot carry the release to QUALIFIED.
    """
    root, commit = lab_repo
    proofs = _write_proofs(tmp_path / "proofs", [_review_proof(commit)],
                           body="unrelated notes, nothing to do with a review\n")
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store, proofs=proofs,
                      attest=ATTESTING_PARTY)
    assert result.returncode == 0, result.stdout + result.stderr
    record = _record(store / "skill-mesh-lab" / "v0.1.0-experimental.1")
    assert record["qualification"] == "INCOMPLETE", (
        "a falsified claim must never reach QUALIFIED, attested or not")
    assert len(record["reviews"]) == 1, "the forged row was silently dropped"
    assert record["reviews"][0]["import_status"] == "imported", (
        "the evidence file resolved; it is its CONTENT the tripwire refuses")
    assert record["reviews"][0]["evidence_consistency"] == "unstated"
    assert record["reviews"][0]["attested_by"] == ATTESTING_PARTY, (
        "the attestation is recorded even when the tripwire refuses the row")
    assert any("evidence-consistency tripwire" in gap for gap in record["known_gaps"])
    assert any("not stated by, the evidence it cites" in reason
               for reason in record["qualification_reasons"])
    assert (store / "skill-mesh-lab" / "v0.1.0-experimental.1" / "source.zip").is_file(), (
        "falsified evidence still keeps the archive")


def test_a_toolkit_release_with_forged_review_evidence_is_not_qualified(
        kit_repo, tmp_path):
    """Every required gate green, review evidence unrelated: still not QUALIFIED.

    This is the gate the charter exists to protect -- the toolkit is the product
    whose QUALIFIED claim would be published -- so it is proven on the toolkit
    path, not only on the cheaper lab one. The attestation is supplied, so the
    refusal is the tripwire's and not a missing flag's.
    """
    if PWSH is None:
        pytest.skip("powershell is not available on PATH")
    root, commit = kit_repo
    proofs = _write_proofs(tmp_path / "proofs", [_review_proof(commit)],
                           body="unrelated notes, nothing to do with a review\n")
    store = tmp_path / "store"
    result = _release("toolkit", root, commit, "v0.1.0-baseline.1", store, proofs=proofs,
                      attest=ATTESTING_PARTY)
    assert result.returncode == 1, result.stdout + result.stderr
    assert not (store / "skill-mesh" / "v0.1.0-baseline.1").exists(), (
        "a forged review must not reserve the version name")
    record = _record(_attempt_dirs(store)[0])
    assert record["qualification"] == "INCOMPLETE", record["qualification_reasons"]
    assert all(row["exit_code"] == 0 for row in record["checks"]
               if row["execution"] == "native"), (
        "the gates were green; only the review evidence failed the tripwire")
    assert record["reviews"][0]["evidence_consistency"] == "unstated"
    assert record["reviews"][0]["attested_by"] == ATTESTING_PARTY


def test_the_round_2_bypass_cannot_reach_qualified_end_to_end(lab_repo, tmp_path):
    """CALIBRATED, end to end, from ONE fixture: the row, the flag, two documents.

    GREEN arm -- the row, a document that states its claims, and
    `--attest-reviews` -- reaches QUALIFIED. That is what makes the RED arm
    meaningful: the release path is demonstrably able to qualify here, so the red
    arm's INCOMPLETE is attributable to the evidence document alone.

    RED arm -- the identical row and flag, pointed at the verbatim document round
    2 used to defeat the presence-only matcher. Read by a human it says the
    review was not independent, not cross-family, and FAILED. It must not
    qualify, and everything must still be retained and marked.
    """
    root, commit = lab_repo
    row = _review_proof(commit, **ROUND2_BYPASS_ROW)

    green_store = tmp_path / "green-store"
    green_proofs = _write_proofs(tmp_path / "green-proofs", [dict(row)])
    green = _release("lab", root, commit, "v0.1.0-experimental.1", green_store,
                     proofs=green_proofs, attest=ATTESTING_PARTY)
    assert green.returncode == 0, green.stdout + green.stderr
    green_record = _record(green_store / "skill-mesh-lab" / "v0.1.0-experimental.1")
    assert green_record["qualification"] == "QUALIFIED", (
        "green arm of the calibration: %s" % green_record["qualification_reasons"])

    red_store = tmp_path / "red-store"
    red_proofs = _write_proofs(
        tmp_path / "red-proofs", [dict(row)],
        body=ROUND2_BYPASS_EVIDENCE.format(source_commit=commit))
    red = _release("lab", root, commit, "v0.1.0-experimental.1", red_store,
                   proofs=red_proofs, attest=ATTESTING_PARTY)
    assert red.returncode == 0, red.stdout + red.stderr
    red_record = _record(red_store / "skill-mesh-lab" / "v0.1.0-experimental.1")
    assert red_record["qualification"] == "INCOMPLETE", (
        "a document that says the review FAILED reached QUALIFIED")
    review = red_record["reviews"][0]
    assert review["evidence_consistency"] == "contradicted"
    assert review["import_status"] == "imported", "nothing was silently dropped"
    assert review["attested_by"] == ATTESTING_PARTY
    assert (red_store / "skill-mesh-lab" / "v0.1.0-experimental.1"
            / review["evidence"]).is_file(), "the cited document is retained verbatim"
    assert any("DENIES" in gap for gap in red_record["known_gaps"])


# --------------------------------------------------------------------------- #
# The attestation act -- the one POSITIVE signal on the review path
# --------------------------------------------------------------------------- #

def test_without_the_attestation_act_a_perfect_review_is_only_incomplete(
        lab_repo, tmp_path):
    """CALIBRATED on the flag alone, from ONE fixture.

    Same repo, same row, same evidence document, same store layout -- the ONLY
    difference between the two arms is `--attest-reviews`. Without it the release
    is INCOMPLETE with the archive retained, the row retained and marked, and a
    reason naming the missing act; with it the row records `attested_by` and the
    release qualifies.
    """
    root, commit = lab_repo
    rows = [_review_proof(commit)]

    bare_store = tmp_path / "bare-store"
    bare_proofs = _write_proofs(tmp_path / "bare-proofs", rows)
    bare = _release("lab", root, commit, "v0.1.0-experimental.1", bare_store,
                    proofs=bare_proofs)
    assert bare.returncode == 0, bare.stdout + bare.stderr
    bare_dir = bare_store / "skill-mesh-lab" / "v0.1.0-experimental.1"
    bare_record = _record(bare_dir)
    assert bare_record["qualification"] == "INCOMPLETE"
    review = bare_record["reviews"][0]
    assert review["attested_by"] is None, "no flag, no attestation -- and it is explicit"
    assert review["evidence_consistency"] == "consistent", (
        "the tripwire is silent here; the ONLY thing missing is the named act")
    assert review["import_status"] == "imported", "the row is retained and marked"
    assert (bare_dir / "source.zip").is_file(), "the archive is retained"
    assert (bare_dir / review["evidence"]).is_file(), "the evidence is retained"
    assert any("--attest-reviews" in gap for gap in bare_record["known_gaps"])
    assert any("--attest-reviews" in reason
               for reason in bare_record["qualification_reasons"])

    named_store = tmp_path / "named-store"
    named_proofs = _write_proofs(tmp_path / "named-proofs", rows)
    named = _release("lab", root, commit, "v0.1.0-experimental.1", named_store,
                     proofs=named_proofs, attest=ATTESTING_PARTY)
    assert named.returncode == 0, named.stdout + named.stderr
    named_record = _record(named_store / "skill-mesh-lab" / "v0.1.0-experimental.1")
    assert named_record["reviews"][0]["attested_by"] == ATTESTING_PARTY
    assert named_record["qualification"] == "QUALIFIED", (
        "green arm of the calibration: %s" % named_record["qualification_reasons"])


def test_the_attestation_cannot_be_carried_by_the_proofs_document(lab_repo, tmp_path):
    """A reused proofs file may never smuggle the attestation forward.

    The act is a CLI flag precisely so that re-running a historical proofs JSON
    cannot silently re-attest it. A row that writes `attested_by` itself must be
    ignored, not honoured.
    """
    root, commit = lab_repo
    row = _review_proof(commit)
    row["attested_by"] = "somebody who never ran this"
    proofs = _write_proofs(tmp_path / "proofs", [row])
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store, proofs=proofs)
    assert result.returncode == 0, result.stdout + result.stderr
    record = _record(store / "skill-mesh-lab" / "v0.1.0-experimental.1")
    assert record["reviews"][0]["attested_by"] is None, (
        "a --proofs field was promoted into the attestation")
    assert record["qualification"] == "INCOMPLETE"


def test_the_attestation_is_published_on_the_review_row_in_the_notes(lab_repo, tmp_path):
    """The public notes must name the accountable party, or QUALIFIED is unreadable."""
    root, commit = lab_repo
    proofs = _write_proofs(tmp_path / "proofs", [_review_proof(commit)])
    store = tmp_path / "store"
    result = _release("lab", root, commit, "v0.1.0-experimental.1", store, proofs=proofs,
                      attest=ATTESTING_PARTY)
    assert result.returncode == 0, result.stdout + result.stderr
    notes = (store / "skill-mesh-lab" / "v0.1.0-experimental.1"
             / "release-notes.md").read_text(encoding="utf-8")
    assert "Attested by" in notes, "the notes hide who stands behind the review"
    assert ATTESTING_PARTY in notes
    assert "does not run or verify a cross-family review" in notes, (
        "the notes must not let a reader mistake attestation for verification")


@pytest.mark.parametrize("attest, expected", [
    ("x" * 150, "longer than"),
    ("<accountable party>", "unresolved placeholder"),
    ("C" + ":/Users/someone/notes", "absolute user path"),
    ("/home/someone/notes", "absolute user path"),
    ("/Users/someone/notes", "absolute user path"),
])
def test_a_malformed_attestation_name_is_an_input_error(lab_repo, tmp_path, attest,
                                                        expected):
    """The name is PUBLISHED, so it is bounded like every other public caller string.

    The absolute-path case is refused UP FRONT (exit 2), not at the end-of-run
    leak guard: reaching that one would mean paying for a whole release first.
    """
    root, commit = lab_repo
    proofs = _write_proofs(tmp_path / "proofs", [_review_proof(commit)])
    result = _release("lab", root, commit, "v0.1.0-experimental.1", tmp_path / "store",
                      proofs=proofs, attest=attest)
    assert result.returncode == 2, result.stdout + result.stderr
    assert expected in (result.stdout + result.stderr)
    assert not (tmp_path / "store").exists(), "the refused run wrote a store anyway"


def test_attesting_without_any_attached_review_is_an_input_error(lab_repo, tmp_path):
    """Naming a party for evidence that was never attached is a mistake, not a pass."""
    root, commit = lab_repo
    result = _release("lab", root, commit, "v0.1.0-experimental.1", tmp_path / "store",
                      attest=ATTESTING_PARTY)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "--attest-reviews was given without --proofs" in (result.stdout + result.stderr)


# --------------------------------------------------------------------------- #
# Evidence-path safety inside the proof importer
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("rel", ["../outside.md", "a/../../outside.md", "/etc/passwd",
                                 "C" + ":/Users/someone/evidence.md"])
def test_an_unsafe_evidence_path_is_refused_by_the_importer(tmp_path, rel):
    """Defence in depth: load_proofs rejects these at parse time, but the copier
    must never resolve one on its own if it is ever called from elsewhere."""
    proofs_dir = tmp_path / "proofs"
    proofs_dir.mkdir()
    (tmp_path / "outside.md").write_text("secret\n", encoding="utf-8")
    relpath, status = br._import_evidence(proofs_dir, rel, tmp_path / "dest", 0)
    assert relpath is None
    assert status == "unsafe-evidence-path"
    assert not (tmp_path / "dest").exists(), "nothing may be copied for a refused path"


def test_evidence_reached_through_a_link_out_of_the_proofs_directory_is_refused(tmp_path):
    """A name that is contained but RESOLVES outside is the traversal that matters."""
    proofs_dir = tmp_path / "proofs"
    proofs_dir.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "evidence.md").write_text("private material\n", encoding="utf-8")
    link = proofs_dir / "linked"
    made = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                          capture_output=True, text=True)
    if made.returncode != 0 or not link.exists():
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("could not create a link on this machine")
    relpath, status = br._import_evidence(proofs_dir, "linked/evidence.md",
                                          tmp_path / "dest", 0)
    assert relpath is None
    assert status == "evidence-escapes-proofs-directory"
    assert not (tmp_path / "dest").exists(), "nothing may be copied for an escaping path"


# --------------------------------------------------------------------------- #
# Qualification arithmetic (pure, no subprocess)
# --------------------------------------------------------------------------- #

def _native(name, exit_code):
    return {"name": name, "execution": "native", "exit_code": exit_code,
            "evidence": "checks/%s.txt" % name}


def test_a_failed_gate_is_blocked_never_qualified():
    checks = [_native("source-pytest", 1)]
    verdict, reasons = br.compute_qualification("lab", checks, [], "a" * 40)
    assert verdict == "BLOCKED"
    assert any("exited 1" in reason for reason in reasons)


def test_a_missing_gate_is_incomplete_never_qualified():
    checks = [_native("source-pytest", 0)]
    verdict, _ = br.compute_qualification("toolkit", checks, [], "a" * 40)
    assert verdict == "INCOMPLETE", "a missing toolkit gate must not produce QUALIFIED"


def test_all_gates_plus_a_charter_review_is_qualified():
    commit = "a" * 40
    checks = [_native(name, 0) for name in
              ("source-pytest", "staged-release", "artifact-verification")]
    verdict, reasons = br.compute_qualification(
        "toolkit", checks, [_qualifying_row(commit)], commit)
    assert verdict == "QUALIFIED", reasons


def test_a_falsified_review_leaves_a_fully_green_toolkit_incomplete():
    """The arithmetic counterpart of the forgery anchor: green gates are not enough."""
    commit = "a" * 40
    checks = [_native(name, 0) for name in
              ("source-pytest", "staged-release", "artifact-verification")]
    row = _qualifying_row(commit)
    row["evidence_consistency"] = "contradicted"
    verdict, reasons = br.compute_qualification("toolkit", checks, [row], commit)
    assert verdict == "INCOMPLETE"
    assert any("not stated by, the evidence it cites" in reason for reason in reasons)


def test_an_unattested_review_leaves_a_fully_green_toolkit_incomplete():
    """Green gates plus a silent tripwire still do not qualify without the named act."""
    commit = "a" * 40
    checks = [_native(name, 0) for name in
              ("source-pytest", "staged-release", "artifact-verification")]
    row = _qualifying_row(commit)
    row["attested_by"] = None
    verdict, reasons = br.compute_qualification("toolkit", checks, [row], commit)
    assert verdict == "INCOMPLETE"
    assert any("--attest-reviews" in reason for reason in reasons)


def test_exit_code_policy():
    assert br.release_exit_code("lab", "INCOMPLETE") == 0, (
        "retaining an explicitly incomplete lab archive is a success")
    assert br.release_exit_code("lab", "QUALIFIED") == 0
    assert br.release_exit_code("lab", "BLOCKED") == 1
    assert br.release_exit_code("toolkit", "QUALIFIED") == 0
    assert br.release_exit_code("toolkit", "INCOMPLETE") == 1
    assert br.release_exit_code("toolkit", "BLOCKED") == 1


def test_a_stalled_subprocess_keeps_the_documented_exit_code_contract(
        lab_repo, tmp_path, monkeypatch, capsys):
    """A timeout must not escape as a traceback and take the contract with it.

    The premise is a stdlib fact worth pinning, because it is the whole bug:
    `subprocess.TimeoutExpired` is a `SubprocessError`, NOT an `OSError`, so the
    io handler never saw it. `run_gate()` converts its own timeout; the
    environment probes and every `git()` call do not, and requiring each new call
    site to remember is how this reappears. One clause at the top catches the
    class once.
    """
    assert not issubclass(subprocess.TimeoutExpired, OSError), (
        "the premise changed: TimeoutExpired is now an OSError")
    assert issubclass(subprocess.TimeoutExpired, subprocess.SubprocessError)

    root, commit = lab_repo

    def stalled(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["git", "rev-parse"], timeout=br.TIMEOUT_GIT)

    monkeypatch.setattr(br, "capture_environment", stalled)
    code = br.main(["lab", "--source-root", str(root), "--source-commit", commit,
                    "--version", "v0.1.0-experimental.1",
                    "--store", str(tmp_path / "store"), "--python-exe", sys.executable])
    err = capsys.readouterr().err

    assert code == br.EXIT_EXEC, err
    assert any(line.startswith("baseline-release: ERROR") for line in err.splitlines()), (
        "a stalled subprocess did not produce the documented error line:\n%s" % err)


class _FakeProc:
    """Enough of a Popen for the timeout-kill path. Records what was called."""

    def __init__(self):
        self.pid = 4242
        self.killed = False
        self.waited = False

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        self.waited = True


def test_the_timeout_kill_reaches_descendants_on_both_platforms(monkeypatch):
    """A `lab` release can legitimately run off Windows, so both branches matter.

    `taskkill /T` is Windows-only; on POSIX a plain `proc.kill()` signals the
    direct child and leaves the grandchild (`release.ps1` -> `python -m pytest`,
    or pytest's own xdist workers) holding handles inside the disposable
    checkout. The POSIX answer is SIGKILL to the child's process group, which
    `run()` makes meaningful by starting each child in a new session.

    Bounded, not total, and not claimed as total: a descendant that has left the
    tree or called setsid for itself is outside both mechanisms.
    """
    proc = _FakeProc()
    signalled = []
    monkeypatch.setattr(br.os, "name", "posix", raising=False)
    monkeypatch.setattr(br.os, "getpgid", lambda pid: pid, raising=False)
    monkeypatch.setattr(br.os, "killpg",
                        lambda pgid, sig: signalled.append((pgid, sig)), raising=False)
    monkeypatch.setattr(br.subprocess, "run", _never_called)
    br._kill_process_tree(proc)
    if hasattr(br.signal, "SIGKILL"):   # true on every POSIX host, false here
        assert br._GROUP_KILL_SIGNAL is br.signal.SIGKILL
    assert signalled == [(4242, br._GROUP_KILL_SIGNAL)], (
        "the POSIX branch signalled only the direct child")
    assert proc.killed and proc.waited, "the direct child must still be killed and reaped"

    taskkilled = []
    monkeypatch.setattr(br.os, "name", "nt", raising=False)
    monkeypatch.setattr(br.subprocess, "run",
                        lambda argv, **kw: taskkilled.append(list(argv)))
    monkeypatch.setattr(br.os, "killpg", _never_called, raising=False)
    br._kill_process_tree(_FakeProc())
    assert taskkilled and taskkilled[0][:3] == ["taskkill", "/T", "/F"], taskkilled


def _never_called(*_args, **_kwargs):
    raise AssertionError("the wrong platform branch was taken")


def test_run_starts_posix_children_in_their_own_session(monkeypatch):
    """The kwarg that makes the POSIX group kill mean anything.

    Asserted in both directions: it is passed on POSIX, and it is NOT passed on
    Windows -- `start_new_session` is a POSIX-only argument, so the Windows path
    has to stay byte-for-byte what it was.
    """
    seen = {}

    class _Recorder:
        args = ["x"]
        returncode = 0

        def __init__(self, argv, **kwargs):
            seen.update(kwargs)

        def communicate(self, timeout=None):
            return "", ""

    monkeypatch.setattr(br.subprocess, "Popen", _Recorder)
    monkeypatch.setattr(br.os, "name", "posix", raising=False)
    br.run(["anything"])
    assert seen.get("start_new_session") is True, (
        "a POSIX child does not lead its own process group, so the group kill "
        "would signal this process's group instead of the child's")

    seen.clear()
    monkeypatch.setattr(br.os, "name", "nt", raising=False)
    br.run(["anything"])
    assert "start_new_session" not in seen, (
        "start_new_session is POSIX-only; passing it on Windows is a new failure "
        "mode on the platform this toolkit actually ships on")


# --------------------------------------------------------------------------- #
# Runbook
# --------------------------------------------------------------------------- #

def test_runbook_exists_and_covers_the_operator_path():
    runbook = REPO_ROOT / "documentation" / "baseline-release-runbook.md"
    assert runbook.is_file(), "missing %s" % runbook
    text = runbook.read_text(encoding="utf-8")
    for token in ("tools/baseline_release.py", "--source-root", "--source-commit",
                  "--version", "--store", "--python-exe", "--proofs",
                  "--attest-reviews", "attested_by", "evidence_consistency",
                  "Exit code", "verify-artifacts.py", ".attempts", ".aborted"):
        assert token in text, "the runbook never mentions %s" % token
    assert br.PRIVATE_PATH_RE.search(text) is None, (
        "the runbook carries an absolute user path; use placeholders")


def test_the_runbook_does_not_over_claim_what_the_tool_establishes():
    """The docs must say what the tool does NOT do, or an operator will assume it does.

    An honest tool paired with documentation that implies verification is still
    an over-claim -- the reader acts on the documentation. Both halves are
    asserted: the disclaimed capability, and the word the record deliberately
    stopped using.
    """
    text = (REPO_ROOT / "documentation" / "baseline-release-runbook.md").read_text(
        encoding="utf-8")
    assert "ATTESTED, not verified" in text
    for claim in ("does not run, and cannot verify, a cross-family review",
                  "negative-only", "upgrades nothing on its own",
                  "can still attest a review that did not happen"):
        assert claim in text, "the runbook never states %r" % claim
    assert "corroborat" not in text.lower(), (
        "the runbook still uses the word the record stopped claiming")


# --------------------------------------------------------------------------- #
# The claims inventory
#
# One defect shape was flagged in three consecutive review rounds of this step,
# each time at a different location -- a docstring, a regex comment, and the
# operator runbook: PROSE ASSERTING A PROTECTION THE CODE DOES NOT PROVIDE.
# Patching the named sentence each time is what produced the pattern, so the
# sentences are enumerated instead, and the enumeration is what a test grades.
#
# WHAT THIS GUARD IS, EXACTLY -- read before trusting it:
#
#   It DOES assert that every guarantee-bearing sentence in the module's
#   docstrings/comments and in the runbook appears in the inventory below with a
#   disposition somebody chose, and that a disposition claiming test coverage
#   names a test function that exists in this file.
#
#   It DOES NOT assert that every guarantee is tested, and it does not read the
#   sentences for truth. A machine cannot do either. What it buys is that a NEW
#   or REWORDED guarantee cannot land silently: the extraction reds until its
#   sentence is dispositioned, which is the review step that was being skipped.
#
# Adding a guarantee therefore costs one inventory line. That is the point.
# --------------------------------------------------------------------------- #

#: What a sentence has to contain to be treated as a guarantee. Deliberately
#: small and literal -- this is a trigger for human review, not a semantic model.
CLAIM_WORDS = re.compile(
    r"(?i)\b(never|always|cannot|can neither|impossible|guarantee[ds]?)\b")

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _sentences(block):
    """A normalized text block split into sentences."""
    return [s.strip() for s in _SENTENCE_SPLIT.split(re.sub(r"\s+", " ", block).strip())
            if s.strip()]


def _markdown_blocks(text):
    """Prose blocks of a markdown document: fenced code excluded.

    A block ends at a blank line, and a table row, a list item and a heading each
    START one -- so an unrelated edit three paragraphs away cannot renumber or
    re-fuse the sentence keys in the inventory.
    """
    blocks, current, fenced = [], [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            if current:
                blocks.append(" ".join(current))
                current = []
            continue
        if fenced:
            continue
        stripped = line.strip()
        starts_block = (not stripped or stripped.startswith("|")
                        or stripped.startswith("#")
                        or re.match(r"^([-*+]|\d+\.)\s", stripped))
        if starts_block and current:
            blocks.append(" ".join(current))
            current = []
        if stripped:
            current.append(stripped)
    if current:
        blocks.append(" ".join(current))
    return blocks


def _python_blocks(text):
    """Docstrings (module, class, function) plus contiguous `#` comment blocks."""
    import ast

    blocks = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if doc:
                blocks.extend(p for p in doc.split("\n\n") if p.strip())
    run = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            run.append(stripped.lstrip("#:").strip())
        elif run:
            blocks.append(" ".join(run))
            run = []
    if run:
        blocks.append(" ".join(run))
    return blocks


def extract_claims():
    """Every guarantee-bearing sentence in the two claim-bearing artifacts.

    Returns a list of (source, sentence). The predicate is FIELD-AGNOSTIC: it
    names no line, no section and no function, so a guarantee added anywhere in
    either file is picked up without this test being taught about it.
    """
    runbook = (REPO_ROOT / "documentation" / "baseline-release-runbook.md").read_text(
        encoding="utf-8")
    module = TOOL.read_text(encoding="utf-8")
    claims = []
    for source, blocks in (("runbook", _markdown_blocks(runbook)),
                           ("module", _python_blocks(module))):
        for block in blocks:
            for sentence in _sentences(block):
                if CLAIM_WORDS.search(sentence):
                    claims.append((source, sentence))
    return claims


#: Closed disposition vocabulary.
#:   test:<name>        a test in THIS file would red if the claim became false
#:   enforced-untested  the code enforces it structurally; no test isolates it
#:   descriptive        not a behavioural guarantee about this tool (a design
#:                      note, a statement about a third party, a restatement)
CLAIM_DISPOSITIONS = {
    # runbook
    "- **run, or verify, a review.** It **does not run, and cannot verify, a cross-family review.** The product charter's release invariant — at least one real representative cross-family review — is satisfied by attaching that review through `--proofs` **and** naming an accountable party with `--attest-reviews`.":
        'test:test_the_runbook_does_not_over_claim_what_the_tool_establishes',
    # runbook
    'Native host acceptance (an observed Claude Code or Codex CLI session) is a different evidence class and is never inferred from a green suite.':
        'test:test_toolkit_without_a_cross_family_review_is_never_qualified',
    # runbook
    'The tool never invents one.':
        'test:test_missing_required_flag_is_rejected',
    # runbook
    'A repeated request either verifies or refuses; it never overwrites.':
        'test:test_repeated_identical_request_verifies_without_overwriting',
    # runbook
    '**That command alone cannot reach `QUALIFIED`**, and it is not meant to — it records the gates it executed.':
        'test:test_toolkit_without_a_cross_family_review_is_never_qualified',
    # runbook
    'The lab archive is **source-only**: `providers` is empty, no `dist/` and no `CHECKSUMS.txt` are produced, and the lab repository is never edited — not its code, its index, its plan, or its acceptance records.':
        'test:test_working_source_is_unchanged_by_a_release',
    # runbook
    '- **A proofs document may not carry text UTF-8 cannot encode.** A `\\udNNN` escape in any string field survives `json.loads` as a lone surrogate, which no artifact this tool writes can hold.':
        'test:test_a_lone_surrogate_in_proofs_is_refused_at_the_boundary',
    # runbook
    "- **A row whose evidence file cannot be resolved, or whose `source_commit` does not bind to this release's source, is still RECORDED** — marked with an `import_status` and listed in `known_gaps`.":
        'test:test_missing_proof_evidence_is_recorded_as_incomplete_not_dropped',
    # runbook
    'It never counts toward qualification and is never silently dropped.':
        'test:test_missing_proof_evidence_is_recorded_as_incomplete_not_dropped',
    # runbook
    'Historical proof is never relabelled as current-source proof.':
        'test:test_proof_bound_to_another_source_commit_is_marked_and_never_relabelled',
    # runbook
    '- **An import binds its own source and environment.** It never implies that anything executed natively during this run.':
        'test:test_imported_check_evidence_is_copied_in_and_marked_as_imported',
    # runbook
    'The attestation is a CLI act so that reusing a historical proofs file can never carry it forward silently.':
        'test:test_the_attestation_cannot_be_carried_by_the_proofs_document',
    # runbook
    '### What the tool cannot do, stated plainly':
        'descriptive',
    # runbook
    'The cross-family review is the **only** required element this tool cannot execute.':
        'descriptive',
    # runbook
    "It is not, and cannot be made into, verification: a presence-only matcher is defeated by a verbatim paste of a *failing* review's transcript, in which every claimed word is present and every one of them is negated — and the bypass family (negation, quotation, rebuttal, sarcasm) is unbounded, because the reader is reading bytes the caller wrote.":
        'descriptive',
    # runbook
    '- It is a **CLI flag, never a `--proofs` field**, so re-running a historical proofs document cannot silently re-attest it.':
        'test:test_the_attestation_cannot_be_carried_by_the_proofs_document',
    # runbook
    '- Giving it **needs `--proofs`**; it is ignored on a repeated request that only verifies an already-retained release, because a retained record is never rewritten.':
        'enforced-untested',
    # runbook
    'What this gives up, stated plainly: **a named party can still attest a review that did not happen.** The tool never had the power to catch that; it only had the appearance of it.':
        'descriptive',
    # runbook
    'Consistency can be locally **falsified**; it can never be locally established.':
        'descriptive',
    # runbook
    'A miss is safe precisely because `consistent` upgrades nothing on its own: it falls through to the `--attest-reviews` requirement, so the tripwire can never manufacture a `QUALIFIED`.':
        'test:test_a_consistent_tripwire_result_upgrades_nothing_on_its_own',
    # runbook
    'Also covers damaged retained bytes found while verifying, and text this tool cannot encode as UTF-8.':
        'test:test_damaged_retained_bytes_are_reported_as_an_execution_failure',
    # runbook
    'A missing or failed gate **can never** produce `QUALIFIED`, and in every case the source archive is still retained.':
        'test:test_a_failed_gate_is_blocked_never_qualified',
    # runbook
    'The payload is built in a unique sibling staging directory and published by **one rename of the complete directory**, so a release directory is never observed half-built.':
        'enforced-untested',
    # runbook
    'The invocation itself always uses the real paths.':
        'enforced-untested',
    # runbook
    'It is recorded **separately** from `source_commit`, the product commit being released, and the two are never conflated.':
        'test:test_builder_commit_is_recorded_separately_from_the_source_commit',
    # runbook
    'A repeated request never overwrites and never rebuilds the distribution; it re-resolves the commit, re-creates the disposable checkout, and then:':
        'test:test_repeated_identical_request_verifies_without_overwriting',
    # runbook
    '**The version name is NOT reserved.** A failed attempt never creates `<store>/<product>/<version>/`.':
        'test:test_failed_source_suite_is_blocked_and_still_keeps_the_archive',
    # runbook
    'What it does carry is `source.zip` and every `checks/` evidence file the run had already produced, which is the part the error message alone cannot give you.':
        'descriptive',
    # runbook
    '| exit `2`, `carries a character UTF-8 cannot encode` | a `--proofs` string, or an argument, holds a lone surrogate.':
        'test:test_a_lone_surrogate_in_proofs_is_refused_at_the_boundary',
    # runbook
    'It is a description, not an action: `publication_status` is always `NOT_PUBLISHED`.':
        'test:test_public_packet_excludes_private_evidence',
    # runbook
    '- **Never publishable**: the exact retained `source.zip` (its member contents are not inspected here), `SHA256SUMS` (it names private files), `checks/` (captured run output carries machine-specific absolute paths), `reviews/` and `proofs/` (imported private evidence), `receipt.json` (a private run record), and `public/` itself.':
        'test:test_public_packet_excludes_private_evidence',
    # runbook
    'Private consumer backups and raw host records are out of scope entirely — they are never inputs.':
        'descriptive',
    # runbook
    '- **Secrets and credentials are never inputs and are never recorded.** Dependency names and authentication prerequisites are all the release notes carry — for the toolkit, that is `gh auth login` for GitHub Copilot CLI, with no `OPENAI_API_KEY` used or needed.':
        'descriptive',
    # runbook
    'Read this before filing a bug against it.** An artifact the tool cannot read back counts as a failure — it is the last gate before a release is kept, so an ungraded file is never treated as clean.':
        'test:test_the_leak_gate_fails_closed_on_an_artifact_it_cannot_grade',
    # module
    'This module orchestrates, records, and retains; it never re-implements a gate and never publishes.':
        'descriptive',
    # module
    'Native host acceptance (an observed Claude Code / Codex CLI session) is a different evidence class and is never inferred from a green suite.':
        'test:test_imported_check_evidence_is_copied_in_and_marked_as_imported',
    # module
    '* It does not run, and cannot verify, a cross-family review.':
        'descriptive',
    # module
    'Absent either, a release CANNOT reach QUALIFIED, no matter how green the suites are.':
        'test:test_a_review_nobody_attested_never_qualifies',
    # module
    'STORE LAYOUT ------------ <store>/<product>/<version>/ a retained release ("release ID" = "<product>/<version>", allocated by the caller, never by this tool) source.zip pinned source payload (git-tracked files of the pinned commit) release.json the record; schema_version 1 SHA256SUMS raw SHA-256 over every retained file except itself (so it covers release.json) release-notes.md sanitized, public-safe notes verify-artifacts.py the retained verifier.':
        'descriptive',
    # module
    "At the release ROOT and PUBLISHABLE, because the notes tell a recipient of the published subset to run it -- `checks/` is private, so the verifier cannot live there receipt.json this operation's argv/time/exit/evidence checks/ raw host run evidence (private) reviews/, proofs/ imported evidence (private; never public) public/packet.json what may be published, and what may not CHECKSUMS.txt toolkit only -- the ORIGINAL normalized manifest produced by release.ps1 dist/{claude,gpt,codex}/ toolkit only -- the built profiles <store>/.attempts/<uuid>/ a COMPLETE payload that was not published -- a qualification failure, or a build that finished and then could not take its version name.":
        'descriptive',
    # module
    'It does NOT reserve the version name; a retry allocates a new attempt and never disturbs this one.':
        'test:test_a_retry_allocates_a_new_attempt_and_preserves_the_previous_one',
    # module
    'Which of the two retention directories a failed run lands in is decided by what the stage CONTAINS (stage_bucket), read off the disk -- never by which exception was in flight.':
        'test:test_the_retention_bucket_is_read_off_the_stage_not_from_the_error',
    # module
    'REPEATED REQUESTS (this is also the reopen / re-verify path) ------------------------------------------------------------ A second invocation naming an existing release ID never overwrites it.':
        'test:test_repeated_identical_request_verifies_without_overwriting',
    # module
    "It never converts one author's self-consistency into a verification.":
        'descriptive',
    # module
    'Every native gate already obeys it: a required gate counts only when THIS process executed it (`execution == "native"`), an import is hardcoded to `execution: "imported"` and can never satisfy one, and a measured environment always beats an imported claim about it.':
        'test:test_imported_check_evidence_is_copied_in_and_marked_as_imported',
    # module
    'The cross-family review is the ONE required element this tool cannot execute.':
        'descriptive',
    # module
    "A token match across them therefore measures the self-consistency of one author's story; it is not, and cannot be made into, verification.":
        'descriptive',
    # module
    'a CLI flag, deliberately NOT a `--proofs` field, so that reusing a historical proofs file can never silently carry the attestation forward.':
        'test:test_the_attestation_cannot_be_carried_by_the_proofs_document',
    # module
    'Consistency can be locally FALSIFIED, never locally established.':
        'descriptive',
    # module
    "Being negative-only is what makes the tripwire's incompleteness safe: a miss falls through to the attestation requirement, so it can never manufacture a QUALIFIED.":
        'test:test_a_consistent_tripwire_result_upgrades_nothing_on_its_own',
    # module
    'The tool never had the power to catch that; it only had the appearance of it.':
        'descriptive',
    # module
    "It is recorded separately from `source_commit` (the product commit being released) and the two are never conflated -- releasing the toolkit from its own repository makes them coincidentally equal only when the caller pins this repository's HEAD.":
        'test:test_builder_commit_is_recorded_separately_from_the_source_commit',
    # module
    'Read that as a CONVENTION the render sites keep, NOT as a mechanism this function enforces: md_inline() cannot tell where its argument came from.':
        'descriptive',
    # module
    "A CommonMark renderer escapes a code span's content, and swapping the backtick means the span cannot be broken open to escape it.":
        'test:test_an_unpaired_caller_backtick_cannot_open_a_code_span_in_the_notes',
    # module
    'By then there is no "value" left to route through md_code() -- only a sentence -- so a sink physically cannot know which substring the caller wrote.':
        'descriptive',
    # module
    'Best effort, never raises.':
        'enforced-untested',
    # module
    '`release.ps1` spawns `python -m pytest` as a GRANDchild, so killing the powershell host on timeout can leave that grandchild alive, holding open file handles inside the disposable checkout that `remove_disposable_workspace` then cannot clear -- its retry/chmod loop cannot force-close a handle a live process still holds.':
        'descriptive',
    # module
    'Never a shell string, never shell=True.':
        'enforced-untested',
    # module
    'Refuse caller text that UTF-8 cannot encode.':
        'test:test_the_unencodable_check_is_scoped_honestly',
    # module
    'Every artifact this tool writes is written as UTF-8, so a string UTF-8 cannot encode is not a rendering problem -- it is a value that CANNOT be published.':
        'descriptive',
    # module
    'Text this tool captures rather than receives cannot carry a surrogate (`run()` decodes with `errors="backslashreplace"`, which emits ASCII, and every file read is strict UTF-8).':
        'test:test_the_unencodable_check_is_scoped_honestly',
    # module
    'A recorded path must never be machine-specific.':
        'test:test_recorded_argv_is_tokenized_and_cwd_is_relative',
    # module
    'This is the last gate before a release is retained, and every file it is handed was written moments earlier by this same process, so one that cannot be read is a FAULT.':
        'test:test_the_leak_gate_fails_closed_on_an_artifact_it_cannot_grade',
    # module
    'Only the second pass is lost, the raw line scan still graded the same bytes, and these documents are written by `json.dumps` -- so the reachable case is not a corrupt artifact but a caller handing this function a file that was never JSON.':
        'test:test_the_leak_gate_fails_closed_on_an_artifact_it_cannot_grade',
    # module
    'The real invocation always uses the real paths; only the RECORD is tokenized.':
        'enforced-untested',
    # module
    "Longest path first, so '<work>/checkout/tools' never wins over '<work>/checkout'.":
        'enforced-untested',
    # module
    "A cheap pre-filter, not a path validator: `os.path.abspath` on a relative argv entry would resolve it against this process's cwd and invent a machine path that was never in the argument.":
        'descriptive',
    # module
    'A precondition failure, not an execution failure: commit resolution and release staging are both git-driven, so a missing git means the request cannot be attempted at all.':
        'descriptive',
    # module
    'Always checked -- a caller that wants the text wants it only when the command succeeded -- so this raises ExecutionError on a nonzero exit rather than returning an empty string that reads like a legitimate answer.':
        'enforced-untested',
    # module
    'Unknown is spelled out, never silently omitted.':
        'enforced-untested',
    # module
    "A row whose evidence file is missing, or whose source id does not bind to this release's source commit, is imported and MARKED -- never silently dropped, and never counted toward qualification.":
        'test:test_missing_proof_evidence_is_recorded_as_incomplete_not_dropped',
    # module
    'It is never read from the proofs document, so a reused historical proofs file can never carry an attestation forward on its own.':
        'test:test_the_attestation_cannot_be_carried_by_the_proofs_document',
    # module
    'A hit is a real falsification and is fail-closed; a MISS is safe, because consistency alone never qualifies a review (the `--attest-reviews` act does).':
        'test:test_a_consistent_tripwire_result_upgrades_nothing_on_its_own',
    # module
    'Read the module docstring first: both the row and the document are authored by the same caller, so comparing them cannot corroborate either.':
        'descriptive',
    # module
    'The charter invariant, spelled out and never softened.':
        'descriptive',
    # module
    'Never overwrites, never rebuilds.':
        'test:test_repeated_identical_request_verifies_without_overwriting',
    # module
    'Never raises.':
        'test:test_a_complete_payload_is_never_announced_as_partial_when_no_move_succeeds',
    # module
    'A missing or failed gate can never produce QUALIFIED.':
        'test:test_a_missing_gate_is_incomplete_never_qualified',
    # module
    'An operator who pastes the runbook line without resolving its variables must be refused, never acted on.':
        'test:test_placeholder_values_are_refused',
    # module
    'Generous ceilings so a real release is never cut short.':
        'descriptive',
    # module
    'Tests never reach them.':
        'descriptive',
    # module
    'The word is "consistent", never "corroborated", because a comparison between two documents the same caller wrote cannot corroborate either one.':
        'descriptive',
    # module
    'Verdict: PASS") cannot trip it.':
        'descriptive',
    # module
    'This list is not, and is not trying to be, a natural-language negation detector -- see the module docstring: a miss falls through to the `--attest-reviews` requirement and can never manufacture a QUALIFIED, so completeness is not what makes it useful.':
        'test:test_the_tripwire_is_not_claimed_to_be_a_negation_detector',
    # module
    "CommonMark backslash-escapes any ASCII punctuation, so one backslash neutralizes each of them: '\\\\' (an escape a caller would otherwise be able to forge), '`' (code span), '*' and '_' (emphasis), '[' and ']' (link/image), '|' (table cell), '~' (GFM strikethrough) and '#' (an ATX heading, reachable only if caller text ever leads a bullet -- cheap insurance rather than a claim that it cannot).":
        'descriptive',
    # module
    "ONE pass over the characters, never chained replaces: a second pass would re-escape the backslashes the first one wrote, turning '\\[' into a literal backslash followed by a LIVE '['.":
        'test:test_md_untrusted_escapes_every_inline_construct_opener',
    # module
    'ONE definition: scan_private_paths writes it and _build_and_publish partitions on it, so the two can never drift into describing a fault as a leak.':
        'test:test_a_leak_and_an_ungraded_artifact_are_reported_as_different_faults',
    # module
    "Every caller-controlled cell is rendered in a CODE SPAN, not as plain cell text: a code span's content is escaped by any CommonMark renderer, and md_code() swaps the backtick so the span cannot be broken open.":
        'test:test_an_unpaired_caller_backtick_cannot_open_a_code_span_in_the_notes',
    # module
    "The manifest is the one thing the gate below cannot grade, because it IS the gate's reference.":
        'descriptive',
    # module
    'Never softened, never inferred.':
        'descriptive',
    # module
    "A failed move raises, and perform_release's handler then files the payload by its CONTENTS through the same stage_bucket -- so it can never be misfiled as an aborted build.":
        'test:test_a_failed_attempt_rename_still_files_the_complete_payload_as_an_attempt',
    # module
    'reject_unencodable() refuses the two CALLER boundaries up front at exit 2; this clause is for what that cannot reach -- a filesystem-supplied name carrying a surrogate.':
        'test:test_the_unencodable_check_is_scoped_honestly',
}


#: Anti-vacuity floors. An extraction that silently stopped finding anything
#: would agree with an empty inventory and pass -- these make that a red.
CLAIM_FLOOR = {"runbook": 25, "module": 45}

_DISPOSITIONS = ("enforced-untested", "descriptive")


def test_every_guarantee_in_the_tool_and_the_runbook_is_dispositioned():
    """The guard against the one defect shape this step kept re-introducing.

    Read the section header above for what this does and does not establish. In
    short: it cannot tell whether a sentence is TRUE, so it does not pretend to.
    It makes a new or reworded guarantee impossible to land without somebody
    writing down what backs it -- which is the step that kept being skipped.
    """
    claims = extract_claims()
    found = {}
    for source, sentence in claims:
        assert sentence not in found or found[sentence] == source, (
            "the same sentence appears in both artifacts; the inventory is keyed "
            "by sentence, so one of them has to be reworded: %r" % sentence)
        found[sentence] = source

    for source, floor in CLAIM_FLOOR.items():
        count = sum(1 for src, _ in claims if src == source)
        assert count >= floor, (
            "only %d guarantee sentences were extracted from the %s (floor %d). "
            "Either the extraction broke -- in which case this whole test is "
            "vacuous -- or a large amount of prose was deleted."
            % (count, source, floor))

    extracted = set(found)
    inventoried = set(CLAIM_DISPOSITIONS)
    undocumented = sorted(extracted - inventoried)
    assert not undocumented, (
        "%d guarantee-bearing sentence(s) are not in CLAIM_DISPOSITIONS. Check "
        "each against what the code ACTUALLY does, then add it with a "
        "disposition -- do not add it unread, and prefer narrowing the sentence "
        "to widening the code:\n  - %s"
        % (len(undocumented), "\n  - ".join(undocumented)))
    stale = sorted(inventoried - extracted)
    assert not stale, (
        "%d inventoried claim(s) no longer appear in either artifact. If the "
        "sentence was reworded, re-read it and re-key the entry; if it was "
        "deleted, delete the entry:\n  - %s" % (len(stale), "\n  - ".join(stale)))


def test_every_claim_that_says_it_has_a_test_names_a_real_one():
    """A disposition is only worth its word if the test it names exists.

    This is the half of the guard that IS mechanical: a `test:` disposition
    pointing at a renamed or deleted test is caught here rather than read as
    coverage. It does not verify that the named test actually grades the claim
    -- no machine can -- so a mapping still has to be read by a reviewer.
    """
    defined = {name for name in globals() if name.startswith("test_")}
    for sentence, disposition in sorted(CLAIM_DISPOSITIONS.items()):
        if disposition.startswith("test:"):
            named = disposition[len("test:"):]
            assert named in defined, (
                "claim %r is dispositioned to %r, which is not a test in this "
                "file" % (sentence[:80], named))
        else:
            assert disposition in _DISPOSITIONS, (
                "claim %r carries an unknown disposition %r; the vocabulary is "
                "test:<name>, %s" % (sentence[:80], disposition,
                                     ", ".join(_DISPOSITIONS)))
