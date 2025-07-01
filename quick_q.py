import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('eliseai_analysis.db')

# SQL query to get agent activity for specific date
query = """
SELECT 
    ed."Event ID",
    ed."Property Name",
    ed."Address",
    ed."City",
    ed."State",
    ed."Start Time",
    ed."End Time",
    ed."Tour Type",
    ed."Duration_Minutes",
    ed."Agent Name"
FROM event_details ed
WHERE ed."Leasing Agent ID" = '0650940d-f99a-48ba-b4f6-cca2a5127b86'
  AND DATE(ed."Start Time") = '2025-05-05'
ORDER BY ed."Start Time"
"""

# Execute query and get results
results = pd.read_sql_query(query, conn)

# Display results
print(f"Agent Activity for 2025-05-05")
print(f"Agent ID: 0650940d-f99a-48ba-b4f6-cca2a5127b86")
print(f"Total Tours: {len(results)}")
print("\nDetailed Schedule:")
print(results.to_string(index=False))

# Get summary statistics
if not results.empty:
    total_duration = results['Duration_Minutes'].sum()
    first_tour = results['Start Time'].min()
    last_tour = results['End Time'].max()
    
    print(f"\nSummary:")
    print(f"Total tour time: {total_duration:.0f} minutes ({total_duration/60:.1f} hours)")
    print(f"First tour: {first_tour}")
    print(f"Last tour: {last_tour}")
    print(f"Agent Name: {results['Agent Name'].iloc[0] if len(results) > 0 else 'N/A'}")
else:
    print("\nNo tours found for this agent on 2025-05-05")

# Close connection
conn.close()