def process(data: dict) -> str:
    text = data.get("selection") or data.get("clipboard") or ""
    return "Adversarial questions:\n- What evidence supports this?\n- What would a critic dispute?\n- Which term is ambiguous?\n\nText checked:\n" + text[:500]
