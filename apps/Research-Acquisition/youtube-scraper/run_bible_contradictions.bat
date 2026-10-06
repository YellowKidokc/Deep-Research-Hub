@echo off
REM YouTube Transcript Scraper - Bible Contradiction Channels
REM Just double-click this file to run the scraper

echo ============================================================
echo YouTube Channel Transcript Scraper
echo Bible Contradiction Channels
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first: python -m venv venv
    echo Then install dependencies: venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create .env file with your YouTube API key
    echo Example: YTB_API_KEY=your-api-key-here
    pause
    exit /b 1
)

REM Run the bible contradictions scraper
echo Starting scraper...
echo.
venv\Scripts\python.exe easy_scrape_bible_contradictions.py

echo.
echo ============================================================
echo Done!
echo ============================================================
pause
