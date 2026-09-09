"""
API tests for the Notes endpoints.
Covers: CRUD, pin, search, filter, sorting, validation, invalid ID, missing note.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import SAMPLE_NOTE, SAMPLE_NOTE_PINNED


# ── Create ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_note_success(client: AsyncClient):
    """Creating a valid note returns 201 with correct fields."""
    resp = await client.post("/api/notes", json=SAMPLE_NOTE)
    assert resp.status_code == 201

    data = resp.json()
    assert data["title"] == SAMPLE_NOTE["title"]
    assert data["content"] == SAMPLE_NOTE["content"]
    assert data["category"] == SAMPLE_NOTE["category"]
    assert data["tags"] == SAMPLE_NOTE["tags"]
    assert data["is_pinned"] is False
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_note_missing_title(client: AsyncClient):
    """Missing title returns 422."""
    resp = await client.post("/api/notes", json={"content": "no title"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_note_blank_title(client: AsyncClient):
    """Blank title returns 422."""
    resp = await client.post("/api/notes", json={**SAMPLE_NOTE, "title": "   "})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_note_missing_content(client: AsyncClient):
    """Missing content returns 422."""
    resp = await client.post("/api/notes", json={"title": "no content"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_note_title_too_long(client: AsyncClient):
    """Title exceeding max length returns 422."""
    resp = await client.post("/api/notes", json={**SAMPLE_NOTE, "title": "A" * 201})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_note_invalid_category_defaults(client: AsyncClient):
    """An unknown category should be silently coerced to 'Other'."""
    resp = await client.post("/api/notes", json={**SAMPLE_NOTE, "category": "NonExistent"})
    assert resp.status_code == 201
    assert resp.json()["category"] == "Other"


@pytest.mark.asyncio
async def test_create_note_with_tags(client: AsyncClient):
    """Tags are stored correctly."""
    data = {**SAMPLE_NOTE, "tags": ["python", "fastapi", "backend"]}
    resp = await client.post("/api/notes", json=data)
    assert resp.status_code == 201
    assert set(resp.json()["tags"]) == {"python", "fastapi", "backend"}


# ── Read ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_all_notes_empty(client: AsyncClient):
    """Empty DB returns empty list."""
    resp = await client.get("/api/notes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["notes"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_all_notes(client: AsyncClient, created_note: dict):
    """Notes list contains created note."""
    resp = await client.get("/api/notes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["notes"][0]["id"] == created_note["id"]


@pytest.mark.asyncio
async def test_get_single_note(client: AsyncClient, created_note: dict):
    """Get single note by ID returns correct data."""
    note_id = created_note["id"]
    resp = await client.get(f"/api/notes/{note_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == note_id
    assert resp.json()["title"] == created_note["title"]


@pytest.mark.asyncio
async def test_get_note_not_found(client: AsyncClient):
    """Non-existent valid ObjectId returns 404."""
    resp = await client.get("/api/notes/507f1f77bcf86cd799439011")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_note_invalid_id(client: AsyncClient):
    """Invalid ObjectId returns 400."""
    resp = await client.get("/api/notes/not-an-id")
    assert resp.status_code == 400


# ── Update ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_note(client: AsyncClient, created_note: dict):
    """Updating title and content is reflected in response."""
    note_id = created_note["id"]
    resp = await client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated Title", "content": "Updated content."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Updated content."


@pytest.mark.asyncio
async def test_update_note_not_found(client: AsyncClient):
    """Updating non-existent note returns 404."""
    resp = await client.put(
        "/api/notes/507f1f77bcf86cd799439011",
        json={"title": "x", "content": "y"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_note_invalid_id(client: AsyncClient):
    """Invalid ObjectId on update returns 400."""
    resp = await client.put("/api/notes/bad-id", json={"title": "x", "content": "y"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_updated_at_changes_on_update(client: AsyncClient, created_note: dict):
    """updated_at timestamp changes after update."""
    import asyncio
    await asyncio.sleep(0.05)
    note_id = created_note["id"]
    resp = await client.put(
        f"/api/notes/{note_id}",
        json={"title": "New Title", "content": "New content"},
    )
    assert resp.status_code == 200
    assert resp.json()["updated_at"] >= created_note["updated_at"]


# ── Delete ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_note(client: AsyncClient, created_note: dict):
    """Deleting a note returns 204 and it's gone."""
    note_id = created_note["id"]
    resp = await client.delete(f"/api/notes/{note_id}")
    assert resp.status_code == 204

    # Confirm it's gone
    get_resp = await client.get(f"/api/notes/{note_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_note_not_found(client: AsyncClient):
    """Deleting non-existent note returns 404."""
    resp = await client.delete("/api/notes/507f1f77bcf86cd799439011")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_note_invalid_id(client: AsyncClient):
    """Deleting with invalid ID returns 400."""
    resp = await client.delete("/api/notes/garbage")
    assert resp.status_code == 400


# ── Pin / Unpin ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pin_note(client: AsyncClient, created_note: dict):
    """Pinning a note toggles is_pinned to True."""
    note_id = created_note["id"]
    resp = await client.patch(f"/api/notes/{note_id}/pin")
    assert resp.status_code == 200
    assert resp.json()["is_pinned"] is True


@pytest.mark.asyncio
async def test_unpin_note(client: AsyncClient, created_note: dict):
    """Pinning twice toggles back to False."""
    note_id = created_note["id"]
    await client.patch(f"/api/notes/{note_id}/pin")  # pin
    resp = await client.patch(f"/api/notes/{note_id}/pin")  # unpin
    assert resp.status_code == 200
    assert resp.json()["is_pinned"] is False


@pytest.mark.asyncio
async def test_pin_note_not_found(client: AsyncClient):
    """Pinning non-existent note returns 404."""
    resp = await client.patch("/api/notes/507f1f77bcf86cd799439011/pin")
    assert resp.status_code == 404


# ── Search ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_by_title(client: AsyncClient):
    """Search returns notes containing the query in title."""
    await client.post("/api/notes", json={**SAMPLE_NOTE, "title": "FastAPI Guide"})
    await client.post("/api/notes", json={**SAMPLE_NOTE, "title": "Django Tutorial"})

    resp = await client.get("/api/notes/search?q=FastAPI")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any("FastAPI" in n["title"] for n in data["notes"])


@pytest.mark.asyncio
async def test_search_no_results(client: AsyncClient):
    """Search with no matches returns empty list."""
    resp = await client.get("/api/notes/search?q=xyznonexistentkeyword123")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# ── Filter ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_filter_by_category(client: AsyncClient):
    """Filter by category returns only matching notes."""
    await client.post("/api/notes", json={**SAMPLE_NOTE, "category": "Work"})
    await client.post("/api/notes", json={**SAMPLE_NOTE, "category": "Personal"})

    resp = await client.get("/api/notes?category=Work")
    assert resp.status_code == 200
    data = resp.json()
    assert all(n["category"] == "Work" for n in data["notes"])


@pytest.mark.asyncio
async def test_filter_by_category_endpoint(client: AsyncClient):
    """/category/{category} endpoint works correctly."""
    await client.post("/api/notes", json={**SAMPLE_NOTE, "category": "Study"})
    resp = await client.get("/api/notes/category/Study")
    assert resp.status_code == 200
    data = resp.json()
    assert all(n["category"] == "Study" for n in data["notes"])


@pytest.mark.asyncio
async def test_filter_pinned(client: AsyncClient):
    """Filtering by is_pinned=true returns only pinned notes."""
    await client.post("/api/notes", json=SAMPLE_NOTE)  # not pinned
    await client.post("/api/notes", json=SAMPLE_NOTE_PINNED)  # pinned

    resp = await client.get("/api/notes?is_pinned=true")
    assert resp.status_code == 200
    data = resp.json()
    assert all(n["is_pinned"] is True for n in data["notes"])


@pytest.mark.asyncio
async def test_filter_by_tag(client: AsyncClient):
    """Filtering by tag returns only notes with that tag."""
    await client.post("/api/notes", json={**SAMPLE_NOTE, "tags": ["python"]})
    await client.post("/api/notes", json={**SAMPLE_NOTE, "tags": ["javascript"]})

    resp = await client.get("/api/notes?tag=python")
    assert resp.status_code == 200
    data = resp.json()
    assert all("python" in n["tags"] for n in data["notes"])


# ── Sorting ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sort_newest(client: AsyncClient):
    """Sort by newest puts most recently created first."""
    import asyncio
    await client.post("/api/notes", json={**SAMPLE_NOTE, "title": "First"})
    await asyncio.sleep(0.05)
    await client.post("/api/notes", json={**SAMPLE_NOTE, "title": "Second"})

    resp = await client.get("/api/notes?sort=newest")
    assert resp.status_code == 200
    notes = resp.json()["notes"]
    assert len(notes) == 2
    assert notes[0]["title"] == "Second"


@pytest.mark.asyncio
async def test_sort_alpha_asc(client: AsyncClient):
    """Alphabetical ascending sort."""
    await client.post("/api/notes", json={**SAMPLE_NOTE, "title": "Zebra"})
    await client.post("/api/notes", json={**SAMPLE_NOTE, "title": "Apple"})

    resp = await client.get("/api/notes?sort=alpha_asc")
    assert resp.status_code == 200
    notes = resp.json()["notes"]
    titles = [n["title"] for n in notes]
    assert titles == sorted(titles)


# ── Pagination ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pagination(client: AsyncClient):
    """Pagination returns correct page and metadata."""
    for i in range(5):
        await client.post("/api/notes", json={**SAMPLE_NOTE, "title": f"Note {i}"})

    resp = await client.get("/api/notes?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["notes"]) == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3
    assert data["has_next"] is True
    assert data["has_prev"] is False


# ── Categories Endpoint ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_categories(client: AsyncClient):
    """Categories endpoint returns the predefined list."""
    resp = await client.get("/api/notes/categories")
    assert resp.status_code == 200
    categories = resp.json()
    assert "Programming" in categories
    assert "Personal" in categories
    assert "Work" in categories
