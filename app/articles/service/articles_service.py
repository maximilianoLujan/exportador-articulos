from app.articles.model.articles_model import ArticleResponseModel
from app.articles.utils.extractor import (
    extract_articles,
    extract_articles_with_category,
)
from app.articles.utils.parse import parse_article
from app.articles.utils.postprocessor import postprocess_articles


class ArticlesService:
    def extract_raw_articles(self, raw_text: str) -> list[str]:
        articles = extract_articles(raw_text)
        return postprocess_articles(articles)

    def extract_raw_articles_with_category(
        self, raw_text: str
    ) -> list[tuple[str, str | None]]:
        extracted = extract_articles_with_category(raw_text)
        # postprocess_articles espera lista de strings; lo aplicamos por sección-categoría.
        by_cat: dict[str | None, list[str]] = {}
        for r in extracted:
            by_cat.setdefault(r.get("category"), []).append(r["raw"])

        results: list[tuple[str, str | None]] = []
        for cat, raws in by_cat.items():
            for raw in postprocess_articles(raws):
                results.append((raw, cat))

        return results

    def read_articles(self, raw_text: str) -> ArticleResponseModel:
        articles = self.extract_raw_articles(raw_text)

        parsed_articles: list[dict] = []
        for article in articles:
            try:
                parsed_articles.append(parse_article(article))
            except ValueError:
                # Si un artículo no se puede parsear, no abortamos todo el proceso.
                # Queda registrado en BBDD durante la importación.
                continue

        articles_count = len(parsed_articles)
        return ArticleResponseModel(articles=parsed_articles, count=articles_count)
