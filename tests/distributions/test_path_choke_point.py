"""Structural gate: every mutating primitive resolves through the path choke point.

WHY THIS FILE EXISTS
--------------------
Three deep-review rounds each found the SAME invariant violated at a NEW site whose
sibling branch already had the guard -- and two of the sites were introduced by the
previous round's own fixes. Enforcing it per call site demonstrably does not hold.

The invariant, stated once:

    No path may read or mutate a consumer-home target without re-resolving
    containment, and no path may destroy or overwrite bytes without first proving
    those bytes are ours.

This module makes the containment half MECHANICAL. It walks every git-tracked
``.ps1``, finds every mutating filesystem primitive, and fails if any of them
operates on a path that did not come from a resolver. The enumeration is what turns
"we fixed the five we found" into "a sixth cannot appear".

THE CONVENTION IT ENFORCES
--------------------------
1. A mutating primitive's path argument is a variable named ``$safe*``.
2. A ``$safe*`` variable is only ever assigned from an approved resolver
   (``Resolve-HomeTarget``, ``Resolve-TxPath``, ``Resolve-Contained``,
   ``Resolve-SafePath``, ...), or derived from another ``$safe*`` variable.

Both halves matter: (1) alone would let someone write ``$safeTarget = $rawPath``.

The file list comes from ``git ls-files`` and is NEVER hand-maintained -- a
hand-maintained list is a false green in this repository's doctrine, and every other
repo-wide gate here (``test_no_committed_skill_md_under_a_discovery_path``,
``test_no_absolute_private_paths_committed``,
``test_tracked_powershell_sources_are_ascii_without_bom``) is enumerated the same
way. A newly added ``.ps1`` is therefore covered the moment it is tracked.
"""
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Filesystem primitives that CREATE, OVERWRITE, MOVE, or DELETE. Read-only calls
# (Get-Content, Get-ChildItem, Test-Path, [IO.File]::Read*, OpenRead) are out of
# scope: a redirected read yields wrong bytes, which fails a hash comparison, while
# a redirected write destroys something.
# Aliases are included deliberately: `rm`, `del`, `ri`, `cpi`, `mi` are the SAME
# cmdlets, and a gate that only knows the long names can be sidestepped -- by
# accident as easily as on purpose. Same for Rename-Item and the
# [IO.Directory] / [IO.File] statics.
#
# Aliases are recognised ONLY in command position (line start, or after `;`/`{`/`|`)
# and only when followed by an argument. Matching them anywhere would make `md` fire
# on every `SKILL.md` and `CLAUDE.md` in the repo -- the gate would drown in false
# positives and get switched off, which is worse than not having it.
ALIAS_TO_CMDLET = {
    "rm": "Remove-Item", "del": "Remove-Item", "erase": "Remove-Item",
    "rd": "Remove-Item", "rmdir": "Remove-Item", "ri": "Remove-Item",
    "cpi": "Copy-Item", "cp": "Copy-Item", "copy": "Copy-Item",
    "mi": "Move-Item", "mv": "Move-Item", "move": "Move-Item",
    "ni": "New-Item", "md": "New-Item", "mkdir": "New-Item",
    "sc": "Set-Content", "ac": "Add-Content",
    "rni": "Rename-Item", "ren": "Rename-Item",
}
MUTATING = re.compile(
    r"\b(?P<cmdlet>Copy-Item|Remove-Item|Move-Item|New-Item|Rename-Item"
    r"|Set-Content|Add-Content|Out-File)\b"
    r"|\[(?:System\.)?IO\.(?:File|Directory)\]::(?P<dotnet>WriteAllText|WriteAllBytes"
    r"|WriteAllLines|AppendAllText|AppendAllLines|Delete|Move|Copy|CreateDirectory)"
    r"|(?:^|[;{|])\s*(?P<alias>" + "|".join(sorted(ALIAS_TO_CMDLET, key=len, reverse=True))
    + r")(?=\s+[-$'\"@(])"
)

# Which argument actually RECEIVES the mutation. For Copy-Item/Move-Item that is
# -Destination; for everything else the path argument is the thing written or deleted.
DESTINATION_IS_TARGET = ("Copy-Item", "Move-Item")
DEST_ARG = re.compile(r"-Destination\s+(?P<arg>\S+)")
PATH_ARG = re.compile(r"-LiteralPath\s+(?P<arg>\S+)|-Path\s+(?P<arg2>\S+)")
DOTNET_FIRST_ARG = re.compile(r"::\w+\(\s*(?P<arg>[^,\)]+)")

