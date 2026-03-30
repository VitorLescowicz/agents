from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT / "desafio-1-assistente-dados"
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.connection import execute_query, get_schema_info  # noqa: E402
from src.viz.chart_picker import pick_chart  # noqa: E402


def main() -> None:
    db_path = PROJECT_ROOT / "data" / "clientes_completo.db"
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    schema = get_schema_info(db_path)
    if "Tabela: clientes" not in schema or "Tabela: compras" not in schema:
        raise SystemExit("Schema introspection did not return the expected tables.")

    columns, rows = execute_query(
        db_path,
        (
            "SELECT categoria, COUNT(*) AS total "
            "FROM compras GROUP BY categoria ORDER BY total DESC LIMIT 5"
        ),
    )
    if columns != ["categoria", "total"]:
        raise SystemExit(f"Unexpected query columns: {columns}")
    if len(rows) != 5:
        raise SystemExit(f"Unexpected row count: {len(rows)}")
    if pick_chart(columns, rows) != "bar":
        raise SystemExit("Chart picker did not choose a bar chart for grouped counts.")

    print("desafio-1 smoke test passed")


if __name__ == "__main__":
    main()
