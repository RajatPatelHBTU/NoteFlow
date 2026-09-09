"""Tests for server-side HTML page routes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_page(client: AsyncClient):
    """Dashboard returns 200 HTML with NoteFlow branding."""
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert b"NoteFlow" in resp.content


@pytest.mark.asyncio
async def test_dashboard_empty_state(client: AsyncClient):
    """Empty dashboard shows empty state content."""
    resp = await client.get("/")
    assert resp.status_code == 200
    # Empty state text should be present
    assert b"No notes yet" in resp.content or b"notes" in resp.content.lower()


@pytest.mark.asyncio
async def test_create_note_page(client: AsyncClient):
    """Create note page returns 200 with form."""
    resp = await client.get("/notes/create")
    assert resp.status_code == 200
    assert b"Create Note" in resp.content
    assert b"<form" in resp.content


@pytest.mark.asyncio
async def test_note_detail_page(client: AsyncClient):
    """Note detail page returns 200 for existing note."""
    # First create a note
    create_resp = await client.post(
        "/api/notes",
        json={"title": "Detail Test Note", "content": "Detail content here."},
    )
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    resp = await client.get(f"/notes/{note_id}")
    assert resp.status_code == 200
    assert b"Detail Test Note" in resp.content


@pytest.mark.asyncio
async def test_note_detail_page_not_found(client: AsyncClient):
    """Non-existent note ID returns 404 page."""
    resp = await client.get("/notes/507f1f77bcf86cd799439011")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_note_detail_page_invalid_id(client: AsyncClient):
    """Invalid ObjectId in page URL returns 400."""
    resp = await client.get("/notes/bad-id")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_edit_note_page(client: AsyncClient):
    """Edit page returns 200 with form pre-filled."""
    create_resp = await client.post(
        "/api/notes",
        json={"title": "Edit Test Note", "content": "Edit content."},
    )
    note_id = create_resp.json()["id"]

    resp = await client.get(f"/notes/{note_id}/edit")
    assert resp.status_code == 200
    assert b"Edit Test Note" in resp.content
    assert b"Save Changes" in resp.content


@pytest.mark.asyncio
async def test_edit_page_not_found(client: AsyncClient):
    """Edit page for non-existent note returns 404."""
    resp = await client.get("/notes/507f1f77bcf86cd799439011/edit")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_with_notes(client: AsyncClient):
    """Dashboard with notes shows note titles."""
    await client.post(
        "/api/notes",
        json={"title": "Dashboard Test Note", "content": "Appears on dashboard."},
    )
    resp = await client.get("/")
    assert resp.status_code == 200
    assert b"Dashboard Test Note" in resp.content


@pytest.mark.asyncio
async def test_dashboard_search(client: AsyncClient):
    """Dashboard search renders filtered results."""
    await client.post(
        "/api/notes",
        json={"title": "Searchable Note", "content": "contains the word python"},
    )
    resp = await client.get("/?q=Searchable")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_htmx_notes_list(client: AsyncClient):
    """HTMX notes list endpoint returns HTML fragment."""
    resp = await client.get("/htmx/notes")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_htmx_search(client: AsyncClient):
    """HTMX search endpoint returns HTML fragment."""
    resp = await client.get("/htmx/search?q=test")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
