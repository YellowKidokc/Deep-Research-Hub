"""Put every analysis of a note ON the note itself (David, 2026-09-27: "all the analysis always goes on the original
transcripts"). One file to read: scorecard, analysis summary, the full reports, then the original transcript.

Between <!-- analysis:start --> and <!-- analysis:end --> (placed after the scorecard block, or after the title) it writes:
  - a summary callout: CKG score, finding, governing question, domain, weakest claim, build next, section scorecard,
    arguments (strength / originality), Fruits of Love and Truth
  - ## Analysis · Deep CKG            the full MASTER PAPER COMPANION (its YAML header and its copy of the source left out)
  - ## Analysis · Argument grades     every argument with its checks' outcome
  - ## Analysis · Fruits of Love and Truth
  - ## Analysis · YouTube CKG         the argument catalogue (its transcript left out)
Rerunning replaces the block; the rest of the note is untouched. The HTML report, which cannot live inside a note,
is copied beside it to _ANALYSIS/ and linked. No JSON goes into the vault.

Sources (latest run of each; a missing one is simply left out):
  deep CKG      D:\\GitHub\\pipeline-workflows\\API\\030_EVIDENCE\\OUTBOX\\BY_DOMAIN\\**\\<slug>_C1_*.md
  arguments     API_HOME\\RUNS\\49_ARGUMENT_GRADE\\<stem>\\<stamp>\\arguments.json
  API Deep      API_HOME\\RUNS\\48_API_DEEP\\<stem>\\<stamp>\\
  YouTube CKG   yt-transcript-downloader\\obsidian_indexed\\<channel>\\_API\\*.index.json matched by video_id

    python tools/publish_analysis.py <note.md or folder> [...] [--dry-run]
"""
from __future__ import annotations
import argparse, json, re, shutil, sys
from pathlib import Path

API_HOME = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = Path(r"D:\GitHub\pipeline-workflows\API\030_EVIDENCE")
YT_ROOT = Path(r"D:\GitHub\Research-Acquisition\yt-transcript-downloader")
START, END = "<!-- analysis:start -->", "<!-- analysis:end -->"


def latest(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern)) if folder.is_dir() else []
    return hits[-1] if hits else None


def load(p: Path | None):
    try: return json.loads(p.read_text(encoding="utf-8")) if p and p.exists() else None
    except (OSError, ValueError): return None


def yaml_field(text: str, key: str) -> str:
    m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', text, re.M)
    return m.group(1).strip() if m else ""


def find_companion(stem: str) -> Path | None:
    slug = re.sub(r"[^\w.-]+", "_", stem).strip("_")[:40]
    hits = [p for p in (EVIDENCE_ROOT / "OUTBOX" / "BY_DOMAIN").glob("*/*_C1_*.md") if p.name.startswith(slug)]
    complete = [p for p in hits if "## S10" in p.read_text(encoding="utf-8", errors="replace")]
    hits = complete or hits
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def find_youtube_note(channel: str, video_id: str) -> Path | None:
    api = YT_ROOT / "obsidian_indexed" / channel / "_API"
    if not (api.is_dir() and video_id): return None
    for j in api.glob("*.index.json"):
        meta = (load(j) or {}).get("_meta") or {}
        if meta.get("video_id") == video_id and meta.get("note"):
            return Path(meta["note"])
    return None


def companion_body(t: str) -> str:
    """The companion's analysis only: after its YAML block, before its own copy of the source."""
    parts = t.split("\n```\n", 1)
    t = parts[1] if len(parts) == 2 and len(parts[0]) < 30000 else t
    m = re.search(r"^#{1,4} Exact source", t, re.M)          # the companion's own copy of the source starts here
    if m: t = t[:m.start()]
    m = re.search(r"\n---\n(?:type|title|channel):", t)
    if m: t = t[:m.start()]
    m = re.search(r"^## Transcript\s*$", t, re.M)
    if m: t = t[:m.start()]
    if t.count("```") % 2: t += "\n```"                      # never leave a code block open inside the note
    return t.strip()


