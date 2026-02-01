from sqlalchemy.orm import Session

from app.articles.model.articles_model import ArticleResponseModel
from app.articles.service.articles_service import ArticlesService
from app.db.models import ItemType
from app.importer.utils.pdf_reader import extract_text_from_pdf
from app.persistence.service import PersistenceService, fingerprint_from_fields


class ImporterService:
    def __init__(self, articles_service: ArticlesService, db: Session):
        self.articles_service = articles_service
        self.db = db
        self._raw_text: str | None = None

    def _get_raw_text(self, file: bytes) -> str:
        if self._raw_text is None:
            self._raw_text = extract_text_from_pdf(file)
        return self._raw_text

    def import_data(
        self,
        file: bytes,
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> ArticleResponseModel:
        raw_text = self._get_raw_text(file)

        persistence = PersistenceService(self.db)
        doc = persistence.get_or_create_document(
            blob=file, filename=filename, content_type=content_type
        )
        run = persistence.start_run(
            document_id=doc.id, pipeline="articles_v1", raw_text=raw_text
        )

        parsed_articles: list[dict] = []

        try:
            raw_articles = self.articles_service.extract_raw_articles(raw_text)
            for raw_article in raw_articles:
                try:
                    from app.articles.utils.parse import parse_article

                    data = parse_article(raw_article)
                    parsed_articles.append(data)
                    fp = fingerprint_from_fields(
                        data.get("title", ""),
                        str(data.get("year", "")),
                        (data.get("authors") or [""])[0],
                    )
                    persistence.add_item(
                        run_id=run.id,
                        item_type=ItemType.article,
                        raw=raw_article,
                        data=data,
                        fingerprint=fp,
                    )
                except Exception as ex:
                    persistence.add_item(
                        run_id=run.id,
                        item_type=ItemType.article,
                        raw=raw_article,
                        data={},
                        fingerprint=None,
                        parse_error=str(ex),
                    )

            persistence.finish_run_success(run)
            self.db.commit()
        except Exception as ex:
            persistence.finish_run_failed(run, str(ex))
            self.db.commit()
            raise

        return ArticleResponseModel(
            articles=parsed_articles, count=len(parsed_articles)
        )


def get_importer_service(db: Session) -> ImporterService:
    articles_service = ArticlesService()
    return ImporterService(articles_service, db)
