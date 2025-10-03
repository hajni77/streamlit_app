# Quick Start Guide - C++ Bathroom Scoring

Get up and running with the C++ bathroom scoring module in 5 minutes.

## Prerequisites Check

Before starting, ensure you have:

- [ ] Python 3.7+ installed
- [ ] C++ compiler (Visual Studio on Windows, GCC/Clang on Linux/macOS)
- [ ] CMake 3.12+

### Quick Check Commands

```bash
# Check Python
python --version

# Check CMake
cmake --version

# Check C++ compiler (Windows)
cl

# Check C++ compiler (Linux/macOS)
g++ --version
```

## Installation (3 Steps)

### Step 1: Install pybind11

```bash
pip install pybind11
```

### Step 2: Navigate to the cpp_scoring directory

```bash
cd optimization/cpp_scoring
```

### Step 3: Build and install

```bash
pip install .
```

That's it! The module should now be installed.

## Quick Test

Test if the module works:

```bash
python -c "import cpp_bathroom_scoring; print('Success! Version:', cpp_bathroom_scoring.__version__)"
```

If you see "Success! Version: 1.0.0", you're ready to go!

## First Example (Copy & Paste)

Create a file `test_quick.py`:

```python
import cpp_bathroom_scoring as cpp_scoring

# Create scorer
scorer = cpp_scoring.BathroomScoringFunction()

# Create a sink
sink = cpp_scoring.PlacedObject()
sink.name = "sink"
sink.x, sink.y = 0, 100
sink.width, sink.depth, sink.height = 60, 50, 85
sink.wall = "top"
sink.shadow = (60, 0, 0, 0)

# Create a door
door = cpp_scoring.WindowDoor()
door.name = "door"
door.x, door.y = 150, 0
door.width, door.depth, door.height = 80, 10, 210
door.wall = "left"
door.hinge = "left"

# Create room
room = cpp_scoring.RoomSize(300, 250, 270)

# Score it!
score, breakdown = scorer.score([sink], [door], room, ["sink"])

print(f"Score: {score:.2f}")
print(f"Components: {len(breakdown)}")
```

Run it:

```bash
python test_quick.py
```

## Using with Existing Python Code

Replace your Python scorer with the C++ version:

```python
# Before (Python)
from optimization.scoring import BathroomScoringFunction
scorer = BathroomScoringFunction()
score, breakdown = scorer.score(layout)

# After (C++ with wrapper)
from optimization.cpp_scoring.python_wrapper import CppBathroomScoringWrapper
scorer = CppBathroomScoringWrapper()
score, breakdown = scorer.score(layout)
```

The API is identical - just faster!

## Performance Check

Run the benchmark:

```python
from optimization.cpp_scoring.python_wrapper import benchmark_comparison

# Assuming you have a layout object
results = benchmark_comparison(layout, iterations=100)
```

You should see 10-100x speedup depending on layout complexity.

## Troubleshooting

### "Module not found"

```bash
# Reinstall
cd optimization/cpp_scoring
pip install --force-reinstall .
```

### "CMake not found"

Install CMake:
- Windows: `choco install cmake` (or download from cmake.org)
- Linux: `sudo apt-get install cmake`
- macOS: `brew install cmake`

### "No C++ compiler"

- Windows: Install Visual Studio Build Tools
- Linux: `sudo apt-get install build-essential`
- macOS: `xcode-select --install`

### Build fails on Windows

Try specifying the generator:

```bash
pip install . --global-option="build_ext" --global-option="-G" --global-option="Visual Studio 16 2019"
```

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Run the test suite: `python test_cpp_scoring.py`
3. Integrate into your project using `python_wrapper.py`
4. Benchmark your specific use case

## Common Use Cases

### Batch Scoring

```python
import cpp_bathroom_scoring as cpp_scoring

scorer = cpp_scoring.BathroomScoringFunction()

# Score many layouts
scores = []
for layout_data in my_layouts:
    score, _ = scorer.score(
        layout_data['objects'],
        layout_data['doors'],
        layout_data['room'],
        layout_data['requested']
    )
    scores.append(score)
```

### RL Training Loop

```python
from optimization.cpp_scoring.python_wrapper import CppBathroomScoringWrapper

scorer = CppBathroomScoringWrapper()

for episode in range(num_episodes):
    layout = generate_layout()
    reward, _ = scorer.score(layout)
    # Use reward for RL update
```

### Beam Search Optimization

```python
import cpp_bathroom_scoring as cpp_scoring

scorer = cpp_scoring.BathroomScoringFunction()

def evaluate_candidates(candidates):
    scores = []
    for candidate in candidates:
        score, _ = scorer.score(
            candidate.objects,
            candidate.doors,
            candidate.room,
            candidate.requested
        )
        scores.append(score)
    return scores
```

## Support

- Full documentation: [README.md](README.md)
- Test suite: `python test_cpp_scoring.py`
- Python wrapper: [python_wrapper.py](python_wrapper.py)

Happy scoring! 🚀
