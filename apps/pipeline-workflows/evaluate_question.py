"""
evaluate_question.py — Apologetics Question Evaluator
Pipeline: question ID → restatement + variants + argument clusters + steelman + framework match + resource stack
Drop into: D:\GitHub\pipeline-workflows\API\_ACTIONS\

Usage:
    python evaluate_question.py Q-EVIL-LOGICAL
    python evaluate_question.py --all                 # run all 80+
    python evaluate_question.py --batch S-EVIL        # run one section
"""

import json, os, sys, re, argparse
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIG — adjust paths and keys to your environment
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-sonnet-4-6"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

OUTPUT_DIR = Path("./output/question_briefs")
DEBATE_MAP_PATH = Path("./debate_map.md")  # your debate map markdown

# Chapter → Lean theorem lookup (extend as theorems compile)
CHAPTER_LEAN_MAP = {
    "01_GOD_AS_ROOT": {"theorem": "axiom_removal_collapses_all", "status": "CANDIDATE"},
    "02_TRUTH_BEFORE_ARGUMENT": {"theorem": "truth_presupposed_by_denial", "status": "CANDIDATE"},
    "03_I_AM": {"theorem": "self_reference_fixed_point", "status": "CANDIDATE"},
    "04_FOUR_DEBTS": {"theorem": "debt_non_cancellation", "status": "CANDIDATE"},
    "05_TRINITY_AND_TRUTH": {"theorem": "three_persons_minimal_complete", "status": "CANDIDATE"},
    "06_LOGOS_WORD_INFORMATION": {"theorem": "semantic_content_requires_source", "status": "CANDIDATE"},
    "07_CREATION_ORDERED_GIFT": {"theorem": "order_precedes_observer", "status": "CANDIDATE"},
    "08_SCIENCE_AS_WITNESS": {"theorem": "independent_convergence_boost", "status": "CANDIDATE"},
    "09_CONSCIOUSNESS_AS_WITNESS": {"theorem": "goedel_meta_requires_exterior", "status": "CANDIDATE"},
    "10_FREEDOM_TRUST_SPACE": {"theorem": "deterministic_system_cannot_generate_choice", "status": "CANDIDATE"},
    "11_FALL_DAMAGED_RECEIVER": {"theorem": "noise_injection_monotone_capacity_loss", "status": "CANDIDATE"},
    "12_EVIL_VANDALIZES": {"theorem": "anti_lagrangian_zero_sum", "status": "COMPILED"},
    "13_COST_JUSTICE_MERCY": {"theorem": "ledger_no_free_closure", "status": "COMPILED"},
    "14_GRACE_EXTERNAL_REPAIR": {"theorem": "five_impossibilities_force_external", "status": "COMPILED"},
    "15_CHRIST_ENTERS_COST": {"theorem": "judge_as_payer_unique", "status": "COMPILED"},
    "16_REDEMPTION_WITHOUT_ERASURE": {"theorem": "landauer_redemption_preserves_record", "status": "CANDIDATE"},
    "17_RESURRECTION_IDENTITY": {"theorem": "identity_preserved_under_transformation", "status": "CANDIDATE"},
    "18_FRUITS_RESTORED_LIFE": {"theorem": "nine_invariants_from_confinement", "status": "CANDIDATE"},
    "19_FRUITS_COUNTERFEITS": {"theorem": "counterfeit_structural_test", "status": "CANDIDATE"},
    "20_SURVIVED_PRESSURE": {"theorem": "perturbation_stability_of_coherence", "status": "CANDIDATE"},
}

