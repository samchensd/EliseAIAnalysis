import geopy.distance
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def geocode_properties(property_mapping):
    """Get coordinates for all properties"""
    
    geolocator = Nominatim(user_agent="eliseai_analysis")
    coords = {}
    
    for _, row in property_mapping.iterrows():
        address = f"{row['Address']}, {row['City']}, {row['State']}"
        try:
            location = geolocator.geocode(address)
            if location:
                coords[row['Property ID']] = (location.latitude, location.longitude)
            else:
                # Fallback to city center if address not found
                city_location = geolocator.geocode(f"{row['City']}, {row['State']}")
                coords[row['Property ID']] = (city_location.latitude, city_location.longitude)
        except:
            # Default coordinates for Columbus, OH
            coords[row['Property ID']] = (39.9612, -82.9988)
    
    return coords

def calculate_travel_time(coord1, coord2, mode='driving'):
    """Calculate travel time between two coordinates"""
    
    # Calculate distance in miles
    distance_miles = geopy.distance.distance(coord1, coord2).miles
    
    # Estimate travel time based on mode and distance
    if mode == 'driving':
        # Urban driving: 25 mph average, plus 2 min buffer per trip
        travel_time_minutes = (distance_miles / 25) * 60 + 2
    
    return max(travel_time_minutes, 5)  # Minimum 5 minutes for any trip

def create_distance_matrix(property_coords):
    """Create distance matrix between all properties"""
    
    property_ids = list(property_coords.keys())
    n = len(property_ids)
    
    distance_matrix = pd.DataFrame(
        index=property_ids,
        columns=property_ids,
        dtype=float
    )
    
    for i, prop1 in enumerate(property_ids):
        for j, prop2 in enumerate(property_ids):
            if i == j:
                distance_matrix.loc[prop1, prop2] = 0
            else:
                travel_time = calculate_travel_time(
                    property_coords[prop1],
                    property_coords[prop2]
                )
                distance_matrix.loc[prop1, prop2] = travel_time
    
    return distance_matrix

def analyze_agent_travel(event_log, distance_matrix):
    """Analyze travel patterns for all agents"""
    results = []
    total_system_travel_time = 0

    # Group by agent and date
    for (agent_id, date), group in event_log.groupby(['Leasing Agent ID', 'Date']):

        #Sort tours by start time
        daily_tours = group.sort_values('Start Time').reset_index(drop=True)
        daily_travel_time = 0
        travel_segments = []

        current_physical_location = None

        for i in range(len(daily_tours)):
            tour  = daily_tours.iloc[i]

            if tour['Tour Type'] == 'ESCORTED':
                #Agent needs to be physically present for escorted tours

                if current_physical_location is not None and current_physical_location != tour['Property ID']:
                    # Agent needs to travel from last escorted location to this one
                    travel_time = distance_matrix.loc[current_physical_location, tour['Property ID']]
                    daily_travel_time += travel_time
                    total_system_travel_time += travel_time

                    travel_segments.append({
                        'from_property': current_physical_location,
                        'to_property': tour['Property ID'],
                        'travel_time': travel_time,
                        'tour_causing_travel': i,  # Which tour required this travel
                        'prev_end': daily_tours.iloc[i-1]['End Time'] if i > 0 else None,
                        'next_start': tour['Start Time'],
                        'buffer_time': (tour['Start Time'] - daily_tours.iloc[i-1]['End Time']).total_seconds() / 60 if i > 0 else None
                    })

                # Update agent's physical location
                current_physical_location = tour['Property ID']
            
        results.append({
        'agent_id': agent_id,
        'date': date,
        'total_tours': len(daily_tours),
        'escorted_tours': len(daily_tours[daily_tours['Tour Type'] == 'ESCORTED']),
        'virtual_tours': len(daily_tours[daily_tours['Tour Type'] == 'VIRTUAL_TOUR']),
        'actual_travels_required': len(travel_segments),
        'daily_travel_time': daily_travel_time,
        'travel_segments': travel_segments,
        'final_physical_location': current_physical_location
        })
    return {
        'detailed_results': pd.DataFrame(results),
        'total_estimated_travel_time': total_system_travel_time,
        'summary_stats': {
            'total_minutes': total_system_travel_time,
            'total_hours': total_system_travel_time / 60,
            'total_actual_travels': sum(len(r['travel_segments']) for r in results)
        }
    }

