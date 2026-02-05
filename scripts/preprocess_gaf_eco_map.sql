-- Preprocess gaf-eco-mapping.txt into koza-compatible TSV format
--
-- Input: data/gaf-eco-mapping.txt (3 columns: code, qualifier, eco_term)
-- Output: data/gaf-eco-map.tsv (2 columns: evidence_code, eco_term)
--
-- When qualifier is "Default", use code as-is
-- Otherwise, create compound key: "{code}-{qualifier}"

CREATE OR REPLACE TABLE gaf_eco_map AS
SELECT
    CASE
        WHEN lower(trim(qualifier)) = 'default' THEN code
        ELSE code || '-' || qualifier
    END AS evidence_code,
    eco_term
FROM read_csv(
    'data/gaf-eco-mapping.txt',
    delim='\t',
    header=false,
    names=['code', 'qualifier', 'eco_term'],
    comment='#'
)
ORDER BY evidence_code;

COPY gaf_eco_map TO 'data/gaf-eco-map.tsv' (HEADER, DELIMITER '\t');