# Question → Chapter mapping (extend as coverage grows)
QUESTION_CHAPTER_MAP = {
    "Q-EVIL-LOGICAL": ["12_EVIL_VANDALIZES", "10_FREEDOM_TRUST_SPACE"],
    "Q-EVIL-EVIDENTIAL": ["12_EVIL_VANDALIZES", "13_COST_JUSTICE_MERCY"],
    "Q-EVIL-REAL-GOOD": ["12_EVIL_VANDALIZES", "13_COST_JUSTICE_MERCY"],
    "Q-EVIL-REAL-CHILDREN": ["12_EVIL_VANDALIZES", "13_COST_JUSTICE_MERCY"],
    "Q-EVIL-REAL-HATE": ["12_EVIL_VANDALIZES", "19_FRUITS_COUNTERFEITS"],
    "Q-MORAL-OBJECTIVE": ["02_TRUTH_BEFORE_ARGUMENT", "13_COST_JUSTICE_MERCY"],
    "Q-MORAL-GOD": ["01_GOD_AS_ROOT", "13_COST_JUSTICE_MERCY"],
    "Q-MORAL-REAL-HELL": ["13_COST_JUSTICE_MERCY", "09_CONSCIOUSNESS_AS_WITNESS"],
    "Q-MORAL-REAL-NEVERHEARD": [],  # GAP
    "Q-MORAL-REAL-PREDESTINATION": ["10_FREEDOM_TRUST_SPACE"],
    "Q-REV-HIDDEN": ["06_LOGOS_WORD_INFORMATION", "11_FALL_DAMAGED_RECEIVER"],
    "Q-REV-REAL-SHOWUP": ["07_CREATION_ORDERED_GIFT", "10_FREEDOM_TRUST_SPACE"],
    "Q-REV-REAL-WORSHIP": [],  # GAP
    "Q-BIBLE-CONTRADICTIONS": ["02_TRUTH_BEFORE_ARGUMENT"],
    "Q-BIBLE-REAL-STORIES": ["08_SCIENCE_AS_WITNESS", "17_RESURRECTION_IDENTITY"],
    "Q-BIBLE-REAL-TRANSLATED": [],  # needs building
    "Q-METHOD-REAL-SCIENCE": ["08_SCIENCE_AS_WITNESS", "06_LOGOS_WORD_INFORMATION"],
    "Q-METHOD-REAL-FAITH": ["07_CREATION_ORDERED_GIFT", "08_SCIENCE_AS_WITNESS"],
    "Q-EXIST-WHY": ["01_GOD_AS_ROOT", "07_CREATION_ORDERED_GIFT"],
    "Q-EXIST-BRUTE": ["01_GOD_AS_ROOT", "02_TRUTH_BEFORE_ARGUMENT"],
    "Q-EXIST-REAL-INVENTED": ["01_GOD_AS_ROOT", "08_SCIENCE_AS_WITNESS"],
    "Q-BEGIN-CAUSE": ["01_GOD_AS_ROOT", "07_CREATION_ORDERED_GIFT"],
    "Q-FINE-EXPLANATION": ["07_CREATION_ORDERED_GIFT", "08_SCIENCE_AS_WITNESS"],
    "Q-FINE-MULTIVERSE": ["07_CREATION_ORDERED_GIFT"],
    "Q-LIFE-INFORMATION": ["06_LOGOS_WORD_INFORMATION"],
    "Q-MIND-PHYSICAL": ["09_CONSCIOUSNESS_AS_WITNESS"],
    "Q-MIND-IDENTITY": ["17_RESURRECTION_IDENTITY"],
    "Q-AGENCY-RESPONSIBILITY": ["10_FREEDOM_TRUST_SPACE"],
    "Q-REASON-EAAN": ["09_CONSCIOUSNESS_AS_WITNESS", "06_LOGOS_WORD_INFORMATION"],
    "Q-JESUS-EXISTENCE": ["17_RESURRECTION_IDENTITY"],
    "Q-JESUS-RESURRECTION": ["17_RESURRECTION_IDENTITY", "15_CHRIST_ENTERS_COST"],
    "Q-JESUS-CLAIMS": ["03_I_AM", "15_CHRIST_ENTERS_COST"],
    "Q-XIAN-UNIQUE": ["14_GRACE_EXTERNAL_REPAIR", "15_CHRIST_ENTERS_COST"],
    "Q-PERSONAL-GOOD-ENOUGH": ["13_COST_JUSTICE_MERCY", "11_FALL_DAMAGED_RECEIVER"],
    "Q-PERSONAL-UNWORTHY": ["14_GRACE_EXTERNAL_REPAIR", "16_REDEMPTION_WITHOUT_ERASURE"],
    "Q-PERSONAL-LOSS": ["12_EVIL_VANDALIZES", "13_COST_JUSTICE_MERCY"],
    "Q-PERSONAL-TRIED": ["18_FRUITS_RESTORED_LIFE", "20_SURVIVED_PRESSURE"],
    "Q-PERSONAL-PRAYER": [],  # GAP
    "Q-ORIGIN-INVENTED": ["01_GOD_AS_ROOT", "08_SCIENCE_AS_WITNESS"],
    "Q-ORIGIN-CONTROL": [],  # GAP
    "Q-ORIGIN-FEAR": ["09_CONSCIOUSNESS_AS_WITNESS"],
    "Q-ORIGIN-CULTURE": ["08_SCIENCE_AS_WITNESS"],
    "Q-CHURCH-HYPOCRISY": ["19_FRUITS_COUNTERFEITS"],
    "Q-CHURCH-HURT": ["19_FRUITS_COUNTERFEITS", "12_EVIL_VANDALIZES"],
    "Q-CHURCH-HISTORY": ["12_EVIL_VANDALIZES", "19_FRUITS_COUNTERFEITS"],
    "Q-REL-REAL-EXCLUSIVE": ["02_TRUTH_BEFORE_ARGUMENT", "03_I_AM"],
}


