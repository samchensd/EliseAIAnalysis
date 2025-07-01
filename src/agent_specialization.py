import pandas as pd
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns


def calculate_agent_specialization_metrics(event_log, agent_mapping, property_mapping):
    """
    Calculate comprehensive agent specialization metrics to understand how 
    "specialized" agents are to specific properties.
    
    Returns multiple metrics that can be compared before/after optimization.
    """
    
    # Group by agent for analysis
    agent_specialization = []
    
    for agent_id in event_log['Leasing Agent ID'].unique():
        agent_events = event_log[event_log['Leasing Agent ID'] == agent_id]
        agent_name = "Unknown"
        if agent_id in agent_mapping['Agent ID'].values:
            agent_name = agent_mapping[agent_mapping['Agent ID'] == agent_id]['Agent Name'].iloc[0]
        
        # Basic counts
        total_tours = len(agent_events)
        unique_properties = agent_events['Property ID'].nunique()
        property_counts = agent_events['Property ID'].value_counts()
        
        # Specialization Metric 1: Property Concentration Index (Herfindahl-Hirschman Index)
        # Ranges from 1/n (perfectly distributed) to 1 (completely specialized)
        property_shares = property_counts / total_tours
        hhi = (property_shares ** 2).sum()
        
        # Specialization Metric 2: Percentage of tours at most frequent property
        most_frequent_property_pct = property_counts.iloc[0] / total_tours if len(property_counts) > 0 else 0
        most_frequent_property_id = property_counts.index[0] if len(property_counts) > 0 else None
        
        # Specialization Metric 3: Percentage of tours at top 3 properties
        top3_tours = property_counts.head(3).sum()
        top3_percentage = top3_tours / total_tours if total_tours > 0 else 0
        
        # Specialization Metric 4: Shannon Diversity Index (entropy-based)
        # Higher values = more diverse (less specialized)
        shannon_diversity = -sum(p * np.log(p) for p in property_shares if p > 0)
        
        # Specialization Metric 5: Gini Coefficient for property distribution
        # 0 = perfectly equal, 1 = maximum inequality (specialization)
        gini_coeff = calculate_gini_coefficient(property_counts.values)
        
        # Specialization Metric 6: Number of properties representing 80% of tours (Pareto)
        cumulative_pct = property_counts.cumsum() / total_tours
        properties_for_80pct = len(cumulative_pct[cumulative_pct <= 0.8]) + 1
        
        # Tour type specialization (if applicable)
        tour_type_counts = agent_events['Tour Type'].value_counts()
        escorted_pct = tour_type_counts.get('ESCORTED', 0) / total_tours if total_tours > 0 else 0
        virtual_pct = tour_type_counts.get('VIRTUAL_TOUR', 0) / total_tours if total_tours > 0 else 0
        
        # Get property name for most frequent property
        most_frequent_property_name = "N/A"
        if most_frequent_property_id and most_frequent_property_id in property_mapping['Property ID'].values:
            most_frequent_property_name = property_mapping[
                property_mapping['Property ID'] == most_frequent_property_id
            ]['Property Name'].iloc[0]
        
        agent_specialization.append({
            'agent_id': agent_id,
            'agent_name': agent_name,
            'total_tours': total_tours,
            'unique_properties_served': unique_properties,
            'property_concentration_index_hhi': hhi,
            'most_frequent_property_percentage': most_frequent_property_pct,
            'most_frequent_property_id': most_frequent_property_id,
            'most_frequent_property_name': most_frequent_property_name,
            'top3_properties_percentage': top3_percentage,
            'shannon_diversity_index': shannon_diversity,
            'gini_coefficient': gini_coeff,
            'properties_for_80_percent_tours': properties_for_80pct,
            'escorted_tour_percentage': escorted_pct,
            'virtual_tour_percentage': virtual_pct,
            'specialization_score': calculate_composite_specialization_score(
                hhi, most_frequent_property_pct, unique_properties, total_tours
            )
        })
    
    return pd.DataFrame(agent_specialization)


