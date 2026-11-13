"""user-pm's Lanes section: lane cards and waiting notes, and lane planning (v3 user-pm plan Step 8, #233).

user-pm is a prose skill, so its Lanes read has no code of its own to run. This file
checks the contract from both ends of the producer-consumer relationship:

* **The consumer (the core).** `lanes_read` below is a small model of the core's
  "Lane cards and waiting notes" procedure. Each branch first looks up the exact core
  sentence that prescribes it (`RULES`) and raises `ContractGap` when that sentence is
  gone, so a scenario test fails on a fixture core with its rule removed. The model is
  this test's reading of the core, not production code; the pins are what tie it to
  the core's text.
* **The producer (the passing-notes tool).** The scenarios feed the model the tool
  output recorded on synthetic temporary stores (`RECORDED`). One live test rebuilds
  those stores under pytest's temp folder, runs only the read verbs `card show` and
  `inbox` against them, and asserts the tool still prints exactly what was recorded,
  creates nothing, and enforces the same byte cap the core uses. It skips when
  `passing-notes` is not on PATH; the core-side tests never skip. No write verb is ever
  called and the real store is never touched (`PASSING_NOTES_ROOT` always points at
  the temp folder).

The fallback branch (Passing Notes not on PATH, or its store absent) reads a plain-text
lane file instead. `fallback_read` models it the same way: each branch looks up its core
sentence first, and the scenarios feed it synthetic file bytes.

Part B (lane planning) has no tool behind it, so its tests pin the core's rules and
prove each pin fails on a fixture core with that rule removed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "skills" / "user-pm" / "core.md"
PROJECT = "demo"
CAP = 8192
LANE_CAP = 20
TIMEOUT_SECONDS = 30
COUNT_PREFIX = "diagnostics:"
DIAGNOSTIC_PREFIX = "diagnostic:"
PART_A = "### Lane cards and waiting notes"
PART_B = "### Lane planning"
FALLBACK_FILE = f"%LOCALAPPDATA%\\lane-notes\\{PROJECT}.txt"
BOM = b"\xef\xbb\xbf"
UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
# The Passing Notes protocol's lane id grammar and card states (passing-notes/docs/protocol.md,
# "Identifiers" and "Lane cards"). The core cites the grammar; this test models it.
LANE_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ID_FLOOR = re.compile(r"^[a-z0-9-]+$")
RESERVED_IDS = {"all", "operator", "con", "prn", "aux", "nul",
                *(f"com{i}" for i in range(10)), *(f"lpt{i}" for i in range(10))}
CARD_STATES = {"active", "waiting", "blocked", "idle", "done"}
PASTE_START = "New-Item"
ITEM_PLACEHOLDER = "<what this lane is doing now>"

# The core sentence (fragment) that prescribes each branch of the model.
RULES = {
    "gate": "When `passing-notes` is not on PATH, or the store folder is absent",
    "gate_silent": "Otherwise skip silently, with zero output, when that folder has no `cards/<project>/` folder",
    "gate_no_lane": "or when the lane list names no lane (the tool prints only `diagnostics: 0`)",
    "timeout": "its own numeric timeout of 30 seconds",
    "cap": "each call's captured output is capped at 8192 bytes",
    "card_columns": "Each line before the diagnostics is tab-separated: lane, host, state, item, updated.",
    "inbox_columns": "Each line before the diagnostics is tab-separated: note id, kind, needs, from, subject.",
    "lane_cap": "for at most 20 lanes",
    "diagnostics": "each line starting `diagnostic:` reports one store problem",
    "read_only": "Never `read`, `ack`, `post` or `card set`",
    "one_note": "Every problem below joins ONE note for the whole read",
    "rest_intact": "the rest of the overview is produced as if the failed call had been skipped",
    "nonzero": "an exit code other than 0",
    "diagnostic_note": "the valid lanes still show; the note gives the diagnostic count",
    "timed_out": "a timed-out lane list means no lanes, and a timed-out inbox leaves its lane's line with `notes unread`",
    "truncated": "only the whole lines within the first 8192 bytes are used",
    "lane_cap_note": "more than 20 lanes: the note gives the number left unread",
    "render": "then the number of open notes and the first three (note id, kind, needs, from, subject), `+N more` past three",
    "pointer": "`messages/<project>/` in the store",
    "no_body": "Never a note body, and never a card's owned paths, checkout or body.",
    # The fallback file (Passing Notes unavailable).
    "fb_only_unavailable": "Read only in the cheap gate's two unavailable cases, never when Passing Notes is present",
    "fb_path": "`%LOCALAPPDATA%\\lane-notes\\<project>.txt`",
    "fb_read": "Through the host's own file tool only: no subprocess and no write.",
    "fb_tail": "Only the last 8192 bytes are read and only whole lines in them are used: a line cut by the start of that window is dropped.",
    "fb_bom": "A leading UTF-8 byte order mark is ignored.",
    "fb_card": "`<utc> | card | <lane> | <state> | <item>`",
    "fb_note": "`<utc> | note | <from> -> <to> | <subject>`",
    "fb_time": "`<utc>` is `YYYY-MM-DDTHH:MM:SSZ`.",
    "fb_malformed": "a line that does not parse is counted, never shown",
    "fb_latest": "Each lane's latest card line (the latest time; a tie goes to the later line), in order of the lane's first card line",
    "fb_cap": "for at most 20 lanes; lanes past the twentieth are not shown",
    "fb_waiting": "A note is waiting for a lane when it is addressed to that lane or to `all`, is not from that lane, and is newer than that lane's latest card line.",
    "fb_render": "with host `unknown`, the card's time as its updated time, each waiting note shown as its UTC time in place of a note id",
    "fb_ids": "`<lane>` and `<from>` are lane ids under the protocol's id grammar",
    "fb_to": "`<to>` is a lane id, `all` or `operator`",
    "fb_states": "`<state>` is one of the protocol's card states: `active`, `waiting`, `blocked`, `idle` or `done`.",
    "fb_ids_floor": "an id holding any character other than a lowercase letter, a digit or a hyphen breaks the line, and the note says the ids were checked without the protocol",
    "fb_ack": "a paste line for the lane's own window that appends a newer card line",
    "fb_no_file_text": "No text from the file goes into a paste line except a validated lane id and card state.",
    "fb_item_placeholder": "'Z | card | <lane> | <state> | <what this lane is doing now>')`",
    "fb_clears": "appending a card acknowledges every note waiting for that lane, not only the first",
    "fb_post": "Then one **Post a note** line, the same command ending `'Z | note | <from> -> <to> | <subject>')`, every field left for the operator to fill in.",
    "fb_typed_quote": "A single quote typed into a field, straight or curly, is doubled.",
    "fb_folder": "Each paste line creates the folder when it is missing and starts its entry with a line break",
    "fb_bootstrap": "shows only the **Acknowledge** line with every field left as a placeholder",
    "fb_no_write": "user-pm never writes the file.",
    "fb_note_used": "Passing Notes is unavailable (not on PATH, or store absent) and the lanes came from the fallback file",
    "fb_note_absent": "when the file is absent, Passing Notes is unavailable and no fallback file was found at",
}


class ContractGap(AssertionError):
    """The core no longer states a rule the model needs."""


@dataclass(frozen=True)
class Call:
    exit_code: int = 0
    stdout: bytes = b""
    timed_out: bool = False


Runner = Callable[[list[str]], Call]


def _part_a(core: str) -> str:
    start = core.find(PART_A)
    end = core.find(PART_B, start)
    return core[start:end] if start >= 0 and end > start else ""


def _rule(part_a: str, key: str) -> None:
    if RULES[key] not in part_a:
        raise ContractGap(f"core no longer states the {key!r} rule: {RULES[key]!r}")


def _lines(part_a: str, call: Call, what: str, problems: list[str]) -> list[str] | None:
    """A call's result lines under the core's fail-open rules; None when the call yields nothing."""
    if call.timed_out:
        _rule(part_a, "timed_out")
        problems.append(f"{what} timed out after {TIMEOUT_SECONDS} s")
        return None
    if call.exit_code != 0:
        _rule(part_a, "nonzero")
        problems.append(f"{what} exit {call.exit_code}")
        return None
    data = call.stdout
    if len(data) > CAP:
        _rule(part_a, "truncated")
        data = data[:CAP]
        data = data[: data.rfind(b"\n") + 1]
        problems.append(f"{what} output truncated at {CAP} bytes")
    lines = data.decode("utf-8", "replace").splitlines()
    _rule(part_a, "diagnostics")
    diagnostics = [line for line in lines if line.startswith(DIAGNOSTIC_PREFIX)]
    count = next((line for line in lines if line.startswith(COUNT_PREFIX)), f"{COUNT_PREFIX} 0")
    total = int(count.split(":", 1)[1].split()[0])
    if diagnostics or total:
        _rule(part_a, "diagnostic_note")
        problems.append(f"{what}: {max(total, len(diagnostics))} diagnostics; run passing-notes card show --project {PROJECT}")
    return [line for line in lines if not line.startswith((DIAGNOSTIC_PREFIX, COUNT_PREFIX))]


def _valid_id(part_a: str, value: str, protocol: bool) -> bool:
    """A lane id under the protocol's grammar, or under the core's floor when the protocol is unreadable."""
    if not protocol:
        _rule(part_a, "fb_ids_floor")
        return bool(ID_FLOOR.match(value))
    return (bool(LANE_ID.match(value)) and len(value) <= 32
            and "to" not in value.split("-") and value not in RESERVED_IDS)


def _parse_fallback_line(part_a: str, line: str, protocol: bool) -> tuple[str, ...] | None:
    """One fallback line as ("card", utc, lane, state, item) or ("note", utc, from, to, subject)."""
    head = line.split(" | ", 2)
    if len(head) < 3 or not UTC.match(head[0]):
        return None
    _rule(part_a, "fb_time")
    if head[1] == "card":
        _rule(part_a, "fb_card")
        fields = line.split(" | ", 4)
        if len(fields) != 5 or not fields[4].strip():
            return None
        _rule(part_a, "fb_ids")
        _rule(part_a, "fb_states")
        if _valid_id(part_a, fields[2], protocol) and fields[3] in CARD_STATES:
            return ("card", fields[0], fields[2], fields[3], fields[4])
    elif head[1] == "note":
        _rule(part_a, "fb_note")
        fields = line.split(" | ", 3)
        ends = fields[2].split(" -> ") if len(fields) == 4 else []
        if len(ends) != 2 or not fields[3].strip():
            return None
        _rule(part_a, "fb_ids")
        _rule(part_a, "fb_to")
        frm, to = ends
        if _valid_id(part_a, frm, protocol) and (to in ("all", "operator") or _valid_id(part_a, to, protocol)):
            return ("note", fields[0], frm, to, fields[3])
    return None


@dataclass
class FallbackFile:
    cards: dict[str, tuple[str, str, str]]  # lane -> latest (utc, state, item), first-seen order
    notes: list[tuple[str, ...]]            # (utc, from, to, subject), file order
    unparsed: int


def _fallback_parse(part_a: str, data: bytes, protocol: bool) -> FallbackFile:
    for key in ("fb_only_unavailable", "fb_read", "fb_no_write"):
        _rule(part_a, key)
    if len(data) > CAP:
        _rule(part_a, "fb_tail")
        window = data[-CAP:]
        if data[-CAP - 1:-CAP] != b"\n":
            window = window[window.find(b"\n") + 1:] if b"\n" in window else b""
        data = window
    elif data.startswith(BOM):
        _rule(part_a, "fb_bom")
        data = data[len(BOM):]
    parsed = FallbackFile({}, [], 0)
    for line in data.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        entry = _parse_fallback_line(part_a, line, protocol)
        if entry is None:
            _rule(part_a, "fb_malformed")
            parsed.unparsed += 1
        elif entry[0] == "card":
            _rule(part_a, "fb_latest")
            _, utc, lane, state, item = entry
            if lane not in parsed.cards or utc >= parsed.cards[lane][0]:
                parsed.cards[lane] = (utc, state, item)
        else:
            parsed.notes.append(entry[1:])
    return parsed


def fallback_read(part_a: str, data: bytes | None, reason: str,
                  protocol: bool = True) -> tuple[list[str], list[str]]:
    """The Lanes lines and the one notes entry the core prescribes from the fallback file."""
    _rule(part_a, "fb_path")
    if data is None:
        _rule(part_a, "fb_note_absent")
        _rule(part_a, "fb_bootstrap")
        return [], [f"lanes: Passing Notes unavailable ({reason}); no fallback file at {FALLBACK_FILE}"]
    parsed = _fallback_parse(part_a, data, protocol)
    problems = [f"Passing Notes unavailable ({reason}); lanes from the fallback file"]
    if not protocol:
        problems.append("ids checked without the protocol")
    if parsed.unparsed:
        problems.append(f"{parsed.unparsed} lines unparsed")
    lanes = list(parsed.cards.items())
    if len(lanes) > LANE_CAP:
        _rule(part_a, "fb_cap")
        problems.append(f"{len(lanes) - LANE_CAP} lanes unread")
        lanes = lanes[:LANE_CAP]
    rendered = []
    for lane, (card_utc, state, item) in lanes:
        _rule(part_a, "fb_waiting")
        _rule(part_a, "fb_render")
        waiting = [(utc, frm, subject) for utc, frm, to, subject in parsed.notes
                   if to in (lane, "all") and frm != lane and utc > card_utc]
        shown = "; ".join(f"`{utc}` from {frm}: {subject}" for utc, frm, subject in waiting[:3])
        more = f"; +{len(waiting) - 3} more" if len(waiting) > 3 else ""
        rendered.append(f"- **{lane}** — {state} on unknown: {item} (card {card_utc}) — "
                        f"{len(waiting)} open, unacknowledged: {shown}{more} — in `{FALLBACK_FILE}`")
    _rule(part_a, "fb_note_used")
    return rendered, ["lanes: " + "; ".join(problems)]


def _paste_template(part_a: str) -> str:
    """The core's own Acknowledge command, the one code span that starts with New-Item."""
    spans = [s for s in re.findall(r"`([^`\n]+)`", part_a) if s.startswith(PASTE_START)]
    if len(spans) != 1:
        raise ContractGap(f"core states {len(spans)} {PASTE_START} paste commands, expected one")
    return spans[0]


