import re

SECTION_TITLES_CUT = [
    "TRABAJOS EN EVENTOS C-T PUBLICADOS",
    "PARTES DE LIBRO",
    "LIBROS",
]

ARTICLE_END_PATTERNS = [
    r"p\.\s*\d+\s*-\s*\d+\.",
    r"vol\.\s*\d+,\s*n°\s*\d+,?",
    r"vol\.\s*\d+,?",
]

SECTION_TITLES_REGEX = "|".join(re.escape(t) for t in SECTION_TITLES_CUT)
