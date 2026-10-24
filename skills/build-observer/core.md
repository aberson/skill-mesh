# NOTE: This is the canonical provider-independent contract. All provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve the packaged validator as `<skill-dir>/scaffold_portfolio.py`, where `<skill-dir>` is the directory containing this loaded skill package. Never substitute a compatibility-launcher path.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# build-observer — propose one `[project.portfolio]` registry block

Scaffolds the `[project.portfolio]` block for one project (dev-observatory portfolio-pages plan,
`dev-observatory/docs/archived-plans/plans/portfolio-pages-plan.md` §5a / §5e / Step 27). Invoke as
`/build-observer <slug>`.

The **CREATIVE** work — wording the blurb, choosing proofs, naming a demo — is done here in prose,
from primary sources. The **MECHANICAL** work — verb-name validation, relates-slug validation,
length/count caps, TOML rendering — is delegated to `scaffold_portfolio.py` in this skill's asset
directory, which **imports `dev_observatory`'s own constants and renderer rather than re-declaring
any of them** (`code-quality.md` § one source of truth for data-shape constants; never duplicate
`registry.py`'s validation).

Run bare: `/build-observer <slug>`. No flags are required and the skill asks no content questions
mid-run: it reads, drafts, validates, and prints a proposal plus a redline report every time. It
never writes into `registry.toml` or `snapshot.json` itself (see **Write mode**). With no slug, print this host's
invocation shape for `build-observer <slug>` and stop; never guess a project.

## Steps

### 1. Locate the project

Resolve the coding root before reading project data. If the caller supplies a root, accept it only
when it is absolute and contains both `dev-observatory/pyproject.toml` and
`.claude/observatory/registry.toml`; an invalid explicit root is **HELD** and never falls through.
Without an explicit root, search the invocation cwd and its ancestors for the nearest directory
containing both markers. A project pin may identify the target project, but it never substitutes for
this coding root. If the inferred root is ambiguous, absent, or lacks the registry, return **HELD**
before invoking the validator.

Resolve the registry as the absolute path `<root>/.claude/observatory/registry.toml`. Read the
relevant `[[project]]` table with the host's file-read primitive; the registry is a small committed
file. Resolve the slug's path and existing fields (`category`, current `launch`/`launches`, whether a
`[project.portfolio]` block already exists). If the slug has no registry entry, say so and continue
anyway (the validator still renders valid TOML; it just has nowhere to be pasted yet).

### 2. Read the derived verbs

Read the absolute path `<root>/.claude/observatory/snapshot.json` and find this slug's `projects[*]` entry — its
`verbs[*].verb` names are what showcase/highlights must resolve against.

**Note:** the snapshot may be absent or carry a stale `snapshot_version`; continue in either case.
`scaffold_portfolio.py` falls back to a raw JSON read of the same `verbs` shape and discloses the
absence, stale version, or unreadable content. **This skill never runs `observatory scan`/`status`
itself** — that would refresh (i.e. WRITE) the on-disk snapshot cache, which is outside a
proposal-only skill's job.

### 3. Read the project's own documentation

In order of preference, read whichever exist: `README.md`, the project's instruction file
(CLAUDE.md or AGENTS.md), `plans/plan.md` (or `docs/*-plan.md`). Pull out, verbatim or close to it:

- the one- or two-sentence **mission** (for the blurb / card);
- **documented guarantees or invariants** — a "Design decisions" section, a bulleted list of hard
  rules, a schema table's "Rule" column — for `proofs`. **Never invent a guarantee the docs don't
  state.**
