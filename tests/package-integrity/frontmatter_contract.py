"""frontmatter_contract.py -- the ONE owner of the SKILL.md frontmatter contract
(Step 68 of documentation/host-parity-repair-plan.md, issue #69).

NOT a test module (no `test_` prefix, never collected). It is imported by both
gates that grade frontmatter, so the contract has a single definition rather than
two that drift:

  * tests/package-integrity/test_frontmatter_yaml.py -- the CANONICAL sources
    (skills/<name>/providers/{claude,gpt}.md), which is where a defect is
    introduced and where it must be caught.
  * tests/distributions/test_distributions.py -- the EMITTED profiles
    (dist/<profile>/<skill>/SKILL.md), which is what a host actually parses.
    Producer and consumer graded by the same rules
    (.claude/rules/code-quality.md, "One source of truth for data-shape
    constants").

WHY A REAL YAML PARSER, HARD-IMPORTED
-------------------------------------
The consumer this contract models is a strict YAML parser -- GitHub Copilot CLI's
scan of the Claude discovery root, which rejected `context-slim` outright
("mapping values are not allowed in this context") because an unquoted
colon-bearing `argument:` value is not YAML. A hand-rolled "strict scanner" would
be this repository's *model* of YAML, and any gap between that model and the real
parser is a gate that says PASS on bytes the host rejects -- an over-claiming gate,
which is worse than no gate at all.

So PyYAML is imported HARD, and declared in CLAUDE.md's Environment requirements
beside Python/pytest. `pytest.importorskip("yaml")` is deliberately NOT used: it
would turn this gate into a silent skip on any machine without PyYAML, and a suite
whose baseline carries one skip cannot see a second one appear. A missing
dependency must ERROR loudly at collection.

WHAT IS DELIBERATELY OUT OF SCOPE
---------------------------------
The 46 legacy top-level `<skill>/SKILL.md` packages. No build path reads them --
tools/build-distributions.ps1 resolves every source inside `skills/` (its
Resolve-SafeSource is pinned to that root), so nothing in the legacy tree reaches
a discovery profile or a consumer home. They are the same frozen deprecation
surface that documentation D-63-B puts outside the link gate's scope
(tests/package-integrity/test_link_resolution.py), and this gate scopes itself the
same way rather than silently implying it covers them.

WHAT THE CONTRACT FORBIDS, AND WHY EACH RULE EXISTS
---------------------------------------------------
1. The block must parse under a strict YAML parser (the original #69 defect).
2. Keys must come from a closed allowlist. `user-invokable` (the misspelling that
   sat in claude-oauth-auth's adapter, where it silently did nothing because every
   host reads `user-invocable`) is caught here for free.
3. A boolean-valued key must parse to a real `bool` -- checked with `is True` /
   `is False`, never truthiness. `user-invocable: "false"` parses to the STRING
   `'false'`, which is truthy everywhere, so a blanket "quote every scalar" fix
   would silently invert a deliberate suppression flag while every presence-only
   assertion stayed green.
4. A string-valued key must not arrive already wrapped in quotes -- `""x""`
   parses to `'"x"'`. That is what a quote-it-twice normalizer produces, and no
   parse error announces it.
5. A single-line plain (unquoted) value must survive the parse byte-for-byte. A
   ` #` in an unquoted value starts a YAML comment and silently TRUNCATES the
   description; the block still parses, so rule 1 alone cannot see it.
6. No duplicate keys: YAML keeps the last, so a duplicated `description:` drops
   text with nothing objecting.
"""

from __future__ import annotations

import re
from collections import Counter

try:
    import yaml
except ImportError as exc:  # pragma: no cover -- environment defect, not a skip
    raise ImportError(
        "PyYAML is required by this repository's frontmatter gate and is declared "
        "in CLAUDE.md's Environment requirements (`pip install pyyaml`). This is "
        "an intentionally HARD import: skipping the gate would hide the exact "
        "defect class it exists to catch (issue #69)."
    ) from exc


# The canonical Claude adapter vocabulary. Closed on purpose: an unknown key is a
# typo until proven otherwise, and proving otherwise means adding it here in the
# same commit that starts using it.
CLAUDE_KEYS = frozenset({"name", "description", "user-invocable", "argument"})

# What tools/build-distributions.ps1's New-GptFrontmatter synthesizes, and the only
# keys a GPT profile SKILL.md may carry.
GPT_KEYS = frozenset({"name", "description"})

# Keys whose value must be a string, and keys whose value must be a real bool.
STRING_KEYS = frozenset({"name", "description", "argument"})
BOOL_KEYS = frozenset({"user-invocable"})

REQUIRED_KEYS = ("name", "description")

# A top-level key line inside a frontmatter block: column 0, no indentation. A
# continuation line of a multi-line value is always indented, so this never
# mistakes value text for a key.
_KEY_LINE = re.compile(r"^([A-Za-z0-9_.-]+):(?:[ \t]|$)")

