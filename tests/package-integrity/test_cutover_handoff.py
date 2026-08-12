"""Consumer-cutover handoff STRUCTURE gate (Step 48 of
documentation/host-native-discovery-cutover-plan.md).

Validates the shape of documentation/coding-root-cutover-handoff.md and the two
documents Step 48 corrects (documentation/migration.md,
documentation/provider-neutral-skill-mesh-plan.md) -- and closes the one coverage
hole the sibling gates leave open: a backticked COMMAND or PATH token inside a
documentation/*.md is validated NOWHERE today.

What this gate asserts:
- The handoff declares an inspection step, a backup requirement, a rollback
  command, a host-acceptance gate, and a separate-coding-root-commit step -- and
  declares them in that ORDER. Relative position is asserted, not mere presence:
  a document that mentions rollback only after the acceptance gate has told the
  operator to test first and learn the escape hatch second.
- Every command block names the repository it runs in AND the output that means
  it worked (`**Run in:**` above, `**Expect:**` below). All three PowerShell
  fence spellings count -- relabelling ```powershell to ```pwsh once dropped a
  block out of both command gates silently.
- Every backticked repo-relative tool/test path token resolves on disk; every
  flag named on a `.ps1` invocation is declared in that script's own `param()`
  block; and every flag VALUE is inside that parameter's `[ValidateSet(...)]`
  when it declares one. Names alone were not enough: `-Provider both` is legal
  for the builder and illegal for the installer, so only a value check separates
  them.
- The two meanings of the migrator's exit `3` stay distinct (telling an operator
  to restore a backup in the preserved-path case is destructive advice) -- and
  that assertion is SCOPED to the exit-3 section, because as a whole-document
  substring search it was satisfied by a different sentence than the one it
  guards. The `failed_incomplete` status keeps a live remedy (it is unresolved
  AND terminal, so both -Resume and -Rollback refuse it). An irreversible delete
  is preceded by a copy into the backup. The retirement rule stays a positive
  `managed` allowlist. README.md and migration.md do not ship contradictory
  status for Step 48. And the handoff never instructs a command that would prompt
  or a linter/typechecker this repository deliberately does not have
  (documentation/architecture.md section 8.4).

- No status-bearing markdown document carries a banned stale-status phrase in
  prose (Step 69 of documentation/host-parity-repair-plan.md). Scope is README.md
  + CLAUDE.md + documentation/**/*.md with NO file excluded, and backticked
  CITATIONS of a banned phrase are exempt so the documents that specify the ban
  can satisfy it.

What this gate deliberately does NOT do:
- It never EXECUTES a handoff step -- no subprocess, no PowerShell, no network.
  test_this_gate_executes_nothing enforces that against this module's own source.
- It never asserts that host acceptance passed. That is operator evidence from
  Steps 43, 45, 49, and 50; a green suite is a precondition, never a substitute.
- The stale-status sweep decides ONE thing: whether a literal phrase appears in
  prose. It does NOT decide the semantic class "a document presents completed
  cutover-path work as outstanding" -- paraphrase defeats any literal list, and
  human review owns that class. See the comment block above
  _STALE_CUTOVER_STATUS_PHRASES, and the decision record at
  documentation/step-69-doc-reconciliation-decisions.md.

Scoping notes (both deliberate):
- Markdown LINKS are already covered by
  tools/release_checks.py::find_broken_local_links(), wired to README.md +
  documentation/**/*.md by test_release_gates.py::_doc_paths(). It is imported
  here, never re-implemented; this module adds only the token half.
- The token sweep enumerates README.md + documentation/**/*.md and skips
  documents whose name ends in `-plan.md`: a plan legitimately names artifacts it
  has not built yet, so asserting their existence would make plans unwritable.
  Path tokens are matched only under `tools/`, `runtime/`, `config/`, and
  `tests/` -- the executable surface, where an unresolvable token is always a
  defect. `documentation/` and `skills/` tokens are excluded on purpose: the
  manifest declares `skills/_shared/` as an EVENTUAL canonical home that does not
  exist yet (architecture.md), and the legacy-source mapping tables name paths
  that are legitimately absent.

Every check is written so it goes RED on a planted defect -- proven by the anchor
tests below (a gate that cannot go red is worthless;
.claude/rules/measurement-validity.md).

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone
(`python tests/package-integrity/test_cutover_handoff.py`).
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_DIR = REPO_ROOT / "documentation"
HANDOFF = DOC_DIR / "coding-root-cutover-handoff.md"
MIGRATION = DOC_DIR / "migration.md"
NEUTRAL_PLAN = DOC_DIR / "provider-neutral-skill-mesh-plan.md"
CUTOVER_PLAN = DOC_DIR / "host-native-discovery-cutover-plan.md"
README = REPO_ROOT / "README.md"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import release_checks  # noqa: E402

# Discovery-root tokens assembled from parts: tests/router/test_no_claude_dependency.py
# fails a load-bearing ".claude/<path>" literal in executable code under tests/.
_DOTCLAUDE = "." + "claude"
CLAUDE_ROOT = _DOTCLAUDE + "/skills"
LEGACY_GPT_ROOT = _DOTCLAUDE + "/skills-gpt"
GITHUB_ROOT = ".github/skills"
LEGACY_ROUTER = _DOTCLAUDE + "/lib/skill-router.ps1"


def _read(path):
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Ordered required steps
# --------------------------------------------------------------------------- #
#
# (label, marker) -- marker is matched case-insensitively and must appear in this
# order. The labels are the five units the plan's Done-when names.

REQUIRED_STEPS = (
    ("inspection step", "inspect the consumer home"),
    ("backup requirement", "external backup directory"),
    ("acceptance-probe revert", "revert the acceptance probe"),
    ("rollback command", "roll back the migration"),
    ("host-acceptance gate", "host-acceptance gate"),
    ("separate coding-root commit", "commit the coding-root change"),
)


def ordering_defects(text):
    """Missing OR mis-ordered required steps. Empty list == correct.

    Position is the first occurrence of each marker; a step that never appears is
    reported as missing rather than silently sorting to the end."""
    low = text.lower()
    defects = []
    positions = []
    for label, marker in REQUIRED_STEPS:
        idx = low.find(marker)
        if idx < 0:
            defects.append(f"missing required step: {label} (no '{marker}')")
        else:
            positions.append((label, idx))
    for (prev_label, prev_idx), (label, idx) in zip(positions, positions[1:]):
        if idx < prev_idx:
            defects.append(
                f"out of order: '{label}' appears before '{prev_label}' "
                f"(offsets {idx} < {prev_idx})")
    return defects


def _synthetic_ordered_doc():
    return "\n\n".join(f"## {marker.title()}\nbody" for _, marker in REQUIRED_STEPS)


def test_ordering_gate_reds_on_reorder_and_on_omission():
    # ANCHOR: the ordering gate must stay silent on a correctly ordered document,
    # flag a swap of two required steps, and flag an omission.
    ordered = _synthetic_ordered_doc()
    assert ordering_defects(ordered) == [], ordering_defects(ordered)

    labels = [m for _, m in REQUIRED_STEPS]
    swapped_order = labels[:2] + [labels[3], labels[2]] + labels[4:]
    swapped = "\n\n".join(f"## {m.title()}\nbody" for m in swapped_order)
    assert ordering_defects(swapped), \
        "ordering gate failed to flag a swapped host-acceptance/rollback pair"

    dropped = "\n\n".join(f"## {m.title()}\nbody" for m in labels[1:])
    assert any("missing" in d for d in ordering_defects(dropped)), \
        "ordering gate failed to flag an omitted required step"


def test_handoff_exists():
    assert HANDOFF.is_file(), f"missing cutover handoff: {HANDOFF}"


def test_handoff_declares_every_required_step_in_order():
    defects = ordering_defects(_read(HANDOFF))
    assert not defects, "handoff step contract violated:\n" + "\n".join(defects)


_PROBE_REVERT_HEADING = "## 10. Revert the acceptance probe before any rollback"
_ROLLBACK_HEADING = "## 11. Roll back the migration"


def probe_revert_ordering_defects(text):
    """The probe revert must be instructed BEFORE the rollback section, and it must
    say how to prove the revert landed.

    This is not a style point. tools/migrate-legacy-install.ps1's
    Assert-OurBytesAtTarget refuses to undo any path whose bytes are no longer the
    ones the transaction wrote, so a rollback run while an acceptance probe is still
    appended to an installed SKILL.md exits 3 and strands the transaction in
    failed_incomplete -- a state -Resume, -Rollback and a bare -Apply all refuse.
    Reproduced end to end before this assertion was written. A handoff that presents
    these two in the other order teaches the operator to destroy their own rollback
    rehearsal."""
    low = text.lower()
    revert_at = low.find(_PROBE_REVERT_HEADING.lower())
    rollback_at = low.find(_ROLLBACK_HEADING.lower())
    defects = []
    if revert_at < 0:
        defects.append(f"missing probe-revert section: {_PROBE_REVERT_HEADING!r}")
    if rollback_at < 0:
        defects.append(f"missing rollback section: {_ROLLBACK_HEADING!r}")
    if defects:
        return defects
    if revert_at > rollback_at:
        defects.append(
            "the probe-revert section appears AFTER the rollback section "
            f"(offsets {revert_at} > {rollback_at}) -- rollback over a probed file "
            "exits 3 into failed_incomplete")
    section = section_block(text, _PROBE_REVERT_HEADING, stop_prefixes=("\n## ",))
    slow = re.sub(r"\s+", " ", section).lower()
    for needle, why in (
            ("backup-manifest.json", "does not name the manifest the restore is verified against"),
            ("installed_files", "does not name the manifest array holding the installed hashes"),
            ("sha256", "does not require a hash comparison"),
            ("match=true", "states no PASS condition for the verification"),
    ):
        if needle not in slow:
            defects.append(f"the probe-revert section {why}")
    return defects


def test_probe_revert_ordering_gate_reds_on_the_reversed_order():
    # ANCHOR: the gate must accept the real document, flag the two sections in the
    # wrong order, and flag a revert section that proves nothing.
    text = _read(HANDOFF)
    assert probe_revert_ordering_defects(text) == [], probe_revert_ordering_defects(text)

    revert = section_block(text, _PROBE_REVERT_HEADING, stop_prefixes=("\n## ",))
    rollback = section_block(text, _ROLLBACK_HEADING, stop_prefixes=("\n## ",))
    assert revert and rollback, "both sections must be sliceable for this anchor to mean anything"
    # section_block stops just before the newline that opens the next heading, so
    # the two slices are joined by exactly one "\n" in the source.
    original = revert + "\n" + rollback
    assert original in text, "the two sections are not adjacent -- the swap probe is invalid"
    swapped = text.replace(original, rollback + "\n" + revert)
    assert swapped != text, "the swap probe did not change the document"
    assert any("AFTER the rollback section" in d
               for d in probe_revert_ordering_defects(swapped)), \
        "the ordering gate accepts a probe revert that follows the rollback section"

    gutted = text.replace(revert, _PROBE_REVERT_HEADING + "\n\nRemove the probe.\n\n")
    assert any("hash comparison" in d or "PASS condition" in d
               for d in probe_revert_ordering_defects(gutted)), \
        "the gate accepts a revert section that never verifies the restore"


def test_handoff_reverts_the_probe_before_it_rolls_back():
    defects = probe_revert_ordering_defects(_read(HANDOFF))
    assert not defects, "probe-revert ordering violated:\n" + "\n".join(defects)


# `-Apply` as a FLAG, not as the tail of an ordinary word. An unanchored
# `low.find("-apply")` matched inside "re-apply" and turned the ordering gate red
# on innocuous prose; `\B` fails at the word boundary between "re" and "-apply"
# but holds after a backtick, a space, or a quote.
_APPLY_FLAG = re.compile(r"\B-apply\b")


def apply_flag_index(low):
    """Offset of the first `-Apply` FLAG mention, or -1."""
    m = _APPLY_FLAG.search(low)
    return m.start() if m else -1


def test_apply_flag_index_is_anchored_to_the_flag():
    # ANCHOR: the ordering gate reads a position out of this, so a substring match
    # inside an ordinary word would make it report a bogus offset.
    assert apply_flag_index("you may re-apply it later") == -1, \
        "-Apply detection matches inside 're-apply'"
    assert apply_flag_index("reapply and preapply") == -1
    assert apply_flag_index("and only then `-apply`.") >= 0
    assert apply_flag_index("run it with -apply once") >= 0
    assert apply_flag_index("you may re-apply it later; then `-apply`") > 0


def test_migration_doc_declares_every_required_step_in_order_or_delegates():
    """migration.md is descriptive, not procedural, so it satisfies the contract by
    DELEGATING: it must link the handoff and must present inspection before apply.
    A migration doc that describes the mutation before the preflight teaches the
    wrong order even if the tooling enforces the right one."""
    text = _read(MIGRATION)
    low = text.lower()
    assert "coding-root-cutover-handoff.md" in text, \
        "migration.md must point at the cutover handoff"
    inspect_at = low.find("inspect-host-install.ps1")
    apply_at = apply_flag_index(low)
    assert inspect_at >= 0, "migration.md never names the read-only inspector"
    assert apply_at >= 0, "migration.md never names the migrator's -Apply mode"
    assert inspect_at < apply_at, \
        "migration.md presents -Apply before the read-only inspection preflight"
    assert "backupdir" in low.replace("-", ""), \
        "migration.md must state the external backup requirement"


# --------------------------------------------------------------------------- #
# Command blocks name their repository and their expected output
# --------------------------------------------------------------------------- #

_RUN_IN = "**Run in:**"
_EXPECT = "**Expect:**"
_LOOKBACK = 4
_LOOKAHEAD = 4


# Every spelling of a PowerShell fence this repository's documents may use. Only
# `powershell` was accepted once, which made relabelling a fence to ```pwsh a
# silent way to drop a block out of BOTH command gates -- and the handoff's own
# "Command spelling" section tells the operator commands are `pwsh`, so that
# relabel is the natural next edit.
_PS_FENCE = re.compile(r"```(?:powershell|pwsh|ps1)\b", re.I)


def command_blocks(text):
    """(open, close) line indices of every PowerShell fenced block."""
    lines = text.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        if _PS_FENCE.match(lines[i].strip()):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            blocks.append((i, j))
            i = j + 1
        else:
            i += 1
    return blocks


def block_contract_defects(text):
    """Every command block must be introduced by a `**Run in:**` line naming its
    target repository and followed by an `**Expect:**` line stating the output
    that means it worked. A command the operator cannot verify is a defect."""
    lines = text.splitlines()
    defects = []
    for open_i, close_i in command_blocks(text):
        before = lines[max(0, open_i - _LOOKBACK):open_i]
        after = lines[close_i + 1:close_i + 1 + _LOOKAHEAD]
        if not any(ln.strip().startswith(_RUN_IN) for ln in before):
            defects.append(f"line {open_i + 1}: command block has no '{_RUN_IN}' line above it")
        if not any(ln.strip().startswith(_EXPECT) for ln in after):
            defects.append(f"line {open_i + 1}: command block has no '{_EXPECT}' line below it")
    return defects


def test_block_contract_gate_reds_on_missing_run_in_or_expect():
    # ANCHOR: the contract gate must accept a well-formed block and flag each half.
    good = ("**Run in:** `<consumer-home>`\n\n```powershell\nGet-Date\n```\n\n"
            "**Expect:** the current date.\n")
    assert block_contract_defects(good) == [], block_contract_defects(good)
    no_expect = "**Run in:** `<consumer-home>`\n\n```powershell\nGet-Date\n```\n\nsome prose.\n"
    assert any(_EXPECT in d for d in block_contract_defects(no_expect)), \
        "gate failed to flag a command block with no expected output"
    no_run_in = "prose.\n\n```powershell\nGet-Date\n```\n\n**Expect:** the current date.\n"
    assert any(_RUN_IN in d for d in block_contract_defects(no_run_in)), \
        "gate failed to flag a command block that names no target repository"

    # ...and a relabelled fence must NOT make a block invisible to the gate. A
    # ```pwsh block with no **Expect:** is still a defect.
    for fence in ("pwsh", "ps1", "PowerShell"):
        relabelled = f"prose.\n\n```{fence}\nGet-Date\n```\n\nmore prose.\n"
        assert len(command_blocks(relabelled)) == 1, \
            f"a ```{fence} block is invisible to the command-block extractor"
        assert block_contract_defects(relabelled), \
            f"a ```{fence} block escapes the Run-in/Expect contract"


def test_handoff_command_blocks_name_repo_and_expected_output():
    text = _read(HANDOFF)
    blocks = command_blocks(text)
    assert blocks, "the handoff declares no command blocks -- the gate would be vacuous"
    defects = block_contract_defects(text)
    assert not defects, "handoff command-block contract violated:\n" + "\n".join(defects)


# --------------------------------------------------------------------------- #
# Token resolution: every named command / path must resolve
# --------------------------------------------------------------------------- #

_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_FENCE = re.compile(r"^\s*```")

# The executable surface only -- see the module docstring for why `documentation/`
# and `skills/` tokens are out of scope.
_TOKEN_PREFIXES = ("tools", "runtime", "config", "tests")
_PATH_TOKEN = re.compile(
    r"^(?:" + "|".join(_TOKEN_PREFIXES) + r")[\\/][A-Za-z0-9._\\/-]+$")

# `-File` and friends belong to the PowerShell host, not to the invoked script.
_HOST_FLAGS = {"file", "noprofile", "noninteractive", "executionpolicy",
               "command", "nologo", "encodedcommand", "version", "help"}
_PS1_IN_SPAN = re.compile(
    r"(?:^|\s)((?:tools|runtime)[\\/][A-Za-z0-9._-]+\.ps1)(?=\s|$)")
_FLAG = re.compile(r"(?<![\w:/\\.-])-([A-Za-z][A-Za-z0-9]*)")


def code_spans(text):
    """Every fenced-block line and every inline `code` span."""
    spans = []
    in_fence = False
    for line in text.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            spans.append(line)
        else:
            spans.extend(_INLINE_CODE.findall(line))
    return spans


def _clean_word(word):
    w = word.strip().strip("`'\"()[]{}<>|")
    w = w.split(":", 1)[0]          # drop `:327-342` line refs and `::func` suffixes
    return w.rstrip(".,;:)]}")


def path_tokens(spans):
    """Repo-relative executable-surface path tokens. Placeholder-bearing tokens
    (`<...>`) and globs are skipped -- they name a shape, not a file."""
    found = []
    for span in spans:
        for word in re.split(r"[\s,;]+", span):
            w = _clean_word(word)
            if not w or any(c in w for c in "<>*"):
                continue
            if _PATH_TOKEN.match(w):
                found.append(w)
    return found


def unresolvable_path_tokens(spans, root):
    return sorted({t for t in path_tokens(spans)
                   if not (root / t.replace("\\", "/")).exists()})


def _param_block(text):
    """The balanced body of a script's top-level `param(...)`, or None."""
    m = re.search(r"(?m)^param\s*\(", text)
    if not m:
        return None
    start = text.index("(", m.start())
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


