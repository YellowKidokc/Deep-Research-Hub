@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title YouTube — Download + Process

REM ============================================================
REM  YOUTUBE.bat — one file: download, clean, index, catalog
REM
REM  Usage:
REM    YOUTUBE                               paste URLs interactively (Webshare)
REM    YOUTUBE "https://youtube.com/@chan"    download a channel
REM    YOUTUBE "https://youtube.com/watch?v=abc"   one video
REM    YOUTUBE --playlist "url"              a playlist
REM    YOUTUBE --channel "url"               explicit channel mode
REM    YOUTUBE --skip-download               process what's already in subtitles/
REM    YOUTUBE --index-only                  skip download + clean, just index
REM    YOUTUBE --workers 30                  parallel workers (default 30)
REM    YOUTUBE --limit 5                     cap items per step
REM    YOUTUBE --dry-run                     show plan, no API
REM    YOUTUBE --no-lenses                   skip lens pass
REM ============================================================

set "ROOT=%~dp0"
for %%I in ("%ROOT%\.") do set "ROOT=%%~fI"
set "SUBS=%ROOT%\subtitles"
set "PY=%ROOT%\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
set "DS=%ROOT%\pipeline-workflows\deepseek-home"

REM --- defaults ---
set "URL="
set "MODE="
set "WORKERS=30"
set "LIMIT="
set "DRY="
set "SKIP_DL="
set "INDEX_ONLY="
set "NO_LENSES="
set "FORCE="

REM --- load Webshare credentials ---
for %%V in (WEBSHARE_USER WEBSHARE_PASS) do (
    if "!%%V!"=="" (
        for /f "usebackq delims=" %%E in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('%%V','User')"`) do (
            if not "%%E"=="" set "%%V=%%E"
        )
    )
)

REM --- parse arguments ---
:parse
if "%~1"=="" goto :decide
if /i "%~1"=="--channel"       ( set "MODE=channel" & set "URL=%~2" & shift & shift & goto :parse )
if /i "%~1"=="--playlist"      ( set "MODE=playlist" & set "URL=%~2" & shift & shift & goto :parse )
if /i "%~1"=="--workers"       ( set "WORKERS=%~2" & shift & shift & goto :parse )
if /i "%~1"=="--limit"         ( set "LIMIT=%~2" & shift & shift & goto :parse )
if /i "%~1"=="--dry-run"       ( set "DRY=1" & shift & goto :parse )
if /i "%~1"=="--skip-download" ( set "SKIP_DL=1" & shift & goto :parse )
if /i "%~1"=="--index-only"    ( set "INDEX_ONLY=1" & shift & goto :parse )
if /i "%~1"=="--no-lenses"     ( set "NO_LENSES=1" & shift & goto :parse )
if /i "%~1"=="--force"         ( set "FORCE=--force" & shift & goto :parse )
REM bare argument = URL
if not defined URL (
    set "URL=%~1"
    shift
    goto :parse
)
shift
goto :parse

:decide
REM ============================================================
REM  STEP 1: Download
REM ============================================================
if defined INDEX_ONLY goto :step_clean_skip
if defined SKIP_DL goto :step_clean

if not defined URL (
    echo.
    echo   No URL given. Entering interactive mode (Webshare proxy).
    echo   Paste a video, playlist, or channel URL. Type Q to quit.
    echo.
    :interactive
    set "IURL="
    set /p "IURL=URL> "
    if /i "!IURL!"=="Q" goto :step_clean
    if "!IURL!"=="" goto :interactive
    echo.
    echo --- Downloading: !IURL! ---
    "%PY%" "%ROOT%\ytgrab.py" "!IURL!"
    echo.
    goto :interactive
)

echo.
echo ============================================================
echo   STEP 1: Download transcripts
echo ============================================================
echo   URL:  %URL%
echo.

if defined DRY (
    echo   [DRY RUN] would download: %URL%
    goto :step_clean
)

REM detect channel vs video vs playlist
echo %URL% | findstr /i "@" >nul && set "MODE=channel"
echo %URL% | findstr /i "playlist?list=" >nul && set "MODE=playlist"
if not defined MODE set "MODE=video"

if "%MODE%"=="channel" (
    echo   Detected: channel — routing through GRAB_CHANNEL
    call "%ROOT%\GRAB_CHANNEL.bat" "%URL%"
) else (
    echo   Detected: %MODE%
    "%PY%" "%ROOT%\ytgrab.py" "%URL%"
)

:step_clean
REM ============================================================
REM  STEP 2: Clean transcripts (local, no API)
REM ============================================================
echo.
echo ============================================================
echo   STEP 2: Clean transcripts (local Python, no API)
echo ============================================================

pushd "%ROOT%\Python Clean Library"
"%PY%" clean_library.py --src "%SUBS%" --out "%ROOT%\obsidian_transcripts" --punctuate
popd

:step_clean_skip
REM ============================================================
REM  STEP 3: Index with DeepSeek (30 workers)
REM ============================================================
echo.
echo ============================================================
echo   STEP 3: Index with DeepSeek (%WORKERS% workers)
echo ============================================================

set "LIM_FLAG="
if defined LIMIT set "LIM_FLAG=--limit %LIMIT%"
set "DRY_FLAG="
if defined DRY set "DRY_FLAG=--dry-run"

pushd "%DS%"
for /f "usebackq eol=# delims=" %%C in ("WATCH_CHANNELS.txt") do (
    echo.
    echo --- Index: %%C ---
    python index_video.py "%SUBS%\%%C" --workers %WORKERS% %LIM_FLAG% %FORCE% %DRY_FLAG%
)
popd

REM ============================================================
REM  STEP 4: Lenses
REM ============================================================
if defined NO_LENSES goto :step_catalog
if defined DRY goto :step_catalog

echo.
echo ============================================================
echo   STEP 4: Lens pass (%WORKERS% workers)
echo ============================================================

pushd "%DS%"
for /f "usebackq eol=# delims=" %%C in ("WATCH_CHANNELS.txt") do (
    echo --- Lenses: %%C ---
    python lens_pass.py "%SUBS%\%%C" --workers %WORKERS% %LIM_FLAG%
)
popd

:step_catalog
REM ============================================================
REM  STEP 5: Rebuild catalog
REM ============================================================
if defined DRY goto :done

echo.
echo ============================================================
echo   STEP 5: Rebuild catalog, overviews, debate pages
echo ============================================================

pushd "%DS%"
python build_catalog.py
popd

:done
echo.
echo ============================================================
echo   Done.
echo.
echo   Raw transcripts:  %SUBS%
echo   Cleaned:          %ROOT%\obsidian_transcripts
echo   Indexed:          %ROOT%\obsidian_indexed
echo ============================================================
pause
