# Pipeline Design

## Stages

1. Extract: query the World Bank API with pagination, retries, and timeouts; persist raw JSON.
2. Clean: normalize columns, parse years, standardize missing values, detect duplicates, validate required fields.
3. Harmonize: standardize ISO-3 codes, country names, years, units; attach metadata.
4. Validate: run quality checks; block publication on errors.
5. Publish: write CSV, Parquet, DuckDB; generate data dictionary.
6. Visualize: generate charts from published data.
7. Analyze: run DuckDB SQL queries.

## Error handling

- Retries with backoff on transient HTTP failures.
- Invalid records are reported, not silently discarded.
- Quality gate prevents invalid publication.
