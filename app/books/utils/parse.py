import html
import re

from app.articles.utils.parse import parse_authors
from app.books.utils.isbn_splitter import ISBN_PATTERN

BOOK_MAIN_PATTERN = re.compile(
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


def parse_book(book_text: str) -> dict:
    match = BOOK_MAIN_PATTERN.search(book_text or "")
    if not match:
        raise ValueError("No se pudo parsear el libro")

    authors = parse_authors(match.group("authors"))
    title = re.sub(r"\s+", " ", match.group("title") or "").strip()
    title = title.lstrip(". ").strip()
    title = html.unescape(title)

    year = int(match.group("year"))
    place, publisher = _extract_place_publisher_near_year(book_text, year)

    isbn_match = ISBN_PATTERN.search(book_text or "")
    isbn = _normalize_isbn(isbn_match.group(0) if isbn_match else None)

    pages_match = PAGES_PATTERN.search(book_text or "")
    pages = (pages_match.group("pages") if pages_match else None) or None

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "place": place,
        "publisher": publisher,
        "pages": pages,
        "isbn": isbn,
    }
