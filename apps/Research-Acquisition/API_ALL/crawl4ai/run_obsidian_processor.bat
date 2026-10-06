@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

:: ============================================================================
:: Obsidian Analytics Processor - Vault Scanner
:: Fully portable: Location-independent, auto-detects paths and Python venv
:: Primary Vault: Z:\Theophysics_Vault
:: ============================================================================

title "Obsidian Analytics Processor - Theophysics Vault"
color 0b

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT="

:: ----------------------------------------------------------------------------
:: 1. DYNAMIC REPOSITORY & LOCATION DISCOVERY
:: ----------------------------------------------------------------------------
if exist "%SCRIPT_DIR%obsidian_analytics_processor.py" (
    set "PROJECT_ROOT=%SCRIPT_DIR%"
    goto :find_python
)
if exist "%SCRIPT_DIR%..\obsidian_analytics_processor.py" (
    pushd "%SCRIPT_DIR%.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :find_python
)
if exist "%SCRIPT_DIR%..\..\obsidian_analytics_processor.py" (
    pushd "%SCRIPT_DIR%..\.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :find_python
)
if exist "%SCRIPT_DIR%.crawl4ai_root.cfg" (
    set /p SAVED_LOC=<"%SCRIPT_DIR%.crawl4ai_root.cfg"
    if exist "!SAVED_LOC!\obsidian_analytics_processor.py" (
        set "PROJECT_ROOT=!SAVED_LOC!"
        if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
        goto :find_python
    )
)
if defined CRAWL4AI_DIR (
    if exist "%CRAWL4AI_DIR%\obsidian_analytics_processor.py" (
        set "PROJECT_ROOT=%CRAWL4AI_DIR%\"
        goto :find_python
    )
)
if exist "D:\GitHub\Research-Acquisition\crawl4ai\obsidian_analytics_processor.py" (
    set "PROJECT_ROOT=D:\GitHub\Research-Acquisition\crawl4ai\"
    echo D:\GitHub\Research-Acquisition\crawl4ai\> "%SCRIPT_DIR%.crawl4ai_root.cfg"
    goto :find_python
)

echo [!] Could not locate obsidian_analytics_processor.py automatically.
set /p USER_PATH="Enter or drag-and-drop crawl4ai folder here: "
set "USER_PATH=!USER_PATH:"=!"
if exist "!USER_PATH!\obsidian_analytics_processor.py" (
    set "PROJECT_ROOT=!USER_PATH!"
    if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
    echo !PROJECT_ROOT!> "%SCRIPT_DIR%.crawl4ai_root.cfg"
    goto :find_python
)

echo [ERROR] Invalid directory. 'obsidian_analytics_processor.py' not found.
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
        goto :detect_vault
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
:: 3. VAULT SELECTION (DEFAULT: Z:\Theophysics_Vault)
:: ----------------------------------------------------------------------------
:detect_vault
cls
echo ============================================================================
echo                    OBSIDIAN ANALYTICS PROCESSOR
echo ============================================================================
echo Project Root    : %PROJECT_ROOT%
echo Python Runtime  : %PYTHON_CMD%
echo ============================================================================
echo.

set "DEFAULT_VAULT=Z:\Theophysics_Vault"
if not exist "%DEFAULT_VAULT%" (
    echo [!] Default vault '%DEFAULT_VAULT%' not accessible.
    set "DEFAULT_VAULT=%PROJECT_ROOT%"
)

set "VAULT_PATH=%~1"
if not defined VAULT_PATH (
    echo Default Target Vault: %DEFAULT_VAULT%
    echo.
    set /p VAULT_INPUT="Enter vault directory to scan [Press Enter for default]: "
    if defined VAULT_INPUT (
        set "VAULT_PATH=!VAULT_INPUT:"=!"
    ) else (
        set "VAULT_PATH=%DEFAULT_VAULT%"
    )
)

if not exist "%VAULT_PATH%" (
    echo [ERROR] Target path does not exist: "%VAULT_PATH%"
    pause
    exit /b 1
)

set "OUTPUT_DIR=%PROJECT_ROOT%obsidian_analytics_output"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo.
echo Target Vault    : %VAULT_PATH%
echo Output Directory: %OUTPUT_DIR%
echo.
echo Scanning vault markdown files, frontmatter, equations, and tags...
echo.

"%PYTHON_CMD%" "%PROJECT_ROOT%obsidian_analytics_processor.py" "%VAULT_PATH%" "%OUTPUT_DIR%"

echo.
echo ============================================================================
echo                            SCAN COMPLETE
echo ============================================================================
echo Analytics reports generated in: %OUTPUT_DIR%
echo.

set /p open_out="Open output directory? (y/n): "
if /i "%open_out%"=="y" start "" "%OUTPUT_DIR%"

echo.
pause
