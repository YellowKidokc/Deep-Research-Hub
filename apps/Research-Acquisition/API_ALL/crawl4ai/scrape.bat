@echo off
REM ============================================================
REM SCRAPE-TO-MARKDOWN — Batch Downloader
REM Reads URLs from scrape.md, downloads each as clean markdown
REM Drop this in D:\crawl4ai\ alongside scrape.md
REM ============================================================
REM Requirements: Python 3.10+ with crawl4ai installed
REM   pip install crawl4ai
REM   crawl4ai-setup (first time only — installs Playwright browsers)
REM
REM If crawl4ai isn't installed, falls back to trafilatura
REM   pip install trafilatura
REM ============================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "SCRAPE_FILE=%SCRIPT_DIR%scrape.md"
set "OUTPUT_DIR=%SCRIPT_DIR%output"
set "LOG_FILE=%SCRIPT_DIR%scrape_log.txt"

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo ============================================================ > "%LOG_FILE%"
echo SCRAPE RUN: %date% %time% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"
echo.
echo Starting scrape run: %date% %time%
echo Reading URLs from: %SCRAPE_FILE%
echo Output directory:   %OUTPUT_DIR%
echo.

REM Run the Python scraper
python "%SCRIPT_DIR%scraper.py" "%SCRAPE_FILE%" "%OUTPUT_DIR%" "%LOG_FILE%"

echo.
echo ============================================================
echo Scrape complete. Check %OUTPUT_DIR% for markdown files.
echo Log saved to %LOG_FILE%
echo ============================================================
pause