- any **named mention of a sibling registry project** (e.g. "External consumers such as Find
  Again... read records only through the format contract") — that sentence is a legitimate,
  grounded `relates` clause. **Never invent a relationship between two projects that isn't written
  down somewhere.**
- **CLI usage / commands** that suggest which verb best demonstrates the tool — candidate
  `showcase`/`highlights` picks (validated in Step 5; a good guess that isn't a real verb yet still
  gets reported, per Step 6).

If none of these documents can be read, leave every prose field (`blurb`, `card`, `proofs`,
`relates`, `live_url`, `contribution`) unset rather than drafting from memory or the slug name.
Leave `tag` unset too: the group-label fallback named in Step 4 is applied by the renderer
(`arc.py` `resolve_tag`), so passing that label would only pin a value the renderer already
supplies. Showcase and highlight picks from Step 2's derived verbs still apply, because they do
not come from the docs; Step 5 then reports what survives (possibly nothing).

### 4. Draft the field values (house voice)

- **`blurb`** — at most 140 chars, a noun-phrase pitch, no leading article, present tense implied.
  Example house voice (plan §5a): *"Immutable Markdown decision records with validated
  supersession"*. Fallback if nothing confident emerges: leave it unset — render falls back to the
  derived plan goal.
- **`card`** — only draft this for a flagship project's fuller card copy; omit for
  utility/fun/professional/third-party entries (plan §5a: "site flagship cards only").
- **`tag`** — one word from the palette in plan §5a (Safety, Decisions, Verification, Coordination,
  Retrieval, Consistency, Measurement, Hygiene, Rigor, Management, Benchmarking, Aesthetics,
  Routing, ...) or coin a new one-word chip if one fits the evidence; otherwise leave it unset and
  let the renderer fall back to the group label.
- **`proofs`** — up to 3, each a short guarantee noun-phrase, each traceable to a specific line you
  just read.
- **`showcase`** — the ONE verb name that best answers "watch this work". Prefer an already-derived,
  non-`status` verb. If the ideal demo command doesn't exist as a derived verb yet, still name it —
  the validator will drop it and the redline report will tell you exactly what `[project.launch]`
  entry would need to be added to realize it.
- **`highlights`** — up to 3 more verb names, same reasoning.
- **`relates`** — up to 4 `"slug: clause"` pairs, only for documented relationships (Step 3).
- **`repo_public` / `public`** — leave both unset (default false) **UNLESS** the operator's
  instruction explicitly named this project as display-listed. If it did, add `--public` to the
  structured switches and add `--public-reason` with the instruction as its structured value in
  Step 5 — the launcher hard-refuses `--public` without a reason string, and this skill's prose
  never fabricates one.
- **`live_url` / `contribution`** — only when the docs state a deployed URL or (third-party rows
  only) an operator contribution.

Build a structured invocation payload in the host's data layer, never by concatenating shell text.
The payload has absolute `project`, `helper`, `root`, `registry`, and `snapshot` strings; a
non-empty `slug`; an ordered `fields` array of `{"name":"--flag","value":"text"}` records; an
ordered `switches` array; and a JSON boolean `public_authorized`. Preserve drafted Unicode and
punctuation exactly in JSON. The only allowed field names are `--blurb`, `--card`, `--tag`,
`--proof`, `--showcase`, `--highlight`,
`--relates`, `--live-url`, `--contribution`, and `--public-reason`; omit empty values.
The only switches are `--repo-public` and `--public`, and either requires
`public_authorized=true` from the operator's explicit display-listing instruction. `--public`
also requires a non-empty `--public-reason`. A non-empty value that begins with `-`, ends in a
backslash, contains backslashes before a quote, or contains Unicode remains data.

Use the host's file-write primitive to write those exact UTF-8 JSON bytes, without a BOM, to a new
ASCII-named `.json` file beneath the host-private `<system-temp>/build-observer/` directory. This is
a data write, never a shell, Python, or model-computed encoding step: drafted text appears only in
the JSON file. Do not write the payload under the project, registry, snapshot, generated package,
or an installed skill tree. The launcher below reads that one file and deletes it in `finally` on
success or failure. If the host cannot create this private transient file, return
`required_tool_missing`; do not improvise an encoder or shell interpolation.
The launcher consumes the exact file the host just wrote, so the host does not compute or compare a
digest. Retain the structured payload as the intended-field record for the final report.

### 5. Validate + render

Use a prepared existing environment and Windows PowerShell 5.1 only. Other editions or a missing
Windows PowerShell capability are HELD; there is no POSIX fallback. Before constructing the payload,
verify that `<project>/uv.lock`, `<project>/.venv/Scripts/python.exe`, the packaged helper, and the
registry are readable. Never install, sync, download, or retry through the network.

Replace `<ASCII-ABSOLUTE-HOST-PRIVATE-PAYLOAD-PATH>` below with only the absolute ASCII path created
by the file-write primitive. Before substitution, require the path to match
`^[A-Za-z]:\\(?:[A-Za-z0-9._-]+\\)*[A-Za-z0-9._-]+\.json$`; no drafted text is inserted into the
block. Run this entire fixed-text block as one Windows PowerShell command:

```powershell
& {
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'
    $utf8 = New-Object System.Text.UTF8Encoding($false, $true)
    $originalLocation = Get-Location
    $process = $null
    $payloadPath = $null
    $deletePayload = $false
    $launcherExit = 125
    try {
        $payloadPathLiteral = '<ASCII-ABSOLUTE-HOST-PRIVATE-PAYLOAD-PATH>'
        if ($payloadPathLiteral -notmatch '^[A-Za-z]:\\(?:[A-Za-z0-9._-]+\\)*[A-Za-z0-9._-]+\.json$') {
            throw 'invalid invocation payload path'
        }
        $payloadRoot = [IO.Path]::GetFullPath((Join-Path ([IO.Path]::GetTempPath()) 'build-observer'))
        $payloadPath = [IO.Path]::GetFullPath($payloadPathLiteral)
        if (-not $payloadPath.StartsWith(
                $payloadRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw 'invalid invocation payload path: outside host-private temp root'
        }
        if (-not (Test-Path -LiteralPath $payloadPath -PathType Leaf)) {
            throw 'invalid invocation payload path: file is missing'
        }
        $deletePayload = $true
        if ($PSVersionTable.PSEdition -ne 'Desktop' -or
                $PSVersionTable.PSVersion.Major -ne 5 -or
                $PSVersionTable.PSVersion.Minor -ne 1) {
            throw 'required_tool_missing: Windows PowerShell 5.1 is required'
        }
        $payloadBytes = [IO.File]::ReadAllBytes($payloadPath)
        if ($payloadBytes.Length -ge 3 -and $payloadBytes[0] -eq 0xEF -and
                $payloadBytes[1] -eq 0xBB -and $payloadBytes[2] -eq 0xBF) {
            throw 'invalid invocation payload encoding: UTF-8 BOM is not allowed'
        }
        $payloadJson = $utf8.GetString($payloadBytes)

        function Assert-NoLoneJsonSurrogateEscape([string]$json) {
            for ($index = 0; $index -lt $json.Length; $index++) {
                if ($json[$index] -ne '\') {
                    continue
                }
                $slashStart = $index
                while ($index -lt $json.Length -and $json[$index] -eq '\') {
                    $index++
                }
                $slashCount = $index - $slashStart
                if (($slashCount % 2) -eq 0 -or $index + 4 -ge $json.Length -or
                        $json[$index] -ne 'u') {
                    $index--
                    continue
                }
                $hex = $json.Substring($index + 1, 4)
                if ($hex -notmatch '^[0-9A-Fa-f]{4}$') {
                    $index--
                    continue
                }
                $code = [Convert]::ToInt32($hex, 16)
                if ($code -ge 0xD800 -and $code -le 0xDBFF) {
                    $next = $index + 5
                    if ($next + 5 -ge $json.Length -or $json[$next] -ne '\' -or
                            $json[$next + 1] -ne 'u' -or
                            $json.Substring($next + 2, 4) -notmatch '^[dD][c-fC-F][0-9A-Fa-f]{2}$') {
                        throw 'invalid invocation payload: lone surrogate escape'
                    }
                    $index = $next + 5
                }
                elseif ($code -ge 0xDC00 -and $code -le 0xDFFF) {
                    throw 'invalid invocation payload: lone surrogate escape'
                }
                else {
                    $index += 4
                }
            }
        }
        Assert-NoLoneJsonSurrogateEscape $payloadJson
        $payload = $payloadJson | ConvertFrom-Json

        function Assert-InvocationText([string]$value, [string]$label) {
            if ($null -eq $value) {
                throw "invalid invocation payload: null $label"
            }
            for ($index = 0; $index -lt $value.Length; $index++) {
                $character = $value[$index]
                if ([int]$character -eq 0) {
                    throw "invalid invocation payload: NUL in $label"
                }
                if ([char]::IsHighSurrogate($character)) {
                    if ($index + 1 -ge $value.Length -or
                            -not [char]::IsLowSurrogate($value[$index + 1])) {
                        throw "invalid invocation payload: lone surrogate in $label"
                    }
                    $index++
                }
                elseif ([char]::IsLowSurrogate($character)) {
                    throw "invalid invocation payload: lone surrogate in $label"
                }
            }
        }

        foreach ($property in @('project', 'helper', 'root', 'registry', 'snapshot', 'slug')) {
            if ([string]::IsNullOrEmpty([string]$payload.$property)) {
                throw "invalid invocation payload: missing $property"
            }
            Assert-InvocationText ([string]$payload.$property) $property
        }
        if ([string]$payload.slug -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
            throw 'invalid invocation payload: unsupported slug shape'
        }
        if ($payload.public_authorized -isnot [bool]) {
            throw 'invalid invocation payload: public_authorized must be a JSON boolean'
        }
        foreach ($property in @('project', 'helper', 'root', 'registry', 'snapshot')) {
            if (-not [IO.Path]::IsPathRooted([string]$payload.$property)) {
                throw "invalid invocation payload: $property is not absolute"
            }
        }

        $root = [IO.Path]::GetFullPath([string]$payload.root)
        $project = [IO.Path]::GetFullPath([string]$payload.project)
        $helper = [IO.Path]::GetFullPath([string]$payload.helper)
        $registry = [IO.Path]::GetFullPath([string]$payload.registry)
        $snapshot = [IO.Path]::GetFullPath([string]$payload.snapshot)
        if ($project -ne [IO.Path]::GetFullPath((Join-Path $root 'dev-observatory')) -or
                $registry -ne [IO.Path]::GetFullPath((Join-Path $root '.claude\observatory\registry.toml')) -or
                $snapshot -ne [IO.Path]::GetFullPath((Join-Path $root '.claude\observatory\snapshot.json'))) {
            throw 'invalid invocation payload: coding-root paths disagree'
        }
        foreach ($requiredFile in @(
                (Join-Path $project 'pyproject.toml'),
                (Join-Path $project 'uv.lock'),
                (Join-Path $project '.venv\Scripts\python.exe'),
                $helper,
                $registry)) {
            if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
                throw "required_tool_missing: $requiredFile"
            }
        }

        $allowedFields = @{
            '--blurb' = $true; '--card' = $true; '--tag' = $true; '--proof' = $true
            '--showcase' = $true; '--highlight' = $true; '--relates' = $true
            '--live-url' = $true; '--contribution' = $true; '--public-reason' = $true
        }
        $allowedSwitches = @{'--repo-public' = $true; '--public' = $true}
        $arguments = @(
            'run', "--project=$project", '--no-sync', '--frozen', '--offline',
            '--no-python-downloads', 'python', '-B', $helper, [string]$payload.slug,
            "--root=$root", "--registry=$registry", "--snapshot=$snapshot"
        )
        $publicReasonPresent = $false
        foreach ($field in @($payload.fields)) {
            $name = [string]$field.name
            $value = [string]$field.value
            Assert-InvocationText $name 'field name'
            Assert-InvocationText $value $name
            if (-not $allowedFields.ContainsKey($name)) {
                throw "invalid invocation payload: unsupported field $name"
            }
            if ([string]::IsNullOrEmpty($value)) {
                continue
            }
            if ($name -eq '--public-reason') {
                $publicReasonPresent = $true
            }
            $arguments += "$name=$value"
        }
        foreach ($switch in @($payload.switches)) {
            $name = [string]$switch
            Assert-InvocationText $name 'switch name'
            if (-not $allowedSwitches.ContainsKey($name)) {
                throw "invalid invocation payload: unsupported switch $name"
            }
            if ($payload.public_authorized -ne $true) {
                throw "invalid invocation payload: $name lacks operator authority"
            }
            $arguments += $name
        }
        if ($arguments -contains '--public' -and -not $publicReasonPresent) {
            throw 'invalid invocation payload: --public requires --public-reason'
        }

        function ConvertTo-CrtArgument([string]$value) {
            if ($null -eq $value) {
                throw 'invalid invocation payload: null argv value'
            }
            $builder = New-Object System.Text.StringBuilder
            [void]$builder.Append('"')
            $backslashes = 0
            foreach ($character in $value.ToCharArray()) {
                if ($character -eq '\') {
                    $backslashes++
                    continue
                }
                if ($character -eq '"') {
                    if ($backslashes -gt 0) {
                        [void]$builder.Append(('\' * (2 * $backslashes)))
                    }
                    [void]$builder.Append('\"')
                    $backslashes = 0
                    continue
                }
                if ($backslashes -gt 0) {
                    [void]$builder.Append(('\' * $backslashes))
                    $backslashes = 0
                }
                [void]$builder.Append($character)
            }
            if ($backslashes -gt 0) {
                [void]$builder.Append(('\' * (2 * $backslashes)))
            }
            [void]$builder.Append('"')
            return $builder.ToString()
        }

        try {
            $uv = Get-Command uv -CommandType Application -ErrorAction Stop
        }
        catch {
            throw 'required_tool_missing: native uv.exe was not found'
        }
        if ([IO.Path]::GetExtension($uv.Source) -ine '.exe') {
            throw 'required_tool_missing: uv must resolve to a native .exe'
        }
        Set-Location -LiteralPath $root -ErrorAction Stop
        $startInfo = New-Object Diagnostics.ProcessStartInfo
        $startInfo.FileName = $uv.Source
        $startInfo.Arguments = (($arguments | ForEach-Object {
            ConvertTo-CrtArgument ([string]$_)
        }) -join ' ')
        $startInfo.WorkingDirectory = $root
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $startInfo.StandardOutputEncoding = $utf8
        $startInfo.StandardErrorEncoding = $utf8
        $startInfo.EnvironmentVariables['PYTHONUTF8'] = '1'
        $startInfo.EnvironmentVariables['PYTHONDONTWRITEBYTECODE'] = '1'

        $process = New-Object Diagnostics.Process
        $process.StartInfo = $startInfo
        if (-not $process.Start()) {
            throw 'required_tool_missing: uv did not start'
        }
        $stdoutBytes = New-Object IO.MemoryStream
        $stderrBytes = New-Object IO.MemoryStream
        $stdoutTask = $process.StandardOutput.BaseStream.CopyToAsync($stdoutBytes)
        $stderrTask = $process.StandardError.BaseStream.CopyToAsync($stderrBytes)
        $process.WaitForExit()
        [Threading.Tasks.Task]::WaitAll(@($stdoutTask, $stderrTask))
        $stdout = [Console]::OpenStandardOutput()
        $stdout.Write($stdoutBytes.GetBuffer(), 0, [int]$stdoutBytes.Length)
        $stdout.Flush()
        $stderr = [Console]::OpenStandardError()
        $stderr.Write($stderrBytes.GetBuffer(), 0, [int]$stderrBytes.Length)
        $stderr.Flush()
        $launcherExit = $process.ExitCode
    }
    catch {
        $reason = $utf8.GetBytes("HELD: " + [string]$_.Exception.Message + "`n")
        $stderr = [Console]::OpenStandardError()
        $stderr.Write($reason, 0, $reason.Length)
        $stderr.Flush()
    }
    finally {
        if ($null -ne $process) {
            $process.Dispose()
        }
        if ($deletePayload -and $null -ne $payloadPath) {
            Remove-Item -LiteralPath $payloadPath -Force -ErrorAction SilentlyContinue
        }
        Set-Location -LiteralPath $originalLocation.Path -ErrorAction Stop
    }
    exit $launcherExit
}
```

The block writes the child's already-captured stdout and stderr bytes directly to its own native
standard streams; the host's PowerShell tool therefore returns the validator's UTF-8 TOML and
redline without base64, model decoding, or text reconstruction. It exits with the child's actual
exit code. A preflight or block failure writes a strict UTF-8 `HELD:` reason to stderr, leaves stdout
empty, and exits 125. Confirm that the private payload no longer exists after either outcome. Treat
a launched nonzero exit as HELD when stderr establishes a missing runtime, lock, import, or helper;
other nonzero exits follow Step 6. Never infer TOML, refresh the snapshot, or write the registry.
Never ask the model to decode transport text or compute a hash.

The script prints:

- **stderr** — **the redline report; relay it per Step 6 (every `[build-observer]` line
  verbatim).** Its own lines are prefixed `[build-observer]`:
  - `blurb`: always one `KEPT` (with its length), `DROPPED` (empty, over length, or bad charset),
    or `OMITTED` line;
  - `showcase` and each `highlight`, when passed: `KEPT` (validated against the derived button
    verbs) or `DROPPED` with the exact reason (unknown or not-yet-derived verb, `status`, or a
    slug absent from the snapshot), plus a truncation notice when more than 3 highlights validate;
  - `proofs`, `relates`, `live_url`, `public`, and `repo_public`, when passed: a `KEPT` count or
    value, a per-item `DROPPED` reason (bad shape, self-relate, dead relates slug, non-http(s)
    URL), or a truncation notice (more than 3 proofs print only the truncation notice, with no
    `KEPT` line);
  - registry and snapshot notes: slug not registered, slug not in the snapshot, the stale-snapshot
    fallback or an unreadable snapshot, and "no portfolio fields survived validation".

  `card`, `tag`, and `contribution` are passed through verbatim with **no** validation line (the
  registry parser only checks that they are strings). `proofs: KEPT` and `relates: KEPT` confirm
  only counts, shape, and slugs; the wording of each proof and relates clause is never validated.
  Lines prefixed `dev-observatory: registry ignored:` mean the registry did not load, so every
  relates slug was checked against an empty registry. Lines prefixed
  `dev-observatory: portfolio '<slug>':` concern blocks already in the registry (this project's
  current block or another project's). Other `dev-observatory:` lines (for example
  `views '<slug>':`) do not concern the portfolio block and are not part of the redline.
- **stdout** — the `[project.portfolio]` TOML snippet, ready to paste under the project's existing
  `[[project]]` entry in `registry.toml`. Empty (with a stderr note) if nothing survived validation.

### 6. Report

Return, in order:

1. the printed TOML snippet (none after a nonzero exit; see item 2);
2. the redline: every `[build-observer]` stderr line verbatim (`KEPT`/`DROPPED`/`OMITTED`,
   truncation notices, and registry and snapshot notes), so the operator sees confident-vs-guessed
   at a glance; any `dev-observatory: registry ignored:` line (relates validation is then not
   meaningful) and any `dev-observatory: portfolio` line naming this slug, verbatim, plus a
   one-line count of those naming other slugs; and one line naming the prose-sourced values that
   were not mechanically validated: any `card`/`tag`/`contribution` value and the wording of each
   kept proof and relates clause (only their counts, shape, and slugs were checked). **On a
   nonzero exit** (Step 5), the redline is instead the command's entire stderr verbatim, including
   lines with no `[build-observer]` prefix (for example argparse `usage:`/`error:` lines or a
   traceback), plus the exit code;
3. any explicit "add a `[project.launch]` entry for X" follow-ups the validator surfaced;
4. a one-line reminder that **no project, registry, snapshot, package, or installed-skill file was
   written** and the private payload was deleted — the operator (or Step 28's authoring pass) pastes
   the block manually.

On HELD, return the reason, including `required_tool_missing` when applicable, then the captured
stdout and stderr verbatim and the actual exit code. Return no snippet, and include the scoped
no-product-write reminder. Never infer or reconstruct output after a failure.

## Write mode

Plan §5e allows either "into the project's registry entry, or emit it for the operator to paste" —
**this skill implements only the latter.** Concretely: `/build-observer <slug>` PROPOSES a block and
PRINTS it (stdout: the TOML snippet; stderr: the redline report). It is **read-only** against both
`registry.toml` and `snapshot.json` — `scaffold_portfolio.py` never opens either for writing, never
calls `registry.upsert_entry`, and never runs `observatory scan`/`status` (which would refresh the
snapshot cache on disk). Two things always stay separate, deliberate, human actions performed AFTER
this skill returns:

1. **Pasting the block** into `registry.toml` under the project's existing `[[project]]` entry.
2. **Setting `public = true` / `repo_public = true`** for real — this skill only ever *proposes*
   those fields when explicitly told to (see **Constraints**); it never applies them to the file
   either way.

Direct-write-into-the-registry tooling belongs to the plan's Step 28 (authoring all the real
blocks). If that step wants it, it can compose `registry.load_registry` + `registry.upsert_entry`
(both already exist and already handle the atomic-write + round-trip contract) around this script's
validated `Portfolio` object; duplicating that logic here would violate the same one-source-of-truth
rule this script exists to uphold.

## Constraints (do not relax)

- **Never invents stats.** `tests`, `last_commit_days`, `commits_30d`, `gap`, and the plan-derived
  goal are DERIVED by dev-observatory at scan time — this skill never writes a stats-shaped field
  into `[project.portfolio]` (there isn't one; the schema in plan §5a has none).
- **Never sets `public = true`** without an explicit, quoted instruction that the project is
  display-listed — mechanically enforced by `scaffold_portfolio.py --public` requiring
  `--public-reason`.
- **Never promotes `status`** into `showcase`/`highlights` — mechanically dropped by the validator
  regardless of what is passed in.
- **Never invents a `relates` clause** — only pairs traceable to a sentence actually read in Step 3,
  and only slugs that exist in the registry (dead slugs are dropped with a loud reason, mirroring
  `registry._drop_dead_relates`).
- **Never edits project files, `registry.toml`, `snapshot.json`, packages, or installed skills.**
  The only mutation is the host-private transient payload, deleted by the launcher in `finally`.
- **Never inserts drafted text into shell source.** It reaches the child only as decoded structured
  data passed through the Step 5 CRT-compatible argv encoder.

## Reference

- Block schema + parse-time validation: `dev-observatory/src/dev_observatory/registry.py`
  `_parse_portfolio` / `_drop_dead_relates` / `_portfolio_to_table`.
- Verb derivation: `dev-observatory/src/dev_observatory/verbs.py` `derive_verbs`, `is_button_verb`.
- Showcase fallback ladder (render-time; informs what makes a good `showcase` pick):
  `dev-observatory/src/dev_observatory/arc.py` `resolve_showcase_verb`, `resolve_highlights`.
- Dataclass: `dev-observatory/src/dev_observatory/model.py` `Portfolio`.
- Repository history contains a worked baseline against a thin utility (`paper-trail`) and a
  flagship (`void_furnace`), including the validator catching an invalid showcase guess. That
  historical sample is not a delivered package resource; Step 5 governs current invocation.
- Registry facts (`owned`, ports, verb schema) are governed by `descriptor-contract.md`; an
  unregistered project is write-blocked by default.
