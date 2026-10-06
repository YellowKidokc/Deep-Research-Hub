"""Fruits of Love and Truth: Truth Engine v2.0 lexicon pass + character profiles. Local, no API, same result every run.

Lexicons: prompts/truth_engine_v2_lexicons.json (extracted from David's Fruits Template workbook).
Profiles: prompts/character_profiles.json, explained in prompts/CHARACTER_PROFILES.md.
Word hits are a trace, never a verdict (rubric invariant: vocabulary is not character evidence).
"""
from __future__ import annotations
import json, math, re
from pathlib import Path

PROMPTS = Path(__file__).resolve().parents[1] / "prompts"
FRUITS = ["love", "joy", "peace", "patience", "kindness", "goodness", "faithfulness", "gentleness", "self_control"]
CATS = ["fruit", "anti_fruit", "grounding", "contradiction", "propaganda", "academic_jargon"]


def _load(name): return json.loads((PROMPTS / name).read_text(encoding="utf-8"))

def _pattern(terms):
    words = sorted({t for t in terms if t}, key=len, reverse=True)
    return re.compile(r"(?<![\w-])(" + "|".join(re.escape(w) for w in words) + r")(?![\w-])", re.I) if words else None


def lexicon_pass(sentences: list[dict]) -> tuple[list[dict], dict]:
    """Per sentence: hits and trigger words per Truth Engine category. Per paper: densities, TRUTH score, characterizations."""
    lex = _load("truth_engine_v2_lexicons.json")
    pats = {c: _pattern([x["term"] for x in lex[c]]) for c in CATS}
    sub = {c: {x["term"]: (x.get("cat") or "") for x in lex[c]} for c in CATS}
    rows, words_total = [], 0
    totals = {c: 0 for c in CATS}; share = {c: 0 for c in CATS}; subtotals: dict[str, int] = {}
    for s in sentences:
        text = s["text"]; words_total += len(re.findall(r"\w+", text))
        hits = {}
        for c in CATS:
            found = [m.group(1).lower() for m in pats[c].finditer(text)] if pats[c] else []
            hits[c] = found; totals[c] += len(found); share[c] += 1 if found else 0
            for f in found:
                key = f"{c}:{sub[c].get(f, '')}"; subtotals[key] = subtotals.get(key, 0) + 1
        rows.append({"id": s["id"], "hits": hits})
    n = max(1, len(sentences)); per100 = {c: round(totals[c] * 100 / max(1, words_total), 3) for c in CATS}
    w = lex["weights"]
    truth_raw = sum(per100[c] * w[c] for c in CATS)
    summary = {"words": words_total, "hits": totals, "per_100_words": per100,
               "sentence_share": {c: round(share[c] / n, 3) for c in CATS},
               "subcategories": dict(sorted(subtotals.items(), key=lambda x: -x[1])[:15]),
               "truth_score_raw": round(truth_raw, 3),
               "truth_score_0_1": round(1 / (1 + math.exp(-truth_raw / 2)), 3),
               "top_words": {c: _top([h for r in rows for h in r["hits"][c]]) for c in CATS}}
    return rows, summary

def _top(items, k=8):
    counts: dict[str, int] = {}
    for x in items: counts[x] = counts.get(x, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1])[:k])


