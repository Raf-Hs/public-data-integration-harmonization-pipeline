"""Tests for the data quality framework."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.transform import clean
from src.pipeline.harmonize import harmonize
from src.pipeline.quality import run_quality_checks

FIXTURES = Path(__file__).parent / "fixtures"


def _harmonised_df():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    cleaned, _ = clean([data])
    return harmonize(cleaned)


def test_quality_passes_on_valid_data():
    df = _harmonised_df()
    report = run_quality_checks(df)
    assert report.passed is True
    assert report.error_count == 0 if hasattr(report, "error_count") else len(report.errors) == 0


def test_quality_detects_invalid_country():
    df = _harmonised_df().copy()
    df.loc[0, "country_iso3"] = "ZZZ"
    report = run_quality_checks(df)
    assert report.passed is False
    assert any("country" in e["check"] for e in report.errors)


def test_quality_detects_duplicates():
    df = _harmonised_df()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    report = run_quality_checks(df)
    assert report.passed is False
    assert any("duplicate" in e["check"] for e in report.errors)


def test_quality_detects_missing_required_field():
    df = _harmonised_df().copy()
    df.loc[0, "country_iso3"] = None
    report = run_quality_checks(df)
    assert report.passed is False


def test_quality_missing_observation_is_warning_not_error():
    df = _harmonised_df().copy()
    df.loc[0, "value"] = None
    report = run_quality_checks(df)
    # missing value alone should not cause failure
    assert report.passed is True
    assert any("missing_observations" in w["check"] or "value" in w["check"] for w in report.warnings + report.info)


def test_quality_report_serializable():
    df = _harmonised_df()
    report = run_quality_checks(df)
    d = report.to_dict()
    assert "passed" in d
    assert "errors" in d and "warnings" in d and "info" in d
