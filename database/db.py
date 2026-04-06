from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import IntegrityError
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Получаем URL базы данных
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DB_USER = os.getenv('DB_USER', 'autobot')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'autobot123')
    DB_NAME = os.getenv('DB_NAME', 'auto_ads')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Конвертируем в асинхронный URL
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)

# Создаём асинхронный движок
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Отключите echo в продакшене
    poolclass=NullPool
)

# Создаём фабрику сессий
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Получение сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Инициализация базы данных (создание таблиц если их нет)"""
    from .models import Base
    try:
        async with engine.begin() as conn:
            # Используем checkfirst=True чтобы игнорировать существующие таблицы
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        logger.info("Database tables created/verified")
    except IntegrityError as e:
        # Игнорируем ошибку "таблица уже существует"
        if "already exists" in str(e).lower() or "duplicate key" in str(e).lower():
            logger.info("Database tables already exist, skipping creation")
        else:
            logger.error(f"Database integrity error: {e}")
            raise
    except Exception as e:
        # Проверяем, связана ли ошибка с существованием таблиц
        error_msg = str(e).lower()
        if "already exists" in error_msg or "duplicate key" in error_msg:
            logger.info("Database tables already exist, skipping creation")
        else:
            logger.error(f"Error initializing database: {e}")
            # Не падаем при ошибке, просто логируем
            # raise
