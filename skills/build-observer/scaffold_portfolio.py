"""Validate + render a proposed ``[project.portfolio]`` registry block.

Thin mechanical layer for the ``/build-observer`` skill (dev-observatory
portfolio-pages plan, Step 27 / section 5e). The SKILL.md prose does the
CREATIVE work (read the project's README/CLAUDE.md/plan, draft a blurb in the
house voice, pick proofs from documented guarantees) and hands the drafted
field values to this script as CLI flags. This script does the MECHANICAL
work: validate verb names against the project's actual derived verbs,
validate ``relates`` slugs against the registry's known slugs, enforce the
same length/count caps ``registry.py`` enforces at parse time, and render the
TOML snippet -- by IMPORTING ``dev_observatory``'s own constants/dataclasses/
renderer rather than re-declaring any of them (``.claude/rules/code-quality.md``
"one source of truth for data-shape constants").

Read-only: this script never writes into ``registry.toml`` or
``snapshot.json``. It prints a validation report to stderr and the proposed
``[project.portfolio]`` TOML snippet to stdout. Pasting that snippet under the
project's existing ``[[project]]`` entry (or handing it to Step 28's
authoring pass) is a separate, deliberate, human/operator-reviewed step.

Usage (from the coding root, PowerShell):

    uv run --project <absolute-root>/dev-observatory --no-sync --frozen --offline --no-python-downloads python -B <skill-dir>/scaffold_portfolio.py <slug> --root <absolute-root> --registry <absolute-registry> --snapshot <absolute-snapshot> [flags]

Flags mirror the ``[project.portfolio]`` fields (plan section 5a):
    --blurb TEXT            <=140-char noun-phrase pitch, house voice
    --card TEXT              optional longer paragraph (flagship cards only)
    --tag TEXT                one-word category chip
    --proof TEXT             repeatable, <=3 kept
    --showcase NAME           verb name; validated against this project's
                               derived button-eligible verbs
    --highlight NAME          repeatable, <=3 kept, same validation
    --relates "slug: clause"  repeatable, <=4 kept after dead-slug filtering
    --live-url URL             http(s) only
    --contribution TEXT        third-party entries only
    --repo-public               default False
    --public                    default False; REQUIRES --public-reason (a
                                 non-empty string naming who told you this
                                 project is display-listed) -- this is the
                                 mechanical half of "never sets public=true
                                 without being told the project is
                                 display-listed"; the other half is the
                                 SKILL.md instruction never to pass this flag
                                 on a guess.
    --public-reason TEXT

Exit status is always 0 (validation drops are reported, not fatal) except for
usage errors (argparse) and the ``--public`` without ``--public-reason`` guard.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

# dev-observatory's own package -- run this script via
# ``uv run --project dev-observatory python <this file>`` so it resolves.
from dev_observatory import registry as registry_mod
from dev_observatory import snapshot as snapshot_mod
from dev_observatory import verbs as verbs_mod
from dev_observatory.model import Portfolio

# Legacy CLI default only; the skill always supplies explicit absolute paths.
_ROOT = Path(__file__).resolve().parents[3]


def _default_registry_path(root: Path) -> Path:
    return root / ".claude" / "observatory" / "registry.toml"


def _default_snapshot_path(root: Path) -> Path:
    return root / ".claude" / "observatory" / "snapshot.json"


def _warn(message: str) -> None:
    print(f"[build-observer] {message}", file=sys.stderr)


def _load_verb_names(snapshot_path: Path, slug: str) -> tuple[set[str], set[str], bool]:
    """Return ``(all_verb_names, button_eligible_names, found)`` for ``slug``.

    Prefers the typed ``snapshot.load_snapshot`` (version-gated -- returns
    ``None`` on a stale/missing cache rather than rebuilding anything; this
    script is read-only and NEVER refreshes the on-disk snapshot). Falls back
    to a raw JSON read of the same ``projects[*].verbs[*].verb`` shape when
    the typed loader declines, since that shape has been stable across the
    portfolio-pages snapshot-version bumps (only new derived FIELDS were
    added, not a verb-shape change) -- callers get a loud warning either way.
    """
    typed = snapshot_mod.load_snapshot(snapshot_path)
    if typed is not None:
        for project in typed.projects:
            if project.slug == slug:
                names = {v.verb for v in project.verbs}
                buttons = {v.verb for v in project.verbs if verbs_mod.is_button_verb(v.verb)}
                return names, buttons, True
        return set(), set(), False

    _warn(
        f"'{snapshot_path}' did not load via the versioned loader (stale/missing "
        "cache) -- falling back to a raw JSON read for verb names. Verb "
        "derivation itself hasn't changed shape across the recent snapshot-"
        "version bumps, but re-run 'observatory status' when convenient to "
        "refresh the cache (this script will NOT do that for you)."
    )
    try:
        raw = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _warn(f"could not read '{snapshot_path}' at all: {exc}")
        return set(), set(), False

    # Malformed/truncated JSON at any nesting level degrades to "no verb names
    # available" rather than crashing -- every level below is shape-checked
    # before use (code-review Nit: a raw fallback must never trust the file).
    if not isinstance(raw, dict):
        _warn(f"'{snapshot_path}' is not a JSON object at the top level -- treating as no verb data")
        return set(), set(), False

    projects = raw.get("projects", [])
    if not isinstance(projects, list):
        _warn(f"'{snapshot_path}' has a non-list 'projects' -- treating as no verb data")
        return set(), set(), False

    for project in projects:
        if not isinstance(project, dict):
            continue  # malformed entry -- skip it, don't crash on it
        if project.get("slug") == slug:
            verb_dicts = project.get("verbs", [])
            if not isinstance(verb_dicts, list):
                _warn(f"'{slug}' has a non-list 'verbs' in the raw snapshot -- treating as no verb data")
                return set(), set(), False
            names = {
                v["verb"]
                for v in verb_dicts
                if isinstance(v, dict) and isinstance(v.get("verb"), str) and v.get("verb")
            }
            buttons = {
                name
                for name in names
                if verbs_mod.is_button_verb(name)
            }
            return names, buttons, True
    return set(), set(), False


def _validate_blurb(blurb: str | None) -> str | None:
    if blurb is None:
        _warn("blurb: OMITTED (not provided) -- render falls back to the derived plan goal")
        return None
    if not blurb.strip():
        _warn("blurb: DROPPED -- empty/whitespace-only")
        return None
    if len(blurb) > registry_mod._BLURB_MAX_LEN or registry_mod._BLURB_CONTROL_RE.search(blurb):
        _warn(
            f"blurb: DROPPED -- over {registry_mod._BLURB_MAX_LEN} chars "
            f"(got {len(blurb)}) or bad charset; shorten and re-run"
        )
        return None
    _warn(f"blurb: KEPT ({len(blurb)}/{registry_mod._BLURB_MAX_LEN} chars)")
    return blurb


def _validate_proofs(proofs: list[str]) -> list[str]:
    if not proofs:
        return []
    if len(proofs) > registry_mod._PROOFS_MAX:
        _warn(
            f"proofs: {len(proofs)} given -- truncated to "
            f"{registry_mod._PROOFS_MAX} (first {registry_mod._PROOFS_MAX} kept)"
        )
        proofs = proofs[: registry_mod._PROOFS_MAX]
    else:
        _warn(f"proofs: KEPT ({len(proofs)})")
    return proofs


def _validate_verb_name(
    field: str, name: str | None, button_verbs: set[str], slug: str, found: bool
) -> str | None:
    if name is None:
        return None
    if not found:
        _warn(
            f"{field}: DROPPED '{name}' -- project '{slug}' was not found in the "
            "snapshot at all; cannot validate a verb name against it"
        )
        return None
    if name == "status":
        _warn(f"{field}: DROPPED 'status' -- status is never promoted to a button surface (DD7)")
        return None
    if name not in button_verbs:
        _warn(
            f"{field}: DROPPED '{name}' -- not a currently-derived button verb for "
            f"'{slug}' (derived buttons today: {sorted(button_verbs) or '(none)'}). "
            "Add a [project.launch] entry for this command (or an existing verb "
            "name) and re-run; leaving this field unset is also safe -- the "
            "render-time showcase ladder falls back to the first launch verb, "
            "then 'open-repo' alone."
        )
        return None
    _warn(f"{field}: KEPT '{name}' (validated against derived verbs)")
    return name


def _validate_highlights(
    highlights: list[str], button_verbs: set[str], slug: str, found: bool
) -> list[str]:
    kept: list[str] = []
    for name in highlights:
        valid = _validate_verb_name("highlight", name, button_verbs, slug, found)
        if valid is not None:
            kept.append(valid)
    if len(kept) > registry_mod._HIGHLIGHTS_MAX:
        _warn(
            f"highlights: {len(kept)} valid entries -- truncated to "
            f"{registry_mod._HIGHLIGHTS_MAX}"
        )
        kept = kept[: registry_mod._HIGHLIGHTS_MAX]
    return kept


def _validate_relates(raw_relates: list[str], known_slugs: set[str], own_slug: str) -> list[tuple[str, str]]:
    kept: list[tuple[str, str]] = []
    for item in raw_relates:
        rel_slug, sep, clause = item.partition(":")
        rel_slug = rel_slug.strip()
        clause = clause.strip()
        if not sep or not rel_slug or not clause:
            _warn(f"relates: DROPPED {item!r} -- not shaped 'slug: clause'")
            continue
        if rel_slug == own_slug:
            _warn(f"relates: DROPPED {item!r} -- a project cannot relate to itself")
            continue
        if rel_slug not in known_slugs:
            _warn(f"relates: DROPPED {item!r} -- '{rel_slug}' is not a known registry slug")
            continue
        kept.append((rel_slug, clause))
    if len(kept) > registry_mod._RELATES_MAX:
        _warn(f"relates: {len(kept)} valid entries -- truncated to {registry_mod._RELATES_MAX}")
        kept = kept[: registry_mod._RELATES_MAX]
    if kept:
        _warn(f"relates: KEPT {len(kept)}")
    return kept


def _validate_live_url(live_url: str | None) -> str | None:
    if live_url is None:
        return None
    stripped = live_url.strip()
    try:
        parsed = urlparse(stripped)
    except ValueError:
        parsed = None
    if parsed is None or parsed.scheme not in ("http", "https") or not parsed.netloc:
        _warn(f"live_url: DROPPED {live_url!r} -- not an http(s) URL")
        return None
    _warn(f"live_url: KEPT {stripped!r}")
    return stripped


def _render_snippet(portfolio: Portfolio) -> str:
    """Render ONLY the ``[project.portfolio]`` snippet via the real renderer.

    Reuses ``registry._portfolio_to_table`` (never re-implements the
    omit-when-empty/relates-string rendering rules) for the FIELD values, then
    dumps that flat dict with ``tomli_w`` and prepends the ``[project.portfolio]``
    header ourselves.

    Deliberately does NOT ask ``tomli_w`` to render the header (e.g. by
    wrapping the table in ``{"project": [{"portfolio": table}]}`` and slicing
    out the header text): for a SCALAR-ONLY table (no array-valued fields --
    e.g. just ``blurb`` + ``tag``, the common early-stage-project case, before
    3 proofs are documented) ``tomli_w`` renders an array-of-tables element
    whose only key is itself a table as a COMPACT INLINE form
    (``project = [{ portfolio = {...} }]``) with NO ``[project.portfolio]``
    substring to slice on at all -- that shape crashed here with
    ``ValueError: substring not found`` (code-review Block, reproduced live via
    ``--blurb "test blurb"`` against paper-trail with no other fields).
    Dumping the flat field dict directly and owning the header ourselves has
    no such header/inline ambiguity for ANY field shape.
    """
    import tomli_w

    table = registry_mod._portfolio_to_table(portfolio)
    if not table:
        return ""
    return "[project.portfolio]\n" + tomli_w.dumps(table)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slug", help="registry slug of the project to scaffold")
    parser.add_argument("--root", default=str(_ROOT))
    parser.add_argument("--registry", default=None)
    parser.add_argument("--snapshot", default=None)
    parser.add_argument("--blurb", default=None)
    parser.add_argument("--card", default=None)
    parser.add_argument("--tag", default=None)
    parser.add_argument("--proof", action="append", default=[])
    parser.add_argument("--showcase", default=None)
    parser.add_argument("--highlight", action="append", default=[])
    parser.add_argument("--relates", action="append", default=[])
    parser.add_argument("--live-url", default=None)
    parser.add_argument("--contribution", default=None)
    parser.add_argument("--repo-public", action="store_true")
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--public-reason", default=None)
    args = parser.parse_args(argv)

    if args.public and not (args.public_reason and args.public_reason.strip()):
        parser.error(
            "--public requires --public-reason \"<who/what told you this project "
            "is display-listed>\" -- never set public=true on a guess"
        )

    root = Path(args.root)
    registry_path = Path(args.registry) if args.registry else _default_registry_path(root)
    snapshot_path = Path(args.snapshot) if args.snapshot else _default_snapshot_path(root)

    entries = registry_mod.load_registry(registry_path)
    known_slugs = set(entries)
    if args.slug not in entries:
        _warn(
            f"'{args.slug}' has no [[project]] entry in {registry_path} -- "
            "the snippet below is still valid TOML but has nowhere to be pasted "
            "yet; register the project first"
        )

    verb_names, button_verbs, found = _load_verb_names(snapshot_path, args.slug)
    if not found:
        _warn(f"'{args.slug}' not found in snapshot projects -- showcase/highlights cannot validate")

    blurb = _validate_blurb(args.blurb)
    proofs = _validate_proofs(args.proof)
    showcase = _validate_verb_name("showcase", args.showcase, button_verbs, args.slug, found)
    highlights = _validate_highlights(args.highlight, button_verbs, args.slug, found)
    relates = _validate_relates(args.relates, known_slugs, args.slug)
    live_url = _validate_live_url(args.live_url)

    if args.public:
        _warn(f"public: KEPT true -- reason given: {args.public_reason!r}")
    if args.repo_public:
        _warn("repo_public: KEPT true")

    portfolio = Portfolio(
        blurb=blurb,
        card=args.card,
        tag=args.tag,
        proofs=proofs,
        relates=relates,
        showcase=showcase,
        highlights=highlights,
        live_url=live_url,
        repo_public=args.repo_public,
        contribution=args.contribution,
        public=args.public,
    )

    snippet = _render_snippet(portfolio)
    if not snippet:
        _warn("no portfolio fields survived validation -- nothing to write")
        return 0
    sys.stdout.write(snippet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
