import pandas as pd
import numpy as np
from datetime import datetime


def examine_saved_analysis_files():
    """
    Examine the saved CSV files from your previous analysis to understand 
    the lateness results without re-running the full analysis.
    """
    
    print("🔍 EXAMINING SAVED ANALYSIS RESULTS")
    print("=" * 60)
    
    # List of files to check
    files_to_check = [
        'daily_travel_details.csv',
        'agent_shift_metrics.csv', 
        'optimization_results_with_trips.csv',
        'lateness_analysis_incidents.csv',
        'lateness_analysis_agent_summary.csv',
        'impossible_schedules.csv'
    ]
    
    available_files = []
    
    # Check which files exist
    for filename in files_to_check:
        try:
            df = pd.read_csv(filename)
            print(f"✅ Found {filename}: {len(df)} rows")
            available_files.append((filename, df))
        except FileNotFoundError:
            print(f"❌ Missing {filename}")
        except Exception as e:
            print(f"⚠️  Error reading {filename}: {e}")
    
    if not available_files:
        print("\n❌ No saved analysis files found. Please run the main analysis first.")
        return None
    
    print(f"\n📊 ANALYZING AVAILABLE DATA")
    print("=" * 60)
    
    results = {}
    
    # Examine each available file
    for filename, df in available_files:
        print(f"\n📁 EXAMINING: {filename}")
        print("-" * 40)
        
        if filename == 'lateness_analysis_incidents.csv':
            examine_lateness_incidents(df)
            results['lateness_incidents'] = df
            
        elif filename == 'lateness_analysis_agent_summary.csv':
            examine_agent_lateness_summary(df)
            results['agent_summary'] = df
            
        elif filename == 'impossible_schedules.csv':
            examine_impossible_schedules(df)
            results['impossible_schedules'] = df
            
        elif filename == 'daily_travel_details.csv':
            examine_daily_travel_details(df)
            results['daily_travel'] = df
            
        elif filename == 'agent_shift_metrics.csv':
            examine_agent_metrics(df)
            results['agent_metrics'] = df
            
        elif filename == 'optimization_results_with_trips.csv':
            examine_optimization_results(df)
            results['optimization'] = df
    
    return results


def examine_lateness_incidents(df):
    """Examine the lateness incidents file in detail"""
    
    print(f"   Total incidents: {len(df)}")
    
    if len(df) == 0:
        print("   No lateness incidents found!")
        return
    
    # Check required columns
    required_cols = ['agent_name', 'is_late', 'lateness_minutes', 'severity']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"   ⚠️  Missing columns: {missing_cols}")
        print(f"   Available columns: {list(df.columns)}")
        return
    
    # Analyze the incidents
    late_incidents = df[df['is_late'] == True] if 'is_late' in df.columns else df
    
    print(f"   Late incidents: {len(late_incidents)}")
    print(f"   Agents affected: {df['agent_name'].nunique() if 'agent_name' in df.columns else 'Unknown'}")
    
    if len(late_incidents) > 0 and 'lateness_minutes' in df.columns:
        print(f"   Average lateness: {late_incidents['lateness_minutes'].mean():.1f} minutes")
        print(f"   Worst lateness: {late_incidents['lateness_minutes'].max():.1f} minutes")
        
        print(f"\n   📋 TOP 5 WORST INCIDENTS:")
        worst_cases = late_incidents.nlargest(5, 'lateness_minutes')
        for idx, incident in worst_cases.iterrows():
            agent = incident.get('agent_name', 'Unknown')
            lateness = incident.get('lateness_minutes', 0)
            from_prop = incident.get('current_property_name', 'Unknown')
            to_prop = incident.get('next_property_name', 'Unknown')
            date = incident.get('date', 'Unknown')
            
            print(f"     {agent}: {lateness:.1f} min late ({from_prop} → {to_prop}) on {date}")


def examine_agent_lateness_summary(df):
    """Examine the agent lateness summary"""
    
    print(f"   Total agents: {len(df)}")
    
    if len(df) == 0:
        print("   No agent data found!")
        return
    
    # Check for agents with issues
    if 'late_transitions' in df.columns:
        agents_with_late = len(df[df['late_transitions'] > 0])
        print(f"   Agents with late incidents: {agents_with_late} ({agents_with_late/len(df)*100:.1f}%)")
        
        if 'lateness_rate' in df.columns:
            avg_lateness_rate = df['lateness_rate'].mean() * 100
            print(f"   Average lateness rate: {avg_lateness_rate:.1f}%")
        
        print(f"\n   📋 TOP 5 MOST PROBLEMATIC AGENTS:")
        problematic = df.nlargest(5, 'late_transitions')
        for idx, agent in problematic.iterrows():
            name = agent.get('agent_name', 'Unknown')
            late_count = agent.get('late_transitions', 0)
            rate = agent.get('lateness_rate', 0) * 100
            print(f"     {name}: {late_count} late incidents ({rate:.1f}% rate)")