# ...but the SOURCE of a Copy-Item/Move-Item is NOT out of scope, and an earlier
# version of this gate wrongly assumed it was ("-LiteralPath is the source being
# READ, and it is legitimately a generated dist file"). That assumption is what let
# the decisive defect through three review rounds:
#
#     Copy-Item -LiteralPath (Join-HomePathLexical $a.rel_path) -Destination $payload
#
# The destination there is a perfectly gated backup payload; the SOURCE is a
# consumer-home path built lexically, so an ancestor junction redirects the READ and
# the "pre-image" captured into the backup is a file from outside the home --
# corrupting the exact artifact rollback depends on.
#
# A dist-file source really is legitimate, so the rule is not "sources must be
# $safe*". It is narrower and exact: a LEXICAL CONSUMER-HOME PATH MAY NEVER REACH
# THE FILESYSTEM, in any argument of any mutating primitive. Anything built from the
# lexical joiner or from the raw home root, and not laundered through a resolver, is
# a violation wherever it appears.
LEXICAL_HOME = re.compile(r"Join-HomePathLexical|\$script:HomeAbs\b|\$HomeAbs\b")
SOURCE_ARG = re.compile(r"-LiteralPath\s+(?P<arg>\S+)|-Path\s+(?P<arg2>\S+)")

SAFE_VAR = re.compile(r"\A\$safe[A-Za-z0-9_]*\Z", re.I)

# A $safe* variable may only be born from one of these.
APPROVED_RESOLVERS = (
    "Resolve-HomeTarget",        # migrator: THE consumer-home choke point
    "Resolve-HomeTargetForRead",
    "Resolve-TxPath",            # migrator: THE transaction-directory choke point
    "Resolve-TxPayloadPath",
    "Assert-SafeActionTarget",   # migrator: thin adapter over Resolve-HomeTarget
    "Resolve-Contained",         # installer: its own choke point over Resolve-SafePath
    "Resolve-SafePath",          # runtime/path-guard.ps1, the primitive itself
)

# --------------------------------------------------------------------------- #
# Allowlist
#
# Modelled on PRIVATE_PATH_EXEMPT in tests/package-integrity/test_manifest_contract.py,
# whose comment is the rule here too: "a path is not exempt because it is
# inconvenient to fix". Every entry carries a written reason, and the reason must be
# that the site provably does not touch a consumer home.
# --------------------------------------------------------------------------- #

# Whole files whose mutating primitives never receive a consumer home at all.
FILE_EXEMPT = {
    "tools/build-distributions.ps1":
        "Writes only into the generated dist/ staging tree it owns and regenerates; "
        "every output path is already asserted inside the profile dir by "
        "Resolve-SafePath in Write-GeneratedFile. It never receives a -Home.",
    "tools/release.ps1":
        "Operates on the release staging dir it creates and on the repo checkout; "
        "takes no consumer-home parameter.",
    "tools/gen-router-shim.ps1":
        "Writes a generated shim into the repo tree; takes no consumer-home parameter.",
    "runtime/skill-router.ps1":
        "Runtime dispatch: writes only its own session-state file, whose path is "
        "validated by Resolve-SafePath before use. Not a consumer-home installer.",
    "runtime/telemetry/telemetry-writer.ps1":
        "Appends to the telemetry log path, validated by Resolve-SafePath. Not a "
        "consumer-home installer.",
}

