from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Servit"
    PROJECT_VERSION: str = "0.1.0"
    API_V0_STR: str = "/api/v0"
    SECRET_KEY: str = "test_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 336
    REFRESH_TOKEN_EXPIRE_DAYS: int = 21
    SUDO_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "postgresql://user:password@localhost/servit"
    TEST_DATABASE_URL: str = "postgresql://user:password@localhost/test_servit"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "rpc://"
    GO_BASE_URL: str = "localhost:8080"
    # default values for localstack
    S3_ENDPOINT_URL: str = "http://localhost:4566"
    S3_REGION_NAME: str = "us-east-1"
    AWS_ACCESS_KEY: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_BUCKET_NAME: str = "my-bucket"

    class Config:
        env_file = ".env"


settings = Settings()
