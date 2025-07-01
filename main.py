#!/usr/bin/env python3
"""
EliseAI Agent-Level Calendar Analysis - COMPLETE ANALYSIS WITH SPECIALIZATION METRICS
Full dataset analysis with insertion heuristic optimization estimation
Enhanced with agent-level shift metrics, travel trip analysis, and agent specialization analysis
"""

import sys
import os
from datetime import datetime
import pandas as pd
pd.set_option('display.float_format', '{:,.2f}'.format)

# Add src directory to path
sys.path.append('src')

try:
    from data_loading import load_excel_data, setup_database
    from travel_analysis import (
        geocode_properties,
        create_distance_matrix,
        analyze_agent_travel,
        calculate_agent_shift_metrics,
        print_agent_shift_analysis
    )
    from optimization import (
        insertion_optimization_estimate as optimization_estimate,
        export_optimization_results
    )
    from agent_specialization import (
        calculate_agent_specialization_metrics,
        analyze_property_coverage,
        compare_specialization_before_after,
        export_specialization_analysis,
        create_specialization_summary_report
    )
    from lateness_analysis import (
        analyze_agent_lateness_risk,
        analyze_schedule_conflicts,
        create_lateness_visualizations,
        export_lateness_analysis
    )
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def create_optimized_schedule(original_events, optimization_results):
    """
    Create the optimized event schedule based on optimization results.
    This applies the agent reassignments to create the "after" scenario.
    """
    optimized_events = original_events.copy()
    
    # Apply daily optimizations
    for daily_result in optimization_results['daily_results']:
        date = daily_result['date']
        assignments = daily_result['assignments']
        
        # Apply each assignment
        for assignment in assignments:
            tour_id = assignment['tour_id']
            new_agent = assignment['assigned_agent']
            
            # Update the agent assignment for this tour
            optimized_events.at[tour_id, 'Leasing Agent ID'] = new_agent
    
    return optimized_events


