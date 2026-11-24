-- Electricity access trends.
SELECT country_iso3, country_name, year, value AS electricity_access_pct
FROM harmonised_data
WHERE indicator_id = 'EG.ELC.ACCS.ZS'
ORDER BY country_iso3, year;
