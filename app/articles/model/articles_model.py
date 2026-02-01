from pydantic import BaseModel


class ArticleResponseModel(BaseModel):
    articles: list[dict]
    count: int | None = None
