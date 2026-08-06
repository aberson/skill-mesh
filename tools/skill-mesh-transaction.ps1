<#
.SYNOPSIS
    skill-mesh-transaction.ps1 -- the SINGLE shared transaction engine for every
    skill-mesh mutation of a consumer home: a state machine, an append-only
    journal, ordered apply with post-mutation verification, ordered (reverse-seq)
    rollback, and idempotent resume.

.DESCRIPTION
    Dot-sourced (never executed), exactly like tools/skill-mesh-provenance.ps1, by
      - tools/install-skill-mesh.ps1      (clean profile install; no backup set)
      - tools/migrate-legacy-install.ps1  (legacy cutover; external backup set)
    so the ordered-apply / journal / verify machinery has ONE implementation and
    cannot drift between install and migration.

    STATE MACHINE. A transaction's status is one of six values; only the
    transitions below are legal, and Set-SkillMeshTxStatus REFUSES any other:

        prepared          -> applying | rolling_back
        applying          -> applied  | rolling_back
        applied           -> rolling_back
        rolling_back      -> rolled_back | failed_incomplete
        rolled_back       -> (terminal)
        failed_incomplete -> (terminal)

    The cutover plan's section 5 narrative enumerates only the FAILURE path into
    `rolling_back` (from `applying`), because that is the only way an unattended
    apply reaches it. The same section's CLI contract also defines an explicit
    operator-initiated `-Rollback` mode whose documented purpose is to "roll back
    one applied transaction", and an operator must likewise be able to discard a
    `prepared` transaction that never mutated anything. Those two entries are
    therefore legal here and are the ONLY additions to the narrative's set; every
    other pair (`prepared -> applied`, `applied -> applying`, anything out of a
    terminal state) is refused.

    APPEND-ONLY JOURNAL. One record per action attempt is appended to a
    `.jsonl` file: a `begin` record is flushed BEFORE the mutation and a `commit`
    record after the post-hash verifies. A crash between the two therefore always
    leaves the in-flight action on record, which is what makes resume decidable.
    Records are only ever appended -- never rewritten, never truncated -- so the
    journal is a faithful audit trail even for a transaction that crashed.

    ORDERED APPLY / ORDERED ROLLBACK. Actions run in ascending `seq`. Any failure
    (a mutation error, or a post-mutation hash that does not equal the action's
    declared `post_hash`) walks the begun set in strict REVERSE `seq` order and
    applies each action's inverse. A successful undo lands `rolled_back`; a failed
    undo stops immediately and lands `failed_incomplete`, leaving the backup for
    manual recovery.

    IDEMPOTENT RESUME. The caller supplies a `-ShouldSkip` predicate that answers
    "does the post-state already hold on disk?". An action whose post-state holds
    is skipped and a `commit` record is appended for it, so a crash after a
    mutation but before its `commit` flush converges to the same terminal state
    instead of being redone.

    ROLLBACK IS OPT-IN. `Invoke-SkillMeshTxApply -NoRollback` runs the same
    ordered, journaled, verified apply but rethrows on failure WITHOUT undoing.
    install-skill-mesh.ps1 uses that mode on purpose: its published contract on a
    partial copy is a RECONCILED RECOVERY LEDGER (files already written stay, and
    a retry resumes without -Force), not an undo. Silently upgrading the installer
    to rollback would change shipped, test-locked behavior.

    TEST SEAMS. Three environment variables let a test drive the failure paths
    that are otherwise unreachable from outside. They are inert when unset, so
    production behavior is unchanged:
      SKILL_MESH_TX_CRASH_AT=<seq>[:<point>]  hard-exits the process (code 9) at
          <point> in { before-begin, after-begin, after-mutate }; default
          after-begin. This is a true crash: no finally block runs.
      SKILL_MESH_TX_FAIL_AT=<seq>             throws during that action's mutation.
      SKILL_MESH_TX_FAIL_UNDO_AT=<seq>        throws during that action's undo.
    They can only affect a process the caller already started, so they grant no
    capability the caller does not already have.

    ASCII-only, no BOM (PowerShell 5.1 reads a no-BOM .ps1 as ANSI/cp1252).
    No Set-StrictMode here on purpose: dot-sourcing runs in the CALLER's scope and
    must not change the caller's strictness. Every read below is StrictMode-safe.
