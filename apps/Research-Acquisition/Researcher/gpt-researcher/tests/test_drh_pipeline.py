"""drh_pipeline.py: the visible pipeline, stage by stage, with a scripted model,
search and scraper (no network). Fixture topic: "the devil" (WEB_RESEARCH_v0.1 §2)."""
import argparse
import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import drh_pipeline as dp  # noqa: E402

PAGES = {
    "https://example.org/hasatan": {
        "title": "Ha-satan in the Hebrew Bible",
        "raw_content": "Navigation | Home\n\nIn Job and Zechariah, ha-satan carries the definite article.\n"
                       "It is a title, “the accuser”, an office in the divine court rather than a proper name. "
                       "Most commentators read him as subordinate to God, not as God’s rival.\n\nFooter",
    },
    "https://example.org/aquinas": {
        "title": "Aquinas on evil as privation",
        "raw_content": "Aquinas holds that evil is not a substance.   Evil is the privation of a due good.\n"
                       "On this view the devil is a created angel whose nature is good and whose will turned away.",
    },
    "https://example.org/secular": {
        "title": "The devil as a psychological projection",
        "raw_content": "Some psychologists argue that the figure of Satan externalises inner conflict. "
                       "The devil, on this reading, is a projection of human aggression onto an imagined agent.",
    },
    "https://example.org/listicle": {"title": "10 scary facts", "raw_content": "Click here for facts."},
}

PREMISE = {
    "neutral_question": "What do sources say about the figure called the devil?",
    "presuppositions": [
        {"id": "A1", "statement": "The devil exists as a personal being", "kind": "existence", "contested": True,
         "how_it_could_fail": "the figure is a literary or psychological construct"},
        {"id": "A2", "statement": "'The devil' names one figure across texts", "kind": "definition", "contested": True,
         "how_it_could_fail": "ha-satan and the NT Satan are different figures"},
    ],
    "loaded_terms": [{"term": "the devil", "why": "assumes one figure", "neutral": "adversary figures"}],
    "expected_legs": [
        {"id": "L1", "position": "A fallen angel, created good", "holders": "Aquinas, classical theism", "rests_on": ["A1"]},
        {"id": "L2", "position": "Ha-satan is a court title, not Satan", "holders": "Hebrew Bible scholars", "rejects": ["A2"]},
        {"id": "L3", "position": "A cosmic rival equal to God", "holders": "dualist traditions", "rests_on": ["A1"]},
        {"id": "L4", "position": "A psychological projection", "holders": "secular psychology", "rejects": ["A1"]},
    ],
}


