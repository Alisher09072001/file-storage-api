from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.file_storage.infra.api.endpoints import router as file_storage_router
from shared.db.connection import engine
from shared.db.base import Base

app = FastAPI(
    title="File Storage API",
    description="REST API for file management with metadata extraction and role-based access",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(file_storage_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "File Storage API is running", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)