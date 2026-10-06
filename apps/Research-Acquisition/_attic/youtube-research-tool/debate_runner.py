"""Drives the debate map end to end and prints it for a human.

Kept separate from debate_map.py so that module stays pure and testable: the
analysis functions there take data and return data, while everything that
touches the network, the filesystem, or the terminal lives here.

yt_scrape is imported lazily inside the functions, because yt_scrape's own
CLI dispatches into this module - a top-level import would be circular.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import debate_map as dm
import ollama_client as oc


def _say(msg: str = "") -> None:
    print(msg, file=sys.stderr)


def _fmt_duration(seconds: int) -> str:
    if not seconds:
        return "?"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _fmt_views(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n or 0)


def _read_body(path: str | Path) -> str:
    """Transcript text with this tool's header stripped off."""
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    marker = raw.find("=" * 20)
    return raw[marker:].lstrip("=\n").strip() if marker != -1 else raw


def present_candidates(candidates: list[dm.Candidate],
                       scores: dict[str, tuple[float, bool]] | None = None) -> None:
    """Show what was found, best matches first, with off-topic ones marked."""
    idx = 1
    for c in candidates:
        score, ok = (scores or {}).get(c.video_id, (0.0, True))
        mark = "   " if ok else "?! "
        tag = f"{score:.2f}" if scores else "    "
        _say(f"   {idx:>3}. {mark}{tag}  {c.title[:60]}")
        _say(f"              {c.channel[:34]:<34} {_fmt_duration(c.duration):>8}  [{c.side_hint[:28]}]")
        idx += 1


def parse_selection(answer: str, total: int) -> list[int] | None:
    """Turn '1,3,5-9' into indices. None means cancel, [] means 'all'."""
    answer = (answer or "").strip().lower()
    if answer in ("", "y", "yes", "a", "all"):
        return []
    if answer in ("n", "no", "q", "quit", "cancel"):
        return None
    picked: list[int] = []
    for part in answer.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            if lo.isdigit() and hi.isdigit():
                picked.extend(range(int(lo), int(hi) + 1))
        elif part.isdigit():
            picked.append(int(part))
    picked = [i for i in picked if 1 <= i <= total]
    return sorted(set(picked)) or None


