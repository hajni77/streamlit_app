"""
Timing Visualization Demo

This script demonstrates the timing visualizations with sample data.
If no real timing data exists, it will generate synthetic data for demonstration purposes.

Usage:
    python demo_visualizations.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import datetime
import random
from utils.timing_visualizer import (
    create_operation_comparison_chart,
    create_scaling_analysis_chart,
    create_operations_timeline_chart
)

def load_or_generate_data():
    """
    Load real timing data if available, otherwise generate synthetic data.
    
    Returns:
        Pandas DataFrame of timing data
    """
    csv_path = Path("logs") / "layout_timing.csv"
    
    if csv_path.exists():
        print("Loading real timing data...")
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['duration_ms'] = df['duration_ms'].astype(float)
        return df
    
    print("No real timing data found. Generating synthetic data for demonstration...")
    
    # Generate synthetic data
    operations = ['layout_generation', 'layout_scoring', 'object_placement']
    
    # Define characteristics for each operation
    operation_params = {
        'layout_generation': {
            'count': 30,
            'mean_duration': 800,
            'std_duration': 200,
            'room_size_effect': 0.5,
            'object_count_effect': 0.7
        },
        'layout_scoring': {
            'count': 100,
            'mean_duration': 250,
            'std_duration': 80,
            'room_size_effect': 0.3,
            'object_count_effect': 0.8
        },
        'object_placement': {
            'count': 500,
            'mean_duration': 50,
            'std_duration': 15,
            'room_size_effect': 0.2,
            'object_count_effect': 0.4
        }
    }
    
    # Generate timestamps spanning last 30 days
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    
    data = []
    
    for op, params in operation_params.items():
        # Create timestamps
        timestamps = [
            start_date + datetime.timedelta(
                seconds=random.randint(0, int((end_date - start_date).total_seconds()))
            )
            for _ in range(params['count'])
        ]
        
        # Sort timestamps
        timestamps.sort()
        
        for i, timestamp in enumerate(timestamps):
            # Create randomized room sizes that make sense
            room_width = random.randint(150, 500)
            room_depth = random.randint(150, 400)
            room_area = room_width * room_depth
            
            # Number of objects depends on room size somewhat
            num_objects = max(3, int(np.sqrt(room_area) / 20) + random.randint(-1, 2))
            
            # Base duration with randomness
            base_duration = np.random.normal(
                params['mean_duration'], 
                params['std_duration']
            )
            
            # Apply scaling factors
            room_effect = (room_area / 10000) ** params['room_size_effect']
            object_effect = num_objects ** params['object_count_effect']
            
            # Calculate final duration with some randomness
            duration = base_duration * room_effect * object_effect * random.uniform(0.85, 1.15)
            
            # Generate a layout ID
            layout_id = f"demo-{random.randint(1000, 9999)}"
            
            # Add record
            data.append({
                'timestamp': timestamp,
                'operation': op,
                'duration_ms': max(1, duration),  # Ensure positive duration
                'layout_id': layout_id,
                'room_width': room_width,
                'room_depth': room_depth,
                'num_objects': num_objects,
                'additional_info': ''
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save synthetic data (optional)
    os.makedirs('logs', exist_ok=True)
    df.to_csv('logs/demo_timing.csv', index=False)
    
    return df

def demo_visualizations():
    """Run visualization demo with real or synthetic data"""
    # Load or generate data
    df = load_or_generate_data()
    
    print(f"Loaded {len(df)} timing records spanning {df['operation'].nunique()} operation types")
    
    # Create directory for visualizations
    output_dir = Path("demo_visualizations")
    output_dir.mkdir(exist_ok=True)
    
    # Create and save visualizations
    print("Generating visualizations...")
    
    # Operation comparison chart
    fig1 = create_operation_comparison_chart(df)
    fig1_path = output_dir / "operation_comparison.png"
    fig1.savefig(fig1_path, dpi=300, bbox_inches='tight')
    print(f"✓ Created operation comparison chart: {fig1_path}")
    
    # Scaling analysis chart
    fig2 = create_scaling_analysis_chart(df)
    fig2_path = output_dir / "scaling_analysis.png"
    fig2.savefig(fig2_path, dpi=300, bbox_inches='tight')
    print(f"✓ Created scaling analysis chart: {fig2_path}")
    
    # Operations timeline chart
    fig3 = create_operations_timeline_chart(df, days=30)
    fig3_path = output_dir / "operations_timeline.png"
    fig3.savefig(fig3_path, dpi=300, bbox_inches='tight')
    print(f"✓ Created operations timeline chart: {fig3_path}")
    
    print(f"\nDemo complete! Visualizations saved to {output_dir}")
    print("Open these files to view the visualization examples.")

if __name__ == "__main__":
    demo_visualizations()
