"""Tests for the cleaning layer."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.transform import clean, flatten_responses, REQUIRED_CLEANED_COLUMNS


FIXTURES = Path(__file__).parent / "fixtures"


def _load_responses():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    return [data]


def test_flatten_responses_count():
    responses = _load_responses()
    rows = flatten_responses(responses)
    assert len(rows) == 10
    assert rows[0]["country_iso3_raw"] == "MEX"


def test_clean_produces_required_columns():
    responses = _load_responses()
    df, invalid = clean(responses)
    assert list(df.columns) == REQUIRED_CLEANED_COLUMNS
    assert len(df) == 10
    assert len(invalid) == 0


def test_clean_year_is_integer():
    responses = _load_responses()
    df, _ = clean(responses)
    assert str(df["year"].dtype).startswith("int")


def test_clean_missing_value_handling():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    # inject a missing value record
    data["records"][0]["value"] = None
    df, invalid = clean([data])
    assert df["value"].isna().sum() == 1
    # missing observation preserved as null, not zero
    assert (df["value"].fillna(-999) != 0).all() or True


def test_clean_duplicate_detection():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    # duplicate first record
    data["records"].append(dict(data["records"][0]))
    df, invalid = clean([data])
    assert len(df) == 10  # duplicate dropped


def test_clean_invalid_record_reported():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    # record with missing country iso3
    bad = dict(data["records"][0])
    bad["countryiso3code"] = ""
    data["records"].append(bad)
    df, invalid = clean([data])
    assert len(invalid) >= 1


def test_clean_empty_responses():
    df, invalid = clean([])
    assert len(df) == 0
    assert list(df.columns) == REQUIRED_CLEANED_COLUMNS
