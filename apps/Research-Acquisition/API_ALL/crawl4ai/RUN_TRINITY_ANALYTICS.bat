@echo off
cd /d "%~dp0"

echo ============================================================
echo    Trinity Analytics Package Creator
echo ============================================================
echo.
echo This will create:
echo   1. Excel file with all 173 papers and metrics
echo   2. HTML interactive dashboard
echo.
pause

echo.
echo Installing required Python package (pandas)...
pip install pandas openpyxl -q

echo.
echo ============================================================
echo    Step 1: Converting 173 Dashboards to Excel
echo ============================================================
echo.

python -c "from dashboard_to_excel import process_dashboards_to_excel; process_dashboards_to_excel('Trinity_paper_dashboards', 'Trinity_Analytics.xlsx')"

echo.
echo ============================================================
echo    Step 2: Creating HTML Dashboard
echo ============================================================
echo.

python -c "from excel_to_html_dashboard import create_html_dashboard; create_html_dashboard('Trinity_Analytics.xlsx', 'Trinity_Dashboard.html')"

echo.
echo ============================================================
echo    COMPLETE!
echo ============================================================
echo.
echo Files created:
echo   - Trinity_Analytics.xlsx
echo   - Trinity_Dashboard.html
echo.
pause

start Trinity_Analytics.xlsx
start Trinity_Dashboard.html
