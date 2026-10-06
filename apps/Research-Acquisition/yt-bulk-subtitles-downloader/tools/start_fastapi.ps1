$ErrorActionPreference = "Stop"

# Always use the authoritative D-drive installation — one server, one database.
$Root   = "D:\DONT TOUCH BOOT UP\AHK"
$Server = Join-Path $Root "sync_server.py"
$LogDir = Join-Path $Root "logs"
$LogFile = Join-Path $LogDir "fastapi.log"
$ErrFile = Join-Path $LogDir "fastapi.err.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path $Server)) {
    throw "Missing FastAPI server: $Server"
}

$listening = Get-NetTCPConnection -LocalPort 3456 -State Listen -ErrorAction SilentlyContinue
if ($listening) {
    Write-Host "FastAPI already listening on port 3456."
    return
}

$python = (Get-Command py -ErrorAction SilentlyContinue)
if ($python) {
    $exe = "py"
    $args = '-3 "' + $Server + '"'
} else {
    $python = Get-Command python -ErrorAction Stop
    $exe = $python.Source
    $args = '"' + $Server + '"'
}

Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $LogFile -RedirectStandardError $ErrFile
Start-Sleep -Seconds 2

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:3456/health" -TimeoutSec 3
    Write-Host "FastAPI started: http://127.0.0.1:3456/health"
    $health | ConvertTo-Json -Compress
} catch {
    Write-Warning "FastAPI start was requested, but health check did not respond. See $LogFile and $ErrFile"
}
