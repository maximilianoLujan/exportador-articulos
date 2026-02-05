from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.db.database import create_all
from app.graph.router import router as graph_router
from app.importer.router.importer_router import router as importer_router
from app.limiter import limiter
from app.runs.router import router as runs_router

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
