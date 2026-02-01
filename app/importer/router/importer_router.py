from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.articles.model.articles_model import ArticleResponseModel
from app.db.database import get_db
from app.importer.service.importer_service import ImporterService, get_importer_service

router = APIRouter(prefix="/import", tags=["importer"])

MAX_PDF_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/pdf")
async def import_articles(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ArticleResponseModel:
    if file.content_type != "application/pdf":
        raise HTTPException(400, "El archivo no es un PDF")

    pdf_bytes = await file.read()

    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(413, "PDF demasiado grande")

    importer_service: ImporterService = get_importer_service(db)
    articles = importer_service.import_data(
        pdf_bytes, filename=file.filename, content_type=file.content_type
    )
    return articles
