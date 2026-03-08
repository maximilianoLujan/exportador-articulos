from __future__ import annotations

from fastapi import APIRouter, Depends

from app.db.models import ExtractedItem
from app.categories.service import CategoriesService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
def get_categories(service: CategoriesService = Depends()):
    return service.list_categories()
