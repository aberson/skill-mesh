"""The companion tables in the README and the release-notes template (core companion plan Step 17).

The README's members table and the release-notes template's companion set table are
generated from config/companions.json by `python tools/companions.py table`. They are
pasted between marker comments, so this file can find them and prove each copy equals
what the tool prints from the manifest today. A manifest change without a regenerated
table fails here, in the per-change pack (this file sits in tests/package-integrity,
which the pack runs whole).

Every table here comes from the production entry point: the tool runs as a child
process, exactly as a maintainer regenerating the table runs it.

The same documents' links are checked too: relative file links must point at files
that exist (the release link checker), and every `#anchor` must name a heading or an
explicit `<a id>` in its target file.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "companions.py"
MANIFEST = REPO_ROOT / "config" / "companions.json"
README = REPO_ROOT / "README.md"
INSTALL_GUIDE = REPO_ROOT / "documentation" / "v2-installation.md"
RELEASE_TEMPLATE = REPO_ROOT / "documentation" / "release-notes-template.md"
INSTALLER = REPO_ROOT / "tools" / "install-skill-mesh.ps1"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import release_checks  # noqa: E402

# Which document carries which generated table, by its --kind.
TABLES = (
    ("members", README),
    ("release", RELEASE_TEMPLATE),
)


def run_table(*args):
    return subprocess.run(
        [sys.executable, str(TOOL), "table", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        timeout=60,
    )


def generated(kind, manifest=None):
    args = ["--kind", kind]
    if manifest is not None:
        args += ["--manifest", str(manifest)]
    proc = run_table(*args)
    assert proc.returncode == 0, proc.stdout.decode("utf-8", "replace")
    return proc.stdout.decode("utf-8")


def marked_block(path, kind):
    """Return the text between this kind's begin and end markers in path (LF endings)."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    begin = "<!-- companions-table:%s:begin -->\n" % kind
    end = "<!-- companions-table:%s:end -->" % kind
    assert text.count(begin) == 1, "%s needs exactly one %r line" % (path.name, begin.strip())
    assert text.count(end) == 1, "%s needs exactly one %r line" % (path.name, end)
    start = text.index(begin) + len(begin)
    stop = text.index(end)
    assert start <= stop, "%s: the %s end marker comes before its begin marker" % (
        path.name, kind)
    return text[start:stop]


def flat(path):
    """The document's text with every run of whitespace collapsed to one space."""
    return " ".join(path.read_text(encoding="utf-8").split())


@pytest.mark.parametrize("kind,path", TABLES, ids=[kind for kind, _ in TABLES])
def test_document_table_equals_the_manifest_generated_rows(kind, path):
    expected = generated(kind)
    actual = marked_block(path, kind)
    assert actual == expected, (
        "%s's %s table is not what the manifest generates. Regenerate it with "
        "`python tools/companions.py table --kind %s` and paste the output between "
        "the markers. Expected:\n%s" % (path.name, kind, kind, expected))


