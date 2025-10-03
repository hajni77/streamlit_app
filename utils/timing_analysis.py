"""
Timing analysis utility for the bathroom layout generator.
This module provides functions to analyze and visualize timing data.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

# Import the logging module
from utils.timing_logger import get_timing_summary

def load_timing_data() -> pd.DataFrame:
    """
    Load the timing data from the CSV file.
    
    Returns:
        Pandas DataFrame containing the timing data
    """
    csv_path = Path("logs") / "layout_timing.csv"
    if not csv_path.exists():
        return pd.DataFrame()
    
    # Define expected column names (must match timing_logger.py CSV_FIELDS)
    column_names = [
        "timestamp", 
        "operation", 
        "duration_ms", 
        "layout_id", 
        "room_width", 
        "room_depth",
        "num_objects",
        "additional_info"
    ]
    
    try:
        # Try reading with header first
        df = pd.read_csv(csv_path)
        
        # Check if the first column is actually 'timestamp' (has header)
        if 'timestamp' not in df.columns:
            # No header found, re-read with explicit column names
            df = pd.read_csv(csv_path, names=column_names, header=None)
    except Exception:
        # If any error, try reading without header
        df = pd.read_csv(csv_path, names=column_names, header=None)
    
    if df.empty:
        return df
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Convert duration to float
    df['duration_ms'] = df['duration_ms'].astype(float)
    
    # Convert room dimensions to numeric
    df['room_width'] = pd.to_numeric(df['room_width'], errors='coerce').fillna(0)
    df['room_depth'] = pd.to_numeric(df['room_depth'], errors='coerce').fillna(0)
    df['num_objects'] = pd.to_numeric(df['num_objects'], errors='coerce').fillna(0).astype(int)
    
    return df

def get_summary_stats(df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Get summary statistics for the timing data.
    
    Args:
        df: Pandas DataFrame containing timing data (optional, will load if not provided)
        
    Returns:
        Dictionary containing summary statistics
    """
    if df is None or df.empty:
        df = load_timing_data()
        
    if df.empty:
        return {"message": "No timing data available"}
        
    # Group by operation
    operation_stats = df.groupby('operation', observed=False).agg({
        'duration_ms': ['count', 'mean', 'min', 'max', 'sum']
    }).reset_index()
    
    # Flatten the multi-index columns
    operation_stats.columns = ['_'.join(col).strip('_') for col in operation_stats.columns.values]
    
    # Rename columns for clarity
    operation_stats = operation_stats.rename(columns={
        'operation_': 'operation',
        'duration_ms_count': 'count',
        'duration_ms_mean': 'avg_ms',
        'duration_ms_min': 'min_ms',
        'duration_ms_max': 'max_ms',
        'duration_ms_sum': 'total_ms'
    })
    
    # Calculate total time across all operations
    total_time_ms = df['duration_ms'].sum()
    total_count = df['duration_ms'].count()
    
    # Get counts for each operation type
    operation_counts = df['operation'].value_counts().to_dict()
    
    return {
        "operations": operation_stats.to_dict('records'),
        "total_time_ms": total_time_ms,
        "total_operations": total_count,
        "operation_counts": operation_counts
    }

