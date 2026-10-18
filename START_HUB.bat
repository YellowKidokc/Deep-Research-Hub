@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Deep Research Hub Launcher
cd /d "%~dp0"

:menu
cls
echo ============================================================
echo   Deep Research Hub — Quick Launcher
echo ============================================================
echo.
echo   [1] OpenWriter  (writing app with Deep Research Hub plugin)
echo   [2] GPT Researcher  (interactive research UI)
echo   [3] GPT Researcher with Local Documents
echo   [4] Last 30 Days skill
echo   [5] Deep Research Queue (command line)
echo.
echo   [T] Troubleshoot Hub
echo   [U] Update Hub from GitHub
echo   [Q] Quit
echo.
echo ============================================================
set /p choice="Choice: "

if /i "%choice%"=="1" goto :openwriter
if /i "%choice%"=="2" goto :gptr
if /i "%choice%"=="3" goto :gptr_local
if /i "%choice%"=="4" goto :last30days
if /i "%choice%"=="5" goto :queue
if /i "%choice%"=="T" goto :troubleshoot
if /i "%choice%"=="U" goto :update
if /i "%choice%"=="Q" goto :eof

echo Invalid choice. Try again.
timeout /t 1 >nul
goto :menu

:openwriter
if not exist "apps\openwriter\START_OPENWRITER.bat" (
  echo ERROR: apps\openwriter\START_OPENWRITER.bat not found.
  pause
  goto :menu
)
call "apps\openwriter\START_OPENWRITER.bat"
goto :menu

:gptr
if not exist "apps\Research-Acquisition\Researcher\gpt-researcher\START_GPT_RESEARCHER.bat" (
  echo ERROR: GPT Researcher launcher not found.
  pause
  goto :menu
)
call "apps\Research-Acquisition\Researcher\gpt-researcher\START_GPT_RESEARCHER.bat"
goto :menu

:gptr_local
if not exist "apps\Research-Acquisition\Researcher\gpt-researcher\START_LOCAL_DOCUMENTS.bat" (
  echo ERROR: GPT Researcher local-doc launcher not found.
  pause
  goto :menu
)
call "apps\Research-Acquisition\Researcher\gpt-researcher\START_LOCAL_DOCUMENTS.bat"
goto :menu

:last30days
if not exist "apps\last30days-skill\START_LAST30DAYS.bat" (
  echo ERROR: Last 30 Days launcher not found.
  pause
  goto :menu
)
call "apps\last30days-skill\START_LAST30DAYS.bat"
goto :menu

:queue
echo.
echo Deep Research Queue: run all jobs in data/jobs
echo   python apps\Research-Acquisition\Researcher\gpt-researcher\drh_queue.py --jobs data\jobs --out data\deep_research --parallel 1
echo.
echo To change parallelism, edit the command above before running.
echo.
pause
goto :menu

:troubleshoot
if not exist "TROUBLESHOOT_HUB.bat" (
  echo ERROR: TROUBLESHOOT_HUB.bat not found.
  pause
  goto :menu
)
call "TROUBLESHOOT_HUB.bat"
goto :menu

:update
echo.
echo Pulling latest changes from GitHub...
git pull --ff-only
if errorlevel 1 (
  echo Update failed. See error above.
) else (
  echo Hub is up to date.
)
pause
goto :menu
