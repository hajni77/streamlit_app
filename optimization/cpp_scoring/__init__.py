"""
C++ Bathroom Scoring Module

High-performance C++ implementation of the bathroom layout scoring function
with pybind11 bindings for seamless Python integration.

This package provides:
- BathroomScoringFunction: C++ scoring class
- PlacedObject: Structure for placed objects
- WindowDoor: Structure for windows/doors
- RoomSize: Structure for room dimensions
- CppBathroomScoringWrapper: Python wrapper for easy integration

Usage:
    # Direct C++ usage
    import cpp_bathroom_scoring as cpp_scoring
    scorer = cpp_scoring.BathroomScoringFunction()
    score, breakdown = scorer.score(objects, doors, room, requested)
    
    # Python wrapper (drop-in replacement)
    from optimization.cpp_scoring.python_wrapper import CppBathroomScoringWrapper
    scorer = CppBathroomScoringWrapper()
    score, breakdown = scorer.score(layout)
"""

__version__ = "1.0.0"
__author__ = "Bathroom Layout Generator Team"

# Try to import the C++ module
try:
    from . import cpp_bathroom_scoring
    CPP_AVAILABLE = True
    
    # Re-export main classes for convenience
    BathroomScoringFunction = cpp_bathroom_scoring.BathroomScoringFunction
    PlacedObject = cpp_bathroom_scoring.PlacedObject
    WindowDoor = cpp_bathroom_scoring.WindowDoor
    RoomSize = cpp_bathroom_scoring.RoomSize
    Rectangle = cpp_bathroom_scoring.Rectangle
    AvailableSpace = cpp_bathroom_scoring.AvailableSpace
    
    create_placed_object_from_dict = cpp_bathroom_scoring.create_placed_object_from_dict
    create_window_door_from_dict = cpp_bathroom_scoring.create_window_door_from_dict
    
except ImportError as e:
    CPP_AVAILABLE = False
    import warnings
    warnings.warn(
        f"C++ bathroom scoring module not available: {e}\n"
        "The module needs to be built first. Run: pip install . in the cpp_scoring directory",
        ImportWarning
    )

# Always import the Python wrapper (doesn't require C++ module to be imported)
try:
    from .python_wrapper import (
        CppBathroomScoringWrapper,
        get_cpp_scorer,
        is_cpp_available,
        benchmark_comparison
    )
except ImportError:
    pass

__all__ = [
    'CPP_AVAILABLE',
    'BathroomScoringFunction',
    'PlacedObject',
    'WindowDoor',
    'RoomSize',
    'Rectangle',
    'AvailableSpace',
    'CppBathroomScoringWrapper',
    'get_cpp_scorer',
    'is_cpp_available',
    'benchmark_comparison',
    'create_placed_object_from_dict',
    'create_window_door_from_dict',
]
