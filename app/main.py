import asyncio
import re
import sys
import time
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v0.api import api_router
from app.core.auth import get_password_hash
from app.core.config import settings
from app.core.database import DataBase
from app.core.dependencies import redis_client
from app.core.logging_config import configure_logging
from app.utils import s3
from app.utils.metrics import (
    REQUEST_COUNT,
    REQUEST_HISTOGRAM,
    REQUEST_IN_PROGRESS,
    REQUEST_LATENCY,
)
from app.utils.metrics import router as metrics_router
from app.utils.metrics import update_system_metrics
from migrate import check_all_migrations_applied

logger = configure_logging()


async def create_staff_user(db):
    query = """
    INSERT INTO staff(email, name, phone, role, password)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT DO NOTHING;
    """
    password = get_password_hash(settings.ADMIN_PASSWORD)
    await db.execute(query, settings.ADMIN_EMAIL, "SuperAdmin", "1234567890", "superadmin", password)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_instance = DataBase()
    await database_instance.create_pool(uri=settings.DATABASE_URL)
    await redis_client.connect()
    all_migrations_applied_check = await check_all_migrations_applied()
    if not all_migrations_applied_check:
        logger.critical("You have pending migrations")
        raise RuntimeError("You have pending migrations")
    asyncio.create_task(update_system_metrics())
    await create_staff_user(database_instance)
    yield
    await database_instance.close_pool()
    await redis_client.close()
    logger.info("Database disconnected successfully")


if "pytest" in sys.modules:
    limiter = Limiter(key_func=get_remote_address, enabled=False)
else:
    limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

app.state.limiter = limiter
app.include_router(metrics_router)


# Middleware to collect request metrics
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)
    start_time = time.time()
    REQUEST_IN_PROGRESS.inc()  # Increment in-progress requests
    sanitized_path = re.sub(
        r"/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|\d+)",
        r"/{id}",
        request.url.path,
    )

    response = await call_next(request)

    process_time = time.time() - start_time
    REQUEST_LATENCY.observe(process_time)
    REQUEST_HISTOGRAM.labels(endpoint=sanitized_path).observe(process_time)

    REQUEST_COUNT.labels(method=request.method, endpoint=sanitized_path, status_code=response.status_code).inc()
    REQUEST_IN_PROGRESS.dec()  # Decrement after completion

    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"\033[1;37m{request.method}\033[0m , {request.url} params: {dict(request.query_params)}")

    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    if response.status_code < 400:
        logger.info(
            f"Request completed with {response.status_code}"
            f" {HTTPStatus(response.status_code).phrase} in {process_time:.6f}s"
        )
    else:
        logger.error(
            f"Request failed with {response.status_code}"
            f" {HTTPStatus(response.status_code).phrase} in {process_time:.6f}s"
        )
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return ORJSONResponse(
        status_code=429,
        content={"detail": [{"msg": "Rate limit exceeded. Please try again later."}]},
    )


app.include_router(api_router, prefix=settings.API_V0_STR)
app.include_router(s3.router, tags=["S3"])
origins = ["http://localhost:3000", "http://localhost:3001"]

# Add CORS middleware to the FastAPI application
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
app.add_middleware(GZipMiddleware, minimum_size=1500)
