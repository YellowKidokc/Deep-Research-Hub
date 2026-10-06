@echo off
echo ============================================================
echo    Moving Trinity Analytics to Trinity Folder
echo ============================================================
echo.

set "source_dir=d:\GitHub\crawl4ai\Trinity_paper_dashboards"
set "dest_dir=O:\_Theophysics\05_Logos_Papers\Core_Papers\Trinity\_paper_analytics"

echo Moving dashboards from:
echo   %source_dir%
echo.
echo To:
echo   %dest_dir%
echo.
pause

if not exist "%dest_dir%" mkdir "%dest_dir%"

echo Copying files...
xcopy "%source_dir%\*.*" "%dest_dir%\" /Y /I

echo.
echo ============================================================
echo    Creating Excel and HTML Dashboard
echo ============================================================
echo.

cd /d "d:\GitHub\crawl4ai"

python -c "from dashboard_to_excel import process_dashboards_to_excel; process_dashboards_to_excel(r'%dest_dir%', r'%dest_dir%\Trinity_Analytics.xlsx')"

python -c "from excel_to_html_dashboard import create_html_dashboard; create_html_dashboard(r'%dest_dir%\Trinity_Analytics.xlsx', r'%dest_dir%\Trinity_Dashboard.html')"

echo.
echo ============================================================
echo    COMPLETE!
echo ============================================================
echo.
echo All files are now in:
echo   %dest_dir%
echo.
echo Files created:
echo   - Trinity_Analytics.xlsx
echo   - Trinity_Dashboard.html
echo   - 173 individual dashboards
echo   - 00_MASTER_INDEX.md
echo.

set /p open_folder="Open Trinity folder? (y/n): "
if /i "%open_folder%"=="y" start "" "%dest_dir%"

set /p open_excel="Open Excel file? (y/n): "
if /i "%open_excel%"=="y" start "" "%dest_dir%\Trinity_Analytics.xlsx"

set /p open_html="Open HTML dashboard? (y/n): "
if /i "%open_html%"=="y" start "" "%dest_dir%\Trinity_Dashboard.html"

pause