def fallback_ack(core: str, data: bytes, lane: str) -> str:
    """The Acknowledge paste line for one lane: only its validated id and state come from the file."""
    part_a = _part_a(core)
    for key in ("fb_ack", "fb_no_file_text", "fb_item_placeholder", "fb_clears", "fb_folder", "fb_typed_quote"):
        _rule(part_a, key)
    _, state, _item = _fallback_parse(part_a, data, True).cards[lane]
    return (_paste_template(part_a).replace("<project>", PROJECT)
            .replace("<lane>", lane).replace("<state>", state))


def fallback_post(core: str) -> str:
    """The Post a note paste line: the same command, every note field a placeholder."""
    part_a = _part_a(core)
    for key in ("fb_post", "fb_item_placeholder", "fb_folder", "fb_typed_quote"):
        _rule(part_a, key)
    template = _paste_template(part_a).replace("<project>", PROJECT)
    return template[: template.index("'Z | card")] + "'Z | note | <from> -> <to> | <subject>')"


def lanes_read(
    core: str,
    run: Runner,
    *,
    on_path: bool = True,
    store_exists: bool = True,
    cards_folder_exists: bool = True,
    fallback: bytes | None = None,
    protocol: bool = True,
) -> tuple[list[str], list[str]]:
    """The Lanes lines and the notes entries (zero or one) the core prescribes.

    `fallback` is the lane fallback file's bytes, or None when that file is absent; `protocol`
    is False when the Passing Notes protocol cannot be read.
    """
    part_a = _part_a(core)
    _rule(part_a, "gate")
    if not (on_path and store_exists):
        return fallback_read(part_a, fallback, "not on PATH" if not on_path else "store absent", protocol)
    if not cards_folder_exists:
        _rule(part_a, "gate_silent")
        return [], []
    for key in ("timeout", "cap", "read_only", "one_note", "rest_intact"):
        _rule(part_a, key)
    problems: list[str] = []
    listing = _lines(part_a, run(["card", "show", "--project", PROJECT]), "lane list", problems)
    cards = []
    for line in listing or []:
        _rule(part_a, "card_columns")
        lane, host, state, item, updated = line.split("\t")
        cards.append((lane, host, state, item, updated))
    if not cards and not problems:
        _rule(part_a, "gate_no_lane")
        return [], []
    if len(cards) > LANE_CAP:
        _rule(part_a, "lane_cap")
        _rule(part_a, "lane_cap_note")
        problems.append(f"{len(cards) - LANE_CAP} lanes unread")
        cards = cards[:LANE_CAP]
    rendered = []
    for lane, host, state, item, updated in cards:
        head = f"- **{lane}** — {state} on {host}: {item} (card {updated})"
        inbox = _lines(part_a, run(["inbox", "--project", PROJECT, "--lane", lane]), f"inbox {lane}", problems)
        if inbox is None:
            rendered.append(f"{head} — notes unread")
            continue
        _rule(part_a, "inbox_columns")
        _rule(part_a, "render")
        _rule(part_a, "pointer")
        _rule(part_a, "no_body")
        notes = [line.split("\t")[:5] for line in inbox]
        shown = "; ".join(f"`{nid}` {kind}, needs {needs}, from {frm}: {subject}"
                          for nid, kind, needs, frm, subject in notes[:3])
        more = f"; +{len(notes) - 3} more" if len(notes) > 3 else ""
        rendered.append(f"{head} — {len(notes)} open, unacknowledged: {shown}{more} — in `messages/{PROJECT}/`")
    return rendered, (["lanes: " + "; ".join(problems)] if problems else [])


