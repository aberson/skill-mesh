# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/repo-wrap/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# repo-wrap — the repo close-out router

`/repo-update` owns the owned-project shipping ceremony, but nothing owned "update the workspace
repo correctly" or "back up this third-party clone" — those close-outs were ad-hoc every time. This
skill routes ONE target repo to the right rail. It invents no new ceremony where an owner exists;
Rail A is a pure pass-through. Invoke as `/repo-wrap [<path-or-slug>] [--dry-run]`.

Throughout this contract, **`<workspace-root>`** means the operator's coding-root workspace
directory (the repo that owns `.claude/observatory/registry.toml`), resolved at run time. It is
never a literal path in this file. **`<login>`** is the operator's own GitHub login as reported by
`gh api user --jq .login`.

**Division of labor (cite, never restate):**

- Owned-project shipping (README/plan/issue/push) → [`/repo-update`](../repo-update/core.md) — Rail
  A delegates verbatim.
- Session transitions and the session-scoped git verb → [`/session-wrap`](../session-wrap/core.md)
  (its git-verb router already delegates phase-complete owned repos to `/repo-update`). repo-wrap is
  **repo-scoped, not session-scoped**: it is safe to run outside any wrap moment and writes no task
  state.
- Build-worktree safety → `<repo>/_shared/worktree-hygiene.md`. Rail A's post-closeout
  reconciliation applies that contract's dirty-state and committed-content proofs before removing
  a linked worktree; age, naming, or a completed build report is never proof by itself.
- Which repo a command lands in → `working-directory.md` (two-repo-layer model; Wrong-directory
  guard).
- `owned` is an **explicit registry fact, never signal-derived** → `descriptor-contract.md`. No
  heuristic in this file may promote a repo to owned treatment; only `owned = true` in
  `.claude/observatory/registry.toml` does.
- Parallel-session safety and commit discipline → the workspace instructions
  (`.claude/workspace-instructions.md`, loaded by the root instruction adapter) §§ "Parallel session
  safety" / "Session wrap & commit discipline" — **senior to everything in this file**.
- Secrets are never dumped to stdout → `security.md` (metadata-only checks; never `cat`/`grep` a
  suspected secrets file).

## When to use / when NOT to use

**Use** when the close-out target is the coding-root, a third-party or unregistered clone, or a
plain directory needing backup — "sync the workspace", "back up the workspace", "update the
workspace repo", "back up `<dir>`", "close out a third-party repo" — or whenever you want one verb
that picks the correct treatment.

**Do NOT use:**

- Session wrap moments → `/session-wrap` (mid-task transition) or `/user-wrap` (sit-back-down).
- An owned project you already know is at a phase boundary → `/repo-update` directly (equivalent;
  Rail A adds only the classification step).
- Workspace-wide hygiene sweeps → `/user-afterparty`.
- Publishing a brand-new project → `/repo-init`.

## Autonomy contract

Autonomous by default; **never a (y/n) gate**. Bare invocation executes the safe subset (local
commits, pushes to remotes the operator owns) and **PARKS** everything ambiguous or outward-facing
as an advisory line with the exact command — printed, not run. `--dry-run` classifies and reports
with zero mutations. **A parked item is a legal, common outcome, not a failure.**

## Writes, failures and re-runs