# One ordered pass over the param block. `[ValidateSet(...)]` and `[Alias(...)]`
# decorate the NEXT `$Variable`, which is the order PowerShell binds them in, so
# they accumulate and flush onto that variable.
_ATTR_OR_VAR = re.compile(
    r"ValidateSet\s*\(([^)]*)\)|Alias\s*\(([^)]*)\)|\$([A-Za-z_]\w*)", re.I)
# `[Parameter(Mandatory = $true)]` is not a parameter declaration; treating `$true`
# as one would flush the pending attributes onto the wrong name.
_PS_LITERAL_VARS = {"true", "false", "null"}


def _literal_set(group):
    return {a.strip().strip("'\"").lower() for a in group.split(",") if a.strip()}


def _parse_param_block(ps1_path):
    """(names, value_sets) for a script's `param(...)` block, lowercased.

    `names` is every parameter name and alias. `value_sets` maps each name/alias
    that carries a `[ValidateSet(...)]` to its legal values -- flag NAMES alone
    were validated once, so a planted `-Provider both` on the installer passed
    even though it declares [ValidateSet('claude','gpt')], and `-Provider both`
    is legitimate two sections earlier for the BUILDER, which does declare it.

    (None, None) when the file declares no param block at all -- a dot-sourced
    library, which has no CLI surface to validate against."""
    block = _param_block(ps1_path.read_text(encoding="utf-8"))
    if block is None:
        return None, None
    names = set()
    value_sets = {}
    pending_values = None
    pending_aliases = set()
    for m in _ATTR_OR_VAR.finditer(block):
        validate_group, alias_group, var = m.group(1), m.group(2), m.group(3)
        if validate_group is not None:
            pending_values = _literal_set(validate_group)
        elif alias_group is not None:
            pending_aliases |= _literal_set(alias_group)
        else:
            name = var.lower()
            if name in _PS_LITERAL_VARS:
                continue
            keys = {name} | pending_aliases
            names |= keys
            if pending_values is not None:
                for key in keys:
                    value_sets[key] = set(pending_values)
            pending_values = None
            pending_aliases = set()
    return names, value_sets


