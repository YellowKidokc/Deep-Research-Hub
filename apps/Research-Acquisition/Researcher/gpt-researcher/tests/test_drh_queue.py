"""drh_queue.py: claim -> run -> outputs -> done/, ledger seeding, validation.
GPT Researcher's network-calling methods are stubbed."""
import argparse
import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from gpt_researcher.agent import GPTResearcher  # bound before other tests stub modules

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("drh_queue", ROOT / "drh_queue.py")
drh_queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drh_queue)


@pytest.fixture(autouse=True)
def real_gpt_researcher_modules(monkeypatch):
    for key, mod in list(sys.modules.items()):
        if key.startswith("gpt_researcher") and getattr(mod, "__file__", None) is None:
            monkeypatch.delitem(sys.modules, key)


@pytest.fixture
def stubbed(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-not-used")
    seen = []

    async def conduct(self):
        seen.append({"query": self.query, "visited_in": set(self.visited_urls),
                     "model": self.cfg.smart_llm_model, "retrievers": [r.__name__ for r in self.retrievers]})
        self.visited_urls.update({f"https://example.org/{self.query[:5]}/{i}" for i in range(3)})
        return []

    async def write(self, *a, **k):
        return f"# Report for {self.query}\n"

    monkeypatch.setattr(GPTResearcher, "conduct_research", conduct)
    monkeypatch.setattr(GPTResearcher, "write_report", write)
    return seen


def run(jobs, out, **kw):
    args = argparse.Namespace(jobs=str(jobs), out=str(out), parallel=kw.get("parallel", 2),
                              only=kw.get("only"), dry_run=kw.get("dry_run", False),
                              retry_failed=kw.get("retry_failed", False))
    return asyncio.run(drh_queue.main_async(args))


def test_queue_runs_moves_and_records(tmp_path, stubbed):
    jobs, out = tmp_path / "jobs", tmp_path / "out"
    jobs.mkdir()
    (jobs / "_defaults.yaml").write_text("report_source: web\nchapter: AX_GI_03\n", encoding="utf-8")
    (jobs / "one.yaml").write_text('query: "first question"\nmeta: {question_id: Q-A}\n', encoding="utf-8")
    (jobs / "two.yaml").write_text('query: "second question"\nmodel: "deepseek:deepseek-reasoner"\n'
                                   'retrievers: [arxiv]\n', encoding="utf-8")
    assert run(jobs, out) == 0

    assert sorted(p.name.split("_", 1)[1] for p in (jobs / "done").iterdir()) == ["one.yaml", "two.yaml"]
    assert {p.name for p in jobs.glob("*.yaml")} == {"_defaults.yaml"}
    assert not list((jobs / "running").iterdir())
    run_dir = next((out / "one").iterdir())
    assert {p.name for p in run_dir.iterdir()} >= {"report.md", "receipt.json", "sources.json", "run.json", "events.jsonl"}
    rec = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert rec["status"] == "done" and rec["job"]["meta"] == {"question_id": "Q-A"}
    assert len(json.loads((run_dir / "sources.json").read_text(encoding="utf-8"))["visited_urls"]) == 3
    by_q = {s["query"]: s for s in stubbed}
    assert by_q["second question"]["model"] == "deepseek-reasoner"
    assert by_q["second question"]["retrievers"] == ["ArxivSearch"]
    ledger = (out / "_ledger" / "AX_GI_03.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(ledger) == 2  # both jobs share the chapter ledger

    # Next run on the same chapter skips what was already visited.
    (jobs / "three.yaml").write_text('query: "third"\nvisited_urls_from: AX_GI_03\n', encoding="utf-8")
    assert run(jobs, out) == 0
    third = next(s for s in stubbed if s["query"] == "third")
    assert len(third["visited_in"]) == 6
    rec3 = json.loads(next((out / "three").iterdir()).joinpath("run.json").read_text(encoding="utf-8"))
    assert rec3["seeded_visited_urls"] == 6


def test_validation_blocks_bad_jobs(tmp_path, stubbed):
    jobs, out = tmp_path / "jobs", tmp_path / "out"
    jobs.mkdir()
    (jobs / "typo.yaml").write_text('query: "q"\nretriver: [arxiv]\n', encoding="utf-8")
    (jobs / "notyet.yaml").write_text('query: "q"\njob_type: prior_art\n', encoding="utf-8")
    (jobs / "nofolder.yaml").write_text('query: "q"\nreport_source: local\n', encoding="utf-8")
    (jobs / "ok.yaml").write_text('query: "fine"\n', encoding="utf-8")
    assert run(jobs, out) == 1           # problems reported -> non-zero
    assert [s["query"] for s in stubbed] == ["fine"]
    assert {p.name for p in jobs.glob("*.yaml")} >= {"typo.yaml", "notyet.yaml", "nofolder.yaml"}


def test_failure_goes_to_failed(tmp_path, stubbed, monkeypatch):
    async def boom(self):
        raise RuntimeError("provider down")
    monkeypatch.setattr(GPTResearcher, "conduct_research", boom)
    jobs, out = tmp_path / "jobs", tmp_path / "out"
    jobs.mkdir()
    (jobs / "x.yaml").write_text('query: "x"\n', encoding="utf-8")
    assert run(jobs, out) == 1
    assert len(list((jobs / "failed").iterdir())) == 1
    run_dir = next((out / "x").iterdir())
    assert json.loads((run_dir / "run.json").read_text(encoding="utf-8"))["error"] == "RuntimeError: provider down"
    assert (run_dir / "error.txt").exists() and (run_dir / "receipt.json").exists()

    assert run(jobs, out, retry_failed=True) == 0
    assert (jobs / "x.yaml").exists() and not list((jobs / "failed").iterdir())
