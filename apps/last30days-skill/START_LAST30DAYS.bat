@echo off
setlocal
title Last 30 Days Research
pushd "%~dp0"
set "L30_SAVE=C:\Users\David\Documents\Last30Days"
if not exist "%L30_SAVE%" mkdir "%L30_SAVE%"

where uv >nul 2>nul
if errorlevel 1 (
  echo ERROR: uv is not available on PATH.
  echo Install uv, then run this launcher again.
  pause
  popd
  exit /b 1
)

echo.
echo LAST 30 DAYS RESEARCH
echo ---------------------
set "L30_TOPIC="
set /p "L30_TOPIC=What topic should we research? "

if not defined L30_TOPIC (
  echo No topic entered. Nothing was run.
  pause
  popd
  exit /b 0
)

echo.
uv run python skills\last30days\scripts\last30days.py "%L30_TOPIC%" --emit=brief --save-dir "%L30_SAVE%"
set "L30_EXIT=%ERRORLEVEL%"

echo.
if "%L30_EXIT%"=="0" (
  echo Research run finished.
  echo Saved research location: %L30_SAVE%
) else (
  echo Research run failed with exit code %L30_EXIT%.
  echo Run LAST30DAYS_DOCTOR.bat for a source health report.
)
pause
popd
exit /b %L30_EXIT%
