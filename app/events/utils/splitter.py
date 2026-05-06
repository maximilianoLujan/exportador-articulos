from __future__ import annotations

import re

def split_event_works(block_text: str) -> list[str]:
    text = (block_text or "").strip()
    if not text:
        return []

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Una línea candidata a "inicio" suele ser:
    # - lista de autores con ';' (puede estar wrappeada)
    # - o autor único que ya trae el tipo: "APELLIDO, NOMBRE . Artículo ..."
    author_line_start = re.compile(r"^[A-ZÁÉÍÓÚÑ].*;")
    author_single_with_type = re.compile(
        r"^[A-ZÁÉÍÓÚÑ].{0,160}\s+\.\s+(Artículo|Resumen|Poster|Póster|Trabajo)\b",
        re.IGNORECASE,
    )

    BODY_TOKENS = {
        "ARTÍCULO COMPLETO.",
        "ARTICULO COMPLETO.",
        "ARTÍCULO BREVE.",
        "ARTICULO BREVE.",
        "RESUMEN.",
        "POSTER.",
        "PÓSTER.",
        "POSTER ",
        "TRABAJO COMPLETO.",
        "CONGRESO.",
        "SIMPOSIO.",
        "ENCUENTRO.",
        "FERIA.",
        "JORNADA.",
        "WORKSHOP.",
        "CONFERENCIA.",
        "SEMINARIO.",
    }

    def _buffer_has_body(buf_text: str) -> bool:
        u = (buf_text or "").upper()
        return any(tok in u for tok in BODY_TOKENS)

    items: list[str] = []
    buf: list[str] = []

    for line in lines:
        is_author_start = bool(
            author_line_start.match(line) or author_single_with_type.match(line)
        )
        if is_author_start and buf and _buffer_has_body(" ".join(buf)):
            items.append(" ".join(buf).strip())
            buf = [line]
            continue

        buf.append(line)

    if buf:
        items.append(" ".join(buf).strip())

    return items
