@echo off
setlocal EnableExtensions EnableDelayedExpansion

title OpenReel Web Launcher
cd /d "%~dp0"

echo ============================================================
echo   OpenReel — Browser-based video editor
echo ============================================================
echo.

:: Check pnpm
where pnpm >nul 2>nul
if errorlevel 1 (
  echo ERROR: pnpm is not on PATH. Install pnpm ^(https://pnpm.io/install^) and try again.
  pause
  exit /b 1
)

:: Install dependencies if needed
if not exist "node_modules" (
  echo Installing dependencies ^(pnpm install^)...
  pnpm install
  if errorlevel 1 (
    echo ERROR: pnpm install failed.
    pause
    exit /b 1
  )
) else (
  echo OK: node_modules exists
)

:: Build WASM modules if needed
if not exist "packages\core\src\wasm\fft\build\fft.wasm" (
  echo Building WASM modules ^(first time^)...
  pnpm build:wasm
  if errorlevel 1 (
    echo ERROR: WASM build failed.
    pause
    exit /b 1
  )
) else (
  echo OK: WASM modules built
)

echo.
echo Starting OpenReel web dev server...
echo   URL will be printed below ^(usually http://localhost:5173^)
echo.
pnpm dev

pause
