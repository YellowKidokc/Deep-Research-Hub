@echo off
REM run_srt_to_markdown.cmd
REM Drag-and-drop or command-line wrapper for srt_to_markdown.py
REM Usage:
REM   run_srt_to_markdown.cmd "C:\path\to\subtitles" "C:\path\to\output"

setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%srt_to_markdown.py"

if not exist "%PYTHON_SCRIPT%" (
    echo ERROR: srt_to_markdown.py not found in %SCRIPT_DIR%
    exit /b 1
)

if "%~1"=="" (
    echo.
    echo SRT to Markdown batch converter
    echo.
    set /p INPUT_FOLDER="Enter input folder containing .srt files: "
    set /p OUTPUT_FOLDER="Enter output folder for .md files: "
) else (
    set "INPUT_FOLDER=%~1"
    if "%~2"=="" (
        set "OUTPUT_FOLDER=%INPUT_FOLDER%_markdown"
    ) else (
        set "OUTPUT_FOLDER=%~2"
    )
)

if not exist "%INPUT_FOLDER%" (
    echo ERROR: Input folder not found: %INPUT_FOLDER%
    exit /b 1
)

echo.
echo Converting .srt files in:
echo   %INPUT_FOLDER%
echo Output folder:
echo   %OUTPUT_FOLDER%
echo.

python "%PYTHON_SCRIPT%" -i "%INPUT_FOLDER%" -o "%OUTPUT_FOLDER%" --batch

echo.
echo Done.
pause
