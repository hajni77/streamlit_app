# Object Enlargement and Shifting System

## Overview

The `try_enlarge_and_shift()` function provides intelligent object resizing with automatic collision resolution through object shifting. This is particularly useful for optimizing bathroom layouts by maximizing fixture sizes while maintaining valid placements.

## Main Function

### `try_enlarge_and_shift(target_obj_entry, bathroom, max_width_increase=50, max_depth_increase=50, shift_step=5)`

**Purpose**: Attempts to enlarge a bathroom fixture (width and depth) and automatically shifts blocking objects when necessary.

**Parameters**:
- `target_obj_entry` (dict): The object entry to enlarge (must contain 'object' key)
- `bathroom`: The Bathroom instance containing all placed objects
- `max_width_increase` (float): Maximum width increase in cm (default: 50)
- `max_depth_increase` (float): Maximum depth increase in cm (default: 50)
- `shift_step` (float): Granularity for enlargement and shifting in cm (default: 5)

**Returns**:
- `success` (bool): True if any enlargement occurred
- `new_width` (float): Final width after enlargement
- `new_depth` (float): Final depth after enlargement
- `shifted_objects` (list): List of tuples `(obj_entry, old_pos, new_pos)` for each shifted object

## How It Works

### 1. **Incremental Enlargement**
The function enlarges the target object incrementally (by `shift_step` cm at a time):
- First attempts to increase **width**
- Then attempts to increase **depth**
- Stops when constraints are hit or blocking objects cannot be shifted

### 2. **Collision Detection**
Uses `_check_collision()` to detect overlaps between:
- Object bodies
- Shadow spaces (clearance zones around objects)
- Combinations of both

### 3. **Automatic Shifting**
When a blocking object is detected:
- Calculates the optimal shift direction (away from the enlarging object)
- Attempts to shift in increments up to `max_shift` distance (default: 100cm)
- Validates the new position against all other objects
- Reverts if shifting is not possible

### 4. **Constraint Validation**
Respects all placement rules:
- Room boundaries
- Object size constraints from `object_types.json`
- Window/door clearances
- Shadow space requirements
- Wall/corner constraints

## Usage Examples

### Example 1: Basic Usage
```python
# Get the bathtub object entry
bathtub_entry = next(
    (e for e in bathroom.objects if e['object'].name == 'bathtub'),
    None
)

if bathtub_entry:
    success, new_w, new_d, shifts = try_enlarge_and_shift(
        bathtub_entry, 
        bathroom,
        max_width_increase=40,
        max_depth_increase=40
    )
    
    if success:
        print(f"✓ Bathtub enlarged to {new_w}x{new_d}cm")
        print(f"✓ Shifted {len(shifts)} objects")
        for obj_entry, old_pos, new_pos in shifts:
            obj_name = obj_entry['object'].name
            print(f"  - {obj_name}: {old_pos} → {new_pos}")
    else:
        print("✗ Could not enlarge bathtub")
```

### Example 2: Optimize All Fixtures
```python
def optimize_all_fixtures(bathroom, target_fixtures=['bathtub', 'sink', 'double sink']):
    """Attempt to enlarge all target fixtures in the bathroom."""
    results = {}
    
    for fixture_name in target_fixtures:
        # Find the fixture
        fixture_entry = next(
            (e for e in bathroom.objects 
             if e.get('object') and e['object'].name == fixture_name),
            None
        )
        
        if fixture_entry:
            success, new_w, new_d, shifts = try_enlarge_and_shift(
                fixture_entry,
                bathroom,
                max_width_increase=50,
                max_depth_increase=50,
                shift_step=5
            )
            
            results[fixture_name] = {
                'success': success,
                'new_size': (new_w, new_d) if success else None,
                'objects_shifted': len(shifts)
            }
    
    return results
```

### Example 3: Integration with Layout Scoring
```python
from optimization.scoring import BathroomScoringFunction

def optimize_and_score(layout):
    """Optimize fixture sizes and calculate new score."""
    bathroom = layout.bathroom
    
    # Get initial score
    scorer = BathroomScoringFunction()
    initial_score = scorer.score(layout)
    
    # Try to enlarge bathtub
    bathtub_entry = next(
        (e for e in bathroom.objects if e['object'].name == 'bathtub'),
        None
    )
    
    if bathtub_entry:
        success, new_w, new_d, shifts = try_enlarge_and_shift(
            bathtub_entry,
            bathroom,
            max_width_increase=30,
            max_depth_increase=30
        )
        
        if success:
            # Recalculate score
            new_score = scorer.score(layout)
            
            if new_score > initial_score:
                print(f"✓ Optimization improved score: {initial_score} → {new_score}")
                return layout, new_score
            else:
                # Revert changes
                bathtub_entry['object'].width = new_w - (new_w - bathtub_entry['object'].width)
                bathtub_entry['object'].depth = new_d - (new_d - bathtub_entry['object'].depth)
                for obj_entry, old_pos, new_pos in shifts:
                    obj_entry['object'].position = old_pos
                print("✗ Optimization decreased score, reverted")
    
    return layout, initial_score
```

