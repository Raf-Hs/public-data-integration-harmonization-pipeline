"""Visualization layer: generate charts from harmonised data."""

from __future__ import annotations

from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .config import FIGURES_DIR, INDICATORS
from .logging_config import configure_logging

logger = configure_logging()

PALETTE = {
    "charcoal": "#171717",
    "offwhite": "#F4F0E8",
    "blue": "#2F5D8C",
    "accent": "#B85C38",
}


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": PALETTE["offwhite"],
            "axes.facecolor": PALETTE["offwhite"],
            "axes.edgecolor": PALETTE["charcoal"],
            "axes.labelcolor": PALETTE["charcoal"],
            "text.color": PALETTE["charcoal"],
            "xtick.color": PALETTE["charcoal"],
            "ytick.color": PALETTE["charcoal"],
            "font.size": 10,
        }
    )


def _save(fig, name: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    logger.info("Saved figure: %s", path)
    return path


def plot_population(df: pd.DataFrame) -> Path:
    _setup_style()
    ind = "SP.POP.TOTL"
    sub = df[df["indicator_id"] == ind]
    fig, ax = plt.subplots(figsize=(9, 5))
    for country, g in sub.groupby("country_name"):
        g = g.sort_values("year")
        ax.plot(g["year"], g["value"] / 1e6, marker="o", label=country)
    ax.set_title("Population Comparison (2015-2024)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Population (millions)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    return _save(fig, "population_comparison.png")


def plot_gdp(df: pd.DataFrame) -> Path:
    _setup_style()
    ind = "NY.GDP.PCAP.CD"
    sub = df[df["indicator_id"] == ind]
    fig, ax = plt.subplots(figsize=(9, 5))
    for country, g in sub.groupby("country_name"):
        g = g.sort_values("year")
        ax.plot(g["year"], g["value"], marker="o", label=country)
    ax.set_title("GDP per Capita Trends (current US$)")
    ax.set_xlabel("Year")
    ax.set_ylabel("GDP per capita (current US$)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    return _save(fig, "gdp_per_capita_trends.png")


def plot_life_expectancy(df: pd.DataFrame) -> Path:
    _setup_style()
    ind = "SP.DYN.LE00.IN"
    sub = df[df["indicator_id"] == ind]
    fig, ax = plt.subplots(figsize=(9, 5))
    for country, g in sub.groupby("country_name"):
        g = g.sort_values("year")
        ax.plot(g["year"], g["value"], marker="o", label=country)
    ax.set_title("Life Expectancy at Birth Trends")
    ax.set_xlabel("Year")
    ax.set_ylabel("Years")
    ax.legend()
    ax.grid(True, alpha=0.3)
    return _save(fig, "life_expectancy_trends.png")


def plot_unemployment(df: pd.DataFrame) -> Path:
    _setup_style()
    ind = "SL.UEM.TOTL.ZS"
    sub = df[df["indicator_id"] == ind]
    # latest year available
    latest_year = int(sub["year"].max())
    latest = sub[sub["year"] == latest_year].sort_values("value", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(latest["country_name"], latest["value"], color=PALETTE["blue"])
    ax.set_title(f"Unemployment Comparison ({latest_year})")
    ax.set_xlabel("Unemployment (% of labor force)")
    ax.set_ylabel("Country")
    return _save(fig, "unemployment_comparison.png")


def plot_electricity(df: pd.DataFrame) -> Path:
    _setup_style()
    ind = "EG.ELC.ACCS.ZS"
    sub = df[df["indicator_id"] == ind]
    fig, ax = plt.subplots(figsize=(9, 5))
    for country, g in sub.groupby("country_name"):
        g = g.sort_values("year")
        ax.plot(g["year"], g["value"], marker="o", label=country)
    ax.set_title("Access to Electricity Trends")
    ax.set_xlabel("Year")
    ax.set_ylabel("Access to electricity (% of population)")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(True, alpha=0.3)
    return _save(fig, "electricity_access_trends.png")


def plot_missing_observations(df: pd.DataFrame, quality_report: dict | None = None) -> Path:
    _setup_style()
    # Build missing matrix from expected years.
    countries = sorted(df["country_name"].unique())
    indicators = list(INDICATORS.keys())
    # expected years
    years = range(2015, 2025)
    # count missing per country-indicator
    matrix = pd.DataFrame(0, index=countries, columns=indicators)
    for c in countries:
        for ind in indicators:
            present = df[(df["country_name"] == c) & (df["indicator_id"] == ind)]["year"].tolist()
            missing = len([y for y in years if y not in present])
            # also count null values
            nulls = int(df[(df["country_name"] == c) & (df["indicator_id"] == ind)]["value"].isna().sum())
            matrix.loc[c, ind] = missing + nulls
    fig, ax = plt.subplots(figsize=(9, 5))
    im = ax.imshow(matrix.values, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(indicators)))
    ax.set_xticklabels([INDICATORS[i]["name"][:18] for i in indicators], rotation=45, ha="right")
    ax.set_yticks(range(len(countries)))
    ax.set_yticklabels(countries)
    ax.set_title("Missing Observation Distribution")
    for i in range(len(countries)):
        for j in range(len(indicators)):
            ax.text(j, i, int(matrix.values[i, j]), ha="center", va="center", color="black")
    fig.colorbar(im, ax=ax, label="Missing observations")
    return _save(fig, "missing_observation_distribution.png")


def plot_coverage(df: pd.DataFrame) -> Path:
    _setup_style()
    cov = df.groupby(["country_name", "indicator_id"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(9, 5))
    im = ax.imshow(cov.values, aspect="auto", cmap="Greens", vmin=0, vmax=10)
    ax.set_xticks(range(len(cov.columns)))
    ax.set_xticklabels([INDICATORS[i]["name"][:18] for i in cov.columns], rotation=45, ha="right")
    ax.set_yticks(range(len(cov.index)))
    ax.set_yticklabels(cov.index)
    ax.set_title("Data Coverage by Country and Indicator (observations)")
    for i in range(len(cov.index)):
        for j in range(len(cov.columns)):
            ax.text(j, i, int(cov.values[i, j]), ha="center", va="center", color="black")
    fig.colorbar(im, ax=ax, label="Observations")
    return _save(fig, "data_coverage.png")


def plot_quality_results(quality_report: dict) -> Path:
    _setup_style()
    counts = {
        "Errors": len(quality_report.get("errors", [])),
        "Warnings": len(quality_report.get("warnings", [])),
        "Info": len(quality_report.get("info", [])),
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(list(counts.keys()), list(counts.values()), color=[PALETTE["accent"], "#D9A441", PALETTE["blue"]])
    ax.set_title("Data Quality Results")
    ax.set_ylabel("Number of checks")
    for b, v in zip(bars, counts.values()):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.1, str(v), ha="center")
    return _save(fig, "data_quality_results.png")


def generate_all_charts(df: pd.DataFrame, quality_report: dict | None = None) -> List[Path]:
    paths = []
    paths.append(plot_population(df))
    paths.append(plot_gdp(df))
    paths.append(plot_life_expectancy(df))
    paths.append(plot_unemployment(df))
    paths.append(plot_electricity(df))
    paths.append(plot_missing_observations(df, quality_report))
    paths.append(plot_coverage(df))
    if quality_report is not None:
        paths.append(plot_quality_results(quality_report))
    return paths
