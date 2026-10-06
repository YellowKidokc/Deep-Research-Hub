from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_LINK_TARGETS = {
    "local_models": r"\\NAS\engines\local_models",
    "tts": r"\\NAS\engines\tts",
    "stt": r"\\NAS\engines\stt",
}


def describe_targets() -> dict[str, str]:
    return dict(ENGINE_LINK_TARGETS)
