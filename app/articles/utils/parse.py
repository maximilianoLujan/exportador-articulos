import html
import re

ARTICLE_MAIN_PATTERN = re.compile(
    r"""
    ^
    (?P<authors>.+?)                  # autores
    \s*\.\s+                          # punto separador
    (?P<title>.+?)                    # título (puede tener guiones)
    \.\s+                             # fin de título
    .*?
    (?P<year>\b(19|20)\d{2}\b)
    """,
    re.VERBOSE | re.DOTALL,
)


def parse_authors(authors_raw: str) -> list[str]:
    return [re.sub(r"\s+", " ", a).strip() for a in authors_raw.split(";") if a.strip()]


def parse_article(article: str) -> dict:
    match = ARTICLE_MAIN_PATTERN.search(article)
    if not match:
        raise ValueError("No se pudo parsear el artículo")

    authors = parse_authors(match.group("authors"))
    title = re.sub(r"\s+", " ", match.group("title")).strip()
    title = title.lstrip(". ").strip()
    title = html.unescape(title)
    year = int(match.group("year"))

    return {
        "title": title,
        "authors": authors,
        "year": year,
    }
