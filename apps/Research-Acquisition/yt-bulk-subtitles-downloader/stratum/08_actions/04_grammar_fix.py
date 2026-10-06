def process(data: dict) -> str:
    text = data.get("selection") or data.get("clipboard") or ""
    return " ".join(text.replace(" ,", ",").replace(" .", ".").split())
