@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title YouTube Pipeline

set "REPO=D:\GitHub\Research-Acquisition\yt-transcript-downloader"
set "SUBS=%REPO%\subtitles"
set "CLEAN=%REPO%\obsidian_transcripts"
set "ANALYSIS=%REPO%\deepseek_arguments_analysis"
set "DS=%REPO%\pipeline-workflows\deepseek-home"
set "PY=%REPO%\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

REM --- load Webshare credentials ---
for %%V in (WEBSHARE_USER WEBSHARE_PASS) do (
    if "!%%V!"=="" (
        for /f "usebackq delims=" %%E in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('%%V','User')"`) do (
            if not "%%E"=="" set "%%V=%%E"
        )
    )
)

echo.
echo =========================================================================
echo  YOUTUBE PIPELINE
echo =========================================================================
echo.
echo  What do you want to do?
echo.
echo    1  Download a channel or playlist
echo    2  Download a single video
echo    3  Process what's already downloaded (skip download)
echo    4  Analyze only (skip download + clean)
echo    5  Debate Map Scanner (pick a folder, match against 80 questions)
echo.
echo =========================================================================
echo.

set "CHOICE="
set /p "CHOICE=  Pick a number (1-5): "

if "%CHOICE%"=="1" goto :download_channel
if "%CHOICE%"=="2" goto :download_video
if "%CHOICE%"=="3" goto :step_clean
if "%CHOICE%"=="4" goto :step_analyze
if "%CHOICE%"=="5" goto :debate_scan
echo  Invalid choice.
pause
exit /b 1

REM =========================================================================
:download_channel
REM =========================================================================
echo.
set "URL="
set /p "URL=  Paste the channel or playlist URL: "
if "!URL!"=="" (
    echo  No URL entered.
    pause
    exit /b 1
)

echo.
echo  Counting videos on the channel...
"%PY%" "%REPO%\channel_size.py" "!URL!" > "%TEMP%\ytcount.txt" 2>nul
set "COUNT=0"
set "CHNAME="
for /f "usebackq tokens=1,2 delims=|" %%A in ("%TEMP%\ytcount.txt") do (
    set "COUNT=%%A"
    set "CHNAME=%%B"
)

if "!CHNAME!"=="" set "CHNAME=Unsorted"

echo.
echo  Channel: !CHNAME!
if not "%COUNT%"=="0" echo  Videos:  !COUNT!
echo.
echo  Where should transcripts be saved?
echo    Default: %SUBS%\!CHNAME!
echo    (Press Enter to use default, or type a full path)
echo.
set "SAVETO="
set /p "SAVETO=  Save to: "
if "!SAVETO!"=="" set "SAVETO=%SUBS%\!CHNAME!"

echo.
echo =========================================================================
echo  STEP 1 of 5: DOWNLOADING TRANSCRIPTS
echo =========================================================================
echo  URL:       !URL!
echo  Channel:   !CHNAME!
echo  Saving to: !SAVETO!
echo  Method:    Direct first, Webshare proxy as fallback
echo =========================================================================
echo.

if "%COUNT%"=="0" (
    echo  Could not count videos. Trying direct download...
    echo.
    echo  Starting background watcher (auto-converts to markdown when downloads go quiet)...
    start "Watcher" /min "%PY%" "%REPO%\watch_subtitles.py" --quiet 10
    echo  [OK] Watcher running in background (minimized window)
    echo.
    "%PY%" "%REPO%\ytgrab.py" "!URL!" --out "!SAVETO!"
) else (
    echo  Downloading !COUNT! videos...
    echo.
    echo  Starting background watcher (auto-converts to markdown when downloads go quiet)...
    start "Watcher" /min "%PY%" "%REPO%\watch_subtitles.py" --quiet 10
    echo  [OK] Watcher running in background (minimized window)
    echo.
    echo  Folder structure:
    echo    !SAVETO!\                     raw transcripts (timestamped)
    echo    !SAVETO!\Clean MD\            converted to clean markdown (auto)
    echo.
    call "%REPO%\GRAB_CHANNEL.bat" "!URL!" "!SAVETO!"
)

if errorlevel 1 (
    echo.
    echo  [WARNING] Download had issues. Check output above.
) else (
    echo.
    echo  [OK] Download complete.
)
goto :step_clean

REM =========================================================================
:download_video
REM =========================================================================
echo.
set "URL="
set /p "URL=  Paste the video URL: "
if "!URL!"=="" (
    echo  No URL entered.
    pause
    exit /b 1
)

