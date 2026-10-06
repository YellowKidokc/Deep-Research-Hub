from collections import Counter
import re

def process(data: dict) -> str:
    text = data.get("selection") or data.get("clipboard") or ""
    words = [w.lower() for w in re.findall(r"[A-Za-z']+", text) if len(w) > 3]
    common = Counter(words).most_common(10)
    if not common:
        return "No motifs found in the available text."
    return "Repeated motifs/terms:\n" + "\n".join(f"- {word}: {count}" for word, count in common)
