"""
Crawl Catherine Austin Fitts' "Dillon Read & Co. Inc. & The Aristocracy of Stock Profits"
from Solari.com and save each chapter as a Markdown file for the Obsidian vault.
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
from datetime import datetime
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

OUTPUT_DIR = Path("O:/Valts/epstein_email_obsidian_vault-main/Dillon_Read_Research")
BASE_URL = "https://solari.com/dillon-read-co-inc-the-aristocracy-of-stock-profits/"

# Known chapter slugs on Solari - will also be discovered from the TOC page
KNOWN_SECTIONS = [
    "https://solari.com/dillon-read-co-inc-the-aristocracy-of-stock-profits/",
]


def safe_filename(title: str, prefix: str = "") -> str:
    """Convert a title to a safe filename."""
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '', title)
    name = re.sub(r'\s+', '_', name.strip())
    name = name[:120]
    return f"{prefix}{name}.md" if prefix else f"{name}.md"


def extract_chapter_links(html: str, base_url: str) -> list[str]:
    """Extract internal chapter/section links from the TOC page."""
    soup = BeautifulSoup(html, 'html.parser')
    base_domain = urlparse(base_url).netloc
    links = []
    seen = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        # Same domain, no fragment-only links, path must be longer than base
        if (parsed.netloc == base_domain
                and parsed.path != '/'
                and absolute not in seen
                and '#' not in absolute
                and absolute.startswith('http')):
            # Filter to only Dillon Read related paths
            if 'dillon-read' in absolute or 'aristocracy' in absolute or 'fitts' in absolute.lower():
                seen.add(absolute)
                links.append(absolute)
    return links


async def crawl_page(crawler: AsyncWebCrawler, url: str) -> dict | None:
    """Crawl a single page and return its content dict."""
    try:
        result = await crawler.arun(url=url)
        if result.success:
            title = "Untitled"
            if hasattr(result, 'metadata') and result.metadata:
                title = result.metadata.get('title', 'Untitled')
            elif hasattr(result, 'title') and result.title:
                title = result.title

            content = ""
            if hasattr(result, 'markdown') and result.markdown:
                content = result.markdown
            elif hasattr(result, 'extracted_content') and result.extracted_content:
                content = result.extracted_content

            html = result.html if hasattr(result, 'html') else ""
            return {"url": url, "title": title, "content": content, "html": html}
        else:
            err = getattr(result, 'error_message', 'Unknown error')
            print(f"  FAILED: {url} — {err}")
            return None
    except Exception as e:
        print(f"  ERROR: {url} — {e}")
        return None


def save_chapter(data: dict, filepath: Path, chapter_num: int | None = None):
    """Write chapter content as an Obsidian-ready Markdown file."""
    header_lines = [
        f"# {data['title']}",
        "",
        f"**Source:** {data['url']}",
        f"**Author:** Catherine Austin Fitts",
        f"**Book:** Dillon Read & Co. Inc. & The Aristocracy of Stock Profits",
        f"**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    if chapter_num is not None:
        header_lines.insert(1, f"**Chapter:** {chapter_num}")

    header_lines += ["", "---", ""]
    header = "\n".join(header_lines)
    filepath.write_text(header + data['content'], encoding='utf-8')
    print(f"  SAVED: {filepath.name}")


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("FITTS BOOK CRAWLER — Dillon Read & The Aristocracy of Stock Profits")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 70)

    async with AsyncWebCrawler(verbose=False) as crawler:
        # Step 1: crawl the main TOC/index page
        print(f"\n[1/2] Fetching Table of Contents: {BASE_URL}")
        toc_data = await crawl_page(crawler, BASE_URL)

        if not toc_data:
            print("FATAL: Could not reach the main Fitts book page. Check the URL.")
            return

        # Save the index page itself
        toc_file = OUTPUT_DIR / "01_FITTS_INTRO_TOC.md"
        save_chapter(toc_data, toc_file)

        # Step 2: extract chapter links from TOC
        chapter_links = extract_chapter_links(toc_data['html'], BASE_URL)

        # Fallback: if no links found on same path, try to grab all solari.com/dillon-read* links
        if not chapter_links:
            soup = BeautifulSoup(toc_data['html'], 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                absolute = urljoin(BASE_URL, href)
                if 'solari.com' in absolute and absolute != BASE_URL and '#' not in absolute:
                    chapter_links.append(absolute)
            chapter_links = list(dict.fromkeys(chapter_links))  # dedupe preserve order

        print(f"\n[2/2] Found {len(chapter_links)} chapter/section links. Crawling...")

        for i, url in enumerate(chapter_links, start=2):
            print(f"\n  [{i}/{len(chapter_links)+1}] {url}")
            data = await crawl_page(crawler, url)
            if data:
                # Zero-pad chapter number for Obsidian sort order
                filename = f"{i:02d}_FITTS_{safe_filename(data['title'])}"
                filepath = OUTPUT_DIR / filename
                save_chapter(data, filepath, chapter_num=i - 1)

    print("\n" + "=" * 70)
    print("DONE — All pages saved to Dillon_Read_Research/")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