def plot_timing_distribution(df: pd.DataFrame = None, 
                            operation: str = None, 
                            last_n_hours: int = None) -> plt.Figure:
    """
    Plot the distribution of timing data.
    
    Args:
        df: Pandas DataFrame containing timing data (optional, will load if not provided)
        operation: Filter by operation type (optional)
        last_n_hours: Filter to only include data from the last n hours (optional)
        
    Returns:
        Matplotlib figure containing the plot
    """
    if df is None or df.empty:
        df = load_timing_data()
        
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No timing data available", ha='center', va='center')
        return fig
        
    # Apply filters
    if operation:
        df = df[df['operation'] == operation]
        
    if last_n_hours:
        cutoff_time = datetime.now() - timedelta(hours=last_n_hours)
        df = df[df['timestamp'] > cutoff_time]
        
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data matching the filters", ha='center', va='center')
        return fig
        
    # Create a figure with multiple plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle("Layout Generation Timing Analysis", fontsize=16)
    
    # Plot 1: Duration distribution by operation
    ax1 = axes[0, 0]
    sns.boxplot(x='operation', y='duration_ms', data=df, ax=ax1)
    ax1.set_title("Duration Distribution by Operation")
    ax1.set_ylabel("Duration (ms)")
    ax1.set_xlabel("Operation")
    ax1.tick_params(axis='x', rotation=45)
    
    # Plot 2: Time series of durations
    ax2 = axes[0, 1]
    for op in df['operation'].unique():
        op_data = df[df['operation'] == op]
        ax2.scatter(op_data['timestamp'], op_data['duration_ms'], label=op, alpha=0.7)
    
    ax2.set_title("Duration Over Time")
    ax2.set_ylabel("Duration (ms)")
    ax2.set_xlabel("Timestamp")
    ax2.tick_params(axis='x', rotation=45)
    ax2.legend()
    
    # Plot 3: Duration vs room size (area)
    ax3 = axes[1, 0]
    df['room_area'] = df['room_width'] * df['room_depth']
    valid_area = df[df['room_area'] > 0]
    
    if not valid_area.empty:
        for op in valid_area['operation'].unique():
            op_data = valid_area[valid_area['operation'] == op]
            ax3.scatter(op_data['room_area'], op_data['duration_ms'], label=op, alpha=0.7)
            
        ax3.set_title("Duration vs Room Area")
        ax3.set_ylabel("Duration (ms)")
        ax3.set_xlabel("Room Area (cm²)")
        ax3.legend()
    else:
        ax3.text(0.5, 0.5, "No room size data available", ha='center', va='center')
    
    # Plot 4: Duration vs Number of Objects
    ax4 = axes[1, 1]
    valid_objects = df[df['num_objects'] > 0]
    
    if not valid_objects.empty:
        for op in valid_objects['operation'].unique():
            op_data = valid_objects[valid_objects['operation'] == op]
            ax4.scatter(op_data['num_objects'], op_data['duration_ms'], label=op, alpha=0.7)
            
        ax4.set_title("Duration vs Number of Objects")
        ax4.set_ylabel("Duration (ms)")
        ax4.set_xlabel("Number of Objects")
        ax4.legend()
    else:
        ax4.text(0.5, 0.5, "No object count data available", ha='center', va='center')
    
    plt.tight_layout()
    return fig

