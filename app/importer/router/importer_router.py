import os

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)

from app.importer.model.importer_model import SummaryModel
from app.importer.service.importer_service import ImporterService, get_importer_service
from app.limiter import limiter

router = APIRouter(prefix="/import", tags=["importer"])

MAX_PDF_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/pdf", response_model_exclude_none=True)
@limiter.limit(os.getenv("RATE_LIMIT_IMPORT_PDF", "5/minute"))
async def import_pdf(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    importer_service: ImporterService = Depends(get_importer_service),
) -> SummaryModel:
    if file.content_type != "application/pdf":
        raise HTTPException(400, "El archivo no es un PDF")

    pdf_bytes = await file.read()

    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(413, "PDF demasiado grande")

    summary = importer_service.import_data(
        pdf_bytes, filename=file.filename, content_type=file.content_type
    )
    return summary
