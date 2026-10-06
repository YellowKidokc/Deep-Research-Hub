#!/usr/bin/env python3
"""
χ Justice–Mercy Diagnostic Engine
=================================

Private research instrument for claim/text evaluation.

Purpose
-------
This script is NOT a truth oracle. It produces a structured diagnostic report
for coherence/discoherence, justice/mercy balance, fruit/anti-fruit output,
evidence pressure, claim maturity, and failure modes.

It is designed as the orchestrator layer for the scripts David already built:
- intake classification / ten-law detection
- claim extraction and paper proof grading
- 7Q forward/reverse rigor gates
- Fruits / emotion profile
- χ coherence scoring
- truth-measurement anchors
- formal/Lean status detection
- heartbeat visualization

It runs standalone with only the Python standard library. If a compatible
fruits_scorer*.py file is present beside it, it will use it as an optional
secondary fruit/coherence signal.

Usage
-----
python chi_jm_diagnostic_engine.py --input paper.md --out ./out
python chi_jm_diagnostic_engine.py --input ./folder --out ./out --recursive
python chi_jm_diagnostic_engine.py --input transcript.txt --out ./out --heartbeat unit=sentence

Outputs
-------
- report.html
- full_report.json
- claims.csv
- heartbeat.csv
- entities.csv
- scores.csv
- engine_manifest.json
- research_architecture diagnostics inside full_report.json/report.html

Core posture
------------
Lean/Formal layer proves formal claims when available.
Domain evidence tests interpretation.
This engine only diagnoses structure, pressure, risk, and repair paths.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import html
import importlib.util
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ENGINE_VERSION = "0.4.0-gold-layers"

# ---------------------------------------------------------------------------
# Regex and lexical resources
# ---------------------------------------------------------------------------

PARA_SPLIT_RE = re.compile(r"\n\s*\n+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“‘])")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-']+|[χΧΩΣΘΛΨΦ][\w_]*")
HTML_TAG_RE = re.compile(r"(?s)<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style).*?>.*?</\1>")

CLAIM_MARKERS = re.compile(
    r"\b("
    r"claim|therefore|thus|shows|demonstrates|proves|predicts|requires|implies|"
    r"falsif|testable|observable|measure|evidence|model|equation|theorem|axiom|"
    r"corresponds|analogous|because|if\b.+\bthen|isomorphic|derives|means|"
    r"must|cannot|can not|only if|so that|result|conclusion"
    r")\b",
    re.IGNORECASE,
)

EVIDENCE_MARKERS = {
    "data", "dataset", "measurement", "measured", "experiment", "experimental",
    "observation", "observed", "citation", "source", "reference", "figure", "table",
    "test", "prediction", "empirical", "study", "replication", "reproducible",
    "sigma", "p-value", "p value", "confidence", "sample", "n=", "peer-reviewed",
}

BOUNDARY_MARKERS = {
    "not claim", "does not prove", "not prove", "not saying", "analogy", "metaphor",
    "framework", "model", "hypothesis", "boundary", "limited", "scope", "caveat",
    "contested", "candidate", "speculative", "interpretation", "under this framework",
    "within the model", "does not by itself", "not established", "source needed",
}

KILL_MARKERS = {
    "falsif", "kill condition", "would fail", "fails if", "refuted", "disconfirm",
    "counterexample", "invalid", "wrong if", "breaks if", "death condition", "null result",
}

OVERCLAIM_MARKERS = {
    "proves", "proven", "proof that", "undeniable", "certainly", "obviously",
    "without question", "settles", "final", "irrefutable", "impossible to deny",
    "must be true", "zero escape", "every", "always", "never", "exactly", "identity",
    "not metaphor", "mathematically identical", "revolutionary", "cannot be challenged",
}

HEDGE_MARKERS = {
    "may", "might", "could", "suggests", "appears", "arguably", "candidate",
    "provisional", "hypothesis", "conjecture", "requires more", "contested", "limited",
    "under review", "uncertain", "not yet", "further work", "needs", "source needed",
}

FEAR_PRESSURE = {
    "danger", "threat", "collapse", "destroy", "catastrophe", "crisis", "enemy",
    "adversary", "attack", "war", "poison", "invasion", "evil people", "they want",
    "hidden", "secret", "cover-up", "traitor", "eliminate", "annihilate",
}

REPAIR_TERMS = {
    "repair", "restore", "restoration", "heal", "reconcile", "reconciliation",
    "forgive", "forgiveness", "redeem", "redemption", "grace", "mercy", "compassion",
    "humility", "revise", "correct", "self-correct", "learn", "update", "repent",
    "non-terminal", "path forward", "rebuild", "renew", "dignity", "human-reviewed",
}

JUSTICE_TERMS = {
    "justice", "judgment", "accountability", "consequence", "record", "debt", "cost",
    "truth", "evidence", "source", "boundary", "measure", "definition", "precise",
    "falsification", "kill", "responsibility", "what is due", "owed", "violation",
}

COHERENCE_TERMS = {
    "coherence", "coherent", "integrate", "integration", "consistent", "consistency",
    "alignment", "structure", "structural", "foundation", "ground", "grounding",
    "mechanism", "bridge", "domain", "isomorphism", "invariant", "preserve", "signal",
    "logos", "order", "stability", "stable", "unify", "whole", "phase", "pattern",
}

DISCOHERENCE_TERMS = {
    "contradiction", "contradict", "incoherent", "fragment", "fragmentation", "noise",
    "distortion", "deception", "lie", "collapse", "decay", "entropy", "drift", "closed loop",
    "unfalsifiable", "totalizing", "ad hoc", "circular", "smuggle", "unsupported",
}

FRUIT_POSITIVE = {
    "love", "joy", "peace", "patience", "kindness", "goodness", "faithfulness",
    "gentleness", "self-control", "hope", "grace", "humility", "unity", "truth",
    "care", "restore", "forgive", "cooperate", "dignity", "mercy", "repair",
}

ANTI_FRUIT = {
    "hatred", "despair", "anxiety", "impatience", "cruelty", "corruption",
    "betrayal", "harshness", "addiction", "rage", "domination", "coercion",
    "dehumanization", "panic", "scapegoat", "manipulate", "contempt",
}

FORMAL_MARKERS = {
    "lean", "lean4", "lake build", "theorem", "lemma", "qed", "proof", "formal",
    "axiom", "∀", "∃", "→", "↔", "∧", "∨", "¬", "sorry", "admit", "kernel",
    "compiled", "machine-checked", "verified", "verification",
}

ENTITY_STOPWORDS = {
    "The", "This", "That", "These", "Those", "When", "Where", "What", "Why", "How",
    "If", "Then", "Because", "Before", "After", "Part", "Section", "Chapter", "Paper",
}

DOMAIN_KEYWORDS: Dict[str, set[str]] = {
    "physics": {"physics", "quantum", "field", "entropy", "thermodynamic", "relativity", "gravity", "mass", "energy", "wave", "particle", "measurement", "tensor", "lagrangian", "hubble", "cosmological", "maxwell", "shannon"},
    "theology": {"god", "christ", "jesus", "spirit", "grace", "sin", "salvation", "cross", "resurrection", "trinity", "logos", "scripture", "biblical", "theism", "mercy"},
    "epistemology": {"truth", "knowledge", "axiom", "foundation", "ground", "munchhausen", "circular", "regress", "assumption", "method", "falsifiability", "prediction"},
    "morality": {"good", "evil", "justice", "moral", "ought", "obligation", "duty", "virtue", "vice", "consequence", "accountability"},
    "consciousness": {"consciousness", "observer", "experience", "qualia", "mind", "cognition", "brain", "neural", "subjective", "perception"},
    "information": {"information", "signal", "noise", "channel", "compression", "entropy", "shannon", "code", "encoding", "transmission", "fidelity"},
    "history": {"historical", "century", "ancient", "document", "transmission", "source", "record", "dated", "event", "timeline"},
    "psychology": {"behavior", "addiction", "habit", "willpower", "therapy", "CBT", "emotion", "anxiety", "trauma", "identity"},
    "sociology": {"society", "institution", "civilization", "culture", "community", "political", "social", "collapse", "family"},
    "formal_math": {"equation", "theorem", "proof", "formal", "lean", "operator", "function", "variable", "matrix", "score", "model"},
}

LAW_KEYWORDS: Dict[str, set[str]] = {
    "L1_Gravity_Grace": {"gravity", "curvature", "spacetime", "mass", "grace", "draw", "attract", "geodesic"},
    "L2_Motion_Will": {"motion", "force", "will", "repentance", "conversion", "momentum", "acceleration"},
    "L3_EM_Truth": {"electromagnetic", "maxwell", "light", "truth", "deception", "witness", "signal"},
    "L4_StrongForce_Love": {"strong force", "quark", "binding", "love", "covenant", "confinement"},
    "L5_Thermo_JusticeMercy": {"entropy", "thermodynamic", "justice", "mercy", "judgment", "free energy", "decay"},
    "L6_Info_Logos": {"information", "shannon", "channel", "logos", "word", "noise", "capacity"},
    "L7_Quantum_Faith": {"quantum", "collapse", "superposition", "measurement", "faith", "observer", "doubt"},
    "L8_Relativity_Relationship": {"relativity", "frame", "lorentz", "relationship", "reference", "invariant"},
    "L9_WeakForce_SinDecay": {"weak force", "decay", "parity", "atonement", "moral conservation", "irreversible"},
    "L10_Coherence_Christ": {"coherence", "christ", "integration", "shalom", "kingdom", "master equation"},
}



# ---------------------------------------------------------------------------
# Optional lexicon workbook support
# ---------------------------------------------------------------------------

ACTIVE_LEXICON: Optional["LexiconStore"] = None
LEXICON_POLICY = "merge"  # merge | replace

@dataclass
class SemanticTerm:
    term: str
    bucket: str
    subbucket: str = ""
    polarity: str = "neutral"
    weight: float = 1.0
    danger_level: str = "low"


@dataclass
class LexiconStore:
    """Loads David's master lexicon workbook and makes it the naming source.

    The engine remains usable without this file. When supplied with --lexicon,
    workbook categories drive law names, semantic buckets, fruit/anti-fruit terms,
    evidence terms, claim-strength terms, and reviewer-risk terms.
    """
    path: str
    loaded: bool = False
    policy: str = "merge"
    warnings: List[str] = field(default_factory=list)
    simple: Dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    keyed: Dict[str, Dict[str, set[str]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    semantic_terms: List[SemanticTerm] = field(default_factory=list)
    semantic_buckets: Dict[str, List[SemanticTerm]] = field(default_factory=lambda: defaultdict(list))
    sheet_names: List[str] = field(default_factory=list)

    @classmethod
    def from_xlsx(cls, path: Path, policy: str = "merge") -> "LexiconStore":
        store = cls(path=str(path), policy=policy)
        try:
            from openpyxl import load_workbook  # optional dependency; only required for --lexicon .xlsx
        except Exception as exc:
            store.warnings.append(f"openpyxl unavailable; lexicon not loaded: {exc}")
            return store
        if not path.exists():
            store.warnings.append(f"lexicon file not found: {path}")
            return store
        try:
            wb = load_workbook(path, read_only=True, data_only=True)
            store.sheet_names = list(wb.sheetnames)
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                rows = list(ws.iter_rows(values_only=True))
                if not rows:
                    continue
                headers = [str(h).strip() if h is not None else "" for h in rows[0]]
                hmap = {h: i for i, h in enumerate(headers) if h}
                def cell(row, key, default=None):
                    idx = hmap.get(key)
                    if idx is None or idx >= len(row):
                        return default
                    return row[idx]
                for row in rows[1:]:
                    if row is None or not any(v is not None and str(v).strip() for v in row):
                        continue
                    collection = str(cell(row, "collection", sheet_name) or sheet_name).strip()
                    # SEMANTIC_BUCKETS has its own canonical schema.
                    if sheet_name == "SEMANTIC_BUCKETS" and "term" in hmap and "bucket" in hmap:
                        term = str(cell(row, "term", "") or "").strip()
                        bucket = str(cell(row, "bucket", "") or "").strip()
                        if not term or not bucket:
                            continue
                        try:
                            weight = float(cell(row, "weight", 1) or 1)
                        except Exception:
                            weight = 1.0
                        st = SemanticTerm(
                            term=term,
                            bucket=bucket,
                            subbucket=str(cell(row, "subbucket", "") or "").strip(),
                            polarity=str(cell(row, "polarity", "neutral") or "neutral").strip(),
                            weight=weight,
                            danger_level=str(cell(row, "danger_level", "low") or "low").strip(),
                        )
                        store.semantic_terms.append(st)
                        store.semantic_buckets[bucket].append(st)
                        store.simple[bucket].add(term)
                        store.simple["SEMANTIC_BUCKETS_ALL"].add(term)
                        continue

                    # Simple term sheets: source_file, collection, item_index, term.
                    if "term" in hmap and "item_index" in hmap:
                        term = str(cell(row, "term", "") or "").strip()
                        if term:
                            store.simple[collection].add(term)
                        continue

                    # Key/value sheets: source_file, collection, key, subkey, item_index, value.
                    if "key" in hmap and "value" in hmap:
                        key = str(cell(row, "key", "") or "").strip()
                        value = cell(row, "value", "")
                        subkey = str(cell(row, "subkey", "") or "").strip()
                        value_str = str(value or "").strip()
                        # COHERENCE_TERMS stores term in key and weight in value.
                        if sheet_name == "COHERENCE_TERMS":
                            if key:
                                store.simple[collection].add(key)
                            continue
                        if key and value_str:
                            compound_key = f"{key}.{subkey}" if subkey else key
                            store.keyed[collection][compound_key].add(value_str)
                            store.keyed[collection][key].add(value_str)
                            store.simple[collection].add(value_str)
                        elif key:
                            store.simple[collection].add(key)
                        continue
            store.loaded = True
        except Exception as exc:
            store.warnings.append(f"failed loading lexicon workbook: {exc}")
        return store

    def terms(self, collection: str) -> set[str]:
        return set(self.simple.get(collection, set()))

    def keyed_terms(self, collection: str) -> Dict[str, set[str]]:
        return {k: set(v) for k, v in self.keyed.get(collection, {}).items()}

    def semantic_hits(self, text: str) -> List[SemanticTerm]:
        if not self.loaded or not self.semantic_terms:
            return []
        low = text.lower()
        tokset = set(tokens(text))
        hits: List[SemanticTerm] = []
        for st in self.semantic_terms:
            term = st.term.lower().strip()
            if not term:
                continue
            if (" " in term and term in low) or (" " not in term and term in tokset):
                hits.append(st)
        return hits

    def semantic_bucket_scores(self, text: str) -> Dict[str, float]:
        hits = self.semantic_hits(text)
        totals: Dict[str, float] = defaultdict(float)
        for h in hits:
            danger_boost = {"low": 1.0, "medium": 1.15, "high": 1.35, "critical": 1.65}.get(h.danger_level.lower(), 1.0)
            totals[h.bucket] += max(0.25, h.weight) * danger_boost
        # 12 weighted points is treated as bucket saturation.
        return {bucket: pct((val / 12.0) * 100.0) for bucket, val in totals.items()}


def _active_terms(collection: str, fallback: Iterable[str] = ()) -> set[str]:
    base = set(fallback)
    if ACTIVE_LEXICON and ACTIVE_LEXICON.loaded:
        found = ACTIVE_LEXICON.terms(collection)
        if found and ACTIVE_LEXICON.policy == "replace":
            return found
        return base | found
    return base


def _active_terms_multi(collections: Iterable[str], fallback: Iterable[str] = ()) -> set[str]:
    out = set(fallback)
    for c in collections:
        out |= _active_terms(c, set())
    return out


def _active_keyed(collection: str, fallback: Dict[str, set[str]]) -> Dict[str, set[str]]:
    if ACTIVE_LEXICON and ACTIVE_LEXICON.loaded:
        found = ACTIVE_LEXICON.keyed_terms(collection)
        if found and ACTIVE_LEXICON.policy == "replace":
            return found
        merged = {k: set(v) for k, v in fallback.items()}
        for k, vals in found.items():
            merged.setdefault(k, set()).update(vals)
        return merged
    return fallback


def semantic_bucket_scores(text: str) -> Dict[str, float]:
    if ACTIVE_LEXICON and ACTIVE_LEXICON.loaded:
        return ACTIVE_LEXICON.semantic_bucket_scores(text)
    return {}


def semantic_hit_labels(text: str, max_hits: int = 40) -> List[str]:
    if not ACTIVE_LEXICON or not ACTIVE_LEXICON.loaded:
        return []
    hits = ACTIVE_LEXICON.semantic_hits(text)
    labels = [f"{h.bucket}:{h.subbucket}:{h.term}" for h in hits[:max_hits]]
    return labels


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SegmentScore:
    coherence: float
    discoherence: float
    justice: float
    mercy: float
    justice_mercy_balance: float
    fruit: float
    anti_fruit: float
    evidence: float
    boundary: float
    falsifiability: float
    formal: float
    overclaim_risk: float
    fear_pressure: float
    truth_pressure: float
    classification: str


@dataclass
class SegmentRecord:
    doc_id: str
    unit_id: str
    unit_type: str
    index: int
    text: str
    score: SegmentScore
    marker_hits: Dict[str, List[str]] = field(default_factory=dict)
    semantic_buckets: Dict[str, float] = field(default_factory=dict)


@dataclass
class ClaimRecord:
    claim_id: str
    doc_id: str
    section: str
    claim_text: str
    claim_type: str
    domains: Dict[str, float]
    law_hits: Dict[str, float]
    semantic_buckets: Dict[str, float]
    seven_q: Dict[str, str]
    reverse_tests: Dict[str, str]
    score: SegmentScore
    entities: List[str]
    evidence_markers: List[str]
    boundary_markers: List[str]
    kill_markers: List[str]
    risky_terms: List[str]
    suggested_repair: str
    verdict: str


@dataclass
class DocumentReport:
    engine_version: str
    generated_at: str
    input_path: str
    doc_id: str
    title: str
    inferred_thesis: str
    overall_scores: Dict[str, float]
    overall_verdict: str
    domains: Dict[str, float]
    laws: Dict[str, float]
    claims: List[ClaimRecord]
    heartbeat: List[SegmentRecord]
    entities: List[Dict[str, Any]]
    architecture: Dict[str, Any]
    methodology: Dict[str, Any]

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    try:
        if math.isnan(x):
            return lo
    except TypeError:
        return lo
    return max(lo, min(hi, float(x)))


def pct(x: float) -> float:
    return round(clamp(x), 2)


def norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def tokens(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


def hash_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def read_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        raw = SCRIPT_STYLE_RE.sub(" ", raw)
        raw = re.sub(r"(?is)<title.*?>(.*?)</title>", r"\n# \1\n", raw)
        raw = re.sub(r"(?is)</(p|div|section|article|li|h[1-6]|tr)>", "\n", raw)
        raw = HTML_TAG_RE.sub(" ", raw)
        raw = html.unescape(raw)
    return re.sub(r"\n{3,}", "\n\n", raw.replace("\r\n", "\n").replace("\r", "\n")).strip()


def iter_input_files(input_path: Path, recursive: bool = False) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    exts = {".md", ".txt", ".html", ".htm"}
    globber = input_path.rglob("*") if recursive else input_path.glob("*")
    return sorted([p for p in globber if p.is_file() and p.suffix.lower() in exts])


def split_paragraphs(text: str) -> List[str]:
    parts = [norm_text(p) for p in PARA_SPLIT_RE.split(text) if norm_text(p)]
    return [p for p in parts if len(p.split()) >= 8]


def split_sentences(text: str) -> List[str]:
    # Keep simple and robust; paragraph split first reduces bad splits.
    out: List[str] = []
    for para in split_paragraphs(text):
        parts = [norm_text(p) for p in SENTENCE_SPLIT_RE.split(para) if norm_text(p)]
        for part in parts:
            if 20 <= len(part) <= 1500:
                out.append(part)
    return out


def marker_hits(text: str, marker_set: Iterable[str]) -> List[str]:
    low = text.lower()
    hits = []
    for m in marker_set:
        if m.lower() in low:
            hits.append(m)
    return sorted(set(hits))


def marker_score(text: str, marker_set: Iterable[str], cap: int = 8) -> float:
    hits = marker_hits(text, marker_set)
    return clamp((len(hits) / max(1, cap)) * 100.0)


def density_score(text: str, marker_set: Iterable[str], cap: int = 8) -> float:
    low_toks = set(tokens(text))
    hits = [m for m in marker_set if len(m.split()) == 1 and m.lower() in low_toks]
    # Include phrase markers.
    hits += [m for m in marker_set if len(m.split()) > 1 and m.lower() in text.lower()]
    return clamp((len(set(hits)) / max(1, cap)) * 100.0)


def geometric_mean(values: Iterable[float]) -> float:
    vals = [clamp(v, 0.0, 100.0) / 100.0 for v in values]
    if not vals:
        return 0.0
    prod = 1.0
    for v in vals:
        prod *= max(0.001, v)
    return clamp((prod ** (1.0 / len(vals))) * 100.0)

# ---------------------------------------------------------------------------
# Optional existing scorer adapter
# ---------------------------------------------------------------------------

class OptionalFruitsAdapter:
    """Dynamically loads fruits_scorer*.py if present; otherwise no-ops."""

    def __init__(self, base_dir: Path):
        self.available = False
        self.module = None
        self.path = None
        for candidate in sorted(base_dir.glob("fruits_scorer*.py")):
            try:
                spec = importlib.util.spec_from_file_location("optional_fruits_scorer", candidate)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)  # type: ignore[union-attr]
                    if hasattr(mod, "analyze_theory_fruits"):
                        self.module = mod
                        self.path = candidate
                        self.available = True
                        break
            except Exception:
                continue

    def score(self, text: str, doc_id: str) -> Optional[Dict[str, Any]]:
        if not self.available or self.module is None:
            return None
        try:
            analysis = self.module.analyze_theory_fruits(text, doc_id)
            return {
                "total_score": getattr(analysis, "total_score", None),
                "normalized_score": getattr(analysis, "normalized_score", None),
                "grade": getattr(analysis, "grade", None),
                "interpretation": getattr(analysis, "interpretation", None),
                "word_count": getattr(analysis, "word_count", None),
            }
        except Exception as exc:
            return {"error": str(exc)}

# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def classify_score(s: SegmentScore) -> str:
    if s.overclaim_risk >= 70 and s.evidence < 35:
        return "high_signal_or_overclaim_risk"
    if s.coherence >= 76 and s.justice_mercy_balance >= 70 and s.discoherence <= 35:
        return "high_coherence"
    if s.discoherence >= 70:
        return "discoherent_or_manipulative"
    if s.justice - s.mercy >= 35:
        return "justice_heavy_mercy_poor"
    if s.mercy - s.justice >= 35:
        return "mercy_heavy_justice_poor"
    if s.truth_pressure >= 65:
        return "partial_high_signal"
    if s.truth_pressure >= 45:
        return "fragile_or_needs_support"
    return "preserve_as_signal_or_reject_form"


def score_text_unit(text: str) -> SegmentScore:
    # Primary dimensions. If a lexicon workbook is loaded, it becomes the naming source.
    evidence_terms = _active_terms("EVIDENCE_TERMS", EVIDENCE_MARKERS)
    boundary_terms = _active_terms_multi(["BOUNDARY_TERMS", "METHODS_PROVENANCE", "PREFERRED_REPLACEMENT"], BOUNDARY_MARKERS)
    kill_terms = _active_terms_multi(["FALSIFY_TERMS", "FALSIFICATION"], KILL_MARKERS)
    formal_terms = _active_terms_multi(["FORMAL_PROOF"], FORMAL_MARKERS)
    coherence_terms = _active_terms_multi(["COHERENCE_TERMS", "ME_VARS"], COHERENCE_TERMS)
    justice_terms = _active_terms_multi(["JUSTICE_TERMS"], JUSTICE_TERMS)
    mercy_terms = _active_terms_multi(["MERCY_TERMS", "REPAIR_TERMS"], REPAIR_TERMS)
    fruit_terms = _active_terms_multi(["FRUITS", "FRUITS_LEXICON", "FRUIT_BEHAVIOR_EXPANSION"], FRUIT_POSITIVE)
    anti_terms = _active_terms_multi(["ANTI_FRUITS_LEXICON", "ANTI_FRUITS", "ANTI_FRUIT_BEHAVIOR_EXPANSION"], ANTI_FRUIT)
    overclaim_terms = _active_terms_multi(["ABSOLUTE_TERMS", "DANGER_LANGUAGE", "REVIEWER_RISK"], OVERCLAIM_MARKERS)
    disco_terms_set = _active_terms_multi(["DISCOHERENCE_TERMS", "DRIFT_WARNING", "NEGATION_TERMS"], DISCOHERENCE_TERMS)

    evidence = density_score(text, evidence_terms, cap=7)
    boundary = marker_score(text, boundary_terms, cap=5)
    falsifiability = marker_score(text, kill_terms, cap=3)
    formal = density_score(text, formal_terms, cap=5)
    coherence_base = density_score(text, coherence_terms, cap=8)
    justice = density_score(text, justice_terms, cap=7)
    mercy = density_score(text, mercy_terms, cap=7)
    fruit = density_score(text, fruit_terms, cap=6)
    anti_fruit = density_score(text, anti_terms, cap=5)

    # Workbook semantic buckets are treated as a second diagnostic panel.
    buckets = semantic_bucket_scores(text)
    evidence = max(evidence, buckets.get("EVIDENCE_MATURITY", 0.0))
    falsifiability = max(falsifiability, buckets.get("FALSIFICATION", 0.0))
    formal = max(formal, buckets.get("FORMAL_PROOF", 0.0))
    fruit = max(fruit, buckets.get("FRUIT_BEHAVIOR_EXPANSION", 0.0))
    anti_fruit = max(anti_fruit, buckets.get("ANTI_FRUIT_BEHAVIOR_EXPANSION", 0.0))

    # Negative/risk dimensions.
    disco_terms = density_score(text, disco_terms_set, cap=6)
    overclaim_risk = marker_score(text, overclaim_terms, cap=5)
    fear_pressure = density_score(text, FEAR_PRESSURE, cap=5)
    reviewer_risk = max(buckets.get("REVIEWER_RISK", 0.0), buckets.get("DANGER_LANGUAGE", 0.0))
    claim_strength_risk = buckets.get("CLAIM_STRENGTH", 0.0)

    # Boundaries reduce risk; evidence also reduces raw overclaim penalty.
    adjusted_risk = clamp(
        (overclaim_risk * 0.55 + fear_pressure * 0.22 + disco_terms * 0.32 + reviewer_risk * 0.45 + claim_strength_risk * 0.18)
        - (boundary * 0.25 + evidence * 0.15 + formal * 0.10)
    )
    discoherence = clamp(disco_terms * 0.42 + adjusted_risk * 0.43 + anti_fruit * 0.20)

    # Justice/mercy balance: high when both are present, low when one dominates or both absent.
    jm_balance = clamp(100.0 - abs(justice - mercy))
    jm_presence = geometric_mean([justice + 5, mercy + 5])
    jm_balance = clamp((jm_balance * 0.65) + (jm_presence * 0.35))

    # Coherence rewards mechanism, evidence, boundary, fruit, justice/mercy; penalizes risk.
    coherence = clamp(
        0.27 * coherence_base
        + 0.18 * evidence
        + 0.13 * boundary
        + 0.13 * formal
        + 0.16 * jm_balance
        + 0.13 * fruit
        - 0.22 * adjusted_risk
        + 18.0
    )

    # Truth pressure is not final truth; it is structured signal pressure.
    truth_pressure = clamp(
        0.28 * coherence
        + 0.18 * justice
        + 0.14 * mercy
        + 0.16 * evidence
        + 0.08 * falsifiability
        + 0.08 * boundary
        + 0.08 * formal
        + 0.12 * fruit
        - 0.22 * adjusted_risk
    )

    temp = SegmentScore(
        coherence=pct(coherence),
        discoherence=pct(discoherence),
        justice=pct(justice),
        mercy=pct(mercy),
        justice_mercy_balance=pct(jm_balance),
        fruit=pct(fruit),
        anti_fruit=pct(anti_fruit),
        evidence=pct(evidence),
        boundary=pct(boundary),
        falsifiability=pct(falsifiability),
        formal=pct(formal),
        overclaim_risk=pct(adjusted_risk),
        fear_pressure=pct(fear_pressure),
        truth_pressure=pct(truth_pressure),
        classification="",
    )
    temp.classification = classify_score(temp)
    return temp

def classify_domains(text: str) -> Dict[str, float]:
    low_toks = set(tokens(text))
    scores: Dict[str, float] = {}
    for domain, kws in DOMAIN_KEYWORDS.items():
        count = sum(1 for kw in kws if (kw in low_toks or kw in text.lower()))
        if count:
            scores[domain] = pct((count / min(len(kws), 8)) * 100)
    return dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))


def classify_laws(text: str) -> Dict[str, float]:
    low = text.lower()
    scores = {}
    law_keywords = _active_keyed("LAW_KEYWORDS", LAW_KEYWORDS)
    for law, kws in law_keywords.items():
        count = sum(1 for kw in kws if kw in low)
        if count:
            scores[law] = pct((count / min(len(kws), 5)) * 100)
    return dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))


def claim_type(text: str) -> str:
    domains = classify_domains(text)
    types = []
    if domains.get("formal_math", 0) or marker_hits(text, FORMAL_MARKERS):
        types.append("formal")
    if domains.get("physics", 0) or domains.get("information", 0):
        types.append("scientific")
    if domains.get("theology", 0):
        types.append("theological")
    if domains.get("morality", 0):
        types.append("moral")
    if domains.get("history", 0):
        types.append("historical")
    if marker_hits(text, HEDGE_MARKERS):
        types.append("speculative")
    if not types:
        return "mixed"
    return "mixed:" + "+".join(sorted(set(types))) if len(set(types)) > 1 else types[0]


def seven_q(text: str) -> Dict[str, str]:
    lower = text.lower()
    return {
        "Q1_identity": "clear" if re.search(r"\b(is|are|equals|means|defined as|called)\b", lower) else "implicit",
        "Q2_scope": "bounded" if re.search(r"\b(if|when|under|within|in this|according to|as used here)\b", lower) else "broad",
        "Q3_mechanism": "present" if re.search(r"\b(because|through|by|via|mechanism|operator|field|equation|function|causes)\b", lower) else "missing",
        "Q4_evidence": "present" if marker_hits(text, EVIDENCE_MARKERS) else "missing",
        "Q5_falsifiability": "present" if marker_hits(text, KILL_MARKERS) or "predict" in lower else "missing",
        "Q6_boundary": "present" if marker_hits(text, BOUNDARY_MARKERS) else "missing",
        "Q7_listener_risk": "high" if marker_hits(text, OVERCLAIM_MARKERS) and not marker_hits(text, BOUNDARY_MARKERS) else "normal",
    }


def reverse_tests(text: str, score: SegmentScore) -> Dict[str, str]:
    return {
        "R1_self_refutation": "watch" if "contradict" in text.lower() or score.discoherence > 65 else "not_detected",
        "R2_infinite_regress": "watch" if "regress" in text.lower() or "turtles" in text.lower() else "not_detected",
        "R3_empirical_contradiction": "needs_evidence" if score.evidence < 25 and any(w in text.lower() for w in ["data", "confirmed", "observed", "science"]) else "not_detected",
        "R4_logical_incoherence": "watch" if "impossible" in text.lower() and score.boundary < 20 else "not_detected",
        "R5_explanatory_failure": "watch" if score.coherence < 40 else "not_detected",
        "R6_overclaim_failure": "watch" if score.overclaim_risk > 55 else "not_detected",
        "R7_mercy_justice_imbalance": "watch" if score.justice_mercy_balance < 50 else "not_detected",
    }


def suggest_repair(text: str, score: SegmentScore) -> str:
    repairs = []
    if score.evidence < 35:
        repairs.append("attach source/evidence or downgrade claim status")
    if score.boundary < 25:
        repairs.append("add boundary: what this does and does not prove")
    if score.falsifiability < 20:
        repairs.append("name a kill condition or counterexample")
    if score.overclaim_risk > 45:
        repairs.append("replace proof/always/never/exact language with scoped language")
    if score.justice - score.mercy > 35:
        repairs.append("add mercy/repair/dignity path")
    if score.mercy - score.justice > 35:
        repairs.append("add accountability/consequence/evidence path")
    if not repairs:
        return "no immediate repair required; preserve and test downstream"
    return "; ".join(repairs)


def claim_verdict(score: SegmentScore) -> str:
    if score.coherence >= 75 and score.truth_pressure >= 65 and score.overclaim_risk < 35:
        return "AUDIT_READY"
    if score.formal >= 40 and score.boundary >= 25 and score.overclaim_risk < 55:
        return "FORMALIZATION_CANDIDATE"
    if score.overclaim_risk >= 70 or score.discoherence >= 70:
        return "NEEDS_RIGOR_HIGH_RISK"
    if score.truth_pressure >= 50:
        return "PROMISING_NEEDS_SUPPORT"
    return "PRESERVE_AS_SIGNAL_OR_REWRITE"

# ---------------------------------------------------------------------------
# Research Architecture Operationalization
# ---------------------------------------------------------------------------

ARCHITECTURE_FIELDS: Dict[str, Dict[str, Any]] = {
    "signal_seed": {
        "label": "Signal / Inquiry Seed",
        "markers": [
            "research question", "guiding_question", "objective question", "why this question matters",
            "initial intuition", "premonition", "what i currently lean", "orientation", "question matters",
        ],
        "weight": 1.1,
        "why": "Captures the pre-claim truth pressure before a formal claim exists.",
    },
    "domain_jurisdiction": {
        "label": "Domain / Jurisdiction",
        "markers": [
            "domain touchpoints", "primary_domain", "classification", "scientific", "mathematical",
            "philosophical", "theological", "historical", "meta / cross-domain", "cross-domain",
            "which domains", "jurisdiction", "domain boundaries",
        ],
        "weight": 1.0,
        "why": "Prevents category mistakes by naming which domains are allowed to answer.",
    },
    "definitions": {
        "label": "Definitions / Terms",
        "markers": [
            "definitions", "definition", "term:", "symbol:", "dimensionality", "meaning:",
            "non-examples", "what it is", "what it is not", "aliases", "glossary_terms",
        ],
        "weight": 1.2,
        "why": "Turns raw language into stable objects that can be tested.",
    },
    "axioms_dependencies": {
        "label": "Axioms / Dependencies",
        "markers": [
            "axioms", "premises", "depends_on", "depends on", "prerequisites", "theory_dependencies",
            "root", "foundation", "minimal starting truths", "derived from", "constraints",
        ],
        "weight": 1.15,
        "why": "Exposes what the claim must already assume to stand.",
    },
    "formal_structure": {
        "label": "Formal Structure / Operators",
        "markers": [
            "formal structure", "field equations", "operators", "operator", "signature", "input type",
            "output type", "state acted upon", "preconditions", "postconditions", "invariants",
            "linearity", "unitarity", "locality", "symmetry", "conservation", "lagrangian",
            "variational", "math translation layer", "formal derivation",
        ],
        "weight": 1.1,
        "why": "Forces mechanisms to become operational instead of rhetorical.",
    },
    "evidence_bundles": {
        "label": "Evidence Bundles / Sources",
        "markers": [
            "evidence bundles", "core sources", "supporting sources", "further study", "source:",
            "core reference", "related_papers", "citation", "references", "dataset", "data",
        ],
        "weight": 1.05,
        "why": "Connects claims to external support rather than self-reference.",
    },
    "predictions_tests": {
        "label": "Predictions / Test Hooks",
        "markers": [
            "predictions", "testable claims", "test hooks", "falsifiable", "expected evidence",
            "verification method", "would fail", "kill condition", "what would change my mind",
            "counterexample", "falsify", "collapse it",
        ],
        "weight": 1.2,
        "why": "Names what the claim risks and how it can be corrected or killed.",
    },
    "contradictions_objections": {
        "label": "Contradictions / Objections",
        "markers": [
            "contradictions", "tensions", "objection", "steelman", "why it seems compelling",
            "reply", "gentle challenger", "strongest charitable challenge", "peripheral", "structural",
            "foundational", "conflict", "unresolved",
        ],
        "weight": 1.05,
        "why": "Turns disagreement into structure and records what survives pressure.",
    },
    "resolution_status": {
        "label": "Resolution / Status",
        "markers": [
            "provisional resolution", "what i tentatively accept", "what i reject", "what remains unresolved",
            "status", "proof_status", "canon-ready", "canonical", "review", "final", "next action",
        ],
        "weight": 0.95,
        "why": "Keeps the system from pretending every signal is already a finished conclusion.",
    },
    "traceability": {
        "label": "Traceability / Cross-Reference",
        "markers": [
            "cross-reference index", "referenced concepts", "canonical hub", "related papers",
            "evidence_bundles", "core_references", "glossary_terms", "theory_dependencies",
            "parents", "children", "related", "used by", "where it appears", "integration with papers",
        ],
        "weight": 1.0,
        "why": "Creates the architecture that links definitions → evidence → theory → papers.",
    },
}

CANON_READY_REQUIRED = [
    "signal_seed", "domain_jurisdiction", "definitions", "axioms_dependencies", "evidence_bundles",
    "predictions_tests", "contradictions_objections", "resolution_status", "traceability",
]

TEMPLATE_TYPE_MARKERS: Dict[str, List[str]] = {
    "universal_note": ["guiding_question", "ideal_outcome", "acceptable_outcome", "roadblocks", "naivety_checks"],
    "research_question": ["research question", "why this question matters", "initial intuition", "domain touchpoints"],
    "physics_math": ["field equations", "operators", "conservation rules", "lagrangian", "formal derivation"],
    "theology_metaphysics": ["scriptural foundations", "conceptual model", "ontology", "symmetries", "states"],
    "definition": ["non-examples", "used by", "aliases", "proof_status", "definition"],
    "entity": ["what it is not", "state", "capabilities", "constraints"],
    "operator": ["signature", "preconditions", "postconditions", "invariants", "algebraic"],
    "objection": ["target claim", "steelman", "why it seems compelling", "reply", "what would change my mind"],
    "paper": ["scope", "canonical axiom list", "operator/action catalog", "lemmas", "test hooks"],
    "cross_reference_footer": ["cross-reference index", "related papers", "evidence bundles", "glossary", "theory dependencies"],
    "urce": ["orientation & jurisdiction", "claim tree", "contradictions & tensions", "gentle ai challenge", "provisional resolution"],
}


def _contains_marker(text_low: str, marker: str) -> bool:
    return marker.lower() in text_low


def _marker_presence(text: str, markers: Iterable[str]) -> Tuple[float, List[str]]:
    low = text.lower()
    hits = []
    for marker in markers:
        if _contains_marker(low, marker):
            hits.append(marker)
    score = pct((len(hits) / max(1, min(len(list(markers)) if not isinstance(markers, list) else len(markers), 8))) * 100.0)
    return score, hits


def detect_template_types(text: str) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for name, markers in TEMPLATE_TYPE_MARKERS.items():
        score, _ = _marker_presence(text, markers)
        if score > 0:
            out[name] = score
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


def research_architecture_assessment(text: str, claims: List[ClaimRecord], scores: Dict[str, float]) -> Dict[str, Any]:
    """Operationalizes David's research-template questions as a diagnostics layer.

    This does not decide truth. It measures whether the text has the research architecture
    that can carry truth-testing: signal capture, domain jurisdiction, definitions,
    dependency chain, evidence, falsification, objections, resolution, and traceability.
    """
    field_results: Dict[str, Any] = {}
    weighted_total = 0.0
    weight_sum = 0.0
    missing = []
    for key, spec in ARCHITECTURE_FIELDS.items():
        presence, hits = _marker_presence(text, spec["markers"])
        # Claims can also contribute structure: if the engine found claim-level evidence/boundaries, count it.
        if key == "predictions_tests":
            claim_bonus = min(35.0, sum(1 for c in claims if c.kill_markers or c.seven_q.get("Q5_falsifiability") == "present") * 7.0)
            presence = max(presence, claim_bonus)
        elif key == "evidence_bundles":
            claim_bonus = min(35.0, sum(1 for c in claims if c.evidence_markers) * 5.0)
            presence = max(presence, claim_bonus)
        elif key == "definitions":
            claim_bonus = min(30.0, sum(1 for c in claims if c.seven_q.get("Q1_identity") == "clear") * 4.0)
            presence = max(presence, claim_bonus)
        elif key == "contradictions_objections":
            claim_bonus = min(30.0, sum(1 for c in claims if any(v == "watch" for v in c.reverse_tests.values())) * 4.0)
            presence = max(presence, claim_bonus)
        w = float(spec.get("weight", 1.0))
        weighted_total += presence * w
        weight_sum += w
        if key in CANON_READY_REQUIRED and presence < 25:
            missing.append(key)
        field_results[key] = {
            "label": spec["label"],
            "score": pct(presence),
            "hits": hits[:20],
            "why_it_matters": spec["why"],
            "status": "present" if presence >= 50 else "weak" if presence >= 25 else "missing",
        }
    architecture_score = pct(weighted_total / max(1e-9, weight_sum))
    template_types = detect_template_types(text)
    traceability_score = field_results.get("traceability", {}).get("score", 0.0)
    testability_score = field_results.get("predictions_tests", {}).get("score", 0.0)
    objection_score = field_results.get("contradictions_objections", {}).get("score", 0.0)
    canon_ready_score = pct(
        architecture_score * 0.45
        + scores.get("boundary", 0) * 0.12
        + scores.get("evidence", 0) * 0.12
        + scores.get("falsifiability", 0) * 0.12
        + traceability_score * 0.09
        + objection_score * 0.06
        + (100 - scores.get("overclaim_risk", 0)) * 0.04
    )
    if canon_ready_score >= 72 and not missing:
        verdict = "CANON_READY_CANDIDATE"
    elif architecture_score >= 55:
        verdict = "STRUCTURED_BUT_NEEDS_GAPS_FILLED"
    elif scores.get("truth_pressure", 0) >= 45:
        verdict = "PROMISING_SIGNAL_NEEDS_ARCHITECTURE"
    else:
        verdict = "PRE_CLAIM_OR_LOW_STRUCTURE"

    next_actions = []
    if "signal_seed" in missing:
        next_actions.append("add the raw research question / premonition before formalizing")
    if "domain_jurisdiction" in missing:
        next_actions.append("name which domains are allowed to answer this claim")
    if "definitions" in missing:
        next_actions.append("define key terms and add non-examples to prevent equivocation")
    if "axioms_dependencies" in missing:
        next_actions.append("list root axioms, dependencies, and prerequisites")
    if "evidence_bundles" in missing:
        next_actions.append("attach evidence bundles or downgrade to signal/hypothesis")
    if "predictions_tests" in missing:
        next_actions.append("add kill conditions, test hooks, or what would change your mind")
    if "contradictions_objections" in missing:
        next_actions.append("add a steelman objection and reply")
    if "traceability" in missing:
        next_actions.append("add cross-reference footer: papers, evidence, glossary, dependencies")
    if not next_actions:
        next_actions.append("run external/source audit; preserve as structured candidate")

    return {
        "architecture_score": architecture_score,
        "canon_ready_score": canon_ready_score,
        "verdict": verdict,
        "template_types_detected": template_types,
        "field_results": field_results,
        "missing_required_fields": missing,
        "next_actions": next_actions,
        "operationalized_from": [
            "Research Question template", "Universal Research & Contradiction Engine", "Physics/Math template",
            "Theology/Metaphysics template", "Definition/Entity/Operator/Objection/Paper templates",
            "Cross-reference footer",
        ],
        "interpretation": "Measures research architecture completeness, not truth.",
    }



# ---------------------------------------------------------------------------
# V4 Gold Layers: Coherence Signature, Canonical Identity, Axiom Wiring,
# Isomorphism, No-Drift, Evidence Tiering, Objection Taxonomy, Deployment
# ---------------------------------------------------------------------------

COHERENCE_POSITIVE_SIGNALS: Dict[str, List[str]] = {
    "cross_domain_convergence": ["cross-domain", "multiple domains", "converge", "convergence", "same structure", "same pattern", "same destination"],
    "compression": ["compress", "compression", "fewer principles", "explains more", "unified", "one equation", "theoretical floor", "parsimony"],
    "loop_closure": ["loop closure", "closes the loop", "clarifies the premise", "explains why", "grounding", "root directory"],
    "bidirectional_translation": ["bidirectional", "both directions", "science to god", "god to science", "maps both ways", "translation"],
    "prediction_constraint": ["prediction", "predicts", "constraint", "test hook", "falsifiable", "would fail", "kill condition"],
    "pressure_simplification": ["under pressure", "stress-tested", "reverse test", "survived", "simplifies", "not more complex"],
    "information_density": ["information density", "signal persistence", "channel capacity", "shannon", "compression ratio"],
    "substitution_resistance": ["wrong substitution", "false positive", "adversarial", "nearby wrong", "rejected", "resistance to arbitrary substitution"],
    "independent_emergence": ["independent", "separate", "operationally independent", "multiple models", "no shared conversation state"],
    "downstream_fruitfulness": ["downstream", "fruitful", "new problem", "solves", "generates", "enables", "application"],
}

COHERENCE_RED_FLAGS: Dict[str, List[str]] = {
    "word_association": ["sounds like", "reminds me", "vibes", "association", "wordplay", "semantic similarity"],
    "metaphor_without_test": ["metaphor", "analogy", "like", "as if", "illustrates", "poetic"],
    "domain_leakage": ["science proves god", "physics proves theology", "standard physics says", "theology proves physics"],
    "unfalsifiable_inflation": ["cannot be disproven", "explains everything", "no matter what", "all outcomes", "unfalsifiable"],
    "ad_hoc_rescue": ["unless we redefine", "special case", "exception", "rescue", "patch"],
    "overfitted_symbolism": ["number symbolism", "hidden code", "secret pattern", "exactly because it matches"],
    "emotion_low_constraint": ["devastating", "destroy", "annihilates", "obvious", "nonsense", "fraud"],
    "vague_universality": ["all", "every", "always", "never", "universal", "total", "zero escape"],
    "authority_substitution": ["because ai said", "because experts", "because scripture says"],
    "terminology_hides_contradiction": ["same word", "different meaning", "equivocation", "relabel", "renaming"],
}

AXIOM_WIRING_GRID: Dict[str, Dict[str, List[str]]] = {
    "A": {"label": "Base axiom / starting claim", "markers": ["axiom", "root", "ground", "starting claim", "foundation", "premise"]},
    "AT": {"label": "Truth condition", "markers": ["true if", "false if", "truth condition", "verification", "valid if", "would be wrong"]},
    "AS": {"label": "Structure / system relation", "markers": ["structure", "system", "relation", "operator", "field", "mechanism", "maps"]},
    "AE": {"label": "Evidence relation", "markers": ["evidence", "source", "data", "citation", "observed", "measurement", "study"]},
    "AQ": {"label": "Question pressure", "markers": ["question", "why", "problem", "ambiguity", "pressure", "what this answers"]},
    "AP": {"label": "Prediction / payoff", "markers": ["predict", "testable", "operational payoff", "consequence", "therefore", "follows"]},
    "AC": {"label": "Contradiction / coherence test", "markers": ["contradiction", "objection", "counterexample", "kill condition", "fails if", "reverse test"]},
    "AI": {"label": "Integration result", "markers": ["integrates", "integration", "unifies", "converges", "fits into", "larger framework"]},
}

OBJECTION_TAXONOMY_MARKERS: Dict[str, List[str]] = {
    "peripheral_tension": ["minor", "peripheral", "edge case", "not load-bearing", "tension"],
    "structural_contradiction": ["structural contradiction", "internal contradiction", "contradicts", "inconsistent"],
    "foundational_contradiction": ["foundation fails", "root fails", "axiom fails", "foundational", "self-refuting"],
    "category_error": ["category error", "wrong category", "wrong kind", "domain mismatch"],
    "equivocation": ["equivocation", "same word", "shifting definition", "changes meaning"],
    "isomorphism_failure": ["isomorphism failure", "analogy only", "not preserved", "mapping fails"],
    "evidence_insufficiency": ["insufficient evidence", "needs source", "unsupported", "weak evidence", "unverified"],
    "domain_boundary_violation": ["domain boundary", "outside scope", "overreach", "not standard physics", "not standard theology"],
    "moral_theological_pressure": ["problem of evil", "suffering", "justice", "mercy", "moral pressure", "theological pressure"],
    "public_comprehension_failure": ["misread", "misunderstood", "public risk", "sounds like", "reader may think"],
}

EVIDENCE_TIER_MARKERS: Dict[str, List[str]] = {
    "tier_1": ["primary source", "direct text", "direct observation", "reproducible", "formal proof", "lean", "lake build", "dataset", "citation", "measurement"],
    "tier_2": ["secondary", "review", "synthesis", "replicated", "academic", "peer-reviewed", "established interpretation", "meta-analysis"],
    "tier_3": ["speculative", "analogy", "conversation", "intuition", "premonition", "hypothesis", "candidate", "early signal"],
}

DEPLOYMENT_MARKERS: Dict[str, List[str]] = {
    "hook": ["here is", "the question", "what if", "nobody", "the simplest", "the problem", "watch what happens"],
    "single_claim": ["one claim", "this paper argues", "the claim", "in one sentence", "core claim"],
    "objection_ready": ["objection", "critic", "steelman", "the strongest counter", "someone will say"],
    "source_backup": ["source", "evidence", "citation", "data", "study", "reference"],
    "followup": ["next", "follow-up", "part two", "see also", "related", "appendix"],
}


def _hit_dict(text: str, spec: Dict[str, List[str]]) -> Dict[str, List[str]]:
    low = text.lower()
    out: Dict[str, List[str]] = {}
    for key, markers in spec.items():
        hits = [m for m in markers if m.lower() in low]
        if hits:
            out[key] = hits[:20]
    return out


def _score_from_hit_dict(hits: Dict[str, List[str]], total_keys: int, cap_per_key: int = 2) -> float:
    if total_keys <= 0:
        return 0.0
    weighted = sum(min(cap_per_key, len(v)) for v in hits.values())
    return pct((weighted / max(1, total_keys * cap_per_key)) * 100.0)


def _extract_frontmatter_value(text: str, key: str) -> str:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*:\s*['\"]?([^\n'\"]+)", text)
    return norm_text(m.group(1)) if m else ""


def _first_nonempty_heading(text: str, fallback: str = "") -> str:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()
    for line in text.splitlines():
        s = line.strip()
        if s and len(s) < 120:
            return s
    return fallback


def extract_snippet_for_markers(text: str, markers: Iterable[str], max_len: int = 220) -> str:
    sentences = split_sentences(text)
    low_markers = [m.lower() for m in markers]
    for s in sentences:
        l = s.lower()
        if any(m in l for m in low_markers):
            return s[:max_len] + ("…" if len(s) > max_len else "")
    return ""


def coherence_signature_assessment(text: str, claims: List[ClaimRecord]) -> Dict[str, Any]:
    pos_hits = _hit_dict(text, COHERENCE_POSITIVE_SIGNALS)
    red_hits = _hit_dict(text, COHERENCE_RED_FLAGS)
    positive_score = _score_from_hit_dict(pos_hits, len(COHERENCE_POSITIVE_SIGNALS))
    red_flag_score = _score_from_hit_dict(red_hits, len(COHERENCE_RED_FLAGS))
    claim_bonus = min(18.0, sum(1 for c in claims if c.score.boundary >= 30 and c.kill_markers) * 3.0)
    score = pct(positive_score + claim_bonus - red_flag_score * 0.55)
    if score >= 72 and red_flag_score < 35:
        status = "STRONG_COHERENCE_SIGNATURE"
    elif score >= 48:
        status = "PARTIAL_COHERENCE_SIGNATURE"
    elif positive_score > 25 and red_flag_score >= 45:
        status = "SIGNAL_WITH_FAKE_COHERENCE_RISK"
    else:
        status = "WEAK_OR_UNDETECTED"
    return {
        "score": score,
        "positive_score": positive_score,
        "red_flag_score": red_flag_score,
        "status": status,
        "positive_hits": pos_hits,
        "red_flags": red_hits,
        "interpretation": "Detects whether coherence is structural rather than only thematic.",
    }


def canonical_identity_assessment(text: str, source_path: str = "") -> Dict[str, Any]:
    object_id = _extract_frontmatter_value(text, "id") or _extract_frontmatter_value(text, "uuid") or "RO-" + hash_text(source_path + text[:300])[:10]
    title = _extract_frontmatter_value(text, "title") or _first_nonempty_heading(text, Path(source_path).stem if source_path else "Untitled")
    raw_type = (_extract_frontmatter_value(text, "type") or _extract_frontmatter_value(text, "epistemic_role") or "").lower()
    low = text.lower()
    if "operator" in raw_type or "preconditions" in low and "postconditions" in low:
        object_type = "operator"
    elif "objection" in raw_type or "steelman" in low:
        object_type = "objection"
    elif "definition" in raw_type or "non-examples" in low:
        object_type = "definition"
    elif "paper" in raw_type or "scope" in low and "test hooks" in low:
        object_type = "paper"
    elif "theorem" in raw_type or "lean" in low or "formal proof" in low:
        object_type = "theorem_or_formal_claim"
    elif "claim" in raw_type or CLAIM_MARKERS.search(text):
        object_type = "claim"
    else:
        object_type = "research_object"
    status = (_extract_frontmatter_value(text, "status") or "staging").lower()
    if "canonical" in status or "status: canonical" in low:
        ring_status = "canonical_candidate_or_declared"
    elif "quarantine" in status or "rejected" in status:
        ring_status = status
    elif "review" in status:
        ring_status = "review"
    else:
        ring_status = "staging"
    parent_hits = marker_hits(text, {"depends_on", "parent", "parents", "children", "related", "canonical hub", "cross-reference"})
    promotion_evidence = marker_hits(text, {"evidence", "proof", "lean", "source", "citation", "test", "prediction", "kill condition", "verified"})
    demotion_triggers = marker_hits(text, {"unverified", "contested", "speculative", "needs source", "high risk", "quarantine", "rejected"})
    missing = []
    if not title or title == "Untitled":
        missing.append("title")
    if not raw_type and object_type == "research_object":
        missing.append("object_type")
    if not parent_hits:
        missing.append("parent_dependency_links")
    if not promotion_evidence:
        missing.append("promotion_evidence")
    score = pct(100 - len(missing) * 18 + min(20, len(promotion_evidence) * 4) - min(15, len(demotion_triggers) * 3))
    return {
        "score": score,
        "research_object": {
            "id": object_id,
            "title": title,
            "object_type": object_type,
            "ring_status": ring_status,
            "source_path": source_path,
        },
        "parent_dependency_markers": parent_hits,
        "promotion_evidence_markers": promotion_evidence,
        "demotion_or_quarantine_triggers": demotion_triggers,
        "missing_identity_fields": missing,
        "status": "IDENTIFIED" if score >= 65 else "IDENTITY_NEEDS_WORK",
    }


def axiom_wiring_assessment(text: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    missing: List[str] = []
    total = 0.0
    for key, spec in AXIOM_WIRING_GRID.items():
        hits = marker_hits(text, spec["markers"])
        score = pct(min(100, len(hits) * 30))
        if score < 25:
            missing.append(key)
        fields[key] = {
            "label": spec["label"],
            "score": score,
            "hits": hits,
            "snippet": extract_snippet_for_markers(text, spec["markers"]),
        }
        total += score
    strength = pct(total / len(AXIOM_WIRING_GRID))
    return {
        "score": strength,
        "wiring_strength": strength,
        "fields": fields,
        "missing_wires": missing,
        "status": "WIRED" if strength >= 70 and not missing else "PARTIAL_WIRING" if strength >= 42 else "WEAK_WIRING",
        "interpretation": "Shows how the claim connects axiom, truth condition, structure, evidence, question, prediction, contradiction, and integration.",
    }


def isomorphism_bridge_assessment(text: str) -> Dict[str, Any]:
    domains = classify_domains(text)
    top_domains = list(domains.keys())[:4]
    low = text.lower()
    bridge_markers = marker_hits(text, {"isomorphism", "isomorphic", "structural correspondence", "maps to", "mapping", "same structure", "preserves", "translation", "bidirectional", "source domain", "target domain"})
    preserved_markers = marker_hits(text, {"preserved", "invariant", "same equation", "same structure", "same boundary", "same symmetry", "same conservation", "variables"})
    nonpreserved_markers = marker_hits(text, {"non-preserved", "does not preserve", "asymmetry", "added term", "free will", "agency", "choice", "not identical"})
    bidirectional = bool(marker_hits(text, {"bidirectional", "both directions", "a to b", "b to a", "reverse translation", "maps back"}))
    failure_markers = marker_hits(text, {"analogy only", "fails", "failure mode", "not preserved", "category error", "domain leakage", "false positive"})
    if len(top_domains) >= 2 and bridge_markers and preserved_markers and bidirectional and len(failure_markers) <= 2:
        iso_status = "strong"
    elif len(top_domains) >= 2 and bridge_markers and preserved_markers:
        iso_status = "partial"
    elif len(top_domains) >= 2 and bridge_markers:
        iso_status = "candidate"
    elif "analogy" in low or "metaphor" in low:
        iso_status = "analogy_not_iso"
    else:
        iso_status = "not_detected"
    score_map = {"strong": 88, "partial": 64, "candidate": 45, "analogy_not_iso": 28, "not_detected": 0}
    return {
        "score": score_map[iso_status],
        "iso_status": iso_status,
        "source_domain_candidates": top_domains[:2],
        "target_domain_candidates": top_domains[1:3],
        "bridge_markers": bridge_markers,
        "preserved_variables_or_relations": preserved_markers,
        "non_preserved_variables_or_asymmetries": nonpreserved_markers,
        "bidirectional_test_detected": bidirectional,
        "failure_markers": failure_markers,
        "interpretation": "Distinguishes candidate/partial/strong isomorphism from analogy.",
    }


def one_variable_no_drift_assessment(text: str) -> Dict[str, Any]:
    low = text.lower()
    equation_hits = re.findall(r"(?:\$\$.*?\$\$|\\\[.*?\\\]|[A-Za-zχΧ][A-Za-z0-9_{}\\^]*\s*=\s*[^\n]{3,120})", text, flags=re.DOTALL)
    source_relation = marker_hits(text, {"maxwell", "shannon", "second law", "einstein", "newton", "noether", "schrodinger", "lagrangian", "field equation", "source law", "physical relation"})
    one_variable = marker_hits(text, {"one variable", "single variable", "one term", "added term", "free will term", "agency term", "choice term", "acceptance", "resistance", "openness"})
    drift_flags = marker_hits(text, {"change the equation", "bend the source law", "redefine", "rescue move", "same math"})
    # Boundary terms reduce the danger that "same math" is overclaiming.
    boundaries = marker_hits(text, BOUNDARY_MARKERS)
    rival = marker_hits(text, {"rival translation", "alternative mapping", "competing translation", "false positive", "wrong mapping"})
    falsifier = marker_hits(text, {"falsifier", "would fail", "kill condition", "fails if", "counterexample"})
    law10 = marker_hits(text, {"law 10", "coherence", "global alignment", "christ", "master equation", "χ"})
    relation_preserved = bool(source_relation or equation_hits) and (bool(boundaries) or bool(one_variable) or "preserve" in low)
    drift_score = pct(15 * bool(source_relation) + 20 * bool(equation_hits) + 25 * bool(one_variable) + 15 * bool(rival) + 15 * bool(falsifier) + 10 * bool(law10) - (12 * max(0, len(drift_flags) - len(boundaries))))
    return {
        "score": drift_score,
        "source_relation_detected": source_relation,
        "equation_samples": [norm_text(e)[:160] for e in equation_hits[:5]],
        "single_interpretive_variable_detected": one_variable,
        "drift_flags": drift_flags,
        "rival_translation_markers": rival,
        "falsifier_markers": falsifier,
        "law10_alignment_markers": law10,
        "relation_preserved": relation_preserved,
        "status": "NO_DRIFT_READY" if drift_score >= 70 and relation_preserved else "PARTIAL_NO_DRIFT" if drift_score >= 40 else "NO_DRIFT_NOT_ESTABLISHED",
    }


def evidence_tier_assessment(text: str) -> Dict[str, Any]:
    sentences = split_sentences(text)
    items = []
    counts = Counter()
    for i, s in enumerate(sentences):
        if not marker_hits(s, EVIDENCE_MARKERS | FORMAL_MARKERS | HEDGE_MARKERS):
            continue
        tier_hits = {tier: marker_hits(s, markers) for tier, markers in EVIDENCE_TIER_MARKERS.items()}
        if tier_hits["tier_1"]:
            tier = "Tier 1"
        elif tier_hits["tier_2"]:
            tier = "Tier 2"
        elif tier_hits["tier_3"]:
            tier = "Tier 3"
        else:
            tier = "Unclassified"
        if marker_hits(s, {"contested", "methodological debate", "mixed", "critic", "questioned"}):
            verification = "contested"
        elif marker_hits(s, {"verified", "confirmed", "reproducible", "compiled", "proved"}):
            verification = "verified_or_claimed_verified"
        elif marker_hits(s, {"needs source", "unverified", "source needed"}):
            verification = "needs_source"
        elif tier == "Tier 3":
            verification = "speculative_only"
        else:
            verification = "plausible_unverified"
        source_type = "formal" if marker_hits(s, FORMAL_MARKERS) else "empirical" if marker_hits(s, EVIDENCE_MARKERS) else "interpretive"
        counts[tier] += 1
        items.append({
            "id": f"EV-{len(items)+1:03d}",
            "tier": tier,
            "source_type": source_type,
            "verification_status": verification,
            "confidence": 0.8 if tier == "Tier 1" and verification.startswith("verified") else 0.55 if tier in {"Tier 1", "Tier 2"} else 0.35,
            "text": s[:380] + ("…" if len(s) > 380 else ""),
        })
        if len(items) >= 40:
            break
    tier_score = pct(counts["Tier 1"] * 10 + counts["Tier 2"] * 6 + counts["Tier 3"] * 2 - sum(1 for it in items if it["verification_status"] == "needs_source") * 8)
    return {
        "score": tier_score,
        "counts": dict(counts),
        "evidence_items": items,
        "status": "EVIDENCE_TIERED" if items else "NO_EVIDENCE_ITEMS_DETECTED",
        "interpretation": "Classifies evidence as primary/formal, secondary, or speculative signal without discarding weak early signals.",
    }


def objection_taxonomy_assessment(text: str) -> Dict[str, Any]:
    hits = _hit_dict(text, OBJECTION_TAXONOMY_MARKERS)
    sentences = split_sentences(text)
    items = []
    for s in sentences:
        low = s.lower()
        if not any(k in low for k in ["objection", "critic", "but", "however", "fails", "contradiction", "problem", "gap", "would change my mind", "steelman"]):
            continue
        classes = [cls for cls, markers in OBJECTION_TAXONOMY_MARKERS.items() if any(m in low for m in markers)]
        if not classes:
            if "but" in low or "however" in low or "gap" in low:
                classes = ["peripheral_tension"]
            else:
                classes = ["unclassified_objection"]
        items.append({
            "id": f"OBJ-{len(items)+1:03d}",
            "taxonomy_class": classes[0],
            "steelman_present": "steelman" in low or "strongest" in low or "charitable" in low,
            "response_present": "reply" in low or "response" in low or "therefore" in low or "counter" in low,
            "what_would_change_verdict_present": "change my mind" in low or "would falsify" in low or "fails if" in low,
            "residual_risk": "high" if classes[0] in {"foundational_contradiction", "structural_contradiction", "isomorphism_failure"} else "medium" if classes[0] != "peripheral_tension" else "low",
            "text": s[:420] + ("…" if len(s) > 420 else ""),
        })
        if len(items) >= 30:
            break
    score = pct(_score_from_hit_dict(hits, len(OBJECTION_TAXONOMY_MARKERS)) + min(25, len(items) * 3))
    return {
        "score": score,
        "taxonomy_hits": hits,
        "objections": items,
        "status": "OBJECTIONS_TAXONOMIZED" if items else "NO_OBJECTION_LAYER_DETECTED",
        "interpretation": "Objections are classified before being answered so disagreement becomes structured.",
    }


def public_deploy_readiness_assessment(text: str, claims: List[ClaimRecord], scores: Dict[str, float]) -> Dict[str, Any]:
    hits = _hit_dict(text, DEPLOYMENT_MARKERS)
    hook_score = pct(50 if DEPLOYMENT_MARKERS["hook"] and any(hits.get("hook", [])) else 0)
    claim_focus = pct(max(0, 100 - max(0, len(claims) - 3) * 12)) if claims else 25
    objection_ready = pct(50 + len(hits.get("objection_ready", [])) * 10) if hits.get("objection_ready") else 25
    source_backup = max(scores.get("evidence", 0), pct(len(hits.get("source_backup", [])) * 25))
    misread_risk = clamp(scores.get("overclaim_risk", 0) * 0.55 + scores.get("fear_pressure", 0) * 0.35 + scores.get("discoherence", 0) * 0.20)
    deploy_score = pct(hook_score * 0.18 + claim_focus * 0.20 + objection_ready * 0.20 + source_backup * 0.22 + (100 - misread_risk) * 0.20)
    if deploy_score >= 72 and misread_risk < 45:
        gate = "PUBLIC_READY_CANDIDATE"
    elif deploy_score >= 55:
        gate = "PUBLIC_READY_WITH_REWRITE"
    else:
        gate = "NOT_PUBLIC_READY"
    domains = classify_domains(text)
    best_audience = "technical/research" if domains.get("formal_math", 0) or domains.get("physics", 0) else "theology/philosophy" if domains.get("theology", 0) else "general_reader"
    return {
        "score": deploy_score,
        "gate": gate,
        "hook_clarity": hook_score,
        "single_claim_focus": claim_focus,
        "objection_readiness": objection_ready,
        "source_backup": source_backup,
        "misread_risk": pct(misread_risk),
        "best_audience": best_audience,
        "markers": hits,
        "follow_up_needed": [] if hits.get("followup") else ["add follow-up path or source card"],
        "interpretation": "Architecture-ready does not mean public-ready; this is a separate deployment gate.",
    }


def v4_research_architecture_assessment(text: str, claims: List[ClaimRecord], scores: Dict[str, float], source_path: str = "") -> Dict[str, Any]:
    base = research_architecture_assessment(text, claims, scores)
    layers = {
        "coherence_signature": coherence_signature_assessment(text, claims),
        "canonical_identity": canonical_identity_assessment(text, source_path),
        "axiom_wiring": axiom_wiring_assessment(text),
        "isomorphism_bridge": isomorphism_bridge_assessment(text),
        "one_variable_no_drift": one_variable_no_drift_assessment(text),
        "evidence_tiering": evidence_tier_assessment(text),
        "objection_taxonomy": objection_taxonomy_assessment(text),
        "public_deploy_readiness": public_deploy_readiness_assessment(text, claims, scores),
    }
    v4_score = pct(sum(float(v.get("score", 0)) for v in layers.values()) / max(1, len(layers)))
    readiness_score = pct(base.get("canon_ready_score", 0) * 0.35 + v4_score * 0.45 + scores.get("boundary", 0) * 0.10 + (100 - scores.get("overclaim_risk", 0)) * 0.10)
    v4_actions: List[str] = []
    if layers["coherence_signature"]["status"] in {"WEAK_OR_UNDETECTED", "SIGNAL_WITH_FAKE_COHERENCE_RISK"}:
        v4_actions.append("add coherence-signature evidence: compression, convergence, bidirectional translation, or false-positive rejection")
    if layers["axiom_wiring"]["status"] != "WIRED":
        v4_actions.append("complete axiom wiring: A/AT/AS/AE/AQ/AP/AC/AI")
    if layers["isomorphism_bridge"]["iso_status"] in {"candidate", "analogy_not_iso"}:
        v4_actions.append("separate analogy from isomorphism and list preserved/non-preserved variables")
    if layers["one_variable_no_drift"]["status"] == "NO_DRIFT_NOT_ESTABLISHED":
        v4_actions.append("add no-drift check: source law, one interpretive variable, rival translation, falsifier")
    if layers["evidence_tiering"]["status"] == "NO_EVIDENCE_ITEMS_DETECTED":
        v4_actions.append("tier evidence: primary/formal, secondary, or speculative signal")
    if layers["objection_taxonomy"]["status"] == "NO_OBJECTION_LAYER_DETECTED":
        v4_actions.append("add objection taxonomy with steelman, response, residual risk, and what would change the verdict")
    if layers["public_deploy_readiness"]["gate"] == "NOT_PUBLIC_READY":
        v4_actions.append("hold for internal/canonical work before public deployment")
    if not v4_actions:
        v4_actions.append("run external review or promote to next ring if sources are adequate")

    if readiness_score >= 76 and not base.get("missing_required_fields") and layers["public_deploy_readiness"]["misread_risk"] < 45:
        v4_verdict = "V4_CANON_OR_PUBLIC_REVIEW_CANDIDATE"
    elif readiness_score >= 60:
        v4_verdict = "V4_STRUCTURED_NEEDS_TARGETED_REPAIR"
    elif scores.get("truth_pressure", 0) >= 45:
        v4_verdict = "V4_SIGNAL_PRESERVED_NEEDS_GOLD_ARCHITECTURE"
    else:
        v4_verdict = "V4_PRE_CLAIM_OR_REWRITE"

    base.update({
        "v4_score": v4_score,
        "v4_readiness_score": readiness_score,
        "v4_verdict": v4_verdict,
        "v4_layers": layers,
        "v4_next_actions": v4_actions,
        "v4_output_shape": {
            "research_object": layers["canonical_identity"].get("research_object", {}),
            "architecture": "base architecture fields + v4 layers",
            "evidence_tiers": layers["evidence_tiering"].get("evidence_items", []),
            "coherence_signature": layers["coherence_signature"],
            "axiom_wiring": layers["axiom_wiring"],
            "isomorphism_bridge": layers["isomorphism_bridge"],
            "no_drift_law_translation": layers["one_variable_no_drift"],
            "objections": layers["objection_taxonomy"].get("objections", []),
            "deployment_readiness": layers["public_deploy_readiness"],
            "verdict": {"v4": v4_verdict, "readiness_score": readiness_score},
            "next_actions": v4_actions,
        },
        "operationalized_from_gold_gap_packet": [
            "GAP_REPORT.md", "MISSING_GOLD_MAP.md", "REWRITE_INSERTS.md", "V4_CODE_GAP_BACKLOG.md",
            "OS Gold", "Canonical Gold", "Deuterocanonical Gold", "TikTok Gold", "Scientific Method Gold",
        ],
    })
    return base


def render_markdown_report(report: DocumentReport, out_path: Path) -> None:
    arch = report.architecture or {}
    layers = arch.get("v4_layers", {}) if isinstance(arch, dict) else {}
    lines = [
        f"# χ-JM Diagnostic Report — {report.title}",
        "",
        f"- Engine: `{report.engine_version}`",
        f"- Overall verdict: `{report.overall_verdict}`",
        f"- Architecture verdict: `{arch.get('verdict', '')}`",
        f"- V4 verdict: `{arch.get('v4_verdict', '')}`",
        f"- V4 readiness: `{arch.get('v4_readiness_score', 0)}`",
        "",
        "## Thesis",
        "",
        report.inferred_thesis,
        "",
        "## Overall Scores",
        "",
    ]
    for k, v in report.overall_scores.items():
        lines.append(f"- {k}: {v}")
    lines.extend(["", "## V4 Layers", ""])
    for name, data in layers.items():
        lines.append(f"### {name}")
        lines.append(f"- score: {data.get('score', '')}")
        for status_key in ["status", "iso_status", "gate"]:
            if status_key in data:
                lines.append(f"- {status_key}: `{data.get(status_key)}`")
        if name == "axiom_wiring":
            lines.append(f"- missing wires: {', '.join(data.get('missing_wires', [])) or 'none'}")
        if name == "evidence_tiering":
            lines.append(f"- evidence counts: {data.get('counts', {})}")
        lines.append("")
    lines.extend(["## Next Actions", ""])
    for a in (arch.get("v4_next_actions") or arch.get("next_actions") or []):
        lines.append(f"- {a}")
    lines.extend(["", "## Top Claims", ""])
    for c in report.claims[:12]:
        lines.append(f"### {c.claim_id} — {c.verdict}")
        lines.append(c.claim_text)
        lines.append(f"- repair: {c.suggested_repair}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def render_next_actions(report: DocumentReport, out_path: Path) -> None:
    arch = report.architecture or {}
    actions = list(arch.get("v4_next_actions") or []) + list(arch.get("next_actions") or [])
    dedup = []
    for a in actions:
        if a not in dedup:
            dedup.append(a)
    lines = [f"# Next Actions — {report.title}", "", f"V4 verdict: `{arch.get('v4_verdict', '')}`", ""]
    for i, a in enumerate(dedup, 1):
        lines.append(f"{i}. {a}")
    if not dedup:
        lines.append("No immediate actions generated.")
    out_path.write_text("\n".join(lines), encoding="utf-8")

# ---------------------------------------------------------------------------
# Extraction functions
# ---------------------------------------------------------------------------

def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("#"):
            return clean.lstrip("#").strip()[:140]
        if len(clean) <= 120 and not clean.endswith("."):
            return clean[:140]
    return fallback


def extract_sections(text: str) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, List[str]]] = []
    current_title = "Document Start"
    current_lines: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if re.match(r"^#{1,6}\s+", line):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines)))
            current_title = re.sub(r"^#{1,6}\s+", "", line).strip()
            current_lines = []
        else:
            current_lines.append(raw)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines)))
    return [(t, b) for t, b in sections if norm_text(b)]


def extract_entities(text: str, max_entities: int = 80) -> List[Dict[str, Any]]:
    # Multi-word proper names and special all-caps terms.
    patterns = [
        r"\b(?:[A-Z][a-z]+(?:'s)?\s+){1,4}[A-Z][a-z]+(?:'s)?\b",
        r"\b(?:[A-Z]{2,}(?:-[A-Z0-9]+)?)(?:\s+[A-Z]{2,}){0,3}\b",
        r"\b(?:GPT|Claude|Gemini|DeepSeek|Lean\s?4|OpenAI|Anthropic|Google|Wigner|Shannon|Plantinga|Hume|Münchhausen|Munchhausen)\b",
    ]
    counts = Counter()
    for pat in patterns:
        for m in re.finditer(pat, text):
            val = norm_text(m.group(0)).strip(" .,;:()[]{}")
            first = val.split()[0] if val.split() else ""
            if first in ENTITY_STOPWORDS or len(val) < 3:
                continue
            counts[val] += 1
    out = []
    for name, count in counts.most_common(max_entities):
        role = "unknown"
        low = name.lower()
        if any(x in low for x in ["god", "christ", "logos", "spirit"]):
            role = "theological_anchor"
        elif any(x in low for x in ["science", "naturalism", "materialism"]):
            role = "framework_or_rival"
        elif any(x in low for x in ["lean", "gpt", "claude", "gemini", "deepseek"]):
            role = "tool_or_model"
        out.append({"entity": name, "count": count, "role_hint": role})
    return out


def extract_claims(doc_id: str, text: str, max_claims: int = 80) -> List[ClaimRecord]:
    claims: List[ClaimRecord] = []
    sections = extract_sections(text)
    used_hashes = set()
    for section_title, body in sections:
        sentences = split_sentences(body)
        for sent in sentences:
            claim_terms = _active_terms("CLAIM_TERMS", set())
            if not (CLAIM_MARKERS.search(sent) or marker_hits(sent, claim_terms)):
                continue
            sent_hash = hash_text(sent)
            if sent_hash in used_hashes:
                continue
            used_hashes.add(sent_hash)
            score = score_text_unit(sent)
            q = seven_q(sent)
            claim_id = f"{doc_id}-C{len(claims)+1:03d}"
            risk_terms = marker_hits(sent, OVERCLAIM_MARKERS)
            evidence_terms = marker_hits(sent, EVIDENCE_MARKERS)
            boundary_terms = marker_hits(sent, BOUNDARY_MARKERS)
            kill_terms = marker_hits(sent, KILL_MARKERS)
            entities = [e["entity"] for e in extract_entities(sent, max_entities=12)]
            claims.append(
                ClaimRecord(
                    claim_id=claim_id,
                    doc_id=doc_id,
                    section=section_title,
                    claim_text=sent,
                    claim_type=claim_type(sent),
                    domains=classify_domains(sent),
                    law_hits=classify_laws(sent),
                    semantic_buckets=semantic_bucket_scores(sent),
                    seven_q=q,
                    reverse_tests=reverse_tests(sent, score),
                    score=score,
                    entities=entities,
                    evidence_markers=evidence_terms,
                    boundary_markers=boundary_terms,
                    kill_markers=kill_terms,
                    risky_terms=risk_terms,
                    suggested_repair=suggest_repair(sent, score),
                    verdict=claim_verdict(score),
                )
            )
            if len(claims) >= max_claims:
                return claims
    return claims


def infer_thesis(text: str, claims: List[ClaimRecord]) -> str:
    if claims:
        top = sorted(claims, key=lambda c: (c.score.truth_pressure, c.score.coherence), reverse=True)[:3]
        pieces = [c.claim_text for c in top]
        joined = " ".join(pieces)
        if len(joined) > 600:
            joined = joined[:597].rstrip() + "..."
        return "The text appears to argue: " + joined
    paras = split_paragraphs(text)
    if paras:
        first = paras[0]
        return "The text appears to center on: " + (first[:500].rstrip() + ("..." if len(first) > 500 else ""))
    return "No thesis detected."


def build_heartbeat(doc_id: str, text: str, unit: str = "sentence") -> List[SegmentRecord]:
    units = split_sentences(text) if unit == "sentence" else split_paragraphs(text)
    records: List[SegmentRecord] = []
    for i, u in enumerate(units, 1):
        score = score_text_unit(u)
        mh = {
            "evidence": marker_hits(u, EVIDENCE_MARKERS),
            "boundary": marker_hits(u, BOUNDARY_MARKERS),
            "kill": marker_hits(u, KILL_MARKERS),
            "overclaim": marker_hits(u, OVERCLAIM_MARKERS),
            "justice": marker_hits(u, JUSTICE_TERMS),
            "mercy": marker_hits(u, REPAIR_TERMS),
            "coherence": marker_hits(u, COHERENCE_TERMS),
            "discoherence": marker_hits(u, _active_terms_multi(["DISCOHERENCE_TERMS", "DRIFT_WARNING", "NEGATION_TERMS"], DISCOHERENCE_TERMS)),
            "semantic": semantic_hit_labels(u),
        }
        records.append(
            SegmentRecord(
                doc_id=doc_id,
                unit_id=f"{doc_id}-{unit[0].upper()}{i:04d}",
                unit_type=unit,
                index=i,
                text=u,
                score=score,
                marker_hits=mh,
                semantic_buckets=semantic_bucket_scores(u),
            )
        )
    return records


def aggregate_scores(segments: List[SegmentRecord], fruit_adapter_result: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    if not segments:
        return {k: 0.0 for k in ["coherence", "discoherence", "justice", "mercy", "justice_mercy_balance", "fruit", "evidence", "boundary", "truth_pressure", "overclaim_risk"]}
    fields = [
        "coherence", "discoherence", "justice", "mercy", "justice_mercy_balance", "fruit",
        "anti_fruit", "evidence", "boundary", "falsifiability", "formal", "overclaim_risk",
        "fear_pressure", "truth_pressure",
    ]
    out: Dict[str, float] = {}
    for f in fields:
        vals = [getattr(s.score, f) for s in segments]
        # Weighted average: high-signal sentences matter more, but every segment counts.
        out[f] = pct(statistics.mean(vals))
    if fruit_adapter_result and isinstance(fruit_adapter_result.get("normalized_score"), (int, float)):
        out["external_fruits_normalized"] = pct(float(fruit_adapter_result["normalized_score"]))
        out["fruit_blended"] = pct((out.get("fruit", 0) * 0.65) + (float(fruit_adapter_result["normalized_score"]) * 0.35))
    else:
        out["fruit_blended"] = out.get("fruit", 0.0)
    return out


def overall_verdict(scores: Dict[str, float], claims: List[ClaimRecord]) -> str:
    high_risk_claims = sum(1 for c in claims if c.verdict == "NEEDS_RIGOR_HIGH_RISK")
    ready_claims = sum(1 for c in claims if c.verdict in {"AUDIT_READY", "FORMALIZATION_CANDIDATE"})
    if scores.get("discoherence", 0) > 70 or high_risk_claims >= max(2, len(claims) // 3):
        return "NEEDS_RIGOR_HIGH_RISK"
    if scores.get("coherence", 0) > 72 and scores.get("truth_pressure", 0) > 62 and scores.get("overclaim_risk", 0) < 40:
        return "AUDIT_READY"
    if ready_claims >= max(1, len(claims) // 3) and scores.get("boundary", 0) >= 25:
        return "PROMISING_NEEDS_SOURCE_REVIEW"
    if scores.get("truth_pressure", 0) >= 45:
        return "PRESERVE_AS_SIGNAL_AND_REPAIR"
    return "LOW_SIGNAL_OR_REWRITE"

# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def write_json(path: Path, data: Any) -> None:
    def default(o: Any):
        if dataclasses.is_dataclass(o):
            return asdict(o)
        return str(o)
    path.write_text(json.dumps(data, default=default, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def score_color(score: float, inverse: bool = False) -> str:
    s = 100 - score if inverse else score
    if s >= 75:
        return "good"
    if s >= 50:
        return "mid"
    if s >= 30:
        return "warn"
    return "bad"


def render_bar(label: str, value: float, cls: str = "") -> str:
    return f"""
    <div class='bar-row {cls}'>
      <div class='bar-label'>{html.escape(label)}</div>
      <div class='bar-track'><div class='bar-fill' style='width:{clamp(value)}%'></div></div>
      <div class='bar-val'>{value:.1f}</div>
    </div>"""


def render_html(report: DocumentReport, out_path: Path) -> None:
    scores = report.overall_scores
    top_domains = "".join(render_bar(k, v) for k, v in list(report.domains.items())[:8])
    top_laws = "".join(render_bar(k, v) for k, v in list(report.laws.items())[:8])
    score_bars = "".join([
        render_bar("Coherence", scores.get("coherence", 0)),
        render_bar("Discoherence", scores.get("discoherence", 0), "danger"),
        render_bar("Justice", scores.get("justice", 0)),
        render_bar("Mercy", scores.get("mercy", 0)),
        render_bar("Justice/Mercy Balance", scores.get("justice_mercy_balance", 0)),
        render_bar("Evidence", scores.get("evidence", 0)),
        render_bar("Boundary", scores.get("boundary", 0)),
        render_bar("Truth Pressure", scores.get("truth_pressure", 0)),
        render_bar("Overclaim Risk", scores.get("overclaim_risk", 0), "danger"),
    ])

    arch = report.architecture or {}
    arch_fields = arch.get("field_results", {}) if isinstance(arch, dict) else {}
    arch_bars = "".join(render_bar(v.get("label", k), float(v.get("score", 0))) for k, v in arch_fields.items())
    arch_missing = ", ".join(arch.get("missing_required_fields", [])) or "none"
    arch_actions = "".join(f"<li>{html.escape(a)}</li>" for a in arch.get("next_actions", [])[:10])
    arch_templates = ", ".join(f"{k}:{v:.0f}" for k, v in list((arch.get("template_types_detected", {}) or {}).items())[:8]) or "none"
    v4_layers = arch.get("v4_layers", {}) if isinstance(arch, dict) else {}
    v4_bars = "".join(render_bar(k.replace('_', ' ').title(), float(v.get('score', 0))) for k, v in v4_layers.items())
    v4_actions = "".join(f"<li>{html.escape(a)}</li>" for a in arch.get("v4_next_actions", [])[:12])
    v4_verdict = html.escape(str(arch.get("v4_verdict", "")))
    v4_ready = float(arch.get("v4_readiness_score", 0) or 0)

    claim_cards = []
    for c in report.claims[:40]:
        risk = ", ".join(c.risky_terms[:8]) or "none"
        sem = ", ".join(f"{k}:{v:.0f}" for k, v in sorted(c.semantic_buckets.items(), key=lambda kv: kv[1], reverse=True)[:6]) or "none"
        claim_cards.append(f"""
        <article class='claim-card'>
          <div class='claim-head'><span>{html.escape(c.claim_id)}</span><b>{html.escape(c.verdict)}</b></div>
          <p>{html.escape(c.claim_text)}</p>
          <div class='claim-meta'>Type: {html.escape(c.claim_type)} · Coherence {c.score.coherence:.1f} · Truth Pressure {c.score.truth_pressure:.1f} · Risk {c.score.overclaim_risk:.1f}</div>
          <details><summary>7Q / Reverse / Repair</summary>
            <pre>{html.escape(json.dumps({'7Q': c.seven_q, 'reverse': c.reverse_tests, 'repair': c.suggested_repair}, indent=2))}</pre>
            <div class='risk'>Risk terms: {html.escape(risk)}</div>
            <div class='risk'>Semantic buckets: {html.escape(sem)}</div>
          </details>
        </article>""")

    heartbeat_rows = []
    for s in report.heartbeat[:240]:
        cls = score_color(s.score.truth_pressure)
        risk_cls = " high-risk" if s.score.overclaim_risk > 55 or s.score.discoherence > 65 else ""
        heartbeat_rows.append(f"""
        <div class='heart-row {cls}{risk_cls}' title='coh {s.score.coherence:.1f} · disc {s.score.discoherence:.1f} · JM {s.score.justice_mercy_balance:.1f} · TP {s.score.truth_pressure:.1f}'>
          <span class='heart-index'>{s.index}</span>
          <span class='heart-dot'></span>
          <span class='heart-text'>{html.escape(s.text[:260])}{'…' if len(s.text)>260 else ''}</span>
          <span class='heart-score'>{s.score.truth_pressure:.0f}</span>
        </div>""")

    ent_rows = "".join(f"<tr><td>{html.escape(e['entity'])}</td><td>{e['count']}</td><td>{html.escape(e.get('role_hint',''))}</td></tr>" for e in report.entities[:80])

    lexicon_note = "Built-in lexicons only."
    if report.methodology.get("lexicon_loaded"):
        lexicon_note = f"Lexicon loaded: {html.escape(str(report.methodology.get('lexicon_path', '')))} · policy {html.escape(str(report.methodology.get('lexicon_policy', 'merge')))} · {len(report.methodology.get('lexicon_sheets', []))} sheets"

    page = f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width,initial-scale=1'/>
<title>χ JM Diagnostic Report — {html.escape(report.title)}</title>
<style>
:root{{--bg:#080808;--card:#111;--line:#2a2a2a;--text:#e7e7e7;--muted:#999;--gold:#d4af37;--blue:#5fb3ff;--green:#22c55e;--red:#ef4444;--orange:#f59e0b;--purple:#a855f7;}}
body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;}}
main{{max-width:1100px;margin:0 auto;padding:36px 20px 80px;}}
h1{{font-size:34px;line-height:1.15;margin:0 0 8px;}}
.kicker{{font:12px/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;text-transform:uppercase;letter-spacing:.12em;color:var(--gold);}}
.subtitle{{color:var(--muted);max-width:850px;margin-bottom:24px;}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:24px 0;}}
.card,.claim-card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;}}
.card h2{{margin:0 0 12px;font-size:18px;color:#fff;}}
.bar-row{{display:grid;grid-template-columns:170px 1fr 52px;gap:10px;align-items:center;margin:9px 0;}}
.bar-label{{color:#ddd;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.bar-track{{height:9px;background:#222;border-radius:99px;overflow:hidden;}}
.bar-fill{{height:100%;background:linear-gradient(90deg,var(--blue),var(--gold));}}
.bar-row.danger .bar-fill{{background:linear-gradient(90deg,var(--orange),var(--red));}}
.bar-val{{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted);text-align:right;}}
.verdict{{display:inline-block;padding:6px 10px;border:1px solid var(--gold);border-radius:99px;color:var(--gold);font:12px ui-monospace,SFMono-Regular,Menlo,monospace;}}
.claim-card{{margin:12px 0;}}
.claim-head{{display:flex;justify-content:space-between;color:var(--gold);font:12px ui-monospace,SFMono-Regular,Menlo,monospace;margin-bottom:8px;}}
.claim-card p{{margin:0 0 8px;}}
.claim-meta,.risk{{color:var(--muted);font-size:12px;}}
details{{margin-top:8px;}}
summary{{cursor:pointer;color:var(--gold);}}
pre{{white-space:pre-wrap;overflow:auto;background:#080808;border:1px solid #222;padding:12px;border-radius:8px;color:#ccc;}}
.heart-row{{display:grid;grid-template-columns:44px 14px 1fr 44px;gap:8px;align-items:center;padding:7px 8px;border-bottom:1px solid #1c1c1c;}}
.heart-index,.heart-score{{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted);}}
.heart-dot{{width:9px;height:9px;border-radius:50%;display:inline-block;background:var(--blue);}}
.heart-row.good .heart-dot{{background:var(--green);box-shadow:0 0 12px rgba(34,197,94,.35);}}
.heart-row.mid .heart-dot{{background:var(--gold);}}
.heart-row.warn .heart-dot{{background:var(--orange);}}
.heart-row.bad .heart-dot,.heart-row.high-risk .heart-dot{{background:var(--red);box-shadow:0 0 12px rgba(239,68,68,.35);}}
.heart-text{{color:#ccc;font-size:13px;}}
table{{width:100%;border-collapse:collapse;}}
td,th{{border-bottom:1px solid #222;padding:8px;text-align:left;}}
th{{color:var(--gold);font-size:12px;text-transform:uppercase;letter-spacing:.08em;}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr;}}.bar-row{{grid-template-columns:120px 1fr 45px;}}}}
</style>
</head>
<body><main>
<div class='kicker'>χ Justice–Mercy Diagnostic Engine · v{ENGINE_VERSION}</div>
<h1>{html.escape(report.title)}</h1>
<p class='subtitle'>{html.escape(report.inferred_thesis)}</p>
<p><span class='verdict'>{html.escape(report.overall_verdict)}</span></p>
<p class='subtitle'>{lexicon_note}</p>
<section class='grid'>
  <div class='card'><h2>Overall Scores</h2>{score_bars}</div>
  <div class='card'><h2>Domains</h2>{top_domains or '<p class="subtitle">No domain concentration detected.</p>'}<h2 style='margin-top:18px'>Ten-Law Hits</h2>{top_laws or '<p class="subtitle">No ten-law concentration detected.</p>'}</div>
</section>
<section class='card' style='margin-top:18px'><h2>Research Architecture</h2>
  <p class='subtitle'>Operationalized from the Research Question, URCE, Definition, Operator, Objection, Paper, and Cross-Reference templates. This measures structure, not truth.</p>
  <div class='verdict'>{html.escape(str(arch.get('verdict', '')))} · Architecture {float(arch.get('architecture_score', 0)):.1f} · Canon Ready {float(arch.get('canon_ready_score', 0)):.1f}</div>
  <div style='margin-top:14px'>{arch_bars or '<p class="subtitle">No architecture markers detected.</p>'}</div>
  <p class='subtitle'><b>Detected template types:</b> {html.escape(arch_templates)}<br/><b>Missing required fields:</b> {html.escape(arch_missing)}</p>
  <details><summary>Next actions</summary><ul>{arch_actions}</ul></details>
  <details style='margin-top:14px'><summary>V4 gold-layer assessments</summary>
    <p class='subtitle'><b>{v4_verdict}</b> · Readiness {v4_ready:.1f}</p>
    {v4_bars or '<p class="subtitle">No V4 layers detected.</p>'}
    <h3>V4 Next Actions</h3><ul>{v4_actions}</ul>
  </details>
</section>
<section class='card' style='margin-top:18px'><h2>Claim Inventory</h2>{''.join(claim_cards) or '<p class="subtitle">No claim candidates detected.</p>'}</section>
<section class='card' style='margin-top:18px'><h2>Heartbeat Trace</h2>{''.join(heartbeat_rows)}</section>
<section class='card' style='margin-top:18px'><h2>Named Entities</h2><table><thead><tr><th>Entity</th><th>Count</th><th>Role Hint</th></tr></thead><tbody>{ent_rows}</tbody></table></section>
</main></body></html>"""
    out_path.write_text(page, encoding="utf-8")

# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

def process_document(path: Path, out_dir: Path, unit: str, fruits_adapter: OptionalFruitsAdapter) -> DocumentReport:
    text = read_text(path)
    doc_id = hash_text(str(path) + text[:1000])
    title = extract_title(text, path.stem)
    claims = extract_claims(doc_id, text)
    heartbeat = build_heartbeat(doc_id, text, unit=unit)
    fruits_external = fruits_adapter.score(text, doc_id) if fruits_adapter.available else None
    scores = aggregate_scores(heartbeat, fruits_external)
    domains = classify_domains(text)
    laws = classify_laws(text)
    entities = extract_entities(text)
    thesis = infer_thesis(text, claims)
    verdict = overall_verdict(scores, claims)
    architecture = v4_research_architecture_assessment(text, claims, scores, source_path=str(path))
    return DocumentReport(
        engine_version=ENGINE_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        input_path=str(path),
        doc_id=doc_id,
        title=title,
        inferred_thesis=thesis,
        overall_scores=scores,
        overall_verdict=verdict,
        domains=domains,
        laws=laws,
        claims=claims,
        heartbeat=heartbeat,
        entities=entities,
        architecture=architecture,
        methodology={
            "not_truth_oracle": True,
            "claim": "diagnostic pressure report, not final truth determination",
            "layers": [
                "claim extraction", "7Q forward", "reverse attack heuristics", "coherence/discoherence", "justice/mercy", "fruit/anti-fruit", "domain/law classification", "formal marker detection", "heartbeat trace", "coherence signature", "canonical identity", "axiom wiring", "isomorphism bridge", "no-drift law translation", "evidence tiering", "objection taxonomy", "public deployment readiness",
            ],
            "optional_fruits_adapter": fruits_adapter.available,
            "optional_fruits_adapter_path": str(fruits_adapter.path) if fruits_adapter.path else None,
            "lexicon_loaded": bool(ACTIVE_LEXICON and ACTIVE_LEXICON.loaded),
            "lexicon_path": ACTIVE_LEXICON.path if ACTIVE_LEXICON else None,
            "lexicon_policy": LEXICON_POLICY,
            "lexicon_sheets": ACTIVE_LEXICON.sheet_names if ACTIVE_LEXICON else [],
            "lexicon_warnings": ACTIVE_LEXICON.warnings if ACTIVE_LEXICON else [],
        },
    )


