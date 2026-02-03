from __future__ import annotations

import re
import unicodedata

CAT_CONGRESOS_INT = "Articulos Congresos Internacionales"
CAT_CONGRESOS_NAC = "Articulos Congresos Nacionales"
CAT_REVISTAS_INT = "Articulos Revistas Internacionales"
CAT_REVISTAS_NAC = "Articulos Revistas Nacionales"

CATEGORIES = {
    CAT_CONGRESOS_INT: "congresos_internacionales",
    CAT_CONGRESOS_NAC: "congresos_nacionales",
    CAT_REVISTAS_INT: "revistas_internacionales",
    CAT_REVISTAS_NAC: "revistas_nacionales",
}


_ARGENTINA_PLACES = {
    "ARGENTINA",
    "BUENOS AIRES",
    "CABA",
    "LA PLATA",
    "TANDIL",
    "ROSARIO",
    "CORDOBA",
    "CÓRDOBA",
    "MENDOZA",
    "SANTA FE",
    "MAR DEL PLATA",
    "SAN MIGUEL DE TUCUMAN",
    "SAN MIGUEL DE TUCUMÁN",
    "TUCUMAN",
    "TUCUMÁN",
    "SALTA",
    "NEUQUEN",
    "NEUQUÉN",
    "USHUAIA",
    "BARILOCHE",
    "SAN JUAN",
    "SAN LUIS",
}


_ARGENTINA_PUBLISHER_HINTS = {
    "UNIVERSIDAD NACIONAL",
    "UNIVERSIDAD DE BUENOS AIRES",
    "UNIVERSIDAD NACIONAL DE LA PLATA",
    "UNIVERSIDAD NACIONAL DEL CENTRO",
    "UNLP",
    "UBA",
    "UNCPBA",
    "CONICET",
    "INTA",
    "MINISTERIO",
    "GOBIERNO",
    "SECRETARIA DE POSTGRADO",
    "SECRETARÍA DE POSTGRADO",
    "FACULTAD",
}


_INTERNATIONAL_PUBLISHERS = {
    "ELSEVIER",
    "SPRINGER",
    "WILEY",
    "IEEE",
    "ACM",
    "TAYLOR",
    "FRANCIS",
    "SAGE",
    "MDPI",
    "NATURE",
    "OXFORD",
    "CAMBRIDGE",
    "IGI GLOBAL",
    "IOS PRESS",
}


_INTERNATIONAL_PLACES = {
    "AMSTERDAM",
    "LONDON",
    "NEW YORK",
    "BERLIN",
    "PARIS",
    "BOSTON",
    "BASEL",
    "GENEVA",
}


def _contains_any(haystack: str, needles: set[str]) -> bool:
    return any(n in haystack for n in needles)


def infer_scope_from_place_publisher(
    *, place: str | None, publisher: str | None
) -> str | None:
    """Devuelve 'nacional' | 'internacional' | None."""

    p = normalize_heading(place or "")
    pub = normalize_heading(publisher or "")

    # Nacional = Argentina (sin APIs externas)
    if "ARGENT" in p or _contains_any(p, _ARGENTINA_PLACES):
        return "nacional"

    if _contains_any(pub, _ARGENTINA_PUBLISHER_HINTS):
        return "nacional"

    # Editoriales típicamente internacionales
    if any(token in pub for token in _INTERNATIONAL_PUBLISHERS):
        return "internacional"

    # Ciudades conocidas fuera de Argentina (lista corta y segura)
    if _contains_any(p, _INTERNATIONAL_PLACES):
        return "internacional"

    # Si hay lugar explícito y no parece Argentina, entonces es internacional.
    # (Regla alineada con "nacional = Argentina".)
    if p:
        return "internacional"

    return None


