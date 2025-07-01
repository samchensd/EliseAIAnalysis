import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict


def analyze_agent_lateness_risk(event_log, distance_matrix, agent_mapping, property_mapping):
    """
    Analyze how many agents are likely to be late to their tours due to 
    insufficient travel time between back-to-back appointments.
    
    Returns detailed analysis of lateness risks and problematic transitions.
    """
    print("\n⏰ ANALYZING AGENT LATENESS RISK")
    print("=" * 60)
    print("   Identifying tours where agents may arrive late due to travel time...")
    
    lateness_incidents = []
    agent_lateness_summary = []
    daily_lateness_stats = []
    
    # Analyze each agent's schedule
    for agent_id in event_log['Leasing Agent ID'].unique():
        agent_events = event_log[event_log['Leasing Agent ID'] == agent_id].copy()
        agent_events = agent_events.sort_values('Start Time').reset_index(drop=True)
        
        agent_name = "Unknown"
        if agent_id in agent_mapping['Agent ID'].values:
            agent_name = agent_mapping[agent_mapping['Agent ID'] == agent_id]['Agent Name'].iloc[0]
        
        total_transitions = 0
        late_transitions = 0
        risky_transitions = 0  # Within 5 minutes of being late
        total_lateness_minutes = 0
        max_lateness = 0
        
        # Analyze consecutive tours
        for i in range(len(agent_events) - 1):
            current_tour = agent_events.iloc[i]
            next_tour = agent_events.iloc[i + 1]
            
            # Only analyze escorted tours (virtual tours don't require travel)
            if current_tour['Tour Type'] == 'ESCORTED' and next_tour['Tour Type'] == 'ESCORTED':
                # Check if tours are on the same day
                if current_tour['Date'] == next_tour['Date']:
                    current_property = current_tour['Property ID']
                    next_property = next_tour['Property ID']
                    
                    # Only analyze if properties are different (travel required)
                    if current_property != next_property:
                        total_transitions += 1
                        
                        # Calculate available time between tours
                        available_time = (next_tour['Start Time'] - current_tour['End Time']).total_seconds() / 60
                        
                        # Get required travel time
                        required_travel_time = distance_matrix.loc[current_property, next_property]
                        
                        # Calculate lateness (negative means early, positive means late)
                        lateness_minutes = required_travel_time - available_time
                        
                        # Categorize the transition
                        is_late = lateness_minutes > 0
                        is_risky = lateness_minutes > -5 and lateness_minutes <= 0  # Within 5 min buffer
                        
                        if is_late:
                            late_transitions += 1
                            total_lateness_minutes += lateness_minutes
                            max_lateness = max(max_lateness, lateness_minutes)
                        elif is_risky:
                            risky_transitions += 1
                        
                        # Get property names for reporting
                        current_prop_name = property_mapping[
                            property_mapping['Property ID'] == current_property
                        ]['Property Name'].iloc[0] if current_property in property_mapping['Property ID'].values else "Unknown"
                        
                        next_prop_name = property_mapping[
                            property_mapping['Property ID'] == next_property
                        ]['Property Name'].iloc[0] if next_property in property_mapping['Property ID'].values else "Unknown"
                        
                        # Record the incident
                        lateness_incidents.append({
                            'agent_id': agent_id,
                            'agent_name': agent_name,
                            'date': current_tour['Date'],
                            'current_tour_end': current_tour['End Time'],
                            'next_tour_start': next_tour['Start Time'],
                            'current_property': current_property,
                            'next_property': next_property,
                            'current_property_name': current_prop_name,
                            'next_property_name': next_prop_name,
                            'available_time_minutes': available_time,
                            'required_travel_time_minutes': required_travel_time,
                            'lateness_minutes': lateness_minutes,
                            'is_late': is_late,
                            'is_risky': is_risky,
                            'severity': 'LATE' if is_late else ('RISKY' if is_risky else 'OK')
                        })
        
        # Calculate agent-level statistics
        lateness_rate = late_transitions / total_transitions if total_transitions > 0 else 0
        risk_rate = (late_transitions + risky_transitions) / total_transitions if total_transitions > 0 else 0
        avg_lateness = total_lateness_minutes / late_transitions if late_transitions > 0 else 0
        
        agent_lateness_summary.append({
            'agent_id': agent_id,
            'agent_name': agent_name,
            'total_travel_transitions': total_transitions,
            'late_transitions': late_transitions,
            'risky_transitions': risky_transitions,
            'on_time_transitions': total_transitions - late_transitions - risky_transitions,
            'lateness_rate': lateness_rate,
            'risk_rate': risk_rate,
            'total_lateness_minutes': total_lateness_minutes,
            'avg_lateness_per_incident': avg_lateness,
            'max_lateness_minutes': max_lateness,
            'has_lateness_issues': late_transitions > 0 or risky_transitions > 0
        })
    
    # Analyze by date
    incidents_df = pd.DataFrame(lateness_incidents)
    if len(incidents_df) > 0:
        daily_stats = incidents_df.groupby('date').agg({
            'is_late': 'sum',
            'is_risky': 'sum',
            'lateness_minutes': lambda x: x[x > 0].sum(),  # Only sum positive lateness
            'agent_id': 'nunique'
        }).rename(columns={
            'is_late': 'late_incidents',
            'is_risky': 'risky_incidents', 
            'lateness_minutes': 'total_daily_lateness',
            'agent_id': 'agents_with_issues'
        }).reset_index()
        
        daily_stats['total_incidents'] = daily_stats['late_incidents'] + daily_stats['risky_incidents']
    else:
        daily_stats = pd.DataFrame()
    
    # Calculate system-wide statistics
    agents_df = pd.DataFrame(agent_lateness_summary)
    total_agents = len(agents_df)
    agents_with_late_incidents = len(agents_df[agents_df['late_transitions'] > 0])
    agents_with_any_issues = len(agents_df[agents_df['has_lateness_issues']])
    total_late_incidents = agents_df['late_transitions'].sum()
    total_risky_incidents = agents_df['risky_transitions'].sum()
    total_transitions = agents_df['total_travel_transitions'].sum()
    system_lateness_rate = total_late_incidents / total_transitions if total_transitions > 0 else 0
    system_risk_rate = (total_late_incidents + total_risky_incidents) / total_transitions if total_transitions > 0 else 0
    
    print(f"✅ Lateness analysis complete!")
    print(f"\n📊 SYSTEM-WIDE LATENESS STATISTICS:")
    print(f"   Total Agents Analyzed: {total_agents}")
    print(f"   Agents with Late Incidents: {agents_with_late_incidents} ({agents_with_late_incidents/total_agents*100:.1f}%)")
    print(f"   Agents with Any Timing Issues: {agents_with_any_issues} ({agents_with_any_issues/total_agents*100:.1f}%)")
    print(f"   Total Travel Transitions: {total_transitions:,}")
    print(f"   Late Transitions: {total_late_incidents:,} ({system_lateness_rate*100:.1f}%)")
    print(f"   Risky Transitions: {total_risky_incidents:,} ({(total_risky_incidents/total_transitions*100) if total_transitions > 0 else 0:.1f}%)")
    print(f"   Combined Risk Rate: {system_risk_rate*100:.1f}%")
    print(f"   Average Lateness per Incident: {agents_df['avg_lateness_per_incident'].mean():.1f} minutes")
    
    if len(incidents_df) > 0:
        worst_incidents = incidents_df[incidents_df['is_late']].nlargest(5, 'lateness_minutes')
        print(f"\n⚠️  TOP 5 WORST LATENESS INCIDENTS:")
        for _, incident in worst_incidents.iterrows():
            print(f"   {incident['agent_name']}: {incident['lateness_minutes']:.1f} min late")
            print(f"      {incident['current_property_name']} → {incident['next_property_name']} on {incident['date']}")
    
    # Identify most problematic agents
    problematic_agents = agents_df[agents_df['has_lateness_issues']].nlargest(5, 'late_transitions')
    print(f"\n👤 TOP 5 AGENTS WITH MOST LATENESS ISSUES:")
    for _, agent in problematic_agents.iterrows():
        print(f"   {agent['agent_name']}: {agent['late_transitions']} late, {agent['risky_transitions']} risky")
        print(f"      Lateness rate: {agent['lateness_rate']*100:.1f}%, Avg late by: {agent['avg_lateness_per_incident']:.1f} min")
    
    return {
        'incidents_df': incidents_df,
        'agent_summary_df': agents_df,
        'daily_stats_df': daily_stats,
        'system_stats': {
            'total_agents': total_agents,
            'agents_with_late_incidents': agents_with_late_incidents,
            'agents_with_any_issues': agents_with_any_issues,
            'total_late_incidents': total_late_incidents,
            'total_risky_incidents': total_risky_incidents,
            'total_transitions': total_transitions,
            'system_lateness_rate': system_lateness_rate,
            'system_risk_rate': system_risk_rate,
            'avg_lateness_per_incident': agents_df['avg_lateness_per_incident'].mean()
        }
    }


