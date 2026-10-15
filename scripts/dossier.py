"""Dossier: dump everything on a topic into one place, then sort it. Not a paper.

    python scripts/dossier.py new  <name> --topic "privatio boni" [--workflow default]
    python scripts/dossier.py add  <name> notes.md transcript.md        # copy files into the dump
    python scripts/dossier.py add  <name> --text "pasted text" --title "from the call"
    python scripts/dossier.py add  <name> --link data/deep_research/devil/20261007-100342
    python scripts/dossier.py run  <name>
    python scripts/dossier.py list

A dossier is a folder, data/writer/dossiers/<name>/:
    dossier.json    name, topic, workflow, linked paths
    inbox/          the dump: .md / .txt / .json files (copied or pasted in)
    pills/          one file per source, keyed by its content hash: the pills it was
                    broken into (slot D/1), each tied to a verbatim quote. Cached, so a
                    re-run only reads sources that are new or changed.
    runs/<stamp>/   one run: sort replies, ledger, dossier.md, cuts.md
    dossier.md      the latest sort: pills by section, strongest first
    cuts.md         what was cut and why (duplicate of X, weaker version of X, off topic...)
    ledger.json     every pill and where it went: placed, cut or unsorted
    status.json     the run in progress or the last one (stage, counts, error)

The sections come from a saved workflow, prompts/D_dossier/workflows/<id>.json.
Model calls are slots D/1 (pills) and D/2 (sort) in prompts/D_dossier.json.
Standard library only. Nothing is deleted: every pill ends placed, cut with a
reason, or listed as unsorted.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys
import time
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
sys.path.insert(0, str(PROMPTS))
import run_slot  # noqa: E402  (slot loading and the OpenAI-compatible call)

DOSSIERS = ROOT / "data" / "writer" / "dossiers"
API_LOG = ROOT / "data" / "api" / "log.jsonl"
WORKFLOWS = PROMPTS / "D_dossier" / "workflows"
NAME = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
TEXT_EXT = {".md", ".txt", ".json"}
KINDS = {"claim", "argument", "objection", "evidence", "statistic", "quote", "story", "weird_fact",
         "definition", "date", "person", "question"}
CUT_REASONS = {"duplicate", "off_topic", "weaker_version", "unsupported", "trivial"}


def CALL(slot: dict, prompt: str) -> tuple[str, dict]:
    """One model call. Tests replace this. DRH_API_BASE_URL points every slot at
    another OpenAI-compatible host (a proxy, a local model) without editing the slot."""
    return run_slot.call(slot, prompt, os.environ.get("DRH_API_BASE_URL") or None)


# ------------------------------------------------------------------ helpers
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-",
                         "—": "-", " ": " ", "…": "..."})


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    out, idx, prev_space = [], [], True
    for i, ch in enumerate(unicodedata.normalize("NFC", text)):
        for c in ch.translate(_QUOTES):
            if c.isspace():
                if prev_space:
                    continue
                c, prev_space = " ", True
            else:
                prev_space = False
            out.append(c)
            idx.append(i)
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def locate(quote: str, norm: tuple[str, list[int]]) -> tuple[int, int] | None:
    ntext, idx = norm
    nq = normalize_with_map(quote)[0].strip()
    if len(nq) < 12:
        return None
    pos = ntext.find(nq)
    if pos < 0:
        pos = ntext.lower().find(nq.lower())
    return None if pos < 0 else (idx[pos], idx[pos + len(nq) - 1] + 1)


def parse_json(text: str):
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        s, e = t.find("{"), t.rfind("}")
        if s >= 0 and e > s:
            try:
                return json.loads(t[s:e + 1])
            except json.JSONDecodeError:
                pass
    return {}


def chunks(text: str, size: int) -> list[tuple[int, str]]:
    """(offset, chunk) pieces of about `size` chars, cut at paragraph breaks where possible."""
    out, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            cut = text.rfind("\n\n", start + size // 2, end)
            if cut > start:
                end = cut
        out.append((start, text[start:end]))
        start = end
    return out


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def dossier_dir(name: str) -> pathlib.Path:
    if not NAME.match(name):
        raise SystemExit(f"bad dossier name {name!r}: letters, digits, _ . - only")
    return DOSSIERS / name


def read_json(p: pathlib.Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(p: pathlib.Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_workflow(wid: str) -> dict:
    wf = read_json(WORKFLOWS / f"{wid}.json")
    if not wf or not wf.get("sections"):
        raise SystemExit(f"workflow {wid!r} not found or has no sections in {WORKFLOWS}")
    return wf


def log_call(slot: dict, stage: str, label: str, usage: dict) -> None:
    API_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(API_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": now(), "slot": slot.get("_ref"), "model": slot["provider"]["model"],
                            "file": f"dossier:{stage}:{label}", "tokens_in": usage.get("prompt_tokens"),
                            "tokens_out": usage.get("completion_tokens")}, ensure_ascii=False) + "\n")


def ask(slot_n: int, stage: str, label: str, payload: dict) -> dict:
    slot = run_slot.load_slot("D", slot_n)
    p = slot["prompt"]
    parts = [run_slot.read_part(x["file"], p.get("strip_comments")) for x in p["parts"] if "file" in x]
    prompt = p.get("join", "\n\n").join(parts) + "\n\n---\n\n# INPUT\n" + json.dumps(payload, ensure_ascii=False)
    text, usage = CALL(slot, prompt)
    log_call(slot, stage, label, usage or {})
    got = parse_json(text)
    return got if isinstance(got, dict) else {}


# ------------------------------------------------------------------ sources
def gather(d: pathlib.Path, meta: dict) -> tuple[list[dict], list[dict]]:
    """Inbox files and linked paths -> [{label, path, text, hash}], plus what was skipped."""
    files: list[tuple[str, pathlib.Path]] = []
    for p in sorted((d / "inbox").glob("*")):
        files.append((f"inbox/{p.name}", p))
    for link in meta.get("links", []):
        p = (ROOT / link) if not pathlib.Path(link).is_absolute() else pathlib.Path(link)
        if p.is_dir():
            files += [(f"{link}/{q.name}", q) for q in sorted(p.glob("*.md")) if not q.name.startswith("_")]
        else:
            files.append((link, p))
    sources, skipped = [], []
    for label, p in files:
        if not p.is_file():
            skipped.append({"source": label, "reason": "not found"})
            continue
        if p.suffix.lower() not in TEXT_EXT:
            skipped.append({"source": label, "reason": f"{p.suffix or 'no extension'} is not .md / .txt / .json"})
            continue
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        if p.suffix.lower() == ".json":
            try:
                text = json.dumps(json.loads(text), indent=1, ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        if not text.strip():
            skipped.append({"source": label, "reason": "empty"})
            continue
        head = next((l[2:].strip() for l in text.splitlines()[:5] if l.startswith("# ")), "")
        title = head or re.sub(r"^\d{8}-\d{6}-", "", p.stem)
        sources.append({"label": label, "title": title, "path": str(p), "text": text,
                        "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()})
    return sources, skipped


def pill_source(d: pathlib.Path, src: dict, topic: str, chunk_chars: int, status) -> dict:
    """The source's pills, from the cache or by calling slot D/1 on each chunk."""
    cache = d / "pills" / f"{src['hash'][:16]}.json"
    got = read_json(cache)
    if got:
        got["label"] = src["label"]
        return {**got, "cached": True}
    norm = normalize_with_map(src["text"])
    pills, rejected = [], []
    pieces = chunks(src["text"], chunk_chars)
    for n, (off, chunk) in enumerate(pieces, 1):
        status(f"pills {src['label']} ({n}/{len(pieces)})")
        reply = ask(1, "pills", src["label"], {"topic": topic, "source": src["label"], "chunk": chunk})
        for p in reply.get("pills", []) if isinstance(reply.get("pills"), list) else []:
            if not isinstance(p, dict) or not str(p.get("text", "")).strip():
                continue
            span = locate(str(p.get("quote", "")), norm)
            if not span:
                rejected.append({"text": p.get("text"), "quote": p.get("quote"), "reason": "quote not found verbatim in the source"})
                continue
            kind = str(p.get("kind", "claim")).strip().lower()
            pills.append({"kind": kind if kind in KINDS else "claim", "text": str(p["text"]).strip(),
                          "quote": src["text"][span[0]:span[1]], "start": span[0], "end": span[1],
                          "who": p.get("who") or None, "when": p.get("when") or None})
    # same span twice (overlapping chunks or a repeated reply) is one pill
    seen, uniq = set(), []
    for p in sorted(pills, key=lambda p: p["start"]):
        if (p["start"], p["end"]) not in seen:
            seen.add((p["start"], p["end"]))
            uniq.append(p)
    for k, p in enumerate(uniq, 1):
        p["id"] = f"{src['hash'][:6]}-{k}"
    out = {"label": src["label"], "hash": src["hash"], "made": now(), "pills": uniq, "rejected": rejected}
    write_json(cache, out)
    return {**out, "cached": False}


