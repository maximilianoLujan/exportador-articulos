from app.books.utils.extractor import extract_books


class BooksService:
    def extract_raw_books(self, raw_text: str) -> list[str]:
        return extract_books(raw_text)
