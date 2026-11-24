# Testing

## Approach

- Unit tests for parsing, normalization, harmonization, quality, publication, and data dictionary.
- Integration tests with controlled API response fixtures.
- End-to-end tests for the full pipeline without live API calls.

## Running

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest
```

## Results

28 tests pass as of the initial release.
