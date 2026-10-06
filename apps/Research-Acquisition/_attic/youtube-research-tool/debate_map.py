"""Map a debate across many videos, not just the one you started from.

Give it a seed YouTube URL and it works out what is actually being contested,
goes looking for videos on every side of it, pulls their transcripts, extracts
each side's claims, and writes up the strongest version of each position.

The point is the steelman. Extracting claims from a single video only tells
you what one person said; the interesting question is what the best people on
each side say, and where they actually disagree.

Pipeline:
  1. proposition   - what is the contested claim? (LLM over the seed transcript)
  2. queries       - searches likely to surface each side (LLM)
  3. candidates    - YouTube search, metadata only, nothing downloaded yet
  4. [approval]    - the caller confirms before any transcripts are fetched
  5. harvest       - transcripts for the approved videos
  6. stance        - where does each video actually stand? (LLM per video)
  7. claims        - what does each video assert? (LLM per video)
  8. clusters      - group claims by meaning, via embeddings
  9. cases         - the best case for each side (LLM synthesis)

Local models throughout, so a 20-video run costs nothing and stays private.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Callable

import ollama_client as oc

# Seed transcripts run long; local models don't need the whole thing to work
# out the topic. Claims are extracted from chunks so nothing gets truncated away.
PROPOSITION_CHARS = 6000
CLAIM_CHUNK_CHARS = 4000
MAX_CLAIM_CHUNKS = 6
# Two claims this close in embedding space are saying the same thing.
CLUSTER_THRESHOLD = 0.78


# ------------------------------------------------------------------ data

@dataclass
class Proposition:
    statement: str = ""
    topic: str = ""
    domain: str = ""
    sides: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Candidate:
    video_id: str = ""
    title: str = ""
    channel: str = ""
    url: str = ""
    duration: int = 0
    views: int = 0
    query: str = ""
    side_hint: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Claim:
    text: str = ""
    video_id: str = ""
    channel: str = ""
    side: str = ""
    kind: str = ""
    support: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Stance:
    video_id: str = ""
    side: str = ""
    confidence: float = 0.0
    rationale: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ClaimCluster:
    label: str = ""
    claims: list[Claim] = field(default_factory=list)
    sides: list[str] = field(default_factory=list)

    @property
    def is_crux(self) -> bool:
        """A point more than one side speaks to - where the debate actually lives."""
        return len(self.sides) > 1

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "sides": self.sides,
            "is_crux": self.is_crux,
            "claims": [c.to_dict() for c in self.claims],
        }


@dataclass
class SideCase:
    side: str = ""
    actual_position: str = ""
    label_warning: str = ""
    best_case: str = ""
    key_claims: list[str] = field(default_factory=list)
    strongest_evidence: str = ""
    weakest_point: str = ""
    video_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ------------------------------------------------------- stage 1: proposition

_SYSTEM = (
    "You analyse debates. You are precise, neutral, and you never take a side. "
    "You always answer with valid JSON and nothing else."
)


def derive_proposition(transcript: str, title: str = "", channel: str = "") -> Proposition | None:
    """Work out the contested claim the seed video is arguing about."""
    excerpt = transcript[:PROPOSITION_CHARS]
    prompt = f"""Read this transcript excerpt from a YouTube video and identify the central CONTESTED proposition - the claim that reasonable people actually disagree about.

Video title: {title}
Channel: {channel}

Transcript excerpt:
\"\"\"{excerpt}\"\"\"

Respond with JSON only:
{{
  "statement": "the contested proposition, as a single neutral declarative sentence that someone could affirm or deny",
  "topic": "3-6 word topic label",
  "domain": "the field this sits in, e.g. theology, economics, climate science, nutrition",
  "sides": ["short label for each distinct position", "..."]
}}

