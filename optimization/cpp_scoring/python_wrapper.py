"""
Python wrapper for the C++ bathroom scoring module.

This module provides a convenient wrapper that allows the C++ scoring function
to be used as a drop-in replacement for the Python version.
"""

import sys
import os

# Add the parent directory to the path to import the C++ module
sys.path.insert(0, os.path.dirname(__file__))

try:
    import cpp_bathroom_scoring as cpp_scoring
    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False
    print("Warning: C++ scoring module not available. Using Python fallback.")


class CppBathroomScoringWrapper:
    """
    Wrapper to use C++ scorer with Python Layout objects.
    
    This class provides a seamless interface between Python Layout objects
    and the C++ scoring implementation.
    
    Example:
        >>> from optimization.cpp_scoring.python_wrapper import CppBathroomScoringWrapper
        >>> scorer = CppBathroomScoringWrapper()
        >>> total_score, breakdown = scorer.score(layout)
    """
    
    def __init__(self):
        """Initialize the C++ scoring function."""
        if not CPP_AVAILABLE:
            raise ImportError(
                "C++ scoring module is not available. "
                "Please build and install it first using 'pip install .' "
                "in the cpp_scoring directory."
            )
        self.cpp_scorer = cpp_scoring.BathroomScoringFunction()
        self.total_score = 0.0
        self.score_breakdown = {}
    
    def _convert_placed_object(self, obj):
        """
        Convert a Python object to a C++ PlacedObject.
        
        Args:
            obj: Python object with position, dimensions, and properties
        
        Returns:
            cpp_scoring.PlacedObject: C++ object
        """
        cpp_obj = cpp_scoring.PlacedObject()
        cpp_obj.x = float(obj.position[0])
        cpp_obj.y = float(obj.position[1])
        cpp_obj.width = float(obj.width)
        cpp_obj.depth = float(obj.depth)
        cpp_obj.height = float(obj.height)
        cpp_obj.name = str(obj.name)
        cpp_obj.wall = str(obj.wall)
        cpp_obj.must_be_corner = bool(getattr(obj, 'must_be_corner', False))
        cpp_obj.must_be_against_wall = bool(getattr(obj, 'must_be_against_wall', False))
        
        # Handle shadow - ensure it's a tuple of 4 floats
        shadow = getattr(obj, 'shadow', (0, 0, 0, 0))
        if isinstance(shadow, (list, tuple)) and len(shadow) >= 4:
            cpp_obj.shadow = (float(shadow[0]), float(shadow[1]), 
                            float(shadow[2]), float(shadow[3]))
        else:
            cpp_obj.shadow = (0.0, 0.0, 0.0, 0.0)
        
        return cpp_obj
    
    def _convert_window_door(self, wd):
        """
        Convert a Python window/door to a C++ WindowDoor.
        
        Args:
            wd: Python window/door object
        
        Returns:
            cpp_scoring.WindowDoor: C++ window/door object
        """
        cpp_wd = cpp_scoring.WindowDoor()
        cpp_wd.x = float(wd.position[0])
        cpp_wd.y = float(wd.position[1])
        cpp_wd.width = float(wd.width)
        cpp_wd.depth = float(wd.depth)
        cpp_wd.height = float(wd.height)
        cpp_wd.name = str(wd.name)
        cpp_wd.wall = str(wd.wall)
        cpp_wd.hinge = str(getattr(wd, 'hinge', 'left'))
        cpp_wd.way = str(getattr(wd, 'way', 'inward'))
        return cpp_wd
    
    def score(self, layout):
        """
        Score a bathroom layout using the C++ implementation.
        
        Args:
            layout: Layout object containing bathroom with placed objects,
                   windows/doors, and room dimensions
        
        Returns:
            tuple: (total_score: float, score_breakdown: dict)
        
        Raises:
            ValueError: If layout is missing required attributes
        """
        # Extract data from layout
        if not hasattr(layout, "bathroom"):
            raise ValueError("Layout object must have a 'bathroom' attribute.")
        
        bathroom = layout.bathroom
        
        # Get placed objects
        if not hasattr(bathroom, "get_placed_objects"):
            raise ValueError("Bathroom must have 'get_placed_objects' method.")
        
        placed_objects_py = bathroom.get_placed_objects() or []
        windows_doors_py = getattr(bathroom, "windows_doors", []) or []
        
        # Get room size
        if not hasattr(bathroom, "get_size"):
            raise ValueError("Bathroom must have 'get_size' method.")
        
        room_size = bathroom.get_size()
        requested_objects = getattr(layout, "requested_objects", []) or []
        
        # Convert to C++ objects
        placed_objects_cpp = []
        for obj_entry in placed_objects_py:
            obj = obj_entry["object"]
            cpp_obj = self._convert_placed_object(obj)
            placed_objects_cpp.append(cpp_obj)
        
        windows_doors_cpp = []
        for wd in windows_doors_py:
            cpp_wd = self._convert_window_door(wd)
            windows_doors_cpp.append(cpp_wd)
        
        room_cpp = cpp_scoring.RoomSize(
            float(room_size[0]),
            float(room_size[1]),
            float(room_size[2])
        )
        
        # Score using C++
        self.total_score, self.score_breakdown = self.cpp_scorer.score(
            placed_objects_cpp,
            windows_doors_cpp,
            room_cpp,
            requested_objects
        )
        
        return self.total_score, self.score_breakdown
    
    def evaluate(self, layout, requested_objects=None, windows_doors=None):
        """
        Evaluate the layout (compatibility method).
        
        This method provides compatibility with the Python scoring function API.
        
        Args:
            layout: Layout object
            requested_objects: Optional list of requested objects (ignored, uses layout.requested_objects)
            windows_doors: Optional windows/doors (ignored, uses layout.bathroom.windows_doors)
        
        Returns:
            tuple: (total_score: float, score_breakdown: dict)
        """
        return self.score(layout)