# --- Producer output, recorded on synthetic temporary stores (see the live test) ------------

NOTE_ID = "20300101T120000Z-lane-a-to-lane-b-1a2b"
NOTE_BODY = "What I need: a synthetic answer."
CARD_LINE = "lane-b\tcodex\tactive\tStep 2 tests\t2030-01-01T12:30:00Z"


def _card(lane: str) -> str:
    return (
        f"---\nlane: {lane}\nproject: {PROJECT}\nhost: codex\nowns:\n  - src/example/\n"
        "holds:\n  - none\nitem: Step 2 tests\nstate: active\nupdated_utc: 2030-01-01T12:30:00Z\n"
        "---\n\nshort synthetic card notes\n"
    )


def _note() -> str:
    return (
        f"---\nid: {NOTE_ID}\ncreated_utc: 2030-01-01T12:00:00Z\nproject: {PROJECT}\nfrom: lane-a\n"
        "to: lane-b\nsubject: Synthetic waiting note\nkind: question\nneeds: reply\nreply_to: none\n"
        f"refs:\n---\n\n{NOTE_BODY}\n"
    )


BIG_CARD = _card("lane-b") + ("x" * 79 + "\n") * 640  # a 50 KiB card file

RECORDED = {
    "empty": "diagnostics: 0\n",
    "malformed_list": (
        "diagnostic: cards/demo/lane-b.md: invalid: header: the file must start with a '---' line\n"
        "diagnostics: 1\n"
    ),
    "one_lane_list": f"{CARD_LINE}\ndiagnostics: 0\n",
    "one_note_inbox": f"{NOTE_ID}\tquestion\treply\tlane-a\tSynthetic waiting note\ndiagnostics: 0\n",
    "big_card_list": (
        f"diagnostic: cards/demo/lane-b.md: oversize: {len(BIG_CARD.encode())} bytes (limit {CAP})\n"
        "diagnostics: 1\n"
    ),
}