Rules:
- The statement must be NEUTRAL. Write it as a claim one side AFFIRMS and another DENIES, with no evaluative adverbs.
- BAD: "The Bible's depiction of labour is consistently condemnatory of slavery" - "consistently condemnatory" is one side's conclusion baked in.
- GOOD: "The Bible endorses slavery rather than merely regulating it" - either side can take this up and argue it.
- Do not use words like "consistently", "clearly", "obviously", "merely" as a verdict.
- List every genuinely distinct position, not just two. Many debates have 3 or 4.
- Side labels are short, e.g. "Traditional apologist", "Critical scholar", "Abolitionist reading".
"""
    data = oc.generate_json(prompt, model=oc.SMART_MODEL, system=_SYSTEM)
    if not isinstance(data, dict) or not data.get("statement"):
        return None
    sides = [str(s).strip() for s in data.get("sides", []) if str(s).strip()]
    return Proposition(
        statement=str(data.get("statement", "")).strip(),
        topic=str(data.get("topic", "")).strip(),
        domain=str(data.get("domain", "")).strip(),
        sides=sides or ["For", "Against"],
    )


# ----------------------------------------------------------- stage 2: queries

def generate_queries(prop: Proposition, per_side: int = 2) -> list[tuple[str, str]]:
    """Search phrases likely to surface each side. Returns (query, side_hint)."""
    prompt = f"""A debate is happening about this proposition:

"{prop.statement}"
Topic: {prop.topic} ({prop.domain})
Known positions: {", ".join(prop.sides)}

Write YouTube search queries that would surface strong, substantive videos arguing each position. Real phrasing people use in video titles - not academic phrasing.

Respond with JSON only:
{{"queries": [{{"query": "...", "side": "which position this would surface"}}]}}

Give {per_side} queries per position. Favour queries that find people making the ARGUMENT, not news coverage or reaction clips.
"""
    data = oc.generate_json(prompt, model=oc.SMART_MODEL, system=_SYSTEM)
    out: list[tuple[str, str]] = []
    if isinstance(data, dict):
        for item in data.get("queries", []):
            if isinstance(item, dict) and item.get("query"):
                out.append((str(item["query"]).strip(), str(item.get("side", "")).strip()))
    if not out:
        out = fallback_queries(prop)
    return out


# Words too generic to anchor a search on. Combined with _STOP at call time,
# since _STOP is defined further down with the clustering helpers.
_ANCHOR_EXTRA_STOP = {
    "bible", "biblical", "does", "say", "says", "about", "really", "actually",
    "people", "thing", "things", "way", "ways", "good", "bad",
}


def anchor_terms(prop: Proposition, limit: int = 2) -> list[str]:
    """The words a query must keep to stay on topic.

    Frequency-ranked content words from the proposition and topic. The LLM
    writes fluent queries but drifts - it produced "Bible verses against
    owning people" for a slavery debate, which YouTube matched on vibes and
    returned devotional playlists. An anchor is the cheap guard against that.
    """
    from collections import Counter
    text = f"{prop.topic} {prop.statement}".lower()
    counts = Counter(w for w in _WORD_RE.findall(text)
                     if w not in (_STOP | _ANCHOR_EXTRA_STOP) and len(w) > 3)
    if not counts:
        return []
    # Ties broken by length: longer words are more discriminating.
    ranked = sorted(counts.items(), key=lambda kv: (kv[1], len(kv[0])), reverse=True)
    return [w for w, _ in ranked[:limit]]


def enforce_anchors(queries: list[tuple[str, str]], anchors: list[str]) -> list[tuple[str, str]]:
    """Append the primary anchor to any query that dropped it."""
    if not anchors:
        return queries
    primary = anchors[0]
    out: list[tuple[str, str]] = []
    for query, hint in queries:
        if not any(a in query.lower() for a in anchors):
            query = f"{query} {primary}".strip()
        out.append((query, hint))
    return out


def fallback_queries(prop: Proposition) -> list[tuple[str, str]]:
    """Template queries for when the model is unavailable or unhelpful."""
    topic = prop.topic or prop.statement[:60]
    return [
        (f"{topic} explained", "overview"),
        (f"{topic} debate", "overview"),
        (f"{topic} debunked", "critical"),
        (f"{topic} response", "critical"),
        (f"case for {topic}", "supportive"),
        (f"{topic} rebuttal", "supportive"),
    ]


# -------------------------------------------------------- stage 3: candidates

def collect_candidates(
    queries: list[tuple[str, str]],
    search_fn: Callable[[str, int], list],
    per_query: int = 5,
    exclude_ids: set[str] | None = None,
    min_duration: int = 240,
) -> list[Candidate]:
    """Search each query and dedupe into one candidate list.

    `search_fn(query, limit)` returns objects with the VideoInfo fields, so the
    caller supplies yt_scrape.search_videos and this module stays testable.
    Short clips are dropped - reaction shorts rarely carry an argument.
    """
    seen: set[str] = set(exclude_ids or set())
    out: list[Candidate] = []
    for query, side_hint in queries:
        try:
            results = search_fn(query, per_query)
        except Exception:
            continue
        for r in results or []:
            vid = getattr(r, "id", "") or ""
            if not vid or vid in seen:
                continue
            duration = getattr(r, "duration", 0) or 0
            if min_duration and duration and duration < min_duration:
                continue
            seen.add(vid)
            out.append(Candidate(
                video_id=vid,
                title=getattr(r, "title", "") or "",
                channel=getattr(r, "channel", "") or "",
                url=getattr(r, "url", "") or f"https://www.youtube.com/watch?v={vid}",
                duration=duration,
                views=getattr(r, "view_count", 0) or 0,
                query=query,
                side_hint=side_hint,
            ))
    return out


# ------------------------------------------------------------ stage 6: stance

def classify_stance(prop: Proposition, transcript: str, title: str,
                    video_id: str, channel: str = "") -> Stance:
    """Decide where one video stands on the proposition."""
    excerpt = transcript[:PROPOSITION_CHARS]
    prompt = f"""Proposition under debate:
