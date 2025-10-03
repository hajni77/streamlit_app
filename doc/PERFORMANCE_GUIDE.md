# Performance Analysis Guide

This guide explains how to use the performance tracking and analysis tools to optimize the bathroom layout generator.

## Available Tools

### 1. Streamlit UI Performance Tab

The simplest way to analyze performance is through the Performance tab in the Streamlit application:

1. Run the Streamlit app: `streamlit run app.py`
2. Navigate to the "Performance" tab
3. View summary statistics and visualizations
4. Use filters to focus on specific operations or time ranges

### 2. Command-Line Visualization

For more detailed visualizations, use the command-line tools:

```bash
# Generate all visualizations and save to the timing_visualizations directory
python visualize_timing.py

# Show visualizations without saving
python visualize_timing.py --show

# Specify custom output directory
python visualize_timing.py --output-dir my_visualizations

# Set the number of days to include in timeline chart
python visualize_timing.py --days 14
```

### 3. Demo Visualizations

If you don't have enough real timing data yet:

```bash
# Generate example visualizations with synthetic data
python demo_visualizations.py
```

### 4. Fix Timing Data

If your timing data contains zero durations or other issues:

```bash
# Fix timing durations based on timestamp differences
python fix_timing_durations.py

# Comprehensive system fix (updates code and fixes data)
python fix_timing_system.py
```

## Interpreting the Visualizations

### Operation Comparison Chart

This chart shows:
- Box plot distribution of durations by operation type
- Violin plots showing the detailed shape of the duration distribution
- Time series showing how durations change over time
- Bar chart of average durations

**What to look for:**
- Operations with unusually high durations
- Wide distribution ranges indicating inconsistent performance
- Upward trends in the time series suggesting performance degradation

### Scaling Analysis Chart

This chart shows:
- Scatter plot of duration vs. room size
- Scatter plot of duration vs. number of objects
- Heatmap of room size vs. object count (with enough data)
- Performance trend lines over time

**What to look for:**
- Super-linear scaling with room size or object count
- Hot spots in the heatmap indicating problematic combinations
- Disproportionate performance impact from certain factors

### Operations Timeline

This chart shows:
- Timeline of all operations with their durations
- Color coding by operation type
- Annotations for operation counts

**What to look for:**
- Clusters of high-duration operations
- Patterns in execution sequence
- Operation types that consistently take longer

## Understanding Performance Metrics

### Key Metrics

1. **Average Duration**
   - Overall average time per operation
   - Baseline for performance benchmarking

2. **Maximum Duration**
   - Worst-case performance scenario
   - Identifies potential outliers

3. **Operation Count**
   - Number of operations performed
   - Indicates algorithm efficiency

4. **Duration Distribution**
   - Spread of operation durations
   - Indicates performance consistency

### Performance Recommendations

The system automatically generates recommendations based on timing analysis:

1. **Algorithm Optimization**
   - Suggestions for improving core algorithms
   - Identification of inefficient code patterns

2. **Scaling Recommendations**
   - How to handle larger rooms or more complex layouts
   - Optimization strategies for edge cases

3. **Caching Opportunities**
   - Identification of repeated calculations
   - Suggestions for caching strategies

## Adding Custom Timing

You can add timing to your own code:

```python
from utils.timing_logger import TimingContext

# Basic usage
with TimingContext("custom_operation", layout_id="abc123") as tc:
    # Code to time goes here
    result = your_function()
    
    # Add additional info during execution
    tc.add_info({"result_quality": result.score})
```

## Analyzing Timing Data Programmatically

For custom analysis, use the provided utilities:

```python
from utils.timing_analysis import load_timing_data, get_summary_stats
from utils.timing_visualizer import create_operation_comparison_chart
import matplotlib.pyplot as plt

# Load timing data
data = load_timing_data()

# Get summary statistics
stats = get_summary_stats(data)

# Print average time for layout generation
for op in stats['operations']:
    if op['operation'] == 'layout_generation':
        print(f"Average layout generation time: {op['avg_ms']} ms")

# Create custom visualization
fig = create_operation_comparison_chart(data)
plt.show()
```

## Tips for Performance Optimization

1. **Optimize Object Placement Logic**
   - This is typically the most time-consuming operation
   - Focus on efficient candidate generation and filtering

2. **Reduce Unnecessary Scoring**
   - Avoid scoring layouts that are clearly invalid
   - Implement early termination for poor layouts

3. **Implement Caching**
   - Cache frequently calculated values
   - Reuse calculations across similar layouts

4. **Optimize Data Structures**
   - Use efficient data structures for layout representation
   - Consider spatial indexing for faster object interaction checks

5. **Parallelize Operations**
   - Generate and evaluate multiple layouts in parallel
   - Use multiprocessing for CPU-intensive operations

6. **Batch Similar Operations**
   - Group similar operations to reduce overhead
   - Process objects by type to leverage similar constraints

7. **Profile Specific Operations**
   - Use the timing system to profile specific algorithm parts
   - Focus optimization efforts on the most time-consuming operations
