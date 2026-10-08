"""Run one API Layer slot against a file, or every new file in a folder.

    python prompts/run_slot.py Y 1 --file "data/youtube/<Channel>/<Title>.md" --append
    python prompts/run_slot.py Y 1 --dir data/youtube --since 1791323565 --append
    python prompts/run_slot.py Y 1 --file x.md --dry-run

The slot (prompts/<SET>_*.json) defines the provider, model, key variable and
prompt parts; nothing about the call is written in this file. Standard library
only. Each call leaves its exact request in data/api/requests/ and one line in
data/api/log.jsonl.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

PROMPTS = pathlib.Path(__file__).resolve().parent
ROOT = PROMPTS.parent
API_DATA = ROOT / "data" / "api"
# Folders ytgrab and its cleaner create beside the raw transcripts.
SKIP_DIRS = {"Clean MD", "Channel Summary", "Prompts", "_archive"}


def load_slot(set_letter, n):
    found = sorted(PROMPTS.glob(f"{set_letter}_*.json"))
    if len(found) != 1:
        sys.exit(f"expected one prompts/{set_letter}_*.json, found {len(found)}")
    slot = json.loads(found[0].read_text(encoding="utf-8"))["slots"].get(str(n))
    if not slot:
        sys.exit(f"slot {set_letter}/{n} is empty")
    slot["_ref"] = f"{set_letter}/{n}"
    return slot


def read_part(name, strip):
    text = (PROMPTS / name).read_text(encoding="utf-8")
    if strip:
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return text.strip()


def meta(text, path):
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), path.stem)
    vid = re.search(r"\*\*Video ID:\*\*\s*`([^`]+)`", text)
    return {"title": title, "video_id": vid.group(1) if vid else "not provided"}


def build(slot, text, path):
    p = slot["prompt"]
    m = meta(text, path)
    parts = []
    for part in p["parts"]:
        if "file" in part:
            parts.append(read_part(part["file"], p.get("strip_comments")))
        else:
            parts.append(part["input"].format(text=text, **m))
    return p.get("join", "\n\n").join(s for s in parts if s)


def skip_reason(slot, text):
    heading = slot.get("output", {}).get("append_heading")
    if heading and re.search(rf"^{re.escape(heading)}\s*$", text, re.M):
        return "already has " + heading
    rules = slot.get("skip_if") or {}
    for s in rules.get("contains", []):
        if s in text:
            return f"contains {s!r}"
    words = len(text.split("## Transcript", 1)[-1].split())
    if words < rules.get("min_words", 0):
        return f"{words} words, under {rules['min_words']}"
    return None


def call(slot, prompt, base_url=None):
    prov = slot["provider"]
    key = os.environ.get(prov["key_env"], "")
    if not key:
        raise RuntimeError(f"{prov['key_env']} is not set")
    url = (base_url or prov["base_url"]).rstrip("/") + "/chat/completions"
    body = {"model": prov["model"], "temperature": slot.get("temperature", 0.3),
            "messages": [{"role": "user", "content": prompt}]}
    if slot.get("max_tokens"):
        body["max_tokens"] = slot["max_tokens"]
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read()[:300].decode(errors='replace')}") from None
    usage = data.get("usage") or {}
    return data["choices"][0]["message"]["content"], usage


def demote(md):
    """The reply's own headings sit one level under the appended heading."""
    return re.sub(r"^(#{1,5}) ", r"#\1 ", md, flags=re.M)


def run_file(slot, path, args):
    text = path.read_text(encoding="utf-8")
    why = skip_reason(slot, text)
    if why:
        print(f"  skip  {path.name}: {why}")
        return "skipped"
    prompt = build(slot, text, path)
    stamp = dt.datetime.now()
    rid = f"{stamp:%Y%m%d-%H%M%S}_{slot['id']}_{re.sub(r'[^A-Za-z0-9]+', '-', path.stem)[:50]}"
    (API_DATA / "requests").mkdir(parents=True, exist_ok=True)
    (API_DATA / "requests" / f"{rid}.md").write_text(prompt, encoding="utf-8")
    if args.dry_run:
        print(f"  dry   {path.name}: {len(prompt.split())} words -> data/api/requests/{rid}.md")
        return "dry"
    try:
        reply, usage = call(slot, prompt, args.base_url)
    except Exception as e:
        print(f"  FAIL  {path.name}: {e}")
        return "failed"
    prov = slot["provider"]
    t_in, t_out = usage.get("prompt_tokens"), usage.get("completion_tokens")
    with open(API_DATA / "log.jsonl", "a", encoding="utf-8") as log:
        log.write(json.dumps({"id": rid, "time": stamp.isoformat(timespec="seconds"),
                              "slot": slot["_ref"], "slot_id": slot["id"], "model": prov["model"],
                              "file": str(path), "tokens_in": t_in, "tokens_out": t_out}) + "\n")
    heading = slot.get("output", {}).get("append_heading")
    if args.append and heading:
        block = (f"\n\n{heading}\n\n"
                 f"*{prov['model']} · slot {slot['_ref']} `{slot['id']}` · "
                 f"{stamp:%Y-%m-%d %H:%M} · tokens in {t_in}, out {t_out} · "
                 f"request `data/api/requests/{rid}.md`*\n\n{demote(reply.strip())}\n")
        with open(path, "a", encoding="utf-8") as f:
            f.write(block)
        print(f"  ok    {path.name}: appended {heading}")
    else:
        print(reply)
    return "ok"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("set", help="slot set letter, e.g. Y")
    ap.add_argument("slot", help="slot number 1-10")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", action="append", help="input file (repeatable)")
    src.add_argument("--dir", help="every .md under this folder")
    ap.add_argument("--since", type=float, default=0, help="with --dir: only files modified at or after this unix time")
    ap.add_argument("--append", action="store_true", help="append the reply under the slot's heading")
    ap.add_argument("--dry-run", action="store_true", help="build and save the request, no API call")
    ap.add_argument("--base-url", help="override the provider URL (testing)")
    args = ap.parse_args()

    slot = load_slot(args.set, args.slot)
    if args.file:
        files = [pathlib.Path(f) for f in args.file]
    else:
        files = sorted(p for p in pathlib.Path(args.dir).rglob("*.md")
                       if not SKIP_DIRS.intersection(p.relative_to(args.dir).parts[:-1])
                       and p.stat().st_mtime >= args.since)
    print(f"slot {slot['_ref']} {slot['id']}: {len(files)} file(s)")
    counts = {}
    for f in files:
        r = run_file(slot, f, args)
        counts[r] = counts.get(r, 0) + 1
    print("done: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) if counts else "done: nothing to do")
    sys.exit(1 if counts.get("failed") else 0)


if __name__ == "__main__":
    main()