def declared_parameters(ps1_path):
    """Every parameter name and alias in a script's top-level `param(...)` block,
    lowercased. None when the file declares no param block at all."""
    return _parse_param_block(ps1_path)[0]


def declared_value_sets(ps1_path):
    """{parameter-or-alias: {legal values}} for every `[ValidateSet(...)]` in the
    script's param block. `{}` when it declares none; None when there is no param
    block at all."""
    return _parse_param_block(ps1_path)[1]


_PLACEHOLDER = re.compile(r"<[^<>]*>")


def _command_head(span):
    """The part of a command that belongs to the invoked script: placeholders
    neutralised first, THEN truncated at the first pipe / redirect / statement
    separator so a downstream cmdlet's flags are never attributed to the script.

    Order is load-bearing and was a real defect here: truncating first made the
    `>` inside `'<consumer-home>'` look like a redirect, so every flag after the
    first placeholder became invisible and the flag gate silently checked only
    `-Home`. Proven by test_token_gate_reds_on_unresolvable_path_and_bad_flag's
    trailing-flag case."""
    head = _PLACEHOLDER.sub("PLACEHOLDER", span)
    return re.split(r"[|>;]", head)[0]


def _is_invocation(head):
    """True when a span RUNS a script rather than merely citing it. A bare
    `tools/install-skill-mesh.ps1` in prose is a citation and carries no arguments
    to check; `pwsh -File ...` or any span bearing a script flag is a command."""
    if re.match(r"\s*(?:pwsh|powershell)\b", head, re.I):
        return True
    return bool({f.lower() for f in _FLAG.findall(head)} - _HOST_FLAGS)


def script_invocations(spans):
    """(command_head, script_rel_path, original_span) for every span that invokes a
    repo `.ps1`. The original span is carried so failure messages quote what the
    document actually says, not the placeholder-neutralised head."""
    found = []
    for span in spans:
        head = _command_head(span)
        m = _PS1_IN_SPAN.search(head)
        if m:
            found.append((head, m.group(1).replace("\\", "/"), span.strip()))
    return found


_BARE_FLAG = re.compile(r"^-([A-Za-z][A-Za-z0-9]*)$")


def flag_value_pairs(head):
    """(flag, value-or-None) for each `-Flag [value]` on a command head. The value
    is the following token when that token is not itself a flag."""
    tokens = [t for t in re.split(r"\s+", head.strip()) if t]
    pairs = []
    for i, token in enumerate(tokens):
        m = _BARE_FLAG.match(token)
        if not m:
            continue
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        value = nxt if (nxt is not None and not nxt.startswith("-")) else None
        pairs.append((m.group(1), value))
    return pairs


def _checkable_value(value):
    """The comparable literal behind a documented argument, or None when it is a
    placeholder / variable / path rather than a fixed vocabulary word."""
    if value is None:
        return None
    v = value.strip().strip("'\"").rstrip(".,;:").lower()
    if not v or "placeholder" in v or "$" in v or "<" in v or "/" in v or "\\" in v:
        return None
    return v


def undeclared_flag_defects(spans, root):
    """A flag named on a documented `.ps1` invocation that the script does not
    declare, OR a flag VALUE outside that parameter's `[ValidateSet(...)]`. Both
    are classes an operator cannot recover from: PowerShell answers them with "A
    parameter cannot be found that matches parameter name '...'" / "does not
    belong to the set ...", after the operator has already committed to the
    sequence."""
    defects = []
    for head, rel, shown in script_invocations(spans):
        script = root / rel
        if not script.is_file():
            defects.append(f"`{shown}` -> script does not exist: {rel}")
            continue
        declared, value_sets = _parse_param_block(script)
        if declared is None:
            # dot-sourced library: ANY flag on it is a defect
            declared, value_sets = set(), {}
        for flag in _FLAG.findall(head):
            if flag.lower() in _HOST_FLAGS or flag.lower() in declared:
                continue
            defects.append(f"`{shown}` -> -{flag} is not a parameter of {rel}")
        for flag, raw in flag_value_pairs(head):
            legal = value_sets.get(flag.lower())
            if not legal:
                continue
            value = _checkable_value(raw)
            if value is None or value in legal:
                continue
            defects.append(
                f"`{shown}` -> -{flag} {raw} is not one of {sorted(legal)} "
                f"in {rel}")
    return defects


def scanned_docs():
    """README.md + documentation/**/*.md, minus plan documents (see docstring).
    Enumerated from the filesystem, never hand-listed."""
    docs = [README] + sorted(DOC_DIR.rglob("*.md"))
    return [d for d in docs if d.is_file() and not d.name.endswith("-plan.md")]


def test_token_gate_reds_on_unresolvable_path_and_bad_flag():
    # ANCHOR: both halves must go red on a planted defect and stay silent on the
    # real, correct spellings.
    real = ["pwsh -File tools/inspect-host-install.ps1 -Home '<consumer-home>' -Format json"]
    assert unresolvable_path_tokens(real, REPO_ROOT) == []
    assert undeclared_flag_defects(real, REPO_ROOT) == []

    missing_path = ["pwsh -File tools/does-not-exist.ps1 -Home x"]
    assert unresolvable_path_tokens(missing_path, REPO_ROOT), \
        "token gate failed to flag a path that does not resolve"
    assert any("does not exist" in d for d in undeclared_flag_defects(missing_path, REPO_ROOT))

    bad_flag = ["pwsh -File tools/inspect-host-install.ps1 -Home x -Verify"]
    defects = undeclared_flag_defects(bad_flag, REPO_ROOT)
    assert any("-Verify" in d for d in defects), \
        "flag gate failed to flag a parameter the script does not declare"

    # ...including a flag that TRAILS a placeholder argument. Truncating the span
    # before neutralising `<...>` made the `>` read as a redirect and hid every
    # later flag -- the gate then inspected one flag per command and looked green.
    trailing = ["pwsh -File tools/migrate-legacy-install.ps1 -Home '<consumer-home>' "
                "-DistDir '<dist-dir>' -BackupDir '<backup-dir>' -ApplyNow"]
    assert any("-ApplyNow" in d for d in undeclared_flag_defects(trailing, REPO_ROOT)), \
        "flag gate stops scanning at the first placeholder argument"
    legit = ["pwsh -File tools/migrate-legacy-install.ps1 -Home '<consumer-home>' "
             "-DistDir '<dist-dir>' -BackupDir '<backup-dir>' -Apply"]
    assert undeclared_flag_defects(legit, REPO_ROOT) == []
    # A real pipeline still stops at the pipe: the downstream cmdlet's flags are
    # not the script's.
    piped = ["pwsh -File tools/inspect-host-install.ps1 -Home '<consumer-home>' "
             "-Format json | Set-Content -LiteralPath out.json -Encoding utf8"]
    assert undeclared_flag_defects(piped, REPO_ROOT) == []

    # The alias half: -Home is an ALIAS of $TargetHome and must stay legal.
    params = declared_parameters(REPO_ROOT / "tools" / "inspect-host-install.ps1")
    assert params is not None
    assert {"home", "destination", "targethome", "format", "absolutepaths"} <= params
    assert "apply" not in params, \
        "declared_parameters is over-collecting -- the inspector has no -Apply"

    # A dot-sourced library legitimately has no param block.
    assert declared_parameters(REPO_ROOT / "tools" / "skill-mesh-provenance.ps1") is None
    assert declared_value_sets(REPO_ROOT / "tools" / "skill-mesh-provenance.ps1") is None


