-- Calculate consecutive tours for each agent by date
WITH agent_consecutive_tours AS (
    SELECT 
        "Date",
        "Leasing Agent ID",
        "Agent Name",
        "Property ID",
        "Property Name",
        "Start Time",
        "End Time",
        LAG("Property ID") OVER (
            PARTITION BY "Date", "Leasing Agent ID" 
            ORDER BY "Start Time"
        ) as prev_property_id,
        LAG("End Time") OVER (
            PARTITION BY "Date", "Leasing Agent ID" 
            ORDER BY "Start Time"
        ) as prev_end_time
    FROM event_details
)
SELECT 
    "Date",
    "Leasing Agent ID",
    "Agent Name",
    COUNT(*) as total_tours,
    COUNT(CASE WHEN prev_property_id IS NOT NULL 
               AND prev_property_id != "Property ID" 
          THEN 1 END) as property_changes,
    COUNT(CASE WHEN prev_property_id IS NOT NULL THEN 1 END) as travel_segments
FROM agent_consecutive_tours
GROUP BY "Date", "Leasing Agent ID", "Agent Name"
ORDER BY property_changes DESC;

-- Find agents with most cross-property travel
SELECT 
    "Agent Name",
    COUNT(DISTINCT "Date") as active_days,
    COUNT(*) as total_tours,
    COUNT(DISTINCT "Property ID") as properties_visited,
    ROUND(
        CAST(COUNT(DISTINCT "Property ID") AS FLOAT) / COUNT(DISTINCT "Date"), 2
    ) as avg_properties_per_day
FROM event_details
GROUP BY "Leasing Agent ID", "Agent Name"
HAVING COUNT(*) > 5
ORDER BY avg_properties_per_day DESC;