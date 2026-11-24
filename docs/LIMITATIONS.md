# Limitations

- Uses a fixed set of five countries and five indicators.
- Depends on World Bank API availability and data revisions.
- No real-time streaming or orchestration beyond GitHub Actions.
- Charts are static PNG files.
- Country metadata is embedded rather than fetched dynamically at runtime (metadata is still extracted and stored in raw layer).
- No authentication or secrets management beyond public API usage.
