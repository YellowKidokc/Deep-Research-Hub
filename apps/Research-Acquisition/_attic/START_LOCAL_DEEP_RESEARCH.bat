@echo off
title Local Deep Research - Choose Folder
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0gpt-researcher\START_GPT_RESEARCHER_CHOOSE_FOLDER.ps1"
if errorlevel 1 pause
