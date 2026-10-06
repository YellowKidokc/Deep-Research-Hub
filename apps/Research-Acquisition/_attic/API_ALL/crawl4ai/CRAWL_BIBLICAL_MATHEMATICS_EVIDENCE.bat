@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Biblical Mathematics & Theophysics - Continuous Evidence Crawler
:: Fully portable: Location-independent, auto-detects paths, resumable state
:: ============================================================================

title Theophysics Evidence Crawler - Biblical Mathematics
color 0e

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT="

:: ----------------------------------------------------------------------------
:: 1. DYNAMIC REPOSITORY & LOCATION DISCOVERY
:: ----------------------------------------------------------------------------
if exist "%SCRIPT_DIR%theophysics_evidence_crawler.py" (
    set "PROJECT_ROOT=%SCRIPT_DIR%"
    goto :find_python
)
if exist "%SCRIPT_DIR%..\theophysics_evidence_crawler.py" (
    pushd "%SCRIPT_DIR%.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :find_python
)
if exist "%SCRIPT_DIR%..\..\theophysics_evidence_crawler.py" (
    pushd "%SCRIPT_DIR%..\.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :find_python
)
if exist "%SCRIPT_DIR%.crawl4ai_root.cfg" (
    set /p SAVED_LOC=<"%SCRIPT_DIR%.crawl4ai_root.cfg"
    if exist "!SAVED_LOC!\theophysics_evidence_crawler.py" (
        set "PROJECT_ROOT=!SAVED_LOC!"
        if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
        goto :find_python
    )
)
if defined CRAWL4AI_DIR (
    if exist "%CRAWL4AI_DIR%\theophysics_evidence_crawler.py" (
        set "PROJECT_ROOT=%CRAWL4AI_DIR%\"
        goto :find_python
    )
)
if exist "D:\GitHub\Research-Acquisition\crawl4ai\theophysics_evidence_crawler.py" (
    set "PROJECT_ROOT=D:\GitHub\Research-Acquisition\crawl4ai\"
    goto :find_python
)

echo [!] Could not locate the research crawler directory automatically.
set /p USER_PATH="Enter or drag-and-drop crawl4ai folder here: "
set "USER_PATH=!USER_PATH:"=!"
if exist "!USER_PATH!\theophysics_evidence_crawler.py" (
    set "PROJECT_ROOT=!USER_PATH!"
    if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
    echo !PROJECT_ROOT!> "%SCRIPT_DIR%.crawl4ai_root.cfg"
    goto :find_python
)

echo [ERROR] Invalid directory. 'theophysics_evidence_crawler.py' not found.
pause
exit /b 1

:: ----------------------------------------------------------------------------
:: 2. PYTHON & VENV DETECTION
:: ----------------------------------------------------------------------------
:find_python
cd /d "%PROJECT_ROOT%"
set "PYTHON_CMD="

if exist "%PROJECT_ROOT%venv\Scripts\python.exe" (
    "%PROJECT_ROOT%venv\Scripts\python.exe" -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=%PROJECT_ROOT%venv\Scripts\python.exe"
        goto :menu
    )
)

:: Base Python fallback
py -3.12 -c "import sys" >nul 2>&1 && set "BASE_PYTHON=py -3.12"
if not defined BASE_PYTHON py -3.11 -c "import sys" >nul 2>&1 && set "BASE_PYTHON=py -3.11"
if not defined BASE_PYTHON py -3 -c "import sys" >nul 2>&1 && set "BASE_PYTHON=py -3"
if not defined BASE_PYTHON python -c "import sys" >nul 2>&1 && set "BASE_PYTHON=python"

