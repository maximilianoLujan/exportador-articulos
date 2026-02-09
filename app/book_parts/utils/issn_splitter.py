import re

# Acepta ISBN-10/13 con guiones o espacios; el PDF suele venir con guiones.
ISBN_PATTERN = re.compile(
    r"ISBN\s*(?:97[89][\-\s]?)?\d[\d\-\s]{8,20}[\dX]",
    re.IGNORECASE,
)


def split_by_isbn(block: str) -> list[str]:
    """Parte un bloque en items, usando la aparición de ISBN como delimitador de fin."""

    parts = re.split(f"({ISBN_PATTERN.pattern})", block or "", flags=re.IGNORECASE)

    items: list[str] = []
    buffer = ""

    for part in parts:
        if not part:
            continue

        if ISBN_PATTERN.fullmatch(part.strip()):
            buffer += " " + part
            if buffer.strip():
                items.append(buffer.strip())
            buffer = ""
        else:
            buffer += " " + part

    if buffer.strip():
        # Puede quedar un último libro sin ISBN (o ISBN perdido por OCR)
        items.append(buffer.strip())

    return items