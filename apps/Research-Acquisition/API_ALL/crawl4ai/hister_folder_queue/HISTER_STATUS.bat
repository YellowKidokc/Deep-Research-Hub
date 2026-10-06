@echo off
setlocal
title Hister - Index and Crawl Status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0HISTER_FOLDER_QUEUE.ps1" -StatusOnly
echo.
pause