def main():
    """Run complete travel analysis and optimization with specialization metrics on full dataset"""
    print("🚀 ELISEAI AGENT-LEVEL CALENDAR ANALYSIS WITH SPECIALIZATION METRICS")
    print("=" * 80)
    print("Complete analysis with insertion heuristic estimation")
    print("Enhanced with agent-level shift metrics, travel trip analysis, and specialization analysis")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Step 1: Load Data
    print("\n📊 Loading complete dataset...")
    event_log, agent_mapping, property_mapping = load_excel_data(
        'data/Agent Calendar Practical Materials.xlsx'
    )
    print(f"✅ Data loaded successfully!")
    print(f"   📊 Events: {len(event_log):,}")
    print(f"   👥 Agents: {len(agent_mapping)}")
    print(f"   🏢 Properties: {len(property_mapping)}")

    # Tour type distribution
    tour_types = event_log['Tour Type'].value_counts()
    print(f"\n📋 Tour Type Distribution:")
    for tour_type, count in tour_types.items():
        percentage = (count / len(event_log)) * 100
        print(f"   {tour_type}: {count:,} tours ({percentage:.1f}%)")
    start_date = event_log['Start Time'].min().strftime('%Y-%m-%d')
    end_date = event_log['End Time'].max().strftime('%Y-%m-%d')
    print(f"   📅 Analysis period: {start_date} to {end_date}")
    
    # Calculate analysis period in months for trip rate calculation
    analysis_days = (event_log['End Time'].max() - event_log['Start Time'].min()).days
    analysis_months = analysis_days / 30.44  # Average days per month

    # Step 2: Setup Database
    print(f"\n🗄️ Setting up database...")
    if os.path.exists('eliseai_analysis.db'):
        os.remove('eliseai_analysis.db')
    setup_database(event_log, agent_mapping, property_mapping)
    print(f"✅ Database created with all views")

    # Step 3: Geocode Properties
    print(f"\n📍 Loading or geocoding {len(property_mapping)} properties…")
    property_coords = geocode_properties(property_mapping)
    for prop_id, coords in list(property_coords.items())[:3]:
        prop_name = property_mapping[property_mapping['Property ID'] == prop_id]['Property Name'].iloc[0]
        print(f"   {prop_name}: {coords}")

    # Step 4: Create Distance Matrix
    print(f"\n📏 Creating distance matrix...")
    distance_matrix = create_distance_matrix(property_coords)
    print(f"✅ Distance matrix created: {distance_matrix.shape}")
    distances = distance_matrix.values[distance_matrix.values > 0]
    print(f"   Average: {distances.mean():.1f} min | Min: {distances.min():.1f} min | Max: {distances.max():.1f} min")

    # Step 5: Current Travel Analysis
    print(f"\n🚗 ANALYZING CURRENT TRAVEL PATTERNS")
    print("=" * 60)
    print("   Calculating current agent travel requirements...")
    travel_results = analyze_agent_travel(event_log, distance_matrix)
    total_travel = travel_results['total_estimated_travel_time']
    stats = travel_results['summary_stats']
    detailed = travel_results['detailed_results']
    print("✅ Current state analysis complete!")

    # Step 6: Agent-Level Shift Metrics
    print(f"\n👥 CALCULATING AGENT-LEVEL SHIFT METRICS")
    print("=" * 60)
    print("   Analyzing travel time per agent per shift...")
    shift_metrics = calculate_agent_shift_metrics(travel_results, agent_mapping)
    print_agent_shift_analysis(shift_metrics)
    print("✅ Agent-level analysis complete!")

    print(f"\n⏰ AGENT LATENESS RISK ANALYSIS")
    print("=" * 70)
    print("   Analyzing agents likely to be late due to insufficient travel time...")
    
    lateness_results = analyze_agent_lateness_risk(
        event_log, distance_matrix, agent_mapping, property_mapping
    )
    
    # Also check for impossible schedules
    impossible_schedules = analyze_schedule_conflicts(event_log, distance_matrix)
    
    print("✅ Lateness risk analysis complete!")
    
    # Step 7: Enhanced Estimation via Insertion Heuristic (NOW WITH TRIP COUNTING)
    print(f"\n🎯 ESTIMATION ANALYSIS - INSERTION HEURISTIC WITH TRIP COUNTING")
    print("=" * 70)
    print("   Estimating savings without full VRPTW solver...")
    print("   NOW INCLUDES: Travel trip counting for before/after comparison")
    est_results = optimization_estimate(event_log, distance_matrix, property_mapping)
    print("✅ Estimation complete!")
    
    # Step 8: NEW - Create Optimized Schedule for Specialization Analysis
    print(f"\n🔄 CREATING OPTIMIZED SCHEDULE FOR SPECIALIZATION ANALYSIS")
    print("=" * 70)
    print("   Applying optimization results to create 'after' scenario...")
    optimized_event_log = create_optimized_schedule(event_log, est_results)
    print("✅ Optimized schedule created!")
    
    # Step 9: NEW - Agent Specialization Analysis
    print(f"\n🎯 AGENT SPECIALIZATION ANALYSIS")
    print("=" * 70)
    print("   Analyzing how 'specialized' agents are to specific properties...")
    print("   Comparing before vs. after optimization...")
    
    # Calculate specialization metrics for original schedule
    original_specialization = calculate_agent_specialization_metrics(
        event_log, agent_mapping, property_mapping
    )
    
    # Calculate specialization metrics for optimized schedule
    optimized_specialization = calculate_agent_specialization_metrics(
        optimized_event_log, agent_mapping, property_mapping
    )
    
    # Compare before vs after
    specialization_comparison = compare_specialization_before_after(
        event_log, optimized_event_log, agent_mapping, property_mapping
    )
    print("✅ Specialization analysis complete!")

    # Step 10: Enhanced Results Display
    print(f"\n📊 ESTIMATION RESULTS:")
    print(f"   🕐 Travel Time:")
    print(f"      Baseline: {est_results['current_travel_minutes']:.1f} min")
    print(f"      Optimized: {est_results['optimized_travel_minutes']:.1f} min")
    print(f"      Savings: {est_results['potential_savings_minutes']:.1f} min ({est_results['savings_percentage']:.1f}%)")
    print(f"   🚗 Travel Trips:")
    print(f"      Current: {est_results['current_travel_trips']} trips")
    print(f"      Optimized: {est_results['optimized_travel_trips']} trips")
    print(f"      Reduction: {est_results['trip_savings']} trips ({est_results['trip_savings_percentage']:.1f}%)")
    print(f"   🎯 Agent Specialization:")
    print(f"      Average Specialization Change: {specialization_comparison['summary_stats']['avg_specialization_change']:+.1f} points")
    print(f"      Agents More Specialized: {specialization_comparison['summary_stats']['agents_more_specialized']}")
    print(f"      Agents Less Specialized: {specialization_comparison['summary_stats']['agents_less_specialized']}")
    
    print(f"   📊 Monthly Trip Rate:")
    current_monthly = est_results['current_travel_trips'] / analysis_months
    optimized_monthly = est_results['optimized_travel_trips'] / analysis_months
    print(f"      Current: {current_monthly:.1f} trips/month")
    print(f"      Optimized: {optimized_monthly:.1f} trips/month")

    # Step 11: Enhanced EliseAI Requirements with Trip Metrics and Specialization
    print(f"\n📊 ENHANCED REQUIREMENTS ANSWERS")
    print("=" * 60)
    print(f"🎯 REQUIREMENT 1 - Total travel: {total_travel:.1f} min ({stats['total_hours']:.1f} h)")
    print(f"🎯 REQUIREMENT 2 - Est. savings: {est_results['potential_savings_minutes']:.1f} min ({est_results['savings_percentage']:.1f}%)")
    print(f"🎯 NEW METRIC - Current trips: {est_results['current_travel_trips']} total ({current_monthly:.1f}/month)")
    print(f"🎯 NEW METRIC - Optimized trips: {est_results['optimized_travel_trips']} total ({optimized_monthly:.1f}/month)")
    print(f"🎯 NEW METRIC - Trip reduction: {est_results['trip_savings']} trips ({est_results['trip_savings_percentage']:.1f}%)")
    print(f"🎯 NEW METRIC - Avg travel per agent per shift: {shift_metrics['system_metrics']['avg_travel_time_per_shift_system']:.1f} min")
    print(f"🎯 NEW METRIC - Travel time range: {shift_metrics['system_metrics']['min_travel_time_per_shift']:.1f} - {shift_metrics['system_metrics']['max_travel_time_per_shift']:.1f} min")
    print(f"🎯 NEW METRIC - Agent specialization change: {specialization_comparison['summary_stats']['avg_specialization_change']:+.1f} points")
    print(f"🎯 NEW METRIC - Single-agent properties change: {specialization_comparison['summary_stats']['single_property_change']:+d}")
    # ADD THESE NEW LATENESS METRICS:
    print(f"🎯 LATENESS METRIC - Agents with timing issues: {lateness_results['system_stats']['agents_with_any_issues']}/{lateness_results['system_stats']['total_agents']} ({lateness_results['system_stats']['agents_with_any_issues']/lateness_results['system_stats']['total_agents']*100:.1f}%)")
    print(f"🎯 LATENESS METRIC - Late arrival rate: {lateness_results['system_stats']['system_lateness_rate']*100:.1f}% of transitions")
    print(f"🎯 LATENESS METRIC - Risk rate (late + risky): {lateness_results['system_stats']['system_risk_rate']*100:.1f}%")
    print(f"🎯 LATENESS METRIC - Average lateness: {lateness_results['system_stats']['avg_lateness_per_incident']:.1f} minutes per incident")
    if len(impossible_schedules) > 0:
        print(f"🚨 CRITICAL METRIC - Impossible schedules: {len(impossible_schedules)} conflicts found")
    # Step 12: Export Enhanced Results
    print(f"\n💾 EXPORTING ENHANCED RESULTS WITH SPECIALIZATION ANALYSIS")
    print("=" * 70)
    
    # Save agent-level metrics to CSV for further analysis
    agent_metrics_df = shift_metrics['agent_metrics']
    agent_metrics_df.to_csv('agent_shift_metrics.csv', index=False)
    print(f"✅ Agent shift metrics exported to 'agent_shift_metrics.csv'")
    
    # Save daily travel details
    detailed.to_csv('daily_travel_details.csv', index=False)
    print(f"✅ Daily travel details exported to 'daily_travel_details.csv'")
    
    # Save optimization results with trip analysis
    optimization_df = export_optimization_results(est_results, 'optimization_results_with_trips.csv')
    print(f"✅ Optimization results with trip analysis exported to 'optimization_results_with_trips.csv'")
    
    # NEW: Export specialization analysis
    export_specialization_analysis(specialization_comparison, 'specialization_analysis')
    print(f"✅ Specialization analysis exported to specialization_analysis_*.csv files")
    
    # NEW: Create specialization summary report
    create_specialization_summary_report(specialization_comparison, 'specialization_summary.txt')
    
    # Save original specialization metrics for reference
    original_specialization.to_csv('original_agent_specialization.csv', index=False)
    optimized_specialization.to_csv('optimized_agent_specialization.csv', index=False)
    print(f"✅ Individual specialization metrics exported")

    export_lateness_analysis(lateness_results, 'lateness_analysis')
    if len(impossible_schedules) > 0:
        impossible_schedules.to_csv('impossible_schedules.csv', index=False)
        print(f"🚨 Impossible schedules exported to 'impossible_schedules.csv'")
    
    # NEW: Create lateness visualization
    try:
        lateness_fig = create_lateness_visualizations(lateness_results)
        lateness_fig.savefig('lateness_analysis_dashboard.png', dpi=300, bbox_inches='tight')
        print(f"📊 Lateness analysis dashboard saved as 'lateness_analysis_dashboard.png'")
    except Exception as e:
        print(f"⚠️ Could not create lateness visualizations: {e}")
    # Create enhanced summary report
    create_enhanced_summary_report(est_results, analysis_months, shift_metrics, stats, specialization_comparison)
    print(f"✅ Enhanced executive summary exported to 'enhanced_executive_summary.txt'")
    
    print(f"\n🎉 ENHANCED ANALYSIS WITH SPECIALIZATION METRICS COMPLETE!")
    print(f"📈 Key Insights:")
    print(f"   • Current: {current_monthly:.1f} trips/month (vs your baseline of 77)")
    print(f"   • Optimized: {optimized_monthly:.1f} trips/month")
    print(f"   • Trip reduction: {est_results['trip_savings']} trips ({est_results['trip_savings_percentage']:.1f}%)")
    print(f"   • Time savings: {est_results['potential_savings_minutes']:.1f} min ({est_results['savings_percentage']:.1f}%)")
    print(f"   • Specialization impact: {specialization_comparison['summary_stats']['avg_specialization_change']:+.1f} avg change")
    
    if specialization_comparison['summary_stats']['avg_specialization_change'] > 5:
        print(f"   • 🎯 Optimization increases agent specialization (more property-focused)")
    elif specialization_comparison['summary_stats']['avg_specialization_change'] < -5:
        print(f"   • 🔄 Optimization decreases agent specialization (more cross-property flexibility)")
    else:
        print(f"   • ⚖️ Optimization maintains balanced specialization levels")

    return {
        'travel_results': travel_results,
        'shift_metrics': shift_metrics,
        'optimization_results': est_results,
        'specialization_comparison': specialization_comparison,
        'original_specialization': original_specialization,
        'optimized_specialization': optimized_specialization,
        'distance_matrix': distance_matrix,
        'analysis_months': analysis_months,
        'optimized_event_log': optimized_event_log
    }


