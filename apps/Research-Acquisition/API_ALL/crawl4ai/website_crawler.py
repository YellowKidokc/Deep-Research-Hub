"""
Website Crawler - Download entire website recursively
Saves all pages as Markdown

Usage: python website_crawler.py <url> <max_depth> <output_dir> [section|site]

  section (default)  only follow links under the starting URL's path,
                     e.g. /writings/popular-writings/existence-nature-of-god/...
  site               follow any link on the same domain
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

SKIP_EXTS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".mp3", ".mp4",
             ".zip", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".css", ".js")


def page_title(result):
    # Crawl4AI moved the title into result.metadata; older versions had result.title.
    meta = getattr(result, "metadata", None) or {}
    return (meta.get("title") or getattr(result, "title", None) or "Untitled").strip()


def normalize(url):
    url = url.split("#")[0]
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return parsed._replace(path=path, fragment="").geturl()


def slug_for(url, used):
    path = urlparse(url).path.strip("/") or "index"
    slug = re.sub(r"[^\w\-]+", "_", path.split("/")[-1] if "/" in path else path).strip("_") or "index"
    slug = slug[:100]
    name, n = slug, 2
    while name in used:
        name, n = f"{slug}_{n}", n + 1
    used.add(name)
    return name


async def crawl_website(start_url, max_depth, output_dir, scope="section"):
    """Recursively crawl entire website"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_domain = urlparse(start_url).netloc
    base_path = urlparse(start_url).path.rstrip("/") + "/"
    visited_urls = set()
    to_visit = [(normalize(start_url), 0)]  # (url, depth)
    saved = []                              # (filename, title, url, depth)
    used_names = set()

    print(f"\n{'='*70}")
    print(f"DOWNLOADING WEBSITE: {start_url}")
    print(f"Base domain: {base_domain}")
    print(f"Scope: {'only pages under ' + base_path if scope == 'section' else 'whole domain'}")
    print(f"Max depth: {max_depth}")
    print(f"{'='*70}\n")

    def in_scope(url):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or parsed.netloc != base_domain:
            return False
        if parsed.path.lower().endswith(SKIP_EXTS):
            return False
        if scope == "section":
            return (parsed.path.rstrip("/") + "/").startswith(base_path)
        return True

    async with AsyncWebCrawler(verbose=True) as crawler:
        while to_visit:
            current_url, depth = to_visit.pop(0)

            if current_url in visited_urls:
                continue

            if depth > max_depth:
                continue

            visited_urls.add(current_url)

            print(f"\n[Depth {depth}] [{len(saved)+1}] {current_url}")

            try:
                result = await crawler.arun(url=current_url)

                if result.success:
                    title = page_title(result)
                    filename = slug_for(current_url, used_names) + ".md"
                    page_file = output_path / filename

                    header = f"# {title}\n\n"
                    header += f"**URL:** {current_url}\n\n"
                    header += f"**Depth:** {depth}\n\n"
                    header += f"**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    header += "---\n\n"

                    page_file.write_text(header + str(result.markdown or ""), encoding='utf-8')
                    saved.append((filename, title, current_url, depth))
                    print(f"  ✓ Saved: {filename}")

                    # Extract links for next depth level
                    if depth < max_depth and result.html:
                        soup = BeautifulSoup(result.html, 'html.parser')

                        for link in soup.find_all('a', href=True):
                            absolute_url = normalize(urljoin(current_url, link['href']))
                            if in_scope(absolute_url) and absolute_url not in visited_urls:
                                to_visit.append((absolute_url, depth + 1))
                else:
                    print(f"  ✗ Failed: {result.error_message or 'Unknown error'}")

            except Exception as e:
                print(f"  ✗ Error: {str(e)}")

    # Create index
    index_file = output_path / "index.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(f"# Website Download Index\n\n")
        f.write(f"**Website:** {start_url}\n\n")
        f.write(f"**Base Domain:** {base_domain}\n\n")
        f.write(f"**Scope:** {scope}\n\n")
        f.write(f"**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Pages:** {len(saved)}\n\n")
        f.write(f"**Max Depth:** {max_depth}\n\n")
        f.write("---\n\n")
        f.write("## Downloaded Pages\n\n")

        for filename, title, url, depth in saved:
            label = title.replace("|", "-").replace("[", "(").replace("]", ")")
            f.write(f"- [[{filename[:-3]}|{label}]] (depth {depth}) - {url}\n")

    print(f"\n{'='*70}")
    print(f"WEBSITE DOWNLOAD COMPLETE")
    print(f"{'='*70}")
    print(f"Pages downloaded: {len(saved)}")
    print(f"Saved to: {output_path}")
    print(f"Index: {index_file}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python website_crawler.py <url> <max_depth> <output_dir> [section|site]")
        sys.exit(1)

    url = sys.argv[1]
    max_depth = int(sys.argv[2])
    output_dir = sys.argv[3]
    scope = sys.argv[4].lower() if len(sys.argv) > 4 else "section"
    if scope not in ("section", "site"):
        scope = "section"

    asyncio.run(crawl_website(url, max_depth, output_dir, scope))
