@echo off
echo ============================================================
echo    Complete Analytics Package Creator
echo    Dashboards + Excel + HTML + RSS + Interactive Tables
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

echo.
echo ============================================================
echo    Step 2: Updating HTML Dashboard with RSS
echo ============================================================
echo.

python update_html_with_rss.py "%analytics_dir%\Trinity_Dashboard.html" "%cloudflare_url%/feed.xml"

echo.
echo ============================================================
echo    Step 3: Creating Interactive Data Tables
echo ============================================================
echo.

python excel_to_interactive_tables.py "%analytics_dir%\Trinity_Analytics.xlsx" "%analytics_dir%\Trinity_Data_Tables.html"

echo.
echo ============================================================
echo    COMPLETE PACKAGE READY!
echo ============================================================
echo.
echo Files created in: %analytics_dir%
echo.
echo Files to upload to Cloudflare:
echo   1. Trinity_Dashboard.html - Main analytics dashboard
echo   2. Trinity_Data_Tables.html - Interactive data tables (NEW!)
echo   3. feed.xml - RSS feed for Substack
echo   4. Trinity_Analytics.xlsx - Excel file
echo   5. All *_dashboard.md files
echo   6. 00_MASTER_INDEX.md
echo.
echo Interactive Tables Features:
echo   - Obsidian-style dark theme
echo   - Tabs for each Excel sheet (All Papers, Summary, Top by Size, etc.)
echo   - Search functionality
echo   - Scrollable tables
echo   - Sticky headers
echo   - Number formatting
echo   - Responsive design
echo.
echo Next Steps:
echo   1. Upload entire folder to Cloudflare Pages
echo   2. Set up password protection (see CLOUDFLARE_PASSWORD_SETUP.md)
echo   3. Import RSS feed to Substack: %cloudflare_url%/feed.xml
echo.

set /p open_tables="Open interactive tables to preview? (y/n): "
if /i "%open_tables%"=="y" start "" "%analytics_dir%\Trinity_Data_Tables.html"

set /p open_dashboard="Open analytics dashboard? (y/n): "
if /i "%open_dashboard%"=="y" start "" "%analytics_dir%\Trinity_Dashboard.html"

set /p open_folder="Open analytics folder? (y/n): "
if /i "%open_folder%"=="y" start "" "%analytics_dir%"

echo.
pause
