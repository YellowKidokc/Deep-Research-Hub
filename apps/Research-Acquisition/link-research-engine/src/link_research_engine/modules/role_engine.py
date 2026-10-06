from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class CandidateLink:
    case_title: str
    url: str
    title: str
    snippet: str
    provider: str
    source_type: str = "general"


@dataclass
class RoleDecision:
    keep: bool
    role: str
    score: int
    reason: str
    source_domain: str


def load_role_rules(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _host(url: str) -> str:
    return urlparse(url).netloc.lower()


def classify_link_role(candidate: CandidateLink, rules: dict) -> RoleDecision:
    host = _host(candidate.url)
    allowed_domains = [d.lower() for d in rules.get("allowed_domains", [])]
    blocked_domains = [d.lower() for d in rules.get("blocked_domains", [])]
    blocked_patterns = [p.lower() for p in rules.get("blocked_url_patterns", [])]
    preferred_patterns = [p.lower() for p in rules.get("preferred_url_patterns", [])]

    if any(blocked in host for blocked in blocked_domains):
        return RoleDecision(False, "blocked", 0, "blocked_domain", host)

    lower_url = candidate.url.lower()
    if any(pattern in lower_url for pattern in blocked_patterns):
        return RoleDecision(False, "discard", 5, "blocked_url_pattern", host)

    score = 10
    role = "related_source"
    reason_parts: list[str] = []

    if any(host.endswith(domain) or domain in host for domain in allowed_domains):
        score += 50
        role = "trusted_source"
        reason_parts.append("allowed_domain")

    if candidate.source_type in rules.get("preferred_source_types", []):
        score += 20
        reason_parts.append("preferred_source_type")

    if any(pattern in lower_url for pattern in preferred_patterns):
        score += 10
        reason_parts.append("preferred_url_pattern")

    title_text = f"{candidate.title} {candidate.snippet}".lower()
    case_tokens = [token for token in candidate.case_title.lower().split() if len(token) > 2]
    token_hits = sum(1 for token in case_tokens if token in title_text)
    score += min(token_hits * 5, 20)
    if token_hits:
        reason_parts.append(f"token_hits:{token_hits}")

    keep = score >= 40
    if keep and role != "trusted_source":
        role = "candidate_source"
    if not keep:
        role = "review_or_discard"
    reason = ",".join(reason_parts) if reason_parts else "low_signal"
    return RoleDecision(keep, role, score, reason, host)
