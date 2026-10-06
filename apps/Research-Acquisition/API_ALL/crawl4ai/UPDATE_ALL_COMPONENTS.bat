@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Crawl4AI - Universal Component Updater
:: Fully portable: Works regardless of where this script or folder is moved.
:: ============================================================================

title Crawl4AI - Update All Components
color 0b

echo ============================================================================
echo                    CRAWL4AI - COMPONENT UPDATER
echo ============================================================================
echo.

:: ----------------------------------------------------------------------------
:: 1. DYNAMIC REPOSITORY & LOCATION DISCOVERY
:: ----------------------------------------------------------------------------
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT="

if exist "%SCRIPT_DIR%pyproject.toml" if exist "%SCRIPT_DIR%crawl4ai" (
    set "PROJECT_ROOT=%SCRIPT_DIR%"
    goto :root_found
)

if exist "%SCRIPT_DIR%..\pyproject.toml" if exist "%SCRIPT_DIR%..\crawl4ai" (
    pushd "%SCRIPT_DIR%.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :root_found
)

if exist "%SCRIPT_DIR%..\..\pyproject.toml" if exist "%SCRIPT_DIR%..\..\crawl4ai" (
    pushd "%SCRIPT_DIR%..\.."
    set "PROJECT_ROOT=!CD!\"
    popd
    goto :root_found
)

if exist "%SCRIPT_DIR%.crawl4ai_root.cfg" (
    set /p SAVED_LOC=<"%SCRIPT_DIR%.crawl4ai_root.cfg"
    if exist "!SAVED_LOC!\pyproject.toml" (
        set "PROJECT_ROOT=!SAVED_LOC!"
        if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
        goto :root_found
    )
)

if defined CRAWL4AI_DIR (
    if exist "%CRAWL4AI_DIR%\pyproject.toml" (
        set "PROJECT_ROOT=%CRAWL4AI_DIR%\"
        goto :root_found
    )
)

if exist "D:\GitHub\Research-Acquisition\crawl4ai\pyproject.toml" (
    set "PROJECT_ROOT=D:\GitHub\Research-Acquisition\crawl4ai\"
    goto :root_found
)

echo [!] Could not automatically locate the Crawl4AI project folder.
echo.
set /p USER_PATH="Please enter or drag-and-drop your Crawl4AI folder here: "
set "USER_PATH=!USER_PATH:"=!"
if exist "!USER_PATH!\pyproject.toml" (
    set "PROJECT_ROOT=!USER_PATH!"
    if not "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT!\"
    echo !PROJECT_ROOT!> "%SCRIPT_DIR%.crawl4ai_root.cfg"
    echo Saved project location for future runs.
    echo.
    goto :root_found
)

echo [ERROR] Invalid Crawl4AI directory. 'pyproject.toml' not found.
pause
exit /b 1

:root_found
cd /d "%PROJECT_ROOT%"
echo [OK] Project Root: %PROJECT_ROOT%
echo.

:: ----------------------------------------------------------------------------
:: 2. PYTHON & VIRTUAL ENVIRONMENT DETECTION
:: ----------------------------------------------------------------------------
echo [i] Detecting Python environment...
set "PYTHON_CMD="
set "PIP_CMD="

if not exist "%PROJECT_ROOT%venv\Scripts\python.exe" goto :find_base_python

"%PROJECT_ROOT%venv\Scripts\python.exe" -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=%PROJECT_ROOT%venv\Scripts\python.exe"
    set "PIP_CMD=%PROJECT_ROOT%venv\Scripts\pip.exe"
    echo [OK] Using active virtual environment: %PROJECT_ROOT%venv
    goto :python_ready
)

echo [!] Existing virtual environment is broken (likely due to folder relocation).
goto :find_base_python

:find_base_python
echo [i] Locating system Python 3.10+...
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
    echo [ERROR] Could not find Python on your system PATH or Windows py launcher.
    echo Please ensure Python 3.10 or newer is installed.
    pause
    exit /b 1
)

echo [i] Found base Python: %BASE_PYTHON%
echo [i] Initializing clean virtual environment at "%PROJECT_ROOT%venv"...
if exist "%PROJECT_ROOT%venv" (
    echo [i] Cleaning outdated virtual environment folder...
    rmdir /s /q "%PROJECT_ROOT%venv" >nul 2>&1
)

