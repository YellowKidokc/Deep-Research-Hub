"""Visible research pipeline: premise audit -> cast -> triage -> extract -> forks -> synthesize.

Every stage writes its record into the run folder as it runs:

    premise.json    what the question assumes, loaded terms, the legs expected before searching
    net.json        every search result: query, which leg/premise the query targets, rank, retriever
    triage.json     every result kept or dropped, with a one-line reason and the legs it bears on
    passages.json   verbatim passages from the kept pages, with url and character offsets;
                    quotes the model returned that are not in the page are listed as rejected
    forks.json      atomic claims and the fork map (fork pills): forks -> positions -> claims -> passages
    forks.md        the same, one pill per position, for reading
    report.md       written only from passages; every factual sentence cites [P#]
    pipeline.json   stage timings, counts, leg coverage, warnings

GPT Researcher stays the acquisition engine (retrievers, scraper, SSRF guard, LLM
providers). Its similarity filter and report writer are not used. Prompts live
in <hub>/prompts/R_web/.

Run inside the queue (job_type: fork_map), or on its own:

    python drh_pipeline.py "Why does God allow evil?" --out ../../../../data/deep_research/manual
    python drh_pipeline.py --resume <run_dir> --from extract     # rerun from a stage

On --resume, <run_dir>/overrides.json is applied to triage before the rerun:
    {"keep": ["https://..."], "drop": ["https://..."]}
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
STAGES = ["premise", "cast", "triage", "extract", "forks", "synthesize"]
DEFAULTS = {
    "max_results_per_query": 8,
    "max_keep": 20,
    "triage_batch": 30,
    "window_chars": 12000,
    "windows_per_page": 3,
    "max_quotes": 6,
    "recast": True,
}
VERDICT_WORDS = re.compile(r"\b(debunk\w*|myth|hoax|proof that|proves?|why .{0,30} (is|are) wrong|is .{0,40} real\??$)\b", re.I)


# ----------------------------------------------------------------- helpers
def find_hub_root(start: Path = HERE) -> Path | None:
    env = os.environ.get("DRH_ROOT")
    if env and (Path(env) / "prompts" / "R_web").is_dir():
        return Path(env)
    for d in [start, *start.parents]:
        if (d / "prompts" / "R_web").is_dir() and (d / "hub").is_dir():
            return d
    return None


def load_prompt(name: str) -> str:
    root = find_hub_root()
    if not root:
        raise FileNotFoundError("prompts/R_web not found; set DRH_ROOT to the Deep Research Hub folder")
    return (root / "prompts" / "R_web" / f"{name}.md").read_text(encoding="utf-8")


def parse_json(text: str) -> Any:
    """The model's reply as JSON: fenced or not, repaired if slightly broken."""
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        import json_repair
        return json_repair.loads(t)


