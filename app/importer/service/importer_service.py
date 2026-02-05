from fastapi import Depends
from sqlalchemy.orm import Session

from app.articles.service.articles_service import ArticlesService
from app.books.service.books_service import BooksService
from app.db.database import get_db
from app.db.models import ItemType
from app.importer.model.importer_model import (
    ArticlesModel,
    BooksModel,
    ImporterResponseModel,
    SummaryModel,
)
from app.importer.repository.importer_repository import (
    ImporterRepository,
    fingerprint_from_fields,
)
from app.importer.utils.pdf_reader import extract_text_from_pdf


class ImporterService:
    def __init__(
        self,
        articles_service: ArticlesService,
        books_service: BooksService,
        repo: ImporterRepository,
    ):
        self.articles_service = articles_service
        self.books_service = books_service
        self.repo = repo
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
    ) -> SummaryModel:
        raw_text = self._get_raw_text(file)

        doc = self.repo.get_or_create_document(
            blob=file, filename=filename, content_type=content_type
        )
        run = self.repo.start_process(
            document_id=doc.id, pipeline="articles_v1", raw_text=raw_text
        )

        parsed_articles: list[dict] = []
        parsed_books: list[dict] = []

        try:
            raw_articles = self.articles_service.extract_raw_articles_with_category(
                raw_text
            )
            for raw_article, category in raw_articles:
                try:
                    from app.articles.utils.parse import parse_article
                    from app.articles.utils.section_splitter import (
                        infer_article_category,
                    )

                    data = parse_article(raw_article)
                    final_category = infer_article_category(
                        article_text=raw_article,
                        parsed=data,
                        heading_category=category,
                    )
                    if final_category is not None:
                        data["category"] = final_category
                    parsed_articles.append(data)
                    fp = fingerprint_from_fields(
                        data.get("title", ""),
                        str(data.get("year", "")),
                        (data.get("authors") or [""])[0],
                    )
                    self.repo.add_item(
                        run_id=run.id,
                        item_type=ItemType.article,
                        raw=raw_article,
                        data=data,
                        fingerprint=fp,
                    )
                except Exception as ex:
                    self.repo.add_item(
                        run_id=run.id,
                        item_type=ItemType.article,
                        raw=raw_article,
                        data={"category": category} if category is not None else {},
                        fingerprint=None,
                        parse_error=str(ex),
                    )

            raw_books = self.books_service.extract_raw_books(raw_text)
            for raw_book in raw_books:
                try:
                    from app.books.utils.parse import parse_book

                    data = parse_book(raw_book)
                    parsed_books.append(data)
                    fp = fingerprint_from_fields(
                        data.get("title", ""),
                        str(data.get("year", "")),
                        (data.get("authors") or [""])[0],
                    )
                    self.repo.add_item(
                        run_id=run.id,
                        item_type=ItemType.book,
                        raw=raw_book,
                        data=data,
                        fingerprint=fp,
                    )
                except Exception as ex:
                    self.repo.add_item(
                        run_id=run.id,
                        item_type=ItemType.book,
                        raw=raw_book,
                        data={},
                        fingerprint=None,
                        parse_error=str(ex),
                    )

            self.repo.finish_process_success(run)
            self.repo.db.commit()
        except Exception as ex:
            self.repo.finish_process_failed(run, str(ex))
            self.repo.db.commit()
            raise

        return SummaryModel(
            summary=ImporterResponseModel(
                articles=ArticlesModel(
                    items=parsed_articles, count=len(parsed_articles)
                ),
                books=BooksModel(items=parsed_books, count=len(parsed_books)),
            )
        )


def get_importer_service(db: Session = Depends(get_db)) -> ImporterService:
    articles_service = ArticlesService()
    books_service = BooksService()
    repo = ImporterRepository(db)
    return ImporterService(articles_service, books_service, repo)
