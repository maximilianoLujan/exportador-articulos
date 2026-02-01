import re

ISSN_PATTERN = re.compile(r"ISSN\s*\d{4}-\d{3}[\dX]")


def split_by_issn(block: str) -> list[str]:
    parts = re.split(f"({ISSN_PATTERN.pattern})", block)

    articles: list[str] = []
    buffer = ""

    for part in parts:
        if ISSN_PATTERN.fullmatch(part):
            buffer += " " + part
            articles.append(buffer.strip())
            buffer = ""
        else:
            buffer += " " + part

    if buffer.strip():
        articles.append(buffer.strip())

    return articles
