@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist "node_modules\tsx" (
  echo Dependencies are missing. Run npm ci in this folder.
  pause
  exit /b 1
)
if not exist "dist\index.cjs" (
  echo Production build is missing. Run npm run build in this folder.
  pause
  exit /b 1
)
if not exist ".env" (
  echo Configuration is missing. Copy .env.example to .env in this folder.
  pause
  exit /b 1
)

set "NODE_ENV=production"
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
  start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --new-window "http://127.0.0.1:5000/"
) else (
  start "" "http://127.0.0.1:5000/"
)

echo YouTube Pro: http://127.0.0.1:5000/
echo Keep this window open while using YouTube Pro. Press Ctrl+C to stop it.
node dist\index.cjs
if errorlevel 1 (
  echo YouTube Pro stopped with an error.
  pause
  exit /b 1
)
