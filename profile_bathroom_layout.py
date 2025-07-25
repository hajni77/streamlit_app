"""
Custom performance profiler for bathroom layout generator.
This script profiles the key functions in the bathroom layout generation pipeline.
"""

import time
import cProfile
import pstats
import io
from functools import wraps
import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import gc

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def profile_function(func):
    """Decorator to profile individual functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"⏱️  {func.__name__}: {execution_time:.4f} seconds")
        return result, execution_time
    return wrapper

class BathroomLayoutProfiler:
    """Custom profiler for bathroom layout generator functions."""
    
    def __init__(self):
        self.results = {}
        self.test_data = self._create_test_data()
    
    def _create_test_data(self):
        """Create test data based on actual application structure."""
        try:
            # Load object types
            with open('object_types.json') as f:
                object_types = json.load(f)
            
            # Import required classes
            from models.bathroom import Bathroom
            from models.windows_doors import WindowsDoors
            from models.object import BathroomObject
            
            # Create test bathroom (3x3m)
            bathroom = Bathroom(300, 300, 250, objects=[], windows_doors=[], object_types=object_types)
            
            # Create test windows/doors
            # WindowsDoors(name, wall, position, width, depth, height, hinge, way)
            door = WindowsDoors("Door", "top", 100, 80, 0, 200, "left", "inwards")
            
            # Test objects to place
            objects_to_place = ["toilet", "sink", "shower"]
            
            # Sample placed objects using your actual BathroomObject class
            placed_objects = [
                # BathroomObject takes (object_type, width, depth, height, shadow, position, wall)
                BathroomObject("toilet", 60, 40, 80, None, (50, 50), "top"),
                BathroomObject("sink", 50, 40, 85, None, (200, 50), "top"),
                BathroomObject("shower", 80, 80, 200, None, (50, 200), "top"),
            ]
            
            # Convert placed_objects to the format expected by your application
            formatted_objects = []
            for obj in placed_objects:
                # Adjust format based on your actual implementation
                x, y = obj.position
                formatted_objects.append((x, y, obj.width, obj.depth, obj.height, obj.object_type, False, True, []))
            
            # Success message
            print("✅ Test data created successfully")
            
            return {
                'bathroom': bathroom,
                'object_types': object_types,
                'objects_to_place': objects_to_place,
                'door': door,
                'windows_doors': [door],
                'placed_objects': placed_objects,
                'formatted_objects': formatted_objects,
                'room_size': (300, 300)
            }
            
        except Exception as e:
            print(f"❌ Failed to create test data: {e}")
            # Create minimal test data
            return {
                'bathroom': None,
                'object_types': {},
                'objects_to_place': ["toilet", "sink", "shower"],
                'windows_doors': [],
                'placed_objects': [],
                'formatted_objects': [],
                'room_size': (300, 300)
            }
    
    def profile_beam_search(self):
        """Profile BeamSearch - typically the most expensive operation."""
        print("\n🔍 Profiling Beam Search Algorithm...")
        
        try:
            from algorithms.beam_search import BeamSearch
            
            beam_search = BeamSearch(
                self.test_data['bathroom'],
                self.test_data['objects_to_place'],
                beam_width=3  # Using smaller beam width for faster profiling
            )
            
            @profile_function
            def run_beam_search():
                return beam_search.generate(
                    self.test_data['objects_to_place'],
                    self.test_data['windows_doors']
                )
            
            layouts, execution_time = run_beam_search()
            self.results['beam_search'] = execution_time
            print(f"   Generated {len(layouts)} layouts")
            return layouts
        
        except Exception as e:
            print(f"❌ Beam search profiling failed: {e}")
            return []
    
    def profile_layout_comparison(self):
        """Profile layout comparison functionality."""
        print("\n🔄 Profiling Layout Comparison...")
        
        try:
            from optimization import compare_room_layouts
            
            # Create mock layouts using your actual data structure
            layouts = [
                self.test_data['formatted_objects'],
                # Slightly modified layout
                [(x+10, y+10, w, d, h, t, mc, mw, s) for x, y, w, d, h, t, mc, mw, s in self.test_data['formatted_objects']]
            ]
            
            @profile_function
            def run_layout_comparison():
                return compare_room_layouts(
                    layouts,
                    self.test_data['room_size'],
                    self.test_data['object_types'],
                    self.test_data['windows_doors']
                )
            
            result, execution_time = run_layout_comparison()
            self.results['layout_comparison'] = execution_time
            return result
        
        except Exception as e:
            print(f"❌ Layout comparison profiling failed: {e}")
            return None
    
    def profile_space_identification(self):
        """Profile available space identification."""
        print("\n🏠 Profiling Available Space Identification...")
        
        try:
            from utils.helpers import identify_available_space
            
            @profile_function
            def run_space_identification():
                # Use grid_size=5 to test the optimization
                return identify_available_space(
                    self.test_data['formatted_objects'],
                    self.test_data['room_size'],
                    grid_size=5,  # Try with 5cm grid resolution
                    windows_doors=self.test_data['windows_doors']
                )
            
            spaces, execution_time = run_space_identification()
            self.results['space_identification'] = execution_time
            return spaces
        
        except Exception as e:
            print(f"❌ Space identification profiling failed: {e}")
            return None
    
    def profile_pathway_accessibility(self):
        """Profile pathway accessibility calculation."""
        print("\n🚶 Profiling Pathway Accessibility...")
        
        try:
            from visualization import Visualizer2D
            
            visualizer = Visualizer2D(
                self.test_data['bathroom']
            )
            
            @profile_function
            def run_pathway_check():
                return visualizer.visualize_pathway_accessibility(
                    self.test_data['formatted_objects'],
                    self.test_data['windows_doors']
                )
            
            result, execution_time = run_pathway_check()
            self.results['pathway_accessibility'] = execution_time
            return result
        
        except Exception as e:
            print(f"❌ Pathway accessibility profiling failed: {e}")
            return None
    
    def profile_visualization_2d(self):
        """Profile 2D visualization - another potentially expensive operation."""
        print("\n🎨 Profiling 2D Visualization...")
        
        try:
            from visualization import Visualizer2D
            
            visualizer = Visualizer2D(
                self.test_data['room_size'][0],
                self.test_data['room_size'][1],
                250  # Height
            )
            
            @profile_function
            def run_visualization():
                fig, ax = plt.subplots(figsize=(10, 8))
                visualizer.draw_bathroom_2d(
                    self.test_data['formatted_objects'],
                    self.test_data['windows_doors'],
                    ax
                )
                plt.close(fig)  # Close to avoid showing
                return fig
            
            result, execution_time = run_visualization()
            self.results['visualization_2d'] = execution_time
            return result
        
        except Exception as e:
            print(f"❌ 2D visualization profiling failed: {e}")
            return None
    
    def profile_room_validation(self):
        """Profile room validation functionality."""
        print("\n✅ Profiling Room Validation...")
        
        try:
            from utils.helpers import check_valid_room
            
            @profile_function
            def run_room_validation():
                return check_valid_room(self.test_data['formatted_objects'])
            
            result, execution_time = run_room_validation()
            self.results['room_validation'] = execution_time
            return result
        
        except Exception as e:
            print(f"❌ Room validation profiling failed: {e}")
            return None
    
    def run_focused_profile(self):
        """Run profiling on key functions in the bathroom layout generation pipeline."""
        print("🚀 Starting Focused Bathroom Layout Profiling...")
        print("=" * 70)
        
        # Track total time
        total_start = time.time()
        
        # Try profiling each component
        try: self.profile_room_validation()
        except Exception as e: print(f"❌ Room validation error: {e}")
        
        try: self.profile_space_identification()
        except Exception as e: print(f"❌ Space identification error: {e}")
        
        try: self.profile_pathway_accessibility()
        except Exception as e: print(f"❌ Pathway accessibility error: {e}")
        
        try: self.profile_visualization_2d()
        except Exception as e: print(f"❌ Visualization error: {e}")
        
        try: self.profile_layout_comparison()
        except Exception as e: print(f"❌ Layout comparison error: {e}")
        
        # Run beam search last as it's typically the most intensive
        try: self.profile_beam_search()
        except Exception as e: print(f"❌ Beam search error: {e}")
        
        # Calculate total time
        total_time = time.time() - total_start
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 BATHROOM LAYOUT GENERATOR PERFORMANCE SUMMARY")
        print("=" * 70)
        
        if self.results:
            # Sort results by execution time (descending)
            sorted_results = sorted(self.results.items(), key=lambda x: x[1], reverse=True)
            
            for func_name, exec_time in sorted_results:
                percentage = (exec_time / total_time) * 100
                print(f"{func_name:25}: {exec_time:8.4f}s ({percentage:5.1f}%)")
            
            print("-" * 70)
            print(f"{'TOTAL TIME':25}: {total_time:8.4f}s (100.0%)")
            
            # Identify top bottlenecks
            print("\n🔍 TOP PERFORMANCE BOTTLENECKS:")
            for i, (func_name, exec_time) in enumerate(sorted_results[:3], 1):
                percentage = (exec_time / total_time) * 100
                print(f"{i}. {func_name}: {exec_time:.4f}s ({percentage:.1f}%)")
                
            # Generate optimization recommendations
            print("\n💡 OPTIMIZATION RECOMMENDATIONS:")
            for func_name, exec_time in sorted_results[:3]:
                if func_name == 'beam_search':
                    print("- Reduce beam_width parameter (e.g., from 5 to 3)")
                    print("- Implement early filtering in placement strategy")
                elif func_name == 'pathway_accessibility' or func_name == 'space_identification':
                    print("- Increase grid resolution from 1cm to 5-10cm")
                    print("- Use NumPy vectorized operations for grid calculations")
                elif func_name == 'visualization_2d':
                    print("- Reduce visualization detail during generation phase")
                else:
                    print(f"- Optimize {func_name} with caching or simplified algorithms")
        else:
            print("❌ No profiling results collected")
        
        # Return results for further analysis
        return self.results

def run_detailed_profile():
    """Run detailed cProfile analysis on the most expensive function."""
    print("\n🔬 Running Detailed cProfile Analysis...")
    
    # Create profiler instance
    profiler = BathroomLayoutProfiler()
    
    # Get the most expensive function based on initial profiling
    results = profiler.run_focused_profile()
    if not results:
        print("❌ No profiling results available for detailed analysis")
        return
    
    # Find most expensive function
    most_expensive = max(results.items(), key=lambda x: x[1])[0]
    print(f"\n📈 Running detailed profiling on: {most_expensive}")
    
    # Set up cProfile
    pr = cProfile.Profile()
    pr.enable()
    
    try:
        # Run the most expensive function
        if most_expensive == 'beam_search':
            profiler.profile_beam_search()
        elif most_expensive == 'pathway_accessibility':
            profiler.profile_pathway_accessibility()
        elif most_expensive == 'space_identification':
            profiler.profile_space_identification()
        elif most_expensive == 'visualization_2d':
            profiler.profile_visualization_2d()
        elif most_expensive == 'layout_comparison':
            profiler.profile_layout_comparison()
        elif most_expensive == 'room_validation':
            profiler.profile_room_validation()
    except Exception as e:
        print(f"❌ Detailed profiling failed: {e}")
    
    pr.disable()
    
    # Print detailed results
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    print("\n" + "=" * 70)
    print("🔍 DETAILED FUNCTION CALL ANALYSIS (Top 20 functions)")
    print("=" * 70)
    print(s.getvalue())

if __name__ == "__main__":
    print("📊 Bathroom Layout Generator Profiler")
    print("This script identifies performance bottlenecks in your layout generator")
    print("=" * 70)
    
    # Run the profiler
    profiler = BathroomLayoutProfiler()
    results = profiler.run_focused_profile()
    
    # Clear memory
    gc.collect()
    
    # Run detailed profiling
    run_detailed_profile()
    
    print("\n✅ Profiling completed!")
    print("💡 Apply the recommended optimizations to improve performance")
