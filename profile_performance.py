"""Performance profiling script for bathroom layout generator.
Focuses on functions actually connected to app_modular.py to measure performance improvements.
"""

import time
import cProfile
import pstats
import io
from functools import wraps
import json
import sys
import os

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import only the modules actually used by app_modular.py
from algorithms.beam_search import BeamSearch
from models.bathroom import Bathroom
from models.layout import Layout
from models.object import BathroomObject
from models.windows_doors import WindowsDoors
from utils.helpers import get_required_area, identify_available_space, mark_inaccessible_spaces, check_valid_room, check_overlap
from optimization import compare_room_layouts
from optimization.scoring import BathroomScoringFunction
from visualization import Visualizer2D, Visualizer3D
from validation import get_constraint_validator

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

class PerformanceProfiler:
    """Main profiler class for bathroom layout generation."""
    
    def __init__(self):
        self.results = {}
        self.test_data = self._create_test_data()
    
    def _create_test_data(self):
        """Create standardized test data for consistent profiling."""
        # Load object types
        with open('object_types.json') as f:
            object_types = json.load(f)
        
        # Create test bathroom
        bathroom = Bathroom(300, 300, 250, object_types)  # 3x3m bathroom
        
        # Test objects to place
        objects_to_place = ["toilet", "sink", "shower", "cabinet"]
        
        # Test windows/doors
        windows_doors = [
            (1, "top", 100, 0, 80, 200, 0)  # Door on north wall
        ]
        
        # Sample placed objects for evaluation
        placed_objects = [
            (50, 50, 60, 40, 80, "toilet", False, True, [(45, 45, 70, 50)]),
            (200, 50, 50, 40, 85, "sink", False, True, [(195, 45, 60, 50)]),
            (50, 200, 80, 80, 200, "shower", True, True, [(45, 195, 90, 90)]),
        ]
        
        return {
            'bathroom': bathroom,
            'object_types': object_types,
            'objects_to_place': objects_to_place,
            'windows_doors': windows_doors,
            'placed_objects': placed_objects,
            'room_sizes': (300, 300)
        }
    
    def profile_beam_search(self):
        """Profile the beam search algorithm."""
        print("\n🔍 Profiling Beam Search Algorithm...")
        
        beam_search = BeamSearch(
            self.test_data['bathroom'], 
            self.test_data['objects_to_place'], 
            beam_width=3  # Reduced from default 5
        )
        
        @profile_function
        def run_beam_search():
            return beam_search.generate(
                self.test_data['objects_to_place'], 
                self.test_data['windows_doors']
            )
        
        layouts, execution_time = run_beam_search()
        self.results['beam_search'] = execution_time
        return layouts
    
    def profile_placement_strategy(self):
        """Profile the placement strategy."""
        print("\n📍 Profiling Placement Strategy...")
        
        strategy = DefaultPlacementStrategy()
        
        @profile_function
        def run_placement_generation():
            return strategy.generate_options(
                None,  # layout
                "toilet",  # obj_type
                self.test_data['object_types']["toilet"],  # obj_def
                self.test_data['room_sizes'],  # bathroom_size
                [],  # placed_objects
                self.test_data['windows_doors'],  # windows_doors
                num_options=10
            )
        
        options, execution_time = run_placement_generation()
        self.results['placement_generation'] = execution_time
        return options
    
    def profile_pathway_accessibility(self):
        """Profile pathway accessibility checking."""
        print("\n🚶 Profiling Pathway Accessibility...")
        
        @profile_function
        def run_pathway_check():
            return check_pathway_accessibility(
                self.test_data['placed_objects'],
                self.test_data['room_sizes'],
                self.test_data['windows_doors'],
                path_width=60
            )
        
        result, execution_time = run_pathway_check()
        self.results['pathway_accessibility'] = execution_time
        return result
    
    def profile_layout_evaluation(self):
        """Profile layout evaluation."""
        print("\n📊 Profiling Layout Evaluation...")
        
        @profile_function
        def run_layout_evaluation():
            return evaluate_room_layout(
                self.test_data['placed_objects'],
                self.test_data['room_sizes'],
                self.test_data['object_types'],
                self.test_data['windows_doors']
            )
        
        result, execution_time = run_layout_evaluation()
        self.results['layout_evaluation'] = execution_time
        return result
    
    def profile_layout_comparison(self):
        """Profile layout comparison."""
        print("\n🔄 Profiling Layout Comparison...")
        
        # Create multiple test layouts
        layouts = [
            self.test_data['placed_objects'],
            # Slightly modified layout
            [(60, 60, 60, 40, 80, "toilet", False, True, [(55, 55, 70, 50)]),
             (210, 60, 50, 40, 85, "sink", False, True, [(205, 55, 60, 50)]),
             (60, 210, 80, 80, 200, "shower", True, True, [(55, 205, 90, 90)])]
        ]
        
        @profile_function
        def run_layout_comparison():
            return compare_room_layouts(
                layouts,
                self.test_data['room_sizes'],
                self.test_data['object_types'],
                self.test_data['windows_doors']
            )
        
        result, execution_time = run_layout_comparison()
        self.results['layout_comparison'] = execution_time
        return result
    
    def profile_space_identification(self):
        """Profile available space identification."""
        print("\n🏠 Profiling Space Identification...")
        
        @profile_function
        def run_space_identification():
            return identify_available_space(
                self.test_data['placed_objects'],
                self.test_data['room_sizes'],
                grid_size=5,  # Using optimized grid size
                windows_doors=self.test_data['windows_doors']
            )
        
        result, execution_time = run_space_identification()
        self.results['space_identification'] = execution_time
        return result
    
    def profile_visualization(self):
        """Profile 2D visualization."""
        print("\n🎨 Profiling 2D Visualization...")
        
        visualizer = Visualizer2D(
            self.test_data['room_sizes'][0],
            self.test_data['room_sizes'][1],
            250
        )
        
        @profile_function
        def run_visualization():
            return visualizer.visualize_pathway_accessibility(
                self.test_data['placed_objects'],
                self.test_data['windows_doors']
            )
        
        result, execution_time = run_visualization()
        self.results['visualization'] = execution_time
        return result
    
    def run_comprehensive_profile(self):
        """Run comprehensive profiling of all key functions."""
        print("🚀 Starting Comprehensive Performance Profiling...")
        print("=" * 60)
        
        total_start = time.time()
        
        # Profile each component
        try:
            self.profile_placement_strategy()
        except Exception as e:
            print(f"❌ Placement strategy profiling failed: {e}")
        
        try:
            self.profile_pathway_accessibility()
        except Exception as e:
            print(f"❌ Pathway accessibility profiling failed: {e}")
        
        try:
            self.profile_layout_evaluation()
        except Exception as e:
            print(f"❌ Layout evaluation profiling failed: {e}")
        
        try:
            self.profile_layout_comparison()
        except Exception as e:
            print(f"❌ Layout comparison profiling failed: {e}")
        
        try:
            self.profile_space_identification()
        except Exception as e:
            print(f"❌ Space identification profiling failed: {e}")
        
        try:
            self.profile_visualization()
        except Exception as e:
            print(f"❌ Visualization profiling failed: {e}")
        
        try:
            self.profile_beam_search()
        except Exception as e:
            print(f"❌ Beam search profiling failed: {e}")
        
        total_time = time.time() - total_start
        
        # Print summary
        print("\n" + "=" * 60)
        print("📈 PERFORMANCE PROFILING SUMMARY")
        print("=" * 60)
        
        for func_name, exec_time in self.results.items():
            percentage = (exec_time / total_time) * 100
            print(f"{func_name:25}: {exec_time:8.4f}s ({percentage:5.1f}%)")
        
        print(f"{'TOTAL TIME':25}: {total_time:8.4f}s (100.0%)")
        
        # Identify bottlenecks
        print("\n🎯 TOP PERFORMANCE BOTTLENECKS:")
        sorted_results = sorted(self.results.items(), key=lambda x: x[1], reverse=True)
        for i, (func_name, exec_time) in enumerate(sorted_results[:3], 1):
            percentage = (exec_time / total_time) * 100
            print(f"{i}. {func_name}: {exec_time:.4f}s ({percentage:.1f}%)")
        
        return self.results

def run_detailed_cprofile():
    """Run detailed cProfile analysis on the most expensive operations."""
    print("\n🔬 Running Detailed cProfile Analysis...")
    
    # Create profiler instance
    profiler = PerformanceProfiler()
    
    # Profile the most expensive operation with cProfile
    pr = cProfile.Profile()
    pr.enable()
    
    try:
        # Run beam search as it's typically the most expensive
        beam_search = BeamSearch(
            profiler.test_data['bathroom'], 
            profiler.test_data['objects_to_place'], 
            beam_width=3
        )
        layouts = beam_search.generate(
            profiler.test_data['objects_to_place'], 
            profiler.test_data['windows_doors']
        )
    except Exception as e:
        print(f"❌ Detailed profiling failed: {e}")
        return
    
    pr.disable()
    
    # Create stats object
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    print("\n📊 DETAILED FUNCTION CALL ANALYSIS (Top 20):")
    print(s.getvalue())

if __name__ == "__main__":
    # Run comprehensive profiling
    profiler = PerformanceProfiler()
    results = profiler.run_comprehensive_profile()
    
    # Run detailed cProfile analysis
    run_detailed_cprofile()
    
    print("\n✅ Profiling completed! Use these results to identify optimization targets.")