def test_flag_value_gate_reds_on_a_value_outside_the_scripts_validateset():
    # ANCHOR: names alone are not enough. `-Provider both` is a REAL spelling in
    # this documentation set -- legal for the builder, illegal for the installer --
    # so a gate that checks only the name accepts the broken one.
    installer = REPO_ROOT / "tools" / "install-skill-mesh.ps1"
    builder = REPO_ROOT / "tools" / "build-distributions.ps1"
    assert declared_value_sets(installer)["provider"] == {"claude", "gpt"}
    assert declared_value_sets(installer)["profile"] == {"claude", "gpt"}, \
        "an alias must inherit its parameter's ValidateSet"
    assert declared_value_sets(builder)["provider"] == {"claude", "gpt", "both"}
    assert "targethome" not in declared_value_sets(installer), \
        "declared_value_sets is over-collecting -- -Home has no ValidateSet"

    planted = ["pwsh -File tools/install-skill-mesh.ps1 -Provider both -Home '<install-home>'"]
    defects = undeclared_flag_defects(planted, REPO_ROOT)
    assert any("-Provider both" in d for d in defects), \
        "flag gate accepts a value outside the script's [ValidateSet]"

    # The confusable-but-correct spelling two sections earlier must stay silent.
    legit = ["pwsh -File tools/build-distributions.ps1 -Provider both -OutputDir '<dist-dir>'"]
    assert undeclared_flag_defects(legit, REPO_ROOT) == [], \
        undeclared_flag_defects(legit, REPO_ROOT)

    # A placeholder argument is a shape, not a value, and must never be judged.
    shaped = ["pwsh -File tools/inspect-host-install.ps1 -Home '<consumer-home>' -Format json"]
    assert undeclared_flag_defects(shaped, REPO_ROOT) == []
    bad_format = ["pwsh -File tools/inspect-host-install.ps1 -Home x -Format yaml"]
    assert any("-Format yaml" in d for d in undeclared_flag_defects(bad_format, REPO_ROOT))


def test_documented_path_tokens_all_resolve():
    docs = scanned_docs()
    assert docs, "no documents enumerated -- the gate would be vacuous"
    all_spans = []
    for doc in docs:
        all_spans.extend(code_spans(_read(doc)))
    tokens = path_tokens(all_spans)
    assert len(tokens) >= 20, (
        f"only {len(tokens)} executable-surface path tokens found -- the gate "
        "would be vacuous; did the code-span extractor break?")
    offenders = {}
    for doc in docs:
        bad = unresolvable_path_tokens(code_spans(_read(doc)), REPO_ROOT)
        if bad:
            offenders[str(doc.relative_to(REPO_ROOT))] = bad
    assert not offenders, "documented path token(s) do not resolve: " + repr(offenders)


def test_documented_script_flags_are_all_declared():
    docs = scanned_docs()
    assert docs, "no documents enumerated -- the gate would be vacuous"
    invocations = []
    for doc in docs:
        invocations.extend(script_invocations(code_spans(_read(doc))))
    assert len(invocations) >= 10, (
        f"only {len(invocations)} script invocations found -- the gate would be "
        "vacuous; did the code-span extractor break?")
    offenders = {}
    for doc in docs:
        defects = undeclared_flag_defects(code_spans(_read(doc)), REPO_ROOT)
        if defects:
            offenders[str(doc.relative_to(REPO_ROOT))] = defects
    assert not offenders, "documented command names an undeclared flag: " + repr(offenders)


def test_handoff_alone_is_a_non_vacuous_token_target():
    """The repo-wide sweeps above would still pass if the handoff itself carried no
    commands at all. Pin the handoff's own contribution."""
    spans = code_spans(_read(HANDOFF))
    assert len(path_tokens(spans)) >= 5, "handoff names too few tool paths to gate"
    assert len(script_invocations(spans)) >= 5, "handoff names too few script invocations to gate"
    assert unresolvable_path_tokens(spans, REPO_ROOT) == []
    assert undeclared_flag_defects(spans, REPO_ROOT) == []


def test_handoff_links_resolve_via_the_shared_link_checker():
    """The link half is release_checks' job, imported and reused (never
    re-implemented). Asserted here too so a broken handoff link fails the fast
    package-integrity gate with a message naming this document."""
    offenders = release_checks.find_broken_local_links([HANDOFF, MIGRATION], REPO_ROOT)
    assert not offenders, "broken local link(s):\n" + "\n".join(offenders)


# --------------------------------------------------------------------------- #
# Safety properties of the documented sequence
# --------------------------------------------------------------------------- #

def section_block(text, heading_needle, stop_prefixes=("\n## ", "\n### ", "\n#### ")):
    """The slice of `text` from the heading line containing `heading_needle` to the
    next heading of the same or higher level. `""` when the heading is absent.

    Lifted out of test_previous_plan_step_41_is_marked_superseded's Step-41 slice
    so SAFETY gates can be scoped too: a whole-document substring search is
    satisfied by any sentence anywhere, including one that is not the sentence the
    gate exists to guard."""
    idx = text.lower().find(heading_needle.lower())
    if idx < 0:
        return ""
    start = text.rfind("\n", 0, idx) + 1
    ends = [e for e in (text.find(p, idx) for p in stop_prefixes) if e > 0]
    return text[start:min(ends)] if ends else text[start:]


_EXIT_THREE_HEADING = "### Exit `3` has two meanings"
_EXIT_THREE_NO_RESTORE = "**Do not restore a backup over it**"


def exit_three_defects(text):
    """Exit 3 means EITHER a mutated path could not be restored (recover from the
    backup) OR a preserved path changed and carries no backup payload by design
    (the consumer's own bytes, already intact). Collapsing them into 'restore the
    backup' is destructive advice.

    SCOPED to the exit-3 section on purpose. As a whole-document search this gate
    was satisfied by a DIFFERENT sentence than the one it guards: rewriting the
    authoritative table cell to 'Restore the backup over it' -- the exact advice
    this gate exists to prevent -- left the suite green."""
    block = section_block(text, _EXIT_THREE_HEADING)
    if not block:
        return ["the handoff has no exit-3 two-meanings section"]
    low = re.sub(r"\s+", " ", block).lower()
    defects = []
    if "two meanings" not in low and "two distinct meanings" not in low:
        defects.append("the exit-3 section does not state exit 3 has two distinct meanings")
    if "mixed" not in low:
        defects.append("the exit-3 section does not name the genuinely-mixed-home case")
    if "no backup payload" not in low:
        defects.append("the exit-3 section does not name the preserved-path case "
                       "that carries no backup payload")
    if "do not restore a backup" not in low:
        defects.append("the exit-3 section does not warn against restoring a backup "
                       "in the preserved-path case")
    # The exit 3 an operator is most likely to hit prints NEITHER of the two
    # quoted diagnostics above: Assert-OurBytesAtTarget's refusal
    # ("refusing to undo the install of '<path>' -- the bytes there are no longer
    # the ones this migration wrote") is what an appended acceptance probe
    # produces, and a table that does not carry it sends the operator matching
    # against rows that cannot match. Reproduced end to end.
    if "no longer the ones this migration wrote" not in low:
        defects.append("the exit-3 section does not carry the byte-drift refusal "
                       "diagnostic (Assert-OurBytesAtTarget), which is the exit 3 an "
                       "appended acceptance probe actually produces")
    return defects


def test_handoff_keeps_both_meanings_of_exit_three():
    defects = exit_three_defects(_read(HANDOFF))
    assert not defects, "exit-3 guidance violated:\n" + "\n".join(defects)


def test_exit_three_gate_is_scoped_to_the_exit_three_section():
    # ANCHOR: rewrite the AUTHORITATIVE table cell to the destructive advice. The
    # phrase survives elsewhere in the document (section 10's clearing subsection
    # says "do not restore a backup over them"), so a whole-document search stays
    # green -- and this assertion is what proves the gate is not one.
    text = _read(HANDOFF)
    assert exit_three_defects(text) == []
    mutated = text.replace(_EXIT_THREE_NO_RESTORE, "Restore the backup over it")
    assert mutated != text, \
        f"the exit-3 table no longer carries {_EXIT_THREE_NO_RESTORE!r}"
    assert "do not restore a backup" in re.sub(r"\s+", " ", mutated).lower(), \
        "the mutation is not a valid scoping probe -- no such phrase survives elsewhere"
    assert any("warn against restoring a backup" in d
               for d in exit_three_defects(mutated)), \
        ("the exit-3 gate is satisfied by prose OUTSIDE the exit-3 section; it is a "
         "whole-document search, not a scoped one")
    # ...and the section itself must still be locatable.
    assert exit_three_defects("no headings here") == [
        "the handoff has no exit-3 two-meanings section"]


def test_handoff_gives_a_live_remedy_for_a_failed_incomplete_transaction():
    """`failed_incomplete` is UNRESOLVED (so it blocks a bare -Apply) and TERMINAL
    at the same time: -Resume refuses it with TRANSACTION_RESOLVED and -Rollback
    refuses it too. "Drive it forward with -Resume or reverse it with -Rollback" is
    therefore two dead ends. The migrator's own Find-UnresolvedTransaction remedy
    text gives the real answer -- recover per the run's diagnostics, then remove the
    transaction directory to clear the block -- and the handoff must agree with it,
    where INCOMPLETE_TRANSACTION is explained AND where exit 3 lands the operator."""
    text = _read(HANDOFF)
    apply_block = section_block(text, "## 8. Apply the migration", stop_prefixes=("\n## ",))
    assert apply_block, "the handoff no longer has an apply section"
    alow = re.sub(r"\s+", " ", apply_block).lower()
    assert "incomplete_transaction" in alow
    assert "failed_incomplete" in alow, \
        ("the INCOMPLETE_TRANSACTION guidance never distinguishes failed_incomplete -- "
         "it prescribes -Resume/-Rollback, which both refuse that status")
    assert "transaction_resolved" in alow, \
        "the guidance does not say -Resume and -Rollback refuse a failed_incomplete transaction"

    clearing = section_block(text, "### Clearing a `failed_incomplete` transaction")
    assert clearing, \
        "the handoff never says how to clear a failed_incomplete transaction"
    clow = re.sub(r"\s+", " ", clearing).lower()
    assert "transaction directory" in clow and "remove" in clow, \
        "the clearing section does not name removing the transaction directory"
    assert "mixed" in clow, \
        "the clearing section collapses exit 3's two meanings into one remedy"
    assert "do not restore a backup" in clow, \
        "the clearing section does not keep the preserved-path case non-destructive"


# --------------------------------------------------------------------------- #
# An irreversible delete must be preceded by a copy the operator can recover from
# --------------------------------------------------------------------------- #

