"""
Test script for the C++ bathroom scoring module.

This script tests the C++ implementation and compares it with the Python version.
"""

import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    import cpp_bathroom_scoring as cpp_scoring
    from python_wrapper import CppBathroomScoringWrapper, is_cpp_available
    CPP_AVAILABLE = True
except ImportError as e:
    print(f"Error importing C++ module: {e}")
    print("Please build the module first with: pip install .")
    CPP_AVAILABLE = False
    sys.exit(1)


def test_basic_functionality():
    """Test basic functionality of the C++ module."""
    print("\n" + "="*60)
    print("TEST 1: Basic Functionality")
    print("="*60)
    
    scorer = cpp_scoring.BathroomScoringFunction()
    
    # Create a simple layout
    sink = cpp_scoring.PlacedObject()
    sink.name = "sink"
    sink.x, sink.y = 0, 100
    sink.width, sink.depth, sink.height = 60, 50, 85
    sink.wall = "top"
    sink.shadow = (60, 0, 0, 0)
    
    toilet = cpp_scoring.PlacedObject()
    toilet.name = "toilet"
    toilet.x, toilet.y = 200, 0
    toilet.width, toilet.depth, toilet.height = 50, 60, 75
    toilet.wall = "left"
    toilet.shadow = (60, 0, 0, 0)
    
    door = cpp_scoring.WindowDoor()
    door.name = "door"
    door.x, door.y = 150, 0
    door.width, door.depth, door.height = 80, 10, 210
    door.wall = "left"
    door.hinge = "left"
    
    room = cpp_scoring.RoomSize(300, 250, 270)
    
    placed_objects = [sink, toilet]
    windows_doors = [door]
    requested_objects = ["sink", "toilet"]
    
    score, breakdown = scorer.score(placed_objects, windows_doors, room, requested_objects)
    
    print(f"[OK] Total Score: {score:.2f}")
    print(f"[OK] Score Components: {len(breakdown)}")
    print(f"\nScore Breakdown:")
    for key, value in sorted(breakdown.items()):
        print(f"  {key:30s}: {value:6.2f}")
    
    assert isinstance(score, float), "Score should be a float"
    assert isinstance(breakdown, dict), "Breakdown should be a dict"
    assert score >= 0, "Score should be non-negative"
    
    print("\n[OK] Test PASSED")
    return True


def test_empty_layout():
    """Test with an empty layout."""
    print("\n" + "="*60)
    print("TEST 2: Empty Layout")
    print("="*60)
    
    scorer = cpp_scoring.BathroomScoringFunction()
    room = cpp_scoring.RoomSize(300, 250, 270)
    
    score, breakdown = scorer.score([], [], room, [])
    
    print(f"[OK] Score for empty layout: {score:.2f}")
    assert score == 0, "Empty layout should have score of 0"
    
    print("[OK] Test PASSED")
    return True


def test_large_layout():
    """Test with a larger, more complex layout."""
    print("\n" + "="*60)
    print("TEST 3: Large Complex Layout")
    print("="*60)
    
    scorer = cpp_scoring.BathroomScoringFunction()
    
    # Create multiple objects
    objects = []
    
    # Sink
    sink = cpp_scoring.PlacedObject()
    sink.name = "sink"
    sink.x, sink.y = 0, 50
    sink.width, sink.depth, sink.height = 80, 50, 85
    sink.wall = "top"
    sink.shadow = (60, 0, 0, 0)
    objects.append(sink)
    
    # Toilet
    toilet = cpp_scoring.PlacedObject()
    toilet.name = "toilet"
    toilet.x, toilet.y = 0, 150
    toilet.width, toilet.depth, toilet.height = 50, 60, 75
    toilet.wall = "top-left"
    toilet.shadow = (60, 0, 0, 0)
    objects.append(toilet)
    
    # Bathtub
    bathtub = cpp_scoring.PlacedObject()
    bathtub.name = "bathtub"
    bathtub.x, bathtub.y = 250, 0
    bathtub.width, bathtub.depth, bathtub.height = 170, 80, 60
    bathtub.wall = "bottom"
    bathtub.shadow = (0, 0, 0, 60)
    objects.append(bathtub)
    
    # Shower
    shower = cpp_scoring.PlacedObject()
    shower.name = "shower"
    shower.x, shower.y = 250, 200
    shower.width, shower.depth, shower.height = 100, 80, 220
    shower.wall = "bottom-right"
    shower.shadow = (0, 0, 0, 0)
    objects.append(shower)
    
    # Door
    door = cpp_scoring.WindowDoor()
    door.name = "door"
    door.x, door.y = 100, 0
    door.width, door.depth, door.height = 80, 10, 210
    door.wall = "left"
    door.hinge = "left"
    
    room = cpp_scoring.RoomSize(350, 300, 270)
    requested = ["sink", "toilet", "bathtub", "shower"]
    
    score, breakdown = scorer.score(objects, [door], room, requested)
    
    print(f"[OK] Total Score: {score:.2f}")
    print(f"[OK] Number of objects: {len(objects)}")
    print(f"\nTop 5 Score Components:")
    sorted_breakdown = sorted(breakdown.items(), key=lambda x: abs(x[1]), reverse=True)
    for key, value in sorted_breakdown[:5]:
        print(f"  {key:30s}: {value:6.2f}")
    
    print("\n[OK] Test PASSED")
    return True


def test_helper_functions():
    """Test helper functions."""
    print("\n" + "="*60)
    print("TEST 4: Helper Functions")
    print("="*60)
    
    # Test create_placed_object_from_dict
    obj_dict = {
        "x": 0,
        "y": 100,
        "width": 60,
        "depth": 50,
        "height": 85,
        "name": "sink",
        "wall": "top",
        "must_be_corner": False,
        "must_be_against_wall": True,
        "shadow": (60, 0, 0, 0)
    }
    
    obj = cpp_scoring.create_placed_object_from_dict(obj_dict)
    
    assert obj.name == "sink", "Name should match"
    assert obj.x == 0, "X should match"
    assert obj.width == 60, "Width should match"
    
    print("[OK] create_placed_object_from_dict works")
    
    # Test create_window_door_from_dict
    wd_dict = {
        "x": 150,
        "y": 0,
        "width": 80,
        "depth": 10,
        "height": 210,
        "name": "door",
        "wall": "left",
        "hinge": "left",
        "way": "inward"
    }
    
    wd = cpp_scoring.create_window_door_from_dict(wd_dict)
    
    assert wd.name == "door", "Name should match"
    assert wd.wall == "left", "Wall should match"
    
    print("[OK] create_window_door_from_dict works")
    print("\n[OK] Test PASSED")
    return True


def test_module_info():
    """Test module information."""
    print("\n" + "="*60)
    print("TEST 5: Module Information")
    print("="*60)
    
    print(f"[OK] Module version: {cpp_scoring.__version__}")
    print(f"[OK] Module author: {cpp_scoring.__author__}")
    print(f"[OK] C++ available: {is_cpp_available()}")
    
    print("\n[OK] Test PASSED")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("C++ BATHROOM SCORING MODULE - TEST SUITE")
    print("="*60)
    
    tests = [
        test_module_info,
        test_basic_functionality,
        test_empty_layout,
        test_large_layout,
        test_helper_functions,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n[FAIL] Test FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n[OK] ALL TESTS PASSED!")
        return True
    else:
        print(f"\n[FAIL] {failed} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    if not CPP_AVAILABLE:
        print("C++ module not available. Cannot run tests.")
        sys.exit(1)
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
