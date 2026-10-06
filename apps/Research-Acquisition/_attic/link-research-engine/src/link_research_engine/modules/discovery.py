from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from link_research_engine.modules.search_providers import duckduckgo_html_search, get_session

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_PAGE_BASE = "https://en.wikipedia.org/wiki/"

DEFAULT_TRUSTED_DOMAINS = [
    "archives.gov",
    "justice.gov",
    "congress.gov",
    "supremecourt.gov",
    "law.cornell.edu",
    "harvardlawreview.org",
    "stanfordlawreview.org",
]


@dataclass
class DiscoveryRequest:
    case_title: str
    max_wikipedia_links: int = 25
    max_results_per_domain: int = 10
    trusted_domains: list[str] | None = None
    include_wikipedia: bool = True
    include_trusted_hubs: bool = True


@dataclass
class CandidateLink:
    url: str
    title: str
    domain: str
    source_type: str
    provider: str
    case_title: str
    snippet: str = ""


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _resolve_wikipedia_page_title(session: requests.Session, case_title: str) -> str | None:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": case_title,
        "srlimit": 1,
        "utf8": 1,
        "format": "json",
    }
    try:
        response = session.get(WIKIPEDIA_API, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return None
    items = response.json().get("query", {}).get("search", [])
    if not items:
        return None
    return items[0]["title"]


def discover_wikipedia_links(
    session: requests.Session,
    case_title: str,
    *,
    max_links: int = 25,
) -> list[CandidateLink]:
    page_title = _resolve_wikipedia_page_title(session, case_title)
    if not page_title:
        return []

    params = {
        "action": "parse",
        "page": page_title,
        "prop": "text",
        "format": "json",
    }
    try:
        response = session.get(WIKIPEDIA_API, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return []
    html = response.json().get("parse", {}).get("text", {}).get("*", "")
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links: list[CandidateLink] = []
    seen: set[str] = set()
    for anchor in soup.select(".mw-parser-output a.external"):
        href = anchor.get("href", "").strip()
        if not href or href in seen:
            continue
        seen.add(href)
        title = anchor.get_text(" ", strip=True) or href
        links.append(
            CandidateLink(
                url=href,
                title=title[:220],
                domain=_domain(href),
                source_type="wikipedia",
                provider="wikipedia_article_outlinks",
                case_title=case_title,
            )
        )
        if len(links) >= max_links:
            break

    article_url = f"{WIKIPEDIA_PAGE_BASE}{page_title.replace(' ', '_')}"
    links.insert(
        0,
        CandidateLink(
            url=article_url,
            title=page_title,
            domain=_domain(article_url),
            source_type="wikipedia",
            provider="wikipedia_page",
            case_title=case_title,
            snippet="Primary article used for outbound link extraction.",
        ),
    )
    return links


def discover_trusted_hub_links(
    session: requests.Session,
    case_title: str,
    *,
    trusted_domains: list[str] | None = None,
    max_results_per_domain: int = 3,
) -> list[CandidateLink]:
    domains = trusted_domains or DEFAULT_TRUSTED_DOMAINS
    links: list[CandidateLink] = []
    for domain in domains:
        query = f"{case_title} site:{domain}"
        try:
            domain_results = duckduckgo_html_search(session, query, max_results=max_results_per_domain)
        except requests.RequestException:
            domain_results = []
        for result in domain_results:
            links.append(
                CandidateLink(
                    url=result.url,
                    title=result.title,
                    domain=_domain(result.url),
                    source_type="trusted_hub",
                    provider=f"{result.provider}:site_filter",
                    case_title=case_title,
                    snippet=result.snippet,
                )
            )
    return links


def discover_links(request: DiscoveryRequest) -> list[dict[str, str]]:
    session = get_session()
    discovered: list[CandidateLink] = []
    if request.include_wikipedia:
        discovered.extend(
            discover_wikipedia_links(
                session,
                request.case_title,
                max_links=request.max_wikipedia_links,
            )
        )
    if request.include_trusted_hubs:
        discovered.extend(
            discover_trusted_hub_links(
                session,
                request.case_title,
                trusted_domains=request.trusted_domains,
                max_results_per_domain=request.max_results_per_domain,
            )
        )
    return [asdict(item) for item in discovered]
