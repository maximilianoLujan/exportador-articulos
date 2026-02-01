import re

from app.config import ARTICLE_END_PATTERNS


def postprocess_articles(articles: list[str]) -> list[str]:
    processed = []

    end_pattern = re.compile(
        "(" + "|".join(ARTICLE_END_PATTERNS) + ")",
        re.IGNORECASE,
    )

    author_start_pattern = re.compile(
        r"""
        [A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\-]+
        (?:
            ,\s*[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\-]+
          |
            \s+[A-ZÁÉÍÓÚÑ]\.
        )
        """,
        re.VERBOSE,
    )

    for article in articles:
        text = article.strip()

        while True:
            split_found = False

            for match in end_pattern.finditer(text):
                end = match.end()
                remainder = text[end:].lstrip()

                if author_start_pattern.match(remainder):
                    processed.append(text[:end].strip())
                    text = remainder
                    split_found = True
                    break

            if not split_found:
                processed.append(text.strip())
                break

    return processed
