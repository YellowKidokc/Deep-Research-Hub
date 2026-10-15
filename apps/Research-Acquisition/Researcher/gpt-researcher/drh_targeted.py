"""Targeted Research (screen 2): one topic, a fixed battery of narrow lookups -> facts.json.

    python drh_targeted.py --topic "privatio boni" --out ../../../../data/targeted
    python drh_targeted.py --topic "entropy" --items origin,first_study --out ...
    python drh_targeted.py --topics-file topics.txt --out ...      # one topic per line, run in turn

The battery is <hub>/prompts/T_targeted/battery.json; prompts beside it. Each item:
    queries   the item's hint queries (topic filled in) + a few the model adds
    search    every query through GPT Researcher's retrievers; results deduped by URL
    read      the top pages by rank; passages pulled and checked verbatim against the page
    answer    findings, each citing passages
    check     a finding is rejected unless it cites real passages and every field the
              item requires (who / when / where) is filled and, for who and when, stated
              in a cited passage. No accepted finding = "unknown", a legal answer.

Output: <out>/<topic-slug>/<YYYYmmdd-HHMMSS>/
    facts.json      every item: status, accepted findings with their passages, rejected
                    findings with the reason, and what was searched and read
    facts.md        the same, for reading
    items/<id>/     queries.json, net.json, passages.json, answer.json (the raw stages)
    run.json        topic, items, models, timings, status
    llm_calls.jsonl every model call and its reply
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import re
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import drh_pipeline as dp  # noqa: E402  (shared helpers: Deps, search/scrape wiring, verbatim check)

FIELDS = ("who", "when", "where")
YEAR = re.compile(r"\b(\d{3,4})(?:s|\b)")


def slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", text.strip().lower()).strip("-")
    return (s or "topic")[:60]


def load_battery() -> dict:
    root = dp.find_hub_root()
    if not root:
        raise FileNotFoundError("prompts/T_targeted not found; set DRH_ROOT to the Deep Research Hub folder")
    return json.loads((root / "prompts" / "T_targeted" / "battery.json").read_text(encoding="utf-8"))


def _norm(s: str) -> str:
    return dp.normalize_with_map(s or "")[0].lower()


def stated_in(field: str, value: str, texts: list[str]) -> bool:
    """Is this who/when value actually stated in one of the cited passages?"""
    hay = " ".join(_norm(t) for t in texts)
    v = _norm(value)
    if not v or v in ("null", "none", "unknown", "n/a"):
        return False
    if re.search(rf"(?<!\w){re.escape(v)}(?!\w)", hay):     # the value as written, as whole words
        return True
    if field == "when":
        years = YEAR.findall(value)
        return bool(years) and any(re.search(rf"(?<!\d){y}(?!\d)", hay) for y in years)
    if field == "who":
        # Authors may be "Smith and Jones" or "J. Smith": accept when every surname
        # (the last word of each name) is in the passages.
        names = [n for n in re.split(r",|;|\band\b|&|\bet al\.?", value) if n.strip()]
        surnames = [re.sub(r"[^\w'-]", "", n.split()[-1]).lower() for n in names if n.split()]
        surnames = [s for s in surnames if len(s) >= 3]
        return bool(surnames) and all(re.search(rf"\b{re.escape(s)}\b", hay) for s in surnames)
    return False


class Targeted:
    def __init__(self, topic: str, run_dir: Path, deps: dp.Deps, battery: dict,
                 items: list[str] | None = None, log=print):
        self.topic = topic.strip()
        self.dir = Path(run_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.deps = deps
        self.battery = battery
        self.s = battery.get("defaults", {})
        known = {i["id"]: i for i in battery["items"]}
        unknown = [i for i in (items or []) if i not in known]
        if unknown:
            raise ValueError(f"unknown battery item(s): {unknown}; known: {sorted(known)}")
        self.items = [known[i] for i in items] if items else [i for i in battery["items"] if i.get("default")]
        self.log = log

    def _write(self, rel: str, data) -> None:
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data if isinstance(data, str) else json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    async def _ask(self, stage: str, item_id: str, payload: dict) -> dict:
        text = await self.deps.llm(stage, dp.load_prompt(stage, "T_targeted"), json.dumps(payload, ensure_ascii=False))
        with open(self.dir / "llm_calls.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": round(time.time(), 3), "item": item_id, "stage": stage,
                                "model": self.deps.models.get(stage), "reply": text}, ensure_ascii=False) + "\n")
        got = dp.parse_json(text)
        return got if isinstance(got, dict) else {}

    # one item -----------------------------------------------------------------
    async def run_item(self, item: dict) -> dict:
        iid = item["id"]
        base = {"id": iid, "label": item["label"], "question": item["question"], "requires": item.get("requires", [])}
        if item.get("needs"):
            return {**base, "status": "skipped",
                    "note": f"needs {item['needs']}: {item.get('instructions', '')}".strip()}
        t0 = time.time()
        req = item.get("requires", [])

        # queries: hints first (deterministic), then the model's additions
        hints = [h.replace("{topic}", self.topic) for h in item.get("query_hints", [])]
        extra = []
        if int(self.s.get("model_queries", 3)) > 0:
            got = await self._ask("queries", iid, {"topic": self.topic, "question": item["question"],
                                                   "instructions": item.get("instructions", ""),
                                                   "hint_queries": hints, "max_queries": int(self.s.get("model_queries", 3))})
            extra = [q for q in got.get("queries", []) if isinstance(q, str) and q.strip()][: int(self.s.get("model_queries", 3))]
        queries = [{"query": q, "source": "hint"} for q in hints] + [{"query": q, "source": "model"} for q in extra]
        for q in queries:
            if dp.VERDICT_WORDS.search(q["query"]):
                q["warning"] = "reads like a verdict"
        self._write(f"items/{iid}/queries.json", {"queries": queries})

        # search, dedupe by URL; best (lowest) rank across queries first
        n = int(self.s.get("results_per_query", 6))
        results = await asyncio.gather(*(self.deps.search(q["query"], n) for q in queries))
        seen: dict[str, dict] = {}
        errors = []
        for q, rows in zip(queries, results):
            for rank, r in enumerate(rows, 1):
                if r.get("error"):
                    errors.append(f"{q['query']!r}: {r['error']}")
                    continue
                url = r.get("href") or r.get("url") or ""
                if not url:
                    continue
                hit = seen.setdefault(url, {"url": url, "title": r.get("title", ""), "best_rank": rank, "found_by": []})
                hit["best_rank"] = min(hit["best_rank"], rank)
                hit["found_by"].append(q["query"])
        ranked = sorted(seen.values(), key=lambda h: (h["best_rank"], -len(h["found_by"])))
        to_read = ranked[: int(self.s.get("max_pages", 6))]
        self._write(f"items/{iid}/net.json", {"results": ranked, "read": [h["url"] for h in to_read], "errors": errors})

        # read: verbatim passages
        pages = {d.get("url"): d for d in await self.deps.scrape([h["url"] for h in to_read]) if d.get("url")}
        win, nwin = int(self.s.get("window_chars", 12000)), int(self.s.get("windows_per_page", 2))
        passages, rejected_quotes, pages_rec = [], [], []
        for h in to_read:
            page = pages.get(h["url"]) or {}
            text = page.get("raw_content") or ""
            if not text.strip():
                pages_rec.append({"url": h["url"], "status": "no text"})
                continue
            norm = dp.normalize_with_map(text)
            title = page.get("title") or h["title"]
            windows = [text[i:i + win] for i in range(0, len(text), win)][:nwin]
            for chunk in windows:
                got = await self._ask("extract", iid, {"topic": self.topic, "question": item["question"], "requires": req,
                                                       "title": title, "url": h["url"],
                                                       "max_quotes": int(self.s.get("max_quotes", 6)), "window": chunk})
                for q in got.get("passages", []):
                    quote = str(q.get("quote", "")).strip()
                    span = dp.locate(quote, text, norm)
                    if not span:
                        rejected_quotes.append({"url": h["url"], "quote": quote, "reason": "not found verbatim in the page"})
                        continue
                    passages.append({"url": h["url"], "title": title, "host": dp.host(h["url"]),
                                     "quote": text[span[0]:span[1]], "start": span[0], "end": span[1], "why": q.get("why", "")})
            pages_rec.append({"url": h["url"], "status": "read", "chars": len(text),
                              "chars_unread": max(0, len(text) - nwin * win)})
        uniq, keys = [], set()
        for p in passages:
            if (p["url"], p["start"], p["end"]) not in keys:
                keys.add((p["url"], p["start"], p["end"]))
                uniq.append(p)
        for i, p in enumerate(uniq, 1):
            p["id"] = f"P{i}"
        self._write(f"items/{iid}/passages.json", {"passages": uniq, "rejected": rejected_quotes, "pages": pages_rec})
        searched = {"queries": len(queries), "urls": len(ranked), "pages_read": sum(1 for p in pages_rec if p["status"] == "read"),
                    "passages": len(uniq), "quotes_not_verbatim": len(rejected_quotes), "search_errors": len(errors)}
        if not uniq:
            return {**base, "status": "unknown", "findings": [], "rejected": [], "searched": searched,
                    "note": "no passage on the question was found in the pages read",
                    "seconds": round(time.time() - t0, 1)}

        # answer, then check every finding against its own passages
        got = await self._ask("answer", iid, {"topic": self.topic, "question": item["question"],
                                              "instructions": item.get("instructions", ""), "requires": req,
                                              "passages": [{"id": p["id"], "quote": p["quote"], "source": p["title"],
                                                            "url": p["url"]} for p in uniq]})
        self._write(f"items/{iid}/answer.json", got)
        by_id = {p["id"]: p for p in uniq}
        accepted, rejected = [], []
        for f in got.get("findings", []) if isinstance(got.get("findings"), list) else []:
            if not isinstance(f, dict):
                continue
            cited = [pid for pid in f.get("passages", []) if pid in by_id]
            reasons = []
            if not cited:
                reasons.append("cites no passage that exists")
            for fld in req:
                val = f.get(fld)
                if not val or str(val).strip().lower() in ("null", "none", "unknown", "n/a"):
                    reasons.append(f"{fld} required but empty")
                elif fld in ("who", "when") and cited and not stated_in(fld, str(val), [by_id[c]["quote"] for c in cited]):
                    reasons.append(f"{fld} {str(val)!r} is not stated in its cited passage(s)")
            if reasons:
                rejected.append({"finding": f, "reasons": reasons})
                continue
            accepted.append({**{k: f.get(k) for k in ("claim", *FIELDS, "note")},
                             "passages": [{k: by_id[c][k] for k in ("id", "url", "title", "quote", "start", "end")} for c in cited]})
        if iid == "origin":
            accepted.sort(key=lambda f: int((YEAR.findall(str(f.get("when") or "")) or ["99999"])[0]))
        return {**base, "status": "found" if accepted else "unknown", "findings": accepted, "rejected": rejected,
                "searched": searched, "note": str(got.get("status_note") or ""), "seconds": round(time.time() - t0, 1)}

    async def run(self) -> dict:
        started = time.time()
        record = {"topic": self.topic, "items": [i["id"] for i in self.items], "models": self.deps.models,
                  "started": dt.datetime.now().isoformat(timespec="seconds"), "status": "running"}
        self._write("run.json", record)

        async def guarded(item):
            self.log(f"[{item['id']}] {item['label']}")
            try:
                res = await self.run_item(item)
            except Exception as e:
                (self.dir / "items" / item["id"]).mkdir(parents=True, exist_ok=True)
                self._write(f"items/{item['id']}/error.txt", traceback.format_exc())
                res = {"id": item["id"], "label": item["label"], "question": item["question"],
                       "status": "failed", "note": f"{type(e).__name__}: {e}"}
            self.log(f"[{item['id']}] {res['status']}: {len(res.get('findings', []))} accepted, "
                     f"{len(res.get('rejected', []))} rejected" + (f" ({res['note'][:120]})" if res.get("note") else ""))
            return res

        results = await asyncio.gather(*(guarded(i) for i in self.items))
        facts = {"topic": self.topic, "generated": dt.datetime.now().isoformat(timespec="seconds"),
                 "items": {r["id"]: r for r in results}}
        self._write("facts.json", facts)
        self._write("facts.md", render_md(facts))
        record.update({
            "status": "failed" if all(r["status"] == "failed" for r in results) else "done",
            "ended": dt.datetime.now().isoformat(timespec="seconds"), "seconds": round(time.time() - started, 1),
            "summary": {r["id"]: r["status"] for r in results},
            "findings": sum(len(r.get("findings", [])) for r in results),
            "rejected": sum(len(r.get("rejected", [])) for r in results),
        })
        self._write("run.json", record)
        return facts


def render_md(facts: dict) -> str:
    out = [f"# Targeted Research: {facts['topic']}", "", f"Generated {facts['generated']}.", ""]
    marks = {"found": "found", "unknown": "unknown (no supported answer)", "skipped": "skipped", "failed": "failed"}
    for it in facts["items"].values():
        out += [f"## {it['label']} — {marks.get(it['status'], it['status'])}", "", f"*{it['question']}*", ""]
        if it.get("note"):
            out += [it["note"], ""]
        for n, f in enumerate(it.get("findings", []), 1):
            meta = " · ".join(str(f[k]) for k in FIELDS if f.get(k))
            out.append(f"{n}. **{f.get('claim', '')}**" + (f" — {meta}" if meta else ""))
            if f.get("note"):
                out.append(f"   - note: {f['note']}")
            for p in f["passages"]:
                q = p["quote"] if len(p["quote"]) < 400 else p["quote"][:400] + "…"
                out.append(f"   - [{p['id']}] “{q}” — {p['title'] or p['url']} <{p['url']}>")
        if it.get("rejected"):
            out += ["", f"Rejected ({len(it['rejected'])}):"]
            for r in it["rejected"]:
                out.append(f"- {r['finding'].get('claim', '')!s} — {'; '.join(r['reasons'])}")
        if it.get("searched"):
            s = it["searched"]
            out += ["", f"<sub>{s['queries']} queries · {s['urls']} results · {s['pages_read']} pages read · "
                        f"{s['passages']} passages · {s['quotes_not_verbatim']} quotes not verbatim</sub>"]
        out.append("")
    return "\n".join(out)


def _cli_deps():
    from gpt_researcher.actions.retriever import get_retrievers
    from gpt_researcher.config import Config
    cfg = Config()
    deps = dp.gptr_deps(cfg, get_retrievers({}, cfg))
    deps.models = {s: f"{cfg.smart_llm_provider}:{cfg.smart_llm_model}" for s in ("queries", "extract", "answer")}
    return deps


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--topic", action="append", default=[], help="a topic (repeatable)")
    ap.add_argument("--topics-file", help="one topic per line; # comments")
    ap.add_argument("--items", default="", help="comma list of battery item ids (blank = the battery's defaults)")
    ap.add_argument("--out", required=True, help="output root; each topic goes in <out>/<slug>/<stamp>/")
    ap.add_argument("--list", action="store_true", help="print the battery and stop")
    args = ap.parse_args()
    from drh_queue import apply_env_file
    apply_env_file(HERE / "PROVIDERS.env")
    apply_env_file(HERE / "RESEARCH_PROFILE.env")
    battery = load_battery()
    if args.list:
        for it in battery["items"]:
            flag = "default" if it.get("default") else (f"needs {it['needs']}" if it.get("needs") else "optional")
            print(f"{it['id']:<16} {flag:<20} {it['question']}")
        return 0
    topics = [t.strip() for t in args.topic if t.strip()]
    if args.topics_file:
        topics += [l.strip() for l in Path(args.topics_file).read_text(encoding="utf-8-sig").splitlines()
                   if l.strip() and not l.lstrip().startswith("#")]
    if not topics:
        ap.error("give --topic or --topics-file")
    items = [i.strip() for i in args.items.split(",") if i.strip()] or None
    bad = [i for i in items or [] if i not in {it["id"] for it in battery["items"]}]
    if bad:
        ap.error(f"unknown item(s) {bad}; see --list")
    deps = _cli_deps()
    failed = 0
    for topic in topics:
        run_dir = Path(args.out) / slug(topic) / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"[start] {topic} -> {run_dir}", flush=True)
        try:
            facts = asyncio.run(Targeted(topic, run_dir, deps, battery, items, log=lambda m: print("  " + m, flush=True)).run())
            print(f"[done] {topic}: " + ", ".join(f"{k} {v['status']}" for k, v in facts["items"].items()), flush=True)
        except Exception as e:
            failed += 1
            (run_dir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            print(f"[failed] {topic}: {type(e).__name__}: {e}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
