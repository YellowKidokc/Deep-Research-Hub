@echo off
setlocal

REM Purpose: Launch a respectful Wikipedia crawl using Crawl4AI and save markdown plus discovered links.
REM Date: 2026-04-05

cd /d D:\GitHub\crawl4ai

set "PYTHON_EXE=C:\Users\lowes\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo Starting Wikipedia ripper...
echo.
echo Seeds:
echo   https://en.wikipedia.org/wiki/List_of_conspiracy_theories
echo   https://en.wikipedia.org/wiki/MKUltra
echo   https://en.wikipedia.org/wiki/Jeffrey_Epstein
echo.
echo Output will be written under:
echo   D:\GitHub\crawl4ai\crawl4ai_downloads\wikipedia_rip_YYYYMMDD_HHMMSS
echo.

"%PYTHON_EXE%" wikipedia_ripper.py %*

echo.
echo Done.
pause
