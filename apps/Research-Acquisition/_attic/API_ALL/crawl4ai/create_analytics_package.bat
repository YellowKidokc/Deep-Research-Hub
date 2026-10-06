@echo off
echo ============================================================
echo    Analytics Package Creator
echo    Dashboards -> Excel -> HTML
echo ============================================================
echo.

set /p dashboard_dir="Dashboard directory (default: Trinity_paper_dashboards): "
if "%dashboard_dir%"=="" set dashboard_dir=Trinity_paper_dashboards

set /p base_name="Output base name (default: Trinity_Analytics): "
if "%base_name%"=="" set base_name=Trinity_Analytics

echo.
echo ============================================================
echo    Step 1: Converting Dashboards to Excel
echo ============================================================
echo.

python dashboard_to_excel.py "%dashboard_dir%" "%base_name%.xlsx"

if errorlevel 1 (
    echo.
    echo Error creating Excel file!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    Step 2: Creating HTML Dashboard
echo ============================================================
echo.

python excel_to_html_dashboard.py "%base_name%.xlsx" "%base_name%_Dashboard.html"

if errorlevel 1 (
    echo.
    echo Error creating HTML dashboard!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    COMPLETE!
echo ============================================================
echo.
echo Created files:
echo   - %base_name%.xlsx (Excel with all data)
echo   - %base_name%_Dashboard.html (Interactive dashboard)
echo.

set /p open_excel="Open Excel file? (y/n): "
if /i "%open_excel%"=="y" start "" "%base_name%.xlsx"

set /p open_html="Open HTML dashboard? (y/n): "
if /i "%open_html%"=="y" start "" "%base_name%_Dashboard.html"

echo.
pause