def calculate_gini_coefficient(values):
    """Calculate Gini coefficient for measuring inequality in property distribution."""
    if len(values) == 0:
        return 0
    
    # Sort values
    sorted_values = np.sort(values)
    n = len(sorted_values)
    
    # Calculate Gini coefficient
    cumsum = np.cumsum(sorted_values)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0


def calculate_composite_specialization_score(hhi, most_frequent_pct, unique_properties, total_tours):
    """
    Calculate a composite specialization score from 0 (not specialized) to 100 (highly specialized).
    Combines multiple metrics into a single interpretable score.
    """
    # Normalize HHI (0 to 1) to 0-100 scale
    hhi_score = hhi * 100
    
    # Most frequent property percentage (already 0-1) to 0-100 scale
    freq_score = most_frequent_pct * 100
    
    # Inverse of property diversity (more properties = less specialized)
    # Scale so that serving 1 property = 100, serving many properties approaches 0
    diversity_penalty = max(0, 100 - (unique_properties - 1) * 10) if total_tours > 0 else 0
    
    # Weighted average of components
    composite_score = (hhi_score * 0.4 + freq_score * 0.4 + diversity_penalty * 0.2)
    
    return min(100, composite_score)  # Cap at 100


def analyze_property_coverage(event_log, property_mapping):
    """
    Analyze how properties are covered by agents - which properties have 
    dedicated agents vs shared agents.
    """
    property_coverage = []
    
    for property_id in property_mapping['Property ID'].unique():
        property_events = event_log[event_log['Property ID'] == property_id]
        property_name = property_mapping[
            property_mapping['Property ID'] == property_id
        ]['Property Name'].iloc[0]
        
        total_tours = len(property_events)
        unique_agents = property_events['Leasing Agent ID'].nunique()
        agent_counts = property_events['Leasing Agent ID'].value_counts()
        
        # Property specialization metrics
        primary_agent_pct = agent_counts.iloc[0] / total_tours if len(agent_counts) > 0 else 0
        primary_agent_id = agent_counts.index[0] if len(agent_counts) > 0 else None
        
        # Gini coefficient for agent distribution at this property
        gini_coeff = calculate_gini_coefficient(agent_counts.values)
        
        property_coverage.append({
            'property_id': property_id,
            'property_name': property_name,
            'total_tours': total_tours,
            'unique_agents_serving': unique_agents,
            'primary_agent_percentage': primary_agent_pct,
            'primary_agent_id': primary_agent_id,
            'agent_distribution_gini': gini_coeff,
            'is_single_agent_property': unique_agents == 1,
            'is_highly_concentrated': primary_agent_pct > 0.8
        })
    
    return pd.DataFrame(property_coverage)