def scripted_llm(calls):
    async def llm(stage, system, user):
        calls.append(stage)
        data = json.loads(user)
        assert system.strip(), f"empty prompt for {stage}"
        if stage == "premise":
            return "```json\n" + json.dumps(PREMISE) + "\n```"
        if stage == "cast":
            # L3 and A2 left out on purpose: the pipeline must fill them.
            return json.dumps({"queries": [
                {"query": "the devil", "targets": "neutral"},
                {"query": "devil existence arguments for and against", "targets": "A1"},
                {"query": "Aquinas devil fallen angel privation", "targets": "L1"},
                {"query": "ha-satan Hebrew Bible accuser title", "targets": "L2"},
                {"query": "devil myth debunked", "targets": "L4"},
            ]})
        if stage == "triage":
            out = []
            for r in data["results"]:
                keep = "listicle" not in r["url"]
                bears = {"hasatan": ["L2", "A2"], "aquinas": ["L1"], "secular": ["L4", "A1"]}
                b = next((v for k, v in bears.items() if k in r["url"]), [])
                out.append({"id": r["id"], "keep": keep, "reason": "primary" if keep else "listicle", "bears_on": b})
            return json.dumps({"results": out})
        if stage == "extract":
            url = data["url"]
            if "hasatan" in url:
                return json.dumps({"passages": [
                    # straight quotes and different spacing vs the page: still verbatim
                    {"quote": 'It is a title, "the accuser", an office in the divine court rather than a proper name.',
                     "bears_on": ["L2"], "stance": "supports", "why": "title not name"},
                    {"quote": "Ha-satan is clearly the same being as Lucifer.", "bears_on": ["L1"],
                     "stance": "opposes", "why": "invented"},
                ]})
            if "aquinas" in url:
                return json.dumps({"passages": [
                    {"quote": "Evil is the privation of a due good.", "bears_on": ["L1"], "stance": "supports", "why": "privatio"},
                    {"quote": "Aquinas holds that evil is not a substance. ... whose will turned away.",
                     "bears_on": ["L1"], "stance": "supports", "why": "elided"},
                ]})
            return json.dumps({"passages": [
                {"quote": "The devil, on this reading, is a projection of human aggression onto an imagined agent.",
                 "bears_on": ["L4"], "stance": "supports", "why": "projection"}]})
        if stage == "forks":
            ids = [p["id"] for p in data["passages"]]
            got = {p["url"].rsplit("/", 1)[1]: p["id"] for p in data["passages"]}
            by = {k: [got[k]] if k in got else [] for k in ("hasatan", "aquinas", "secular")}
            return json.dumps({
                "claims": [{"id": "C1", "claim": "Ha-satan is a title", "passages": by["hasatan"]},
                           {"id": "C2", "claim": "Evil is privation", "passages": [ids[1]]}],
                "forks": [
                    {"id": "F1", "fork_name": "Identity", "core_question": "Is ha-satan the NT Satan?",
                     "tests_presupposition": "A2",
                     "positions": [{"id": "F1.a", "position": "A title", "strongest_form": "...", "matches_leg": "L2",
                                    "claims": ["C1"], "passages": by["hasatan"]}]},
                    {"id": "F2", "fork_name": "Ontology", "core_question": "What is the devil?",
                     "tests_presupposition": "A1",
                     "positions": [
                         {"id": "F2.a", "position": "Fallen angel", "strongest_form": "...", "matches_leg": "L1",
                          "claims": ["C2"], "passages": [ids[1], "P99"]},
                         {"id": "F2.b", "position": "Cosmic rival", "strongest_form": "", "matches_leg": "L3",
                          "claims": [], "passages": []},
                         {"id": "F2.c", "position": "Projection", "strongest_form": "...", "matches_leg": "L4",
                          "claims": [], "passages": by["secular"]},
                         {"id": "F2.d", "position": "Folk figure", "strongest_form": "...", "matches_leg": "L9",
                          "claims": [], "passages": by["secular"]},
                     ]},
                ],
                "unplaced_passages": []})
        if stage == "synthesize":
            return ("# The devil\n\nHa-satan is a court title in Job and Zechariah [P1]. "
                    "Aquinas treats evil as a privation of a due good [P2, P3]. "
                    "This sentence has no citation at all and should be counted. "
                    "A wrong id gets flagged here too [P42].\n")
        raise AssertionError(stage)
    return llm


async def fake_search(query, n):
    rows = {
        "ha-satan": ["hasatan", "listicle"], "Aquinas": ["aquinas", "hasatan"], "debunked": ["secular"],
        "existence": ["secular", "aquinas"], "the devil": ["listicle"],
    }
    hit = next((v for k, v in rows.items() if k in query), [])
    return [{"href": f"https://example.org/{h}", "title": PAGES[f"https://example.org/{h}"]["title"],
             "body": "snippet", "retriever": "FakeRetriever"} for h in hit][:n]


async def fake_scrape(urls):
    return [{"url": u, **PAGES[u]} for u in urls if u in PAGES]


@pytest.fixture
def deps():
    calls = []
    return dp.Deps(llm=scripted_llm(calls), search=fake_search, scrape=fake_scrape,
                   models={s: "fake:model" for s in dp.STAGES}), calls


def test_locate_tolerates_spacing_and_quote_style_only():
    page = "He said “no”   to the  offer, and left.\nThen more."
    s, e = dp.locate('He said "no" to the offer, and left.', page)
    assert page[s:e] == "He said “no”   to the  offer, and left."
    assert dp.locate("He said yes to the offer, and left.", page) is None
    assert dp.locate("short", page) is None