# ---------------------------------------------------------------------------
# API CALLER
# ---------------------------------------------------------------------------
def call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
    """Call Anthropic API. Returns text response."""
    import urllib.request

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    body = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }).encode()

    req = urllib.request.Request(ANTHROPIC_URL, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())

    return "".join(
        block["text"] for block in data.get("content", []) if block.get("type") == "text"
    )


# ---------------------------------------------------------------------------
# STAGE 1: RESTATE + GENERATE SEARCH VARIANTS
# ---------------------------------------------------------------------------
def generate_variants(question_id: str, question_text: str) -> dict:
    """Restate the question in plain language and generate 10-15 search variants."""
    system = (
        "You are a research assistant helping build an apologetics question database. "
        "Return ONLY valid JSON with no markdown fences."
    )
    prompt = f"""Question ID: {question_id}
Question: {question_text}

Return a JSON object with these keys:
1. "real_question": Restate this the way a real person asks it — raw, emotional, unacademic. One or two sentences.
2. "expanded": A 2-3 sentence expansion of what's really being asked underneath the surface question.
3. "search_variants": A list of 12-15 different phrasings someone might use to ask this same question. Include:
   - The casual/conversational version ("why does God let bad stuff happen")
   - The angry version ("if God is real he's either evil or useless")
   - The intellectual version ("the evidential problem of evil")
   - The churched version ("how do we reconcile suffering with sovereignty")
   - The search-engine version ("problem of evil best arguments")
   - The YouTube comment version
   - The late-night-doubt version
   - Fragment versions people might type: "evil god why" or "suffering no god"
4. "corpus_search_terms": A list of 8-10 keyword phrases optimized for searching a local document corpus (Obsidian vault, markdown files, HTML papers). These should catch the way David Lowe writes about this topic — framework language, not academic language. Include terms like "entropy," "veto," "damaged receiver," "noise floor," "moral conservation," "anti-Lagrangian" etc. where they apply.
"""
    raw = call_claude(system, prompt)
    # Strip markdown fences if present
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())
    return json.loads(raw)


# ---------------------------------------------------------------------------
# STAGE 2: ARGUMENT CLUSTERS + STEELMAN
# ---------------------------------------------------------------------------
def build_argument_clusters(question_id: str, question_text: str, real_question: str) -> dict:
    """Identify argument clusters, steelman the best skeptic argument, build the brief."""
    system = (
        "You are an expert in philosophy of religion, apologetics, and theology. "
        "You give BOTH sides full strength. Return ONLY valid JSON with no markdown fences."
    )
    prompt = f"""Question ID: {question_id}
Academic form: {question_text}
Real form: {real_question}

Return a JSON object with these keys:
1. "argument_clusters": A list of objects, each with:
   - "name": short label for this line of reasoning
   - "side": "against" or "for" (against Christianity or for)
   - "summary": 2-3 sentence summary of the argument
   - "best_advocate": who makes this argument best (name + work if known)
   - "strength": 1-10 rating of how strong this argument is at its best

2. "best_shot_against": An object with:
   - "argument": The single strongest skeptic/atheist argument on this question, stated as well as its best advocate would state it. 4-6 sentences. Full strength, no straw.
   - "advocate": Who makes it best
   - "why_it_hits": One sentence on why this argument lands with real people

3. "best_shot_for": An object with:
   - "argument": The single strongest Christian/theist argument on this question. 4-6 sentences. Full strength.
   - "advocate": Who makes it best

4. "cluster_count": How many distinct lines of reasoning exist on this question total (both sides)

5. "difficulty_rating": 1-10, how hard is this question for Christianity? 10 = genuinely threatening to the position.
"""
    raw = call_claude(system, prompt)
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())
    return json.loads(raw)