def infer_venue_type_from_text(article_text: str) -> str | None:
    """Devuelve 'revistas' | 'congresos' | None."""

    h = normalize_heading(article_text)
    if "ISSN" in h or "VOL." in h or "VOLUME" in h:
        return "revistas"

    if any(
        k in h
        for k in [
            "CONGRESO",
            "CONFERENCE",
            "PROCEEDINGS",
            "ACTAS",
            "SYMPOSIUM",
            "WORKSHOP",
        ]
    ):
        return "congresos"

    # Tokens típicos de revistas/series (cuando falta ISSN en el recorte de texto)
    if "IEEE ACCESS" in h:
        return "revistas"

    if any(
        k in h
        for k in [
            "JOURNAL",
            "LETTERS",
            "REVIEWS",
            "TRANSACTIONS",
            "MAGAZINE",
            "BULLETIN",
            "REVISTA",
        ]
    ):
        return "revistas"

    return None


def infer_article_category(
    *,
    article_text: str,
    parsed: dict | None = None,
    heading_category: str | None = None,
) -> str | None:
    """Devuelve una de las 4 categorías finales o None.

    Prioridad:
    1) categoría por heading (si existe)
    2) heurística por tipo (revistas/congresos) + scope (nacional/internacional)
    """

    if heading_category is not None:
        return heading_category

    venue = infer_venue_type_from_text(article_text)
    scope = infer_scope_from_place_publisher(
        place=(parsed or {}).get("place"),
        publisher=(parsed or {}).get("publisher"),
    )

    if venue is None or scope is None:
        return None

    if venue == "revistas" and scope == "internacional":
        return CAT_REVISTAS_INT
    if venue == "revistas" and scope == "nacional":
        return CAT_REVISTAS_NAC
    if venue == "congresos" and scope == "internacional":
        return CAT_CONGRESOS_INT
    if venue == "congresos" and scope == "nacional":
        return CAT_CONGRESOS_NAC

    return None


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def normalize_heading(line: str) -> str:
    line = _strip_accents(line or "")
    line = re.sub(r"\s+", " ", line).strip().upper()
    return line


def detect_article_category_from_heading(line: str) -> str | None:
    """Devuelve una de las 4 categorías si la línea parece un título de sección."""

    h = normalize_heading(line)
    if not h:
        return None

    # Heurística: encabezados suelen venir en mayúsculas y sin muchos números.
    if any(ch.isdigit() for ch in h):
        return None

    has_congresos = "CONGRES" in h or "EVENTOS" in h
    has_revistas = "REVIST" in h

    if not (has_congresos or has_revistas):
        return None

    is_international = "INTERNAC" in h or "INTERNACIONAL" in h
    is_national = "NACIONAL" in h

    if has_congresos and is_international:
        return CAT_CONGRESOS_INT
    if has_congresos and is_national:
        return CAT_CONGRESOS_NAC
    if has_revistas and is_international:
        return CAT_REVISTAS_INT
    if has_revistas and is_national:
        return CAT_REVISTAS_NAC

    return None


def split_block_by_category(block_text: str) -> list[tuple[str | None, str]]:
    """Divide el bloque de artículos en secciones por categoría.

    Retorna lista de (category, section_text). Si no detecta headings, devuelve [(None, block_text)].
    """

    lines = (block_text or "").splitlines()

    sections: list[tuple[str | None, list[str]]] = []
    current_category: str | None = None
    current_lines: list[str] = []
    found_any_heading = False

    for line in lines:
        maybe_cat = detect_article_category_from_heading(line)
        if maybe_cat is not None:
            found_any_heading = True
            # cerrar sección previa
            if current_lines:
                sections.append((current_category, current_lines))
            current_category = maybe_cat
            current_lines = []
            continue

        current_lines.append(line)

    if current_lines:
        sections.append((current_category, current_lines))

    if not found_any_heading:
        return [(None, block_text)]

    return [
        (cat, "\n".join(ls).strip()) for cat, ls in sections if "\n".join(ls).strip()
    ]
