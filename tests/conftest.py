import pytest
from httpx import AsyncClient
from app.main import app  # Import your FastAPI app
from app.core.database import DataBase


@pytest.fixture(scope="session", autouse=True)
async def initialize_db():
    # Initialize your test database (this should point to a test database URL)
    await DataBase.create_pool("postgresql://sarzz:Welcome@localhost/testdb")


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
