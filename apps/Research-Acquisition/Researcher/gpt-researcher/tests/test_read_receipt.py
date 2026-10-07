"""Read receipt: per-request doc_path, config overrides, and the counts the
receipt records. No network: embeddings are a deterministic fake and the
LLM planning step is stubbed."""
import asyncio
import json
import os
import sys

import pytest
from langchain_core.embeddings import Embeddings

# Bound at import: other test files swap stub modules into sys.modules.
from gpt_researcher.agent import GPTResearcher
from gpt_researcher.context.compression import ContextCompressor
from gpt_researcher.document import DocumentLoader
from gpt_researcher.receipts import ReadReceipt


@pytest.fixture(autouse=True)
def real_gpt_researcher_modules(monkeypatch):
    """Other test files leave stub modules (no __file__) in sys.modules, and
    Config imports lazily. Hide the stubs for the length of each test here."""
    for key, mod in list(sys.modules.items()):
        if key.startswith("gpt_researcher") and getattr(mod, "__file__", None) is None:
            monkeypatch.delitem(sys.modules, key)


class KeywordEmbeddings(Embeddings):
    """Similarity 1.0 when both texts mention 'gravity', else 0."""

    def _v(self, t):
        return [1.0, 0.0] if "gravity" in t.lower() else [0.0, 1.0]

    def embed_documents(self, texts):
        return [self._v(t) for t in texts]

    def embed_query(self, text):
        return self._v(text)


