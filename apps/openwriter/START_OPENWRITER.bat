@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo Starting OpenWriter with the Deep Research Hub plugin
echo ============================================================
echo.

REM The app must be built first: npm install ^&^& npm run build
if not exist "%~dp0packages\openwriter\dist\bin\pad.js" (
  echo ERROR: OpenWriter has not been built yet.
  echo   packages\openwriter\dist\bin\pad.js was not found.
  echo.
  echo Run this once first, from the apps\openwriter folder:
  echo   npm install ^&^& npm run build
  echo.
  pause
  exit /b 1
)

node "%~dp0packages\openwriter\dist\bin\pad.js" --port 5050 --plugins @openwriter/plugin-drh
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ============================================================
if "%EXIT_CODE%"=="0" (
  echo OpenWriter closed normally.
) else (
  echo OpenWriter stopped with error code %EXIT_CODE%.
)
echo ============================================================
pause
exit /b %EXIT_CODE%
