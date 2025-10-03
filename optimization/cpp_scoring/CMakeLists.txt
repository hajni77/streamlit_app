cmake_minimum_required(VERSION 3.12)
project(cpp_bathroom_scoring)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Optimization flags
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

if(MSVC)
    set(CMAKE_CXX_FLAGS_RELEASE "/O2 /DNDEBUG")
    set(CMAKE_CXX_FLAGS_DEBUG "/Od /Zi")
else()
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")
    set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
endif()

# Find Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Find pybind11 - try CONFIG first, then fallback to Python module
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    # Use pybind11's Python module to get CMake configuration
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
        OUTPUT_VARIABLE pybind11_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE pybind11_RESULT
    )
    if(pybind11_RESULT EQUAL 0)
        find_package(pybind11 CONFIG REQUIRED PATHS ${pybind11_DIR} NO_DEFAULT_PATH)
    else()
        message(FATAL_ERROR "pybind11 not found. Install with: pip install pybind11")
    endif()
endif()

# Source files
set(SOURCES
    bathroom_scoring.cpp
    bindings.cpp
)

set(HEADERS
    bathroom_scoring.h
)

# Create the Python module
pybind11_add_module(cpp_bathroom_scoring ${SOURCES} ${HEADERS})

# Set properties
set_target_properties(cpp_bathroom_scoring PROPERTIES
    CXX_VISIBILITY_PRESET hidden
    INTERPROCEDURAL_OPTIMIZATION TRUE
)

# Platform-specific settings
if(MSVC)
    target_compile_options(cpp_bathroom_scoring PRIVATE /W4 /WX-)
else()
    target_compile_options(cpp_bathroom_scoring PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Installation
install(TARGETS cpp_bathroom_scoring
    LIBRARY DESTINATION .
    RUNTIME DESTINATION .
)