@pytest.mark.parametrize("kind,path", TABLES, ids=[kind for kind, _ in TABLES])
def test_a_manifest_change_without_regeneration_is_caught(tmp_path, kind, path):
    """Red anchor: bump one installed member's tag in a copy of the manifest; the
    generated table must change, so the equality test above would fail."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    row = next(r for r in manifest["members"] if r["ring"] in ("core", "optional"))
    row["tag"] = "v99.0.0"
    copy = tmp_path / "companions.json"
    copy.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    changed = generated(kind, copy)
    assert "`v99.0.0`" in changed
    assert changed != marked_block(path, kind)


def test_members_table_lists_every_manifest_row_and_release_lists_only_installed():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    members = generated("members")
    release = generated("release")
    for row in manifest["members"]:
        link = "[%s](%s)" % (row["slug"], row["repo"])
        assert members.count(link) == 1, row["slug"]
        installed = row["ring"] in ("core", "optional")
        assert (link in release) is installed, row["slug"]
    # Header, separator and one line per row; LF only.
    assert len(members.splitlines()) == 2 + len(manifest["members"])
    assert "\r" not in members and "\r" not in release


def test_table_refuses_a_manifest_verify_refuses(tmp_path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    duplicate = dict(manifest, members=manifest["members"] + [manifest["members"][-1]])
    bad = tmp_path / "duplicate.json"
    bad.write_text(json.dumps(duplicate), encoding="utf-8")
    proc = run_table("--manifest", str(bad))
    assert proc.returncode == 11
    payload = json.loads(proc.stdout.decode("ascii"))
    assert payload["command"] == "table" and payload["exit_code"] == 11
    assert payload["error"]["check"] == "duplicate-slug"


def test_release_table_refuses_an_untagged_member(tmp_path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    row = next(r for r in manifest["members"] if r["ring"] == "core")
    row["tag"] = None
    untagged = tmp_path / "untagged.json"
    untagged.write_text(json.dumps(manifest), encoding="utf-8")
    assert run_table("--kind", "members", "--manifest", str(untagged)).returncode == 0
    proc = run_table("--kind", "release", "--manifest", str(untagged))
    assert proc.returncode == 19
    assert json.loads(proc.stdout.decode("ascii"))["kind"] == "release"


def test_table_escapes_a_pipe_in_a_cell(tmp_path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    row = next(r for r in manifest["members"] if r["setup_write"])
    row["setup_write"]["install"] = [row["cli"], "apply", "a|b"]
    copy = tmp_path / "pipe.json"
    copy.write_text(json.dumps(manifest), encoding="utf-8")
    text = generated("members", copy)
    line = next(item for item in text.splitlines() if "[%s]" % row["slug"] in item)
    assert "a\\|b" in line
    assert line.replace("\\|", "").count("|") == 6  # five columns


# --------------------------------------------------------------------------- #
# The documents' wording: what Step 17 puts in front of readers.
# --------------------------------------------------------------------------- #

def test_readme_says_what_the_companion_installs():
    text = flat(README)
    assert "These projects remain separate." in text
    assert "One option installs the core companion; `-Companions all` adds Find Again." in text
    # The membership rule, in one sentence.
    assert re.search(
        r"A tool joins the companion only when a skill or hook in a released Skill Mesh "
        r"calls it, it installs from a public repository at a tag that passed Skill "
        r"Mesh's checks for it, and it meets the utility project standard\.", text)
    assert "Tripwire's hook is advisory" in text and "It never blocks a command." in text
    assert "`-NoHooks`" in text and "`-SkipHook <slug>`" in text
    switchboard = next(
        line for line in README.read_text(encoding="utf-8").splitlines()
        if line.startswith("| [Switchboard](https://github.com/aberson/switchboard)"))
    assert "role registry" in switchboard
    tripwire = next(
        line for line in README.read_text(encoding="utf-8").splitlines()
        if line.startswith("| [Tripwire](https://github.com/aberson/tripwire)"))
    assert "advisory" in tripwire and "never blocks" in tripwire


def test_install_guide_and_template_carry_the_companion_text():
    guide = flat(INSTALL_GUIDE)
    assert "`-Companions all` adds Find Again" in guide
    assert "A tool joins the companion only when" in guide
    assert "Tripwire's hook is advisory" in guide and "never blocks a command" in guide
    assert "**Companion set**" in RELEASE_TEMPLATE.read_text(encoding="utf-8")


def test_documented_companion_options_exist_in_the_installer():
    source = INSTALLER.read_text(encoding="utf-8")
    match = re.search(r"\[ValidateSet\(([^)]*)\)\]\s*\[string\]\$Companions\b", source)
    assert match, "install-skill-mesh.ps1 no longer declares -Companions with a ValidateSet"
    options = set(re.findall(r"'([^']+)'", match.group(1)))
    for doc in (README, INSTALL_GUIDE, RELEASE_TEMPLATE):
        named = set(re.findall(r"-Companions (\w+)", doc.read_text(encoding="utf-8")))
        assert named, doc.name
        assert named <= options, (doc.name, named - options)


# --------------------------------------------------------------------------- #
# Links: relative files exist, and anchors exist in their targets.
# --------------------------------------------------------------------------- #

LINKED_DOCS = (README, INSTALL_GUIDE, RELEASE_TEMPLATE)
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
_EXPLICIT_ID_RE = re.compile(r"<a\s+(?:id|name)=\"([^\"]+)\"", re.I)
_CODE_SPAN_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")


def _prose_lines(text):
    """The lines outside fenced code blocks."""
    out, fenced = [], False
    for line in text.splitlines():
        if _FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return out


def github_slug(heading):
    slug = heading.strip().lower()
    slug = re.sub(r"[^\w\- ]", "", slug)
    return slug.replace(" ", "-")


def anchors_of(path):
    text = path.read_text(encoding="utf-8")
    anchors = set(_EXPLICIT_ID_RE.findall(text))
    seen = {}
    for line in _prose_lines(text):
        match = _HEADING_RE.match(line)
        if not match:
            continue
        slug = github_slug(match.group(1))
        count = seen.get(slug, 0)
        anchors.add(slug if count == 0 else "%s-%d" % (slug, count))
        seen[slug] = count + 1
    return anchors


def broken_anchors(doc, root):
    offenders = []
    lines = [_CODE_SPAN_RE.sub("", line) for line in _prose_lines(
        doc.read_text(encoding="utf-8"))]
    for raw in release_checks._LINK_RE.findall("\n".join(lines)):
        target = raw.strip().split()[0]
        if target.startswith(("http://", "https://", "mailto:")) or "#" not in target:
            continue
        file_part, anchor = target.split("#", 1)
        target_file = (doc.parent / file_part).resolve() if file_part else doc
        try:
            target_file.relative_to(root.resolve())
        except ValueError:
            continue
        if not target_file.is_file():
            offenders.append("%s: %s -> missing file" % (doc.name, target))
        elif anchor not in anchors_of(target_file):
            offenders.append("%s: %s -> no such anchor" % (doc.name, target))
    return offenders


def test_companion_docs_links_resolve():
    offenders = release_checks.find_broken_local_links(list(LINKED_DOCS), REPO_ROOT)
    assert not offenders, "broken local link(s):\n" + "\n".join(offenders)


def test_companion_docs_anchors_resolve():
    offenders = []
    for doc in LINKED_DOCS:
        offenders += broken_anchors(doc, REPO_ROOT)
    assert not offenders, "broken anchor(s):\n" + "\n".join(offenders)


def test_anchor_check_reds_on_a_missing_anchor(tmp_path):
    """Red anchor for the check above, plus the heading forms it must accept."""
    target = tmp_path / "guide.md"
    target.write_text(
        "# Guide\n\n## Companion tools (`-Companions`)\n\n<a id=\"pinned\"></a>\n\n"
        "```\n# not a heading\n```\n", encoding="utf-8")
    doc = tmp_path / "README.md"
    doc.write_text(
        "[a](guide.md#companion-tools--companions) [b](guide.md#pinned) "
        "[c](#local)\n\n## Local\n\n[d](guide.md#not-a-heading) [e](guide.md#absent) "
        "`[f](guide.md#in-code)`\n", encoding="utf-8")
    offenders = broken_anchors(doc, tmp_path)
    assert offenders == [
        "README.md: guide.md#not-a-heading -> no such anchor",
        "README.md: guide.md#absent -> no such anchor",
    ]
