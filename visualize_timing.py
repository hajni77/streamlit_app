"""
Timing Visualization Generator

This script generates visualizations from the timing logs to help identify
performance patterns and bottlenecks in the bathroom layout generator.

Usage:
    python visualize_timing.py

Output:
    Creates visualizations in the 'timing_visualizations' directory
"""

import os
import argparse
from pathlib import Path
from utils.timing_visualizer import (
    generate_all_visualizations, 
    load_timing_data, 
    create_operation_comparison_chart,
    create_scaling_analysis_chart,
    create_operations_timeline_chart
)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate timing visualizations')
    parser.add_argument('--output-dir', type=str, default='timing_visualizations',
                        help='Directory to save visualizations (default: timing_visualizations)')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to include in timeline chart (default: 30)')
    parser.add_argument('--show', action='store_true',
                        help='Show visualizations instead of saving them')
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    if not args.show:
        output_path = Path(args.output_dir)
        output_path.mkdir(exist_ok=True)
        print(f"Output directory: {output_path}")
    
    # Load timing data
    df = load_timing_data()
    
    if df.empty:
        print("No timing data available. Generate some layouts first to collect performance metrics.")
        return
    
    print(f"Loaded {len(df)} timing records spanning {df['operation'].nunique()} operation types")
    
    # Generate visualizations
    if args.show:
        print("Generating visualizations for display...")
        
        import matplotlib.pyplot as plt
        
        # Create charts
        op_fig = create_operation_comparison_chart(df)
        scaling_fig = create_scaling_analysis_chart(df)
        timeline_fig = create_operations_timeline_chart(df, days=args.days)
        
        # Show figures
        plt.show()
    else:
        print(f"Generating visualizations in {args.output_dir}...")
        generate_all_visualizations(args.output_dir)
        print("\nVisualization complete! Open the files in your image viewer to see the results.")

if __name__ == "__main__":
    main()