# Individual sites inside the consumer-home tools. Keyed by (file, exact stripped
# source line) rather than a line number, which drifts on every edit and would make
# the allowlist silently stale.
SITE_EXEMPT = {
    ("tools/skill-mesh-transaction.ps1",
     "New-Item -ItemType Directory -Path $dir -Force | Out-Null"):
        "Shared engine. $dir is the parent of the caller-supplied JOURNAL path -- a "
        "transaction directory or an OS-temp dir -- never a consumer-home target. The "
        "engine is deliberately unaware of consumer homes; its callers own that gate.",
    ("tools/skill-mesh-transaction.ps1",
     "[System.IO.File]::WriteAllText($Path, '', (New-Object System.Text.UTF8Encoding($false)))"):
        "Creates the empty journal file at the caller-supplied journal path (see above).",
    ("tools/skill-mesh-transaction.ps1",
     "[System.IO.File]::AppendAllText($path, ($line + \"`n\"),"):
        "Appends one journal record to the caller-supplied journal path (see above).",
    ("tools/migrate-legacy-install.ps1",
     "New-Item -ItemType Directory -Path $dir -Force | Out-Null"):
        "New-DirectoryFor creates the PARENT chain of an already-resolved path: every "
        "caller passes a $safe* value from Resolve-HomeTarget or Resolve-TxPath, and "
        "the leaf write re-resolves afterwards anyway.",
    ("tools/migrate-legacy-install.ps1",
     "New-Item -ItemType Directory -Path $script:TxDir -Force | Out-Null"):
        "Creates the transaction directory under the operator-supplied -BackupDir, "
        "which is asserted OUTSIDE the consumer home at argument-validation time. "
        "$script:TxDir is re-resolved through Resolve-SafePath on the next line.",
    ("tools/install-skill-mesh.ps1",
     "New-Item -ItemType Directory -Path $homeAbs -Force | Out-Null"):
        "Creates the install home ROOT itself, which IS the containment boundary -- "
        "there is no enclosing root to validate it against.",
    ("tools/install-skill-mesh.ps1",
     "New-Item -ItemType Directory -Path $current -Force | Out-Null"):
        "New-TrackedDir walks the segment chain and calls Resolve-SafePath on "
        "$current immediately above this line, on every segment.",
    ("tools/install-skill-mesh.ps1",
     "Remove-Item -LiteralPath $stage -Recurse -Force"):
        "Removes the OS-temp build staging dir this process just created; not a "
        "consumer-home path.",
    ("tools/install-skill-mesh.ps1",
     "Remove-Item -LiteralPath $stageDir -Recurse -Force"):
        "Removes the OS-temp build staging dir this process just created; not a "
        "consumer-home path.",
    ("tools/install-skill-mesh.ps1",
     "Remove-Item -LiteralPath $txStateDir -Recurse -Force"):
        "Removes the per-run OS-temp transaction-state dir; not a consumer-home path.",
}


# --------------------------------------------------------------------------- #
# Scanner
# --------------------------------------------------------------------------- #

def strip_ps_comments(text):
    """Drop block and line comments so documentation cannot trip the sweep.

    Same idiom as tests/router/test_no_claude_dependency.py. A backtick-escaped `#
    is not a comment, so it is preserved."""
    text = re.sub(r"<#.*?#>", "", text, flags=re.S)
    return "\n".join(re.sub(r"(?<!`)#.*", "", line) for line in text.split("\n"))


