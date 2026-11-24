-- Missing data analysis: country-indicator pairs with null values.
SELECT country_iso3, country_name, indicator_id, year
FROM harmonised_data
WHERE value IS NULL
ORDER BY country_iso3, indicator_id, year;
