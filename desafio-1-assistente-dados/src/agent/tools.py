"""Thin wrappers around DB functions used by the agent graph nodes."""

from pathlib import Path

from src.db.connection import execute_query, get_schema_info


def fetch_schema(db_path: Path) -> str:
    """Return the full database schema as a formatted string."""
    return get_schema_info(db_path)


def run_sql(db_path: Path, sql: str) -> tuple[list[str], list[tuple]]:
    """Execute *sql* against the database and return (columns, rows)."""
    return execute_query(db_path, sql)
