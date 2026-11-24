# Data Quality

## Checks

- Structural: required columns, data types, year range.
- Completeness: missing identifiers and years; missing values counted as observations.
- Uniqueness: duplicate country-indicator-year combinations.
- Validity: valid country and indicator identifiers, finite numeric values.
- Consistency: units per indicator, country code format.
- Time-series: missing historical observations, unexpected gaps, unusual changes (>50% YoY) flagged as warnings.

## Publication gate

Publication is blocked if any error-level check fails. Warnings and informational observations do not block publication.

## Missing observations vs zero

A missing observation is represented as null. It is never converted to zero.
