import re

ARTICLE_NOISE_PATTERN = re.compile(
    r"""
    ^(?:CE\*?\s+)+ |                # CE, CE*, CE* CE al inicio
    \b\d{8,}CE\b |                  # códigos tipo 10620180100029CE
    Página\s+\d+\s+de\s+\d+ |       # numeración de páginas
    ^\s*$                           # líneas vacías
    """,
    re.IGNORECASE | re.VERBOSE,
)

LEADING_SYMBOLS_PATTERN = re.compile(r"^[\*\-–—•·\u2022]+\s*")


def clean_article_noise(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = ARTICLE_NOISE_PATTERN.sub("", line).strip()
        line = LEADING_SYMBOLS_PATTERN.sub("", line).strip()
        if line:
            cleaned_lines.append(line)

    return " ".join(cleaned_lines)