# ---------------------------------------------------------------------------
# STAGE 3: FRAMEWORK MATCH (local lookup, no API needed)
# ---------------------------------------------------------------------------
def framework_match(question_id: str) -> dict:
    """Map question to THE_STORY chapters and Lean theorems."""
    chapters = QUESTION_CHAPTER_MAP.get(question_id, [])

    if not chapters:
        return {
            "chapters": [],
            "lean_theorems": [],
            "coverage_status": "GAP",
            "gap_flag": True,
        }

    lean_entries = []
    statuses = []
    for ch in chapters:
        entry = CHAPTER_LEAN_MAP.get(ch)
        if entry:
            lean_entries.append({
                "chapter": ch,
                "theorem": entry["theorem"],
                "status": entry["status"],
            })
            statuses.append(entry["status"])

    if "COMPILED" in statuses:
        coverage = "FORMALLY_VERIFIED"
    elif "CANDIDATE" in statuses:
        coverage = "BRIDGE_CANDIDATE"
    else:
        coverage = "MAPPED_NO_THEOREM"

    return {
        "chapters": chapters,
        "lean_theorems": lean_entries,
        "coverage_status": coverage,
        "gap_flag": False,
    }


# ---------------------------------------------------------------------------
# STAGE 4: RESOURCE STACK (web search via API with tool use)
# ---------------------------------------------------------------------------
def build_resource_stack(question_id: str, question_text: str, real_question: str) -> dict:
    """Find the best resources — videos, debates, articles — for both sides."""
    system = (
        "You are a research librarian specializing in apologetics and philosophy of religion. "
        "Return ONLY valid JSON with no markdown fences. "
        "For YouTube videos, provide real video titles and channel names you are confident exist. "
        "If you are not confident a specific video exists, say so in a 'confidence' field."
    )
    prompt = f"""Question ID: {question_id}
Question: {question_text}
Real version: {real_question}

Return a JSON object with:
1. "youtube_videos": list of 4-6 objects, each with:
   - "title": video title
   - "channel": channel name
   - "side": "for" | "against" | "balanced"
   - "level": "pastoral" | "popular" | "academic"
   - "confidence": "high" | "medium" — how sure you are this video exists
   - "search_query": a YouTube search string that would find this or similar content

2. "best_debate": object with:
   - "title": debate title
   - "participants": list of names
   - "search_query": YouTube/web search to find it

3. "written_sources": list of 3-4 objects, each with:
   - "title": article/book/paper title
   - "author": author name
   - "side": "for" | "against"
   - "type": "book" | "article" | "paper" | "blog"

4. "recommended_order": list of 3 resource titles — what to read/watch FIRST if you only have 30 minutes
"""
    raw = call_claude(system, prompt)
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())
    return json.loads(raw)


# ---------------------------------------------------------------------------
# ASSEMBLER — full brief per question
# ---------------------------------------------------------------------------
def evaluate_question(question_id: str, question_text: str) -> dict:
    """Run the full pipeline for one question."""
    print(f"\n{'='*60}")
    print(f"  Processing: {question_id}")
    print(f"  {question_text}")
    print(f"{'='*60}")

    # Stage 1
    print("  [1/4] Generating variants and search terms...")
    variants = generate_variants(question_id, question_text)

    # Stage 2
    print("  [2/4] Building argument clusters...")
    arguments = build_argument_clusters(
        question_id, question_text, variants.get("real_question", question_text)
    )

    # Stage 3
    print("  [3/4] Matching to framework...")
    framework = framework_match(question_id)

    # Stage 4
    print("  [4/4] Building resource stack...")
    resources = build_resource_stack(
        question_id, question_text, variants.get("real_question", question_text)
    )

    # Assemble
    brief = {
        "question_id": question_id,
        "question_text": question_text,
        "timestamp": datetime.utcnow().isoformat(),
        "variants": variants,
        "arguments": arguments,
        "framework": framework,
        "resources": resources,
    }

    return brief


