"""MongoDB async connection management using Motor."""

import logging
from typing import Optional

import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
_client_loop = None
_indexes_created: bool = False


def _get_current_loop():
    import asyncio
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


def get_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    """Get or create the Motor client, ensuring it is attached to the current event loop."""
    global _client, _db, _client_loop
    current_loop = _get_current_loop()

    # If client is missing, or event loop has changed / closed (serverless warm container reuse)
    if (
        _client is None
        or _client_loop is None
        or (_client_loop is not None and current_loop is not None and _client_loop is not current_loop)
        or (_client_loop is not None and _client_loop.is_closed())
    ):
        if _client is not None:
            try:
                _client.close()
            except Exception:
                pass
        settings = get_settings()
        _client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=10,
        )
        _client_loop = current_loop
        _db = _client[settings.database_name]
        logger.info("Initialized MongoDB client (serverless-compatible).")

    return _client


async def connect_to_mongo() -> None:
    """Create Motor client and connect to MongoDB."""
    get_client()
    await create_indexes()


async def close_mongo_connection() -> None:
    """Close the Motor client connection."""
    global _client, _db, _client_loop
    if _client:
        _client.close()
        _client = None
        _db = None
        _client_loop = None
        logger.info("MongoDB connection closed.")


def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Return the active database instance (dependency injection).

    Lazily initializes the Motor client if needed and guarantees connection to current loop.
    """
    get_client()
    return _db


def get_notes_collection() -> motor.motor_asyncio.AsyncIOMotorCollection:
    """Return the notes collection."""
    return get_database()["notes"]


async def create_indexes() -> None:
    """Create MongoDB indexes for optimal query performance."""
    global _indexes_created
    if _indexes_created:
        return

    collection = get_notes_collection()

    indexes = [
        IndexModel([("created_at", DESCENDING)], name="idx_created_at"),
        IndexModel([("updated_at", DESCENDING)], name="idx_updated_at"),
        IndexModel([("category", ASCENDING)], name="idx_category"),
        IndexModel([("tags", ASCENDING)], name="idx_tags"),
        IndexModel([("is_pinned", DESCENDING)], name="idx_is_pinned"),
        IndexModel(
            [("title", TEXT), ("content", TEXT), ("tags", TEXT), ("category", TEXT)],
            name="idx_text_search",
            weights={"title": 10, "tags": 5, "category": 3, "content": 1},
        ),
    ]

    try:
        await collection.create_indexes(indexes)
        _indexes_created = True
        logger.info("MongoDB indexes created successfully.")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")
