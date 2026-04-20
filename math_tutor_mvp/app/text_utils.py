import re


def normalize_text(text: str) -> str:
    """Lowercase ASCII chars, collapse whitespace; preserve Chinese characters."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    # Normalize common math notation variants
    text = text.replace("²", "^2").replace("³", "^3")
    return text
