$ErrorActionPreference = 'Stop'
$siteRoot = $PSScriptRoot
$url = 'http://127.0.0.1:8774'
function Test-Site {
    try { return (Invoke-RestMethod "$url/__local_site" -TimeoutSec 2).site -eq 'axiom-navigator-local' } catch { return $false }
}
try {
    if (-not (Test-Site)) {
        if (Get-NetTCPConnection -LocalPort 8774 -State Listen -ErrorAction SilentlyContinue) { throw 'Port 8774 is occupied by another app. No process was stopped.' }
        if (-not (Test-Path -LiteralPath (Join-Path $siteRoot 'dist\public\index.html'))) { throw 'The built site is missing. Rebuild Axiom Navigator before launching.' }
        $nodePath = (Get-Command node.exe -ErrorAction Stop).Source
        Start-Process -FilePath $nodePath -ArgumentList ('"' + (Join-Path $siteRoot 'local-server.mjs') + '"') -WorkingDirectory $siteRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $siteRoot 'local-server.log') -RedirectStandardError (Join-Path $siteRoot 'local-server-error.log') | Out-Null
        $ready = $false
        for ($attempt=0; $attempt -lt 30; $attempt++) {
            if (Test-Site) { $ready=$true; break }
            Start-Sleep -Milliseconds 300
        }
        if (-not $ready) { throw 'The server did not start. See local-server-error.log in the app folder.' }
    }
    Start-Process $url
} catch {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($_.Exception.Message, 'Axiom Navigator could not start') | Out-Null
    exit 1
}
