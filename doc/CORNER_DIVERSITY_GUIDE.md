# Bathtub/Shower Corner Diversity System

## Overview

The beam search algorithm now ensures **diversity in bathtub and shower corner placements** across the final layout results. This guarantees that users see at least **4 different corner placement options** for their bathtub or shower.

## Problem Statement

Without diversity enforcement, beam search might return 10 layouts where the bathtub/shower is always in the same corner (e.g., all in top-left). This limits user choice and doesn't showcase the full range of possible layouts.

## Solution: Corner Diversity Enforcement

### **New Methods**

#### 1. `get_bathtub_shower_corner(layout)`
Located in `algorithms/beam_search.py` (lines 44-81)

**Purpose**: Determines which corner contains the bathtub or shower.

**Returns**:
- `'top_left'` - Object in top-left corner
- `'top_right'` - Object in top-right corner  
- `'bottom_left'` - Object in bottom-left corner
- `'bottom_right'` - Object in bottom-right corner
- `None` - No bathtub/shower or not in a corner

**Algorithm**:
```python
# Calculate object center
center_x = x + depth / 2
center_y = y + width / 2

# Use 1/3 room threshold to determine corner
threshold_x = room_width / 3
threshold_y = room_depth / 3

# Example: Top-left corner
if center_x < threshold_x and center_y < threshold_y:
    return 'top_left'
```

