import asyncio
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from crawl4ai import AsyncWebCrawler

OUTPUT_DIR = Path("D:/GitHub/crawl4ai/downloaded_pages")
URLS_FILE = Path("D:/GitHub/crawl4ai/carm_urls.txt")
MAX_CONCURRENT = 5
DELAY_BETWEEN = 0.5  # seconds between launches


def url_to_filename(url):
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "").replace(".", "_")
    path = parsed.path.strip("/")
    query = parsed.query
    fragment = parsed.fragment

    if not path or path == "index.php":
        name = domain
    else:
        name = domain + "_" + path.replace("/", "_").replace(".html", "")

    if query:
        name += "_" + query.replace("&", "_").replace("=", "_")

    if fragment:
        name += "_" + fragment

    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    if len(name) > 180:
        name = name[:180]
    return name + ".md"


async def download_one(crawler, url, idx, total, sem, results):
    async with sem:
        try:
            result = await crawler.arun(url=url)
            if result.success and result.markdown:
                filename = url_to_filename(url)
                filepath = OUTPUT_DIR / filename
                content = f"---\nurl: {url}\n---\n\n{result.markdown}"
                filepath.write_text(content, encoding="utf-8")
                size = len(result.markdown)
                results["ok"] += 1
                print(f"  [{results['ok']+results['fail']:>4}/{total}] OK  {size:>8,} chars  {filename}")
            else:
                results["fail"] += 1
                err = getattr(result, 'error_message', 'unknown error') if result else 'no result'
                print(f"  [{results['ok']+results['fail']:>4}/{total}] FAIL  {url}  ({err})")
        except Exception as e:
            results["fail"] += 1
            print(f"  [{results['ok']+results['fail']:>4}/{total}] ERR   {url}  ({e})")

        await asyncio.sleep(DELAY_BETWEEN)


async def main():
    # Load URLs
    lines = URLS_FILE.read_text(encoding="utf-8").splitlines()
    urls = []
    seen = set()
    for line in lines:
        u = line.strip()
        if u and u.startswith("http") and u not in seen:
            urls.append(u)
            seen.add(u)

    total = len(urls)
    print(f"Loaded {total} unique URLs (from {len(lines)} lines)")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Concurrency: {MAX_CONCURRENT}, delay: {DELAY_BETWEEN}s")
    print("-" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    results = {"ok": 0, "fail": 0}

    async with AsyncWebCrawler(verbose=False) as crawler:
        tasks = []
        for i, url in enumerate(urls):
            tasks.append(download_one(crawler, url, i, total, sem, results))

        await asyncio.gather(*tasks)

    print("-" * 70)
    print(f"Done! {results['ok']} saved, {results['fail']} failed out of {total}")
    print(f"Files in: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
