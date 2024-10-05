import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.database import DataBase
from app.main import app
from migrate import apply_migrations, create_migrations_table


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    # Initialize the database connection pool asynchronously
    database_instance = DataBase()
    await database_instance.create_pool(uri=settings.TEST_DATABASE_URL)
    await create_migrations_table(database_instance.pool)
    await apply_migrations(database_instance.pool)
    print("Database connected successfully")

    # Yield control back to the tests
    yield

    # Close the database connection pool after tests
    await apply_migrations(database_instance.pool, "down")
    await database_instance.close_pool()
    print("Database disconnected successfully")


@pytest.fixture(scope="function")
async def test_user_token():
    async with AsyncClient(app=app, base_url="http://test") as client:
        user_data = {"username": "testuser", "password": "testpassword", "email": "test@test.com"}
        token = await user_token(user_data, client)
        return token


@pytest.fixture(scope="function")
async def test_user_token2():
    async with AsyncClient(app=app, base_url="http://test") as client:
        user_data = {"username": "testuser2", "password": "testpassword", "email": "test2@test.com"}
        token = await user_token(user_data, client)
        return token


async def user_token(user_data, client):
    # Check if the user already exists, if not, create it
    register_response = await client.post("/api/v0/users/register", json=user_data)
    print(register_response)
    if register_response.status_code != 201:
        # If the user exists, log in instead
        login_response = await client.post("/api/v0/users/login", json=user_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
    else:
        # If user registration was successful, log in the newly created user
        login_response = await client.post("/api/v0/users/login", json=user_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

    # Return the access token to be used in tests
    return token


@pytest.fixture(scope="function")
async def test_server(test_user_token):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Define server data for creation
        server_data = {"name": "testserver"}
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Make a POST request to the server creation endpoint using AsyncClient
        response = await client.post("/api/v0/servers/", json=server_data, headers=headers)
        assert response.status_code == 201

        # Check the response JSON
        response_data = response.json()
        server_data = await client.get("/api/v0/servers/user_servers", headers=headers)
        return server_data.json()["servers"][0]


@pytest.fixture(scope="function")
async def client():
    # Use httpx.AsyncClient for async testing with FastAPI
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
