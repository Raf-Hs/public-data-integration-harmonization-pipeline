"""Publication layer: write validated datasets to CSV, Parquet, and DuckDB."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .config import PUBLISHED_DIR
from .logging_config import configure_logging

logger = configure_logging()


def publish_csv(df: pd.DataFrame, name: str = "harmonised_dataset") -> Path:
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    path = PUBLISHED_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    logger.info("Published CSV: %s (%d rows)", path, len(df))
    return path


def publish_parquet(df: pd.DataFrame, name: str = "harmonised_dataset") -> Path:
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    path = PUBLISHED_DIR / f"{name}.parquet"
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path)
    logger.info("Published Parquet: %s (%d rows)", path, len(df))
    return path


def publish_duckdb(df: pd.DataFrame, table_name: str = "harmonised_data", db_name: str = "analytics.duckdb") -> Path:
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    path = PUBLISHED_DIR / db_name
    # Remove existing to ensure clean state.
    if path.exists():
        path.unlink()
    conn = duckdb.connect(str(path))
    try:
        conn.register("df_view", df)
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_view")
        conn.commit()
    finally:
        conn.close()
    logger.info("Published DuckDB table '%s' in %s", table_name, path)
    return path


def publish_all(df: pd.DataFrame, quality_passed: bool) -> dict:
    """Publish only if quality gate passed. Returns dict of output paths."""
    if not quality_passed:
        raise ValueError("Publication gate blocked: quality checks did not pass.")
    paths = {}
    paths["csv"] = publish_csv(df)
    paths["parquet"] = publish_parquet(df)
    paths["duckdb"] = publish_duckdb(df)
    return paths
