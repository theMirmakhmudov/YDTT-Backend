"""
Digital Library API tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_library_book_admin(client: AsyncClient, admin_token_headers: dict):
    """Admin can upload a book to the library."""
    # 1. Create Subject first
    subject_resp = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={"name": "Literature", "code": "LIT-101"}
    )
    assert subject_resp.status_code in [201, 200]
    subject_id = subject_resp.json()["id"]
    
    # 2. Create Book
    response = await client.post(
        "/api/v1/library/",
        headers=admin_token_headers,
        json={
            "title": "Uzbek Literature Anthology",
            "description": "Collection of classic poems",
            "subject_id": subject_id,
            "grade": 9,
            "author": "Alisher Navoi",
            "publication_year": 2020,
            "file_path": "s3://books/lit-9.pdf",
            "file_size": 1024000,
            "mime_type": "application/pdf"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Uzbek Literature Anthology"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_list_books(client: AsyncClient, admin_token_headers: dict, user_token_headers: dict):
    """Users can list books with filters."""
    # 1. Create Subject & Book (Admin)
    subject_resp = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={"name": "Physics", "code": "PHYS-101"}
    )
    subject_id = subject_resp.json()["id"]
    
    await client.post(
        "/api/v1/library/",
        headers=admin_token_headers,
        json={
            "title": "Physics Grade 10",
            "subject_id": subject_id,
            "grade": 10,
            "file_path": "s3://books/phys-10.pdf",
            "file_size": 500000
        }
    )
    
    # 2. List Books (Student)
    # Filter by subject
    response = await client.get(
        f"/api/v1/library/?subject_id={subject_id}",
        headers=user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["title"] == "Physics Grade 10"
    
    # Filter by grade
    response = await client.get(
        "/api/v1/library/?grade=10",
        headers=user_token_headers
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_update_book_admin(client: AsyncClient, admin_token_headers: dict):
    """Admin can update a book."""
    # Setup
    subject_resp = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={"name": "Chemistry", "code": "CHEM-LIB-101"}
    )
    subject_id = subject_resp.json()["id"]
    
    book_resp = await client.post(
        "/api/v1/library/",
        headers=admin_token_headers,
        json={
            "title": "Old Chemistry Book",
            "subject_id": subject_id,
            "grade": 11,
            "file_path": "path/to/old.pdf",
            "file_size": 100
        }
    )
    book_id = book_resp.json()["id"]
    
    # Update
    response = await client.put(
        f"/api/v1/library/{book_id}",
        headers=admin_token_headers,
        json={"title": "Modern Chemistry Book"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Modern Chemistry Book"


@pytest.mark.asyncio
async def test_delete_book_admin(client: AsyncClient, admin_token_headers: dict):
    """Admin can delete a book."""
    # Setup
    subject_resp = await client.post(
        "/api/v1/subjects/",
        headers=admin_token_headers,
        json={"name": "History", "code": "HIST-LIB-101"}
    )
    subject_id = subject_resp.json()["id"]
    
    book_resp = await client.post(
        "/api/v1/library/",
        headers=admin_token_headers,
        json={
            "title": "History Book",
            "subject_id": subject_id,
            "grade": 8,
            "file_path": "path",
            "file_size": 100
        }
    )
    book_id = book_resp.json()["id"]
    
    # Delete
    response = await client.delete(
        f"/api/v1/library/{book_id}",
        headers=admin_token_headers
    )
    assert response.status_code == 204
    
    # Verify
    get_resp = await client.get(
        f"/api/v1/library/{book_id}",
        headers=admin_token_headers
    )
    assert get_resp.status_code == 404
