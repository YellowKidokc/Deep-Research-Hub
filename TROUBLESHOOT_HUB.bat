@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Deep Research Hub — Troubleshoot
cd /d "%~dp0"

:menu
cls
echo ============================================================
echo   Deep Research Hub — Troubleshooting Doctor
echo ============================================================
echo.
echo   [1] Run full diagnostic scan
echo   [2] Check ports (8000, 5050) and list occupiers
echo   [3] Change OpenWriter port
echo   [4] Install / update OpenWriter dependencies and build
echo   [5] Install / update GPT Researcher Python environment
echo   [6] Pull latest Hub updates from GitHub
echo   [7] Show git status and last commits
echo   [8] Open runtime logs folder
echo.
echo   [Q] Quit
echo.
echo ============================================================
set /p choice="Choice: "

if /i "%choice%"=="1" goto :full_scan
if /i "%choice%"=="2" goto :port_check
if /i "%choice%"=="3" goto :change_port
if /i "%choice%"=="4" goto :update_openwriter
if /i "%choice%"=="5" goto :update_gptr
if /i "%choice%"=="6" goto :git_pull
if /i "%choice%"=="7" goto :git_status
if /i "%choice%"=="8" goto :open_logs
if /i "%choice%"=="Q" goto :eof

echo Invalid choice.
timeout /t 1 >nul
goto :menu

:full_scan
echo.
echo --- Environment ---
call :check_tool git
if !tool_ok!==1 (
  git --version
  git config --get remote.origin.url 2>nul
)
call :check_tool node
if !tool_ok!==1 node --version
call :check_tool npm
if !tool_ok!==1 npm --version
call :check_tool python
if !tool_ok!==1 python --version
call :check_tool uv
if !tool_ok!==1 uv --version
call :check_tool npx
if !tool_ok!==1 npx --version

echo.
echo --- Hub folders ---
if exist "apps\openwriter" (echo OK: apps\openwriter) else (echo MISSING: apps\openwriter)
if exist "apps\Research-Acquisition\Researcher\gpt-researcher" (echo OK: apps\Research-Acquisition\Researcher\gpt-researcher) else (echo MISSING: GPT Researcher)
if exist "data\jobs" (echo OK: data\jobs) else (echo MISSING: data\jobs)
if exist "prompts\W_story_checklist.json" (echo OK: prompts) else (echo MISSING: prompts)

echo.
echo --- Ports ---
call :port_status 8000 "GPT Researcher"
call :port_status 5050 "OpenWriter"

echo.
echo --- OpenWriter build ---
if exist "apps\openwriter\packages\openwriter\dist\bin\pad.js" (
  echo OK: OpenWriter is built
) else (
  echo MISSING: OpenWriter build ^(run option 4^)
)

echo.
echo --- GPT Researcher venv ---
if exist "apps\Research-Acquisition\Researcher\gpt-researcher\.venv\Scripts\python.exe" (
  echo OK: GPT Researcher venv exists
) else (
  echo MISSING: GPT Researcher venv ^(run option 5^)
)

echo.
echo --- Key env vars ---
if defined OPENROUTER_API_KEY (echo OK: OPENROUTER_API_KEY set) else (echo NOT SET: OPENROUTER_API_KEY)
if defined DEEPSEEK_API_KEY (echo OK: DEEPSEEK_API_KEY set) else (echo NOT SET: DEEPSEEK_API_KEY)
if defined ANTHROPIC_API_KEY (echo OK: ANTHROPIC_API_KEY set) else (echo NOT SET: ANTHROPIC_API_KEY)
if defined TAVILY_API_KEY (echo OK: TAVILY_API_KEY set) else (echo NOT SET: TAVILY_API_KEY)

echo.
pause
goto :menu

:port_check
echo.
call :port_status 8000 "GPT Researcher"
call :port_status 5050 "OpenWriter"
echo.
echo To see which process owns a port, run as Administrator:
echo   netstat -ano ^| findstr :8000
echo Then: taskkill /PID ^<PID^> /F
echo.
pause
goto :menu

:change_port
echo.
echo OpenWriter currently uses port 5050 (set in START_OPENWRITER.bat).
echo GPT Researcher currently uses port 8000 (set in windows_launcher.py).
echo.
echo To change OpenWriter's port, edit apps\openwriter\START_OPENWRITER.bat
echo and replace 5050 with your desired port, then save.
echo.
echo To change GPT Researcher's port, edit
echo   apps\Research-Acquisition\Researcher\gpt-researcher\windows_launcher.py
echo and replace both occurrences of 8000 with your desired port, then save.
echo.
start "" notepad "apps\openwriter\START_OPENWRITER.bat"
start "" notepad "apps\Research-Acquisition\Researcher\gpt-researcher\windows_launcher.py"
pause
goto :menu

:update_openwriter
echo.
echo Updating OpenWriter dependencies and rebuilding...
cd /d "%~dp0apps\openwriter"
if not exist package.json (
  echo ERROR: apps\openwriter\package.json not found.
  pause
  goto :menu_root
)
npm install
if errorlevel 1 (
  echo npm install failed.
  pause
  goto :menu_root
)
npm run build
if errorlevel 1 (
  echo Build failed.
  pause
  goto :menu_root
)
echo OpenWriter updated and rebuilt.
pause
goto :menu_root

:update_gptr
echo.
echo Setting up GPT Researcher Python environment...
cd /d "%~dp0apps\Research-Acquisition\Researcher\gpt-researcher"
if exist "setup.py" (
  python -m pip install -e .
) else if exist "pyproject.toml" (
  python -m pip install -e "."
) else (
  echo No setup.py or pyproject.toml found. Skipping package install.
)
if exist requirements.txt (
  python -m pip install -r requirements.txt
) else (
  echo No requirements.txt found.
)
echo GPT Researcher environment updated.
pause
goto :menu_root

:git_pull
echo.
cd /d "%~dp0"
git pull --ff-only
if errorlevel 1 (
  echo Pull failed. You may have uncommitted local changes.
) else (
  echo Pull succeeded.
)
pause
goto :menu_root

:git_status
echo.
cd /d "%~dp0"
echo --- Git status ---
git status --short
echo.
echo --- Last 5 commits ---
git log --oneline -5
echo.
pause
goto :menu_root

:open_logs
echo.
start "" "apps\Research-Acquisition\Researcher\gpt-researcher\.runtime"
pause
goto :menu_root

:menu_root
cd /d "%~dp0"
goto :menu

:check_tool
set "tool_ok=0"
where %~1 >nul 2>nul
if errorlevel 1 (
  echo MISSING: %~1 is not on PATH
) else (
  set "tool_ok=1"
)
exit /b 0

:port_status
set "port=%~1"
set "name=%~2"
powershell -Command "(New-Object System.Net.Sockets.TcpClient).ConnectAsync('127.0.0.1', %port%).Wait(500)" >nul 2>nul
if errorlevel 1 (
  echo OK: Port %port% is free ^(%name%^)
) else (
  echo IN USE: Port %port% is occupied ^(%name%^)
)
exit /b 0