def test_full_pipeline_writes_every_stage(tmp_path, deps):
    d, calls = deps
    pipe = dp.Pipeline("Who is the devil?", tmp_path, d, {"recast": False}, log=lambda m: None)
    rec = asyncio.run(pipe.run())
    for f in ["premise.json", "net.json", "triage.json", "passages.json", "forks.json", "forks.md",
              "report.md", "pipeline.json", "llm_calls.jsonl"]:
        assert (tmp_path / f).exists(), f
    assert [s for s in rec["stages"]] == dp.STAGES
    assert all(v["status"] == "done" for v in rec["stages"].values())

    net = json.loads((tmp_path / "net.json").read_text())
    targets = {q["targets"]: q["source"] for q in net["queries"]}
    assert targets["L3"] == "filled" and targets["A2"] == "filled"      # balance by construction
    assert any("verdict" in w and "debunked" in w for w in rec["warnings"])
    listicle = next(r for r in net["results"] if r["url"].endswith("listicle"))
    assert len(listicle["found_by"]) == 2                               # deduped, both finders kept

    tri = json.loads((tmp_path / "triage.json").read_text())
    assert all(r["reason"] for r in tri["results"])
    assert [r["keep"] for r in tri["results"] if r["url"].endswith("listicle")] == [False]

    ps = json.loads((tmp_path / "passages.json").read_text())
    quotes = {p["id"]: p for p in ps["passages"]}
    assert len(quotes) == 4
    p1 = next(p for p in ps["passages"] if "hasatan" in p["url"])
    page = PAGES[p1["url"]]["raw_content"]
    assert page[p1["start"]:p1["end"]] == p1["quote"] and "“the accuser”" in p1["quote"]
    assert any(p["elided"] for p in ps["passages"])
    assert [r["quote"] for r in ps["rejected"]] == ["Ha-satan is clearly the same being as Lucifer."]

    forks = json.loads((tmp_path / "forks.json").read_text())
    legs = forks["legs"]
    assert legs["expected_not_found"] == ["L3"]                          # the empty leg is a finding
    assert legs["found_not_expected"] == ["F2.d"]                        # L9 doesn't exist -> unexpected
    assert "F1" in legs["one_fork_one_side"]
    pos = {p["id"]: p for f in forks["forks"] for p in f["positions"]}
    assert "P99" not in pos["F2.a"]["passages"]
    assert pos["F2.b"]["status"] == "no source"
    assert any("do not exist" in w and "P99" in w for w in rec["warnings"])
    md = (tmp_path / "forks.md").read_text()
    assert "L3 (A cosmic rival equal to God)" in md and "### F2.b" in md

    syn = rec["stages"]["synthesize"]
    assert syn["unknown_ids"] == ["P42"] and syn["sentences_without_citation"] == 1
    report = (tmp_path / "report.md").read_text()
    assert "## Passages" in report and "chars" in report

    assert pipe.summary()["legs_expected_not_found"] == ["L3"]
    assert pipe.summary()["legs_expected_found"] == 3 and pipe.summary()["legs_found_not_expected"] == 1
    assert calls.count("premise") == 1 and calls.count("synthesize") == 1


def test_recast_runs_once_for_uncovered_legs(tmp_path, deps):
    d, calls = deps
    pipe = dp.Pipeline("Who is the devil?", tmp_path, d, {"recast": True}, log=lambda m: None)
    asyncio.run(pipe.run())
    tri = json.loads((tmp_path / "triage.json").read_text())
    assert tri["recast"]["legs"] == ["L3"]
    assert tri["recast"]["still_uncovered"] == ["L3"]
    net = json.loads((tmp_path / "net.json").read_text())
    assert [q["source"] for q in net["queries"]].count("recast") == 1


def test_seen_urls_are_not_triaged(tmp_path, deps):
    d, _ = deps
    pipe = dp.Pipeline("Who is the devil?", tmp_path, d, {"recast": False},
                       skip_urls={"https://example.org/secular"}, log=lambda m: None)
    asyncio.run(pipe.run())
    tri = json.loads((tmp_path / "triage.json").read_text())
    sec = next(r for r in tri["results"] if r["url"].endswith("secular"))
    assert not sec["keep"] and "earlier run" in sec["reason"]


