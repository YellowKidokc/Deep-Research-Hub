"""
GotQuestions.org Q&A Crawler
Crawls GotQuestions.org, extracts questions and answers, exports to Excel.
Uses httpx for fast, reliable HTTP fetching (no browser - avoids timeouts).
"""

import asyncio
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime

import httpx
import pandas as pd
from bs4 import BeautifulSoup

SEED_URLS = [
    "https://www.gotquestions.org/",
    "https://www.gotquestions.org/content_God.html",
    "https://www.gotquestions.org/content_Jesus-Christ.html",
    "https://www.gotquestions.org/content_Holy-Spirit.html",
    "https://www.gotquestions.org/content_salvation.html",
    "https://www.gotquestions.org/content_Bible.html",
    "https://www.gotquestions.org/new-believer-article-index.html",
    "https://www.gotquestions.org/content_church.html",
    "https://www.gotquestions.org/content_end-times.html",
    "https://www.gotquestions.org/content_angels_demons.html",
    "https://www.gotquestions.org/content_humanity.html",
    "https://www.gotquestions.org/content_theology.html",
    "https://www.gotquestions.org/content_apologetics.html",
    "https://www.gotquestions.org/content_worldview.html",
    "https://www.gotquestions.org/content_spiritual-life.html",
    "https://www.gotquestions.org/content_prayer.html",
    "https://www.gotquestions.org/content_sin.html",
    "https://www.gotquestions.org/content_eternity.html",
    "https://www.gotquestions.org/content_relationships.html",
    "https://www.gotquestions.org/content_family.html",
    "https://www.gotquestions.org/content_creation.html",
    "https://www.gotquestions.org/content_cults_religions.html",
    "https://www.gotquestions.org/content_false-beliefs.html",
    "https://www.gotquestions.org/content_Christianity.html",
    "https://www.gotquestions.org/content_Christian-history.html",
    "https://www.gotquestions.org/content_places.html",
    "https://www.gotquestions.org/content_people.html",
    "https://www.gotquestions.org/content_health.html",
    "https://www.gotquestions.org/content_life.html",
    "https://www.gotquestions.org/content_topical.html",
    "https://www.gotquestions.org/questions-about-books-Bible.html",
    "https://www.gotquestions.org/content_Catholicism.html",
    "https://www.gotquestions.org/content_Judaism.html",
    "https://www.gotquestions.org/content_Islam.html",
    "https://www.gotquestions.org/content_GotQuestions.html",
    "https://www.gotquestions.org/content.html",
]

# Skip non-article URLs
SKIP_PATTERNS = (
    "subscribe", "youtube", "facebook", "pinterest", "x.com", "twitter",
    "share", "email", "text/sms", "random", "gotquestions.net/admin"
)

MAX_PAGES = 0  # 0 = no limit; use --limit N for quick test

# HTTP client limits
REQUEST_TIMEOUT = 15.0
DELAY_BETWEEN_REQUESTS = 0.8  # Be polite to the server


