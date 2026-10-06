@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

:: ============================================================================
:: Crawl4AI - Package Updater & Diagnostic Troubleshooter
:: Fully portable: Location-independent, auto-detects paths, repairs environments
:: ============================================================================

title "Crawl4AI - Package Updater & Troubleshooter"
color 0a

set "CLI_CHOICE=%~1"
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT="

:: ----------------------------------------------------------------------------
:: 1. DYNAMIC REPOSITORY & LOCATION DISCOVERY
:: ----------------------------------------------------------------------------
if exist "%SCRIPT_DIR%pyproject.toml" if exist "%SCRIPT_DIR%crawl4ai" (
    set "PROJECT_ROOT=%SCRIPT_DIR%"
    goto :find_python
)
if exist "%SCRIPT_DIR%..\pyproject.toml" if exist "%SCRIPT_DIR%..\crawl4ai" (
    pushd "%SCRIPT_DIR%.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :find_python
)
if exist "%SCRIPT_DIR%..\..\pyproject.toml" if exist "%SCRIPT_DIR%..\..\crawl4ai" (
    pushd "%SCRIPT_DIR%..\.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :find_python
)
if exist "%SCRIPT_DIR%.crawl4ai_root.cfg" (
    set /p SAVED_LOC=<"%SCRIPT_DIR%.crawl4ai_root.cfg"
    if exist "!SAVED_LOC!\pyproject.toml" (
        set "PROJECT_ROOT=!SAVED_LOC!"
        if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
        goto :find_python
    )
)
if defined CRAWL4AI_DIR (
    if exist "%CRAWL4AI_DIR%\pyproject.toml" (
        set "PROJECT_ROOT=%CRAWL4AI_DIR%\"
        goto :find_python
    )
)
if exist "D:\GitHub\Research-Acquisition\crawl4ai\pyproject.toml" (
    set "PROJECT_ROOT=D:\GitHub\Research-Acquisition\crawl4ai\"
    echo D:\GitHub\Research-Acquisition\crawl4ai\> "%SCRIPT_DIR%.crawl4ai_root.cfg"
    goto :find_python
)

echo [!] Crawl4AI repository folder not found automatically.
set /p USER_PATH="Enter or drag-and-drop Crawl4AI folder here: "
set "USER_PATH=!USER_PATH:"=!"
if exist "!USER_PATH!\pyproject.toml" (
    set "PROJECT_ROOT=!USER_PATH!"
    if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
    echo !PROJECT_ROOT!> "%SCRIPT_DIR%.crawl4ai_root.cfg"
    goto :find_python
)

echo [ERROR] Invalid path. 'pyproject.toml' not found.
pause
exit /b 1

:: ----------------------------------------------------------------------------
:: 2. PYTHON & VENV DETECTION
:: ----------------------------------------------------------------------------
:find_python
cd /d "%PROJECT_ROOT%"
set "PYTHON_CMD="
set "PIP_CMD="

if not exist "%PROJECT_ROOT%venv\Scripts\python.exe" goto :locate_base_python

"%PROJECT_ROOT%venv\Scripts\python.exe" -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=%PROJECT_ROOT%venv\Scripts\python.exe"
    set "PIP_CMD=%PROJECT_ROOT%venv\Scripts\pip.exe"
    goto :check_cli
)

:locate_base_python
set "BASE_PYTHON="
py -3.12 -c "import sys" >nul 2>&1
if !errorlevel! equ 0 set "BASE_PYTHON=py -3.12"

if not defined BASE_PYTHON (
    py -3.11 -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 set "BASE_PYTHON=py -3.11"
)

if not defined BASE_PYTHON (
    py -3 -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 set "BASE_PYTHON=py -3"
)

if not defined BASE_PYTHON (
    python -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 set "BASE_PYTHON=python"
)

if not defined BASE_PYTHON (
    echo [ERROR] Python 3.10+ was not found on your system.
    pause
    exit /b 1
)

if exist "%PROJECT_ROOT%venv" rmdir /s /q "%PROJECT_ROOT%venv" >nul 2>&1
%BASE_PYTHON% -m venv "%PROJECT_ROOT%venv"
set "PYTHON_CMD=%PROJECT_ROOT%venv\Scripts\python.exe"
set "PIP_CMD=%PROJECT_ROOT%venv\Scripts\pip.exe"

:check_cli
if defined CLI_CHOICE (
    set "choice=%CLI_CHOICE%"
    if "!choice!"=="1" goto :run_diagnostics
    if "!choice!"=="2" goto :update_packages
    if "!choice!"=="3" goto :update_and_diagnose
    if "!choice!"=="4" goto :repair_environment
    if "!choice!"=="5" goto :run_official_doctor
    if "!choice!"=="6" exit /b 0
)

:: ----------------------------------------------------------------------------
:: MAIN MENU
:: ----------------------------------------------------------------------------
:menu
cls
echo ============================================================================
echo           CRAWL4AI - PACKAGE UPDATER ^& TROUBLESHOOTING TOOLKIT
echo ============================================================================
echo Root Directory : %PROJECT_ROOT%
echo Python Path    : %PYTHON_CMD%
echo ============================================================================
echo.
echo Select an operation:
echo.
echo   1. [Troubleshoot] Run Full Health Check ^& Diagnostics
echo   2. [Update]       Update All Packages ^& Dependencies
echo   3. [All-in-One]   Update Packages AND Run Full Diagnostics
echo   4. [Repair]       Auto-Repair Environment (Fix venv, reinstall browsers)
echo   5. [Doctor]       Run Official 'crawl4ai-doctor' Crawl Test
echo   6. Exit
echo.
set /p choice="Enter choice (1-6): "

