@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Deep Research Hub — Generate Debate Map Assets
pushd "%~dp0"

echo ============================================================
echo   Generate DEBATE_MAP assets from a source file
echo ============================================================
echo.
echo This runs the D_debate_map API slot set:
echo   1 = claims      -^> 01_CLAIMS
echo   2 = evidence    -^> 02_EVIDENCE
echo   3 = script      -^> 05_SCRIPTS
echo   4 = short       -^> 06_SHORTS
echo   5 = rebuttals   -^> 07_REBUTTALS
echo.

if "%~1"=="" (
  set /p source="Path to source markdown file: "
) else (
  set "source=%~1"
)
if not exist "%source%" (
  echo ERROR: source file not found: %source%
  pause
  exit /b 1
)

if "%~2"=="" (
  set /p question="Path to target question folder (e.g. ..\DEBATE_MAP\02_S-MORAL_Morality\Q-MORAL-OBJECTIVE): "
) else (
  set "question=%~2"
)
if not exist "%question%" (
  echo ERROR: question folder not found: %question%
  pause
  exit /b 1
)

if "%DEEPSEEK_API_KEY%"=="" (
  echo ERROR: DEEPSEEK_API_KEY is not set.
  echo   Set it before running this script, e.g.
  echo   set DEEPSEEK_API_KEY=sk-...
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: python is not available on PATH.
  pause
  exit /b 1
)

for %%d in (01_CLAIMS 02_EVIDENCE 05_SCRIPTS 06_SHORTS 07_REBUTTALS) do (
  if not exist "%question%\%%d" mkdir "%question%\%%d"
)

echo.
echo Generating assets for: %question%
echo.

python prompts\run_slot.py D 1 --file "%source%" --out "%question%\01_CLAIMS\extracted_claims.md"
python prompts\run_slot.py D 2 --file "%source%" --out "%question%\02_EVIDENCE\extracted_evidence.md"
python prompts\run_slot.py D 3 --file "%source%" --out "%question%\05_SCRIPTS\youtube_script.md"
python prompts\run_slot.py D 4 --file "%source%" --out "%question%\06_SHORTS\short_script.md"
python prompts\run_slot.py D 5 --file "%source%" --out "%question%\07_REBUTTALS\rebuttals.md"

echo.
echo Done. Check the subfolders in: %question%
echo.
pause
popd
