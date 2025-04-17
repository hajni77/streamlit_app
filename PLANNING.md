# 3D Bathroom Layout Generator - Project Planning

## Project Overview
The 3D Bathroom Layout Generator is a Streamlit web application that allows users to design and visualize bathroom layouts in both 3D and 2D. The application uses algorithms to automatically place bathroom fixtures in optimal positions based on room dimensions, fixture requirements, and design constraints.

## Goals
1. Create an intuitive interface for designing bathroom layouts
2. Generate realistic and practical bathroom designs
3. Visualize designs in both 3D and 2D
4. Optimize fixture placement for usability and aesthetics
5. Allow users to save and share their designs
6. Collect user feedback for continuous improvement

## Architecture

### Core Components

#### 1. User Interface (`app.py`)
- Streamlit web application
- Input forms for room dimensions and fixture selection
- Authentication system using Supabase
- Review submission and data storage

#### 2. Room Generation (`generate_room.py`)
- Core placement algorithm
- Object constraint handling
- Placement validation
- Multiple placement attempts with optimization

#### 3. Visualization (`visualization.py`)
- 3D visualization using Matplotlib
- 2D floorplan generation
- Shadow visualization for usability analysis
- Door and window rendering

#### 4. Optimization (`optimization.py`)
- Object position optimization
- Space utilization algorithms
- Wall proximity adjustments
- Overlap prevention

#### 5. Utilities (`utils.py`)
- Helper functions for geometry calculations
- Validation utilities
- Wall detection and distance calculations
- Object sizing and positioning utilities

#### 6. Data Models (`object_types.json`)
- Fixture specifications
- Constraint definitions
- Size ranges and optimal dimensions
- Placement priorities

#### 7. Authentication (`authentication.py`)
- User authentication flows
- Session management
- Protected routes

### Data Flow
1. User inputs room dimensions and selects fixtures
2. Application generates initial placement using `fit_objects_in_room`
3. Optimization algorithms improve the placement
4. 3D and 2D visualizations are generated
5. User reviews and can save the design
6. Feedback is stored for future improvements

## Design Principles

### 1. Usability
- Intuitive interface
- Clear visualization
- Practical layouts that follow bathroom design best practices

### 2. Modularity
- Separation of concerns between components
- Reusable utility functions
- Clear interfaces between modules

### 3. Optimization
- Efficient algorithms for fixture placement
- Space utilization optimization
- Consideration of real-world constraints (e.g., door swing space)

### 4. Extensibility
- Easy addition of new fixture types
- Configurable constraints
- Pluggable optimization algorithms

## Technical Constraints
- Python-based implementation
- Streamlit for web interface
- Matplotlib for visualization
- Supabase for authentication and data storage
- Maximum file size of 400 lines per module

## Style Guide
- PEP 8 compliant Python code
- Google-style docstrings
- Clear variable naming
- Comprehensive comments for complex algorithms
- Type hints for function parameters and return values

## Future Enhancements
1. Machine learning for layout optimization
2. AR/VR visualization options
3. Integration with product catalogs
4. Cost estimation
5. Plumbing and electrical layout consideration
6. Material and finish selection
7. Lighting simulation
8. Multiple room support for whole-house design

## Performance Targets
- Layout generation in under 5 seconds
- Smooth 3D visualization on standard hardware
- Support for complex bathroom designs with 10+ fixtures
- Responsive UI even during computation-intensive operations
