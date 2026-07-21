$ErrorActionPreference = "Stop"

$DoltPath = Join-Path $PSScriptRoot "..\.tools\dolt\dolt-windows-amd64\bin\dolt.exe"

if (-not (Test-Path $DoltPath)) {
    Write-Error "Dolt portable binary not found at $DoltPath. Reinstall or download Dolt first."
}

& $DoltPath @args
exit $LASTEXITCODE
