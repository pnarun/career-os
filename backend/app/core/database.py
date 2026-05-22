import logging
import os
from typing import Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_NAME = "career_os"

_PLACEHOLDER_MARKERS = ("<user>", "<password>", "<cluster>")


def _validate_mongo_uri(mongo_uri: str) -> None:
    """Reject example/placeholder URIs before DNS lookup."""
    if any(marker in mongo_uri for marker in _PLACEHOLDER_MARKERS):
        raise ValueError(
            "MONGO_URI contains placeholder values (<user>, <password>, <cluster>). "
            "Copy your real connection string from MongoDB Atlas → Connect → Drivers "
            "into backend/.env"
        )


_client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None


def get_database() -> AsyncIOMotorDatabase:
    """Return the active MongoDB database instance."""
    if db is None:
        raise RuntimeError(
            "MongoDB is not initialized. Ensure the application lifespan has started."
        )
    return db


async def connect_to_mongo() -> None:
    """Create the Motor client and verify connectivity."""
    global _client, db

    mongo_uri = os.getenv("MONGO_URI", "").strip()
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable is not set")
    _validate_mongo_uri(mongo_uri)

    logger.info("Connecting to MongoDB (database: %s)...", DATABASE_NAME)
    _client = AsyncIOMotorClient(mongo_uri)
    db = _client[DATABASE_NAME]

    await _client.admin.command("ping")
    logger.info("MongoDB connection established successfully")


async def close_mongo_connection() -> None:
    """Close the Motor client and release resources."""
    global _client, db

    if _client is None:
        return

    logger.info("Closing MongoDB connection...")
    _client.close()
    _client = None
    db = None
    logger.info("MongoDB connection closed")