echo.
echo =========================================================================
echo  STEP 1 of 5: DOWNLOADING TRANSCRIPT
echo =========================================================================
echo  URL:       !URL!
echo  Method:    Direct first, Webshare proxy as fallback
echo  Saving to: %SUBS%
echo =========================================================================
echo.

echo  Fetching transcript...
"%PY%" "%REPO%\ytgrab.py" "!URL!" --out "%SUBS%"

if errorlevel 1 (
    echo.
    echo  [WARNING] Download had issues. Check output above.
) else (
    echo.
    echo  [OK] Download complete.
)
goto :step_clean

REM =========================================================================
:step_clean
REM =========================================================================
echo.
echo =========================================================================
echo  STEP 2 of 5: CLEANING TRANSCRIPTS
echo =========================================================================
echo  Converting raw downloads to punctuated Obsidian-ready markdown
echo  Source:  %SUBS%
echo  Output:  %CLEAN%
echo  (Local Python only — no API calls, no tokens burned)
echo =========================================================================
echo.

pushd "%REPO%\Python Clean Library"
"%PY%" clean_library.py --src "%SUBS%" --out "%CLEAN%" --punctuate
if errorlevel 1 (
    echo.
    echo  [WARNING] Cleaning had issues. Check output above.
) else (
    echo.
    echo  [OK] Cleaning complete.
)
popd

REM =========================================================================
:step_analyze
REM =========================================================================
echo.
set "WORKERS=30"
set /p "WORKERS=  How many parallel workers? [30]: "
if "!WORKERS!"=="" set "WORKERS=30"

echo.
echo =========================================================================
echo  STEP 3 of 5: ANALYZING WITH DEEPSEEK
echo =========================================================================
echo  Extracting arguments, debates, stories, claims from transcripts
echo  Workers:  !WORKERS! parallel calls
echo  Model:    deepseek-chat
echo  Output:   %ANALYSIS%
echo =========================================================================
echo.

pushd "%DS%"
for /f "usebackq eol=# delims=" %%C in ("WATCH_CHANNELS.txt") do (
    echo  --- Analyzing channel: %%C ---
    python index_video.py "%SUBS%\%%C" --workers !WORKERS!
    echo.
)
popd

echo  [OK] DeepSeek analysis complete.

REM =========================================================================
echo.
echo =========================================================================
echo  STEP 4 of 5: RUNNING LENS PASS
echo =========================================================================
echo  Applying saved channel focus (clips, soft-spots, theology, etc.)
echo  Workers: !WORKERS! parallel calls
echo =========================================================================
echo.

pushd "%DS%"
for /f "usebackq eol=# delims=" %%C in ("WATCH_CHANNELS.txt") do (
    echo  --- Lenses: %%C ---
    python lens_pass.py "%SUBS%\%%C" --workers !WORKERS!
    echo.
)
popd

echo  [OK] Lens pass complete.

REM =========================================================================
echo.
echo =========================================================================
echo  STEP 5 of 5: REBUILDING CATALOG
echo =========================================================================
echo  Building channel overviews, debate pages, Excel + SQLite
echo =========================================================================
echo.

pushd "%DS%"
python build_catalog.py
popd

echo  [OK] Catalog rebuilt.

REM =========================================================================
echo.
echo =========================================================================
echo  PIPELINE COMPLETE
echo =========================================================================
echo.
echo  Raw transcripts:     %SUBS%
echo  Cleaned markdown:    %CLEAN%
echo  DeepSeek analysis:   %ANALYSIS%
echo  Catalog:             %ANALYSIS%\catalog.xlsx
echo.
echo  Channels watched:
pushd "%DS%"
if exist "WATCH_CHANNELS.txt" (
    for /f "usebackq eol=# delims=" %%C in ("WATCH_CHANNELS.txt") do echo    - %%C
)
popd
echo.
echo =========================================================================
pause


REM =========================================================================
:debate_scan
REM =========================================================================
echo.
echo =========================================================================
echo  DEBATE MAP SCANNER
echo  Scan transcripts against 80 apologetics questions
echo =========================================================================
echo.
echo  Enter the folder containing transcripts to scan:
echo  (drag and drop, or type the full path)
echo.
set "SCANDIR="
set /p "SCANDIR=  Folder: "
set "SCANDIR=!SCANDIR:"=!"