def analyze_schedule_conflicts(event_log, distance_matrix, buffer_minutes=5):
    """
    Identify scheduling conflicts where tours overlap when accounting for travel time.
    This is different from lateness - these are impossible schedules.
    """
    print(f"\n🚨 ANALYZING IMPOSSIBLE SCHEDULES (with {buffer_minutes} min buffer)")
    print("=" * 60)
    
    conflicts = []
    
    for agent_id in event_log['Leasing Agent ID'].unique():
        agent_events = event_log[event_log['Leasing Agent ID'] == agent_id].copy()
        agent_events = agent_events.sort_values('Start Time').reset_index(drop=True)
        
        for i in range(len(agent_events) - 1):
            current_tour = agent_events.iloc[i]
            next_tour = agent_events.iloc[i + 1]
            
            # Only check escorted tours on same day
            if (current_tour['Tour Type'] == 'ESCORTED' and 
                next_tour['Tour Type'] == 'ESCORTED' and
                current_tour['Date'] == next_tour['Date']):
                
                current_property = current_tour['Property ID']
                next_property = next_tour['Property ID']
                
                if current_property != next_property:
                    # Calculate if schedule is physically impossible
                    available_time = (next_tour['Start Time'] - current_tour['End Time']).total_seconds() / 60
                    required_time = distance_matrix.loc[current_property, next_property] + buffer_minutes
                    
                    if available_time < required_time:
                        conflicts.append({
                            'agent_id': agent_id,
                            'date': current_tour['Date'],
                            'conflict_severity': required_time - available_time,
                            'available_time': available_time,
                            'required_time': required_time,
                            'current_tour_end': current_tour['End Time'],
                            'next_tour_start': next_tour['Start Time']
                        })
    
    conflicts_df = pd.DataFrame(conflicts)
    
    if len(conflicts_df) > 0:
        print(f"   Impossible Schedules Found: {len(conflicts_df)}")
        print(f"   Agents Affected: {conflicts_df['agent_id'].nunique()}")
        print(f"   Average Conflict Severity: {conflicts_df['conflict_severity'].mean():.1f} minutes")
        print(f"   Worst Conflict: {conflicts_df['conflict_severity'].max():.1f} minutes short")
    else:
        print(f"   No impossible schedules found!")
    
    return conflicts_df


