import re

PAGE_PATTERN = re.compile(r"p\.\s*\d+\s*-\s*\d+")


def split_by_pages(article: str) -> list[str]:
    parts = re.split(f"({PAGE_PATTERN.pattern})", article)

    result: list[str] = []
    buffer = ""

    for part in parts:
        if PAGE_PATTERN.fullmatch(part):
            buffer += " " + part
            result.append(buffer.strip())
            buffer = ""
        else:
            buffer += " " + part

    if buffer.strip():
        result.append(buffer.strip())

    return result