def compare_specialization_before_after(original_events, optimized_events, agent_mapping, property_mapping):
    """
    Compare agent specialization metrics before and after optimization.
    """
    print("\n🔍 AGENT SPECIALIZATION COMPARISON ANALYSIS")
    print("=" * 70)
    
    # Calculate metrics for both scenarios
    before_metrics = calculate_agent_specialization_metrics(original_events, agent_mapping, property_mapping)
    after_metrics = calculate_agent_specialization_metrics(optimized_events, agent_mapping, property_mapping)
    
    # Property coverage analysis
    before_coverage = analyze_property_coverage(original_events, property_mapping)
    after_coverage = analyze_property_coverage(optimized_events, property_mapping)
    
    print(f"📊 SYSTEM-WIDE SPECIALIZATION CHANGES:")
    print(f"   Average Specialization Score:")
    print(f"      Before: {before_metrics['specialization_score'].mean():.1f}")
    print(f"      After:  {after_metrics['specialization_score'].mean():.1f}")
    print(f"      Change: {after_metrics['specialization_score'].mean() - before_metrics['specialization_score'].mean():+.1f}")
    
    print(f"\n   Average Properties per Agent:")
    print(f"      Before: {before_metrics['unique_properties_served'].mean():.1f}")
    print(f"      After:  {after_metrics['unique_properties_served'].mean():.1f}")
    print(f"      Change: {after_metrics['unique_properties_served'].mean() - before_metrics['unique_properties_served'].mean():+.1f}")
    
    print(f"\n   Average Most Frequent Property %:")
    print(f"      Before: {before_metrics['most_frequent_property_percentage'].mean():.1%}")
    print(f"      After:  {after_metrics['most_frequent_property_percentage'].mean():.1%}")
    print(f"      Change: {after_metrics['most_frequent_property_percentage'].mean() - before_metrics['most_frequent_property_percentage'].mean():+.1%}")
    
    print(f"\n   Average Property Concentration (HHI):")
    print(f"      Before: {before_metrics['property_concentration_index_hhi'].mean():.3f}")
    print(f"      After:  {after_metrics['property_concentration_index_hhi'].mean():.3f}")
    print(f"      Change: {after_metrics['property_concentration_index_hhi'].mean() - before_metrics['property_concentration_index_hhi'].mean():+.3f}")
    
    # Property-level changes
    print(f"\n📍 PROPERTY-LEVEL COVERAGE CHANGES:")
    print(f"   Single-Agent Properties:")
    single_before = before_coverage['is_single_agent_property'].sum()
    single_after = after_coverage['is_single_agent_property'].sum()
    print(f"      Before: {single_before} properties")
    print(f"      After:  {single_after} properties")
    print(f"      Change: {single_after - single_before:+d} properties")
    
    print(f"\n   Highly Concentrated Properties (>80% one agent):")
    concentrated_before = before_coverage['is_highly_concentrated'].sum()
    concentrated_after = after_coverage['is_highly_concentrated'].sum()
    print(f"      Before: {concentrated_before} properties")
    print(f"      After:  {concentrated_after} properties")
    print(f"      Change: {concentrated_after - concentrated_before:+d} properties")
    
    # Individual agent changes
    print(f"\n👥 INDIVIDUAL AGENT CHANGES:")
    print("   Top 5 agents with biggest specialization changes:")
    
    # Merge before/after data
    comparison = before_metrics[['agent_id', 'agent_name', 'specialization_score']].merge(
        after_metrics[['agent_id', 'specialization_score']], 
        on='agent_id', 
        suffixes=('_before', '_after')
    )
    comparison['specialization_change'] = comparison['specialization_score_after'] - comparison['specialization_score_before']
    
    # Show biggest changes
    biggest_changes = comparison.nlargest(5, 'specialization_change')
    for _, agent in biggest_changes.iterrows():
        print(f"      {agent['agent_name']}: {agent['specialization_score_before']:.1f} → {agent['specialization_score_after']:.1f} ({agent['specialization_change']:+.1f})")
    
    print(f"\n   Top 5 agents with biggest specialization decreases:")
    biggest_decreases = comparison.nsmallest(5, 'specialization_change')
    for _, agent in biggest_decreases.iterrows():
        print(f"      {agent['agent_name']}: {agent['specialization_score_before']:.1f} → {agent['specialization_score_after']:.1f} ({agent['specialization_change']:+.1f})")
    
    return {
        'before_agent_metrics': before_metrics,
        'after_agent_metrics': after_metrics,
        'before_property_coverage': before_coverage,
        'after_property_coverage': after_coverage,
        'agent_comparison': comparison,
        'summary_stats': {
            'avg_specialization_change': comparison['specialization_change'].mean(),
            'median_specialization_change': comparison['specialization_change'].median(),
            'agents_more_specialized': (comparison['specialization_change'] > 0).sum(),
            'agents_less_specialized': (comparison['specialization_change'] < 0).sum(),
            'single_property_change': single_after - single_before,
            'concentrated_property_change': concentrated_after - concentrated_before
        }
    }