#>

# -- Schema / vocabulary ------------------------------------------------------

function Get-SkillMeshTxSchemaVersion {
    return 1
}

function Test-SkillMeshTxMember {
    # ORDINAL membership. PowerShell's -contains is CULTURE-aware, so a value
    # padded with Unicode-ignorable characters compares EQUAL to a vocabulary
    # member (the same trap tools/inspect-host-install.ps1 documents for provider
    # slugs). A transaction status is read back from a hand-editable manifest
    # file, so it gets the ordinal treatment too.
    param([string[]]$Vocabulary, [string]$Value)
    if ($null -eq $Vocabulary) { return $false }
    if ([string]::IsNullOrEmpty($Value)) { return $false }
    foreach ($v in $Vocabulary) {
        if ([string]::Equals($v, $Value, [System.StringComparison]::Ordinal)) { return $true }
    }
    return $false
}

# These two are NEVER empty, so they are returned WITHOUT the comma-wrap: a
# comma-wrapped return survives `$x = f` but turns `@(f)` into a one-element array
# holding the array, which silently breaks every enumerating call site.
function Get-SkillMeshTxStates {
    return @('prepared', 'applying', 'applied', 'rolling_back', 'rolled_back', 'failed_incomplete')
}

function Get-SkillMeshTxActionKinds {
    return @('backup', 'install', 'retire', 'preserve', 'ledger')
}

function Get-SkillMeshTxLegalNext {
    # The ONE owner of the legal-transition map (see .DESCRIPTION). Comma-wrapped
    # because the terminal states return an EMPTY array, which would otherwise
    # unroll to $null; call sites must therefore never wrap this in @().
    param([string]$State)
    switch ($State) {
        'prepared' { return , @('applying', 'rolling_back') }
        'applying' { return , @('applied', 'rolling_back') }
        'applied' { return , @('rolling_back') }
        'rolling_back' { return , @('rolled_back', 'failed_incomplete') }
        'rolled_back' { return , @() }
        'failed_incomplete' { return , @() }
    }
    return , @()
}

function Test-SkillMeshTxTransition {
    param([string]$From, [string]$To)
    if (-not (Test-SkillMeshTxMember (Get-SkillMeshTxStates) $From)) { return $false }
    if (-not (Test-SkillMeshTxMember (Get-SkillMeshTxStates) $To)) { return $false }
    return (Test-SkillMeshTxMember (Get-SkillMeshTxLegalNext $From) $To)
}

function Test-SkillMeshTxTerminal {
    param([string]$State)
    return (Test-SkillMeshTxMember @('applied', 'rolled_back') $State)
}

# -- Small helpers ------------------------------------------------------------

function Get-SkillMeshTxField {
    # StrictMode-safe property read: $Default when the property is absent (or the
    # container is null), so a truncated/hand-edited manifest or journal record
    # yields a clean diagnostic path rather than a PropertyNotFoundException.
    param($Object, [string]$Name, $Default = $null)
    if ($null -eq $Object) { return $Default }
    $p = $Object.PSObject.Properties[$Name]
    if ($p) { return $p.Value }
    return $Default
}

function Get-SkillMeshFileSha256 {
    # Lowercase hex SHA-256 of a file, or $null when the path is not a file. A
    # $null hash is the canonical "this path does not exist" marker throughout the
    # engine, so an absent target and an empty file are never confused.
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $fs = [System.IO.File]::OpenRead($Path)
        try {
            $bytes = $sha.ComputeHash($fs)
        } finally {
            $fs.Dispose()
        }
    } finally {
        $sha.Dispose()
    }
    return ([System.BitConverter]::ToString($bytes) -replace '-', '').ToLowerInvariant()
}

function Get-SkillMeshTxUtcNow {
    # RFC 3339 UTC. 'T' and 'Z' are QUOTED: an unquoted literal in a .NET custom
    # format string is not guaranteed to survive.
    return ([DateTime]::UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss'.'fff'Z'",
        [System.Globalization.CultureInfo]::InvariantCulture))
}

