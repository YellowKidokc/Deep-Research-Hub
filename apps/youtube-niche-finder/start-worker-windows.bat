@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%backend"
echo Niche Finder background collector is running.
"%ROOT%.venv\Scripts\python.exe" worker.py
if errorlevel 1 (
  echo Collector stopped with an error.
  pause
  exit /b 1
)
