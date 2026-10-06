$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

# Same credential contract as the downloader's RUN_WITH_WEBSHARE.ps1: the
# values live in the Windows user environment, never in this repository.
foreach ($name in @('WEBSHARE_USER', 'WEBSHARE_PASS')) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name, 'Process'))) {
        [Environment]::SetEnvironmentVariable($name, [Environment]::GetEnvironmentVariable($name, 'User'), 'Process')
    }
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name, 'Process'))) {
        throw "Missing $name. Run SET_WEBSHARE_CREDENTIALS.bat in yt-transcript-downloader first."
    }
}

# Webshare's rotating residential endpoint. The -rotate suffix is what the
# transcript library appends internally; yt-dlp needs it spelled out.
$user = [Environment]::GetEnvironmentVariable('WEBSHARE_USER', 'Process').Trim()
$pass = [Environment]::GetEnvironmentVariable('WEBSHARE_PASS', 'Process').Trim()
if ($user -notmatch '-rotate$') { $user = "$user-rotate" }
$proxy = "http://{0}:{1}@p.webshare.io:80" -f $user, $pass

# If yt-dlp gets blocked anyway, hand acquisition off to the downloader's
# ytgrab.py, which grinds through rotating Webshare passes. The research
# pipeline then continues here as normal.
$env:YTGRAB_FALLBACK = '1'
$downloader = Join-Path (Split-Path $PSScriptRoot -Parent) 'yt-transcript-downloader'
if (Test-Path (Join-Path $downloader 'ytgrab.py')) {
    $env:YTGRAB_PATH = Join-Path $downloader 'ytgrab.py'
    $env:YTGRAB_PYTHON = Join-Path $downloader 'venv\Scripts\python.exe'
}

Write-Host ''
Write-Host 'YouTube Research Tool - routed through your saved Webshare proxy.' -ForegroundColor Cyan
Write-Host ("Proxy: http://{0}:****@p.webshare.io:80" -f $user) -ForegroundColor DarkGray
Write-Host 'Fallback: ytgrab.py (downloader) if yt-dlp comes back empty.' -ForegroundColor DarkGray
Write-Host ''
Write-Host '  1. Transcript (clean, timestamps)'
Write-Host '  2. Light research'
Write-Host '  3. Deep research'
Write-Host '  4. Debate map (find both sides, steelman each) - needs Ollama'
Write-Host '  5. Custom command (type the whole yt_scrape.py command line)'
Write-Host ''

$choice = Read-Host 'Choose an option [1]'
if ([string]::IsNullOrWhiteSpace($choice)) { $choice = '1' }

$launcher = Join-Path $PSScriptRoot 'youtube-research-tool.bat'

if ($choice -eq '5') {
    $line = Read-Host 'Command (without yt_scrape.py, without --proxy)'
    if ([string]::IsNullOrWhiteSpace($line)) { exit 1 }
    $argv = @($line -split '\s+') + @('--proxy', $proxy)
} else {
    $url = Read-Host 'Paste a video, playlist, or channel URL'
    if ([string]::IsNullOrWhiteSpace($url)) { exit 1 }
    switch ($choice) {
        '2' { $argv = @('research', $url, '--proxy', $proxy) }
        '3' { $argv = @('deep-research', $url, '--proxy', $proxy) }
        '4' { $argv = @('debate', $url, '--proxy', $proxy) }
        default { $argv = @('transcript', $url, '--clean', '--timestamps', '--proxy', $proxy) }
    }
}

& $launcher @argv
exit $LASTEXITCODE