def is_gotquestions_url(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc or "gotquestions.org" not in parsed.netloc:
        return False
    path = (parsed.path or "").lower()
    if path in ("/", "/index.html", ""):
        return False
    if any(skip in path for skip in SKIP_PATTERNS):
        return False
    return ".html" in path or path.endswith("/")


def is_index_page(url: str) -> bool:
    """Index pages list links to Q&A articles."""
    path = (urlparse(url).path or "").lower()
    return "content_" in path or "questions-about" in path or "new-believer" in path


def is_qa_page(url: str) -> bool:
    """Q&A pages have a single question and answer; not index pages."""
    return is_gotquestions_url(url) and not is_index_page(url)


def extract_links(html: str, base_url: str) -> tuple[set[str], set[str]]:
    """Extract links: (qa_pages, index_pages)."""
    soup = BeautifulSoup(html, "html.parser")
    qa_links = set()
    index_links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue
        full = urljoin(base_url, href)
        if not is_gotquestions_url(full):
            continue
        if is_qa_page(full):
            qa_links.add(full)
        elif is_index_page(full):
            index_links.add(full)
    return qa_links, index_links


def extract_question_answer(html: str, url: str) -> tuple[str, str]:
    """Extract question and answer from a Q&A page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    question = ""
    answer = ""

    # Question: usually in h1
    h1 = soup.find("h1")
    if h1:
        question = h1.get_text(separator=" ", strip=True)

    # Answer: try article/main content first
    for tag in soup.find_all(["article", "main"]) or []:
        pts = tag.find_all("p")
        if len(pts) >= 2:
            answer = "\n\n".join(p.get_text(strip=True) for p in pts[:20])
            if len(answer) > 100:
                break

    # Fallback: text-based parsing after "Answer"
    if not answer or len(answer) < 50:
        text = (soup.find("body") or soup).get_text(separator="\n", strip=False)
        lines = text.split("\n")
        in_answer = False
        answer_lines = []
        stop_markers = ("related articles", "for further study", "return to:", "subscribe to")
        for line in lines:
            s = line.strip()
            if not s:
                continue
            low = s.lower()
            if "answer" in low and len(s) < 35:
                in_answer = True
                continue
            if in_answer:
                if any(m in low for m in stop_markers):
                    break
                if low.startswith("home") or low.startswith("content index"):
                    continue
                answer_lines.append(s)
        answer = "\n\n".join(answer_lines).strip()

    return question or "(No question extracted)", answer or "(No answer extracted)"


async def fetch_html(client: httpx.AsyncClient, url: str) -> str | None:
    """Fetch HTML; return None on failure."""
    try:
        r = await client.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  Error {url[:55]}...: {e!r}")
        return None


async def crawl_for_links(client: httpx.AsyncClient, seed_urls: list[str]) -> set[str]:
    """Crawl seed + index pages to collect Q&A page links."""
    all_qa = set()
    to_crawl = set()
    for u in seed_urls:
        if u.startswith("http") and "gotquestions.org" in u and is_gotquestions_url(u):
            to_crawl.add(u)
    crawled = set()

    while to_crawl:
        if MAX_PAGES and len(all_qa) >= min(MAX_PAGES * 2, 50):
            print(f"  (early stop: {len(all_qa)} Q&A links collected)")
            break
        url = to_crawl.pop()
        if url in crawled:
            continue
        crawled.add(url)
        html = await fetch_html(client, url)
        if html:
            qa_links, index_links = extract_links(html, url)
            all_qa.update(qa_links)
            for idx in index_links:
                if idx not in crawled:
                    to_crawl.add(idx)
            print(f"  [{len(crawled)}] {url[:65]}... -> {len(qa_links)} Q&A, {len(index_links)} index")
        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

    return all_qa


async def crawl_qa_page(
    client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore, results: list
) -> None:
    """Fetch a Q&A page and append to results."""
    async with sem:
        html = await fetch_html(client, url)
        if html:
            q, a = extract_question_answer(html, url)
            results.append({
                "Question": q,
                "Answer": a,
                "URL": url,
                "Category": urlparse(url).path.split("/")[-1].replace(".html", "")[:80]
            })
            print(f"  OK  {q[:55]}...")
        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)


async def main():
    output_dir = Path(__file__).parent
    output_file = output_dir / f"GotQuestions_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    print("\n" + "=" * 70)
    print("GOTQUESTIONS.ORG Q&A CRAWLER (httpx)")
    print("=" * 70)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        # Phase 1: Collect Q&A links
        print("\nPhase 1: Collecting Q&A page links...")
        qa_urls = await crawl_for_links(client, SEED_URLS)
        qa_list = sorted(qa_urls)
        if MAX_PAGES:
            qa_list = qa_list[:MAX_PAGES]
            print(f"\nCrawling first {len(qa_list)} Q&A pages (limit set).")
        else:
            print(f"\nFound {len(qa_list)} unique Q&A pages to crawl.")

        if not qa_list:
            print("No Q&A pages found. Exiting.")
            return

        # Phase 2: Crawl each Q&A page
        print("\nPhase 2: Crawling Q&A pages...")
        results = []
        sem = asyncio.Semaphore(5)  # Concurrency
        tasks = [crawl_qa_page(client, u, sem, results) for u in qa_list]
        await asyncio.gather(*tasks)

        # Phase 3: Export to Excel
        if results:
            df = pd.DataFrame(results)
            df = df.drop_duplicates(subset=["URL"], keep="first")
            df = df.sort_values("URL")
            df.to_excel(output_file, index=False, engine="openpyxl")
            print("\n" + "=" * 70)
            print("EXPORT COMPLETE")
            print("=" * 70)
            print(f"Rows: {len(df)}")
            print(f"File: {output_file}")
        else:
            print("\nNo Q&A data extracted.")


if __name__ == "__main__":
    import sys
    limit = 0
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 20
    if limit:
        globals()["MAX_PAGES"] = limit
    asyncio.run(main())
