# 3D Bathroom Layout Generator - Task Tracking

## Current Tasks
Last updated: 2025-04-16

### High Priority
- [ ] Implement toilet placement constraint to avoid placement opposite to the door (referenced in generate_room.py)
- [ ] Improve optimization algorithm for better space utilization
- [ ] Add comprehensive error handling for edge cases in fixture placement

### Medium Priority
- [ ] Refactor code to improve modularity and reduce file sizes
- [ ] Add unit tests for core algorithms
- [ ] Implement more sophisticated collision detection
- [ ] Enhance 3D visualization with textures and materials
- [ ] Add ability to manually adjust fixture positions after automatic placement

### Low Priority
- [ ] Create user documentation and tutorials
- [ ] Implement additional fixture types
- [ ] Add export functionality for designs (e.g., PDF, 3D model formats)
- [ ] Create a gallery of pre-designed layouts for inspiration
- [ ] Implement undo/redo functionality

## Completed Tasks
- [x] Create basic Streamlit interface
- [x] Implement core fixture placement algorithm
- [x] Develop 3D visualization with Matplotlib
- [x] Add 2D floorplan visualization
- [x] Implement Supabase authentication
- [x] Create review submission functionality
- [x] Define fixture types and constraints in JSON format

## Discovered During Work
- [ ] Need to improve performance for rooms with many fixtures
- [ ] Consider adding accessibility compliance checking
- [ ] Explore alternative visualization libraries for better performance
- [ ] Add water and drainage pipe placement considerations

## Future Enhancements

### Algorithm Improvements
- [ ] Implement machine learning for layout optimization based on user reviews
- [ ] Add heatmap visualization for traffic flow and usability
- [ ] Develop more sophisticated shadow space calculations based on fixture usage patterns
- [ ] Implement multi-objective optimization (aesthetics, usability, cost)

### User Experience
- [ ] Add drag-and-drop interface for manual fixture placement
- [ ] Implement virtual reality visualization option
- [ ] Create mobile-friendly interface
- [ ] Add voice command support for hands-free design

### Integration
- [ ] Connect with product catalogs for real fixture dimensions and costs
- [ ] Implement cost estimation based on selected fixtures and room size
- [ ] Add integration with home design software
- [ ] Develop API for third-party applications

## Technical Debt
- [ ] Refactor visualization.py to reduce complexity and improve maintainability
- [ ] Optimize database queries and storage in app.py
- [ ] Improve type hinting throughout codebase
- [ ] Add comprehensive docstrings to all functions
- [ ] Create developer documentation for future contributors

## Bug Tracking
- [ ] Some fixtures may overlap in corner cases
- [ ] Shadow visualization sometimes extends beyond room boundaries
- [ ] Authentication flow has edge cases with token expiration
- [ ] 2D visualization doesn't always match 3D placement exactly

## Notes
- Prioritize usability improvements based on user feedback
- Consider performance optimizations for complex room layouts
- Explore alternative visualization techniques for better realism
- Research bathroom design best practices for algorithm improvements

## Create more constraints for reward function
-  if an object not placed on the wall or in the corner when must, that will be always zero point
- if a sink in the corner, get fewer point
- if the whole wall is covered, get more point
- if the whole corner is covered, get more point
- if sink in on the opposite wall of the door, get more point
- if toilet in on the opposite wall of the door, get fewer point
- if the distance between objects is less than 30 cm, get more point

## create a function which resize the objects to bigger size if the space is enough

## Create deep-q network 


## this project will be the backend for my flutter application, without the streamlit.

How to communicate flutter with backend?

1. when in the flutter app the generate button clicked, all information came to backend that needed for floorplan generation (beamsearch generate function).
2. When the Room floorplans generated one of them given back to the flutter app(layout positions)

You need to:
create functions to handle API calls and create a file siliral to app.py without the streamlit, which could be the main backend file for my project