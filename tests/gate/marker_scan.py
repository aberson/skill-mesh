"""Static PowerShell-marker scan for skill-mesh test files (catalog gate).

documentation/v3-catalog-gate-plan.md (Steps 1 and 2) defines two derived, not
judged, per-file facts; tests/package-integrity/test_gate_classes.py enforces
them against tests/gate-classes.json:

  powershell_marker  the file's text contains any MARKERS entry.
  mixed              the file has tests that exercise a marker and tests that do
                     not. (Step 1's timing evidence also counted any test over
                     5 s as exercising one; the committed check has no timings.)

"Exercises a marker" is decided per test by a static reach scan: starting at the
test's own source (decorators included), follow every name it references into
module-level functions, classes, assignments, fixtures (by argument name, plus
autouse fixtures in scope), conftest.py fixtures in the file's directory chain,
and functions of local helper modules it imports. A test exercises a marker when
any source it reaches contains one. The Step 1 evidence was built with this same
scan (a copy outside the repository); this file is its one owner from Step 2 on.

No test is imported or executed; only `ast` parsing.
"""

import ast
import sys
from pathlib import Path

MARKERS = ("subprocess", "powershell", "install-skill-mesh", "build-distributions", "release.ps1")


def has_marker(text):
    low = text.lower()
    return any(m in low for m in MARKERS)


def _is_fixture(node):
    for dec in node.decorator_list:
        src = ast.unparse(dec)
        if "fixture" in src:
            return True, ("autouse=True" in src.replace(" ", ""))
    return False, False


class Module:
    """Top-level definitions of one parsed file: name -> (source text, node)."""

    def __init__(self, path, root, _cache):
        self.path = path
        text = path.read_text(encoding="utf-8", errors="replace")
        self.text = text
        self.tree = ast.parse(text, filename=str(path))
        self.defs = {}       # name -> source
        self.fixtures = {}   # name -> source
        self.autouse = []    # source of autouse fixtures
        self.aliases = {}    # local alias -> Module (import X as fx)
        self.imported = {}   # local name -> (Module, name in that module)
        for node in self.tree.body:
            self._add(node, text)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    mod = _resolve(a.name, path, root, _cache)
                    if mod is not None:
                        self.aliases[a.asname or a.name.split(".")[-1]] = mod
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mod = _resolve(node.module, path, root, _cache)
                if mod is not None:
                    for a in node.names:
                        if a.name != "*":
                            self.imported[a.asname or a.name] = (mod, a.name)

    def _add(self, node, text):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            src = ast.get_source_segment(text, node, padded=False) or ""
            dec = "\n".join(ast.get_source_segment(text, d) or "" for d in node.decorator_list)
            src = dec + "\n" + src
            self.defs[node.name] = src
            if not isinstance(node, ast.ClassDef):
                fx, auto = _is_fixture(node)
                if fx:
                    self.fixtures[node.name] = src
                    if auto:
                        self.autouse.append(src)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            src = ast.get_source_segment(text, node) or ""
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        self.defs[n.id] = self.defs.get(n.id, "") + "\n" + src


def _resolve(modname, from_path, root, cache):
    """Find a repository-local module by name; None for stdlib/third party."""
    leaf = modname.split(".")
    candidates = []
    d = from_path.parent
    while True:
        candidates.append(d.joinpath(*leaf).with_suffix(".py"))
        if d == root or root not in d.parents:
            break
        d = d.parent
    candidates.append(root.joinpath(*leaf).with_suffix(".py"))
    for sub in ("tools", "_shared", "tests/smoke", "tests/fixtures"):
        candidates.append((root / sub).joinpath(*leaf).with_suffix(".py"))
    for c in candidates:
        if c.is_file():
            key = c.resolve()
            if key not in cache:
                cache[key] = None  # break import cycles
                try:
                    cache[key] = Module(c, root, cache)
                except SyntaxError:
                    cache[key] = None
            return cache[key]
    return None


