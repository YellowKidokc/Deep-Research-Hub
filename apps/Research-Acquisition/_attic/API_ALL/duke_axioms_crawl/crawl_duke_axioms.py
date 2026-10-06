import asyncio
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


BASE = "https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/"
SEEDS = [urljoin(BASE, "Contents.html"), urljoin(BASE, "index.html")]
ROOT = Path(__file__).resolve().parent
RAW = ROOT / "source_html_complete"
MARKDOWN = ROOT / "source_markdown_complete"


def discover_urls() -> list[str]:
    found = set(SEEDS)
    for seed in SEEDS:
        req = Request(seed, headers={"User-Agent": "TheophysicsResearchArchive/1.0"})
        with urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8", errors="replace")
        for href in re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I):
            url = urljoin(seed, href).split("#", 1)[0]
            parsed = urlparse(url)
            if url.startswith(BASE) and parsed.path.lower().endswith((".html", ".htm")):
                found.add(url)
    return sorted(found)


def safe_name(url: str) -> str:
    name = Path(urlparse(url).path).name or "index.html"
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    stem = Path(cleaned).stem
    suffix = Path(cleaned).suffix or ".html"
    url_tag = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    return f"{stem}__{url_tag}{suffix}"


async def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    MARKDOWN.mkdir(parents=True, exist_ok=True)
    urls = discover_urls()
    browser = BrowserConfig(headless=True)
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=60000)
    rows = []
    async with AsyncWebCrawler(config=browser) as crawler:
        for number, url in enumerate(urls, start=1):
            result = await crawler.arun(url=url, config=run)
            name = safe_name(url)
            if result.success:
                html = result.html or ""
                markdown = result.markdown.raw_markdown if hasattr(result.markdown, "raw_markdown") else str(result.markdown or "")
                (RAW / name).write_text(html, encoding="utf-8")
                (MARKDOWN / f"{Path(name).stem}.md").write_text(markdown, encoding="utf-8")
                digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
                rows.append({"number": number, "url": url, "title": result.metadata.get("title", ""), "status": "PASS", "html_file": name, "markdown_file": f"{Path(name).stem}.md", "sha256": digest, "error": ""})
            else:
                rows.append({"number": number, "url": url, "title": "", "status": "FAILED", "html_file": "", "markdown_file": "", "sha256": "", "error": result.error_message or "unknown error"})

    with (ROOT / "URL_LEDGER.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    receipt = {
        "crawl_scope": BASE,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "discovered": len(urls),
        "passed": sum(row["status"] == "PASS" for row in rows),
        "failed": sum(row["status"] != "PASS" for row in rows),
        "external_urls_followed": 0,
        "authority": "Preserved research source; not canon and not an admission event.",
    }
    (ROOT / "CRAWL_RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
