from app.articles.model.articles_model import ArticleResponseModel
from app.articles.utils.extractor import extract_articles
from app.articles.utils.parse import parse_article
from app.articles.utils.postprocessor import postprocess_articles


class ArticlesService:
    def read_articles(self, raw_text: str) -> ArticleResponseModel:
        articles = extract_articles(raw_text)
        articles = postprocess_articles(articles)
        parsed_articles = [parse_article(article) for article in articles]
        articles_count = len(parsed_articles)
        return ArticleResponseModel(articles=parsed_articles, count=articles_count)
