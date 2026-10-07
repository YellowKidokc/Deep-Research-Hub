@echo off
setlocal
cd /d "%~dp0"
set /p "DOCFOLDER=Paste the full folder path to research: "
if not defined DOCFOLDER exit /b 1
python "%~dp0windows_launcher.py" local --documents "%DOCFOLDER%"
if errorlevel 1 pause
