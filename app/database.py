"""MongoDB async connection management using Motor."""

import logging
from typing import Optional

import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """Create Motor client and connect to MongoDB."""
    global _client, _db
    settings = get_settings()
    _client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
    _db = _client[settings.database_name]
    logger.info(f"Connected to MongoDB: {settings.mongodb_url}/{settings.database_name}")
    await create_indexes()


async def close_mongo_connection() -> None:
    """Close the Motor client connection."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")


def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Return the active database instance (dependency injection)."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return _db


def get_notes_collection() -> motor.motor_asyncio.AsyncIOMotorCollection:
    """Return the notes collection."""
    return get_database()["notes"]


async def create_indexes() -> None:
    """Create MongoDB indexes for optimal query performance."""
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
        logger.info("MongoDB indexes created successfully.")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")
