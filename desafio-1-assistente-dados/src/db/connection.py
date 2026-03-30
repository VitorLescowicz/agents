"""Database connection and introspection utilities.

Provides read-only SQLite access and dynamic schema introspection
for the LangGraph agent.
"""

import sqlite3
from pathlib import Path


def _read_only_connection(db_path: Path) -> sqlite3.Connection:
    """Open a read-only SQLite connection using URI mode."""
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def get_schema_info(db_path: Path) -> str:
    """Return a human-readable schema description for every table.

    Includes column names/types, foreign keys, and a sample of distinct
    values per column (up to 10) so the LLM understands the data domain.
    """
    conn = _read_only_connection(db_path)
    cursor = conn.cursor()

    # Discover tables
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]

    parts: list[str] = []

    for table in tables:
        # Row count
        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")  # noqa: S608
        row_count = cursor.fetchone()[0]

        # Column info
        cursor.execute(f"PRAGMA table_info([{table}])")
        columns = cursor.fetchall()  # cid, name, type, notnull, default, pk

        # Foreign keys
        cursor.execute(f"PRAGMA foreign_key_list([{table}])")
        fks = cursor.fetchall()
        fk_map: dict[str, str] = {}
        for fk in fks:
            fk_map[fk[3]] = f"{fk[2]}.{fk[4]}"  # from_col -> table.to_col

        lines = [f"### Tabela: {table}  ({row_count} registros)"]
        lines.append("| Coluna | Tipo | PK | FK | Exemplos |")
        lines.append("|--------|------|----|----|----------|")

        for col in columns:
            col_name = col[1]
            col_type = col[2] or "TEXT"
            is_pk = "Sim" if col[5] else ""
            fk_ref = fk_map.get(col_name, "")

            # Sample distinct values
            try:
                cursor.execute(
                    f"SELECT DISTINCT [{col_name}] FROM [{table}] "  # noqa: S608
                    f"WHERE [{col_name}] IS NOT NULL LIMIT 10"
                )
                samples = [str(r[0]) for r in cursor.fetchall()]
                samples_str = ", ".join(samples)
                if len(samples_str) > 80:
                    samples_str = samples_str[:77] + "..."
            except Exception:
                samples_str = ""

            lines.append(
                f"| {col_name} | {col_type} | {is_pk} | {fk_ref} | {samples_str} |"
            )

        parts.append("\n".join(lines))

    conn.close()
    return "\n\n".join(parts)


def execute_query(db_path: Path, sql: str) -> tuple[list[str], list[tuple]]:
    """Execute a read-only SQL query and return (column_names, rows).

    Raises ``sqlite3.Error`` on failure so the caller can capture the
    message for LLM retry logic.
    """
    conn = _read_only_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return columns, rows
    finally:
        conn.close()
