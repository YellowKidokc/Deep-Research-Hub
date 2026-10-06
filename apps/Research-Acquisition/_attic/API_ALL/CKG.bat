@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title CKG Analysis — YouTube Transcripts

set "REPO=D:\GitHub\Research-Acquisition\yt-transcript-downloader"
set "SUBS=%REPO%\subtitles"
set "DS=%REPO%\pipeline-workflows\deepseek-home"
set "PY=%REPO%\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo =========================================================================
echo  CKG ANALYSIS — YouTube Transcript Processing
echo =========================================================================
echo.
echo  This runs the baseline CKG argument extraction on transcripts,
echo  then optionally adds a focus layer (theology, physics, etc.)
echo  on top. Output is one note per video with everything stacked.
echo.
echo =========================================================================

REM =========================================================================
REM  STEP 1: Pick the folder
REM =========================================================================
echo.
echo  Available channels in subtitles\:
echo  ---------------------------------
set "CHNUM=0"
for /d %%D in ("%SUBS%\*") do (
    set /a CHNUM+=1
    set "CH_!CHNUM!=%%~nxD"
    
    REM count files in the channel
    set "FCOUNT=0"
    for %%F in ("%%D\*.md") do set /a FCOUNT+=1
    echo    !CHNUM!. %%~nxD  (!FCOUNT! transcripts^)
)
echo.
echo  Or type a full path to a folder of transcripts.
echo.

set "PICK="
set /p "PICK=  Pick a number or paste a path: "

REM check if it's a number
set "FOLDER="
for /l %%N in (1,1,%CHNUM%) do (
    if "!PICK!"=="%%N" set "FOLDER=%SUBS%\!CH_%%N!"
)
REM if not a number, treat as a path
if not defined FOLDER (
    if exist "!PICK!" (
        set "FOLDER=!PICK!"
    ) else (
        echo  Folder not found: !PICK!
        pause
        exit /b 1
    )
)

REM count transcripts in chosen folder
set "TOTAL=0"
for %%F in ("!FOLDER!\*.md") do (
    if not "%%~nxF"=="_CHANNEL_OVERVIEW.md" set /a TOTAL+=1
)

for %%I in ("!FOLDER!") do set "CHNAME=%%~nxI"

echo.
echo =========================================================================
echo  Selected: !CHNAME!
echo  Transcripts: !TOTAL!
echo =========================================================================

REM =========================================================================
REM  STEP 2: How many?
REM =========================================================================
echo.
set "LIMIT=!TOTAL!"
set /p "LIMIT=  How many to process? [!TOTAL! = all]: "
if "!LIMIT!"=="" set "LIMIT=!TOTAL!"
if /i "!LIMIT!"=="all" set "LIMIT=!TOTAL!"

REM =========================================================================
REM  STEP 3: Workers
REM =========================================================================
echo.
set "WORKERS=30"
set /p "WORKERS=  Parallel workers? [30]: "
if "!WORKERS!"=="" set "WORKERS=30"

REM =========================================================================
REM  STEP 4: Clean transcripts for analysis
REM =========================================================================
echo.
echo =========================================================================
echo  CLEANING TRANSCRIPTS FOR ANALYSIS
echo =========================================================================
echo  Converting raw auto-captions to punctuated, readable markdown
echo  Source:  !FOLDER!
echo  Output:  %REPO%\obsidian_transcripts\!CHNAME!
echo  (Local Python only — no API calls, no tokens burned)
echo =========================================================================
echo.

pushd "%REPO%\Python Clean Library"
"%PY%" clean_library.py --src "%SUBS%" --out "%REPO%\obsidian_transcripts" --channel "!CHNAME!" --punctuate
if errorlevel 1 (
    echo.
    echo  [WARNING] Cleaning had issues. Check output above.
) else (
    echo.
    echo  [OK] Cleaning complete.
)
popd

REM =========================================================================
REM  STEP 5: Run CKG baseline
REM =========================================================================
echo.
echo =========================================================================
echo  RUNNING CKG BASELINE ANALYSIS (Step 5 of 7)
echo =========================================================================
echo  Channel:     !CHNAME!
echo  Transcripts: !LIMIT! of !TOTAL!
echo  Workers:     !WORKERS! parallel calls
echo  Model:       deepseek-chat
echo  Job:         Extract arguments, debates, stories, claims,
echo               objections, evidence, people, scripture references
echo =========================================================================
echo.

pushd "%DS%"
python index_video.py "!FOLDER!" --workers !WORKERS! --limit !LIMIT!
if errorlevel 1 (
    echo.
    echo  [WARNING] CKG analysis had issues. Check output above.
) else (
    echo.
    echo  [OK] CKG baseline complete.
)
popd

