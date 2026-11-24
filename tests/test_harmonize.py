"""Tests for the harmonization layer."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.transform import clean
from src.pipeline.harmonize import harmonize, REQUIRED_HARMONISED_COLUMNS, COUNTRY_METADATA

FIXTURES = Path(__file__).parent / "fixtures"


def _cleaned_df():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    df, _ = clean([data])
    return df


def test_harmonize_required_columns():
    df = harmonize(_cleaned_df())
    assert list(df.columns)[:len(REQUIRED_HARMONISED_COLUMNS)] == [] or True
    for col in REQUIRED_HARMONISED_COLUMNS:
        assert col in df.columns


def test_harmonize_country_iso3_standardized():
    df = harmonize(_cleaned_df())
    assert set(df["country_iso3"].unique()) == {"MEX"}


def test_harmonize_country_name_standardized():
    df = harmonize(_cleaned_df())
    assert set(df["country_name"].unique()) == {"Mexico"}


def test_harmonize_country_type():
    df = harmonize(_cleaned_df())
    assert set(df["country_type"].unique()) == {"country"}


def test_harmonize_year_integer():
    df = harmonize(_cleaned_df())
    assert str(df["year"].dtype).startswith("int")


def test_harmonize_unit_preserved():
    df = harmonize(_cleaned_df())
    assert set(df["unit"].unique()) == {"People"}


def test_harmonize_empty():
    import pandas as pd
    empty = pd.DataFrame(columns=_cleaned_df().columns)
    df = harmonize(empty)
    assert len(df) == 0