def _scripted(responses: dict[str, Call]) -> tuple[Runner, list[list[str]]]:
    calls: list[list[str]] = []

    def run(args: list[str]) -> Call:
        calls.append(args)
        key = "list" if args[:2] == ["card", "show"] else f"inbox {args[-1]}"
        return responses[key]

    return run, calls


def _ok(text: str) -> Call:
    return Call(stdout=text.encode("utf-8"))


def _core() -> str:
    return CORE.read_text(encoding="utf-8")


# --- Part A scenarios (the Step 8 Done-when list) --------------------------------------------


def test_no_cards_folder_gives_no_output_and_no_call() -> None:
    # Arrange
    run, calls = _scripted({})

    # Act
    no_cards = lanes_read(_core(), run, cards_folder_exists=False, fallback=b"ignored\n")

    # Assert
    assert no_cards == ([], [])
    assert calls == []


def test_passing_notes_unavailable_and_no_fallback_file_names_the_path() -> None:
    # Arrange
    run, calls = _scripted({})

    # Act
    absent = lanes_read(_core(), run, store_exists=False)
    no_tool = lanes_read(_core(), run, on_path=False)

    # Assert: never silent; one note naming the file looked for, unexpanded.
    assert calls == []
    for (lines, notes), reason in ((absent, "store absent"), (no_tool, "not on PATH")):
        assert lines == [] and len(notes) == 1
        assert reason in notes[0] and FALLBACK_FILE in notes[0]


def test_store_with_no_lanes_gives_no_output() -> None:
    # Arrange: an existing but empty store prints only the count line.
    run, calls = _scripted({"list": _ok(RECORDED["empty"])})

    # Act
    result = lanes_read(_core(), run)

    # Assert
    assert result == ([], [])
    assert calls == [["card", "show", "--project", PROJECT]]


def test_malformed_store_gives_one_notes_line() -> None:
    # Arrange: a malformed card, and separately a store the tool refuses (exit 4).
    malformed, _ = _scripted({"list": _ok(RECORDED["malformed_list"])})
    refused, _ = _scripted({"list": Call(exit_code=4)})

    # Act
    lines, notes = lanes_read(_core(), malformed)
    refused_lines, refused_notes = lanes_read(_core(), refused)

    # Assert
    assert lines == [] and len(notes) == 1 and "1 diagnostics" in notes[0]
    assert refused_lines == [] and len(refused_notes) == 1 and "exit 4" in refused_notes[0]


def test_one_lane_with_one_waiting_note_is_rendered() -> None:
    # Arrange
    run, calls = _scripted({"list": _ok(RECORDED["one_lane_list"]),
                            "inbox lane-b": _ok(RECORDED["one_note_inbox"])})

    # Act
    lines, notes = lanes_read(_core(), run)

    # Assert
    assert notes == []
    assert len(lines) == 1
    line = lines[0]
    for part in ("lane-b", "active", "codex", "Step 2 tests", "2030-01-01T12:30:00Z",
                 "1 open, unacknowledged", NOTE_ID, "question", "needs reply", "lane-a",
                 "Synthetic waiting note", f"`messages/{PROJECT}/`"):
        assert part in line, part
    assert NOTE_BODY not in line and "src/example/" not in line
    assert calls == [["card", "show", "--project", PROJECT],
                     ["inbox", "--project", PROJECT, "--lane", "lane-b"]]


def test_tool_timeout_gives_one_notes_line_and_the_rest_intact() -> None:
    # Arrange: two lanes; lane-b's inbox call times out. Separately, the lane list times out.
    two_lanes = f"lane-a\tclaude\tidle\tReview\t2030-01-01T10:00:00Z\n{CARD_LINE}\ndiagnostics: 0\n"
    run, _ = _scripted({"list": _ok(two_lanes),
                        "inbox lane-a": _ok(RECORDED["empty"]),
                        "inbox lane-b": Call(timed_out=True)})
    list_timeout, _ = _scripted({"list": Call(timed_out=True)})
    board = ["| Step 3 | plan | Direct task | agent | run it | now |"]

    # Act
    lines, notes = lanes_read(_core(), run)
    snapshot = {"board": list(board), "lanes": lines, "notes": notes}
    none_lines, none_notes = lanes_read(_core(), list_timeout)

    # Assert
    assert len(notes) == 1 and "inbox lane-b timed out after 30 s" in notes[0]
    assert lines[0].startswith("- **lane-a**") and "0 open" in lines[0]
    assert lines[1].startswith("- **lane-b**") and lines[1].endswith("notes unread")
    assert snapshot["board"] == board
    assert none_lines == [] and len(none_notes) == 1 and "timed out" in none_notes[0]