# ---------------------------------------------------------------------------
# DEBATE MAP PARSER
# ---------------------------------------------------------------------------
def parse_debate_map(path: Path) -> dict:
    """Parse the debate map markdown into {question_id: question_text}."""
    questions = {}
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        m = re.match(r"^-\s+`(Q-[A-Z0-9_-]+)`\s+(.+)$", line.strip())
        if m:
            questions[m.group(1)] = m.group(2).strip()
    return questions


# ---------------------------------------------------------------------------
# MARKDOWN BRIEF RENDERER
# ---------------------------------------------------------------------------
def render_markdown(brief: dict) -> str:
    """Render a single question brief as readable markdown."""
    v = brief["variants"]
    a = brief["arguments"]
    f = brief["framework"]
    r = brief["resources"]

    lines = []
    lines.append(f"# {brief['question_id']}")
    lines.append(f"**Academic:** {brief['question_text']}")
    lines.append(f"**Real:** {v.get('real_question', 'N/A')}")
    lines.append(f"**Expanded:** {v.get('expanded', 'N/A')}")
    lines.append("")

    # Search variants
    lines.append("## Search Variants (for corpus scanning)")
    for sv in v.get("search_variants", []):
        lines.append(f"- {sv}")
    lines.append("")

    # Corpus search terms
    lines.append("## Corpus Search Terms (framework language)")
    for ct in v.get("corpus_search_terms", []):
        lines.append(f"- `{ct}`")
    lines.append("")

    # Argument clusters
    lines.append(f"## Argument Clusters ({a.get('cluster_count', '?')} distinct lines)")
    lines.append(f"**Difficulty for Christianity:** {a.get('difficulty_rating', '?')}/10")
    lines.append("")
    for cluster in a.get("argument_clusters", []):
        side_tag = "FOR" if cluster["side"] == "for" else "AGAINST"
        lines.append(
            f"### [{side_tag}] {cluster['name']} (strength: {cluster.get('strength', '?')}/10)"
        )
        lines.append(f"{cluster['summary']}")
        lines.append(f"*Best advocate: {cluster.get('best_advocate', 'unknown')}*")
        lines.append("")

    # Best shots
    bsa = a.get("best_shot_against", {})
    lines.append("## Best Shot Against (steelmanned)")
    lines.append(f"{bsa.get('argument', 'N/A')}")
    lines.append(f"*Advocate: {bsa.get('advocate', 'unknown')}*")
    lines.append(f"*Why it hits: {bsa.get('why_it_hits', '')}*")
    lines.append("")

    bsf = a.get("best_shot_for", {})
    lines.append("## Best Shot For")
    lines.append(f"{bsf.get('argument', 'N/A')}")
    lines.append(f"*Advocate: {bsf.get('advocate', 'unknown')}*")
    lines.append("")

    # Framework match
    lines.append("## Framework Match")
    lines.append(f"**Coverage:** {f['coverage_status']}")
    if f["gap_flag"]:
        lines.append("**⚠️ GAP — no chapter or theorem covers this question yet**")
    for ch in f.get("chapters", []):
        lines.append(f"- Chapter: `{ch}`")
    for lt in f.get("lean_theorems", []):
        lines.append(
            f"- Lean: `{lt['theorem']}` → **{lt['status']}**"
        )
    lines.append("")

    # Resources
    lines.append("## Resources")
    lines.append("### Videos")
    for vid in r.get("youtube_videos", []):
        conf = f" [{vid.get('confidence', '?')}]" if vid.get("confidence") else ""
        lines.append(
            f"- [{vid.get('side', '?').upper()}] {vid.get('title', '?')} "
            f"— {vid.get('channel', '?')} ({vid.get('level', '?')}){conf}"
        )
        lines.append(f"  Search: `{vid.get('search_query', '')}`")

    bd = r.get("best_debate", {})
    if bd:
        lines.append(f"\n### Best Debate")
        lines.append(f"- {bd.get('title', '?')} — {', '.join(bd.get('participants', []))}")
        lines.append(f"  Search: `{bd.get('search_query', '')}`")

    lines.append("\n### Written Sources")
    for ws in r.get("written_sources", []):
        lines.append(
            f"- [{ws.get('side', '?').upper()}] *{ws.get('title', '?')}* "
            f"by {ws.get('author', '?')} ({ws.get('type', '?')})"
        )

    ro = r.get("recommended_order", [])
    if ro:
        lines.append(f"\n### 30-Minute Path")
        for i, item in enumerate(ro, 1):
            lines.append(f"{i}. {item}")

    lines.append(f"\n---\n*Generated: {brief['timestamp']}*")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Apologetics Question Evaluator")
    parser.add_argument("question", nargs="?", help="Question ID (e.g. Q-EVIL-LOGICAL)")
    parser.add_argument("--all", action="store_true", help="Run all questions")
    parser.add_argument("--batch", type=str, help="Run all questions in a section (e.g. S-EVIL)")
    parser.add_argument("--map", type=str, default=str(DEBATE_MAP_PATH), help="Path to debate_map.md")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    # Parse the debate map
    debate_map = parse_debate_map(Path(args.map))
    if not debate_map:
        print(f"No questions found in {args.map}")
        print("Falling back to QUESTION_CHAPTER_MAP keys...")
        # Use the built-in map as fallback
        debate_map = {k: k.replace("Q-", "").replace("-", " ").title()
                      for k in QUESTION_CHAPTER_MAP}

    # Determine which questions to run
    if args.all:
        targets = debate_map
    elif args.batch:
        section = args.batch.upper()
        targets = {k: v for k, v in debate_map.items()
                   if k.startswith(f"Q-{section.replace('S-', '')}")}
    elif args.question:
        qid = args.question.upper()
        if qid in debate_map:
            targets = {qid: debate_map[qid]}
        else:
            print(f"Question {qid} not found in debate map. Running with ID as text.")
            targets = {qid: qid}
    else:
        parser.print_help()
        return

    print(f"\nRunning {len(targets)} question(s)...\n")

    results = []
    for qid, qtext in targets.items():
        try:
            brief = evaluate_question(qid, qtext)
            results.append(brief)

            # Save JSON
            json_path = out / f"{qid}.json"
            json_path.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")

            # Save markdown
            md_path = out / f"{qid}.md"
            md_path.write_text(render_markdown(brief), encoding="utf-8")

            print(f"  ✓ Saved: {json_path.name} + {md_path.name}")

        except Exception as e:
            print(f"  ✗ FAILED {qid}: {e}")

    # Save summary index
    summary = {
        "total": len(results),
        "gaps": [r["question_id"] for r in results if r["framework"]["gap_flag"]],
        "verified": [r["question_id"] for r in results
                     if r["framework"]["coverage_status"] == "FORMALLY_VERIFIED"],
        "bridge": [r["question_id"] for r in results
                   if r["framework"]["coverage_status"] == "BRIDGE_CANDIDATE"],
        "timestamp": datetime.utcnow().isoformat(),
        "questions": [
            {
                "id": r["question_id"],
                "real_question": r["variants"].get("real_question", ""),
                "coverage": r["framework"]["coverage_status"],
                "difficulty": r["arguments"].get("difficulty_rating", "?"),
                "cluster_count": r["arguments"].get("cluster_count", "?"),
            }
            for r in results
        ],
    }
    idx_path = out / "_INDEX.json"
    idx_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{'='*60}")
    print(f"  COMPLETE: {len(results)} briefs generated")
    print(f"  Gaps: {len(summary['gaps'])}")
    print(f"  Verified: {len(summary['verified'])}")
    print(f"  Bridge: {len(summary['bridge'])}")
    print(f"  Index: {idx_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
