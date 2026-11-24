-- GDP per capita comparison across countries (latest available year).
SELECT country_iso3, country_name, year, value AS gdp_per_capita_usd
FROM harmonised_data
WHERE indicator_id = 'NY.GDP.PCAP.CD'
  AND year = (SELECT MAX(year) FROM harmonised_data WHERE indicator_id = 'NY.GDP.PCAP.CD')
ORDER BY value DESC;
