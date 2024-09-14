from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Servit"
    PROJECT_VERSION: str = "0.1.0"
    API_V0_STR: str = "/api/v0"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3000
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    # default values for localstack
    S3_ENDPOINT_URL: str = "http://localhost:4566"
    S3_REGION_NAME: str = "us-east-1"
    AWS_ACCESS_KEY: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_BUCKET_NAME: str = "my-bucket"

    class Config:
        env_file = ".env"


settings = Settings()
