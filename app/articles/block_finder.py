import re

from app.config import SECTION_TITLES_REGEX

ARTICLE_BLOCK_PATTERN = re.compile(
    rf"""
    ARTICULOS\ Total:\s*\d+.*?
    Publicado\ Total\ publicado:\s*\d+
    (.*?)
    (?:{SECTION_TITLES_REGEX})
    """,
    re.DOTALL | re.VERBOSE,
)


def find_article_block(raw_text: str) -> str | None:
    match = ARTICLE_BLOCK_PATTERN.search(raw_text)
    return match.group(1) if match else None
