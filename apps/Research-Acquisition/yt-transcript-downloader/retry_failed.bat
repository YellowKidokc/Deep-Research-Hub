@echo off
REM Re-fetch every failure placeholder in the transcript library through Webshare.
REM Double-click and type a channel folder name, or leave blank for the whole library.
REM   retry_failed.bat "Andrei Jikh"   also works from a command line.
setlocal
cd /d "%~dp0"
set "FOLDER=%~1"
if "%FOLDER%"=="" (
  echo Channel folder name under subtitles\ ^(blank = whole library^):
  set /p "FOLDER=> "
)
echo.
if "%FOLDER%"=="" (
  venv\Scripts\python.exe ytgrab.py --retry-failed --skip-direct
) else (
  venv\Scripts\python.exe ytgrab.py --retry-failed "%FOLDER%" --skip-direct
)
echo.
pause
