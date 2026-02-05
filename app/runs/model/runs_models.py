from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProcessModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    document_id: int
    pipeline: str | None = None
    status: str | None = None

    started_at: datetime | None = None
    finished_at: datetime | None = None

    error: str | None = None


class ExtractedItemModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    run_id: int

    item_type: str
    fingerprint: str | None = None
    parse_error: str | None = None

    data: dict[str, Any] | None = None
