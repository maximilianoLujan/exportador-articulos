from app.book_parts.utils.extractor import extract_book_parts


class BookPartsService:
    def extract_raw_book_parts(self, raw_text: str) -> list[str]:
        return extract_book_parts(raw_text)