def create_lateness_visualizations(lateness_results):
    """
    Create visualizations for the lateness analysis.
    Returns matplotlib figure objects that can be saved or displayed.
    """
    incidents_df = lateness_results['incidents_df']
    agents_df = lateness_results['agent_summary_df']
    system_stats = lateness_results['system_stats']
    
    # Create subplot figure
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Agent Lateness Risk Analysis', fontsize=16, fontweight='bold')
    
    # 1. Overall lateness rate pie chart
    labels = ['On Time', 'Risky (0-5 min)', 'Late (>5 min)']
    sizes = [
        system_stats['total_transitions'] - system_stats['total_late_incidents'] - system_stats['total_risky_incidents'],
        system_stats['total_risky_incidents'],
        system_stats['total_late_incidents']
    ]
    colors = ['green', 'orange', 'red']
    axes[0,0].pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    axes[0,0].set_title('System-Wide Lateness Risk')
    
    # 2. Agent lateness distribution
    if len(agents_df) > 0:
        lateness_rates = agents_df['lateness_rate'] * 100
        axes[0,1].hist(lateness_rates, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
        axes[0,1].set_xlabel('Lateness Rate (%)')
        axes[0,1].set_ylabel('Number of Agents')
        axes[0,1].set_title('Distribution of Agent Lateness Rates')
        axes[0,1].axvline(lateness_rates.mean(), color='red', linestyle='--', label=f'Mean: {lateness_rates.mean():.1f}%')
        axes[0,1].legend()
    
    # 3. Top problematic agents
    if len(agents_df) > 0:
        top_problem_agents = agents_df.nlargest(10, 'late_transitions')
        axes[0,2].barh(range(len(top_problem_agents)), top_problem_agents['late_transitions'], color='coral')
        axes[0,2].set_yticks(range(len(top_problem_agents)))
        axes[0,2].set_yticklabels([name[:15] + '...' if len(name) > 15 else name 
                                  for name in top_problem_agents['agent_name']], fontsize=8)
        axes[0,2].set_xlabel('Late Incidents')
        axes[0,2].set_title('Top 10 Agents with Most Late Incidents')
    
    # 4. Daily lateness trends
    if len(lateness_results['daily_stats_df']) > 0:
        daily_stats = lateness_results['daily_stats_df']
        dates = pd.to_datetime(daily_stats['date'])
        axes[1,0].plot(dates, daily_stats['late_incidents'], marker='o', color='red', label='Late')
        axes[1,0].plot(dates, daily_stats['risky_incidents'], marker='s', color='orange', label='Risky')
        axes[1,0].set_xlabel('Date')
        axes[1,0].set_ylabel('Number of Incidents')
        axes[1,0].set_title('Daily Lateness Incidents Over Time')
        axes[1,0].legend()
        axes[1,0].tick_params(axis='x', rotation=45)
    
    # 5. Lateness severity distribution
    if len(incidents_df) > 0:
        late_incidents = incidents_df[incidents_df['is_late']]
        if len(late_incidents) > 0:
            axes[1,1].hist(late_incidents['lateness_minutes'], bins=15, color='lightcoral', 
                          edgecolor='black', alpha=0.7)
            axes[1,1].set_xlabel('Minutes Late')
            axes[1,1].set_ylabel('Number of Incidents')
            axes[1,1].set_title('Distribution of Lateness Severity')
            axes[1,1].axvline(late_incidents['lateness_minutes'].mean(), color='darkred', 
                             linestyle='--', label=f'Mean: {late_incidents["lateness_minutes"].mean():.1f} min')
            axes[1,1].legend()
    
    # 6. Summary statistics text
    summary_text = f"""
System Statistics:
• Total Agents: {system_stats['total_agents']}
• Agents with Issues: {system_stats['agents_with_any_issues']} ({system_stats['agents_with_any_issues']/system_stats['total_agents']*100:.1f}%)
• Late Incidents: {system_stats['total_late_incidents']:,}
• Lateness Rate: {system_stats['system_lateness_rate']*100:.1f}%
• Risk Rate: {system_stats['system_risk_rate']*100:.1f}%
• Avg Late Duration: {system_stats['avg_lateness_per_incident']:.1f} min
    """
    axes[1,2].text(0.1, 0.5, summary_text, fontsize=10, verticalalignment='center', 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
    axes[1,2].set_xlim(0, 1)
    axes[1,2].set_ylim(0, 1)
    axes[1,2].axis('off')
    axes[1,2].set_title('Summary Statistics')
    
    plt.tight_layout()
    return fig


def export_lateness_analysis(lateness_results, filename_prefix='lateness_analysis'):
    """Export lateness analysis results to CSV files."""
    
    # Export detailed incidents
    lateness_results['incidents_df'].to_csv(f'{filename_prefix}_incidents.csv', index=False)
    
    # Export agent summary
    lateness_results['agent_summary_df'].to_csv(f'{filename_prefix}_agent_summary.csv', index=False)
    
    # Export daily statistics
    if len(lateness_results['daily_stats_df']) > 0:
        lateness_results['daily_stats_df'].to_csv(f'{filename_prefix}_daily_stats.csv', index=False)
    
    # Create summary report
    system_stats = lateness_results['system_stats']
    
    summary_report = f"""
AGENT LATENESS RISK ANALYSIS SUMMARY
===================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY:
-----------------
Current State Problem: {system_stats['agents_with_any_issues']} out of {system_stats['total_agents']} agents ({system_stats['agents_with_any_issues']/system_stats['total_agents']*100:.1f}%) 
have scheduling issues that cause lateness or risky timing.

KEY METRICS:
-----------
• Total Travel Transitions: {system_stats['total_transitions']:,}
• Late Arrivals: {system_stats['total_late_incidents']:,} ({system_stats['system_lateness_rate']*100:.1f}%)
• Risky Timing: {system_stats['total_risky_incidents']:,}
• Combined Risk Rate: {system_stats['system_risk_rate']*100:.1f}%
• Average Lateness: {system_stats['avg_lateness_per_incident']:.1f} minutes per incident

BUSINESS IMPACT:
---------------
• Agent Stress: {system_stats['agents_with_late_incidents']} agents regularly arrive late to appointments
• Customer Experience: Late arrivals impact {system_stats['system_lateness_rate']*100:.1f}% of property transitions
• Operational Efficiency: {system_stats['total_late_incidents']:,} incidents requiring schedule adjustments or apologies

AGENT-LEVEL CALENDAR SOLUTION:
------------------------------
✅ Eliminates travel time conflicts through intelligent scheduling
✅ Reduces agent stress and improves punctuality
✅ Enhances customer experience with reliable arrival times
✅ Enables proactive schedule optimization vs reactive problem-solving

RECOMMENDED ACTIONS:
-------------------
1. Implement agent-level calendar system to prevent scheduling conflicts
2. Add travel time buffers to current scheduling logic
3. Prioritize optimization for the {system_stats['agents_with_late_incidents']} agents with frequent lateness
4. Monitor customer satisfaction improvements post-implementation
    """
    
    with open(f'{filename_prefix}_summary_report.txt', 'w') as f:
        f.write(summary_report)
    
    print(f"✅ Lateness analysis exported to {filename_prefix}_*.csv and summary report")
    
    return True