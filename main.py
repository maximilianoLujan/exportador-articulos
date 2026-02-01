from fastapi import FastAPI

from app.db.database import create_all
from app.graph.router import router as graph_router
from app.importer.router.importer_router import router as importer_router
from app.runs.router import router as runs_router

app = FastAPI()

app.include_router(importer_router)
app.include_router(runs_router)
app.include_router(graph_router)


@app.on_event("startup")
def _startup() -> None:
    # Create tables for the configured DATABASE_URL.
    create_all()


@app.get("/")
async def root():
    return {"message": "Nodexl Web App is running"}
