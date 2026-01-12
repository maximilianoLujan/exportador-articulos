from app.articles.block_finder import find_article_block
from app.articles.issn_splitter import ISSN_PATTERN, split_by_issn
from app.articles.page_splitter import split_by_pages
from app.text_cleaning import clean_text


def extract_articles(raw_text: str) -> list[str]:
    block = find_article_block(raw_text)
    if not block:
        return []

    candidates = split_by_issn(block)

    articles: list[str] = []

    for candidate in candidates:
        if ISSN_PATTERN.search(candidate):
            articles.append(candidate.strip())
        else:
            articles.extend(split_by_pages(candidate))

    return [clean_text(article) for article in articles]