if "%choice%"=="1" goto :run_diagnostics
if "%choice%"=="2" goto :update_packages
if "%choice%"=="3" goto :update_and_diagnose
if "%choice%"=="4" goto :repair_environment
if "%choice%"=="5" goto :run_official_doctor
if "%choice%"=="6" exit /b 0

echo Invalid choice.
timeout /t 2 >nul
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION: UPDATE PACKAGES
:: ----------------------------------------------------------------------------
:update_packages
echo.
echo ============================================================================
echo                        UPDATING ALL PACKAGES
echo ============================================================================
echo.
echo [1/4] Upgrading pip, setuptools, wheel...
"%PYTHON_CMD%" -m pip install --upgrade pip setuptools wheel

echo.
echo [2/4] Updating dependencies from requirements.txt...
if exist "%PROJECT_ROOT%requirements.txt" (
    "%PIP_CMD%" install --upgrade -r "%PROJECT_ROOT%requirements.txt"
) else (
    echo requirements.txt not found, skipping.
)

echo.
echo [3/4] Updating Crawl4AI editable install...
"%PIP_CMD%" install -e .

echo.
echo [4/4] Checking for broken dependencies or version conflicts...
"%PIP_CMD%" check
if !errorlevel! equ 0 (
    echo [OK] All package dependencies are consistent!
) else (
    echo [!] Warnings detected by pip check above.
)
echo.
echo Package update completed.
if defined CLI_CHOICE exit /b 0
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION: UPDATE AND DIAGNOSE
:: ----------------------------------------------------------------------------
:update_and_diagnose
echo.
echo ============================================================================
echo                  STEP 1: UPDATING PACKAGES
echo ============================================================================
"%PYTHON_CMD%" -m pip install --upgrade pip setuptools wheel
if exist "%PROJECT_ROOT%requirements.txt" (
    "%PIP_CMD%" install --upgrade -r "%PROJECT_ROOT%requirements.txt"
)
"%PIP_CMD%" install -e .
echo.
echo Update complete. Proceeding to health diagnostics...
goto :run_diagnostics

:: ----------------------------------------------------------------------------
:: ACTION: RUN DIAGNOSTICS & TROUBLESHOOTING
:: ----------------------------------------------------------------------------
:run_diagnostics
cls
echo ============================================================================
echo                  RUNNING SYSTEM ^& CRAWL4AI DIAGNOSTICS
echo ============================================================================
echo.

"%PYTHON_CMD%" "%PROJECT_ROOT%test_diagnostics_suite.py"
set "DIAG_CODE=!errorlevel!"

:: If script was executed from outside project root (e.g. Desktop), copy receipt beside script
if not "%SCRIPT_DIR%"=="%PROJECT_ROOT%" (
    copy /y "%PROJECT_ROOT%output\diagnostic_receipt.txt" "%SCRIPT_DIR%diagnostic_receipt.txt" >nul 2>&1
    echo [OK] Copied receipt to local script folder: %SCRIPT_DIR%diagnostic_receipt.txt
)

echo.
if defined CLI_CHOICE exit /b !DIAG_CODE!
pause
goto :menu

:: ----------------------------------------------------------------------------
:: ACTION: REPAIR ENVIRONMENT
:: ----------------------------------------------------------------------------
:repair_environment
echo.
echo ============================================================================
echo                    ENVIRONMENT REPAIR WIZARD
echo ============================================================================
echo.
echo This will:
echo   1. Reinstall/repair Playwright Chromium browser
echo   2. Reinstall/repair Patchright Chromium browser
echo   3. Initialize database and reset cache directories
echo   4. Re-install Crawl4AI in editable mode
echo.
set /p confirm_repair="Proceed with repair? (y/n): "
if /i not "%confirm_repair%"=="y" goto :menu

echo.
echo [1/4] Installing Playwright Chromium browser...
"%PYTHON_CMD%" -m playwright install --with-deps chromium

echo.
echo [2/4] Installing Patchright Chromium browser...
"%PYTHON_CMD%" -m patchright install --with-deps chromium

echo.
echo [3/4] Initializing database and cache...
"%PYTHON_CMD%" -c "from crawl4ai.install import setup_home_directory, run_migration; setup_home_directory(); run_migration()"

echo.
echo [4/4] Reinstalling Crawl4AI (-e .)...
"%PIP_CMD%" install -e .

echo.
echo [OK] Repair actions completed. Running diagnostics to verify...
timeout /t 2 >nul
goto :run_diagnostics

:: ----------------------------------------------------------------------------
:: ACTION: RUN OFFICIAL CRAWL4AI DOCTOR
:: ----------------------------------------------------------------------------
:run_official_doctor
echo.
echo ============================================================================
echo                    RUNNING 'crawl4ai-doctor'
echo ============================================================================
echo.
"%PYTHON_CMD%" -c "from crawl4ai.install import doctor; doctor()"
echo.
if defined CLI_CHOICE exit /b 0
pause
goto :menu
