@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or not on PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" python -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if not exist ".env" copy /y ".env.example" ".env" >nul
echo.
echo Setup completed. Add your provider keys to .env, then run START_GPT_RESEARCHER.bat.
pause
