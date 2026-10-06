@echo off
title Text Cleanup — Server + Hotkey
echo ============================================
echo  Text Cleanup (Ctrl+Space)
echo  Starting server + AHK hotkey...
echo ============================================
echo.

cd /d "%~dp0"

:: SET YOUR DEEPSEEK API KEY HERE
set DEEPSEEK_API_KEY=sk-PASTE-YOUR-KEY-HERE

:: Start AHK hotkey script
start "" "C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe" "%~dp0TextCleanup.ahk"

:: Start server (stays in foreground so you see errors)
echo Starting cleanup server on port 10790...
python text_cleanup_server.py