def characterizations(lex_summary: dict, coherence: dict | None, fruits: dict | None) -> list[dict]:
    """The workbook's 10 patterns, conditions read literally; densities = share of sentences with a hit."""
    lex = _load("truth_engine_v2_lexicons.json"); sh = lex_summary["sentence_share"]; subs = lex_summary["subcategories"]
    gates = {g.get("gate_id"): g.get("status") for g in (fruits or {}).get("gate_results", [])}
    total_anti = max(1, lex_summary["hits"]["anti_fruit"])
    env = {"fruit": sh["fruit"], "anti_fruit": sh["anti_fruit"], "grounding": sh["grounding"], "contradiction": sh["contradiction"],
           "propaganda": sh["propaganda"], "jargon": sh["academic_jargon"],
           "coherence": ((coherence or {}).get("overall") or {}).get("score", 0) / 10 if isinstance(((coherence or {}).get("overall") or {}).get("score"), (int, float)) else 0,
           "kill_conditions": 1 if gates.get("gate.falsifiability") == "PASS" else 0, "role": "unknown",
           "anti_fruit_woke": sh["anti_fruit"] * sum(v for k, v in subs.items() if k.startswith("anti_fruit:woke")) / total_anti,
           "anti_fruit_fitts": sh["anti_fruit"] * sum(v for k, v in subs.items() if k.startswith("anti_fruit:fitts")) / total_anti}
    out = []
    for ch in lex["characterizations"]:
        ok = True
        for cond in re.split(r"\s+AND\s+", ch["conditions"] or ""):
            m = re.match(r"\s*(\w+)\s*(>=|<=|>|<|=)\s*([\w.]+)", cond)
            if not m: ok = False; break
            k, op, v = m.groups(); x = env.get(k)
            if isinstance(x, str) or not re.match(r"^[\d.]+$", v):
                ok = ok and str(x) == v; continue
            v = float(v); x = x or 0
            ok = ok and {">": x > v, "<": x < v, ">=": x >= v, "<=": x <= v, "=": x == v}[op]
        if ok: out.append({"name": ch["name"], "output": ch["output"], "conditions": ch["conditions"]})
    return out


def fruit_scores(fruits: dict | None) -> tuple[dict, float]:
    prof = (fruits or {}).get("fruit_profile") or []
    scores = {p["fruit_id"].split(".")[-1]: p.get("score") for p in prof if isinstance(p.get("score"), int)}
    conf = [p.get("confidence") for p in prof if isinstance(p.get("confidence"), (int, float))]
    return scores, (sum(conf) / len(conf) if conf else 0.0)


def profiles(fruits: dict | None, coherence: dict | None, lex_summary: dict) -> dict:
    cfg = _load("character_profiles.json"); scores, mean_conf = fruit_scores(fruits)
    result = {"version": cfg["version"], "scores": scores, "mean_confidence": round(mean_conf, 3)}
    if len(scores) != 9:
        return {**result, "status": "NOT_ASSESSED", "reason": "fruit verdict missing"}
    vals = [scores[f] for f in FRUITS]
    love_axis = sum(vals) / 36
    gate = next((g.get("status") for g in fruits.get("gate_results", []) if g.get("gate_id") == "gate.truth_evidence"), None)
    parts = {"lexicon": lex_summary["truth_score_0_1"]}
    co = ((coherence or {}).get("overall") or {}).get("score")
    if isinstance(co, (int, float)): parts["coherence"] = co / 10
    if gate: parts["truth_gate"] = {"PASS": 1, "WARN": 0.66, "UNKNOWN": 0.5, "FAIL": 0}.get(gate, 0.5)
    truth_axis = sum(parts.values()) / len(parts)
    cut = cfg["quadrant_cut"]
    quadrant = cfg["quadrants"][f"love_{'high' if love_axis >= cut else 'low'}_truth_{'high' if truth_axis >= cut else 'low'}"]
    levels = []
    for lv in cfg["verdict_levels"]:
        if lv["rule"] == "all_at_least" and min(vals) >= lv["value"] and scores["love"] >= lv.get("love_at_least", 0): levels.append(lv["name"])
        if lv["rule"] == "count_at_most" and sum(v <= lv["value"] for v in vals) >= lv["count"]: levels.append(lv["name"])
        if lv["rule"] == "count_equal" and (sum(v == lv["value"] for v in vals) >= lv["count"] or mean_conf < lv.get("or_mean_confidence_below", -1)): levels.append(lv["name"])
    mean = sum(vals) / 9; dev = {f: scores[f] - mean for f in FRUITS}
    shapes = []
    for sp in cfg["shapes"]:
        hi = [dev[f] for f in sp["high"]]; lo = [dev[f] for f in (sp["low"] or [f for f in FRUITS if f not in sp["high"]])]
        gap = sum(hi) / len(hi) - sum(lo) / len(lo)
        shapes.append({"name": sp["name"], "gap": round(gap, 2), "match": gap >= cfg["verdict_shape_gap"], "high": sp["high"], "low": sp["low"]})
    shapes.sort(key=lambda x: -x["gap"])
    return {**result, "status": "ASSESSED", "love_axis": round(love_axis, 3), "truth_axis": round(truth_axis, 3), "truth_parts": parts,
            "quadrant": quadrant if "No Signal" not in levels else f"No Signal (nearest: {quadrant})",
            "levels": levels, "shapes_matched": [s for s in shapes if s["match"]][:2], "shapes_ranked": shapes,
            "profile_deviation": {f: round(d, 2) for f, d in dev.items()}}