def test_resume_applies_person_overrides(tmp_path, deps):
    d, calls = deps
    pipe = dp.Pipeline("Who is the devil?", tmp_path, d, {"recast": False}, log=lambda m: None)
    asyncio.run(pipe.run())
    (tmp_path / "overrides.json").write_text(json.dumps({"keep": ["https://example.org/listicle"],
                                                         "drop": ["https://example.org/secular"]}))
    calls.clear()
    again = dp.Pipeline("Who is the devil?", tmp_path, d, {"recast": False}, log=lambda m: None)
    rec = asyncio.run(again.run("extract"))
    assert calls[0] == "extract" and "premise" not in calls and "triage" not in calls
    assert rec["overrides_applied"] == 2
    assert set(rec["stages"]) == set(dp.STAGES)                          # earlier stages' record kept
    tri = json.loads((tmp_path / "triage.json").read_text())
    lst = next(r for r in tri["results"] if r["url"].endswith("listicle"))
    assert lst["keep"] and lst["by"] == "person" and "model said: listicle" in lst["reason"]
    ps = json.loads((tmp_path / "passages.json").read_text())
    assert not any("secular" in p["url"] for p in ps["passages"])


def test_failed_stage_is_recorded(tmp_path, deps):
    d, _ = deps

    async def broken(stage, system, user):
        if stage == "triage":
            raise RuntimeError("provider down")
        return await scripted_llm([])(stage, system, user)

    d.llm = broken
    pipe = dp.Pipeline("Who is the devil?", tmp_path, d, log=lambda m: None)
    with pytest.raises(RuntimeError):
        asyncio.run(pipe.run())
    rec = json.loads((tmp_path / "pipeline.json").read_text())
    assert rec["failed_at"] == "triage" and rec["stages"]["triage"]["status"] == "failed"
    assert rec["stages"]["cast"]["status"] == "done"


# ------------------------------------------------------------ via the queue
spec = importlib.util.spec_from_file_location("drh_queue", ROOT / "drh_queue.py")
drh_queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drh_queue)


@pytest.fixture(autouse=True)
def real_gpt_researcher_modules(monkeypatch):
    for key, mod in list(sys.modules.items()):
        if key.startswith("gpt_researcher") and getattr(mod, "__file__", None) is None:
            monkeypatch.delitem(sys.modules, key)


def test_queue_runs_fork_map_job(tmp_path, monkeypatch, deps):
    from gpt_researcher.agent import GPTResearcher

    monkeypatch.setenv("OPENAI_API_KEY", "dummy-not-used")
    d, _ = deps
    monkeypatch.setattr(dp, "gptr_deps", lambda cfg, retrievers, add_costs=None, websocket=None: d)

    async def never(self, *a, **k):
        raise AssertionError("fork_map must not use GPT Researcher's own research or report")
    monkeypatch.setattr(GPTResearcher, "conduct_research", never)
    monkeypatch.setattr(GPTResearcher, "write_report", never)

    jobs, out = tmp_path / "jobs", tmp_path / "out"
    jobs.mkdir()
    (jobs / "devil.yaml").write_text('query: "Who is the devil?"\njob_type: fork_map\n'
                                     'pipeline: {recast: false, max_keep: 10}\n', encoding="utf-8")
    (jobs / "bad.yaml").write_text('query: "x"\njob_type: fork_map\npipeline: {max_kept: 3}\n', encoding="utf-8")
    args = argparse.Namespace(jobs=str(jobs), out=str(out), parallel=1, only=None, dry_run=False, retry_failed=False)
    assert asyncio.run(drh_queue.main_async(args)) == 1                  # bad.yaml is a problem, not run
    assert (jobs / "bad.yaml").exists()
    run_dir = next((out / "devil").iterdir())
    rec = json.loads((run_dir / "run.json").read_text())
    assert rec["status"] == "done", rec.get("error")
    assert rec["receipt_summary"]["legs_expected_not_found"] == ["L3"]
    assert (run_dir / "forks.md").exists() and (run_dir / "report.md").read_text().startswith("# The devil")
    ledger = (out / "_ledger" / "devil.jsonl").read_text().splitlines()
    assert "https://example.org/hasatan" in json.loads(ledger[0])["visited_urls"]
    assert list((jobs / "done").glob("*_devil.yaml"))
