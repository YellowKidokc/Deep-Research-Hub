"""
SCRAPE-TO-MARKDOWN — Python Scraper
Reads URLs from scrape.md, downloads each page as clean markdown.
Tries crawl4ai first (best quality), falls back to trafilatura, then raw requests.

Usage: python scraper.py scrape.md ./output ./scrape_log.txt
"""

import sys
import os
import re
import hashlib
from datetime import datetime
from urllib.parse import urlparse

def extract_urls_from_markdown(filepath):
    """Read scrape.md and extract all URLs, skipping comments and blanks."""
    urls = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Extract URL (handle bare URLs or markdown links)
            url_match = re.search(r'https?://[^\s\)]+', line)
            if url_match:
                urls.append(url_match.group(0))
    return urls

def url_to_filename(url):
    """Convert a URL to a safe, readable filename."""
    parsed = urlparse(url)
    # Use domain + path, cleaned up
    name = parsed.netloc + parsed.path
    # Remove trailing slash
    name = name.rstrip('/')
    # Replace special chars
    name = re.sub(r'[^\w\-.]', '_', name)
    # Truncate if too long
    if len(name) > 120:
        name = name[:120] + '_' + hashlib.md5(url.encode()).hexdigest()[:8]
    return name + '.md'

def scrape_with_crawl4ai(url):
    """Try crawl4ai first — best quality extraction."""
    try:
        from crawl4ai import WebCrawler
        crawler = WebCrawler()
        crawler.warmup()
        result = crawler.run(url=url)
        if result.success and result.markdown:
            return result.markdown
        return None
    except ImportError:
        return None
    except Exception as e:
        print(f"  crawl4ai error: {e}")
        return None

def scrape_with_crawl4ai_async(url):
    """Try crawl4ai async version (newer API)."""
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler

        async def _crawl():
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                if result.success and result.markdown:
                    return result.markdown
            return None

        return asyncio.run(_crawl())
    except ImportError:
        return None
    except Exception as e:
        print(f"  crawl4ai async error: {e}")
        return None

def scrape_with_trafilatura(url):
    """Fallback: trafilatura — good at article extraction."""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, output_format='txt',
                                       include_links=True, include_tables=True)
            if text:
                return text
        return None
    except ImportError:
        return None
    except Exception as e:
        print(f"  trafilatura error: {e}")
        return None

def scrape_with_requests(url):
    """Last resort: raw requests + basic HTML stripping."""
    try:
        import requests
        from html.parser import HTMLParser

        class MLStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.fed = []
                self.skip = False
            def handle_starttag(self, tag, attrs):
                if tag in ('script', 'style', 'nav', 'footer', 'header'):
                    self.skip = True
            def handle_endtag(self, tag):
                if tag in ('script', 'style', 'nav', 'footer', 'header'):
                    self.skip = False
            def handle_data(self, d):
                if not self.skip:
                    self.fed.append(d)
            def get_data(self):
                return '\n'.join(self.fed)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()

        stripper = MLStripper()
        stripper.feed(resp.text)
        text = stripper.get_data()

        # Clean up excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        if len(text.strip()) > 100:
            return text.strip()
        return None
    except Exception as e:
        print(f"  requests error: {e}")
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python scraper.py <scrape.md> <output_dir> [log_file]")
        sys.exit(1)

    scrape_file = sys.argv[1]
    output_dir = sys.argv[2]
    log_file = sys.argv[3] if len(sys.argv) > 3 else None

    if not os.path.exists(scrape_file):
        print(f"ERROR: {scrape_file} not found")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    urls = extract_urls_from_markdown(scrape_file)
    print(f"Found {len(urls)} URLs to scrape\n")

    log_lines = []
    success_count = 0
    fail_count = 0

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        filename = url_to_filename(url)
        outpath = os.path.join(output_dir, filename)

        # Skip if already downloaded
        if os.path.exists(outpath):
            print(f"  SKIP (already exists): {filename}")
            log_lines.append(f"SKIP: {url} -> {filename}")
            continue

        # Try each method in order
        content = None
        method = None

        # Method 1: crawl4ai async (newer)
        content = scrape_with_crawl4ai_async(url)
        if content:
            method = "crawl4ai-async"

        # Method 2: crawl4ai sync (older)
        if not content:
            content = scrape_with_crawl4ai(url)
            if content:
                method = "crawl4ai-sync"

        # Method 3: trafilatura
        if not content:
            content = scrape_with_trafilatura(url)
            if content:
                method = "trafilatura"

        # Method 4: raw requests
        if not content:
            content = scrape_with_requests(url)
            if content:
                method = "requests"

        if content:
            # Add source header
            header = f"---\nsource: {url}\nscraped: {datetime.now().isoformat()}\nmethod: {method}\n---\n\n"
            with open(outpath, 'w', encoding='utf-8') as f:
                f.write(header + content)
            print(f"  OK ({method}): {filename} ({len(content):,} chars)")
            log_lines.append(f"OK [{method}]: {url} -> {filename} ({len(content):,} chars)")
            success_count += 1
        else:
            print(f"  FAIL: Could not extract content")
            log_lines.append(f"FAIL: {url}")
            fail_count += 1

    # Summary
    summary = f"\n{'='*60}\nDone: {success_count} success, {fail_count} failed, out of {len(urls)} total\n{'='*60}"
    print(summary)

    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(log_lines) + summary + '\n')

if __name__ == '__main__':
    main()