def _names(src):
    """Every Name id and `alias.attr` pair referenced in a source fragment."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        try:
            import textwrap
            tree = ast.parse(textwrap.dedent(src))
        except SyntaxError:
            return set(), set(), set()
    names, attrs, args = set(), set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            names.add(n.id)
        elif isinstance(n, ast.Attribute):
            attrs.add(n.attr)
            if isinstance(n.value, ast.Name):
                names.add(n.value.id + "." + n.attr)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for a in n.args.args + n.args.kwonlyargs:
                args.add(a.arg)
    return names, attrs, args


class Scanner:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.cache = {}

    def module(self, path):
        key = Path(path).resolve()
        if key not in self.cache or self.cache[key] is None:
            self.cache[key] = Module(key, self.root, self.cache)
        return self.cache[key]

    def conftests(self, path):
        mods = []
        d = Path(path).resolve().parent
        while True:
            c = d / "conftest.py"
            if c.is_file():
                mods.append(self.module(c))
            if d == self.root or self.root not in d.parents:
                break
            d = d.parent
        return mods

    def reach_has_marker(self, start_src, mod, extra_scopes, cls=None):
        """BFS from a test's source through the definitions it can reach.

        `cls` is a ClassScope for a method test: `self.x` / `cls.x` resolve to
        that class's own members, and its setup methods are always reached.
        """
        seen = set()
        queue = [(start_src, mod)]
        for scope in [mod] + extra_scopes:
            for s in scope.autouse:
                queue.append((s, scope))
        if cls is not None:
            queue.extend((s, mod) for s in cls.always)
        while queue:
            src, owner = queue.pop()
            if has_marker(src):
                return True
            names, attrs, args = _names(src)
            hits = []
            for name in names | args:
                for scope in [owner] + ([mod] + extra_scopes if owner is mod else []):
                    hit = self._lookup(name, scope)
                    if hit is not None:
                        hits.append(hit)
                        break
            if cls is not None and owner is mod:
                for name in names:
                    head, _, attr = name.partition(".")
                    if head in ("self", "cls") and attr in cls.members:
                        hits.append((cls.members[attr], mod))
            for hit in hits:
                key = (id(hit[1]), hash(hit[0]))
                if key not in seen:
                    seen.add(key)
                    queue.append(hit)
        return False

    def _lookup(self, name, scope):
        if "." in name:
            alias, attr = name.split(".", 1)
            m = scope.aliases.get(alias)
            if m is not None and attr in m.defs:
                return (m.defs[attr], m)
            return None
        if name in scope.defs:
            return (scope.defs[name], scope)
        if name in scope.fixtures:
            return (scope.fixtures[name], scope)
        if name in scope.imported:
            m, real = scope.imported[name]
            if real in m.defs:
                return (m.defs[real], m)
        return None

    def tests_in(self, path):
        """Yield (test name, source, ClassScope or None)."""
        mod = self.module(path)
        for node in mod.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                yield node.name, mod.defs[node.name], None
            elif isinstance(node, ast.ClassDef) and (
                    node.name.startswith("Test")
                    or any(ast.unparse(b).endswith("TestCase") for b in node.bases)):
                # pytest collects Test* classes and any unittest.TestCase subclass.
                cls = ClassScope(node, mod.text)
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name.startswith("test"):
                        yield node.name + "::" + sub.name, cls.members[sub.name], cls

    def scan_file(self, path):
        """Return {'powershell_marker': bool, 'tests': {name: bool}}."""
        mod = self.module(path)
        scopes = self.conftests(path)
        result = {}
        for name, src, cls in self.tests_in(path):
            result[name] = self.reach_has_marker(src, mod, scopes, cls)
        return {"powershell_marker": has_marker(mod.text), "tests": result}


SETUP_NAMES = {"setup_method", "setup_class", "setup", "setUp", "setUpClass",
               "teardown_method", "teardown_class", "tearDown", "tearDownClass"}


class ClassScope:
    """A test class: its members by name, and the sources every method reaches."""

    def __init__(self, node, text):
        self.members = {}
        self.always = []
        for base in node.bases:
            self.always.append(ast.get_source_segment(text, base) or "")
        for sub in node.body:
            src = ast.get_source_segment(text, sub) or ""
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                dec = "\n".join(ast.get_source_segment(text, d) or "" for d in sub.decorator_list)
                src = dec + "\n" + src
                self.members[sub.name] = src
                fx, auto = _is_fixture(sub)
                if sub.name in SETUP_NAMES or auto:
                    self.always.append(src)
            else:
                # Class attributes: reachable by name and run at class creation.
                self.always.append(src)
                if isinstance(sub, ast.Assign):
                    for t in sub.targets:
                        if isinstance(t, ast.Name):
                            self.members[t.id] = src


if __name__ == "__main__":
    sc = Scanner(sys.argv[1])
    for p in sys.argv[2:]:
        r = sc.scan_file(p)
        hits = sum(r["tests"].values())
        print("%s\tmarker=%s\ttests=%d\tmarker_tests=%d" % (p, r["powershell_marker"], len(r["tests"]), hits))
