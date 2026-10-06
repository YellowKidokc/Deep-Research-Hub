$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Checks = New-Object System.Collections.Generic.List[object]

function Add-Check($Name, $Ok, $Detail) {
    $Checks.Add([pscustomobject]@{
        Check = $Name
        OK = [bool]$Ok
        Detail = $Detail
    })
}

$server = Join-Path $Root "sync_server.py"
$bridge = Join-Path $Root "clipsync-bridge\clipsync_bridge.ahk"
$hub = Join-Path $Root "AI-HUB.ahk"
$config = Join-Path $Root "config\bridge.ini"
$logs = Join-Path $Root "logs"

Add-Check "FastAPI file" (Test-Path $server) $server
Add-Check "AHK bridge file" (Test-Path $bridge) $bridge
Add-Check "AI-HUB entry" (Test-Path $hub) $hub
Add-Check "Bridge config" (Test-Path $config) $config
Add-Check "Log directory" (Test-Path $logs) $logs

$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
}
Add-Check "Python command" ($null -ne $python) ($(if ($python) { $python.Source } else { "py/python not found on PATH" }))

$ahk = Get-Command AutoHotkey64,AutoHotkey,ahk -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $ahk) {
    $knownAhk = @(
        "C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
        "C:\Program Files\AutoHotkey\v2\AutoHotkey.exe",
        "C:\Program Files (x86)\AutoHotkey\v2\AutoHotkey64.exe",
        "C:\Program Files (x86)\AutoHotkey\v2\AutoHotkey.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
}
Add-Check "AutoHotkey command" (($null -ne $ahk) -or ($null -ne $knownAhk)) ($(if ($ahk) { $ahk.Source } elseif ($knownAhk) { $knownAhk } else { "AutoHotkey not found" }))

$listening = Get-NetTCPConnection -LocalPort 3456 -State Listen -ErrorAction SilentlyContinue
Add-Check "Port 3456 listening" ($null -ne $listening) ($(if ($listening) { "PID " + (($listening | Select-Object -First 1).OwningProcess) } else { "No listener" }))

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:3456/health" -TimeoutSec 3
    Add-Check "FastAPI health" $true ($health | ConvertTo-Json -Compress)
} catch {
    Add-Check "FastAPI health" $false $_.Exception.Message
}

$Checks | Format-Table -AutoSize

if (($Checks | Where-Object { -not $_.OK }).Count -gt 0) {
    exit 1
}
