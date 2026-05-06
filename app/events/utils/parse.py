import html
import re

from app.articles.utils.parse import parse_authors

# Separa "autores . resto" usando el separador real de estos textos: " . "
AUTHORS_SPLIT_PATTERN = re.compile(r"\s+\.\s+")

DOC_TYPE_PREFIX_PATTERN = re.compile(
    r"^(?:Artículo\s+Completo|Artículo\s+Breve|Resumen|Poster|Póster|Trabajo\s+Completo)\.\s*",
    re.IGNORECASE,
)

VENUE_KIND_PATTERN = re.compile(
    r"\b(Congreso|Simposio|Encuentro|Feria|Jornada|Workshop|Conferencia|Seminario)\.\s*",
    re.IGNORECASE,
)

YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

# Ej.: "Congreso. CASE 2019. : Rosario. 2019 - . Universidad ..."
VENUE_DETAIL_PATTERN = re.compile(
    r"(?P<kind>Congreso|Simposio|Encuentro|Feria|Jornada|Workshop|Conferencia|Seminario)\.\s*"
    r"(?P<event>.+?)\.\s*:\s*(?P<place>[^.]{2,}?)\.\s*(?P<year>\b(?:19|20)\d{2}\b)",
    re.IGNORECASE,
)


def _split_authors_and_rest(text: str) -> tuple[str, str]:
    m = AUTHORS_SPLIT_PATTERN.search(text or "")
    if not m:
        raise ValueError("No se pudo separar autores del resto")
    return (text[: m.start()].strip(), text[m.end() :].strip())


def _extract_title(rest: str) -> str:
    r = re.sub(r"\s+", " ", (rest or "").strip())
    r = DOC_TYPE_PREFIX_PATTERN.sub("", r).strip()

    # Preferimos cortar antes de "Congreso./Simposio./..." si aparece.
    m = VENUE_KIND_PATTERN.search(r)
    if m:
        title = r[: m.start()].strip()
        # Si el título termina con punto, lo quitamos
        title = title.rstrip(". ").strip()
        return title

    # Fallback: hasta el primer punto.
    dot = r.find(".")
    if dot > 0:
        return r[:dot].strip()

    return r


def parse_event_work(text: str) -> dict:
    authors_raw, rest = _split_authors_and_rest(text)
    authors = parse_authors(authors_raw)

    title = _extract_title(rest)
    title = title.lstrip(". ").strip()
    title = html.unescape(title)

    year = None
    year_m = YEAR_PATTERN.search(text or "")
    if year_m:
        year = int(year_m.group(0))

    venue_kind = None
    venue_event = None
    place = None

    vd = VENUE_DETAIL_PATTERN.search(text or "")
    if vd:
        venue_kind = (vd.group("kind") or "").strip().lower()
        venue_event = re.sub(r"\s+", " ", (vd.group("event") or "")).strip()
        place = re.sub(r"\s+", " ", (vd.group("place") or "")).strip()
        if year is None and vd.group("year"):
            year = int(vd.group("year"))

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue_kind": venue_kind,
        "venue_event": venue_event,
        "place": place,
    }