def calculate_agent_shift_metrics(travel_results, agent_mapping):
    """Calculate average travel time per agent per shift and other agent-level metrics"""
    
    detailed_results = travel_results['detailed_results']
    
    # Calculate per-agent metrics
    agent_metrics = []
    
    for agent_id in detailed_results['agent_id'].unique():
        agent_data = detailed_results[detailed_results['agent_id'] == agent_id]
        
        # Get agent name
        agent_name = "Unknown"
        if agent_id in agent_mapping['Agent ID'].values:
            agent_name = agent_mapping[agent_mapping['Agent ID'] == agent_id]['Agent Name'].iloc[0]
        
        # Calculate metrics for this agent
        total_shifts = len(agent_data)
        total_travel_time = agent_data['daily_travel_time'].sum()
        avg_travel_per_shift = total_travel_time / total_shifts if total_shifts > 0 else 0
        
        # Calculate other useful metrics
        total_tours = agent_data['total_tours'].sum()
        total_escorted_tours = agent_data['escorted_tours'].sum()
        total_virtual_tours = agent_data['virtual_tours'].sum()
        total_travels = agent_data['actual_travels_required'].sum()
        
        avg_tours_per_shift = total_tours / total_shifts if total_shifts > 0 else 0
        avg_escorted_per_shift = total_escorted_tours / total_shifts if total_shifts > 0 else 0
        avg_travels_per_shift = total_travels / total_shifts if total_shifts > 0 else 0
        
        # Travel efficiency metrics
        travel_time_per_tour = total_travel_time / total_tours if total_tours > 0 else 0
        travel_time_per_escorted_tour = total_travel_time / total_escorted_tours if total_escorted_tours > 0 else 0
        
        agent_metrics.append({
            'agent_id': agent_id,
            'agent_name': agent_name,
            'total_shifts': total_shifts,
            'total_travel_time_minutes': total_travel_time,
            'avg_travel_time_per_shift_minutes': avg_travel_per_shift,
            'total_tours': total_tours,
            'total_escorted_tours': total_escorted_tours,
            'total_virtual_tours': total_virtual_tours,
            'total_actual_travels': total_travels,
            'avg_tours_per_shift': avg_tours_per_shift,
            'avg_escorted_tours_per_shift': avg_escorted_per_shift,
            'avg_travels_per_shift': avg_travels_per_shift,
            'travel_time_per_tour_minutes': travel_time_per_tour,
            'travel_time_per_escorted_tour_minutes': travel_time_per_escorted_tour,
            'travel_efficiency_score': (total_tours / (total_travel_time + 1)) * 100  # Tours per minute * 100
        })
    
    agent_metrics_df = pd.DataFrame(agent_metrics)
    
    # Calculate system-wide averages
    system_metrics = {
        'total_agents': len(agent_metrics_df),
        'total_shifts': agent_metrics_df['total_shifts'].sum(),
        'avg_travel_time_per_shift_system': agent_metrics_df['avg_travel_time_per_shift_minutes'].mean(),
        'median_travel_time_per_shift': agent_metrics_df['avg_travel_time_per_shift_minutes'].median(),
        'max_travel_time_per_shift': agent_metrics_df['avg_travel_time_per_shift_minutes'].max(),
        'min_travel_time_per_shift': agent_metrics_df['avg_travel_time_per_shift_minutes'].min(),
        'std_travel_time_per_shift': agent_metrics_df['avg_travel_time_per_shift_minutes'].std(),
        'avg_tours_per_shift_system': agent_metrics_df['avg_tours_per_shift'].mean(),
        'avg_travels_per_shift_system': agent_metrics_df['avg_travels_per_shift'].mean(),
        'system_travel_efficiency': agent_metrics_df['travel_efficiency_score'].mean()
    }
    
    # Identify high and low performers
    top_efficient_agents = agent_metrics_df.nlargest(3, 'travel_efficiency_score')[['agent_name', 'travel_efficiency_score', 'avg_travel_time_per_shift_minutes']].to_dict('records')
    least_efficient_agents = agent_metrics_df.nsmallest(3, 'travel_efficiency_score')[['agent_name', 'travel_efficiency_score', 'avg_travel_time_per_shift_minutes']].to_dict('records')
    
    return {
        'agent_metrics': agent_metrics_df,
        'system_metrics': system_metrics,
        'top_efficient_agents': top_efficient_agents,
        'least_efficient_agents': least_efficient_agents
    }

def print_agent_shift_analysis(shift_metrics):
    """Print detailed analysis of agent shift metrics"""
    
    print(f"\n🎯 AGENT-LEVEL SHIFT ANALYSIS")
    print("=" * 60)
    
    system_metrics = shift_metrics['system_metrics']
    
    print(f"📊 SYSTEM-WIDE METRICS:")
    print(f"   Total Agents: {system_metrics['total_agents']}")
    print(f"   Total Shifts: {system_metrics['total_shifts']}")
    print(f"   Average Travel Time per Shift: {system_metrics['avg_travel_time_per_shift_system']:.1f} min")
    print(f"   Median Travel Time per Shift: {system_metrics['median_travel_time_per_shift']:.1f} min")
    print(f"   Travel Time Range: {system_metrics['min_travel_time_per_shift']:.1f} - {system_metrics['max_travel_time_per_shift']:.1f} min")
    print(f"   Standard Deviation: {system_metrics['std_travel_time_per_shift']:.1f} min")
    print(f"   Average Tours per Shift: {system_metrics['avg_tours_per_shift_system']:.1f}")
    print(f"   Average Travels per Shift: {system_metrics['avg_travels_per_shift_system']:.1f}")
    
    print(f"\n🏆 TOP PERFORMING AGENTS (Most Efficient):")
    for i, agent in enumerate(shift_metrics['top_efficient_agents'], 1):
        print(f"   {i}. {agent['agent_name']}: {agent['avg_travel_time_per_shift_minutes']:.1f} min/shift (Efficiency: {agent['travel_efficiency_score']:.1f})")
    
    print(f"\n⚠️  LEAST EFFICIENT AGENTS (Most Travel Time):")
    for i, agent in enumerate(shift_metrics['least_efficient_agents'], 1):
        print(f"   {i}. {agent['agent_name']}: {agent['avg_travel_time_per_shift_minutes']:.1f} min/shift (Efficiency: {agent['travel_efficiency_score']:.1f})")
    
    print(f"\n📈 OPTIMIZATION POTENTIAL:")
    agent_metrics = shift_metrics['agent_metrics']
    high_travel_agents = agent_metrics[agent_metrics['avg_travel_time_per_shift_minutes'] > system_metrics['avg_travel_time_per_shift_system']]
    potential_savings = (high_travel_agents['avg_travel_time_per_shift_minutes'] - system_metrics['avg_travel_time_per_shift_system']).sum()
    
    print(f"   Agents above average travel time: {len(high_travel_agents)}")
    print(f"   Potential daily savings if optimized to average: {potential_savings:.1f} min")
    print(f"   Potential weekly savings (5 days): {potential_savings * 5:.1f} min ({(potential_savings * 5)/60:.1f} hours)")
    
    return shift_metrics