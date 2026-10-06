def process(data: dict) -> str:
    words = (data.get("selection") or data.get("clipboard") or "").split()
    if len(words) < 2:
        return "Need at least two words for a Markov-style continuation."
    return " ".join(words + words[: min(8, len(words))])
