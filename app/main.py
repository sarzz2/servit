import sys
import time
import uuid
from contextlib import asynccontextmanager
from http import HTTPStatus
from mimetypes import guess_type

from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import FastAPI, File, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse, StreamingResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v0.api import api_router
from app.core.aws_localstack import s3_client
from app.core.config import settings
from app.core.database import DataBase
from app.core.dependencies import redis_client
from app.core.logging_config import configure_logging
from migrate import check_all_migrations_applied

logger = configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_instance = DataBase()
    await database_instance.create_pool(uri=settings.DATABASE_URL)
    await redis_client.connect()
    all_migrations_applied_check = await check_all_migrations_applied()
    if not all_migrations_applied_check:
        logger.critical("You have pending migrations")
        raise RuntimeError("You have pending migrations")
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


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return ORJSONResponse(
        status_code=429,
        content={"detail": [{"msg": "Rate limit exceeded. Please try again later."}]},
    )


app.include_router(api_router, prefix=settings.API_V0_STR)

origins = [
    "http://localhost:3000",
]

# Add CORS middleware to the FastAPI application
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
app.add_middleware(GZipMiddleware, minimum_size=1500)


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


@app.post("/api/v0/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    try:
        unique_key = f"{uuid.uuid4()}_{file.filename}"
        s3_client.upload_fileobj(file.file, settings.AWS_BUCKET_NAME, unique_key)
        return {
            "url": f"{str(request.base_url)[:-1]}/files/{unique_key}",
            "message": "File uploaded successfully",
        }
    except (NoCredentialsError, PartialCredentialsError):
        return {"error": "Credentials not available"}


@app.get("/files/{unique_key}")
async def get_file(unique_key: str):
    try:
        # Get the object from S3
        response = s3_client.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=unique_key)
        # Guess the content type of the file (like image/jpeg, image/png)
        content_type, _ = guess_type(unique_key.split("_", 1)[1])  # Extract original filename from unique key
        if not content_type:
            content_type = "application/octet-stream"
        return StreamingResponse(response["Body"], media_type=content_type)
    except s3_client.exceptions.NoSuchKey:
        return {"error": "File not found"}


@app.delete("/files/{unique_key}")
async def delete_file(unique_key: str):
    try:
        s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=unique_key)
        return {"message": f"File '{unique_key}' deleted successfully"}
    except s3_client.exceptions.NoSuchKey:
        return {"error": "File not found"}