%BASE_PYTHON% -m venv "%PROJECT_ROOT%venv"
if not exist "%PROJECT_ROOT%venv\Scripts\python.exe" (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)

set "PYTHON_CMD=%PROJECT_ROOT%venv\Scripts\python.exe"
set "PIP_CMD=%PROJECT_ROOT%venv\Scripts\pip.exe"
echo [OK] Virtual environment successfully created at %PROJECT_ROOT%venv

:python_ready
echo.
"%PYTHON_CMD%" -c "import sys; print('Python runtime:', sys.version.split()[0])"
echo.

:: ----------------------------------------------------------------------------
:: 3. COMPONENT 1: GIT REPOSITORY SYNC (SAFE)
:: ----------------------------------------------------------------------------
echo ============================================================================
echo [Step 1/5] Updating Git Repository (if applicable)
echo ============================================================================
where git >nul 2>&1
if !errorlevel! neq 0 (
    echo [i] Git not detected on PATH. Skipping git sync.
    goto :step_pip
)

if not exist "%PROJECT_ROOT%.git" (
    echo [i] Not a Git clone. Skipping git sync.
    goto :step_pip
)

set "HAS_GIT_CHANGES="
for /f %%i in ('git status --porcelain 2^>nul') do set "HAS_GIT_CHANGES=1"
if defined HAS_GIT_CHANGES (
    echo [!] Uncommitted files detected in workspace.
    echo [i] Skipping 'git pull' to safeguard your local files.
) else (
    echo [i] Pulling latest updates from remote repository...
    git pull
)

:step_pip
echo.
:: ----------------------------------------------------------------------------
:: 4. COMPONENT 2: PIP, WHEEL, SETUPTOOLS
:: ----------------------------------------------------------------------------
echo ============================================================================
echo [Step 2/5] Updating Core Build Tools (pip, setuptools, wheel)
echo ============================================================================
"%PYTHON_CMD%" -m pip install --upgrade pip setuptools wheel
echo.

:: ----------------------------------------------------------------------------
:: 5. COMPONENT 3: CRAWL4AI INSTALLATION & DEPENDENCIES
:: ----------------------------------------------------------------------------
echo ============================================================================
echo [Step 3/5] Installing / Updating Crawl4AI and Python Requirements
echo ============================================================================
echo [i] Installing Crawl4AI in editable development mode...
"%PIP_CMD%" install -e .

if exist "%PROJECT_ROOT%requirements.txt" (
    echo [i] Verifying requirements.txt dependencies...
    "%PIP_CMD%" install -r "%PROJECT_ROOT%requirements.txt"
)
echo.

:: ----------------------------------------------------------------------------
:: 6. COMPONENT 4: BROWSER ENGINES (PLAYWRIGHT & PATCHRIGHT)
:: ----------------------------------------------------------------------------
echo ============================================================================
echo [Step 4/5] Updating Browser Engines (Playwright & Patchright Chromium)
echo ============================================================================
echo [i] Installing/Updating Playwright Chromium browser...
"%PYTHON_CMD%" -m playwright install chromium
echo.
echo [i] Installing/Updating Patchright Chromium browser (Stealth Engine)...
"%PYTHON_CMD%" -m patchright install chromium
echo.

:: ----------------------------------------------------------------------------
:: 7. COMPONENT 5: DATABASE & CACHE STRUCTURE
:: ----------------------------------------------------------------------------
echo ============================================================================
echo [Step 5/5] Initializing Database & User Home Cache
echo ============================================================================
"%PYTHON_CMD%" -c "from crawl4ai.install import setup_home_directory, run_migration; setup_home_directory(); run_migration()"
echo.

:: ----------------------------------------------------------------------------
:: SUMMARY & QUICK CHECK
:: ----------------------------------------------------------------------------
echo ============================================================================
echo                          UPDATE COMPLETE!
echo ============================================================================
echo [OK] Project Directory : %PROJECT_ROOT%
echo [OK] Python Interpreter: %PYTHON_CMD%
"%PYTHON_CMD%" -c "import crawl4ai; print('Crawl4AI Version  :', getattr(crawl4ai, '__version__', 'Installed'))"
echo.
echo All components are updated and configured.
echo You can move this folder to any drive or path at any time.
echo ============================================================================
echo.
pause
