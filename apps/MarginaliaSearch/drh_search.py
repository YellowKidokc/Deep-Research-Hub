#!/usr/bin/env python3
"""Deep Research Hub: Search > Marginalia links, through Marginalia's official API (v2).

    python drh_search.py "entropy and grace" --out <data>/search
    python drh_search.py "entropy and grace" --out <data>/search --count 50 --read 10

Writes <out>/<query-slug>/<stamp>/:
    results.json   [{rank, url, title, description}]
    links.txt      one URL per line (feed it to the Links tab or anything else)
    results.md     readable list
    pages/         with --read N: the top N results as markdown, via the local Deepcrawl worker

API key: MARGINALIA_API_KEY in the environment, else the shared "public" key, which is often at its
per-minute limit (HTTP 429). A free personal key for non-commercial use: ask kontakt@marginalia.nu.
On 429 this waits and retries a few times. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

API = "https://api2.marginalia-search.com/search"
DEEPCRAWL = "http://127.0.0.1:8080"


def slug(text: str, n: int = 60) -> str:
    return (re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()[:n].rstrip("-")) or "query"


def search(query: str, count: int, page: int, key: str, tries: int = 5) -> dict:
    url = API + "?" + urllib.parse.urlencode({"query": query, "count": count, "page": page})
    wait = 15
    for attempt in range(1, tries + 1):
        req = urllib.request.Request(url, headers={"API-Key": key, "User-Agent": "deep-research-hub/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:200]
            if exc.code == 429 and "daily" in body.lower():
                sys.exit(f"Marginalia: {body.strip()} for the {'personal' if key != 'public' else 'shared public'} key. "
                         "Waiting will not help today. Set MARGINALIA_API_KEY to a personal key "
                         "(free for non-commercial use: kontakt@marginalia.nu), then restart the hub.")
            if exc.code == 429 and attempt < tries:
                print(f"  rate limited ({body.strip()}); waiting {wait}s, try {attempt + 1}/{tries}", flush=True)
                time.sleep(wait)
                wait = min(wait * 2, 120)
                continue
            if exc.code == 429:
                sys.exit("Marginalia's shared 'public' key is at its per-minute limit. Try again in a few minutes, "
                         "or set MARGINALIA_API_KEY to a personal key (free for non-commercial use: kontakt@marginalia.nu).")
            if exc.code in (401, 403):
                sys.exit(f"Marginalia rejected the API key ({exc.code}): {body}")
            raise
    raise RuntimeError("unreachable")


def read_markdown(url: str) -> dict:
    req = urllib.request.Request(DEEPCRAWL + "/read", data=json.dumps({"url": url}).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Get result links from Marginalia Search.")
    ap.add_argument("query")
    ap.add_argument("--out", required=True)
    ap.add_argument("--count", type=int, default=30, help="results to fetch (max 100)")
    ap.add_argument("--read", type=int, default=0, help="also read the top N results to markdown via Deepcrawl")
    a = ap.parse_args()

    key = os.environ.get("MARGINALIA_API_KEY", "").strip() or "public"
    count = max(1, min(a.count, 100))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run = Path(a.out) / slug(a.query) / stamp
    run.mkdir(parents=True, exist_ok=True)
    print(f"marginalia: {a.query!r}  count={count}  key={'personal' if key != 'public' else 'public (shared)'}", flush=True)

    data = search(a.query, count, 1, key)
    results = [{"rank": i + 1, "url": r.get("url", ""), "title": r.get("title", ""),
                "description": r.get("description", "")} for i, r in enumerate(data.get("results") or [])]
    (run / "results.json").write_text(json.dumps({"query": a.query, "stamp": stamp, "source": "marginalia-search.com",
                                                  "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    (run / "links.txt").write_text("".join(r["url"] + "\n" for r in results), encoding="utf-8")
    md = [f"# Marginalia: {a.query}", "", f"{stamp} - {len(results)} result(s)", ""]
    md += [f"{r['rank']}. [{r['title'] or r['url']}]({r['url']})" + (f" - {r['description']}" if r["description"] else "")
           for r in results]
    for r in results:
        print(f"  {r['rank']:3d}. {r['url']}", flush=True)

    if a.read and results:
        pages = run / "pages"
        pages.mkdir(exist_ok=True)
        try:
            urllib.request.urlopen(DEEPCRAWL + "/", timeout=5)
        except urllib.error.HTTPError:
            pass
        except Exception:
            print("  (Deepcrawl worker not running - links saved, pages skipped. Start it from the hub's Home.)")
            a.read = 0
        md += ["", "## Pages read", ""]
        for r in results[: a.read]:
            try:
                page = read_markdown(r["url"])
                name = f"{r['rank']:03d}_{slug(page.get('title') or r['title'] or r['url'])}.md"
                head = {"url": r["url"], "title": page.get("title") or r["title"], "query": a.query,
                        "rank": str(r["rank"]), "fetched": datetime.now().isoformat(timespec="seconds")}
                (pages / name).write_text("---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n"
                                                            for k, v in head.items()) + "---\n\n"
                                          + (page.get("markdown") or ""), encoding="utf-8")
                md.append(f"- [{head['title'] or r['url']}](pages/{name})")
                print(f"  read {r['rank']:3d} -> pages/{name}", flush=True)
            except Exception as exc:
                md.append(f"- {r['url']} (read failed: {str(exc)[:120]})")
                print(f"  ! read {r['url']}: {exc}", flush=True)
            time.sleep(0.5)
    (run / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"done: {len(results)} link(s) -> {run}")
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
