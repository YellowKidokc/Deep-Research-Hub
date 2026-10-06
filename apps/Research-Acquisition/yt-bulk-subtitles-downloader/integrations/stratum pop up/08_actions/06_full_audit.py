def process(data: dict) -> str:
    text = data.get("selection") or data.get("clipboard") or ""
    words = text.split()
    return f"Length: {len(text)} chars / {len(words)} words\nStarts with: {text[:80]}\nChecks: clarity, claims, grammar, repetition."
