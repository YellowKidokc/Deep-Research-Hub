from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from re import sub

from link_research_engine.modules.dedupe import dedupe_rows
from link_research_engine.modules.discovery import DiscoveryRequest, discover_links
from link_research_engine.modules.exporter import ensure_output_dir, write_csv_rows
from link_research_engine.modules.intake import describe_questions


def _slug(text: str) -> str:
    collapsed = sub(r"[^a-zA-Z0-9]+", "_", text.strip()).strip("_")
    return collapsed.lower() or "case"


def _load_trusted_domains(config_path: str | None) -> list[str] | None:
    if not config_path:
        return None
    config_data = json.loads(Path(config_path).read_text(encoding="utf-8"))
    return config_data.get("trusted_domains")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run link discovery pipeline for a single case name.")
    parser.add_argument("case_name", nargs="?", help="Case name to research.")
    parser.add_argument("--max-wikipedia-links", type=int, default=25)
    parser.add_argument("--max-results-per-domain", type=int, default=10)
    parser.add_argument("--trusted-domains-config", default=None)
    parser.add_argument("--output-dir", default="data/output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.case_name:
        print("Link Research Engine")
        print("====================")
        print("Provide a case name to run discovery.")
        for line in describe_questions():
            print(f"- {line}")
        return

    trusted_domains = _load_trusted_domains(args.trusted_domains_config)
    request = DiscoveryRequest(
        case_title=args.case_name,
        max_wikipedia_links=args.max_wikipedia_links,
        max_results_per_domain=args.max_results_per_domain,
        trusted_domains=trusted_domains,
    )
    discovered_rows = discover_links(request)
    dedupe_result = dedupe_rows(discovered_rows, case_field="case_title")
    output_dir = ensure_output_dir(args.output_dir)

    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    base_name = f"{_slug(args.case_name)}_{stamp}"
    raw_path = output_dir / f"{base_name}_discovery_raw.csv"
    deduped_path = output_dir / f"{base_name}_discovery_deduped.csv"
    duplicates_path = output_dir / f"{base_name}_discovery_duplicates.csv"
    summary_path = output_dir / f"{base_name}_summary.json"

    write_csv_rows(raw_path, discovered_rows)
    write_csv_rows(deduped_path, dedupe_result.unique_rows)
    write_csv_rows(duplicates_path, dedupe_result.duplicate_rows)
    summary = {
        "case_name": args.case_name,
        "raw_rows": len(discovered_rows),
        "deduped_rows": len(dedupe_result.unique_rows),
        "duplicate_rows": len(dedupe_result.duplicate_rows),
        "domain_groups": {domain: len(items) for domain, items in dedupe_result.grouped_domains.items()},
        "outputs": {
            "raw_csv": str(raw_path),
            "deduped_csv": str(deduped_path),
            "duplicates_csv": str(duplicates_path),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Case: {args.case_name}")
    print(f"Raw discovery rows: {len(discovered_rows)}")
    print(f"Deduped rows: {len(dedupe_result.unique_rows)}")
    print(f"Duplicate rows removed: {len(dedupe_result.duplicate_rows)}")
    print(f"Wrote raw CSV: {raw_path}")
    print(f"Wrote deduped CSV: {deduped_path}")
    print(f"Wrote duplicates CSV: {duplicates_path}")
    print(f"Wrote summary JSON: {summary_path}")


if __name__ == "__main__":
    main()
