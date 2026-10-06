@echo off
setlocal
title Hister - Desktop Pages Queue
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0HISTER_FOLDER_QUEUE.ps1" -GroupFile "%~dp0GROUP_1_DESKTOP_PAGES.txt"
echo.
echo Finished. The log and receipt are in: %~dp0logs
pause
