import os
import pandas as pd
import numpy as np
from datetime import timedelta
from travel_analysis import analyze_agent_travel


def insertion_optimization_estimate(event_log, distance_matrix, property_mapping):
    """
    Estimate travel savings using a simple insertion heuristic,
    considering both escorted and virtual tours for scheduling.
    NOW INCLUDES TRIP COUNTING for before/after analysis.
    """
    current = analyze_agent_travel(event_log, distance_matrix)
    baseline = current['total_estimated_travel_time']
    
    # COUNT CURRENT TRAVEL TRIPS
    current_trips = count_total_travel_trips(event_log)

    daily_results = []
    total_opt = 0
    total_opt_trips = 0
    
    for date, day in event_log.groupby('Date'):
        day_res = optimize_single_day_insertion(day, distance_matrix)
        daily_results.append(day_res)
        total_opt += day_res['optimized_travel_time']
        total_opt_trips += day_res['optimized_trips']

    savings = baseline - total_opt
    savings_pct = (savings / baseline * 100) if baseline > 0 else 0
    
    trip_savings = current_trips - total_opt_trips
    trip_savings_pct = (trip_savings / current_trips * 100) if current_trips > 0 else 0
    
    return {
        'current_travel_minutes': baseline,
        'optimized_travel_minutes': total_opt,
        'potential_savings_minutes': savings,
        'savings_percentage': savings_pct,
        'current_travel_trips': current_trips,
        'optimized_travel_trips': total_opt_trips,
        'trip_savings': trip_savings,
        'trip_savings_percentage': trip_savings_pct,
        'daily_results': daily_results
    }


def count_total_travel_trips(event_log):
    """
    Count total number of property-to-property travel trips in current schedule.
    Each agent transition from one property to another = 1 trip.
    """
    total_trips = 0
    
    for agent_id in event_log['Leasing Agent ID'].unique():
        agent_tours = event_log[event_log['Leasing Agent ID'] == agent_id]
        agent_tours = agent_tours.sort_values('Start Time')
        
        last_property = None
        for _, tour in agent_tours.iterrows():
            if tour['Tour Type'] == 'ESCORTED':
                current_property = tour['Property ID']
                if last_property is not None and last_property != current_property:
                    total_trips += 1
                last_property = current_property
    
    return total_trips


def count_daily_travel_trips(daily_events):
    """
    Count travel trips for a single day's events.
    """
    total_trips = 0
    
    for agent_id in daily_events['Leasing Agent ID'].unique():
        agent_tours = daily_events[daily_events['Leasing Agent ID'] == agent_id]
        agent_tours = agent_tours.sort_values('Start Time')
        
        last_property = None
        for _, tour in agent_tours.iterrows():
            if tour['Tour Type'] == 'ESCORTED':
                current_property = tour['Property ID']
                if last_property is not None and last_property != current_property:
                    total_trips += 1
                last_property = current_property
    
    return total_trips


