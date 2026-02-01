import re


def clean_text(text: str) -> str:
    text = re.sub(r"\*?\d{14,}\*?", " ", text)
    text = re.sub(r"Página\s+\d+\s+de\s+\d+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
