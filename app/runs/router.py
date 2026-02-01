from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ExtractedItem, ExtractionRun

# "run" = una ejecución del pipeline sobre un documento.
# En la API lo exponemos como "proceso" por claridad.
router = APIRouter(prefix="/procesos", tags=["procesos"])


@router.get("")
def list_runs(db: Session = Depends(get_db)):
    runs = (
        db.execute(select(ExtractionRun).order_by(ExtractionRun.id.desc()).limit(50))
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "document_id": r.document_id,
            "pipeline": r.pipeline,
            "status": r.status,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "error": r.error,
        }
        for r in runs
    ]


@router.get("/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    r = db.get(ExtractionRun, run_id)
    if r is None:
        raise HTTPException(status_code=404, detail="proceso no encontrado")
    return {
        "id": r.id,
        "document_id": r.document_id,
        "pipeline": r.pipeline,
        "status": r.status,
        "started_at": r.started_at,
        "finished_at": r.finished_at,
        "error": r.error,
    }


@router.get("/{run_id}/items")
def list_run_items(run_id: int, db: Session = Depends(get_db)):
    r = db.get(ExtractionRun, run_id)
    if r is None:
        raise HTTPException(status_code=404, detail="proceso no encontrado")
    items = (
        db.execute(
            select(ExtractedItem)
            .where(ExtractedItem.run_id == run_id)
            .order_by(ExtractedItem.id.asc())
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": i.id,
            "run_id": i.run_id,
            "item_type": i.item_type,
            "fingerprint": i.fingerprint,
            "parse_error": i.parse_error,
            "data": i.data,
        }
        for i in items
    ]