def get_performance_recommendations(df: pd.DataFrame = None) -> List[str]:
    """
    Analyze the timing data and provide recommendations for performance improvements.
    
    Args:
        df: Pandas DataFrame containing timing data (optional, will load if not provided)
        
    Returns:
        List of recommendation strings
    """
    if df is None or df.empty:
        df = load_timing_data()
        
    if df.empty:
        return ["No timing data available for analysis"]
        
    recommendations = []
    
    # Check for unusually slow operations
    operation_stats = df.groupby('operation', observed=False).agg({
        'duration_ms': ['mean', 'std', 'max']
    })
    
    for op, stats in operation_stats.iterrows():
        mean = stats[('duration_ms', 'mean')]
        std = stats[('duration_ms', 'std')]
        max_val = stats[('duration_ms', 'max')]
        
        # If max is significantly higher than mean (3+ std devs), suggest optimization
        if max_val > mean + 3 * std:
            recommendations.append(
                f"The '{op}' operation has outliers (max: {max_val:.2f}ms vs avg: {mean:.2f}ms). "
                f"Consider optimizing or investigating these slow cases."
            )
        
    # Check if room size correlates strongly with duration
    if 'room_width' in df.columns and 'room_depth' in df.columns:
        df['room_area'] = df['room_width'] * df['room_depth']
        
        # Group by room area ranges and check duration trends
        df['area_bin'] = pd.qcut(df['room_area'], 4, duplicates='drop')

        area_stats = df.groupby(['operation', 'area_bin'], observed=False).agg({
            'duration_ms': 'mean'
        }).reset_index()
        
        # Check if the largest rooms take disproportionately longer
        for op in area_stats['operation'].unique():
            op_stats = area_stats[area_stats['operation'] == op]
            if len(op_stats) > 1:
                min_duration = op_stats['duration_ms'].min()
                max_duration = op_stats['duration_ms'].max()
                
                if max_duration > 2 * min_duration:
                    recommendations.append(
                        f"The '{op}' operation scales poorly with room size. "
                        f"Consider optimizing algorithms for larger rooms."
                    )
    
    # Check if object count correlates strongly with duration
    if 'num_objects' in df.columns:
        # Filter to rows with object count data
        obj_df = df[df['num_objects'] > 0]
        
        if not obj_df.empty:
            # Group by object count ranges and check duration trends
            obj_df['obj_bin'] = pd.qcut(obj_df['num_objects'], min(4, obj_df['num_objects'].nunique()), duplicates='drop')
            obj_stats = obj_df.groupby(['operation', 'obj_bin'], observed=False).agg({
                'duration_ms': 'mean'
            }).reset_index()
            
            # Check for super-linear scaling with object count
            for op in obj_stats['operation'].unique():
                op_stats = obj_stats[obj_stats['operation'] == op]
                if len(op_stats) > 1:
                    # Check if duration increases faster than linearly with object count
                    first_bin = op_stats.iloc[0]
                    last_bin = op_stats.iloc[-1]
                    
                    first_bin_label = first_bin['obj_bin']
                    last_bin_label = last_bin['obj_bin']
                    
                    # Extract the average value from the bin (approximate)
                    try:
                        first_count = first_bin_label.mid
                        last_count = last_bin_label.mid
                        
                        first_duration = first_bin['duration_ms']
                        last_duration = last_bin['duration_ms']
                        
                        count_ratio = last_count / first_count if first_count > 0 else 1
                        duration_ratio = last_duration / first_duration if first_duration > 0 else 1
                        
                        if duration_ratio > count_ratio * 1.5:
                            recommendations.append(
                                f"The '{op}' operation scales super-linearly with object count. "
                                f"Consider optimizing algorithms for layouts with more objects."
                            )
                    except:
                        pass  # Skip if bin extraction fails
    
    # General recommendations if we have enough data
    if len(df) > 10:
        mean_gen_time = df[df['operation'] == 'layout_generation']['duration_ms'].mean() if 'layout_generation' in df['operation'].values else 0
        mean_score_time = df[df['operation'] == 'layout_scoring']['duration_ms'].mean() if 'layout_scoring' in df['operation'].values else 0
        
        if mean_gen_time > 1000:  # More than 1 second
            recommendations.append(
                "Layout generation takes more than 1 second on average. "
                "Consider implementing caching strategies or optimizing placement algorithms."
            )
            
        if mean_score_time > 500:  # More than 500ms
            recommendations.append(
                "Layout scoring takes more than 500ms on average. "
                "Consider optimizing scoring calculations or implementing early termination for low-scoring layouts."
            )
    
    # If no specific recommendations, add some general ones
    if not recommendations:
        recommendations = [
            "Implement caching for repeated calculations during layout generation.",
            "Consider parallel processing for generating multiple layout candidates.",
            "Review and optimize the constraint checking logic in the scoring function."
        ]
        
    return recommendations

if __name__ == "__main__":
    # Simple test to load and display timing data
    df = load_timing_data()
    if not df.empty:
        print(f"Loaded {len(df)} timing records")
        print(get_summary_stats(df))
        print("\nPerformance Recommendations:")
        for rec in get_performance_recommendations(df):
            print(f"- {rec}")
    else:
        print("No timing data available")