def make_folder(tmp_path):
    (tmp_path / "a.txt").write_text("gravity " * 50, encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("unrelated words " * 40, encoding="utf-8")
    (tmp_path / "c.xyz").write_text("not a supported type", encoding="utf-8")
    (tmp_path / "d.txt").write_text("", encoding="utf-8")
    (tmp_path / "big.txt").write_text("x" * 5000, encoding="utf-8")
    return tmp_path


def test_loader_records_every_file(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_DOCUMENT_MAX_BYTES", "4000")
    folder = make_folder(tmp_path)
    r = ReadReceipt()
    docs = asyncio.run(DocumentLoader(str(folder), receipt=r).load())
    files = {f["path"]: f for f in r.to_dict()["files"]}
    assert set(files) == {"a.txt", os.path.join("sub", "b.txt"), "c.xyz", "d.txt", "big.txt"}
    assert files["a.txt"]["status"] == "loaded"
    assert files[os.path.join("sub", "b.txt")]["status"] == "loaded"
    assert files["c.xyz"]["reason"] == "unsupported type: .xyz"
    assert files["d.txt"]["reason"] == "empty: no text extracted"
    assert files["big.txt"]["reason"].startswith("size cap: 5000 bytes")
    assert {d["url"] for d in docs} == {"a.txt", os.path.join("sub", "b.txt")}


def _pages(n_good, n_bad):
    pages = [{"url": f"good{i}.txt", "raw_content": "gravity pulls " * 120} for i in range(n_good)]
    pages += [{"url": f"bad{i}.txt", "raw_content": "other topic " * 120} for i in range(n_bad)]
    return pages


def test_compressor_counts_and_unchanged_output():
    pages = _pages(3, 3)
    plain = ContextCompressor(pages, KeywordEmbeddings(), similarity_threshold=0.5)
    expected = asyncio.run(plain.async_get_context("gravity", max_results=10))

    r = ReadReceipt()
    seen = ContextCompressor(pages, KeywordEmbeddings(), similarity_threshold=0.5,
                             receipt=r, receipt_query="sub q")
    got = asyncio.run(seen.async_get_context("gravity", max_results=10))
    assert got == expected  # observing must not change the context

    q = r.to_dict()["sub_queries"][0]
    assert q["sub_query"] == "sub q" and q["path"] == "filtered"
    assert q["chunks_produced"] > q["chunks_kept"] > 0
    assert q["chunks_returned"] == min(10, q["chunks_kept"])
    assert all(c["kept"] == 0 for s, c in q["by_source"].items() if s.startswith("bad"))
    assert q["chunks_dropped_by_similarity"] == q["chunks_produced"] - q["chunks_kept"]


def test_researcher_per_request_folder_and_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-not-used")
    monkeypatch.setenv("TAVILY_API_KEY", "dummy-not-used")
    monkeypatch.delenv("DOC_PATH", raising=False)

    (tmp_path / "docs").mkdir()
    folder = make_folder(tmp_path / "docs")
    (folder / "a.txt").write_text("gravity bends light. " * 600, encoding="utf-8")
    other = tmp_path / "other"
    other.mkdir()
    (other / "only.txt").write_text("gravity in another folder " * 400, encoding="utf-8")

    # Cost estimation downloads a tiktoken encoding; not what is under test.
    import gpt_researcher.context.compression as compression
    monkeypatch.setattr(compression, "estimate_embedding_cost", lambda **k: 0.0)

    def run(path):
        r = GPTResearcher(query="gravity", report_source="local", doc_path=str(path),
                          agent="test", role="test", verbose=False,
                          config_overrides={"SIMILARITY_THRESHOLD": "0.5", "CURATE_SOURCES": "false",
                                            "MAX_SEARCH_RESULTS_PER_QUERY": 3})
        r.memory.get_embeddings = lambda: KeywordEmbeddings()

        async def plan(query, query_domains=None):
            return ["gravity sub-query"]
        r.research_conductor.plan_research = plan
        asyncio.run(r.conduct_research())
        return r

    first = run(folder)
    rec = first.get_read_receipt()
    assert rec["doc_path"] == str(folder)
    assert rec["settings"]["overrides"] == {"SIMILARITY_THRESHOLD": 0.5, "CURATE_SOURCES": False,
                                           "MAX_SEARCH_RESULTS_PER_QUERY": 3}
    assert first.cfg.similarity_threshold == 0.5
    assert rec["summary"]["files_found"] == 5 and rec["summary"]["files_loaded"] == 3
    # one planned sub-query plus the original query
    assert sorted(q["sub_query"] for q in rec["sub_queries"]) == ["gravity", "gravity sub-query"]
    assert rec["errors"] == []
    assert "a.txt" not in rec["summary"]["local_files_never_used"]

    second = run(other)  # same process, different folder: no restart
    rec2 = second.get_read_receipt()
    assert rec2["summary"]["files_found"] == 1
    assert [f["path"] for f in rec2["files"]] == ["only.txt"]
    out = second.write_read_receipt(str(tmp_path / "out" / "r.receipt.json"))
    assert json.load(open(out))["doc_path"] == str(other)


def test_sub_query_error_is_recorded(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-not-used")
    (tmp_path / "a.txt").write_text("gravity " * 2000, encoding="utf-8")
    r = GPTResearcher(query="gravity", report_source="local", doc_path=str(tmp_path),
                      agent="t", role="t", verbose=False, config_overrides={"CURATE_SOURCES": False})

    def boom():
        raise RuntimeError("embeddings offline")
    r.memory.get_embeddings = boom

    async def plan(query, query_domains=None):
        return []
    r.research_conductor.plan_research = plan
    asyncio.run(r.conduct_research())
    rec = r.get_read_receipt()
    assert rec["summary"]["sub_query_errors"] == 1
    assert rec["errors"][0]["error"] == "RuntimeError: embeddings offline"


def test_override_whitelist():
    os.environ.setdefault("OPENAI_API_KEY", "dummy-not-used")
    with pytest.raises(ValueError, match="not allowed"):
        GPTResearcher(query="q", config_overrides={"SMART_LLM": "openai:gpt-4o"})
    with pytest.raises(ValueError, match="not a folder"):
        GPTResearcher(query="q", report_source="local", doc_path="/nonexistent/folder")