## Helper Functions

### `_can_place_with_shift(new_rect, target_entry, bathroom, shadow_space, door_walls, windows_doors, shifted_objects, shift_step=5, max_shift=100)`

Validates placement and attempts to shift blocking objects.

**Key Features**:
- Checks room boundaries
- Validates against windows/doors
- Detects collisions with other objects
- Automatically shifts blocking objects
- Tracks all shifts in `shifted_objects` list

### `_check_collision(x1, y1, w1, d1, shadow1, x2, y2, w2, d2, shadow2)`

Comprehensive collision detection including shadow spaces.

**Returns**: `True` if any overlap is detected between:
- Object 1 body ↔ Object 2 body
- Object 1 shadow ↔ Object 2 body
- Object 1 body ↔ Object 2 shadow

### `_try_shift_object(obj_entry, blocking_rect, bathroom, other_objects, shift_step=5, max_shift=100)`

Attempts to shift an object away from a blocking rectangle.

**Algorithm**:
1. Calculate center points of both objects
2. Determine optimal shift direction (away from blocker)
3. Try incremental shifts up to `max_shift` distance
4. Validate each position against all other objects
5. Return first valid position found

## Integration Points

### With Reinforcement Learning Agent

This function can be used as an **action** in an RL environment:

```python
class BathroomLayoutEnv:
    def step(self, action):
        """
        Actions:
        - 0-N: Move object N
        - N+1-2N: Resize object N (using try_enlarge_and_shift)
        - 2N+1-3N: Swap objects
        """
        if action in resize_actions:
            obj_idx = action - len(move_actions)
            obj_entry = self.bathroom.objects[obj_idx]
            
            success, new_w, new_d, shifts = try_enlarge_and_shift(
                obj_entry,
                self.bathroom,
                max_width_increase=20,
                max_depth_increase=20
            )
            
            # Calculate reward based on new layout score
            reward = self.calculate_reward()
            
            return self.get_state(), reward, False, {}
```

### With Optimization Pipeline

```python
def post_placement_optimization(layout):
    """Run after initial placement to maximize fixture sizes."""
    bathroom = layout.bathroom
    
    # Priority order: larger fixtures first
    priority_fixtures = ['bathtub', 'double sink', 'sink', 'shower']
    
    for fixture_name in priority_fixtures:
        fixture_entry = next(
            (e for e in bathroom.objects if e['object'].name == fixture_name),
            None
        )
        
        if fixture_entry:
            try_enlarge_and_shift(
                fixture_entry,
                bathroom,
                max_width_increase=50,
                max_depth_increase=50
            )
    
    return layout
```

## Performance Considerations

- **Time Complexity**: O(n × m × k) where:
  - n = number of enlargement steps
  - m = number of objects in bathroom
  - k = number of shift attempts per blocking object

- **Optimization Tips**:
  - Use larger `shift_step` (e.g., 10cm) for faster but coarser results
  - Reduce `max_shift` to limit search space
  - Process fixtures in priority order (largest/most important first)

## Constraints and Limitations

1. **Wall/Corner Constraints**: Objects with `must_be_against_wall` or `must_be_corner` cannot be shifted away from their required positions

2. **Cascading Shifts**: Currently shifts one object at a time; doesn't handle cascading shifts (shifting A to make room, which requires shifting B, etc.)

3. **Rotation**: Does not attempt to rotate objects; only shifts positions

4. **Reversibility**: Changes are applied immediately; caller must manually revert if needed

## Future Enhancements

1. **Cascading Shift Support**: Allow multi-level shifting chains
2. **Rotation Attempts**: Try rotating objects before giving up
3. **Smart Prioritization**: Prefer shifting smaller/less important objects
4. **Undo Stack**: Built-in rollback mechanism
5. **Parallel Optimization**: Optimize multiple objects simultaneously

## Related Functions

- `optimize_object_sizes()`: Existing optimization function (lines 1516+)
- `is_valid_placement()`: Core placement validation (line 847)
- `check_overlap()`: Rectangle overlap detection (line 591)
- `has_free_side()`: Check if object has clearance (line 1744)

---

**Created**: 2025-10-01  
**Last Updated**: 2025-10-01  
**Related Files**: 
- `utils/helpers.py` (implementation)
- `optimization/scoring.py` (scoring integration)
- `algorithms/placement.py` (placement logic)
