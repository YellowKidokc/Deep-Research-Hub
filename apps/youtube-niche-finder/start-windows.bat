@echo off
setlocal
set "ROOT=%~dp0"
set "PG=C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe"
set "PY=%ROOT%.venv\Scripts\python.exe"
set "DATA=%ROOT%data\postgres"

if not exist "%PY%" (
  echo Python environment missing. Run: py -3.12 -m venv .venv
  echo Then run: .venv\Scripts\python.exe -m pip install -r backend\requirements-windows.txt
  pause
  exit /b 1
)
if not exist "%PG%" (
  echo PostgreSQL 17 was not found at %PG%
  pause
  exit /b 1
)
if not exist "%ROOT%.env" (
  echo Configuration missing: %ROOT%.env
  pause
  exit /b 1
)
if not exist "%DATA%\PG_VERSION" (
  echo Project database missing: %DATA%
  pause
  exit /b 1
)

"%PG%" -D "%DATA%" status >nul 2>&1
if errorlevel 1 (
  "%PG%" -D "%DATA%" -l "%ROOT%data\postgres.log" -o "-p 55433 -h 127.0.0.1" start
  if errorlevel 1 (
    echo PostgreSQL failed to start. See data\postgres.log
    pause
    exit /b 1
  )
)

cd /d "%ROOT%backend"
set "HAS_YOUTUBE_KEY="
for /f "usebackq tokens=1,* delims==" %%A in ("%ROOT%.env") do (
  if /I "%%A"=="YOUTUBE_API_KEY" if not "%%B"=="" set "HAS_YOUTUBE_KEY=1"
)
if defined HAS_YOUTUBE_KEY (
  start "Niche Finder Collector" "%ROOT%start-worker-windows.bat"
) else (
  echo YouTube collection is paused until YOUTUBE_API_KEY is filled in .env.
)
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
  start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --new-window "http://127.0.0.1:8080/"
) else (
  start "" "http://127.0.0.1:8080/"
)
echo Dashboard: http://127.0.0.1:8080
echo Press Ctrl+C to stop the web server.
"%PY%" -m uvicorn api:app --host 127.0.0.1 --port 8080
if errorlevel 1 (
  echo Web server stopped with an error.
  pause
  exit /b 1
)
