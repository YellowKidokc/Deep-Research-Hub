$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$StartupRoot = "\\192.168.2.50\h_hp\Desktop\Startup\Startup\ai-hub-v2"

$pairs = @(
    @{ Source = Join-Path $Root "sync_server.py"; Destination = Join-Path $StartupRoot "sync_server.py" },
    @{ Source = Join-Path $Root "clipsync-bridge\clipsync_bridge.ahk"; Destination = Join-Path $StartupRoot "clipsync-bridge\clipsync_bridge.ahk" },
    @{ Source = Join-Path $Root "config\bridge.ini"; Destination = Join-Path $StartupRoot "config\bridge.ini" }
)

foreach ($pair in $pairs) {
    if (-not (Test-Path $pair.Source)) {
        throw "Missing source: $($pair.Source)"
    }
    $destDir = Split-Path -Parent $pair.Destination
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    Copy-Item -Force -Path $pair.Source -Destination $pair.Destination
    Write-Host "Copied $($pair.Source) -> $($pair.Destination)"
}

