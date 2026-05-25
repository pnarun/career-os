"""Browser automation primitives (Playwright).

Submodules are imported explicitly so the worker subprocess does not load
Playwright when only lightweight helpers (e.g. session_logging) are needed.
"""
