@echo off
REM Build script for C++ Bathroom Scoring Module (Windows)

echo ========================================
echo C++ Bathroom Scoring Module - Build
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.7+ and add it to PATH
    exit /b 1
)

REM Check if CMake is available
cmake --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: CMake not found in PATH
    echo Please install CMake 3.12+ and add it to PATH
    echo Download from: https://cmake.org/download/
    exit /b 1
)

echo Step 1: Installing pybind11...
pip install pybind11
if errorlevel 1 (
    echo ERROR: Failed to install pybind11
    exit /b 1
)

echo.
echo Step 2: Building and installing C++ module...
pip install . --no-build-isolation
if errorlevel 1 (
    echo ERROR: Build failed
    echo.
    echo Common issues:
    echo - No C++ compiler found: Install Visual Studio Build Tools
    echo - CMake errors: Check CMake version (need 3.12+)
    echo - Python dev headers missing: Reinstall Python with dev tools
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Testing the module...
python -c "import cpp_bathroom_scoring; print('SUCCESS! Version:', cpp_bathroom_scoring.__version__)"
if errorlevel 1 (
    echo WARNING: Module built but import failed
    exit /b 1
)

echo.
echo Next steps:
echo 1. Run tests: python test_cpp_scoring.py
echo 2. Read QUICKSTART.md for usage examples
echo 3. Check README.md for detailed documentation
echo.

pause
