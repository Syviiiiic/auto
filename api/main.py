import logging
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db
from api.routes import auth, ads, search, uploads, favorites, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API...")
    await init_db()
    yield
    logger.info("Shutting down API...")


app = FastAPI(title="Auto Ads API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=str(UPLOAD_DIR)), name="media")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(ads.router, prefix="/api/ads", tags=["ads"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(favorites.router, prefix="/api/favorites", tags=["favorites"])
app.include_router(users.router, prefix="/api/user", tags=["user"])


@app.get("/")
async def root():
    return {"message": "Auto Ads API is running"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "API is running"}
