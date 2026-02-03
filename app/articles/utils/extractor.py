from app.articles.utils.block_finder import find_article_block
from app.articles.utils.clean_noise import clean_article_noise
from app.articles.utils.issn_splitter import ISSN_PATTERN, split_by_issn
from app.articles.utils.page_splitter import split_by_pages
from app.articles.utils.section_splitter import split_block_by_category
from app.importer.utils.text_cleaning import clean_text


def _extract_articles_from_block(block_text: str) -> list[str]:
    block_text = clean_article_noise(block_text)

    candidates = split_by_issn(block_text)

    articles: list[str] = []
    for candidate in candidates:
        if ISSN_PATTERN.search(candidate):
            articles.append(candidate.strip())
        else:
            articles.extend(split_by_pages(candidate))

    return [clean_text(article) for article in articles]


def extract_articles_with_category(raw_text: str) -> list[dict]:
    """Extrae artículos y les asigna categoría si detecta headings dentro del bloque."""

    block = find_article_block(raw_text)
    if not block:
        return []

    results: list[dict] = []
    for category, section_text in split_block_by_category(block):
        for article in _extract_articles_from_block(section_text):
            results.append({"raw": article, "category": category})

    return results


def extract_articles(raw_text: str) -> list[str]:
    return [r["raw"] for r in extract_articles_with_category(raw_text)]
