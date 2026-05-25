"""WebSocket manager tests."""

from app.realtime.websocket_manager import RealtimeConnectionManager


def test_connection_count_empty():
    manager = RealtimeConnectionManager()
    assert manager.total_connections() == 0
    assert manager.connection_count("user-1") == 0