def get_cpp_scorer():
    """
    Factory function to get a C++ scorer instance.
    
    Returns:
        CppBathroomScoringWrapper: Wrapper instance
    
    Raises:
        ImportError: If C++ module is not available
    """
    return CppBathroomScoringWrapper()


def is_cpp_available():
    """
    Check if the C++ scoring module is available.
    
    Returns:
        bool: True if C++ module is available, False otherwise
    """
    return CPP_AVAILABLE


def benchmark_comparison(layout, iterations=100):
    """
    Benchmark C++ vs Python scoring implementations.
    
    Args:
        layout: Layout object to score
        iterations: Number of iterations for benchmarking
    
    Returns:
        dict: Benchmark results with timing information
    """
    import time
    
    # Import Python scorer
    from optimization.scoring import BathroomScoringFunction as PythonScorer
    
    if not CPP_AVAILABLE:
        print("C++ module not available for benchmarking")
        return None
    
    # Python benchmark
    python_scorer = PythonScorer()
    python_start = time.time()
    for _ in range(iterations):
        python_scorer.score(layout)
    python_time = time.time() - python_start
    
    # C++ benchmark
    cpp_scorer = CppBathroomScoringWrapper()
    cpp_start = time.time()
    for _ in range(iterations):
        cpp_scorer.score(layout)
    cpp_time = time.time() - cpp_start
    
    # Results
    speedup = python_time / cpp_time if cpp_time > 0 else float('inf')
    
    results = {
        'iterations': iterations,
        'python_time': python_time,
        'cpp_time': cpp_time,
        'python_avg': python_time / iterations,
        'cpp_avg': cpp_time / iterations,
        'speedup': speedup
    }
    
    print(f"\nBenchmark Results ({iterations} iterations):")
    print(f"  Python total: {python_time:.4f}s (avg: {results['python_avg']*1000:.2f}ms)")
    print(f"  C++ total:    {cpp_time:.4f}s (avg: {results['cpp_avg']*1000:.2f}ms)")
    print(f"  Speedup:      {speedup:.1f}x")
    
    return results


if __name__ == "__main__":
    # Test the wrapper
    if CPP_AVAILABLE:
        print(f"C++ Bathroom Scoring Module v{cpp_scoring.__version__}")
        print(f"Author: {cpp_scoring.__author__}")
        print("\nModule loaded successfully!")
        
        # Create a simple test
        scorer = cpp_scoring.BathroomScoringFunction()
        
        sink = cpp_scoring.PlacedObject()
        sink.name = "sink"
        sink.x, sink.y = 0, 100
        sink.width, sink.depth, sink.height = 60, 50, 85
        sink.wall = "top"
        sink.shadow = (60, 0, 0, 0)
        
        door = cpp_scoring.WindowDoor()
        door.name = "door"
        door.x, door.y = 150, 0
        door.width, door.depth, door.height = 80, 10, 210
        door.wall = "left"
        door.hinge = "left"
        
        room = cpp_scoring.RoomSize(300, 250, 270)
        
        score, breakdown = scorer.score([sink], [door], room, ["sink"])
        
        print(f"\nTest Score: {score:.2f}")
        print(f"Breakdown: {breakdown}")
    else:
        print("C++ module not available. Please build it first.")
        print("Run: pip install . in the cpp_scoring directory")
