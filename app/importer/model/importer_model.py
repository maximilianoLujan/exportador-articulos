from pydantic import BaseModel


class ArticlesModel(BaseModel):
    items: list[dict]
    count: int | None = None


class BooksModel(BaseModel):
    items: list[dict]
    count: int | None = None


class ImporterResponseModel(BaseModel):
    articles: ArticlesModel
    books: BooksModel


class SummaryModel(BaseModel):
    summary: ImporterResponseModel