_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                         " ": " ", "…": "..."})


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Text with unified quotes/dashes and collapsed whitespace, plus a map from
    each normalized character back to its index in the original."""
    out, idx = [], []
    prev_space = True
    for i, ch in enumerate(unicodedata.normalize("NFC", text)):
        ch = ch.translate(_QUOTES)
        for c in ch:
            if c.isspace():
                if prev_space:
                    continue
                c, prev_space = " ", True
            else:
                prev_space = False
            out.append(c)
            idx.append(i)
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def locate(quote: str, page: str, norm: tuple[str, list[int]] | None = None) -> tuple[int, int] | None:
    """(start, end) of quote in page, tolerant of whitespace and quote-style only."""
    ntext, idx = norm or normalize_with_map(page)
    nq, _ = normalize_with_map(quote)
    nq = nq.strip()
    if len(nq) < 12:
        return None
    pos = ntext.find(nq)
    if pos < 0:
        pos = ntext.lower().find(nq.lower())
    if pos < 0:
        return None
    return idx[pos], idx[pos + len(nq) - 1] + 1


def host(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except ValueError:
        return ""


# -------------------------------------------------------------- the model
@dataclass
class Deps:
    """What the pipeline needs from the outside world. Tests pass fakes."""
    llm: Callable[[str, str, str], Awaitable[str]]          # (stage, system, user) -> text
    search: Callable[[str, int], Awaitable[list[dict]]]     # (query, n) -> [{title, href|url, body|content, retriever}]
    scrape: Callable[[list[str]], Awaitable[list[dict]]]    # urls -> [{url, raw_content, title}]
    models: dict = field(default_factory=dict)              # stage -> "provider:model", for the record


def gptr_deps(cfg, retrievers, add_costs: Callable[[float], None] | None = None, websocket=None) -> Deps:
    """Deps backed by GPT Researcher: its LLM providers, retrievers and scraper."""
    from gpt_researcher.actions.query_processing import get_search_results
    from gpt_researcher.actions.web_scraping import scrape_urls
    from gpt_researcher.utils.llm import create_chat_completion
    from gpt_researcher.utils.workers import WorkerPool

    fast = ("triage",)

    def model_for(stage):
        return (cfg.fast_llm_provider, cfg.fast_llm_model, cfg.fast_token_limit) if stage in fast \
            else (cfg.smart_llm_provider, cfg.smart_llm_model, cfg.smart_token_limit)

    async def llm(stage, system, user):
        provider, model, limit = model_for(stage)
        return await create_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            model=model, llm_provider=provider, temperature=0.2, max_tokens=min(limit or 4000, 8000),
            llm_kwargs=cfg.llm_kwargs, cost_callback=add_costs)

    async def search(query, n):
        out = []
        for r in retrievers:
            try:
                rows = await get_search_results(query, r, max_results=n)
            except Exception as e:                       # one dead retriever must not stop the cast
                rows = [{"error": f"{type(e).__name__}: {e}"}]
            for row in rows or []:
                out.append({**row, "retriever": r.__name__})
        return out

    async def scrape(urls):
        pool = WorkerPool(cfg.max_scraper_workers, getattr(cfg, "scraper_rate_limit_delay", 0.0))
        data, _ = await scrape_urls(urls, cfg, pool)
        return data

    models = {s: ":".join(model_for(s)[:2]) for s in STAGES}
    return Deps(llm=llm, search=search, scrape=scrape, models=models)


# --------------------------------------------------------------- pipeline
class Pipeline:
    def __init__(self, question: str, run_dir: Path, deps: Deps, settings: dict | None = None,
                 skip_urls: set[str] | None = None, log: Callable[[str], None] = print):
        self.q = question
        self.dir = Path(run_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.deps = deps
        self.s = {**DEFAULTS, **(settings or {})}
        self.skip = set(skip_urls or ())
        self.log = log
        self.record: dict = {"question": question, "settings": self.s, "models": deps.models,
                             "stages": {}, "warnings": []}

    # file helpers -------------------------------------------------------
    def write(self, name: str, data) -> None:
        p = self.dir / name
        p.write_text(data if isinstance(data, str) else json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def read(self, name: str):
        return json.loads((self.dir / name).read_text(encoding="utf-8"))

    def warn(self, msg: str) -> None:
        self.record["warnings"].append(msg)
        self.log(f"  ! {msg}")

    async def ask(self, stage: str, payload: dict) -> Any:
        text = await self.deps.llm(stage, load_prompt(stage), json.dumps(payload, ensure_ascii=False))
        with open(self.dir / "llm_calls.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": round(time.time(), 3), "stage": stage, "model": self.deps.models.get(stage),
                                "input_chars": len(json.dumps(payload)), "reply": text}, ensure_ascii=False) + "\n")
        return parse_json(text)

    # stages -------------------------------------------------------------
    async def premise(self):
        p = await self.ask("premise", {"question": self.q})
        p = p if isinstance(p, dict) else {}
        p.setdefault("neutral_question", self.q)
        for i, a in enumerate(p.setdefault("presuppositions", []), 1):
            a.setdefault("id", f"A{i}")
        for i, leg in enumerate(p.setdefault("expected_legs", []), 1):
            leg.setdefault("id", f"L{i}")
        p.setdefault("loaded_terms", [])
        if len(p["expected_legs"]) < 3:
            self.warn(f"premise audit found only {len(p['expected_legs'])} leg(s); the prompt asks for at least 3")
        self.write("premise.json", p)
        return {"presuppositions": len(p["presuppositions"]), "expected_legs": len(p["expected_legs"]),
                "loaded_terms": len(p["loaded_terms"])}

    def _premise(self):
        return self.read("premise.json")

    def _targets(self, p) -> list[str]:
        return ["neutral"] + [a["id"] for a in p["presuppositions"] if a.get("contested", True)] \
            + [leg["id"] for leg in p["expected_legs"]]

    async def _run_queries(self, queries: list[dict], start_rank: int = 0) -> list[dict]:
        rows = []
        n = int(self.s["max_results_per_query"])
        results = await asyncio.gather(*(self.deps.search(q["query"], n) for q in queries))
        for q, res in zip(queries, results):
            for rank, r in enumerate(res, 1):
                if r.get("error"):
                    self.warn(f"search failed for {q['id']} ({r.get('retriever')}): {r['error']}")
                    continue
                url = r.get("href") or r.get("url") or ""
                if not url:
                    continue
                rows.append({"query_id": q["id"], "targets": q["targets"], "rank": rank,
                             "retriever": r.get("retriever", ""), "url": url, "title": r.get("title", ""),
                             "snippet": (r.get("body") or r.get("content") or r.get("raw_content") or "")[:600]})
        return rows

    def _dedupe(self, rows: list[dict], start: int = 0) -> list[dict]:
        merged: dict[str, dict] = {}
        for row in rows:
            m = merged.get(row["url"])
            if m:
                m["found_by"].append({k: row[k] for k in ("query_id", "targets", "rank", "retriever")})
                continue
            merged[row["url"]] = {"id": "", "url": row["url"], "title": row["title"], "snippet": row["snippet"],
                                  "found_by": [{k: row[k] for k in ("query_id", "targets", "rank", "retriever")}],
                                  "seen_before": row["url"] in self.skip}
        out = list(merged.values())
        for i, r in enumerate(out, start + 1):
            r["id"] = f"R{i}"
        return out

    async def cast(self):
        p = self._premise()
        got = await self.ask("cast", {"neutral_question": p["neutral_question"],
                                      "presuppositions": p["presuppositions"], "expected_legs": p["expected_legs"]})
        queries = [q for q in (got.get("queries", []) if isinstance(got, dict) else []) if q.get("query")]
        for i, q in enumerate(queries, 1):
            q["id"] = f"Q{i}"
            q.setdefault("targets", "neutral")
            q["source"] = "model"
            if VERDICT_WORDS.search(q["query"]):
                self.warn(f"{q['id']} reads like a verdict, not a neutral query: {q['query']!r}")
        # Balance by construction: every target gets at least one query.
        covered = {q["targets"] for q in queries}
        names = {a["id"]: a["statement"] for a in p["presuppositions"]} | {l["id"]: l["position"] for l in p["expected_legs"]}
        for t in self._targets(p):
            if t not in covered:
                text = p["neutral_question"] if t == "neutral" else \
                    (f"arguments for and against {names[t]}" if t.startswith("A") else f"{names[t]} strongest case")
                queries.append({"id": f"Q{len(queries) + 1}", "query": text[:200], "targets": t, "source": "filled"})
                self.warn(f"no query targeted {t}; added one: {text[:80]!r}")
        rows = await self._run_queries(queries)
        net = {"queries": queries, "results": self._dedupe(rows)}
        self.write("net.json", net)
        per_target = {}
        for r in net["results"]:
            for t in {f["targets"] for f in r["found_by"]}:
                per_target[t] = per_target.get(t, 0) + 1
        return {"queries": len(queries), "results": len(rows), "unique_urls": len(net["results"]),
                "results_per_target": per_target}

    async def _triage_batch(self, p, results, max_keep) -> dict[str, dict]:
        out: dict[str, dict] = {}
        size = int(self.s["triage_batch"])
        for i in range(0, len(results), size):
            batch = results[i:i + size]
            got = await self.ask("triage", {
                "neutral_question": p["neutral_question"], "expected_legs": p["expected_legs"],
                "presuppositions": p["presuppositions"], "max_keep": max_keep,
                "results": [{"id": r["id"], "title": r["title"], "url": r["url"], "snippet": r["snippet"],
                             "found_by": sorted({f["targets"] for f in r["found_by"]})} for r in batch]})
            for d in (got.get("results", []) if isinstance(got, dict) else []):
                if isinstance(d, dict) and d.get("id"):
                    out[d["id"]] = d
        return out

    async def triage(self):
        p = self._premise()
        net = self.read("net.json")
        results = [r for r in net["results"] if not r["seen_before"]]
        decided = await self._triage_batch(p, results, int(self.s["max_keep"]))
        rows = self._triage_rows(net["results"], decided)

        # One recast round for legs nothing kept speaks to.
        recast = {}
        if self.s.get("recast"):
            uncovered = self._uncovered(p, rows)
            if uncovered:
                legs = {l["id"]: l for l in p["expected_legs"]}
                queries = [{"id": f"Q{len(net['queries']) + i}", "targets": t, "source": "recast",
                            "query": f"{legs[t]['position']} {legs[t].get('holders', '')}".strip()[:200]}
                           for i, t in enumerate(uncovered, 1)]
                self.log(f"  recast for uncovered legs: {', '.join(uncovered)}")
                new = [r for r in self._dedupe(await self._run_queries(queries), start=len(net["results"]))
                       if r["url"] not in {x["url"] for x in net["results"]}]
                net["queries"] += queries
                net["results"] += new
                self.write("net.json", net)
                more = await self._triage_batch(p, [r for r in new if not r["seen_before"]], max(3, len(uncovered) * 2))
                decided.update(more)
                rows = self._triage_rows(net["results"], decided)
                recast = {"legs": uncovered, "queries": len(queries), "new_results": len(new),
                          "still_uncovered": self._uncovered(p, rows)}

        # max_keep is a hard cap. Trim round-robin across the targets each page
        # bears on, so the cap never falls on the legs that happen to come last
        # (results are listed neutral -> presuppositions -> legs in order; a
        # tail trim would cut the last legs first and undo the balanced cast).
        cap = int(self.s["max_keep"]) + (len(recast.get("legs", [])) * 2)
        kept = [r for r in rows if r["keep"]]
        if len(kept) > cap:
            by_target: dict[str, list] = {}
            for r in kept:
                key = (r["bears_on"] or r["found_by"] or ["neutral"])[0]
                by_target.setdefault(key, []).append(r)
            chosen, lanes = [], list(by_target.values())
            while len(chosen) < cap and any(lanes):
                for lane in lanes:
                    if lane and len(chosen) < cap:
                        chosen.append(lane.pop(0))
            keep_ids = {r["id"] for r in chosen}
            for r in kept:
                if r["id"] not in keep_ids:
                    r["keep"], r["reason"] = False, f"over max_keep, per-leg round robin (was kept: {r['reason']})"
        self.write("triage.json", {"results": rows, "recast": recast})
        kept = [r for r in rows if r["keep"]]
        return {"kept": len(kept), "dropped": len(rows) - len(kept),
                "no_decision": sum(1 for r in rows if r["reason"].startswith("no decision")),
                "kept_per_leg": self._per_leg(p, kept), "recast": recast}

    def _triage_rows(self, results, decided):
        rows = []
        for r in results:
            d = decided.get(r["id"])
            if r["seen_before"]:
                keep, reason, bears = False, "seen in an earlier run (visited_urls_from)", []
            elif d is None:
                keep, reason, bears = False, "no decision returned by the model", []
            else:
                keep, reason, bears = bool(d.get("keep")), str(d.get("reason", "")), list(d.get("bears_on") or [])
            rows.append({"id": r["id"], "url": r["url"], "title": r["title"], "keep": keep, "reason": reason,
                         "bears_on": bears, "found_by": sorted({f["targets"] for f in r["found_by"]}), "by": "model"})
        return rows

    def _per_leg(self, p, rows):
        return {l["id"]: sum(1 for r in rows if l["id"] in r["bears_on"]) for l in p["expected_legs"]}

    def _uncovered(self, p, rows):
        per = self._per_leg(p, [r for r in rows if r["keep"]])
        return [k for k, v in per.items() if v == 0]

    def apply_overrides(self):
        path = self.dir / "overrides.json"
        if not path.exists():
            return 0
        ov = json.loads(path.read_text(encoding="utf-8"))
        tri = self.read("triage.json")
        n = 0
        for r in tri["results"]:
            for key, val in (("keep", True), ("drop", False)):
                if r["url"] in set(ov.get(key, [])) and r["keep"] != val:
                    r["keep"], r["by"], r["reason"] = val, "person", f"{key} by person (model said: {r['reason']})"
                    n += 1
        self.write("triage.json", tri)
        return n

    async def extract(self):
        p = self._premise()
        tri = self.read("triage.json")
        kept = [r for r in tri["results"] if r["keep"]]
        pages = {d.get("url"): d for d in await self.deps.scrape([r["url"] for r in kept]) if d.get("url")}
        passages, rejected, pages_rec = [], [], []
        win, nwin = int(self.s["window_chars"]), int(self.s["windows_per_page"])

        async def one(r):
            page = pages.get(r["url"])
            text = (page or {}).get("raw_content") or ""
            if not text.strip():
                return {"url": r["url"], "status": "no text"}, [], []
            windows = [(i, text[i:i + win]) for i in range(0, len(text), win)]
            read = windows[:nwin]
            found, bad = [], []
            norm = normalize_with_map(text)
            for start, chunk in read:
                got = await self.ask("extract", {
                    "neutral_question": p["neutral_question"], "expected_legs": p["expected_legs"],
                    "presuppositions": p["presuppositions"], "title": (page or {}).get("title") or r["title"],
                    "url": r["url"], "max_quotes": int(self.s["max_quotes"]), "window": chunk})
                for q in (got.get("passages", []) if isinstance(got, dict) else []):
                    quote = str(q.get("quote", "")).strip()
                    parts = [s for s in re.split(r"\s*(?:\.\.\.|…)\s*", quote) if s.strip()]
                    spans = [locate(s, text, norm) for s in parts] if parts else [None]
                    if not quote or any(s is None for s in spans):
                        bad.append({"url": r["url"], "quote": quote, "reason": "not found verbatim in the page (or under 12 characters)"})
                        continue
                    found.append({"url": r["url"], "title": (page or {}).get("title") or r["title"],
                                  "host": host(r["url"]), "quote": text[spans[0][0]:spans[-1][1]] if len(spans) == 1 else quote,
                                  "start": spans[0][0], "end": spans[-1][1], "elided": len(spans) > 1,
                                  "bears_on": list(q.get("bears_on") or []), "stance": q.get("stance", "context"),
                                  "why": q.get("why", "")})
            unread = len(text) - min(len(text), nwin * win)
            return ({"url": r["url"], "status": "read", "chars": len(text), "windows_read": len(read),
                     "windows_total": len(windows), "chars_unread": unread}, found, bad)

        for rec, found, bad in await asyncio.gather(*(one(r) for r in kept)):
            pages_rec.append(rec)
            passages += found
            rejected += bad
            if rec.get("chars_unread"):
                self.warn(f"{rec['url']}: {rec['chars_unread']} chars past windows_per_page were not read")
        # Same span twice (two windows / two calls) is one passage.
        seen, unique = set(), []
        for ps in passages:
            key = (ps["url"], ps["start"], ps["end"])
            if key not in seen:
                seen.add(key)
                unique.append(ps)
        for i, ps in enumerate(unique, 1):
            ps["id"] = f"P{i}"
        self.write("passages.json", {"passages": unique, "rejected": rejected, "pages": pages_rec})
        return {"pages_read": sum(1 for x in pages_rec if x["status"] == "read"),
                "pages_without_text": sum(1 for x in pages_rec if x["status"] != "read"),
                "passages": len(unique), "rejected_not_verbatim": len(rejected),
                "passages_per_leg": {l["id"]: sum(1 for x in unique if l["id"] in x["bears_on"]) for l in p["expected_legs"]}}

    async def forks(self):
        p = self._premise()
        ps = self.read("passages.json")["passages"]
        by_id = {x["id"]: x for x in ps}
        got = await self.ask("forks", {
            "neutral_question": p["neutral_question"], "presuppositions": p["presuppositions"],
            "expected_legs": p["expected_legs"],
            "passages": [{"id": x["id"], "quote": x["quote"], "source": x["title"], "url": x["url"],
                          "bears_on": x["bears_on"], "stance": x["stance"]} for x in ps]})
        got = got if isinstance(got, dict) else {}
        claims = {c["id"]: c for c in got.get("claims", []) if isinstance(c, dict) and c.get("id")}
        bad_refs = []
        for c in claims.values():
            good = [pid for pid in c.get("passages", []) if pid in by_id]
            bad_refs += [f"{c['id']}->{pid}" for pid in c.get("passages", []) if pid not in by_id]
            c["passages"] = good
        legs = {l["id"] for l in p["expected_legs"]}
        forks = [f for f in got.get("forks", []) if isinstance(f, dict)]
        for f in forks:
            for pos in f.get("positions", []):
                good = [pid for pid in pos.get("passages", []) if pid in by_id]
                bad_refs += [f"{pos.get('id')}->{pid}" for pid in pos.get("passages", []) if pid not in by_id]
                pos["claims"] = [c for c in pos.get("claims", []) if c in claims]
                # A position's passages include those of its claims.
                for c in pos["claims"]:
                    good += [pid for pid in claims[c]["passages"] if pid not in good]
                pos["passages"] = good
                if pos.get("matches_leg") not in legs:
                    pos["matches_leg"] = None
                pos["sources"] = len({by_id[pid]["url"] for pid in good})
                pos["hosts"] = sorted({by_id[pid]["host"] for pid in good})
                pos["status"] = "no source" if not good else ("one source" if pos["sources"] == 1 else "sourced")
        if bad_refs:
            self.warn(f"fork map cited {len(bad_refs)} passage id(s) that do not exist; removed: {', '.join(bad_refs[:10])}")
        cited = {pid for f in forks for pos in f.get("positions", []) for pid in pos["passages"]}
        unplaced = [x["id"] for x in ps if x["id"] not in cited]

        positions = [pos for f in forks for pos in f.get("positions", [])]
        matched = {pos["matches_leg"] for pos in positions if pos["matches_leg"] and pos["passages"]}
        legs_summary = {
            "expected": len(legs),
            "found": sum(1 for pos in positions if pos["passages"]),
            "expected_and_found": sorted(matched),
            "expected_not_found": sorted(legs - matched),
            "found_not_expected": [pos["id"] for pos in positions if pos["passages"] and not pos["matches_leg"]],
            "one_source": [pos["id"] for pos in positions if pos["status"] == "one source"],
            "one_fork_one_side": [f["id"] for f in forks if sum(1 for pos in f.get("positions", []) if pos["passages"]) < 2],
        }
        doc = {"question": self.q, "neutral_question": p["neutral_question"], "claims": list(claims.values()),
               "forks": forks, "unplaced_passages": unplaced, "legs": legs_summary}
        self.write("forks.json", doc)
        self.write("forks.md", render_forks_md(doc, p, by_id))
        return {"forks": len(forks), "positions": len(positions), "claims": len(claims),
                "unplaced_passages": len(unplaced), "legs": legs_summary}

    async def synthesize(self):
        p = self._premise()
        doc = self.read("forks.json")
        ps = self.read("passages.json")["passages"]
        ids = {x["id"] for x in ps}
        text = await self.deps.llm("synthesize", load_prompt("synthesize"), json.dumps({
            "question": self.q, "presuppositions": p["presuppositions"], "forks": doc["forks"],
            "expected_not_found": [l for l in p["expected_legs"] if l["id"] in doc["legs"]["expected_not_found"]],
            "passages": [{"id": x["id"], "quote": x["quote"], "source": x["title"], "url": x["url"]} for x in ps],
        }, ensure_ascii=False))
        text = re.sub(r"^```(?:markdown|md)?\s*|```\s*$", "", text.strip())
        cited = re.findall(r"\[(P\d+(?:\s*,\s*P\d+)*)\]", text)
        refs = [r.strip() for group in cited for r in group.split(",")]
        unknown = sorted({r for r in refs if r not in ids}, key=lambda s: int(s[1:]))
        if unknown:
            self.warn(f"report cites passage ids that do not exist: {', '.join(unknown)}")
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", re.sub(r"^\s*(#|\|).*$", "", text, flags=re.M)) if len(s.split()) >= 6]
        uncited = [s.strip()[:160] for s in sentences if not re.search(r"\[P\d+", s)]
        sources = "\n".join(f"- **[{x['id']}]** {x['title'] or x['host']} — <{x['url']}> (chars {x['start']}–{x['end']})"
                            for x in ps)
        self.write("report.md", text.rstrip() + "\n\n## Passages\n\n" + sources + "\n")
        return {"citations": len(refs), "unknown_ids": unknown, "sentences_without_citation": len(uncited),
                "uncited_examples": uncited[:5]}

    # driver -------------------------------------------------------------
    async def run(self, start: str = "premise") -> dict:
        if start != "premise":
            # Resume: keep the record of the stages before `start`; a person's
            # keep/drop overrides apply to triage before anything after it reruns.
            if (self.dir / "pipeline.json").exists():
                old = self.read("pipeline.json")
                self.record["stages"] = {k: v for k, v in old.get("stages", {}).items()
                                         if STAGES.index(k) < STAGES.index(start)}
            if STAGES.index(start) > STAGES.index("triage"):
                self.record["overrides_applied"] = self.apply_overrides()
        for name in STAGES[STAGES.index(start):]:
            t0 = time.time()
            self.log(f"[{name}]")
            try:
                counts = await getattr(self, name)()
            except Exception as e:
                self.record["stages"][name] = {"status": "failed", "error": f"{type(e).__name__}: {e}",
                                               "seconds": round(time.time() - t0, 1)}
                self.record["failed_at"] = name
                self.write("pipeline.json", self.record)
                raise
            self.record["stages"][name] = {"status": "done", "seconds": round(time.time() - t0, 1), **counts}
            self.log(f"  {json.dumps(counts, ensure_ascii=False)[:300]}")
            self.write("pipeline.json", self.record)
        self.record.pop("failed_at", None)
        self.write("pipeline.json", self.record)
        return self.record

    def summary(self) -> dict:
        st = self.record["stages"]
        return {
            "expected_legs": st.get("premise", {}).get("expected_legs"),
            "presuppositions": st.get("premise", {}).get("presuppositions"),
            "unique_urls": st.get("cast", {}).get("unique_urls"),
            "kept": st.get("triage", {}).get("kept"),
            "passages": st.get("extract", {}).get("passages"),
            "rejected_not_verbatim": st.get("extract", {}).get("rejected_not_verbatim"),
            "forks": st.get("forks", {}).get("forks"),
            "legs_found": st.get("forks", {}).get("legs", {}).get("found"),
            "legs_expected_found": len(st.get("forks", {}).get("legs", {}).get("expected_and_found", [])),
            "legs_found_not_expected": len(st.get("forks", {}).get("legs", {}).get("found_not_expected", [])),
            "legs_expected_not_found": st.get("forks", {}).get("legs", {}).get("expected_not_found"),
            "warnings": len(self.record["warnings"]),
        }

    def visited_urls(self) -> set[str]:
        try:
            return {r["url"] for r in self.read("net.json")["results"]}
        except (FileNotFoundError, KeyError):
            return set()


def render_forks_md(doc: dict, premise: dict, by_id: dict) -> str:
    """One pill per position. Pills, not prose: every line is a field."""
    legs = {l["id"]: l for l in premise["expected_legs"]}
    out = [f"# Fork map: {doc['neutral_question']}", "", f"Asked as: {doc['question']}", ""]
    out += ["## What the question assumes", ""]
    for a in premise["presuppositions"]:
        out.append(f"- **{a['id']}** {a['statement']} — *{a.get('kind', '')}*; could fail: {a.get('how_it_could_fail', '')}")
    lg = doc["legs"]
    out += ["", "## Legs", "",
            f"- expected before searching: {lg['expected']}; positions with sources: {lg['found']}",
            "- expected, not found in any source: " + (", ".join(f"{k} ({legs[k]['position']})" for k in lg["expected_not_found"]) or "none"),
            f"- found, not expected: {', '.join(lg['found_not_expected']) or 'none'}",
            f"- resting on one source: {', '.join(lg['one_source']) or 'none'}",
            f"- forks with fewer than two sourced sides: {', '.join(lg['one_fork_one_side']) or 'none'}", ""]
    for f in doc["forks"]:
        out += [f"## {f['id']} · {f.get('fork_name', '')}", "", f"**Question:** {f.get('core_question', '')}"]
        if f.get("tests_presupposition"):
            out.append(f"**Tests:** {f['tests_presupposition']}")
        out.append("")
        for pos in f.get("positions", []):
            leg = f"{pos['matches_leg']}" if pos["matches_leg"] else "not expected"
            out += [f"### {pos.get('id')} · {pos.get('position', '')}", "",
                    f"- status: {pos['status']} · leg: {leg} · sources: {pos['sources']} ({', '.join(pos['hosts']) or '—'})",
                    f"- strongest form: {pos.get('strongest_form', '')}",
                    f"- passages: {', '.join(pos['passages']) or '—'}"]
            for pid in pos["passages"][:6]:
                x = by_id[pid]
                q = x["quote"] if len(x["quote"]) < 400 else x["quote"][:400] + "…"
                out.append(f"  - **{pid}** “{q}” — {x['title'] or x['host']} <{x['url']}>")
            out.append("")
    if doc["unplaced_passages"]:
        out += ["## Unplaced passages", "", ", ".join(doc["unplaced_passages"]), ""]
    return "\n".join(out)


# ------------------------------------------------------------------- CLI
def _cli_deps():
    from gpt_researcher.actions.retriever import get_retrievers
    from gpt_researcher.config import Config
    cfg = Config()
    return gptr_deps(cfg, get_retrievers({}, cfg))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", nargs="?")
    ap.add_argument("--out", help="folder; the run goes in <out>/<YYYYmmdd-HHMMSS>/")
    ap.add_argument("--resume", help="an existing run folder")
    ap.add_argument("--from", dest="start", default="premise", choices=STAGES)
    args = ap.parse_args()
    sys.path.insert(0, str(HERE))
    from drh_queue import apply_env_file
    apply_env_file(HERE / "PROVIDERS.env")
    apply_env_file(HERE / "RESEARCH_PROFILE.env")
    if args.resume:
        run_dir = Path(args.resume)
        question = json.loads((run_dir / "pipeline.json").read_text(encoding="utf-8"))["question"]
    else:
        if not args.question or not args.out:
            ap.error("give a question and --out, or --resume")
        run_dir = Path(args.out) / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        question = args.question
    pipe = Pipeline(question, run_dir, _cli_deps())
    asyncio.run(pipe.run(args.start))
    print(json.dumps(pipe.summary(), indent=2))
    print(f"-> {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
