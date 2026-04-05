from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from database.db import init_db, engine
from api.routes import ads, auth, favorites, search, uploads, users

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    yield
    # Shutdown
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

app = FastAPI(
    title="Auto Ads API",
    description="API для площадки объявлений о продаже автомобилей",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://avtoads.duckdns.org", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(ads.router, prefix="/ads", tags=["ads"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auto-ads-api"}

# Корневой endpoint
@app.get("/")
async def root():
    return {
        "message": "Auto Ads API",
        "version": "1.0.0",
        "docs": "/docs"
    }
