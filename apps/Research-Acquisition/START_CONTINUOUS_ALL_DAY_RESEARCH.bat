@echo off
setlocal EnableExtensions
title Continuous Local Deep Researcher (All-Day Runner)
color 0A

set "ROOT=%~dp0"
set "PY=%ROOT%gpt-researcher\.venv\Scripts\python.exe"

echo.
echo ================================================================
echo  CONTINUOUS LOCAL DEEP RESEARCHER - 24/7 ALL-DAY RUNNER
echo ================================================================
echo.
echo This runner will continuously research your local files all day long
echo and write comprehensive research papers to outputs\local_research\.
echo.

set "DEFAULT_FOLDER=Z:\Theophysics_Vault"
if not exist "%DEFAULT_FOLDER%" set "DEFAULT_FOLDER=C:\theophysics"

echo Choose folder to research:
echo   [Enter / 3] Default: %DEFAULT_FOLDER%
echo   [1]         Browse for folder (Windows Explorer dialog)
echo   [2]         Type or paste folder path
echo.
set /p choice="Select [1/2/3, Enter for default]: "

if "%choice%"=="" set "SELECTED_FOLDER=%DEFAULT_FOLDER%"
if "%choice%"=="3" set "SELECTED_FOLDER=%DEFAULT_FOLDER%"
if "%choice%"=="1" (
    for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description = 'Choose research folder'; if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $d.SelectedPath } else { '%DEFAULT_FOLDER%' }"`) do set "SELECTED_FOLDER=%%F"
)
if "%choice%"=="2" (
    set /p "SELECTED_FOLDER=Paste folder path: "
)

if "%SELECTED_FOLDER%"=="" set "SELECTED_FOLDER=%DEFAULT_FOLDER%"

echo.
echo [OK] Active Research Folder: %SELECTED_FOLDER%
echo.

rem Check API keys
for /f "usebackq delims=" %%K in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')"`) do set "DEEPSEEK_API_KEY=%%K"
if "%DEEPSEEK_API_KEY%"=="" (
    echo [FAIL] DEEPSEEK_API_KEY is not set in the Windows user environment.
    pause
    exit /b 1
)

rem Check Ollama for embeddings
curl -s http://127.0.0.1:11434/api/tags >nul
if errorlevel 1 (
    echo [START] Starting Ollama for local embeddings...
    powershell -NoProfile -Command "Start-Process -FilePath '%LOCALAPPDATA%\Programs\Ollama\ollama.exe' -ArgumentList 'serve' -WindowStyle Hidden"
    timeout /t 3 /nobreak >nul
)

cd /d "%ROOT%gpt-researcher"
if not exist "research_queue.txt" (
    echo # Add one research question or topic per line. > research_queue.txt
    echo # The runner will pick them up automatically and write deep research papers. >> research_queue.txt
    echo Analyze foundational mathematical axioms and physics derivations across the vault >> research_queue.txt
)

echo.
echo  --------------------------------------------------------------
echo   Queue file: %ROOT%gpt-researcher\research_queue.txt
echo   Add any topics to this file anytime and the agent will run them.
echo  --------------------------------------------------------------
echo.
echo Starting continuous research loop...
echo.

"%PY%" continuous_runner.py --folder "%SELECTED_FOLDER%" --continuous
pause