function New-SkillMeshMigrationId {
    # yyyyMMddTHHmmssZ-<8 lowercase hex>, from UTC time plus four
    # cryptographically random bytes. Used as a directory leaf, so its charset is
    # deliberately a safe single path segment (see Test-SkillMeshMigrationId).
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMdd'T'HHmmss'Z'",
        [System.Globalization.CultureInfo]::InvariantCulture)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $buf = New-Object byte[] 4
        $rng.GetBytes($buf)
    } finally {
        $rng.Dispose()
    }
    $hex = ([System.BitConverter]::ToString($buf) -replace '-', '').ToLowerInvariant()
    return ($stamp + '-' + $hex)
}

function Test-SkillMeshMigrationId {
    # A migration id arrives from the CLI and is JOINED INTO A PATH, so it is
    # validated as an exact-shape single segment before use -- never merely
    # "contains no separator". Two details are load-bearing:
    #   \A..\z, not ^..$: in .NET '$' also matches BEFORE a trailing newline, so a
    #     newline-terminated value would pass a '$'-anchored gate.
    #   -cmatch, not -match: PowerShell's -match is case-INSENSITIVE, which would
    #     admit a spelling New-SkillMeshMigrationId never mints. The id is the
    #     join key between a directory leaf, a plan, a manifest, and a journal, so
    #     exactly one spelling is accepted (the diagnostic names the required form).
    param([string]$Id)
    if ([string]::IsNullOrWhiteSpace($Id)) { return $false }
    return ($Id -cmatch '\A[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}\z')
}

# -- Append-only journal ------------------------------------------------------

function New-SkillMeshTxJournal {
    # Create (but never truncate) the journal file and its parent directory.
    param([string]$Path)
    $dir = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        [System.IO.File]::WriteAllText($Path, '', (New-Object System.Text.UTF8Encoding($false)))
    }
    return $Path
}

function Add-SkillMeshTxJournalRecord {
    # APPEND one record. Never rewrites or truncates: the journal is the only
    # evidence a crashed transaction leaves behind.
    param(
        $Transaction,
        [int]$Seq,
        [string]$Action,
        [string]$RelPath,
        [string]$Phase,
        $PreHash,
        $PostHash
    )
    $record = [PSCustomObject][ordered]@{
        schema_version = (Get-SkillMeshTxSchemaVersion)
        migration_id   = (Get-SkillMeshTxField $Transaction 'migration_id')
        seq            = $Seq
        action         = $Action
        rel_path       = $RelPath
        phase          = $Phase
        pre_hash       = $PreHash
        post_hash      = $PostHash
        utc            = (Get-SkillMeshTxUtcNow)
    }
    $line = ($record | ConvertTo-Json -Compress -Depth 5)
    $path = (Get-SkillMeshTxField $Transaction 'journal_path')
    [System.IO.File]::AppendAllText($path, ($line + "`n"),
        (New-Object System.Text.UTF8Encoding($false)))
}

function Read-SkillMeshTxJournal {
    # Parse the journal into records. A truncated final line (the signature of a
    # crash mid-append) is DROPPED rather than fatal -- an unparseable record is by
    # definition one that never completed, so treating it as absent is exactly the
    # conservative reading.
    param([string]$Path)
    $out = @()
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return , $out }
    foreach ($line in [System.IO.File]::ReadAllLines($Path, [System.Text.Encoding]::UTF8)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $out += ($line | ConvertFrom-Json)
        } catch {
            continue
        }
    }
    return , $out
}

function Get-SkillMeshTxBegunSeqs {
    # The set of seq values that reached `begin` (committed or not). This is the
    # undo set: anything begun may have mutated the target.
    param($Records)
    $set = New-Object 'System.Collections.Generic.HashSet[int]'
    foreach ($r in @($Records)) {
        if ((Get-SkillMeshTxField $r 'phase') -eq 'begin') {
            [void]$set.Add([int](Get-SkillMeshTxField $r 'seq' -1))
        }
    }
    return , $set
}

# -- Transaction handle -------------------------------------------------------

function New-SkillMeshTransaction {
    <#
      $StatusWriter is invoked with the new status every time it changes, so the
      owner can persist it (the migrator writes BackupManifest.status; the
      installer, which keeps no durable transaction record, passes $null).
    #>
    param(
        [Parameter(Mandatory = $true)][string]$MigrationId,
        [Parameter(Mandatory = $true)][string]$JournalPath,
        [string]$Status = 'prepared',
        [scriptblock]$StatusWriter = $null
    )
    if (-not (Test-SkillMeshTxMember (Get-SkillMeshTxStates) $Status)) {
        throw "skill-mesh-transaction: unknown initial status '$Status'."
    }
    New-SkillMeshTxJournal $JournalPath | Out-Null
    return [PSCustomObject]@{
        migration_id  = $MigrationId
        journal_path  = $JournalPath
        status        = $Status
        status_writer = $StatusWriter
    }
}

