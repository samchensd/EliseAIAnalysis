#!/usr/bin/env python3
"""
EliseAI Database Explorer
Analyzes the structure and content of eliseai_analysis.db
"""

import sqlite3
import pandas as pd
from pathlib import Path

def explore_database(db_path="eliseai_analysis.db"):
    """
    Comprehensive exploration of the EliseAI database
    """
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"❌ Database {db_path} not found!")
        return
    
    print(f"🔍 Exploring database: {db_path}")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No tables found in database!")
            return
        
        print(f"📊 Found {len(tables)} tables:")
        table_names = [table[0] for table in tables]
        for i, table_name in enumerate(table_names, 1):
            print(f"  {i}. {table_name}")
        
        print("\n" + "=" * 60)
        
        # 2. Analyze each table
        for table_name in table_names:
            print(f"\n🔍 TABLE: {table_name}")
            print("-" * 40)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("📋 Schema:")
            for col in columns:
                col_id, name, data_type, not_null, default, pk = col
                pk_marker = " (PRIMARY KEY)" if pk else ""
                null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default}" if default else ""
                print(f"  • {name}: {data_type}{pk_marker}{null_marker}{default_marker}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            print(f"\n📈 Row count: {row_count}")
            
            if row_count > 0:
                # Get sample data
                print(f"\n📝 Sample data (first 5 rows):")
                df = pd.read_sql_query(f"SELECT * FROM [{table_name}] LIMIT 5", conn)
                print(df.to_string(index=False))
                
                # Get column statistics for numeric columns
                numeric_cols = []
                for col in columns:
                    col_name = col[1]
                    col_type = col[2].upper()
                    if any(t in col_type for t in ['INT', 'REAL', 'FLOAT', 'NUMERIC', 'DECIMAL']):
                        numeric_cols.append(col_name)
                
                if numeric_cols:
                    print(f"\n📊 Numeric column statistics:")
                    for col in numeric_cols:
                        try:
                            cursor.execute(f"""
                                SELECT 
                                    MIN([{col}]) as min_val,
                                    MAX([{col}]) as max_val,
                                    AVG([{col}]) as avg_val,
                                    COUNT(DISTINCT [{col}]) as unique_count
                                FROM [{table_name}]
                                WHERE [{col}] IS NOT NULL
                            """)
                            stats = cursor.fetchone()
                            if stats and stats[0] is not None:
                                print(f"  • {col}: min={stats[0]:.2f}, max={stats[1]:.2f}, avg={stats[2]:.2f}, unique={stats[3]}")
                        except sqlite3.Error as e:
                            print(f"  • {col}: Error analyzing - {e}")
                
                # Check for date/time columns
                date_cols = []
                for col in columns:
                    col_name = col[1]
                    col_type = col[2].upper()
                    if any(t in col_type for t in ['DATE', 'TIME', 'TIMESTAMP']) or any(t in col_name.lower() for t in ['date', 'time', 'timestamp', 'created', 'updated']):
                        date_cols.append(col_name)
                
                if date_cols:
                    print(f"\n📅 Date/Time column ranges:")
                    for col in date_cols:
                        try:
                            cursor.execute(f"""
                                SELECT 
                                    MIN([{col}]) as earliest,
                                    MAX([{col}]) as latest,
                                    COUNT(DISTINCT [{col}]) as unique_dates
                                FROM [{table_name}]
                                WHERE [{col}] IS NOT NULL
                            """)
                            stats = cursor.fetchone()
                            if stats and stats[0] is not None:
                                print(f"  • {col}: {stats[0]} to {stats[1]} ({stats[2]} unique)")
                        except sqlite3.Error as e:
                            print(f"  • {col}: Error analyzing - {e}")
            
            print("\n" + "-" * 40)
        
        # 3. Look for relationships between tables
        print(f"\n🔗 FOREIGN KEY RELATIONSHIPS:")
        print("-" * 40)
        
        for table_name in table_names:
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            fks = cursor.fetchall()
            if fks:
                print(f"\n{table_name}:")
                for fk in fks:
                    print(f"  • {fk[3]} → {fk[2]}.{fk[4]}")
        
        # 4. Look for common patterns in column names
        print(f"\n🏷️  COMMON COLUMN PATTERNS:")
        print("-" * 40)
        
        all_columns = []
        for table_name in table_names:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                all_columns.append((table_name, col[1]))
        
        # Group by column name patterns
        patterns = {}
        for table, col in all_columns:
            col_lower = col.lower()
            if 'id' in col_lower:
                patterns.setdefault('IDs', []).append(f"{table}.{col}")
            elif any(t in col_lower for t in ['date', 'time', 'timestamp']):
                patterns.setdefault('Dates/Times', []).append(f"{table}.{col}")
            elif any(t in col_lower for t in ['name', 'title']):
                patterns.setdefault('Names/Titles', []).append(f"{table}.{col}")
            elif any(t in col_lower for t in ['agent', 'user']):
                patterns.setdefault('Agent/User', []).append(f"{table}.{col}")
            elif any(t in col_lower for t in ['property', 'location']):
                patterns.setdefault('Property/Location', []).append(f"{table}.{col}")
        
        for pattern, cols in patterns.items():
            if len(cols) > 1:  # Only show patterns with multiple columns
                print(f"\n{pattern}:")
                for col in cols[:10]:  # Limit to first 10
                    print(f"  • {col}")
                if len(cols) > 10:
                    print(f"  ... and {len(cols) - 10} more")
        
        conn.close()
        
        print(f"\n✅ Database exploration complete!")
        print(f"💡 Ready to create metrics.py based on this structure")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    explore_database()