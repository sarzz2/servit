import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture(scope="function")
async def test_channel(test_user_token, test_server, test_category):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Define channel data for creation
        channel_data = {"name": "testchannel", "description": "test description"}
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Make a POST request to create a channel
        await client.post(
            f"/api/v0/channels/{test_server['id']}/{test_category['id']}", json=channel_data, headers=headers
        )

        channel_response = await client.get(
            f"/api/v0/channels/{test_server['id']}/{test_category['id']}", headers=headers
        )
        return channel_response.json()[0]


@pytest.mark.asyncio
async def test_create_channel(client: AsyncClient, test_user_token, test_server, test_category):
    # Define channel data for creation
    channel_data = {"name": "testchannel", "description": "test description"}
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Make a POST request to create a channel
    response = await client.post(
        f"/api/v0/channels/{test_server['id']}/{test_category['id']}", json=channel_data, headers=headers
    )

    # Check the status code
    assert response.status_code == 201

    # Check the response JSON
    response_data = response.json()
    assert response_data["channel"]["name"] == "testchannel"


@pytest.mark.asyncio
async def test_create_channel_invalid_category_id(client: AsyncClient, test_user_token, test_server, test_category):
    # Define channel data for creation
    channel_data = {"name": "testchannel", "description": "test description"}
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Make a POST request to create a channel
    response = await client.post(
        f"/api/v0/channels/{test_server['id']}/{'d51d95ec-e95b-4a57-bc06-4f618baea1f3'}",
        json=channel_data,
        headers=headers,
    )

    # Check the status code
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_channel_unauthorized(client: AsyncClient, test_server, test_category):
    # Attempt to create a channel without authorization
    channel_data = {"name": "Unauthorized Channel", "description": "test description"}

    response = await client.post(f"/api/v0/channels/{test_server['id']}/{test_category['id']}", json=channel_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_category_channels(client: AsyncClient, test_user_token, test_server, test_category):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.get(f"/api/v0/channels/{test_server['id']}/{test_category['id']}", headers=headers)
    assert response.status_code == 200

    # Check if channels are returned
    response_data = response.json()
    assert isinstance(response_data, list)


@pytest.mark.asyncio
async def test_update_channel(client: AsyncClient, test_user_token, test_server, test_category, test_channel):
    # Define channel data for update
    channel_data = {"name": "updatedchannel", "description": "updated description"}
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Make a PATCH request to update a channel
    response = await client.patch(
        f"/api/v0/channels/{test_server['id']}/{test_channel['id']}", json=channel_data, headers=headers
    )
    assert response.status_code == 200

    # Check the response JSON
    response_data = response.json()
    assert response_data["channel"]["name"] == "updatedchannel"


@pytest.mark.asyncio
async def test_update_invalid_channel_id(client: AsyncClient, test_server, test_user_token, test_channel):
    channel_data = {"name": "updatedchannel", "description": "updated description"}
    headers = {"Authorization": f"Bearer {test_user_token}"}
    # Passing server id as channel id to simulate invalid id
    response = await client.patch(
        f"/api/v0/channels/{test_server['id']}/{test_server['id']}", json=channel_data, headers=headers
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_channel_unauthorized(client: AsyncClient, test_server, test_channel):
    # Attempt to update a channel without authorization
    channel_data = {"name": "Unauthorized Channel", "description": "test description"}

    response = await client.patch(f"/api/v0/channels/{test_server['id']}/{test_channel['id']}", json=channel_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_channel(client: AsyncClient, test_user_token, test_server, test_channel):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.delete(f"/api/v0/channels/{test_server['id']}/{test_channel['id']}", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_invalid_channel(client: AsyncClient, test_user_token, test_server, test_channel):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = await client.delete(f"/api/v0/channels/{test_server['id']}/{test_server['id']}", headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_channel_unauthorized(client: AsyncClient, test_server, test_channel):
    response = await client.delete(f"/api/v0/channels/{test_server['id']}/{test_channel['id']}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_channel_without_permission(client: AsyncClient, test_user_token2, test_server, test_category):
    # Define channel data for creation
    channel_data = {"name": "testchannel", "description": "test description"}
    headers = {"Authorization": f"Bearer {test_user_token2}"}

    response = await client.post(
        f"/api/v0/channels/{test_server['id']}/{test_category['id']}", json=channel_data, headers=headers
    )
    assert response.status_code == 403
