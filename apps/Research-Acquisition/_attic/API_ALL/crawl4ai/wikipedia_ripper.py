"""
Purpose: Crawl Wikipedia from one or more seed pages and save markdown plus discovered links.
Inputs: Seed URL list, output directory, page limit, crawl delay, allowed host.
Outputs: Markdown files, a CSV of discovered links, and a crawl manifest JSON.
Master Equation Relation: None - external data ingestion utility.
Date: 2026-04-05
"""

import asyncio
import csv
import json
import os
import re
import sys
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_ALLOWED_HOST = "en.wikipedia.org"
DEFAULT_DELAY_SECONDS = 1.5
DEFAULT_MAX_PAGES = 50


@dataclass
class CrawlRecord:
    url: str
    title: str
    saved_file: str
    discovered_at: str
    outgoing_links: int


def sanitize_filename(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_") or "index"
    query = parsed.query.replace("=", "_").replace("&", "_")
    base = f"{parsed.netloc}_{path}"
    if query:
        base = f"{base}_{query}"
    base = re.sub(r"[<>:\"/\\|?*]+", "_", base)
    return base[:180]


def normalize_url(url: str, base_url: str) -> str:
    absolute = urljoin(base_url, url)
    absolute, _ = urldefrag(absolute)
    return absolute


def is_allowed_wikipedia_url(url: str, allowed_host: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc.lower() != allowed_host.lower():
        return False
    if not parsed.path.startswith("/wiki/"):
        return False
    banned_prefixes = (
        "/wiki/Special:",
        "/wiki/Help:",
        "/wiki/File:",
        "/wiki/Template:",
        "/wiki/Category_talk:",
        "/wiki/Talk:",
        "/wiki/Portal:",
        "/wiki/Wikipedia:",
    )
    return not parsed.path.startswith(banned_prefixes)


def extract_links_from_html(html: str, base_url: str, allowed_host: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        normalized = normalize_url(anchor["href"], base_url)
        if is_allowed_wikipedia_url(normalized, allowed_host) and normalized not in seen:
            seen.add(normalized)
            found.append(normalized)
    return found


async def crawl_pages(
    seeds: Iterable[str],
    output_dir: Path,
    max_pages: int = DEFAULT_MAX_PAGES,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    allowed_host: str = DEFAULT_ALLOWED_HOST,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    queue = deque()
    visited: set[str] = set()
    for seed in seeds:
        normalized = normalize_url(seed, seed)
        if is_allowed_wikipedia_url(normalized, allowed_host):
            queue.append(normalized)

    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(stream=False)
    discovered_rows: list[dict[str, str]] = []
    manifest: list[CrawlRecord] = []

    async with AsyncWebCrawler(config=browser_config, verbose=False) as crawler:
        while queue and len(visited) < max_pages:
            url = queue.popleft()
            if url in visited:
                continue

            print(f"[{len(visited)+1}/{max_pages}] Crawling {url}")
            result = await crawler.arun(url=url, config=run_config)
            visited.add(url)

            if not getattr(result, "success", False):
                print(f"  Failed: {getattr(result, 'error_message', 'unknown error')}")
                await asyncio.sleep(delay_seconds)
                continue

            title = "Untitled"
            metadata = getattr(result, "metadata", None)
            if metadata:
                title = metadata.get("title", title)

            markdown_obj = getattr(result, "markdown", None)
            if hasattr(markdown_obj, "fit_markdown"):
                markdown_text = markdown_obj.fit_markdown or markdown_obj.raw_markdown or ""
            elif hasattr(markdown_obj, "raw_markdown"):
                markdown_text = markdown_obj.raw_markdown or ""
            else:
                markdown_text = markdown_obj or ""

            html = getattr(result, "html", "") or ""
            outgoing_links = extract_links_from_html(html, url, allowed_host)

            filename = sanitize_filename(url) + ".md"
            page_path = pages_dir / filename
            header = [
                f"# {title}",
                "",
                f"**URL:** {url}",
                f"**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Outgoing Links Captured:** {len(outgoing_links)}",
                "",
                "---",
                "",
            ]
            page_path.write_text("\n".join(header) + markdown_text, encoding="utf-8")

            manifest.append(
                CrawlRecord(
                    url=url,
                    title=title,
                    saved_file=str(page_path),
                    discovered_at=datetime.now().isoformat(timespec="seconds"),
                    outgoing_links=len(outgoing_links),
                )
            )

            for link in outgoing_links:
                discovered_rows.append({"source_url": url, "target_url": link})
                if link not in visited and link not in queue and len(visited) + len(queue) < max_pages * 4:
                    queue.append(link)

            await asyncio.sleep(delay_seconds)

    links_csv = output_dir / "discovered_links.csv"
    with links_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_url", "target_url"])
        writer.writeheader()
        writer.writerows(discovered_rows)

    manifest_path = output_dir / "crawl_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "allowed_host": allowed_host,
                "max_pages": max_pages,
                "delay_seconds": delay_seconds,
                "pages_crawled": len(manifest),
                "records": [asdict(item) for item in manifest],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nFinished. Crawled {len(manifest)} pages.")
    print(f"Markdown pages: {pages_dir}")
    print(f"Link graph CSV: {links_csv}")
    print(f"Manifest: {manifest_path}")


def parse_seeds(argv: list[str]) -> list[str]:
    if len(argv) > 1:
        return argv[1:]
    return [
        "https://en.wikipedia.org/wiki/List_of_conspiracy_theories",
        "https://en.wikipedia.org/wiki/MKUltra",
        "https://en.wikipedia.org/wiki/Jeffrey_Epstein",
    ]


if __name__ == "__main__":
    seeds = parse_seeds(sys.argv)
    base_output_dir = Path(r"D:\GitHub\crawl4ai\crawl4ai_downloads")
    run_dir = base_output_dir / f"wikipedia_rip_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    asyncio.run(crawl_pages(seeds=seeds, output_dir=run_dir))
