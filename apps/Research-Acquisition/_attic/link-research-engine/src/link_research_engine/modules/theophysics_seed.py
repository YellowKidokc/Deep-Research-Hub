from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SeedPage:
    page_id: str
    title: str
    export_path: str
    source_path: str
    full_url: str
    link_count: int
    backlink_count: int
    source_size: int
    modified_time: int | None
    show_in_tree: bool
    page_type: str


@dataclass
class SeedEdge:
    source_page_id: str
    source_title: str
    target_url: str
    target_type: str
    target_domain: str


def _classify_target(url: str) -> tuple[str, str]:
    lower = url.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        host = lower.split("/")[2]
        return "external", host
    if lower.endswith(".html"):
        return "internal_page", "local_export"
    return "asset_or_other", "local_export"


def load_theophysics_seed_index(metadata_path: str) -> tuple[list[SeedPage], list[SeedEdge]]:
    path = Path(metadata_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    webpages = payload.get("webpages", {})

    pages: list[SeedPage] = []
    edges: list[SeedEdge] = []

    for page_id, page in webpages.items():
        links = page.get("links", []) or []
        backlinks = page.get("backlinks", []) or []
        seed_page = SeedPage(
            page_id=page_id,
            title=page.get("title", page_id),
            export_path=page.get("exportPath", ""),
            source_path=page.get("sourcePath", ""),
            full_url=page.get("fullURL", ""),
            link_count=len(links),
            backlink_count=len(backlinks),
            source_size=int(page.get("sourceSize", 0) or 0),
            modified_time=page.get("modifiedTime"),
            show_in_tree=bool(page.get("showInTree", False)),
            page_type=page.get("type", "unknown"),
        )
        pages.append(seed_page)

        for link in links:
            target_type, target_domain = _classify_target(link)
            edges.append(
                SeedEdge(
                    source_page_id=page_id,
                    source_title=seed_page.title,
                    target_url=link,
                    target_type=target_type,
                    target_domain=target_domain,
                )
            )

    pages.sort(key=lambda row: row.title.lower())
    edges.sort(key=lambda row: (row.source_title.lower(), row.target_url.lower()))
    return pages, edges