function Set-SkillMeshTxStatus {
    # The ONLY way a transaction's status changes. An illegal transition throws
    # BEFORE the status is mutated and BEFORE the writer runs, so a refused
    # transition can never be persisted.
    param($Transaction, [string]$Status)
    $from = [string](Get-SkillMeshTxField $Transaction 'status')
    if ($from -eq $Status) { return }
    if (-not (Test-SkillMeshTxTransition $from $Status)) {
        throw ("skill-mesh-transaction: ILLEGAL state transition '$from' -> '$Status'. " +
               "Legal from '$from': [" + ((Get-SkillMeshTxLegalNext $from) -join ', ') + '].')
    }
    $Transaction.status = $Status
    $writer = Get-SkillMeshTxField $Transaction 'status_writer'
    if ($null -ne $writer) { & $writer $Status }
}

# -- Test seams (inert unless the environment variable is set) ----------------

function Get-SkillMeshTxSeamValue {
    param([string]$Name)
    $v = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($v)) { return $null }
    return $v.Trim()
}

function Test-SkillMeshTxSeamSeq {
    param([string]$Name, [int]$Seq)
    $v = Get-SkillMeshTxSeamValue $Name
    if ($null -eq $v) { return $false }
    $n = 0
    if (-not [int]::TryParse($v, [ref]$n)) { return $false }
    return ($n -eq $Seq)
}

function Invoke-SkillMeshTxCrashPoint {
    # Hard process exit: no finally block runs, so this models a real crash (a
    # killed process, a power loss) rather than a catchable error.
    param([int]$Seq, [string]$Point)
    $v = Get-SkillMeshTxSeamValue 'SKILL_MESH_TX_CRASH_AT'
    if ($null -eq $v) { return }
    $parts = $v.Split(':')
    $n = 0
    if (-not [int]::TryParse($parts[0], [ref]$n)) { return }
    if ($n -ne $Seq) { return }
    $wanted = 'after-begin'
    if ($parts.Count -gt 1 -and -not [string]::IsNullOrWhiteSpace($parts[1])) {
        $wanted = $parts[1].Trim()
    }
    if ($wanted -ne $Point) { return }
    [Console]::Error.WriteLine(
        "skill-mesh-transaction: TEST SEAM -- simulated crash at seq $Seq ($Point).")
    [Environment]::Exit(9)
}

# -- Ordered rollback ---------------------------------------------------------

function Invoke-SkillMeshTxRollback {
    <#
      Undo $Actions (which MUST already be the begun set, in ascending apply
      order) in strict REVERSE order. Returns $null when every inverse succeeded
      (status -> rolled_back), or the failing ErrorRecord (status ->
      failed_incomplete, backup retained for manual recovery).
    #>
    param(
        $Transaction,
        [object[]]$Actions = @(),
        [Parameter(Mandatory = $true)][scriptblock]$Undo
    )
    Set-SkillMeshTxStatus $Transaction 'rolling_back'
    $failure = $null
    for ($i = @($Actions).Count - 1; $i -ge 0; $i--) {
        $action = @($Actions)[$i]
        $seq = [int](Get-SkillMeshTxField $action 'seq' -1)
        try {
            if (Test-SkillMeshTxSeamSeq 'SKILL_MESH_TX_FAIL_UNDO_AT' $seq) {
                throw "skill-mesh-transaction: TEST SEAM -- injected undo failure at seq $seq."
            }
            & $Undo $action
        } catch {
            $failure = $_
            break
        }
    }
    if ($null -eq $failure) {
        Set-SkillMeshTxStatus $Transaction 'rolled_back'
        return $null
    }
    Set-SkillMeshTxStatus $Transaction 'failed_incomplete'
    return $failure
}

# -- Ordered apply ------------------------------------------------------------

