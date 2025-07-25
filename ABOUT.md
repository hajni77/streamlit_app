# 3D Bathroom Layout Generator

## Project Overview

The 3D Bathroom Layout Generator is an intelligent system that creates optimized bathroom layouts with realistic fixture placement. The system uses rule-based generation with various constraints to ensure practical, functional, and aesthetically pleasing bathroom designs.

## Key Features

### 1. Smart Fixture Placement
- **Constraint-Based Positioning**: Places fixtures according to real-world requirements
  - Wall-mounted fixtures (sinks, toilets) are properly positioned against walls
  - Corner fixtures are correctly placed in corners
  - Free-standing objects have appropriate spacing
- **Collision Detection**: Ensures no overlapping between fixtures
- **Window/Door Awareness**: Prevents fixtures from blocking windows and doors

### 2. Accessibility & Usability Scoring
- **Pathway Analysis**: Evaluates movement paths within the bathroom
- **Minimum Score Threshold**: Layouts with accessibility scores below 4 are automatically rejected
- **Clearance Validation**: Ensures sufficient space around fixtures (toilets, showers, etc.)

### 3. Size-Adaptive Design
- **Bathroom Size Recognition**: Adapts fixture selection based on available space
- **Smart Sink Selection**:
  - Small bathrooms (<300x300cm): Always uses regular sinks
  - Larger bathrooms: Intelligently chooses between regular and double sinks

### 4. Optimization Algorithms
- **Fixture Spacing**: Optimizes distances between fixtures for comfort and usability
- **Size Maximization**: Selects optimal fixture sizes based on available space
- **Position Refinement**: Fine-tunes fixture positions for better overall layout

### 5. Layout Comparison
- **Multi-criteria Evaluation**: Scores layouts based on multiple factors
- **Comparative Analysis**: Allows comparison between different generated layouts
- **Best Layout Selection**: Identifies the most optimal design from multiple candidates

## Technical Implementation

### Architecture
- **Modular Design**: Separated into placement, validation, and optimization components
- **Extensible Framework**: Easily add new fixture types and constraints
- **Rule-Based System**: Uses predefined rules for realistic bathroom layouts

### Validation System
- **Object Constraints**: Each fixture type has specific placement requirements
- **Room Constraints**: Overall bathroom layout must meet usability standards
- **Comprehensive Validation**: Multiple validation passes ensure quality results

### Future Enhancements
- **Reinforcement Learning**: Planning to implement RL agents to optimize floorplans by:
  - Moving fixtures to better positions
  - Switching fixture types when appropriate
  - Resizing objects for optimal space utilization
- **Style Templates**: Adding design style presets (modern, traditional, etc.)
- **User Preference Learning**: Adapting to individual user preferences over time

## Applications

- **Interior Design**: Assist designers in creating efficient bathroom layouts
- **Home Renovation**: Help homeowners visualize bathroom remodeling options
- **Real Estate Development**: Quickly generate optimal bathroom designs for new constructions
- **Virtual Reality Visualization**: Create 3D models for immersive design experiences

## Benefits

- **Time Efficiency**: Generate multiple layout options in seconds
- **Design Quality**: Ensure all designs meet practical usability requirements
- **Optimization**: Maximize space utilization in bathrooms of all sizes
- **Customization**: Adapt to specific user needs and preferences
- **Visualization**: Present realistic 3D models of potential bathroom designs