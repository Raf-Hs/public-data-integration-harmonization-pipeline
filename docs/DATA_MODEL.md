# Data Model

## Layers

- **RAW**: Original API responses preserved as JSON with extraction timestamps.
- **CLEANED**: Normalized columns, parsed years, standardized missing values, duplicates removed.
- **HARMONISED**: Standardized ISO-3 country codes, canonical country names, canonical units, source traceability.
- **PUBLISHED**: CSV, Parquet, and DuckDB table for analytics.

## Harmonised table schema

| Column | Type | Description |
|---|---|---|
| country_iso3 | string | ISO-3 country code |
| country_iso2 | string | ISO-2 country code |
| country_name | string | Standardized country name |
| country_type | string | country vs aggregate/territory |
| region | string | World Bank region |
| income_level | string | World Bank income classification |
| indicator_id | string | Original World Bank indicator id |
| indicator_name | string | Human-readable name |
| year | int | Calendar year |
| value | float | Observed value (null for missing) |
| unit | string | Unit of measurement |
| source | string | Data source |
| extracted_at | string | UTC extraction timestamp |
