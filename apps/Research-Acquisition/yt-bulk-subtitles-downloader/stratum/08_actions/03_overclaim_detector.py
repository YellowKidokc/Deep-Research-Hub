def process(data: dict) -> str:
    text = data.get("selection") or data.get("clipboard") or ""
    flags = [w for w in ["always", "never", "guaranteed", "proves", "everyone", "no one"] if w in text.lower()]
    if not flags:
        return "No obvious overclaim trigger words found. Still verify factual claims before publishing."
    return "Potential overclaim terms: " + ", ".join(flags) + "\nConsider softening or adding evidence."
