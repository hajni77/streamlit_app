# Usage Examples - C++ Bathroom Scoring Module

Complete examples showing how to use the C++ scoring module in various scenarios.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Integration with Existing Code](#integration-with-existing-code)
3. [Batch Scoring](#batch-scoring)
4. [RL Training Loop](#rl-training-loop)
5. [Beam Search Optimization](#beam-search-optimization)
6. [Performance Benchmarking](#performance-benchmarking)

---

## Basic Usage

### Example 1: Simple Layout Scoring

```python
import cpp_bathroom_scoring as cpp_scoring

# Create the scoring function
scorer = cpp_scoring.BathroomScoringFunction()

# Create a sink
sink = cpp_scoring.PlacedObject()
sink.name = "sink"
sink.x, sink.y = 0, 100
sink.width, sink.depth, sink.height = 60, 50, 85
sink.wall = "top"
sink.must_be_against_wall = True
sink.shadow = (60, 0, 0, 0)  # top, left, right, bottom clearance

# Create a toilet
toilet = cpp_scoring.PlacedObject()
toilet.name = "toilet"
toilet.x, toilet.y = 200, 0
toilet.width, toilet.depth, toilet.height = 50, 60, 75
toilet.wall = "left"
toilet.must_be_against_wall = True
toilet.shadow = (60, 0, 0, 0)

# Create a door
door = cpp_scoring.WindowDoor()
door.name = "door"
door.x, door.y = 150, 0
door.width, door.depth, door.height = 80, 10, 210
door.wall = "left"
door.hinge = "left"
door.way = "inward"

# Create room dimensions
room = cpp_scoring.RoomSize(300, 250, 270)  # width, depth, height in cm

# Score the layout
placed_objects = [sink, toilet]
windows_doors = [door]
requested_objects = ["sink", "toilet"]

total_score, score_breakdown = scorer.score(
    placed_objects,
    windows_doors,
    room,
    requested_objects
)

print(f"Total Score: {total_score:.2f}")
print(f"\nScore Breakdown:")
for component, value in sorted(score_breakdown.items()):
    print(f"  {component:30s}: {value:6.2f}")
```

### Example 2: Using Helper Functions

```python
import cpp_bathroom_scoring as cpp_scoring

# Create objects from dictionaries
sink_dict = {
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

sink = cpp_scoring.create_placed_object_from_dict(sink_dict)

door_dict = {
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

door = cpp_scoring.create_window_door_from_dict(door_dict)

# Use them for scoring
scorer = cpp_scoring.BathroomScoringFunction()
room = cpp_scoring.RoomSize(300, 250, 270)
score, breakdown = scorer.score([sink], [door], room, ["sink"])
```

---

## Integration with Existing Code

### Example 3: Drop-in Replacement with Python Wrapper

```python
from optimization.cpp_scoring.python_wrapper import CppBathroomScoringWrapper

# Create wrapper (works with Layout objects)
scorer = CppBathroomScoringWrapper()

# Assuming you have a Layout object from your existing code
# layout = generate_bathroom_layout(...)

# Score it (exact same API as Python version)
total_score, score_breakdown = scorer.score(layout)

print(f"Total Score: {total_score:.2f}")
print(f"Critical constraints passed: {total_score > 0}")
```

### Example 4: Conditional C++ Usage with Fallback

```python
from optimization.cpp_scoring import is_cpp_available

if is_cpp_available():
    print("Using C++ scorer (fast)")
    from optimization.cpp_scoring import CppBathroomScoringWrapper
    scorer = CppBathroomScoringWrapper()
else:
    print("Using Python scorer (fallback)")
    from optimization.scoring import BathroomScoringFunction
    scorer = BathroomScoringFunction()

# Use scorer regardless of which one is loaded
score, breakdown = scorer.score(layout)
```

---

## Batch Scoring

### Example 5: Score Multiple Layouts

```python
import cpp_bathroom_scoring as cpp_scoring
import time

# Create scorer once
scorer = cpp_scoring.BathroomScoringFunction()

# Generate or load multiple layouts
layouts = []  # Your list of layout data

# Score all layouts
scores = []
start_time = time.time()

for layout_data in layouts:
    score, breakdown = scorer.score(
        layout_data['objects'],
        layout_data['doors'],
        layout_data['room'],
        layout_data['requested']
    )
    scores.append({
        'layout_id': layout_data['id'],
        'score': score,
        'breakdown': breakdown
    })

elapsed = time.time() - start_time
print(f"Scored {len(layouts)} layouts in {elapsed:.2f}s")
print(f"Average: {elapsed/len(layouts)*1000:.2f}ms per layout")

# Find best layout
best = max(scores, key=lambda x: x['score'])
print(f"\nBest layout: {best['layout_id']} with score {best['score']:.2f}")
```

### Example 6: Parallel Batch Scoring

```python
import cpp_bathroom_scoring as cpp_scoring
from concurrent.futures import ThreadPoolExecutor
import time

def score_layout(layout_data):
    """Score a single layout."""
    scorer = cpp_scoring.BathroomScoringFunction()
    score, breakdown = scorer.score(
        layout_data['objects'],
        layout_data['doors'],
        layout_data['room'],
        layout_data['requested']
    )
    return {
        'layout_id': layout_data['id'],
        'score': score,
        'breakdown': breakdown
    }

# Your layouts
layouts = []  # List of layout data

# Score in parallel
start_time = time.time()
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(score_layout, layouts))

elapsed = time.time() - start_time
print(f"Scored {len(layouts)} layouts in {elapsed:.2f}s using 4 threads")
```

---

## RL Training Loop

### Example 7: Reinforcement Learning Integration

```python
from optimization.cpp_scoring.python_wrapper import CppBathroomScoringWrapper
import numpy as np

class BathroomLayoutEnv:
    """RL environment for bathroom layout optimization."""
    
    def __init__(self):
        self.scorer = CppBathroomScoringWrapper()
        self.reset()
    
    def reset(self):
        """Reset environment to initial state."""
        self.layout = self._create_empty_layout()
        return self._get_state()
    
    def step(self, action):
        """Take an action and return reward."""
        # Apply action to layout
        self._apply_action(action)
        
        # Score the layout using C++ (fast!)
        score, breakdown = self.scorer.score(self.layout)
        
        # Calculate reward
        reward = score / 100.0  # Normalize to 0-1
        
        # Check if done
        done = self._is_terminal()
        
        return self._get_state(), reward, done, breakdown
    
    def _create_empty_layout(self):
        # Your layout creation logic
        pass
    
    def _get_state(self):
        # Convert layout to state representation
        pass
    
    def _apply_action(self, action):
        # Apply action to modify layout
        pass
    
    def _is_terminal(self):
        # Check if episode is done
        pass

# Training loop
env = BathroomLayoutEnv()
num_episodes = 1000

for episode in range(num_episodes):
    state = env.reset()
    total_reward = 0
    
    for step in range(100):
        action = select_action(state)  # Your policy
        next_state, reward, done, info = env.step(action)
        
        # Update your RL agent here
        total_reward += reward
        state = next_state
        
        if done:
            break
    
    if episode % 100 == 0:
        print(f"Episode {episode}: Total Reward = {total_reward:.2f}")
```

---

## Beam Search Optimization

### Example 8: Beam Search with C++ Scoring

```python
import cpp_bathroom_scoring as cpp_scoring
from typing import List, Tuple
import heapq

def beam_search_layout_optimization(
    initial_layouts: List,
    beam_width: int = 10,
    max_iterations: int = 50
) -> Tuple[float, dict]:
    """
    Optimize bathroom layout using beam search with C++ scoring.
    
    Args:
        initial_layouts: Starting layouts
        beam_width: Number of candidates to keep
        max_iterations: Maximum search iterations
    
    Returns:
        Best score and layout
    """
    scorer = cpp_scoring.BathroomScoringFunction()
    
    # Initialize beam with scored layouts
    beam = []
    for layout in initial_layouts:
        score, breakdown = scorer.score(
            layout['objects'],
            layout['doors'],
            layout['room'],
            layout['requested']
        )
        heapq.heappush(beam, (-score, layout))  # Max heap
    
    best_score = -float('inf')
    best_layout = None
    
    for iteration in range(max_iterations):
        # Generate candidates from current beam
        candidates = []
        
        for score, layout in beam[:beam_width]:
            # Generate variations of this layout
            variations = generate_layout_variations(layout)
            
            # Score all variations (fast with C++)
            for variation in variations:
                var_score, breakdown = scorer.score(
                    variation['objects'],
                    variation['doors'],
                    variation['room'],
                    variation['requested']
                )
                candidates.append((-var_score, variation))
                
                # Track best
                if var_score > best_score:
                    best_score = var_score
                    best_layout = variation
        
        # Keep top beam_width candidates
        beam = heapq.nsmallest(beam_width, candidates)
        
        print(f"Iteration {iteration}: Best score = {best_score:.2f}")
    
    return best_score, best_layout

def generate_layout_variations(layout):
    """Generate variations of a layout."""
    # Your variation logic here
    return []

# Run beam search
initial_layouts = []  # Your initial layouts
best_score, best_layout = beam_search_layout_optimization(
    initial_layouts,
    beam_width=20,
    max_iterations=100
)

print(f"\nFinal best score: {best_score:.2f}")
```

---

## Performance Benchmarking

### Example 9: Compare Python vs C++ Performance

```python
from optimization.cpp_scoring.python_wrapper import benchmark_comparison
from optimization.scoring import BathroomScoringFunction as PythonScorer
from optimization.cpp_scoring import CppBathroomScoringWrapper
import time

# Assuming you have a layout object
# layout = your_layout

# Quick benchmark
print("Running benchmark (100 iterations)...")
results = benchmark_comparison(layout, iterations=100)

print(f"\nResults:")
print(f"  Python: {results['python_avg']*1000:.2f}ms per score")
print(f"  C++:    {results['cpp_avg']*1000:.2f}ms per score")
print(f"  Speedup: {results['speedup']:.1f}x")
```

### Example 10: Detailed Performance Analysis

```python
import cpp_bathroom_scoring as cpp_scoring
from optimization.scoring import BathroomScoringFunction as PythonScorer
import time
import numpy as np

def benchmark_detailed(layouts, iterations=10):
    """Detailed performance comparison."""
    
    # Python benchmark
    python_scorer = PythonScorer()
    python_times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        for layout in layouts:
            python_scorer.score(layout)
        python_times.append(time.perf_counter() - start)
    
    # C++ benchmark
    cpp_scorer = cpp_scoring.BathroomScoringFunction()
    cpp_times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        for layout_data in layouts:
            cpp_scorer.score(
                layout_data['objects'],
                layout_data['doors'],
                layout_data['room'],
                layout_data['requested']
            )
        cpp_times.append(time.perf_counter() - start)
    
    # Statistics
    python_mean = np.mean(python_times)
    python_std = np.std(python_times)
    cpp_mean = np.mean(cpp_times)
    cpp_std = np.std(cpp_times)
    
    print(f"Benchmark Results ({len(layouts)} layouts, {iterations} iterations)")
    print(f"\nPython:")
    print(f"  Mean: {python_mean:.4f}s ± {python_std:.4f}s")
    print(f"  Per layout: {python_mean/len(layouts)*1000:.2f}ms")
    
    print(f"\nC++:")
    print(f"  Mean: {cpp_mean:.4f}s ± {cpp_std:.4f}s")
    print(f"  Per layout: {cpp_mean/len(layouts)*1000:.2f}ms")
    
    print(f"\nSpeedup: {python_mean/cpp_mean:.1f}x")
    print(f"Time saved: {(python_mean - cpp_mean):.4f}s per batch")

# Run benchmark
layouts = []  # Your layouts
benchmark_detailed(layouts, iterations=10)
```

---

## Tips and Best Practices

### 1. Reuse Scorer Instances

```python
# Good: Create once, use many times
scorer = cpp_scoring.BathroomScoringFunction()
for layout in layouts:
    score, _ = scorer.score(...)

# Avoid: Creating new scorer each time
for layout in layouts:
    scorer = cpp_scoring.BathroomScoringFunction()  # Slower
    score, _ = scorer.score(...)
```

### 2. Use Python Wrapper for Layout Objects

```python
# If you have Layout objects, use the wrapper
from optimization.cpp_scoring.python_wrapper import CppBathroomScoringWrapper

scorer = CppBathroomScoringWrapper()
score, breakdown = scorer.score(layout)  # Automatic conversion
```

### 3. Check Critical Constraints

```python
score, breakdown = scorer.score(...)

# Check if layout passes critical constraints
if score == 0:
    print("Layout failed critical constraints:")
    if breakdown['no_overlap'] == 0:
        print("  - Objects overlap")
    if breakdown['corner_accessibility'] == 0:
        print("  - Corners not accessible")
    if breakdown['shower_space'] == 0:
        print("  - Shower has no free side")
```

### 4. Use Score Breakdown for Debugging

```python
score, breakdown = scorer.score(...)

# Find weak points in layout
weak_points = {k: v for k, v in breakdown.items() if v < 5}
print(f"Weak scoring components: {weak_points}")

# Find strengths
strengths = {k: v for k, v in breakdown.items() if v >= 9}
print(f"Strong scoring components: {strengths}")
```

---

## Complete Example: Layout Generator with C++ Scoring

```python
import cpp_bathroom_scoring as cpp_scoring
import random

class FastLayoutGenerator:
    """Generate and score bathroom layouts using C++ for speed."""
    
    def __init__(self, room_size):
        self.room = cpp_scoring.RoomSize(*room_size)
        self.scorer = cpp_scoring.BathroomScoringFunction()
    
    def generate_and_score(self, num_layouts=100):
        """Generate multiple layouts and return best."""
        best_score = -1
        best_layout = None
        
        for i in range(num_layouts):
            # Generate random layout
            objects = self._generate_random_objects()
            doors = self._generate_doors()
            requested = ["sink", "toilet"]
            
            # Score it (fast!)
            score, breakdown = self.scorer.score(
                objects, doors, self.room, requested
            )
            
            if score > best_score:
                best_score = score
                best_layout = {
                    'objects': objects,
                    'doors': doors,
                    'score': score,
                    'breakdown': breakdown
                }
            
            if (i + 1) % 10 == 0:
                print(f"Generated {i+1} layouts, best score: {best_score:.2f}")
        
        return best_layout
    
    def _generate_random_objects(self):
        # Your object generation logic
        return []
    
    def _generate_doors(self):
        # Your door generation logic
        return []

# Use it
generator = FastLayoutGenerator((300, 250, 270))
best = generator.generate_and_score(num_layouts=1000)
print(f"\nBest layout score: {best['score']:.2f}")
```

---

For more examples and documentation, see:
- **README.md** - Complete documentation
- **QUICKSTART.md** - Quick start guide
- **test_cpp_scoring.py** - Test examples
