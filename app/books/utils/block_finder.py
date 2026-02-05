import re

# Encabezado de sección típico (en mayúsculas) con "Total: N".
# Ej.: "TRABAJOS EN EVENTOS C-T PUBLICADOS Total: 22"
SECTION_HEADER_TOTAL_PATTERN = re.compile(
    r"^\s*[A-ZÁÉÍÓÚÑ0-9][A-ZÁÉÍÓÚÑ0-9\-\s\./\(\)]+?\s+Total:\s*\d+\s*$",
    re.MULTILINE,
)

BOOK_HEADER_PATTERN = re.compile(
    r"^\s*LIBROS\s+Total:\s*\d+\s*$",
    re.MULTILINE,
)

PUBLISHED_LINE_PATTERN = re.compile(
    r"^\s*Publicado\s+Total\s+publicado:\s*\d+\s*$",
    re.MULTILINE,
)


def find_book_block(raw_text: str) -> str | None:
    """Devuelve el bloque de texto correspondiente a la sección LIBROS."""

    text = raw_text or ""
    header = BOOK_HEADER_PATTERN.search(text)
    if not header:
        return None

    start = header.end()

    # Salta la línea opcional de "Publicado Total publicado" si aparece inmediatamente.
    pub = PUBLISHED_LINE_PATTERN.search(text, pos=start)
    if (
        pub
        and pub.start() == start
        or (pub and text[start : pub.start()].strip() == "")
    ):
        # Asegura que sólo saltemos si está pegada al header (permitiendo \n).
        start = pub.end()

    # El bloque termina donde arranca el próximo encabezado tipo "... Total: N".
    next_header = SECTION_HEADER_TOTAL_PATTERN.search(text, pos=start)
    end = next_header.start() if next_header else len(text)

    body = text[start:end].strip()
    return body or None
