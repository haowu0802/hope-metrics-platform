# Deploy hope-metrics (single machine).
# Requires: flyctl logged in, DATABASE_URL already set as a secret.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

fly deploy --ha=false --wait-timeout 15m
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

fly scale count 1 -y
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "ok https://hope-metrics.fly.dev/"
