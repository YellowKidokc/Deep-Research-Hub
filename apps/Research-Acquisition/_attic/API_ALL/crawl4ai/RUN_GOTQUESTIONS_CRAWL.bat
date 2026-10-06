@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d D:\GitHub\crawl4ai
echo Installing openpyxl pandas if needed...
pip install openpyxl pandas httpx -q
echo.
echo Run full crawl:  python gotquestions_crawler.py
echo Quick test (5): python gotquestions_crawler.py --limit 5
echo.
python gotquestions_crawler.py %*
pause