"{prop.statement}"

Known positions: {", ".join(prop.sides)}

Video title: {title}
Channel: {channel}
Transcript excerpt:
\"\"\"{excerpt}\"\"\"

Which position does THIS video take? If it takes a position not in the list, name it. If it is genuinely neutral or purely explanatory, say "Neutral".

Respond with JSON only:
{{"side": "...", "confidence": 0.0-1.0, "rationale": "one sentence citing what in the transcript shows this"}}
"""
    data = oc.generate_json(prompt, model=oc.FAST_MODEL, system=_SYSTEM)
    if not isinstance(data, dict) or not data.get("side"):
        return Stance(video_id=video_id, side="Unclassified", confidence=0.0,
                      rationale="Model unavailable or gave no usable answer.")
    try:
        conf = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    return Stance(
        video_id=video_id,
        side=str(data["side"]).strip(),
        confidence=max(0.0, min(1.0, conf)),
        rationale=str(data.get("rationale", "")).strip(),
    )


# ------------------------------------------------------------ stage 7: claims

def chunk_text(text: str, size: int, limit: int) -> list[str]:
    chunks = [text[i:i + size] for i in range(0, len(text), size)]
    return chunks[:limit]


def extract_claims(prop: Proposition, transcript: str, video_id: str,
                   channel: str = "", side: str = "") -> list[Claim]:
    """Pull the arguable assertions out of one transcript."""
    claims: list[Claim] = []
    for chunk in chunk_text(transcript, CLAIM_CHUNK_CHARS, MAX_CLAIM_CHUNKS):
        prompt = f"""Proposition under debate: "{prop.statement}"

Extract the ARGUABLE CLAIMS this speaker makes that bear on the proposition. A claim is something that could be true or false and that someone could dispute. Ignore pleasantries, asides, and pure narration.

Transcript chunk:
\"\"\"{chunk}\"\"\"

Respond with JSON only:
{{"claims": [{{"text": "the claim in one clear sentence", "kind": "empirical|interpretive|moral|definitional", "support": "what the speaker offers as support, or 'asserted' if nothing"}}]}}

