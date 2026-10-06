def process(data: dict) -> str:
    text = data.get("selection") or data.get("clipboard") or ""
    return "\n".join([
        f"1. {text}",
        f"2. In short: {text}",
        f"3. Put another way, {text}",
        f"4. A clearer version: {text}",
        f"5. More directly: {text}",
    ])
