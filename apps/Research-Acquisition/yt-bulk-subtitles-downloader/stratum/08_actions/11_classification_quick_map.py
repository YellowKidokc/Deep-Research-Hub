from __future__ import annotations

import re
from collections import Counter


DOMAIN_KEYWORDS = {
    "THEOPHYSICS": {"logos", "axiom", "grace", "christ", "trinity", "coherence", "master equation", "theophysics"},
    "SCIENCE": {"experiment", "measurement", "physics", "biology", "chemistry", "hypothesis", "evidence"},
    "LAW": {"statute", "court", "legal", "contract", "liability", "plaintiff", "defendant"},
    "MEDICINE": {"patient", "clinical", "diagnosis", "treatment", "symptom", "medical"},
    "FINANCE": {"invoice", "revenue", "balance", "expense", "budget", "financial"},
    "PERSONAL": {"i ", "my ", "me ", "journal", "diary", "family"},
    "TECH": {"python", "api", "database", "script", "server", "json", "schema", "sqlite"},
    "EDUCATION": {"lesson", "student", "curriculum", "teach", "learning"},
    "BUSINESS": {"client", "customer", "market", "sales", "business", "strategy"},
    "RELIGION": {"god", "scripture", "church", "theology", "biblical", "faith"},
    "HISTORY": {"century", "historical", "archive", "dated", "record"},
    "MDA": {"mda", "moral decline", "decline"},
    "DATA": {"csv", "dataset", "table", "column", "row", "spreadsheet"},
}

TRUTH_MODES = {
    "MATHEMATICAL_PROOF": {"theorem", "proof", "proved", "derive", "derivation"},
    "FORMAL_DERIVATION": {"derive", "formal", "equation", "lagrangian", "operator"},
    "EMPIRICAL_EVENT": {"observed", "measured", "experiment", "data", "result"},
    "HISTORICAL_RECORD": {"historical", "dated", "archive", "record", "witness"},
    "THEOLOGICAL_CLAIM": {"god", "grace", "sin", "christ", "trinity", "theology"},
    "MORAL_CLAIM": {"right", "wrong", "justice", "mercy", "moral", "ought"},
    "INTERPRETATION": {"suggests", "implies", "could mean", "interprets", "reading"},
    "CLASSIFICATION": {"classify", "taxonomy", "schema", "label", "category"},
    "EXPERIENTIAL_REPORT": {"i felt", "i experienced", "it seemed", "i saw"},
}

OVERCLAIM_TERMS = ["proves", "undeniable", "definitive", "settled", "impossible", "only", "destroyed", "refuted"]


def process(data: dict) -> str:
    text = (data.get("selection") or data.get("clipboard") or "").strip()
    if not text:
        return "No text supplied. Paste or select text, then run Classification Quick Map."

    lowered = f" {text.lower()} "
    domain = _pick_domain(lowered)
    audience = _pick_audience(lowered)
    use_direction = _pick_use(lowered)
    risk = _pick_risk(lowered)
    vector = _build_vector(lowered)
    claim_modes = _pick_claim_modes(lowered)
    flags = [term for term in OVERCLAIM_TERMS if term in lowered]

    lines = [
        "STRATUM / CLASSIFICATION QUICK MAP",
        "",
        f"Domain: {domain}",
        "Entity: X",
        "State: W",
        f"Audience: {audience}",
        f"Use: {use_direction}",
        f"Risk: {risk}",
        f"Vector: {vector}",
        f"Dominants: {', '.join(_dominants(vector)) or 'none'}",
        f"Likely claim modes: {', '.join(claim_modes)}",
        f"Review flags: {', '.join(flags) if flags else 'none obvious'}",
        "",
        "Reminder: address is not truth. Run evidence, claim-type, and repair passes separately.",
    ]
    return "\n".join(lines)


def _pick_domain(text: str) -> str:
    scores = Counter()
    for domain, words in DOMAIN_KEYWORDS.items():
        for word in words:
            if word in text:
                scores[domain] += 1
    return scores.most_common(1)[0][0] if scores else "UNKNOWN"


def _pick_audience(text: str) -> str:
    if any(word in text for word in ("peer review", "journal", "academic", "paper")):
        return "ACADEMIC"
    if any(word in text for word in ("public", "reader", "audience", "website")):
        return "PUBLIC_RESEARCH"
    if any(word in text for word in ("team", "internal", "ops", "workflow")):
        return "TEAM"
    return "AI_RESEARCH"


def _pick_use(text: str) -> str:
    if any(word in text for word in ("log", "record", "archive", "ledger")):
        return "R"
    if any(word in text for word in ("must", "required", "contract", "policy", "shall")):
        return "B"
    if any(word in text for word in ("synthesize", "transform", "reframe", "convert", "repair")):
        return "T"
    return "I"


def _pick_risk(text: str) -> str:
    if any(word in text for word in ("medical", "safety", "life-critical")):
        return "R4"
    if any(word in text for word in ("legal", "financial", "liability", "reputation")):
        return "R3"
    if any(word in text for word in ("private", "personal", "sensitive", "pii")):
        return "R2"
    if any(word in text for word in ("research", "draft", "framework")):
        return "R1"
    return "R0"


def _build_vector(text: str) -> str:
    signals = {
        "G": any(word in text for word in ("axiom", "authority", "law", "ground", "canon", "foundational")),
        "M": any(word in text for word in ("process", "mechanism", "workflow", "operator", "algorithm", "how it works")),
        "E": any(word in text for word in ("corrupt", "fragment", "redact", "contradict", "damaged", "noisy")),
        "S": any(word in text for word in (" i ", " my ", " myself", "identity", "self", "personhood")),
        "T": any(word in text for word in ("before", "after", "sequence", "timeline", "history", "version")),
        "K": any(word in text for word in ("data", "equation", "definition", "proof", "fact", "claim", "knowledge")),
        "R": any(word in text for word in ("relation", "bond", "network", "covenant", "dependency", "link")),
        "Q": any(word in text for word in ("felt", "experience", "emotion", "perception", "lived")),
        "F": any(word in text for word in ("faith", "trust", "belief", "reliance", "uncertainty")),
        "C": any(word in text for word in ("unify", "cohere", "integrate", "reconcile", "system", "whole")),
    }
    return "".join(f"{key}{3 if value else 0}" for key, value in signals.items())


def _dominants(vector: str) -> list[str]:
    pairs = re.findall(r"([A-Z])([03])", vector)
    return [name for name, score in pairs if score == "3"]


def _pick_claim_modes(text: str) -> list[str]:
    scores = Counter()
    for mode, words in TRUTH_MODES.items():
        for word in words:
            if word in text:
                scores[mode] += 1
    modes = [mode for mode, _ in scores.most_common(3)]
    return modes or ["UNKNOWN"]
