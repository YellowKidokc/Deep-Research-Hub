@echo off
setlocal
title Update and Install Last 30 Days
pushd "%~dp0"

echo Updating the repository without overwriting local work...
git pull --ff-only
if errorlevel 1 goto :failed

echo.
echo Synchronizing the Python environment...
uv sync
if errorlevel 1 goto :failed

echo.
echo Installing the current skill for Codex and compatible AI tools...
call npx skills add . -g -y
if errorlevel 1 goto :failed

echo.
echo Last 30 Days is updated and installed.
pause
popd
exit /b 0

:failed
echo.
echo Update or installation stopped because one step failed.
echo Existing files were not reset or discarded.
pause
popd
exit /b 1
