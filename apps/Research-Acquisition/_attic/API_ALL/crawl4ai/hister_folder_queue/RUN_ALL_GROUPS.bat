@echo off
setlocal
title Hister - All Folder Groups

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0HISTER_FOLDER_QUEUE.ps1" -GroupFile "%~dp0GROUP_1_DESKTOP_PAGES.txt"
if errorlevel 1 echo Group 1 reported an error. Continuing to Group 2.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0HISTER_FOLDER_QUEUE.ps1" -GroupFile "%~dp0GROUP_2_THEOPHYSICS.txt"
if errorlevel 1 exit /b 1
exit /b 0