Restate each claim so it stands alone without the surrounding context. Return an empty list if the chunk contains no real claims.
"""
        data = oc.generate_json(prompt, model=oc.FAST_MODEL, system=_SYSTEM)
        if not isinstance(data, dict):
            continue
        for item in data.get("claims", []):
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", "")).strip()
            if len(text) < 15:
                continue
            claims.append(Claim(
                text=text, video_id=video_id, channel=channel, side=side,
                kind=str(item.get("kind", "")).strip(),
                support=str(item.get("support", "")).strip(),
            ))
    return claims


# ---------------------------------------------------------- stage 8: clusters

def cluster_claims(claims: list[Claim], threshold: float = CLUSTER_THRESHOLD) -> list[ClaimCluster]:
    """Group claims that are making the same point, by embedding similarity.

    Greedy single-pass clustering against cluster seeds. Good enough at this
    scale (a few hundred claims) and keeps the output stable and explainable.
    Falls back to word overlap if embeddings are unavailable.
    """
    if not claims:
        return []
    vectors = [oc.embed(c.text) for c in claims]
    use_embeddings = any(v for v in vectors)

    seeds: list[tuple[list[float] | None, ClaimCluster, set[str]]] = []
    for claim, vec in zip(claims, vectors):
        placed = False
        for seed_vec, cluster, seed_words in seeds:
            if use_embeddings and vec and seed_vec:
                score = oc.cosine(vec, seed_vec)
                hit = score >= threshold
            else:
                hit = word_overlap(words_of(claim.text), seed_words) >= 0.5
            if hit:
                cluster.claims.append(claim)
                if claim.side and claim.side not in cluster.sides:
                    cluster.sides.append(claim.side)
                placed = True
                break
        if not placed:
            cluster = ClaimCluster(
                label=claim.text[:90],
                claims=[claim],
                sides=[claim.side] if claim.side else [],
            )
            seeds.append((vec, cluster, words_of(claim.text)))

    clusters = [c for _, c, _ in seeds]
    # Cruxes first, then the busiest points.
    clusters.sort(key=lambda c: (c.is_crux, len(c.claims)), reverse=True)
    return clusters


_WORD_RE = re.compile(r"[a-z']+")
_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "that", "this",
    "of", "to", "in", "it", "and", "or", "but", "not", "for", "on", "as", "with",
    "they", "there", "their", "he", "she", "we", "you", "does", "do", "did",
    "has", "have", "had", "can", "could", "would", "should", "what", "which",
}


def words_of(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if w not in _STOP and len(w) > 2}


def word_overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ------------------------------------------------------------- stage 9: cases

def build_side_case(prop: Proposition, side: str, claims: list[Claim],
                    video_ids: list[str]) -> SideCase:
    """Write the strongest honest version of one side's argument."""
    claim_lines = "\n".join(
        f"- {c.text} (support: {c.support or 'asserted'})" for c in claims[:40]
    )
    prompt = f"""Proposition under debate: "{prop.statement}"

These are the claims made by people arguing the "{side}" position, gathered from {len(video_ids)} videos:

{claim_lines}

Construct the STRONGEST HONEST version of this side's case - a steelman. Represent it as its most capable advocate would, not as its opponents caricature it.

IMPORTANT: the label "{side}" was assigned upstream and may be wrong. Read the claims themselves and describe the position they ACTUALLY argue. If the claims contradict the label, say so in "label_warning".

Respond with JSON only:
{{
  "actual_position": "a short label for what these claims actually argue, taken from the claims themselves",
  "label_warning": "if the claims do not match the assigned label, explain briefly; otherwise empty string",
  "best_case": "2-4 sentences putting the strongest version of the position the claims actually argue",
  "key_claims": ["the 3-5 claims that actually carry the argument"],
  "strongest_evidence": "the single most compelling piece of support offered",
  "weakest_point": "the place this position is genuinely most vulnerable"
}}

Be fair. Do not strawman, and do not inflate a weak case into a strong one - if the case is thin, the weakest_point should say so.
"""
    data = oc.generate_json(prompt, model=oc.SMART_MODEL, system=_SYSTEM)
    if not isinstance(data, dict):
        return SideCase(side=side, best_case="(synthesis unavailable)",
                        key_claims=[c.text for c in claims[:5]], video_ids=video_ids)
    return SideCase(
        side=side,
        actual_position=str(data.get("actual_position", "")).strip(),
        label_warning=str(data.get("label_warning", "")).strip(),
        best_case=str(data.get("best_case", "")).strip(),
        key_claims=[str(k).strip() for k in data.get("key_claims", []) if str(k).strip()],
        strongest_evidence=str(data.get("strongest_evidence", "")).strip(),
        weakest_point=str(data.get("weakest_point", "")).strip(),
        video_ids=video_ids,
    )


def group_by_side(claims: list[Claim]) -> dict[str, list[Claim]]:
    """Claims bucketed by side, skipping the ones with no usable stance."""
    grouped: dict[str, list[Claim]] = {}
    for c in claims:
        if not c.side or c.side.lower() in ("neutral", "unclassified"):
            continue
        grouped.setdefault(c.side, []).append(c)
    return grouped


# -------------------------------------------------- relevance (stage 3b)

# Embedding similarity alone is too forgiving here: "Bible Verses On Arguing"
# scores 0.61 against a proposition about biblical slavery, because the model
# recognises the religious register and not the topic. So a title clears the
# bar either by containing an anchor term (lexical, exact) or by scoring well
# above the fuzzy threshold on its own.
RELEVANCE_THRESHOLD = 0.55
RELEVANCE_STRONG = 0.75


