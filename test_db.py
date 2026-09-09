"""Utility script to verify MongoDB connection from .env settings."""
import asyncio
import sys
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient


async def main():
    settings = get_settings()
    print(f"Testing connection to: {settings.mongodb_url}")
    print(f"Target database: {settings.database_name}")
    try:
        client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
        # Test basic server connectivity
        ping_res = await client.admin.command("ping")
        print("[SUCCESS] Connected to MongoDB cluster successfully! Ping response:", ping_res)

        # Test database access
        db = client[settings.database_name]
        collections = await db.list_collection_names()
        print(f"[SUCCESS] Database '{settings.database_name}' accessible! Existing collections: {collections}")
        client.close()
    except Exception as e:
        print(f"\n[FAILED] Connection failed: {e}\n", file=sys.stderr)
        if "Authentication failed" in str(e):
            print("Troubleshooting 'Authentication failed':", file=sys.stderr)
            print("1. In MongoDB Atlas, go to 'Database Access' and check your exact username.", file=sys.stderr)
            print("2. Atlas passwords must be at least 8 characters. Make sure you are using the database password, not your Atlas account login password.", file=sys.stderr)
            print("3. Reset the user password in Atlas ('Edit' -> 'Edit Password') and update .env.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
