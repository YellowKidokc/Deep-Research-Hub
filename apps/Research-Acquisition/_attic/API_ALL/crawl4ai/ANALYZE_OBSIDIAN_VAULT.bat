@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

:: ============================================================================
:: Theophysics Vault - Deep Research & Analytics Engine
:: Fully portable: Location-independent, non-blocking, resumable batch processing
:: Primary Vault: Z:\Theophysics_Vault
:: ============================================================================

title "Theophysics Vault - Deep Research & Analytics Engine"
color 0b

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT="

:: ----------------------------------------------------------------------------
:: 1. DYNAMIC REPOSITORY & LOCATION DISCOVERY
:: ----------------------------------------------------------------------------
if exist "%SCRIPT_DIR%vault_deep_analytics.py" (
    set "PROJECT_ROOT=%SCRIPT_DIR%"
    goto :find_python
)
if exist "%SCRIPT_DIR%..\vault_deep_analytics.py" (
    pushd "%SCRIPT_DIR%.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :find_python
)
if exist "%SCRIPT_DIR%..\..\vault_deep_analytics.py" (
    pushd "%SCRIPT_DIR%..\.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :find_python
)
if exist "%SCRIPT_DIR%.crawl4ai_root.cfg" (
    set /p SAVED_LOC=<"%SCRIPT_DIR%.crawl4ai_root.cfg"
    if exist "!SAVED_LOC!\vault_deep_analytics.py" (
        set "PROJECT_ROOT=!SAVED_LOC!"
        if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
        goto :find_python
    )
)
if defined CRAWL4AI_DIR (
    if exist "%CRAWL4AI_DIR%\vault_deep_analytics.py" (
        set "PROJECT_ROOT=%CRAWL4AI_DIR%\"
        goto :find_python
    )
)
if exist "D:\GitHub\Research-Acquisition\crawl4ai\vault_deep_analytics.py" (
    set "PROJECT_ROOT=D:\GitHub\Research-Acquisition\crawl4ai\"
    echo D:\GitHub\Research-Acquisition\crawl4ai\> "%SCRIPT_DIR%.crawl4ai_root.cfg"
    goto :find_python
)

echo [!] Could not locate vault_deep_analytics.py automatically.
set /p USER_PATH="Enter or drag-and-drop crawl4ai folder here: "
set "USER_PATH=!USER_PATH:"=!"
if exist "!USER_PATH!\vault_deep_analytics.py" (
    set "PROJECT_ROOT=!USER_PATH!"
    if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
    echo !PROJECT_ROOT!> "%SCRIPT_DIR%.crawl4ai_root.cfg"
    goto :find_python
)

echo [ERROR] Invalid directory. 'vault_deep_analytics.py' not found.
pause
exit /b 1

:: ----------------------------------------------------------------------------
:: 2. PYTHON RUNTIME DETECTION
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

py -3.12 -c "import sys" >nul 2>&1 && set "BASE_PYTHON=py -3.12"
if not defined BASE_PYTHON py -3.11 -c "import sys" >nul 2>&1 && set "BASE_PYTHON=py -3.11"
if not defined BASE_PYTHON py -3 -c "import sys" >nul 2>&1 && set "BASE_PYTHON=py -3"
if not defined BASE_PYTHON python -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1 && set "BASE_PYTHON=python"

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
echo      THEOPHYSICS OBSIDIAN VAULT - DEEP RESEARCH ^& ANALYTICS ENGINE
echo ============================================================================
echo Project Root    : %PROJECT_ROOT%
echo Python Runtime  : %PYTHON_CMD%
echo Primary Vault   : Z:\Theophysics_Vault
echo ============================================================================
echo.
echo Select an action:
echo.
echo   1. [Full Scan]    Scan Complete Master Vault (Z:\Theophysics_Vault)
echo   2. [Targeted]     Scan Specific Folder(s) (e.g. 02_Evidence_Matrix, 01_Cannon_Papers)
echo   3. [Progress]     Check Queue Status ^& Progress Metrics
echo   4. [Export]       Generate Research Dashboard, Equations Index ^& CSV
echo   5. [Open Vault]   Open Analytics Reports Folder in Z:\Theophysics_Vault
echo   6. Exit
echo.
set /p choice="Enter choice (1-6): "

