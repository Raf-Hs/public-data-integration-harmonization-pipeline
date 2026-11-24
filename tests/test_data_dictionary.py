"""Tests for data dictionary generation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.pipeline.transform import clean
from src.pipeline.harmonize import harmonize
from src.pipeline.data_dictionary import generate_data_dictionary, save_data_dictionary

FIXTURES = Path(__file__).parent / "fixtures"


def _df():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    cleaned, _ = clean([data])
    return harmonize(cleaned)


def test_generate_data_dictionary_nonempty():
    df = _df()
    dd = generate_data_dictionary(df)
    assert len(dd) > 0
    assert "column" in dd.columns
    assert "description" in dd.columns


def test_save_data_dictionary(tmp_path, monkeypatch):
    import src.pipeline.data_dictionary as ddmod
    monkeypatch.setattr(ddmod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ddmod, "DOCS_DIR", tmp_path)
    df = _df()
    path = save_data_dictionary(df, out_dir=tmp_path)
    assert path.exists()
    assert (tmp_path / "data_dictionary.csv").exists()
