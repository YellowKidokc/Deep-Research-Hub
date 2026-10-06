"""
Single Page Crawler - Download one page as Markdown
FIXED VERSION for Attribute Error
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import sys
from datetime import datetime
import re
from urllib.parse import urlparse

def sanitize_filename(url):
    """Create safe filename from URL"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.strip('/').replace('/', '_')
    
    if not path:
        filename = domain + '_index'
    else:
        filename = domain + '_' + path

    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    if len(filename) > 200:
        filename = filename[:200]

    return filename

async def crawl_single_page(url, output_dir):
    """Download single page"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"DOWNLOADING: {url}")
    print(f"{ '='*70}\n")

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=url)

        if result.success:
            filename = sanitize_filename(url) + ".md"
            page_file = output_path / filename

            # FIXED: Handle attribute differences in Crawl4AI versions
            title = "Untitled"
            if hasattr(result, 'metadata') and result.metadata:
                title = result.metadata.get('title', 'Untitled')
            elif hasattr(result, 'title'):
                title = result.title or 'Untitled'

            header = f"# {title}\n\n"
            header += f"**URL:** {url}\n\n"
            header += f"**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"       
            header += "---\n\n"

            content = ""
            if hasattr(result, 'markdown'):
                content = result.markdown
            elif hasattr(result, 'extracted_content'):
                content = result.extracted_content

            page_file.write_text(header + content, encoding='utf-8')

            print(f"\n{'='*70}")
            print(f"DOWNLOAD COMPLETE")
            print(f"{ '='*70}")
            print(f"✅ Saved: {page_file}")
            print(f"{ '='*70}\n")
        else:
            err_msg = "Unknown error"
            if hasattr(result, 'error_message'):
                err_msg = result.error_message
            print(f"\n❌ Failed: {err_msg}\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python single_page_crawler.py <url> <output_dir>")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2]

    asyncio.run(crawl_single_page(url, output_dir))
