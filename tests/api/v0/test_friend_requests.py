import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture(scope="function")
async def test_friend(test_user_token, test_user_token2):
    """
    Fixture to create and return a test friend user for friend request-related tests.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get the current user details (friend's details)
        headers = {"Authorization": f"Bearer {test_user_token2}"}
        friend_profile_response = await client.get("/api/v0/users/me", headers=headers)
        assert friend_profile_response.status_code == 200

        return friend_profile_response.json()


@pytest.mark.asyncio
async def test_send_friend_request(client: AsyncClient, test_user_token2, test_user, test_friend):
    headers = {"Authorization": f"Bearer {test_user_token2}"}
    response = await client.post(f"/api/v0/friends/{test_user['id']}", headers=headers)

    assert response.status_code == 201
    assert response.json()["message"] == "Friend request sent successfully"


@pytest.mark.asyncio
async def test_send_friend_request_to_self(client: AsyncClient, test_user_token, test_user):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    response = await client.post(f"/api/v0/friends/{test_user['id']}", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot send a friend request to yourself"


@pytest.mark.asyncio
async def test_send_duplicate_friend_request(client: AsyncClient, test_user_token, test_friend):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    friend_id = test_friend["id"]

    # Send the first request
    await client.post(f"/api/v0/friends/{friend_id}", headers=headers)
    # Send the second request (should trigger a conflict)
    response = await client.post(f"/api/v0/friends/{friend_id}", headers=headers)

    assert response.status_code == 409
    assert response.json()["detail"] == "Friend request already sent"


@pytest.mark.asyncio
async def test_get_friends(client: AsyncClient, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    response = await client.get("/api/v0/friends/", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_friend_requests(client: AsyncClient, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    response = await client.get("/api/v0/friends/requests", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_friend_status(client: AsyncClient, test_user_token, test_friend, test_user_token2, test_user):
    headers = {"Authorization": f"Bearer {test_user_token2}"}
    await client.post(f"/api/v0/friends/{test_user['id']}", headers=headers)

    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    friend_id = test_friend["id"]

    response = await client.patch(f"/api/v0/friends/{friend_id}/accepted", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_update_friend_status_invalid(client: AsyncClient, test_user_token, test_friend):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    friend_id = test_friend["id"]

    response = await client.patch(f"/api/v0/friends/{friend_id}/invalid_status", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid status"


@pytest.mark.asyncio
async def test_update_invalid_user(client: AsyncClient, test_user_token, test_friend):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    friend_id = test_friend["id"]

    response = await client.patch(f"/api/v0/friends/{friend_id}/accepted", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Friend request not found"


@pytest.mark.asyncio
async def test_remove_friend(client: AsyncClient, test_user_token, test_friend, test_user_token2, test_user):
    headers = {"Authorization": f"Bearer {test_user_token2}"}
    await client.post(f"/api/v0/friends/{test_user['id']}", headers=headers)

    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    friend_id = test_friend["id"]
    await client.patch(f"/api/v0/friends/{friend_id}/accepted", headers=headers)

    response = await client.delete(f"/api/v0/friends/{friend_id}", headers=headers)

    assert response.status_code == 204  # No Content


@pytest.mark.asyncio
async def test_remove_nonexistent_friend(client: AsyncClient, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    invalid_friend_id = "00000000-0000-0000-0000-000000000000"

    response = await client.delete(f"/api/v0/friends/{invalid_friend_id}", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Friend not found"


@pytest.mark.asyncio
async def test_cancel_friend_request(client: AsyncClient, test_user_token2, test_user):
    headers = {"Authorization": f"Bearer {test_user_token2}"}
    await client.post(f"/api/v0/friends/{test_user['id']}", headers=headers)

    response = await client.delete(f"/api/v0/friends/cancel/{test_user['id']}", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cancel_invalid_friend_request(client: AsyncClient, test_user_token2, test_user):
    headers = {"Authorization": f"Bearer {test_user_token2}"}
    await client.post(f"/api/v0/friends/{test_user['id']}", headers=headers)
    invalid_friend_id = "00000000-0000-0000-0000-000000000000"

    response = await client.delete(f"/api/v0/friends/cancel/{invalid_friend_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_blocked_friends(client: AsyncClient, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token["access_token"]}"}
    response = await client.get("/api/v0/friends/blocked", headers=headers)
    assert response.status_code == 200