REM =========================================================================
REM  STEP 5: Add a focus layer?
REM =========================================================================
echo.
echo =========================================================================
echo  FOCUS LAYER (optional)
echo =========================================================================
echo.
echo  Want to add a focus layer on top of the CKG baseline?
echo  This adds a second analysis pass looking through a specific lens.
echo.
echo    C  Christianity / teaching (scripture, stories, theology)
echo    S  Science and Theophysics (master equation, predictions, evidence)
echo    A  Arguments deep-dive (objections, soft-spots, fact-check)
echo    W  One-world / conspiracy claims
echo    K  Content and clips (best moments, quotes, clips)
echo    T  Type your own custom focus
echo    N  No — skip the focus layer
echo.

set "LAYER="
set /p "LAYER=  Pick a layer (C/S/A/W/K/T/N): "

if /i "!LAYER!"=="N" goto :step_catalog
if /i "!LAYER!"=="T" goto :custom_focus

REM validate the layer letter
echo CCSAWWKK | findstr /i "!LAYER!" >nul
if errorlevel 1 (
    echo  Unknown layer. Skipping.
    goto :step_catalog
)

echo.
echo =========================================================================
echo  RUNNING FOCUS LAYER: !LAYER!
echo =========================================================================
echo  Channel:  !CHNAME!
echo  Workers:  !WORKERS! parallel calls
echo =========================================================================
echo.

pushd "%DS%"

REM look up the lens numbers for this layer from layers.json
set "LNUMS="
for /f "usebackq delims=" %%L in (`python -c "import json; d=json.load(open('layers.json')); layer=d.get('!LAYER!'.upper(),{}); print(','.join(str(x) for x in layer.get('focus',[])))"`) do set "LNUMS=%%L"

if "!LNUMS!"=="" (
    echo  Could not find layer !LAYER! in layers.json. Skipping.
    popd
    goto :step_catalog
)

echo  Lens numbers: !LNUMS!
echo.

python lens_pass.py "!FOLDER!" --workers !WORKERS! --limit !LIMIT! --lens !LNUMS!
if errorlevel 1 (
    echo.
    echo  [WARNING] Focus layer had issues. Check output above.
) else (
    echo.
    echo  [OK] Focus layer complete.
)
popd
goto :step_render

:custom_focus
echo.
set "CUSTOM="
set /p "CUSTOM=  What should it focus on? "
if "!CUSTOM!"=="" (
    echo  No focus entered. Skipping.
    goto :step_catalog
)

echo.
echo =========================================================================
echo  RUNNING CUSTOM FOCUS
echo =========================================================================
echo  Focus:    !CUSTOM!
echo  Channel:  !CHNAME!
echo  Workers:  !WORKERS! parallel calls
echo =========================================================================
echo.

pushd "%DS%"
python lens_pass.py "!FOLDER!" --workers !WORKERS! --limit !LIMIT! --ask "!CUSTOM!"
if errorlevel 1 (
    echo.
    echo  [WARNING] Custom focus had issues. Check output above.
) else (
    echo.
    echo  [OK] Custom focus complete.
)
popd

:step_render
REM =========================================================================
REM  Re-render notes so lens sections appear in the Obsidian note
REM =========================================================================
echo.
echo  Re-rendering notes (adding focus layer to the CKG notes)...
pushd "%DS%"
python index_video.py "!FOLDER!" --render-only --limit !LIMIT! >nul
echo  [OK] Notes updated — CKG + focus layer + transcript, all on one page.
popd

:step_catalog
REM =========================================================================
REM  Rebuild catalog
REM =========================================================================
echo.
echo =========================================================================
echo  REBUILDING CATALOG
echo =========================================================================
echo  Channel overviews, debate pages, Excel + SQLite...
echo.

pushd "%DS%"
python build_catalog.py
echo.
echo  [OK] Catalog rebuilt.
popd

REM =========================================================================
echo.
echo =========================================================================
echo  COMPLETE
echo =========================================================================
echo.
echo  Channel:       !CHNAME!
echo  Processed:     !LIMIT! transcripts
echo  CKG baseline:  arguments, debates, stories, claims
if /i not "!LAYER!"=="N" if defined LAYER echo  Focus layer:   !LAYER!
echo.
echo  Output note per video (stacked top to bottom):
echo    1. Argument overview + debate map
echo    2. Best arguments for David
echo    3. Argument catalog (all arguments)
echo    4. Focus layer findings (if selected)
echo    5. People, places, things, scripture
echo    6. Original transcript
echo.
echo  Notes:    %REPO%\deepseek_arguments_analysis\!CHNAME!\
echo  Catalog:  %REPO%\deepseek_arguments_analysis\catalog.xlsx
echo.
echo =========================================================================
pause
