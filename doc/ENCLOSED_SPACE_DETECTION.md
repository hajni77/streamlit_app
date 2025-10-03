# Enclosed Space Detection System

## Overview

The enclosed space detection system identifies **inaccessible areas** in bathroom layouts - spaces that are completely surrounded by objects and cannot be reached from room edges. This is critical for ensuring practical, functional layouts.

## Problem Statement

In bathroom layout generation, objects can sometimes be placed in a way that creates **trapped/enclosed spaces** - areas that are technically free but completely inaccessible because they're surrounded by fixtures.

### Example of Problematic Layout

```
┌─────────────────────────┐
│  toilet  │   shower     │
├──────────┤              │
│          │              │
│  sink    │  [TRAPPED]   │  ← This space is enclosed!
│          │   SPACE      │
│          │              │
└──────────┴──────────────┘
```

## Solution: Flood-Fill Algorithm

The system uses a **flood-fill algorithm** starting from room edges to detect unreachable spaces.

### Algorithm Steps

1. **Create Grid**: Convert room to 10cm×10cm grid cells
2. **Mark Spaces**: Mark available spaces as free (1), objects as occupied (0)
3. **Flood-Fill**: Starting from all room edges, mark all reachable free cells
4. **Detect Enclosed**: Any free cell not reached by flood-fill is enclosed

## Main Function

### `check_enclosed_spaces(spaces_dict, room_width, room_depth, min_distance=20)`

**Purpose**: Detect if any enclosed/inaccessible spaces exist in the layout.

**Parameters**:
- `spaces_dict` (list): List of available space tuples `(x, y, width, depth)`
- `room_width` (int): Room width in cm
- `room_depth` (int): Room depth in cm
- `min_distance` (int): Legacy parameter (not used in new implementation)

**Returns**:
- `bool`: `True` if enclosed spaces detected, `False` otherwise

**Example**:
```python
from algorithms.available_space import check_enclosed_spaces

# Available spaces after object placement
spaces = [
    (0, 0, 100, 80),      # Space 1
    (150, 0, 50, 80),     # Space 2 (isolated)
    (0, 100, 200, 100)    # Space 3
]

has_enclosed = check_enclosed_spaces(spaces, 300, 200)
if has_enclosed:
    print("⚠️ Layout has inaccessible enclosed spaces!")
```

## Debug Function

### `get_enclosed_spaces_debug_info(spaces_dict, room_width, room_depth)`

**Purpose**: Get detailed information about enclosed spaces for visualization and debugging.

**Returns**:
```python
{
    'has_enclosed': bool,              # True if enclosed spaces found
    'grid': list[list[int]],           # 2D grid (1=free, 0=occupied)
    'reachable': list[list[bool]],     # 2D grid (True=reachable, False=enclosed)
    'enclosed_cells': list[tuple],     # List of (x, y) coords of enclosed cells
    'grid_size': int                   # Cell size in cm (default: 10)
}
```

**Example**:
```python
from algorithms.available_space import get_enclosed_spaces_debug_info

debug_info = get_enclosed_spaces_debug_info(spaces, 300, 200)

if debug_info['has_enclosed']:
    print(f"Found {len(debug_info['enclosed_cells'])} enclosed cells")
    print(f"Enclosed cell coordinates: {debug_info['enclosed_cells']}")
    
    # Visualize the grid
    for x in range(len(debug_info['grid'])):
        for y in range(len(debug_info['grid'][0])):
            if debug_info['grid'][x][y] == 1 and not debug_info['reachable'][x][y]:
                print(f"Enclosed cell at grid position ({x}, {y})")
```

## Integration with Scoring System

The enclosed space check is integrated into the bathroom scoring function as a **critical constraint**.

### In `optimization/scoring.py`:

```python
# Line ~270-276
available_space = identify_available_space(
    placed_objects, 
    (room_width, room_depth), 
    grid_size=1, 
    windows_doors=windows_doors
)
available_space_without_shadow = available_space['without_shadow']

if check_enclosed_spaces(available_space_without_shadow, room_width, room_depth):
    scores["enclosed_spaces"] = 0  # Critical failure
else:
    scores["enclosed_spaces"] = 10

# Line ~582
# Critical constraints check
if (scores["no_overlap"] == 0 or 
    scores["wall_corner_constraints"] == 0 or 
    scores["opposite_walls_distance"] < 5 or 
    scores["enclosed_spaces"] == 0 or          # ← Enclosed space check
    scores["shower_space"] == 0):
    total_score = 0  # Layout is invalid
```

## How It Works: Technical Details

### 1. Grid Creation

```python
grid_size = 10  # 10cm cells for performance
grid_width = int(room_width // grid_size)
grid_depth = int(room_depth // grid_size)

# Initialize as all occupied
grid = [[0 for _ in range(grid_depth)] for _ in range(grid_width)]

# Mark available spaces as free
for space in spaces_dict:
    x, y, width, depth = space
    start_x = max(0, int(x // grid_size))
    start_y = max(0, int(y // grid_size))
    end_x = min(grid_width, int((x + depth) // grid_size))
    end_y = min(grid_depth, int((y + width) // grid_size))
    
    for i in range(start_x, end_x):
        for j in range(start_y, end_y):
            grid[i][j] = 1  # Mark as free
```

### 2. Flood-Fill Implementation

Uses **iterative flood-fill** (stack-based) to avoid recursion depth issues:

