"""
Purpose: Harvest non-Wikipedia source links for case titles using curated source hubs.
Inputs: Master case list, credible source hub list, optional limit and start offset.
Outputs: case_links_credible_master.csv plus per-batch CSV/JSON summaries.
Master Equation Relation: None - external research intake utility.
Date: 2026-04-05
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(r"D:\GitHub\crawl4ai\case_lists")
MASTER_CSV = BASE_DIR / "conspiracy_cases_master.csv"
HUBS_CSV = BASE_DIR / "credible_source_hubs.csv"
OUT_CSV = BASE_DIR / "case_links_credible_master.csv"
OUT_JSON = BASE_DIR / "case_links_credible_summary.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"
REQUEST_DELAY = 0.7
TOP_RESULTS_PER_SOURCE = 1


@dataclass
class CaseRow:
    case_id: str
    case_title: str
    priority_order: int


@dataclass
class SourceHub:
    source_id: str
    source_name: str
    base_domain: str
    source_type: str
    credibility_tier: str


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


def load_hubs() -> list[SourceHub]:
    hubs: list[SourceHub] = []
    with HUBS_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            hubs.append(
                SourceHub(
                    source_id=row["source_id"],
                    source_name=row["source_name"],
                    base_domain=row["base_domain"],
                    source_type=row["source_type"],
                    credibility_tier=row["credibility_tier"],
                )
            )
    return hubs


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def duckduckgo_search(session: requests.Session, query: str) -> list[dict[str, str]]:
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    response = session.get(url, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows: list[dict[str, str]] = []
    for result in soup.select(".result"):
        anchor = result.select_one(".result__title a")
        snippet = result.select_one(".result__snippet")
        if not anchor:
            continue
        href = anchor.get("href", "").strip()
        title = anchor.get_text(" ", strip=True)
        if not href:
            continue
        rows.append(
            {
                "url": href,
                "link_label": title[:220],
                "notes": snippet.get_text(" ", strip=True)[:300] if snippet else "",
            }
        )
        if len(rows) >= TOP_RESULTS_PER_SOURCE:
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
    hubs = load_hubs()
    session = get_session()
    written_rows: list[dict[str, str]] = []
    summary: list[dict[str, str | int]] = []

    for idx, case in enumerate(cases, start=1):
        print(f"[{idx}/{len(cases)}] {case.case_title}", flush=True)
        added_for_case = 0
        for hub in hubs:
            query = f'{case.case_title} site:{hub.base_domain}'
            try:
                results = duckduckgo_search(session, query)
            except Exception:
                results = []
            time.sleep(REQUEST_DELAY)
            for result_index, result in enumerate(results, start=1):
                written_rows.append(
                    {
                        "case_id": case.case_id,
                        "case_title": case.case_title,
                        "matched_title": "",
                        "discovery_method": f"duckduckgo_site_search:{hub.source_id}",
                        "url": result["url"],
                        "source_domain": hub.base_domain,
                        "source_type": hub.source_type,
                        "priority": result_index,
                        "link_label": result["link_label"],
                        "notes": result["notes"],
                    }
                )
                added_for_case += 1
        summary.append(
            {
                "case_id": case.case_id,
                "case_title": case.case_title,
                "links_added": added_for_case,
            }
        )

    batch_csv = BASE_DIR / f"case_links_credible_batch_{start}_{len(cases)}.csv"
    batch_json = BASE_DIR / f"case_links_credible_batch_{start}_{len(cases)}_summary.json"

    fieldnames = [
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
    ]

    with batch_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(written_rows)

    existing_master_rows = merge_existing_rows(OUT_CSV)
    merged_master_rows = dedupe_rows(existing_master_rows + written_rows)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_master_rows)

    batch_json.write_text(
        json.dumps(
            {
                "start_offset": start,
                "cases_processed": len(cases),
                "source_hubs": len(hubs),
                "batch_rows_written": len(written_rows),
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
