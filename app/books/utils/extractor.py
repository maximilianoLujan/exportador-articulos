from app.books.utils.block_finder import find_book_block
from app.books.utils.clean_noise import clean_book_noise
from app.books.utils.isbn_splitter import ISBN_PATTERN, split_by_isbn
from app.importer.utils.text_cleaning import clean_text


def extract_books(raw_text: str) -> list[str]:
    """Extrae libros (raw strings) desde el texto completo del PDF."""

    block = find_book_block(raw_text)
    if not block:
        return []

    block = clean_book_noise(block)

    candidates = split_by_isbn(block)

    # Si no hay ISBN en ningún candidato, lo tratamos como un único item.
    if not any(ISBN_PATTERN.search(c or "") for c in candidates):
        candidates = [block]

    return [clean_text(c).strip() for c in candidates if clean_text(c).strip()]
