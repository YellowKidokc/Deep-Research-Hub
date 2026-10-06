from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLASSIFICATION_DIR = ROOT / "06_engines" / "classification"
QUICK_REF = CLASSIFICATION_DIR / "NABLA_CHI_CLASSIFICATION_QUICK_REFERENCE.md"
FULL_STANDARD = CLASSIFICATION_DIR / "NABLA_CHI_UNIVERSAL_CLASSIFICATION_STANDARD_v1.0.md"


def process(data: dict) -> str:
    selection = (data.get("selection") or data.get("clipboard") or "").strip()
    quick_text = QUICK_REF.read_text(encoding="utf-8") if QUICK_REF.exists() else "Quick reference missing."
    lines = [
        "STRATUM / CLASSIFICATION CANON",
        "",
        f"Folder: {CLASSIFICATION_DIR}",
        f"Quick reference: {QUICK_REF}",
        f"Full standard: {FULL_STANDARD}",
        "",
    ]
    if selection:
        lines.extend(
            [
                "Selected text detected.",
                "Recommended pass order:",
                "1. classification_quick_map",
                "2. overclaim_detector",
                "3. adversarial_check",
                "4. full_audit",
                "",
            ]
        )
    lines.append(quick_text)
    return "\n".join(lines)
