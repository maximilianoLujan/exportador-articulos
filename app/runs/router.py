from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.runs.model import ExtractedItemModel, ProcessModel
from app.runs.service import RunsService, get_runs_service

# "run" = una ejecución del pipeline sobre un documento.
# En la API lo exponemos como "proceso" por claridad.
router = APIRouter(prefix="/procesos", tags=["procesos"])


@router.get("", response_model=list[ProcessModel], response_model_exclude_none=True)
def list_runs(service: RunsService = Depends(get_runs_service)):
    runs = service.list_processes()
    return [
        ProcessModel(
            id=r.id,
            document_id=r.document_id,
            pipeline=r.pipeline,
            status=getattr(r.status, "value", r.status),
            started_at=r.started_at,
            finished_at=r.finished_at,
            error=r.error,
        )
        for r in runs
    ]


@router.get("/{run_id}", response_model=ProcessModel, response_model_exclude_none=True)
def get_run(run_id: int, service: RunsService = Depends(get_runs_service)):
    r = service.get_process(run_id)
    if r is None:
        raise HTTPException(status_code=404, detail="proceso no encontrado")
    return ProcessModel(
        id=r.id,
        document_id=r.document_id,
        pipeline=r.pipeline,
        status=getattr(r.status, "value", r.status),
        started_at=r.started_at,
        finished_at=r.finished_at,
        error=r.error,
    )


@router.get(
    "/{run_id}/items",
    response_model=list[ExtractedItemModel],
    response_model_exclude_none=True,
)
def list_run_items(run_id: int, service: RunsService = Depends(get_runs_service)):
    r = service.get_process(run_id)
    if r is None:
        raise HTTPException(status_code=404, detail="proceso no encontrado")
    items = service.list_items(run_id)
    return [
        ExtractedItemModel(
            id=i.id,
            run_id=i.run_id,
            item_type=getattr(i.item_type, "value", i.item_type),
            fingerprint=i.fingerprint,
            parse_error=i.parse_error,
            data=i.data,
        )
        for i in items
    ]