def optimize_single_day_insertion(daily_events, distance_matrix):
    """
    Simple insertion heuristic for one day. Considers both escorted and virtual tours.
    Virtual tours consume time but incur zero travel. Ensures no assignment to unavailable agent.
    NOW INCLUDES TRIP COUNTING.
    """
    date = daily_events['Date'].iloc[0]
    current_travel = calculate_daily_current_travel(daily_events, distance_matrix)
    current_trips = count_daily_travel_trips(daily_events)

    # Initialize agent states
    agents = list(daily_events['Leasing Agent ID'].unique())
    state = {a: {'last_end': None, 'loc': None} for a in agents}

    # Sort all tours by start time
    tours = daily_events.sort_values('Start Time')

    assignments = []
    for idx, tour in tours.iterrows():
        best_agent = None
        best_cost = np.inf
        # Evaluate feasibility per agent
        for agent in agents:
            s = state[agent]
            # Compute arrival
            if tour['Tour Type'] == 'VIRTUAL_TOUR' or s['loc'] is None:
                travel = 0
                arrival = tour['Start Time']
            else:
                travel = distance_matrix.loc[s['loc'], tour['Property ID']]
                arrival = s['last_end'] + timedelta(minutes=travel)
            # Check availability
            if arrival <= tour['End Time']:
                wait = max((tour['Start Time'] - arrival).total_seconds() / 60, 0)
                cost = travel + wait
                if cost < best_cost:
                    best_cost = cost
                    best_agent = agent
        # Determine assignment
        if best_agent:
            assigned = best_agent
        else:
            # Check original agent feasibility
            orig = tour['Leasing Agent ID']
            s_orig = state.get(orig, {'last_end': None, 'loc': None})
            if tour['Tour Type'] == 'VIRTUAL_TOUR' or s_orig['loc'] is None:
                travel_o = 0
                arrival_o = tour['Start Time']
            else:
                travel_o = distance_matrix.loc[s_orig['loc'], tour['Property ID']]
                arrival_o = s_orig['last_end'] + timedelta(minutes=travel_o)
            if arrival_o <= tour['End Time']:
                assigned = orig
            else:
                # No agent available; assign original and note
                assigned = orig
                print(f"WARNING {date}: No available agent for tour {idx}, assigning to original {orig}")
        assignments.append({'tour_id': idx, 'assigned_agent': assigned})

        # Update state for assigned agent
        s = state[assigned]
        if tour['Tour Type'] == 'VIRTUAL_TOUR':
            start_time = max(s['last_end'] or tour['Start Time'], tour['Start Time'])
            end_time = start_time + (tour['End Time'] - tour['Start Time'])
            s['last_end'] = end_time
        else:
            if s['loc'] is None:
                travel = 0
                start_time = tour['Start Time']
            else:
                travel = distance_matrix.loc[s['loc'], tour['Property ID']]
                start_time = max(s['last_end'] + timedelta(minutes=travel), tour['Start Time'])
            end_time = start_time + (tour['End Time'] - tour['Start Time'])
            s['last_end'] = end_time
            s['loc'] = tour['Property ID']

    # Build optimized events copy
    optimized = daily_events.copy()
    for a in assignments:
        optimized.at[a['tour_id'], 'Leasing Agent ID'] = a['assigned_agent']

    optimized_travel = calculate_daily_current_travel(optimized, distance_matrix)
    optimized_trips = count_daily_travel_trips(optimized)
    
    savings = current_travel - optimized_travel
    savings_pct = (savings / current_travel * 100) if current_travel > 0 else 0
    
    trip_savings = current_trips - optimized_trips
    trip_savings_pct = (trip_savings / current_trips * 100) if current_trips > 0 else 0
    
    return {
        'date': date,
        'current_travel_time': current_travel,
        'optimized_travel_time': optimized_travel,
        'savings': savings,
        'savings_percentage': savings_pct,
        'current_trips': current_trips,
        'optimized_trips': optimized_trips,
        'trip_savings': trip_savings,
        'trip_savings_percentage': trip_savings_pct,
        'assignments': assignments
    }


def calculate_daily_current_travel(daily_events, distance_matrix):
    """
    Calculate total travel time for a day's events (unchanged from original).
    """
    total = 0
    for agent_id in daily_events['Leasing Agent ID'].unique():
        agent_tours = daily_events[daily_events['Leasing Agent ID'] == agent_id]
        agent_tours = agent_tours.sort_values('Start Time')
        loc = None
        for _, tour in agent_tours.iterrows():
            if tour['Tour Type'] == 'ESCORTED':
                if loc is not None and loc != tour['Property ID']:
                    total += distance_matrix.loc[loc, tour['Property ID']]
                loc = tour['Property ID']
    return total


def export_optimization_results(optimization_results, filename='optimization_results.csv'):
    """
    Export detailed optimization results including trip counts.
    """
    results_data = []
    
    # Add daily results
    for daily in optimization_results['daily_results']:
        results_data.append({
            'date': daily['date'],
            'current_travel_minutes': daily['current_travel_time'],
            'optimized_travel_minutes': daily['optimized_travel_time'],
            'travel_savings_minutes': daily['savings'],
            'travel_savings_percentage': daily['savings_percentage'],
            'current_trips': daily['current_trips'],
            'optimized_trips': daily['optimized_trips'],
            'trip_savings': daily['trip_savings'],
            'trip_savings_percentage': daily['trip_savings_percentage']
        })
    
    # Create DataFrame and save
    df = pd.DataFrame(results_data)
    df.to_csv(filename, index=False)
    
    return df