_UNTRACKED_FALLBACK_HEADING = "#### If the legacy tree is not tracked"


def _backup_rooted_names(lines):
    """Shell variables assigned a path under `<backup-dir>` in these lines."""
    names = set()
    for line in lines:
        for m in re.finditer(r"\$([A-Za-z_]\w*)\s*=[^=]*<backup-dir>", line):
            names.add("$" + m.group(1))
    return names


def unbacked_deletion_defects(text, heading=_UNTRACKED_FALLBACK_HEADING):
    """A `Remove-Item` inside `heading`'s section that is NOT preceded, in the same
    section, by a `Copy-Item` into `<backup-dir>`.

    This section deletes the managed legacy GPT directories when they are untracked
    in git, and NOTHING else holds those bytes: the migrator's backup carries
    pre-images only of paths IT mutates and never touches that tree at all, and
    preserved-legacy-gpt.csv is built from the NON-managed set, so it has zero rows
    for every directory the delete removes. The bytes are hand-authored
    SKILL-core.md / SKILL-gpt.md files with no generated counterpart, so local drift
    in them is unrecoverable. An explicit copy first is the only recovery source."""
    block = section_block(text, heading)
    if not block:
        return [f"section not found: {heading!r}"]
    lines = command_lines(block)
    rooted = _backup_rooted_names(lines)
    copy_at = None
    for i, line in enumerate(lines):
        if not re.search(r"\bCopy-Item\b", line, re.I):
            continue
        if "<backup-dir>" in line or any(v in line for v in rooted):
            copy_at = i
            break
    defects = []
    for i, line in enumerate(lines):
        if not re.search(r"\bRemove-Item\b", line, re.I):
            continue
        if copy_at is None:
            defects.append("destructive command with no copy into <backup-dir> "
                           f"anywhere in the section: {line.strip()}")
        elif copy_at > i:
            defects.append("destructive command runs BEFORE the copy into "
                           f"<backup-dir>: {line.strip()}")
    return defects


def test_unbacked_deletion_gate_reds_on_a_delete_with_no_recovery_source():
    # ANCHOR: all three shapes must be caught, and the correct shape must be silent.
    head = "#### If the legacy tree is not tracked\n\n**Run in:** `<consumer-home>`\n\n"
    copy_block = ("```powershell\n$rescue = Join-Path '<backup-dir>' 'rescue'\n"
                  "Copy-Item -LiteralPath x -Destination $rescue -Recurse\n```\n\n"
                  "**Expect:** a copy.\n\n**Run in:** `<consumer-home>`\n\n")
    del_block = ("```powershell\nRemove-Item -LiteralPath x -Recurse -Force -Confirm:$false\n"
                 "```\n\n**Expect:** gone.\n")
    assert unbacked_deletion_defects(head + copy_block + del_block,
                                     "#### If the legacy tree") == []
    assert unbacked_deletion_defects(head + del_block, "#### If the legacy tree"), \
        "gate accepts an irreversible delete with no copy at all"
    reversed_order = head + del_block + "\n**Run in:** `<consumer-home>`\n\n" + copy_block
    assert any("BEFORE the copy" in d for d in
               unbacked_deletion_defects(reversed_order, "#### If the legacy tree")), \
        "gate accepts a copy that happens AFTER the delete"
    assert unbacked_deletion_defects("nothing here", "#### If the legacy tree"), \
        "gate silently passes when its section has been renamed away"


def test_handoff_backs_up_before_the_untracked_legacy_deletion():
    text = _read(HANDOFF)
    defects = unbacked_deletion_defects(text)
    assert not defects, ("irreversible deletion without a recovery source:\n"
                         + "\n".join(defects))
    block = section_block(text, _UNTRACKED_FALLBACK_HEADING)
    low = re.sub(r"\s+", " ", block).lower()
    assert re.search(r"\bRemove-Item\b", block, re.I), \
        "the untracked-deletion fallback no longer deletes anything -- gate is vacuous"
    # The two false claims this section used to make must not come back.
    assert "zero rows" in low, \
        "the section must state preserved-legacy-gpt.csv has no rows for the deleted set"
    assert "skill-core.md" in low and "skill-gpt.md" in low, \
        "the section must name the hand-authored artifacts whose drift is unrecoverable"
    for overclaim in ("the retained backup are the only audit trail",
                      "the only audit trail"):
        assert overclaim not in low, \
            f"the section still claims a backup that does not exist: {overclaim!r}"


def test_handoff_retires_on_a_managed_allowlist_and_preserves_consumer_only():
    low = re.sub(r"\s+", " ", _read(HANDOFF)).lower()
    assert "allowlist" in low, \
        "retirement must be a positive allowlist, not a denylist"
    assert "goblin-sweep" in low, \
        "handoff must name the concrete consumer-only entry that is preserved"
    assert "never payload-copied" in low, \
        "handoff must state preserved entries are recorded by path and hash only"
    assert LEGACY_GPT_ROOT in _read(HANDOFF), \
        "handoff must name the legacy GPT core tree it retires from"


def test_readme_points_at_the_handoff_with_the_completed_cutover_status():
    """The README keeps the reusable handoff discoverable and records accepted evidence."""
    text = _read(README)
    low = re.sub(r"\s+", " ", text).lower()
    assert "documentation/coding-root-cutover-handoff.md" in text, \
        "README does not point at the cutover handoff"
    assert "phase 7 complete" in low, "README does not record the accepted Phase 7 result"
    assert "issues #62" in low and "#63 closed" in low, \
        "README does not identify the closed acceptance/cutover issues"
    assert "step 48 is done" in low, \
        "README no longer records the completed handoff status"
    assert "what remains is operator-only" not in low, \
        "README still presents completed host acceptance as pending"


# --------------------------------------------------------------------------- #
# Stale cutover-path status, across the WHOLE published markdown surface
# --------------------------------------------------------------------------- #
#
# Step 69 of documentation/host-parity-repair-plan.md. The README assertion just
# above bans one literal phrase in ONE file, and that file was never where the
# phrase actually lived: it sat in
# documentation/host-native-discovery-cutover-plan.md, which the README gate does
# not read. A ban whose scope excludes the site of the only real instance is a
# ban in name only, so the scope is widened here -- deliberately, and recorded in
# documentation/step-69-doc-reconciliation-decisions.md rather than left to luck.
#
# WHAT THIS GATE CAN DECIDE -- and it is narrow, on purpose:
#   Every phrase in `_STALE_CUTOVER_STATUS_PHRASES` is absent from the PROSE of
#   every README.md + documentation/**/*.md file. That is a syntactic question
#   about literal strings and it is fully decidable.
#
# WHAT IT CANNOT DECIDE, and must never be read as certifying:
#   Whether any document presents completed Phase 7 cutover-path work (Steps
#   42-50) as outstanding. That is a SEMANTIC class, and a literal-phrase matcher
#   decides a syntactic one; the gap between them is unbounded, and paraphrase
#   defeats any fixed list. This is the same over-claiming failure Step 66 hit
#   three times (see step-66-vendored-reference-decisions.md section 7.1): a gate
#   that claims a class it cannot decide is worse than no gate, because the team
#   stops looking. The class-level authority is human review, exactly as tier 3
#   is there. This list is a TRIPWIRE for one phrase that has ACTUALLY shipped
#   stale in this repository, and it is maintained by adding the next phrase that
#   actually does.
#
# It also cannot see a stale claim written INSIDE backticks -- see
# `strip_code_spans` for why that exclusion exists and what it costs.
#
# SCOPE IS DERIVED, NEVER HAND-LISTED. `status_scanned_docs` globs the whole
# published markdown surface with NO file excluded -- not even a plan. The
# earlier `scanned_docs` skips `*-plan.md` because a plan legitimately names
# artifacts it has not built yet; that reasoning is about PATH TOKENS and does
# not transfer to status prose, where a plan is one of the likeliest places for a
# stale claim to sit. Reusing that exclusion here would have re-created the exact
# hole this gate exists to close.

_STALE_CUTOVER_STATUS_PHRASES = (
    # Shipped stale at host-native-discovery-cutover-plan.md:679 while Steps 49
    # and 50 were already accepted (2026-08-09, #62/#63 closed).
    "what remains is operator-only",
)

_CODE_SPAN_RE = re.compile(r"`[^`\n]*`")


def strip_code_spans(text):
    """Blank every single-line backtick span, leaving only prose.

    A backticked phrase is a CITATION of a token, not a claim about status. Two
    documents legitimately quote the banned phrase in order to specify the ban
    itself -- this plan's Step 69 block and the decision record -- and a gate that
    reds on the document that DEFINES it is a gate nobody can satisfy. Excluding
    code spans is a rule about markup meaning, not a hole cut for named files: it
    is derived from the text, so a future citation is covered by construction.

    The cost, stated rather than hidden: a stale status claim written inside
    backticks is invisible to this gate. That is an accepted, deliberate blind
    spot -- prose does not get written in code spans -- and it is the price of not
    excluding whole files by name.

    Triple-backtick fences degrade harmlessly: the pattern is single-line, so it
    consumes the leading pair of a ``` fence and leaves the fenced body as prose.
    """
    return _CODE_SPAN_RE.sub(" ", text)


def stale_cutover_status_defects(text, label=""):
    """Banned status phrases present in `text`'s prose. Empty list == clean.

    Whitespace is normalized AFTER stripping, so a phrase broken across a
    markdown line wrap is still caught -- a line-scoped matcher would miss the
    single most likely spelling in a wrapped document.
    """
    prose = re.sub(r"\s+", " ", strip_code_spans(text)).lower()
    return [f"{label}stale status phrase in prose: {phrase!r}"
            for phrase in _STALE_CUTOVER_STATUS_PHRASES if phrase in prose]