def test_50_kib_card_is_cut_at_the_cap() -> None:
    # Arrange: the tool itself refuses a 50 KiB card (recorded); a tool that printed one
    # anyway would hand user-pm 50 KiB of output, which the core cuts at the cap.
    refused, _ = _scripted({"list": _ok(RECORDED["big_card_list"])})
    flood_lines = [f"lane-{i:02d}\tcodex\tactive\t{'x' * 180}\t2030-01-01T12:30:00Z" for i in range(240)]
    flood = ("\n".join(flood_lines) + "\ndiagnostics: 0\n").encode("utf-8")
    seen: list[list[str]] = []

    def run(args: list[str]) -> Call:
        seen.append(args)
        return Call(stdout=flood) if args[:2] == ["card", "show"] else _ok(RECORDED["empty"])

    # Act
    refused_lines, refused_notes = lanes_read(_core(), refused)
    lines, notes = lanes_read(_core(), run)

    # Assert
    assert len(flood) > 50 * 1024
    assert refused_lines == [] and len(refused_notes) == 1 and "x" * 79 not in refused_notes[0]
    kept = flood[:CAP][: flood[:CAP].rfind(b"\n") + 1].decode().splitlines()
    assert len(notes) == 1 and f"truncated at {CAP} bytes" in notes[0]
    assert len(lines) == min(len(kept), LANE_CAP)
    assert all(line.split(" — ")[0][4:-2] in {k.split("\t")[0] for k in kept} for line in lines)
    assert len(kept) > LANE_CAP and "lanes unread" in notes[0]


def test_the_lane_count_cap_reads_at_most_20_lanes() -> None:
    # Arrange
    listing = "".join(f"lane-{i:02d}\tclaude\tidle\tItem\t2030-01-01T10:00:00Z\n" for i in range(25))
    responses = {"list": _ok(listing + "diagnostics: 0\n")}
    responses.update({f"inbox lane-{i:02d}": _ok(RECORDED["empty"]) for i in range(25)})
    run, calls = _scripted(responses)

    # Act
    lines, notes = lanes_read(_core(), run)

    # Assert
    assert len(lines) == LANE_CAP
    assert sum(call[0] == "inbox" for call in calls) == LANE_CAP
    assert len(notes) == 1 and "5 lanes unread" in notes[0]


def test_core_never_calls_a_write_verb_or_reads_a_body() -> None:
    # Arrange
    part_a = _part_a(_core())
    steps = [line for line in part_a.splitlines() if line.lstrip().startswith(("1. ", "2. "))]

    # Act
    commands = [segment for line in steps for segment in line.split("`") if segment.startswith("passing-notes ")]

    # Assert
    assert [c.split()[1] for c in commands] == ["card", "inbox"]
    assert RULES["read_only"] in part_a


# --- The fallback file (Passing Notes unavailable) -------------------------------------------


def _fb(*lines: str) -> bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")


FB_FULL = BOM + _fb(
    "2030-01-01T10:00:00Z | card | lane-a | active | Step 1 docs",
    "2030-01-01T10:05:00Z | card | lane-b | idle | Review",
    "2030-01-01T10:10:00Z | note | lane-b -> lane-a | Old question",  # older than lane-a's latest card
    "2030-01-01T11:00:00Z | card | lane-a | active | Step 2 tests",   # lane-a's latest card
    "2030-01-01T09:00:00Z | card | lane-a | done | Stale card",       # appended later, but older
    "",
    "2030-01-01T11:30:00Z | note | lane-b -> lane-a | Fresh question",
    "2030-01-01T11:40:00Z | note | lane-c -> all | Broadcast",
    "2030-01-01T11:45:00Z | note | lane-a -> all | Own broadcast",
    "2030-01-01T11:50:00Z | note | lane-a -> operator | For the operator",
    "not a lane line",
    "2030-01-01 11:00 | card | lane-x | active | bad time",
    "2030-01-01T12:00:00Z | card | lane-y | active",
)


def _fallback(data: bytes | None) -> tuple[list[str], list[str]]:
    return lanes_read(_core(), _scripted({})[0], on_path=False, fallback=data)


def _lane_ids(lines: list[str]) -> list[str]:
    return [line.split("**")[1] for line in lines]


def test_fallback_file_gives_lanes_and_one_note() -> None:
    # Act
    lines, notes = _fallback(FB_FULL)

    # Assert
    assert len(notes) == 1
    assert "not on PATH" in notes[0] and "lanes from the fallback file" in notes[0]
    assert _lane_ids(lines) == ["lane-a", "lane-b"]
    assert all("on unknown:" in line and f"`{FALLBACK_FILE}`" in line for line in lines)


def test_fallback_uses_each_lanes_latest_card() -> None:
    # Act
    lines, _ = _fallback(FB_FULL)

    # Assert: lane-a's 11:00 card wins over the later-appended but older 09:00 one.
    assert "active on unknown: Step 2 tests (card 2030-01-01T11:00:00Z)" in lines[0]
    assert "Stale card" not in lines[0]
    assert "idle on unknown: Review (card 2030-01-01T10:05:00Z)" in lines[1]


def test_fallback_card_time_tie_goes_to_the_later_line() -> None:
    # Arrange
    data = _fb("2030-01-01T10:00:00Z | card | lane-a | idle | First",
               "2030-01-01T10:00:00Z | card | lane-a | active | Second")

    # Act
    lines, _ = _fallback(data)

    # Assert
    assert len(lines) == 1 and "active on unknown: Second" in lines[0]


def test_fallback_waiting_notes_are_newer_than_the_card_and_include_all() -> None:
    # Act
    lines, _ = _fallback(FB_FULL)

    # Assert
    lane_a, lane_b = lines
    assert ("2 open, unacknowledged: `2030-01-01T11:30:00Z` from lane-b: Fresh question; "
            "`2030-01-01T11:40:00Z` from lane-c: Broadcast") in lane_a
    assert "Old question" not in lane_a and "Own broadcast" not in lane_a
    # lane-b's card is 10:05: both broadcasts after it wait for it; its own note to lane-a does not.
    assert "2 open" in lane_b and "from lane-c: Broadcast" in lane_b and "Own broadcast" in lane_b
    assert "Fresh question" not in lane_b
    assert not any("For the operator" in line for line in lines)


def test_fallback_more_than_three_waiting_notes_shows_three_and_a_count() -> None:
    # Arrange
    data = _fb("2030-01-01T10:00:00Z | card | lane-a | active | Work",
               *(f"2030-01-01T11:0{i}:00Z | note | lane-b -> lane-a | Q{i}" for i in range(5)))

    # Act
    lines, _ = _fallback(data)

    # Assert
    assert "5 open" in lines[0] and "Q2" in lines[0] and "Q3" not in lines[0] and "+2 more" in lines[0]


