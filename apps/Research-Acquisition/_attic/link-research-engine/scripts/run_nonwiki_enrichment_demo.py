from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from link_research_engine.modules.role_engine import (
    CandidateLink,
    classify_link_role,
    load_role_rules,
)
from link_research_engine.modules.search_providers import (
    duckduckgo_html_search,
    exa_browser_query_hint,
    get_session,
)


CASE_CSV = Path(r"D:\GitHub\crawl4ai\case_lists\conspiracy_cases_master.csv")
OUT_CSV = ROOT / "data" / "output" / "nonwiki_enrichment_demo.csv"
OUT_JSON = ROOT / "data" / "output" / "nonwiki_enrichment_demo_summary.json"
RULES_JSON = ROOT / "config" / "source_role_rules.example.json"
REQUEST_DELAY = 0.8


def load_cases(limit: int = 5, start: int = 0) -> list[dict[str, str]]:
    with CASE_CSV.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows[start : start + limit]


def main(limit: int = 5, start: int = 0) -> None:
    rules = load_role_rules(str(RULES_JSON))
    session = get_session()
    cases = load_cases(limit=limit, start=start)

    fieldnames = [
        "case_id",
        "case_title",
        "provider",
        "discovery_query",
        "url",
        "title",
        "snippet",
        "source_domain",
        "role",
        "score",
        "keep",
        "reason",
        "provider_hint",
    ]
    rows: list[dict[str, str | int | bool]] = []

    for index, case in enumerate(cases, start=1):
        case_title = case["case_title"]
        query = f"{case_title} evidence timeline documents"
        print(f"[{index}/{len(cases)}] {case_title}", flush=True)
        results = duckduckgo_html_search(
            session,
            query,
            max_results=rules.get("max_results_per_query", 5),
        )
        time.sleep(REQUEST_DELAY)

        for result in results:
            candidate = CandidateLink(
                case_title=case_title,
                url=result.url,
                title=result.title,
                snippet=result.snippet,
                provider=result.provider,
            )
            decision = classify_link_role(candidate, rules)
            rows.append(
                {
                    "case_id": case["case_id"],
                    "case_title": case_title,
                    "provider": result.provider,
                    "discovery_query": query,
                    "url": result.url,
                    "title": result.title,
                    "snippet": result.snippet,
                    "source_domain": decision.source_domain,
                    "role": decision.role,
                    "score": decision.score,
                    "keep": decision.keep,
                    "reason": decision.reason,
                    "provider_hint": exa_browser_query_hint(query),
                }
            )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    OUT_JSON.write_text(
        json.dumps(
            {
                "cases_processed": len(cases),
                "rows_written": len(rows),
                "rules_path": str(RULES_JSON),
                "output_csv": str(OUT_CSV),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved enrichment demo CSV to {OUT_CSV}")
    print(f"Saved enrichment summary to {OUT_JSON}")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    main(limit=limit, start=start)
