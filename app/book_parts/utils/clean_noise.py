import re

LEADING_SYMBOLS_PATTERN = re.compile(r"^[\*\-–—•·]+\s*")

CE_START_PATTERN = re.compile(r"^(?:CE\*?\s+)+", re.IGNORECASE)
CE_CODE_PATTERN = re.compile(r"\b\d{8,}CE\b", re.IGNORECASE)
PAGE_NUMBERING_PATTERN = re.compile(
    r"Página\s+\d+\s+de\s+\d+",
    re.IGNORECASE,
)


def clean_book_parts_noise(text: str) -> str:
    lines = (text or "").splitlines()
    cleaned_lines: list[str] = []

    for line in lines:
        line = CE_START_PATTERN.sub("", line)
        line = CE_CODE_PATTERN.sub("", line)
        line = PAGE_NUMBERING_PATTERN.sub("", line)
        line = line.strip()
        line = LEADING_SYMBOLS_PATTERN.sub("", line).strip()
        if line:
            cleaned_lines.append(line)
            
    return " ".join(cleaned_lines)