@echo off
setlocal
cd /d "%~dp0"
python "%~dp0windows_launcher.py" standard
if errorlevel 1 pause
