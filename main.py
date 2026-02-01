from fastapi import FastAPI

from app.importer.router.importer_router import router as importer_router

app = FastAPI()

app.include_router(importer_router)


@app.get("/")
async def root():
    return {"message": "Nodexl Web App is running"}
