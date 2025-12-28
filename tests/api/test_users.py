"""
User management API tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_users_admin(client: AsyncClient, admin_token_headers: dict):
    """Admin can list all users."""
    response = await client.get(
        "/api/v1/users/",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1  # Should at least have the admin


@pytest.mark.asyncio
async def test_list_users_student_forbidden(client: AsyncClient, user_token_headers: dict):
    """Student cannot list users."""
    response = await client.get(
        "/api/v1/users/",
        headers=user_token_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_admin(client: AsyncClient, admin_token_headers: dict):
    """Admin can create a new user."""
    response = await client.post(
        "/api/v1/users/",
        headers=admin_token_headers,
        json={
            "email": "newuser@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
            "role": "TEACHER"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "TEACHER"


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, admin_token_headers: dict, test_user):
    """Admin can get user by ID."""
    response = await client.get(
        f"/api/v1/users/{test_user.id}",
        headers=admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email
