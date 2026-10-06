@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

:: Use this folder's venv (it has all crawl4ai packages); fall back to system Python.
set "PY=python"
if exist "%~dp0venv\Scripts\python.exe" set "PY=%~dp0venv\Scripts\python.exe"

:: Crawl4AI Launcher
:: Quick launcher for web crawling tasks

echo ============================================================
echo    Crawl4AI Quick Launcher
echo ============================================================
echo.

echo Select crawling mode:
echo.
echo   1. Search Web - Find specific content (continuous search)
echo   2. Download Entire Website (recursive crawl)
echo   3. Single Page Download
echo   4. Exit
echo.

set /p mode="Enter choice (1-4): "

if "%mode%"=="1" goto search_mode
if "%mode%"=="2" goto website_mode
if "%mode%"=="3" goto single_mode
if "%mode%"=="4" goto end

echo Invalid choice. Exiting.
goto end

:search_mode
echo.
echo ============================================================
echo    Search Web Mode
echo ============================================================
echo.
set /p search_query="Enter search query: "
set /p max_results="Maximum results to find (default: 50): "
if "%max_results%"=="" set max_results=50

set /p output_dir="Output directory (default: search_results): "
if "%output_dir%"=="" set output_dir=search_results

echo.
echo Starting web search for: %search_query%
echo Maximum results: %max_results%
echo Output: %output_dir%
echo.
echo Press Ctrl+C to stop searching...
echo.

"%PY%" search_crawler.py "%search_query%" %max_results% "%output_dir%"
goto end

:website_mode
echo.
echo ============================================================
echo    Download Entire Website Mode
echo ============================================================
echo.
set /p website_url="Enter website URL: "
set /p max_depth="Maximum depth (default: 3): "
if "%max_depth%"=="" set max_depth=3

set /p output_dir="Output directory (default: website_download): "
if "%output_dir%"=="" set output_dir=website_download

set "scope=section"
set "whole_site="
set /p whole_site="Stay inside this section of the site? (Y/n - n crawls the whole domain): "
if /i "%whole_site%"=="n" set "scope=site"

echo.
echo Downloading entire website: %website_url%
echo Maximum depth: %max_depth%
echo Scope: %scope%
echo Output: %output_dir%
echo.
echo This may take a while...
echo.

"%PY%" website_crawler.py "%website_url%" %max_depth% "%output_dir%" %scope%
goto end

:single_mode
echo.
echo ============================================================
echo    Single Page Download Mode
echo ============================================================
echo.
set /p page_url="Enter page URL: "
set /p output_dir="Output directory (default: single_page): "
if "%output_dir%"=="" set output_dir=single_page

echo.
echo Downloading: %page_url%
echo Output: %output_dir%
echo.

"%PY%" single_page_crawler.py "%page_url%" "%output_dir%"
goto end

:end
echo.
echo Done!
pause
