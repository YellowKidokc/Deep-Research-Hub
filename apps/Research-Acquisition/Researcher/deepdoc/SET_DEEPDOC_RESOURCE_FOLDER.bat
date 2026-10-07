@echo off
setlocal
cd /d "%~dp0"
set /p "RESOURCEFOLDER=Paste the full folder path to research recursively: "
if not defined RESOURCEFOLDER exit /b 1
if not exist ".venv\Scripts\python.exe" (
  echo DeepDoc is not set up yet. Run SETUP_DEEPDOC.bat first.
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" --resource-path "%RESOURCEFOLDER%"
if errorlevel 1 pause
