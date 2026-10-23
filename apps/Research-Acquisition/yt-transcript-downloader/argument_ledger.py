#!/usr/bin/env python3
"""
argument_ledger.py

Increment 1 of the Argument Whiteboard: pull every structured argument out of
the indexed YouTube notes (obsidian_indexed/<Channel>/_API/*.index.json),
score each one for airtightness, and emit:

  argument_ledger.json   canonical data (one entry per argument)
  argument_ledger.csv    spreadsheet view
  whiteboard.html        self-contained visual board (no server needed)

Airtightness v0 (transparent, tunable - see WEIGHTS):
  structure  has premises, inferences, a conclusion, evidence steps
  dispute    share of steps flagged disputed_by (the leaks)
  grounding  timestamps present (resolvable against the v2 transcripts)
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

OBSIDIAN_INDEXED = Path("//192.168.2.50/h_hp/Desktop/Youtube API CKG/obsidian_indexed")
OUT_DIR = Path("//192.168.2.50/h_hp/Desktop/Youtube API CKG/_ARGUMENTS")
MARKDOWN_V2 = Path(r"D:\GitHub\Research-Acquisition\yt-transcript-downloader\markdown_v2")

# The objection map recovered from the Oct 8 debate-map session (17 open items).
# status: "build" = needs building, "candidate" = discussed, not hardened.
OBJECTIONS = [
    ("Bible", "Isn't it just stories written by men?", "build", "Already called self-defeating"),
    ("Bible", "Why trust a book translated and edited for thousands of years?", "build", ""),
    ("Method", "How can you believe in God when science explains everything?", "build", "Rated winnable"),
    ("Moral", "People who never heard of Jesus", "build", "Hardest — can't land before the listener holds God's character"),
    ("Moral", "If God knows everything, why create people he knew would go to hell?", "build", ""),
    ("Revelation", "Why does God need to be worshipped?", "build", ""),
    ("Religions", "How can one religion be right and everyone else wrong?", "build", ""),
    ("Church", "The church is full of hypocrites", "build", ""),
    ("Church", "People hurt by the church", "build", ""),
    ("Church", "Grew up around Christians, they're no different", "build", ""),
    ("Church", "Crusades, Inquisition, slavery", "build", ""),
    ("Personal", "I tried Christianity and it didn't work", "build", ""),
    ("Personal", "I prayed and nothing happened", "build", ""),
    ("Origin", "Religion is a tool to control people", "build", ""),
    ("Psychology", "Humans invented God to explain what they didn't understand", "candidate", ""),
    ("Psychology", "God is a coping mechanism for fear of death", "candidate", ""),
    ("Psychology", "Born somewhere else, you'd believe something else", "candidate", ""),
]

WEIGHTS = {"evidence_step": 4, "max_evidence": 16, "three_steps": 10,
           "has_conclusion": 10, "grounded": 10, "dispute_penalty": 45}


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", t.lower())


def grade(score: float) -> str:
    if score >= 75:
        return "A"
    if score >= 55:
        return "B"
    if score >= 35:
        return "C"
    return "D"


def build_transcript_index() -> dict:
    """normalized video title -> markdown_v2 relative path, best effort."""
    idx = {}
    if not MARKDOWN_V2.is_dir():
        return idx
    for f in MARKDOWN_V2.rglob("*.md"):
        m = re.match(r"^(.+?) - Chapter \d+ - (.+)$", f.stem)
        if m:
            idx[norm(m.group(2))] = f"{f.parent.name}/{f.name}"
    return idx


def score_argument(arg: dict) -> tuple[float, dict]:
    steps = arg.get("steps", [])
    n = len(steps)
    roles = [s.get("role", "") for s in steps]
    disputed = [s for s in steps if s.get("disputed_by")]
    evidence = sum(1 for r in roles if r == "evidence")

    parts = {
        "evidence": min(evidence * WEIGHTS["evidence_step"], WEIGHTS["max_evidence"]),
        "structure": (WEIGHTS["three_steps"] if n >= 3 else 0)
                     + (WEIGHTS["has_conclusion"] if "conclusion" in roles else 0),
        "grounded": WEIGHTS["grounded"] if arg.get("timestamps") else 0,
        "dispute": -WEIGHTS["dispute_penalty"] * (len(disputed) / n if n else 0),
    }
    return max(0.0, 40.0 + sum(parts.values())), parts


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    transcripts = build_transcript_index()

    ledger = []
    for jf in sorted(OBSIDIAN_INDEXED.rglob("*.index.json")):
        channel = jf.parent.parent.name
        video = jf.name[: -len(".index.json")]
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"FAIL {jf}: {e}", file=sys.stderr)
            continue
        for arg in data.get("arguments", []):
            steps = arg.get("steps", [])
            disputed = [s for s in steps if s.get("disputed_by")]
            score, parts = score_argument(arg)
            ledger.append({
                "argument": arg.get("name", "(unnamed)"),
                "family": arg.get("family", ""),
                "stance": arg.get("stance", ""),
                "speaker": arg.get("speaker", ""),
                "channel": channel,
                "video": video,
                "timestamps": arg.get("timestamps", []),
                "steps": steps,
                "n_steps": len(steps),
                "n_disputed": len(disputed),
                "leaks": [{"step": s.get("n"), "claim": s.get("claim", "")[:200],
                           "disputed_by": s.get("disputed_by", "")} for s in disputed],
                "score": round(score, 1),
                "grade": grade(score),
                "score_parts": parts,
                "transcript": transcripts.get(norm(video), ""),
            })

    ledger.sort(key=lambda r: -r["score"])
    (OUT_DIR / "argument_ledger.json").write_text(
        json.dumps(ledger, indent=1, ensure_ascii=False), encoding="utf-8")

    with open(OUT_DIR / "argument_ledger.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["grade", "score", "argument", "family", "stance", "speaker",
                    "channel", "video", "steps", "disputed", "timestamps"])
        for r in ledger:
            w.writerow([r["grade"], r["score"], r["argument"], r["family"],
                        r["stance"], r["speaker"], r["channel"], r["video"],
                        r["n_steps"], r["n_disputed"], ";".join(r["timestamps"])])

    write_whiteboard(ledger)

    by_grade = {}
    for r in ledger:
        by_grade[r["grade"]] = by_grade.get(r["grade"], 0) + 1
    print(f"{len(ledger)} arguments from {len(list(OBSIDIAN_INDEXED.rglob(chr(42)+'.index.json')))} videos")
    print("grades:", by_grade)
    print(f"-> {OUT_DIR}")


def write_whiteboard(ledger: list) -> None:
    def esc(t):
        return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    cards = []
    for r in ledger:
        cls = {"A": "a", "B": "b", "C": "c", "D": "d"}[r["grade"]]
        steps_html = ""
        for s in r["steps"]:
            leak = " leak" if s.get("disputed_by") else ""
            disp = f' &mdash; <span class="disp">disputed by {esc(s["disputed_by"])}</span>' if s.get("disputed_by") else ""
            steps_html += (f'<li class="{s.get("role","")}{leak}"><b>{s.get("n")}.</b> '
                           f'<i>{esc(s.get("role",""))}</i>: {esc(s.get("claim",""))}{disp}</li>')
        ts = " ".join(f"<code>{esc(t)}</code>" for t in r["timestamps"])
        cards.append(f"""
