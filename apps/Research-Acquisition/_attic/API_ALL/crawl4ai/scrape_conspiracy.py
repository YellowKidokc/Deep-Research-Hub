import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from crawl4ai import AsyncWebCrawler
import asyncio

async def main():
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url='https://en.wikipedia.org/wiki/List_of_conspiracy_theories')
        outpath = r'D:\GitHub\crawl4ai\crawl4ai_downloads\conspiracy_theories.md'
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(result.markdown)
        print(f'Downloaded: {len(result.markdown)} chars')
        print(f'Saved to: {outpath}')

asyncio.run(main())
