# Bake configs\probe.build.env into hope-probe.exe
# Runtime: flag > env > baked file

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$src = Join-Path $PSScriptRoot "configs\probe.build.env"
$dst = Join-Path $PSScriptRoot "internal\config\probe.build.env"
if (-not (Test-Path $src)) { throw "Missing $src" }

Copy-Item -Path $src -Destination $dst -Force
Write-Host "synced build env"

$map = @{}
foreach ($raw in Get-Content -Path $src) {
    $line = $raw.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) { continue }
    $i = $line.IndexOf("=")
    if ($i -lt 1) { continue }
    $map[$line.Substring(0, $i).Trim()] = $line.Substring($i + 1).Trim().Trim('"').Trim("'")
}

$url = ""
$outDir = ""
$tz = ""
$idle = ""
if ($map.ContainsKey("HOPE_INGEST_URL")) { $url = [string]$map["HOPE_INGEST_URL"] }
if ($map.ContainsKey("HOPE_OUT_DIR")) { $outDir = [string]$map["HOPE_OUT_DIR"] }
if ($map.ContainsKey("HOPE_TZ")) { $tz = [string]$map["HOPE_TZ"] }
if ($map.ContainsKey("HOPE_IDLE_SECONDS")) { $idle = [string]$map["HOPE_IDLE_SECONDS"] }

if ([string]::IsNullOrWhiteSpace($url)) {
    Write-Warning "HOPE_INGEST_URL empty"
} else {
    Write-Host "ingest=$url"
}

$pkg = "github.com/haowu0802/hope-metrics-platform/probe/internal/config"
$ldflags = "-X ${pkg}.buildIngestURL=$url -X ${pkg}.buildOutDir=$outDir -X ${pkg}.buildTimezone=$tz -X ${pkg}.buildIdleSec=$idle"

go build -ldflags $ldflags -o hope-probe.exe ./cmd/hope-probe
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "ok hope-probe.exe"