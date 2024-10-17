import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, test_user_token, test_server):
    # Define category data for creation
    category_data = {"name": "testcategory"}
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Make a POST request to create a category
    response = await client.post(f"/api/v0/category/{test_server['id']}", json=category_data, headers=headers)

    # Check the status code
    assert response.status_code == 201

    # Check the response JSON
    response_data = response.json()
    assert response_data == {"message": "Category created successfully", "category": {"name": "testcategory"}}


@pytest.mark.asyncio
async def test_create_category_unauthorized(client: AsyncClient, test_server):
    # Attempt to create a category without authorization
    category_data = {"name": "Unauthorized Category"}

    response = await client.post(f"/api/v0/category/{test_server['id']}", json=category_data)

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_get_server_categories(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.get(f"/api/v0/category/{test_server['id']}", headers=headers)
    assert response.status_code == 200

    # Check if categories are returned
    response_data = response.json()
    assert isinstance(response_data, list)


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, test_user_token, test_server, test_category):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    category_id = test_category["id"]
    update_data = {"name": "updatedcategory", "position": 1}

    response = await client.patch(
        f"/api/v0/category/{test_server['id']}/{category_id}", json=update_data, headers=headers
    )

    # Check the status code
    assert response.status_code == 200

    # Check if the category was updated
    response_data = response.json()
    assert response_data["name"] == "updatedcategory"


@pytest.mark.asyncio
async def test_update_category_invalid_data(client: AsyncClient, test_user_token, test_server, test_category):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    category_id = test_category["id"]
    update_data = {"name": "", "position": "invalid"}  # Invalid data

    response = await client.patch(
        f"/api/v0/category/{test_server['id']}/{category_id}", json=update_data, headers=headers
    )

    # Check the status code
    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient, test_user_token, test_server, test_category):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    category_id = test_category["id"]

    response = await client.delete(f"/api/v0/category/{test_server['id']}/{category_id}", headers=headers)

    # Check the status code
    assert response.status_code == 200

    # Check the response message


@pytest.mark.asyncio
async def test_delete_category_without_permission(client: AsyncClient, test_user_token2, test_server, test_category):
    headers = {"Authorization": f"Bearer {test_user_token2}"}
    category_id = test_category["id"]

    response = await client.delete(f"/api/v0/category/{test_server['id']}/{category_id}", headers=headers)

    # Check the status code
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_category_invalid_name(client: AsyncClient, test_user_token, test_server):
    # Attempt to create a category with an invalid name
    invalid_names = ["", "a", "x" * 256]  # Empty, too short, too long
    headers = {"Authorization": f"Bearer {test_user_token}"}

    for name in invalid_names:
        response = await client.post(f"/api/v0/category/{test_server['id']}", json={"name": name}, headers=headers)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_non_existent_category(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    non_existent_id = "7442e730-e3d2-442e-917d-96de9846989d"
    update_data = {"name": "updatedcategory"}

    response = await client.patch(
        f"/api/v0/category/{test_server['id']}/{non_existent_id}", json=update_data, headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_category_without_permission(client: AsyncClient, test_user_token2, test_server):
    # Attempt to create a category without the required permissions
    category_data = {"name": "No Permission Category"}
    headers = {"Authorization": f"Bearer {test_user_token2}"}

    response = await client.post(f"/api/v0/category/{test_server['id']}", json=category_data, headers=headers)

    assert response.status_code == 403  # Forbidden
