"""doc_path and config_overrides travel from the websocket start message to
GPTResearcher, per request, and the read receipt lands next to the report."""
import asyncio
import json
import os
import sys

import pytest

# Bound at import: other test files swap stub modules into sys.modules.
import backend.server.server_utils as server_utils
from backend.server.websocket_manager import WebSocketManager
from gpt_researcher.agent import GPTResearcher


@pytest.fixture(autouse=True)
def real_gpt_researcher_modules(monkeypatch):
    for key, mod in list(sys.modules.items()):
        if key.startswith("gpt_researcher") and getattr(mod, "__file__", None) is None:
            monkeypatch.delitem(sys.modules, key)


class FakeSocket:
    def __init__(self):
        self.sent = []

    async def send_json(self, data):
        self.sent.append(data)


def test_start_message_carries_folder_and_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-not-used")
    folder = tmp_path / "chapter_docs"
    folder.mkdir()
    (folder / "a.md").write_text("# A\n\ngravity", encoding="utf-8")
    seen = {}

    async def conduct(self):
        seen["doc_path"] = self.cfg.doc_path
        seen["similarity"] = self.cfg.similarity_threshold
        seen["curate"] = self.cfg.curate_sources
        self.read_receipt.file_found("a.md", 10)
        self.read_receipt.file_loaded("a.md", 1, 10)
        return []

    async def write(self, *a, **k):
        return "# report"

    async def files(report, name):
        os.makedirs("outputs", exist_ok=True)
        p = os.path.join("outputs", f"{name}.md")
        open(p, "w").write(report)
        return {"md": p}

    monkeypatch.setattr(GPTResearcher, "conduct_research", conduct)
    monkeypatch.setattr(GPTResearcher, "write_report", write)
    monkeypatch.setattr(server_utils, "generate_report_files", files)

    msg = {"task": "gravity", "report_type": "research_report", "report_source": "local",
           "tone": "Objective", "doc_path": str(folder),
           "config_overrides": {"SIMILARITY_THRESHOLD": "0.2", "CURATE_SOURCES": "false"}}
    ws = FakeSocket()
    asyncio.run(server_utils.handle_start_command(ws, "start " + json.dumps(msg), WebSocketManager()))

    assert seen == {"doc_path": str(folder), "similarity": 0.2, "curate": False}
    paths = next(m["output"] for m in ws.sent if m.get("type") == "path")
    assert paths["receipt"].endswith(".receipt.json")
    receipt = json.load(open(paths["receipt"]))
    assert receipt["doc_path"] == str(folder)
    assert receipt["settings"]["overrides"] == {"SIMILARITY_THRESHOLD": 0.2, "CURATE_SOURCES": False}
    assert receipt["summary"]["files_loaded"] == 1
    assert any(m.get("content") == "read_receipt" for m in ws.sent)
