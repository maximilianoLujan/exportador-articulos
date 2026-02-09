import re

SECTION_HEADER_TOTAL_PATTERN = re.compile(
    r"^\s*[A-ZÁÉÍÓÚÑ0-9][A-ZÁÉÍÓÚÑ0-9\-\s\./\(\)]+?\s+Total:\s*\d+\s*$",
    re.MULTILINE,
)

BOOK_PARTS_HEADER_PATTERN = re.compile(
    r"^\s*PARTES DE LIBRO\s+Total:\s*\d+\s*$",
    re.MULTILINE,
)

PUBLISHED_LINE_PATTERN = re.compile(
    r"^\s*Publicado\s+Total\s+publicado:\s*\d+\s*$",
    re.MULTILINE,
)


def find_book_parts_block(raw_text: str) -> str | None:
    """Devuelve el bloque de texto correspondiente a la sección PARTES DE LIBRO."""

    text = raw_text or ""
    header = BOOK_PARTS_HEADER_PATTERN.search(text)
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