# --------------------------------------------------------------------- run
def run(name: str) -> dict:
    d = dossier_dir(name)
    meta = read_json(d / "dossier.json")
    if not meta:
        raise SystemExit(f"no dossier {name!r}; make it with: dossier.py new {name} --topic ...")
    wf = load_workflow(meta.get("workflow", "default"))
    sections = {s["id"]: s for s in wf["sections"]}
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    rd = d / "runs" / stamp
    rd.mkdir(parents=True, exist_ok=True)
    st = {"run": stamp, "state": "running", "stage": "gather", "started": now()}

    def status(stage: str, **extra):
        st.update(stage=stage, **extra)
        write_json(d / "status.json", st)
        print(f"  {stage}", flush=True)

    try:
        status("gather")
        sources, skipped = gather(d, meta)
        if not sources:
            raise RuntimeError("the dump is empty: add files, text or links first")
        all_pills, rejected, by_source = [], [], []
        for src in sources:
            got = pill_source(d, src, meta.get("topic", name), int(wf.get("chunk_chars", 12000)), status)
            for p in got["pills"]:
                all_pills.append({**p, "source": src["label"], "title": src["title"]})
            rejected += [{**r, "source": src["label"]} for r in got.get("rejected", [])]
            by_source.append({"source": src["label"], "pills": len(got["pills"]), "rejected": len(got.get("rejected", [])),
                              "cached": got["cached"]})

        # exact duplicates across sources (same words) never reach the model twice
        ledger: dict[str, dict] = {}
        first: dict[str, str] = {}
        to_sort = []
        for p in all_pills:
            key = normalize_with_map(p["quote"])[0].lower()
            if key in first:
                ledger[p["id"]] = {"state": "cut", "reason": "duplicate", "of": first[key], "by": "dedupe",
                                   "note": "same words as the pill it duplicates"}
            else:
                first[key] = p["id"]
                to_sort.append(p)

        notes: dict[str, list[str]] = {}
        size = int(wf.get("sort_batch", 120))
        batches = [to_sort[i:i + size] for i in range(0, len(to_sort), size)]
        for n, batch in enumerate(batches, 1):
            status(f"sort ({n}/{len(batches)})", pills=len(all_pills))
            ids = {p["id"] for p in batch}
            reply = ask(2, "sort", f"{name} batch {n}", {
                "topic": meta.get("topic", name),
                "sections": [{"id": s["id"], "label": s["label"], "holds": s.get("holds", "")} for s in wf["sections"]],
                "pills": [{k: p.get(k) for k in ("id", "kind", "text", "who", "when", "source")} for p in batch]})
            write_json(rd / f"sort_{n}.json", reply)
            for x in reply.get("placed", []) if isinstance(reply.get("placed"), list) else []:
                pid, sec = (x or {}).get("pill"), (x or {}).get("section")
                if pid in ids and pid not in ledger and sec in sections:
                    rank = x.get("rank")
                    ledger[pid] = {"state": "placed", "section": sec, "rank": rank if isinstance(rank, int) else 999}
            for x in reply.get("cut", []) if isinstance(reply.get("cut"), list) else []:
                pid = (x or {}).get("pill")
                if pid in ids and pid not in ledger:
                    reason = x.get("reason") if x.get("reason") in CUT_REASONS else "unsupported"
                    ledger[pid] = {"state": "cut", "reason": reason, "of": x.get("of") or None, "by": "model",
                                   "note": str(x.get("note") or "")}
            for sec, note in (reply.get("notes") or {}).items() if isinstance(reply.get("notes"), dict) else []:
                if sec in sections and note:
                    notes.setdefault(sec, []).append(str(note))
        for p in all_pills:
            ledger.setdefault(p["id"], {"state": "unsorted", "note": "the sort returned nothing for this pill"})

        counts = {s: sum(1 for v in ledger.values() if v["state"] == s) for s in ("placed", "cut", "unsorted")}
        doc = {"name": name, "topic": meta.get("topic", name), "workflow": wf["id"], "run": stamp, "made": now(),
               "counts": {"sources": len(sources), "pills": len(all_pills), **counts,
                          "quotes_not_verbatim": len(rejected)},
               "sections": [{"id": s["id"], "label": s["label"], "notes": notes.get(s["id"], [])} for s in wf["sections"]],
               "pills": [{**p, **ledger[p["id"]]} for p in all_pills],
               "sources": by_source, "skipped": skipped, "rejected_pills": rejected}
        write_json(rd / "ledger.json", doc)
        (rd / "dossier.md").write_text(render_dossier(doc), encoding="utf-8")
        (rd / "cuts.md").write_text(render_cuts(doc), encoding="utf-8")
        for f in ("ledger.json", "dossier.md", "cuts.md"):
            shutil.copyfile(rd / f, d / f)
        st.update(state="done", stage="done", ended=now(), counts=doc["counts"])
        write_json(d / "status.json", st)
        return doc
    except Exception as e:
        st.update(state="failed", error=f"{type(e).__name__}: {e}", ended=now())
        write_json(d / "status.json", st)
        raise


