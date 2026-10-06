@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
if errorlevel 1 goto :failed
"%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
"%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :failed
echo.
echo DeepDoc setup is complete. It can use OPENAI_API_KEY from your Windows environment.
echo No Docker server is required; its local vector database is stored under .runtime.
pause
exit /b 0
:failed
echo DeepDoc setup failed. Review the messages above.
pause
exit /b 1