def test_fallback_malformed_lines_are_counted_never_shown() -> None:
    # Act
    lines, notes = _fallback(FB_FULL)

    # Assert: three bad lines; the blank line is skipped, not counted.
    assert "3 lines unparsed" in notes[0]
    assert not any(bad in "".join(lines) for bad in ("not a lane line", "lane-x", "lane-y"))


def test_fallback_reads_only_whole_lines_in_the_last_8192_bytes() -> None:
    # Arrange: old lines push the file past the cap; the window starts mid-line.
    old = [f"2030-01-01T08:{i % 60:02d}:00Z | card | old-{i:03d} | idle | {'o' * 40}" for i in range(200)]
    new = [f"2030-01-01T12:00:00Z | card | new-{i:02d} | active | Item {i}" for i in range(5)]
    data = BOM + _fb(*old, *new)
    window = data[-CAP:]
    whole = window[window.find(b"\n") + 1:].decode().splitlines()
    expected_old = [line.split(" | ")[2] for line in whole if " old-" in line]

    # Act
    lines, notes = _fallback(data)

    # Assert
    assert len(data) > CAP and data[-CAP - 1:-CAP] != b"\n"
    assert "unparsed" not in notes[0]  # the cut line was dropped, not counted
    assert _lane_ids(lines) == (expected_old + [f"new-{i:02d}" for i in range(5)])[:LANE_CAP]
    assert "old-000" not in _lane_ids(lines)


def test_fallback_window_on_a_line_boundary_keeps_its_first_line() -> None:
    # Arrange: the byte before the window is a newline, so the window's first line is whole.
    lane_line = _fb("2030-01-01T12:00:00Z | card | lane-a | active | Work")
    padding = b"p" * (CAP - len(lane_line) - 1) + b"\n"
    data = _fb("2030-01-01T08:00:00Z | card | old | idle | Gone") + padding + lane_line

    # Act
    lines, notes = _fallback(data)

    # Assert: the whole padding line is read (and does not parse); the line before it is not.
    assert len(padding + lane_line) == CAP
    assert _lane_ids(lines) == ["lane-a"]
    assert "1 lines unparsed" in notes[0]


def test_fallback_ignores_a_leading_bom() -> None:
    # Arrange
    data = BOM + _fb("2030-01-01T10:00:00Z | card | lane-a | active | Work")

    # Act
    lines, notes = _fallback(data)

    # Assert
    assert _lane_ids(lines) == ["lane-a"]
    assert "unparsed" not in notes[0]


def test_fallback_reads_at_most_20_lanes() -> None:
    # Arrange
    data = _fb(*(f"2030-01-01T10:00:00Z | card | lane-{i:02d} | idle | Item" for i in range(25)))

    # Act
    lines, notes = _fallback(data)

    # Assert
    assert _lane_ids(lines) == [f"lane-{i:02d}" for i in range(LANE_CAP)]
    assert "5 lanes unread" in notes[0]


def test_fallback_is_not_used_when_passing_notes_is_present() -> None:
    # Arrange: the tool and store are present but the call fails.
    refused, _ = _scripted({"list": Call(exit_code=4)})

    # Act
    lines, notes = lanes_read(_core(), refused, fallback=FB_FULL)

    # Assert: the existing fail-open note, no fallback lanes.
    assert lines == [] and len(notes) == 1 and "exit 4" in notes[0]
    assert "fallback" not in notes[0]


CURLY = "’"
HOSTILE = _fb(
    f"2030-01-01T10:00:00Z | card | lane-a | idle | Fix the user{CURLY}s bug{CURLY}; Remove-Item x",
    f"2030-01-01T10:00:00Z | card | lane{CURLY}b | idle | Curly lane id",
    f"2030-01-01T10:01:00Z | note | lane-c -> lane{CURLY}d | Curly recipient",
    "2030-01-01T10:02:00Z | card | lane-e | busy | Not a card state",
    "2030-01-01T10:03:00Z | card | operator | active | Reserved id",
    "2030-01-01T10:04:00Z | card | go-to-x | active | A to segment",
    "2030-01-01T10:05:00Z | card | Lane-F | active | Upper case",
    "2030-01-01T10:06:00Z | note | lane-c -> operator | For the operator",
)


def test_fallback_ids_and_states_follow_the_protocol() -> None:
    # Act
    lines, notes = _fallback(HOSTILE)

    # Assert: a curly quote in an id, an unknown state, a reserved id, a `to` segment and
    # upper case all break their line; a note to `operator` parses but is never listed.
    assert _lane_ids(lines) == ["lane-a"]
    assert "6 lines unparsed" in notes[0]
    assert "For the operator" not in lines[0]


def test_fallback_paste_lines_never_echo_file_text() -> None:
    # Act
    ack = fallback_ack(_core(), HOSTILE, "lane-a")
    post = fallback_post(_core())

    # Assert: only the validated lane id and state come from the file; the item is a placeholder.
    for line in (ack, post):
        assert CURLY not in line and "Fix the user" not in line and "Remove-Item" not in line
        assert line.startswith('New-Item -ItemType Directory -Force "$env:LOCALAPPDATA\\lane-notes" | Out-Null; ')
        assert "(Join-Path \"$env:LOCALAPPDATA\\lane-notes\" 'demo.txt')" in line
        assert "[Environment]::NewLine + (Get-Date).ToUniversalTime().ToString('s')" in line
    assert ack.endswith(f"'Z | card | lane-a | idle | {ITEM_PLACEHOLDER}')")
    assert post.endswith("'Z | note | <from> -> <to> | <subject>')")


def test_fallback_without_the_protocol_checks_ids_against_the_floor() -> None:
    # Act
    lines, notes = lanes_read(_core(), _scripted({})[0], on_path=False, fallback=HOSTILE, protocol=False)

    # Assert: the floor admits `go-to-x` and `operator` as ids but still rejects a curly quote.
    assert _lane_ids(lines) == ["lane-a", "operator", "go-to-x"]
    assert "ids checked without the protocol" in notes[0] and "4 lines unparsed" in notes[0]


