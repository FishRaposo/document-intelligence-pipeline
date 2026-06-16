"""Database availability probe and store selection.

Implements the migrated-service ``db_available`` pattern with a sync
``DatabaseManager``: on startup we probe the configured database; if reachable,
documents/chunks/jobs/quarantine persist to PostgreSQL via
``DatabaseDocumentStore`` and survive restarts. If the database is unavailable
(the offline-first default for tests and the demo), we transparently fall back to
``InMemoryDocumentStore`` so the service still runs with NO database.
"""

import socket
from typing import Optional
from urllib.parse import urlsplit

from loguru import logger
from shared_core.database import DatabaseManager
from sqlalchemy import text

from .config import AppConfig
from .storage import InMemoryDocumentStore
from .storage_db import DatabaseDocumentStore

config = AppConfig()

db_manager = DatabaseManager(
    config.DATABASE_URL,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_timeout=config.DB_POOL_TIMEOUT,
)

db_available: bool = False

# How long to wait for a TCP connection to the DB host before declaring it
# unreachable. Kept short so the offline-first fallback is fast (no slow driver
# connection timeout) for tests and the demo.
_SOCKET_TIMEOUT_SECONDS = 0.25


def _db_reachable(url: str) -> bool:
    """Fast TCP pre-check: can we open a socket to the database host:port?

    Avoids paying the SQLAlchemy/psycopg connection timeout (seconds) when no
    database is running — the common offline-first case. SQLite URLs are always
    considered reachable (file-based, no socket).
    """
    parts = urlsplit(url)
    if parts.scheme.startswith("sqlite"):
        return True
    host = parts.hostname or "localhost"
    port = parts.port or 5432
    try:
        # Resolve once and try a single address family so an unreachable host
        # costs one timeout, not one per IPv4/IPv6 candidate.
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError:
        return False
    family, socktype, proto, _, sockaddr = infos[0]
    sock = socket.socket(family, socktype, proto)
    sock.settimeout(_SOCKET_TIMEOUT_SECONDS)
    try:
        sock.connect(sockaddr)
        return True
    except OSError:
        return False
    finally:
        sock.close()


def check_db() -> bool:
    """Probe database connectivity and cache the result in ``db_available``."""
    global db_available
    if not _db_reachable(config.DATABASE_URL):
        db_available = False
        logger.info(
            "Database host unreachable — using in-memory document store (offline)."
        )
        return db_available
    try:
        with db_manager.SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_manager.create_tables()
        db_available = True
        logger.info("Database connected — documents will persist to PostgreSQL.")
    except Exception as exc:  # noqa: BLE001 - offline-first fallback
        db_available = False
        logger.warning(
            "Database unavailable — falling back to in-memory document store: {}",
            exc,
        )
    return db_available


def build_store(in_memory_fallback: Optional[InMemoryDocumentStore] = None):
    """Return the active document store based on the last probe result.

    When the DB is available, returns a ``DatabaseDocumentStore`` bound to the
    shared ``DatabaseManager`` session factory. Otherwise returns the provided
    in-memory fallback (or a fresh one).
    """
    if db_available:
        return DatabaseDocumentStore(db_manager.get_session)
    return in_memory_fallback or InMemoryDocumentStore()
