@echo off
setlocal
title Mathematical Scripture and Theology Harvester
cd /d "%~dp0"

echo ================================================================
echo  MATHEMATICAL SCRIPTURE / THEOLOGY HARVESTER
echo  Provenance-first scholarly discovery; no paid API required
echo ================================================================
echo.
python math_scripture_harvester.py --self-test
if errorlevel 1 (
  echo SELF-TEST FAILED. No web requests were made.
  pause
  exit /b 1
)
echo.
echo Self-test passed. Starting bounded discovery...
python math_scripture_harvester.py --run --providers crossref,arxiv --max-results 10 --delay 1
echo.
echo Results: output_math_scripture\harvest_report.md
pause