def status_scanned_docs():
    """The whole status-bearing markdown surface: the two root status documents
    plus documentation/**/*.md, with NO file excluded and no glob narrowing.

    CLAUDE.md is included on purpose and is not merely more coverage. The repair
    plan's Step 62 makes the point directly -- it is "the one instruction a fresh
    dev agent actually reads" -- so a stale Phase status there propagates into
    work rather than merely sitting on a page. The sibling doc gates in this
    repository stop at README + documentation/ because they validate PUBLISHED
    link and path tokens; this one grades status claims, which is a different
    question with a different surface.
    """
    docs = [README, CLAUDE_MD] + sorted(DOC_DIR.rglob("*.md"))
    return [d for d in docs if d.is_file()]


# Scope floor. Measured 2026-08-11: README.md + CLAUDE.md + 18 documents under
# documentation/ = 20, BEFORE this step added its decision record. Pinned at the
# PRE-EXISTING surface rather than the post-step count so the number is robust to
# whether a just-written file is in the git index yet -- tools/release.ps1 runs
# this suite from inside a `git ls-files` stage, where an unindexed file is simply
# absent. A floor, not an equality: adding documents never reds it, and narrowing
# the enumeration (an exclusion list, a tightened glob) always does. Step 63 set
# this precedent after a sibling gate silently returned None for a whole defect
# class and the burn-down measured nothing.
_STATUS_SCAN_FLOOR = 20


def test_status_scan_reaches_the_documents_that_carry_phase_status():
    """Anti-narrowing. A burn-down that is satisfied by scanning less is not a
    burn-down, so the surface has a floor and named must-reach members."""
    docs = status_scanned_docs()
    assert len(docs) >= _STATUS_SCAN_FLOOR, (
        f"status scan reaches only {len(docs)} documents, below the committed "
        f"floor of {_STATUS_SCAN_FLOOR} -- the enumeration was narrowed")
    names = {d.name for d in docs}
    # A membership FLOOR, not the scanned set: these are the documents that carry
    # Phase 7 status, including the plans the sibling token gate excludes.
    for required in ("README.md",
                     "CLAUDE.md",
                     "host-native-discovery-cutover-plan.md",
                     "host-parity-repair-plan.md",
                     "coding-root-cutover-handoff.md",
                     "provider-neutral-skill-mesh-plan.md",
                     "migration.md"):
        assert required in names, \
            f"status scan no longer reaches {required} -- scope was narrowed"


def test_stale_status_gate_reds_on_prose_and_stays_silent_on_a_citation():
    # ANCHOR: watched to go red on a planted defect before being believed. Pure
    # function, synthetic inputs -- the style of test_skill_tree.py's anchors.
    planted = "Every code step on the cutover path has landed. What remains is operator-only."
    assert stale_cutover_status_defects(planted), \
        "the gate did not flag the exact sentence that shipped stale"

    # ...and across a markdown line wrap, which is how it would really appear.
    wrapped = "Every code step has landed. What remains is\noperator-only.\n"
    assert stale_cutover_status_defects(wrapped), \
        "the gate is line-scoped -- a wrapped claim would slip through"

    # A CITATION of the token is not a claim: both documents that specify the ban
    # quote it this way, and they must stay green.
    cited = "the surviving README assertion bans `what remains is operator-only`."
    assert stale_cutover_status_defects(cited) == [], \
        "the gate reds on the document that DEFINES the ban"

    # The strip must not swallow prose outside the span, or the gate would go
    # quiet in exactly the case it exists for.
    assert stale_cutover_status_defects(
        "see `:679` -- what remains is operator-only, per the roll-up"), \
        "code-span stripping ate the surrounding prose"

    # And it must stay silent on an unrelated document.
    assert stale_cutover_status_defects("Steps 49 and 50 were accepted 2026-08-09.") == []


def test_no_published_doc_presents_the_completed_cutover_as_pending():
    """Step 69's widened ban: no document returned by status_scanned_docs()
    (README.md + CLAUDE.md + documentation/**/*.md, nothing excluded) may carry a
    banned status phrase in PROSE. Backticked citations are exempt, and this
    decides only the literal phrases in _STALE_CUTOVER_STATUS_PHRASES -- not the
    semantic class. Scope decision and rationale:
    documentation/step-69-doc-reconciliation-decisions.md section 2."""
    defects = []
    for doc in status_scanned_docs():
        rel = doc.relative_to(REPO_ROOT).as_posix()
        defects.extend(stale_cutover_status_defects(_read(doc), f"{rel}: "))
    assert not defects, (
        "a published document still presents completed cutover-path work as "
        "pending:\n" + "\n".join(defects))


def test_handoff_names_both_discovery_roots_and_the_legacy_router():
    text = _read(HANDOFF)
    for token in (CLAUDE_ROOT, GITHUB_ROOT, LEGACY_ROUTER):
        assert token in text, f"handoff never names {token}"


def command_lines(text):
    """Only the lines INSIDE ```powershell blocks -- i.e. the things an operator
    actually pastes. Prose that merely names a cmdlet is not an instruction."""
    lines = text.splitlines()
    out = []
    for open_i, close_i in command_blocks(text):
        out.extend(ln for ln in lines[open_i + 1:close_i] if ln.strip())
    return out


def prompting_command_defects(lines):
    """Command lines that can stop at an interactive prompt. `Remove-Item` over a
    populated directory prompts unless confirmation is suppressed."""
    defects = []
    for line in lines:
        low = line.lower()
        if "read-host" in low:
            defects.append(f"Read-Host prompts: {line.strip()}")
        if "get-credential" in low:
            defects.append(f"Get-Credential prompts: {line.strip()}")
        if re.search(r"\bRemove-Item\b", line) and "-Confirm:$false" not in line:
            defects.append(f"Remove-Item without -Confirm:$false may prompt: {line.strip()}")
    return defects


def test_prompt_gate_reds_on_an_interactive_command():
    # ANCHOR: the prompt gate must flag each shape and stay silent on the safe forms.
    assert prompting_command_defects(["$x = Read-Host 'which home?'"])
    assert prompting_command_defects(["Get-Credential"])
    assert prompting_command_defects(["Remove-Item -LiteralPath x -Recurse -Force"])
    assert prompting_command_defects(
        ["Remove-Item -LiteralPath x -Recurse -Force -Confirm:$false"]) == []
    assert prompting_command_defects(["pwsh -File tools/inspect-host-install.ps1 -Home x"]) == []


def test_handoff_never_instructs_an_interactive_command():
    """The inspector and migrator exit 2 rather than prompt, precisely so an
    unattended run is safe. A handoff that reintroduces a prompt throws that away."""
    lines = command_lines(_read(HANDOFF))
    assert lines, "no command lines found -- the prompt gate would be vacuous"
    defects = prompting_command_defects(lines)
    assert not defects, "handoff instructs a command that can prompt:\n" + "\n".join(defects)


def installer_mandatory_defects(spans, label=""):
    """`-Provider` and `-Home` are the installer's only [Parameter(Mandatory)] pair.
    Returns (defects, invocations_checked); a bare citation is not an invocation."""
    defects = []
    checked = 0
    for head, rel, shown in script_invocations(spans):
        if not rel.endswith("install-skill-mesh.ps1") or not _is_invocation(head):
            continue
        checked += 1
        flags = {f.lower() for f in _FLAG.findall(head)}
        if not flags & {"provider", "profile"}:
            defects.append(f"{label}installer call omits -Provider: `{shown}`")
        if not flags & {"home", "destination", "targethome"}:
            defects.append(f"{label}installer call omits -Home: `{shown}`")
    return defects, checked


def test_installer_mandatory_gate_reds_on_an_omitted_mandatory_parameter():
    # ANCHOR: a missing mandatory parameter is exactly how an unattended run turns
    # into an interactive prompt, so the gate must catch it -- and must not mistake
    # a prose citation for an incomplete command.
    ok = ["pwsh -File tools/install-skill-mesh.ps1 -Provider claude -Home '<install-home>'"]
    assert installer_mandatory_defects(ok) == ([], 1)
    missing_home = ["pwsh -File tools/install-skill-mesh.ps1 -Provider claude"]
    defects, checked = installer_mandatory_defects(missing_home)
    assert checked == 1 and any("-Home" in d for d in defects), \
        "gate failed to flag an installer call with no -Home"
    citation = ["tools/install-skill-mesh.ps1"]
    assert installer_mandatory_defects(citation) == ([], 0), \
        "gate mistook a prose citation for an incomplete command"


def test_documented_installer_calls_always_pass_both_mandatory_parameters():
    """Swept across every operational document, not just the handoff -- the README
    and architecture.md are where these calls actually live."""
    total_checked = 0
    defects = []
    for doc in scanned_docs():
        d, checked = installer_mandatory_defects(code_spans(_read(doc)), f"{doc.name}: ")
        defects.extend(d)
        total_checked += checked
    assert total_checked >= 2, (
        f"only {total_checked} installer invocations found -- the gate would be vacuous")
    assert not defects, "\n".join(defects)


_TOOLCHAIN_THIS_REPO_DOES_NOT_HAVE = (
    "npm run lint", "ruff check", "flake8", "mypy", "pyright", "eslint",
    "tsc --noemit", "invoke-scriptanalyzer", "pylint",
)


def test_handoff_never_instructs_a_linter_or_typechecker():
    """documentation/architecture.md section 8.4: this repository has no lint and no
    typecheck command, deliberately. Telling an operator to run one sends them
    hunting for a gate that does not exist."""
    low = _read(HANDOFF).lower()
    offenders = [t for t in _TOOLCHAIN_THIS_REPO_DOES_NOT_HAVE if t in low]
    assert not offenders, (
        "handoff instructs a toolchain this repository does not have: " + repr(offenders))


def test_handoff_defers_host_acceptance_to_the_operator_steps():
    """The handoff PREPARES Steps 49-50; it must never read as performing them."""
    low = re.sub(r"\s+", " ", _read(HANDOFF)).lower()
    assert "step 49" in low and "step 50" in low, \
        "handoff must name the operator acceptance steps it hands off to"
    assert "operator evidence" in low, \
        "handoff must state host acceptance is operator evidence, not a test result"
    assert "parked-work handshake" in low, \
        "handoff must make the parked-work handshake an explicit gate"


