from __future__ import annotations

from fastapi import APIRouter, Depends

from app.memories.model import MemoryModel
from app.memories.service import MemoriesService, get_memories_service

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("", response_model=list[MemoryModel])
def list_memories(service: MemoriesService = Depends(get_memories_service)):
    memories = service.list_memories()
    return [
        MemoryModel(
            id=m.id,
            filename=m.filename,
            content_type=m.content_type,
            sha256=m.sha256,
            size_bytes=m.size_bytes,
            created_at=m.created_at,
        )
        for m in memories
    ]
