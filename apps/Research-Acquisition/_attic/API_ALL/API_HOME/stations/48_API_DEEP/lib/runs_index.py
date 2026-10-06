"""RUNS/48_API_DEEP/INDEX.html: one row per paper (its latest run), linking to each API_DEEP.html. Local, no API."""
from __future__ import annotations
import html, json
from pathlib import Path

FRUITS = ["love", "joy", "peace", "patience", "kindness", "goodness", "faithfulness", "gentleness", "self_control"]


def _load(p: Path):
    try: return json.loads(p.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError): return {}


def build(root: Path) -> Path:
    rows = []
    for paper in sorted(p for p in root.iterdir() if p.is_dir()):
        runs = sorted(r for r in paper.iterdir() if (r / "API_DEEP.html").exists())
        if not runs: continue
        run = runs[-1]; lt = _load(run / "love_truth.json"); pr = lt.get("profile") or {}
        co = (_load(run / "coherence.json").get("overall") or {}); me = _load(run / "master_equation.json"); fr = _load(run / "fruits.json")
        rc = _load(run / "API_DEEP.run.json"); net = pr.get("net_per_100") or {}
        rows.append({"name": paper.name, "href": f"{paper.name}/{run.name}/API_DEEP.html", "run": run.name,
                     "quadrant": pr.get("quadrant", "—"), "shape": ", ".join(x["name"] for x in pr.get("shapes_matched", [])) or "—",
                     "active": pr.get("active_share"), "net": [net.get(f, 0) for f in FRUITS], "coh": co.get("score"),
                     "me": me.get("analog_strength"), "verdict": fr.get("system_status", "—"), "tokens": rc.get("tokens_new", 0), "errors": len(rc.get("errors") or {})})
    def cell(v):
        c = "var(--g3)" if v >= 5 else "var(--g1)" if v > 0 else "var(--b3)" if v <= -5 else "var(--b1)" if v < 0 else "var(--mid)"
        return f'<span class="c" title="{v:+}" style="background:{c}"></span>'
    body = "".join(
        f'<tr><td><a href="{html.escape(r["href"])}">{html.escape(r["name"])}</a><div class="id">{r["run"]}</div></td>'
        f'<td>{html.escape(r["quadrant"])}</td><td>{html.escape(r["shape"])}</td>'
        f'<td class="n">{"" if r["active"] is None else f"{round(100 * r["active"])}%"}</td><td style="white-space:nowrap">{"".join(cell(v) for v in r["net"])}</td>'
        f'<td class="n">{r["coh"] if r["coh"] is not None else "—"}</td><td class="n">{r["me"] if r["me"] is not None else "—"}</td>'
        f'<td>{html.escape(str(r["verdict"]))}</td><td class="n">{r["tokens"]:,}</td><td class="n">{r["errors"] or ""}</td></tr>' for r in rows)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>API Deep index</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap" rel="stylesheet">
<style>
:root{{--plane:#f5f5f2;--surface:#fcfcfb;--ink:#0b0b0b;--muted:#6f6d67;--grid:#e1e0d9;--axis:#c3c2b7;--mid:#e4e3de;--g1:#86b6ef;--g3:#104281;--b1:#f0a39d;--b3:#a8292a;--link:#1c5cab}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--plane:#0f0f0e;--surface:#1a1a19;--ink:#fff;--muted:#9a988f;--grid:#2c2c2a;--axis:#383835;--mid:#383835;--g1:#1c5cab;--g3:#9ec5f4;--b1:#7d2a28;--b3:#f4aaa6;--link:#9ec5f4}}}}
:root[data-theme="dark"]{{--plane:#0f0f0e;--surface:#1a1a19;--ink:#fff;--muted:#9a988f;--grid:#2c2c2a;--axis:#383835;--mid:#383835;--g1:#1c5cab;--g3:#9ec5f4;--b1:#7d2a28;--b3:#f4aaa6;--link:#9ec5f4}}
body{{margin:0;background:var(--plane);color:var(--ink);font:14px/1.5 "IBM Plex Sans",system-ui,sans-serif}}.wrap{{max-width:1180px;margin:0 auto;padding:24px 16px}}
h1{{font-size:24px;margin:0 0 4px}}p{{color:var(--muted);margin:0 0 16px}}.scroll{{overflow-x:auto;background:var(--surface);border:1px solid var(--grid);border-radius:10px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th{{text-align:left;color:var(--muted);font-weight:500;border-bottom:1px solid var(--axis);padding:8px;white-space:nowrap}}
td{{border-bottom:1px solid var(--grid);padding:8px;vertical-align:top}}td.n{{text-align:right;font-variant-numeric:tabular-nums}}a{{color:var(--link);text-decoration:none}}a:hover{{text-decoration:underline}}
.id{{font:11px "IBM Plex Mono",monospace;color:var(--muted)}}.c{{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:2px}}
</style></head><body><div class="wrap"><h1>API Deep: every paper</h1>
<p>{len(rows)} papers, latest run each. Fruit squares in order love … self-control: blue = net toward the fruit, red = away, grey = none. "Engaged" = share of sentences that do anything a fruit can be scored on.</p>
<div class="scroll"><table><thead><tr><th>Paper</th><th>Love × Truth</th><th>Shape</th><th>Engaged</th><th>Nine fruits</th><th>Coherence</th><th>ME analog</th><th>Fruits verdict</th><th>Tokens</th><th>Errors</th></tr></thead>
<tbody>{body}</tbody></table></div></div></body></html>"""
    out = root / "INDEX.html"; out.write_text(page, encoding="utf-8"); return out
