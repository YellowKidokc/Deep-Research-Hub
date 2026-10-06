param(
    [Parameter(Mandatory = $false)]
    [string]$GroupFile,
    [switch]$StatusOnly
)

$ErrorActionPreference = 'Stop'
$ServerUrl = 'http://192.168.1.177:4433'
$HisterExe = 'C:\Users\David\Tools\Hister\hister.exe'
$QueueRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogRoot = Join-Path $QueueRoot 'logs'

if (-not (Test-Path -LiteralPath $HisterExe -PathType Leaf)) {
    throw "Hister was not found at $HisterExe"
}

New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null

function Get-IndexedCount {
    $lines = & $HisterExe --server-url $ServerUrl list-urls 2>$null
    if ($LASTEXITCODE -ne 0) { return 'unavailable' }
    return @($lines | Where-Object { $_.Trim() }).Count
}

function Show-HisterStatus {
    Write-Host "Hister server: $ServerUrl"
    Write-Host "Indexed documents reported by CLI: $(Get-IndexedCount)"
    Write-Host ''
    Write-Host 'Persistent website crawl jobs:'
    & $HisterExe --server-url $ServerUrl crawl list
}

if ($StatusOnly) {
    Show-HisterStatus
    exit $LASTEXITCODE
}

if (-not $GroupFile) {
    throw 'A group file is required. Launch GROUP_1_DESKTOP_PAGES.bat or GROUP_2_THEOPHYSICS.bat.'
}

$GroupPath = if ([IO.Path]::IsPathRooted($GroupFile)) {
    $GroupFile
} else {
    Join-Path $QueueRoot $GroupFile
}

if (-not (Test-Path -LiteralPath $GroupPath -PathType Leaf)) {
    throw "Folder group file was not found: $GroupPath"
}

$Folders = Get-Content -LiteralPath $GroupPath -Encoding UTF8 |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ -and -not $_.StartsWith('#') } |
    Select-Object -Unique

if (-not $Folders) {
    throw "No folders are enabled in $GroupPath. Add one full folder path per line."
}

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$GroupName = [IO.Path]::GetFileNameWithoutExtension($GroupPath)
$LogPath = Join-Path $LogRoot "${GroupName}_${Stamp}.log"
$ReceiptPath = Join-Path $LogRoot "${GroupName}_${Stamp}_receipt.csv"
$Results = [Collections.Generic.List[object]]::new()

Start-Transcript -LiteralPath $LogPath -Force | Out-Null
try {
    Write-Host "Hister folder queue: $GroupName"
    Write-Host "Server: $ServerUrl"
    Write-Host "Folders queued: $($Folders.Count)"
    Write-Host 'Mode: sequential, recursive, skip existing, 25 documents per request'
    Write-Host ''
    $Before = Get-IndexedCount
    Write-Host "Indexed before: $Before"

    foreach ($Folder in $Folders) {
        $Started = Get-Date
        if (-not (Test-Path -LiteralPath $Folder -PathType Container)) {
            Write-Warning "Missing folder; skipped: $Folder"
            $Results.Add([pscustomobject]@{
                folder = $Folder; status = 'missing'; exit_code = ''; started = $Started
                finished = Get-Date; log = $LogPath
            })
            continue
        }

        Write-Host ''
        Write-Host "Importing: $Folder"
        & $HisterExe --server-url $ServerUrl --client-timeout 0 import file `
            --skip-existing --batch-size 25 --source "folder-$GroupName" --label $GroupName -- $Folder
        $Code = $LASTEXITCODE
        $Status = if ($Code -eq 0) { 'completed' } else { 'failed' }
        $Results.Add([pscustomobject]@{
            folder = $Folder; status = $Status; exit_code = $Code; started = $Started
            finished = Get-Date; log = $LogPath
        })
    }

    $After = Get-IndexedCount
    Write-Host ''
    Write-Host "Indexed after: $After"
    Write-Host "Receipt: $ReceiptPath"
    $Results | Export-Csv -LiteralPath $ReceiptPath -NoTypeInformation -Encoding UTF8
}
finally {
    Stop-Transcript | Out-Null
}

if ($Results.Where({ $_.status -eq 'failed' }).Count -gt 0) { exit 1 }
exit 0
