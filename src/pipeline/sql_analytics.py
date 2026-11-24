"""SQL analytics helpers using DuckDB over published datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import duckdb
import pandas as pd

from .config import PUBLISHED_DIR, SQL_DIR
from .logging_config import configure_logging

logger = configure_logging()


def load_published(db_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    db_path = db_path or (PUBLISHED_DIR / "analytics.duckdb")
    return duckdb.connect(str(db_path), read_only=True)


def run_sql_file(conn: duckdb.DuckDBPyConnection, sql_path: Path) -> pd.DataFrame:
    sql = sql_path.read_text(encoding="utf-8")
    return conn.execute(sql).fetchdf()


def run_all_queries() -> Dict[str, pd.DataFrame]:
    conn = load_published()
    results: Dict[str, pd.DataFrame] = {}
    try:
        for sql_path in sorted(SQL_DIR.glob("*.sql")):
            try:
                results[sql_path.stem] = run_sql_file(conn, sql_path)
                logger.info("Executed SQL: %s (%d rows)", sql_path.name, len(results[sql_path.stem]))
            except Exception as exc:
                logger.error("SQL failed %s: %s", sql_path.name, exc)
                raise
    finally:
        conn.close()
    return results
