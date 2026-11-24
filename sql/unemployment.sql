-- Unemployment comparison (latest year).
SELECT country_iso3, country_name, year, value AS unemployment_pct
FROM harmonised_data
WHERE indicator_id = 'SL.UEM.TOTL.ZS'
  AND year = (SELECT MAX(year) FROM harmonised_data WHERE indicator_id = 'SL.UEM.TOTL.ZS')
ORDER BY value DESC;
