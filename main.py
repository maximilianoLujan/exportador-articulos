import os
from datetime import datetime

from app.articles.extractor import extract_articles
from app.articles.postprocessor import postprocess_articles
from app.pdf_reader import extract_text_from_pdf
from app.utils import save_json


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for filename in os.listdir("memorias"):
        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join("memorias", filename)
        text = extract_text_from_pdf(pdf_path)

        articles = extract_articles(text)
        articles = postprocess_articles(articles)

        output_path = (
            f"procesados/{timestamp}/articles_{filename.replace('.pdf', '')}.json"
        )

        save_json(output_path, articles)

        print(f"✔ {filename}: {len(articles)} articles")
        print(f"→ {output_path}")


if __name__ == "__main__":
    main()
