"""
Authentication API tests.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    """Test successful login returns tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "STUDENT"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """Test login with incorrect password fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, test_db: AsyncSession):
    """Test login with non-existent email fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, user_token_headers: dict):
    """Test retrieving current user profile."""
    response = await client.get(
        "/api/v1/auth/me",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "student@example.com"
    assert data["role"] == "STUDENT"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test retrieving profile without token fails."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403
