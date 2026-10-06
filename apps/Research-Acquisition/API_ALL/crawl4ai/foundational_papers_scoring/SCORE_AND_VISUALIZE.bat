@echo off
REM ==============================================================================
REM THEOPHYSICS COHERENCE FRAMEWORK
REM Double-Click Automation - Windows Batch File
REM ==============================================================================

title Theophysics Coherence Framework - Automated Analysis

echo.
echo ================================================================================
echo THEOPHYSICS COHERENCE FRAMEWORK
echo Automated Scoring and Visualization Pipeline
echo ================================================================================
echo.
echo Starting analysis...
echo.

REM Run the Python automation script
python "%~dp0SCORE_AND_VISUALIZE.py"

REM Check if it succeeded
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS! Dashboard and Excel files are ready.
    echo ================================================================================
    echo.
    echo Check your browser for the interactive dashboard!
    echo.
) else (
    echo.
    echo ================================================================================
    echo ERROR: Something went wrong. Check the output above for details.
    echo ================================================================================
    echo.
)

pause