def _line(p: dict) -> list[str]:
    meta = " · ".join(str(x) for x in (p.get("who"), p.get("when")) if x)
    q = p["quote"] if len(p["quote"]) < 500 else p["quote"][:500] + "…"
    return [f"- **{p['text']}**" + (f" — {meta}" if meta else "") + f" `{p['id']}` *{p['kind']}*",
            f"  > “{q}” — {p.get('title') or p['source']} ({p['source']})"]


def render_dossier(doc: dict) -> str:
    c = doc["counts"]
    out = [f"# Dossier: {doc['topic']}", "",
           f"Workflow `{doc['workflow']}` · run {doc['run']} · {c['sources']} sources · {c['pills']} pills: "
           f"{c['placed']} placed, {c['cut']} cut (see cuts.md), {c['unsorted']} unsorted.", ""]
    for s in doc["sections"]:
        here = sorted((p for p in doc["pills"] if p["state"] == "placed" and p.get("section") == s["id"]),
                      key=lambda p: p.get("rank", 999))
        out += [f"## {s['label']} ({len(here)})", ""]
        out += [f"*{n}*" for n in s["notes"]] + ([""] if s["notes"] else [])
        for p in here:
            out += _line(p)
        out.append("")
    uns = [p for p in doc["pills"] if p["state"] == "unsorted"]
    if uns:
        out += [f"## Unsorted ({len(uns)})", ""]
        for p in uns:
            out += _line(p)
    return "\n".join(out) + "\n"


