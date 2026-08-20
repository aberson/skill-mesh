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
- Which repo a command lands in → `working-directory.md` (two-repo-layer model; Wrong-directory
  guard).
- `owned` is an **explicit registry fact, never signal-derived** → `descriptor-contract.md`. No
  heuristic in this file may promote a repo to owned treatment; only `owned = true` in
  `.claude/observatory/registry.toml` does.
- Parallel-session safety and commit discipline → the workspace `CLAUDE.md` §§ "Parallel session
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

## Owner-match check (shared definition — cited by Step 1 and Rail C)

"Remote owned by the operator" means, exactly: extract the owner path segment from the remote URL
with a regex handling both forms — `(?:git@|https://)[^/:]+[:/]([^/]+)/` — and compare it
**case-insensitively, exact equality** (never substring / `-like`) against the login from
`gh api user --jq .login`. **Any error along the way** (`gh` unauthenticated, URL doesn't parse,
`git remote get-url` fails) counts as **does not match** — the safe default, never "matches". This
check gates **pushes only**; it NEVER gates ownership class (see the descriptor-contract bullet
above).

## Step 0 — resolve the target (exactly ONE repo per invocation)

Precedence:

1. **Explicit positional arg** — tried first as a literal path (relative to cwd, then absolute); if
   no such path exists, as a registry slug (resolved the way [`/user-project`](../user-project/core.md)'s
   SET step resolves a name: match `slug` or `path` in `registry.toml`'s `[[project]]` blocks, then
   `<workspace-root>/<path>`).
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
   `.claude/observatory/registry.toml`:
   - `owned = true` → **OWNED (Rail A)**.
   - `owned = false` → **THIRD-PARTY (Rail C)**.
   - **Unregistered → Rail C treatment, never Rail A** (`owned` is an explicit registry fact; a
     remote-owner match is not ownership). The Owner-match check only sharpens the advisory line: on
     a match, print
     `looks like your own repo — register to unlock the full /repo-update ceremony: uv run --project <workspace-root>/dev-observatory observatory register <slug> --owned`;
     on no match, the standard `--not-owned` form (registration details owned by
     `descriptor-contract.md`).

State the classification in one line before acting:
`repo-wrap: <target> → <OWNED | CODING-ROOT | THIRD-PARTY | BACKUP> (<evidence>[, normalized from <subdir>])`.

## Rail A — registered owned project → delegate

Invoke [`/repo-update`](../repo-update/core.md) via the host's named-skill dispatch against the
target. **This skill adds NOTHING to the ceremony** — repo-update owns docs, commit, posterity
issue, push, and the `observatory sync` hook. If repo-update fails partway, surface its failure
verbatim; do not improvise a fallback ceremony here.

## Rail B — coding-root sync

The formalized version of the previously ad-hoc "back up the workspace": make the coding-root tree
durable **without sweeping parallel sessions, nested repos, or junk**. All git commands run at
`<workspace-root>`; PowerShell-first forms (windows-shell.md — no `&&` on the PowerShell 5.1 floor).

1. **Pre-flight.** Run the same anomaly pre-flight as [`/session-wrap`](../session-wrap/core.md)'s
   Git-verb router Step A — cite, don't restate: foreign state files, active foreign worktrees,
   foreign edits, foreign commits — with two Rail-B deltas: **scope is the coding-root only**, and a
   trigger **downgrades the affected paths to parked-advisory** — it never halts the rail and never
   opens session-wrap's ask gate.
