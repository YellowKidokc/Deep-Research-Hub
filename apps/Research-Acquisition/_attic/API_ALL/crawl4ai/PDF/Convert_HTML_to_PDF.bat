@echo off
cd /d "%~dp0"

echo ============================================================
echo    HTML to PDF Converter
echo ============================================================
echo.
echo This will convert all HTML files in the inbox to PDFs
echo.
echo Checking inbox...

set inbox_count=0
for %%f in (inbox\*.html inbox\*.htm) do set /a inbox_count+=1

if %inbox_count%==0 (
    echo.
    echo No HTML files found in inbox!
    echo.
    echo Please:
    echo   1. Copy your HTML files to the 'inbox' folder
    echo   2. Run this script again
    echo.
    pause
    exit /b
)

echo Found %inbox_count% HTML file(s) to convert
echo.
echo Conversion settings:
echo   - Single-page layout: ON (fits all content on one page)
echo   - Text size: Optimized for readability
echo   - Background: Preserved
echo   - Margins: 0.5 inch
echo.
echo Output:
echo   - PDFs will be saved to: outbox\
echo   - Processed HTML moved to: processed\
echo.

set /p confirm="Continue with conversion? (y/n): "
if /i not "%confirm%"=="y" (
    echo Conversion cancelled.
    pause
    exit /b
)

echo.
echo ============================================================
echo    Installing/Checking Dependencies
echo ============================================================
echo.

REM Check if playwright is installed
python -c "import playwright" 2>nul
if errorlevel 1 (
    echo Installing Playwright...
    pip install playwright -q
    echo Installing Playwright browsers...
    python -m playwright install chromium
) else (
    echo Playwright already installed
)

echo.
echo ============================================================
echo    Converting HTML to PDF
echo ============================================================
echo.

python scripts\html_to_pdf_converter.py

echo.
echo ============================================================
echo    Conversion Complete!
echo ============================================================
echo.
echo Check the 'outbox' folder for your PDFs
echo.

set /p open_outbox="Open outbox folder? (y/n): "
if /i "%open_outbox%"=="y" start "" "outbox"

pause
