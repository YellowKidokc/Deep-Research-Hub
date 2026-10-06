@echo off
setlocal
title Last 30 Days - Source Doctor
pushd "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
  echo ERROR: uv is not available on PATH.
  pause
  popd
  exit /b 1
)

echo Checking Last 30 Days sources and configuration...
echo.
uv run python skills\last30days\scripts\last30days.py doctor
set "L30_EXIT=%ERRORLEVEL%"

echo.
pause
popd
exit /b %L30_EXIT%
