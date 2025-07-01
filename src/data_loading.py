import pandas as pd
import sqlite3
from datetime import datetime
import numpy as np

def load_excel_data(file_path):
    """Load all sheets from Excel file"""
    
    # Load each sheet
    event_log = pd.read_excel(file_path, sheet_name='AGENT CALENDAR EVENT LOG')
    agent_mapping = pd.read_excel(file_path, sheet_name='Agent Mapping')
    property_mapping = pd.read_excel(file_path, sheet_name='Property Mapping')
    
    # Clean and process event log
    event_log['Start Time'] = pd.to_datetime(event_log['Start Time'])
    event_log['End Time'] = pd.to_datetime(event_log['End Time'])
    event_log['Duration_Minutes'] = (event_log['End Time'] - event_log['Start Time']).dt.total_seconds() / 60
    event_log['Date'] = event_log['Start Time'].dt.date
    
    return event_log, agent_mapping, property_mapping

def setup_database(event_log, agent_mapping, property_mapping):
    """Create SQLite database with all tables"""
    conn = sqlite3.connect('eliseai_analysis.db')

    # Create tables
    event_log.to_sql('events', conn, if_exists='replace', index=False)
    agent_mapping.to_sql('agents', conn, if_exists='replace', index=False)
    property_mapping.to_sql('properties', conn, if_exists='replace', index=False)

    # Create indexes for performance
    conn.execute('CREATE INDEX idx_events_agent_id ON events("Leasing Agent ID")')
    conn.execute('CREATE INDEX idx_events_property_id ON events("Property ID")')
    conn.execute('CREATE INDEX idx_events_start_time ON events("Start Time")')

    conn.execute('''
    CREATE VIEW event_details AS
    SELECT 
        e."Event ID",
        e."Property ID",
        p."Property Name",
        p."Address",
        p."City",
        p."State",
        e."Start Time",
        e."End Time",
        e."Tour Type",
        e."Leasing Agent ID",
        a."Agent Name",
        e."Duration_Minutes",
        e."Date"
    FROM events e
    JOIN agents a ON e."Leasing Agent ID" = a."Agent ID"
    JOIN properties p ON e."Property ID" = p."Property ID"
    ORDER BY e."Start Time"
    ''')

    conn.execute('''
    CREATE VIEW daily_agent_schedule AS
    SELECT 
        "Date",
        "Leasing Agent ID",
        "Agent Name",
        COUNT(*) as tours_count,
        MIN("Start Time") as first_tour,
        MAX("End Time") as last_tour,
        SUM("Duration_Minutes") as total_tour_minutes
    FROM event_details
    GROUP BY "Date", "Leasing Agent ID", "Agent Name"
    ORDER BY "Date", "Leasing Agent ID"
    ''')
    
    conn.close()
    return "Database created successfully"

event_log, agent_mapping, property_mapping = load_excel_data('data/Agent Calendar Practical Materials.xlsx')