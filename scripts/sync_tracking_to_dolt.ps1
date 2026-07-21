param(
    [string]$CommitMessage = "Sync tracking CSVs to Dolt"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Dolt = Join-Path $PSScriptRoot "dolt.ps1"

function Import-TrackingTable {
    param(
        [string]$Table,
        [string]$PrimaryKey,
        [string]$CsvPath
    )

    & $Dolt table import -r --pk=$PrimaryKey $Table $CsvPath
}

Push-Location $Root
try {
    if (-not (Test-Path ".dolt")) {
        & $Dolt init
    }

    Import-TrackingTable "requirements" "requirement_id" "tracking/requirements.csv"
    Import-TrackingTable "tasks" "task_id" "tracking/tasks.csv"
    Import-TrackingTable "judges" "judge_id" "tracking/judges.csv"
    Import-TrackingTable "evidence" "evidence_id" "tracking/evidence.csv"
    Import-TrackingTable "decisions" "decision_id" "tracking/decisions.csv"
    Import-TrackingTable "platform_snapshots" "snapshot_id" "tracking/platform_snapshots.csv"
    Import-TrackingTable "status_log" "log_id" "tracking/status_log.csv"

    & $Dolt add .
    $status = & $Dolt status
    Write-Output $status

    if ($status -match "nothing to commit") {
        Write-Output "Dolt already clean; no commit created."
        exit 0
    }

    & $Dolt commit -m $CommitMessage
    & $Dolt status
}
finally {
    Pop-Location
}
