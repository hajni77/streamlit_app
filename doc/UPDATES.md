# Bathroom Layout Generator: Updates Summary

## Performance Tracking and Visualization System

This update introduces a comprehensive performance tracking system to monitor and analyze the efficiency of the bathroom layout generator. The system provides detailed insights into the time required for various operations, helping identify bottlenecks and optimize performance.

## Key Changes

### 1. Timing Logger System

- **New File:** `utils/timing_logger.py`
  - Added a context manager (`TimingContext`) to track operation durations
  - Created logging functionality that records timestamps, durations, and metadata
  - Implemented millisecond precision timing for accurate performance tracking
  - Added safeguards to prevent zero duration recordings

- **Modified Files:**
  - Updated `algorithms/beam_search.py` to track layout generation and object placement times
  - Updated `optimization/scoring.py` to track layout scoring times

### 2. Performance Analysis Tools

- **New File:** `utils/timing_analysis.py`
  - Created functions to analyze timing data and generate statistics
  - Added capability to identify performance patterns and bottlenecks
  - Implemented functions to generate performance recommendations

- **New File:** `utils/timing_visualizer.py`
  - Created visualization functions for timing data
  - Added support for various chart types (box plots, scatter plots, heatmaps)
  - Implemented performance scaling analysis

### 3. User Interface for Performance Analysis

- **Modified:** `app.py`
  - Added new "Performance" tab to the Streamlit interface
  - Implemented interactive visualization of timing data
  - Added filtering options for different operation types
  - Created summary statistics display and performance recommendations

### 4. Performance Metrics

The system now tracks the following operation types:
- `layout_generation`: Overall time to generate a layout
- `layout_scoring`: Time to evaluate a layout's quality
- `object_placement`: Time to place individual objects in the layout

For each operation, the following metadata is recorded:
- Operation type
- Duration in milliseconds
- Layout identifier
- Room dimensions
- Number of objects
- Additional context-specific information

### 5. Selective Timing

- Modified beam search algorithm to only track object placement timing for layouts that make it into the final beam (top 10)
- Added beam position information to the timing logs
- Optimized timing to focus on the most relevant operations

### 6. Utility Scripts

- **New File:** `visualize_timing.py`
  - Command-line script to generate timing visualizations
  - Options to save or display visualizations

- **New File:** `demo_visualizations.py`
  - Creates example visualizations with synthetic data if needed
  - Useful for development and testing

- **New File:** `fix_timing_durations.py`
  - Fixes any zero or invalid durations in existing timing logs
  - Calculates timing based on timestamp differences

- **New File:** `fix_timing_system.py`
  - Comprehensive script that updates all timing-related components
  - Backs up files before modification

### 7. Documentation

- **New File:** `logs/README.md`
  - Documentation for the timing system
  - Usage instructions for the timing tools
  - Examples of programmatic access to timing data

## Usage Instructions

### Recording Timing Data

Timing data is automatically collected during layout generation. For custom code:

```python
from utils.timing_logger import TimingContext

# Basic timing of an operation
with TimingContext("operation_name", layout_id="abc123") as tc:
    # Code to time goes here
    result = perform_operation()
    
    # Add additional information
    tc.add_info({"key": "value"})
```

### Analyzing Timing Data

From the Streamlit UI:
1. Navigate to the "Performance" tab
2. View summary statistics and visualizations
3. Filter by operation type or time range

From the command line:
```
python visualize_timing.py --show  # Display visualizations
python visualize_timing.py         # Save to timing_visualizations folder
```

## Benefits

- Enables data-driven optimization of the layout generator
- Identifies performance bottlenecks in the algorithm
- Provides insights into scaling behavior with room size and complexity
- Helps track performance improvements over time
- Supports development of more efficient algorithms

## User Authentication System

**Date: September 30, 2025**

This update introduces a comprehensive user authentication system for the Bathroom Layout Generator API, enabling secure access to user-specific layouts and features.

