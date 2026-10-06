from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "gclid",
    "fbclid",
    "ref",
    "ref_src",
}


@dataclass
class DedupeResult:
    unique_rows: list[dict[str, str]]
    duplicate_rows: list[dict[str, str]]
    grouped_domains: dict[str, list[dict[str, str]]]


def canonicalize_url(url: str) -> str:
    """Normalize URL for dedupe and grouping."""
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_QUERY_KEYS
    ]
    query_pairs.sort()
    query = urlencode(query_pairs)
    return urlunparse((scheme, netloc, path, "", query, ""))


def dedupe_rows(
    rows: list[dict[str, str]],
    *,
    score_field: str = "score",
    case_field: str = "case_id",
    url_field: str = "url",
) -> DedupeResult:
    """Dedupe rows by canonical URL per case, keeping the highest score."""
    best_by_key: dict[tuple[str, str], dict[str, str]] = {}
    duplicate_rows: list[dict[str, str]] = []

    for row in rows:
        canonical = canonicalize_url(row[url_field])
        row_with_canonical = dict(row)
        row_with_canonical["canonical_url"] = canonical
        key = (row_with_canonical.get(case_field, ""), canonical)
        existing = best_by_key.get(key)
        if existing is None:
            best_by_key[key] = row_with_canonical
            continue

        new_score = int(row_with_canonical.get(score_field, 0) or 0)
        old_score = int(existing.get(score_field, 0) or 0)
        if new_score > old_score:
            duplicate_rows.append(existing)
            best_by_key[key] = row_with_canonical
        else:
            duplicate_rows.append(row_with_canonical)

    unique_rows = list(best_by_key.values())
    grouped_domains: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in unique_rows:
        domain = urlparse(row["canonical_url"]).netloc
        grouped_domains[domain].append(row)

    return DedupeResult(
        unique_rows=unique_rows,
        duplicate_rows=duplicate_rows,
        grouped_domains=dict(grouped_domains),
    )
