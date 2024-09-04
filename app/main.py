from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v0.api import api_router
from app.core.config import settings
from app.core.database import DataBase
from app.core.logging_config import configure_logging

logger = configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_instance = DataBase()
    await database_instance.create_pool(uri=settings.DATABASE_URL)
    logger.info("Database connected successfully")
    yield
    await database_instance.close_pool()
    logger.info("Database disconnected successfully")


app = FastAPI(
    title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION, lifespan=lifespan
)


app.include_router(api_router, prefix=settings.API_V0_STR)
