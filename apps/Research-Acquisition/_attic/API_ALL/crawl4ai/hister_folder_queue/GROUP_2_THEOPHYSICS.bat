@echo off
setlocal
title Hister - Theophysics Queue
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0HISTER_FOLDER_QUEUE.ps1" -GroupFile "%~dp0GROUP_2_THEOPHYSICS.txt"
echo.
echo Finished. The log and receipt are in: %~dp0logs
pause
