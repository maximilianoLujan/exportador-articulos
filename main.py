import uvicorn
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.categories.router import router as categories_routes
from app.db.database import create_all
from app.graph.router import router as graph_router
from app.importer.router.importer_router import router as importer_router
from app.limiter import limiter
from app.memories.router import router as memories_router
from app.runs.router import router as runs_router

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(importer_router)
app.include_router(runs_router)
app.include_router(graph_router)
app.include_router(memories_router)
app.include_router(categories_routes)


@app.on_event("startup")
def _startup() -> None:
    # Create tables for the configured DATABASE_URL.
    create_all()


@app.get("/")
async def root():
    return {"message": "Nodexl Web App is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
