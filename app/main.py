import uuid
from contextlib import asynccontextmanager
from mimetypes import guess_type

from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse, StreamingResponse

from app.api.v0.api import api_router
from app.core.aws_localstack import s3_client
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
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
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


# S3 endpoints for file upload, view and delete
AWS_BUCKET_NAME = settings.AWS_BUCKET_NAME


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        unique_key = f"{uuid.uuid4()}_{file.filename}"
        s3_client.upload_fileobj(file.file, AWS_BUCKET_NAME, unique_key)
        return {"message": "File uploaded successfully", "unique_key": unique_key, "original_filename": file.filename}
    except (NoCredentialsError, PartialCredentialsError):
        return {"error": "Credentials not available"}


@app.get("/files/{unique_key}")
async def get_file(unique_key: str):
    try:
        # Get the object from S3
        response = s3_client.get_object(Bucket=AWS_BUCKET_NAME, Key=unique_key)
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
        s3_client.delete_object(Bucket=AWS_BUCKET_NAME, Key=unique_key)
        return {"message": f"File '{unique_key}' deleted successfully"}
    except s3_client.exceptions.NoSuchKey:
        return {"error": "File not found"}
