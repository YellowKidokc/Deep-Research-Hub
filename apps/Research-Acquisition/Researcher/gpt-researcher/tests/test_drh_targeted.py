"""drh_targeted.py: the Targeted Research battery with a scripted model, search and
scraper (no network). Fixture topic: "privatio boni"."""
import asyncio
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import drh_pipeline as dp  # noqa: E402
import drh_targeted as dt  # noqa: E402

PAGES = {
    "https://example.org/etym": {
        "title": "Privatio boni — a short history",
        "raw_content": "Home | About\n\nThe phrase privatio boni is Latin for “privation of the good”. "
                       "Augustine of Hippo, writing in the Confessions (c. 397), described evil as nothing but "
                       "the privation of good. Later writers took the idea up.",
    },
    "https://example.org/aquinas": {
        "title": "Aquinas on evil",
        "raw_content": "Thomas Aquinas, in the Summa Theologiae (1265–1274), held that evil is a privation "
                       "of a due good and not a substance.",
    },
    "https://example.org/apol": {
        "title": "Privation theory in apologetics",
        "raw_content": "William Lane Craig argues that the privation view answers the charge that God created evil. "
                       "Critics such as J. L. Mackie objected that pain is a positive reality, not an absence.",
    },
    "https://example.org/blank": {"title": "Nothing here", "raw_content": ""},
}

SEARCH = {"etymology": ["etym", "aquinas"], "earliest": ["etym"], "coined": ["etym"], "first proposed": ["etym", "aquinas"],
          "apologetics": ["apol"], "objection": ["apol"], "first study": ["blank"], "experiment": ["blank"]}


def scripted(calls):
    async def llm(stage, system, user):
        d = json.loads(user)
        calls.append((stage, d.get("question", "")[:20]))
        assert system.strip()
        if stage == "queries":
            assert d["hint_queries"] and "privatio boni" in d["hint_queries"][0]
            return json.dumps({"queries": ["malum privatio boni Augustine", "evil as absence debunked"]})
        if stage == "extract":
            text = PAGES[d["url"]]["raw_content"]
            sents = [s.strip() for s in text.replace("\n", " ").split(". ") if len(s) > 30]
            out = [{"quote": s if s.endswith(".") else s + ".", "why": "x"} for s in sents]
            if "etym" in d["url"]:
                out.append({"quote": "Plotinus coined the phrase privatio boni in 250 AD.", "why": "invented"})
            return json.dumps({"passages": out})
        if stage == "answer":
            ps = {p["url"].rsplit("/", 1)[1]: [] for p in d["passages"]}
            for p in d["passages"]:
                ps[p["url"].rsplit("/", 1)[1]].append(p["id"])
            q = d["question"]
            if q.startswith("Where and when"):
                return json.dumps({"findings": [
                    {"claim": "Aquinas: evil is privation of a due good", "who": "Thomas Aquinas", "when": "1265",
                     "where": "Summa Theologiae", "passages": ps["aquinas"][:1], "note": ""},
                    {"claim": "Augustine calls evil the privation of good", "who": "Augustine of Hippo", "when": "c. 397",
                     "where": "Confessions", "passages": ps["etym"], "note": "earliest found, not proven first"},
                    {"claim": "Plotinus coined it", "who": "Plotinus", "when": "250 AD", "where": None,
                     "passages": ps["etym"][:1], "note": ""},
                    {"claim": "Ghost citation", "who": "Nobody", "when": "1500", "where": None, "passages": ["P99"]},
                ], "status_note": "Chain from Augustine to Aquinas; no hop before Augustine found."})
            if q.startswith("Who first stated"):
                return json.dumps({"findings": [
                    {"claim": "Augustine states it", "who": "Augustine of Hippo", "when": "c. 397", "passages": ps["etym"]},
                    {"claim": "Plato anticipated it", "who": "Plato", "when": "380 BC", "passages": ps["etym"]},
                    {"claim": "No date", "who": "Augustine", "when": None, "passages": ps["etym"]},
                ], "status_note": ""})
            if q.startswith("How is this used in apologetics"):
                return json.dumps({"findings": [
                    {"claim": "Privation view answers 'God created evil'", "who": "William Lane Craig", "passages": ps["apol"][:1]},
                    {"claim": "Pain is positive, not absence", "who": "J. L. Mackie", "passages": ps["apol"]},
                ], "status_note": ""})
            raise AssertionError(q)
        raise AssertionError(stage)
    return llm


async def fake_search(query, n):
    hit = next((v for k, v in SEARCH.items() if k in query), [])
    return [{"href": f"https://example.org/{h}", "title": PAGES[f"https://example.org/{h}"]["title"],
             "body": "s", "retriever": "Fake"} for h in hit][:n]


async def fake_scrape(urls):
    return [{"url": u, **PAGES[u]} for u in urls if u in PAGES]


