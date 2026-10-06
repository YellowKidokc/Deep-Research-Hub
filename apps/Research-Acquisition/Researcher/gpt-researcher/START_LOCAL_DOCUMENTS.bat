@echo off
setlocal
cd /d "%~dp0"
python "%~dp0windows_launcher.py" local
if errorlevel 1 pause
