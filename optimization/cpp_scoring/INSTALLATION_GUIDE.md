# Installation Guide - C++ Bathroom Scoring Module

Complete step-by-step installation guide for all platforms.

## Table of Contents

1. [Windows Installation](#windows-installation)
2. [Linux Installation](#linux-installation)
3. [macOS Installation](#macos-installation)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

---

## Windows Installation

### Prerequisites

#### 1. Install Python 3.7+

Download from [python.org](https://www.python.org/downloads/)

**Important**: Check "Add Python to PATH" during installation

Verify:
```cmd
python --version
```

#### 2. Install Visual Studio Build Tools

**Option A**: Visual Studio 2019/2022 (Recommended)
- Download from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/downloads/)
- Select "Desktop development with C++" workload
- Install

**Option B**: Build Tools Only (Smaller download)
- Download [Build Tools for Visual Studio](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
- Select "C++ build tools"
- Install

Verify:
```cmd
cl
```
(Should show Microsoft C/C++ compiler version)

#### 3. Install CMake

**Option A**: Using Chocolatey (if installed)
```cmd
choco install cmake
```

**Option B**: Direct Download
- Download from [cmake.org](https://cmake.org/download/)
- Run installer
- **Important**: Check "Add CMake to system PATH"

Verify:
```cmd
cmake --version
```

### Build Steps

#### Option 1: Automated Build (Recommended)

```cmd
cd optimization\cpp_scoring
build.bat
```

The script will:
1. Check prerequisites
2. Install pybind11
3. Build the C++ module
4. Test the installation

#### Option 2: Manual Build

```cmd
cd optimization\cpp_scoring

REM Install pybind11
pip install pybind11

REM Build and install
pip install .
```

### Verification

```cmd
python -c "import cpp_bathroom_scoring; print('Success! Version:', cpp_bathroom_scoring.__version__)"
```

---

## Linux Installation

### Prerequisites

#### 1. Install Python Development Headers

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3-dev python3-pip
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-devel python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
```

Verify:
```bash
python3 --version
```

#### 2. Install Build Tools

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential cmake
```

**Fedora/RHEL:**
```bash
sudo dnf install gcc gcc-c++ cmake
```

**Arch Linux:**
```bash
sudo pacman -S base-devel cmake
```

Verify:
```bash
g++ --version
cmake --version
```

### Build Steps

```bash
cd optimization/cpp_scoring

# Install pybind11
pip3 install pybind11

# Build and install
pip3 install .
```

### Verification

```bash
python3 -c "import cpp_bathroom_scoring; print('Success! Version:', cpp_bathroom_scoring.__version__)"
```

---

## macOS Installation

### Prerequisites

#### 1. Install Xcode Command Line Tools

```bash
xcode-select --install
```

Click "Install" in the dialog that appears.

Verify:
```bash
clang --version
```

#### 2. Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 3. Install Python and CMake

```bash
brew install python cmake
```

Verify:
```bash
python3 --version
cmake --version
```

### Build Steps

```bash
cd optimization/cpp_scoring

# Install pybind11
pip3 install pybind11

# Build and install
pip3 install .
```

### Verification

```bash
python3 -c "import cpp_bathroom_scoring; print('Success! Version:', cpp_bathroom_scoring.__version__)"
```

---

## Verification

### Quick Test

After installation, run:

```python
python test_cpp_scoring.py
```

You should see:
```
========================================
C++ BATHROOM SCORING MODULE - TEST SUITE
========================================

TEST 1: Module Information
...
✓ Test PASSED

TEST 2: Basic Functionality
...
✓ Test PASSED

...

========================================
TEST SUMMARY
========================================
Total tests: 5
Passed: 5
Failed: 0

✓ ALL TESTS PASSED!
```

### Integration Test

Test with your existing code:

```python
from optimization.cpp_scoring.python_wrapper import CppBathroomScoringWrapper

# This should work if you have a layout object
scorer = CppBathroomScoringWrapper()
# score, breakdown = scorer.score(your_layout)
print("C++ scorer ready!")
```

---

## Troubleshooting

### Windows Issues

#### "CMake not found"
**Solution**: 
1. Reinstall CMake and check "Add to PATH"
2. Restart terminal/IDE
3. Verify: `cmake --version`

#### "cl is not recognized"
**Solution**:
1. Install Visual Studio Build Tools with C++ workload
2. Use "Developer Command Prompt for VS"
3. Or run: `"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"`

#### "error: Microsoft Visual C++ 14.0 or greater is required"
**Solution**: Install Visual Studio Build Tools (see Prerequisites)

#### Build succeeds but import fails
**Solution**:
```cmd
pip install --force-reinstall .
```

### Linux Issues

#### "Python.h: No such file or directory"
**Solution**:
```bash
sudo apt-get install python3-dev
```

#### "cmake: command not found"
**Solution**:
```bash
sudo apt-get install cmake
```

#### Permission denied
**Solution**:
```bash
pip3 install --user .
```

### macOS Issues

#### "xcrun: error: invalid active developer path"
**Solution**:
```bash
xcode-select --install
```

#### "clang: error: unsupported option '-fopenmp'"
**Solution**: This is normal, OpenMP is not used. Ignore this warning.

#### "ld: library not found"
**Solution**:
```bash
# Reinstall Python
brew reinstall python

# Rebuild
pip3 install --force-reinstall .
```

### General Issues

#### "ModuleNotFoundError: No module named 'cpp_bathroom_scoring'"
**Solution**:
1. Ensure you're in the correct directory: `cd optimization/cpp_scoring`
2. Reinstall: `pip install --force-reinstall .`
3. Check Python path: `python -c "import sys; print(sys.path)"`

#### "ImportError: DLL load failed" (Windows)
**Solution**:
1. Install Visual C++ Redistributable
2. Rebuild with: `pip install --force-reinstall .`

#### Build is very slow
**Solution**: This is normal for first build. Subsequent builds are faster.

#### Tests fail
**Solution**:
1. Check Python version matches (3.7+)
2. Verify build completed successfully
3. Try: `pip install --force-reinstall .`

---

## Advanced Installation

### Development Installation

For development (changes to Python files reflect immediately):

```bash
pip install -e .
```

### Debug Build

For debugging with symbols:

```bash
mkdir build_debug
cd build_debug
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build .
```

### Specific Python Version

```bash
# Use specific Python version
python3.9 -m pip install .
```

### Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install
pip install .
```

---

## Uninstallation

```bash
pip uninstall cpp-bathroom-scoring
```

---

## Getting Help

1. **Check logs**: Look at build output for specific errors
2. **Verify prerequisites**: Ensure all tools are installed and in PATH
3. **Try clean build**: Delete `build/` directory and rebuild
4. **Check Python version**: Must be 3.7+
5. **Check compiler**: Must support C++17

### Support Resources

- **QUICKSTART.md**: Quick start guide
- **README.md**: Full documentation
- **test_cpp_scoring.py**: Test suite
- **IMPLEMENTATION_SUMMARY.md**: Technical details

---

## Next Steps

After successful installation:

1. ✅ Run test suite: `python test_cpp_scoring.py`
2. ✅ Read QUICKSTART.md for usage examples
3. ✅ Try the Python wrapper with your layouts
4. ✅ Run benchmarks to see performance gains

Happy scoring! 🚀