_OPEN = "---\n"
_CLOSE = "\n---\n"


def split_frontmatter(text):
    """(block, rest) for a leading `---\\n ... \\n---\\n` block, else None.

    `block` excludes both fences; `rest` is everything after the closing fence.
    Returns None -- not a partial parse -- for a file that does not lead with a
    block, or whose block is never closed.
    """
    if not text.startswith(_OPEN):
        return None
    end = text.find(_CLOSE, len(_OPEN))
    if end < 0:
        return None
    return text[len(_OPEN):end], text[end + len(_CLOSE):]


def _literal_keys(block):
    """Every key spelled at column 0 in the raw block, in order, including
    duplicates the parser would silently collapse."""
    return [m.group(1) for m in (_KEY_LINE.match(line) for line in block.splitlines())
            if m]


def _plain_single_line_values(block):
    """{key: raw text after `key:`} for keys whose value is a single-line PLAIN
    scalar -- unquoted, and not continued onto a following line.

    Quoted and multi-line values are excluded: for those the parser's result is
    authoritative and cannot be compared against raw text.
    """
    lines = block.splitlines()
    key_at = {}
    for idx, line in enumerate(lines):
        m = _KEY_LINE.match(line)
        if not m:
            continue
        # Continued onto the next line? Then it is not single-line.
        nxt = lines[idx + 1] if idx + 1 < len(lines) else None
        if nxt is not None and not _KEY_LINE.match(nxt):
            continue
        raw = line[len(m.group(1)) + 1:].strip()
        if not raw or raw[0] in ('"', "'", "|", ">", "&", "*", "[", "{"):
            continue
        key_at[m.group(1)] = raw
    return key_at


def frontmatter_defects(text, allowed_keys=CLAUDE_KEYS, required=REQUIRED_KEYS):
    """Every way `text`'s leading frontmatter block violates the contract.

    Returns a list of human-readable defect strings; an EMPTY list means the block
    satisfies every rule in this module's docstring. Never raises on bad input --
    a YAML error is a reported defect, so one bad file cannot mask the others.
    """
    defects = []
    split = split_frontmatter(text)
    if split is None:
        return ["does not lead with a `---` frontmatter block closed by a `---` line"]
    block, _rest = split

    try:
        parsed = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        detail = " ".join(str(exc).split())
        return [f"frontmatter is not valid YAML: {detail}"]
    if not isinstance(parsed, dict):
        return [f"frontmatter is not a mapping (parsed as {type(parsed).__name__})"]

    literal = _literal_keys(block)
    for key, count in sorted(Counter(literal).items()):
        if count > 1:
            defects.append(
                f"duplicate key {key!r} ({count} times) -- YAML keeps the last, so "
                "the earlier value is silently dropped")

    parsed_keys = {str(k) for k in parsed}
    if parsed_keys != set(literal):
        defects.append(
            f"the parsed key set {sorted(parsed_keys)} does not match the keys "
            f"spelled in the block {sorted(set(literal))} -- the block is not the "
            "flat `key: value` mapping this contract grades")

    for key in sorted(parsed_keys | set(literal)):
        if key not in allowed_keys:
            defects.append(
                f"unknown key {key!r} (allowed: {sorted(allowed_keys)}) -- a "
                "misspelled key is silently ignored by every host")

    for key in required:
        if key not in parsed_keys:
            defects.append(f"missing required key {key!r}")

    plain = _plain_single_line_values(block)
    for key, value in sorted(parsed.items(), key=lambda kv: str(kv[0])):
        key = str(key)
        if key in BOOL_KEYS:
            if value is not True and value is not False:
                defects.append(
                    f"{key!r} is {value!r} ({type(value).__name__}), not an unquoted "
                    "YAML boolean -- a quoted 'false' is a TRUTHY string in every "
                    "strict parser")
            continue
        if key in STRING_KEYS:
            if not isinstance(value, str):
                defects.append(
                    f"{key!r} parsed as {type(value).__name__} ({value!r}), not a string")
                continue
            if not value.strip():
                defects.append(f"{key!r} is empty")
                continue
            if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
                defects.append(
                    f"{key!r} parsed to a value that is itself wrapped in quotes "
                    f"({value!r}) -- an already-quoted value was quoted a second time")
            raw = plain.get(key)
            if raw is not None and raw != value:
                defects.append(
                    f"{key!r} did not survive the parse: source line carries {raw!r} "
                    f"but YAML reads {value!r} (an unescaped ' #' starts a comment and "
                    "truncates the value)")
    return defects


def parse_frontmatter(text):
    """The parsed mapping, or None when there is no well-formed leading block.

    Callers that need the VALUES (round-trip assertions) use this; callers that
    need the VERDICT use frontmatter_defects().
    """
    split = split_frontmatter(text)
    if split is None:
        return None
    try:
        parsed = yaml.safe_load(split[0])
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None
