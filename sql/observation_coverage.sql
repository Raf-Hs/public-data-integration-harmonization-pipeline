-- Observation coverage per country and indicator.
SELECT country_iso3, country_name, indicator_id, COUNT(*) AS observations,
       MIN(year) AS first_year, MAX(year) AS last_year
FROM harmonised_data
GROUP BY country_iso3, country_name, indicator_id
ORDER BY country_iso3, indicator_id;
