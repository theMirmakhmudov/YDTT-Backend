"""
School, Class, and Subject API tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_school_admin(client: AsyncClient, admin_token_headers: dict):
    """Admin can create a school."""
    response = await client.post(
        "/api/v1/schools/",
        headers=admin_token_headers,
        json={
            "name": "Test School #1",
            "region": "Tashkent",
            "district": "Yunusabad",
            "address": "123 Street"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test School #1"
    assert data["code"] == "TASHKENT_SCH_001"  # Auto-generated
    return data["id"]


@pytest.mark.asyncio
async def test_create_class_admin(client: AsyncClient, admin_token_headers: dict):
    """Admin can create a class in a school."""
    # First create school
    school_headers = admin_token_headers
    school_resp = await client.post(
        "/api/v1/schools/",
        headers=school_headers,
        json={
            "name": "Test School #2",
            "region": "Tashkent",
            "district": "Mirzo Ulugbek"
        }
    )
    school_id = school_resp.json()["id"]
    
    # Create class
    response = await client.post(
        "/api/v1/classes/",
        headers=admin_token_headers,
        json={
            "name": "9-A",
            "grade": 9,
            "school_id": school_id,
            "academic_year": "2024-2025"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "9-A"
    assert data["school_id"] == school_id


@pytest.mark.asyncio
async def test_create_subject(client: AsyncClient, admin_token_headers: dict):
    """Admin can create a subject."""
    response = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={
            "name": "Mathematics",
            "description": "Basic Algebra"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Mathematics"
    assert data["code"] == "MATHEMATICS_001"  # Auto-generated
