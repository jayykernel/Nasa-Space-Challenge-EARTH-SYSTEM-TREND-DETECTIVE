"""FastAPI application setup; request behavior is organized under app.api."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv

_repo_root=Path(__file__).resolve().parents[2]
load_dotenv(_repo_root/"backend"/".env",override=False)
load_dotenv(_repo_root/".env",override=False)

from app.api.analysis import router as analysis_router
from app.api.datasets import router as datasets_router
from app.api.providers import router as providers_router
from app.registry.variable_registry import SUPPORTED_VARIABLES
from app.storage import jobs

@asynccontextmanager
async def lifespan(_app):
    jobs.initialize()
    yield

app=FastAPI(title="Earth System Trend Detective API",description="Earth science investigation API",version="1.0.0",lifespan=lifespan)
origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS","http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["GET","POST","OPTIONS"],allow_headers=["*"])
app.include_router(datasets_router,prefix="/api/v1")
app.include_router(providers_router,prefix="/api/v1")
app.include_router(analysis_router,prefix="/api/v1")

@app.get("/api/v1/health")
async def health():
    return {"status":"ok","service":"earth-system-trend-detective","supported_variables":list(SUPPORTED_VARIABLES)}

def main():
    import uvicorn
    uvicorn.run("app.main:app",host=os.getenv("BACKEND_HOST","127.0.0.1"),port=int(os.getenv("BACKEND_PORT","8001")),reload=False)
