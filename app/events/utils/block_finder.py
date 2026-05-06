import re

# Header de secciones tipo: "TRABAJOS EN EVENTOS C-T PUBLICADOS Total: 14"
SECTION_HEADER_TOTAL_PATTERN = re.compile(
    r"^\s*[A-ZÁÉÍÓÚÑ0-9][A-ZÁÉÍÓÚÑ0-9\-\s\./\(\)]+?\s+Total:\s*\d+\s*$",
    re.MULTILINE,
)

EVENT_WORKS_HEADER_PATTERN = re.compile(
    r"^\s*TRABAJOS\s+EN\s+EVENTOS\s+C-T\s+PUBLICADOS\s+Total:\s*\d+\s*$",
    re.MULTILINE,
)


def find_event_works_block(raw_text: str) -> str | None:
    """Devuelve el bloque de texto correspondiente a TRABAJOS EN EVENTOS C-T PUBLICADOS."""

    text = raw_text or ""
    header = EVENT_WORKS_HEADER_PATTERN.search(text)
    if not header:
        return None

    start = header.end()

    # El bloque termina en el próximo encabezado "... Total: N".
    next_header = SECTION_HEADER_TOTAL_PATTERN.search(text, pos=start)
    end = next_header.start() if next_header else len(text)

    body = text[start:end].strip()
    return body or None
