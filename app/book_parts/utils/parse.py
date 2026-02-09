import html
import re

from app.articles.utils.parse import parse_authors
from app.book_parts.utils.issn_splitter import ISBN_PATTERN

BOOK_PARTS_MAIN_PATTERN = re.compile(
    r"^(?P<authors>.+?)\s+\.\s+(?P<title>.+?)\.\s+.*?(?P<year>\b(?:19|20)\d{2}\b)",
    re.DOTALL,
)

PAGES_PATTERN = re.compile(r"\bp\.?\s*(?P<pages>\d+(?:\s*-\s*\d+)?)\b", re.IGNORECASE)

PLACE_PUBLISHER_PATTERN = re.compile(
    r"(?P<place>[A-Za-zÁÉÍÓÚÑáéíóúñ][A-Za-zÁÉÍÓÚÑáéíóúñ\s\-,]{2,}?)\s*:\s*(?P<publisher>[^,]{2,}?)\s*,\s*(?P<year>\b(?:19|20)\d{2}\b)",
)

PUBLISHER_YEAR_PATTERN = re.compile(
    r":\s*(?P<publisher>[^,]{2,}?)\s*,\s*(?P<year>\b(?:19|20)\d{2}\b)",
)

COLLABORATOR_PREFIX_RE = re.compile(r"^\s*(?:EDITOR|EDITORES?|ED\.?|EDS\.?)\s+(.+)$", re.IGNORECASE)

def split_authors_and_collaborators(authors: list[str]) -> tuple[list[str], list[str]]:
    clean_authors: list[str] = []
    collaborators: list[str] = []

    for a in authors or []:
        s = (a or "").strip()
        if not s:
            continue

        m = COLLABORATOR_PREFIX_RE.match(s)
        if m:
            name = (m.group(1) or "").strip(" -–—,;:. \t")
            if name:
                collaborators.append(name.upper())
            continue

        clean_authors.append(s.upper())

    def uniq(xs: list[str]) -> list[str]:
        seen = set()
        out = []
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return uniq(clean_authors), uniq(collaborators)


def _extract_place_publisher_near_year(
    text: str, year: int
) -> tuple[str | None, str | None]:
    year_str = str(year)
    year_idx = (text or "").rfind(year_str)
    if year_idx < 0:
        return None, None

    window_start = max(0, year_idx - 400)
    window = text[window_start : year_idx + len(year_str)]

    place = None
    publisher = None

    # Preferimos "Lugar: Editorial, Año".
    matches = [
        m
        for m in PLACE_PUBLISHER_PATTERN.finditer(window)
        if m.group("year") == year_str
    ]
    if matches:
        m = matches[-1]
        candidate_publisher = (m.group("publisher") or "").strip()
        if ":" not in candidate_publisher:
            place = re.sub(r"\s+", " ", (m.group("place") or "")).strip()
            publisher = re.sub(r"\s+", " ", candidate_publisher).strip()
            if place:
                return place, publisher

    # Fallback: sólo editorial cerca del año.
    pub_matches = [
        m
        for m in PUBLISHER_YEAR_PATTERN.finditer(window)
        if m.group("year") == year_str
    ]
    if pub_matches:
        m = pub_matches[-1]
        publisher = re.sub(r"\s+", " ", (m.group("publisher") or "")).strip()
        return None, publisher

    return None, None


def _normalize_isbn(raw: str | None) -> str | None:
    if not raw:
        return None
    # deja dígitos, X y guiones
    s = raw.upper().strip()
    s = s.replace("ISBN", "").strip()
    s = re.sub(r"[^0-9X\-]", "", s)
    return s or None


def parse_book_parts(book_parts_text: str) -> dict:
    match = BOOK_PARTS_MAIN_PATTERN.search(book_parts_text or "")
    if not match:
        raise ValueError("No se pudo parsear el libro")

    authors_raw = parse_authors(match.group("authors"))
    authors, collaborators = split_authors_and_collaborators(authors_raw)
    title = re.sub(r"\s+", " ", match.group("title") or "").strip()
    title = title.lstrip(". ").strip()
    title = html.unescape(title)

    year = int(match.group("year"))
    place, publisher = _extract_place_publisher_near_year(book_parts_text, year)

    isbn_match = ISBN_PATTERN.search(book_parts_text or "")
    isbn = _normalize_isbn(isbn_match.group(0) if isbn_match else None)

    pages_match = PAGES_PATTERN.search(book_parts_text or "")
    pages = (pages_match.group("pages") if pages_match else None) or None

    return {
        "title": title,
        "authors": authors,
        "collaborators": collaborators,
        "year": year,
        "place": place,
        "publisher": publisher,
        "pages": pages,
        "isbn": isbn,
    }