_SPELLING_HEADING = "## 0. Precondition: resolve your PowerShell executable"


def powershell_spelling_defects(text):
    """The handoff must resolve the PowerShell executable BEFORE its first tool
    invocation, and every block must then be spelled the way that probe decided.

    `pwsh` is PowerShell 7 and is NOT present on a stock Windows install; Windows
    PowerShell 5.1 is the floor every tool in this repository is written for and is
    what the test suites shell out to. A document whose first command block is
    unrunnable strands the operator at step one -- so the probe comes first and the
    blocks carry the spelling that always resolves. (documentation/architecture.md
    keeps the `pwsh` spelling in its command contract; the probe's table states the
    substitution both ways, so the two documents agree rather than conflict.)"""
    defects = []
    low = text.lower()
    heading_at = low.find(_SPELLING_HEADING.lower())
    if heading_at < 0:
        return [f"missing spelling precondition section: {_SPELLING_HEADING!r}"]
    lines = text.splitlines()
    first_tool_line = None
    for line in command_lines(text):
        if _PS1_IN_SPAN.search(_command_head(line)):
            first_tool_line = line
            break
    if first_tool_line is None:
        return ["the handoff invokes no tool at all -- this gate would be vacuous"]
    if text.find(first_tool_line) < heading_at:
        defects.append("a tool is invoked before the PowerShell-spelling precondition: "
                       + first_tool_line.strip())
    for i, line in enumerate(lines):
        if re.search(r"(?<![\w.-])pwsh\s+-File\b", line, re.I):
            defects.append(f"line {i + 1}: a command block is spelled `pwsh -File`, which "
                           "does not resolve on a stock Windows install: " + line.strip())
    section = section_block(text, _SPELLING_HEADING, stop_prefixes=("\n## ",))
    slow = re.sub(r"\s+", " ", section).lower()
    if "get-command pwsh" not in slow:
        defects.append("the precondition never actually probes for pwsh")
    if "substitution" not in slow:
        defects.append("the precondition states no substitution rule")
    return defects


def test_spelling_gate_reds_on_a_pwsh_block_and_on_a_missing_probe():
    # ANCHOR: the gate must accept the real document and flag each failure shape.
    text = _read(HANDOFF)
    assert powershell_spelling_defects(text) == [], powershell_spelling_defects(text)

    relapsed = text.replace("powershell -File tools/inspect-host-install.ps1",
                            "pwsh -File tools/inspect-host-install.ps1", 1)
    assert relapsed != text, "no inspector invocation to mutate -- probe is invalid"
    assert any("`pwsh -File`" in d for d in powershell_spelling_defects(relapsed)), \
        "the spelling gate accepts a block spelled pwsh -File"

    dropped = text.replace(_SPELLING_HEADING, "## 0. Something else")
    assert any("missing spelling precondition" in d
               for d in powershell_spelling_defects(dropped)), \
        "the spelling gate passes silently when its section is renamed away"


def test_handoff_resolves_the_powershell_executable_before_its_first_tool_call():
    defects = powershell_spelling_defects(_read(HANDOFF))
    assert not defects, "PowerShell spelling contract violated:\n" + "\n".join(defects)


_COMMIT_SECTION = "## 14. Commit the coding-root change"


def staging_split_defects(text):
    """`git add` and `git commit` must live in SEPARATE fenced blocks, and the add
    list must carry the ownership ledger.

    Operators paste a whole fenced block. `git add` is atomic on an unmatched
    pathspec -- one absent file (AGENTS.md, on a first cutover) fails the add with
    exit 128 and stages nothing -- but a `commit` in the same paste still runs and
    records whatever the index already held. Reproduced: `94 files changed, 94
    deletions(-)`, i.e. the legacy tree retired and nothing installed, on the cutover
    branch. Separate blocks are the workspace's command-presentation rule for
    sequential-with-observation commands, and here they are the whole defense.

    The ledger (.skill-mesh-install.json) is the only untracked row a clean migration
    leaves behind; omitting it from the add list makes the section's own "any
    unrelated path means stop" rule fire falsely on it."""
    section = section_block(text, _COMMIT_SECTION, stop_prefixes=("\n## ",))
    if not section:
        return [f"section not found: {_COMMIT_SECTION!r}"]
    lines = section.splitlines()
    add_blocks, commit_blocks = set(), set()
    for n, (open_i, close_i) in enumerate(command_blocks(section)):
        body = " ".join(lines[open_i + 1:close_i])
        if re.search(r"\bgit\b[^|;]*\badd\b", body):
            add_blocks.add(n)
        if re.search(r"\bgit\b[^|;]*\bcommit\b", body):
            commit_blocks.add(n)
    defects = []
    if not add_blocks:
        defects.append("the commit section stages nothing -- this gate would be vacuous")
    if not commit_blocks:
        defects.append("the commit section commits nothing -- this gate would be vacuous")
    shared = add_blocks & commit_blocks
    if shared:
        defects.append("`git add` and `git commit` share one fenced block, so a failed "
                       "add still commits: block index "
                       + ", ".join(str(i) for i in sorted(shared)))
    ledger = "." + "skill-mesh-install.json"
    if not any(ledger in " ".join(lines[o + 1:c])
               for o, c in command_blocks(section)
               if re.search(r"\bgit\b[^|;]*\badd\b", " ".join(lines[o + 1:c]))):
        defects.append(f"the `git add` pathspec list omits the ownership ledger {ledger}")
    return defects


def test_staging_split_gate_reds_on_a_shared_add_commit_block():
    # ANCHOR: the real section must pass; a merged block and a dropped ledger must
    # each go red.
    text = _read(HANDOFF)
    assert staging_split_defects(text) == [], staging_split_defects(text)

    merged = text.replace(
        "```\n\n**Expect:** `add` prints **nothing**",
        "git -C '<consumer-home>' commit -m 'x'\n```\n\n**Expect:** `add` prints **nothing**",
        1)
    assert merged != text, "the merge probe did not change the document"
    assert any("share one fenced block" in d for d in staging_split_defects(merged)), \
        "the staging gate accepts add and commit in one pasteable block"

    ledger = "." + "skill-mesh-install.json"
    no_ledger = text.replace(f" '{ledger}'", "", 1)
    assert no_ledger != text, "the ledger probe did not change the document"
    assert any("ownership ledger" in d for d in staging_split_defects(no_ledger)), \
        "the staging gate accepts an add list with no ownership ledger"


def test_handoff_stages_and_commits_in_separate_blocks():
    defects = staging_split_defects(_read(HANDOFF))
    assert not defects, "staging contract violated:\n" + "\n".join(defects)


# Phrases that RE-INSTATE the retired one-exempt-skill discriminator. Each one, on its
# own, tells an operator to look past a YAML error; together they are the exact prose
# Step 68 removed. Matched against whitespace-normalized lowercase text.
_RETIRED_YAML_EXEMPTIONS = (
    "is expected and is not a failure",
    "any other skill named in a yaml error",
    "one known name, expected",
    "the one expected yaml error",
)


def copilot_yaml_error_defects(text):
    """Ways the handoff's Copilot-output section could mislead an operator about a YAML
    parse failure. Empty list == correct."""
    low = re.sub(r"\s+", " ", text).lower()
    defects = []
    if "any skill named in a yaml error is a real failure" not in low:
        defects.append("the handoff does not state that ANY skill named in a YAML "
                       "error is a real failure")
    if "context-slim" not in low:
        defects.append("the handoff never names context-slim, so an operator working "
                       "from the retired exemption is never corrected")
    if "#69" not in low:
        defects.append("the handoff does not tie the retired exemption to its issue")
    for phrase in _RETIRED_YAML_EXEMPTIONS:
        # Banned outright, including as a quotation. The correction paragraph explains
        # what it retires in its OWN words for exactly this reason: an operator skimming
        # for "is expected and is not a failure" must not find it anywhere on the page,
        # whatever sentence it is embedded in.
        if phrase in low:
            defects.append(
                f"the handoff still carries the retired exemption phrase: {phrase!r}")
    return defects


def test_copilot_yaml_error_gate_reds_on_the_retired_exemption():
    """ANCHOR: the live document must pass, and the prose this step retired must red.

    Before Step 68 (#69) this section told the operator that context-slim's YAML parse
    failure "is expected and is not a failure", with the discriminator "any other skill
    named in a YAML error is a real failure". The defect is now fixed at its canonical
    source and gated by a strict YAML parse, so that instruction is not merely stale --
    it would talk an operator out of the one signal that the tree in the home is not
    the tree this repository released."""
    text = _read(HANDOFF)
    assert copilot_yaml_error_defects(text) == [], copilot_yaml_error_defects(text)

    retired = ("`copilot skill list` in a migrated home ends with a \"failed to load\" "
               "block naming **`context-slim`**. That one is expected and is not a "
               "failure. **Any other skill named in a YAML error is a real failure** -- "
               "one known name, expected; any second name, stop. Issue #69.")
    defects = copilot_yaml_error_defects(retired)
    assert any("ANY skill named in a YAML" in d for d in defects), defects
    assert any("retired exemption phrase" in d for d in defects), defects

    dropped = text.replace("Any skill named in a YAML error is a real failure", "", 1)
    assert dropped != text, "the probe did not change the document"
    assert copilot_yaml_error_defects(dropped), \
        "the gate accepts a handoff that never states the real-failure rule"


def test_handoff_treats_every_copilot_yaml_error_as_a_real_failure():
    defects = copilot_yaml_error_defects(_read(HANDOFF))
    assert not defects, "Copilot-output section violated:\n" + "\n".join(defects)