<div class="card {cls}">
 <div class="hd"><span class="grade">{r['grade']}</span> <span class="score">{r['score']}</span>
  <span class="stance {esc(r['stance'])}">{esc(r['stance'])}</span></div>
 <h3>{esc(r['argument'])}</h3>
 <div class="meta">{esc(r['speaker'])} &middot; {esc(r['family'])} &middot;
  <b>{esc(r['channel'])}</b> — {esc(r['video'])}</div>
 <div class="ts">{ts}</div>
 <ol>{steps_html}</ol>
</div>""")

    total = len(ledger)
    counts = {g: sum(1 for r in ledger if r["grade"] == g) for g in "ABCD"}
    weak = [r for r in ledger if r["n_disputed"] > 0]
    strong = [r for r in ledger if r["grade"] == "A"]

    obj_rows = ""
    for cat, text, status, note in OBJECTIONS:
        badge = ("<span class='bstat build'>NEEDS BUILDING</span>" if status == "build"
                 else "<span class='bstat cand'>CANDIDATE</span>")
        n = f" <span class='onote'>— {esc(note)}</span>" if note else ""
        obj_rows += f"<tr><td>{esc(cat)}</td><td>{esc(text)}{n}</td><td>{badge}</td></tr>\n"
    n_build = sum(1 for o in OBJECTIONS if o[2] == "build")
    n_cand = sum(1 for o in OBJECTIONS if o[2] == "candidate")
    objection_html = f"""