def test_core_fallback_paste_command_only_creates_the_folder_and_appends() -> None:
    # Arrange
    part_a = _part_a(_core())

    # Act
    spans = [s for s in re.findall(r"`([^`\n]+)`", part_a) if s.startswith(PASTE_START)]

    # Assert: one command, which makes the folder and appends to the lane file, nothing else.
    assert len(spans) == 1
    verbs = set(re.findall(r"\b[A-Z][a-z]+-[A-Z][A-Za-z]+\b", spans[0]))
    assert verbs == {"New-Item", "Out-Null", "Add-Content", "Join-Path", "Get-Date"}, verbs
    assert "'<project>.txt'" in spans[0]
    assert RULES["fb_no_write"] in part_a and RULES["fb_read"] in part_a


# Fallback sentences outside the Lanes procedure: the output shape, the notes, --json and Limitations.
FALLBACK_PINS = {
    "post_a_note_shape": "- **Post a note:** <fallback file only: the paste line that appends a note line>",
    "fetched_text": "Passing Notes card fields and note subjects, the lines of the lane fallback file, and any",
    "limitations": ("- The lane fallback file is a by-hand convention, read by user-pm alone. The other skills' "
                    "Passing Notes inbox hooks (task-handoff, session-wrap, build-step, repo-update) still skip "
                    "when Passing Notes is absent, and none of them writes the file."),
    "lanes_source_row": "| `lanes_source` | default | optional, present only with `lanes` | `passing-notes` or `fallback-file` |",
    "json_host_unknown": "From the fallback file, `host` is `unknown` and `note_ids` holds up to three waiting notes' UTC times.",
    "read_only_constraint": "The lane fallback file is only read, through the host's own file tool.",
}


def fallback_pin_defects(core: str) -> list[str]:
    return [f"{key}: missing {pin!r}" for key, pin in FALLBACK_PINS.items() if pin not in core]


def test_core_states_the_fallback_outside_the_lanes_procedure() -> None:
    # Act
    defects = fallback_pin_defects(_core())

    # Assert
    assert defects == [], "\n".join(defects)


@pytest.mark.parametrize("key", sorted(FALLBACK_PINS))
def test_garbage_anchor_each_fallback_pin_fails_when_removed(key: str) -> None:
    # Arrange
    core = _core()
    garbage = core.replace(FALLBACK_PINS[key], "")

    # Act
    defects = fallback_pin_defects(garbage)

    # Assert
    assert garbage != core
    assert any(d.startswith(f"{key}:") for d in defects), defects


@pytest.mark.parametrize("key", sorted(RULES))
def test_garbage_anchor_part_a_scenarios_fail_on_a_core_without_the_rule(key: str) -> None:
    """Each pinned rule, removed from the real core, makes at least one scenario raise."""
    # Arrange
    core = _core()
    garbage = core.replace(RULES[key], "")
    assert garbage != core, f"{key} is not in the core verbatim"
    scenarios = {
        "absent": lambda c: lanes_read(c, _scripted({})[0], store_exists=False),
        "no_cards": lambda c: lanes_read(c, _scripted({})[0], cards_folder_exists=False),
        "fb_full": lambda c: lanes_read(c, _scripted({})[0], on_path=False, fallback=FB_FULL),
        "fb_big": lambda c: lanes_read(c, _scripted({})[0], on_path=False, fallback=_fb(*(
            f"2030-01-01T10:00:00Z | card | lane-{i:03d} | idle | {'x' * 60}" for i in range(150)))),
        "fb_floor": lambda c: lanes_read(c, _scripted({})[0], on_path=False, fallback=HOSTILE, protocol=False),
        "fb_ack": lambda c: fallback_ack(c, FB_FULL, "lane-a"),
        "fb_post": lambda c: fallback_post(c),
        "empty": lambda c: lanes_read(c, _scripted({"list": _ok(RECORDED["empty"])})[0]),
        "malformed": lambda c: lanes_read(c, _scripted({"list": _ok(RECORDED["malformed_list"])})[0]),
        "refused": lambda c: lanes_read(c, _scripted({"list": Call(exit_code=4)})[0]),
        "one_note": lambda c: lanes_read(c, _scripted({
            "list": _ok(RECORDED["one_lane_list"]), "inbox lane-b": _ok(RECORDED["one_note_inbox"])})[0]),
        "timeout": lambda c: lanes_read(c, _scripted({
            "list": _ok(RECORDED["one_lane_list"]), "inbox lane-b": Call(timed_out=True)})[0]),
        "flood": lambda c: lanes_read(c, _scripted({
            "list": Call(stdout=("".join(f"lane-{i:02d}\tclaude\tidle\t{'x' * 180}\t2030-01-01T10:00:00Z\n"
                                         for i in range(60)) + "diagnostics: 0\n").encode()),
            **{f"inbox lane-{i:02d}": _ok(RECORDED["empty"]) for i in range(60)}})[0]),
    }
    for scenario in scenarios.values():
        scenario(core)  # every scenario runs clean on the real core

    # Act
    gaps = []
    for name, scenario in scenarios.items():
        try:
            scenario(garbage)
        except ContractGap:
            gaps.append(name)

    # Assert
    assert gaps, f"removing the {key!r} rule from the core broke no scenario"


# --- The producer half: the real tool on temporary stores ------------------------------------


def _store_cases() -> dict[str, Callable[[Path], None]]:
    def absent(root: Path) -> None:
        pass

    def empty(root: Path) -> None:
        root.mkdir()

    def malformed(root: Path) -> None:
        (root / "cards" / PROJECT).mkdir(parents=True)
        (root / "cards" / PROJECT / "lane-b.md").write_bytes(b"not a card at all\n")

    def one_note(root: Path) -> None:
        (root / "cards" / PROJECT).mkdir(parents=True)
        (root / "messages" / PROJECT).mkdir(parents=True)
        (root / "cards" / PROJECT / "lane-b.md").write_bytes(_card("lane-b").encode())
        (root / "messages" / PROJECT / f"{NOTE_ID}.md").write_bytes(_note().encode())

    def big_card(root: Path) -> None:
        (root / "cards" / PROJECT).mkdir(parents=True)
        (root / "cards" / PROJECT / "lane-b.md").write_bytes(BIG_CARD.encode())

    return {"absent": absent, "empty": empty, "malformed": malformed,
            "one_note": one_note, "big_card": big_card}