def test_handoff_warns_that_a_repeat_apply_is_not_a_no_op():
    """A second bare -Apply on an already-migrated home mints a NEW transaction whose
    backup pre-images are the GENERATED files, so rolling that id back leaves the home
    fully cut over. Only the FIRST transaction id restores the legacy home."""
    low = re.sub(r"\s+", " ", _read(HANDOFF)).lower()
    assert "not a no-op" in low or "is **not** a no-op" in low, \
        "the handoff never says a repeat -Apply is not a no-op"
    assert "only the first" in low, \
        "the handoff never says only the first transaction id restores the legacy home"


def test_handoff_rescues_the_router_before_the_shim_overwrites_it():
    """tools/gen-router-shim.ps1 overwrites <consumer-home>/.claude/lib/skill-router.ps1
    unconditionally, and the migrator's backup never covers .claude/lib -- so without
    an explicit copy first there is no recovery source at all for a locally-edited
    router."""
    text = _read(HANDOFF)
    section = section_block(text, "### 13.3 Retire the old router")
    assert section, "the router-retirement section is gone -- this gate would be vacuous"
    lines = command_lines(section)
    rooted = _backup_rooted_names(lines)
    copy_at = next((i for i, ln in enumerate(lines)
                    if re.search(r"\bCopy-Item\b", ln, re.I)
                    and ("<backup-dir>" in ln or any(v in ln for v in rooted))),
                   None)
    shim_at = next((i for i, ln in enumerate(lines) if "gen-router-shim.ps1" in ln), None)
    assert shim_at is not None, "the section no longer runs the shim generator"
    assert copy_at is not None, \
        "the shim overwrite has no copy of the existing router into <backup-dir>"
    assert copy_at < shim_at, \
        "the router rescue copy runs AFTER the shim has already overwritten the file"
    assert "git restore" in re.sub(r"\s+", " ", section).lower(), \
        "the section does not name git restore as the second recovery source"


def test_handoff_parked_work_probes_are_satisfiable():
    """Two of the four handshake probes cannot go green as absence checks on a mature
    consumer: archived `.plan-expedite-state.*` files and long-lived worktrees exist
    by design. A gate that can never pass gets waved through, which is worse than no
    gate -- so they are freshness / idleness probes instead."""
    text = _read(HANDOFF)
    section = section_block(text, "## 2. Preconditions: the parked-work handshake",
                            stop_prefixes=("\n## ",))
    assert section, "the parked-work handshake section is gone"
    joined = " ".join(command_lines(section))
    assert "LastWriteTimeUtc" in joined and "AddHours(-8)" in joined, \
        ("the expedite-state probe is a bare existence check; archived state files make "
         "that unsatisfiable")
    low = re.sub(r"\s+", " ", section).lower()
    assert "idle" in low, \
        "the worktree probe is not stated as an idleness check"
    assert "dirty=0" in joined or "dirty=0" in low, \
        "the worktree probe states no per-worktree PASS condition"


def test_handoff_documents_backup_retention_and_secure_deletion():
    low = re.sub(r"\s+", " ", _read(HANDOFF)).lower()
    assert "retention window" in low, "handoff must state a backup retention window"
    assert "cipher /w:" in low, \
        "handoff must give the exact secure-deletion (free-space wipe) command"
    assert "remove-item" in low, "handoff must give the deletion command itself"


# --------------------------------------------------------------------------- #
# The superseded-plan marker (a Done-when clause), and what it must NOT claim
# --------------------------------------------------------------------------- #

def test_previous_plan_step_41_is_marked_superseded():
    text = _read(NEUTRAL_PLAN)
    idx = text.find("### Step 41:")
    assert idx >= 0, "provider-neutral-skill-mesh-plan.md no longer has a Step 41"
    nxt = text.find("\n## ", idx)
    block = text[idx:nxt if nxt > 0 else len(text)]
    assert "**Status:** SUPERSEDED" in block, \
        "Step 41 carries no explicit SUPERSEDED status marker"
    assert "host-native-discovery-cutover-plan.md" in block, \
        "Step 41's supersession does not name the superseding plan"


def test_step_41_marker_records_issue_50_closure_as_already_discharged():
    """Closing #50 was a /repo-sync/operator action and was never this code step's
    criterion -- and it is already DONE (closed 2026-08-03, superseded against
    umbrella #56). The marker must keep the not-our-criterion point while not
    listing the closure as outstanding work someone still owes."""
    text = _read(NEUTRAL_PLAN)
    idx = text.find("### Step 41:")
    nxt = text.find("\n## ", idx)
    block = text[idx:nxt if nxt > 0 else len(text)]
    low = re.sub(r"\s+", " ", block).lower()
    assert "#50" in block, "Step 41 must still name its issue"
    assert "operator action" in low, \
        "Step 41's marker must record issue closure as an operator action"
    assert "2026-08-03" in block, \
        "Step 41's marker must cite the date #50 was actually closed"
    assert "not a criterion" in low or "never a criterion" in low, \
        "Step 41's marker must keep the point that #50's closure was not Step 48's criterion"
    for outstanding in ("outstanding obligation:", "still needs closing", "remains open",
                        "must be closed", "closing issue #50 ... is a"):
        assert outstanding not in low, \
            f"Step 41 lists an already-discharged action as outstanding: {outstanding}"


# --------------------------------------------------------------------------- #
# README and migration.md must not ship contradictory status in one delta
# --------------------------------------------------------------------------- #

_STEP_48_DONE = re.compile(r"step 48[^.]{0,120}?\bis\b[^.]{0,40}?\bdone\b")
_STEP_48_PROGRESS = re.compile(r"step 48[^.]{0,160}?\bin progress\b")


def step_48_status_claim(text):
    """'done' / 'in progress' / None -- what a document claims about Step 48."""
    low = re.sub(r"\s+", " ", text).lower().replace("*", "")
    if _STEP_48_DONE.search(low):
        return "done"
    if _STEP_48_PROGRESS.search(low):
        return "in progress"
    return None


def test_step_48_status_reader_distinguishes_the_two_claims():
    # ANCHOR: the cross-check below is only worth anything if the reader can tell
    # the claims apart.
    assert step_48_status_claim("The consumer handoff (Step 48) is **DONE**: ...") == "done"
    assert step_48_status_claim("Step 48 (this handoff) is in progress; ...") == "in progress"
    assert step_48_status_claim("Steps 48-50 remain.") is None


def plan_step_48_status():
    """'done' / 'in progress' -- what the cutover PLAN records for Step 48.

    The plan's own `### Step 48:` block is the authoritative status record; the
    narrative documents restate it. Deriving the expectation from that block
    instead of hardcoding a literal is deliberate: this assertion originally
    pinned 'in progress' as an invariant, which meant the merge of Step 48 could
    not be written into the docs without turning the gate red -- a gate that
    enforced a stale claim rather than agreement.
    """
    text = _read(CUTOVER_PLAN)
    idx = text.find("### Step 48:")
    assert idx >= 0, "the cutover plan no longer has a Step 48"
    nxt = text.find("\n### ", idx + 1)
    block = text[idx:nxt if nxt > 0 else len(text)]
    match = re.search(r"^-\s*\*\*Status:\*\*\s*(\S+)", block, re.M)
    assert match, "the cutover plan's Step 48 carries no **Status:** marker"
    return "done" if match.group(1).upper().startswith("DONE") else "in progress"


def test_readme_and_migration_doc_agree_on_step_48():
    """They shipped contradictory status in the same delta once -- README said DONE
    while migration.md said in progress. Both must agree, and both must match the
    status the cutover plan actually records for the step."""
    expected = plan_step_48_status()
    readme = step_48_status_claim(_read(README))
    migration = step_48_status_claim(_read(MIGRATION))
    assert readme == migration, (
        f"README claims Step 48 is {readme!r} but migration.md claims {migration!r}")
    assert readme == expected, (
        f"the cutover plan records Step 48 as {expected!r}; both narrative "
        f"documents must say so, not {readme!r}")


def test_cutover_plan_step_48_still_owns_this_handoff():
    """Guards the acceptance contract itself: if Step 48's Files/Produces stop
    naming the handoff, this whole module is gating an orphan."""
    text = _read(CUTOVER_PLAN)
    idx = text.find("### Step 48:")
    assert idx >= 0, "the cutover plan no longer has a Step 48"
    nxt = text.find("\n### Step 49:", idx)
    block = text[idx:nxt if nxt > 0 else len(text)]
    assert "coding-root-cutover-handoff.md" in block, \
        "Step 48 no longer names the handoff document this gate validates"


# --------------------------------------------------------------------------- #
# This gate executes nothing, and claims nothing about host acceptance
# --------------------------------------------------------------------------- #

# Assembled at runtime from halves: this module scans its OWN source, so a literal
# here would make the check self-flagging and permanently red.
_EXECUTION_PRIMITIVES = tuple(a + b for a, b in (
    ("sub", "process"), ("os.", "system"), ("Po", "pen"), ("check_", "output"),
    ("shutil.", "which"), ("os.", "popen"), ("import", "lib"), ("ev", "al("),
))


def test_this_gate_executes_nothing():
    """A structure gate that shells out is no longer hermetic -- and a gate that
    ran a handoff step would mutate a consumer home from a test run. Enforced
    against this module's own source so it cannot drift."""
    own = Path(__file__).read_text(encoding="utf-8")
    body = re.sub(r'"""(?:.|\n)*?"""', "", own)          # drop docstrings
    body = re.sub(r"(?m)#.*$", "", body)                  # drop comments
    offenders = [p for p in _EXECUTION_PRIMITIVES if p in body]
    assert not offenders, (
        "this gate must never execute anything; found: " + repr(offenders))


def _all_tests():
    return [v for k, v in sorted(globals().items())
            if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    passed = 0
    for fn in _all_tests():
        fn()
        passed += 1
        print(f"PASS {fn.__name__}")
    print(f"\n{passed} checks passed")
