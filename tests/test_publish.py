"""Tests for the publication layer."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from src.pipeline.transform import clean
from src.pipeline.harmonize import harmonize
from src.pipeline.publish import publish_all, publish_csv, publish_parquet, publish_duckdb
from src.pipeline.quality import run_quality_checks

FIXTURES = Path(__file__).parent / "fixtures"


def _df():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    cleaned, _ = clean([data])
    return harmonize(cleaned)


def test_publish_blocked_on_failed_quality(tmp_path, monkeypatch):
    import src.pipeline.publish as pub
    monkeypatch.setattr(pub, "PUBLISHED_DIR", tmp_path)
    df = _df()
    with pytest.raises(ValueError):
        publish_all(df, quality_passed=False)


def test_publish_csv_parquet_duckdb(tmp_path, monkeypatch):
    import src.pipeline.publish as pub
    monkeypatch.setattr(pub, "PUBLISHED_DIR", tmp_path)
    df = _df()
    paths = publish_all(df, quality_passed=True)
    assert Path(paths["csv"]).exists()
    assert Path(paths["parquet"]).exists()
    assert Path(paths["duckdb"]).exists()
    # verify duckdb readable
    conn = duckdb.connect(str(paths["duckdb"]), read_only=True)
    n = conn.execute("SELECT COUNT(*) FROM harmonised_data").fetchone()[0]
    conn.close()
    assert n == len(df)
