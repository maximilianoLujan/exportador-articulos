from app.articles.model.articles_model import ArticleResponseModel
from app.articles.service.articles_service import ArticlesService
from app.importer.utils.pdf_reader import extract_text_from_pdf


class ImporterService:
    def __init__(self, articles_service: ArticlesService):
        self.articles_service = articles_service
        self._raw_text: str | None = None

    def _get_raw_text(self, file: bytes) -> str:
        if self._raw_text is None:
            self._raw_text = extract_text_from_pdf(file)
        return self._raw_text

    def import_data(self, file: bytes) -> ArticleResponseModel:
        raw_text = self._get_raw_text(file)

        articles = self.articles_service.read_articles(raw_text)

        return articles


def get_importer_service() -> ImporterService:
    articles_service = ArticlesService()
    return ImporterService(articles_service)
