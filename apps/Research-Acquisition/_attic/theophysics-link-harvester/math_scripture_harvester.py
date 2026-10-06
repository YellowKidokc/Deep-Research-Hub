"""Provenance-first discovery of mathematical work related to Scripture and theology.

This program searches scholarly metadata APIs. It does not bypass paywalls,
download arbitrary copyrighted full text, or treat keyword overlap as evidence.
Default mode is a dry-run that prints the query plan. Use --run for live calls.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
DEFAULT_QUERIES = ROOT / "math_scripture_queries.json"

THEOLOGY_TERMS = {
    "god", "divine", "theology", "theological", "christ", "jesus",
    "christology", "trinity", "scripture", "biblical", "bible", "gospel",
    "atonement", "resurrection", "incarnation", "grace", "logos", "creation",
    "moral", "mercy", "justice", "forgiveness", "sin", "salvation",
}

MATH_TERMS = {
    "mathematical", "mathematics", "equation", "theorem", "proof", "axiom",
    "formal", "logic", "modal", "model", "topology", "algebra", "geometry",
    "category theory", "graph", "network", "bayesian", "probability",
    "statistical", "dynamical", "differential", "optimization", "game theory",
    "information theory", "entropy", "symmetry", "isomorphism", "semantics",
    "lean", "coq", "isabelle",
}

FORMAL_TERMS = {
    "theorem", "proof", "axiom", "formal logic", "formalized", "modal logic",
    "proof assistant", "lean", "coq", "isabelle", "type theory", "semantics",
}

EMPIRICAL_TERMS = {
    "experiment", "empirical", "dataset", "statistical", "regression", "survey",
    "correlation", "measurement", "observed", "sample", "network analysis",
}

CHALLENGE_TERMS = {
    "critique", "criticism", "counterexample", "countermodel", "fallacy",
    "objection", "problem", "against", "failure", "invalid", "numerology",
}


@dataclass
class Candidate:
    title: str
    url: str
    provider: str
    query_lane: str
    query: str
    retrieved_at: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    abstract: str = ""
    venue: str = ""
    doi: str = ""
    cited_by_count: int | None = None
    open_access_url: str = ""
    provider_id: str = ""
    source_type: str = "scholarly_metadata"
    math_signals: list[str] = field(default_factory=list)
    theology_signals: list[str] = field(default_factory=list)
    lane: str = "BACKGROUND"
    relevance_score: int = 0
    evidence_grade: str = "D"
    screening_status: str = "CANDIDATE"
    content_hash: str = ""
    ollama_model: str = ""
    ollama_status: str = "NOT_RUN"
    ollama_assessment: dict = field(default_factory=dict)
    ollama_consistency: str = "NOT_RUN"

    def finalize(self) -> "Candidate":
        text = f"{self.title} {self.abstract}".lower()
        self.math_signals = sorted(t for t in MATH_TERMS if contains_term(text, t))
        self.theology_signals = sorted(t for t in THEOLOGY_TERMS if contains_term(text, t))
        formal = sorted(t for t in FORMAL_TERMS if contains_term(text, t))
        empirical = sorted(t for t in EMPIRICAL_TERMS if contains_term(text, t))
        challenge = sorted(t for t in CHALLENGE_TERMS if contains_term(text, t))

        if challenge:
            self.lane = "CHALLENGE"
        elif formal and self.math_signals and self.theology_signals:
            self.lane = "FORMAL"
        elif empirical and self.math_signals and self.theology_signals:
            self.lane = "EMPIRICAL"
        elif self.math_signals and self.theology_signals:
            self.lane = "THEOLOGICAL_BRIDGE"
        else:
            self.lane = "BACKGROUND"

        score = 0
        score += min(30, 6 * len(self.math_signals))
        score += min(30, 6 * len(self.theology_signals))
        score += 10 if self.abstract else 0
        score += 8 if self.doi else 0
        score += 6 if self.venue else 0
        score += 6 if self.open_access_url else 0
        if self.lane in {"FORMAL", "EMPIRICAL", "CHALLENGE"}:
            score += 10
        self.relevance_score = min(100, score)

        self.screening_status = (
            "SCREEN" if self.math_signals and self.theology_signals
            else "BACKGROUND_ONLY"
        )

        if self.doi and self.abstract and self.relevance_score >= 70:
            self.evidence_grade = "A"
        elif (self.doi or self.provider_id) and self.relevance_score >= 55:
            self.evidence_grade = "B"
        elif self.relevance_score >= 40:
            self.evidence_grade = "C"
        else:
            self.evidence_grade = "D"

        canonical = json.dumps({
            "title": normalize_title(self.title), "doi": self.doi.lower(),
            "provider_id": self.provider_id, "abstract": self.abstract,
        }, sort_keys=True, ensure_ascii=False)
        self.content_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return self


def normalize_title(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def contains_term(text: str, term: str) -> bool:
    """Match complete words/phrases, never accidental substrings."""
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def clean_abstract(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def console_safe(value: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return value.encode(encoding, errors="backslashreplace").decode(encoding)


def get_json(url: str, user_agent: str, timeout: int = 30) -> dict:
    request = urllib.request.Request(url, headers={
        "User-Agent": user_agent,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_text(url: str, user_agent: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={
        "User-Agent": user_agent,
        "Accept": "application/atom+xml,application/xml,text/xml",
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def post_json(url: str, payload: dict, user_agent: str, timeout: int = 180) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"User-Agent": user_agent, "Content-Type": "application/json",
                 "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def assess_with_ollama(item: Candidate, base_url: str, model: str, agent: str) -> None:
    """Add an advisory local-model assessment without changing deterministic grades."""
    schema = {
        "relevant": "boolean",
        "claim_layer": "FORMAL|EMPIRICAL|THEOLOGICAL_BRIDGE|CHALLENGE|BACKGROUND",
        "mathematical_component": "short string",
        "theological_target": "short string",
        "reason": "one short sentence",
        "human_review_priority": "HIGH|MEDIUM|LOW",
    }
    prompt = f"""You screen research metadata for a Christian theophysics project.
