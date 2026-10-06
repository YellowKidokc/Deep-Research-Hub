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
RETRY_FILE = Path("D:/GitHub/crawl4ai/retry_urls.txt")


def url_to_filename(url):
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "").replace(".", "_")
    path = parsed.path.strip("/")
    fragment = parsed.fragment
    if not path:
        name = domain + "_index"
    else:
        name = domain + "_" + path.replace("/", "_").replace(".html", "")
    if fragment:
        name += "_" + fragment
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    if len(name) > 180:
        name = name[:180]
    return name + ".md"


async def main():
    urls = [u.strip() for u in RETRY_FILE.read_text(encoding="utf-8").splitlines() if u.strip()]
    total = len(urls)
    ok = 0
    fail = 0
    print(f"Retrying {total} failed URLs (one at a time, 2s delay)...")
    async with AsyncWebCrawler(verbose=False) as crawler:
        for i, url in enumerate(urls, 1):
            try:
                result = await crawler.arun(url=url)
                if result.success and result.markdown:
                    fn = url_to_filename(url)
                    fp = OUTPUT_DIR / fn
                    content = f"---\nurl: {url}\n---\n\n{result.markdown}"
                    fp.write_text(content, encoding="utf-8")
                    ok += 1
                    print(f"  [{i}/{total}] OK  {len(result.markdown):>8,} chars  {fn}")
                else:
                    fail += 1
                    print(f"  [{i}/{total}] FAIL  {url}")
            except Exception as e:
                fail += 1
                print(f"  [{i}/{total}] ERR   {url}  ({e})")
            await asyncio.sleep(2)
    print(f"\nDone! {ok} saved, {fail} still failed")


if __name__ == "__main__":
    asyncio.run(main())
