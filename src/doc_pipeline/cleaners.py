import re


def clean_extracted_text(text: str) -> str:
    """Removes extra whitespaces, junk characters, and normalizes breaks."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()
