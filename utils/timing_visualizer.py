"""
Timing Visualization Generator.

This script creates visualizations from the timing log data,
providing insights into performance patterns in the layout generator.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any

# Set the style for visualizations
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'figure.figsize': (12, 9),
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12
})

def load_timing_data() -> pd.DataFrame:
    """
    Load the timing data from the CSV file.
    
    Returns:
        Pandas DataFrame containing the timing data
    """
    csv_path = Path("logs") / "layout_timing.csv"
    if not csv_path.exists():
        print(f"Warning: No timing data found at {csv_path}")
        return pd.DataFrame()
        
    df = pd.read_csv(csv_path)
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Convert duration to float
    df['duration_ms'] = df['duration_ms'].astype(float)
    
    return df

def create_operation_comparison_chart(df: pd.DataFrame, 
                                     save_path: Optional[str] = None) -> plt.Figure:
    """
    Create a chart comparing different operations' durations.
    
    Args:
        df: Timing data DataFrame
        save_path: Optional path to save the chart
        
    Returns:
        Matplotlib figure
    """
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data available", ha='center', va='center')
        return fig
    
    # Create a figure with subplots
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Operation Performance Analysis", fontsize=20)
    
    # 1. Boxplot of operation durations
    ax1 = axs[0, 0]
    sns.boxplot(x='operation', y='duration_ms', data=df, ax=ax1, palette="viridis")
    ax1.set_title("Duration Distribution by Operation Type")
    ax1.set_ylabel("Duration (ms)")
    ax1.set_xlabel("Operation")
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Violin plot for more detailed distribution view
    ax2 = axs[0, 1]
    sns.violinplot(x='operation', y='duration_ms', data=df, ax=ax2, palette="viridis", inner="quartile")
    ax2.set_title("Duration Distribution Detail")
    ax2.set_ylabel("Duration (ms)")
    ax2.set_xlabel("Operation")
    ax2.tick_params(axis='x', rotation=45)
    
    # 3. Time series of durations
    ax3 = axs[1, 0]
    for op in df['operation'].unique():
        op_data = df[df['operation'] == op]
        ax3.scatter(op_data['timestamp'], op_data['duration_ms'], label=op, alpha=0.6)
        # Add trend line
        if len(op_data) > 1:
            z = np.polyfit(op_data['timestamp'].astype(int) / 10**9, op_data['duration_ms'], 1)
            p = np.poly1d(z)
            ax3.plot(op_data['timestamp'], p(op_data['timestamp'].astype(int) / 10**9), 
                    '--', linewidth=2)
    
    ax3.set_title("Operation Duration Over Time")
    ax3.set_ylabel("Duration (ms)")
    ax3.set_xlabel("Timestamp")
    ax3.tick_params(axis='x', rotation=45)
    ax3.legend()
    
    # 4. Bar chart of average durations
    ax4 = axs[1, 1]
    avg_durations = df.groupby('operation')['duration_ms'].agg(['mean', 'count']).reset_index()
    sns.barplot(x='operation', y='mean', data=avg_durations, ax=ax4, palette="viridis")
    ax4.set_title("Average Duration by Operation")
    ax4.set_ylabel("Average Duration (ms)")
    ax4.set_xlabel("Operation")
    
    # Add count labels on bars
    for i, p in enumerate(ax4.patches):
        height = p.get_height()
        count = avg_durations.iloc[i]['count']
        ax4.text(p.get_x() + p.get_width()/2., height + height*0.02,
                f'n={count}', ha="center", fontsize=10)
    
    plt.tight_layout()
    fig.subplots_adjust(top=0.92)
    
    # Save the figure if a path is provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_scaling_analysis_chart(df: pd.DataFrame,
                                save_path: Optional[str] = None) -> plt.Figure:
    """
    Create charts showing how performance scales with room size and object count.
    
    Args:
        df: Timing data DataFrame
        save_path: Optional path to save the chart
        
    Returns:
        Matplotlib figure
    """
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data available", ha='center', va='center')
        return fig
    
    # Calculate room area
    df['room_area'] = df['room_width'] * df['room_depth']
    
    # Create figure with subplots
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Performance Scaling Analysis", fontsize=20)
    
    # 1. Duration vs room area scatter plot with regression line
    ax1 = axs[0, 0]
    valid_area = df[df['room_area'] > 0]
    
    if not valid_area.empty:
        for op in valid_area['operation'].unique():
            op_data = valid_area[valid_area['operation'] == op]
            ax1.scatter(op_data['room_area'], op_data['duration_ms'], label=op, alpha=0.6)
            
            # Add regression line if we have enough data points
            if len(op_data) > 1:
                sns.regplot(x='room_area', y='duration_ms', data=op_data, 
                          scatter=False, ax=ax1, label=f"{op} trend")
        
        ax1.set_title("Duration vs Room Area")
        ax1.set_ylabel("Duration (ms)")
        ax1.set_xlabel("Room Area (cm²)")
        ax1.legend()
    else:
        ax1.text(0.5, 0.5, "No room size data available", ha='center', va='center')
    
    # 2. Duration vs number of objects
    ax2 = axs[0, 1]
    valid_objects = df[df['num_objects'] > 0]
    
    if not valid_objects.empty:
        for op in valid_objects['operation'].unique():
            op_data = valid_objects[valid_objects['operation'] == op]
            ax2.scatter(op_data['num_objects'], op_data['duration_ms'], label=op, alpha=0.6)
            
            # Add regression line if we have enough data points
            if len(op_data) > 1:
                sns.regplot(x='num_objects', y='duration_ms', data=op_data, 
                          scatter=False, ax=ax2, label=f"{op} trend")
        
        ax2.set_title("Duration vs Number of Objects")
        ax2.set_ylabel("Duration (ms)")
        ax2.set_xlabel("Number of Objects")
        ax2.legend()
    else:
        ax2.text(0.5, 0.5, "No object count data available", ha='center', va='center')
    
    # 3. Heatmap of room size vs object count (if we have enough data)
    ax3 = axs[1, 0]
    valid_data = df[(df['room_area'] > 0) & (df['num_objects'] > 0)]
    
    if len(valid_data) >= 10:  # Only create heatmap with enough data points
        # Create room area and object count bins
        valid_data['area_bin'] = pd.qcut(valid_data['room_area'], min(5, valid_data['room_area'].nunique()), 
                                      duplicates='drop')
        valid_data['obj_bin'] = pd.qcut(valid_data['num_objects'], min(5, valid_data['num_objects'].nunique()), 
                                     duplicates='drop')
        
        # Create pivot table
        pivot_data = valid_data.pivot_table(
            values='duration_ms',
            index='area_bin',
            columns='obj_bin',
            aggfunc='mean'
        )
        
        # Create heatmap
        sns.heatmap(pivot_data, annot=True, fmt=".0f", cmap="viridis", ax=ax3)
        ax3.set_title("Average Duration by Room Size and Object Count")
        ax3.set_ylabel("Room Area (cm²)")
        ax3.set_xlabel("Number of Objects")
    else:
        ax3.text(0.5, 0.5, "Not enough data for heatmap analysis", ha='center', va='center')
    
    # 4. Line chart showing performance trend over time
    ax4 = axs[1, 1]
    
    # Group by day and operation
    df['date'] = df['timestamp'].dt.date
    time_trend = df.groupby(['date', 'operation'])['duration_ms'].mean().reset_index()
    
    # Plot trend lines
    for op in time_trend['operation'].unique():
        op_data = time_trend[time_trend['operation'] == op]
        ax4.plot(op_data['date'], op_data['duration_ms'], 'o-', label=op)
    
    ax4.set_title("Average Duration Trend Over Time")
    ax4.set_ylabel("Average Duration (ms)")
    ax4.set_xlabel("Date")
    ax4.tick_params(axis='x', rotation=45)
    ax4.legend()
    
    plt.tight_layout()
    fig.subplots_adjust(top=0.92)
    
    # Save the figure if a path is provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_operations_timeline_chart(df: pd.DataFrame, 
                                   days: int = 7,
                                   save_path: Optional[str] = None) -> plt.Figure:
    """
    Create a timeline chart showing operations over time.
    
    Args:
        df: Timing data DataFrame
        days: Number of days to include in the timeline
        save_path: Optional path to save the chart
        
    Returns:
        Matplotlib figure
    """
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data available", ha='center', va='center')
        return fig
    
    # Filter to the last N days of data
    end_date = df['timestamp'].max()
    start_date = end_date - timedelta(days=days)
    recent_data = df[df['timestamp'] >= start_date]
    
    if recent_data.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f"No data available for the last {days} days", ha='center', va='center')
        return fig
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Create operation-specific colors
    operations = recent_data['operation'].unique()
    colors = plt.cm.viridis(np.linspace(0, 1, len(operations)))
    color_map = dict(zip(operations, colors))
    
    # Plot operations as scatter points
    for op in operations:
        op_data = recent_data[recent_data['operation'] == op]
        ax.scatter(op_data['timestamp'], op_data['duration_ms'], 
                  label=op, color=color_map[op], alpha=0.7, s=50)
    
    # Add operation count annotations
    op_counts = recent_data['operation'].value_counts()
    legend_labels = [f"{op} (n={op_counts[op]})" for op in operations]
    
    ax.legend(legend_labels)
    ax.set_title(f"Operations Timeline (Last {days} Days)")
    ax.set_xlabel("Time")
    ax.set_ylabel("Duration (ms)")
    ax.grid(True, alpha=0.3)
    
    # Format x-axis with dates
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Save the figure if a path is provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def generate_all_visualizations(output_dir: str = "timing_visualizations"):
    """
    Generate all timing visualizations and save them to the specified directory.
    
    Args:
        output_dir: Directory to save the visualizations
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Load timing data
    df = load_timing_data()
    
    if df.empty:
        print("No timing data available for visualization.")
        return
    
    # Generate visualizations
    print(f"Generating visualizations in {output_path}...")
    
    # Operation comparison chart
    create_operation_comparison_chart(df, str(output_path / "operation_comparison.png"))
    print("✓ Created operation comparison chart")
    
    # Scaling analysis chart
    create_scaling_analysis_chart(df, str(output_path / "scaling_analysis.png"))
    print("✓ Created scaling analysis chart")
    
    # Operations timeline
    create_operations_timeline_chart(df, days=30, save_path=str(output_path / "operations_timeline.png"))
    print("✓ Created operations timeline chart")
    
    print(f"All visualizations saved to {output_path}")

if __name__ == "__main__":
    # When run directly, generate all visualizations
    generate_all_visualizations()