```python
def flood_fill(x, y):
    """Iterative flood-fill to mark reachable spaces."""
    stack = [(x, y)]
    
    while stack:
        cx, cy = stack.pop()
        
        # Boundary checks
        if cx < 0 or cx >= grid_width or cy < 0 or cy >= grid_depth:
            continue
        if visited[cx][cy] or grid[cx][cy] == 0:
            continue
        
        visited[cx][cy] = True
        
        # Add 4-directional neighbors
        stack.append((cx + 1, cy))  # Right
        stack.append((cx - 1, cy))  # Left
        stack.append((cx, cy + 1))  # Down
        stack.append((cx, cy - 1))  # Up
```

### 3. Edge Starting Points

Flood-fill starts from **all four edges** of the room:

```python
# Top edge (x=0)
for y in range(grid_depth):
    if grid[0][y] == 1:
        flood_fill(0, y)

# Bottom edge (x=grid_width-1)
for y in range(grid_depth):
    if grid[grid_width - 1][y] == 1:
        flood_fill(grid_width - 1, y)

# Left edge (y=0)
for x in range(grid_width):
    if grid[x][0] == 1:
        flood_fill(x, 0)

# Right edge (y=grid_depth-1)
for x in range(grid_width):
    if grid[x][grid_depth - 1] == 1:
        flood_fill(x, grid_depth - 1)
```

**Reason**: Starting from edges ensures we mark all spaces accessible from room entry points (doors are on walls/edges).

### 4. Detection

After flood-fill, any free cell that wasn't visited is enclosed:

```python
for x in range(grid_width):
    for y in range(grid_depth):
        if grid[x][y] == 1 and not visited[x][y]:
            return True  # Found enclosed space!

return False  # No enclosed spaces
```

## Performance Characteristics

- **Time Complexity**: O(W × D) where W and D are room dimensions in grid cells
- **Space Complexity**: O(W × D) for grid and visited arrays
- **Grid Size**: 10cm cells provides good balance between accuracy and performance

### Performance Example

For a 300cm × 200cm room:
- Grid dimensions: 30 × 20 = 600 cells
- Memory: ~2 arrays × 600 cells = ~1.2KB
- Time: < 1ms on modern hardware

## Edge Cases Handled

### 1. No Available Spaces
```python
if len(spaces_dict) < 1:
    return False  # No spaces = no enclosed spaces
```

### 2. All Space Occupied
```python
total_free = sum(sum(row) for row in grid)
if total_free == 0:
    return False  # No free space at all
```

### 3. Spaces at Room Edges
Flood-fill starts from edges, so edge spaces are always marked as reachable.

### 4. Narrow Passages
Uses 4-directional connectivity - passages must be at least 10cm wide (1 grid cell) to be considered accessible.

## Visualization Example

You can visualize enclosed spaces using the debug function:

```python
import matplotlib.pyplot as plt
import numpy as np

def visualize_enclosed_spaces(spaces, room_width, room_depth):
    """Visualize enclosed space detection."""
    debug_info = get_enclosed_spaces_debug_info(spaces, room_width, room_depth)
    
    grid = np.array(debug_info['grid'])
    reachable = np.array(debug_info['reachable'])
    
    # Create visualization
    viz = np.zeros_like(grid, dtype=float)
    viz[grid == 0] = 0.0  # Occupied = black
    viz[(grid == 1) & reachable] = 0.5  # Reachable = gray
    viz[(grid == 1) & ~reachable] = 1.0  # Enclosed = white/red
    
    plt.figure(figsize=(10, 8))
    plt.imshow(viz.T, origin='lower', cmap='RdYlGn_r')
    plt.colorbar(label='0=Occupied, 0.5=Reachable, 1=Enclosed')
    plt.title('Enclosed Space Detection')
    plt.xlabel('X (grid cells)')
    plt.ylabel('Y (grid cells)')
    
    # Mark enclosed cells
    for x, y in debug_info['enclosed_cells']:
        grid_x = x // debug_info['grid_size']
        grid_y = y // debug_info['grid_size']
        plt.plot(grid_x, grid_y, 'rx', markersize=10)
    
    plt.show()
```

## Common Patterns That Create Enclosed Spaces

### 1. Corner Trap
```
┌─────────┐
│ [TRAP]  │
│  ┌──────┤
│  │ obj  │
└──┴──────┘
```

### 2. Center Island
```
┌──────────┐
│  ┌────┐  │
│  │obj │  │  ← Space around object is enclosed
│  └────┘  │
└──────────┘
```

### 3. L-Shape Blockage
```
┌──────────┐
│ obj1     │
├────┐     │
│    │ obj2│  ← Corner space is trapped
└────┴─────┘
```

## Recommendations for Layout Generation

To **prevent enclosed spaces** during layout generation:

1. **Place objects along walls first** - reduces chance of creating islands
2. **Maintain minimum clearances** - ensure pathways between objects
3. **Check accessibility after each placement** - reject placements that create enclosed spaces
4. **Prioritize corner placements** - corners are less likely to create enclosed spaces

## Future Enhancements

1. **Minimum Passage Width**: Configurable minimum width for accessible passages (currently 10cm)
2. **Partial Accessibility Scoring**: Instead of binary pass/fail, score based on percentage of accessible space
3. **Door-Aware Detection**: Start flood-fill specifically from door locations
4. **Multi-Room Support**: Handle bathrooms with separate toilet compartments
5. **3D Accessibility**: Consider height constraints (e.g., space under sinks)

## Related Functions

- `identify_available_space()` - Generates the spaces list used as input
- `BathroomScoringFunction.score()` - Uses enclosed space check for scoring
- `has_free_side()` - Checks if objects have clearance on at least one side

---

**Created**: 2025-10-01  
**Last Updated**: 2025-10-01  
**Related Files**:
- `algorithms/available_space.py` (implementation)
- `optimization/scoring.py` (integration)
- `utils/helpers.py` (helper functions)