**Why 1/3 threshold?**
- More lenient than 1/4 (allows objects slightly away from exact corner)
- Stricter than 1/2 (ensures it's actually in corner region)
- Works well for typical bathroom dimensions

#### 2. `_ensure_corner_diversity(layouts, min_different_corners=4)`
Located in `algorithms/beam_search.py` (lines 43-113)

**Purpose**: Selects 10 layouts ensuring at least 4 different corner placements.

**Strategy** (4 phases):

##### **Phase 1: One from Each Corner**
```python
# Get the best scoring layout from each corner
for corner in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
    if corner_to_layouts[corner]:
        selected.append(corner_to_layouts[corner][0])  # Best from this corner
```

**Result**: Up to 4 layouts (one per corner)

##### **Phase 2: Fill Missing Corners**
```python
# If we have less than 4 corners covered, try to get more
if len(corners_covered) < min_different_corners:
    # Add more layouts from uncovered corners
```

**Result**: Ensures minimum diversity requirement

##### **Phase 3: Second-Best from Each Corner**
```python
# Add second-best from each corner to increase diversity
for corner in corners:
    if len(corner_to_layouts[corner]) > 1:
        selected.append(corner_to_layouts[corner][1])
```

**Result**: 4-8 layouts (2 per corner if available)

##### **Phase 4: Fill with Best Scores**
```python
# Fill remaining slots (up to 10) with best overall scores
for layout in layouts:
    if layout not in selected:
        selected.append(layout)
```

**Result**: Exactly 10 layouts total

### **Integration**

Modified in `algorithms/beam_search.py` (lines 221-228):

```python
# OLD: Simple top-10 selection
beam = beam_temp[:10]

# NEW: Diversity-aware selection
beam = self._ensure_corner_diversity(beam_temp, min_different_corners=4)

# Fallback: Fill if needed
if len(beam) < 10:
    remaining = [l for l in beam_temp if l not in beam]
    beam.extend(remaining[:10 - len(beam)])
```

## How It Works: Example

### Input: 30 candidate layouts
```
Candidates sorted by score:
1. Score 95 - bathtub in top_left
2. Score 94 - bathtub in top_left
3. Score 93 - bathtub in bottom_right
4. Score 92 - bathtub in top_right
5. Score 91 - bathtub in top_left
6. Score 90 - bathtub in bottom_left
7. Score 89 - bathtub in top_right
8. Score 88 - bathtub in bottom_right
9. Score 87 - bathtub in top_left
10. Score 86 - bathtub in bottom_left
... (20 more)
```

### Without Diversity Enforcement:
```
Top 10 selected:
1-5: All top_left (scores 95, 94, 91, 87, ...)
6-7: bottom_right (scores 93, 88)
8-9: top_right (scores 92, 89)
10: bottom_left (score 90)

Result: Only 4 different corners, but heavily biased to top_left
```

### With Diversity Enforcement:
```
Phase 1 - Best from each corner:
✓ #1 (95) - top_left
✓ #4 (92) - top_right  
✓ #3 (93) - bottom_right
✓ #6 (90) - bottom_left

Phase 2 - Already have 4 corners: SKIP

Phase 3 - Second-best from each corner:
✓ #2 (94) - top_left (2nd best)
✓ #7 (89) - top_right (2nd best)
✓ #8 (88) - bottom_right (2nd best)
✓ #10 (86) - bottom_left (2nd best)

Phase 4 - Fill remaining 2 slots:
✓ #5 (91) - top_left (3rd best overall)
✓ #9 (87) - top_left (4th best overall)

Final Result: 10 layouts with guaranteed 4 different corners
- top_left: 4 layouts
- top_right: 2 layouts
- bottom_right: 2 layouts
- bottom_left: 2 layouts
```

## Benefits

### 1. **User Choice**
Users see bathtub/shower in all 4 corners, allowing them to choose based on:
- Personal preference
- Plumbing location
- Window placement
- Door swing direction

### 2. **Better Exploration**
Beam search explores more of the solution space instead of converging on one corner.

### 3. **Balanced Results**
Even if one corner scores slightly higher, users still see other options.

### 4. **Maintains Quality**
Still prioritizes high-scoring layouts - just ensures diversity within those high scores.

## Configuration

### Adjust Minimum Corners
```python
# In beam_search.py, line 223
beam = self._ensure_corner_diversity(beam_temp, min_different_corners=4)

# Options:
min_different_corners=2  # Relaxed (at least 2 corners)
min_different_corners=3  # Moderate (at least 3 corners)
min_different_corners=4  # Strict (all 4 corners) ← DEFAULT
```

### Adjust Corner Threshold
```python
# In get_bathtub_shower_corner(), lines 69-70
threshold_x = room_width / 3  # Current: 1/3
threshold_y = room_depth / 3

# Options:
threshold = room_width / 4  # Stricter (must be very close to corner)
threshold = room_width / 2.5  # Moderate
threshold = room_width / 3  # Balanced ← DEFAULT
threshold = room_width / 2  # Relaxed (anywhere in that half)
```

## Edge Cases Handled

### 1. **Not Enough Corners**
If candidates only have 2 different corners:
```python
# Phase 2 tries to find more, but if unavailable:
# Phases 3-4 fill with best available layouts
```

### 2. **No Bathtub/Shower**
If layout doesn't have bathtub or shower:
```python
corner = self.get_bathtub_shower_corner(layout)
# Returns None
# These layouts grouped separately and can still be selected in Phase 4
```

### 3. **Bathtub Not in Corner**
If bathtub is in center of room:
```python
# get_bathtub_shower_corner() returns None
# Layout treated as "no corner placement"
```

### 4. **Fewer Than 10 Candidates**
```python
if len(beam) < 10:
    remaining = [l for l in beam_temp if l not in beam]
    beam.extend(remaining[:10 - len(beam)])
# Fills with whatever is available
```

## Testing

### Test Corner Detection
```python
from algorithms.beam_search import BeamSearch

bs = BeamSearch(bathroom, object_types)

# Test on a layout
corner = bs.get_bathtub_shower_corner(layout)
print(f"Bathtub/Shower in: {corner}")
```

### Test Diversity
```python
# After generation
layouts = bs.generate(objects, windows_doors)

# Check corner distribution
corners = {}
for layout in layouts:
    corner = bs.get_bathtub_shower_corner(layout)
    corners[corner] = corners.get(corner, 0) + 1

print(f"Corner distribution: {corners}")
# Expected: At least 4 different corners represented
```

### Verify Results
```python
# Should see output like:
{
    'top_left': 3,
    'top_right': 2,
    'bottom_left': 2,
    'bottom_right': 3
}
# ✓ All 4 corners present
```

## Performance Impact

- **Minimal overhead**: O(n) where n = number of candidates (~30-50)
- **No additional placements**: Works with existing candidates
- **Sorting preserved**: Maintains score-based ordering within corners

## Future Enhancements

1. **Configurable per object type**: Different diversity rules for bathtub vs shower
2. **Wall diversity**: Ensure diversity in which wall objects are placed on
3. **Symmetry diversity**: Mix of symmetric and asymmetric layouts
4. **Size diversity**: Ensure variety in bathtub/shower sizes

---

**Created**: 2025-10-01  
**Last Updated**: 2025-10-01  
**Related Files**:
- `algorithms/beam_search.py` (implementation)
- `algorithms/placement.py` (placement strategies)
- `optimization/scoring.py` (scoring function)