def youtube_body(t: str) -> str:
    """The YouTube CKG note without its front matter, title and transcript."""
    if t.startswith("---"):
        end = t.find("\n---", 3)
        t = t[end + 4:] if end > 0 else t
    t = re.sub(r"^# .*$", "", t, count=1, flags=re.M)
    m = re.search(r"^## Transcript\s*$", t, re.M)
    if m: t = t[:m.start()]
    return t.strip().rstrip("-").strip()


def demote(t: str) -> str:
    """One heading level down so each report sits under its '## Analysis · ...' heading (H1 becomes ###)."""
    return re.sub(r"^(#{1,5}) ", lambda m: "### " if len(m.group(1)) == 1 else "#" + m.group(1) + " ", t, flags=re.M)


def cell(x) -> str:
    return str(x if x is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def block(note: Path, text: str, out_dir: Path, dry: bool) -> tuple[str, list[str]]:
    stem = note.stem; found = []; L = []
    # a note renamed to its standard title keeps its old name in original_file; runs made before the rename use that
    stems = [stem] + ([Path(yaml_field(text, "original_file")).stem] if yaml_field(text, "original_file") else [])
    pick = lambda f: next((r for r in map(f, stems) if r), None)
    comp = pick(find_companion)
    run48 = pick(lambda s: latest(API_HOME / "RUNS" / "48_API_DEEP" / s, "*/love_truth.json"))
    run49 = pick(lambda s: latest(API_HOME / "RUNS" / "49_ARGUMENT_GRADE" / s, "*/arguments.json"))
    yt = find_youtube_note(yaml_field(text, "channel"), yaml_field(text, "video_id"))
    ctext = comp.read_text(encoding="utf-8", errors="replace") if comp else ""
    lt = load(run48); args = (load(run49) or {}).get("arguments") or []

    # ---- summary callout
    head = []
    if comp:
        found.append("deep CKG")
        head.append(f"CKG {yaml_field(ctext, 'score_total') or '?'}/100 ({yaml_field(ctext, 'score_class') or '?'}) · rating +{yaml_field(ctext, 'paper_rating') or '?'}")
    if lt:
        found.append("API Deep"); pr = lt.get("profile") or {}
        head.append(f"{pr.get('quadrant', '?')} · {' / '.join(x['name'] for x in pr.get('shapes_matched', [])) or 'no clear shape'}")
    if args: found.append("argument grades")
    L.append(f"> [!summary]+ Analysis · {' · '.join(head) or 'no analysis found yet'}")
    if comp:
        dom = f"{yaml_field(ctext, 'domain_primary')} {yaml_field(ctext, 'domain_primary_pct')}%"
        if yaml_field(ctext, "domain_secondary"): dom += f" · {yaml_field(ctext, 'domain_secondary')} {yaml_field(ctext, 'domain_secondary_pct')}%"
        L += [f"> **Finding:** {cell(yaml_field(ctext, 'one_sentence_finding'))}", ">",
              f"> **Governing question:** {cell(yaml_field(ctext, 'governing_question'))}", ">",
              f"> **Domain:** {cell(dom)} · **Evidence:** {yaml_field(ctext, 'evd_support') or '?'} for / {yaml_field(ctext, 'evd_counter') or '?'} against", ">",
              f"> **Weakest claim:** {cell(yaml_field(ctext, 'evd_weakest_claim'))}", ">",
              f"> **Build next:** {cell(yaml_field(ctext, 'build_next'))}", ">"]
        nets = [(f"S{i:02d}", yaml_field(ctext, f"s{i:02d}_net")) for i in range(1, 11)]
        if any(v for _, v in nets):
            L += ["> | " + " | ".join(s for s, _ in nets) + " |", "> |" + "---:|" * 10, "> | " + " | ".join(v or "—" for _, v in nets) + " |", ">"]
    if args:
        L.append("> **Arguments** (strength / originality, each 0–8):")
        for g in sorted(args, key=lambda g: -g["strength"]):
            L.append(f"> - **{cell(g['name'])}**: S {g['strength']} · O {g['originality']}" + (f" · {' '.join(g['case_map'])}" if g.get("case_map") else ""))
        L.append(">")
    if lt:
        pr = lt.get("profile") or {}; net = pr.get("net_per_100") or {}
        top = sorted(net, key=lambda f: -net[f])[:3]
        co = ((load(run48.parent / "coherence.json") or {}).get("overall") or {}).get("score")
        me = (load(run48.parent / "master_equation.json") or {}).get("analog_strength")
        L.append(f"> **Fruits of Love and Truth:** {cell(pr.get('quadrant'))} · leading " + ", ".join(f"{f.replace('_', ' ')} {net[f]:+}" for f in top)
                 + f" (net per 100 {pr.get('unit', 'sentences')}) · coherence {co if co is not None else '—'}/10 · master-equation analog {me if me is not None else '—'}/5")
    L.append("")

    # ---- the full reports, on the note
    if lt and (run48.parent / "API_DEEP.html").exists():
        dest = out_dir / f"{stem} — Fruits.html"          # HTML cannot live inside a note; it sits beside it
        if not dry: out_dir.mkdir(exist_ok=True); shutil.copy2(run48.parent / "API_DEEP.html", dest)
        L += [f"Interactive charts: [Fruits of Love and Truth report](<_ANALYSIS/{dest.name}>)", ""]
    if comp:
        L += ["## Analysis · Deep CKG (MASTER PAPER COMPANION)", "", demote(companion_body(ctext)), ""]
    if args:
        L += ["## Analysis · Argument grades", "",
              "Strength and originality are each 0–8, computed from yes / partly / no checks with quotes and averaged over two "
              "independent gradings. Machine ceiling 8; human review +1; Lean receipt +1.", "",
              "| Argument | Strength | Originality | Agreement | Case map | Weakest link | Develop next | Closest prior art |",
              "|---|---:|---:|---:|---|---|---|---|"]
        for g in sorted(args, key=lambda g: -g["strength"]):
            L.append(f"| **{cell(g['name'])}**: {cell(g.get('conclusion'))} | {g['strength']} | {g['originality']} | {g['agreement']} | "
                     f"{' '.join(g.get('case_map') or [])} | {cell(g.get('weakest_link'))} | {cell(g.get('develop_next'))} | {cell(g.get('prior_art'))} |")
        L.append("")
    if lt:
        pr = lt.get("profile") or {}; net = pr.get("net_per_100") or {}; te = lt.get("truth_engine") or {}
        L += ["## Analysis · Fruits of Love and Truth", "",
              f"**{cell(pr.get('quadrant'))}** · shape: {' / '.join(x['name'] for x in pr.get('shapes_matched', [])) or 'none'} · "
              f"love axis {pr.get('love_axis')} · truth axis {pr.get('truth_axis')} · scored from {pr.get('sentences')} {pr.get('unit', 'sentences')}", "",
              "| " + " | ".join(f.replace("_", " ") for f in net) + " |", "|" + "---:|" * len(net),
              "| " + " | ".join(f"{v:+}" for v in net.values()) + " |", "",
              f"Truth Engine: TRUTH {te.get('truth_score_raw')} · per 100 words " +
              ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in (te.get("per_100_words") or {}).items()), ""]
    if yt and yt.exists():
        found.append("YouTube CKG")
        L += ["## Analysis · YouTube CKG (argument catalogue)", "", demote(youtube_body(yt.read_text(encoding="utf-8", errors="replace"))), ""]
    return "\n".join([START, *L, END]), found


def publish(note: Path, dry: bool) -> str:
    text = note.read_text(encoding="utf-8")
    new_block, found = block(note, text, note.parent / "_ANALYSIS", dry)
    if START in text and END in text:
        out = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: new_block, text, count=1, flags=re.S)
    elif "<!-- scorecard:end -->" in text:
        out = text.replace("<!-- scorecard:end -->", "<!-- scorecard:end -->\n\n" + new_block, 1)
    else:
        m = re.search(r"^# .*$", text, re.M)
        out = text[:m.end()] + "\n\n" + new_block + text[m.end():] if m else new_block + "\n\n" + text
    if not dry and out != text: note.write_text(out, encoding="utf-8")
    return f"{'plan' if dry else 'done'}  {note.name}: {', '.join(found) or 'nothing found'} ({len(out.split()):,} words)"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("items", nargs="+"); p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    notes = []
    for raw in a.items:
        x = Path(raw)
        notes += sorted(n for n in x.glob("*.md") if not n.name.startswith("_") and " - 000 " not in n.name) if x.is_dir() else [x]
    for n in notes: print(publish(n, a.dry_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
