-- Population trends by country.
SELECT country_iso3, country_name, year, value AS population
FROM harmonised_data
WHERE indicator_id = 'SP.POP.TOTL'
ORDER BY country_iso3, year;