<div class="summary">
<h2>The objection map — {len(OBJECTIONS)} open items ({n_build} to build, {n_cand} candidates)</h2>
<p>Recovered from the Oct 8 debate-map session. Airtight = every argument
graded AND every row below carrying a hardened answer.</p>
<table class="objs">
<tr><th>Category</th><th>Objection</th><th>Status</th></tr>
{obj_rows}</table>
</div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Argument Whiteboard</title>
<style>
body {{ background:#111; color:#ddd; font-family:Georgia,serif; margin:2em; }}
h1 {{ color:#eee; }} .stats span {{ margin-right:1.5em; }}
.card {{ background:#1c1c1e; border-left:6px solid #555; border-radius:6px;
        padding:1em 1.2em; margin:1em 0; }}
.card.a {{ border-color:#3fa34d; }} .card.b {{ border-color:#d4a017; }}
.card.c {{ border-color:#cc5500; }} .card.d {{ border-color:#b03030; }}
.grade {{ font-size:1.6em; font-weight:bold; }}
.card.a .grade {{ color:#3fa34d; }} .card.b .grade {{ color:#d4a017; }}
.card.c .grade {{ color:#cc5500; }} .card.d .grade {{ color:#b03030; }}
.score {{ color:#888; }} .stance {{ float:right; font-size:.85em; color:#9cf; }}
.stance.against-christianity {{ color:#f99; }}
h3 {{ margin:.3em 0; color:#eee; }}
.meta {{ color:#999; font-size:.9em; }} .ts {{ margin:.3em 0; }}
code {{ background:#2a2a2e; padding:0 .3em; border-radius:3px; }}
ol {{ margin:.5em 0 0; }} li {{ margin:.25em 0; }}
li.leak {{ color:#f0b0a0; }} .disp {{ color:#e07070; font-size:.85em; }}
li i {{ color:#7ab; }}
.summary {{ background:#1c1c1e; border-radius:6px; padding:1em 1.2em; margin:1em 0; }}
table.objs {{ border-collapse:collapse; width:100%; }}
table.objs td, table.objs th {{ border-bottom:1px solid #333; padding:.4em .6em;
                               text-align:left; vertical-align:top; }}
table.objs th {{ color:#9cf; }}
.bstat {{ font-size:.8em; padding:.1em .5em; border-radius:3px; white-space:nowrap; }}
.bstat.build {{ background:#5a2020; color:#f0a090; }}
.bstat.cand {{ background:#4a4020; color:#e0c070; }}
.onote {{ color:#998; font-size:.85em; }}
</style></head><body>
<h1>Argument Whiteboard — the case, as it stands</h1>
<div class="stats">
<span><b>{total}</b> arguments</span>
<span style="color:#3fa34d">A: {counts['A']}</span>
<span style="color:#d4a017">B: {counts['B']}</span>
<span style="color:#cc5500">C: {counts['C']}</span>
<span style="color:#b03030">D: {counts['D']}</span>
<span><b>{len(weak)}</b> with known leaks</span>
</div>
{objection_html}
<div class="summary">
<h2>Where the case is strong</h2>
<p>{len(strong)} A-grade arguments — the load-bearing walls.</p>
<h2>Where it leaks</h2>
<p>{len(weak)} arguments have at least one disputed step. Those are the
work items: each leak names who disputes it and which step.</p>
</div>
{''.join(cards)}
</body></html>"""
    (OUT_DIR / "whiteboard.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