def run_debate_map(
    url: str,
    output_dir: Path | None = None,
    per_query: int = 5,
    max_videos: int = 12,
    proxy: str | None = None,
    auto_yes: bool = False,
    cookies_file: str | None = None,
    cookies_from_browser: str | None = None,
) -> dict:
    """Seed URL in, multi-sided debate map out."""
    import yt_scrape  # lazy: yt_scrape dispatches into this module

    out_dir = output_dir or yt_scrape.OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    if not oc.is_available():
        return {"ok": False, "error": "Ollama is not running. Start it with: ollama serve",
                "error_type": "no_llm"}

    # --- seed -------------------------------------------------------------
    _say("[1/7] Fetching the seed video...")
    seed = yt_scrape.extract_transcript(
        url, output_dir=out_dir, proxy=proxy,
        cookies_file=cookies_file, cookies_from_browser=cookies_from_browser,
    )
    if not seed.has_transcript:
        return {"ok": False, "error": seed.error or "No transcript for the seed video",
                "error_type": seed.error_type or "no_transcript"}
    seed_text = _read_body(seed.transcript_path)

    # --- proposition ------------------------------------------------------
    _say("[2/7] Working out what is actually being contested...")
    prop = dm.derive_proposition(seed_text, seed.title, seed.channel)
    if not prop:
        return {"ok": False, "error": "Could not derive a proposition from the seed video",
                "error_type": "no_proposition"}
    _say(f"      Proposition: {prop.statement}")
    _say(f"      Domain: {prop.domain}   Sides: {', '.join(prop.sides)}")

    # --- queries + candidates --------------------------------------------
    _say("[3/7] Generating searches for each side...")
    queries = dm.enforce_anchors(dm.generate_queries(prop), dm.anchor_terms(prop))
    for q, hint in queries:
        _say(f"      \"{q}\"  -> {hint}")

    _say("[4/7] Searching YouTube (metadata only, nothing downloaded yet)...")

    def search_fn(query: str, limit: int):
        return yt_scrape.search_videos(
            query, limit=limit, transcripts=False, output_dir=out_dir, proxy=proxy,
            cookies_file=cookies_file, cookies_from_browser=cookies_from_browser,
        )

    candidates = dm.collect_candidates(
        queries, search_fn, per_query=per_query, exclude_ids={seed.id},
    )
    if not candidates:
        return {"ok": False, "error": "No candidate videos found", "error_type": "no_candidates"}

    # --- approval gate ----------------------------------------------------
    _say(f"\n  Found {len(candidates)} candidates. Scoring relevance...")
    ranked = dm.rank_candidates(prop, candidates)
    candidates = [c for c, _, _ in ranked]
    scores = {c.video_id: (sc, ok) for c, sc, ok in ranked}
    flagged = sum(1 for _, _, ok in ranked if not ok)
    if flagged:
        _say(f"  {flagged} look off-topic (marked ?!) - YouTube search matches loosely.")
    present_candidates(candidates, scores)

    if auto_yes:
        chosen = dm.balance_by_side(ranked, max_videos)
    else:
        _say(f"\n  Transcripts will be downloaded for the ones you pick (max {max_videos}).")
        _say("  [Enter] take all   [1,3,5-9] pick specific   [n] cancel")
        try:
            answer = input("  > ")
        except EOFError:
            answer = ""
        picks = parse_selection(answer, len(candidates))
        if picks is None:
            return {"ok": False, "error": "Cancelled at the approval step",
                    "error_type": "cancelled"}
        chosen = [candidates[i - 1] for i in picks] if picks else candidates[:max_videos]

    chosen = chosen[:max_videos]
    _say(f"\n[5/7] Fetching {len(chosen)} transcripts...")

    # --- harvest + stance + claims ---------------------------------------
    stances: list[dm.Stance] = []
    all_claims: list[dm.Claim] = []
    harvested: list[dict] = []

    for n, cand in enumerate(chosen, 1):
        _say(f"      ({n}/{len(chosen)}) {cand.title[:58]}")
        info = yt_scrape.extract_transcript(
            cand.url, output_dir=out_dir, proxy=proxy,
            cookies_file=cookies_file, cookies_from_browser=cookies_from_browser,
        )
        if not info.has_transcript:
            _say(f"          skipped - {info.error_type or 'no transcript'}")
            continue
        body = _read_body(info.transcript_path)

        stance = dm.classify_stance(prop, body, info.title or cand.title,
                                    cand.video_id, info.channel or cand.channel)
        stances.append(stance)
        _say(f"          side: {stance.side} ({stance.confidence:.0%})")

        claims = dm.extract_claims(prop, body, cand.video_id,
                                   info.channel or cand.channel, stance.side)
        if not claims:
            # A video can otherwise be fetched, classified, and then silently
            # vanish from the analysis. When it is the only voice for its side,
            # that turns a debate map into a monologue without saying so.
            _say(f"          no claims extracted - this video adds nothing to the map")
        all_claims.extend(claims)
        harvested.append({
            "video_id": cand.video_id, "title": info.title or cand.title,
            "channel": info.channel or cand.channel, "url": cand.url,
            "side": stance.side, "claims": len(claims),
        })

    if not all_claims:
        return {"ok": False, "error": "No claims could be extracted from any video",
                "error_type": "no_claims"}

    # --- cluster ----------------------------------------------------------
    _say(f"\n[6/7] Clustering {len(all_claims)} claims across {len(harvested)} videos...")
    before = len(all_claims)
    all_claims = dm.drop_proposition_echo(all_claims, prop)
    if len(all_claims) < before:
        _say(f"      dropped {before - len(all_claims)} claim(s) that just echoed the proposition")
    clusters = dm.cluster_claims(all_claims)
    cruxes = [c for c in clusters if c.is_crux]
    _say(f"      {len(clusters)} distinct points, {len(cruxes)} contested by more than one side")

    # --- steelman each side ----------------------------------------------
    by_side = dm.group_by_side(all_claims)
    if len(by_side) < 2:
        # Worth saying out loud: the whole point is contrast between sides.
        _say("      WARNING: only one side produced claims - this is not a debate map.")
        _say("      Re-run picking videos from other positions at the approval step.")
    _say(f"[7/7] Building the best case for each of {len(by_side)} sides...")
    cases: list[dm.SideCase] = []
    for side, claims in sorted(by_side.items(), key=lambda kv: len(kv[1]), reverse=True):
        _say(f"      {side} ({len(claims)} claims)...")
        vids = sorted({c.video_id for c in claims})
        cases.append(dm.build_side_case(prop, side, claims, vids))

    result = {
        "ok": True,
        "seed": {"video_id": seed.id, "title": seed.title,
                 "channel": seed.channel, "url": seed.url},
        "proposition": prop.to_dict(),
        "queries": [{"query": q, "side_hint": h} for q, h in queries],
        "candidates_found": len(candidates),
        "videos_analysed": harvested,
        "claim_count": len(all_claims),
        "sides": [c.to_dict() for c in cases],
        "cruxes": [c.to_dict() for c in cruxes[:15]],
        "stances": [s.to_dict() for s in stances],
    }

    path = out_dir / f"{seed.id}_debate_map.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["output_path"] = str(path)
    return result


def print_report(result: dict) -> None:
    """Human-readable rendering of the map."""
    prop = result["proposition"]
    bar = "=" * 74
    print(bar)
    print("  DEBATE MAP")
    print(bar)
    print(f"  Proposition: {prop['statement']}")
    print(f"  Domain:      {prop['domain']}")
    print(f"  Seed:        {result['seed']['title'][:56]}")
    print(f"  Analysed:    {len(result['videos_analysed'])} videos, "
          f"{result['claim_count']} claims, {len(result['sides'])} sides")
    print(bar)

    for case in result["sides"]:
        print(f"\n  ---- {case['side'].upper()} ----  ({len(case['video_ids'])} videos)")
        if case.get("actual_position"):
            print(f"       claims actually argue: {case['actual_position']}")
        if case.get("label_warning"):
            print(f"       !! LABEL MISMATCH: {case['label_warning']}")
        print(f"\n  BEST CASE:\n    {case['best_case']}")
        if case["key_claims"]:
            print("\n  LOAD-BEARING CLAIMS:")
            for k in case["key_claims"]:
                print(f"    - {k}")
        if case["strongest_evidence"]:
            print(f"\n  STRONGEST EVIDENCE:\n    {case['strongest_evidence']}")
        if case["weakest_point"]:
            print(f"\n  MOST VULNERABLE:\n    {case['weakest_point']}")

    if result["cruxes"]:
        print(f"\n{bar}")
        print("  CRUXES - points more than one side actually engages")
        print(bar)
        for c in result["cruxes"][:10]:
            print(f"\n  * {c['label']}")
            print(f"    contested by: {', '.join(c['sides'])}")
            for claim in c["claims"][:4]:
                print(f"      [{claim['side'][:18]:<18}] {claim['text'][:60]}")

    print(f"\n{bar}")
    print(f"  Saved: {result.get('output_path', '')}")
    print(bar)
