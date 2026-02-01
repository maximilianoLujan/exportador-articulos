from app.articles.model.articles_model import ArticleResponseModel
from app.articles.utils.extractor import extract_articles
from app.articles.utils.parse import parse_article
from app.articles.utils.postprocessor import postprocess_articles


class ArticlesService:
    def extract_raw_articles(self, raw_text: str) -> list[str]:
        articles = extract_articles(raw_text)
        return postprocess_articles(articles)

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
