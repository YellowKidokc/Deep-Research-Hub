@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "PY=%ROOT%\.venv\Scripts\python.exe"
set "PIP=%ROOT%\.venv\Scripts\pip.exe"
set "LOGDIR=%ROOT%\logs"
set "LOG=%LOGDIR%\launcher-%DATE:/=-%_%TIME::=-%.log"
set "LOG=%LOG: =0%"

if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>nul
cd /d "%ROOT%"

if /I "%~1"=="update" goto update
if /I "%~1"=="troubleshoot" goto troubleshoot
if /I "%~1"=="diagnose" goto troubleshoot
if /I "%~1"=="test" goto test
if /I "%~1"=="help" goto help
if /I "%~1"=="menu" goto menu

if not "%~1"=="" goto run_args

:menu
cls
echo.
echo YouTube Research Tool
echo =====================
echo.
echo Repo: %ROOT%
echo.
echo 1. Show CLI help
echo 2. List saved transcripts
echo 3. Run a transcript command
echo 4. Run light research
echo 5. Run deep research
echo 6. Update/install dependencies
echo 7. Troubleshoot / diagnostics
echo 8. Run tests
echo 9. Exit
echo.
REM set /p keeps the old value when you just press Enter, so clear it first
set "CHOICE="
set /p "CHOICE=Choose an option: "
if "%CHOICE%"=="1" call "%~f0" help & goto after_run
if "%CHOICE%"=="2" call "%~f0" list & goto after_run
if "%CHOICE%"=="3" goto prompt_transcript
if "%CHOICE%"=="4" goto prompt_research
if "%CHOICE%"=="5" goto prompt_deep
if "%CHOICE%"=="6" call "%~f0" update & goto after_run
if "%CHOICE%"=="7" call "%~f0" troubleshoot & goto after_run
if "%CHOICE%"=="8" call "%~f0" test & goto after_run
if /I "%CHOICE%"=="9" exit /b 0
if /I "%CHOICE%"=="q" exit /b 0
goto menu

:prompt_transcript
set "URL="
set /p "URL=YouTube URL or video ID (Enter = back): "
if "%URL%"=="" goto menu
call "%~f0" transcript "%URL%" --clean --timestamps
goto after_run

:prompt_research
set "URL="
set /p "URL=YouTube URL or video ID (Enter = back): "
if "%URL%"=="" goto menu
call "%~f0" research "%URL%"
goto after_run

:prompt_deep
set "URL="
set /p "URL=YouTube URL or video ID (Enter = back): "
if "%URL%"=="" goto menu
call "%~f0" deep-research "%URL%"
goto after_run

:after_run
echo.
set "NEXT="
set /p "NEXT=[Enter] menu   [O] open transcripts folder   [Q] quit: "
if /I "%NEXT%"=="q" exit /b 0
if /I "%NEXT%"=="o" start "" "%USERPROFILE%\yt_transcripts" & goto after_run
goto menu

:help
call :ensure_ready || exit /b 1
"%PY%" yt_scrape.py --help
exit /b %ERRORLEVEL%

:run_args
call :ensure_ready || exit /b 1
echo Running: yt_scrape.py %*
"%PY%" yt_scrape.py %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo Command failed with exit code %RC%.
  echo Try: "%~f0" troubleshoot
)
exit /b %RC%

:update
echo Updating YouTube Research Tool...
echo Log: %LOG%
echo.

where git >nul 2>nul
if "%ERRORLEVEL%"=="0" (
  echo [1/5] Fetching latest git changes...
  git status --short --branch
  git pull --ff-only 1>>"%LOG%" 2>>&1
  if not "%ERRORLEVEL%"=="0" (
    echo Git pull failed. See log: %LOG%
    echo If you have local edits, commit/stash them before updating.
  )
) else (
  echo [1/5] Git not found on PATH; skipping git update.
)

echo [2/5] Ensuring Python virtual environment...
call :ensure_venv || exit /b 1

echo [3/5] Upgrading pip...
"%PY%" -m pip install --upgrade pip 1>>"%LOG%" 2>>&1
if not "%ERRORLEVEL%"=="0" goto update_failed

echo [4/5] Installing requirements and test runner...
"%PY%" -m pip install -r requirements.txt pytest 1>>"%LOG%" 2>>&1
if not "%ERRORLEVEL%"=="0" goto update_failed

echo [5/5] Updating yt-dlp...
"%PY%" -m pip install --upgrade yt-dlp 1>>"%LOG%" 2>>&1
if not "%ERRORLEVEL%"=="0" goto update_failed

echo.
echo Update/install complete.
echo Run diagnostics with: "%~f0" troubleshoot
exit /b 0

:update_failed
echo.
echo Update failed. See log:
echo %LOG%
exit /b 1

:troubleshoot
echo YouTube Research Tool Diagnostics
echo ================================
echo Repo: %ROOT%
echo Log:  %LOG%
echo.

echo [Python]
where py
where python
if exist "%PY%" (
  "%PY%" --version
) else (
  echo Missing venv Python: %PY%
)
echo.

echo [Git]
where git
if "%ERRORLEVEL%"=="0" git status --short --branch
echo.

echo [Virtual environment and dependencies]
call :ensure_ready
if not "%ERRORLEVEL%"=="0" (
  echo Dependency setup failed. Run: "%~f0" update
  exit /b 1
)
"%PY%" -m pip --version
"%PY%" -m pip show yt-dlp edge-tts pytest
echo.

echo [Optional tools]
where ffmpeg
if not "%ERRORLEVEL%"=="0" echo ffmpeg not found. Whisper fallback will not work until ffmpeg is installed and on PATH.
"%PY%" -c "import importlib.util; print('faster-whisper installed:', importlib.util.find_spec('faster_whisper') is not None)"
echo.

echo [CLI smoke checks]
"%PY%" yt_scrape.py --help >nul
if not "%ERRORLEVEL%"=="0" (
  echo CLI help failed.
  exit /b 1
)
"%PY%" yt_scrape.py list --json
if not "%ERRORLEVEL%"=="0" (
  echo List command failed.
  exit /b 1
)
echo.

echo Diagnostics complete.
exit /b 0

:test
call :ensure_ready || exit /b 1
"%PY%" -m pytest -q
exit /b %ERRORLEVEL%

:ensure_ready
call :ensure_venv || exit /b 1
if not exist "%ROOT%\requirements.txt" (
  echo Missing requirements.txt in %ROOT%
  exit /b 1
)
"%PY%" -c "import yt_dlp, edge_tts" >nul 2>nul
if not "%ERRORLEVEL%"=="0" (
  echo Required packages are missing. Installing now...
  "%PY%" -m pip install -r requirements.txt pytest
  if not "%ERRORLEVEL%"=="0" exit /b 1
)
exit /b 0

:ensure_venv
if exist "%PY%" exit /b 0
echo Creating .venv...
where py >nul 2>nul
if "%ERRORLEVEL%"=="0" (
  py -3.12 -m venv "%ROOT%\.venv" 2>>"%LOG%"
  if "%ERRORLEVEL%"=="0" exit /b 0
  py -3 -m venv "%ROOT%\.venv" 2>>"%LOG%"
  if "%ERRORLEVEL%"=="0" exit /b 0
) else (
  python -m venv "%ROOT%\.venv" 2>>"%LOG%"
  if "%ERRORLEVEL%"=="0" exit /b 0
)
echo Failed to create virtual environment. Install Python 3.10+ and try again.
exit /b 1