- **Allowed writes.** Rail A: none of its own (repo-update's). Rail B: root `.gitignore`
  nested-repo lines, the index, the snapshot commit(s) on the current branch (step 3), and their
  push. Rail C: the index, a commit on the current branch or on a new `local/<date>-work` branch
  that step 1 creates, explicit pushes to owner-verified remotes, and the remote-tracking refs that
  step 4's upstream fetch updates. Rail D: `git init` and a commit in the target, explicit pushes
  to owner-verified remotes, and one private GitHub repo plus the `origin` remote that
  `gh repo create --source` adds (`git init` and repo creation subject to Rail D's guard).
  Nothing else: no task state, memory, registry or session-file writes; registration and
  off-machine commands are printed.
- **Failure.** A git or `gh` command that exits non-zero is reported verbatim with its exit code;
  the rail runs no later mutating step that depends on it, and the remedy is a parked advisory.
  Never retry with `--force` or `--force-with-lease`, never `--no-verify`, never fall back to pull,
  rebase, merge, stash or reset (Rail B's `git reset -- <dir>` undo excepted). A rejected push keeps
  the local commit.
- **Re-run.** Re-invoking on the same target converges: a clean tree commits nothing, an up-to-date
  branch pushes nothing, and a Rail D target that gained an owned remote takes Rail D step 2.

## Owner-match check (shared definition — cited by Step 1 and Rails B, C and D)

"Remote owned by the operator" means, exactly: extract the owner path segment from the remote URL
with a regex handling both forms — `(?:git@|https://)[^/:]+[:/]([^/]+)/` — and compare it
**case-insensitively, exact equality** (never substring / `-like`) against the login from
`gh api user --jq .login`. **Any error along the way** (`gh` unauthenticated, URL doesn't parse,
`git remote get-url` fails) counts as **does not match** — the safe default, never "matches". This
check gates **pushes only**; it NEVER gates ownership class (see the descriptor-contract bullet
above).

## Secrets screen (shared definition — cited by Rails B, C and D)

A filename-level screen, metadata checks only (per `security.md`): `.env`, `.env.*`, `*secret*`,
`*token*`, `*credential*`, `*.pem`, `*.pfx`, `*.p12`, `*.ppk`, `*.key`, `*.crt`, `*.cer`, `*.jks`,
`*.keystore`, `id_rsa*`, `id_ed25519*`, `.npmrc`, `.netrc`, `auth.json`, and anything under `.aws/`
or `.ssh/`. **Any hit is parked with an advisory line naming the path — never staged, never
committed, and its contents are never read or printed.**

- **Per-file enumeration.** The screen runs on file paths, never on a collapsed directory line:
  enumerate untracked additions with `git status --porcelain --untracked-files=all` (or
  `git ls-files --others --exclude-standard`), so `?? newdir/` becomes `newdir/.env` and its
  siblings. A `?? <dir>/` line that survives that enumeration is a nested repo: never staged,
  parked with an advisory line.
- **Staging form.** Every `git add` stages exactly the screened per-file list as literal paths —
  never a directory pathspec, never `git add .` or `git add -A`; a long list goes on stdin
  (`git --literal-pathspecs add --pathspec-from-file=-`). Rail B's own `git rm -r --cached <dir>`
  and its `git reset -- <dir>` undo are the only directory pathspecs. A printed staging command
  names the same screened list. Where no list can be computed without mutating (a directory that
  is not yet a repo), print two blocks in this order: first `git -C <abs-target> init`, then
  `/repo-wrap <abs-target>`. The re-invocation stays subject to Step 0's explicitness rule; once
  the directory is a repo its commit is no longer guarded (Rail D step 3), so that run stages the
  screened per-file list and prints, but does not run, the remote creation.
- **Scope.** Rail B screens its untracked additions; Rails C and D screen every path they would
  stage, tracked modifications included. Rail B leaves tracked paths unscreened to avoid parking
  tracked false positives (design-token and documentation files whose names match the list), at a
  residual risk: a modified tracked file with a secret-like name is committed and pushed to an
  owner-verified `origin`. A filename screen cannot prove a file is free of secrets; it is a floor,
  not a clearance.

## Step 0 — resolve the target (exactly ONE repo per invocation)

Resolve `<workspace-root>` first, the way `/user-project` does: walk up to the first directory
holding `.claude/observatory/registry.toml`, starting from the path being resolved — a path-form
argument, else the pin's path when the pin applies, else cwd; a slug argument walks from cwd. If
none is found there is no registry: slugs cannot resolve, and Step 1 classifies by its cases 1
and 3 only.

Precedence:

1. **Explicit positional arg** — tried first as a literal path (relative to cwd, then absolute); if
   no such path exists, as a registry slug (resolved the way [`/user-project`](../user-project/core.md)'s
   SET step resolves a name: match `slug` or `path` in `registry.toml`'s `[[project]]` blocks, then
   `<workspace-root>/<path>`). An argument that is neither stops the run with zero mutations and
   one line: `repo-wrap: cannot resolve <arg> (no such path or registry slug)`.
2. **The `/user-project` pin**, if set.
3. **The cwd repo** (`git rev-parse --show-toplevel`); if cwd is not inside a git repo, the cwd
   directory itself.

**Named deviation from `transition-directory-contract.md`** (which orders pin → argument → cwd):
here an operator-typed positional target outranks the pin — `/repo-wrap career-ops` with a different
pin set means `career-ops`, full stop. **The pin governs bare invocations only.**

An arg of `.`, or any path resolving to exactly what bare resolution (pin/cwd) would have produced,
does **NOT** count as "explicit" for Rail D's creation guard below.

Multi-repo close-out is out of charter — run once per target. For "close out everything I touched
this session", that is `/session-wrap`'s job, not this skill's.

## Step 1 — classify (normalize, then first match wins)

**Normalize first.** Run `git -C <target> rev-parse --show-toplevel` (swallow the not-a-repo error).
If it succeeds and the toplevel differs from the named target, the **toplevel becomes the effective
target for classification** — but when the operator explicitly named a subdirectory, mutating rails
scope their `git add` to that subdirectory's paths within the repo, and the classification line
states the widening.

1. **NOT in any git repo** (probe errored) → **BACKUP (Rail D)**. Normalization guarantees Rail D's
   `git init` can never nest a repo inside an existing one.
2. **Toplevel == `<workspace-root>`** → **CODING-ROOT (Rail B)**. In-coding-root project directories
   land here by construction — they ARE coding-root work (working-directory.md, third case).
3. **Toplevel outside `<workspace-root>`** → **BACKUP (Rail D)** — out of registry scope by
   definition; Rail D's step 2 handles the owned-remote case with the appropriate lighter touch.
4. **Nested repo under `<workspace-root>`** → registry lookup in
   `.claude/observatory/registry.toml`: the `[[project]]` entry whose own top-level `path` (absent →
   its `slug`) equals the repo's workspace-relative path (separator-normalized; case-insensitive on
   Windows). Nested tables' `path` keys are not project paths.
   - `owned = true` → **OWNED (Rail A)**.
   - `owned = false` → **THIRD-PARTY (Rail C)**.
   - A missing or non-boolean `owned`, more than one matching entry, or an unreadable registry →
     **Rail C treatment, never Rail A**, with the reason in the classification evidence.
   - **Unregistered → Rail C treatment, never Rail A** (`owned` is an explicit registry fact; a
     remote-owner match is not ownership). The Owner-match check only sharpens the advisory line: on
     a match, print
     `looks like your own repo — register to unlock the full /repo-update ceremony: uv run --project <workspace-root>/dev-observatory observatory register <slug> --owned`;
     on no match, the standard `--not-owned` form (registration details owned by
     `descriptor-contract.md`).

State the classification in one line before acting:
`repo-wrap: <target> → <OWNED | CODING-ROOT | THIRD-PARTY | BACKUP> (<evidence>[, normalized from <subdir>])`.

## Rail A — registered owned project → delegate

Invoke [`/repo-update`](../repo-update/core.md) via the host's named-skill dispatch with the
effective target's absolute path as its argument. repo-update owns docs, commit, posterity issue,
push, and the `observatory sync` hook. repo-wrap adds only the post-closeout build-worktree
reconciliation below. If repo-update fails partway or returns anything other than
`Result: COMPLETE`, surface its result verbatim and skip reconciliation; do not improvise a fallback
ceremony here.

**Delegate only when the delegation is exact.** Otherwise print the commands below as a parked
advisory (execution-context line naming the target directory), invoke nothing, and stop:

- `--dry-run` → print `/repo-update`. It has no dry-run mode, so invoking it would mutate.
- A `/user-project` pin is set and resolves to a different repo than the effective target → print
  `/user-project <slug>` (or `/user-project clear`), then `/repo-update`. repo-update honors the pin
  ([`/user-project`](../user-project/core.md) § Relationship to other skills;
  `transition-directory-contract.md` § resolved target), so delegating would run its commit, push
  and posterity issue against the pinned repo.
- The operator named a subdirectory (Step 1 widening) → print `/repo-update`. Its ceremony is
  project-wide and cannot honor the subdirectory scope.

### Post-closeout build-worktree reconciliation

Run only after Rail A returns `Result: COMPLETE` and repo-update's pushed
`origin/<default>` ref is verified. Enumerate linked worktrees with
`git -C <target> worktree list --porcelain`, excluding the main checkout. Consider only build
worktrees (branch leaf `build-step-*` or path leaf `worktree_build-step-*`) that session-wrap's
activity probe classifies as stale. Remove a candidate only when it is unlocked, attached to a
branch, `git -C <worktree> status --porcelain --untracked-files=all` is empty, and
`git -C <target> cherry origin/<default> <branch>` contains no `+` line. Those checks apply
`<repo>/_shared/worktree-hygiene.md` §3: no dirty state and no unique committed patch.

Remove a qualifying candidate from outside it with
`git -C <target> worktree remove <canonical-path>` (never `--force`), verify it disappeared from
both the registry and disk, and keep its branch. A failed or uncertain check keeps the worktree and
reports the reason; never prune, raw-delete, or delete its branch. Under `--dry-run`, report what
would be removed without mutating. End with
`Worktrees: removed <N> redundant build worktree(s); kept <M> (<reasons>)` (or `would remove`).
Zero candidates is a normal result.

## Rail B — coding-root sync

The formalized version of the previously ad-hoc "back up the workspace": make the coding-root tree
durable **without sweeping parallel sessions, nested repos, or junk**. All git commands run at
`<workspace-root>`; PowerShell-first forms (windows-shell.md — no `&&` on the PowerShell 5.1 floor).

1. **Pre-flight.** Run the same anomaly pre-flight as [`/session-wrap`](../session-wrap/core.md)'s
   Git-verb router Step A — cite, don't restate: foreign state files, active foreign worktrees,
   foreign edits, foreign commits — with two Rail-B deltas: **scope is the coding-root only**, and a
   trigger **downgrades the affected paths to parked-advisory** — it never halts the rail and never
   opens session-wrap's ask gate. repo-wrap has no session edit set, so session-wrap's check 3
   (foreign edits) is replaced by step 3's concurrent-edit suspect test. Checks 1, 2 and 4 are
   **signals**: a state file whose plan matches the invoking session's active plan is not foreign
   (unknown = foreign), and a signal's own artifacts (state files, worktree paths) are never staged.
2. **Junk / anomaly triage.** Untracked root-level oddities (shell-expansion accidents, stray state
   files, another session's scratch) are **NEVER staged**. Each gets one advisory line with a
   suggested disposition (delete / gitignore / leave — belongs to a live session) and the exact
   command.
3. **Assemble the path-scoped snapshot commit** (gitignore hygiene folded in, atomically):
   - **Snapshot checks first, before any index mutation.** Honor the Wrong-directory guard
     (working-directory.md) and verify the branch (`git branch --show-current`; empty = detached
     HEAD → commit nothing, park the whole snapshot). If `git diff --cached --name-only` lists
     anything, another actor staged it: commit nothing and park the whole snapshot, naming those
     paths — a plain commit would sweep them in.
   - Enumerate immediate child directories having their own `.git`; any lacking an explicit
     `<dir>/` line in the root `.gitignore` gets one added under a dated comment banner (the
     established onboarding pattern), with `git rm -r --cached <dir>` in the SAME invocation when
     the directory was previously tracked. Apply the concurrent-edit suspect test (next bullet) to
     the root `.gitignore` **before** writing it: if it is already a suspect, mutate nothing, park
     the hygiene as an advisory with its exact commands, and park any tracked paths under those
     directories with it. Otherwise the rail's own `.gitignore` edit and its `git rm --cached` go
     into the same commit. If the rail stops before that commit lands, it undoes both halves —
     `git reset -- <dir>` and removal of the lines it appended to `.gitignore` — so a re-run meets
     the same trigger; **never leave the shared index mutated without its commit.** A
     subdirectory-scoped run (Step 1) skips this bullet and prints it as a parked advisory: the root
     `.gitignore` lies outside the named scope.
   - Build the add list explicitly, per file, from `git status --porcelain --untracked-files=all`
     (Secrets screen above): tracked modifications plus safe untracked additions, MINUS step-2
     anomalies, MINUS foreign-session state files, MINUS Secrets-screen hits among the untracked
     additions, MINUS concurrent-edit suspects — a path this invocation did not write that was
     modified within the last ~5 minutes is a suspect and gets **parked**, not committed, whether or
     not a step-1 signal is present. repo-wrap cannot tell another live window's fresh edit from its
     own session's, so both park; a re-run after the window commits them.
   - **Never `git add -A`, never `git add .`, never stash** (a coding-root stash sweeps nested
     repos).
   - Commit message: `chore(sync): workspace snapshot <date> - <buckets>` (ASCII hyphen). Split
     into per-topic commits only when buckets are cleanly separable; one snapshot commit is the
     default, and committing a (non-suspect) file another session touched is legal in a labeled
     snapshot.
4. **Push the CURRENT branch** (`git push origin HEAD`) only when `origin` passes the Owner-match
   check and step 3 did not park the whole snapshot (detached HEAD, or an index another actor
   staged — a live session may be mid-commit); otherwise park the push command. **Never merge,
   never switch branches.**
   Close with one advisory line comparing the current branch to the main branch
   (`git rev-list --count <main>..HEAD` / `HEAD..<main>`) — merging is a separate operator decision,
   never taken here.

## Rail C — third-party or unregistered clone

**Safety-critical, non-negotiable:** never push ANY ref to a remote the operator does not own
(Owner-match check above; on-error = not owned); never a bare `git push`, never `git push origin`,
never rely on a branch's configured upstream — **every push names an owner-verified remote and
refspec explicitly.** Never open PRs or issues upstream; never touch the upstream default branch.
All git commands in this rail run as `git -C <target> ...`.

The **upstream remote** is the first of `upstream`, `origin` that is configured and fails the
Owner-match check (after `gh repo fork --remote`, `origin` is the operator's fork and the original
is `upstream`). With neither, there is no upstream remote.

1. **Local durability (executed).** If the tree is dirty, commit on the current branch when it is
   already local work; otherwise commit to a clearly-named local branch (`local/<date>-work`). Local
   commits on a clone touch nothing upstream. The current branch is **already local work** when it
   is not the upstream remote's default branch and does not track a branch on a remote failing the
   Owner-match check; an unknown default branch (no upstream remote included) or a detached HEAD
   counts as not local work. The new branch is created at HEAD with `switch -c`, which carries the
   working tree (append `-2`, `-3`, … if the name exists). Stage the explicit per-file list —
   tracked modifications and untracked additions (scoped per Step 1), minus every Secrets-screen
   hit, tracked or untracked.
2. **Owned-remote push (executed only if one already exists).** For each configured remote passing
   the Owner-match check (an unregistered repo's own origin included), push explicitly:
   `git -C <target> push <remote> <branch>:<branch>`.
3. **Off-machine options (printed, never executed).** When no operator-owned remote exists, print the
   choices as next-step blocks (execution-context line naming the target directory above each, per
   `command-presentation.md`): `gh repo fork --remote` (note: a fork of a public upstream is
   public), or a private mirror — `gh repo create <login>/<name>-mirror --private` + push.
4. **Upstream drift (read-only).** `git -C <target> fetch <upstream-remote>`, then report
   ahead/behind vs the upstream default branch as one advisory line. **Never auto-pull or rebase.**
   Under `--dry-run`, skip the fetch and report from the existing remote-tracking refs, labeled
   "as of last fetch". With no upstream remote, print one advisory line and fetch nothing.

## Rail D — outside-workspace or non-repo directory backup

For directories that just need to be durable off-machine. **Backup means PRIVATE** — this rail never
creates a public repo and never flips visibility. All git commands run as `git -C <target> ...`;
printed next-step commands name the target directory.

1. **Secrets posture first.** Apply the Secrets screen (above) to every path this rail would
   stage. **Any hit is parked with an advisory line — never committed, never printed.**
2. **Git repo with an operator-owned remote** (Owner-match check) → path-scoped commit + explicit
   push (`git -C <target> push <remote> <branch>:<branch>`). Done.
3. **Git repo without a remote / not a git repo** → `git init` if needed (safe: Step 1's
   normalization guarantees no enclosing repo exists), commit, then create the off-machine home:
   `gh repo create <login>/<dirname> --private --source <target> --push` (the target path, never
   `.`: cwd is often not the target). **Guard:** remote creation — and, for a directory that is
   not yet a git repo, the `git init` and its commit — executes **only** when the target was named
   EXPLICITLY as the positional arg (per Step 0's explicitness rule — `.`/cwd-equivalent args don't
   count); a pin- or cwd-resolved Rail D target gets those commands **printed** instead (order:
   Secrets screen § Staging form) — a bare invocation must never surprise-create a repo, local or
   remote, for whatever directory it happened to resolve. State the creation loudly, including the
   undo (`gh repo delete <login>/<dirname>`).
4. **Registry advisory (under-workspace targets only).** A Rail D directory living under
   `<workspace-root>` gets one line suggesting
   `uv run --project <workspace-root>/dev-observatory observatory register <slug> --not-owned`;
   directories outside the workspace are out of observatory scope — no registration advisory.

## Flags

- **bare `[<path-or-slug>]`** — default and safest: classify, execute the safe subset, park the rest
  as advisories.
- **`--dry-run`** — classify + full report, **zero mutations** (no commit, no push, no gitignore
  edit, no repo creation, no fetch, no `/repo-update` delegation).

## Final report

One classification line, then one line per action taken (with short SHAs / push targets; a failed
command with its exit code), then the parked-advisory list (each with its exact command), then any
next-step fenced blocks last — execution-context line naming the target directory above each block,
one block per observation point (`command-presentation.md`). On Rail A, the report is
`/repo-update`'s own report plus the classification line.

## Maintenance

No evals suite yet — bootstrap via `/skill-eval-setup repo-wrap` when the contract stabilizes. The
session-wrap git-verb router extension (repo-class-aware delegation, so `/user-wrap` alone covers
these rails) is tracked in the workspace's own issue tracker and sequenced with the utility-hookup
plan's session-wrap step batch — do not hand-edit session-wrap's core ahead of that plan.