def render_cuts(doc: dict) -> str:
    cut = [p for p in doc["pills"] if p["state"] == "cut"]
    out = [f"# Cut from the dossier: {doc['topic']}", "", f"{len(cut)} pills cut in run {doc['run']}. Nothing is deleted; "
           "each line says why, and which pill it lost to.", ""]
    for reason in sorted({p["reason"] for p in cut}):
        group = [p for p in cut if p["reason"] == reason]
        out += [f"## {reason.replace('_', ' ')} ({len(group)})", ""]
        for p in group:
            out += _line(p)
            extra = " · ".join(x for x in (f"lost to `{p['of']}`" if p.get("of") else "", p.get("note") or "") if x)
            if extra:
                out.append(f"  - {extra}")
        out.append("")
    if doc["rejected_pills"]:
        out += [f"## Not verbatim ({len(doc['rejected_pills'])})", "",
                "Pills the model proposed whose quote is not in the source; never sorted.", ""]
        out += [f"- {r.get('text')} — {r['source']}" for r in doc["rejected_pills"]]
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------- CLI
def cmd_new(a):
    d = dossier_dir(a.name)
    if (d / "dossier.json").exists():
        raise SystemExit(f"{a.name} already exists")
    load_workflow(a.workflow)
    (d / "inbox").mkdir(parents=True, exist_ok=True)
    write_json(d / "dossier.json", {"name": a.name, "topic": a.topic or a.name, "workflow": a.workflow,
                                    "created": now(), "links": []})
    print(f"made {d}")


