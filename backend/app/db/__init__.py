"""Database utilities (indexes, query performance)."""

from app.db.indexes import ensure_all_mongo_indexes

__all__ = ["ensure_all_mongo_indexes"]
