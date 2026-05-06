from pydantic import BaseModel


class ArticlesModel(BaseModel):
    items: list[dict]
    count: int | None = None


class BooksModel(BaseModel):
    items: list[dict]
    count: int | None = None

class BookPartsModel(BaseModel):
    items: list[dict]
    count: int | None = None


class EventWorksModel(BaseModel):
    items: list[dict]
    count: int | None = None

class ImporterResponseModel(BaseModel):
    articles: ArticlesModel
    books: BooksModel
    book_parts: BookPartsModel
    event_works: EventWorksModel


class SummaryModel(BaseModel):
    summary: ImporterResponseModel
