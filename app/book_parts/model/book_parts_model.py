from pydantic import BaseModel


class BookPartsResponseModel(BaseModel):
    book_parts: list[dict]
    count: int | None = None