if not exist "!SCANDIR!" (
    echo  [ERROR] Folder not found: !SCANDIR!
    pause
    exit /b 1
)

REM Count files
set "SCAN_COUNT=0"
for %%f in ("!SCANDIR!\*.txt") do set /a SCAN_COUNT+=1
for %%f in ("!SCANDIR!\*.md") do set /a SCAN_COUNT+=1
for %%f in ("!SCANDIR!\*.json") do set /a SCAN_COUNT+=1
for %%f in ("!SCANDIR!\*.srt") do set /a SCAN_COUNT+=1
for %%f in ("!SCANDIR!\*.vtt") do set /a SCAN_COUNT+=1

echo.
echo  Found !SCAN_COUNT! transcript files.
echo.

if !SCAN_COUNT! EQU 0 (
    echo  [ERROR] No transcript files found.
    pause
    exit /b 1
)

set "SCAN_LIMIT="
set /p "SCAN_LIMIT=  How many to process? (number or 'all' for !SCAN_COUNT!): "
if /i "!SCAN_LIMIT!"=="all" set "SCAN_LIMIT=!SCAN_COUNT!"
if "!SCAN_LIMIT!"=="" set "SCAN_LIMIT=!SCAN_COUNT!"

echo.
echo  Select scan mode:
echo    1  Question Match  — which of the 80 questions does each video address?
echo    2  Framework Match — map to THE_STORY chapters + find physics-theology bridges
echo    3  Full Brief      — everything (question match + framework + steelman + action items)
echo    4  Raw Summary     — fast title/speaker/summary/tags only
echo.
set "SCAN_MODE="
set /p "SCAN_MODE=  Mode (1-4): "

if "!SCAN_MODE!"=="1" set "MODE_NAME=question_match"
if "!SCAN_MODE!"=="2" set "MODE_NAME=framework_extract"
if "!SCAN_MODE!"=="3" set "MODE_NAME=full_brief"
if "!SCAN_MODE!"=="4" set "MODE_NAME=raw_summary"

if not defined MODE_NAME (
    echo  [ERROR] Invalid mode.
    pause
    exit /b 1
)

set "TIMESTAMP=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%"
set "TIMESTAMP=!TIMESTAMP: =0!"
set "SCAN_OUT=!SCANDIR!\__DEBATE_SCAN_!TIMESTAMP!"
mkdir "!SCAN_OUT!" 2>nul

echo.
echo =========================================================================
echo  SCANNING !SCAN_LIMIT! of !SCAN_COUNT! transcripts
echo  Mode: !MODE_NAME!
echo  Output: !SCAN_OUT!
echo =========================================================================
echo.

set "SCAN_DONE=0"
set "SCAN_FAIL=0"

REM Build temp file list
set "SCAN_LIST=!SCAN_OUT!\__filelist.tmp"
(
    for %%f in ("!SCANDIR!\*.txt") do echo %%f
    for %%f in ("!SCANDIR!\*.md") do echo %%f
    for %%f in ("!SCANDIR!\*.json") do echo %%f
    for %%f in ("!SCANDIR!\*.srt") do echo %%f
    for %%f in ("!SCANDIR!\*.vtt") do echo %%f
) > "!SCAN_LIST!"

set "PROCESSOR=%~dp0youtube_processor.py"

for /f "usebackq delims=" %%f in ("!SCAN_LIST!") do (
    if !SCAN_DONE! LSS !SCAN_LIMIT! (
        set /a SCAN_DONE+=1
        echo  [!SCAN_DONE!/!SCAN_LIMIT!] %%~nxf

        "%PY%" "!PROCESSOR!" --file "%%f" --mode "!MODE_NAME!" --output "!SCAN_OUT!" 2>nul

        if errorlevel 1 (
            echo           [FAILED]
            set /a SCAN_FAIL+=1
        ) else (
            echo           [OK]
        )
    )
)

del "!SCAN_LIST!" 2>nul

REM Generate index
"%PY%" "!PROCESSOR!" --index "!SCAN_OUT!" 2>nul

set /a SCAN_OK=SCAN_DONE-SCAN_FAIL
echo.
echo =========================================================================
echo  DEBATE SCAN COMPLETE
echo =========================================================================
echo  Processed: !SCAN_DONE!
echo  OK:        !SCAN_OK!
echo  Failed:    !SCAN_FAIL!
echo  Output:    !SCAN_OUT!
echo =========================================================================
echo.
pause