def flatten_claim(c: ClaimRecord) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        "claim_id": c.claim_id,
        "doc_id": c.doc_id,
        "section": c.section,
        "claim_text": c.claim_text,
        "claim_type": c.claim_type,
        "verdict": c.verdict,
        "suggested_repair": c.suggested_repair,
        "entities": "; ".join(c.entities),
        "evidence_markers": "; ".join(c.evidence_markers),
        "boundary_markers": "; ".join(c.boundary_markers),
        "kill_markers": "; ".join(c.kill_markers),
        "risky_terms": "; ".join(c.risky_terms),
    }
    d.update({f"score_{k}": v for k, v in asdict(c.score).items() if k != "classification"})
    d["score_classification"] = c.score.classification
    for k, v in c.seven_q.items():
        d[k] = v
    for k, v in c.reverse_tests.items():
        d[k] = v
    d["domains_json"] = json.dumps(c.domains, ensure_ascii=False)
    d["law_hits_json"] = json.dumps(c.law_hits, ensure_ascii=False)
    d["semantic_buckets_json"] = json.dumps(c.semantic_buckets, ensure_ascii=False)
    return d


def export_report(report: DocumentReport, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "full_report.json", report)
    render_html(report, out_dir / "report.html")
    render_markdown_report(report, out_dir / "report.md")
    render_next_actions(report, out_dir / "next_actions.md")

    claim_rows = [flatten_claim(c) for c in report.claims]
    if claim_rows:
        claim_fields = list(claim_rows[0].keys())
    else:
        claim_fields = ["claim_id", "doc_id", "claim_text", "verdict"]
    write_csv(out_dir / "claims.csv", claim_rows, claim_fields)

    heartbeat_rows = []
    for s in report.heartbeat:
        row = {
            "doc_id": s.doc_id,
            "unit_id": s.unit_id,
            "unit_type": s.unit_type,
            "index": s.index,
            "text": s.text,
            "marker_hits_json": json.dumps(s.marker_hits, ensure_ascii=False),
            "semantic_buckets_json": json.dumps(s.semantic_buckets, ensure_ascii=False),
        }
        row.update({f"score_{k}": v for k, v in asdict(s.score).items()})
        heartbeat_rows.append(row)
    heartbeat_fields = list(heartbeat_rows[0].keys()) if heartbeat_rows else ["unit_id", "text"]
    write_csv(out_dir / "heartbeat.csv", heartbeat_rows, heartbeat_fields)

    entity_rows = report.entities
    write_csv(out_dir / "entities.csv", entity_rows, ["entity", "count", "role_hint"])

    score_rows = [{"metric": k, "value": v} for k, v in report.overall_scores.items()]
    write_csv(out_dir / "scores.csv", score_rows, ["metric", "value"])

    manifest = {
        "engine_version": ENGINE_VERSION,
        "generated_at": report.generated_at,
        "input_path": report.input_path,
        "doc_id": report.doc_id,
        "outputs": ["report.html", "report.md", "next_actions.md", "full_report.json", "claims.csv", "heartbeat.csv", "entities.csv", "scores.csv"],
        "methodology": report.methodology,
    }
    write_json(out_dir / "engine_manifest.json", manifest)


