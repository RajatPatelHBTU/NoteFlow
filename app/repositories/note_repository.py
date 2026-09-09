"""Note repository — all raw async MongoDB operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING

import motor.motor_asyncio

from app.schemas.note import NoteCreate, NoteUpdate, NoteQueryParams

logger = logging.getLogger(__name__)


def _parse_object_id(note_id: str) -> ObjectId:
    """Convert string to ObjectId, raising ValueError if invalid."""
    try:
        return ObjectId(note_id)
    except (InvalidId, TypeError):
        raise ValueError(f"Invalid note ID: '{note_id}'")


def _doc_to_dict(doc: dict) -> dict:
    """Convert a MongoDB document to a serializable dict."""
    if doc is None:
        return None
    doc["id"] = str(doc.pop("_id"))
    return doc


def _build_sort(sort: str) -> list[tuple]:
    """Build pymongo sort specification from sort parameter string."""
    sort_map = {
        "newest": [("is_pinned", DESCENDING), ("created_at", DESCENDING)],
        "oldest": [("is_pinned", DESCENDING), ("created_at", ASCENDING)],
        "updated": [("is_pinned", DESCENDING), ("updated_at", DESCENDING)],
        "alpha_asc": [("is_pinned", DESCENDING), ("title", ASCENDING)],
        "alpha_desc": [("is_pinned", DESCENDING), ("title", DESCENDING)],
    }
    return sort_map.get(sort, sort_map["newest"])


def _build_filter(params: NoteQueryParams) -> dict:
    """Build MongoDB filter dict from query parameters."""
    query: dict[str, Any] = {}

    if params.q:
        query["$text"] = {"$search": params.q}

    if params.category:
        query["category"] = params.category

    if params.tag:
        query["tags"] = {"$in": [params.tag]}

    if params.is_pinned is not None:
        query["is_pinned"] = params.is_pinned

    return query


class NoteRepository:
    """Async MongoDB repository for notes."""

    def __init__(self, collection: motor.motor_asyncio.AsyncIOMotorCollection):
        self.collection = collection

    # ── Create ───────────────────────────────────────────────────────────────

    async def create(self, note_data: NoteCreate) -> dict:
        """Insert a new note and return the created document."""
        now = datetime.now(timezone.utc)
        doc = {
            "title": note_data.title,
            "content": note_data.content,
            "category": note_data.category,
            "tags": note_data.tags,
            "is_pinned": note_data.is_pinned,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        created = await self.collection.find_one({"_id": result.inserted_id})
        return _doc_to_dict(created)

    # ── Read ─────────────────────────────────────────────────────────────────

    async def get_by_id(self, note_id: str) -> Optional[dict]:
        """Find a single note by its ID."""
        oid = _parse_object_id(note_id)
        doc = await self.collection.find_one({"_id": oid})
        return _doc_to_dict(doc) if doc else None

    async def list_notes(self, params: NoteQueryParams) -> tuple[list[dict], int]:
        """Return paginated list of notes and total count matching the filter."""
        query = _build_filter(params)
        sort = _build_sort(params.sort)
        skip = (params.page - 1) * params.page_size

        total = await self.collection.count_documents(query)

        cursor = self.collection.find(query).sort(sort).skip(skip).limit(params.page_size)
        docs = await cursor.to_list(length=params.page_size)

        return [_doc_to_dict(doc) for doc in docs], total

    async def get_all_categories(self) -> list[str]:
        """Return list of distinct categories that have notes."""
        cats = await self.collection.distinct("category")
        return [str(c) for c in cats if c and str(c).strip()]

    async def get_all_tags(self) -> list[str]:
        """Return list of distinct tags used across all notes."""
        tags = await self.collection.distinct("tags")
        return [str(t) for t in tags if t is not None and str(t).strip()]

    async def count_by_category(self) -> list[dict]:
        """Return note count per category."""
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"_id": ASCENDING}},
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=100)
        return [{"category": r["_id"] or "Other", "count": r["count"]} for r in result]

    async def count_pinned(self) -> int:
        """Return count of pinned notes."""
        return await self.collection.count_documents({"is_pinned": True})

    async def get_total_count(self) -> int:
        """Return total note count."""
        return await self.collection.count_documents({})

    # ── Update ───────────────────────────────────────────────────────────────

    async def update(self, note_id: str, note_data: NoteUpdate) -> Optional[dict]:
        """Update a note and return the updated document."""
        oid = _parse_object_id(note_id)

        update_fields = note_data.model_dump(exclude_none=True)
        if not update_fields:
            return await self.get_by_id(note_id)

        update_fields["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_fields},
            return_document=True,
        )
        return _doc_to_dict(result) if result else None

    async def toggle_pin(self, note_id: str) -> Optional[dict]:
        """Toggle the is_pinned field of a note."""
        oid = _parse_object_id(note_id)
        existing = await self.collection.find_one({"_id": oid})
        if not existing:
            return None

        new_pin_state = not existing.get("is_pinned", False)
        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": {"is_pinned": new_pin_state, "updated_at": datetime.now(timezone.utc)}},
            return_document=True,
        )
        return _doc_to_dict(result) if result else None

    # ── Delete ───────────────────────────────────────────────────────────────

    async def delete(self, note_id: str) -> bool:
        """Delete a note. Returns True if deleted, False if not found."""
        oid = _parse_object_id(note_id)
        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count == 1
