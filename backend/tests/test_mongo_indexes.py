"""Mongo index registry tests."""

from app.db.indexes import COLLECTION_INDEX_REGISTRY, _normalize_keys


def test_jobs_indexes_registered():
    names = {spec.name for spec in COLLECTION_INDEX_REGISTRY["jobs"]}
    assert "jobs_user_created" in names
    assert "jobs_user_latest_scan" in names
    assert "jobs_source_created" in names


def test_normalize_keys_string():
    assert _normalize_keys(["user_id"]) == [("user_id", 1)]


def test_scan_sessions_unique_scan_id():
    specs = COLLECTION_INDEX_REGISTRY["scan_sessions"]
    unique = [s for s in specs if s.unique and "scan_id" in s.name]
    assert len(unique) == 1
