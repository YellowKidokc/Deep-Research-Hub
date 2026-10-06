"""
youtube_processor.py — Per-transcript processor called by YOUTUBE.bat Option 5
Modes: question_match | framework_extract | full_brief | raw_summary

Usage (called by YOUTUBE.bat, or standalone):
    python youtube_processor.py --file transcript.txt --mode question_match --output ./out
    python youtube_processor.py --index ./out
"""

import json, os, sys, re, argparse
from pathlib import Path
from datetime import datetime

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    # Try user-level env var (Windows)
    try:
        import subprocess
        result = subprocess.run(['powershell', '-NoProfile', '-Command', "[Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')"], capture_output=True, text=True)
        DEEPSEEK_API_KEY = result.stdout.strip()
    except: pass
API_MODEL = "deepseek-chat"
API_URL = "https://api.deepseek.com/v1/chat/completions"
MAX_TRANSCRIPT_CHARS = 60000

DEBATE_QUESTIONS = {
    "Q-EVIL-LOGICAL": "Is God's existence logically incompatible with evil?",
    "Q-EVIL-EVIDENTIAL": "Does the amount or kind of suffering make God unlikely?",
    "Q-EVIL-REAL-GOOD": "If God is real, why do bad things happen to good people?",
    "Q-EVIL-REAL-CHILDREN": "Why would God let children die?",
    "Q-EVIL-REAL-HATE": "If God is love, why is there so much hate done in his name?",
    "Q-MORAL-OBJECTIVE": "Is morality objective or subjective?",
    "Q-MORAL-GOD": "Does objective morality require God?",
    "Q-MORAL-REAL-HELL": "Why would God send good people to hell?",
    "Q-MORAL-REAL-NEVERHEARD": "What about people who never heard of Jesus?",
    "Q-MORAL-REAL-PREDESTINATION": "Why create people he knew would go to hell?",
    "Q-REV-HIDDEN": "Why is God not more evident?",
    "Q-REV-REAL-SHOWUP": "Why doesn't God just show himself?",
    "Q-REV-REAL-WORSHIP": "Why does God need to be worshipped?",
    "Q-BIBLE-RELIABLE": "Are the biblical texts historically reliable?",
    "Q-BIBLE-CONTRADICTIONS": "Does the Bible contradict itself or science?",
    "Q-BIBLE-REAL-STORIES": "Isn't the Bible just stories written by men?",
    "Q-BIBLE-REAL-TRANSLATED": "Why trust a translated and edited book?",
    "Q-METHOD-REAL-SCIENCE": "How can you believe in God when science explains everything?",
    "Q-METHOD-REAL-FAITH": "Isn't faith just believing without evidence?",
    "Q-REL-REAL-EXCLUSIVE": "How can one religion be right?",
    "Q-EXIST-WHY": "Why does anything exist at all?",
    "Q-EXIST-REAL-INVENTED": "Didn't humans invent God?",
    "Q-BEGIN-CAUSE": "Does whatever begins need a cause?",
    "Q-FINE-EXPLANATION": "Is design better than chance or necessity?",
    "Q-LIFE-INFORMATION": "Does biological information require intelligence?",
    "Q-MIND-PHYSICAL": "Can consciousness be entirely physical?",
    "Q-MIND-IDENTITY": "What explains continuing identity?",
    "Q-AGENCY-RESPONSIBILITY": "Does moral responsibility require genuine choice?",
    "Q-REASON-EAAN": "Would unguided evolution give trustworthy reasoning?",
    "Q-JESUS-EXISTENCE": "Did Jesus exist historically?",
    "Q-JESUS-CLAIMS": "Did Jesus claim to be God?",
    "Q-JESUS-RESURRECTION": "Did Jesus rise from the dead?",
    "Q-XIAN-UNIQUE": "Is Christianity unique among religions?",
    "Q-PERSONAL-GOOD-ENOUGH": "I'm a good person. Why do I need Jesus?",
    "Q-PERSONAL-UNWORTHY": "I've done too much wrong.",
    "Q-PERSONAL-TRIED": "I tried Christianity and it didn't work.",
    "Q-PERSONAL-PRAYER": "I prayed and nothing happened.",
    "Q-PERSONAL-LOSS": "I lost someone. Where was God?",
    "Q-ORIGIN-INVENTED": "Didn't people just make up God?",
    "Q-ORIGIN-CONTROL": "Isn't religion just a tool to control people?",
    "Q-ORIGIN-FEAR": "Isn't God just a coping mechanism?",
    "Q-ORIGIN-CULTURE": "Born elsewhere, you'd believe differently.",
    "Q-CHURCH-HYPOCRISY": "Why is the church full of hypocrites?",
    "Q-CHURCH-HURT": "What about people hurt by the church?",
    "Q-CHURCH-HISTORY": "What about the Crusades, Inquisition, slavery?",
}

def call_claude(system_prompt, user_prompt, max_tokens=4000):
    import urllib.request
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    body = json.dumps({"model": API_MODEL, "max_tokens": max_tokens, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]}).encode()
    req = urllib.request.Request(API_URL, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]

def read_transcript(filepath):
    text = filepath.read_text(encoding="utf-8", errors="replace")
    if filepath.suffix in (".srt", ".vtt"):
        text = re.sub(r"^WEBVTT.*?\n\n", "", text, flags=re.DOTALL)
        text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"<[^>]+>", "", text)
    if filepath.suffix == ".json":
        try:
            data = json.loads(text)
            if isinstance(data, list): text = " ".join(item.get("text", str(item)) for item in data)
            elif isinstance(data, dict): text = data.get("text", data.get("transcript", json.dumps(data)))
        except: pass
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    if len(text) > MAX_TRANSCRIPT_CHARS: text = text[:MAX_TRANSCRIPT_CHARS] + "\n\n[TRUNCATED]"
    return text.strip()

