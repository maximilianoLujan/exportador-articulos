from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.runs.service import RunsService, get_runs_service

# "run" = una ejecución del pipeline sobre un documento.
# En la API lo exponemos como "proceso" por claridad.
router = APIRouter(prefix="/procesos", tags=["procesos"])


@router.get("")
def list_runs(service: RunsService = Depends(get_runs_service)):
    runs = service.list_processes()
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
def get_run(run_id: int, service: RunsService = Depends(get_runs_service)):
    r = service.get_process(run_id)
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
def list_run_items(run_id: int, service: RunsService = Depends(get_runs_service)):
    r = service.get_process(run_id)
    if r is None:
        raise HTTPException(status_code=404, detail="proceso no encontrado")
    items = service.list_items(run_id)
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
