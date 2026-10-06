@echo off
title Theophysics Link Harvester
color 0E
echo.
echo  ================================================================
echo   THEOPHYSICS LINK HARVESTER — Setup ^& Run
echo  ================================================================
echo.

echo  [1] Checking Python...
python --version 2>nul
if errorlevel 1 (
    echo  [ERROR] Python not found!
    pause
    exit /b 1
)
echo       OK
echo.

cd /d "%~dp0"

echo  [2] Installing dependencies...
pip install requests beautifulsoup4 psycopg2-binary lxml -q 2>nul
echo       OK
echo.

echo  [3] Configuration check...
echo.
echo       Engine:   semantic_scholar (free, no key needed)
echo       Output:   harvested_links.md (in this folder)
echo       Database: PostgreSQL at 192.168.1.177:2665
echo                 (will fall back to markdown-only if DB is down)
echo.
echo       Edit harvester.py CONFIG section to change:
echo         - search_terms (what to search for)
echo         - engine (semantic_scholar, arxiv, duckduckgo, openalex)
echo         - direct_urls (pages to crawl for links)
echo         - fringe_boost_keywords (what scores higher)
echo.
echo  ================================================================
echo   READY — Press ENTER to start harvesting
echo   Or Ctrl+C to exit and edit config first
echo  ================================================================
pause

echo.
echo  [*] Starting harvester...
echo.
python harvester.py
echo.
echo  [*] Done. Check harvested_links.md for results.
echo.
pause