def sentence_profile(rows: list[dict], fruits: dict | None, coherence: dict | None, lex_summary: dict, unit: str = "sentences") -> dict:
    """The headline profile, scored automatically from the per-sentence pass (what the text itself does).
    Each fruit = net points per 100 sentences; shapes are read from each fruit's distance from the paper's own average."""
    cfg = _load("character_profiles.json")
    scored = [r for r in rows if r.get("v")]
    if not scored: return {"version": cfg["version"], "status": "NOT_ASSESSED", "reason": "no scored sentences"}
    n = len(scored)
    net = {f: round(100 * sum(r["v"][i] for r in scored) / n, 2) for i, f in enumerate(FRUITS)}
    active = {f: sum(1 for r in scored if r["v"][i]) for i, f in enumerate(FRUITS)}
    active_share = sum(1 for r in scored if any(r["v"])) / n
    k = cfg["axis_scale"]
    love_axis = 0.5 + 0.5 * math.tanh(sum(net.values()) / 9 / k)
    gate = next((g.get("status") for g in (fruits or {}).get("gate_results", []) if g.get("gate_id") == "gate.truth_evidence"), None)
    parts = {"lexicon": lex_summary["truth_score_0_1"]}
    co = ((coherence or {}).get("overall") or {}).get("score")
    if isinstance(co, (int, float)): parts["coherence"] = co / 10
    if gate: parts["truth_gate"] = {"PASS": 1, "WARN": 0.66, "UNKNOWN": 0.5, "FAIL": 0}.get(gate, 0.5)
    truth_axis = sum(parts.values()) / len(parts)
    cut = cfg["quadrant_cut"]
    quadrant = cfg["quadrants"][f"love_{'high' if love_axis >= cut else 'low'}_truth_{'high' if truth_axis >= cut else 'low'}"]
    levels = []
    for lv in cfg["levels"]:
        if lv["rule"] == "all_at_least" and min(net.values()) >= lv["value"]: levels.append(lv["name"])
        if lv["rule"] == "count_at_most" and sum(v <= lv["value"] for v in net.values()) >= lv["count"]: levels.append(lv["name"])
        if lv["rule"] == "active_share_below" and active_share < lv["value"]: levels.append(lv["name"])
    mean = sum(net.values()) / 9; dev = {f: net[f] - mean for f in FRUITS}
    shapes = []
    for sp in cfg["shapes"]:
        low = sp["low"] or [f for f in FRUITS if f not in sp["high"]]
        gap = sum(dev[f] for f in sp["high"]) / len(sp["high"]) - sum(dev[f] for f in low) / len(low)
        enough = sum(active[f] for f in sp["high"]) >= cfg["min_active_sentences"]
        # A vice shape (low_means "negative") needs its low fruits to actually score below zero: absent love is not cold love.
        truly_low = sp.get("low_means") != "negative" or sum(net[f] for f in sp["low"]) / len(sp["low"]) < 0
        shapes.append({"name": sp["name"], "gap": round(gap, 2), "match": gap >= cfg["shape_gap"] and enough and truly_low,
                       "high": sp["high"], "low": sp["low"], "low_means": sp.get("low_means", ""),
                       **({} if truly_low else {"blocked": "low fruits are absent, not negative"})})
    shapes.sort(key=lambda x: -x["gap"])
    return {"version": cfg["version"], "status": "ASSESSED", "source": unit, "unit": unit, "sentences": n,
            "active_share": round(active_share, 3), "net_per_100": net, "active_sentences": active,
            "love_axis": round(love_axis, 3), "truth_axis": round(truth_axis, 3), "truth_parts": parts,
            "quadrant": quadrant if "No Signal" not in levels else f"No Signal (nearest: {quadrant})",
            "levels": levels, "shapes_matched": [s for s in shapes if s["match"]][:2], "shapes_ranked": shapes,
            "profile_deviation": {f: round(d, 2) for f, d in dev.items()}}
