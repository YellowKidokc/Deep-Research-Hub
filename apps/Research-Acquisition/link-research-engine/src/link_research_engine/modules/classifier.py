from urllib.parse import urlparse


def classify_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "wikipedia.org" in host:
        return "encyclopedic"
    if host.endswith(".gov"):
        return "government"
    if host.endswith(".edu"):
        return "academic"
    if "archive.org" in host:
        return "archive"
    return "general"
