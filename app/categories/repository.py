from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import distinct,func

from app.db.database import get_db
from app.db.models import ExtractedItem


class CategoriesRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_categories(self) -> list[dict]:
        category_field = ExtractedItem.data["category"].as_string()

        result = (
            self.db.query(
                func.min(ExtractedItem.id).label("id"),
                category_field.label("name"),
            )
            .filter(category_field.isnot(None))
            .group_by(category_field)
            .order_by(category_field)
            .all()
        )

        return [
            {
                "id": row.id,
                "name": row.name,
            }
            for row in result
        ]

def get_categories_repository(
    db: Session = Depends(get_db),
) -> CategoriesRepository:
    return CategoriesRepository(db)