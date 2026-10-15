-- KPI queries run by ttc_pipeline/analyze.py.
-- Each query starts with a "-- name:" line; its result is saved to reports/kpis/<name>.csv.
-- "Incident" = any logged event. "Delay minutes" = sum of min_delay.
-- Many incidents have min_delay = 0 (logged but no service delay), so both are reported.

-- name: delays_by_line
SELECT
    line_name,
    COUNT(*)                                        AS incidents,
    SUM(CASE WHEN min_delay > 0 THEN 1 ELSE 0 END)  AS delayed_incidents,
    SUM(min_delay)                                  AS delay_minutes,
    ROUND(AVG(CASE WHEN min_delay > 0 THEN min_delay END), 1) AS avg_minutes_when_delayed
FROM delays
GROUP BY line_name
ORDER BY delay_minutes DESC;

-- name: top_stations
SELECT
    station,
    COUNT(*)        AS incidents,
    SUM(min_delay)  AS delay_minutes
FROM delays
WHERE location_type = 'STATION'
GROUP BY station
ORDER BY delay_minutes DESC
LIMIT 15;

-- name: top_causes
SELECT
    d.code,
    d.code_description,
    COUNT(*)          AS incidents,
    SUM(d.min_delay)  AS delay_minutes
FROM delays AS d
WHERE d.min_delay > 0
GROUP BY d.code, d.code_description
ORDER BY delay_minutes DESC
LIMIT 15;

-- name: delays_by_hour
SELECT
    hour,
    COUNT(*)                                        AS incidents,
    SUM(CASE WHEN min_delay > 0 THEN 1 ELSE 0 END)  AS delayed_incidents,
    SUM(min_delay)                                  AS delay_minutes
FROM delays
GROUP BY hour
ORDER BY hour;

-- name: delays_by_day_of_week
SELECT
    day_of_week,
    COUNT(*)        AS incidents,
    SUM(min_delay)  AS delay_minutes
FROM delays
GROUP BY day_of_week
ORDER BY CASE day_of_week
    WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4
    WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 ELSE 7 END;

-- name: monthly_trend
SELECT
    month,
    COUNT(*)                                        AS incidents,
    SUM(CASE WHEN min_delay > 0 THEN 1 ELSE 0 END)  AS delayed_incidents,
    SUM(min_delay)                                  AS delay_minutes
FROM delays
GROUP BY month
ORDER BY month;

-- name: yearly_summary
SELECT
    year,
    COUNT(*)                                        AS incidents,
    SUM(CASE WHEN min_delay > 0 THEN 1 ELSE 0 END)  AS delayed_incidents,
    SUM(min_delay)                                  AS delay_minutes,
    COUNT(DISTINCT month)                           AS months_covered
FROM delays
GROUP BY year
ORDER BY year;
