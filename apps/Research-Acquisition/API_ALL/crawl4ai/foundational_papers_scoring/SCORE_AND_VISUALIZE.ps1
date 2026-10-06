# ==============================================================================
# THEOPHYSICS COHERENCE FRAMEWORK
# One-Click Scoring & Visualization Automation
# ==============================================================================

param(
    [switch]$SkipScoring,  # Skip scoring if you already have recent data
    [switch]$OpenDashboard = $true
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=" -ForegroundColor Yellow -NoNewline
Write-Host ("="*79) -ForegroundColor Yellow
Write-Host "THEOPHYSICS COHERENCE FRAMEWORK" -ForegroundColor Yellow
Write-Host "Automated Scoring & Visualization Pipeline" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Yellow -NoNewline
Write-Host ("="*79) -ForegroundColor Yellow
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScoringScript = Join-Path $ScriptDir "score_all_canonical.py"
$DashboardScript = Join-Path $ScriptDir "create_dashboard.py"
$OutputDir = Join-Path $ScriptDir "outputs\dashboard"
$DashboardHTML = Join-Path $OutputDir "coherence_dashboard.html"

# Step 1: Run Comprehensive Scoring
if (-not $SkipScoring) {
    Write-Host "[STEP 1/3] " -NoNewline -ForegroundColor Yellow
    Write-Host "Running Comprehensive Document Scoring..." -ForegroundColor White
    Write-Host "  - Theophysics Foundational Papers" -ForegroundColor Cyan
    Write-Host "  - US Founding Documents" -ForegroundColor Cyan
    Write-Host "  - Scientific Theories (118 documents)" -ForegroundColor Cyan
    Write-Host "  - World Religions Sacred Texts" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        python $ScoringScript
        if ($LASTEXITCODE -ne 0) {
            throw "Scoring script failed with exit code $LASTEXITCODE"
        }
        Write-Host ""
        Write-Host "[OK] Scoring Complete!" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Scoring failed: $_" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "[STEP 1/3] " -NoNewline -ForegroundColor Yellow
    Write-Host "Skipping scoring (using existing data)" -ForegroundColor Gray
}

Write-Host ""

# Step 2: Generate Interactive Dashboard
Write-Host "[STEP 2/3] " -NoNewline -ForegroundColor Yellow
Write-Host "Generating Interactive HTML Dashboard..." -ForegroundColor White
Write-Host "  - Category comparison charts" -ForegroundColor Cyan
Write-Host "  - Top 20 documents ranking" -ForegroundColor Cyan
Write-Host "  - 12 Fruits radar analysis" -ForegroundColor Cyan
Write-Host "  - Grade distribution" -ForegroundColor Cyan
Write-Host "  - Enhanced Excel workbook" -ForegroundColor Cyan
Write-Host ""

try {
    python $DashboardScript 2>&1 | Out-Null  # Suppress Unicode errors
    if (-not (Test-Path $DashboardHTML)) {
        throw "Dashboard file was not created"
    }
    Write-Host ""
    Write-Host "[OK] Dashboard Generated!" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Dashboard generation failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Open Dashboard in Browser
if ($OpenDashboard) {
    Write-Host "[STEP 3/3] " -NoNewline -ForegroundColor Yellow
    Write-Host "Opening Dashboard in Browser..." -ForegroundColor White
    
    Start-Process $DashboardHTML
    
    Write-Host "[OK] Dashboard Opened!" -ForegroundColor Green
}
else {
    Write-Host "[STEP 3/3] " -NoNewline -ForegroundColor Yellow
    Write-Host "Dashboard ready (not auto-opening)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=" -ForegroundColor Yellow -NoNewline
Write-Host ("="*79) -ForegroundColor Yellow
Write-Host "PIPELINE COMPLETE!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Yellow -NoNewline
Write-Host ("="*79) -ForegroundColor Yellow
Write-Host ""
Write-Host "Output Files:" -ForegroundColor White
Write-Host "  HTML Dashboard: " -NoNewline -ForegroundColor Cyan
Write-Host $DashboardHTML -ForegroundColor White
Write-Host "  Excel Workbook: " -NoNewline -ForegroundColor Cyan
Write-Host (Join-Path $OutputDir "coherence_analysis_with_charts.xlsx") -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review the interactive charts in your browser" -ForegroundColor White
Write-Host "  2. Open the Excel file for detailed analysis" -ForegroundColor White
Write-Host "  3. Share findings with collaborators" -ForegroundColor White
Write-Host ""
Write-Host "To re-run scoring: " -NoNewline -ForegroundColor Cyan
Write-Host ".\SCORE_AND_VISUALIZE.ps1" -ForegroundColor White
Write-Host "To regenerate dashboard only: " -NoNewline -ForegroundColor Cyan
Write-Host ".\SCORE_AND_VISUALIZE.ps1 -SkipScoring" -ForegroundColor White
Write-Host ""