def parse_json(raw):
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())
    return json.loads(raw)

def mode_question_match(transcript, filename):
    questions_block = "\n".join(f"- {qid}: {qtxt}" for qid, qtxt in DEBATE_QUESTIONS.items())
    system = "You are a research assistant analyzing YouTube transcripts for an apologetics project. Return ONLY valid JSON with no markdown fences."
    prompt = f"Transcript filename: {filename}\n\nTRANSCRIPT:\n{transcript}\n\nDEBATE MAP QUESTIONS:\n{questions_block}\n\nAnalyze this transcript and return a JSON object with:\n1. \"title\": inferred title\n2. \"speaker\": who is speaking\n3. \"channel\": channel name if identifiable\n4. \"side\": \"christian\" | \"skeptic\" | \"debate\" | \"neutral\"\n5. \"questions_addressed\": list of objects with \"question_id\", \"relevance\" (1-10), \"position\" (for/against/both), \"key_argument\" (one sentence), \"timestamp_hint\"\n6. \"new_arguments\": list of any arguments NOT in the debate map\n7. \"quotable_moments\": 2-3 short indexing phrases (under 10 words each)\n8. \"framework_connections\": list of any Theophysics-relevant concepts (entropy, coherence, conservation, information, noise, veto, etc.)"
    return parse_json(call_claude(system, prompt))

def mode_framework_extract(transcript, filename):
    system = "You are a research assistant for the Theophysics Research Initiative. Return ONLY valid JSON with no markdown fences."
    prompt = f"Transcript filename: {filename}\n\nTRANSCRIPT:\n{transcript}\n\nTHE_STORY CHAPTERS: 01_GOD_AS_ROOT through 20_SURVIVED_PRESSURE\n\nReturn JSON with: \"title\", \"speaker\", \"chapter_matches\" (list with chapter, claim, alignment, strength), \"physics_bridges\", \"novel_claims\", \"overall_usefulness\" (1-10)"
    return parse_json(call_claude(system, prompt))

def mode_full_brief(transcript, filename):
    system = "You are a senior research analyst for an apologetics and physics-theology project. Return ONLY valid JSON with no markdown fences."
    prompt = f"Transcript filename: {filename}\n\nTRANSCRIPT:\n{transcript}\n\nReturn JSON with: \"title\", \"speaker\", \"channel\", \"summary\" (3-4 sentences), \"side\", \"top_3_questions\" (debate map IDs), \"strongest_argument\" (2-3 sentences), \"weakest_point\", \"framework_relevance\" (THE_STORY chapters), \"steelman_counter\" (2-3 sentences), \"action_items\", \"tags\" (5-8 keywords)"
    return parse_json(call_claude(system, prompt))

def mode_raw_summary(transcript, filename):
    system = "You are a research assistant. Summarize YouTube transcripts concisely. Return ONLY valid JSON with no markdown fences."
    prompt = f"Transcript filename: {filename}\n\nTRANSCRIPT:\n{transcript}\n\nReturn JSON with: \"title\", \"speaker\", \"summary\" (4-6 sentences), \"key_claims\" (3-5 one-sentence claims), \"side\", \"tags\" (5-8 keywords)"
    return parse_json(call_claude(system, prompt))

MODE_MAP = {"question_match": mode_question_match, "framework_extract": mode_framework_extract, "full_brief": mode_full_brief, "raw_summary": mode_raw_summary}

def generate_index(outdir):
    results = []
    for jf in sorted(Path(outdir).glob("*.json")):
        if jf.name.startswith("__"): continue
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            results.append({"file": jf.name, "title": data.get("result", {}).get("title", "unknown"), "speaker": data.get("result", {}).get("speaker", "unknown"), "side": data.get("result", {}).get("side", "unknown"), "mode": data.get("mode", "unknown")})
        except: pass
    index = {"total_processed": len(results), "timestamp": datetime.utcnow().isoformat(), "files": results}
    idx_path = Path(outdir) / "__INDEX.json"
    idx_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return index

def main():
    parser = argparse.ArgumentParser(description="YouTube Transcript Processor")
    parser.add_argument("--file", type=str)
    parser.add_argument("--mode", type=str, choices=MODE_MAP.keys(), default="question_match")
    parser.add_argument("--output", type=str, default="./output")
    parser.add_argument("--index", type=str)
    args = parser.parse_args()
    if args.index:
        idx = generate_index(args.index)
        print(f"Index: {idx['total_processed']} files")
        return
    if not args.file: parser.print_help(); return
    filepath = Path(args.file)
    if not filepath.exists(): print(f"File not found: {filepath}", file=sys.stderr); sys.exit(1)
    outdir = Path(args.output); outdir.mkdir(parents=True, exist_ok=True)
    transcript = read_transcript(filepath)
    if not transcript: print(f"Empty transcript: {filepath}", file=sys.stderr); sys.exit(1)
    result = MODE_MAP[args.mode](transcript, filepath.name)
    output = {"source_file": str(filepath), "mode": args.mode, "timestamp": datetime.utcnow().isoformat(), "transcript_length": len(transcript), "result": result}
    out_path = outdir / (filepath.stem + f"__{args.mode}.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