def tracked_ps1():
    out = subprocess.run(["git", "ls-files", "*.ps1"], cwd=REPO_ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [f.strip() for f in out.split("\n") if f.strip()]


def _path_argument(line, match):
    """The path expression the mutation actually WRITES TO or DELETES, or None."""
    if match.group("dotnet"):
        m = DOTNET_FIRST_ARG.search(line, match.start())
        return m.group("arg").strip() if m else None
    cmdlet = match.group("cmdlet") or ALIAS_TO_CMDLET.get((match.group("alias") or "").lower())
    if cmdlet in DESTINATION_IS_TARGET:
        m = DEST_ARG.search(line, match.end())
        return m.group("arg").strip() if m else None
    m = PATH_ARG.search(line, match.end())
    if not m:
        return None
    return (m.group("arg") or m.group("arg2")).strip()


def scan_source(rel, text):
    """Every mutating site in `text`. Returns [(rel, line_no, stripped, path_arg)]."""
    sites = []
    for i, line in enumerate(strip_ps_comments(text).split("\n"), 1):
        m = MUTATING.search(line)
        if not m:
            continue
        sites.append((rel, i, line.strip(), _path_argument(line, m)))
    return sites


def safe_var_assignments(text):
    """name -> list of right-hand sides, for every `$safeX = ...` assignment."""
    out = {}
    for line in strip_ps_comments(text).split("\n"):
        m = re.match(r"\s*(\$safe[A-Za-z0-9_]*)\s*=\s*(.+)$", line.strip(), re.I)
        if m:
            out.setdefault(m.group(1).lower(), []).append(m.group(2).strip())
    return out


def ungated_reason(var, assigns, seen=None):
    """None if `var` is TRANSITIVELY born from an approved resolver, else why not.

    Follows `$safeB = $safeA` chains to their origin. Stopping at one hop -- the
    earlier behaviour, a bare `continue  # derived from another gated value` -- meant
    a two-link alias chain (`$safeA = $rawPath; $safeB = $safeA`) laundered a raw
    path into a name the gate trusted, so the gate could be defeated by renaming.
    A cycle counts as ungated: `$safeA = $safeB; $safeB = $safeA` proves nothing.
    """
    key = var.lower()
    seen = set() if seen is None else seen
    if key in seen:
        return f"{var} is part of an assignment cycle, which proves nothing"
    seen = seen | {key}
    rhs_list = assigns.get(key)
    if not rhs_list:
        return f"{var} is never assigned in this file"
    for rhs in rhs_list:
        if any(r in rhs for r in APPROVED_RESOLVERS):
            continue
        parents = re.findall(r"\$safe[A-Za-z0-9_]*", rhs, re.I)
        if parents:
            for p in parents:
                why = ungated_reason(p, assigns, seen)
                if why:
                    return f"{var} derives from {why}"
            # A gated PARENT is not enough: `$safeT = $safeBase + $rawSuffix` and
            # `$safeT = Join-Path $safeBase $rawSuffix` both mix a resolved value
            # with an unresolved one, and the result is no longer proven to be
            # inside the home. Every other variable operand must be gated too.
            others = [v for v in re.findall(r"\$[A-Za-z_][A-Za-z0-9_:]*", rhs)
                      if not re.match(r"\A\$safe", v, re.I)
                      and v.lower() not in ("$_", "$true", "$false", "$null", "$pid")]
            if others:
                return (f"{var} mixes gated value(s) with unresolved operand(s) "
                        f"{', '.join(sorted(set(others)))} in ({rhs})")
            continue
        return f"{var} is assigned from an ungated expression ({rhs})"
    return None


def _check_expression(rel, line_no, stripped, arg, assigns, bad, role):
    """Assert one path expression is a transitively-gated $safe* value."""
    found = re.findall(r"\$safe[A-Za-z0-9_]*", arg, re.I)
    if not found:
        bad.append(f"{rel}:{line_no}: {role} is not a $safe* value ({arg}): {stripped}")
        return
    for var in found:
        why = ungated_reason(var, assigns)
        if why:
            bad.append(f"{rel}:{line_no}: {why}, so the $safe* name is not proof of anything")


def violations_in(rel, text):
    """Sites in `rel` that break the convention, as human-readable strings."""
    if rel in FILE_EXEMPT:
        return []
    bad = []
    assigns = safe_var_assignments(text)
    for _, line_no, stripped, arg in scan_source(rel, text):
        if (rel, stripped) in SITE_EXEMPT:
            continue

        # Rule 1: no lexical consumer-home path may reach the filesystem, in ANY
        # argument -- source or destination. This is the rule that would have caught
        # the prepared-phase backup read.
        m = MUTATING.search(strip_ps_comments(stripped))
        if LEXICAL_HOME.search(stripped):
            bad.append(f"{rel}:{line_no}: a lexical consumer-home path reaches the "
                       f"filesystem un-resolved: {stripped}")
            continue

        # Rule 2: the argument RECEIVING the mutation is a transitively-gated $safe*.
        if arg is None:
            bad.append(f"{rel}:{line_no}: cannot identify the path argument: {stripped}")
            continue
        # `"$safeTarget.$PID.tmp"` and a bare `$safeTarget` both count; a raw
        # expression, a lexical join, or any other variable does not.
        _check_expression(rel, line_no, stripped, arg, assigns, bad, "path")

        # Rule 3: for Copy-Item/Move-Item the SOURCE is checked too -- but only for
        # the lexical-home shape (rule 1), since a dist-file source is legitimate.
        # A source naming a $safe* variable must still be gated transitively.
        if m and m.group("cmdlet") in DESTINATION_IS_TARGET:
            sm = SOURCE_ARG.search(stripped, m.end())
            src = (sm.group("arg") or sm.group("arg2")).strip() if sm else None
            if src and re.search(r"\$safe[A-Za-z0-9_]*", src, re.I):
                _check_expression(rel, line_no, stripped, src, assigns, bad, "source")
    return bad


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #

def test_every_mutating_primitive_resolves_through_the_choke_point():
    files = tracked_ps1()
    assert files, "git ls-files matched no .ps1 -- the gate would be vacuous"
    bad = []
    for rel in files:
        bad.extend(violations_in(rel, (REPO_ROOT / rel).read_text(encoding="utf-8")))
    assert not bad, (
        "mutating filesystem primitives that do not resolve through the path choke "
        "point (see this module's docstring; add an allowlist entry ONLY with a "
        "reason that the site cannot touch a consumer home):\n  " + "\n  ".join(bad))


def test_the_sweep_actually_finds_the_known_sites():
    """The gate is only meaningful if the scanner sees real code.

    A regex that matched nothing would make the assertion above pass over a
    completely unguarded codebase."""
    migrate = (REPO_ROOT / "tools" / "migrate-legacy-install.ps1").read_text(encoding="utf-8")
    sites = scan_source("tools/migrate-legacy-install.ps1", migrate)
    assert len(sites) >= 10, f"scanner found only {len(sites)} mutating sites"
    assert any("Copy-Item" in s[2] for s in sites)
    assert any("Remove-Item" in s[2] for s in sites)


def test_gate_reds_on_a_planted_unguarded_mutation():
    """Red-on-garbage anchor.

    The planted source is BUILT AT RUNTIME from fragments so this test file does not
    contain a literal unguarded mutating call -- otherwise the sweep above, which
    walks git-tracked files, would eventually trip over this module's own text if it
    were ever renamed to .ps1, and the anchor would be self-defeating."""
    plant = "Copy-Item " + "-LiteralPath " + "$rawPath " + "-Destination $x -Force"
    bad = violations_in("tools/migrate-legacy-install.ps1", plant)
    assert bad, "the sweep did not flag a planted unguarded mutation"
    assert "not a $safe* value" in bad[0]


def test_gate_reds_on_a_safe_name_assigned_from_an_ungated_expression():
    """The second half of the convention: naming a variable $safe* proves nothing
    unless it came from a resolver. Without this, the gate would be defeated by a
    one-line rename."""
    plant = ("$safeTarget = " + "$rawPath\n"
             + "Remove-Item " + "-LiteralPath " + "$safeTarget -Force")
    bad = violations_in("tools/migrate-legacy-install.ps1", plant)
    assert bad, "a $safe* name assigned from an ungated expression was accepted"
    assert "ungated expression" in bad[0]


def test_gate_accepts_a_properly_resolved_mutation():
    """The complement: correctly gated code must PASS, or the gate would be a
    blanket refusal that says nothing about correctness."""
    good = ("$safeTarget = " + "Resolve-HomeTarget -RelPosix $rel -Operation 'x'\n"
            + "Remove-Item " + "-LiteralPath " + "$safeTarget -Force")
    assert violations_in("tools/migrate-legacy-install.ps1", good) == []


def test_gate_would_have_caught_the_five_escaped_sites():
    """The sharpest anchor available: the EXACT source lines that escaped three
    review rounds must be flagged by this gate.

    A structural gate written after the fact is only credible if it demonstrably
    catches the defects that motivated it. Each string below is a verbatim
    reconstruction of a shipped line, assembled from fragments so this module's own
    text carries no unguarded mutating call."""
    escaped = {
        # iteration 2's decisive miss: the PREPARED-phase backup materialization,
        # present since the first Step 47 commit.
        "prepared-phase backup":
            "Copy-Item " + "-LiteralPath " + "(Join-HomePath $a.rel_path) "
            + "-Destination $payload -Force",
        # Remove-EmptiedRetiredDirs.
        "emptied retired dir":
            "Remove-Item " + "-LiteralPath " + "$d -Force",
        # iteration 1: the retire delete, whose sibling install branch was gated.
        "retire delete":
            "Remove-Item " + "-LiteralPath " + "$targetAbs -Force",
        # iteration 1: undo restoring a backup payload over an ungated target.
        "undo restore":
            "Copy-Item " + "-LiteralPath " + "$payload -Destination $targetAbs -Force",
        # the ledger rewrite before it was gated.
        "ledger rewrite":
            "Move-Item " + "-LiteralPath " + "$tmp -Destination $targetAbs -Force",
    }
    for label, line in escaped.items():
        bad = violations_in("tools/migrate-legacy-install.ps1", line)
        assert bad, f"the gate would NOT have caught the {label} site: {line}"


def test_gate_catches_a_lexical_home_path_used_as_a_COPY_SOURCE():
    """The exact defect that escaped three review rounds.

    An earlier version of this gate inspected only -Destination for Copy-Item,
    reasoning that the source is "legitimately a generated dist file". The decisive
    defect was a consumer-home pre-image read through the lexical joiner, with a
    perfectly gated destination -- so the gate returned zero violations on the very
    line it was written to prevent. Assembled from fragments so this module's own
    text carries no unguarded mutating call.
    """
    line = ("Copy-Item " + "-LiteralPath " + "(Join-HomePathLexical $a.rel_path) "
            + "-Destination $safePayload -Force")
    src = "$safePayload = Resolve-TxPayloadPath $a.backup_payload\n" + line
    bad = violations_in("tools/migrate-legacy-install.ps1", src)
    assert bad, "the gate must flag a lexical consumer-home path used as a copy SOURCE"
    assert any("lexical consumer-home path" in b for b in bad), bad


def test_gate_follows_safe_alias_chains_transitively():
    """A two-hop alias chain must not launder a raw path into a trusted name.

    `$safeA = $rawPath; $safeB = $safeA` previously produced zero violations, so the
    gate could be defeated by renaming -- which made "a sixth unguarded site is
    impossible" untrue.
    """
    two_hop = ("$safeA = $rawPath\n"
               "$safeB = $safeA\n"
               + "Remove-Item " + "-LiteralPath " + "$safeB -Force")
    bad = violations_in("tools/migrate-legacy-install.ps1", two_hop)
    assert bad, "the gate must follow $safe* alias chains to their origin"
    assert any("derives from" in b for b in bad), bad

    # ...and a chain that bottoms out in a real resolver is still accepted.
    good = ("$safeA = Resolve-HomeTarget -RelPosix $rel\n"
            "$safeB = $safeA\n"
            + "Remove-Item " + "-LiteralPath " + "$safeB -Force")
    assert violations_in("tools/migrate-legacy-install.ps1", good) == []

    # An assignment cycle proves nothing and must not be mistaken for gated.
    cycle = ("$safeA = $safeB\n"
             "$safeB = $safeA\n"
             + "Remove-Item " + "-LiteralPath " + "$safeA -Force")
    assert violations_in("tools/migrate-legacy-install.ps1", cycle), "a cycle is not proof"


def test_gate_catches_a_gated_value_mixed_with_an_unresolved_operand():
    """A gated PARENT does not make the whole expression gated.

    `$safeT = $safeBase + $rawSuffix` splices unresolved text onto a resolved path,
    so the result is no longer proven inside the home -- but an earlier version
    accepted it because it found one `$safe*` ancestor that traced to a resolver.
    """
    for rhs in ("$safeBase + $rawSuffix", "Join-Path $safeBase $rawSuffix",
                '"$safeBase\\$rawSuffix"'):
        src = ("$safeBase = Resolve-HomeTarget -RelPosix $rel\n"
               "$safeT = " + rhs + "\n"
               + "Remove-Item " + "-LiteralPath " + "$safeT -Force")
        bad = violations_in("tools/migrate-legacy-install.ps1", src)
        assert bad, f"the gate must reject a gated value mixed with an unresolved operand: {rhs}"
        assert any("unresolved operand" in b for b in bad), bad

    # ...and a purely-gated composition is still accepted.
    ok = ("$safeBase = Resolve-HomeTarget -RelPosix $rel\n"
          '$safeT = "$safeBase.$PID.tmp"\n'
          + "Remove-Item " + "-LiteralPath " + "$safeT -Force")
    assert violations_in("tools/migrate-legacy-install.ps1", ok) == []


def test_gate_knows_the_cmdlet_aliases():
    """`rm`/`del`/`cpi` are the same cmdlets. A gate that only knows the long names
    can be sidestepped by accident as easily as on purpose."""
    for verb in ("rm", "del", "ri", "mv", "cpi", "Rename-Item"):
        src = verb + " " + "-LiteralPath " + "$rawPath -Force"
        bad = violations_in("tools/migrate-legacy-install.ps1", src)
        assert bad, f"the gate must recognise '{verb}' as a mutating primitive"


def test_allowlist_entries_are_live_and_carry_a_reason():
    """A stale allowlist entry is a silent hole: it would keep excusing a site that
    no longer exists while nobody notices the real one moved."""
    tracked = set(tracked_ps1())
    for rel, reason in FILE_EXEMPT.items():
        assert rel in tracked, f"FILE_EXEMPT names an untracked file: {rel}"
        assert len(reason) > 40, f"FILE_EXEMPT[{rel}] needs a real reason"
    seen = {}
    for rel in tracked:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for site in scan_source(rel, text):
            seen[(site[0], site[2])] = True
    for key, reason in SITE_EXEMPT.items():
        assert len(reason) > 40, f"SITE_EXEMPT[{key}] needs a real reason"
        assert key in seen, (
            f"SITE_EXEMPT entry no longer matches any real site (stale): {key}")
