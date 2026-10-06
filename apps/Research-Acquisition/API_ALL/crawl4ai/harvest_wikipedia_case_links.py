"""
Purpose: Build a Wikipedia-first link inventory for case titles in the master case list.
Inputs: conspiracy_cases_master.csv or conspiracy_cases_master.txt
Outputs: case_links_master.csv and a JSON harvest summary
Master Equation Relation: None - external research intake utility.
Date: 2026-04-05
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(r"D:\GitHub\crawl4ai\case_lists")
MASTER_CSV = BASE_DIR / "conspiracy_cases_master.csv"
OUT_CSV = BASE_DIR / "case_links_master.csv"
OUT_JSON = BASE_DIR / "case_links_harvest_summary.json"
USER_AGENT = "OpenIntelResearchBot/0.1 (respectful harvesting; contact local operator)"
MAX_LINKS_PER_CASE = 20
REQUEST_DELAY = 0.6


@dataclass
class CaseRow:
    case_id: str
    case_title: str
    priority_order: int


def load_cases(limit: int | None = None, start: int = 0) -> list[CaseRow]:
    rows: list[CaseRow] = []
    with MASTER_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                CaseRow(
                    case_id=row["case_id"],
                    case_title=row["case_title"],
                    priority_order=int(row["priority_order"]),
                )
            )
    if start:
        rows = rows[start:]
    return rows[:limit] if limit else rows


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def wikipedia_search_url(title: str) -> str:
    return f"https://en.wikipedia.org/w/index.php?search={quote(title)}&title=Special:Search&ns0=1"


def wikipedia_api_search(session: requests.Session, query: str) -> tuple[str | None, str | None]:
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 1,
        "format": "json",
    }
    resp = session.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    hits = data.get("query", {}).get("search", [])
    if not hits:
        return None, None
    title = hits[0]["title"]
    page_url = f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
    return title, page_url


def harvest_article_links(session: requests.Session, article_url: str, max_links: int) -> list[dict[str, str]]:
    resp = session.get(article_url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.select_one("#mw-content-text")
    if not content:
        return []

    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for anchor in content.select("a[href]"):
        href = anchor.get("href", "")
        text = anchor.get_text(" ", strip=True)
        if not href.startswith("/wiki/"):
            continue
        if ":" in href:
            continue
        absolute = urljoin("https://en.wikipedia.org", href)
        if absolute in seen:
            continue
        seen.add(absolute)
        rows.append(
            {
                "url": absolute,
                "source_domain": "en.wikipedia.org",
                "source_type": "wikipedia_internal",
                "link_label": text[:180],
            }
        )
        if len(rows) >= max_links:
            break
    return rows


def merge_existing_rows(existing_path: Path) -> list[dict[str, str]]:
    if not existing_path.exists():
        return []
    with existing_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for row in rows:
        key = (row["case_id"], row["url"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def main(limit: int | None = None, start: int = 0) -> None:
    cases = load_cases(limit=limit, start=start)
    session = get_session()
    written_rows: list[dict[str, str]] = []
    summary: list[dict[str, str | int | None]] = []

    for idx, case in enumerate(cases, start=1):
        print(f"[{idx}/{len(cases)}] {case.case_title}", flush=True)
        matched_title, page_url = wikipedia_api_search(session, case.case_title)
        time.sleep(REQUEST_DELAY)

        if not page_url:
            summary.append(
                {
                    "case_id": case.case_id,
                    "case_title": case.case_title,
                    "matched_title": None,
                    "page_url": None,
                    "links_added": 0,
                }
            )
            continue

        seed_row = {
            "case_id": case.case_id,
            "case_title": case.case_title,
            "matched_title": matched_title or "",
            "discovery_method": "wikipedia_search",
            "url": page_url,
            "source_domain": "en.wikipedia.org",
            "source_type": "wikipedia_primary",
            "priority": 1,
            "link_label": matched_title or case.case_title,
            "notes": "",
        }
        written_rows.append(seed_row)

        related = harvest_article_links(session, page_url, MAX_LINKS_PER_CASE - 1)
        time.sleep(REQUEST_DELAY)
        for rel_idx, item in enumerate(related, start=2):
            written_rows.append(
                {
                    "case_id": case.case_id,
                    "case_title": case.case_title,
                    "matched_title": matched_title or "",
                    "discovery_method": "wikipedia_article_links",
                    "url": item["url"],
                    "source_domain": item["source_domain"],
                    "source_type": item["source_type"],
                    "priority": rel_idx,
                    "link_label": item["link_label"],
                    "notes": "",
                }
            )

        summary.append(
            {
                "case_id": case.case_id,
                "case_title": case.case_title,
                "matched_title": matched_title,
                "page_url": page_url,
                "links_added": 1 + len(related),
            }
        )

    batch_csv = BASE_DIR / f"case_links_batch_{start}_{len(cases)}.csv"
    batch_json = BASE_DIR / f"case_links_batch_{start}_{len(cases)}_summary.json"

    with batch_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "case_title",
                "matched_title",
                "discovery_method",
                "url",
                "source_domain",
                "source_type",
                "priority",
                "link_label",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(written_rows)

    existing_master_rows = merge_existing_rows(OUT_CSV)
    merged_master_rows = dedupe_rows(existing_master_rows + written_rows)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "case_title",
                "matched_title",
                "discovery_method",
                "url",
                "source_domain",
                "source_type",
                "priority",
                "link_label",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(merged_master_rows)

    batch_json.write_text(
        json.dumps(
            {
                "start_offset": start,
                "cases_processed": len(cases),
                "max_links_per_case": MAX_LINKS_PER_CASE,
                "rows_written": len(written_rows),
                "summary": summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    OUT_JSON.write_text(
        json.dumps(
            {
                "last_batch_start_offset": start,
                "last_batch_cases_processed": len(cases),
                "master_rows_written": len(merged_master_rows),
                "batch_rows_written": len(written_rows),
                "batch_file": str(batch_csv),
                "batch_summary_file": str(batch_json),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Saved batch rows to {batch_csv}", flush=True)
    print(f"Saved batch summary to {batch_json}", flush=True)
    print(f"Updated master rows in {OUT_CSV}", flush=True)
    print(f"Updated master summary in {OUT_JSON}", flush=True)


if __name__ == "__main__":
    import sys

    limit = None
    start = 0
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            limit = None
    if len(sys.argv) > 2:
        try:
            start = int(sys.argv[2])
        except ValueError:
            start = 0
    main(limit=limit, start=start)
