"""
pytest configuration and shared fixtures.
Uses a separate test MongoDB database to avoid polluting development data.
"""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ── Override DB before importing anything from app ────────────────────────────
os.environ.setdefault("DATABASE_NAME", "noteflow_test_db")
os.environ["DATABASE_NAME"] = "noteflow_test_db"

from app.config import get_settings  # noqa: E402 — must be after env override

get_settings.cache_clear()


# ── Event loop (session-scoped) ───────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop required for session-scoped async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── HTTP Test Client (session-scoped) ─────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP test client with full FastAPI app.
    The lifespan (MongoDB connect/disconnect) is triggered via the ASGITransport.
    """
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        # Connect to MongoDB for the session
        from app.database import connect_to_mongo
        await connect_to_mongo()
        yield ac

    # Cleanup: drop test database and close connection
    from app.database import close_mongo_connection, get_database
    try:
        db = get_database()
        await db.client.drop_database("noteflow_test_db")
    except Exception:
        pass
    await close_mongo_connection()


# ── Per-test cleanup ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def clean_notes():
    """Delete all notes before each test for complete isolation."""
    from app.database import get_notes_collection
    try:
        col = get_notes_collection()
        await col.delete_many({})
    except RuntimeError:
        pass  # DB not yet connected (early fixtures)
    yield


# ── Sample Note Data ──────────────────────────────────────────────────────────

SAMPLE_NOTE = {
    "title": "Test Note",
    "content": "This is test content for a note.",
    "category": "Programming",
    "tags": ["python", "testing"],
    "is_pinned": False,
}

SAMPLE_NOTE_PINNED = {
    "title": "Pinned Test Note",
    "content": "A pinned note for testing.",
    "category": "Work",
    "tags": ["pinned", "important"],
    "is_pinned": True,
}


@pytest_asyncio.fixture
async def created_note(client: AsyncClient) -> dict:
    """Create a note via API and return the response data."""
    resp = await client.post("/api/notes", json=SAMPLE_NOTE)
    assert resp.status_code == 201, f"Failed to create test note: {resp.text}"
    return resp.json()