if "%choice%"=="1" goto :scan_master_vault
if "%choice%"=="2" goto :scan_custom_folders
if "%choice%"=="3" goto :check_progress
if "%choice%"=="4" goto :export_reports
if "%choice%"=="5" goto :open_vault_folder
if "%choice%"=="6" exit /b 0

echo Invalid choice.
timeout /t 2 >nul
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 1: SCAN MASTER VAULT
:: ----------------------------------------------------------------------------
:scan_master_vault
cls
echo ============================================================================
echo              SCANNING MASTER VAULT: Z:\Theophysics_Vault
echo ============================================================================
echo.
if not exist "Z:\Theophysics_Vault" (
    echo [ERROR] 'Z:\Theophysics_Vault' is not accessible or drive Z: is disconnected.
    pause
    goto :menu
)

echo Scanning all folders, extracting equations, axioms, and scriptural cross-links...
echo (Non-blocking: gentle on CPU and RAM; resumable if paused).
echo.
"%PYTHON_CMD%" vault_deep_analytics.py "Z:\Theophysics_Vault"
echo.
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 2: SCAN CUSTOM FOLDERS
:: ----------------------------------------------------------------------------
:scan_custom_folders
echo.
echo ============================================================================
echo                    SCAN SPECIFIC VAULT FOLDER(S)
echo ============================================================================
echo Available Presets:
echo   1. 02_Evidence_Matrix (Z:\Theophysics_Vault\02_Evidence_Matrix)
echo   2. 01_Cannon_Papers   (Z:\Theophysics_Vault\01_Cannon_Papers)
echo   3. 00_REFINED_PAPERS  (Z:\Theophysics_Vault\00_REFINED_PAPERS_MASTER)
echo   4. Custom Folder Path
echo.
set /p fchoice="Enter preset (1-4): "

set "TARGET_DIR="
if "%fchoice%"=="1" set "TARGET_DIR=Z:\Theophysics_Vault\02_Evidence_Matrix"
if "%fchoice%"=="2" set "TARGET_DIR=Z:\Theophysics_Vault\01_Cannon_Papers"
if "%fchoice%"=="3" set "TARGET_DIR=Z:\Theophysics_Vault\00_REFINED_PAPERS_MASTER"
if "%fchoice%"=="4" (
    set /p TARGET_DIR="Enter or drag-and-drop folder: "
    set "TARGET_DIR=!TARGET_DIR:"=!"
)

if not defined TARGET_DIR (
    echo No folder selected.
    timeout /t 2 >nul
    goto :menu
)

if not exist "!TARGET_DIR!" (
    echo [ERROR] Folder does not exist: "!TARGET_DIR!"
    pause
    goto :menu
)

echo.
echo Scanning target folder: "!TARGET_DIR!"...
"%PYTHON_CMD%" vault_deep_analytics.py "!TARGET_DIR!"
echo.
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 3: PROGRESS & METRICS
:: ----------------------------------------------------------------------------
:check_progress
cls
echo ============================================================================
echo                     CURRENT VAULT SCAN PROGRESS
echo ============================================================================
echo.
"%PYTHON_CMD%" vault_deep_analytics.py --progress
echo.
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 4: EXPORT REPORTS
:: ----------------------------------------------------------------------------
:export_reports
echo.
echo Compiling and exporting vault analytics reports...
"%PYTHON_CMD%" vault_deep_analytics.py --export
echo.
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION 5: OPEN VAULT FOLDER
:: ----------------------------------------------------------------------------
:open_vault_folder
if exist "Z:\Theophysics_Vault\07_System_and_Operations\Vault_Analytics" (
    start "" "Z:\Theophysics_Vault\07_System_and_Operations\Vault_Analytics"
) else if exist "obsidian_analytics_output" (
    start "" "%PROJECT_ROOT%obsidian_analytics_output"
) else (
    echo No reports folder found yet. Run a scan first.
)
goto :menu
