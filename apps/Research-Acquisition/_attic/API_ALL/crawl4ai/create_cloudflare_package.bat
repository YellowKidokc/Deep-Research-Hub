@echo off
echo ============================================================
echo    Cloudflare Deployment Package Creator
echo    HTML Dashboard + RSS Feed
echo ============================================================
echo.

set /p analytics_dir="Analytics directory (default: Trinity_paper_dashboards): "
if "%analytics_dir%"=="" set analytics_dir=Trinity_paper_dashboards

set /p cloudflare_url="Cloudflare Pages URL (default: https://theophysics.pages.dev): "
if "%cloudflare_url%"=="" set cloudflare_url=https://theophysics.pages.dev

echo.
echo ============================================================
echo    Step 1: Generating RSS Feed
echo ============================================================
echo.

python generate_rss_feed.py "%analytics_dir%\Trinity_Analytics.xlsx" "%analytics_dir%\feed.xml" "%cloudflare_url%"

if errorlevel 1 (
    echo Error generating RSS feed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    Step 2: Updating HTML with RSS Link
echo ============================================================
echo.

python update_html_with_rss.py "%analytics_dir%\Trinity_Dashboard.html" "%cloudflare_url%/feed.xml"

if errorlevel 1 (
    echo Error updating HTML!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    PACKAGE READY FOR CLOUDFLARE!
echo ============================================================
echo.
echo Files prepared in: %analytics_dir%
echo.
echo Files to upload:
echo   - Trinity_Dashboard.html (main dashboard)
echo   - feed.xml (RSS feed for Substack)
echo   - All *_dashboard.md files (individual papers)
echo   - 00_MASTER_INDEX.md (index)
echo.
echo Cloudflare Pages Deployment:
echo   1. Go to Cloudflare Pages dashboard
echo   2. Create new project or update existing
echo   3. Upload the entire %analytics_dir% folder
echo   4. Your RSS feed will be at: %cloudflare_url%/feed.xml
echo.
echo Password Protection (Optional):
echo   See CLOUDFLARE_PASSWORD_SETUP.md for detailed instructions
echo   Recommended: Use Cloudflare Access with One-Time PIN
echo   - Protect: /_paper_analytics/* (dashboards)
echo   - Leave public: /feed.xml (for Substack RSS import)
echo.
echo Substack Import:
echo   1. Go to Substack Settings ^> Import
echo   2. Choose "Import from RSS"
echo   3. Enter: %cloudflare_url%/feed.xml
echo   4. Substack will import all papers as posts
echo.

set /p open_folder="Open analytics folder? (y/n): "
if /i "%open_folder%"=="y" start "" "%analytics_dir%"

set /p open_html="Open HTML dashboard to preview? (y/n): "
if /i "%open_html%"=="y" start "" "%analytics_dir%\Trinity_Dashboard.html"

set /p open_rss="Open RSS feed to preview? (y/n): "
if /i "%open_rss%"=="y" start "" "%analytics_dir%\feed.xml"

echo.
pause
