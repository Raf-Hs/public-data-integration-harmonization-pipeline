-- Life expectancy trends.
SELECT country_iso3, country_name, year, value AS life_expectancy_years
FROM harmonised_data
WHERE indicator_id = 'SP.DYN.LE00.IN'
ORDER BY country_iso3, year;