Do not decide truth. Do not call analogy an isomorphism. Do not upgrade a theological
interpretation to physics or a formal model to empirical evidence. Return JSON only.

Required JSON schema:
{json.dumps(schema)}

Title: {item.title}
Abstract: {item.abstract[:5000]}
Provider: {item.provider}
Deterministic math signals: {item.math_signals}
Deterministic theology signals: {item.theology_signals}
"""
    response = post_json(base_url.rstrip("/") + "/api/generate", {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }, agent)
    parsed = json.loads(response.get("response", "{}"))
    if not isinstance(parsed, dict):
        raise ValueError("Ollama response was not a JSON object")
    item.ollama_model = model
    item.ollama_status = "REVIEWED"
    item.ollama_assessment = parsed
    ai_relevant = parsed.get("relevant") is True
    deterministic_intersection = bool(item.math_signals and item.theology_signals)
    item.ollama_consistency = (
        "CONSISTENT" if ai_relevant == deterministic_intersection
        else "CONFLICT_WITH_DETERMINISTIC_GATE"
    )


def run_ollama_pass(items: list[Candidate], base_url: str, model: str,
                    max_items: int, agent: str) -> list[dict]:
    errors = []
    # Review strongest intersections first; background items remain deterministic.
    selected = sorted(
        (item for item in items if item.screening_status == "SCREEN"),
        key=lambda x: (-x.relevance_score, x.title.lower()),
    )[:max_items]
    for index, item in enumerate(selected, 1):
        try:
            assess_with_ollama(item, base_url, model, agent)
            print(f"OLLAMA {index:3}/{len(selected):3} REVIEWED  {console_safe(item.title[:70])}")
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, json.JSONDecodeError) as exc:
            item.ollama_model = model
            item.ollama_status = "ERROR"
            error = {"title": item.title, "error": f"{type(exc).__name__}: {exc}"}
            errors.append(error)
            print(f"OLLAMA ERROR {console_safe(item.title[:60])}: {exc}", file=sys.stderr)
    return errors


def search_crossref(query: str, lane: str, limit: int, mailto: str, agent: str) -> list[Candidate]:
    params = {"query.bibliographic": query, "rows": str(limit), "select":
              "DOI,title,author,published,abstract,URL,container-title,is-referenced-by-count,type"}
    if mailto:
        params["mailto"] = mailto
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = get_json(url, agent)
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for item in data.get("message", {}).get("items", []):
        title = " ".join(item.get("title") or [])
        authors = [" ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip()
                   for a in item.get("author", [])]
        parts = (item.get("published") or {}).get("date-parts") or []
        year = parts[0][0] if parts and parts[0] else None
        doi = item.get("DOI", "")
        out.append(Candidate(
            title=title, url=item.get("URL") or (f"https://doi.org/{doi}" if doi else ""),
            provider="crossref", query_lane=lane, query=query, retrieved_at=now,
            authors=authors, year=year, abstract=clean_abstract(item.get("abstract", "")),
            venue="; ".join(item.get("container-title") or []), doi=doi,
            cited_by_count=item.get("is-referenced-by-count"), provider_id=doi,
        ).finalize())
    return out


def search_semantic_scholar(query: str, lane: str, limit: int, agent: str) -> list[Candidate]:
    params = {"query": query, "limit": str(min(limit, 100)),
              "fields": "paperId,title,abstract,authors,year,venue,url,externalIds,citationCount,openAccessPdf"}
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    data = get_json(url, agent)
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for item in data.get("data", []):
        external = item.get("externalIds") or {}
        oa = item.get("openAccessPdf") or {}
        out.append(Candidate(
            title=item.get("title", ""), url=item.get("url", ""), provider="semantic_scholar",
            query_lane=lane, query=query, retrieved_at=now,
            authors=[a.get("name", "") for a in item.get("authors", [])],
            year=item.get("year"), abstract=clean_abstract(item.get("abstract", "")),
            venue=item.get("venue", ""), doi=external.get("DOI", ""),
            cited_by_count=item.get("citationCount"), open_access_url=oa.get("url", ""),
            provider_id=item.get("paperId", ""),
        ).finalize())
    return out


def search_arxiv(query: str, lane: str, limit: int, agent: str) -> list[Candidate]:
    tokens = [t for t in re.findall(r"[A-Za-z0-9-]+", query.lower())
              if t not in {"a", "an", "and", "or", "the", "of", "in", "on", "for"}]
    # arXiv's API treats a quoted multiword query as one exact phrase. Requiring
    # every meaningful token is still precise without accidentally demanding
    # an unlikely literal title/abstract phrase.
    arxiv_query = " AND ".join(f"all:{token}" for token in tokens)
    params = {"search_query": arxiv_query, "start": "0", "max_results": str(limit),
              "sortBy": "relevance", "sortOrder": "descending"}
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    root = ET.fromstring(get_text(url, agent))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for entry in root.findall("a:entry", ns):
        entry_url = (entry.findtext("a:id", default="", namespaces=ns) or "").strip()
        published = entry.findtext("a:published", default="", namespaces=ns)
        year = int(published[:4]) if published[:4].isdigit() else None
        authors = [a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns)]
        out.append(Candidate(
            title=clean_abstract(entry.findtext("a:title", default="", namespaces=ns)),
            url=entry_url, provider="arxiv", query_lane=lane, query=query, retrieved_at=now,
            authors=authors, year=year,
            abstract=clean_abstract(entry.findtext("a:summary", default="", namespaces=ns)),
            venue="arXiv", provider_id=entry_url.rsplit("/", 1)[-1], open_access_url=entry_url,
        ).finalize())
    return out


def search_searxng(query: str, lane: str, limit: int, base_url: str, agent: str) -> list[Candidate]:
    params = {"q": query, "format": "json", "language": "en", "safesearch": "1"}
    url = base_url.rstrip("/") + "/search?" + urllib.parse.urlencode(params)
    data = get_json(url, agent)
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for item in data.get("results", [])[:limit]:
        out.append(Candidate(
            title=item.get("title", ""), url=item.get("url", ""), provider="searxng",
            query_lane=lane, query=query, retrieved_at=now,
            abstract=clean_abstract(item.get("content", "")), venue=item.get("engine", ""),
            provider_id=item.get("url", ""), source_type="web_discovery_metadata",
        ).finalize())
    return out


def deduplicate(items: Iterable[Candidate]) -> list[Candidate]:
    winners: dict[str, Candidate] = {}
    for item in items:
        key = f"doi:{item.doi.lower()}" if item.doi else f"title:{normalize_title(item.title)}"
        if not key.split(":", 1)[1]:
            continue
        existing = winners.get(key)
        if existing is None or (item.relevance_score, bool(item.abstract)) > (existing.relevance_score, bool(existing.abstract)):
            winners[key] = item
    return sorted(winners.values(), key=lambda x: (-x.relevance_score, x.title.lower()))


def write_outputs(items: list[Candidate], output_dir: Path, run_meta: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl = output_dir / "candidates.jsonl"
    with jsonl.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
    (output_dir / "run_manifest.json").write_text(
        json.dumps(run_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["# Mathematical Scripture / Theology Harvest", "",
             f"**Generated:** {run_meta['finished_at']}",
             f"**Candidates:** {len(items)}", "",
             "> Candidate discovery only. No result is promoted to evidence or canon without content review.", ""]
    for lane in ["FORMAL", "EMPIRICAL", "THEOLOGICAL_BRIDGE", "CHALLENGE", "BACKGROUND"]:
        selected = [x for x in items if x.lane == lane]
        if not selected:
            continue
        lines.extend([f"## {lane} ({len(selected)})", ""])
        for item in selected:
            lines.extend([
                f"### {item.title or '[untitled]'}",
                f"- Score / grade: {item.relevance_score} / {item.evidence_grade}",
                f"- Provider: {item.provider}; query lane: {item.query_lane}",
                f"- Year / venue: {item.year or 'unknown'} / {item.venue or 'unknown'}",
                f"- DOI: {item.doi or 'none'}",
                f"- URL: {item.url}",
                f"- Math signals: {', '.join(item.math_signals) or 'none'}",
                f"- Theology signals: {', '.join(item.theology_signals) or 'none'}",
                f"- Screening: {item.screening_status}", "",
            ])
    (output_dir / "harvest_report.md").write_text("\n".join(lines), encoding="utf-8")


def load_queries(path: Path) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(v, list) for v in data.values()):
        raise ValueError("query file must be an object mapping lane names to query lists")
    return data


def self_test() -> None:
    sample = Candidate(
        title="A Formal Modal Logic of the Trinity", url="https://example.test/paper",
        provider="test", query_lane="formal_theology", query="test",
        retrieved_at="2026-08-25T00:00:00+00:00", doi="10.0000/test",
        abstract="We present a theorem and formal proof concerning God and the Trinity.",
    ).finalize()
    assert sample.lane == "FORMAL"
    assert sample.relevance_score >= 70
    assert not contains_term("structural analysis using graphs", "sin")
    assert contains_term("a model of sin and grace", "sin")
    duplicate = Candidate(**{**asdict(sample), "provider": "test2"})
    assert len(deduplicate([sample, duplicate])) == 1
    assert len(sample.content_hash) == 64
    print("SELF_TEST_OK")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="perform live free API discovery")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--providers", default="crossref,arxiv")
    parser.add_argument("--lanes", default="", help="optional comma-separated query lanes")
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--max-queries", type=int, default=0, help="0 means all configured queries")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--mailto", default="", help="optional Crossref polite-pool contact")
    parser.add_argument("--searxng-url", default="http://192.168.2.50:5147")
    parser.add_argument("--ollama", action="store_true", help="run advisory local-model screening")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--ollama-model", default="qwen3:4b-instruct")
    parser.add_argument("--ollama-max-items", type=int, default=25)
    parser.add_argument("--output", type=Path, default=ROOT / "output_math_scripture")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    queries = load_queries(args.queries)
    selected_lanes = {x.strip() for x in args.lanes.split(",") if x.strip()}
    if selected_lanes:
        unknown = selected_lanes.difference(queries)
        if unknown:
            parser.error(f"unknown query lanes: {', '.join(sorted(unknown))}")
        queries = {lane: lane_queries for lane, lane_queries in queries.items()
                   if lane in selected_lanes}
    planned = [(lane, query) for lane, lane_queries in queries.items() for query in lane_queries]
    if args.max_queries > 0:
        planned = planned[:args.max_queries]
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    print(f"Plan: {len(planned)} queries x {len(providers)} providers; max {args.max_results} each")
    print("Providers:", ", ".join(providers))
    if not args.run:
        print("DRY_RUN_ONLY: add --run to issue live free API requests")
        for lane, query in planned:
            print(f"  [{lane}] {query}")
        return 0

    started = datetime.now(timezone.utc).isoformat()
    agent = "TheophysicsResearchHarvester/1.0 (provenance-first; contact supplied via --mailto)"
    all_items: list[Candidate] = []
    errors = []
    adapters = {
        "crossref": lambda q, lane: search_crossref(q, lane, args.max_results, args.mailto, agent),
        "semantic_scholar": lambda q, lane: search_semantic_scholar(q, lane, args.max_results, agent),
        "arxiv": lambda q, lane: search_arxiv(q, lane, args.max_results, agent),
        "searxng": lambda q, lane: search_searxng(q, lane, args.max_results, args.searxng_url, agent),
    }
    for lane, query in planned:
        for provider in providers:
            if provider not in adapters:
                errors.append({"provider": provider, "query": query, "error": "unknown provider"})
                continue
            try:
                found = adapters[provider](query, lane)
                all_items.extend(found)
                print(f"OK {provider:18} {len(found):3}  {query}")
            except (urllib.error.URLError, urllib.error.HTTPError, ET.ParseError, ValueError) as exc:
                errors.append({"provider": provider, "query": query, "error": f"{type(exc).__name__}: {exc}"})
                print(f"ERROR {provider:15} {query}: {exc}", file=sys.stderr)
            time.sleep(max(0.0, args.delay))

    items = deduplicate(all_items)
    ollama_errors = []
    if args.ollama:
        ollama_errors = run_ollama_pass(
            items, args.ollama_url, args.ollama_model,
            max(0, args.ollama_max_items), agent)
    finished = datetime.now(timezone.utc).isoformat()
    meta = {
        "started_at": started, "finished_at": finished, "providers": providers,
        "query_count": len(planned), "raw_candidate_count": len(all_items),
        "deduplicated_candidate_count": len(items), "errors": errors,
        "query_file": str(args.queries.resolve()), "full_text_downloaded": False,
        "ollama_requested": args.ollama,
        "ollama_model": args.ollama_model if args.ollama else "",
        "ollama_reviewed_count": sum(x.ollama_status == "REVIEWED" for x in items),
        "ollama_errors": ollama_errors,
    }
    write_outputs(items, args.output, meta)
    print(f"WROTE {len(items)} candidates to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
