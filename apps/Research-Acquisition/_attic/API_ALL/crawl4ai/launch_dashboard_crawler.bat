@echo off
setlocal enabledelayedexpansion

:: Dashboard Batch Crawler Launcher

echo ============================================================
echo    Dashboard Analytics Batch Crawler
echo ============================================================
echo.

:: Check if dashboard_urls.txt exists
if not exist "dashboard_urls.txt" (
    echo ERROR: dashboard_urls.txt not found!
    echo.
    echo Creating template file...
    echo # Dashboard URLs to Crawl > dashboard_urls.txt
    echo # Add one URL per line >> dashboard_urls.txt
    echo # Lines starting with # are comments >> dashboard_urls.txt
    echo. >> dashboard_urls.txt
    echo Template created: dashboard_urls.txt
    echo Please add your dashboard URLs to this file and run again.
    echo.
    pause
    exit /b 1
)

:: Count URLs in file
set count=0
for /f "usebackq tokens=*" %%a in ("dashboard_urls.txt") do (
    set "line=%%a"
    if not "!line:~0,1!"=="#" (
        if not "!line!"=="" (
            set /a count+=1
        )
    )
)

echo Found %count% dashboard URLs to crawl
echo.

if %count%==0 (
    echo ERROR: No URLs found in dashboard_urls.txt
    echo Please add dashboard URLs to the file.
    echo.
    pause
    exit /b 1
)

echo Options:
echo   1. Use default settings (dashboard_analytics folder)
echo   2. Specify custom output directory
echo   3. Exit
echo.

set /p choice="Enter choice (1-3): "

if "%choice%"=="3" goto end
if "%choice%"=="2" goto custom_dir

:default_dir
set output_dir=dashboard_analytics
goto start_crawl

:custom_dir
echo.
set /p output_dir="Enter output directory name: "
if "%output_dir%"=="" set output_dir=dashboard_analytics

:start_crawl
echo.
echo ============================================================
echo    Starting Dashboard Crawl
echo ============================================================
echo.
echo Dashboards to crawl: %count%
echo Output directory: %output_dir%
echo.
echo This will take approximately %count% minutes (1 min per dashboard)
echo Press Ctrl+C to cancel, or
pause

echo.
echo Starting crawl...
echo.

python dashboard_crawler.py dashboard_urls.txt "%output_dir%"

echo.
echo ============================================================
echo    Crawl Complete!
echo ============================================================
echo.
echo Results saved to: %output_dir%
echo.

set /p open_folder="Open output folder? (y/n): "
if /i "%open_folder%"=="y" (
    start "" "%output_dir%"
)

:end
echo.
pause