def _live(exe: str, root: Path, *args: str) -> tuple[int, str, str]:
    env = dict(os.environ)
    env["PASSING_NOTES_ROOT"] = str(root)
    proc = subprocess.run([exe, *args], env=env, capture_output=True, timeout=TIMEOUT_SECONDS)
    norm = lambda b: b.decode("utf-8", "replace").replace("\r\n", "\n")  # noqa: E731
    return proc.returncode, norm(proc.stdout), norm(proc.stderr)


def test_the_real_tool_still_prints_what_the_scenarios_assume(tmp_path: Path) -> None:
    exe = shutil.which("passing-notes")
    if exe is None:
        pytest.skip("passing-notes is not on PATH: the producer half cannot run here; "
                    "the recorded outputs and the core-side tests still stand")
    expected_list = {"absent": RECORDED["empty"], "empty": RECORDED["empty"],
                     "malformed": RECORDED["malformed_list"], "one_note": RECORDED["one_lane_list"],
                     "big_card": RECORDED["big_card_list"]}
    expected_inbox = {"one_note": RECORDED["one_note_inbox"]}
    for name, build in _store_cases().items():
        # Arrange: a fresh store under pytest's temp folder, never the real one.
        root = tmp_path / name / "store"
        root.parent.mkdir()
        build(root)
        before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))

        # Act
        list_result = _live(exe, root, "card", "show", "--project", PROJECT)
        inbox_result = _live(exe, root, "inbox", "--project", PROJECT, "--lane", "lane-b")
        after = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))

        # Assert
        assert list_result == (0, expected_list[name], ""), name
        assert inbox_result == (0, expected_inbox.get(name, RECORDED["empty"]), ""), name
        assert after == before, f"{name}: a read verb created or removed store files"


def test_the_real_tool_enforces_the_cap_the_core_uses(tmp_path: Path) -> None:
    exe = shutil.which("passing-notes")
    if exe is None:
        pytest.skip("passing-notes is not on PATH: the producer half cannot run here")
    # Arrange: one card a byte over the core's cap, and a store root that is a file.
    root = tmp_path / "store"
    (root / "cards" / PROJECT).mkdir(parents=True)
    card = _card("lane-b").encode()
    (root / "cards" / PROJECT / "lane-b.md").write_bytes(card + b"y" * (CAP + 1 - len(card)))
    file_root = tmp_path / "file-root"
    file_root.write_bytes(b"not a folder")

    # Act
    code, out, _ = _live(exe, root, "card", "show", "--project", PROJECT)
    refused_code, refused_out, refused_err = _live(exe, file_root, "card", "show", "--project", PROJECT)

    # Assert
    assert code == 0 and f"oversize: {CAP + 1} bytes (limit {CAP})" in out
    assert (refused_code, refused_out) == (4, "") and "store-unusable" in refused_err
    assert RULES["cap"] in _part_a(_core())


# --- Part B: lane planning rules -------------------------------------------------------------

PLANNING_RULES = {
    "documents_lanes_flag": [
        "/ `--outstanding` / `--lanes`).** Three-part deep dive",
        "/ `--outstanding` / `--lanes`, replace",
        "- **`--lanes`** — the project's split into lanes",
    ],
    "draft_text_no_write": [
        "Close **The work** with paste-ready draft text: a draft `docs/lanes/README.md` table",
        "user-pm writes neither: creating the table and the cards is the operator's act, or a lane window's.",
        "Lane planning proposes draft text only: it never writes a lanes table, a card, a note or an acknowledgement.",
    ],
    "main_lane": [
        "Every split has a `main` lane, the lane the operator coordinates through.",
        "A board item with no known path goes to `main`, never guessed into a work lane.",
    ],
    "park": [
        "Each lane can park without stalling the others; a lane that cannot is merged into the lane it waits on.",
    ],
    "lane_count": [
        "`main` plus at most four work lanes by default.",
    ],
    "operator_reserved": [
        "Human-only items keep owner `you` on the board and are never placed in a lane.",
        "`operator` is a reserved id in the protocol's id grammar, so it is never a lane id in the draft table.",
    ],
    "id_grammar_cited": [
        "Lane ids follow the id grammar in the protocol's \"Identifiers\" section (`passing-notes/docs/protocol.md`), which is cited here, not restated.",
    ],
}

# Fragments that would mean the protocol's id grammar has been copied into the core.
RESTATED_GRAMMAR = ("[a-z0-9", "at most 32", "32 char", "`to` segment", "single hyphen",
                    "com0", "lpt0", "reserved device")


def planning_defects(core: str) -> list[str]:
    defects = [f"{key}: missing {pin!r}" for key, pins in PLANNING_RULES.items()
               for pin in pins if pin not in core]
    defects += [f"id_grammar_cited: restates the grammar ({token!r})"
                for token in RESTATED_GRAMMAR if token.lower() in core.lower()]
    return defects


def test_core_documents_lane_planning() -> None:
    # Act
    defects = planning_defects(_core())

    # Assert
    assert defects == [], "\n".join(defects)


@pytest.mark.parametrize("key", sorted(PLANNING_RULES))
def test_garbage_anchor_each_planning_rule_fails_when_removed(key: str) -> None:
    # Arrange
    core = _core()
    garbage = core
    for pin in PLANNING_RULES[key]:
        garbage = garbage.replace(pin, "")
    if key == "documents_lanes_flag":
        garbage = garbage.replace("--lanes", "")

    # Act
    defects = planning_defects(garbage)

    # Assert
    assert garbage != core
    assert any(d.startswith(f"{key}:") for d in defects), defects


def test_garbage_anchor_a_restated_id_grammar_fails() -> None:
    # Arrange: the citation kept, but the grammar copied in beside it.
    core = _core()
    garbage = core.replace(
        PLANNING_RULES["id_grammar_cited"][0],
        PLANNING_RULES["id_grammar_cited"][0] + " A lane id is `[a-z0-9]+(-[a-z0-9]+)*`, at most 32 characters.",
    )

    # Act
    defects = planning_defects(garbage)

    # Assert
    assert garbage != core
    assert any("restates the grammar" in d for d in defects), defects
