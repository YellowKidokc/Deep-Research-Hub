from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from link_research_engine.modules.dedupe import dedupe_rows


IN_CSV = ROOT / "data" / "output" / "nonwiki_enrichment_demo.csv"
OUT_CLEAN_CSV = ROOT / "data" / "output" / "nonwiki_enrichment_demo_deduped.csv"
OUT_DUPS_CSV = ROOT / "data" / "output" / "nonwiki_enrichment_demo_duplicates.csv"
OUT_SUMMARY_JSON = ROOT / "data" / "output" / "nonwiki_enrichment_demo_dedupe_summary.json"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    with IN_CSV.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    result = dedupe_rows(rows)
    OUT_CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)

    _write_csv(OUT_CLEAN_CSV, result.unique_rows)
    _write_csv(OUT_DUPS_CSV, result.duplicate_rows)

    summary = {
        "input_rows": len(rows),
        "unique_rows": len(result.unique_rows),
        "duplicates_removed": len(result.duplicate_rows),
        "domain_groups": {domain: len(items) for domain, items in result.grouped_domains.items()},
        "output_clean_csv": str(OUT_CLEAN_CSV),
        "output_duplicates_csv": str(OUT_DUPS_CSV),
    }
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote deduped rows to {OUT_CLEAN_CSV}")
    print(f"Wrote duplicate rows to {OUT_DUPS_CSV}")
    print(f"Wrote dedupe summary to {OUT_SUMMARY_JSON}")


if __name__ == "__main__":
    main()
