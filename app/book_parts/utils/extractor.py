from app.book_parts.utils.block_finder import find_book_parts_block
from app.book_parts.utils.clean_noise import clean_book_parts_noise
from app.book_parts.utils.issn_splitter import ISBN_PATTERN, split_by_isbn
from app.importer.utils.text_cleaning import clean_text


def extract_book_parts(raw_text: str) -> list[str]:

    block = find_book_parts_block(raw_text)
    if not block:
        return []

    block = clean_book_parts_noise(block)

    candidates = split_by_isbn(block)

    # Si no hay ISBN en ningún candidato, lo tratamos como un único item.
    if not any(ISBN_PATTERN.search(c or "") for c in candidates):
        candidates = [block]

    return [clean_text(c).strip() for c in candidates if clean_text(c).strip()]