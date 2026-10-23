@echo off
REM Watches subtitles\ and cleans each channel into obsidian_transcripts\
REM once no new transcripts have arrived for 10 minutes. Leave this window open.
cd /d "%~dp0"
title Subtitle Watcher
set "PY=python"
if exist venv\Scripts\python.exe set "PY=venv\Scripts\python.exe"
"%PY%" watch_subtitles.py --catch-up %*
pause
