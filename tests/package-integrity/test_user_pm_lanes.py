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

Part B (lane planning) has no tool behind it, so its tests pin the core's rules and
prove each pin fails on a fixture core with that rule removed.
"""

from __future__ import annotations

import os
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

# The core sentence (fragment) that prescribes each branch of the model.
RULES = {
    "gate": "Skip silently, with zero output, when `passing-notes` is not on PATH, when the store folder is absent",
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


def lanes_read(
    core: str,
    run: Runner,
    *,
    on_path: bool = True,
    store_exists: bool = True,
    cards_folder_exists: bool = True,
) -> tuple[list[str], list[str]]:
    """The Lanes lines and the notes entries (zero or one) the core prescribes."""
    part_a = _part_a(core)
    _rule(part_a, "gate")
    if not (on_path and store_exists and cards_folder_exists):
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


def test_store_absent_gives_no_output_and_no_call() -> None:
    # Arrange
    run, calls = _scripted({})

    # Act
    absent = lanes_read(_core(), run, store_exists=False)
    no_tool = lanes_read(_core(), run, on_path=False)
    no_cards = lanes_read(_core(), run, cards_folder_exists=False)

    # Assert
    assert absent == no_tool == no_cards == ([], [])
    assert calls == []


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


@pytest.mark.parametrize("key", sorted(RULES))
def test_garbage_anchor_part_a_scenarios_fail_on_a_core_without_the_rule(key: str) -> None:
    """Each pinned rule, removed from the real core, makes at least one scenario raise."""
    # Arrange
    core = _core()
    garbage = core.replace(RULES[key], "")
    assert garbage != core, f"{key} is not in the core verbatim"
    scenarios = {
        "absent": lambda c: lanes_read(c, _scripted({})[0], store_exists=False),
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
