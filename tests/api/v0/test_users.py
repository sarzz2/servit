import pytest
from httpx import AsyncClient

from app.services.v0.user_service import register_user


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    # Define user data for creation
    user_data = {
        "username": "testuserr",
        "email": "testuserr@example.com",
        "password": "testpassword@123",
    }

    # Make a POST request to the user creation endpoint using AsyncClient
    response = await client.post("/api/v0/users/register", json=user_data)
    assert response.status_code == 201
    response_data = response.json()
    assert "password" not in response_data  # Ensure password is not returned


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    # Register a user directly
    await register_user(username="loginuser", email="loginuser@example.com", password="testpassword@123")

    # Make a POST request to the login endpoint using AsyncClient
    response = await client.post(
        "/api/v0/users/login",
        json={"username": "loginuser", "password": "testpassword@123"},
    )
    assert response.status_code == 200

    # Verify the access token in the response
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient):
    # Make a POST request to the login endpoint with invalid credentials
    response = await client.post(
        "/api/v0/users/login",
        json={"username": "invaliduser", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    # Register a user directly
    await register_user(username="loginuser2", email="loginuser2@example.com", password="testpassword@123")
    response = await client.post("/api/v0/users/login", json={"username": "loginuser2", "password": "testpassword@123"})
    data = response.json()
    access_token = data["access_token"]
    response = await client.get("/api/v0/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "loginuser2"
    assert data["email"] == "loginuser2@example.com"


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_token(client: AsyncClient):
    response = await client.get("/api/v0/users/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    response = await client.get("/api/v0/users/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_user(client: AsyncClient, test_user_token):
    response = await client.get("/api/v0/users/search/test", headers={"Authorization": f"Bearer {test_user_token}"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, test_user_token):
    updated_data = {"email": "updated@test.com"}
    response = await client.patch(
        "/api/v0/users/update", headers={"Authorization": f"Bearer {test_user_token}"}, json=updated_data
    )
    assert response.status_code == 200