def build_index(reports: List[Tuple[DocumentReport, Path]], out_dir: Path) -> None:
    cards = []
    for report, rel_dir in reports:
        scores = report.overall_scores
        cards.append(f"""
        <a class='card' href='{html.escape(rel_dir.name)}/report.html'>
          <div class='title'>{html.escape(report.title)}</div>
          <div class='verdict'>{html.escape(report.overall_verdict)}</div>
          <div class='small'>Coherence {scores.get('coherence',0):.1f} · Truth Pressure {scores.get('truth_pressure',0):.1f} · Risk {scores.get('overclaim_risk',0):.1f}</div>
        </a>""")
    page = f"""<!doctype html><html><head><meta charset='utf-8'><title>χ JM Batch Index</title>
<style>body{{background:#080808;color:#eee;font-family:system-ui;margin:0;padding:30px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}.card{{display:block;text-decoration:none;color:inherit;background:#111;border:1px solid #2a2a2a;border-radius:12px;padding:16px}}.title{{font-weight:700;margin-bottom:8px}}.verdict{{color:#d4af37;font-family:monospace;font-size:12px}}.small{{color:#999;font-size:13px;margin-top:8px}}</style></head><body><h1>χ Justice–Mercy Batch Index</h1><div class='grid'>{''.join(cards)}</div></body></html>"""
    (out_dir / "index.html").write_text(page, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="χ Justice–Mercy Diagnostic Engine")
    parser.add_argument("--input", "-i", required=True, help="Input .md/.txt/.html file or folder")
    parser.add_argument("--out", "-o", required=True, help="Output folder")
    parser.add_argument("--recursive", action="store_true", help="Process input folder recursively")
    parser.add_argument("--unit", choices=["sentence", "paragraph"], default="sentence", help="Heartbeat unit")
    parser.add_argument("--max-files", type=int, default=0, help="Limit number of files processed; 0 means no limit")
    parser.add_argument("--lexicon", help="Optional lexicon workbook (.xlsx) that drives naming/categories")
    parser.add_argument("--lexicon-policy", choices=["merge", "replace"], default="merge", help="merge = add workbook terms to built-ins; replace = use workbook terms when present")
    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()

    global ACTIVE_LEXICON, LEXICON_POLICY
    LEXICON_POLICY = args.lexicon_policy
    if args.lexicon:
        ACTIVE_LEXICON = LexiconStore.from_xlsx(Path(args.lexicon).expanduser().resolve(), policy=args.lexicon_policy)
        if ACTIVE_LEXICON.loaded:
            print(f"Loaded lexicon: {ACTIVE_LEXICON.path} ({len(ACTIVE_LEXICON.sheet_names)} sheets, {len(ACTIVE_LEXICON.semantic_terms)} semantic rows)")
        else:
            print(f"WARNING: lexicon not loaded: {ACTIVE_LEXICON.warnings}")
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise SystemExit(f"Input does not exist: {input_path}")

    files = iter_input_files(input_path, recursive=args.recursive)
    if args.max_files and args.max_files > 0:
        files = files[: args.max_files]
    if not files:
        raise SystemExit(f"No supported input files found: {input_path}")

    fruits_adapter = OptionalFruitsAdapter(Path(__file__).resolve().parent)

    reports: List[Tuple[DocumentReport, Path]] = []
    for i, path in enumerate(files, 1):
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-._") or f"doc-{i}"
        doc_out = out_dir / slug
        print(f"[{i}/{len(files)}] diagnosing {path.name} -> {doc_out}")
        report = process_document(path, doc_out, args.unit, fruits_adapter)
        export_report(report, doc_out)
        reports.append((report, doc_out))

    if len(reports) > 1:
        build_index(reports, out_dir)

    summary = {
        "engine_version": ENGINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": str(input_path),
        "output": str(out_dir),
        "file_count": len(reports),
        "fruits_adapter_available": fruits_adapter.available,
        "lexicon_loaded": bool(ACTIVE_LEXICON and ACTIVE_LEXICON.loaded),
        "lexicon_path": ACTIVE_LEXICON.path if ACTIVE_LEXICON else None,
        "lexicon_policy": LEXICON_POLICY,
        "reports": [
            {
                "title": r.title,
                "doc_id": r.doc_id,
                "verdict": r.overall_verdict,
                "folder": str(p),
                "coherence": r.overall_scores.get("coherence"),
                "truth_pressure": r.overall_scores.get("truth_pressure"),
                "overclaim_risk": r.overall_scores.get("overclaim_risk"),
                "architecture_score": r.architecture.get("architecture_score") if isinstance(r.architecture, dict) else None,
                "canon_ready_score": r.architecture.get("canon_ready_score") if isinstance(r.architecture, dict) else None,
                "architecture_verdict": r.architecture.get("verdict") if isinstance(r.architecture, dict) else None,
            }
            for r, p in reports
        ],
    }
    write_json(out_dir / "batch_summary.json", summary)
    print(f"\nDone. Open: {out_dir / ('index.html' if len(reports)>1 else reports[0][1].name + '/report.html')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
