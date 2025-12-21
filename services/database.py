import hashlib
import sqlite3
from pathlib import Path

import orjson

DB_PATH = Path(__file__).parent.parent / "cache.db"


def _get_connection() -> sqlite3.Connection:
    """Get a database connection, creating tables if needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resume_cache (
            content_hash TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            parsed_resume TEXT NOT NULL,
            assessment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def get_content_hash(content: bytes) -> str:
    """Generate SHA256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def get_cached_result(content_hash: str) -> dict | None:
    """Retrieve cached parsing result by content hash.

    Returns:
        Dict with 'parsed_resume' and 'assessment' if found, None otherwise
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT parsed_resume, assessment, filename FROM resume_cache WHERE content_hash = ?",
            (content_hash,)
        ).fetchone()

        if not row:
            return None

        parsed_resume = orjson.loads(row["parsed_resume"])
        assessment = orjson.loads(row["assessment"])

        # If the previous parse failed, treat this as a cache miss so we can retry
        if not parsed_resume.get("parse_success", False):
            return None

        return {
            "parsed_resume": parsed_resume,
            "assessment": assessment,
            "filename": row["filename"],
        }
    finally:
        conn.close()


def cache_result(
    content_hash: str,
    filename: str,
    parsed_resume: dict,
    assessment: dict,
) -> None:
    """Store parsing result in cache."""
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO resume_cache (content_hash, filename, parsed_resume, assessment)
            VALUES (?, ?, ?, ?)
            """,
            (
                content_hash,
                filename,
                orjson.dumps(parsed_resume).decode(),
                orjson.dumps(assessment).decode(),
            )
        )
        conn.commit()
    finally:
        conn.close()
