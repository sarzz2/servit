import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_server(client: AsyncClient, test_user_token):
    # Define user data for creation
    server_data = {"name": "testserver"}
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Make a POST request to the user creation endpoint using AsyncClient
    response = await client.post("/api/v0/servers/", json=server_data, headers=headers)

    # Check the status code
    assert response.status_code == 201

    # Check the response JSON
    response_data = response.json()
    assert response_data["server"]["name"] == "testserver"


@pytest.mark.asyncio
async def test_create_server_unauthorized(client: AsyncClient):
    # Attempt to create a server without authorization
    server_data = {"name": "Unauthorized Test"}

    response = await client.post("/api/v0/servers/", json=server_data)

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_get_server_by_name(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.get(f"/api/v0/servers/{test_server['name']}", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_join_server_by_invite_code(client: AsyncClient, test_user_token2, test_server):
    # Define user data for creation
    invite_link = test_server["invite_code"]
    headers = {"Authorization": f"Bearer {test_user_token2}"}

    # Make a POST request to the user creation endpoint using AsyncClient
    response = await client.post(f"/api/v0/servers/join/{invite_link}", headers=headers)

    # Check the status code
    assert response.status_code == 200

    # Check the response JSON
    response_data = response.json()
    assert response_data["server_details"]["name"] == test_server["name"]


@pytest.mark.asyncio
async def test_join_server_by_invalid_invite_code(client: AsyncClient, test_user_token2):
    # Define user data for creation
    invite_link = "invalid_invite_code"
    headers = {"Authorization": f"Bearer {test_user_token2}"}

    # Make a POST request to the user creation endpoint using AsyncClient
    response = await client.post(f"/api/v0/servers/join/{invite_link}", headers=headers)

    # Check the status code
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_joining_server_twice(client: AsyncClient, test_user_token, test_server):
    # Define user data for creation
    invite_link = test_server["invite_code"]
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Make a POST request to the user creation endpoint using AsyncClient
    response = await client.post(f"/api/v0/servers/join/{invite_link}", headers=headers)

    # Check the status code
    assert response.status_code == 302


@pytest.mark.asyncio
async def test_leave_server(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    server_id = test_server["id"]
    response = await client.post(f"/api/v0/servers/leave/{server_id}", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_server(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    server_id = test_server["id"]
    update_data = {"description": "updatedserver", "is_public": True}
    response = await client.patch(f"/api/v0/servers/{server_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["server"]["description"] == "updatedserver"


@pytest.mark.asyncio
async def test_update_server_invalid_data(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    server_id = test_server["id"]
    update_data = {"description": "updatedserver", "is_public": "invalid"}
    response = await client.patch(f"/api/v0/servers/{server_id}", json=update_data, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_server_with_duplicate_name(client: AsyncClient, test_user_token, test_server):
    # Try creating a server with the same name as an existing server
    server_data = {"name": test_server["name"]}
    headers = {"Authorization": f"Bearer {test_user_token}"}

    response = await client.post("/api/v0/servers/", json=server_data, headers=headers)
    assert response.status_code == 400
    assert "Server creation failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    # Try accessing the create server endpoint without providing an authorization token
    server_data = {"name": "unauthorizedtestserver"}

    response = await client.post("/api/v0/servers/", json=server_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_server_not_found(client: AsyncClient, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.get("/api/v0/servers/nonexistentserver", headers=headers)
    assert response.status_code == 404
    assert "Server not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_non_existent_server(client: AsyncClient, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    update_data = {"description": "updatedserver", "is_public": True}

    response = await client.patch(
        "/api/v0/servers/b5040109-5ea8-4018-854f-c981d3d0b413", json=update_data, headers=headers
    )
    assert response.status_code == 404
    assert "Server not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_server_valid_and_invalid_data(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    server_id = test_server["id"]
    update_data = {"description": "Valid description", "is_public": "invalid"}
    response = await client.patch(f"/api/v0/servers/{server_id}", json=update_data, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_duplicate_server(client: AsyncClient, test_user_token, test_server):
    server_data = {"name": test_server["name"]}
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.post("/api/v0/servers/", json=server_data, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_server_valid_and_invalid_data(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    server_id = test_server["id"]
    update_data = {"description": "Valid description", "is_public": "invalid"}
    response = await client.patch(f"/api/v0/servers/{server_id}", json=update_data, headers=headers)
    assert response.status_code == 422
