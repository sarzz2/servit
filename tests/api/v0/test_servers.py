import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_server(client: AsyncClient, test_user_token):
    # Define user data for creation
    server_data = {"name": "testserver"}
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}

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
async def test_get_server_by_id(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    response = await client.get(f"/api/v0/servers/{test_server['id']}", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_server_roles_permission(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    response = await client.get(f"/api/v0/servers/{test_server['id']}/roles_permissions", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_server_roles_permission_for_invalid_user(client: AsyncClient, test_user_token2, test_server):
    headers = {"Authorization": f"Bearer {test_user_token2}"}
    response = await client.get(f"/api/v0/servers/{test_server['id']}/roles_permissions", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "No roles or permissions found for the user in this server"


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
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}

    # Make a POST request to the user creation endpoint using AsyncClient
    response = await client.post(f"/api/v0/servers/join/{invite_link}", headers=headers)

    # Check the status code
    assert response.status_code == 302


@pytest.mark.asyncio
async def test_leave_server(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    server_id = test_server["id"]
    response = await client.post(f"/api/v0/servers/leave/{server_id}", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_server(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    server_id = test_server["id"]
    update_data = {"description": "updatedserver", "is_public": True}
    response = await client.patch(f"/api/v0/servers/{server_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["server"]["description"] == "updatedserver"


@pytest.mark.asyncio
async def test_update_server_invalid_data(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    server_id = test_server["id"]
    update_data = {"description": "updatedserver", "is_public": "invalid"}
    response = await client.patch(f"/api/v0/servers/{server_id}", json=update_data, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    # Try accessing the create server endpoint without providing an authorization token
    server_data = {"name": "unauthorizedtestserver"}

    response = await client.post("/api/v0/servers/", json=server_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_server_not_found(client: AsyncClient, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    response = await client.get("/api/v0/servers/7442e730-e3d2-442e-917d-96de9846989d", headers=headers)
    assert response.status_code == 404
    assert "Server not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_server_valid_and_invalid_data(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    server_id = test_server["id"]
    update_data = {"description": "Valid description", "is_public": "invalid"}
    response = await client.patch(f"/api/v0/servers/{server_id}", json=update_data, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_updating_server_without_permission(client: AsyncClient, test_user_token2, test_server):
    headers = {"Authorization": f"Bearer {test_user_token2}"}
    server_id = test_server["id"]
    update_data = {"description": "updatedserver", "is_public": True}
    response = await client.patch(f"/api/v0/servers/{server_id}", json=update_data, headers=headers)
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def get_user_permissions_in_server(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    server_id = test_server["id"]
    response = await client.get(f"/api/v0/servers/{server_id}/roles_permissions", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"roles": [], "permissions": []}


@pytest.mark.asyncio
async def no_permissions_found_for_user(client: AsyncClient, test_user_token2, test_server):
    headers = {"Authorization": f"Bearer {test_user_token2}"}
    server_id = test_server["id"]
    response = await client.get(f"/api/v0/servers/{server_id}/roles_permissions", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def update_server_with_invalid_id(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    update_data = {"description": "updatedserver", "is_public": True}
    response = await client.patch(
        "/api/v0/servers/d51d95ec-e95b-4a57-bc06-4f618baea1f3", json=update_data, headers=headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_regenerate_code(client: AsyncClient, test_user_token, test_server):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    server_id = test_server["id"]
    response = await client.patch(f"/api/v0/servers/regenerate_invite_code/{server_id}", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_kick_server_user(client: AsyncClient, test_user_token, test_server, test_user):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    server_id = test_server["id"]
    body = [test_user["id"]]
    response = await client.post(f"/api/v0/servers/kick_user/{server_id}", headers=headers, json=body)
    assert response.status_code == 200
