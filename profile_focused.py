"""
Focused performance profiling script for bathroom layout generator.
Only profiles functions actually used in app_modular.py.
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
try:
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
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

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

class FocusedProfiler:
    """Focused profiler for functions actually used in app_modular.py."""
    
    def __init__(self):
        self.results = {}
        self.test_data = self._create_test_data()
    
    def _create_test_data(self):
        """Create standardized test data for consistent profiling."""
        # Load object types
        try:
            with open('object_types.json') as f:
                object_types = json.load(f)
        except FileNotFoundError:
            print("❌ object_types.json not found. Using minimal test data.")
            object_types = {
                "toilet": {"width": [35, 40], "depth": [60, 70], "height": [80, 85]},
                "sink": {"width": [40, 60], "depth": [35, 45], "height": [80, 90]},
                "shower": {"width": [80, 100], "depth": [80, 100], "height": [200, 220]}
            }
        
        # Create test bathroom
        bathroom = Bathroom(300, 300, 250, object_types)  # 3x3m bathroom
        
        # Test objects to place
        objects_to_place = ["toilet", "sink", "shower"]
        
        # Test windows/doors
        windows_doors = [
            WindowsDoors(1, "top", 100, 0, 80, 200, 0, "inwards")  # Door on north wall
        ]
        
        # Sample placed objects for evaluation
        placed_objects = [
            BathroomObject(50, 50, 60, 40, 80, "toilet"),
            BathroomObject(200, 50, 50, 40, 85, "sink"),
            BathroomObject(50, 200, 80, 80, 200, "shower"),
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
        """Profile the beam search algorithm - main bottleneck in app_modular.py."""
        print("\n🔍 Profiling Beam Search Algorithm...")
        
        try:
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
        except Exception as e:
            print(f"❌ Beam search profiling failed: {e}")
            return []
    
    def profile_layout_comparison(self):
        """Profile layout comparison - used in app_modular.py."""
        print("\n🔄 Profiling Layout Comparison...")
        
        try:
            # Create test layouts (simplified format)
            layouts = [
                [self.test_data['placed_objects'][0], self.test_data['placed_objects'][1]],
                [self.test_data['placed_objects'][1], self.test_data['placed_objects'][2]]
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
        except Exception as e:
            print(f"❌ Layout comparison profiling failed: {e}")
            return None
    
    def profile_space_identification(self):
        """Profile available space identification - used in app_modular.py."""
        print("\n🏠 Profiling Space Identification...")
        
        try:
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
        except Exception as e:
            print(f"❌ Space identification profiling failed: {e}")
            return None
    
    def profile_room_validation(self):
        """Profile room validation - used in app_modular.py."""
        print("\n✅ Profiling Room Validation...")
        
        try:
            @profile_function
            def run_room_validation():
                return check_valid_room(self.test_data['placed_objects'])
            
            result, execution_time = run_room_validation()
            self.results['room_validation'] = execution_time
            return result
        except Exception as e:
            print(f"❌ Room validation profiling failed: {e}")
            return False
    
    def profile_visualization_2d(self):
        """Profile 2D visualization - used in app_modular.py."""
        print("\n🎨 Profiling 2D Visualization...")
        
        try:
            visualizer = Visualizer2D(
                self.test_data['room_sizes'][0],
                self.test_data['room_sizes'][1],
                250
            )
            
            @profile_function
            def run_visualization_2d():
                return visualizer.visualize_pathway_accessibility(
                    self.test_data['placed_objects'],
                    self.test_data['windows_doors']
                )
            
            result, execution_time = run_visualization_2d()
            self.results['visualization_2d'] = execution_time
            return result
        except Exception as e:
            print(f"❌ 2D visualization profiling failed: {e}")
            return None
    
    def profile_scoring_function(self):
        """Profile bathroom scoring function - used in beam search."""
        print("\n📊 Profiling Scoring Function...")
        
        try:
            scoring_function = BathroomScoringFunction()
            
            # Create a simple layout for scoring
            layout = Layout(self.test_data['bathroom'].clone(), self.test_data['objects_to_place'])
            for obj in self.test_data['placed_objects'][:2]:  # Add first 2 objects
                layout.bathroom.add_object(obj)
            
            @profile_function
            def run_scoring():
                return scoring_function.evaluate(layout)
            
            result, execution_time = run_scoring()
            self.results['scoring_function'] = execution_time
            return result
        except Exception as e:
            print(f"❌ Scoring function profiling failed: {e}")
            return 0
    
    def run_focused_profile(self):
        """Run focused profiling of functions actually used in app_modular.py."""
        print("🚀 Starting Focused Performance Profiling...")
        print("=" * 60)
        
        total_start = time.time()
        
        # Profile each component actually used in app_modular.py
        self.profile_room_validation()
        self.profile_space_identification()
        self.profile_scoring_function()
        self.profile_layout_comparison()
        self.profile_visualization_2d()
        self.profile_beam_search()  # This is typically the most expensive
        
        total_time = time.time() - total_start
        
        # Print summary
        print("\n" + "=" * 60)
        print("📈 FOCUSED PERFORMANCE PROFILING SUMMARY")
        print("=" * 60)
        
        if self.results:
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
        else:
            print("❌ No profiling results collected")
        
        return self.results

def run_detailed_beam_search_profile():
    """Run detailed cProfile analysis on beam search - the main bottleneck."""
    print("\n🔬 Running Detailed Beam Search cProfile Analysis...")
    
    profiler = FocusedProfiler()
    
    pr = cProfile.Profile()
    pr.enable()
    
    try:
        beam_search = BeamSearch(
            profiler.test_data['bathroom'], 
            profiler.test_data['objects_to_place'], 
            beam_width=3
        )
        layouts = beam_search.generate(
            profiler.test_data['objects_to_place'], 
            profiler.test_data['windows_doors']
        )
        print(f"✅ Generated {len(layouts)} layouts")
    except Exception as e:
        print(f"❌ Detailed beam search profiling failed: {e}")
        pr.disable()
        return
    
    pr.disable()
    
    # Create stats object
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(15)  # Top 15 functions
    
    print("\n📊 DETAILED BEAM SEARCH ANALYSIS (Top 15):")
    print(s.getvalue())

if __name__ == "__main__":
    print("🎯 Focused Performance Profiler for app_modular.py")
    print("Only profiling functions actually used in the main application\n")
    
    # Run focused profiling
    profiler = FocusedProfiler()
    results = profiler.run_focused_profile()
    
    # Run detailed beam search analysis if it worked
    if 'beam_search' in results:
        run_detailed_beam_search_profile()
    
    print("\n✅ Focused profiling completed!")
    print("💡 Use these results to optimize the most impactful functions first.")