def examine_impossible_schedules(df):
    """Examine impossible schedules in detail"""
    
    print(f"   Total impossible schedules: {len(df)}")
    
    if len(df) == 0:
        print("   ✅ No impossible schedules found!")
        return
    
    print(f"   Agents affected: {df['agent_id'].nunique()}")
    
    if 'conflict_severity' in df.columns:
        print(f"   Average conflict: {df['conflict_severity'].mean():.1f} minutes")
        print(f"   Worst conflict: {df['conflict_severity'].max():.1f} minutes")
        
        print(f"\n   📋 WORST SCHEDULING CONFLICTS:")
        worst_conflicts = df.nlargest(5, 'conflict_severity')
        for idx, conflict in worst_conflicts.iterrows():
            agent = conflict.get('agent_id', 'Unknown')
            severity = conflict.get('conflict_severity', 0)
            date = conflict.get('date', 'Unknown')
            available = conflict.get('available_time', 0)
            required = conflict.get('required_time', 0)
            
            print(f"     Agent {agent}: {severity:.1f} min short on {date}")
            print(f"       Available: {available:.1f} min, Required: {required:.1f} min")


def examine_daily_travel_details(df):
    """Examine daily travel details"""
    
    print(f"   Total daily records: {len(df)}")
    
    if 'daily_travel_time' in df.columns:
        avg_daily_travel = df['daily_travel_time'].mean()
        print(f"   Average daily travel time: {avg_daily_travel:.1f} minutes")
        
        # Find agents with highest travel time
        if 'agent_id' in df.columns:
            high_travel_days = df.nlargest(5, 'daily_travel_time')
            print(f"\n   📋 HIGHEST TRAVEL TIME DAYS:")
            for idx, day in high_travel_days.iterrows():
                agent = day.get('agent_id', 'Unknown')
                travel_time = day.get('daily_travel_time', 0)
                date = day.get('date', 'Unknown')
                tours = day.get('total_tours', 0)
                
                print(f"     Agent {agent}: {travel_time:.1f} min on {date} ({tours} tours)")


def examine_agent_metrics(df):
    """Examine agent shift metrics"""
    
    print(f"   Total agents: {len(df)}")
    
    if 'avg_travel_time_per_shift_minutes' in df.columns:
        avg_travel_per_shift = df['avg_travel_time_per_shift_minutes'].mean()
        print(f"   System avg travel per shift: {avg_travel_per_shift:.1f} minutes")
        
        # Show distribution
        high_travel_agents = len(df[df['avg_travel_time_per_shift_minutes'] > avg_travel_per_shift])
        print(f"   Agents above average: {high_travel_agents} ({high_travel_agents/len(df)*100:.1f}%)")


def examine_optimization_results(df):
    """Examine optimization results"""
    
    print(f"   Total daily results: {len(df)}")
    
    if 'travel_savings_minutes' in df.columns:
        total_savings = df['travel_savings_minutes'].sum()
        avg_savings_pct = df['travel_savings_percentage'].mean()
        print(f"   Total potential savings: {total_savings:.1f} minutes")
        print(f"   Average savings rate: {avg_savings_pct:.1f}%")
    
    if 'trip_savings' in df.columns:
        total_trip_savings = df['trip_savings'].sum()
        print(f"   Total trip reduction: {total_trip_savings} trips")


def create_verification_summary(results):
    """Create a summary of findings to verify the lateness analysis"""
    
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    # Check if the impossible schedules claim is supported
    impossible_count = 0
    if 'impossible_schedules' in results:
        impossible_count = len(results['impossible_schedules'])
    
    lateness_count = 0
    if 'lateness_incidents' in results:
        lateness_df = results['lateness_incidents']
        if 'is_late' in lateness_df.columns:
            lateness_count = len(lateness_df[lateness_df['is_late'] == True])
        else:
            lateness_count = len(lateness_df)  # Assume all are late incidents
    
    agents_affected = 0
    if 'agent_summary' in results:
        agents_df = results['agent_summary']
        if 'late_transitions' in agents_df.columns:
            agents_affected = len(agents_df[agents_df['late_transitions'] > 0])
    
    print(f"🔍 FINDINGS VERIFICATION:")
    print(f"   Impossible schedules reported: 120")
    print(f"   Impossible schedules in data: {impossible_count}")
    print(f"   Match: {'✅' if impossible_count > 100 else '❌'}")
    
    print(f"\n   Agents affected reported: 12")
    print(f"   Agents with issues in data: {agents_affected}")
    print(f"   Match: {'✅' if agents_affected > 10 else '❌'}")
    
    print(f"\n   Late incidents found: {lateness_count}")
    
    # Overall assessment
    print(f"\n🎯 ASSESSMENT:")
    if impossible_count > 100 and agents_affected > 10:
        print(f"   ✅ The reported numbers appear CREDIBLE")
        print(f"   The analysis likely found real scheduling conflicts")
    elif impossible_count > 0:
        print(f"   ⚠️  Some issues found, but fewer than reported")
        print(f"   May need to review analysis parameters")
    else:
        print(f"   ❌ Numbers don't match - analysis may need review")
        print(f"   Check distance matrix and time calculations")
    
    return {
        'impossible_schedules_found': impossible_count,
        'lateness_incidents_found': lateness_count,
        'agents_affected_found': agents_affected,
        'analysis_credible': impossible_count > 50 and agents_affected > 5
    }


if __name__ == "__main__":
    print("Starting examination of saved analysis results...")
    results = examine_saved_analysis_files()
    
    if results:
        verification = create_verification_summary(results)
        print(f"\n💾 Results available in 'results' dictionary for further analysis")
    else:
        print(f"\n❌ No results to examine. Run the main analysis first.")