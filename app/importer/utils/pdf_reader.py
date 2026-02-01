import io

import pdfplumber


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    pages = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

    return "\n".join(pages)
