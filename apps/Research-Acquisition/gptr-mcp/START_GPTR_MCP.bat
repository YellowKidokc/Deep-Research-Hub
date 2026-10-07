@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
cd /d "%ROOT%"

for /f "usebackq delims=" %%K in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')"`) do set "DEEPSEEK_API_KEY=%%K"
for /f "usebackq delims=" %%K in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('TAVILY_API_KEY','User')"`) do set "TAVILY_API_KEY=%%K"

if not exist "%PY%" (
  echo [FAIL] Python environment missing. Re-run the MCP installation.
  exit /b 1
)
if "%DEEPSEEK_API_KEY%"=="" (
  echo [FAIL] DEEPSEEK_API_KEY is not set in the Windows user environment.
  exit /b 1
)
if "%TAVILY_API_KEY%"=="" (
  echo [FAIL] TAVILY_API_KEY is not set in the Windows user environment.
  exit /b 1
)

"%PY%" "%ROOT%server.py"