@pytest.fixture
def run(tmp_path):
    calls = []
    deps = dp.Deps(llm=scripted(calls), search=fake_search, scrape=fake_scrape,
                   models={s: "fake:model" for s in ("queries", "extract", "answer")})

    def go(items=None):
        t = dt.Targeted("privatio boni", tmp_path, deps, dt.load_battery(), items, log=lambda m: None)
        return asyncio.run(t.run()), calls
    return go


def test_stated_in():
    texts = ["Augustine of Hippo, writing in the Confessions (c. 397), said so.", "In the 1590s it spread."]
    assert dt.stated_in("when", "c. 397", texts)
    assert dt.stated_in("when", "397 AD", texts)                 # the year is what must be stated
    assert dt.stated_in("when", "1590s", texts)
    assert not dt.stated_in("when", "250 AD", texts)
    assert not dt.stated_in("when", "unknown", texts)
    assert dt.stated_in("who", "Augustine of Hippo", texts)
    assert not dt.stated_in("who", "Plato", texts)
    assert dt.stated_in("who", "Smith and Jones", ["Smith and Jones (1952) found it."])
    assert not dt.stated_in("who", "Smith and Brown", ["Smith and Jones (1952) found it."])
    assert not dt.stated_in("when", "397", ["It was written in 1397."])          # whole numbers only
    assert not dt.stated_in("who", "Ann Craig", ["Found on craigslist."])          # whole words only


def test_battery_runs_and_rejects_unsupported(run, tmp_path):
    facts, calls = run()
    items = facts["items"]
    assert list(items) == ["origin", "first_statement", "first_study", "apologetics"]   # the defaults

    o = items["origin"]
    assert o["status"] == "found"
    assert [f["who"] for f in o["findings"]] == ["Augustine of Hippo", "Thomas Aquinas"]   # oldest first
    reasons = {r["finding"]["claim"]: r["reasons"] for r in o["rejected"]}
    assert any("250 AD" in x for x in reasons["Plotinus coined it"])
    assert reasons["Ghost citation"] == ["cites no passage that exists"]
    p = o["findings"][0]["passages"][0]
    page = PAGES[p["url"]]["raw_content"]
    assert page[p["start"]:p["end"]] == p["quote"]
    ps = json.loads((tmp_path / "items/origin/passages.json").read_text(encoding="utf-8"))
    assert [r["quote"] for r in ps["rejected"]] == ["Plotinus coined the phrase privatio boni in 250 AD."]
    q = json.loads((tmp_path / "items/origin/queries.json").read_text(encoding="utf-8"))["queries"]
    assert q[0] == {"query": "privatio boni etymology", "source": "hint"}
    assert any(x.get("warning") for x in q if "debunked" in x["query"])

    fs = items["first_statement"]
    assert [f["who"] for f in fs["findings"]] == ["Augustine of Hippo"]
    why = {r["finding"]["claim"]: r["reasons"] for r in fs["rejected"]}
    assert any("Plato" in x for x in why["Plato anticipated it"])
    assert "when required but empty" in why["No date"]

    st = items["first_study"]
    assert st["status"] == "unknown" and st["findings"] == []          # unknown is a legal answer
    assert "no passage" in st["note"]

    ap = items["apologetics"]
    assert sorted(f["who"] for f in ap["findings"]) == ["J. L. Mackie", "William Lane Craig"]

    md = (tmp_path / "facts.md").read_text(encoding="utf-8")
    assert "## Origin and first use — found" in md and "## First study — unknown" in md
    assert "Rejected (2)" in md
    rec = json.loads((tmp_path / "run.json").read_text(encoding="utf-8"))
    assert rec["status"] == "done" and rec["summary"]["first_study"] == "unknown"
    assert rec["findings"] == 5 and rec["rejected"] == 4


def test_items_needing_other_runs_are_skipped(run):
    facts, calls = run(["origin", "essence_paper", "last30"])
    assert facts["items"]["essence_paper"]["status"] == "skipped"
    assert "fork_map" in facts["items"]["essence_paper"]["note"]
    assert facts["items"]["last30"]["status"] == "skipped"
    assert not any(q.startswith("Which study") for _, q in calls)


def test_unknown_item_is_refused(tmp_path):
    deps = dp.Deps(llm=None, search=None, scrape=None)
    with pytest.raises(ValueError):
        dt.Targeted("x", tmp_path, deps, dt.load_battery(), ["nope"])


def test_failed_item_does_not_stop_the_others(run, tmp_path, monkeypatch):
    real = dt.Targeted.run_item

    async def boom(self, item):
        if item["id"] == "apologetics":
            raise RuntimeError("provider down")
        return await real(self, item)
    monkeypatch.setattr(dt.Targeted, "run_item", boom)
    facts, _ = run()
    assert facts["items"]["apologetics"]["status"] == "failed"
    assert facts["items"]["origin"]["status"] == "found"
    assert (tmp_path / "items/apologetics/error.txt").exists()