2. **Junk / anomaly triage.** Untracked root-level oddities (shell-expansion accidents, stray state
   files, another session's scratch) are **NEVER staged**. Each gets one advisory line with a
   suggested disposition (delete / gitignore / leave — belongs to a live session) and the exact
   command.
3. **Assemble the path-scoped snapshot commit** (gitignore hygiene folded in, atomically):
   - Enumerate immediate child directories having their own `.git`; any lacking an explicit
     `<dir>/` line in the root `.gitignore` gets one added under a dated comment banner (the
     established onboarding pattern), with `git rm -r --cached <dir>` in the SAME invocation when
     the directory was previously tracked. If the rail stops before committing,
     `git reset -- <dir>` undoes the cache removal — **never leave the shared index mutated without
     its commit.**
   - Build the add list explicitly from `git status --porcelain`: tracked modifications plus safe
     untracked additions, MINUS step-2 anomalies, MINUS foreign-session state files, MINUS
     concurrent-edit suspects — a path already staged by another actor (`M `/`A ` index-side codes
     this invocation didn't create) or modified within the last ~5 minutes AND correlated with a
     step-1 signal gets **parked**, not committed.
   - **Never `git add -A`, never `git add .`, never stash** (a coding-root stash sweeps nested
     repos). Verify the branch first (`git branch --show-current`) and honor the Wrong-directory
     guard (working-directory.md).
   - Commit message: `chore(sync): workspace snapshot <date> — <buckets>`. Split into per-topic
     commits only when buckets are cleanly separable; one snapshot commit is the default, and
     committing a (non-suspect) file another session touched is legal in a labeled snapshot.
4. **Push the CURRENT branch** (`git push origin HEAD`). **Never merge, never switch branches.**
   Close with one advisory line comparing the current branch to the main branch
   (`git rev-list --count <main>..HEAD` / `HEAD..<main>`) — merging is a separate operator decision,
   never taken here.

## Rail C — third-party or unregistered clone

**Safety-critical, non-negotiable:** never push ANY ref to a remote the operator does not own
(Owner-match check above; on-error = not owned); never a bare `git push`, never `git push origin`,
never rely on a branch's configured upstream — **every push names an owner-verified remote and
refspec explicitly.** Never open PRs or issues upstream; never touch the upstream default branch.
All git commands in this rail run as `git -C <target> ...`.

1. **Local durability (executed).** If the tree is dirty, commit on the current branch when it is
   already local work; otherwise commit to a clearly-named local branch (`local/<date>-work`). Local
   commits on a clone touch nothing upstream.
2. **Owned-remote push (executed only if one already exists).** For each configured remote passing
   the Owner-match check (an unregistered repo's own origin included), push explicitly:
   `git -C <target> push <remote> <branch>:<branch>`.
3. **Off-machine options (printed, never executed).** When no operator-owned remote exists, print the
   choices as next-step blocks (execution-context line naming the target directory above each, per
   `command-presentation.md`): `gh repo fork --remote` (note: a fork of a public upstream is
   public), or a private mirror — `gh repo create <login>/<name>-mirror --private` + push.
4. **Upstream drift (read-only).** `git -C <target> fetch origin`, then report ahead/behind vs the
   upstream default branch as one advisory line. **Never auto-pull or rebase.**

## Rail D — outside-workspace or non-repo directory backup

For directories that just need to be durable off-machine. **Backup means PRIVATE** — this rail never
creates a public repo and never flips visibility. All git commands run as `git -C <target> ...`;
printed next-step commands name the target directory.

1. **Secrets posture first.** Filename-level screen (metadata checks only, per `security.md`):
   `.env`, `*secret*`, `*token*`, `*credential*`, `.pem`, `.pfx`, `.p12`, `.ppk`, `id_rsa*`,
   `id_ed25519*`, `.npmrc`, `.aws/`, `.ssh/`, key/cert files. **Any hit is parked with an advisory
   line — never committed, never printed.**
2. **Git repo with an operator-owned remote** (Owner-match check) → path-scoped commit + explicit
   push (`git -C <target> push <remote> <branch>:<branch>`). Done.
3. **Git repo without a remote / not a git repo** → `git init` if needed (safe: Step 1's
   normalization guarantees no enclosing repo exists), commit, then create the off-machine home:
   `gh repo create <login>/<dirname> --private --source . --push`. **Guard:** remote creation
   executes **only** when the target was named EXPLICITLY as the positional arg (per Step 0's
   explicitness rule — `.`/cwd-equivalent args don't count); a pin- or cwd-resolved Rail D target
   gets the commands **printed** instead — a bare invocation must never surprise-create a repo for
   whatever directory it happened to resolve. State the creation loudly, including the undo
   (`gh repo delete <login>/<dirname>`).
4. **Registry advisory (under-workspace targets only).** A Rail D directory living under
   `<workspace-root>` gets one line suggesting
   `uv run --project <workspace-root>/dev-observatory observatory register <slug> --not-owned`;
   directories outside the workspace are out of observatory scope — no registration advisory.

## Flags

- **bare `[<path-or-slug>]`** — default and safest: classify, execute the safe subset, park the rest
  as advisories.
- **`--dry-run`** — classify + full report, **zero mutations** (no commit, no push, no gitignore
  edit, no repo creation).

## Final report

One classification line, then one line per action taken (with short SHAs / push targets), then the
parked-advisory list (each with its exact command), then any next-step fenced blocks last —
execution-context line naming the target directory above each block, one block per observation point
(`command-presentation.md`). On Rail A, the report is `/repo-update`'s own report plus the
classification line.

## Maintenance

No evals suite yet — bootstrap via `/skill-eval-setup repo-wrap` when the contract stabilizes. The
session-wrap git-verb router extension (repo-class-aware delegation, so `/user-wrap` alone covers
these rails) is tracked in the workspace's own issue tracker and sequenced with the utility-hookup
plan's session-wrap step batch — do not hand-edit session-wrap's core ahead of that plan.
