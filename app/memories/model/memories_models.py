from __future__ import annotations

import datetime as dt
from pydantic import BaseModel


class MemoryModel(BaseModel):
    id: int
    filename: str | None
    content_type: str | None
    sha256: str
    size_bytes: int
    created_at: dt.datetime

    class Config:
        from_attributes = True
