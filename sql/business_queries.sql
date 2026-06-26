SELECT
    category,
    COUNT(*) AS total_funds
FROM fund_master
GROUP BY category
ORDER BY total_funds DESC;

SELECT
    fund_house,
    COUNT(*) AS total_funds
FROM fund_master
GROUP BY fund_house
ORDER BY total_funds DESC;


SELECT *
FROM scheme_performance
ORDER BY return_1y DESC
LIMIT 10;