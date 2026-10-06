#!/usr/bin/env python3
"""
Test script for Crawl4AI functionality
"""

import asyncio
import sys
import os

# Add the crawl4ai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crawl4ai'))

async def test_basic_crawling():
    """Test basic web crawling functionality"""
    try:
        from crawl4ai import AsyncWebCrawler

        print("Testing Crawl4AI basic functionality...")

        # Test with a simple website
        async with AsyncWebCrawler() as crawler:
            print("Starting crawler...")
            result = await crawler.arun(
                url="https://httpbin.org/html",
                verbose=True
            )

            print("[SUCCESS] Crawl completed successfully!")
            print(f"Content length: {len(result.content) if result.content else 0} characters")
            print(f"Status code: {result.status_code}")

            # Show a snippet of the content
            if result.content:
                content_preview = result.content[:200].replace('\n', ' ').strip()
                print(f"Content preview: {content_preview}...")

            return True

    except Exception as e:
        print(f"[ERROR] Error during crawling: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("Crawl4AI Installation Test")
    print("=" * 50)

    # Test import
    try:
        from crawl4ai import AsyncWebCrawler, CacheMode
        print("[SUCCESS] Import successful")
        print(f"AsyncWebCrawler available: {AsyncWebCrawler is not None}")
        print(f"CacheMode available: {CacheMode is not None}")
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        return

    # Test basic crawling
    print("\nTesting web crawling...")
    success = await test_basic_crawling()

    if success:
        print("\n[SUCCESS] Crawl4AI is working perfectly!")
        print("You can now use Crawl4AI for web scraping and crawling!")
    else:
        print("\n[WARNING] Crawl4AI imported but crawling test failed")
        print("You may need to install additional dependencies or configure your environment")

if __name__ == "__main__":
    asyncio.run(main())