if defined BASE_PYTHON (
    set "PYTHON_CMD=!BASE_PYTHON!"
) else (
    echo [ERROR] Python 3.10+ was not found on your system.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------------------
:: MAIN MENU
:: ----------------------------------------------------------------------------
:menu
cls
echo ============================================================================
echo      THEOPHYSICS EVIDENCE ENGINE: BIBLICAL MATHEMATICS ^& EQUATIONS
echo ============================================================================
echo Root Directory : %PROJECT_ROOT%
echo Python Runtime : %PYTHON_CMD%
echo ============================================================================
echo.
echo Select an action:
echo.
echo   1. [Continuous Crawl] Start / Resume Evidence Mining (Can run for days)
echo   2. [Targeted Query]   Search specific topic, thinker, or mathematical equation
echo   3. [Dashboard]        View Real-Time Evidence Statistics ^& Receipts
echo   4. [Export]           Generate Top 100 Evidence Report ^& Master CSV
echo   5. [Open Vault]       Open Theophysics Vault Evidence Matrix Folder
echo   6. Exit
echo.
set /p choice="Enter choice (1-6): "

if "%choice%"=="1" goto :start_continuous
if "%choice%"=="2" goto :start_targeted
if "%choice%"=="3" goto :view_stats
if "%choice%"=="4" goto :export_reports
if "%choice%"=="5" goto :open_vault
if "%choice%"=="6" exit /b 0

echo Invalid choice.
timeout /t 2 >nul
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 1: CONTINUOUS CRAWL
:: ----------------------------------------------------------------------------
:start_continuous
cls
echo ============================================================================
echo               CONTINUOUS RESEARCH CRAWLER RUNNING
echo ============================================================================
echo Searching academic repositories (OpenAlex, arXiv, Crossref) and the web...
echo State is saved in SQLite after every page.
echo Press Ctrl+C at any time to pause. You can resume whenever you want.
echo ============================================================================
echo.
"%PYTHON_CMD%" theophysics_evidence_crawler.py
echo.
echo [i] Crawl stopped. State is preserved.
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 2: TARGETED QUERY
:: ----------------------------------------------------------------------------
:start_targeted
echo.
echo ============================================================================
echo                    TARGETED EVIDENCE DISCOVERY
echo ============================================================================
echo Examples:
echo   - Euler's identity God Christian faith
echo   - Gödel ontological proof modal logic formalized
echo   - Resurrection Jesus Bayesian probability Swinburne
echo   - Cantor transfinite numbers absolute infinite theology
echo   - Fine tuning cosmological constant anthropic equation
echo.
set /p target_q="Enter search query: "
if "%target_q%"=="" goto :menu

echo.
echo Searching and crawling candidates for: "%target_q%"...
"%PYTHON_CMD%" theophysics_evidence_crawler.py --query "%target_q%"
echo.
echo Targeted search completed.
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 3: DASHBOARD & STATS
:: ----------------------------------------------------------------------------
:view_stats
cls
echo ============================================================================
echo                     EVIDENCE ENGINE STATISTICS
echo ============================================================================
echo.
"%PYTHON_CMD%" theophysics_evidence_crawler.py --stats
echo.
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 4: EXPORT REPORTS
:: ----------------------------------------------------------------------------
:export_reports
echo.
echo Exporting Top 100 Evidence Report and CSV Index...
"%PYTHON_CMD%" theophysics_evidence_crawler.py --export
echo.
echo Files created:
echo   - output\theophysics_evidence\00_TOP_100_RANKED_EVIDENCE.md
echo   - output\theophysics_evidence\00_EVIDENCE_INDEX.csv
echo.
set /p open_rep="Open Top 100 Evidence Report now? (y/n): "
if /i "%open_rep%"=="y" start "" "%PROJECT_ROOT%output\theophysics_evidence\00_TOP_100_RANKED_EVIDENCE.md"
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 5: OPEN THEOPHYSICS VAULT
:: ----------------------------------------------------------------------------
:open_vault
if exist "Z:\Theophysics_Vault\02_Evidence_Matrix" (
    echo Opening Z:\Theophysics_Vault\02_Evidence_Matrix...
    start "" "Z:\Theophysics_Vault\02_Evidence_Matrix\47_Formal_Logic_and_Epistemic_Intake"
) else (
    echo [!] 'Z:\Theophysics_Vault' not found or drive Z: is disconnected.
)
pause
goto :menu
