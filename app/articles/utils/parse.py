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


PLACE_PUBLISHER_PATTERN = re.compile(
    r"""
    (?P<place>[A-Za-zÁÉÍÓÚÑáéíóúñ][A-Za-zÁÉÍÓÚÑáéíóúñ\s\-,]{2,}?)
    \s*:\s*
    (?P<publisher>[^,]{2,}?)
    \s*,\s*
    (?P<year>\b(19|20)\d{2}\b)
    """,
    re.VERBOSE,
)

# Versiones con lookahead para permitir matches solapados (ej.: un ": ... , 2024" dentro
# de otro match más largo). Esto evita falsos positivos cuando el título contiene ":".
PLACE_PUBLISHER_OVERLAP_PATTERN = re.compile(
    r"""
    (?=(?:^|[\s\(\[\{\.,;])(?P<place>[A-Za-zÁÉÍÓÚÑáéíóúñ][A-Za-zÁÉÍÓÚÑáéíóúñ\s\-,]{2,}?)
    \s*:\s*
    (?P<publisher>[^,]{2,}?)
    \s*,\s*
    (?P<year>\b(19|20)\d{2}\b))
    """,
    re.VERBOSE,
)


PUBLISHER_YEAR_PATTERN = re.compile(
    r"""
    :\s*
    (?P<publisher>[^,]{2,}?)
    \s*,\s*
    (?P<year>\b(19|20)\d{2}\b)
    """,
    re.VERBOSE,
)


PUBLISHER_YEAR_OVERLAP_PATTERN = re.compile(
    r"""
    (?=:\s*
    (?P<publisher>[^,]{2,}?)
    \s*,\s*
    (?P<year>\b(19|20)\d{2}\b))
    """,
    re.VERBOSE,
)


def parse_authors(authors_raw: str) -> list[str]:
    return [re.sub(r"\s+", " ", a).strip() for a in authors_raw.split(";") if a.strip()]


def _extract_place_publisher_near_year(
    article: str, year: int
) -> tuple[str | None, str | None]:
    year_str = str(year)
    year_idx = article.rfind(year_str)
    if year_idx < 0:
        return None, None

    window_start = max(0, year_idx - 350)
    window = article[window_start : year_idx + len(year_str)]

    place_candidates: list[tuple[int, re.Match]] = []
    publisher_candidates: list[tuple[int, re.Match]] = []

    for m in PLACE_PUBLISHER_OVERLAP_PATTERN.finditer(window):
        if m.group("year") == year_str:
            # Evita falsos positivos cuando el match abarca dos segmentos (ej. título con ':'
            # que termina incluyendo ": IEEE" dentro del publisher).
            if ":" in m.group("publisher"):
                continue
            if len(m.group("place").strip()) < 3:
                continue
            place_candidates.append((m.start(), m))

    for m in PUBLISHER_YEAR_OVERLAP_PATTERN.finditer(window):
        if m.group("year") == year_str:
            publisher_candidates.append((m.start(), m))

    if place_candidates:

        def _place_key(item: tuple[int, re.Match]) -> tuple[int, int, int]:
            start, m = item
            place = (m.group("place") or "").strip()
            return (1 if "," in place else 0, len(place), start)

        _, m = max(place_candidates, key=_place_key)
        place = re.sub(r"\s+", " ", m.group("place")).strip()
        publisher = re.sub(r"\s+", " ", m.group("publisher")).strip()
        return place, publisher

    if publisher_candidates:
        _, m = max(publisher_candidates, key=lambda t: t[0])
        publisher = re.sub(r"\s+", " ", m.group("publisher")).strip()
        return None, publisher

    return None, None


def parse_article(article: str) -> dict:
    match = ARTICLE_MAIN_PATTERN.search(article)
    if not match:
        raise ValueError("No se pudo parsear el artículo")

    authors = parse_authors(match.group("authors"))
    title = re.sub(r"\s+", " ", match.group("title")).strip()
    title = title.lstrip(". ").strip()
    title = html.unescape(title)
    year = int(match.group("year"))

    place, publisher = _extract_place_publisher_near_year(article, year)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "place": place,
        "publisher": publisher,
    }
