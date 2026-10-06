@echo off
setlocal
cd /d "%~dp0"
title GO — YouTube Pipeline (30 workers)

REM ============================================================
REM  GO.bat — one front door for the whole YouTube pipeline
REM
REM  Usage:
REM    GO                          all watched channels, full chain
REM    GO "Daily Dose Of Wisdom"   one channel
REM    GO video "path\to\file.md"  one video file
REM    GO --workers 10             override parallelism
REM    GO --limit 5                cap items per step
REM    GO --dry-run                show what would run, no API
REM    GO --index-only             skip clean, skip catalog
REM    GO --no-lenses              skip the lens pass
REM ============================================================

set "ROOT=%~dp0..\.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "SUBS=%ROOT%\subtitles"
set "VENV=%ROOT%\venv\Scripts\python.exe"

REM --- defaults ---
set "CHAN="
set "VIDEO="
set "WORKERS=30"
set "LIMIT="
set "DRY="
set "INDEX_ONLY="
set "NO_LENSES="
set "FORCE="

REM --- parse arguments ---
:parse
if "%~1"=="" goto :run
if /i "%~1"=="video"       ( set "VIDEO=%~2" & shift & shift & goto :parse )
if /i "%~1"=="--workers"   ( set "WORKERS=%~2" & shift & shift & goto :parse )
if /i "%~1"=="--limit"     ( set "LIMIT=%~2" & shift & shift & goto :parse )
if /i "%~1"=="--dry-run"   ( set "DRY=--dry-run" & shift & goto :parse )
if /i "%~1"=="--index-only"( set "INDEX_ONLY=1" & shift & goto :parse )
if /i "%~1"=="--no-lenses" ( set "NO_LENSES=1" & shift & goto :parse )
if /i "%~1"=="--force"     ( set "FORCE=--force" & shift & goto :parse )
REM anything else is the channel name
set "CHAN=%~1"
shift
goto :parse

:run
set "LIM_FLAG="
if defined LIMIT set "LIM_FLAG=--limit %LIMIT%"

REM ============================================================
REM  STEP 0: Convert (SRT/VTT/JSON → subtitles, if station reachable)
REM ============================================================
if defined INDEX_ONLY goto :step2
echo.
echo === STEP 0  Convert inbox (if X: reachable) ===
if exist "X:\00_CONVERSION_STATION\Transcripts to Markdown\scripts\Run-Inbox.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "X:\00_CONVERSION_STATION\Transcripts to Markdown\scripts\Run-Inbox.ps1"
) else (
    echo   X: not reachable — skipping conversion
)

REM ============================================================
REM  STEP 1: Clean (local Python, no API)
REM ============================================================
echo.
echo === STEP 1  Clean transcripts (local, no API) ===
pushd "%ROOT%\Python Clean Library"
if defined VIDEO (
    REM single video: clean its parent channel folder
    for %%F in ("%VIDEO%") do set "_VCHAN=%%~dpF"
    "%VENV%" clean_library.py --src "%SUBS%" --out "%ROOT%\obsidian_transcripts" --punctuate
) else if defined CHAN (
    "%VENV%" clean_library.py --src "%SUBS%" --out "%ROOT%\obsidian_transcripts" --channel "%CHAN%" --punctuate
) else (
    "%VENV%" clean_library.py --src "%SUBS%" --out "%ROOT%\obsidian_transcripts" --punctuate
)
popd

:step2
REM ============================================================
REM  STEP 2: Index with DeepSeek (30 workers default)
REM ============================================================
echo.
echo === STEP 2  Index with DeepSeek (%WORKERS% workers) ===
if defined VIDEO (
    python index_video.py "%VIDEO%" --workers %WORKERS% %FORCE% %DRY%
) else if defined CHAN (
    python index_video.py "%SUBS%\%CHAN%" --workers %WORKERS% %LIM_FLAG% %FORCE% %DRY%
) else (
    for /f "usebackq eol=# delims=" %%C in ("WATCH_CHANNELS.txt") do (
        echo --- %%C ---
        python index_video.py "%SUBS%\%%C" --workers %WORKERS% %LIM_FLAG% %FORCE% %DRY%
    )
)

REM ============================================================
REM  STEP 3: Lenses (channel saved focus, 30 workers)
REM ============================================================
if defined NO_LENSES goto :step4
if defined DRY goto :step4
echo.
echo === STEP 3  Lens pass (%WORKERS% workers) ===
if defined VIDEO (
    python lens_pass.py "%VIDEO%" --workers %WORKERS%
) else if defined CHAN (
    python lens_pass.py "%SUBS%\%CHAN%" --workers %WORKERS% %LIM_FLAG%
) else (
    for /f "usebackq eol=# delims=" %%C in ("WATCH_CHANNELS.txt") do (
        echo --- lenses: %%C ---
        python lens_pass.py "%SUBS%\%%C" --workers %WORKERS% %LIM_FLAG%
    )
)

:step4
REM ============================================================
REM  STEP 4: Rebuild catalog, overviews, debate pages
REM ============================================================
if defined DRY goto :done
echo.
echo === STEP 4  Rebuild catalog ===
python build_catalog.py

:done
echo.
echo ============================================================
echo   Done.  Notes: %ROOT%\obsidian_indexed
echo ============================================================
pause
