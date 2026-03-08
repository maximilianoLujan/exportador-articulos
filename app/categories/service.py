from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.categories.repository import get_categories_repository,CategoriesRepository



class CategoriesService:
    def __init__(
        self,
        repository: CategoriesRepository = Depends(get_categories_repository),
    ):
        self.repository = repository

    def list_categories(self):
        return self.repository.list_categories()