### Key Features

#### 1. Authentication API

- **New File:** `user_api.py`
  - Implementation of JWT token-based authentication
  - Support for multiple authentication providers (Supabase and Firebase)
  - User registration and login functionality
  - Protected API endpoints for user-specific data
  - Token verification and validation

#### 2. Integration Examples

- **New File:** `example_protected_api.py`
  - Demonstration of protected endpoints integration
  - Examples of user-specific layout generation and retrieval
  - Authentication middleware usage patterns

#### 3. Flutter Integration

- **New File:** `flutter_integration_example/auth_example.dart`
  - Flutter client for the authentication API
  - Login and registration UI examples
  - Token management and secure API requests
  - Social authentication integration (Google, GitHub)

#### 4. Documentation

- **New File:** `USER_API_README.md`
  - Comprehensive documentation for the authentication system
  - Setup instructions and environment configuration
  - API endpoint descriptions and usage examples
  - Security best practices

### Authentication Flow

The system supports the following authentication flows:

1. **Email/Password Authentication**
   - Standard login with email and password
   - User registration with email verification
   - Secure password hashing and storage

2. **Token-Based Authentication**
   - JWT tokens for API authentication
   - Configurable token expiration
   - Protected API endpoints

3. **OAuth/Social Authentication**
   - Integration with Firebase Authentication
   - Support for Google and GitHub login
   - Token verification and exchange

4. **Supabase Integration**
   - Direct authentication with Supabase
   - Row-level security for user data

### User-Specific Layout Management

With this authentication system, users can now:

- Save and retrieve their bathroom layouts
- Track layout generation history
- Share layouts with other users
- Access personalized layout recommendations

### Security Considerations

- All passwords are securely hashed using bcrypt
- JWT tokens use industry-standard security practices
- Environment variables for sensitive configuration
- CORS protection for API endpoints

### Usage Instructions

Authentication can be easily integrated with existing API endpoints:

```python
from fastapi import Depends
from user_api import get_current_active_user, User

@app.post("/generate_layout/")
async def generate_layout(data: dict, current_user: User = Depends(get_current_active_user)):
    # User is now authenticated
    # Generate layout and associate with current_user.id
    return {"message": "Layout generated for user: " + current_user.email}
```

### Integration with Main API

**Date: September 30, 2025**

The authentication system has been fully integrated into the main `api.py` file:

#### Changes Made:

1. **Imports Added**
   - Added `Depends` from FastAPI for dependency injection
   - Imported authentication utilities from `user_api.py`

2. **Authentication Routes Setup**
   - Called `setup_user_api_routes(app)` to register all authentication endpoints
   - All authentication endpoints are now available in the main API

3. **Protected Endpoints Added**
   - `POST /api/protected/generate` - Generate layouts for authenticated users
   - `GET /api/protected/layouts/` - Get all layouts for the current user
   - `GET /api/protected/layout/{layout_id}` - Get specific layout (with ownership check)
   - `DELETE /api/protected/layout/{layout_id}` - Delete user's layout
   - `GET /api/protected/layouts/public/` - Get public/template layouts

4. **User Association**
   - Layouts generated through protected endpoints are automatically associated with the user
   - User ID and email are stored in layout metadata
   - Ownership checks prevent unauthorized access to other users' layouts

5. **Backward Compatibility**
   - Public endpoints remain unchanged and functional
   - No breaking changes to existing API functionality
   - Optional `user_id` field added to `GenerateLayoutRequest` model

#### Testing

A comprehensive test script `test_auth_integration.py` has been created to verify:
- User registration and login
- Token-based authentication
- Protected endpoint access
- User layout management (create, read, delete)
- Unauthorized access prevention

Run tests with:
```bash
python test_auth_integration.py
```

#### Documentation Updates

- `API_DOCUMENTATION.md` updated with all authentication endpoints
- Flutter integration examples added
- Authentication best practices documented
