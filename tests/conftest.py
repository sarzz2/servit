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
        token = await test_user_data(user_data, client)
        return token["access_token"]


@pytest.fixture(scope="function")
async def test_user_token2():
    async with AsyncClient(app=app, base_url="http://test") as client:
        user_data = {"username": "testuser2", "password": "testpassword", "email": "test2@test.com"}
        token = await test_user_data(user_data, client)
        return token["access_token"]


@pytest.fixture()
async def test_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        user_data = {"username": "testuser", "password": "testpassword", "email": "test@test.com"}
        user_data = await test_user_data(user_data, client)
        headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        response = await client.get("/api/v0/users/me", headers=headers)
        return response.json()


@pytest.fixture(scope="function")
async def test_category(test_user_token, test_server):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Define category data for creation
        category_data = {"name": "testcategory"}
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Make a POST request to create a category
        await client.post(f"/api/v0/category/{test_server['id']}", json=category_data, headers=headers)

        category_response = await client.get(f"/api/v0/category/{test_server['id']}", headers=headers)
        return category_response.json()[0]


async def test_user_data(user_data, client):
    # Check if the user already exists, if not, create it
    register_response = await client.post("/api/v0/users/register", json=user_data)
    if register_response.status_code != 201:
        # If the user exists, log in instead
        login_response = await client.post("/api/v0/users/login", json=user_data)
        assert login_response.status_code == 200
        user_data = login_response.json()
    else:
        # If user registration was successful, log in the newly created user
        login_response = await client.post("/api/v0/users/login", json=user_data)
        assert login_response.status_code == 200
        user_data = login_response.json()

    # Return the access token to be used in tests
    return user_data


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
        server_data = await client.get("/api/v0/servers/user_servers", headers=headers)
        return server_data.json()["servers"][0]


@pytest.fixture(scope="function")
async def client():
    # Use httpx.AsyncClient for async testing with FastAPI
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
