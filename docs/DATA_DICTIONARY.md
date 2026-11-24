# Data Dictionary

| Column | Data Type | Description |
|---|---|---|
| country_iso3 | string | ISO 3166-1 alpha-3 country code (standardized). |
| country_iso2 | string | ISO 3166-1 alpha-2 country code. |
| country_name | string | Standardized country name. |
| country_type | string | Classification: country vs aggregate/territory. |
| region | string | World Bank region. |
| income_level | string | World Bank income classification. |
| indicator_id | string | Original World Bank indicator identifier (preserved). |
| indicator_name | string | Human-readable indicator name. |
| year | int64 | Calendar year of observation (integer). |
| value | float64 | Observed numeric value (missing observations are null, not zero). |
| unit | string | Unit of measurement. |
| source | str | Data source identifier. |
| extracted_at | str | UTC timestamp of extraction. |
| indicator_id=SP.POP.TOTL | identifier | Population, total | unit: People | Total population based on the de facto definition of population. |
| indicator_id=NY.GDP.PCAP.CD | identifier | GDP per capita (current US$) | unit: Current US$ | Gross domestic product divided by midyear population. |
| indicator_id=SP.DYN.LE00.IN | identifier | Life expectancy at birth, total (years) | unit: Years | Number of years a newborn infant would live if prevailing mortality patterns persist. |
| indicator_id=SL.UEM.TOTL.ZS | identifier | Unemployment, total (% of total labor force) | unit: Percentage | Share of the labor force without work but available for and seeking employment (modeled ILO estimate). |
| indicator_id=EG.ELC.ACCS.ZS | identifier | Access to electricity (% of population) | unit: Percentage | Percentage of population with access to electricity. |
| country_iso3=MEX | identifier | Country: Mexico |
| country_iso3=USA | identifier | Country: United States |
| country_iso3=BRA | identifier | Country: Brazil |
| country_iso3=IND | identifier | Country: India |
| country_iso3=DEU | identifier | Country: Germany |
