def process(data: dict) -> str:
    text = data.get("selection") or data.get("clipboard") or ""
    text = " ".join(text.split())
    replacements = {" period": ".", " comma": ",", " question mark": "?", " exclamation point": "!"}
    lowered = text
    for old, new in replacements.items():
        lowered = lowered.replace(old, new)
    return lowered[:1].upper() + lowered[1:]