function Invoke-SkillMeshTxApply {
    <#
      Run $Actions in ascending seq with a journal record before and after each
      mutation, verifying each action's post-state hash.

      Scriptblock contract (each is called with the action object as $args[0]):
        -GetPreHash   returns the target's current hash (or $null when absent)
        -Mutate       performs the mutation
        -GetPostHash  returns the target's hash after the mutation
        -Undo         reverses one action (required unless -NoRollback)
        -ShouldSkip   optional; $true when the post-state ALREADY holds on disk
                      (resume). A skipped action still gets a `commit` record, so
                      a crash between a mutation and its commit converges.

      Throws the original error on failure; the caller reads $Transaction.status
      to distinguish rolled_back (recoverable) from failed_incomplete (mixed).
    #>
    param(
        $Transaction,
        [object[]]$Actions = @(),
        [Parameter(Mandatory = $true)][scriptblock]$GetPreHash,
        [Parameter(Mandatory = $true)][scriptblock]$Mutate,
        [Parameter(Mandatory = $true)][scriptblock]$GetPostHash,
        [scriptblock]$Undo = $null,
        [scriptblock]$ShouldSkip = $null,
        [switch]$NoRollback
    )
    if (-not $NoRollback -and $null -eq $Undo) {
        throw "skill-mesh-transaction: -Undo is required unless -NoRollback is passed."
    }

    $from = [string](Get-SkillMeshTxField $Transaction 'status')
    if ($from -ne 'applying') {
        # prepared -> applying is the only legal entry; anything else (a terminal
        # or rolling-back transaction) is refused by Set-SkillMeshTxStatus.
        Set-SkillMeshTxStatus $Transaction 'applying'
    }

    # Every action that may have touched a target -- the undo set. A resume-skipped
    # action belongs here too: it IS applied, so a later failure must undo it.
    $begun = New-Object System.Collections.Generic.List[object]

    try {
        foreach ($action in @($Actions)) {
            $seq = [int](Get-SkillMeshTxField $action 'seq' -1)
            $kind = [string](Get-SkillMeshTxField $action 'action')
            $rel = [string](Get-SkillMeshTxField $action 'rel_path')
            $expected = Get-SkillMeshTxField $action 'post_hash'

            if ($null -ne $ShouldSkip -and (& $ShouldSkip $action)) {
                $begun.Add($action)
                Add-SkillMeshTxJournalRecord $Transaction $seq $kind $rel 'commit' `
                    (& $GetPreHash $action) (& $GetPostHash $action)
                continue
            }

            Invoke-SkillMeshTxCrashPoint $seq 'before-begin'
            $pre = & $GetPreHash $action
            Add-SkillMeshTxJournalRecord $Transaction $seq $kind $rel 'begin' $pre $null
            # Recorded as begun the instant the `begin` record is durable: from
            # here on the action may have mutated its target.
            $begun.Add($action)
            Invoke-SkillMeshTxCrashPoint $seq 'after-begin'

            if (Test-SkillMeshTxSeamSeq 'SKILL_MESH_TX_FAIL_AT' $seq) {
                throw "skill-mesh-transaction: TEST SEAM -- injected failure at seq $seq ($kind $rel)."
            }
            & $Mutate $action

            Invoke-SkillMeshTxCrashPoint $seq 'after-mutate'
            $post = & $GetPostHash $action
            # [string] coercion so an absent target ($null) compares cleanly with a
            # declared-absent post_hash ($null) -- '' -eq ''.
            if ([string]$post -ne [string]$expected) {
                throw ("skill-mesh-transaction: post-mutation verification FAILED for " +
                       "seq $seq ($kind '$rel'): expected hash '" + [string]$expected +
                       "' but found '" + [string]$post + "'.")
            }
            Add-SkillMeshTxJournalRecord $Transaction $seq $kind $rel 'commit' $pre $post
        }
    } catch {
        $applyError = $_
        if ($NoRollback) {
            # Deliberate: the caller owns recovery (see .DESCRIPTION). The status
            # stays `applying`, which is the truthful record of a partial apply.
            throw
        }
        $undoFailure = Invoke-SkillMeshTxRollback $Transaction @($begun.ToArray()) $Undo
        if ($null -ne $undoFailure) {
            [Console]::Error.WriteLine(
                "skill-mesh-transaction: ROLLBACK FAILED -- $($undoFailure.Exception.Message)")
        }
        throw $applyError
    }

    Set-SkillMeshTxStatus $Transaction 'applied'
}
