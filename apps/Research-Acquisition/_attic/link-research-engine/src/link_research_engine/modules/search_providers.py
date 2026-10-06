from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, quote, urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    provider: str


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def duckduckgo_html_search(session: requests.Session, query: str, max_results: int = 5) -> list[SearchResult]:
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    response = session.get(url, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []
    for result in soup.select(".result"):
        anchor = result.select_one(".result__title a")
        snippet = result.select_one(".result__snippet")
        if not anchor:
            continue
        href = anchor.get("href", "").strip()
        title = anchor.get_text(" ", strip=True)
        if not href:
            continue
        parsed = urlparse(href)
        if "duckduckgo.com" in parsed.netloc and parsed.path == "/l/":
            params = parse_qs(parsed.query)
            href = params.get("uddg", [href])[0]
        if "duckduckgo.com/y.js" in href:
            continue
        results.append(
            SearchResult(
                url=href,
                title=title[:220],
                snippet=snippet.get_text(" ", strip=True)[:300] if snippet else "",
                provider="duckduckgo_html",
            )
        )
        if len(results) >= max_results:
            break
    return results


def exa_browser_query_hint(query: str) -> str:
    return (
        "Optional provider: Exa via Playwright/browser automation. "
        f"Use this query in Exa search UI: {query}"
    )