def create_enhanced_summary_report(est_results, analysis_months, shift_metrics, stats, specialization_comparison):
    """Create an enhanced executive summary report including specialization analysis."""
    current_monthly = est_results['current_travel_trips'] / analysis_months
    optimized_monthly = est_results['optimized_travel_trips'] / analysis_months
    spec_stats = specialization_comparison['summary_stats']
    
    summary = f"""
ELISEAI TRAVEL OPTIMIZATION ANALYSIS - ENHANCED EXECUTIVE SUMMARY
================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TRAVEL TRIP ANALYSIS:
--------------------
Current Travel Trips:     {est_results['current_travel_trips']} total ({current_monthly:.1f} per month)
Optimized Travel Trips:   {est_results['optimized_travel_trips']} total ({optimized_monthly:.1f} per month)
Trip Reduction:           {est_results['trip_savings']} trips ({est_results['trip_savings_percentage']:.1f}% reduction)

TRAVEL TIME ANALYSIS:
--------------------
Current Travel Time:      {est_results['current_travel_minutes']:.1f} minutes ({stats['total_hours']:.1f} hours)
Optimized Travel Time:    {est_results['optimized_travel_minutes']:.1f} minutes
Time Savings:             {est_results['potential_savings_minutes']:.1f} minutes ({est_results['savings_percentage']:.1f}% reduction)

AGENT SHIFT METRICS:
-------------------
Average Travel per Shift: {shift_metrics['system_metrics']['avg_travel_time_per_shift_system']:.1f} minutes
Travel Range per Shift:   {shift_metrics['system_metrics']['min_travel_time_per_shift']:.1f} - {shift_metrics['system_metrics']['max_travel_time_per_shift']:.1f} minutes
Analysis Period:          {analysis_months:.1f} months

AGENT SPECIALIZATION ANALYSIS:
------------------------------
Average Specialization Change:     {spec_stats['avg_specialization_change']:+.1f} points (on 0-100 scale)
Median Specialization Change:      {spec_stats['median_specialization_change']:+.1f} points
Agents Becoming More Specialized:  {spec_stats['agents_more_specialized']} agents
Agents Becoming Less Specialized:  {spec_stats['agents_less_specialized']} agents

Property Coverage Changes:
• Single-Agent Properties:         {spec_stats['single_property_change']:+d} change
• Highly Concentrated Properties:  {spec_stats['concentrated_property_change']:+d} change

SPECIALIZATION METRICS EXPLAINED:
---------------------------------
• Specialization Score (0-100): Composite metric where:
  - 0-20: Very flexible (works across many properties)
  - 21-40: Somewhat flexible 
  - 41-60: Moderately specialized
  - 61-80: Highly specialized
  - 81-100: Extremely specialized (mostly one property)

• Property Concentration (HHI): Measures how concentrated an agent's work is
• Most Frequent Property %: What percentage of tours are at agent's primary property

COMPARISON TO BASELINE:
----------------------
Your baseline: 77 trips/month
Our analysis: {current_monthly:.1f} trips/month (current)
Difference: {current_monthly - 77:.1f} trips/month

OPTIMIZATION IMPACT SUMMARY:
---------------------------
Trip Efficiency Gain: {est_results['trip_savings_percentage']:.1f}% fewer trips needed
Time Efficiency Gain: {est_results['savings_percentage']:.1f}% less travel time required
Monthly Trip Reduction: {(current_monthly - optimized_monthly):.1f} trips per month

Specialization Impact:"""
    
    if spec_stats['avg_specialization_change'] > 5:
        summary += f"""
✅ INCREASED SPECIALIZATION: Optimization makes agents MORE specialized to specific properties.
   • Pros: Improved property familiarity, potential for better customer relationships
   • Cons: Reduced system flexibility, potential scheduling constraints
   • Net Effect: {spec_stats['avg_specialization_change']:+.1f} point increase in specialization
"""
    elif spec_stats['avg_specialization_change'] < -5:
        summary += f"""
✅ DECREASED SPECIALIZATION: Optimization distributes agents across MORE properties.
   • Pros: Increased system flexibility, better load balancing
   • Cons: Reduced property-specific expertise
   • Net Effect: {spec_stats['avg_specialization_change']:+.1f} point decrease in specialization
"""
    else:
        summary += f"""
✅ MAINTAINED SPECIALIZATION: Optimization preserves existing agent-property relationships.
   • Pros: Efficiency gains without disrupting established workflows
   • Cons: May miss opportunities for further optimization
   • Net Effect: {spec_stats['avg_specialization_change']:+.1f} point change (minimal impact)
"""

    summary += f"""

BUSINESS RECOMMENDATIONS:
------------------------
1. EFFICIENCY: Implement optimization to achieve {est_results['savings_percentage']:.1f}% travel time reduction
2. TRIPS: Reduce monthly travel trips from {current_monthly:.1f} to {optimized_monthly:.1f} per month
3. SPECIALIZATION: {"Consider gradual implementation to maintain agent expertise" if abs(spec_stats['avg_specialization_change']) > 10 else "Low specialization impact allows for immediate implementation"}
4. MONITORING: Track agent satisfaction and customer experience during rollout

NEXT STEPS:
----------
• Review individual agent specialization changes in detailed CSV exports
• Consider pilot program with agents showing minimal specialization impact
• Develop training for agents transitioning between properties
• Monitor customer satisfaction metrics during optimization implementation
"""
    
    with open('enhanced_executive_summary.txt', 'w') as f:
        f.write(summary)


if __name__ == "__main__":
    results = main()