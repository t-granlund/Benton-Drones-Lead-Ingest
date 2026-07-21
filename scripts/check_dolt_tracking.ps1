$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Dolt = Join-Path $PSScriptRoot "dolt.ps1"

$Tables = @(
    @{ Name = "requirements"; Csv = "tracking/requirements.csv"; PrimaryKey = "requirement_id" },
    @{ Name = "tasks"; Csv = "tracking/tasks.csv"; PrimaryKey = "task_id" },
    @{ Name = "judges"; Csv = "tracking/judges.csv"; PrimaryKey = "judge_id" },
    @{ Name = "evidence"; Csv = "tracking/evidence.csv"; PrimaryKey = "evidence_id" },
    @{ Name = "decisions"; Csv = "tracking/decisions.csv"; PrimaryKey = "decision_id" },
    @{ Name = "platform_snapshots"; Csv = "tracking/platform_snapshots.csv"; PrimaryKey = "snapshot_id" },
    @{ Name = "status_log"; Csv = "tracking/status_log.csv"; PrimaryKey = "log_id" }
)

Push-Location $Root
try {
    if (-not (Test-Path ".dolt")) {
        Write-Error "No .dolt database found. Run scripts/sync_tracking_to_dolt.ps1 first."
    }

    $status = & $Dolt status
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Output $status

    $ls = & $Dolt ls
    foreach ($table in $Tables) {
        if (-not ($ls -match "\b$($table.Name)\b")) {
            Write-Error "Missing Dolt table: $($table.Name)"
        }

        $csvRows = @(Import-Csv $table.Csv)
        $sql = "select count(*) as row_count from $($table.Name);"
        $countResult = (& $Dolt sql -r csv -q $sql | ConvertFrom-Csv)
        $doltRows = [int]$countResult.row_count

        if ($csvRows.Count -ne $doltRows) {
            Write-Error "Row count drift for $($table.Name): CSV=$($csvRows.Count), Dolt=$doltRows"
        }

        $missingPk = $csvRows | Where-Object { -not $_.$($table.PrimaryKey) }
        if ($missingPk) {
            Write-Error "Missing primary key values in $($table.Csv)"
        }

        Write-Output "[PASS] $($table.Name): $doltRows rows match CSV"
    }

    if (-not ($status -match "nothing to commit")) {
        Write-Error "Dolt working tree is not clean. Commit or revert changes."
    }

    Write-Output "[PASS] Dolt tracking check complete"
}
finally {
    Pop-Location
}
