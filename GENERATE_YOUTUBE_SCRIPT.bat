@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Deep Research Hub — Generate YouTube Script
cd /d "%~dp0"

echo ============================================================
echo   Generate YouTube script from a paper / research file
echo ============================================================
echo.
echo This calls the OpenWriter Deep Research Hub plugin endpoint.
echo OpenWriter must be running (usually http://127.0.0.1:5050).
echo.

where curl >nul 2>nul
if errorlevel 1 (
  echo ERROR: curl is not available on PATH.
  pause
  exit /b 1
)

set /p source="Path to source markdown file (e.g. data\deep_research\Q-EVIL-LOGICAL\report.md): "
if not exist "%source%" (
  echo ERROR: file not found: %source%
  pause
  exit /b 1
)

set /p topic="Topic (optional, press Enter to skip): "

if not exist "data\writer\youtube_scripts" mkdir "data\writer\youtube_scripts"
for /f "delims=" %%a in ('powershell -Command "[datetime]::UtcNow.ToString('yyyyMMdd-HHmmss')"') do set "stamp=%%a"
set "outfile=data\writer\youtube_scripts\%stamp%_youtube_script.json"
set "bodyfile=%TEMP%\drh_youtube_body_%stamp%.json"

powershell -Command "$text = (Get-Content -Raw -Path '%source%') -replace '\r?\n','\n'; $topic = '%topic%'; @{ text = $text; topic = $topic } | ConvertTo-Json -Depth 2 | Set-Content -Path '%bodyfile%' -Encoding UTF8"

echo.
echo Calling /api/drh/youtube-script ...
curl -s -X POST "http://127.0.0.1:5050/api/drh/youtube-script" -H "Content-Type: application/json" -d "@%bodyfile%" -o "%outfile%" --max-time 300
set "CURL_EXIT=%ERRORLEVEL%"
del "%bodyfile%" 2>nul

if %CURL_EXIT% neq 0 (
  echo.
  echo ERROR: request failed ^(curl exit %CURL_EXIT%^). Make sure OpenWriter is running on port 5050.
  echo   Start it with: START_HUB.bat ^> OpenWriter
  pause
  exit /b 1
)

echo.
echo Done. Output saved to %outfile%
echo.
powershell -Command "$r = Get-Content -Raw -Path '%outfile%' | ConvertFrom-Json; Write-Host 'Title (long):' $r.title_long; Write-Host 'Title (short):' $r.title_short"
pause
