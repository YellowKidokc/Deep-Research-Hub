"""scripts/dossier.py with a scripted model (no network). Standard library only:

    python -m unittest scripts/test_dossier.py
"""
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dossier as D  # noqa: E402

NOTES = """# My notes on privatio boni

Augustine of Hippo, writing in the Confessions (c. 397), described evil as nothing but the privation of good.
Mackie objected that pain is a positive reality, not an absence.

A boy in Carthage stole pears he did not want, and Augustine spent a chapter asking why.
"""
TRANSCRIPT = """Thomas Aquinas, in the Summa Theologiae (1265-1274), held that evil is a privation of a due good.
Augustine of Hippo, writing in the Confessions (c. 397), described evil as nothing but the privation of good.
The weather in Hippo was warm that year, according to one blog.
"""


class Model:
    """Plays slot D/1 (pills) and D/2 (sort); records what it was asked."""

    def __init__(self):
        self.calls = []

    def __call__(self, slot, prompt):
        payload = json.loads(prompt.split("# INPUT\n", 1)[1])
        self.calls.append((slot["id"], payload))
        if slot["id"] == "pills":
            chunk = payload["chunk"]
            pills = []
            for line in chunk.splitlines():
                line = line.strip()
                if len(line) > 40 and not line.startswith("#"):
                    kind = "objection" if "objected" in line else "story" if "pears" in line else "claim"
                    pills.append({"kind": kind, "text": line[:60], "quote": line,
                                  "who": "Augustine of Hippo" if "Augustine" in line else None,
                                  "when": "c. 397" if "397" in line else None})
            pills.append({"kind": "claim", "text": "invented", "quote": "Plotinus coined privatio boni in 250 AD."})
            return json.dumps({"pills": pills}), {"prompt_tokens": 10, "completion_tokens": 5}
        if slot["id"] == "sort":
            placed, cut = [], []
            for p in payload["pills"]:
                if "weather" in p["text"]:
                    cut.append({"pill": p["id"], "reason": "off_topic", "of": None, "note": "not about the idea"})
                elif "Aquinas" in p["text"]:
                    continue                                   # left out on purpose -> unsorted
                elif p["kind"] == "objection":
                    placed.append({"pill": p["id"], "section": "against", "rank": 1})
                elif p["kind"] == "story":
                    placed.append({"pill": p["id"], "section": "stories", "rank": 1})
                else:
                    placed.append({"pill": p["id"], "section": "origin", "rank": 1})
            placed.append({"pill": "nope-1", "section": "origin", "rank": 1})   # not in the batch: ignored
            return json.dumps({"placed": placed, "cut": cut,
                               "notes": {"origin": "Augustine only; no hop before him."}}), {}
        raise AssertionError(slot["id"])


class DossierTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.old = (D.DOSSIERS, D.API_LOG, D.CALL)
        D.DOSSIERS = root / "dossiers"
        D.API_LOG = root / "api" / "log.jsonl"
        self.model = Model()
        D.CALL = self.model
        self.files = root / "src"
        self.files.mkdir()
        (self.files / "notes.md").write_text(NOTES, encoding="utf-8")
        (self.files / "talk.txt").write_text(TRANSCRIPT, encoding="utf-8")
        (self.files / "pic.png").write_bytes(b"\x89PNG")

    def tearDown(self):
        D.DOSSIERS, D.API_LOG, D.CALL = self.old
        self.tmp.cleanup()

    def cli(self, *argv):
        sys.argv = ["dossier.py", *argv]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            D.main()
        return out.getvalue()

    def make(self):
        self.cli("new", "pb", "--topic", "privatio boni")
        self.cli("add", "pb", str(self.files / "notes.md"), str(self.files / "talk.txt"), str(self.files / "pic.png"))
        self.cli("add", "pb", "--text", "Pasted: the privation view says evil has no being of its own at all.",
                 "--title", "From the call")
        return D.DOSSIERS / "pb"

    def test_dump_sort_and_account_for_every_pill(self):
        d = self.make()
        self.assertEqual(len(list((d / "inbox").iterdir())), 4)         # 3 files + 1 paste
        self.cli("run", "pb")
        led = json.loads((d / "ledger.json").read_text(encoding="utf-8"))
        c = led["counts"]
        self.assertEqual(c["sources"], 3)                          # png skipped, not read
        self.assertEqual(led["skipped"], [{"source": "inbox/pic.png", "reason": ".png is not .md / .txt / .json"}])
        self.assertEqual(c["pills"], c["placed"] + c["cut"] + c["unsorted"])   # nothing vanishes
        states = {p["text"][:20]: (p["state"], p.get("section"), p.get("reason")) for p in led["pills"]}
        self.assertEqual(states["Mackie objected that"][:2], ("placed", "against"))
        self.assertEqual(states["A boy in Carthage st"][:2], ("placed", "stories"))
        self.assertEqual(states["The weather in Hippo"][::2], ("cut", "off_topic"))
        self.assertEqual(states["Thomas Aquinas, in t"][0], "unsorted")
        # the Augustine line is in two sources: the second copy is cut as a duplicate before sorting
        aug = [p for p in led["pills"] if p["text"].startswith("Augustine of Hippo")]
        self.assertEqual(sorted(p["state"] for p in aug), ["cut", "placed"])
        dup = next(p for p in aug if p["state"] == "cut")
        self.assertEqual((dup["reason"], dup["by"]), ("duplicate", "dedupe"))
        self.assertEqual(dup["of"], next(p for p in aug if p["state"] == "placed")["id"])
        # the invented quote never becomes a pill
        self.assertEqual(c["quotes_not_verbatim"], 3)
        self.assertNotIn("invented", json.dumps(led["pills"]))
        # every pill's quote is the source's own text at its offsets
        notes = (d / "inbox" / "notes.md").read_text(encoding="utf-8")
        p = next(p for p in led["pills"] if p["source"] == "inbox/notes.md")
        self.assertEqual(notes[p["start"]:p["end"]], p["quote"])

        self.assertEqual(p["title"], "My notes on privatio boni")              # the file's own heading
        talk = next(p for p in led["pills"] if p["source"] == "inbox/talk.txt")
        self.assertEqual(talk["title"], "talk")                                 # no heading: the file name
        md = (d / "dossier.md").read_text(encoding="utf-8")
        self.assertIn("## Origin and history (", md)
        self.assertIn("*Augustine only; no hop before him.*", md)
        self.assertIn("## Unsorted (1)", md)
        cuts = (d / "cuts.md").read_text(encoding="utf-8")
        self.assertIn("## duplicate (1)", cuts)
        self.assertIn("## off topic (1)", cuts)
        self.assertIn("## Not verbatim (3)", cuts)
        st = json.loads((d / "status.json").read_text(encoding="utf-8"))
        self.assertEqual(st["state"], "done")
        self.assertTrue(list((d / "runs").glob("*/dossier.md")))
        self.assertTrue(D.API_LOG.read_text(encoding="utf-8").count("dossier:pills") == 3)

    def test_rerun_only_reads_new_sources(self):
        d = self.make()
        self.cli("run", "pb")
        first = [k for k, _ in self.model.calls].count("pills")
        self.model.calls.clear()
        self.cli("add", "pb", "--text", "New: Plotinus treated matter as the privation of form, long before Augustine.")
        self.cli("run", "pb")
        self.assertEqual(first, 3)
        self.assertEqual([k for k, _ in self.model.calls].count("pills"), 1)   # only the new paste
        led = json.loads((d / "ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(led["counts"]["sources"], 4)

    def test_links_and_saved_workflow(self):
        d = self.make()
        linked = self.files / "run"
        linked.mkdir()
        (linked / "facts.md").write_text("Augustine of Hippo, writing in the Confessions (c. 397), described evil as nothing but the privation of good.\n", encoding="utf-8")
        (linked / "_skip.md").write_text("ignored file that starts with an underscore character", encoding="utf-8")
        self.cli("add", "pb", "--link", str(linked))
        meta = json.loads((d / "dossier.json").read_text(encoding="utf-8"))
        self.assertEqual(len(meta["links"]), 1)
        self.cli("run", "pb")
        led = json.loads((d / "ledger.json").read_text(encoding="utf-8"))
        self.assertIn(meta["links"][0] + "/facts.md", [s["source"] for s in led["sources"]])
        self.assertEqual(led["workflow"], "default")
        sort_call = next(p for k, p in self.model.calls if k == "sort")
        self.assertEqual([s["id"] for s in sort_call["sections"]][:3], ["core", "origin", "people"])

    def test_empty_dump_fails_with_status(self):
        self.cli("new", "empty")
        with self.assertRaises(RuntimeError):
            self.cli("run", "empty")
        st = json.loads((D.DOSSIERS / "empty" / "status.json").read_text(encoding="utf-8"))
        self.assertEqual(st["state"], "failed")
        self.assertIn("empty", st["error"])

    def test_bad_names_refused(self):
        for bad in ("../x", "a/b", "", "x" * 81):
            with self.assertRaises(SystemExit):
                D.dossier_dir(bad)


if __name__ == "__main__":
    unittest.main()