def is_relevant(title: str, score: float, anchors: list[str],
                threshold: float = RELEVANCE_THRESHOLD,
                strong: float = RELEVANCE_STRONG) -> bool:
    """Keep a candidate if it is on-topic lexically or convincingly close."""
    if score >= strong:
        return True
    if score < threshold:
        return False
    if not anchors:
        return True
    low = title.lower()
    return any(a in low for a in anchors)


def score_candidates(prop: Proposition, candidates: list[Candidate],
                     threshold: float = RELEVANCE_THRESHOLD) -> list[tuple[Candidate, float]]:
    """Rank candidates by how close their title is to the proposition.

    YouTube search matches loosely, so a query about biblical slavery can
    return generic devotional content. Comparing the title against the
    proposition in embedding space catches that before any transcript is
    downloaded - which is the expensive, proxy-metered part.

    Returns (candidate, score) sorted best first. If embeddings are
    unavailable everything is returned unscored rather than silently dropped.
    """
    if not candidates:
        return []
    target = oc.embed(f"{prop.statement} {prop.topic}")
    if not target:
        return [(c, 0.0) for c in candidates]

    scored: list[tuple[Candidate, float]] = []
    for c in candidates:
        vec = oc.embed(f"{c.title} {c.channel}")
        score = oc.cosine(vec, target) if vec else 0.0
        scored.append((c, score))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


def rank_candidates(prop: Proposition, candidates: list[Candidate],
                    threshold: float = RELEVANCE_THRESHOLD) -> list[tuple[Candidate, float, bool]]:
    """Score, sort, and flag - but never discard.

    An earlier version dropped anything that failed the gate, which also threw
    away "You Think You Own It? (Leviticus 25)" - a title with no anchor word
    that is nonetheless about the central slavery text. Since a human approves
    the list anyway, the honest move is to sort the junk to the bottom and mark
    it, rather than decide silently.

    Returns (candidate, score, looks_relevant), best first.
    """
    anchors = anchor_terms(prop)
    return [
        (c, sc, is_relevant(c.title, sc, anchors, threshold))
        for c, sc in score_candidates(prop, candidates, threshold)
    ]


def balance_by_side(ranked: list[tuple[Candidate, float, bool]],
                    limit: int) -> list[Candidate]:
    """Pick a spread across sides rather than the top N overall.

    Relevance is scored against the proposition, and the proposition is
    phrased from somebody's point of view - so a straight top-N favours
    whichever side words things the way the proposition does. On the first
    live run that handed back videos that all agreed with each other, which
    is the one thing a debate map must not do.

    Round-robins the best remaining candidate from each side_hint. Relevant
    candidates go first; flagged ones only fill leftover slots.
    """
    buckets: dict[str, list[Candidate]] = {}
    for cand, _score, ok in ranked:
        if ok:
            buckets.setdefault(cand.side_hint or "unsorted", []).append(cand)

    picked: list[Candidate] = []
    while len(picked) < limit and any(buckets.values()):
        for key in list(buckets):
            if not buckets[key]:
                continue
            picked.append(buckets[key].pop(0))
            if len(picked) >= limit:
                break

    if len(picked) < limit:
        chosen = {c.video_id for c in picked}
        for cand, _score, _ok in ranked:
            if cand.video_id not in chosen:
                picked.append(cand)
                chosen.add(cand.video_id)
                if len(picked) >= limit:
                    break
    return picked[:limit]


# ------------------------------------------------- contamination guards

ECHO_THRESHOLD = 0.92


def drop_proposition_echo(claims: list[Claim], prop: Proposition,
                          threshold: float = ECHO_THRESHOLD) -> list[Claim]:
    """Remove claims that are just the proposition handed back.

    The proposition sits in the extraction prompt, and models will happily
    return it as a finding. On the first live run "The Bible's depiction of
    human ownership ... is consistently condemnatory of slavery" came back as
    a load-bearing claim - it is the question, not an answer to it.
    """
    if not claims or not prop.statement:
        return claims
    target = oc.embed(prop.statement)
    if not target:
        needle = words_of(prop.statement)
        return [c for c in claims if word_overlap(words_of(c.text), needle) < 0.85]
    kept: list[Claim] = []
    for c in claims:
        vec = oc.embed(c.text)
        if vec and oc.cosine(vec, target) >= threshold:
            continue
        kept.append(c)
    return kept
