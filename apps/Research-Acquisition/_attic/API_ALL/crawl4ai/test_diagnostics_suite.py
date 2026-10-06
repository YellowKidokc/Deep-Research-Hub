"""
Crawl4AI Diagnostics & Health Verification Suite
-----------------------------------------------
Performs 6 comprehensive checks:
1. Python runtime & 64-bit architecture
2. Core dependencies import verification
3. Crawl4AI package import & version
4. Playwright Chromium browser launch
5. Patchright Chromium stealth browser launch
6. Dual Crawl: Ordinary static page + Dynamic JavaScript-rendered page
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = WORKSPACE_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RECEIPT_FILE = OUTPUT_DIR / "diagnostic_receipt.txt"

class DiagnosticRunner:
    def __init__(self):
        self.failures = 0
        self.receipt_lines = []

    def log(self, text: str, is_fail: bool = False):
        print(text)
        self.receipt_lines.append(text)
        if is_fail:
            self.failures += 1

    def run_all(self):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        header = [
            "=" * 76,
            "               CRAWL4AI DIAGNOSTIC RECEIPT & HEALTH VERIFICATION",
            "=" * 76,
            f"Timestamp       : {timestamp}",
            f"Project Root    : {WORKSPACE_ROOT}",
            f"Python Runtime  : {sys.executable}",
            "=" * 76,
            ""
        ]
        for h in header:
            print(h)
            self.receipt_lines.append(h)

        # Test 1: Python Version
        self.log("[Test 1/6] Checking Python version & architecture...")
        try:
            is_64 = sys.maxsize > 2**32
            v_str = sys.version.split()[0]
            assert sys.version_info >= (3, 10), "Python 3.10+ required"
            self.log(f"  Python {v_str} [64-bit: {is_64}]")
            self.log("  [PASS] Python version check passed.")
        except Exception as e:
            self.log(f"  [FAIL] Python version error: {e}", is_fail=True)
        self.log("")

        # Test 2: Core Dependencies
        self.log("[Test 2/6] Checking critical modules import...")
        try:
            import aiohttp
            import playwright
            import patchright
            import pydantic
            import litellm
            import bs4
            import rich
            import OpenSSL
            self.log("  Modules verified: aiohttp, playwright, patchright, pydantic, litellm, bs4, rich, OpenSSL")
            self.log("  [PASS] All critical dependencies loaded successfully.")
        except Exception as e:
            self.log(f"  [FAIL] Missing dependency: {e}", is_fail=True)
        self.log("")

        # Test 3: Crawl4AI Core Import
        self.log("[Test 3/6] Checking Crawl4AI library import...")
        try:
            import crawl4ai
            from crawl4ai import AsyncWebCrawler
            from crawl4ai.__version__ import __version__
            self.log(f"  Crawl4AI Version: {__version__}")
            self.log("  [PASS] Crawl4AI library imported cleanly.")
        except Exception as e:
            self.log(f"  [FAIL] Crawl4AI import error: {e}", is_fail=True)
        self.log("")

        # Test 4: Playwright Chromium Browser Launch
        self.log("[Test 4/6] Confirming Playwright Chromium browser launch...")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                v = browser.version
                browser.close()
            self.log(f"  Playwright Chromium launched successfully. Browser Version: {v}")
            self.log("  [PASS] Playwright Chromium launched and closed successfully.")
        except Exception as e:
            self.log(f"  [FAIL] Playwright Chromium launch failed: {e}", is_fail=True)
        self.log("")

        # Test 5: Patchright Stealth Engine Launch
        self.log("[Test 5/6] Confirming Patchright Chromium stealth browser launch...")
        try:
            from patchright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                v = browser.version
                browser.close()
            self.log(f"  Patchright Chromium launched successfully. Browser Version: {v}")
            self.log("  [PASS] Patchright Chromium stealth engine launched and closed successfully.")
        except Exception as e:
            self.log(f"  [FAIL] Patchright Chromium launch failed: {e}", is_fail=True)
        self.log("")

        # Test 6: Dual Crawl (Ordinary Page + JavaScript-Heavy Page)
        self.log("[Test 6/6] Crawling Ordinary Page and JavaScript-Heavy Page...")
        try:
            asyncio.run(self._test_crawls())
            self.log("  [PASS] Both ordinary and JavaScript-heavy pages crawled and rendered.")
        except Exception as e:
            self.log(f"  [FAIL] Dual crawl test failed: {e}", is_fail=True)
        self.log("")

        # Summary
        self.log("=" * 76)
        self.log("                           DIAGNOSTIC SUMMARY")
        self.log("=" * 76)
        if self.failures == 0:
            self.log("[STATUS] ALL TESTS PASSED! Your Crawl4AI setup is completely healthy.")
        else:
            self.log(f"[STATUS] {self.failures} test failed.")
        self.log("=" * 76)

        # Write Receipt File
        with open(RECEIPT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(self.receipt_lines) + "\n")

        print(f"\nDiagnostic receipt saved to: {RECEIPT_FILE}")
        return self.failures

    async def _test_crawls(self):
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

        cfg = BrowserConfig(headless=True, light_mode=True)
        run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

        async with AsyncWebCrawler(config=cfg) as crawler:
            # 6A: Ordinary Static Page
            r1 = await crawler.arun(url="https://example.com", config=run_cfg)
            assert r1.status_code == 200 and r1.markdown, "Ordinary page failed"
            self.log(f"  [6A] Ordinary Page (example.com): Status {r1.status_code}, Markdown: {len(r1.markdown)} chars")

            # 6B: JavaScript-Heavy Dynamic Page
            r2 = await crawler.arun(url="https://quotes.toscrape.com/js/", config=run_cfg)
            assert r2.status_code == 200 and r2.markdown, "JS page crawl failed"
            assert "Albert Einstein" in r2.markdown, "JavaScript content did not render in DOM"
            self.log(f"  [6B] JS-Heavy Page (quotes.toscrape.com/js/): Status {r2.status_code}, Markdown: {len(r2.markdown)} chars (Dynamic JS Execution Verified)")

if __name__ == "__main__":
    runner = DiagnosticRunner()
    ret = runner.run_all()
    sys.exit(ret)