def cmd_add(a):
    d = dossier_dir(a.name)
    meta = read_json(d / "dossier.json")
    if not meta:
        raise SystemExit(f"no dossier {a.name!r}")
    inbox = d / "inbox"
    inbox.mkdir(exist_ok=True)
    added = []
    for f in a.files:
        src = pathlib.Path(f)
        if not src.is_file():
            raise SystemExit(f"not a file: {f}")
        dest = inbox / src.name
        k = 2
        while dest.exists():
            dest = inbox / f"{src.stem}-{k}{src.suffix}"
            k += 1
        shutil.copyfile(src, dest)
        added.append(dest.name)
    if a.text:
        stem = re.sub(r"[^A-Za-z0-9]+", "-", (a.title or "pasted").lower()).strip("-")[:40] or "pasted"
        dest = inbox / f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{stem}.md"
        dest.write_text((f"# {a.title}\n\n" if a.title else "") + a.text.strip() + "\n", encoding="utf-8")
        added.append(dest.name)
    for link in a.link:
        p = pathlib.Path(link).resolve()
        if not p.exists():
            raise SystemExit(f"not found: {link}")
        rel = p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)
        if rel not in meta["links"]:
            meta["links"].append(rel)
            added.append(f"link {rel}")
    write_json(d / "dossier.json", meta)
    print("added: " + (", ".join(added) or "nothing"))


def cmd_run(a):
    print(f"[dossier] {a.name}", flush=True)
    doc = run(a.name)
    c = doc["counts"]
    print(f"[done] {c['sources']} sources, {c['pills']} pills: {c['placed']} placed, {c['cut']} cut, "
          f"{c['unsorted']} unsorted -> {dossier_dir(a.name) / 'dossier.md'}", flush=True)


def cmd_list(_a):
    for d in sorted(DOSSIERS.glob("*/dossier.json")) if DOSSIERS.is_dir() else []:
        meta = read_json(d) or {}
        st = read_json(d.parent / "status.json") or {}
        print(f"{d.parent.name:<30} {st.get('state', 'not run'):<8} {meta.get('topic', '')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new")
    p.add_argument("name")
    p.add_argument("--topic", default="")
    p.add_argument("--workflow", default="default")
    p.set_defaults(fn=cmd_new)
    p = sub.add_parser("add")
    p.add_argument("name")
    p.add_argument("files", nargs="*")
    p.add_argument("--text", default="")
    p.add_argument("--title", default="")
    p.add_argument("--link", action="append", default=[])
    p.set_defaults(fn=cmd_add)
    p = sub.add_parser("run")
    p.add_argument("name")
    p.set_defaults(fn=cmd_run)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