def export_specialization_analysis(specialization_comparison, filename_prefix='specialization_analysis'):
    """Export all specialization analysis results to CSV files."""
    
    # Export agent-level metrics
    specialization_comparison['before_agent_metrics'].to_csv(
        f'{filename_prefix}_before_agents.csv', index=False
    )
    specialization_comparison['after_agent_metrics'].to_csv(
        f'{filename_prefix}_after_agents.csv', index=False
    )
    
    # Export property coverage
    specialization_comparison['before_property_coverage'].to_csv(
        f'{filename_prefix}_before_properties.csv', index=False
    )
    specialization_comparison['after_property_coverage'].to_csv(
        f'{filename_prefix}_after_properties.csv', index=False
    )
    
    # Export comparison
    specialization_comparison['agent_comparison'].to_csv(
        f'{filename_prefix}_agent_comparison.csv', index=False
    )
    
    print(f"✅ Specialization analysis exported to {filename_prefix}_*.csv files")
    
    return True


def create_specialization_summary_report(specialization_comparison, filename='specialization_summary.txt'):
    """Create a summary report of specialization analysis."""
    
    summary_stats = specialization_comparison['summary_stats']
    comparison = specialization_comparison['agent_comparison']
    
    report = f"""
AGENT SPECIALIZATION ANALYSIS SUMMARY
=====================================
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW:
---------
This analysis measures how "specialized" agents are to specific properties.
Higher specialization = agents work primarily at one or few properties.
Lower specialization = agents work across many different properties.

KEY METRICS EXPLAINED:
---------------------
• Specialization Score (0-100): Composite metric where 100 = highly specialized to one property
• Property Concentration (HHI): 0-1 scale, higher = more concentrated at fewer properties  
• Most Frequent Property %: Percentage of tours at agent's most common property
• Unique Properties Served: Number of different properties agent works at

SYSTEM-WIDE IMPACT:
------------------
Average Specialization Change: {summary_stats['avg_specialization_change']:+.1f} points
Median Specialization Change:  {summary_stats['median_specialization_change']:+.1f} points

Agents Becoming MORE Specialized:  {summary_stats['agents_more_specialized']} agents
Agents Becoming LESS Specialized:  {summary_stats['agents_less_specialized']} agents

Property Coverage Changes:
• Single-Agent Properties: {summary_stats['single_property_change']:+d} change
• Highly Concentrated Properties: {summary_stats['concentrated_property_change']:+d} change

INTERPRETATION:
--------------
"""
    
    if summary_stats['avg_specialization_change'] > 5:
        report += "✅ INCREASED SPECIALIZATION: Optimization tends to make agents more specialized to specific properties.\n"
        report += "   This could improve agent familiarity with properties but may reduce flexibility.\n"
    elif summary_stats['avg_specialization_change'] < -5:
        report += "✅ DECREASED SPECIALIZATION: Optimization tends to distribute agents across more properties.\n"
        report += "   This increases system flexibility but may reduce property-specific expertise.\n"
    else:
        report += "✅ MINIMAL SPECIALIZATION CHANGE: Optimization maintains similar specialization levels.\n"
        report += "   This suggests good balance between efficiency and current agent-property relationships.\n"
    
    report += f"""
DETAILED STATISTICS:
-------------------
Most Specialized Agent (After): {comparison.loc[comparison['specialization_score_after'].idxmax(), 'agent_name']} ({comparison['specialization_score_after'].max():.1f} score)
Least Specialized Agent (After): {comparison.loc[comparison['specialization_score_after'].idxmin(), 'agent_name']} ({comparison['specialization_score_after'].min():.1f} score)

Biggest Specialization Increase: {comparison.loc[comparison['specialization_change'].idxmax(), 'agent_name']} ({comparison['specialization_change'].max():+.1f} points)
Biggest Specialization Decrease: {comparison.loc[comparison['specialization_change'].idxmin(), 'agent_name']} ({comparison['specialization_change'].min():+.1f} points)
"""
    
    with open(filename, 'w') as f:
        f.write(report)
    
    print(f"✅ Specialization summary report saved to {filename}")
    
    return report